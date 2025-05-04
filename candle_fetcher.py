# candle_fetcher.py
#!/usr/bin/env python3

import time
import datetime
import pytz
import MetaTrader5 as mt5
import pandas_market_calendars as mcal
from pymongo import MongoClient
import logging
import argparse
import os
import sys

def parse_args():
    parser = argparse.ArgumentParser(description='Fetch and store candles from MT5')
    parser.add_argument('--timeframe', required=True, choices=['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1'], 
                        help='Timeframe for candles')
    parser.add_argument('--mt5_path', required=True, help='Path to MT5 executable')
    parser.add_argument('--account', required=True, type=int, help='MT5 account number')
    parser.add_argument('--password', required=True, help='MT5 password')
    parser.add_argument('--server', required=True, help='MT5 server')
    parser.add_argument('--symbol', required=True, help='Symbol to fetch (e.g. EURUSD)')
    parser.add_argument('--mongo_uri', default="mongodb://localhost:27017/", 
                        help='MongoDB URI (default: mongodb://localhost:27017/)')
    parser.add_argument('--fetch_interval', type=int, default=60,
                        help='Seconds between fetches (default: 60)')
    parser.add_argument('--candles_per_fetch', type=int, default=1,
                        help='Number of candles per fetch (default: 1)')
    return parser.parse_args()

# Timeframe mapping
TIMEFRAME_MAP = {
    'M1': mt5.TIMEFRAME_M1,
    'M5': mt5.TIMEFRAME_M5,
    'M15': mt5.TIMEFRAME_M15,
    'M30': mt5.TIMEFRAME_M30,
    'H1': mt5.TIMEFRAME_H1,
    'H4': mt5.TIMEFRAME_H4,
    'D1': mt5.TIMEFRAME_D1
}

# Timezones
LOCAL_TZ = pytz.timezone('Asia/Nicosia')  # local timezone
MARKET_TZ = pytz.timezone('US/Eastern')    # market timezone

# Market calendar
MARKET_CAL = mcal.get_calendar('NYSE')

def connect_mongo(mongo_uri, db_name, collection_name):
    client = MongoClient(mongo_uri)
    return client[db_name][collection_name], client


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


def fetch_and_store(collection, symbol, timeframe, candles_per_fetch):
    # fetch the most recent candles
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, candles_per_fetch)
    if rates is None:
        logging.error(f"mt5.copy_rates_from_pos failed: {mt5.last_error()}")
        return

    for r in rates:
        # convert record to native Python types
        doc = {name: r[name].item() for name in rates.dtype.names}
        # original MT5 timestamp and converted datetimes
        ts = doc.get('time')  # seconds since epoch
        dt_utc = datetime.datetime.fromtimestamp(ts, tz=pytz.UTC)
        dt_local = dt_utc.astimezone(LOCAL_TZ)
        doc.update({
            "symbol": symbol,
            "timeframe": int(timeframe),
            "timestamp": ts,
            "datetime_utc": dt_utc.isoformat(),
            "datetime_local": dt_local.isoformat()
        })

        collection.insert_one(doc)
        logging.info(f"Inserted candle @ {doc['datetime_local']} → {doc}")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
    
    args = parse_args()
    
    # Convert timeframe string to MT5 constant
    timeframe = TIMEFRAME_MAP[args.timeframe]
    
    # Database settings
    db_name = "mt5_data"
    collection_name = f"candles_{args.symbol}_{args.timeframe}"
    
    # Check MT5 executable path exists
    if args.mt5_path:
        mt5_path = os.path.normpath(args.mt5_path)
        if not os.path.exists(mt5_path):
            logging.critical(f"MT5 executable not found at: {mt5_path}")
            sys.exit(1)
    
    # Initialize MT5 connection with login credentials
    if not mt5.initialize(
        path=args.mt5_path,
        login=args.account,
        password=args.password,
        server=args.server
    ):
        logging.critical(f"MT5 initialize() failed: {mt5.last_error()}")
        return
    
    # Display connection info
    logging.info(f"MT5 Package Version: {mt5.__version__}")
    logging.info(f"Terminal Info: {mt5.terminal_info()}")
    logging.info(f"MT5 Version: {mt5.version()}")
    
    logging.info(f"Connected to MT5: account={args.account}, server={args.server}")
    logging.info(f"Fetching {args.timeframe} candles for {args.symbol}")

    # connect to MongoDB
    col, client = connect_mongo(args.mongo_uri, db_name, collection_name)
    logging.info(f"Connected to MongoDB: {args.mongo_uri}, collection={collection_name}")
    logging.info("Started candle fetcher")

    try:
        while True:
            now_local = datetime.datetime.now(LOCAL_TZ)
            if is_market_open(now_local):
                fetch_and_store(col, args.symbol, timeframe, args.candles_per_fetch)
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
