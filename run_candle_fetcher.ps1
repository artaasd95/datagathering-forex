# PowerShell script to run candle_fetcher.py
param (
    [Parameter(Mandatory=$true)]
    [string]$Timeframe,
    
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
    
    [int]$FetchInterval = 60,
    
    [int]$CandlesPerFetch = 1
)

# Validate timeframe
$validTimeframes = @('M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1')
if ($validTimeframes -notcontains $Timeframe) {
    Write-Error "Invalid timeframe: $Timeframe. Must be one of: $($validTimeframes -join ', ')"
    exit 1
}

# Construct the command
$pythonCommand = "python candle_fetcher.py --timeframe=$Timeframe --mt5_path=`"$MT5Path`" --account=$Account --password=`"$Password`" --server=`"$Server`" --symbol=`"$Symbol`" --mongo_uri=`"$MongoURI`" --fetch_interval=$FetchInterval --candles_per_fetch=$CandlesPerFetch"

# Log the command (with password masked)
$logCommand = $pythonCommand -replace "--password=`"[^`"]+`"", "--password=`"********`""
Write-Host "Running: $logCommand"

# Execute the command
Invoke-Expression $pythonCommand 