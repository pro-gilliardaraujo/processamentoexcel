"""
Script para análise de manobras de equipamentos agrícolas.
Processa dados de monitoramento para identificar e analisar padrões de manobra.
Suporta arquivos CSV na pasta dados/manobras.
Salva resultados na pasta output/manobras.
"""

import pandas as pd
import numpy as np
import os
import sys
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import zipfile
import tempfile
import shutil
import glob

def processar_arquivo_base(caminho_arquivo):
    """
    Processa o arquivo CSV e retorna um DataFrame.
    
    Args:
        caminho_arquivo (str): Caminho do arquivo a ser processado
        
    Returns:
        DataFrame: DataFrame com os dados processados ou None se houver erro
    """
    try:
        # Verificar se é um arquivo CSV
        if not caminho_arquivo.lower().endswith('.csv'):
            print(f"Aviso: Arquivo {caminho_arquivo} não é um arquivo CSV")
            return None
            
        # Ler apenas as colunas necessárias
        colunas_necessarias = ['Data/Hora', 'Operacao', 'Equipamento', 'Velocidade', 'Operador']
        df = pd.read_csv(caminho_arquivo, sep=';', usecols=colunas_necessarias)
        
        if df is None or df.empty:
            return None
            
        # Converter Data/Hora para datetime
        df['Data/Hora'] = pd.to_datetime(df['Data/Hora'], format='%d/%m/%Y %H:%M:%S')
        
        # Criar colunas separadas de Data e Hora
        df['Data'] = df['Data/Hora'].dt.date
        df['Hora'] = df['Data/Hora'].dt.time
        
        # Converter Velocidade para número (tratando formato brasileiro)
        df['Velocidade'] = df['Velocidade'].astype(str).str.replace(',', '.').astype(float)
        
        # Calcular Diferença_Hora
        df['Diferença_Hora'] = df['Data/Hora'].diff().dt.total_seconds() / 3600
        df['Diferença_Hora'] = df['Diferença_Hora'].fillna(0)
        
        # Corrigir valores negativos ou muito grandes
        df.loc[df['Diferença_Hora'] < 0, 'Diferença_Hora'] = 0
        df.loc[df['Diferença_Hora'] > 0.50, 'Diferença_Hora'] = 0  # Limitar a 30 minutos
        
        # Tratar valores nulos
        df['Velocidade'] = df['Velocidade'].fillna(0)
        df['Operador'] = df['Operador'].fillna('SEM OPERADOR')
        df['Operacao'] = df['Operacao'].fillna('SEM OPERACAO')
        
        print(f"Arquivo processado com sucesso. Total de linhas: {len(df)}")
        print(f"Colunas encontradas: {', '.join(df.columns)}")
        print("Amostra de dados processados:")
        print(df[['Data/Hora', 'Operacao', 'Velocidade']].head())
        
        return df
        
    except Exception as e:
        print(f"Erro ao processar arquivo {caminho_arquivo}: {str(e)}")
        print("Detalhes do erro:")
        import traceback
        traceback.print_exc()
        return None

