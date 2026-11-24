param(
    [string]$Village = ".\data\34855_vadnerbhairav_chandavad_nashik"
)

$python = "..\.venv-validate\Scripts\python.exe"
$output = ".\data\vadnerbhairav\independent_predictions.geojson"
$model = ".\data\vadnerbhairav\ml_confidence_model.joblib"

& $python .\main.py $Village --output $output --model-output $model
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python .\evaluate.py $Village $output
