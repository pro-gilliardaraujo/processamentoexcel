"""
Script para processamento completo de dados de monitoramento de colhedoras.
Lê arquivos TXT ou CSV na pasta raiz, processa-os e gera arquivos Excel com planilhas auxiliares prontas.
Também processa arquivos ZIP contendo TXT ou CSV.
"""

import pandas as pd
import numpy as np
import os
import glob
import zipfile
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

# Configurações
processCsv = False  # Altere para True quando quiser processar arquivos CSV

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

# Valores a serem filtrados
OPERADORES_EXCLUIR = ["9999 - TROCA DE TURNO"]

def processar_arquivo_base(caminho_arquivo):
    """
    Processa o arquivo TXT ou CSV e retorna o DataFrame com as transformações necessárias.
    
    Args:
        caminho_arquivo (str): Caminho do arquivo TXT ou CSV de entrada
    
    Returns:
        DataFrame: DataFrame processado com todas as transformações
    """
    # Lista de codificações para tentar
    codificacoes = ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252']
    
    for codificacao in codificacoes:
        try:
            # Leitura do arquivo (TXT ou CSV são tratados da mesma forma se usarem separador ';')
            df = pd.read_csv(caminho_arquivo, sep=';', encoding=codificacao)
            print(f"Arquivo lido com sucesso usando {codificacao}! Total de linhas: {len(df)}")
            
            # Verificar se o DataFrame está vazio (apenas cabeçalhos sem dados)
            if len(df) == 0:
                print(f"O arquivo {caminho_arquivo} contém apenas cabeçalhos sem dados.")
                # Retornar o DataFrame vazio mas com as colunas, em vez de None
                # Garantir que todas as colunas desejadas existam
                for col in COLUNAS_DESEJADAS:
                    if col not in df.columns:
                        df[col] = np.nan
                # Reorganizar as colunas na ordem desejada
                colunas_existentes = [col for col in COLUNAS_DESEJADAS if col in df.columns]
                colunas_extras = [col for col in df.columns if col not in COLUNAS_DESEJADAS]
                return df[colunas_existentes + colunas_extras]
            
            # Limpeza de espaços extras nos nomes das colunas
            df.columns = df.columns.str.strip()
            
            # Verificar se 'Data/Hora' existe e processá-la
            if 'Data/Hora' in df.columns:
                df[['Data', 'Hora']] = df['Data/Hora'].str.split(' ', expand=True)
                df = df.drop(columns=['Data/Hora'])
            
            # Conversão de Hora para datetime
            df['Hora'] = pd.to_datetime(df['Hora'], format='%H:%M:%S', errors='coerce')
            
            # IMPORTANTE: Usar a mesma lógica do Codigo_Base_C.py para cálculo da Diferença_Hora
            # Primeiro ordenar os dados para garantir que o diff() funcione corretamente
            df = df.sort_values(by=['Equipamento', 'Data', 'Hora'])
            
            # Calcular a diferença de hora usando a lógica do Codigo_Base_C.py
            # Realizar o cálculo para cada equipamento separadamente
            equipamentos = df['Equipamento'].unique()
            df['Diferença_Hora'] = 0.0
            
            for equipamento in equipamentos:
                # Filtrar dados deste equipamento
                mask = df['Equipamento'] == equipamento
                # Calcular diferenças usando diff() como no Codigo_Base_C.py
                df.loc[mask, 'Diferença_Hora'] = df.loc[mask, 'Hora'].diff().dt.total_seconds() / 3600
                # Aplicar regras exatamente como no Codigo_Base_C.py
                df.loc[mask, 'Diferença_Hora'] = df.loc[mask, 'Diferença_Hora'].apply(lambda x: max(x, 0))
                # Nova regra: se Diferença_Hora > 0.50, então 0
                df.loc[mask, 'Diferença_Hora'] = df.loc[mask, 'Diferença_Hora'].apply(lambda x: 0 if x > 0.50 else x)
            
            print(f"Diferença_Hora calculada usando lógica do Codigo_Base_C.py. Soma total: {df['Diferença_Hora'].sum():.2f} horas")
            
            # Cálculos adicionais
            RPM_MINIMO = 300  # Definindo constante para RPM mínimo
            if 'Parada com Motor Ligado' not in df.columns:
                df['Parada com Motor Ligado'] = ((df['Velocidade'] == 0) & 
                                               (df['RPM Motor'] >= RPM_MINIMO)).astype(int)
            
            # Verifica se Horas Produtivas já existe
            if 'Horas Produtivas' not in df.columns or df['Horas Produtivas'].isna().any():
                # Calcular horas produtivas sem arredondamento, mantendo a precisão completa
                df['Horas Produtivas'] = df.apply(
                    lambda row: row['Diferença_Hora'] if row['Grupo Operacao'] == 'Produtiva' else 0,
                    axis=1
                )
            else:
                # Limpa e converte para número
                df['Horas Produtivas'] = pd.to_numeric(df['Horas Produtivas'].astype(str).str.strip(), errors='coerce')
                df['Horas Produtivas'] = df['Horas Produtivas'].fillna(0)
            
            # Conversão de colunas binárias para valores numéricos (garantindo que sejam números)
            for col in ['Esteira Ligada', 'Motor Ligado', 'Field Cruiser', 'RTK (Piloto Automatico)', 'Implemento Ligado']:
                if col in df.columns:
                    # Se a coluna for texto (LIGADO/DESLIGADO), converter para 1/0
                    if df[col].dtype == 'object':
                        df[col] = df[col].replace({'LIGADO': 1, 'DESLIGADO': 0})
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
            # Limpeza e organização das colunas
            df = df.drop(columns=COLUNAS_REMOVER, errors='ignore')
            
            # Garantir que todas as colunas desejadas existam
            for col in COLUNAS_DESEJADAS:
                if col not in df.columns:
                    df[col] = np.nan
            
            # Reorganizar as colunas na ordem desejada
            colunas_existentes = [col for col in COLUNAS_DESEJADAS if col in df.columns]
            colunas_extras = [col for col in df.columns if col not in COLUNAS_DESEJADAS]
            df = df[colunas_existentes + colunas_extras]
            
            return df
            
        except UnicodeDecodeError:
            print(f"Tentativa com codificação {codificacao} falhou, tentando próxima codificação...")
            continue
        except Exception as e:
            print(f"Erro ao processar o arquivo com codificação {codificacao}: {str(e)}")
            continue
    
    # Se chegou aqui, todas as tentativas de codificação falharam
    print(f"Erro: Não foi possível ler o arquivo {caminho_arquivo} com nenhuma das codificações tentadas.")
    return None

