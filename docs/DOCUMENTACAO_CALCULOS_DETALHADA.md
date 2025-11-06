# Documentação Detalhada dos Cálculos - Sistema de Processamento Agrícola

## Visão Geral

O sistema processa dados de equipamentos agrícolas (colhedoras e transbordos) gerando métricas operacionais. Existem dois módulos principais:

1. **1_ProcessadorColhedorasMaq.py** - Processamento de dados de colhedoras
2. **2_ProcessadorTransbordosMaq.py** - Processamento de dados de transbordos

---

## ESTRUTURA DE DADOS

### Colunas Originais dos Arquivos de Entrada
```
- Data/Hora (combinada) -> separada em 'Data' e 'Hora'
- Equipamento
- Operador
- Grupo Operacao
- Operacao
- Estado
- Estado Operacional
- Horimetro
- Motor Ligado
- Velocidade
- Pressao de Corte
- RPM Motor
- RTK (Piloto Automatico)
- Esteira Ligada
- Implemento Ligado
- Grupo Equipamento/Frente
- Latitude
- Longitude
- Fazenda
- Zona
- Talhao
- [Outras colunas removidas no processamento]
```

### Colunas Calculadas (Adicionadas durante o processamento)
```
- Diferença_Hora (calculada a partir da diferença entre registros sequenciais)
- Parada com Motor Ligado (calculada baseada em condições)
- Motor Ocioso (método avançado com intervalos)
- Motor Ocioso Correto (método sequencial aprimorado)
- Motor Ocioso Simples (soma direta de condições)
```

### Colunas Removidas (Por serem irrelevantes para os cálculos)
```
- Justificativa Corte Base Desligado
- Regional
- Tipo de Equipamento
- Unidade
- Centro de Custo
- Trabalhando em File
- Trabalhando Frente Dividida
- Trabalhando em Fila
- Apertura do Rolo
- Codigo da Operacao
- Codigo Frente (digitada)
- Corporativo
- Corte Base Automatico/Manual
- Descricao Equipamento
```

---

## CONFIGURAÇÕES GLOBAIS

### Constantes de Validação
- **TEMPO_MINIMO_VALIDO**: 0.001 horas (3.6 segundos) - tempo mínimo para considerar um registro válido
- **RPM_MINIMO**: 300 RPM - valor mínimo para considerar motor em funcionamento
- **tempoMinimoManobras**: 15 segundos - tempo mínimo para validar uma manobra
- **velocidadeMinimaManobras**: 0 km/h (colhedoras) / 1.5 km/h (transbordos)

### Operações Excluídas dos Cálculos de Motor Ocioso
**Colhedoras (CD):**
```
- "8490 - LAVAGEM"
- "MANUTENCAO" 
- "LAVAGEM"
- "INST CONFIG TECNOL EMBARCADAS"
- "1055 - MANOBRA"
```

**Transbordos (TT):**
```
- "9016 - ENCH SISTEMA FREIO"
- "6340 - BASCULANDO TRANSBORDAGEM"
- "9024 - DESATOLAMENTO"
- "MANUTENCAO"
- "MANUTENÇÃO"
- "INST CONFIG TECNOL EMBARCADAS"
- "1055 - MANOBRA"
```

### Grupos de Operação Excluídos
```
- "Manutenção"
- "Inaptidão"
```

---

## PROCESSAMENTO DE DADOS BASE

### 1. Leitura e Validação de Arquivos
- **Formatos suportados**: TXT, CSV, ZIP
- **Codificações tentadas**: utf-8, latin1, ISO-8859-1, cp1252
- **Separador**: `;` (ponto e vírgula)

