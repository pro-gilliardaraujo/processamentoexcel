import pandas as pd
from openpyxl import load_workbook
import numpy as np

caminho_txt = r"D:\Projetos\IB\2_NOVAPLATAFORMA\processamentoexcel\dados\transbordosSemanalFrente1-teste.txt"
caminho_excel = r"D:\Projetos\IB\2_NOVAPLATAFORMA\processamentoexcel\dados\transbordosSemanalFrente1-teste-precisao-completa.xlsx"

try:
    df = pd.read_csv(caminho_txt, sep=';', encoding='utf-8')
    print("Arquivo lido com sucesso!")
except Exception as e:
    print(f"Ocorreu um erro ao ler o arquivo: {e}")
    exit()

# Exibindo as colunas antes de reordenar
print(f"Colunas do DataFrame antes de reordenar: {df.columns}")

# Separando 'Data/Hora' em 'Data' e 'Hora'
df[['Data', 'Hora']] = df['Data/Hora'].str.split(' ', expand=True)
df = df.drop(columns=['Data/Hora'])

# Continuando o processamento conforme o seu código original
for col in ['Motor Ligado']:
    if col in df.columns:
        df[col] = df[col].replace({1: 'LIGADO', 0: 'DESLIGADO'})

# Criando a coluna 'Parado com motor ligado'
df['Parado com motor ligado'] = (df['Velocidade'] == 0) & (df['Motor Ligado'] == 'LIGADO')

# Reordenando as colunas conforme solicitado
ordem_desejada = [
    'Data', 'Hora', 'Equipamento', 'Descricao Equipamento', 'Estado', 'Estado Operacional', 
    'Grupo Equipamento/Frente', 'Grupo Operacao', 'Horimetro', 'Motor Ligado', 'Operacao', 'Operador', 
    'RPM Motor', 'Tipo de Equipamento', 'Velocidade', 'Parado com motor ligado'
]

# Garantir que a ordem desejada seja aplicada
df = df[ordem_desejada]

# Removendo as colunas especificadas
colunas_remover = ['Unidade', 'Centro de Custo', 'Fazenda', 'Zona', 'Talhao']
df = df.drop(columns=colunas_remover, errors='ignore')

# Calcular Diferença_Hora sem arredondamentos para preservar precisão total
df['Diferença_Hora'] = pd.to_datetime(df['Hora'], format='%H:%M:%S').diff()
df['Diferença_Hora'] = pd.to_timedelta(df['Diferença_Hora'], errors='coerce')
df['Diferença_Hora'] = df['Diferença_Hora'].dt.total_seconds() / 3600  # Conversor para horas.
df['Diferença_Hora'] = df['Diferença_Hora'].apply(lambda x: x if x >= 0 else 0)

# Calcular Horas Produtivas sem arredondamentos, preservando toda a precisão
df['Horas Produtivas'] = df.apply(lambda row: row['Diferença_Hora'] if row['Grupo Operacao'] == 'Produtiva' else 0, axis=1)

# Salvando o DataFrame com todos os valores originais sem arredondamentos
try:
    # Criar o Excel Writer usando openpyxl como engine
    writer = pd.ExcelWriter(caminho_excel, engine='openpyxl')
    
    # Escrever o DataFrame sem índice
    df.to_excel(writer, index=False, sheet_name='Dados')
    
    # Obter o objeto workbook e worksheet
    workbook = writer.book
    worksheet = writer.sheets['Dados']
    
    # Adicionar formato específico para a coluna "Diferença_Hora" para exibir mais casas decimais
    if 'Diferença_Hora' in df.columns:
        col_idx = list(df.columns).index('Diferença_Hora') + 1  # +1 porque openpyxl usa índice 1-based
        for row in range(2, len(df) + 2):  # +2 porque temos cabeçalho e openpyxl é 1-based
            cell = worksheet.cell(row=row, column=col_idx)
            cell.number_format = '0.00000000'  # Exibir 8 casas decimais
    
    # Salvar o arquivo
    writer.close()
    
    print(f"Arquivo salvo com sucesso em {caminho_excel}")
    print(f"Total de horas calculadas (soma de Diferença_Hora): {df['Diferença_Hora'].sum():.8f}")
    print(f"Total de horas produtivas: {df['Horas Produtivas'].sum():.8f}")
except Exception as e:
    print(f"Ocorreu um erro ao salvar o arquivo: {e}")