def calcular_base_calculo(df):
    """
    Calcula a tabela de Base Calculo a partir do DataFrame processado.
    Calcula médias diárias considerando os dias efetivos de trabalho de cada operador.
    
    Args:
        df (DataFrame): DataFrame processado
    
    Returns:
        DataFrame: Tabela Base Calculo com todas as métricas calculadas
    """
    # Detectar número de dias totais nos dados (apenas para informação)
    dias_unicos_total = df['Data'].nunique() if 'Data' in df.columns else 1
    print(f"Detectados {dias_unicos_total} dias distintos na base de dados.")
    
    # Extrair combinações únicas de Equipamento, Grupo Equipamento/Frente e Operador
    combinacoes = df[['Equipamento', 'Grupo Equipamento/Frente', 'Operador']].drop_duplicates().reset_index(drop=True)
    
    # Filtrar operadores excluídos
    combinacoes = combinacoes[~combinacoes['Operador'].isin(OPERADORES_EXCLUIR)]
    
    # Inicializar as colunas de métricas
    resultados = []
    
    # Função para calcular valores com alta precisão e depois formatar
    def calcular_porcentagem(numerador, denominador, precisao=4):
        """Calcula porcentagem como decimal (0-1) evitando divisão por zero."""
        if denominador > 0:
            return round((numerador / denominador), precisao)
        return 0.0
    
    # Calcular as métricas para cada combinação
    for idx, row in combinacoes.iterrows():
        equipamento = row['Equipamento']
        grupo = row['Grupo Equipamento/Frente']
        operador = row['Operador']
        
        # Filtrar dados para esta combinação
        filtro = (df['Equipamento'] == equipamento) & \
                (df['Grupo Equipamento/Frente'] == grupo) & \
                (df['Operador'] == operador)
        
        dados_filtrados = df[filtro]
        
        # Determinar o número de dias efetivos para este operador
        dias_operador = dados_filtrados['Data'].nunique() if 'Data' in dados_filtrados.columns else 1
        
        # Horas totais - calcular a média diária usando os dias efetivos deste operador
        horas_totais = round(dados_filtrados['Diferença_Hora'].sum(), 4)
        if dias_operador > 1:
            # Usar média diária baseada nos dias específicos deste operador
            horas_totais = round(horas_totais / dias_operador, 4)
            print(f"Operador: {operador}, Dias efetivos: {dias_operador}, Média diária: {horas_totais:.2f} horas")
        
        # Horas elevador (Esteira Ligada = 1 E Pressão de Corte > 400) - calcular a média diária
        horas_elevador = round(dados_filtrados[
            (dados_filtrados['Esteira Ligada'] == 1) & 
            (dados_filtrados['Pressao de Corte'] > 400)
        ]['Diferença_Hora'].sum(), 4)
        if dias_operador > 1:
            horas_elevador = round(horas_elevador / dias_operador, 4)
        
        # Percentual horas elevador (em decimal 0-1)
        percent_elevador = calcular_porcentagem(horas_elevador, horas_totais)
        
        # RTK (Piloto Automático = 1 e Field Cruiser = 1) - calcular a média diária
        rtk = round(dados_filtrados[(dados_filtrados['RTK (Piloto Automatico)'] == 1) & 
                             (dados_filtrados['Field Cruiser'] == 1)]['Diferença_Hora'].sum(), 4)
        if dias_operador > 1:
            rtk = round(rtk / dias_operador, 4)
        
        # Horas Produtivas - calcular a média diária
        horas_produtivas = round(dados_filtrados['Horas Produtivas'].sum(), 4)
        if dias_operador > 1:
            horas_produtivas = round(horas_produtivas / dias_operador, 4)
        
        # % Utilização RTK (em decimal 0-1)
        utilizacao_rtk = calcular_porcentagem(rtk, horas_produtivas)
        
        # Motor Ligado - calcular a média diária
        motor_ligado = round(dados_filtrados[dados_filtrados['Motor Ligado'] == 1]['Diferença_Hora'].sum(), 4)
        if dias_operador > 1:
            motor_ligado = round(motor_ligado / dias_operador, 4)
        
        # % Eficiência Elevador (em decimal 0-1)
        eficiencia_elevador = calcular_porcentagem(horas_elevador, motor_ligado)
        
        # Parado com Motor Ligado - calcular a média diária
        parado_motor_ligado = round(dados_filtrados[dados_filtrados['Parada com Motor Ligado'] == 1]['Diferença_Hora'].sum(), 4)
        if dias_operador > 1:
            parado_motor_ligado = round(parado_motor_ligado / dias_operador, 4)
        
        # % Parado com motor ligado (em decimal 0-1)
        percent_parado_motor = calcular_porcentagem(parado_motor_ligado, motor_ligado)
        
        resultados.append({
            'Equipamento': equipamento,
            'Grupo Equipamento/Frente': grupo,
            'Operador': operador,
            'Horas totais': horas_totais,
            'Horas elevador': horas_elevador,
            '%': percent_elevador,
            'RTK': rtk,
            'Horas Produtivas': horas_produtivas,
            '% Utilização RTK': utilizacao_rtk,
            'Motor Ligado': motor_ligado,
            '% Eficiência Elevador': eficiencia_elevador,
            'Parado Com Motor Ligado': parado_motor_ligado,
            '% Parado com motor ligado': percent_parado_motor
        })
    
    return pd.DataFrame(resultados)

def calcular_disponibilidade_mecanica(df):
    """
    Calcula a disponibilidade mecânica para cada equipamento.
    Calcula médias diárias considerando os dias efetivos de cada equipamento.
    
    Args:
        df (DataFrame): DataFrame processado
    
    Returns:
        DataFrame: Disponibilidade mecânica por equipamento
    """
    # Filtramos os dados excluindo os operadores da lista
    df_filtrado = df[~df['Operador'].isin(OPERADORES_EXCLUIR)]
    
    # Função para calcular valores com alta precisão e depois formatar
    def calcular_porcentagem(numerador, denominador, precisao=4):
        """Calcula porcentagem como decimal (0-1) evitando divisão por zero."""
        if denominador > 0:
            return round((numerador / denominador), precisao)
        return 0.0
    
    # Agrupar por Equipamento e calcular horas por grupo operacional
    equipamentos = df_filtrado['Equipamento'].unique()
    resultados = []
    
    for equipamento in equipamentos:
        dados_equip = df_filtrado[df_filtrado['Equipamento'] == equipamento]
        
        # Determinar número de dias efetivos para este equipamento
        dias_equip = dados_equip['Data'].nunique() if 'Data' in dados_equip.columns else 1
        
        total_horas = round(dados_equip['Diferença_Hora'].sum(), 4)
        
        # Calcular horas de manutenção
        manutencao = round(dados_equip[dados_equip['Grupo Operacao'] == 'Manutenção']['Diferença_Hora'].sum(), 4)
        
        # Se houver múltiplos dias, usar médias diárias
        if dias_equip > 1:
            total_horas = round(total_horas / dias_equip, 4)
            manutencao = round(manutencao / dias_equip, 4)
            print(f"Equipamento: {equipamento}, Dias efetivos: {dias_equip}, Média diária: {total_horas:.2f} horas")
        
        # A disponibilidade mecânica é o percentual de tempo fora de manutenção
        disp_mecanica = calcular_porcentagem(total_horas - manutencao, total_horas)
        
        resultados.append({
            'Frota': equipamento,
            'Disponibilidade': disp_mecanica
        })
    
    return pd.DataFrame(resultados)

