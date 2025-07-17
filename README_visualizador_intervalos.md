# Visualizador de Intervalos Operacionais

## 📊 Sobre o Gráfico

O **Gráfico de Gantt** (ou Timeline Chart) é uma ferramenta de visualização que mostra atividades ao longo do tempo usando barras horizontais. Cada barra representa um intervalo operacional com:

- **Posição horizontal**: Horário de início e duração
- **Posição vertical**: Tipo de operação
- **Cor**: Classificação do intervalo

## 🎨 Configuração Visual

### Posições Verticais:
- **Produtivo** (verde): Linha superior (y=1)
- **Disponível** (azul claro): Linha central (y=0)
- **Manutenção** (vermelho): Linha inferior (y=-1)

### Cores:
- 🟢 **Produtivo**: `#51CF66` (verde)
- 🔵 **Disponível**: `#74C0FC` (azul claro)
- 🔴 **Manutenção**: `#FF6B6B` (vermelho)

### Régua de Tempo:
- Eixo X: 24 horas (00:00 às 24:00)
- Marcações: A cada 2 horas
- Unidade: Minutos (convertido automaticamente)

## 🚀 Como Usar

### Método 1: Processar Todos os Arquivos
```bash
python scripts/visualizador_intervalos.py
```

Este comando:
1. Encontra todos os arquivos `*_processado.xlsx` na pasta `output/`
2. Lê a planilha "Intervalos" de cada arquivo
3. Cria um gráfico de Gantt para cada equipamento
4. Salva os gráficos na pasta `output/graficos/`

### Método 2: Teste com Equipamento Específico
```bash
python scripts/teste_grafico_unico.py
```

Este comando:
- Cria um gráfico de exemplo para o equipamento 7042
- Salva como `gantt_7042_teste.png`
- Útil para testes e ajustes

## 📁 Estrutura de Arquivos

```
output/
├── graficos/
│   ├── gantt_intervalos_7042_15-07-2025.png
│   ├── gantt_intervalos_7029_15-07-2025.png
│   └── ...
├── colhedorasFrente03_15072025_processado.xlsx
├── colhedorasFrente08_15072025_processado.xlsx
└── ...
```

## 📋 Requisitos

### Dependências Python:
```bash
pip install pandas matplotlib numpy openpyxl
```

### Dados Necessários:
- Arquivos Excel processados com planilha "Intervalos"
- Colunas obrigatórias na planilha:
  - `Equipamento`: Nome/ID do equipamento
  - `Tipo`: Classificação (Produtivo, Disponível, Manutenção)
  - `Início`: Hora de início (HH:MM:SS)
  - `Fim`: Hora de fim (HH:MM:SS)
  - `Duração (horas)`: Duração em horas
  - `Data`: Data do registro (opcional)

## 🔧 Personalização

### Modificar Cores:
```python
cores = {
    'Manutenção': '#FF6B6B',    # Vermelho
    'Disponível': '#74C0FC',    # Azul claro
    'Produtivo': '#51CF66'      # Verde
}
```

### Modificar Posições:
```python
posicoes_y = {
    'Manutenção': -1,    # Abaixo
    'Disponível': 0,     # Centro
    'Produtivo': 1       # Acima
}
```

### Modificar Tamanho da Figura:
```python
plt.figure(figsize=(16, 8))  # Largura x Altura
```

## 📊 Interpretação do Gráfico

### Análise Visual:
1. **Densidade de barras**: Mais intervalos = mais mudanças de estado
2. **Comprimento das barras**: Duração dos intervalos
3. **Distribuição vertical**: Proporção entre tipos de operação
4. **Gaps horizontais**: Períodos sem registros

### Métricas Importantes:
- **Tempo produtivo**: Soma das barras verdes
- **Tempo disponível**: Soma das barras azuis
- **Tempo manutenção**: Soma das barras vermelhas
- **Eficiência**: Proporção produtivo/total

## 🎯 Casos de Uso

### Análise de Eficiência:
- Identificar períodos de baixa produtividade
- Comparar performance entre equipamentos
- Visualizar padrões de manutenção

### Planejamento Operacional:
- Otimizar horários de manutenção
- Identificar gargalos operacionais
- Planejar turnos de trabalho

### Relatórios Gerenciais:
- Apresentar dados visuais para gestores
- Demonstrar utilização de equipamentos
- Justificar investimentos em manutenção

## 🐛 Troubleshooting

### Erro: "Nenhum arquivo encontrado"
- Verificar se os arquivos `*_processado.xlsx` estão na pasta `output/`
- Confirmar que a planilha "Intervalos" existe nos arquivos

### Erro: "Equipamento não encontrado"
- Verificar nome/ID do equipamento na planilha
- Confirmar se há dados para o equipamento selecionado

### Gráfico não abre:
- Verificar se matplotlib está instalado
- Verificar se há dados válidos na planilha
- Confirmar formato das colunas de hora (HH:MM:SS)

## 📞 Suporte

Para dúvidas ou problemas:
1. Verificar se todas as dependências estão instaladas
2. Confirmar formato dos dados de entrada
3. Verificar logs de erro no terminal
4. Testar com o script de exemplo (`teste_grafico_unico.py`)

---

**Desenvolvido para análise de intervalos operacionais em equipamentos agrícolas** 🚜 