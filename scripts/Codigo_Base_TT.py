import pandas as pd
from openpyxl import load_workbook

caminho_txt = r"C:\Users\IB\Desktop\Gilliard\Arquivos Relatórios\1_TRATAMENTOS\frente03transbordos0804.txt"
caminho_excel = r"C:\Users\IB\Desktop\Gilliard\Arquivos Relatórios\1_TRATAMENTOS\frente03transbordos0804.xlsx"

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

# Criando a coluna 'Parado com motor ligado'
df['Parado com motor ligado'] = (df['Velocidade'] == 0) & (df['Motor Ligado'] == 1)

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

# Continuando o processamento conforme o seu código original
for col in ['Motor Ligado']:
    if col in df.columns:
        df[col] = df[col].replace({1: 'LIGADO', 0: 'DESLIGADO'})
df['Diferença_Hora'] = pd.to_datetime(df['Hora'], format='%H:%M:%S').diff()
df['Diferença_Hora'] = pd.to_timedelta(df['Diferença_Hora'], errors='coerce')
df['Diferença_Hora'] = df['Diferença_Hora'].dt.total_seconds() / 3600  # Conversor para horas.
df['Diferença_Hora'] = df['Diferença_Hora'].apply(lambda x: x if x >= 0 else 0)
df['Horas Produtivas'] = df.apply(lambda row: row['Diferença_Hora'] if row['Grupo Operacao'] == 'Produtiva' else 0, axis=1)

# Salvando o DataFrame reordenado
try:
    df.to_excel(caminho_excel, index=False, engine='openpyxl')
    print(f"Arquivo salvo com sucesso em {caminho_excel}")
except Exception as e:
    print(f"Ocorreu um erro ao salvar o arquivo: {e}")