def calcular_horas_por_frota(df):
    """
    Calcula o total de horas registradas para cada frota e a diferença para 24 horas.
    Calcula médias diárias considerando os dias efetivos de cada frota.
    Esta função NÃO aplica qualquer filtro de operador.
    Também identifica as faltas de horário por dia específico.
    
    Args:
        df (DataFrame): DataFrame processado
    
    Returns:
        DataFrame: Horas totais por frota com detalhamento por dia
    """
    # Agrupar por Equipamento e somar as diferenças de hora
    equipamentos = df['Equipamento'].unique()
    resultados = []
    
    # Obter todos os dias únicos no dataset
    dias_unicos = sorted(df['Data'].unique()) if 'Data' in df.columns else []
    
    for equipamento in equipamentos:
        dados_equip = df[df['Equipamento'] == equipamento]
        
        # Determinar número de dias efetivos para este equipamento
        dias_equip = dados_equip['Data'].nunique() if 'Data' in dados_equip.columns else 1
        
        total_horas = round(dados_equip['Diferença_Hora'].sum(), 2)
        
        # Se houver múltiplos dias, usar média diária
        if dias_equip > 1:
            total_horas = round(total_horas / dias_equip, 2)
        
        # Calcular a diferença para 24 horas
        diferenca_24h = round(max(24 - total_horas, 0), 2)
        
        # Criar o resultado básico (colunas originais mantidas)
        resultado = {
            'Frota': equipamento,
            'Horas Registradas': total_horas,
            'Diferença para 24h': diferenca_24h
        }
        
        # Adicionar detalhamento por dia (novas colunas)
        if len(dias_unicos) > 0:
            for dia in dias_unicos:
                dados_dia = dados_equip[dados_equip['Data'] == dia]
                
                # Se não houver dados para este dia e equipamento, a diferença é 24h
                if len(dados_dia) == 0:
                    resultado[f'Falta {dia}'] = 24.0
                    continue
                
                # Calcular horas registradas neste dia
                horas_dia = round(dados_dia['Diferença_Hora'].sum(), 2)
                
                # Calcular a diferença para 24 horas neste dia
                diferenca_dia = round(max(24 - horas_dia, 0), 2)
                
                # Adicionar ao resultado apenas se houver falta (diferença > 0)
                if diferenca_dia > 0:
                    resultado[f'Falta {dia}'] = diferenca_dia
                else:
                    resultado[f'Falta {dia}'] = 0.0
        
        resultados.append(resultado)
    
    return pd.DataFrame(resultados)

def calcular_eficiencia_energetica(base_calculo):
    """
    Calcula a eficiência energética por operador.
    Eficiência energética = Horas elevador / Horas motor ligado
    
    Args:
        base_calculo (DataFrame): Tabela Base Calculo
    
    Returns:
        DataFrame: Eficiência energética por operador
    """
    # Função para calcular valores com alta precisão e depois formatar
    def calcular_porcentagem(numerador, denominador, precisao=4):
        """Calcula porcentagem como decimal (0-1) evitando divisão por zero."""
        if denominador > 0:
            return round((numerador / denominador), precisao)
        return 0.0
    
    # Agrupar por operador (já filtrado pela função calcular_base_calculo)
    operadores = base_calculo[['Operador', 'Grupo Equipamento/Frente']].drop_duplicates()
    resultados = []
    
    for _, row in operadores.iterrows():
        operador = row['Operador']
        grupo = row['Grupo Equipamento/Frente']
        
        # Filtrar dados para este operador e grupo
        filtro = (base_calculo['Operador'] == operador) & (base_calculo['Grupo Equipamento/Frente'] == grupo)
        dados_op = base_calculo[filtro]
        
        # Eficiência Energética = horas elevador / motor ligado
        horas_elevador_sum = round(dados_op['Horas elevador'].sum(), 4)
        motor_ligado_sum = round(dados_op['Motor Ligado'].sum(), 4)
        
        # Calcular eficiência - já está em decimal, não precisa multiplicar por 100
        eficiencia = calcular_porcentagem(horas_elevador_sum, motor_ligado_sum)
        
        # Garantir que não ultrapasse 100%
        eficiencia = min(eficiencia, 1.0)
        
        resultados.append({
            'Operador': operador,
            'Eficiência': eficiencia
        })
    
    return pd.DataFrame(resultados)

def calcular_hora_elevador(df, base_calculo):
    """
    Calcula as horas de elevador por operador.
    Considera-se horas de elevador quando:
    - Esteira Ligada = 1
    - Pressão de Corte > 400
    
    Args:
        df (DataFrame): DataFrame base processado
        base_calculo (DataFrame): Tabela Base Calculo
    
    Returns:
        DataFrame: Horas de elevador por operador
    """
    # Agrupar por operador (já filtrado pela função calcular_base_calculo)
    operadores = base_calculo[['Operador', 'Grupo Equipamento/Frente']].drop_duplicates()
    resultados = []
    
    for _, row in operadores.iterrows():
        operador = row['Operador']
        grupo = row['Grupo Equipamento/Frente']
        
        # Filtrar dados para este operador e grupo
        filtro = (base_calculo['Operador'] == operador) & (base_calculo['Grupo Equipamento/Frente'] == grupo)
        dados_op = base_calculo[filtro]
        
        # Somar horas de elevador da base de cálculo (já filtradas corretamente)
        horas_elevador_sum = round(dados_op['Horas elevador'].sum(), 2)
        
        resultados.append({
            'Operador': operador,
            'Horas': horas_elevador_sum
        })
    
    return pd.DataFrame(resultados)

