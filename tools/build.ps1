param([string]$BuildDir = "build")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
cmake -S . -B $BuildDir
if ($LASTEXITCODE -ne 0) { throw "configure failed" }
cmake --build $BuildDir --config Release
if ($LASTEXITCODE -ne 0) { throw "build failed" }
ctest --test-dir $BuildDir -C Release --output-on-failure
if ($LASTEXITCODE -ne 0) { throw "tests failed" }
& (Join-Path $BuildDir "Release\open-spin-fv1.exe") --version
