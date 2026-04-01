[CmdletBinding()]
param(
    [string]$Python = "python",
    [string]$VenvPath = ".venv"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Get-VenvPythonPath {
    param([string]$Path)

    $windowsPython = Join-Path $Path "Scripts/python.exe"
    if (Test-Path $windowsPython) {
        return $windowsPython
    }

    $unixPython = Join-Path $Path "bin/python"
    if (Test-Path $unixPython) {
        return $unixPython
    }

    throw "Unable to find virtual environment Python executable under '$Path'."
}

if (-not (Test-Path $VenvPath)) {
    Write-Host "Creating virtual environment in '$VenvPath'..."
    & $Python -m venv $VenvPath
}
else {
    Write-Host "Using existing virtual environment in '$VenvPath'..."
}

$venvPython = Get-VenvPythonPath -Path $VenvPath

Write-Host "Installing development dependencies..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -e '.[dev]'

if (Test-Path .git) {
    Write-Host "Installing pre-commit hooks..."
    & $venvPython -m pre_commit install
}
else {
    Write-Host "Skipping pre-commit hook installation (no .git folder found)."
}

Write-Host ""
Write-Host "Development environment is ready."

$activatePs1 = Join-Path $VenvPath "Scripts/Activate.ps1"
$activateSh = Join-Path $VenvPath "bin/activate"

if (Test-Path $activatePs1) {
    Write-Host "Activate with: .\$VenvPath\Scripts\Activate.ps1"
}
elseif (Test-Path $activateSh) {
    Write-Host "Activate with: source $VenvPath/bin/activate"
}
