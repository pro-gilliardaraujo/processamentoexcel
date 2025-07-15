import pandas as pd
import openpyxl
from openpyxl.styles import numbers

# Criar um DataFrame simples com valores decimais (0-1)
df = pd.DataFrame({
    'Valores': [0.25, 0.5, 0.75]
})

print("DataFrame criado:")
print(df)

# Salvar para Excel
arquivo = 'teste_simples.xlsx'
df.to_excel(arquivo, index=False)

# Abrir o arquivo Excel para formatar
wb = openpyxl.load_workbook(arquivo)
ws = wb.active

# Aplicar formato de porcentagem às células
for row in range(2, len(df) + 2):  # +2 porque o Excel é 1-indexado e temos um cabeçalho
    cell = ws.cell(row=row, column=1)
    cell.number_format = '0.00%'

# Salvar as alterações
wb.save(arquivo)

print(f"Arquivo '{arquivo}' criado com sucesso!")
print("Abra o arquivo no Excel e verifique que os valores são mostrados como porcentagens")
print("mas na barra de fórmulas aparecem como decimais (0-1).") 