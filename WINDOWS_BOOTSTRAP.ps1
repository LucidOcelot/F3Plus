$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$Log = Join-Path $Root 'F3Plus_startup.log'
$Runtime = Join-Path $Root '.runtime'
$ManagedPythonDir = Join-Path $Runtime 'python'
$UvDir = Join-Path $Runtime 'uv'
$UvExe = Join-Path $UvDir 'uv.exe'
$MinMajor = 3
$MinMinor = 11
$UvVersion = '0.12.0'

function Write-Status([string]$Text = '') {
    Write-Host $Text
    try { Add-Content -LiteralPath $Log -Value $Text -Encoding UTF8 } catch {}
}

function Reset-Log {
    @(
        'F3+ 1.16.2 startup log',
        ('Started: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),
        ('Folder: ' + $Root),
        ''
    ) | Set-Content -LiteralPath $Log -Encoding UTF8
}

function Add-Candidate([System.Collections.Generic.List[string]]$List, [string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    $Path = $Path.Trim().Trim('"')
    if ($Path -and -not $List.Contains($Path)) { [void]$List.Add($Path) }
}

function Test-PythonExecutable([string]$Exe) {
    if ([string]::IsNullOrWhiteSpace($Exe)) { return $null }
    $Exe = $Exe.Trim().Trim('"')

    # A rooted path must exist. Command names (e.g. python.exe) may be resolved by Windows.
    if ([System.IO.Path]::IsPathRooted($Exe) -and -not (Test-Path -LiteralPath $Exe -PathType Leaf)) { return $null }

    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $Exe
        $psi.Arguments = '-c "import sys; print(sys.version.split()[0]); print(sys.executable); raise SystemExit(0 if sys.version_info >= (3,11) else 7)"'
        $psi.WorkingDirectory = $Root
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true
        $proc = New-Object System.Diagnostics.Process
        $proc.StartInfo = $psi
        if (-not $proc.Start()) { return $null }
        if (-not $proc.WaitForExit(10000)) {
            try { $proc.Kill() } catch {}
            return $null
        }
        $stdout = $proc.StandardOutput.ReadToEnd().Trim() -split "`r?`n"
        if ($proc.ExitCode -ne 0 -or $stdout.Count -lt 2) { return $null }
        return [pscustomobject]@{
            Exe = [string]$stdout[1].Trim()
            Version = [string]$stdout[0].Trim()
        }
    } catch {
        return $null
    }
}

function Get-RegistryPythonCandidates {
    $out = New-Object 'System.Collections.Generic.List[string]'
    $roots = @(
        'Registry::HKEY_CURRENT_USER\Software\Python\PythonCore',
        'Registry::HKEY_LOCAL_MACHINE\Software\Python\PythonCore',
        'Registry::HKEY_LOCAL_MACHINE\Software\WOW6432Node\Python\PythonCore'
    )
    foreach ($root in $roots) {
        if (-not (Test-Path $root)) { continue }
        foreach ($verKey in @(Get-ChildItem $root -ErrorAction SilentlyContinue)) {
            $installKeyPath = Join-Path $verKey.PSPath 'InstallPath'
            if (-not (Test-Path $installKeyPath)) { continue }
            try {
                $installKey = Get-Item $installKeyPath
                $exe = [string]$installKey.GetValue('ExecutablePath', '')
                $dir = [string]$installKey.GetValue('', '')
                if ($exe) { Add-Candidate $out $exe }
                if ($dir) { Add-Candidate $out (Join-Path $dir 'python.exe') }
            } catch {}
        }
    }
    return $out
}

function Get-UninstallPythonCandidates {
    $out = New-Object 'System.Collections.Generic.List[string]'
    $roots = @(
        'Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall',
        'Registry::HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Uninstall',
        'Registry::HKEY_LOCAL_MACHINE\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
    )
    foreach ($root in $roots) {
        if (-not (Test-Path $root)) { continue }
        foreach ($key in @(Get-ChildItem $root -ErrorAction SilentlyContinue)) {
            try {
                $item = Get-ItemProperty $key.PSPath -ErrorAction Stop
                $name = [string]$item.DisplayName
                if ($name -notmatch '^Python 3\.') { continue }
                $loc = [string]$item.InstallLocation
                if ($loc) { Add-Candidate $out (Join-Path $loc 'python.exe') }
                $icon = [string]$item.DisplayIcon
                if ($icon) {
                    $icon = ($icon -split ',')[0].Trim('"')
                    if ($icon -match 'python(?:w)?\.exe$') {
                        $icon = $icon -replace 'pythonw\.exe$', 'python.exe'
                        Add-Candidate $out $icon
                    }
                }
            } catch {}
        }
    }
    return $out
}

function Get-AppPathPythonCandidates {
    $out = New-Object 'System.Collections.Generic.List[string]'
    foreach ($root in @(
        'Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\App Paths\python.exe',
        'Registry::HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\App Paths\python.exe'
    )) {
        if (-not (Test-Path $root)) { continue }
        try {
            $item = Get-Item $root
            Add-Candidate $out ([string]$item.GetValue('', ''))
        } catch {}
    }
    return $out
}

function Find-Python {
    $candidates = New-Object 'System.Collections.Generic.List[string]'

    # 1. F3+-managed Python installations, regardless of uv's internal folder name.
    if (Test-Path -LiteralPath $ManagedPythonDir) {
        try {
            foreach ($exe in @(Get-ChildItem -LiteralPath $ManagedPythonDir -Filter 'python.exe' -File -Recurse -ErrorAction SilentlyContinue)) {
                Add-Candidate $candidates $exe.FullName
            }
        } catch {}
    }

    # 2. Windows Python launcher environments.
    try {
        if (Get-Command py.exe -ErrorAction SilentlyContinue) {
            foreach ($line in @(& py.exe -0p 2>$null)) {
                if ($line -match '([A-Za-z]:\\.+?python(?:w)?\.exe)\s*$') {
                    $p = $Matches[1] -replace 'pythonw\.exe$', 'python.exe'
                    Add-Candidate $candidates $p
                }
            }
        }
    } catch {}

    # 3. PATH / command discovery. Do not reject WindowsApps automatically: a Store
    #    alias is valid when an actual Store Python package is installed and runnable.
    foreach ($name in @('python.exe','python3.exe')) {
        try {
            foreach ($cmd in @(Get-Command $name -All -ErrorAction SilentlyContinue)) {
                if ($cmd.Source) { Add-Candidate $candidates $cmd.Source }
                elseif ($cmd.Path) { Add-Candidate $candidates $cmd.Path }
            }
        } catch {}
        try { foreach ($p in @(& where.exe $name 2>$null)) { Add-Candidate $candidates $p } } catch {}
    }

    # 4. Python.org registration, App Paths, and installer/uninstall metadata.
    foreach ($p in @(Get-RegistryPythonCandidates)) { Add-Candidate $candidates $p }
    foreach ($p in @(Get-AppPathPythonCandidates)) { Add-Candidate $candidates $p }
    foreach ($p in @(Get-UninstallPythonCandidates)) { Add-Candidate $candidates $p }

    # 5. Common install folders. Scan recursively because Python's patch/install layout
    #    differs across installer, Store, package manager, and per-user installs.
    foreach ($base in @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python'),
        (Join-Path $env:LOCALAPPDATA 'Python'),
        (Join-Path $env:APPDATA 'Python'),
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)}
    )) {
        if (-not $base -or -not (Test-Path -LiteralPath $base)) { continue }
        try {
            foreach ($exe in @(Get-ChildItem -LiteralPath $base -Filter 'python.exe' -File -Recurse -Depth 4 -ErrorAction SilentlyContinue)) {
                Add-Candidate $candidates $exe.FullName
            }
        } catch {}
    }

    # 6. Microsoft Store alias only when an actual Python Store package is installed.
    try {
        $storePython = @(Get-AppxPackage -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'PythonSoftwareFoundation\.Python' })
        if ($storePython.Count -gt 0) {
            Add-Candidate $candidates (Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\python.exe')
            Add-Candidate $candidates (Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\python3.exe')
        }
    } catch {}

    foreach ($candidate in $candidates) {
        $found = Test-PythonExecutable $candidate
        if ($null -ne $found) { return $found }
    }
    return $null
}

