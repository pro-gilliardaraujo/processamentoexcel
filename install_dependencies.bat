@echo off
echo ===============================================
echo Instalando dependencias do projeto de colhedoras
echo ===============================================

echo.
echo Verificando se Python esta instalado...
python --version
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado! Por favor, instale o Python primeiro.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo Atualizando pip...
python -m pip install --upgrade pip

echo.
echo Instalando dependencias principais...
python -m pip install pandas>=1.5.0
python -m pip install numpy>=1.21.0
python -m pip install openpyxl>=3.1.0

echo.
echo Instalando dependencias opcionais para visualizacao...
python -m pip install plotly>=5.13.0
python -m pip install dash>=2.8.0
python -m pip install dash-bootstrap-components>=1.3.0

echo.
echo Instalando dependencias adicionais...
python -m pip install xlrd>=2.0.0
python -m pip install xlsxwriter>=3.0.0
python -m pip install python-dateutil>=2.8.0
python -m pip install pytz>=2022.1

echo.
echo ===============================================
echo Instalacao concluida!
echo ===============================================
echo.
echo Para testar se tudo esta funcionando, execute:
echo python scripts/colhedorasMinOcioso.py
echo.
pause
