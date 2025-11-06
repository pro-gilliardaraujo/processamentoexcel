# Documentação Completa dos Sistemas de Processamento Agrícola

## Visão Geral

O sistema possui **4 módulos principais** de processamento, divididos por tipo de equipamento e abordagem de cálculo:

### **Módulos Baseados em MÁQUINAS/FROTAS:**
1. **1_ProcessadorColhedorasMaq.py** - Colhedoras por máquina/frota
2. **2_ProcessadorTransbordosMaq.py** - Transbordos por máquina/frota

### **Módulos Baseados em OPERADORES:**
3. **zip_processor_colheita-operadores.py** - Colhedoras por operador
4. **zip_processor_transbordo-operadores.py** - Transbordos por operador

---

## DIFERENÇAS FUNDAMENTAIS ENTRE ABORDAGENS

### **📊 PROCESSADORES POR MÁQUINA/FROTA**
- **Foco**: Desempenho e eficiência dos equipamentos
- **Agrupamento principal**: Por `Equipamento` (frota)
- **Métricas-chave**: Disponibilidade mecânica, horas de funcionamento, motor ocioso por máquina
- **Uso**: Análise técnica de equipamentos, manutenção, otimização de frotas

### **👨‍🌾 PROCESSADORES POR OPERADOR**
- **Foco**: Desempenho e produtividade dos operadores
- **Agrupamento principal**: Por `Operador` (com indicação das frotas utilizadas)
- **Métricas-chave**: Eficiência energética, horas elevador, uso GPS por operador
- **Uso**: Gestão de pessoas, treinamento, avaliação de performance

---

## ESTRUTURA DE DADOS COMUM

### Colunas Originais dos Arquivos
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
- Pressao de Corte (colhedoras)
- RPM Motor
- RTK (Piloto Automatico) (colhedoras)
- Esteira Ligada (colhedoras)
- Implemento Ligado (colhedoras)
- Grupo Equipamento/Frente
- Latitude
- Longitude
```

### Colunas Calculadas (Adicionadas)
```
- Diferença_Hora (tempo entre registros sequenciais)
- Parada com Motor Ligado
- Motor Ocioso (método avançado)
- Motor Ocioso Correto (método sequencial aprimorado)
- Horas Produtivas
```

---

## CONFIGURAÇÕES E CONSTANTES

### Validação de Dados
- **TEMPO_MINIMO_VALIDO**: 0.001 horas (3.6 segundos)
- **RPM_MINIMO**: 300 RPM
- **Diferença_Hora > 0.50**: zerada (quebras/pausas longas)

### Operadores Excluídos
```
- "9999 - TROCA DE TURNO"
- "1 - SEM OPERADOR"
```

### Operações Excluídas (Motor Ocioso)
**Colhedoras:**
```
- "8490 - LAVAGEM"
- "MANUTENCAO"
- "INST CONFIG TECNOL EMBARCADAS"
- "1055 - MANOBRA"
```

**Transbordos:**
```
- "9016 - ENCH SISTEMA FREIO"
- "6340 - BASCULANDO TRANSBORDAGEM"
- "9024 - DESATOLAMENTO"
- "MANUTENCAO"
- "INST CONFIG TECNOL EMBARCADAS"
- "1055 - MANOBRA"
```

---

## CÁLCULOS POR TIPO DE EQUIPAMENTO

## A. COLHEDORAS

### 1. HORAS ELEVADOR

#### **🏭 Por Máquina/Frota:**
```python
# Condições
filtro = (
    (df['Grupo Operacao'] == 'Produtiva') & 
    (df['Pressao de Corte'] >= 400) &
    (df['Velocidade'] > 0)
)

# Cálculo por equipamento
for equipamento in df['Equipamento'].unique():
    dados_equip = df[df['Equipamento'] == equipamento]
    horas_elevador = dados_equip[filtro]['Diferença_Hora'].sum()
```

#### **👨‍🌾 Por Operador:**
```python
# Agregação por operador (múltiplas frotas)
for operador in df['Operador'].unique():
    dados_operador = df[df['Operador'] == operador]
    frotas_utilizadas = sorted(dados_operador['Equipamento'].unique())
    
    # Cálculo total do operador em todas as frotas
    horas_elevador_total = dados_operador[filtro]['Diferença_Hora'].sum()
    dias_trabalhados = dados_operador['Data'].nunique()
    horas_elevador_media = horas_elevador_total / dias_trabalhados
    
    # Nome: "ID - NOME (frota1, frota2, frota3)"
    operador_com_frotas = f"{operador} ({', '.join(frotas_utilizadas)})"
