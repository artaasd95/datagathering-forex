#!/usr/bin/env python3

import time
import datetime
import pytz
import MetaTrader5 as mt5
import pandas as pd
from pymongo import MongoClient, errors
import logging
import argparse
import os
import sys
import csv
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description='Fetch historical data for a long timeframe by breaking it into smaller chunks')
    parser.add_argument('--timeframe', required=True, choices=['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1'], 
                        help='Timeframe for candles')
    parser.add_argument('--mt5_path', required=False, help='Path to MT5 executable')
    parser.add_argument('--account', required=False, type=int, help='MT5 account number')
    parser.add_argument('--password', required=False, help='MT5 password')
    parser.add_argument('--server', required=False, help='MT5 server')
    parser.add_argument('--symbol', required=True, help='Symbol to fetch (e.g. EURUSD)')
    parser.add_argument('--start_date', required=True, help='Start date in format YYYY-MM-DD')
    parser.add_argument('--end_date', required=True, help='End date in format YYYY-MM-DD')
    parser.add_argument('--mongo_uri', default="mongodb://localhost:27017/", 
                        help='MongoDB URI (default: mongodb://localhost:27017/)')
    parser.add_argument('--csv_output', default=None, help='Path to CSV output file (optional)')
    parser.add_argument('--chunk_days', type=int, default=2, 
                        help='Number of days per chunk (default: 2)')
    parser.add_argument('--min_data_points', type=int, default=10, 
                        help='Minimum number of data points to consider a chunk valid (default: 10)')
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
UTC_TZ = pytz.timezone('UTC')

def connect_mongo(mongo_uri, db_name, collection_name):
    """Connect to MongoDB and return collection and client"""
    client = MongoClient(mongo_uri)
    col = client[db_name][collection_name]
    # Create a compound index on symbol and time to prevent duplicates
    col.create_index([("symbol", 1), ("time", 1)], unique=True)
    return col, client

def generate_date_chunks(start_date, end_date, chunk_days):
    """Generate date chunks of specified days between start and end dates"""
    current_date = start_date
    while current_date < end_date:
        chunk_end = current_date + datetime.timedelta(days=chunk_days)
        # Ensure we don't go beyond the end date
        if chunk_end > end_date:
            chunk_end = end_date
        
        yield (current_date, chunk_end)
        current_date = chunk_end

def get_timeframe_minutes(timeframe):
    """Get the number of minutes for a given timeframe"""
    if timeframe == mt5.TIMEFRAME_M1:
        return 1
    elif timeframe == mt5.TIMEFRAME_M5:
        return 5
    elif timeframe == mt5.TIMEFRAME_M15:
        return 15
    elif timeframe == mt5.TIMEFRAME_M30:
        return 30
    elif timeframe == mt5.TIMEFRAME_H1:
        return 60
    elif timeframe == mt5.TIMEFRAME_H4:
        return 240
    elif timeframe == mt5.TIMEFRAME_D1:
        return 1440
    return 1  # Default to 1 minute

def fetch_candles(symbol, timeframe, from_date, to_date):
    """Fetch candles for a specific time period using copy_rates_from with chunks"""
    all_candles = []
    current_date = from_date
    max_bars_per_request = 1000
    timeframe_minutes = get_timeframe_minutes(timeframe)
    
    while current_date < to_date:
        # Log the current fetch attempt
        logging.info(f"Fetching {max_bars_per_request} {symbol} bars from {current_date.isoformat()}")
        
        # Fetch candles using copy_rates_from with limited count
        candles = mt5.copy_rates_from(symbol, timeframe, current_date, max_bars_per_request)
        
        if candles is None:
            error_code = mt5.last_error()
            logging.error(f"Failed to fetch candles: Error code {error_code}")
            break
            
        if len(candles) == 0:
            logging.warning(f"No data returned for {current_date.isoformat()}")
            break
            
        logging.info(f"Successfully fetched {len(candles)} candles")
        
        # Filter out candles beyond the end date
        valid_candles = [c for c in candles if datetime.datetime.fromtimestamp(c['time'], tz=UTC_TZ) <= to_date]
        
        if valid_candles:
            all_candles.extend(valid_candles)
            
            # Get the last timestamp and add one timeframe unit to avoid duplicates
            last_candle_time = valid_candles[-1]['time']
            last_datetime = datetime.datetime.fromtimestamp(last_candle_time, tz=UTC_TZ)
            
            # Update current_date to the next timeframe unit after the last candle
            current_date = last_datetime + datetime.timedelta(minutes=timeframe_minutes)
            
            logging.info(f"Added {len(valid_candles)} candles, last time: {last_datetime.isoformat()}")
            logging.info(f"Next fetch will start from: {current_date.isoformat()}")
            
            # Debug info for the first few and last few candles
            if len(valid_candles) > 0:
                first_time = datetime.datetime.fromtimestamp(valid_candles[0]['time'], tz=UTC_TZ)
                last_time = datetime.datetime.fromtimestamp(valid_candles[-1]['time'], tz=UTC_TZ)
                logging.debug(f"First candle time: {first_time.isoformat()}, Last candle time: {last_time.isoformat()}")
        else:
            # If we filtered out all candles (all are beyond to_date), we're done
            logging.info("All fetched candles are beyond the end date, stopping")
            break
            
        # If we got fewer than max_bars_per_request, there's no more data to fetch
        if len(candles) < max_bars_per_request:
            logging.info(f"Received fewer candles ({len(candles)}) than requested ({max_bars_per_request}), stopping")
            break
            
        # Add a small delay to avoid overwhelming the MT5 API
        time.sleep(0.1)
    
    logging.info(f"Total candles fetched: {len(all_candles)}")
    return all_candles

