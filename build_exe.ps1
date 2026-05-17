param(
  [string]$HostName = "ssh-chat-host",
  [string]$UiName = "ssh-chat-ui"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path ".venv")) {
  python -m venv .venv
}

$Py = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (!(Test-Path $Py)) {
  throw "Não encontrei $Py. Recrie a venv ou reinstale Python."
}

function Invoke-Checked {
  param(
    [Parameter(Mandatory=$true)][string]$Exe,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$Args
  )
  & $Exe @Args
  if ($LASTEXITCODE -ne 0) {
    throw "Falhou: $Exe $($Args -join ' ') (exit=$LASTEXITCODE)"
  }
}

Invoke-Checked $Py -m pip install --upgrade pip
Invoke-Checked $Py -m pip install -r .\requirements.txt
Invoke-Checked $Py -m pip install pyinstaller

# Host: com consola (para ver logs e parar com Ctrl+C)
Invoke-Checked $Py -m PyInstaller --noconfirm --clean --onefile --console --name $HostName .\entry_host.py

# UI: sem consola
Invoke-Checked $Py -m PyInstaller --noconfirm --clean --onefile --windowed --name $UiName .\entry_ui.py

Write-Host ""
Write-Host "Gerados em:"
Write-Host "  .\\dist\\$HostName.exe"
Write-Host "  .\\dist\\$UiName.exe"
