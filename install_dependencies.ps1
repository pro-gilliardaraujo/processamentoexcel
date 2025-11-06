# Script PowerShell para instalar dependências do projeto de colhedoras
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Instalando dependências do projeto de colhedoras" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

Write-Host ""
Write-Host "Verificando se Python está instalado..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERRO: Python não encontrado! Por favor, instale o Python primeiro." -ForegroundColor Red
    Write-Host "Download: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

Write-Host ""
Write-Host "Atualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host ""
Write-Host "Instalando dependências principais..." -ForegroundColor Yellow
python -m pip install "pandas>=1.5.0"
python -m pip install "numpy>=1.21.0"
python -m pip install "openpyxl>=3.1.0"

Write-Host ""
Write-Host "Instalando dependências opcionais para visualização..." -ForegroundColor Yellow
python -m pip install "plotly>=5.13.0"
python -m pip install "dash>=2.8.0"
python -m pip install "dash-bootstrap-components>=1.3.0"

Write-Host ""
Write-Host "Instalando dependências adicionais..." -ForegroundColor Yellow
python -m pip install "xlrd>=2.0.0"
python -m pip install "xlsxwriter>=3.0.0"
python -m pip install "python-dateutil>=2.8.0"
python -m pip install "pytz>=2022.1"

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Instalação concluída!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Para testar se tudo está funcionando, execute:" -ForegroundColor Cyan
Write-Host "python scripts/colhedorasMinOcioso.py" -ForegroundColor White
Write-Host ""
Read-Host "Pressione Enter para sair"