def calcular_motor_ocioso(base_calculo):
    """
    Calcula o percentual de motor ocioso por operador.
    
    Args:
        base_calculo (DataFrame): Tabela Base Calculo
    
    Returns:
        DataFrame: Percentual de motor ocioso por operador
    """
    # Função para calcular valores com alta precisão e depois formatar
    def calcular_porcentagem(numerador, denominador, precisao=4):
        """Calcula porcentagem como decimal (0-1) evitando divisão por zero."""
        if denominador > 0:
            return round((numerador / denominador), precisao)
        return 0.0
    
    # Agrupar por operador (já filtrado pela função calcular_base_calculo)
    operadores = base_calculo[['Operador', 'Grupo Equipamento/Frente']].drop_duplicates()
    resultados = []
    
    for _, row in operadores.iterrows():
        operador = row['Operador']
        grupo = row['Grupo Equipamento/Frente']
        
        # Filtrar dados para este operador e grupo
        filtro = (base_calculo['Operador'] == operador) & (base_calculo['Grupo Equipamento/Frente'] == grupo)
        dados_op = base_calculo[filtro]
        
        # Motor Ocioso = Parado Com Motor Ligado / Motor Ligado
        parado_motor_sum = round(dados_op['Parado Com Motor Ligado'].sum(), 4)
        motor_ligado_sum = round(dados_op['Motor Ligado'].sum(), 4)
        
        percentual = calcular_porcentagem(parado_motor_sum, motor_ligado_sum)
        
        resultados.append({
            'Operador': operador,
            'Porcentagem': percentual
        })
    
    return pd.DataFrame(resultados)

def calcular_uso_gps(df, base_calculo):
    """
    Calcula o percentual de uso de GPS por operador.
    O uso de GPS é definido como o tempo em que o equipamento está:
    - Estado é "TRABALHANDO" ou "COLHEITA" 
    - Piloto Automático (RTK) = 1
    - Velocidade > 0
    
    Args:
        df (DataFrame): DataFrame base processado
        base_calculo (DataFrame): Tabela Base Calculo
    
    Returns:
        DataFrame: Percentual de uso de GPS por operador
    """
    # Função para calcular valores com alta precisão e depois formatar
    def calcular_porcentagem(numerador, denominador, precisao=4):
        """Calcula porcentagem como decimal (0-1) evitando divisão por zero."""
        if denominador > 0:
            return round((numerador / denominador), precisao)
        return 0.0
    
    # Agrupar por operador (já filtrado pela função calcular_base_calculo)
    operadores = base_calculo[['Operador', 'Grupo Equipamento/Frente']].drop_duplicates()
    resultados = []
    
    for _, row in operadores.iterrows():
        operador = row['Operador']
        grupo = row['Grupo Equipamento/Frente']
        
        # Filtrar dados base para este operador e grupo
        filtro_base = (df['Operador'] == operador) & \
                      (df['Grupo Equipamento/Frente'] == grupo)
        dados_op_base = df[filtro_base]
        
        # Determinar número de dias efetivos para este operador/grupo
        dias_operador = dados_op_base['Data'].nunique() if 'Data' in dados_op_base.columns else 1
        
        # Calcular tempo total trabalhando
        tempo_trabalhando = round(dados_op_base[
            (dados_op_base['Estado'].isin(['TRABALHANDO', 'COLHEITA']))
        ]['Diferença_Hora'].sum(), 4)
        
        # Calcular tempo com GPS ativo (condições combinadas)
        tempo_gps_ativo = round(dados_op_base[
            (dados_op_base['Estado'].isin(['TRABALHANDO', 'COLHEITA'])) &
            (dados_op_base['RTK (Piloto Automatico)'] == 1) &
            (dados_op_base['Velocidade'] > 0)
        ]['Diferença_Hora'].sum(), 4)
        
        # Se houver múltiplos dias, usar médias diárias
        if dias_operador > 1:
            tempo_trabalhando = round(tempo_trabalhando / dias_operador, 4)
            tempo_gps_ativo = round(tempo_gps_ativo / dias_operador, 4)
        
        # Calcular percentual em formato decimal (0-1)
        percentual = calcular_porcentagem(tempo_gps_ativo, tempo_trabalhando)
        
        # Garantir que não ultrapasse 100% (1.0)
        percentual = min(percentual, 1.0)
        
        resultados.append({
            'Operador': operador,
            'Porcentagem': percentual
        })
    
    return pd.DataFrame(resultados)

def calcular_media_velocidade(df):
    """
    Calcula a média de velocidade para cada operador considerando apenas registros produtivos e deslocamentos.
    
    Args:
        df (DataFrame): DataFrame processado
    
    Returns:
        DataFrame: DataFrame com a média de velocidade por operador
    """
    # Filtramos os dados excluindo os operadores da lista de exclusão
    df_filtrado = df[~df['Operador'].isin(OPERADORES_EXCLUIR)]
    
    # Identificar registros produtivos e deslocamentos
    # Produtivos: onde Grupo Operacao é 'Produtiva'
    # Deslocamentos: onde Estado é 'DESLOCAMENTO' ou velocidade > 0 em operações não produtivas
    registros_validos = (
        (df_filtrado['Grupo Operacao'] == 'Produtiva') | 
        (df_filtrado['Estado'] == 'DESLOCAMENTO') |
        ((df_filtrado['Velocidade'] > 0) & (df_filtrado['Estado'] != 'PARADO'))
    )
    
    df_velocidade = df_filtrado[registros_validos]
    
    # Verificar se há dados para processar
    if len(df_velocidade) == 0:
        return pd.DataFrame(columns=['Operador', 'Velocidade'])
    
    # Determinar os dias efetivos para cada operador para cálculo de médias
    operadores = df_velocidade['Operador'].unique()
    resultados = []
    
    for operador in operadores:
        # Filtrar dados para este operador
        dados_op = df_velocidade[df_velocidade['Operador'] == operador]
        
        # Calcular a média de velocidade (ponderada pelo tempo, se houver a coluna Diferença_Hora)
        if 'Diferença_Hora' in dados_op.columns:
            # Média ponderada pelo tempo 
            velocidade_media = round(
                (dados_op['Velocidade'] * dados_op['Diferença_Hora']).sum() / dados_op['Diferença_Hora'].sum()
                if dados_op['Diferença_Hora'].sum() > 0 else 0,
                2
            )
        else:
            # Média simples
            velocidade_media = round(dados_op['Velocidade'].mean(), 2)
        
        resultados.append({
            'Operador': operador,
            'Velocidade': velocidade_media
        })
    
    return pd.DataFrame(resultados)