function Ensure-Uv {
    if (Test-Path -LiteralPath $UvExe -PathType Leaf) { return $UvExe }
    New-Item -ItemType Directory -Force -Path $UvDir | Out-Null
    Write-Status ''
    Write-Status 'No usable Python 3.11+ installation was found.'
    Write-Status 'F3+ will prepare a private managed Python runtime.'
    Write-Status 'No administrator rights are required and Windows PATH will not be changed.'

    $arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
    if ($arch -eq 'X64') {
        $asset = 'uv-x86_64-pc-windows-msvc.zip'
        $expected = '68200e25de594df92387186bbfb9d9df606ec1d87efaa0ae0c7f690970e53db6'
    } elseif ($arch -eq 'Arm64') {
        $asset = 'uv-aarch64-pc-windows-msvc.zip'
        $expected = '60c12dc34a8ff0269d7744a3a94506fa8f140618a82194b7bf7834fa789a765b'
    } else {
        throw ('Automatic runtime bootstrap is not available for Windows architecture ' + $arch + '.')
    }

    $url = 'https://releases.astral.sh/github/uv/releases/download/' + $UvVersion + '/' + $asset
    $archive = Join-Path $Runtime $asset
    Write-Status ('Downloading verified project-local runtime bootstrap (uv ' + $UvVersion + ')...')
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $archive
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant()
    if ($actual -ne $expected) {
        Remove-Item -LiteralPath $archive -Force -ErrorAction SilentlyContinue
        throw ('uv download failed SHA-256 verification. Expected ' + $expected + ', got ' + $actual + '.')
    }
    Write-Status 'Runtime bootstrap download verified.'
    try {
        Expand-Archive -LiteralPath $archive -DestinationPath $UvDir -Force
    } finally {
        Remove-Item -LiteralPath $archive -Force -ErrorAction SilentlyContinue
    }
    $foundUv = Get-ChildItem -LiteralPath $UvDir -Filter 'uv.exe' -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $foundUv) { throw 'The verified uv archive did not contain uv.exe.' }
    if ($foundUv.FullName -ne $UvExe) { Copy-Item -LiteralPath $foundUv.FullName -Destination $UvExe -Force }
    return $UvExe
}

