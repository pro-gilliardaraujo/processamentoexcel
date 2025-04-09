"""
Script para processamento de dados de monitoramento de colhedoras.
Converte arquivo TXT para Excel e realiza transformações nos dados.
"""

import pandas as pd
from pathlib import Path
from openpyxl import load_workbook

# Constantes
COLUNAS_REMOVER = [
    'Justificativa Corte Base Desligado',
    'Latitude',
    'Longitude',
    'Regional',
    'Tipo de Equipamento',
    'Unidade',
    'Centro de Custo'
]

COLUNAS_DESEJADAS = [
    'Data', 'Hora', 'Equipamento', 'Apertura do Rolo', 'Codigo da Operacao',
    'Codigo Frente (digitada)', 'Corporativo', 'Corte Base Automatico/Manual',
    'Descricao Equipamento', 'Estado', 'Estado Operacional', 'Esteira Ligada',
    'Field Cruiser', 'Grupo Equipamento/Frente', 'Grupo Operacao', 'Horimetro',
    'Implemento Ligado', 'Motor Ligado', 'Operacao', 'Operador', 'Pressao de Corte',
    'RPM Extrator', 'RPM Motor', 'RTK (Piloto Automatico)', 'Fazenda', 'Zona',
    'Talhao', 'Velocidade', 'Diferença_Hora', 'Parada com Motor Ligado',
    'Horas Produtivas'
]

def processar_arquivo(caminho_txt, caminho_excel):
    """
    Processa o arquivo TXT e salva como Excel com as transformações necessárias.
    
    Args:
        caminho_txt (str): Caminho do arquivo TXT de entrada
        caminho_excel (str): Caminho do arquivo Excel de saída
    """
    try:
        # Leitura do arquivo
        df = pd.read_csv(caminho_txt, sep=';', encoding='utf-8')
        print(f"Arquivo lido com sucesso! Total de linhas: {len(df)}")
        
        # Processamento de data e hora
        df[['Data', 'Hora']] = df['Data/Hora'].str.split(' ', expand=True)
        df = df.drop(columns=['Data/Hora'])
        
        # Conversão e cálculo de diferenças de hora
        df['Hora'] = pd.to_datetime(df['Hora'], format='%H:%M:%S')
        df['Diferença_Hora'] = df['Hora'].diff().dt.total_seconds() / 3600
        df['Diferença_Hora'] = df['Diferença_Hora'].apply(lambda x: max(x, 0))
        
        # Nova regra: se Diferença_Hora > 0.50, então 0
        df['Diferença_Hora'] = df['Diferença_Hora'].apply(lambda x: 0 if x > 0.50 else x)
        
        # Cálculos adicionais
        RPM_MINIMO = 300  # Definindo constante para RPM mínimo
        df['Parada com Motor Ligado'] = ((df['Velocidade'] == 0) & (df['RPM Motor'] >= RPM_MINIMO)).astype(int)
        df['Horas Produtivas'] = df.apply(
            lambda row: row['Diferença_Hora'] if row['Grupo Operacao'] == 'Produtiva' else 0,
            axis=1
        )
        
        # Limpeza e organização das colunas
        df = df.drop(columns=COLUNAS_REMOVER, errors='ignore')
        df = df[COLUNAS_DESEJADAS]
        
        # Verificar dados antes de salvar
        print("\nResumo dos dados processados:")
        print(f"Total de registros: {len(df)}")
        print(f"Total de horas produtivas: {df['Horas Produtivas'].sum():.2f}")
        print("\nPrimeiras 5 linhas do DataFrame:")
        print(df.head())
        
        # Salvamento do arquivo
        df.to_excel(caminho_excel, index=False, engine='openpyxl')
        print(f"\nArquivo salvo com sucesso em {caminho_excel}")
        
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {caminho_txt}")
    except pd.errors.EmptyDataError:
        print("Erro: O arquivo está vazio")
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")

if __name__ == "__main__":
    # Caminhos dos arquivos
    caminho_txt = r"C:\Users\IB\Desktop\Gilliard\Arquivos Relatórios\1_TRATAMENTOS\frente04colhedoras0804.txt"
    caminho_excel = r"C:\Users\IB\Desktop\Gilliard\Arquivos Relatórios\1_TRATAMENTOS\frente04colhedoras0804.xlsx"
    
    processar_arquivo(caminho_txt, caminho_excel)
