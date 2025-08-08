# 🏭 Configuração de Produção por Frente

## 🎯 **Configuração Automática por Arquivo**

O sistema agora identifica automaticamente a frente baseada no nome do arquivo e usa a produção configurada específica para cada frente.

## ⚙️ **Configurações Disponíveis**

### **Variáveis de Configuração (Linha 22-26)**
```python
# Configurações de produção por frente - CONFIGURE ANTES DE EXECUTAR
TONELADAS_FRENTE_03 = 1200   # Toneladas Frente03
TONELADAS_FRENTE_04 = 1500   # Toneladas Frente04  
TONELADAS_FRENTE_08 = 1800   # Toneladas Frente08
TONELADAS_FRENTE_ZIRLENO = 1000  # Toneladas FrenteZirleno
```

### **Mapeamento Automático**
| **Padrão no Nome do Arquivo** | **Frente Identificada** | **Variável Usada** |
|------------------------------|------------------------|-------------------|
| `frente03` | Frente03 | `TONELADAS_FRENTE_03` |
| `frente04` | Frente04 | `TONELADAS_FRENTE_04` |
| `frente08` | Frente08 | `TONELADAS_FRENTE_08` |
| `zirleno` | Zirleno | `TONELADAS_FRENTE_ZIRLENO` |

## 📁 **Exemplos de Identificação**

### **Arquivos de Exemplo**
```
colhedorasFrente03_05082025.zip     → Frente03 (1200t)
colhedorasFrente04_05082025.zip     → Frente04 (1500t)
colhedorasFrente08_05082025.zip     → Frente08 (1800t)
colhedorasZirleno_05082025.zip      → Zirleno (1000t)
```

### **Log de Identificação**
```
🔍 Analisando arquivo: colhedorasfrente04_05082025.zip
✅ Frente identificada: Frente04 = 1500 toneladas

=== CALCULANDO PRODUÇÃO POR FROTA ===
Frente: Frente04
Total de toneladas a distribuir: 1500
```

## 🔧 **Como Configurar**

### **1. Editar Configurações (Obrigatório)**
Edite as linhas 23-26 no arquivo `scripts/1_ProcessadorColhedorasMaq.py`:

```python
TONELADAS_FRENTE_03 = 1400    # Sua produção Frente03
TONELADAS_FRENTE_04 = 1600    # Sua produção Frente04  
TONELADAS_FRENTE_08 = 2000    # Sua produção Frente08
TONELADAS_FRENTE_ZIRLENO = 1200  # Sua produção Zirleno
```

### **2. Executar Processamento**
```bash
python scripts/1_ProcessadorColhedorasMaq.py
```

### **3. Verificar Logs**
O sistema mostrará:
```
🔍 Analisando arquivo: [nome_do_arquivo]
✅ Frente identificada: [Frente] = [toneladas] toneladas
```

## 📊 **Resultado no Excel e Supabase**

### **Planilha "Produção"**
```
Frota | Toneladas | Horas Elevador | Ton/h
------|-----------|----------------|-------
7032  | 623.50    | 8.2           | 76.04
7036  | 542.25    | 7.1           | 76.37
7037  | 334.25    | 4.4           | 75.96
Total | 1500.00   | 19.7          | 76.14
```

### **Campo Supabase `painel_esquerdo`**
```json
{
  "frota": 7032,
  "toneladas": 623.50,
  "ton_por_hora": 76.04,
  // ... outros campos
}
```

## 🛡️ **Tratamento de Erros**

### **Arquivo Não Reconhecido**
```
⚠️ Frente não identificada no arquivo, usando Frente03 como padrão
```
- **Solução**: Renomear arquivo para incluir padrão reconhecido

### **Configuração Ausente**
```
⚠️ Frente Frente04 identificada mas sem configuração de toneladas
```
- **Solução**: Verificar se a variável está definida corretamente

### **Erro Geral**
```
❌ Erro ao identificar frente: [erro]
```
- **Fallback**: Usa `TONELADAS_FRENTE_03` como padrão

## 📈 **Cenários de Uso**

### **Cenário 1: Processamento Único**
```python
# Configurar para uma frente específica
TONELADAS_FRENTE_04 = 1800
# Processar apenas: colhedorasFrente04_05082025.zip
```

### **Cenário 2: Processamento em Lote**
```python
# Configurar todas as frentes
TONELADAS_FRENTE_03 = 1200
TONELADAS_FRENTE_04 = 1500  
TONELADAS_FRENTE_08 = 1800
TONELADAS_FRENTE_ZIRLENO = 1000
# Processar múltiplos arquivos automaticamente
```

### **Cenário 3: Ajuste Dinâmico**
```python
# Ajustar conforme produção real do dia
TONELADAS_FRENTE_03 = 1350   # Produção acima da média
TONELADAS_FRENTE_04 = 1200   # Produção abaixo da média
```

## 🔄 **Compatibilidade com Função Anterior**

### **Modo Manual (Mantido)**
```python
# Ainda é possível forçar um valor específico
calcular_producao_por_frota(df, toneladas_totais=2000)
```

### **Modo Automático (Novo)**
```python
# Identificação automática baseada no arquivo
calcular_producao_por_frota(df, caminho_arquivo=caminho)
```

## ✅ **Verificação da Implementação**

### **1. Configurações Corretas**
- ✅ Variáveis definidas no topo do arquivo
- ✅ Valores numéricos válidos
- ✅ Mapeamento no dicionário `TONELADAS_POR_FRENTE`

### **2. Funcionamento**
- ✅ Identificação automática da frente pelo nome do arquivo
- ✅ Uso da configuração específica da frente
- ✅ Fallback para Frente03 em caso de erro

### **3. Logs de Confirmação**
- ✅ Exibe frente identificada
- ✅ Mostra toneladas utilizadas
- ✅ Confirma cálculos realizados

## 🎉 **Benefícios da Nova Implementação**

1. **🎯 Precisão**: Cada frente usa sua produção real
2. **🚀 Automação**: Identificação automática sem intervenção
3. **🔧 Flexibilidade**: Configuração simples e clara
4. **🛡️ Robustez**: Tratamento de erros e fallbacks
5. **📊 Rastreabilidade**: Logs detalhados do processo

**Status: ✅ Implementado e Testado**
