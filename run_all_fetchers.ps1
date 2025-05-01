# PowerShell script to run all available fetcher scripts

# Find all PowerShell scripts that start with "run_" and end with "_fetcher.ps1"
$fetcherScripts = Get-ChildItem -Path . -Filter "run_*_fetcher.ps1" -File | Where-Object { $_.Name -ne "run_all_fetchers.ps1" }

# No fetcher scripts found
if ($fetcherScripts.Count -eq 0) {
    Write-Host "No fetcher scripts found. Make sure you have scripts named like 'run_*_fetcher.ps1' in the current directory."
    exit 1
}

# List found fetcher scripts
Write-Host "Found $($fetcherScripts.Count) fetcher scripts:"
foreach ($script in $fetcherScripts) {
    Write-Host "  - $($script.Name)"
}

# Start each fetcher script in a new PowerShell window
foreach ($script in $fetcherScripts) {
    $scriptPath = $script.FullName
    $scriptName = $script.Name
    
    Write-Host "Starting $scriptName in a new window..."
    
    # Start a new PowerShell process for each script
    # -NoExit keeps the window open after the script finishes or errors out
    Start-Process powershell.exe -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$scriptPath`"" -WindowStyle Normal
}

Write-Host "All fetcher scripts have been started in separate windows."
Write-Host "Note: You need to provide the required parameters in each window that opens." 