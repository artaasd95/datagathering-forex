# Example PowerShell script for historical data fetcher

# MetaTrader 5 connection settings
# Update these values with your actual MetaTrader 5 credentials
$MetaTraderPath = "C:\Program Files\MetaTrader 5\terminal64.exe"
$Account = "12345678"
$Password = "your-password"
$Server = "your-broker-server"

# MongoDB settings
$MongoURI = "mongodb://localhost:27017/"

# Example 1: Fetch EURUSD H1 data for the year 2022
Write-Host "Example 1: Fetching EURUSD H1 data for 2022" -ForegroundColor Green
python historical_data_fetcher.py `
    --mt5_path "$MetaTraderPath" `
    --account $Account `
    --password $Password `
    --server $Server `
    --symbol "EURUSD" `
    --timeframe "H1" `
    --start_date "2022-01-01" `
    --end_date "2022-12-31" `
    --mongo_uri $MongoURI `
    --csv_output ".\data\EURUSD_H1_2022.csv" `
    --chunk_days 2

# Example 2: Fetch GBPUSD M15 data for Q1 2023 with custom chunk size
Write-Host "Example 2: Fetching GBPUSD M15 data for Q1 2023" -ForegroundColor Green
python historical_data_fetcher.py `
    --mt5_path "$MetaTraderPath" `
    --account $Account `
    --password $Password `
    --server $Server `
    --symbol "GBPUSD" `
    --timeframe "M15" `
    --start_date "2023-01-01" `
    --end_date "2023-03-31" `
    --mongo_uri $MongoURI `
    --csv_output ".\data\GBPUSD_M15_Q1_2023.csv" `
    --chunk_days 3 `
    --min_data_points 20

# Example 3: Fetch USDJPY D1 data for a long period (2 years)
Write-Host "Example 3: Fetching USDJPY D1 data for 2 years" -ForegroundColor Green
python historical_data_fetcher.py `
    --mt5_path "$MetaTraderPath" `
    --account $Account `
    --password $Password `
    --server $Server `
    --symbol "USDJPY" `
    --timeframe "D1" `
    --start_date "2021-01-01" `
    --end_date "2022-12-31" `
    --mongo_uri $MongoURI `
    --csv_output ".\data\USDJPY_D1_2021_2022.csv" `
    --chunk_days 5

Write-Host "All examples completed!" -ForegroundColor Green 