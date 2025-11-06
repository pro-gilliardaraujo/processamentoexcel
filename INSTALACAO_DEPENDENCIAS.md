# Instalação de Dependências - Projeto de Processamento de Colhedoras

## Visão Geral
Este projeto processa dados de monitoramento de colhedoras e gera planilhas Excel com métricas de performance. Para funcionar corretamente, são necessárias várias bibliotecas Python.

## Pré-requisitos
- Python 3.7 ou superior
- pip (geralmente vem com Python)

## Métodos de Instalação

### Método 1: Script Automático (Recomendado)

#### Para Windows (CMD):
```cmd
install_dependencies.bat
```

#### Para Windows (PowerShell):
```powershell
.\install_dependencies.ps1
```

### Método 2: Instalação Manual

#### 1. Verificar se Python está instalado:
```cmd
python --version
```

#### 2. Atualizar pip:
```cmd
python -m pip install --upgrade pip
```

#### 3. Instalar dependências principais:
```cmd
python -m pip install pandas>=1.5.0
python -m pip install numpy>=1.21.0
python -m pip install openpyxl>=3.1.0
```

#### 4. Instalar dependências opcionais:
```cmd
python -m pip install plotly>=5.13.0
python -m pip install dash>=2.8.0
python -m pip install dash-bootstrap-components>=1.3.0
python -m pip install xlrd>=2.0.0
python -m pip install xlsxwriter>=3.0.0
python -m pip install python-dateutil>=2.8.0
python -m pip install pytz>=2022.1
```

### Método 3: Usando requirements.txt

```cmd
python -m pip install -r requirements_complete.txt
```

## Dependências Principais

### Obrigatórias:
- **pandas** (>=1.5.0): Manipulação de dados e DataFrames
- **numpy** (>=1.21.0): Operações numéricas
- **openpyxl** (>=3.1.0): Manipulação de arquivos Excel

### Opcionais (para funcionalidades avançadas):
- **plotly** (>=5.13.0): Visualizações interativas
- **dash** (>=2.8.0): Aplicações web
- **dash-bootstrap-components** (>=1.3.0): Componentes Bootstrap para Dash
- **xlrd** (>=2.0.0): Leitura de arquivos Excel antigos
- **xlsxwriter** (>=3.0.0): Escrita avançada de Excel
- **python-dateutil** (>=2.8.0): Manipulação de datas
- **pytz** (>=2022.1): Fusos horários

## Verificação da Instalação

Para verificar se todas as dependências foram instaladas corretamente:

```cmd
python -c "import pandas, numpy, openpyxl; print('Dependências principais instaladas com sucesso!')"
```

## Solução de Problemas

### Erro: "Python não encontrado"
- Instale o Python em: https://www.python.org/downloads/
- Certifique-se de marcar "Add Python to PATH" durante a instalação

### Erro: "pip não encontrado"
- Reinstale o Python ou use: `python -m ensurepip --upgrade`

### Erro de permissão
- Use: `python -m pip install --user [nome_da_biblioteca]`

### Erro de versão
- Atualize pip: `python -m pip install --upgrade pip`
- Use versões específicas: `python -m pip install pandas==1.5.3`

## Testando o Projeto

Após a instalação, teste o projeto:

```cmd
python scripts/colhedorasMinOcioso.py
```

## Estrutura do Projeto

```
processamentoexcel/
├── scripts/
│   └── colhedorasMinOcioso.py    # Script principal
├── dados/                        # Pasta para arquivos de entrada
├── output/                       # Pasta para arquivos de saída
├── config/                       # Arquivos de configuração
├── requirements.txt              # Dependências básicas
├── requirements_complete.txt     # Dependências completas
├── install_dependencies.bat     # Script de instalação (CMD)
├── install_dependencies.ps1     # Script de instalação (PowerShell)
└── INSTALACAO_DEPENDENCIAS.md   # Este arquivo
```

## Suporte

Se encontrar problemas durante a instalação:
1. Verifique se o Python está instalado corretamente
2. Tente usar `python -m pip` em vez de apenas `pip`
3. Use ambientes virtuais se necessário: `python -m venv venv`