def identificar_manobras(df):
    """
    Identifica manobras nos dados de monitoramento.
    
    Regras:
    1. Sequências de operações "MANOBRA" são consideradas como uma única manobra
    2. Ao encontrar uma operação diferente de "MANOBRA":
       - Se duração > 1 minuto: fecha o intervalo anterior
       - Se duração < 1 minuto: continua procurando próxima operação
       - Se não encontrar outra "MANOBRA" dentro de 1 minuto: fecha o intervalo
    
    Args:
        df (DataFrame): DataFrame com os dados de monitoramento
        
    Returns:
        DataFrame: DataFrame com as manobras identificadas e suas características
    """
    # Verificar se temos as colunas necessárias
    colunas_necessarias = ['Equipamento', 'Data/Hora', 'Operacao', 'Velocidade', 'Operador']
    if not all(col in df.columns for col in colunas_necessarias):
        print("Erro: Colunas necessárias não encontradas no DataFrame")
        print(f"Colunas esperadas: {colunas_necessarias}")
        print(f"Colunas encontradas: {df.columns.tolist()}")
        return pd.DataFrame()
    
    print("\nIniciando identificação de manobras...")
    
    # Ordenar dados por equipamento e data/hora
    df = df.sort_values(['Equipamento', 'Data/Hora'])
    
    # Lista para armazenar manobras identificadas
    manobras = []
    
    # Processar cada equipamento separadamente
    for equipamento in df['Equipamento'].unique():
        print(f"\nProcessando equipamento: {equipamento}")
        dados_equip = df[df['Equipamento'] == equipamento].copy()
        dados_equip = dados_equip.reset_index(drop=True)
        
        # Inicializar variáveis para detecção de manobras
        em_manobra = False
        inicio_manobra = None
        tempo_manobra = 0
        linhas_manobra = []
        tempo_desde_ultima_manobra = 0
        
        i = 0
        while i < len(dados_equip):
            linha_atual = dados_equip.iloc[i]
            
            # Verificar se é uma operação de manobra
            if 'MANOBRA' in str(linha_atual['Operacao']).upper():
                if not em_manobra:
                    # Início de uma nova sequência de manobras
                    em_manobra = True
                    inicio_manobra = linha_atual
                    tempo_manobra = linha_atual['Diferença_Hora']
                    linhas_manobra = [i]
                else:
                    # Continuar somando tempo da manobra
                    tempo_manobra += linha_atual['Diferença_Hora']
                    linhas_manobra.append(i)
                
                # Resetar o contador de tempo desde a última manobra
                tempo_desde_ultima_manobra = 0
                i += 1
            else:
                if em_manobra:
                    # Verificar se esta operação não-manobra fecha o intervalo
                    if linha_atual['Diferença_Hora'] > 1/60:  # Mais de 1 minuto
                        # Registrar a manobra anterior
                        if tempo_manobra > 0:
                            ultima_linha = dados_equip.iloc[linhas_manobra[-1]]
                            velocidades = dados_equip.iloc[linhas_manobra]['Velocidade']
                            manobras.append({
                                'Equipamento': equipamento,
                                'Data': inicio_manobra['Data'],
                                'Hora_Inicio': inicio_manobra['Data/Hora'],
                                'Hora_Fim': ultima_linha['Data/Hora'],
                                'Duracao': tempo_manobra,
                                'Velocidade_Media': velocidades.mean() if len(velocidades) > 0 else 0,
                                'Operador': inicio_manobra['Operador'],
                                'Linhas_Sequencia': len(linhas_manobra)
                            })
                            print(f"Manobra registrada: {inicio_manobra['Data/Hora']} - {ultima_linha['Data/Hora']}")
                        
                        # Resetar variáveis
                        em_manobra = False
                        inicio_manobra = None
                        tempo_manobra = 0
                        linhas_manobra = []
                        tempo_desde_ultima_manobra = 0
                        i += 1
                    else:
                        # Operação < 1 minuto, acumular tempo e continuar verificando
                        tempo_desde_ultima_manobra += linha_atual['Diferença_Hora']
                        
                        # Se passou mais de 1 minuto sem encontrar outra manobra, fechar o intervalo
                        if tempo_desde_ultima_manobra > 1/60:
                            if tempo_manobra > 0:
                                ultima_linha = dados_equip.iloc[linhas_manobra[-1]]
                                velocidades = dados_equip.iloc[linhas_manobra]['Velocidade']
                                manobras.append({
                                    'Equipamento': equipamento,
                                    'Data': inicio_manobra['Data'],
                                    'Hora_Inicio': inicio_manobra['Data/Hora'],
                                    'Hora_Fim': ultima_linha['Data/Hora'],
                                    'Duracao': tempo_manobra,
                                    'Velocidade_Media': velocidades.mean() if len(velocidades) > 0 else 0,
                                    'Operador': inicio_manobra['Operador'],
                                    'Linhas_Sequencia': len(linhas_manobra)
                                })
                                print(f"Manobra registrada: {inicio_manobra['Data/Hora']} - {ultima_linha['Data/Hora']}")
                            
                            # Resetar variáveis
                            em_manobra = False
                            inicio_manobra = None
                            tempo_manobra = 0
                            linhas_manobra = []
                            tempo_desde_ultima_manobra = 0
                        i += 1
                else:
                    i += 1
        
        # Verificar se há uma manobra em aberto no final do arquivo
        if em_manobra and tempo_manobra > 0:
            ultima_linha = dados_equip.iloc[linhas_manobra[-1]]
            velocidades = dados_equip.iloc[linhas_manobra]['Velocidade']
            manobras.append({
                'Equipamento': equipamento,
                'Data': inicio_manobra['Data'],
                'Hora_Inicio': inicio_manobra['Data/Hora'],
                'Hora_Fim': ultima_linha['Data/Hora'],
                'Duracao': tempo_manobra,
                'Velocidade_Media': velocidades.mean() if len(velocidades) > 0 else 0,
                'Operador': inicio_manobra['Operador'],
                'Linhas_Sequencia': len(linhas_manobra)
            })
            print(f"Manobra final registrada: {inicio_manobra['Data/Hora']} - {ultima_linha['Data/Hora']}")
    
    # Criar DataFrame com as manobras identificadas
    df_manobras = pd.DataFrame(manobras)
    
    # Adicionar informações adicionais
    if not df_manobras.empty:
        df_manobras['Periodo'] = df_manobras['Hora_Inicio'].dt.hour.map(
            lambda x: 'Manhã' if 6 <= x < 12 else
                     'Tarde' if 12 <= x < 18 else
                     'Noite' if 18 <= x < 24 else 'Madrugada'
        )
        
        # Adicionar métricas adicionais
        df_manobras['Duracao_Minutos'] = df_manobras['Duracao'] * 60
        
        print(f"\nTotal de manobras identificadas: {len(df_manobras)}")
    else:
        print("\nNenhuma manobra identificada")
    
    return df_manobras

