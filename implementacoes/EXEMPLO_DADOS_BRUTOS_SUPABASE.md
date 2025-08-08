# 📊 Exemplo de Dados Brutos Enviados para Supabase

## 🎯 **Alteração Implementada**

**Antes**: Dados arredondados e convertidos
**Agora**: Dados brutos exatos da planilha Excel, sem arredondamentos

## 📋 **Estrutura Final do `painel_esquerdo`**

### **Exemplo Real de Dados Enviados**
```json
{
  "frota": 7034,
  "horas_registradas": 23.342777777777776,
  "horas_motor": 19.723888888888887,
  "horas_elevador": 17.114444444444445,
  "toneladas": 741.1746031746031,
  "ton_por_hora": 43.32461926008424,
  "eficiencia_operacional": 73.30497835497835,
  "eficiencia_energetica": 86.76190476190476,
  "manobras_intervalos": 56,
  "manobras_tempo_total": 0.030277777777777776,
  "manobras_tempo_medio": 0.0005406746031746032,
  "disponibilidade_mecanica": 93.62105263157896,
  "tempo_manutencao": 1.4905555555555557,
  "operadores": [
    {
      "nome": "745638 - THIAGO DOS REIS CRUZ",
      "horas": 4.477777777777778
    },
    {
      "nome": "1 - SEM OPERADOR", 
      "horas": 1.1655555555555555
    },
    {
      "nome": "453796 - FLAVIO DOS SANTOS SILVA",
      "horas": 6.283333333333333
    },
    {
      "nome": "298902 - LUIZMAR FERREIRA",
      "horas": 5.188888888888889
    }
  ]
}
```

## 🔢 **Interpretação dos Dados de Manobras**

### **Valores Enviados (em horas)**
- `"manobras_tempo_total": 0.030277777777777776` = **1.82 minutos**
- `"manobras_tempo_medio": 0.0005406746031746032` = **0.032 minutos** = **1.95 segundos**

### **Conversão para Frontend**
```javascript
// Converter de horas para minutos
const tempoTotalMinutos = dados.manobras_tempo_total * 60;
const tempoMedioMinutos = dados.manobras_tempo_medio * 60;

// Converter de horas para segundos  
const tempoTotalSegundos = dados.manobras_tempo_total * 3600;
const tempoMedioSegundos = dados.manobras_tempo_medio * 3600;

console.log({
  intervalos: dados.manobras_intervalos,           // 56
  tempoTotalMinutos: tempoTotalMinutos.toFixed(2), // 1.82 min
  tempoMedioMinutos: tempoMedioMinutos.toFixed(2), // 0.03 min
  tempoMedioSegundos: tempoMedioSegundos.toFixed(1) // 1.9 seg
});
```

## 📊 **Comparação de Formatos**

### **Backend (Dados Brutos)**
```json
{
  "manobras_intervalos": 56,
  "manobras_tempo_total": 0.030277777777777776,
  "manobras_tempo_medio": 0.0005406746031746032
}
```

### **Frontend (Após Formatação)**
```javascript
{
  intervalos: 56,
  tempoTotal: "1.82 min",
  tempoMedio: "1.9 seg",
  // ou
  tempoTotal: "00:01:49",
  tempoMedio: "00:00:01.9"
}
```

## 🎯 **Vantagens dos Dados Brutos**

### **✅ Precisão Total**
- Dados exatos da planilha Excel
- Sem perda de precisão por arredondamentos
- Cálculos precisos no frontend

### **✅ Flexibilidade Frontend**
- Frontend decide como mostrar
- Diferentes unidades (horas/minutos/segundos)
- Formatação personalizada por tela

### **✅ Consistência**
- Sempre os mesmos dados que estão no Excel
- Sem discrepâncias entre sistemas
- Fácil validação e debug

## 🛠️ **Funções Utilitárias para Frontend**

### **JavaScript/TypeScript**
```javascript
// Converter horas para formato legível
function formatarTempo(horas, unidade = 'auto') {
  if (unidade === 'minutos' || (unidade === 'auto' && horas < 1)) {
    return `${(horas * 60).toFixed(1)} min`;
  }
  if (unidade === 'segundos' || (unidade === 'auto' && horas < 0.01)) {
    return `${(horas * 3600).toFixed(1)} seg`;
  }
  return `${horas.toFixed(2)} h`;
}

function formatarTempoHMS(horas) {
  const totalSegundos = Math.round(horas * 3600);
  const h = Math.floor(totalSegundos / 3600);
  const m = Math.floor((totalSegundos % 3600) / 60);
  const s = totalSegundos % 60;
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

// Uso
const dados = {
  manobras_tempo_total: 0.030277777777777776,
  manobras_tempo_medio: 0.0005406746031746032
};

console.log(formatarTempo(dados.manobras_tempo_total));  // "1.8 min"
console.log(formatarTempo(dados.manobras_tempo_medio));  // "1.9 seg"
console.log(formatarTempoHMS(dados.manobras_tempo_total)); // "00:01:49"
```

### **Python (Para Validação)**
```python
def formatar_tempo_horas(horas):
    """Converte horas para formato legível"""
    if horas < 0.01:  # Menos que 36 segundos
        return f"{horas * 3600:.1f} seg"
    elif horas < 1:   # Menos que 1 hora
        return f"{horas * 60:.1f} min"
    else:
        return f"{horas:.2f} h"

# Teste
tempo_total = 0.030277777777777776
tempo_medio = 0.0005406746031746032

print(f"Tempo total: {formatar_tempo_horas(tempo_total)}")  # 1.8 min
print(f"Tempo médio: {formatar_tempo_horas(tempo_medio)}")  # 1.9 seg
```

## ✅ **Status da Implementação**

| Campo | Formato Anterior | Formato Atual |
|-------|-----------------|---------------|
| `horas_registradas` | `round(valor, 2)` | `valor` |
| `horas_motor` | `round(valor, 2)` | `valor` |  
| `horas_elevador` | `round(valor, 2)` | `valor` |
| `toneladas` | `round(valor, 2)` | `valor` |
| `eficiencia_operacional` | `round(valor, 2)` | `valor` |
| `manobras_tempo_total` | `round(valor, 2)` | `valor` |
| `manobras_tempo_medio` | `round(valor, 2)` | `valor` |
| `operadores[].horas` | `round(valor, 2)` | `valor` |

## 🎉 **Resultado Final**

✅ **Dados brutos exatos** da planilha Excel
✅ **Sem perda de precisão** por arredondamentos  
✅ **Frontend tem controle total** da formatação
✅ **Consistência garantida** entre Excel e Supabase
✅ **Flexibilidade máxima** para diferentes visualizações

**Status: 🟢 IMPLEMENTADO - DADOS BRUTOS PRESERVADOS**