```

### 2. MOTOR OCIOSO

#### **🏭 Por Máquina/Frota:**
- Foco na eficiência técnica da máquina
- Cálculo baseado em intervalos sequenciais com tolerância de 1 minuto
- Resultado: percentual de tempo ocioso por equipamento

#### **👨‍🌾 Por Operador:**
- Foco na eficiência operacional do operador
- Agrega dados de todas as frotas que o operador utilizou
- Resultado: percentual de ociosidade médio do operador

### 3. RTK/GPS

#### **🏭 Por Máquina/Frota:**
```python
# Por equipamento
rtk_por_equipamento = df[filtro_rtk]['Diferença_Hora'].sum()
produtivas_por_equipamento = df[filtro_produtivo]['Diferença_Hora'].sum()
porcentagem = rtk_por_equipamento / produtivas_por_equipamento
```

#### **👨‍🌾 Por Operador:**
```python
# Agregado por operador
rtk_total_operador = dados_operador[filtro_rtk]['Diferença_Hora'].sum()
produtivas_total_operador = dados_operador[filtro_produtivo]['Diferença_Hora'].sum()
dias_trabalhados = dados_operador['Data'].nunique()

rtk_media = rtk_total_operador / dias_trabalhados
produtivas_media = produtivas_total_operador / dias_trabalhados
porcentagem = rtk_media / produtivas_media
```

---

## B. TRANSBORDOS

### 1. EFICIÊNCIA ENERGÉTICA

#### **🏭 Por Máquina/Frota:**
```python
# Por equipamento
horas_produtivas = dados_equip[dados_equip['Grupo Operacao'] == 'Produtiva']['Diferença_Hora'].sum()
horas_motor = dados_equip[dados_equip['Motor Ligado'] == 1]['Diferença_Hora'].sum()
eficiencia = horas_produtivas / horas_motor
```

#### **👨‍🌾 Por Operador:**
```python
# Agregado por operador (múltiplas frotas)
horas_produtivas_total = dados_operador[filtro_produtivo]['Diferença_Hora'].sum()
horas_motor_total = dados_operador[filtro_motor]['Diferença_Hora'].sum()
dias_trabalhados = dados_operador['Data'].nunique()

horas_produtivas_media = horas_produtivas_total / dias_trabalhados
horas_motor_media = horas_motor_total / dias_trabalhados
eficiencia = horas_produtivas_media / horas_motor_media
```

### 2. HORAS CARREGANDO
- **Operação específica**: `'6300 - CARREG CANA COLHIDA NO TRANSBORDO'`
- **Por máquina**: Total por equipamento
- **Por operador**: Média diária considerando todas as frotas utilizadas

### 3. BASCULAMENTO
- **Operação específica**: `'6340 - BASCULANDO TRANSBORDAGEM'`
- **Método**: Intervalos sequenciais (similar às manobras)
- **Validação**: Tempo mínimo de 15 segundos

### 4. VELOCIDADES (Carregado vs Vazio)
- **Carregado**: `Estado == 'CARREGADO'` + `Velocidade > 0`
- **Vazio**: `Estado == 'VAZIO'` + `Velocidade > 0`
- **Cálculo**: Média ponderada pelo tempo

---

## PLANILHAS GERADAS

### **🏭 PROCESSADORES POR MÁQUINA/FROTA:**

#### Colhedoras:
1. **BASE** - Dados processados completos
2. **Disponibilidade Mecânica** - Por equipamento
3. **Eficiência Energética** - Horas elevador/motor por equipamento
4. **Velocidade Média Produtiva** - Por equipamento
5. **Uso GPS** - Percentual RTK por equipamento
6. **Motor Ocioso** - Por equipamento
7. **Manobras Frotas** - Intervalos de manobras por equipamento
8. **Coordenadas** - Para mapas

#### Transbordos:
1. **BASE** - Dados processados completos
2. **Disponibilidade Mecânica** - Por equipamento
3. **Eficiência Energética** - Por equipamento
4. **Velocidade Carregado/Vazio** - Por equipamento
5. **Motor Ocioso** - Por equipamento
6. **Basculamento Frotas** - Intervalos por equipamento
7. **Falta Apontamento** - Inconsistências por equipamento

### **👨‍🌾 PROCESSADORES POR OPERADOR:**

#### Colhedoras:
1. **BASE** - Dados processados completos
2. **Base Calculo** - Métricas por operador/equipamento/frente
3. **1_Disponibilidade Mecânica** - Por equipamento (técnica)
4. **2_Eficiência Energética** - Por operador (com frotas)
5. **3_Hora Elevador** - Por operador (com frotas)
6. **4_Motor Ocioso** - Por operador (com frotas)
7. **5_Uso GPS** - Por operador (com frotas)
8. **Média Velocidade** - Por operador (com frotas)
9. **Manobras Operador** - Por operador
10. **Manobras Frotas** - Por equipamento
11. **IDs Encontradas** - Duplicidades detectadas
12. **IDs Substituídas** - Correções aplicadas

#### Transbordos:
1. **BASE** - Dados processados completos
2. **Base Calculo** - Métricas por operador/equipamento/frente
3. **1_Disponibilidade Mecânica** - Por equipamento (técnica)
4. **2_Eficiência Energética** - Por operador (com frotas)
5. **3_Motor Ocioso** - Por operador (com frotas)
6. **4_Falta Apontamento** - Por operador (com frotas)
7. **5_Uso GPS** - Por operador (com frotas)
8. **Média Velocidade** - Por operador (com frotas)

---

## RECURSOS ESPECÍFICOS DOS PROCESSADORES POR OPERADOR

### 1. **Consolidação de Operadores**
```python
# Detecta IDs duplicadas automaticamente
# Exemplo: "1330001 - JOÃO" e "331 - JOÃO" → consolida para "331 - JOÃO"

