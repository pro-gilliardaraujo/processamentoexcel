import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# Criar DataFrame com valores decimais (0-1)
df = pd.DataFrame({
    'Valor': [0.25, 0.5, 0.75],
    'Descrição': ['25%', '50%', '75%']
})

print("DataFrame criado:")
print(df)

# Salvar para Excel
arquivo = 'teste_porcentagem.xlsx'
with pd.ExcelWriter(arquivo, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Teste', index=False)
    
    # Aplicar formatação
    workbook = writer.book
    worksheet = workbook['Teste']
    
    # Formatar coluna Valor como porcentagem
    for row in range(2, len(df) + 2):  # +2 porque o Excel é 1-indexado e temos um cabeçalho
        cell = worksheet.cell(row=row, column=1)  # Coluna A (Valor)
        cell.number_format = '0.00%'  # Formato de porcentagem com 2 casas decimais

print(f"Arquivo '{arquivo}' criado com sucesso!") 