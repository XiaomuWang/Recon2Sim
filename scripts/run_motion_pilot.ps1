param(
    [ValidateSet('024388','0508656','019742')][string]$Scene='024388',
    [ValidateSet('baseline','optimized')][string]$Mode='optimized',
    [string]$Tag='v1',
    [string]$Python='python'
)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$clientRoot=Join-Path $projectRoot 'runtime\motion_python'
if (-not (Test-Path (Join-Path $clientRoot 'carla'))) {
    throw 'Install the matching CARLA 0.9.15 wheel with: python -m pip install --no-deps --target runtime\motion_python <wheel-path>'
}
$previousPythonPath=$env:PYTHONPATH
try {
    $env:PYTHONPATH=$clientRoot
    Push-Location $projectRoot
    try {
        & $Python -m a2s.motion_pilot --scene $Scene --mode $Mode --tag $Tag
        if ($LASTEXITCODE -ne 0) { throw 'CARLA pilot failed; inspect outputs/<scene>/validation/motion_pilot/<tag>/<mode>/run.json' }
    } finally { Pop-Location }
} finally { $env:PYTHONPATH=$previousPythonPath }
