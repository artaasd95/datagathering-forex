# Example script for running candle_fetcher.py with sample parameters
# Replace the values below with your actual MT5 account details and settings

# MT5 installation path (usually in Program Files)
$MT5Path = "C:\Program Files\MetaTrader 5\terminal64.exe"

# MT5 account credentials
$Account = 12345678  # Your MT5 account number
$Password = "your_password"  # Your MT5 password
$Server = "Your-Broker-Server"  # Your MT5 server name

# Trading parameters
$Symbol = "EURUSD"  # The symbol/asset to fetch
$Timeframe = "M5"  # Timeframe (M1, M5, M15, M30, H1, H4, D1)

# MongoDB settings
$MongoURI = "mongodb://localhost:27017/"

# Fetching settings
$FetchInterval = 60  # Seconds between fetches
$CandlesPerFetch = 1  # Candles per fetch

# Run the candle fetcher script with the above parameters
& .\run_candle_fetcher.ps1 -Timeframe $Timeframe -MT5Path $MT5Path -Account $Account -Password $Password -Server $Server -Symbol $Symbol -MongoURI $MongoURI -FetchInterval $FetchInterval -CandlesPerFetch $CandlesPerFetch 