def identificar_operadores_duplicados(df):
    """
    Identifica operadores que aparecem com IDs diferentes no mesmo conjunto de dados.
    Detecta principalmente IDs que começam com '133' e têm 7 dígitos, verificando se
    existe outra ID com o mesmo nome mas com menos dígitos.
    
    Args:
        df (DataFrame): DataFrame com os dados dos operadores
    
    Returns:
        dict: Dicionário com mapeamento {id_incorreta: id_correta}
        DataFrame: DataFrame com as duplicidades encontradas para relatório
    """
    if 'Operador' not in df.columns or len(df) == 0:
        return {}, pd.DataFrame(columns=['ID Incorreta', 'ID Correta', 'Nome'])
    
    # Extrair operadores únicos
    operadores = df['Operador'].unique()
    
    # Mapear nomes para IDs
    nomes_para_ids = {}
    for op in operadores:
        if ' - ' in op:
            try:
                id_parte, nome_parte = op.split(' - ', 1)
                if nome_parte not in nomes_para_ids:
                    nomes_para_ids[nome_parte] = []
                nomes_para_ids[nome_parte].append(op)
            except:
                continue
    
    # Encontrar nomes com múltiplas IDs
    duplicidades = []
    mapeamento = {}
    
    for nome, ids in nomes_para_ids.items():
        if len(ids) > 1:
            # Verificar se uma das IDs inicia com 133 e tem 7 dígitos
            ids_longas = [id_op for id_op in ids if ' - ' in id_op and id_op.split(' - ')[0].startswith('133') and len(id_op.split(' - ')[0]) == 7]
            ids_curtas = [id_op for id_op in ids if id_op not in ids_longas]
            
            if ids_longas and ids_curtas:
                for id_longa in ids_longas:
                    # Encontrar a ID correta (a mais curta)
                    id_correta = min(ids_curtas, key=lambda x: len(x.split(' - ')[0]) if ' - ' in x else float('inf'))
                    
                    # Adicionar ao mapeamento
                    mapeamento[id_longa] = id_correta
                    
                    # Adicionar à lista de duplicidades para o relatório
                    duplicidades.append({
                        'ID Incorreta': id_longa,
                        'ID Correta': id_correta,
                        'Nome': nome
                    })
    
    print(f"Encontrados {len(duplicidades)} operadores com IDs duplicadas.")
    return mapeamento, pd.DataFrame(duplicidades)