def calcular_metricas_manobras(df_manobras):
    """
    Calcula métricas relacionadas às manobras identificadas.
    
    Args:
        df_manobras (DataFrame): DataFrame com as manobras identificadas
        
    Returns:
        dict: Dicionário com as métricas calculadas
    """
    metricas = {}
    
    if df_manobras.empty:
        return {
            'total_manobras': 0,
            'tempo_medio': 0,
            'tempo_total': 0,
            'manobras_por_periodo': {},
            'manobras_por_equipamento': {},
            'tempo_medio_por_equipamento': {},
            'manobras_por_operador': {},
            'operacoes_media': 0,
            'operacoes_max': 0,
            'distribuicao_duracao': {},
            'manobras_por_hora': {}
        }
    
    # Métricas gerais
    metricas['total_manobras'] = len(df_manobras)
    metricas['tempo_medio'] = df_manobras['Duracao'].mean()
    metricas['tempo_total'] = df_manobras['Duracao'].sum()
    
    # Métricas de operações por manobra
    metricas['operacoes_media'] = df_manobras['Linhas_Sequencia'].mean()
    metricas['operacoes_max'] = df_manobras['Linhas_Sequencia'].max()
    
    # Distribuição por período
    metricas['manobras_por_periodo'] = df_manobras['Periodo'].value_counts().to_dict()
    
    # Métricas por equipamento
    metricas['manobras_por_equipamento'] = df_manobras['Equipamento'].value_counts().to_dict()
    metricas['tempo_medio_por_equipamento'] = df_manobras.groupby('Equipamento')['Duracao'].mean().to_dict()
    
    # Métricas por operador
    metricas['manobras_por_operador'] = df_manobras.groupby('Operador').agg({
        'Equipamento': 'count',
        'Duracao': ['mean', 'sum'],
        'Linhas_Sequencia': 'mean'
    }).round(4)
    
    # Renomear as colunas agregadas para facilitar o acesso
    metricas['manobras_por_operador'].columns = ['quantidade', 'duracao_media', 'duracao_total', 'operacoes_media']
    metricas['manobras_por_operador'] = metricas['manobras_por_operador'].to_dict()
    
    # Distribuição da duração das manobras (em minutos)
    duracao_bins = [0, 1, 2, 3, 5, 10, float('inf')]
    duracao_labels = ['0-1', '1-2', '2-3', '3-5', '5-10', '10+']
    df_manobras['Faixa_Duracao'] = pd.cut(df_manobras['Duracao_Minutos'], 
                                         bins=duracao_bins, 
                                         labels=duracao_labels, 
                                         include_lowest=True)
    metricas['distribuicao_duracao'] = df_manobras['Faixa_Duracao'].value_counts().to_dict()
    
    # Manobras por hora do dia
    df_manobras['Hora'] = df_manobras['Hora_Inicio'].dt.hour
    metricas['manobras_por_hora'] = df_manobras.groupby('Hora').size().to_dict()
    
    return metricas

