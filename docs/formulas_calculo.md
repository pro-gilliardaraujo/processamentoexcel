# Documentação das Fórmulas de Cálculo - Guia Completo

Este documento explica em detalhes todas as fórmulas e métodos de cálculo utilizados no sistema de processamento de dados de monitoramento de colhedoras (CD) e transbordos (TT).

## Conceitos Básicos

### O que é "Diferença_Hora"?
A "Diferença_Hora" é o tempo (em horas) entre dois registros consecutivos de um mesmo equipamento no sistema. Esta é a nossa unidade básica para todos os cálculos.

**Exemplo:** Se um equipamento tem registros às 10:30:00 e às 10:45:00, a Diferença_Hora é de 0,25 horas (15 minutos).

**Importante:** Se a diferença entre dois registros for maior que 30 minutos (0,50 horas), consideramos que houve uma interrupção no monitoramento e atribuímos valor zero.

### Como calculamos as porcentagens?

Todas as porcentagens são calculadas como números decimais entre 0 e 1, onde:
- 0.00 = 0% 
- 0.50 = 50%
- 1.00 = 100%

A fórmula básica é:
```
Porcentagem = Numerador ÷ Denominador
```

Se o denominador for zero, a porcentagem é sempre zero para evitar erros de divisão por zero.

## Métricas para Transbordos (TT)

### Disponibilidade Mecânica

**O que é:** Porcentagem do tempo em que o equipamento estava disponível (não estava em manutenção).

**Fórmula detalhada:**
1. Total de Horas = Soma de todas as Diferença_Hora para o equipamento
2. Horas em Manutenção = Soma de Diferença_Hora onde "Grupo Operacao" = "Manutenção"
3. Disponibilidade Mecânica = (Total de Horas - Horas em Manutenção) ÷ Total de Horas

**Exemplo:** Se um transbordo operou por 20 horas no total, e dessas, 2 horas estavam marcadas como manutenção:
- Disponibilidade Mecânica = (20 - 2) ÷ 20 = 0.90 = 90%

### Horas Produtivas

**O que é:** Total de horas em que o equipamento estava em operação produtiva.

**Fórmula simples:**
```
Horas Produtivas = Soma de Diferença_Hora onde "Grupo Operacao" = "Produtiva"
```

**Exemplo:** Se em um dia o equipamento trabalhou 8 horas, mas apenas 6 horas estavam marcadas como "Produtiva", então as Horas Produtivas = 6 horas.

### Eficiência Energética (Transbordos)

**O que é:** Proporção de tempo produtivo em relação ao tempo total registrado.

**Fórmula detalhada:**
1. Horas Produtivas = Soma de Diferença_Hora onde "Grupo Operacao" = "Produtiva"
2. Horas Totais = Soma de todas as Diferença_Hora para o equipamento e operador
3. Eficiência Energética = Horas Produtivas ÷ Horas Totais

**Exemplo:** Se um operador trabalhou 10 horas no total e 7 horas foram produtivas:
- Eficiência Energética = 7 ÷ 10 = 0.70 = 70%

### Motor Ocioso (Transbordos)

**O que é:** Proporção de tempo em que o motor estava ligado mas o veículo estava parado, excluindo operações específicas definidas na configuração.

**Operações excluídas por padrão:**
- "9016 - ENCH SISTEMA FREIO"
- "6340 - BASCULANDO TRANSBORDAGEM"
- "9024 - DESATOLAMENTO"

**Por que excluímos estas operações?** Porque nestas operações é normal e necessário que o veículo esteja parado com o motor ligado.

**Fórmula detalhada:**
1. Filtrar dados: 
   - Incluir apenas dados do operador e frente específicos
   - Excluir registros onde "Operacao" está na lista de operações excluídas
2. Motor Ligado = Soma de Diferença_Hora onde "Motor Ligado" = 1 (nos dados filtrados)
3. Parado com Motor Ligado = Soma de Diferença_Hora onde todos os seguintes são verdadeiros:
   - "Motor Ligado" = 1
   - "Velocidade" = 0
   - "RPM Motor" ≥ 300
4. Motor Ocioso = Parado com Motor Ligado ÷ Motor Ligado

**Exemplo prático:**
- Um transbordo operou por 8 horas
- Motor ficou ligado por 7 horas
- Veículo ficou parado com motor ligado por 3 horas no total
- Dessas 3 horas, 1 hora foi gasta em "BASCULANDO TRANSBORDAGEM"
- Cálculo do Motor Ocioso:
  - Tempo de Motor Ligado após exclusões = 7 horas
  - Tempo Parado com Motor Ligado após exclusões = 3 - 1 = 2 horas
  - Motor Ocioso = 2 ÷ 7 = 0.29 = 29%

### Falta de Apontamento

**O que é:** Proporção de tempo em que o motor estava ligado e o sistema registrou "FALTA DE APONTAMENTO".