# Nomenclatura final
operador_com_frotas = f"{operador} ({frota1, frota2, frota3})"
# Resultado: "331 - JOÃO (7041, 7042, 7043)"
```

### 2. **Substituições de Operadores**
- **Arquivo**: `config/substituiroperadores.json`
- **Arquivo horário**: `config/substituiroperadores_horario.json`
- **Aplicação**: Antes de todos os cálculos

### 3. **Métricas Corrigidas**
- **Problema**: Operador trabalha em múltiplas frotas no mesmo dia
- **Solução**: Cálculo total dividido por dias únicos trabalhados
- **Benefício**: Médias diárias corretas independente do número de frotas

### 4. **Base Calculo**
- **Estrutura**: Operador + Equipamento + Grupo Equipamento/Frente
- **Função**: Fonte de dados para cálculos agregados
- **Vantagem**: Rastreabilidade completa

---

## COMPARAÇÃO DE RESULTADOS

### **Cenário Exemplo:**
Operador "João" trabalha em 3 frotas (7041, 7042, 7043) no mesmo dia.

#### **🏭 Por Máquina:**
```
- Frota 7041: 8.5h elevador
- Frota 7042: 7.2h elevador  
- Frota 7043: 6.8h elevador
Total: 22.5h (soma das frotas)
```

#### **👨‍🌾 Por Operador:**
```
- João (7041, 7042, 7043): 22.5h elevador total / 1 dia = 22.5h/dia
Resultado: Média diária correta considerando todas as frotas
```

---

## QUANDO USAR CADA ABORDAGEM

### **🏭 Use Processadores POR MÁQUINA quando:**
- Análise de disponibilidade mecânica
- Planejamento de manutenção
- Otimização de frotas
- Relatórios técnicos de equipamentos
- Análise de custos operacionais por máquina

### **👨‍🌾 Use Processadores POR OPERADOR quando:**
- Avaliação de desempenho de operadores
- Programas de treinamento
- Definição de metas individuais
- Análise de produtividade pessoal
- Gestão de recursos humanos

---

## VALIDAÇÕES E CONSISTÊNCIA

### Filtros Comuns:
1. Remove `Diferença_Hora < 0.001 horas`
2. Zera `Diferença_Hora > 0.50 horas`
3. Exclui operadores da lista `OPERADORES_EXCLUIR`
4. Aplica filtros específicos por tipo de operação

### Métodos de Cálculo:
1. **Horímetro** (preferencial): `final - inicial`
2. **Diferença_Hora** (fallback): `soma(tempos_filtrados)`
3. **Sequencial** (motor ocioso): intervalos com tolerância

### Formatação Excel:
- **Percentuais**: `0.00%`
- **Horas**: `0.00` ou `h:mm:ss`
- **Coordenadas**: `0.000000`
- **Velocidades**: `0.00`

---

## OBSERVAÇÕES FINAIS

1. **Compatibilidade**: Ambas abordagens usam os mesmos dados de entrada
2. **Complementaridade**: Resultados são complementares, não concorrentes
3. **Precisão**: Processadores por operador têm correções mais avançadas
4. **Escalabilidade**: Sistema modular permite extensão fácil
5. **Manutenibilidade**: Configurações centralizadas em constantes e arquivos JSON

Este sistema oferece **flexibilidade total** para análises tanto técnicas (equipamentos) quanto operacionais (pessoas), atendendo diferentes necessidades gerenciais e operacionais do agronegócio.
