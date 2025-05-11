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

## Data Storage

Data is stored in MongoDB with the following collections:
- `ticks_SYMBOL`: Raw tick data
- `candles_SYMBOL_TIMEFRAME`: Candle data for specific timeframe

## Notes

- The fetchers run continuously and store data only when the market is open
- Market hours: Opens Sunday 22:00 UTC, closes Friday 22:00 UTC
- Make sure to use different MT5 terminals for different fetchers to avoid conflicts
- The Docker containers use host networking to access the MT5 instance running on your host machine
- Ensure your MT5 terminals are running before starting the Docker containers 