**Fórmula detalhada:**
1. Tempo com Falta de Apontamento = Soma de Diferença_Hora onde:
   - "Motor Ligado" = 1 E
   - Uma destas condições é verdadeira:
     - "Codigo da Operacao" = 8340, OU
     - "Codigo da Operacao" começa com "8340", OU
     - "Operacao" contém o texto "FALTA DE APONTAMENTO"
2. Tempo Total de Motor Ligado = Soma de Diferença_Hora onde "Motor Ligado" = 1
3. % Falta de Apontamento = Tempo com Falta de Apontamento ÷ Tempo Total de Motor Ligado

**Exemplo:** Se em 8 horas de operação, o motor ficou ligado por 7 horas, e dessas, 1 hora estava com "FALTA DE APONTAMENTO":
- % Falta de Apontamento = 1 ÷ 7 = 0.14 = 14%

### Uso GPS (Transbordos)

**O que é:** Proporção de tempo em que o equipamento estava usando GPS durante operações produtivas.

**Fórmula detalhada:**
1. Tempo com GPS Ativo = Soma de Diferença_Hora onde:
   - "RTK (Piloto Automatico)" = 1 E
   - "Velocidade" > 0 E
   - "Grupo Operacao" = "Produtiva"
2. Horas Produtivas = Soma de Diferença_Hora onde "Grupo Operacao" = "Produtiva"
3. % Uso GPS = Tempo com GPS Ativo ÷ Horas Produtivas

**Exemplo:** Se um equipamento teve 6 horas produtivas, e durante 4 horas estava com o GPS ligado:
- % Uso GPS = 4 ÷ 6 = 0.67 = 67%

### Horas por Frota

**O que é:** Total de horas registradas por cada frota (equipamento) e a diferença para completar 24 horas.

**Fórmula simples:**
1. Horas Registradas = Soma de todas as Diferença_Hora para o equipamento
2. Diferença para 24h = 24 - Horas Registradas (se o resultado for negativo, consideramos 0)

**Exemplo:** Se um equipamento operou por 20 horas em um dia:
- Horas Registradas = 20 horas
- Diferença para 24h = 24 - 20 = 4 horas

## Métricas para Colhedoras (CD)

### Disponibilidade Mecânica

Mesma fórmula usada para transbordos.

### Horas Produtivas

Mesma fórmula usada para transbordos.

### Horas Elevador

**O que é:** Total de horas em que o elevador (esteira) da colhedora estava efetivamente funcionando.

**Fórmula detalhada:**
1. Horas Elevador = Soma de Diferença_Hora onde:
   - "Esteira Ligada" = 1 E
   - "Pressao de Corte" > 400

**Exemplo:** Se uma colhedora operou por 8 horas, mas a esteira só estava ligada com pressão adequada por 5 horas:
- Horas Elevador = 5 horas

### Eficiência Energética (Colhedoras)

**O que é:** Proporção de tempo em que o elevador estava ativo em relação ao tempo total com motor ligado.

**Fórmula detalhada:**
1. Horas Elevador = (como calculado acima)
2. Tempo Motor Ligado = Soma de Diferença_Hora onde "Motor Ligado" = 1
3. Eficiência Energética = Horas Elevador ÷ Tempo Motor Ligado

**Exemplo:** Se uma colhedora teve o motor ligado por 8 horas, e o elevador funcionou por 6 horas:
- Eficiência Energética = 6 ÷ 8 = 0.75 = 75%

### Motor Ocioso (Colhedoras)

Segue a mesma lógica do cálculo para transbordos, mas sem operações excluídas por padrão (a lista de exclusões pode ser configurada separadamente no arquivo de configuração).

### Uso GPS (Colhedoras)

**O que é:** Proporção de tempo em que o GPS estava ativo durante o trabalho efetivo.

**Fórmula detalhada:**
1. Tempo Trabalhando = Soma de Diferença_Hora onde "Estado" = "TRABALHANDO" ou "COLHEITA"
2. Tempo GPS Ativo = Soma de Diferença_Hora onde:
   - "Estado" = "TRABALHANDO" ou "COLHEITA" E
   - "RTK (Piloto Automatico)" = 1 E
   - "Velocidade" > 0
3. % Uso GPS = Tempo GPS Ativo ÷ Tempo Trabalhando

**Exemplo:** Se uma colhedora trabalhou por 8 horas, e usou GPS por 6 horas durante este trabalho:
- % Uso GPS = 6 ÷ 8 = 0.75 = 75%

## Configuração de Cálculos

O sistema permite configurar quais operações devem ser excluídas do cálculo de Motor Ocioso através do arquivo `config/calculos_config.json`.

### Estrutura do arquivo de configuração:

```json
{
  "CD": {
    "motor_ocioso": {
      "tipo_calculo": "Remover do cálculo",
      "operacoes_excluidas": []
    }
  },
  "TT": {
    "motor_ocioso": {
      "tipo_calculo": "Remover do cálculo",
      "operacoes_excluidas": [
        "9016 - ENCH SISTEMA FREIO",
        "6340 - BASCULANDO  TRANSBORDAGEM"
      ]
    }
  }
}
```

Para modificar as operações excluídas, basta editar as listas `operacoes_excluidas` correspondentes. 