def criar_excel_com_planilhas(df_base, base_calculo, disp_mecanica, eficiencia_energetica, 
                             hora_elevador, motor_ocioso, uso_gps, horas_por_frota, caminho_saida,
                             df_duplicados=None, media_velocidade=None):
    """
    Cria um arquivo Excel com todas as planilhas auxiliares.
    
    Args:
        df_base (DataFrame): DataFrame base processado
        base_calculo (DataFrame): Tabela Base Calculo
        disp_mecanica (DataFrame): Disponibilidade mecânica
        eficiencia_energetica (DataFrame): Eficiência energética
        hora_elevador (DataFrame): Horas de elevador
        motor_ocioso (DataFrame): Motor ocioso
        uso_gps (DataFrame): Uso GPS
        horas_por_frota (DataFrame): Horas totais registradas por frota
        caminho_saida (str): Caminho do arquivo Excel de saída
        df_duplicados (DataFrame, optional): Tabela de IDs duplicadas
        media_velocidade (DataFrame, optional): Média de velocidade por operador
    """
    writer = pd.ExcelWriter(caminho_saida, engine='openpyxl')
    
    # Arredondamento fixo para 2 casas decimais em todas as colunas numéricas antes de exportar
    # Base Calculo - garantir que todas as colunas numéricas tenham 2 casas decimais
    colunas_numericas = ['Horas totais', 'Horas elevador', '%', 'RTK', 'Horas Produtivas', 
                         '% Utilização RTK', 'Motor Ligado', '% Eficiência Elevador', 
                         'Parado Com Motor Ligado', '% Parado com motor ligado']
    
    for col in colunas_numericas:
        if col in base_calculo.columns:
            base_calculo[col] = base_calculo[col].apply(lambda x: round(x, 2))
    
    # Arredondar valores nas outras planilhas
    disp_mecanica['Disponibilidade'] = disp_mecanica['Disponibilidade'].apply(lambda x: round(x, 4))
    eficiencia_energetica['Eficiência'] = eficiencia_energetica['Eficiência'].apply(lambda x: round(x, 4))
    hora_elevador['Horas'] = hora_elevador['Horas'].apply(lambda x: round(x, 2))
    motor_ocioso['Porcentagem'] = motor_ocioso['Porcentagem'].apply(lambda x: round(x, 4))
    uso_gps['Porcentagem'] = uso_gps['Porcentagem'].apply(lambda x: round(x, 4))
    
    # Arredondar apenas as colunas originais em horas_por_frota (mantendo as novas colunas intactas)
    horas_por_frota['Horas Registradas'] = horas_por_frota['Horas Registradas'].apply(lambda x: round(x, 2))
    horas_por_frota['Diferença para 24h'] = horas_por_frota['Diferença para 24h'].apply(lambda x: round(x, 2))
    
    # Arredondar as colunas de falta por dia
    for col in horas_por_frota.columns:
        if col.startswith('Falta '):
            horas_por_frota[col] = horas_por_frota[col].apply(lambda x: round(x, 2) if pd.notna(x) else x)
    
    # Salvar cada DataFrame em uma planilha separada
    df_base.to_excel(writer, sheet_name='BASE', index=False)
    base_calculo.to_excel(writer, sheet_name='Base Calculo', index=False)
    
    # Planilhas auxiliares (formatadas conforme necessário)
    disp_mecanica.to_excel(writer, sheet_name='1_Disponibilidade Mecânica', index=False)
    eficiencia_energetica.to_excel(writer, sheet_name='2_Eficiência Energética', index=False)
    hora_elevador.to_excel(writer, sheet_name='3_Hora Elevador', index=False)
    motor_ocioso.to_excel(writer, sheet_name='4_Motor Ocioso', index=False)
    uso_gps.to_excel(writer, sheet_name='5_Uso GPS', index=False)
    horas_por_frota.to_excel(writer, sheet_name='Horas por Frota', index=False)
    
    # Adicionar planilha de Média Velocidade, se existir
    if media_velocidade is not None and not media_velocidade.empty:
        media_velocidade.to_excel(writer, sheet_name='Média Velocidade', index=False)
    
    # Adicionar planilha de IDs duplicadas, se existir
    if df_duplicados is not None and not df_duplicados.empty:
        df_duplicados.to_excel(writer, sheet_name='IDs Duplicadas', index=False)
    
    # Aplicar formatação nas planilhas
    workbook = writer.book
    
    # Definir larguras de colunas padrão
    def ajustar_largura_colunas(worksheet):
        """Ajusta a largura das colunas da planilha"""
        for col in worksheet.columns:
            # Definir uma largura mínima para todas as colunas
            max_length = 10
            column = col[0].column_letter  # Obter a letra da coluna
            
            # Verificar largura baseada no conteúdo do cabeçalho
            header_text = str(col[0].value)
            if header_text:
                max_length = max(max_length, len(header_text) + 2)  # +2 para dar espaço extra
            
            # Ajustar a largura baseada no conteúdo das células (amostragem)
            for cell in col[1:min(20, len(col))]:  # Limitar a verificação a 20 linhas para performance
                if cell.value:
                    cell_text = str(cell.value)
                    max_length = max(max_length, len(cell_text) + 2)
            
            # Limitar a largura máxima para evitar colunas excessivamente largas
            max_length = min(max_length, 40)
            
            # Definir a largura da coluna
            worksheet.column_dimensions[column].width = max_length
    
    # Formatar planilha de Disponibilidade Mecânica
    worksheet = workbook['1_Disponibilidade Mecânica']
    ajustar_largura_colunas(worksheet)
    for row in range(2, worksheet.max_row + 1):  # Começando da linha 2 (ignorando cabeçalho)
        cell = worksheet.cell(row=row, column=2)  # Coluna B (Disponibilidade)
        cell.number_format = '0.00%'  # Formato de porcentagem com 2 casas
    
    # Formatar planilha de Eficiência Energética
    worksheet = workbook['2_Eficiência Energética']
    ajustar_largura_colunas(worksheet)
    for row in range(2, worksheet.max_row + 1):
        cell = worksheet.cell(row=row, column=2)  # Coluna B (Eficiência)
        cell.number_format = '0.00%'  # Formato de porcentagem com 2 casas
    
    # Formatar planilha de Hora Elevador
    worksheet = workbook['3_Hora Elevador']
    ajustar_largura_colunas(worksheet)
    for row in range(2, worksheet.max_row + 1):
        cell = worksheet.cell(row=row, column=2)  # Coluna B (Horas)
        cell.number_format = '0.00'  # Formato decimal com 2 casas
    
    # Formatar planilha de Motor Ocioso
    worksheet = workbook['4_Motor Ocioso']
    ajustar_largura_colunas(worksheet)
    for row in range(2, worksheet.max_row + 1):
        cell = worksheet.cell(row=row, column=2)  # Coluna B (Porcentagem)
        cell.number_format = '0.00%'  # Formato de porcentagem com 2 casas
    
    # Formatar planilha de Uso GPS
    worksheet = workbook['5_Uso GPS']
    ajustar_largura_colunas(worksheet)
    for row in range(2, worksheet.max_row + 1):
        cell = worksheet.cell(row=row, column=2)  # Coluna B (Porcentagem)
        cell.number_format = '0.00%'  # Formato de porcentagem com 2 casas
    
    # Formatar planilha de Média Velocidade
    if media_velocidade is not None and not media_velocidade.empty:
        worksheet = workbook['Média Velocidade']
        ajustar_largura_colunas(worksheet)
        for row in range(2, worksheet.max_row + 1):
            cell = worksheet.cell(row=row, column=2)  # Coluna B (Velocidade)
            cell.number_format = '0.00'  # Formato decimal normal com 2 casas
    
    # Formatar planilha de Base Calculo
    worksheet = workbook['Base Calculo']
    ajustar_largura_colunas(worksheet)
    for row in range(2, worksheet.max_row + 1):
        # Formatar colunas decimais
        columns_decimal = [4, 5, 7, 8, 10, 12]  # Colunas D, E, G, H, J, L (Horas totais, Horas elevador, etc.)
        for col in columns_decimal:
            if col <= worksheet.max_column:
                cell = worksheet.cell(row=row, column=col)
                cell.number_format = '0.00'  # Formato decimal com 2 casas
        
        # Formatar colunas de porcentagem
        columns_percent = [6, 9, 11, 13]  # Colunas F, I, K, M (%, % Utilização RTK, etc.)
        for col in columns_percent:
            if col <= worksheet.max_column:
                cell = worksheet.cell(row=row, column=col)
                cell.number_format = '0.00%'  # Formato de porcentagem com 2 casas
    
    # Formatar planilha de Horas por Frota
    worksheet = workbook['Horas por Frota']
    ajustar_largura_colunas(worksheet)
    
    # Identificar colunas específicas por nome para garantir compatibilidade
    for row in range(2, worksheet.max_row + 1):
        # Formatar todas as colunas como decimais
        for col in range(2, worksheet.max_column + 1):
            cell = worksheet.cell(row=row, column=col)
            cell.number_format = '0.00'  # Formato decimal com 2 casas
        
        # Destacar visualmente as colunas originais (opcional)
        # Para as primeiras três colunas, manter a formatação original sem destaque
    
    # Ajustar a planilha BASE (apenas largura das colunas)
    worksheet = workbook['BASE']
    ajustar_largura_colunas(worksheet)
    
    # Ajustar a planilha de IDs duplicadas, se existir
    if df_duplicados is not None and not df_duplicados.empty:
        worksheet = workbook['IDs Duplicadas']
        ajustar_largura_colunas(worksheet)
    
    writer.close()
    print(f"Arquivo Excel salvo com sucesso em {caminho_saida}")

