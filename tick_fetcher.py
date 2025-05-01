# tick_fetcher.py
#!/usr/bin/env python3

import time
import datetime
import pytz
import MetaTrader5 as mt5
import pandas_market_calendars as mcal
from pymongo import MongoClient, errors
import logging
import argparse
import os
import sys

def parse_args():
    parser = argparse.ArgumentParser(description='Fetch and store ticks from MT5')
    parser.add_argument('--mt5_path', required=True, help='Path to MT5 executable')
    parser.add_argument('--account', required=True, type=int, help='MT5 account number')
    parser.add_argument('--password', required=True, help='MT5 password')
    parser.add_argument('--server', required=True, help='MT5 server')
    parser.add_argument('--symbol', required=True, help='Symbol to fetch (e.g. EURUSD)')
    parser.add_argument('--mongo_uri', default="mongodb://localhost:27017/", 
                        help='MongoDB URI (default: mongodb://localhost:27017/)')
    parser.add_argument('--fetch_interval', type=int, default=1,
                        help='Seconds between fetches (default: 1)')
    parser.add_argument('--history_batch', type=int, default=500,
                        help='Number of ticks per batch when fetching history (default: 500)')
    return parser.parse_args()

# Timezones
LOCAL_TZ = pytz.timezone('Asia/Nicosia')  # local timezone
MARKET_TZ = pytz.timezone('US/Eastern')    # market timezone

# Market calendar (NYSE)
MARKET_CAL = mcal.get_calendar('NYSE')

# track last inserted tick timestamp (seconds since epoch)
LAST_TICK_TS = None

def connect_mongo(mongo_uri, db_name, collection_name):
    client = MongoClient(mongo_uri)
    col = client[db_name][collection_name]
    # unique index to prevent duplicate tick inserts
    col.create_index([
        ("symbol", 1),
        ("time", 1),
        ("bid", 1),
        ("ask", 1)
    ], unique=True)
    return col, client


def is_market_open(now_local=None):
    """
    Check Forex market hours: opens Sunday 22:00 UTC, closes Friday 22:00 UTC.
    """
    if now_local is None:
        now_local = datetime.datetime.now(LOCAL_TZ)
    # convert to UTC
    dt_utc = now_local.astimezone(pytz.UTC)
    wd = dt_utc.weekday()  # Mon=0 ... Sun=6
    hhmm = dt_utc.hour + dt_utc.minute/60.0

    # Saturday (5): closed all day
    if wd == 5:
        return False
    # Sunday (6): open only at or after 22:00 UTC
    if wd == 6:
        return hhmm >= 22.0
    # Friday (4): open until 22:00 UTC
    if wd == 4:
        return hhmm < 22.0
    # Mon–Thu (0–3): open 24h
    return True


def fetch_and_store(collection, symbol, history_batch):
    global LAST_TICK_TS
    # retrieve latest tick info
    tick_info = mt5.symbol_info_tick(symbol)
    if tick_info is None:
        logging.error(f"symbol_info_tick failed: {mt5.last_error()}")
        return
    now = tick_info.time

    # initial setup: get history around now to set LAST_TICK_TS
    if LAST_TICK_TS is None:
        history = mt5.copy_ticks_from(symbol, now, history_batch, mt5.COPY_TICKS_ALL)
        if history is None or len(history) == 0:
            logging.warning("No history ticks retrieved on first run")
            LAST_TICK_TS = now
        else:
            LAST_TICK_TS = max(h['time'].item() for h in history)
            logging.info(f"Initialized LAST_TICK_TS={LAST_TICK_TS}")
        return

    # fetch all ticks since last timestamp
    ticks = mt5.copy_ticks_range(symbol, LAST_TICK_TS, now, mt5.COPY_TICKS_ALL)
    if ticks is None:
        logging.error(f"mt5.copy_ticks_range failed: {mt5.last_error()}")
        return

    # filter out any duplicates
    new_ticks = [t for t in ticks if t['time'].item() > LAST_TICK_TS]
    if not new_ticks:
        return

    inserted = 0
    for t in new_ticks:
        doc = {name: t[name].item() for name in ticks.dtype.names}
        ts = doc['time']
        dt_utc = datetime.datetime.fromtimestamp(ts, tz=pytz.UTC)
        dt_local = dt_utc.astimezone(LOCAL_TZ)
        doc.update({
            "symbol": symbol,
            "timestamp": ts,
            "datetime_utc": dt_utc.isoformat(),
            "datetime_local": dt_local.isoformat()
        })
        try:
            collection.insert_one(doc)
            inserted += 1
        except errors.DuplicateKeyError:
            continue

    # update LAST_TICK_TS to highest timestamp seen
    LAST_TICK_TS = max(t['time'].item() for t in new_ticks)
    logging.info(f"Inserted {inserted}/{len(new_ticks)} ticks; updated LAST_TICK_TS={LAST_TICK_TS}")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
    
    args = parse_args()
    
    # Set MT5 path
    if args.mt5_path:
        mt5_path = os.path.normpath(args.mt5_path)
        if not os.path.exists(mt5_path):
            logging.critical(f"MT5 executable not found at: {mt5_path}")
            sys.exit(1)
        mt5.set_path(mt5_path)
    
    # Database settings
    db_name = "mt5_data"
    collection_name = f"ticks_{args.symbol}"
    
    # initialize MT5 connection
    if not mt5.initialize():
        logging.critical(f"MT5 initialize() failed: {mt5.last_error()}")
        return
    
    # Login to MT5
    if not mt5.login(args.account, args.password, args.server):
        logging.critical(f"MT5 login failed: {mt5.last_error()}")
        mt5.shutdown()
        return
    
    logging.info(f"Connected to MT5: account={args.account}, server={args.server}")
    logging.info(f"Fetching ticks for {args.symbol}")

    col, client = connect_mongo(args.mongo_uri, db_name, collection_name)
    logging.info(f"Connected to MongoDB: {args.mongo_uri}, collection={collection_name}")
    logging.info("Started tick fetcher")

    try:
        while True:
            now_local = datetime.datetime.now(LOCAL_TZ)
            if is_market_open(now_local):
                fetch_and_store(col, args.symbol, args.history_batch)
            else:
                logging.info(f"Market closed at {now_local.isoformat()}, skipping fetch")
            time.sleep(args.fetch_interval)
    except KeyboardInterrupt:
        logging.info("Shutting down (KeyboardInterrupt)")
    finally:
        mt5.shutdown()
        client.close()


if __name__ == "__main__":
    main()
