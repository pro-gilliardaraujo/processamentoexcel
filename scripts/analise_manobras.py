"""
Script para análise de manobras de equipamentos agrícolas.
Processa dados de monitoramento para identificar e analisar padrões de manobra.
Suporta arquivos CSV na pasta dados/manobras.
Salva resultados na pasta output/manobras.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import zipfile
import tempfile
import shutil
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Output, Input
import dash_bootstrap_components as dbc
import glob

# Configurações
CONFIG_FILE = 'config/config_calculos.json'
INPUT_DIR = 'dados/manobras'
OUTPUT_DIR = 'output/manobras'

# Garante que os diretórios existem
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def processar_arquivo_base(caminho_arquivo):
    """
    Processa um arquivo base (TXT, CSV ou ZIP) e retorna um DataFrame.
    """
    print(f"\nProcessando arquivo: {caminho_arquivo}")
    
    # Verifica se o arquivo existe
    if not os.path.exists(caminho_arquivo):
        print(f"Arquivo não encontrado: {caminho_arquivo}")
        return None
        
    # Processa arquivo ZIP
    if caminho_arquivo.lower().endswith('.zip'):
        print("Arquivo ZIP detectado")
        return processar_arquivo_zip(caminho_arquivo)
        
    # Processa arquivo TXT ou CSV
    if caminho_arquivo.lower().endswith(('.txt', '.csv')):
        print("Arquivo TXT/CSV detectado")
        return ler_arquivo_com_encoding(caminho_arquivo)
        
    print(f"Formato de arquivo não suportado: {caminho_arquivo}")
    return None

def identificar_manobras(df):
    """
    Identifica manobras no DataFrame baseado na velocidade e direção.
    """
    try:
        print("\nIniciando identificação de manobras...")
        
        # Verifica se as colunas necessárias existem
        colunas_necessarias = ['Data/Hora', 'Equipamento', 'Velocidade']
        for coluna in colunas_necessarias:
            if coluna not in df.columns:
                print(f"Erro: Coluna '{coluna}' não encontrada no DataFrame")
                return None
        
        # Cria cópia do DataFrame para não modificar o original
        df_manobras = df.copy()
        
        # Adiciona coluna de direção se não existir
        if 'Direção' not in df_manobras.columns:
            print("Adicionando coluna de direção...")
            df_manobras['Direção'] = df_manobras['Velocidade'].apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)
        
        # Identifica mudanças de direção
        print("Identificando mudanças de direção...")
        df_manobras['Mudança_Direção'] = df_manobras['Direção'].diff().fillna(0) != 0
        
        # Agrupa por equipamento
        print("Agrupando por equipamento...")
        manobras_por_equipamento = []
        
        for equipamento, grupo in df_manobras.groupby('Equipamento'):
            print(f"\nProcessando equipamento: {equipamento}")
            
            # Ordena por data/hora
            grupo = grupo.sort_values('Data/Hora')
            
            # Identifica início e fim das manobras
            inicio_manobras = grupo[grupo['Mudança_Direção']].index
            if len(inicio_manobras) == 0:
                print(f"Nenhuma manobra encontrada para o equipamento {equipamento}")
                continue
                
            print(f"Encontradas {len(inicio_manobras)} manobras para o equipamento {equipamento}")
            
            # Processa cada manobra
            for i in range(len(inicio_manobras)):
                inicio_idx = inicio_manobras[i]
                fim_idx = inicio_manobras[i + 1] if i < len(inicio_manobras) - 1 else grupo.index[-1]
                
                manobra = grupo.loc[inicio_idx:fim_idx].copy()
                
                # Calcula duração da manobra
                duracao = (manobra['Data/Hora'].iloc[-1] - manobra['Data/Hora'].iloc[0]).total_seconds() / 3600
                
                # Adiciona informações da manobra
                manobra['Duração_Horas'] = duracao
                manobra['Tipo_Manobra'] = 'Reversão' if manobra['Direção'].iloc[0] != manobra['Direção'].iloc[-1] else 'Mudança'
                
                manobras_por_equipamento.append(manobra)
        
        if not manobras_por_equipamento:
            print("Nenhuma manobra foi identificada")
            return None
            
        # Concatena todas as manobras
        df_manobras_final = pd.concat(manobras_por_equipamento)
        print(f"\nTotal de manobras identificadas: {len(df_manobras_final)}")
        
        return df_manobras_final
        
    except Exception as e:
        print(f"Erro ao identificar manobras: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def calcular_horas_por_frota(df, df_manobras):
    """
    Calcula as horas totais, horas em manobra e horas sem manobra por frota.
    """
    try:
        # Cria uma cópia do DataFrame para não modificar o original
        df_horas = df.copy()
        
        # Calcula horas totais por frota (Equipamento)
        horas_totais = df_horas.groupby('Equipamento')['Diferença_Hora'].sum() / 24
        
        # Calcula horas em manobra por frota (Equipamento)
        horas_manobra = df_manobras.groupby('Frota')['Tempo_Manobra'].sum()
        
        # Cria DataFrame com as métricas
        df_horas_por_frota = pd.DataFrame({
            'Horas_Totais': horas_totais,
            'Horas_Manobra': horas_manobra
        }).fillna(0)
        
        # Calcula horas sem manobra
        df_horas_por_frota['Horas_Sem_Manobra'] = (
            df_horas_por_frota['Horas_Totais'] - df_horas_por_frota['Horas_Manobra']
        )
        
        # Calcula porcentagem de manobra
        df_horas_por_frota['Porcentagem_Manobra'] = (
            df_horas_por_frota['Horas_Manobra'] / df_horas_por_frota['Horas_Totais']
        ).fillna(0)
        
        # Arredonda valores
        df_horas_por_frota = df_horas_por_frota.round(4)
        
        return df_horas_por_frota
        
    except Exception as e:
        print(f"Erro ao calcular horas por frota: {str(e)}")
        return None

def criar_dashboard(df_manobras, metricas):
    """
    Cria uma dashboard interativa com Plotly Dash para visualização das métricas de manobra.
    
    Args:
        df_manobras (DataFrame): DataFrame com as manobras identificadas
        metricas (dict): Dicionário com as métricas calculadas
    """
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    # Extrair opções únicas para os filtros
    frentes = sorted(df_manobras['Frente'].unique())
    frotas = sorted(df_manobras['Frota'].unique())
    tipos_equipamento = sorted(df_manobras['Tipo_Equipamento'].unique())
    operadores = sorted(df_manobras['Operador'].unique())
    
    # Layout da dashboard
    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Dashboard de Análise de Manobras", className="text-center mb-4"), width=12)
        ]),
        
        # Filtros
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Filtros", className="card-title"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Frente:"),
                                dcc.Dropdown(
                                    id='filtro-frente',
                                    options=[{'label': f, 'value': f} for f in frentes],
                                    value=None,
                                    clearable=True,
                                    placeholder="Selecione a Frente"
                                )
                            ], width=3),
                            dbc.Col([
                                html.Label("Frota:"),
                                dcc.Dropdown(
                                    id='filtro-frota',
                                    options=[{'label': f, 'value': f} for f in frotas],
                                    value=None,
                                    clearable=True,
                                    placeholder="Selecione a Frota"
                                )
                            ], width=3),
                            dbc.Col([
                                html.Label("Tipo de Equipamento:"),
                                dcc.Dropdown(
                                    id='filtro-tipo-equipamento',
                                    options=[{'label': t, 'value': t} for t in tipos_equipamento],
                                    value=None,
                                    clearable=True,
                                    placeholder="Selecione o Tipo"
                                )
                            ], width=3),
                            dbc.Col([
                                html.Label("Operador:"),
                                dcc.Dropdown(
                                    id='filtro-operador',
                                    options=[{'label': o, 'value': o} for o in operadores],
                                    value=None,
                                    clearable=True,
                                    placeholder="Selecione o Operador"
                                )
                            ], width=3)
                        ])
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Cards com métricas principais
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Total de Manobras", className="card-title"),
                        html.H2(id="total-manobras", className="card-text text-center")
                    ])
                ]), width=3
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Tempo Médio (min)", className="card-title"),
                        html.H2(id="tempo-medio", className="card-text text-center")
                    ])
                ]), width=3
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Tempo Total (h)", className="card-title"),
                        html.H2(id="tempo-total", className="card-text text-center")
                    ])
                ]), width=3
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Manobras por Hora", className="card-title"),
                        html.H2(id="manobras-por-hora", className="card-text text-center")
                    ])
                ]), width=3
            ),
        ], className="mb-4"),
        
        # Gráficos - Primeira linha
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Manobras por Hora do Dia", className="card-title"),
                        dcc.Graph(id='grafico-manobras-hora')
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Evolução das Manobras", className="card-title"),
                        dcc.Graph(id='grafico-evolucao-manobras')
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Gráficos - Segunda linha
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Distribuição por Tipo de Equipamento", className="card-title"),
                        dcc.Graph(id='grafico-tipo-equipamento')
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Distribuição por Frota", className="card-title"),
                        dcc.Graph(id='grafico-frota')
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Tabela de detalhes por operador
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Detalhes por Operador", className="card-title"),
                        html.Div(id='tabela-operadores')
                    ])
                ])
            ], width=12)
        ], className="mb-4")
    ], fluid=True)
    
    # Callbacks para atualização dos gráficos e tabelas
    @app.callback(
        [Output('total-manobras', 'children'),
         Output('tempo-medio', 'children'),
         Output('tempo-total', 'children'),
         Output('manobras-por-hora', 'children'),
         Output('grafico-manobras-hora', 'figure'),
         Output('grafico-evolucao-manobras', 'figure'),
         Output('grafico-tipo-equipamento', 'figure'),
         Output('grafico-frota', 'figure'),
         Output('tabela-operadores', 'children')],
        [Input('filtro-frente', 'value'),
         Input('filtro-frota', 'value'),
         Input('filtro-tipo-equipamento', 'value'),
         Input('filtro-operador', 'value')]
    )
    def atualizar_dashboard(frente, frota, tipo_equipamento, operador):
        # Aplicar filtros
        df_filtrado = df_manobras.copy()
        if frente:
            df_filtrado = df_filtrado[df_filtrado['Frente'] == frente]
        if frota:
            df_filtrado = df_filtrado[df_filtrado['Frota'] == frota]
        if tipo_equipamento:
            df_filtrado = df_filtrado[df_filtrado['Tipo_Equipamento'] == tipo_equipamento]
        if operador:
            df_filtrado = df_filtrado[df_filtrado['Operador'] == operador]
        
        # Calcular métricas atualizadas
        total_manobras = len(df_filtrado)
        tempo_medio = df_filtrado['Tempo_Manobra'].mean() * 60 if not df_filtrado.empty else 0
        tempo_total = df_filtrado['Tempo_Manobra'].sum() if not df_filtrado.empty else 0
        manobras_por_hora = total_manobras / tempo_total if tempo_total > 0 else 0
        
        # Gráfico de manobras por hora
        manobras_hora = df_filtrado.groupby('Inicio').size()
        fig_manobras_hora = go.Figure(data=[
            go.Scatter(
                x=manobras_hora.index,
                y=manobras_hora.values,
                mode='lines+markers',
                line=dict(shape='spline', smoothing=0.3)
            )
        ])
        fig_manobras_hora.update_layout(
            title="Manobras por Hora do Dia",
            xaxis_title="Hora",
            yaxis_title="Quantidade de Manobras",
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        # Gráfico de evolução
        df_filtrado['Data'] = pd.to_datetime(df_filtrado['Inicio'])
        evolucao = df_filtrado.groupby('Data').size()
        fig_evolucao = go.Figure(data=[
            go.Scatter(
                x=evolucao.index,
                y=evolucao.values,
                mode='lines+markers',
                line=dict(shape='spline', smoothing=0.3)
            )
        ])
        fig_evolucao.update_layout(
            title="Evolução das Manobras",
            xaxis_title="Data",
            yaxis_title="Quantidade de Manobras",
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        # Gráfico por tipo de equipamento
        tipo_equip = df_filtrado.groupby('Tipo_Equipamento').size()
        fig_tipo_equip = go.Figure(data=[
            go.Bar(
                x=tipo_equip.index,
                y=tipo_equip.values,
                text=tipo_equip.values,
                textposition='auto'
            )
        ])
        fig_tipo_equip.update_layout(
            title="Distribuição por Tipo de Equipamento",
            xaxis_title="Tipo de Equipamento",
            yaxis_title="Quantidade de Manobras",
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        # Gráfico por frota
        frota_dist = df_filtrado.groupby('Frota').size()
        fig_frota = go.Figure(data=[
            go.Bar(
                x=frota_dist.index,
                y=frota_dist.values,
                text=frota_dist.values,
                textposition='auto'
            )
        ])
        fig_frota.update_layout(
            title="Distribuição por Frota",
            xaxis_title="Frota",
            yaxis_title="Quantidade de Manobras",
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        # Tabela de operadores
        df_operadores = df_filtrado.groupby(['Frota', 'Operador']).agg({
            'Equipamento': 'count',
            'Tempo_Manobra': 'sum'
        }).round(4)
        
        df_operadores.columns = ['Quantidade', 'Tempo_Total (h)']
        df_operadores = df_operadores.reset_index()
        
        tabela = dbc.Table.from_dataframe(
            df_operadores,
            striped=True,
            bordered=True,
            hover=True,
            responsive=True
        )
        
        return (
            f"{total_manobras:,}",
            f"{tempo_medio:.1f}",
            f"{tempo_total:.1f}",
            f"{manobras_por_hora:.1f}",
            fig_manobras_hora,
            fig_evolucao,
            fig_tipo_equip,
            fig_frota,
            tabela
        )
    
    return app

def criar_excel_com_planilhas(df_base, df_resultado, df_horas_por_frota, caminho_saida):
    """
    Cria um arquivo Excel com as planilhas de resultados.
    """
    try:
        # Cria um ExcelWriter
        with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
            # Salva cada DataFrame em uma planilha
            df_base.to_excel(writer, sheet_name='BASE_CALCULO', index=False)
            df_resultado.to_excel(writer, sheet_name='RESULTADOS', index=False)
            
            if df_horas_por_frota is not None:
                df_horas_por_frota.to_excel(writer, sheet_name='HORAS_POR_FROTA', index=False)
                
            # Ajusta largura das colunas
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for idx, col in enumerate(df_base.columns):
                    max_length = max(
                        df_base[col].astype(str).apply(len).max(),
                        len(str(col))
                    )
                    worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2
                    
        return True
        
    except Exception as e:
        print(f"Erro ao criar arquivo Excel: {str(e)}")
        return False

def processar_todos_arquivos():
    """
    Processa todos os arquivos CSV na pasta de dados e gera um arquivo Excel com as métricas.
    """
    try:
        # Lista todos os arquivos CSV na pasta de dados
        arquivos_csv = [f for f in os.listdir(INPUT_DIR) if f.endswith('.csv')]
        
        if not arquivos_csv:
            print("Nenhum arquivo CSV encontrado na pasta dados/manobras")
            return
        
        # Processa cada arquivo
        for arquivo in arquivos_csv:
            print(f"\nProcessando arquivo: {arquivo}")
            
            # Caminho completo do arquivo
            caminho_arquivo = os.path.join(INPUT_DIR, arquivo)
            
            # Processa o arquivo base
            df = processar_arquivo_base(caminho_arquivo)
            if df is None or df.empty:
                print(f"Erro ao processar arquivo {arquivo}")
                continue
            
            # Identifica manobras
            df_manobras = identificar_manobras(df)
            
            # Calcula horas por frota
            df_horas_por_frota = calcular_horas_por_frota(df, df_manobras)
            
            # Nome do arquivo de saída
            nome_base = os.path.splitext(arquivo)[0]
            arquivo_saida = os.path.join(OUTPUT_DIR, f"{nome_base}.xlsx")
            
            # Cria diretório de saída se não existir
            os.makedirs(os.path.dirname(arquivo_saida), exist_ok=True)
            
            # Criar arquivo Excel com as planilhas formatadas
            if criar_excel_com_planilhas(df, df_manobras, df_horas_por_frota, arquivo_saida):
                print(f"Arquivo de métricas salvo em {arquivo_saida}")
            else:
                print(f"Erro ao salvar arquivo {arquivo_saida}")
                
    except Exception as e:
        print(f"Erro ao processar arquivos: {str(e)}")
        import traceback
        traceback.print_exc()

def processar_arquivo_manobras(caminho_arquivo):
    """
    Processa um arquivo de monitoramento e gera análise de manobras com dashboard.
    """
    try:
        print(f"\nIniciando processamento de manobras para o arquivo: {caminho_arquivo}")
        
        # Carrega e processa o arquivo base
        df = processar_arquivo_base(caminho_arquivo)
        if df is None or len(df) == 0:
            print("Erro: Não foi possível processar o arquivo base ou o arquivo está vazio")
            return False
            
        print(f"\nArquivo base processado com sucesso. Total de registros: {len(df)}")
        
        # Identifica manobras
        print("\nIdentificando manobras...")
        df_manobras = identificar_manobras(df)
        if df_manobras is None or len(df_manobras) == 0:
            print("Erro: Não foi possível identificar manobras no arquivo")
            return False
            
        print(f"Manobras identificadas com sucesso. Total de manobras: {len(df_manobras)}")
        
        # Calcula métricas
        print("\nCalculando métricas...")
        df_metricas = calcular_horas_por_frota(df, df_manobras)
        if df_metricas is None or len(df_metricas) == 0:
            print("Erro: Não foi possível calcular métricas das manobras")
            return False
            
        print(f"Métricas calculadas com sucesso. Total de equipamentos analisados: {len(df_metricas)}")
        
        # Cria dashboard
        print("\nCriando dashboard...")
        app = criar_dashboard(df_manobras, df_metricas)
        if app is None:
            print("Erro: Não foi possível criar o dashboard")
            return False
            
        print("Dashboard criado com sucesso")
        
        # Salva métricas em Excel
        print("\nSalvando métricas em Excel...")
        nome_arquivo = os.path.splitext(os.path.basename(caminho_arquivo))[0]
        caminho_saida = os.path.join(OUTPUT_DIR, f'{nome_arquivo}.xlsx')
        
        # Cria diretório de saída se não existir
        os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
        
        # Salva arquivo Excel
        with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
            df_manobras.to_excel(writer, sheet_name='MANOBRAS', index=False)
            df_metricas.to_excel(writer, sheet_name='MÉTRICAS', index=False)
            
            # Ajusta largura das colunas
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for idx, col in enumerate(df_manobras.columns if sheet_name == 'MANOBRAS' else df_metricas.columns):
                    max_length = max(
                        df_manobras[col].astype(str).apply(len).max() if sheet_name == 'MANOBRAS' else df_metricas[col].astype(str).apply(len).max(),
                        len(str(col))
                    )
                    worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2
        
        print(f"Métricas salvas com sucesso em: {caminho_saida}")
        
        # Inicia o servidor
        print("\nIniciando servidor...")
        app.run_server(debug=True, port=8050)
        
        return True
        
    except Exception as e:
        print(f"Erro ao processar arquivo de manobras: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def calcular_metricas_manobras(df_manobras, df_base):
    """
    Calcula métricas de manobras por equipamento, operador e frente.
    """
    try:
        print("\nIniciando cálculo de métricas de manobras...")
        
        if df_manobras is None or df_manobras.empty:
            print("Erro: DataFrame de manobras está vazio")
            return None, None, None
            
        # Calcula métricas por equipamento
        print("\nCalculando métricas por equipamento...")
        metricas_equipamento = df_manobras.groupby('Equipamento').agg({
            'Duração_Horas': ['count', 'sum', 'mean'],
            'Tipo_Manobra': lambda x: x.value_counts().to_dict()
        }).reset_index()
        
        # Renomeia colunas
        metricas_equipamento.columns = ['Equipamento', 'Quantidade_Manobras', 'Tempo_Total_Manobras', 
                                      'Tempo_Medio_Manobras', 'Tipos_Manobra']
        
        # Calcula métricas por operador
        print("Calculando métricas por operador...")
        metricas_operador = df_manobras.groupby('Operador').agg({
            'Duração_Horas': ['count', 'sum', 'mean'],
            'Tipo_Manobra': lambda x: x.value_counts().to_dict()
        }).reset_index()
        
        # Renomeia colunas
        metricas_operador.columns = ['Operador', 'Quantidade_Manobras', 'Tempo_Total_Manobras', 
                                   'Tempo_Medio_Manobras', 'Tipos_Manobra']
        
        # Calcula métricas por frente
        print("Calculando métricas por frente...")
        metricas_frente = df_manobras.groupby('Frente').agg({
            'Duração_Horas': ['count', 'sum', 'mean'],
            'Tipo_Manobra': lambda x: x.value_counts().to_dict()
        }).reset_index()
        
        # Renomeia colunas
        metricas_frente.columns = ['Frente', 'Quantidade_Manobras', 'Tempo_Total_Manobras', 
                                 'Tempo_Medio_Manobras', 'Tipos_Manobra']
        
        # Calcula tempo total de operação para cada equipamento
        print("Calculando tempo total de operação...")
        tempo_total_operacao = df_base.groupby('Equipamento')['Data/Hora'].agg(
            lambda x: (x.max() - x.min()).total_seconds() / 3600
        ).to_dict()
        
        # Adiciona porcentagem de tempo em manobra
        for df in [metricas_equipamento, metricas_operador, metricas_frente]:
            df['Porcentagem_Tempo_Manobra'] = df.apply(
                lambda row: (row['Tempo_Total_Manobras'] / tempo_total_operacao.get(row['Equipamento'], 1)) * 100 
                if row['Equipamento'] in tempo_total_operacao else 0, 
                axis=1
            )
        
        print("\nMétricas calculadas com sucesso:")
        print(f"- Equipamentos: {len(metricas_equipamento)}")
        print(f"- Operadores: {len(metricas_operador)}")
        print(f"- Frentes: {len(metricas_frente)}")
        
        return metricas_equipamento, metricas_operador, metricas_frente
        
    except Exception as e:
        print(f"Erro ao calcular métricas de manobras: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, None

def ler_arquivo_com_encoding(caminho_arquivo):
    """
    Tenta ler um arquivo com diferentes encodings.
    """
    encodings = ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            print(f"\nTentando ler arquivo com encoding: {encoding}")
            
            # Detecta o tipo de arquivo
            if caminho_arquivo.lower().endswith('.csv'):
                # Tenta primeiro com o separador padrão
                try:
                    print("Tentando ler com separador vírgula...")
                    df = pd.read_csv(caminho_arquivo, encoding=encoding, sep=',', on_bad_lines='warn')
                except Exception as e:
                    print(f"Erro ao ler com vírgula: {str(e)}")
                    # Se falhar, tenta detectar o separador
                    try:
                        with open(caminho_arquivo, 'r', encoding=encoding) as f:
                            primeira_linha = f.readline().strip()
                            print(f"Primeira linha do arquivo: {primeira_linha}")
                            possiveis_separadores = [',', ';', '\t']
                            separador = max(possiveis_separadores, key=primeira_linha.count)
                            print(f"Separador detectado: '{separador}'")
                            df = pd.read_csv(caminho_arquivo, encoding=encoding, sep=separador, on_bad_lines='warn')
                    except Exception as e:
                        print(f"Erro ao detectar separador: {str(e)}")
                        continue
            else:
                print("Tentando ler arquivo TXT com separador tab...")
                df = pd.read_csv(caminho_arquivo, encoding=encoding, sep='\t', on_bad_lines='warn')
                
            # Verifica se o DataFrame está vazio
            if df.empty:
                print(f"DataFrame vazio com encoding {encoding}")
                continue
                
            # Remove linhas com valores nulos em todas as colunas
            df = df.dropna(how='all')
            
            # Converte colunas de data/hora
            colunas_data_hora = ['Data', 'Hora']
            for coluna in colunas_data_hora:
                if coluna in df.columns:
                    try:
                        df[coluna] = pd.to_datetime(df[coluna], errors='coerce')
                    except Exception as e:
                        print(f"Erro ao converter coluna {coluna}: {str(e)}")
                        
            # Cria coluna Data_Hora
            if 'Data' in df.columns and 'Hora' in df.columns:
                df['Data_Hora'] = pd.to_datetime(df['Data'].dt.date.astype(str) + ' ' + df['Hora'].dt.time.astype(str))
                
            # Garante que a coluna 'Parada com Motor Ligado' é numérica
            if 'Parada com Motor Ligado' in df.columns:
                df['Parada com Motor Ligado'] = pd.to_numeric(df['Parada com Motor Ligado'], errors='coerce')
                
            print(f"\nArquivo lido com sucesso usando encoding {encoding}")
            print(f"Colunas encontradas: {df.columns.tolist()}")
            print(f"Total de linhas: {len(df)}")
            print("\nPrimeiras 5 linhas do DataFrame:")
            print(df.head())
            return df
            
        except Exception as e:
            print(f"Erro ao ler arquivo com encoding {encoding}: {str(e)}")
            continue
            
    print("\nNão foi possível ler o arquivo com nenhum dos encodings tentados")
    return None

def processar_arquivo_zip(caminho_zip):
    """
    Extrai e processa um arquivo ZIP contendo arquivos TXT ou CSV.
    """
    print("Iniciando processamento do arquivo ZIP...")
    
    # Cria diretório temporário
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Extrai arquivo ZIP
            with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                
            # Lista arquivos extraídos
            arquivos = [f for f in os.listdir(temp_dir) if f.lower().endswith(('.txt', '.csv'))]
            
            if not arquivos:
                print("Nenhum arquivo TXT ou CSV encontrado no ZIP")
                return None
                
            print(f"Arquivos encontrados no ZIP: {arquivos}")
            
            # Processa cada arquivo
            for arquivo in arquivos:
                caminho_arquivo = os.path.join(temp_dir, arquivo)
                print(f"\nProcessando arquivo do ZIP: {arquivo}")
                
                df = ler_arquivo_com_encoding(caminho_arquivo)
                if df is not None and not df.empty:
                    print(f"Arquivo {arquivo} processado com sucesso")
                    return df
                    
            print("Nenhum arquivo válido encontrado no ZIP")
            return None
            
        except Exception as e:
            print(f"Erro ao processar arquivo ZIP: {str(e)}")
            return None

def calcular_motor_ocioso(df):
    """
    Calcula o tempo de motor ocioso baseado nas regras definidas.
    
    Regras:
    1. Um intervalo é fechado quando há uma sequência de "Parada com Motor Ligado = 0" 
       com duração maior que 1 minuto
    2. Soma-se o tempo quando há sequências de "Parada com Motor Ligado = 1" 
       seguidas de "Parada com Motor Ligado = 0" de menos de 1 minuto
    3. Um novo intervalo começa com "Parada com Motor Ligado = 1"
    """
    if df is None or df.empty:
        print("DataFrame vazio ou inválido")
        return None
        
    if 'Parada com Motor Ligado' not in df.columns:
        print("Coluna 'Parada com Motor Ligado' não encontrada")
        return None
        
    # Garante que a coluna é numérica
    df['Parada com Motor Ligado'] = pd.to_numeric(df['Parada com Motor Ligado'], errors='coerce')
    
    # Inicializa variáveis
    tempo_total = 0
    tempo_intervalo = 0
    inicio_intervalo = None
    ultimo_timestamp = None
    
    # Itera sobre as linhas do DataFrame
    for idx, row in df.iterrows():
        timestamp = row['Data_Hora']
        parada_motor = row['Parada com Motor Ligado']
        
        # Se é a primeira linha
        if ultimo_timestamp is None:
            ultimo_timestamp = timestamp
            if parada_motor == 1:
                inicio_intervalo = timestamp
            continue
            
        # Calcula o intervalo de tempo em minutos
        intervalo = (timestamp - ultimo_timestamp).total_seconds() / 60
        
        # Se motor está ligado (parada_motor = 1)
        if parada_motor == 1:
            # Se não há intervalo iniciado, inicia um novo
            if inicio_intervalo is None:
                inicio_intervalo = timestamp
            # Se há intervalo iniciado, soma o tempo
            else:
                tempo_intervalo += intervalo
                
        # Se motor está desligado (parada_motor = 0)
        elif parada_motor == 0:
            # Se há intervalo iniciado
            if inicio_intervalo is not None:
                # Se o intervalo é menor que 1 minuto, soma ao tempo total
                if intervalo < 1:
                    tempo_total += tempo_intervalo + intervalo
                    tempo_intervalo = 0
                    inicio_intervalo = None
                # Se o intervalo é maior que 1 minuto, fecha o intervalo atual
                else:
                    tempo_total += tempo_intervalo
                    tempo_intervalo = 0
                    inicio_intervalo = None
                    
        ultimo_timestamp = timestamp
        
    # Adiciona o último intervalo se houver
    if inicio_intervalo is not None:
        tempo_total += tempo_intervalo
        
    return tempo_total

def carregar_config_calculos():
    """
    Carrega as configurações de cálculos do arquivo JSON.
    """
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar configurações: {str(e)}")
        return None

def listar_arquivos_para_processar():
    """
    Lista os arquivos disponíveis para processamento.
    """
    arquivos = []
    
    # Lista arquivos TXT e CSV
    for ext in ['.txt', '.csv']:
        arquivos.extend(glob.glob(os.path.join(INPUT_DIR, f'*{ext}')))
        
    # Lista arquivos ZIP
    arquivos.extend(glob.glob(os.path.join(INPUT_DIR, '*.zip')))
    
    if not arquivos:
        print(f"Nenhum arquivo TXT, CSV ou ZIP encontrado em {INPUT_DIR}")
    else:
        print(f"Arquivos encontrados: {len(arquivos)}")
        
    return arquivos

if __name__ == "__main__":
    # Se nenhum arquivo for especificado como argumento, processa todos os arquivos
    if len(sys.argv) == 1:
        arquivos = listar_arquivos_para_processar()
        if not arquivos:
            print("Nenhum arquivo encontrado para processamento")
            sys.exit(1)
            
        for arquivo in arquivos:
            print(f"\nProcessando arquivo: {arquivo}")
            df = processar_arquivo_base(arquivo)
            
            if df is not None and not df.empty:
                # Calcula motor ocioso
                tempo_motor_ocioso = calcular_motor_ocioso(df)
                if tempo_motor_ocioso is not None:
                    print(f"Tempo de motor ocioso: {tempo_motor_ocioso:.2f} minutos")
                    
                    # Cria DataFrame com resultados
                    df_resultado = pd.DataFrame({
                        'Arquivo': [os.path.basename(arquivo)],
                        'Tempo Motor Ocioso (min)': [tempo_motor_ocioso]
                    })
                    
                    # Salva resultados em Excel
                    caminho_saida = os.path.join(OUTPUT_DIR, f"{os.path.splitext(os.path.basename(arquivo))[0]}.xlsx")
                    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
                    
                    if criar_excel_com_planilhas(df, df_resultado, None, caminho_saida):
                        print(f"Resultados salvos em: {caminho_saida}")
                    else:
                        print("Erro ao salvar resultados")
            else:
                print("Não foi possível processar o arquivo")
                
    else:
        # Processa apenas o arquivo especificado
        arquivo = sys.argv[1]
        if not os.path.exists(arquivo):
            print(f"Arquivo não encontrado: {arquivo}")
            sys.exit(1)
            
        print(f"\nProcessando arquivo: {arquivo}")
        df = processar_arquivo_base(arquivo)
        
        if df is not None and not df.empty:
            # Calcula motor ocioso
            tempo_motor_ocioso = calcular_motor_ocioso(df)
            if tempo_motor_ocioso is not None:
                print(f"Tempo de motor ocioso: {tempo_motor_ocioso:.2f} minutos")
                
                # Cria DataFrame com resultados
                df_resultado = pd.DataFrame({
                    'Arquivo': [os.path.basename(arquivo)],
                    'Tempo Motor Ocioso (min)': [tempo_motor_ocioso]
                })
                
                # Salva resultados em Excel
                caminho_saida = os.path.join(OUTPUT_DIR, f"{os.path.splitext(os.path.basename(arquivo))[0]}.xlsx")
                os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
                
                if criar_excel_com_planilhas(df, df_resultado, None, caminho_saida):
                    print(f"Resultados salvos em: {caminho_saida}")
                else:
                    print("Erro ao salvar resultados")
        else:
            print("Não foi possível processar o arquivo") 