def criar_dashboard(df_manobras, metricas):
    """
    Cria uma dashboard interativa com Plotly Dash para visualização das métricas de manobra.
    
    Args:
        df_manobras (DataFrame): DataFrame com as manobras identificadas
        metricas (dict): Dicionário com as métricas calculadas
    """
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    # Layout da dashboard
    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Dashboard de Análise de Manobras", className="text-center mb-4"), width=12)
        ]),
        
        # Cards com métricas principais
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Total de Manobras", className="card-title"),
                        html.H2(f"{metricas['total_manobras']:,}", className="card-text text-center")
                    ])
                ]), width=3
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Tempo Médio (min)", className="card-title"),
                        html.H2(f"{metricas['tempo_medio']*60:.1f}", className="card-text text-center")
                    ])
                ]), width=3
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Tempo Total (h)", className="card-title"),
                        html.H2(f"{metricas['tempo_total']:.1f}", className="card-text text-center")
                    ])
                ]), width=3
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Média Operações/Manobra", className="card-title"),
                        html.H2(f"{metricas['operacoes_media']:.1f}", className="card-text text-center")
                    ])
                ]), width=3
            ),
        ], className="mb-4"),
        
        # Gráficos - Primeira linha
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Manobras por Período", className="card-title"),
                        dcc.Graph(
                            figure=go.Figure(
                                data=[go.Bar(
                                    x=list(metricas['manobras_por_periodo'].keys()),
                                    y=list(metricas['manobras_por_periodo'].values()),
                                    text=list(metricas['manobras_por_periodo'].values()),
                                    textposition='auto'
                                )],
                                layout=go.Layout(
                                    margin=dict(l=40, r=40, t=40, b=40),
                                    yaxis_title="Quantidade de Manobras"
                                )
                            )
                        )
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Distribuição da Duração das Manobras", className="card-title"),
                        dcc.Graph(
                            figure=go.Figure(
                                data=[go.Bar(
                                    x=list(metricas['distribuicao_duracao'].keys()),
                                    y=list(metricas['distribuicao_duracao'].values()),
                                    text=list(metricas['distribuicao_duracao'].values()),
                                    textposition='auto'
                                )],
                                layout=go.Layout(
                                    margin=dict(l=40, r=40, t=40, b=40),
                                    xaxis_title="Duração (minutos)",
                                    yaxis_title="Quantidade de Manobras"
                                )
                            )
                        )
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Gráficos - Segunda linha
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Manobras por Hora do Dia", className="card-title"),
                        dcc.Graph(
                            figure=go.Figure(
                                data=[go.Scatter(
                                    x=list(metricas['manobras_por_hora'].keys()),
                                    y=list(metricas['manobras_por_hora'].values()),
                                    mode='lines+markers',
                                    line=dict(shape='spline', smoothing=0.3)
                                )],
                                layout=go.Layout(
                                    margin=dict(l=40, r=40, t=40, b=40),
                                    xaxis_title="Hora do Dia",
                                    yaxis_title="Quantidade de Manobras"
                                )
                            )
                        )
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Tempo Médio por Equipamento (min)", className="card-title"),
                        dcc.Graph(
                            figure=go.Figure(
                                data=[go.Bar(
                                    x=list(metricas['tempo_medio_por_equipamento'].keys()),
                                    y=[x*60 for x in metricas['tempo_medio_por_equipamento'].values()],
                                    text=[f"{x*60:.1f}" for x in metricas['tempo_medio_por_equipamento'].values()],
                                    textposition='auto'
                                )],
                                layout=go.Layout(
                                    margin=dict(l=40, r=40, t=40, b=40),
                                    yaxis_title="Minutos"
                                )
                            )
                        )
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Tabela detalhada por operador
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Detalhes por Operador", className="card-title"),
                        html.Div([
                            dbc.Table.from_dataframe(
                                pd.DataFrame({
                                    'Operador': list(metricas['manobras_por_operador']['quantidade'].keys()),
                                    'Quantidade': list(metricas['manobras_por_operador']['quantidade'].values()),
                                    'Tempo Médio (min)': [x*60 for x in metricas['manobras_por_operador']['duracao_media'].values()],
                                    'Tempo Total (h)': list(metricas['manobras_por_operador']['duracao_total'].values()),
                                    'Média Operações': list(metricas['manobras_por_operador']['operacoes_media'].values())
                                }).round(2),
                                striped=True,
                                bordered=True,
                                hover=True
                            )
                        ])
                    ])
                ])
            ], width=12)
        ])
    ], fluid=True)
    
    return app