function Install-ManagedPython {
    $uv = Ensure-Uv
    New-Item -ItemType Directory -Force -Path $ManagedPythonDir | Out-Null
    $oldPythonDir = $env:UV_PYTHON_INSTALL_DIR
    $oldNoModify = $env:UV_NO_MODIFY_PATH
    try {
        $env:UV_PYTHON_INSTALL_DIR = $ManagedPythonDir
        $env:UV_NO_MODIFY_PATH = '1'
        Write-Status 'Downloading a private Python 3.13 runtime...'
        & $uv python install 3.13 --install-dir $ManagedPythonDir --no-config
        if ($LASTEXITCODE -ne 0) { throw "uv could not install Python (exit code $LASTEXITCODE)." }

        $path = (& $uv python find 3.13 --managed-python --no-config 2>$null | Select-Object -First 1)
        if ($path) {
            $found = Test-PythonExecutable ([string]$path)
            if ($null -ne $found) { return $found }
        }
    } finally {
        $env:UV_PYTHON_INSTALL_DIR = $oldPythonDir
        $env:UV_NO_MODIFY_PATH = $oldNoModify
    }

    $rescanned = Find-Python
    if ($null -ne $rescanned) { return $rescanned }
    throw 'Private Python was downloaded, but F3+ could not locate a runnable interpreter afterward.'
}

try {
    Reset-Log
    Write-Host 'F3+ 1.16.2 - LucidOcelot'
    Write-Host '===================================' 
    Write-Host ''
    Write-Status 'Checking installation...'

    foreach ($required in @('launcher.py','main.py','requirements.txt','minescript\app.py')) {
        if (-not (Test-Path (Join-Path $Root $required))) {
            throw 'F3+ is not fully extracted. Extract the complete ZIP first, then run START_F3PLUS.bat from the extracted F3+ folder.'
        }
    }

    $python = Find-Python
    if ($null -eq $python) { $python = Install-ManagedPython }

    Write-Status ('Found Python ' + $python.Version)
    Write-Status ('Interpreter: ' + $python.Exe)
    Write-Status ''
    Write-Status 'Starting F3+ setup and launch...'
    Write-Status 'The first launch may install interface/input packages and can take several minutes.'
    Write-Status 'This window will remain open and show progress.'
    Write-Status ''

    & $python.Exe (Join-Path $Root 'launcher.py')
    $rc = $LASTEXITCODE
    if ($rc -ne 0) { throw "F3+ startup returned exit code $rc. See the messages above and F3Plus_startup.log." }

    Write-Status ''
    Write-Status 'F3+ closed normally.'
    Start-Sleep -Seconds 1
    exit 0
} catch {
    Write-Status ''
    Write-Status 'ERROR: F3+ could not finish starting.'
    Write-Status $_.Exception.Message
    Write-Status ('Startup log: ' + $Log)
    Write-Host ''
    Write-Host 'Press Enter to open the startup log in Notepad.'
    [void](Read-Host)
    try { Start-Process notepad.exe -ArgumentList ('"' + $Log + '"') } catch {}
    exit 1
}
