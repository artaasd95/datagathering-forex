# Example script for running tick_fetcher.py with sample parameters
# Replace the values below with your actual MT5 account details and settings

# MT5 installation path (usually in Program Files)
$MT5Path = "C:\Program Files\MetaTrader 5\terminal64.exe"

# MT5 account credentials
$Account = 12345678  # Your MT5 account number
$Password = "your_password"  # Your MT5 password
$Server = "Your-Broker-Server"  # Your MT5 server name

# Trading parameters
$Symbol = "EURUSD"  # The symbol/asset to fetch

# MongoDB settings
$MongoURI = "mongodb://localhost:27017/"

# Fetching settings
$FetchInterval = 1  # Seconds between fetches
$HistoryBatch = 500  # Number of ticks per batch when fetching history

# Run the tick fetcher script with the above parameters
& .\run_tick_fetcher.ps1 -MT5Path $MT5Path -Account $Account -Password $Password -Server $Server -Symbol $Symbol -MongoURI $MongoURI -FetchInterval $FetchInterval -HistoryBatch $HistoryBatch 