def criar_excel_com_planilhas(df_manobras, metricas, caminho_saida):
    """
    Cria um arquivo Excel com todas as planilhas de análise de manobras.
    
    Args:
        df_manobras (DataFrame): DataFrame com as manobras identificadas
        metricas (dict): Dicionário com as métricas calculadas
        caminho_saida (str): Caminho onde o arquivo Excel será salvo
    """
    with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
        # Salvar dados das manobras
        if not df_manobras.empty:
            # Converter tempos para formato Excel (dividir por 24 para formato de horas)
            df_manobras_excel = df_manobras.copy()
            df_manobras_excel['Duracao'] = df_manobras_excel['Duracao'] / 24  # Dividir por 24 para formato de horas
            df_manobras_excel.to_excel(writer, sheet_name='Manobras', index=False)
            
            # Formatar células de duração
            ws = writer.sheets['Manobras']
            for idx, col in enumerate(df_manobras_excel.columns, 1):
                if col == 'Duracao':
                    for row in range(2, len(df_manobras_excel) + 2):
                        ws.cell(row=row, column=idx).number_format = 'h:mm:ss'
        
        # Salvar métricas em formato tabular
        df_metricas = pd.DataFrame([{
            'Métrica': 'Total de Manobras',
            'Valor': metricas['total_manobras']
        }, {
            'Métrica': 'Tempo Médio',
            'Valor': metricas['tempo_medio'] / 24  # Dividir por 24 para formato de horas
        }, {
            'Métrica': 'Tempo Total',
            'Valor': metricas['tempo_total'] / 24  # Dividir por 24 para formato de horas
        }])
        
        df_metricas.to_excel(writer, sheet_name='Métricas Gerais', index=False)
        
        # Formatar células de tempo na planilha de métricas gerais
        ws = writer.sheets['Métricas Gerais']
        for row in range(2, 5):  # Linhas 2 a 4 (tempo médio e total)
            if df_metricas.iloc[row-2]['Métrica'] in ['Tempo Médio', 'Tempo Total']:
                ws.cell(row=row, column=2).number_format = 'h:mm:ss'
        
        # Salvar distribuição por período
        pd.DataFrame(metricas['manobras_por_periodo'].items(), 
                    columns=['Período', 'Quantidade']).to_excel(writer, sheet_name='Por Período', index=False)
        
        # Salvar métricas por equipamento
        df_equip = pd.DataFrame({
            'Equipamento': list(metricas['manobras_por_equipamento'].keys()),
            'Quantidade': list(metricas['manobras_por_equipamento'].values()),
            'Tempo Médio': [x/24 for x in metricas['tempo_medio_por_equipamento'].values()],  # Dividir por 24 para formato de horas
            'Tempo Total': [(metricas['manobras_por_equipamento'][eq] * metricas['tempo_medio_por_equipamento'][eq])/24 
                           for eq in metricas['manobras_por_equipamento'].keys()]  # Dividir por 24 para formato de horas
        })
        
        df_equip.to_excel(writer, sheet_name='Por Equipamento', index=False)
        
        # Formatar células de tempo na planilha por equipamento
        ws = writer.sheets['Por Equipamento']
        for row in range(2, len(df_equip) + 2):
            ws.cell(row=row, column=3).number_format = 'h:mm:ss'  # Tempo Médio
            ws.cell(row=row, column=4).number_format = 'h:mm:ss'  # Tempo Total
        
        # Salvar métricas por operador
        df_operador = pd.DataFrame({
            'Operador': list(metricas['manobras_por_operador']['quantidade'].keys()),
            'Quantidade': list(metricas['manobras_por_operador']['quantidade'].values()),
            'Tempo Médio': [x/24 for x in metricas['manobras_por_operador']['duracao_media'].values()],  # Dividir por 24 para formato de horas
            'Tempo Total': [x/24 for x in metricas['manobras_por_operador']['duracao_total'].values()],  # Dividir por 24 para formato de horas
            'Média Operações': list(metricas['manobras_por_operador']['operacoes_media'].values())
        })
        
        df_operador.to_excel(writer, sheet_name='Por Operador', index=False)
        
        # Formatar células de tempo na planilha por operador
        ws = writer.sheets['Por Operador']
        for row in range(2, len(df_operador) + 2):
            ws.cell(row=row, column=3).number_format = 'h:mm:ss'  # Tempo Médio
            ws.cell(row=row, column=4).number_format = 'h:mm:ss'  # Tempo Total
        
        # Ajustar largura das colunas em todas as planilhas
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column_cells in worksheet.columns:
                length = max(len(str(cell.value)) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 30)

