$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    & $python.Source -3 --version *> $null
    if ($LASTEXITCODE -ne 0) {
        $python = $null
    }
}

if ($python) {
    $pythonArguments = @("-3", (Join-Path $PSScriptRoot "web_app.py"), "--host", "127.0.0.1", "--port", "8000")
} else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source --version *> $null
        if ($LASTEXITCODE -ne 0) {
            $python = $null
        }
    }
    if (-not $python) {
        Write-Error "Python tidak ditemukan. Pasang Python 3 dan aktifkan opsi Add Python to PATH."
        exit 1
    }
    $pythonArguments = @((Join-Path $PSScriptRoot "web_app.py"), "--host", "127.0.0.1", "--port", "8000")
}

$secureKeyBuffer = [IntPtr]::Zero
if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)) {
    $secureKey = Read-Host "Masukkan API key OpenAI (input tidak ditampilkan)" -AsSecureString
    if ($secureKey.Length -eq 0) {
        Write-Error "API key kosong. Server tidak dijalankan."
        exit 1
    }

    $secureKeyBuffer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
    $env:OPENAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($secureKeyBuffer)
}

Write-Host "Stars web berjalan di http://127.0.0.1:8000/"
Write-Host "Biarkan jendela ini terbuka selama menggunakan Stars."
try {
    & $python.Source @pythonArguments
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
} finally {
    $env:OPENAI_API_KEY = $null
    if ($secureKeyBuffer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($secureKeyBuffer)
    }
}
