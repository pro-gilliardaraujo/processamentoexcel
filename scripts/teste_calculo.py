"""
Script de teste para validar o cálculo de Diferença_Hora usando o método do Codigo_Base_TT.py
"""

import pandas as pd
import os

# Caminho do arquivo de teste
caminho_txt = r"D:\Projetos\IB\2_NOVAPLATAFORMA\processamentoexcel\dados\transbordosSemanalFrente1-teste.txt"

try:
    # Leitura do arquivo
    df = pd.read_csv(caminho_txt, sep=';', encoding='utf-8')
    print(f"Arquivo lido com sucesso! Total de linhas: {len(df)}")
    
    # Separar Data/Hora
    if 'Data/Hora' in df.columns:
        df[['Data', 'Hora']] = df['Data/Hora'].str.split(' ', expand=True)
        df = df.drop(columns=['Data/Hora'])
    
    # Conversão de 'Motor Ligado'
    for col in ['Motor Ligado']:
        if col in df.columns:
            df[col] = df[col].replace({1: 'LIGADO', 0: 'DESLIGADO'})
    
    # Convertendo Hora para datetime
    df['Hora'] = pd.to_datetime(df['Hora'], format='%H:%M:%S', errors='coerce')
    
    # Método de Codigo_Base_TT.py para cálculo de Diferença_Hora
    df['Diferença_Hora_TT'] = pd.to_datetime(df['Hora'], format='%H:%M:%S').diff()
    df['Diferença_Hora_TT'] = pd.to_timedelta(df['Diferença_Hora_TT'], errors='coerce')
    df['Diferença_Hora_TT'] = df['Diferença_Hora_TT'].dt.total_seconds() / 3600  # Conversor para horas.
    df['Diferença_Hora_TT'] = df['Diferença_Hora_TT'].apply(lambda x: x if x >= 0 else 0)
    
    # Método original do processamento_completo_transbordos.py
    # Ordenar os dados
    df = df.sort_values(by=['Equipamento', 'Data', 'Hora'])
    
    # Calcular a diferença de hora usando a lógica original
    df['Diferença_Hora_Original'] = 0.0
    equipamentos = df['Equipamento'].unique()
    
    for equipamento in equipamentos:
        # Filtrar dados deste equipamento
        mask = df['Equipamento'] == equipamento
        # Calcular diferenças 
        df.loc[mask, 'Diferença_Hora_Original'] = df.loc[mask, 'Hora'].diff().dt.total_seconds() / 3600
        # Aplicar regras
        df.loc[mask, 'Diferença_Hora_Original'] = df.loc[mask, 'Diferença_Hora_Original'].apply(lambda x: max(x, 0))
        # Nova regra: se Diferença_Hora > 0.50, então 0
        df.loc[mask, 'Diferença_Hora_Original'] = df.loc[mask, 'Diferença_Hora_Original'].apply(lambda x: 0 if x > 0.50 else x)
    
    # Calcular somas e exibir diferenças
    soma_tt = df['Diferença_Hora_TT'].sum()
    soma_original = df['Diferença_Hora_Original'].sum()
    
    print(f"\nRESULTADOS DO TESTE:")
    print(f"Soma do método Codigo_Base_TT.py: {soma_tt:.8f} horas")
    print(f"Soma do método original: {soma_original:.8f} horas")
    print(f"Diferença: {soma_tt - soma_original:.8f} horas")
    
    # Verificar linhas com grandes diferenças
    df['Diferença_Abs'] = (df['Diferença_Hora_TT'] - df['Diferença_Hora_Original']).abs()
    linhas_diferentes = df[df['Diferença_Abs'] > 0.01].sort_values(by='Diferença_Abs', ascending=False)
    
    if len(linhas_diferentes) > 0:
        print(f"\nEncontradas {len(linhas_diferentes)} linhas com diferenças significativas (>0.01 hora)")
        print("Primeiras 5 linhas com maiores diferenças:")
        for _, row in linhas_diferentes.head(5).iterrows():
            print(f"Equipamento: {row['Equipamento']}, Data: {row['Data']}, Hora: {row['Hora']}")
            print(f"  Método TT: {row['Diferença_Hora_TT']:.8f}, Método Original: {row['Diferença_Hora_Original']:.8f}")
            print(f"  Diferença: {row['Diferença_Abs']:.8f}")
    
    # Verificar se a regra "se > 0.50, então 0" é a principal causa da diferença
    df_sem_regra = df.copy()
    for equipamento in equipamentos:
        mask = df_sem_regra['Equipamento'] == equipamento
        df_sem_regra.loc[mask, 'Diferença_Hora_Original'] = df_sem_regra.loc[mask, 'Hora'].diff().dt.total_seconds() / 3600
        df_sem_regra.loc[mask, 'Diferença_Hora_Original'] = df_sem_regra.loc[mask, 'Diferença_Hora_Original'].apply(lambda x: max(x, 0))
        # Sem aplicar a regra "se > 0.50, então 0"
    
    soma_sem_regra = df_sem_regra['Diferença_Hora_Original'].sum()
    print(f"\nSoma sem aplicar regra '> 0.50 => 0': {soma_sem_regra:.8f} horas")
    print(f"Impacto da regra: {soma_sem_regra - soma_original:.8f} horas")
    
    # Contar quantos registros são zerados por esta regra
    zerados_por_regra = len(df_sem_regra[df_sem_regra['Diferença_Hora_Original'] > 0.50])
    print(f"Número de registros zerados pela regra '> 0.50 => 0': {zerados_por_regra}")
    print(f"Isto representa {zerados_por_regra / len(df) * 100:.2f}% do total de {len(df)} registros.")
    
except Exception as e:
    print(f"Erro durante o teste: {str(e)}") 