def processar_todos_arquivos():
    """
    Processa todos os arquivos CSV na pasta dados/manobras.
    """
    # Obter o diretório onde está o script
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    diretorio_raiz = os.path.dirname(diretorio_script)
    
    # Diretórios para dados de entrada e saída
    diretorio_manobras = os.path.join(diretorio_raiz, "dados", "manobras")
    diretorio_saida = os.path.join(diretorio_raiz, "output", "manobras")
    
    # Criar diretórios se não existirem
    os.makedirs(diretorio_manobras, exist_ok=True)
    os.makedirs(diretorio_saida, exist_ok=True)
    
    # Encontrar apenas arquivos CSV
    arquivos = glob.glob(os.path.join(diretorio_manobras, "*.csv"))
    
    if not arquivos:
        print("Nenhum arquivo CSV encontrado na pasta dados/manobras")
        return
    
    print(f"Encontrados {len(arquivos)} arquivos CSV para processar")
    print(f"Os resultados serão salvos em {diretorio_saida}")
    
    # Processar cada arquivo
    for arquivo in arquivos:
        print(f"\nProcessando arquivo: {os.path.basename(arquivo)}")
        app = processar_arquivo_manobras(arquivo)
        if app:
            print(f"Dashboard criado para {os.path.basename(arquivo)}")
            return app  # Retorna o primeiro dashboard criado com sucesso
    
    return None

def processar_arquivo_manobras(caminho_arquivo):
    """
    Processa um arquivo de monitoramento e gera análise de manobras com dashboard.
    
    Args:
        caminho_arquivo (str): Caminho do arquivo a ser processado
    """
    # Carregar e processar o arquivo base (usando função existente)
    df = processar_arquivo_base(caminho_arquivo)
    
    if df is None or len(df) == 0:
        print(f"Erro ao processar arquivo {caminho_arquivo}")
        return
    
    # Identificar manobras
    df_manobras = identificar_manobras(df)
    
    # Calcular métricas
    metricas = calcular_metricas_manobras(df_manobras)
    
    # Criar e iniciar dashboard
    app = criar_dashboard(df_manobras, metricas)
    
    # Salvar métricas em Excel
    nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
    diretorio_saida = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "manobras")
    
    # Criar diretório de saída se não existir
    os.makedirs(diretorio_saida, exist_ok=True)
    
    arquivo_saida = os.path.join(diretorio_saida, f"{nome_base}_manobras.xlsx")
    
    # Criar arquivo Excel com as planilhas formatadas
    criar_excel_com_planilhas(df_manobras, metricas, arquivo_saida)
    
    print(f"Arquivo de métricas salvo em {arquivo_saida}")
    
    return app

if __name__ == "__main__":
    # Se nenhum arquivo for especificado como argumento, processa todos os arquivos
    if len(sys.argv) < 2:
        print("Processando todos os arquivos em dados/manobras...")
        app = processar_todos_arquivos()
        if app:
            app.run(debug=True, port=8050)
    else:
        # Se um arquivo específico for fornecido, processa apenas ele
        caminho_arquivo = sys.argv[1]
        app = processar_arquivo_manobras(caminho_arquivo)
        if app:
            app.run(debug=True, port=8050) 