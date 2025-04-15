"""
Script para testar o processamento completo e comparar os resultados
entre Codigo_Base_TT.py e processamento_completo_transbordos.py
"""

import pandas as pd
import sys
import os

# Adicionando o diretório pai ao path para importar corretamente
sys.path.append(os.path.abspath('..'))
from scripts.processamento_completo_transbordos import processar_arquivo_base

# Caminho do arquivo de teste
caminho_txt = r"D:\Projetos\IB\2_NOVAPLATAFORMA\processamentoexcel\dados\transbordosSemanalFrente1-teste.txt"

# Teste do Codigo_Base_TT.py
def teste_codigo_base_tt():
    try:
        # Leitura do arquivo
        df = pd.read_csv(caminho_txt, sep=';', encoding='utf-8')
        print(f"Arquivo lido com sucesso (Codigo_Base_TT)! Total de linhas: {len(df)}")
        
        # Separando 'Data/Hora' em 'Data' e 'Hora'
        df[['Data', 'Hora']] = df['Data/Hora'].str.split(' ', expand=True)
        df = df.drop(columns=['Data/Hora'])
        
        # Convertendo para LIGADO/DESLIGADO
        for col in ['Motor Ligado']:
            if col in df.columns:
                df[col] = df[col].replace({1: 'LIGADO', 0: 'DESLIGADO'})
        
        # Criando a coluna 'Parado com motor ligado'
        df['Parado com motor ligado'] = (df['Velocidade'] == 0) & (df['Motor Ligado'] == 'LIGADO')
        
        # Calcular Diferença_Hora sem arredondamentos
        df['Hora'] = pd.to_datetime(df['Hora'], format='%H:%M:%S')
        df['Diferença_Hora'] = pd.to_datetime(df['Hora'], format='%H:%M:%S').diff()
        df['Diferença_Hora'] = pd.to_timedelta(df['Diferença_Hora'], errors='coerce')
        df['Diferença_Hora'] = df['Diferença_Hora'].dt.total_seconds() / 3600  # Conversor para horas.
        df['Diferença_Hora'] = df['Diferença_Hora'].apply(lambda x: x if x >= 0 else 0)
        
        # Calcular Horas Produtivas
        df['Horas Produtivas'] = df.apply(lambda row: row['Diferença_Hora'] if row['Grupo Operacao'] == 'Produtiva' else 0, axis=1)
        
        return df
    except Exception as e:
        print(f"Erro no teste_codigo_base_tt: {str(e)}")
        return None

# Teste do processamento_completo_transbordos.py
def teste_processamento_completo():
    try:
        # Usar a função processar_arquivo_base do módulo
        df = processar_arquivo_base(caminho_txt)
        print(f"Arquivo processado com sucesso (processamento_completo)! Total de linhas: {len(df)}")
        
        return df
    except Exception as e:
        print(f"Erro no teste_processamento_completo: {str(e)}")
        return None

# Executar os testes
df_tt = teste_codigo_base_tt()
df_pc = teste_processamento_completo()

# Comparar resultados
if df_tt is not None and df_pc is not None:
    soma_tt = df_tt['Diferença_Hora'].sum()
    soma_pc = df_pc['Diferença_Hora'].sum()
    
    print("\nRESULTADOS DO TESTE:")
    print(f"Total de horas calculadas por Codigo_Base_TT.py: {soma_tt:.8f}")
    print(f"Total de horas calculadas por processamento_completo_transbordos.py: {soma_pc:.8f}")
    print(f"Diferença: {soma_tt - soma_pc:.8f}")
    
    # Verificar se as colunas são as mesmas
    colunas_tt = set(df_tt.columns)
    colunas_pc = set(df_pc.columns)
    
    print("\nCOLUNAS:")
    print(f"Colunas em Codigo_Base_TT.py: {len(colunas_tt)}")
    print(f"Colunas em processamento_completo_transbordos.py: {len(colunas_pc)}")
    
    colunas_apenas_tt = colunas_tt - colunas_pc
    colunas_apenas_pc = colunas_pc - colunas_tt
    
    if colunas_apenas_tt:
        print(f"\nColunas apenas em Codigo_Base_TT.py: {colunas_apenas_tt}")
    
    if colunas_apenas_pc:
        print(f"\nColunas apenas em processamento_completo_transbordos.py: {colunas_apenas_pc}")
    
else:
    print("Não foi possível comparar os resultados devido a erros no processamento.") 