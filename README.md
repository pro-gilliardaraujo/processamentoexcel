# Sistema de Processamento de Dados de Monitoramento

Este projeto contém scripts para processamento de dados de monitoramento de colhedoras e transbordos.

## Estrutura do Projeto

```
├── dados/              # Pasta para arquivos de dados de entrada
│   ├── colhedoras/     # Dados de colhedoras (.txt, .csv)
│   └── transbordos/    # Dados de transbordos (.txt, .csv)
├── docs/               # Documentação do projeto
├── output/             # Resultados processados (.xlsx)
└── scripts/            # Scripts Python para processamento
    ├── processamento_completo.py           # Script genérico
    ├── processamento_completo_colhedoras.py # Para colhedoras
    ├── processamento_completo_transbordos.py # Para transbordos
    ├── Codigo_Base_C.py                    # Código base para colhedoras
    └── Codigo_Base_TT.py                   # Código base para transbordos
```

## Como Usar

1. Coloque os arquivos de dados de entrada nas respectivas pastas:
   - Arquivos relacionados a colhedoras em `dados/colhedoras/`
   - Arquivos relacionados a transbordos em `dados/transbordos/`

2. Execute o script de processamento desejado:

```
python scripts/processamento_completo_colhedoras.py  # Para processar colhedoras
python scripts/processamento_completo_transbordos.py  # Para processar transbordos
```

3. Os resultados serão gerados na pasta `output/`

## Requisitos

- Python 3.6+
- Bibliotecas:
  - pandas
  - numpy
  - openpyxl

## Funcionalidades

O processamento calcula:
- Disponibilidade mecânica
- Eficiência energética
- Motor ocioso
- Falta de apontamento
- Uso de GPS
- Horas por frota

Os arquivos processados incluem várias planilhas para facilitar a análise dos dados. 