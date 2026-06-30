# ============================================================================
#  windows-setup.ps1  -  ensure Python is installed, then run convert_to_mp3.py
#  Invoked by convert-windows.bat. Do not run videos through this directly;
#  just double-click convert-windows.bat.
# ============================================================================
param([Parameter(ValueFromRemainingArguments = $true)] $Rest)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }

# The Microsoft Store ships fake python.exe/python3.exe "app execution alias"
# stubs in ...\WindowsApps\. Running them opens the Store. Detect by path so we
# skip them (without falsely rejecting a real per-user install under AppData).
function Test-IsStoreStub($exe) {
    try {
        $src = (Get-Command $exe -ErrorAction SilentlyContinue).Source
        if ($src -and $src -match '\\WindowsApps\\') { return $true }
    } catch { }
    return $false
}

# Return the working python invocation as an array (e.g. @('py','-3')) or $null.
function Get-PythonInvocation {
    $candidates = @(
        @('py', '-3'),
        @('python'),
        @('python3')
    )
    foreach ($cand in $candidates) {
        $exe = $cand[0]
        $pre = if ($cand.Length -gt 1) { $cand[1..($cand.Length - 1)] } else { @() }
        if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
        if (Test-IsStoreStub $exe) { continue }   # don't trigger the Store popup
        try {
            $out = & $exe @pre -c "import sys; print(sys.version_info[0])" 2>$null
            if ($LASTEXITCODE -eq 0 -and "$out".Trim() -eq '3') { return $cand }
        } catch { }
    }
    return $null
}

function Update-PathFromRegistry {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user    = [Environment]::GetEnvironmentVariable('Path', 'User')
    if ($machine) { $machine = $machine.TrimEnd(';') }   # avoid '...;;...'
    if ($user)    { $user    = $user.TrimEnd(';') }
    $env:Path = @($machine, $user | Where-Object { $_ }) -join ';'
}

function Install-Python {
    # 1) Try winget (present on Windows 10 1709+ / Windows 11).
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Step "Installing Python via winget (this can take a minute)..."
        try {
            winget install -e --id Python.Python.3.12 --scope user --silent `
                --accept-package-agreements --accept-source-agreements | Out-Host
            Update-PathFromRegistry
            if (Get-PythonInvocation) { return $true }
        } catch { Write-Host "winget install did not complete: $_" }
    }

    # 2) Fall back to the official installer download (per-user, no admin).
    Write-Step "Downloading the official Python installer..."
    # Windows PowerShell 5.1 defaults to TLS 1.0; python.org requires TLS 1.2.
    try {
        [Net.ServicePointManager]::SecurityProtocol = `
            [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    } catch { }
    $ver = '3.12.7'
    $arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'arm64' } else { 'amd64' }
    $url = "https://www.python.org/ftp/python/$ver/python-$ver-$arch.exe"
    $dest = Join-Path $env:TEMP "python-$ver-$arch.exe"
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
        Write-Step "Installing Python $ver (per-user)..."
        # -PassThru so we can actually read the installer's exit code.
        $proc = Start-Process -FilePath $dest -Wait -PassThru -ArgumentList @(
            '/quiet', 'InstallAllUsers=0', 'PrependPath=1',
            'Include_pip=1', 'Include_launcher=1'
        )
        if ($proc.ExitCode -ne 0) {
            Write-Host "Python installer failed (exit code $($proc.ExitCode))."
            return $false
        }
        Update-PathFromRegistry
        return [bool](Get-PythonInvocation)
    } catch {
        Write-Host "Automatic install failed: $_"
        return $false
    }
}

# ---- main ----------------------------------------------------------------
$py = Get-PythonInvocation
if (-not $py) {
    Write-Step "Python 3 was not found. Setting it up for you..."
    if (-not (Install-Python)) {
        Write-Host ""
        Write-Host "Could not install Python automatically." -ForegroundColor Yellow
        Write-Host "Please install it from https://www.python.org/downloads/"
        Write-Host "(tick 'Add python.exe to PATH'), then run this again."
        Read-Host "Press Enter to close"
        exit 1
    }
    $py = Get-PythonInvocation
    if (-not $py) {
        Write-Host ""
        Write-Host "Python was installed but still can't be found in this session." -ForegroundColor Yellow
        Write-Host "Please close this window and run convert-windows.bat again."
        Read-Host "Press Enter to close"
        exit 1
    }
}

$exe = $py[0]
$pre = if ($py.Length -gt 1) { $py[1..($py.Length - 1)] } else { @() }
Write-Step "Using Python: $exe $($pre -join ' ')"

$scriptArgs = @($pre) + @('convert_to_mp3.py', '--no-pause') + @($Rest)
& $exe @scriptArgs
$code = $LASTEXITCODE

Write-Host ""
Read-Host "Press Enter to close"
exit $code
