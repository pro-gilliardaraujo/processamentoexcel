# Instruções de Uso do Sistema de Processamento Unificado

## Visão Geral

Este sistema permite o processamento unificado de dados de colhedoras e transbordos, gerando relatórios em formato específico para visualização e análise.

## Estrutura do Projeto

```
.
├── dados/              # Pasta para arquivos de dados de entrada
│   ├── colhedoras/     # Dados de colhedoras (.txt, .csv)
│   └── transbordos/    # Dados de transbordos (.txt, .csv)
├── docs/               # Documentação do projeto
├── output/             # Resultados processados (.xlsx)
├── scripts/            # Scripts Python para processamento 
│   └── processamento_unificado.py  # Script principal unificado
├── frontend/           # Interface web para visualização
└── README.md           # Documentação principal
```

## Instruções de Uso

### Processamento de Dados

1. Coloque os arquivos de dados na pasta `dados/`:
   - Arquivos de colhedoras em `dados/colhedoras/`
   - Arquivos de transbordos em `dados/transbordos/`

2. Execute o script de processamento unificado:

```bash
python scripts/processamento_unificado.py
```

3. Os resultados serão gerados na pasta `output/` com o seguinte formato:
   - Prefixo `CD_` para planilhas de colhedoras
   - Prefixo `TT_` para planilhas de transbordos
   - Planilha `METADATA` com informações sobre frentes e tipos de equipamento

### Interface Web

1. Instale as dependências:

```bash
npm run setup
```

2. Execute o frontend:

```bash
npm run dev
```

3. Acesse a aplicação em http://localhost:3000

### Upload e Geração de Relatórios

1. Na interface web, acesse "Upload de Dados"
2. Selecione a data do relatório
3. Selecione a frente de trabalho
4. Marque os tipos de relatório desejados (podem ser múltiplos)
5. Arraste ou selecione o arquivo Excel processado
6. Clique em "Processar Arquivo"
7. Os relatórios serão gerados e você será redirecionado para a visualização

## Recursos Adicionais

- **Processamento em Lote**: É possível processar múltiplos arquivos colocando-os na pasta `dados/`
- **Múltiplos Relatórios**: O frontend permite gerar diversos tipos de relatório a partir de um único arquivo Excel
- **Configuração de Frentes**: Os mapeamentos de frentes podem ser ajustados no arquivo `config/reports.config.json`

## Suporte

Em caso de problemas, verifique:
1. Se os arquivos estão nos formatos corretos (.txt, .csv)
2. Se as pastas de dados existem e têm permissões de leitura/escrita
3. Se as dependências foram instaladas corretamente 