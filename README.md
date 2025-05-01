# MT5 Data Fetcher

This package contains scripts for fetching market data (candles and ticks) from MetaTrader 5 and storing them in MongoDB.

## Prerequisites

1. MetaTrader 5 installed
2. Python 3.6+ with the following packages:
   - `pytz`
   - `MetaTrader5`
   - `pandas_market_calendars`
   - `pymongo`
3. MongoDB instance running (default: localhost:27017)
4. PowerShell (Windows)

## Files

- `candle_fetcher.py` - Fetches candle data for a specific symbol and timeframe
- `tick_fetcher.py` - Fetches tick data for a specific symbol
- `run_candle_fetcher.ps1` - PowerShell script to run candle fetcher
- `run_tick_fetcher.ps1` - PowerShell script to run tick fetcher
- `run_all_fetchers.ps1` - PowerShell script to run all fetcher scripts
- `example_candle_fetcher.ps1` - Example script with predefined parameters for candle fetcher
- `example_tick_fetcher.ps1` - Example script with predefined parameters for tick fetcher

## Usage

### Setting Up

1. Edit the example scripts (`example_candle_fetcher.ps1` and `example_tick_fetcher.ps1`) with your actual MetaTrader 5 account details:
   - Path to MT5 executable
   - Account number
   - Password
   - Server
   - Symbol to fetch
   - Other parameters as needed

### Running Individual Fetchers

For candle data:

```powershell
.\run_candle_fetcher.ps1 -Timeframe "M5" -MT5Path "C:\path\to\terminal64.exe" -Account 12345678 -Password "your_password" -Server "Your-Broker-Server" -Symbol "EURUSD"
```

Optional parameters:
- `-MongoURI` - MongoDB connection URI (default: "mongodb://localhost:27017/")
- `-FetchInterval` - Seconds between fetches (default: 60)
- `-CandlesPerFetch` - Number of candles per fetch (default: 1)

For tick data:

```powershell
.\run_tick_fetcher.ps1 -MT5Path "C:\path\to\terminal64.exe" -Account 12345678 -Password "your_password" -Server "Your-Broker-Server" -Symbol "EURUSD"
```

Optional parameters:
- `-MongoURI` - MongoDB connection URI (default: "mongodb://localhost:27017/")
- `-FetchInterval` - Seconds between fetches (default: 1)
- `-HistoryBatch` - Number of ticks per batch when fetching history (default: 500)

### Running Both Fetchers

For convenience, you can use the provided example scripts with predefined parameters:

```powershell
.\example_candle_fetcher.ps1
.\example_tick_fetcher.ps1
```

Or to run all fetcher scripts (will open multiple PowerShell windows):

```powershell
.\run_all_fetchers.ps1
```

## Data Storage

The data is stored in MongoDB with the following collection names:
- Candle data: `candles_{symbol}_{timeframe}` (e.g., `candles_EURUSD_M5`)
- Tick data: `ticks_{symbol}` (e.g., `ticks_EURUSD`)

## Notes

- The scripts check if the market is open before fetching data
- Each script runs continuously until interrupted (Ctrl+C)
- Duplicate data points are automatically filtered out 