def store_candles_mongodb(collection, symbol, candles, timeframe_value):
    """Store candles in MongoDB"""
    inserted_count = 0
    for candle in candles:
        # Convert record to native Python types
        doc = {name: candle[name].item() for name in candles.dtype.names}
        # Add additional fields
        ts = doc.get('time')
        dt_utc = datetime.datetime.fromtimestamp(ts, tz=UTC_TZ)
        
        doc.update({
            "symbol": symbol,
            "timeframe": timeframe_value,
            "timestamp": ts,
            "datetime_utc": dt_utc.isoformat()
        })
        
        try:
            collection.insert_one(doc)
            inserted_count += 1
        except errors.DuplicateKeyError:
            # Skip duplicates
            pass
    
    return inserted_count

def write_candles_csv(csv_path, symbol, candles, first_write=False):
    """Write candles to CSV file"""
    mode = 'w' if first_write else 'a'
    write_header = first_write
    
    with open(csv_path, mode, newline='') as f:
        fieldnames = ['symbol', 'time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume', 'datetime_utc']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if write_header:
            writer.writeheader()
        
        for candle in candles:
            # Convert numpy types to Python types
            row = {name: candle[name].item() for name in candles.dtype.names}
            # Add datetime field
            ts = row.get('time')
            dt_utc = datetime.datetime.fromtimestamp(ts, tz=UTC_TZ)
            row.update({
                "symbol": symbol,
                "datetime_utc": dt_utc.isoformat()
            })
            writer.writerow(row)

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
    
    args = parse_args()
    
    # Convert timeframe string to MT5 constant
    timeframe_str = args.timeframe
    timeframe = TIMEFRAME_MAP[timeframe_str]
    
    # Parse dates and ensure they are in UTC timezone
    try:
        # Create datetime objects with UTC timezone
        start_date = datetime.datetime.strptime(args.start_date, "%Y-%m-%d")
        start_date = start_date.replace(tzinfo=UTC_TZ)
        
        end_date = datetime.datetime.strptime(args.end_date, "%Y-%m-%d")
        # Ensure end_date is set to end of day
        end_date = end_date.replace(hour=23, minute=59, second=59, tzinfo=UTC_TZ)
        
        if start_date >= end_date:
            logging.critical("Start date must be before end date")
            sys.exit(1)
    except ValueError as e:
        logging.critical(f"Invalid date format. Use YYYY-MM-DD: {e}")
        sys.exit(1)
    
    # Check MT5 executable path exists if provided
    if args.mt5_path:
        mt5_path = os.path.normpath(args.mt5_path)
        if not os.path.exists(mt5_path):
            logging.critical(f"MT5 executable not found at: {mt5_path}")
            sys.exit(1)
    
    # Database settings
    db_name = "mt5_historical_data"
    collection_name = f"candles_{args.symbol}_{timeframe_str}"
    
    # Initialize MT5 connection with login credentials if provided
    init_params = {}
    if args.mt5_path:
        init_params['path'] = args.mt5_path
    if args.account:
        init_params['login'] = args.account
    if args.password:
        init_params['password'] = args.password
    if args.server:
        init_params['server'] = args.server
    
    logging.info("Initializing MT5 connection...")
    if not mt5.initialize():
        error = mt5.last_error()
        logging.critical(f"MT5 initialize() failed: {error}")
        sys.exit(1)
    
    # Display connection info
    logging.info(f"MT5 Package Version: {mt5.__version__}")
    logging.info(f"Terminal Info: {mt5.terminal_info()}")
    logging.info(f"MT5 Version: {mt5.version()}")
    
    # Log connection details if provided
    if args.account and args.server:
        logging.info(f"Connected to MT5: account={args.account}, server={args.server}")
    else:
        logging.info("Connected to MT5 using default settings")
    
    logging.info(f"Fetching {timeframe_str} candles for {args.symbol} from {args.start_date} to {args.end_date}")

    # Connect to MongoDB
    col, client = connect_mongo(args.mongo_uri, db_name, collection_name)
    logging.info(f"Connected to MongoDB: {args.mongo_uri}, collection={collection_name}")
    
    # Setup CSV output if requested
    csv_path = None
    if args.csv_output:
        csv_path = Path(args.csv_output)
        csv_dir = csv_path.parent
        if not csv_dir.exists():
            csv_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"CSV output will be written to: {csv_path}")
    
    # Process date chunks
    total_inserted = 0
    first_csv_write = True
    
    try:
        for chunk_start, chunk_end in generate_date_chunks(start_date, end_date, args.chunk_days):
            logging.info(f"Processing chunk: {chunk_start.date()} to {chunk_end.date()}")
            
            # Fetch candles for this chunk
            candles = fetch_candles(args.symbol, timeframe, chunk_start, chunk_end)
            
            # Check if we have enough data
            if len(candles) < args.min_data_points:
                logging.warning(f"Insufficient data points ({len(candles)}) for this chunk, skipping")
                continue
            
            # Store in MongoDB
            inserted = store_candles_mongodb(col, args.symbol, candles, timeframe)
            logging.info(f"Inserted {inserted}/{len(candles)} candles into MongoDB")
            total_inserted += inserted
            
            # Write to CSV if requested
            if csv_path:
                write_candles_csv(csv_path, args.symbol, candles, first_csv_write)
                first_csv_write = False
                logging.info(f"Appended {len(candles)} candles to CSV file")
            
            # Add a short delay to avoid overwhelming the MT5 API
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
    except Exception as e:
        logging.error(f"Error during processing: {e}")
    finally:
        mt5.shutdown()
        client.close()
        logging.info(f"Process completed. Total candles inserted: {total_inserted}")


if __name__ == "__main__":
    main() 