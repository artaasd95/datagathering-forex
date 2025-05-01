# PowerShell script to run tick_fetcher.py
param (
    [Parameter(Mandatory=$true)]
    [string]$MT5Path,
    
    [Parameter(Mandatory=$true)]
    [int]$Account,
    
    [Parameter(Mandatory=$true)]
    [string]$Password,
    
    [Parameter(Mandatory=$true)]
    [string]$Server,
    
    [Parameter(Mandatory=$true)]
    [string]$Symbol,
    
    [string]$MongoURI = "mongodb://localhost:27017/",
    
    [int]$FetchInterval = 1,
    
    [int]$HistoryBatch = 500
)

# Construct the command
$pythonCommand = "python tick_fetcher.py --mt5_path=`"$MT5Path`" --account=$Account --password=`"$Password`" --server=`"$Server`" --symbol=`"$Symbol`" --mongo_uri=`"$MongoURI`" --fetch_interval=$FetchInterval --history_batch=$HistoryBatch"

# Log the command (with password masked)
$logCommand = $pythonCommand -replace "--password=`"[^`"]+`"", "--password=`"********`""
Write-Host "Running: $logCommand"

# Execute the command
Invoke-Expression $pythonCommand 