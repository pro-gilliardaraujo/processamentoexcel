# Configurações do Sistema de Processamento

Este diretório contém arquivos de configuração para o sistema de processamento de dados de colhedoras e transbordos.

## Arquivo `calculos_config.json`

Este arquivo contém configurações específicas para o cálculo de motor ocioso, separadas por tipo de equipamento: colhedoras (CD) e transbordos (TT).

### Estrutura

```json
{
  "CD": {
    "motor_ocioso": {
      "tipo_calculo": "Remover do cálculo",
      "operacoes_excluidas": [
        "Código - Descrição da Operação"
      ],
      "grupos_operacao_excluidos": [
        "Nome do Grupo de Operação"
      ]
    },
    "operadores_excluidos": [
      "Código - Nome do Operador"
    ],
    "equipamentos_excluidos": [
      "Código do Equipamento"
    ]
  },
  "TT": {
    "motor_ocioso": {
      "tipo_calculo": "Remover do cálculo",
      "operacoes_excluidas": [
        "Código - Descrição da Operação"
      ],
      "grupos_operacao_excluidos": [
        "Nome do Grupo de Operação"
      ]
    },
    "operadores_excluidos": [
      "Código - Nome do Operador"
    ],
    "equipamentos_excluidos": [
      "Código do Equipamento"
    ]
  }
}
```

### Configurações Suportadas

- **CD**: Configurações específicas para colhedoras
  - `motor_ocioso`: Configuração para o cálculo de motor ocioso de colhedoras
    - `tipo_calculo`: Define a forma de cálculo (atualmente apenas "Remover do cálculo" é suportado)
    - `operacoes_excluidas`: Lista de códigos de operação que devem ser excluídos ao calcular o motor ocioso
    - `grupos_operacao_excluidos`: Lista de grupos de operação que devem ser excluídos ao calcular o motor ocioso
  - `operadores_excluidos`: Lista de operadores que serão excluídos de todos os cálculos
  - `equipamentos_excluidos`: Lista de equipamentos/frotas que serão excluídos de todos os cálculos

- **TT**: Configurações específicas para transbordos
  - `motor_ocioso`: Configuração para o cálculo de motor ocioso de transbordos
    - `tipo_calculo`: Define a forma de cálculo (atualmente apenas "Remover do cálculo" é suportado)
    - `operacoes_excluidas`: Lista de códigos de operação que devem ser excluídos ao calcular o motor ocioso
    - `grupos_operacao_excluidos`: Lista de grupos de operação que devem ser excluídos ao calcular o motor ocioso
  - `operadores_excluidos`: Lista de operadores que serão excluídos de todos os cálculos
  - `equipamentos_excluidos`: Lista de equipamentos/frotas que serão excluídos de todos os cálculos

### Exemplo

```json
{
  "CD": {
    "motor_ocioso": {
      "tipo_calculo": "Remover do cálculo",
      "operacoes_excluidas": [],
      "grupos_operacao_excluidos": [
        "Manutenção"
      ]
    },
    "operadores_excluidos": [
      "9999 - TROCA DE TURNO",
      "1 -SEM OPERADOR"
    ],
    "equipamentos_excluidos": [
      "7035.0",
      "7044.0"
    ]
  },
  "TT": {
    "motor_ocioso": {
      "tipo_calculo": "Remover do cálculo",
      "operacoes_excluidas": [
        "9016 - ENCH SISTEMA FREIO",
        "6340 - BASCULANDO  TRANSBORDAGEM"
      ],
      "grupos_operacao_excluidos": [
        "Manutenção"
      ]
    },
    "operadores_excluidos": [
      "9999 - TROCA DE TURNO",
      "1 -SEM OPERADOR"
    ],
    "equipamentos_excluidos": [
      "8011.0"
    ]
  }
}
```

Neste exemplo:
- Para colhedoras (CD), nenhuma operação específica é excluída do cálculo de motor ocioso
- Para transbordos (TT), as operações "9016 - ENCH SISTEMA FREIO" e "6340 - BASCULANDO TRANSBORDAGEM" são excluídas do cálculo de motor ocioso
- Para ambos tipos de equipamento, o grupo de operação "Manutenção" é excluído do cálculo de motor ocioso
- Os operadores "9999 - TROCA DE TURNO" e "1 -SEM OPERADOR" são excluídos de todos os cálculos para ambos tipos de equipamento
- Os equipamentos "7035.0" e "7044.0" da frota de colhedoras (CD) são excluídos de todos os cálculos
- O equipamento "8011.0" da frota de transbordos (TT) é excluído de todos os cálculos

## Como Modificar

Para adicionar ou remover entradas das listas de exclusão:

1. Abra o arquivo `calculos_config.json`
2. Localize a seção do tipo de equipamento (`CD` ou `TT`)
3. Adicione ou remova entradas nas listas apropriadas (`operacoes_excluidas`, `grupos_operacao_excluidos`, `operadores_excluidos` ou `equipamentos_excluidos`)
4. Salve o arquivo

Não é necessário reiniciar o sistema; as mudanças serão aplicadas na próxima execução do script de processamento. 