### 2. Processamento de Data/Hora
```python
# Separação da coluna Data/Hora
df[['Data', 'Hora']] = df['Data/Hora'].str.split(' ', expand=True)

# Cálculo de Diferença_Hora (tempo entre registros sequenciais)
df_hora_temp = pd.to_datetime(df['Hora'], format='%H:%M:%S')
df['Diferença_Hora'] = df_hora_temp.diff().dt.total_seconds() / 3600

# Regra de validação: se Diferença_Hora > 0.50, então 0
df['Diferença_Hora'] = df['Diferença_Hora'].apply(lambda x: 0 if x > 0.50 else x)
```

### 3. Filtros de Validação
- Remove registros com `Diferença_Hora < TEMPO_MINIMO_VALIDO`
- Mantém registros com `Diferença_Hora = 0` (criados pela regra dos 0.50)

---

## CÁLCULOS ESPECÍFICOS POR TIPO DE EQUIPAMENTO

## A. COLHEDORAS (1_ProcessadorColhedorasMaq.py)

### 1. HORAS ELEVADOR
**Objetivo**: Medir tempo efetivo de operação do elevador da colhedora

**Colunas utilizadas:**
- `Grupo Operacao`
- `Pressao de Corte`
- `Velocidade`
- `Horimetro` (quando disponível)
- `Diferença_Hora` (fallback)

**Condições/Filtros:**
```python
condicao_elevador = (
    (df['Grupo Operacao'] == 'Produtiva') & 
    (df['Pressao de Corte'] >= 400) &
    (df['Velocidade'] > 0)
)
```

**Método de Cálculo:**
1. **Preferencial**: Diferença entre horímetro final e inicial dos registros filtrados
2. **Fallback**: Soma de `Diferença_Hora` dos registros que atendem às condições

### 2. MOTOR OCIOSO (Método Correto)
**Objetivo**: Calcular tempo de motor ligado sem produção, com tolerância

**Colunas utilizadas:**
- `Motor Ligado`
- `Estado Operacional`
- `Grupo Operacao`
- `Diferença_Hora`

**Filtros aplicados ANTES do cálculo:**
1. Excluir registros onde `Grupo Operacao == 'Manutenção'`
2. Considerar apenas `Motor Ligado == 1` E `Estado Operacional == 'PARADA'`

**Lógica Sequencial:**
1. Identificar intervalos contínuos de registros que atendem aos critérios
2. Para cada intervalo:
   - Somar todo o tempo (`Diferença_Hora`) do intervalo
   - Subtrair 1 minuto do total
   - Se resultado ≥ 1 minuto → incluir no cálculo
   - Se resultado < 1 minuto → descartar intervalo

### 3. RTK (USO DE GPS)
**Objetivo**: Medir utilização do sistema de navegação por GPS

**Colunas utilizadas:**
- `Grupo Operacao`
- `Pressao de Corte`
- `Velocidade`
- `RTK (Piloto Automatico)`
- `Horimetro`/`Diferença_Hora`

**Condições:**
```python
condicao_rtk = (
    (df['Grupo Operacao'] == 'Produtiva') &
    (df['Pressao de Corte'] >= 400) &
    (df['Velocidade'] > 0) &
    (df['RTK (Piloto Automatico)'] == 1)
)
```

**Cálculo:** Tempo com RTK ativo / Tempo de horas produtivas

### 4. VELOCIDADE MÉDIA PRODUTIVA
**Objetivo**: Calcular velocidade média durante operações produtivas

**Colunas utilizadas:**
- `Grupo Operacao`
- `Pressao de Corte`
- `Velocidade`
- `Diferença_Hora`

**Filtros:**
```python
dados_produtivos = df[
    (df['Grupo Operacao'] == 'Produtiva') & 
    (df['Pressao de Corte'] > 400) &
    (df['Velocidade'] > 0)
]
```

**Cálculo:** Média ponderada pelo tempo
```python
velocidade_media = (dados['Velocidade'] * dados['Diferença_Hora']).sum() / dados['Diferença_Hora'].sum()
```

### 5. DISPONIBILIDADE MECÂNICA
**Objetivo**: Medir percentual de tempo disponível (não em manutenção)

