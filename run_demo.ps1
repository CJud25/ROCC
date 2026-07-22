$ErrorActionPreference = 'Stop'

$ProjectRoot = $PSScriptRoot
$VenvRoot = Join-Path $ProjectRoot '.venv'
$VenvPython = Join-Path $VenvRoot 'Scripts\python.exe'

if (-not (Test-Path -LiteralPath $VenvPython)) {
    if ($env:ROCC_PYTHON) {
        $PythonCommand = Get-Command $env:ROCC_PYTHON -ErrorAction SilentlyContinue
        if ($null -eq $PythonCommand) {
            throw 'ROCC_PYTHON does not point to a usable Python interpreter.'
        }
        $BasePython = $PythonCommand.Source
    }
    else {
        $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if ($null -eq $PythonCommand) {
            throw 'Python 3.11+ was not found. Install Python 3.11+ and try again.'
        }
        $BasePython = $PythonCommand.Source
    }
    & $BasePython -m venv $VenvRoot
    & $VenvPython -m pip install --disable-pip-version-check -r (Join-Path $ProjectRoot 'requirements-dev.txt')
}

& $VenvPython -m streamlit run (Join-Path $ProjectRoot 'app.py')