def extrair_arquivo_zip(caminho_zip, pasta_destino=None):
    """
    Extrai o conteúdo de um arquivo ZIP para uma pasta temporária ou destino especificado.
    Renomeia os arquivos extraídos para terem o mesmo nome do arquivo ZIP original.
    
    Args:
        caminho_zip (str): Caminho para o arquivo ZIP
        pasta_destino (str, optional): Pasta onde os arquivos serão extraídos.
                                       Se None, usa uma pasta temporária.
    
    Returns:
        list: Lista de caminhos dos arquivos extraídos e renomeados (apenas TXT e CSV)
        str: Caminho da pasta temporária (se criada) ou None
    """
    # Se pasta_destino não foi especificada, criar uma pasta temporária
    pasta_temp = None
    if pasta_destino is None:
        pasta_temp = tempfile.mkdtemp()
        pasta_destino = pasta_temp
    
    arquivos_extraidos = []
    nome_zip_sem_extensao = os.path.splitext(os.path.basename(caminho_zip))[0]
    
    try:
        with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
            # Extrair todos os arquivos do ZIP
            zip_ref.extractall(pasta_destino)
            
            # Processar cada arquivo extraído (apenas TXT e CSV)
            for arquivo in zip_ref.namelist():
                caminho_completo = os.path.join(pasta_destino, arquivo)
                # Verificar se é um arquivo e não uma pasta
                if os.path.isfile(caminho_completo):
                    # Verificar extensão
                    extensao = os.path.splitext(arquivo)[1].lower()
                    if extensao in ['.txt', '.csv']:
                        # Criar novo nome: nome do ZIP + extensão original
                        novo_nome = f"{nome_zip_sem_extensao}{extensao}"
                        novo_caminho = os.path.join(pasta_destino, novo_nome)
                        
                        # Renomear o arquivo extraído
                        try:
                            # Se já existe um arquivo com esse nome, remover primeiro
                            if os.path.exists(novo_caminho):
                                os.remove(novo_caminho)
                            # Renomear o arquivo
                            os.rename(caminho_completo, novo_caminho)
                            arquivos_extraidos.append(novo_caminho)
                            print(f"Arquivo extraído renomeado: {novo_nome}")
                        except Exception as e:
                            print(f"Erro ao renomear arquivo {arquivo} para {novo_nome}: {str(e)}")
                            arquivos_extraidos.append(caminho_completo)  # Adicionar o caminho original em caso de erro
        
        return arquivos_extraidos, pasta_temp
    
    except Exception as e:
        print(f"Erro ao extrair o arquivo ZIP {caminho_zip}: {str(e)}")
        # Se houve erro e criamos uma pasta temporária, tentar limpá-la
        if pasta_temp:
            try:
                shutil.rmtree(pasta_temp)
            except:
                pass
        return [], None

def processar_todos_arquivos():
    """
    Processa todos os arquivos TXT, CSV ou ZIP de colhedoras nas pastas dados e dados/colhedoras.
    Ignora arquivos que contenham "transbordo" no nome.
    """
    # Obter o diretório onde está o script
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    
    # Diretório raiz do projeto
    diretorio_raiz = os.path.dirname(diretorio_script)
    
    # Diretórios para dados de entrada e saída
    diretorio_dados = os.path.join(diretorio_raiz, "dados")
    diretorio_colhedoras = os.path.join(diretorio_raiz, "dados", "colhedoras")
    diretorio_saida = os.path.join(diretorio_raiz, "output")
    
    # Verificar se os diretórios existem, caso contrário criar
    if not os.path.exists(diretorio_dados):
        os.makedirs(diretorio_dados)
    if not os.path.exists(diretorio_colhedoras):
        os.makedirs(diretorio_colhedoras)
    if not os.path.exists(diretorio_saida):
        os.makedirs(diretorio_saida)
    
    # Lista de diretórios para buscar arquivos
    diretorios_busca = [diretorio_dados, diretorio_colhedoras]
    
    # Encontrar todos os arquivos TXT/CSV/ZIP de colhedoras em ambos os diretórios
    arquivos = []
    arquivos_zip = []
    
    for diretorio in diretorios_busca:
        # Adicionar arquivos TXT sempre
        arquivos += glob.glob(os.path.join(diretorio, "RV Colhedora*.txt"))
        arquivos += glob.glob(os.path.join(diretorio, "*colhedora*.txt"))
        arquivos += glob.glob(os.path.join(diretorio, "colhedora*.txt"))
        
        # Adicionar arquivos CSV apenas se processCsv for True
        if processCsv:
            arquivos += glob.glob(os.path.join(diretorio, "RV Colhedora*.csv"))
            arquivos += glob.glob(os.path.join(diretorio, "*colhedora*.csv"))
            arquivos += glob.glob(os.path.join(diretorio, "colhedora*.csv"))
        
        # Adicionar arquivos ZIP
        arquivos_zip += glob.glob(os.path.join(diretorio, "RV Colhedora*.zip"))
        arquivos_zip += glob.glob(os.path.join(diretorio, "*colhedora*.zip"))
        arquivos_zip += glob.glob(os.path.join(diretorio, "colhedora*.zip"))
    
    # Filtrar arquivos que contenham "transbordo" no nome (case insensitive)
    arquivos = [arquivo for arquivo in arquivos if "transbordo" not in os.path.basename(arquivo).lower()]
    arquivos_zip = [arquivo for arquivo in arquivos_zip if "transbordo" not in os.path.basename(arquivo).lower()]
    
    # Remover possíveis duplicatas
    arquivos = list(set(arquivos))
    arquivos_zip = list(set(arquivos_zip))
    
    if not arquivos and not arquivos_zip:
        print("Nenhum arquivo de colhedoras encontrado nas pastas dados ou dados/colhedoras!")
        return
    
    print(f"Encontrados {len(arquivos)} arquivos de colhedoras (TXT/CSV) para processar.")
    print(f"Encontrados {len(arquivos_zip)} arquivos ZIP de colhedoras para processar.")
    
    # Processar cada arquivo TXT/CSV
    for arquivo in arquivos:
        processar_arquivo(arquivo, diretorio_saida)
    
    # Processar cada arquivo ZIP
    for arquivo_zip in arquivos_zip:
        print(f"\nProcessando arquivo ZIP: {os.path.basename(arquivo_zip)}")
        
        # Extrair arquivo ZIP para pasta temporária
        arquivos_extraidos, pasta_temp = extrair_arquivo_zip(arquivo_zip)
        
        if not arquivos_extraidos:
            print(f"Nenhum arquivo TXT ou CSV encontrado no ZIP {os.path.basename(arquivo_zip)}")
            continue
        
        print(f"Extraídos {len(arquivos_extraidos)} arquivos do ZIP.")
        
        # Processar cada arquivo extraído
        for arquivo_extraido in arquivos_extraidos:
            # Filtrar arquivos que contenham "transbordo" no nome
            if "transbordo" not in os.path.basename(arquivo_extraido).lower():
                processar_arquivo(arquivo_extraido, diretorio_saida)
        
        # Limpar pasta temporária se foi criada
        if pasta_temp:
            try:
                shutil.rmtree(pasta_temp)
                print(f"Pasta temporária removida: {pasta_temp}")
            except Exception as e:
                print(f"Erro ao remover pasta temporária {pasta_temp}: {str(e)}")