**Colunas utilizadas:**
- `Grupo Operacao`
- `Diferença_Hora`

**Fórmula:**
```python
disponibilidade = (Total_Geral - Tempo_Manutencao) / Total_Geral
```

**Onde:**
- Total_Geral = soma de `Diferença_Hora` (todos os registros)
- Tempo_Manutencao = soma de `Diferença_Hora` onde `Grupo Operacao == 'Manutenção'`

### 6. MANOBRAS POR INTERVALOS
**Objetivo**: Contar e cronometrar intervalos de manobras válidos

**Colunas utilizadas:**
- `Estado`
- `Diferença_Hora`

**Lógica:**
1. Analisa registros sequencialmente por equipamento/data/hora
2. Agrupa manobras consecutivas (`Estado == 'MANOBRA'`) em intervalos
3. Tolerância: registros NÃO-MANOBRA < 30 segundos continuam o intervalo (sem somar duração)
4. Interrupção: registros NÃO-MANOBRA ≥ 30 segundos fecham o intervalo
5. Validação: intervalos são válidos apenas se tempo total ≥ 15 segundos
6. Soma APENAS a duração de registros com `Estado = 'MANOBRA'`

### 7. LAVAGEM
**Objetivo**: Identificar e cronometrar intervalos de lavagem

**Colunas utilizadas:**
- `Operacao`
- `Diferença_Hora`
- `Hora`

**Filtro:** `Operacao == '8490 - LAVAGEM'`

**Lógica:**
- Agrupa registros consecutivos de lavagem
- Pausa > 30 minutos = novo intervalo
- Calcula início, fim e duração de cada intervalo

---

## B. TRANSBORDOS (2_ProcessadorTransbordosMaq.py)

### 1. EFICIÊNCIA ENERGÉTICA
**Objetivo**: Medir eficiência operacional do transbordo

**Colunas utilizadas:**
- `Grupo Operacao`
- `Motor Ligado`
- `Diferença_Hora`

**Fórmula:**
```python
eficiencia = Horas_Produtivas / Horas_Motor
```

**Onde:**
- Horas_Produtivas = soma de `Diferença_Hora` onde `Grupo Operacao == 'Produtiva'`
- Horas_Motor = soma de `Diferença_Hora` onde `Motor Ligado == 1`

### 2. HORAS CARREGANDO
**Objetivo**: Tempo específico de carregamento de cana

**Colunas utilizadas:**
- `Operacao`
- `Diferença_Hora`

**Filtro:** `Operacao == '6300 - CARREG CANA COLHIDA NO TRANSBORDO'`

**Cálculo:** Soma de `Diferença_Hora` dos registros filtrados

### 3. BASCULAMENTO POR INTERVALOS
**Objetivo**: Cronometrar intervalos de basculamento

**Colunas utilizadas:**
- `Operacao`
- `Diferença_Hora`

**Filtro:** `Operacao == '6340 - BASCULANDO TRANSBORDAGEM'`

**Lógica similar às manobras:**
- Intervalos sequenciais com tolerância de 30 segundos
- Tempo mínimo de 15 segundos para validação
- Soma apenas tempo de registros de basculamento

### 4. VELOCIDADE MÉDIA (Carregado vs Vazio)
**Objetivo**: Comparar velocidades em diferentes estados operacionais

**Velocidade Carregado:**
- Filtro: `Estado == 'CARREGADO'` E `Velocidade > 0`
- Cálculo: Média ponderada pelo tempo

**Velocidade Vazio:**
- Filtro: `Estado == 'VAZIO'` E `Velocidade > 0`
- Cálculo: Média ponderada pelo tempo

### 5. FALTA DE APONTAMENTO
**Objetivo**: Identificar inconsistências nos registros

**Colunas utilizadas:**
- `Horas totais`
- `Horas Produtivas`
- `Horas Carregando`

**Lógica:**
- Calcula diferenças entre métricas esperadas e registradas
- Identifica gaps de tempo não categorizados

