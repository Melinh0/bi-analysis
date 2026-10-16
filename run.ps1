<# 
.SYNOPSIS
    Runs BI Analysis full stack using Node.js runner (recommended)
    
.DESCRIPTION
    Wrapper that calls the Node.js runner script which properly handles
    concurrent logging from both backend and frontend.
#>

param(
    [ValidateSet('development', 'production')]
    [string]$Mode = 'development',
    
    [switch]$BackendOnly,
    
    [switch]$FrontendOnly
)

$nodeArgs = @()
if ($Mode -eq 'production') { $nodeArgs += '--production' }
if ($BackendOnly) { $nodeArgs += '--backend-only' }
if ($FrontendOnly) { $nodeArgs += '--frontend-only' }

node run.js @nodeArgs