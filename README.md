# MT5 Data Fetcher

This project fetches tick and candle data from MetaTrader 5 and stores it in MongoDB.

## Docker Setup

### Prerequisites

1. Install Docker and Docker Compose
2. Install MetaTrader 5 on your host machine
3. Make sure MetaTrader 5 is running and configured with your accounts

### Running with Docker Compose

1. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

2. To stop the containers:
   ```bash
   docker-compose down
   ```

### Running Individual Containers

To run a new instance with different parameters:

1. For tick fetcher:
   ```bash
   docker run -d \
     --name tick-fetcher-new \
     --network host \
     -e MT5_PATH="F:/path/to/your/terminal64.exe" \
     -e ACCOUNT=your_account \
     -e PASSWORD=your_password \
     -e SERVER=your_server \
     -e SYMBOL=your_symbol \
     -e MONGO_URI=mongodb://localhost:27018/ \
     mt5-fetcher \
     python tick_fetcher.py \
     --mt5_path "${MT5_PATH}" \
     --account ${ACCOUNT} \
     --password ${PASSWORD} \
     --server ${SERVER} \
     --symbol ${SYMBOL} \
     --mongo_uri ${MONGO_URI}
   ```

2. For candle fetcher:
   ```bash
   docker run -d \
     --name candle-fetcher-new \
     --network host \
     -e MT5_PATH="F:/path/to/your/terminal64.exe" \
     -e ACCOUNT=your_account \
     -e PASSWORD=your_password \
     -e SERVER=your_server \
     -e SYMBOL=your_symbol \
     -e TIMEFRAME=M1 \
     -e MONGO_URI=mongodb://localhost:27018/ \
     mt5-fetcher \
     python candle_fetcher.py \
     --mt5_path "${MT5_PATH}" \
     --account ${ACCOUNT} \
     --password ${PASSWORD} \
     --server ${SERVER} \
     --symbol ${SYMBOL} \
     --timeframe ${TIMEFRAME} \
     --mongo_uri ${MONGO_URI}
   ```

## Original Python Setup

### Prerequisites

1. Python 3.9 or higher
2. MetaTrader 5 terminal installed
3. MongoDB installed and running

### Installation

1. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the tick fetcher:
   ```bash
   python tick_fetcher.py --mt5_path "path/to/terminal64.exe" --account YOUR_ACCOUNT --password YOUR_PASSWORD --server YOUR_SERVER --symbol SYMBOL --mongo_uri "mongodb://localhost:27018/"
   ```

3. Run the candle fetcher:
   ```bash
   python candle_fetcher.py --mt5_path "path/to/terminal64.exe" --account YOUR_ACCOUNT --password YOUR_PASSWORD --server YOUR_SERVER --symbol SYMBOL --timeframe TIMEFRAME --mongo_uri "mongodb://localhost:27018/"
   ```

## Historical Data Fetcher

The historical data fetcher allows you to retrieve data for a long date range by breaking it into smaller chunks (default is 2-day periods). This is useful for gathering extensive historical data when MetaTrader 5 has limitations on the amount of data it can return in a single request.

### Running the Historical Data Fetcher

```bash
python historical_data_fetcher.py --mt5_path "path/to/terminal64.exe" --account YOUR_ACCOUNT --password YOUR_PASSWORD --server YOUR_SERVER --symbol SYMBOL --timeframe TIMEFRAME --start_date "YYYY-MM-DD" --end_date "YYYY-MM-DD" --mongo_uri "mongodb://localhost:27018/" --csv_output "path/to/output.csv" --chunk_days 2 --min_data_points 10
```

### Parameters

- `--start_date`: Start date in YYYY-MM-DD format
- `--end_date`: End date in YYYY-MM-DD format
- `--csv_output`: (Optional) Path to CSV output file
- `--chunk_days`: Number of days per chunk (default: 2)
- `--min_data_points`: Minimum number of data points to consider a chunk valid (default: 10)

### Example PowerShell Scripts

The repository includes example PowerShell scripts to run the historical data fetcher:

1. `run_historical_data_fetcher.ps1`: Basic script with configurable parameters
2. `example_historical_data_fetcher.ps1`: Examples showing different configurations

## Data Storage

Data is stored in MongoDB with the following collections:
- `ticks_SYMBOL`: Raw tick data
- `candles_SYMBOL_TIMEFRAME`: Candle data for specific timeframe
- `mt5_historical_data.candles_SYMBOL_TIMEFRAME`: Historical candle data retrieved by the historical data fetcher

## Notes

- The tick and candle fetchers run continuously and store data only when the market is open
- Market hours: Opens Sunday 22:00 UTC, closes Friday 22:00 UTC
- Make sure to use different MT5 terminals for different fetchers to avoid conflicts
- The Docker containers use host networking to access the MT5 instance running on your host machine
- Ensure your MT5 terminals are running before starting the Docker containers
- The historical data fetcher creates a compound index on symbol and time to prevent duplicate entries
- For very long date ranges, the historical data fetcher breaks the request into smaller chunks to prevent MT5 API limitations 