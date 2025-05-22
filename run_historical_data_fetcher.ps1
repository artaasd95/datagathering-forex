# PowerShell script to run the historical data fetcher

# MetaTrader 5 connection settings
$MetaTraderPath = "C:\Program Files\MetaTrader 5\terminal64.exe"  # Update with your MT5 path
$Account = "12345678"  # Update with your account number
$Password = "your-password"  # Update with your password
$Server = "your-broker-server"  # Update with your broker server

# MongoDB settings
$MongoURI = "mongodb://localhost:27017/"

# Symbol and timeframe settings
$Symbol = "EURUSD"  # Update with the symbol you want to fetch
$Timeframe = "H1"  # Choose from: M1, M5, M15, M30, H1, H4, D1

# Date range settings
$StartDate = "2020-01-01"  # Format: YYYY-MM-DD
$EndDate = "2020-12-31"  # Format: YYYY-MM-DD

# Optional: CSV output path
$CSVOutput = ".\data\${Symbol}_${Timeframe}_${StartDate}_to_${EndDate}.csv"

# Chunk settings
$ChunkDays = 2  # Number of days per chunk
$MinDataPoints = 10  # Minimum number of data points to consider a chunk valid

# Run the historical data fetcher
python historical_data_fetcher.py `
    --mt5_path "$MetaTraderPath" `
    --account $Account `
    --password $Password `
    --server $Server `
    --symbol $Symbol `
    --timeframe $Timeframe `
    --start_date $StartDate `
    --end_date $EndDate `
    --mongo_uri $MongoURI `
    --csv_output $CSVOutput `
    --chunk_days $ChunkDays `
    --min_data_points $MinDataPoints

Write-Host "Historical data fetching complete!" 