---

## PLANILHAS GERADAS

### Para Colhedoras:
1. **BASE** - Dados processados completos
2. **Disponibilidade Mecânica** - Por equipamento
3. **Eficiência Energética** - Baseada em horas elevador
4. **Velocidade Média Produtiva** - Por equipamento
5. **Uso GPS** - Percentual de uso do RTK
6. **Motor Ocioso** - Por equipamento
7. **Lavagem** - Intervalos de lavagem
8. **Manobras Frotas** - Estatísticas de manobras
9. **Coordenadas** - Para mapas (GPS válidos)
10. **Semanal** - Consolidação por data/frota

### Para Transbordos:
1. **BASE** - Dados processados completos
2. **Disponibilidade Mecânica** - Por equipamento
3. **Eficiência Energética** - Por frota e operador
4. **Velocidade Média Carregado** - Por equipamento
5. **Velocidade Média Vazio** - Por equipamento
6. **Uso GPS** - Percentual de uso do RTK
7. **Motor Ocioso** - Por equipamento
8. **Basculamento Frotas** - Intervalos de basculamento
9. **Falta Apontamento** - Por operador
10. **Coordenadas** - Para mapas (GPS válidos)
11. **Semanal** - Consolidação por data/frota

---

## MÉTODOS DE CÁLCULO DE TEMPO

### 1. Método Horímetro (Preferencial)
```python
tempo_horimetro = horimetro_final - horimetro_inicial
# Validação: 0 < tempo_horimetro < 24 horas
```

### 2. Método Diferença_Hora (Fallback)
```python
tempo_diferenca = soma(Diferença_Hora dos registros filtrados)
```

### 3. Método Sequencial (Motor Ocioso)
```python
# Para cada intervalo contínuo:
tempo_intervalo = soma(Diferença_Hora do intervalo)
tempo_ocioso = max(tempo_intervalo - 1_minuto, 0)
# Se tempo_ocioso >= 1_minuto: incluir no cálculo
```

---

## TRATAMENTO DE RELATÓRIOS SEMANAIS

Quando `is_semanal = True`:
- Calcula número de dias únicos por equipamento
- Aplica médias diárias: `valor_final = valor_total / num_dias`
- Exceção: Tempo médio de manobras NÃO é dividido (já é média)

---

## VALIDAÇÕES E FILTROS APLICADOS

### Filtros de Qualidade de Dados:
1. Remove registros com `Diferença_Hora < 0.001 horas`
2. Zera `Diferença_Hora > 0.50 horas`
3. Remove equipamentos com valores NaN
4. Exclui operadores na lista `OPERADORES_EXCLUIR`

### Filtros de Negócio:
1. **Motor Ocioso**: Exclui operações de manutenção e específicas
2. **Horas Elevador**: Apenas produtiva + pressão ≥ 400 + velocidade > 0
3. **RTK**: Horas elevador + RTK ativo
4. **Coordenadas**: Remove GPS inválidos (0,0)

---

## OBSERVAÇÕES IMPORTANTES

1. **Precisão**: Todos os cálculos mantêm 4 casas decimais internamente
2. **Formatação**: Excel aplica formatação específica por tipo de dado
3. **Fallback**: Sistema sempre tem método alternativo se horímetro não disponível
4. **Consistência**: Validações impedem valores impossíveis (ex: ocioso > motor ligado)
5. **Performance**: Filtros aplicados antes dos cálculos para otimização

---

## ARQUIVOS CSV GERADOS

### Coordenadas:
- **Finalidade**: Geração de mapas
- **Formato**: CSV com separador `;`
- **Filtros**: Apenas coordenadas válidas (não 0,0)
- **Colunas**: Equipamento, Hora, Latitude, Longitude, Velocidade, RTK

Este sistema garante rastreabilidade completa dos cálculos e consistência entre diferentes tipos de equipamentos agrícolas.
