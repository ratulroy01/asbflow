[CmdletBinding()]
param(
    [string]$Python = "python",
    [string]$VenvPath = ".venv"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Resolve-PythonPath {
    param(
        [string]$Path,
        [string]$FallbackPython
    )

    $windowsPython = Join-Path $Path "Scripts/python.exe"
    if (Test-Path $windowsPython) {
        return $windowsPython
    }

    $unixPython = Join-Path $Path "bin/python"
    if (Test-Path $unixPython) {
        return $unixPython
    }

    return $FallbackPython
}

$pythonExe = Resolve-PythonPath -Path $VenvPath -FallbackPython $Python

Write-Host "Using Python executable: $pythonExe"
Write-Host "Running local checks..."

& $pythonExe -m pytest -q test/unit
& $pythonExe -m black --check src test
& $pythonExe -m isort --check-only src test

Write-Host ""
Write-Host "All local checks passed."
