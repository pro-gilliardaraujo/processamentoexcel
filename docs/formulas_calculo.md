# Documentação das Fórmulas de Cálculo

Este documento descreve todas as fórmulas e métodos de cálculo utilizados no sistema de processamento de dados de monitoramento de colhedoras e transbordos.

## Métricas Comuns

### Cálculo de Porcentagem
Usado em várias fórmulas:
```python
def calcular_porcentagem(numerador, denominador, precisao=4):
    """Calcula porcentagem como decimal (0-1) evitando divisão por zero."""
    if denominador > 0:
        return round((numerador / denominador), precisao)
    return 0.0
```

### Horas Totais
```
Horas Totais = Soma de todas as 'Diferença_Hora' para um Equipamento/Grupo/Operador
```

### Diferença_Hora
```
Diferença_Hora = Diferença de tempo entre registros consecutivos (em horas)
Se Diferença_Hora > 0.50, então = 0
```

## Colhedoras

### Disponibilidade Mecânica
```
Total Horas = Soma de 'Diferença_Hora' para cada equipamento
Horas Manutenção = Soma de 'Diferença_Hora' onde 'Grupo Operacao' = 'Manutenção'
Disponibilidade Mecânica = (Total Horas - Horas Manutenção) / Total Horas
```

### Horas Produtivas
```
Horas Produtivas = Soma de 'Diferença_Hora' onde 'Grupo Operacao' = 'Produtiva'
```

### Horas Elevador
```
Horas Elevador = Soma de 'Diferença_Hora' onde:
    'Esteira Ligada' = 1 E
    'Pressao de Corte' > 400
```

### Eficiência Energética
```
Horas Elevador = Como definido acima
Motor Ligado = Soma de 'Diferença_Hora' onde 'Motor Ligado' = 1
Eficiência Energética = Horas Elevador / Motor Ligado
```

### Motor Ocioso
```
Parado com Motor Ligado = Soma de 'Diferença_Hora' onde:
    'Velocidade' = 0 E
    'RPM Motor' >= 300 (RPM_MINIMO) E
    'Motor Ligado' = 1
Motor Ligado = Soma de 'Diferença_Hora' onde 'Motor Ligado' = 1
Motor Ocioso = Parado com Motor Ligado / Motor Ligado
```

### Uso GPS (Colhedoras)
```
Tempo Trabalhando = Soma de 'Diferença_Hora' onde 'Estado' = 'TRABALHANDO' ou 'COLHEITA'
Tempo GPS Ativo = Soma de 'Diferença_Hora' onde:
    'Estado' = 'TRABALHANDO' ou 'COLHEITA' E
    'RTK (Piloto Automatico)' = 1 E
    'Velocidade' > 0
Uso GPS = Tempo GPS Ativo / Tempo Trabalhando
```

## Transbordos

### Disponibilidade Mecânica
```
Total Horas = Soma de 'Diferença_Hora' para cada equipamento
Horas Manutenção = Soma de 'Diferença_Hora' onde 'Grupo Operacao' = 'Manutenção'
Disponibilidade Mecânica = (Total Horas - Horas Manutenção) / Total Horas
```

### Horas Produtivas (Transbordos)
```
Horas Produtivas = Soma de 'Diferença_Hora' onde 'Grupo Operacao' = 'Produtiva'
```

### GPS (Transbordos)
```
GPS = Soma de 'Diferença_Hora' onde:
    'RTK (Piloto Automatico)' = 1 E
    'Velocidade' > 0 E
    'Grupo Operacao' = 'Produtiva'
```

### Uso GPS (Transbordos)
```
GPS = Como definido acima
Horas Produtivas = Como definido acima
Uso GPS = GPS / Horas Produtivas
```

### Eficiência Energética (Transbordos)
```
Eficiência Energética = Calculado por métodos específicos para transbordos
```

### Motor Ocioso (Transbordos)
```
Parado com Motor Ligado = Soma de 'Diferença_Hora' onde:
    'Velocidade' = 0 E
    'RPM Motor' >= 300 (RPM_MINIMO)
Motor Ligado = Soma de 'Diferença_Hora' onde 'Motor Ligado' = 1
Motor Ocioso = Parado com Motor Ligado / Motor Ligado
```

### Falta de Apontamento
```
Falta de Apontamento = Soma de 'Diferença_Hora' onde:
    'Motor Ligado' = 1 E
    ('Codigo da Operacao' = 8340 OU
     'Codigo da Operacao' começa com '8340' OU
     'Operacao' contém 'FALTA DE APONTAMENTO')

% Falta de Apontamento = Falta de Apontamento / Horas Totais
```
*Nota: Modificado para usar Horas Totais como denominador, em vez de Motor Ligado.*

## Horas por Frota

```
Horas Registradas = Soma de 'Diferença_Hora' para cada equipamento (sem filtros)
Diferença para 24h = 24 - Horas Registradas (ou 0 se negativo)
``` 