def carregar_substituicoes_operadores():
    """
    Carrega o arquivo substituiroperadores.json que contém os mapeamentos 
    de substituição de operadores.
    
    Returns:
        dict: Dicionário com mapeamento {operador_origem: operador_destino}
        ou dicionário vazio se o arquivo não existir ou for inválido
    """
    # Obter o diretório onde está o script
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    
    # Diretório raiz do projeto
    diretorio_raiz = os.path.dirname(diretorio_script)
    
    # Caminho para o arquivo de substituição
    arquivo_substituicao = os.path.join(diretorio_raiz, "substituiroperadores.json")
    
    # Verificar se o arquivo existe
    if not os.path.exists(arquivo_substituicao):
        print(f"Arquivo de substituição de operadores não encontrado: {arquivo_substituicao}")
        return {}
    
    try:
        # Carregar o arquivo JSON
        with open(arquivo_substituicao, 'r', encoding='utf-8') as f:
            substituicoes = json.load(f)
        
        # Criar dicionário de substituições
        mapeamento = {item['operador_origem']: item['operador_destino'] for item in substituicoes}
        
        print(f"Carregadas {len(mapeamento)} substituições de operadores.")
        return mapeamento
        
    except Exception as e:
        print(f"Erro ao carregar arquivo de substituição de operadores: {str(e)}")
        return {}

def aplicar_substituicao_operadores(df, mapeamento_substituicoes):
    """
    Aplica as substituições de operadores no DataFrame.
    
    Args:
        df (DataFrame): DataFrame a ser processado
        mapeamento_substituicoes (dict): Dicionário com mapeamento {operador_origem: operador_destino}
    
    Returns:
        DataFrame: DataFrame com as substituições aplicadas
    """
    if not mapeamento_substituicoes or 'Operador' not in df.columns:
        return df
    
    # Criar uma cópia para não alterar o DataFrame original
    df_modificado = df.copy()
    
    # Contar operadores antes da substituição
    contagem_antes = df_modificado['Operador'].value_counts()
    
    # Aplicar as substituições
    df_modificado['Operador'] = df_modificado['Operador'].replace(mapeamento_substituicoes)
    
    # Contar operadores depois da substituição
    contagem_depois = df_modificado['Operador'].value_counts()
    
    # Verificar quais operadores foram substituídos
    for operador_origem, operador_destino in mapeamento_substituicoes.items():
        if operador_origem in contagem_antes and operador_origem not in contagem_depois:
            print(f"Operador '{operador_origem}' substituído por '{operador_destino}'")
    
    return df_modificado

def processar_arquivo(caminho_arquivo, diretorio_saida):
    """
    Processa um único arquivo e gera o Excel de saída.
    
    Args:
        caminho_arquivo (str): Caminho do arquivo a ser processado
        diretorio_saida (str): Diretório onde o arquivo de saída será salvo
    """
    # Obter apenas o nome do arquivo (sem caminho e sem extensão)
    nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
    
    # Nome de saída igual ao original, mas com extensão .xlsx na pasta output
    arquivo_saida = os.path.join(diretorio_saida, f"{nome_base}.xlsx")
    
    print(f"\nProcessando arquivo: {os.path.basename(caminho_arquivo)}")
    print(f"Arquivo de saída: {os.path.basename(arquivo_saida)}")
    
    # Processar o arquivo base
    df_base = processar_arquivo_base(caminho_arquivo)
    if df_base is None:
        print(f"Erro ao processar {os.path.basename(caminho_arquivo)}. Pulando para o próximo arquivo.")
        return
    
    # Identificar operadores duplicados antes de aplicar as substituições manuais
    mapeamento_duplicados, df_duplicados = identificar_operadores_duplicados(df_base)
    
    # Carregar e aplicar substituições de operadores (manuais + automáticas)
    substituicoes = carregar_substituicoes_operadores()
    
    # Combinar as substituições manuais com as automáticas (automáticas têm precedência)
    substituicoes_combinadas = {**substituicoes, **mapeamento_duplicados}
    
    if substituicoes_combinadas:
        df_base = aplicar_substituicao_operadores(df_base, substituicoes_combinadas)
    
    # Se o DataFrame estiver vazio, gerar apenas a planilha BASE
    if len(df_base) == 0:
        writer = pd.ExcelWriter(arquivo_saida, engine='openpyxl')
        df_base.to_excel(writer, sheet_name='BASE', index=False)
        if not df_duplicados.empty:
            df_duplicados.to_excel(writer, sheet_name='IDs Duplicadas', index=False)
        writer.close()
        print(f"Arquivo {arquivo_saida} gerado com apenas a planilha BASE (sem dados).")
        return
    
    # ORDENAR o DataFrame base por Equipamento e depois por Hora
    # Isso garante que os registros sejam agrupados por frota na visualização
    if 'Data' in df_base.columns:
        # Ordenar por Equipamento, Data e depois Hora
        df_base = df_base.sort_values(by=['Equipamento', 'Data', 'Hora'])
    else:
        # Se não tiver Data, ordenar apenas por Equipamento e Hora
        df_base = df_base.sort_values(by=['Equipamento', 'Hora'])
    
    # Calcular a Base Calculo
    base_calculo = calcular_base_calculo(df_base)
    
    # Calcular as métricas auxiliares
    disp_mecanica = calcular_disponibilidade_mecanica(df_base)
    eficiencia_energetica = calcular_eficiencia_energetica(base_calculo)
    hora_elevador = calcular_hora_elevador(df_base, base_calculo)
    motor_ocioso = calcular_motor_ocioso(base_calculo)
    uso_gps = calcular_uso_gps(df_base, base_calculo)
    horas_por_frota = calcular_horas_por_frota(df_base)
    
    # Calcular média de velocidade por operador
    media_velocidade = calcular_media_velocidade(df_base)
    
    # Criar o arquivo Excel com todas as planilhas
    criar_excel_com_planilhas(
        df_base, base_calculo, disp_mecanica, eficiencia_energetica,
        hora_elevador, motor_ocioso, uso_gps, horas_por_frota, arquivo_saida,
        df_duplicados,  # Adicionar a tabela de IDs duplicadas
        media_velocidade  # Adicionar a tabela de média de velocidade
    )
    
    print(f"Arquivo {arquivo_saida} gerado com sucesso!")

if __name__ == "__main__":
    print("="*80)
    print("Iniciando processamento de arquivos de colhedoras...")
    print(f"Processamento de arquivos CSV: {'ATIVADO' if processCsv else 'DESATIVADO'}")
    print("Este script processa arquivos de colhedoras e gera planilhas Excel com métricas")
    print("Suporta arquivos TXT, CSV e ZIP")
    print("Ignorando arquivos que contenham 'transbordo' no nome")
    print("="*80)
    processar_todos_arquivos()
    print("\nProcessamento concluído!") 