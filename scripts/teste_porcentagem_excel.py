import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# Criar DataFrame com valores decimais (0-1)
df = pd.DataFrame({
    'Valor Decimal (0-1)': [0.25, 0.5, 0.75],
    'Valor Percentual (0-100)': [25, 50, 75],
    'Texto com %': ['25%', '50%', '75%']
})

print("DataFrame criado:")
print(df)

# Salvar para Excel
arquivo = 'teste_formatos_porcentagem.xlsx'
with pd.ExcelWriter(arquivo, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Teste', index=False)
    
    # Aplicar formatação
    workbook = writer.book
    worksheet = workbook['Teste']
    
    # Formatar colunas com diferentes formatos de porcentagem
    for row in range(2, len(df) + 2):  # +2 porque o Excel é 1-indexado e temos um cabeçalho
        # Coluna A - Formato porcentagem para valor decimal (0-1)
        cell = worksheet.cell(row=row, column=2)  # Coluna A
        cell.number_format = '0.00%'  # Formato de porcentagem com 2 casas decimais
        
        # Coluna B - Formato porcentagem para valor percentual (0-100)
        cell = worksheet.cell(row=row, column=3)  # Coluna B
        # Converter para decimal (dividir por 100)
        valor = float(cell.value) / 100  # Converter explicitamente para float
        cell.value = valor
        cell.number_format = '0.00%'  # Formato de porcentagem com 2 casas decimais

print(f"Arquivo '{arquivo}' criado com sucesso!")
print("Abra o arquivo no Excel e selecione cada célula para ver como aparece na barra de fórmulas.") 