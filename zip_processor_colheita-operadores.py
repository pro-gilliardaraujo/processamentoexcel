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
from openpyxl.utils import get_column_letter
import re
import time
import builtins as _builtins

# Configurações
processCsv = True  # Altere para True quando quiser processar arquivos CSV
LIMPAR_ARQUIVOS = False  # Altere para True em produção para limpar arquivos após processamento

# Configurações para operações produtivas (CORREÇÃO INTELIGENTE DE INTERVALOS)
OPERACOES_PRODUTIVAS_COLHEITA = [
    'colhendo', 'colheita', 'trabalhando', 'operando', 'carregando',
    'descarregando', 'em operação', 'produtivo', 'ativo'
]

# Parâmetros de correção
INTERVALO_NORMAL_MIN = 3     # minutos mínimos considerados normais
INTERVALO_NORMAL_MAX = 12    # minutos máximos considerados normais
INTERVALO_ANOMALO_MIN = 30   # minutos mínimos para considerar anômalo

# Constantes
COLUNAS_REMOVER = [
    'Justificativa Corte Base Desligado',
    'Regional',
    'Tipo de Equipamento',
    'Unidade',
    'Centro de Custo',
    'Trabalhando em File',
    'Trabalhando Frente Dividida',
    'Trabalhando em Fila'
]

COLUNAS_DESEJADAS = [
    'Data', 'Hora', 'Equipamento', 'Apertura do Rolo', 'Codigo da Operacao',
    'Codigo Frente (digitada)', 'Corporativo', 'Corte Base Automatico/Manual',
    'Descricao Equipamento', 'Estado', 'Estado Operacional', 'Esteira Ligada',
    'Field Cruiser', 'Grupo Equipamento/Frente', 'Grupo Operacao', 'Horimetro',
    'Implemento Ligado', 'Motor Ligado', 'Operacao', 'Operador', 'Pressao de Corte',
    'RPM Extrator', 'RPM Motor', 'RTK (Piloto Automatico)', 'Fazenda', 'Zona',
    'Talhao', 'Velocidade', 'Diferença_Hora', 'Parada com Motor Ligado',
    'Horas Produtivas','Latitude','Longitude',
]

# Valores a serem filtrados
OPERADORES_EXCLUIR = ["9999 - TROCA DE TURNO", "1 - SEM OPERADOR"]

# Mapeamento de valores booleanos para 1/0
MAPEAMENTO_BOOLEANO = {
    'VERDADEIRO': 1, 'FALSO': 0,
    'TRUE': 1, 'FALSE': 0,
    'LIGADO': 1, 'DESLIGADO': 0,
    True: 1, False: 0,
    1: 1, 0: 0
}

# ============================================================
# CONTROLE DE LOG
# ============================================================
# Deixe VERBOSE = True para restaurar todos os prints detalhados.
# Mantemos impressões que contenham palavras-chave importantes
# (💾, ⚠️, ❌, ===, CSV coordenadas, Gerando, PROCESSAMENTO CONCLUÍDO).

VERBOSE = False

def _filtered_print(*args, **kwargs):
    if VERBOSE:
        _builtins.print(*args, **kwargs)
    else:
        texto = str(args[0]) if args else ""
        keywords = ["💾", "⚠️", "❌", "✅", "===", "CSV coordenadas", "PROCESSAMENTO CONCLUÍDO", "🗺️", "mapas", "Mapa", "UsoGPS", "URLs", "Supabase"]
        if any(k in texto for k in keywords):
            _builtins.print(*args, **kwargs)

# Substitui print globalmente dentro deste módulo
print = _filtered_print

def carregar_config_calculos():
    """
    Retorna as configurações de cálculos embutidas diretamente no código.
    As configurações são as mesmas definidas no arquivo calculos_config.json.
    """
    # Configurações embutidas diretamente no código
    config = {
        "CD": {
            "motor_ocioso": {
                "tipo_calculo": "Remover do cálculo",
                "operacoes_excluidas": [
                    "8490 - LAVAGEM",
                    "MANUTENCAO",
                    "LAVAGEM",
                    "INST CONFIG TECNOL EMBARCADAS",
                    "1055 - MANOBRA"
                ],
                "grupos_operacao_excluidos": [
                    "Manutenção", 
                    "Inaptidão"
                ]
            },
            "equipamentos_excluidos": []
        },
        "TT": {
            "motor_ocioso": {
                "tipo_calculo": "Remover do cálculo",
                "operacoes_excluidas": [
                    "9016 - ENCH SISTEMA FREIO",
                    "6340 - BASCULANDO  TRANSBORDAGEM",
                    "9024 - DESATOLAMENTO",
                    "MANUTENCAO",
                    "MANUTENÇÃO",
                    "INST CONFIG TECNOL EMBARCADAS",
                    "1055 - MANOBRA"
                ],
                "grupos_operacao_excluidos": [
                    "Manutenção", 
                    "Inaptidão"
                ]
            },
            "equipamentos_excluidos": []
        }
    }
    
    print("Usando configurações embutidas no código, ignorando o arquivo calculos_config.json")
    return config

def calcular_motor_ocioso_novo(df):
    """
    Calcula o tempo de motor ocioso de acordo com as novas regras:
    1. Intervalo é fechado quando encontra 'Parada com Motor Ligado = 0' com duração > 1 minuto
    2. Soma sequências de 'Parada com Motor Ligado = 1' com 'Parada com Motor Ligado = 0' < 1 minuto
    3. Se o total > 1 minuto, subtrai 1 minuto; se menor, descarta o intervalo
    
    Args:
        df (DataFrame): DataFrame com os dados de operação
        
    Returns:
        DataFrame: DataFrame com a coluna 'Motor Ocioso' atualizada
    """
    # Converter a coluna de diferença para minutos
    df['Diferença_Minutos'] = df['Diferença_Hora'] * 60
    
    # Inicializar colunas
    df['Motor Ocioso'] = 0
    df['Em_Intervalo'] = False
    df['Soma_Intervalo'] = 0
    
    # Variáveis para controle do intervalo atual
    em_intervalo = False
    soma_intervalo = 0
    inicio_intervalo = None
    
    # Iterar sobre as linhas do DataFrame
    for i in range(len(df)):
        parada_motor = df.iloc[i]['Parada com Motor Ligado']
        diferenca = df.iloc[i]['Diferença_Minutos']
        
        # Se não estamos em um intervalo
        if not em_intervalo:
            # Se encontrar Parada com Motor Ligado = 1, inicia novo intervalo
            if parada_motor == 1:
                em_intervalo = True
                soma_intervalo = diferenca
                inicio_intervalo = i
                df.at[i, 'Em_Intervalo'] = True
                df.at[i, 'Soma_Intervalo'] = soma_intervalo
        
        # Se estamos em um intervalo
        else:
            # Se encontrar Parada com Motor Ligado = 0
            if parada_motor == 0:
                # Se a duração for > 1 minuto, fecha o intervalo
                if diferenca > 1:
                    # Se o total acumulado > 1 minuto, subtrai 1 minuto
                    if soma_intervalo > 1:
                        tempo_ocioso = soma_intervalo - 1
                        # Atribui o tempo ocioso à primeira linha do intervalo
                        # IMPORTANTE: Converter de minutos para horas antes de atribuir
                        df.at[inicio_intervalo, 'Motor Ocioso'] = tempo_ocioso / 60.0  # CORREÇÃO: Dividir por 60 para converter minutos em horas
                    
                    # Reseta o intervalo
                    em_intervalo = False
                    soma_intervalo = 0
                    inicio_intervalo = None
                else:
                    # Se <= 1 minuto, soma ao intervalo atual
                    soma_intervalo += diferenca
                    df.at[i, 'Em_Intervalo'] = True
                    df.at[i, 'Soma_Intervalo'] = soma_intervalo
            
            # Se encontrar Parada com Motor Ligado = 1
            else:
                soma_intervalo += diferenca
                df.at[i, 'Em_Intervalo'] = True
                df.at[i, 'Soma_Intervalo'] = soma_intervalo
    
    # Tratar último intervalo aberto, se houver
    if em_intervalo and soma_intervalo > 1:
        tempo_ocioso = soma_intervalo - 1
        # CORREÇÃO: Converter de minutos para horas antes de atribuir
        df.at[inicio_intervalo, 'Motor Ocioso'] = tempo_ocioso / 60.0  # Dividir por 60 para converter minutos em horas
    
    # Remover colunas auxiliares
    df = df.drop(['Diferença_Minutos', 'Em_Intervalo', 'Soma_Intervalo'], axis=1)
    
    # Garantir que o tempo ocioso nunca seja maior que o tempo ligado para cada registro
    for i in range(len(df)):
        if df.iloc[i]['Motor Ocioso'] > 0:
            # Se o motor estiver ligado, limitar o tempo ocioso ao tempo ligado
            if df.iloc[i]['Motor Ligado'] == 1:
                tempo_hora = df.iloc[i]['Diferença_Hora']
                if df.iloc[i]['Motor Ocioso'] > tempo_hora:
                    df.at[i, 'Motor Ocioso'] = tempo_hora
            else:
                # Se o motor não estiver ligado, o tempo ocioso deve ser zero
                df.at[i, 'Motor Ocioso'] = 0
    
    return df

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
                # Processamento de data e hora
                df[['Data', 'Hora']] = df['Data/Hora'].str.split(' ', expand=True)
                df = df.drop(columns=['Data/Hora'])
                
                # Conversão e cálculo de diferenças de hora
                df['Hora'] = pd.to_datetime(df['Hora'], format='%H:%M:%S')
                df['Diferença_Hora'] = df['Hora'].diff().dt.total_seconds() / 3600
                df['Diferença_Hora'] = df['Diferença_Hora'].apply(lambda x: max(x, 0))
                
                # Nova regra: se Diferença_Hora > 0.50, então 0
                df['Diferença_Hora'] = df['Diferença_Hora'].apply(lambda x: 0 if x > 0.50 else x)
                
                # NOVA FUNCIONALIDADE: Aplicar correção inteligente de intervalos
                df = aplicar_correcao_intervalos_inteligente(df, tipo_operacao='colheita')
            
            # Cálculos adicionais
            RPM_MINIMO = 300  # Definindo constante para RPM mínimo

            # Carregar configurações
            config = carregar_config_calculos()
            operacoes_excluidas = config['CD']['motor_ocioso']['operacoes_excluidas']
            grupos_operacao_excluidos = config['CD']['motor_ocioso']['grupos_operacao_excluidos']

            # Filtrar dados para cálculo de motor ocioso
            df_motor_ocioso = df[
                ~df['Operacao'].isin(operacoes_excluidas) & 
                ~df['Grupo Operacao'].isin(grupos_operacao_excluidos)
            ]

            # Calcular Parada com Motor Ligado usando dados filtrados
            df['Parada com Motor Ligado'] = 0  # Inicializa com 0
            df.loc[df_motor_ocioso.index, 'Parada com Motor Ligado'] = (
                (df_motor_ocioso['Velocidade'] == 0) & 
                (df_motor_ocioso['RPM Motor'] >= RPM_MINIMO)
            ).astype(int)
            
            # Aplicar o novo cálculo de motor ocioso com intervalos de 1 minuto
            df = calcular_motor_ocioso_novo(df)
            
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
    
    Cálculos principais:
    - Horas totais: soma de Diferença_Hora
    - Horas elevador: soma de Diferença_Hora onde Esteira Ligada = 1 E Pressão de Corte > 400
    - Motor Ligado: soma de Diferença_Hora onde Motor Ligado = 1
    - Parado Com Motor Ligado: MÉTODO AVANÇADO - soma da coluna Motor Ocioso, que usa o cálculo com intervalos
    
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
        
        # Horas totais - soma de Diferença_Hora (IGUAL AO ORIGINAL)
        horas_totais = dados_filtrados['Diferença_Hora'].sum()
        if dias_operador > 1:
            horas_totais = horas_totais / dias_operador
        
        # Motor Ligado - soma de Diferença_Hora onde Motor Ligado = 1 (IGUAL AO ORIGINAL)
        motor_ligado = dados_filtrados[
            dados_filtrados['Motor Ligado'] == 1
        ]['Diferença_Hora'].sum()
        if dias_operador > 1:
            motor_ligado = motor_ligado / dias_operador
        
        # Horas elevador - soma de Diferença_Hora onde Esteira Ligada = 1 E Pressão de Corte > 400 (IGUAL AO ORIGINAL)
        horas_elevador = dados_filtrados[
            (dados_filtrados['Esteira Ligada'] == 1) & 
            (dados_filtrados['Pressao de Corte'] > 400)
        ]['Diferença_Hora'].sum()
        if dias_operador > 1:
            horas_elevador = horas_elevador / dias_operador
        
        # Percentual horas elevador (em decimal 0-1)
        percent_elevador = calcular_porcentagem(horas_elevador, horas_totais)
        
        # RTK - soma de Diferença_Hora onde todas as condições são atendidas (IGUAL AO ORIGINAL)
        rtk = dados_filtrados[
            (dados_filtrados['Grupo Operacao'] == 'Produtiva') &
            (dados_filtrados['Pressao de Corte'] >= 400) &
            (dados_filtrados['RTK (Piloto Automatico)'] == 1) &
            (dados_filtrados['Esteira Ligada'] == 1)
        ]['Diferença_Hora'].sum()
        if dias_operador > 1:
            rtk = rtk / dias_operador
        
        # Horas Produtivas (IGUAL AO ORIGINAL)
        horas_produtivas = dados_filtrados[
            dados_filtrados['Grupo Operacao'] == 'Produtiva'
        ]['Diferença_Hora'].sum()
        if dias_operador > 1:
            horas_produtivas = horas_produtivas / dias_operador
        
        # % Utilização RTK (em decimal 0-1)
        utilizacao_rtk = calcular_porcentagem(rtk, horas_produtivas)
        
        # % Eficiência Elevador (em decimal 0-1)
        eficiencia_elevador = calcular_porcentagem(horas_elevador, motor_ligado)
        
        # NOVO MÉTODO: Parado com Motor Ligado - usando o valor calculado pela função calcular_motor_ocioso_novo
        # A coluna 'Motor Ocioso' contém o tempo ocioso após aplicar a lógica de intervalos e tolerância
        parado_motor_ligado = dados_filtrados['Motor Ocioso'].sum()
        if dias_operador > 1:
            parado_motor_ligado = parado_motor_ligado / dias_operador
        
        # % Parado com motor ligado (em decimal 0-1)
        percent_parado_motor = calcular_porcentagem(parado_motor_ligado, motor_ligado)
        
        # Calculado com método avançado
        
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
    Calcula a disponibilidade mecânica e uso de GPS para cada equipamento.
    Calcula médias diárias considerando os dias efetivos de cada equipamento.
    
    Args:
        df (DataFrame): DataFrame processado
    
    Returns:
        DataFrame: Disponibilidade mecânica e GPS por equipamento
    """
    # Função auxiliar para extrair frente do Grupo Equipamento/Frente
    def extrair_frente(grupo):
        """Extrai a frente do campo 'Grupo Equipamento/Frente' usando regex"""
        if pd.isna(grupo):
            return ''
        grupo_str = str(grupo).lower()
        
        # MAPEAMENTO ESPECÍFICO PARA ZIRLENO - CORRETO
        if 'zirleno' in grupo_str:
            return 'zirleno'  # Retorna zirleno diretamente (não número)
        
        # Padrões para extrair a frente numerada
        padroes = [
            r'frente[\s]*([0-9]+)',
            r'fte[\s]*([0-9]+)', 
            r'([0-9]+)[\s]*frente',
            r'([0-9]+)[\s]*fte',
            r'f[\s]*([0-9]+)',
            r'([0-9]+)'
        ]
        
        for padrao in padroes:
            match = re.search(padrao, grupo_str, re.IGNORECASE)
            if match:
                numero = match.group(1)
                # MAPEAMENTO CORRETO baseado na operação real
                if numero in ['03', '3']:
                    return '3'    # frente3 (Alexandrita) ✅
                elif numero in ['08', '8']:  
                    return '8'    # frente8 (CMAA Canápolis) ✅
                elif numero in ['04', '4', '05', '5']:
                    return '5'    # frente5 (BP Ituiutaba) ✅
                else:
                    return numero
        
        return ''
    
    # Importar re se não estiver importado
    import re
    
    # DISPONIBILIDADE MECÂNICA: Considera TODOS os operadores, incluindo "SEM OPERADOR" e "TROCA DE TURNO"
    # A disponibilidade mecânica é um indicador técnico do equipamento, não do operador
    df_filtrado = df  # Usar todos os dados sem filtros de operador
    
    # Função para calcular valores com alta precisão e depois formatar
    def calcular_porcentagem(numerador, denominador, precisao=4):
        """Calcula porcentagem como decimal (0-1) evitando divisão por zero."""
        if denominador > 0:
            return round((numerador / denominador), precisao)
        return 0.0
    
    # Agrupar por Equipamento e Frente
    df_filtrado['Frente'] = df_filtrado['Grupo Equipamento/Frente'].apply(extrair_frente)
    
    resultados = []
    
    # Agrupar apenas por Equipamento, não por Frente para evitar duplicações
    for equipamento in df_filtrado['Equipamento'].unique():
        dados_equip = df_filtrado[df_filtrado['Equipamento'] == equipamento]
        
        # Determinar número de dias efetivos para este equipamento
        dias_equip = dados_equip['Data'].nunique() if 'Data' in dados_equip.columns else 1
        
        total_horas = round(dados_equip['Diferença_Hora'].sum(), 4)
        
        # Calcular horas de manutenção
        manutencao = round(dados_equip[dados_equip['Grupo Operacao'] == 'Manutenção']['Diferença_Hora'].sum(), 4)
        
        # Calcular GPS para operações produtivas (para colheita, usar RTK)
        dados_produtivos = dados_equip[dados_equip['Grupo Operacao'] == 'Produtiva']
        
        # Verificar se coluna RTK existe (para colheita)
        if 'RTK' in dados_produtivos.columns:
            gps_horas = dados_produtivos['RTK'].sum()
        else:
            gps_horas = 0
            print(f"Coluna RTK não encontrada para {equipamento}")
        
        # Se houver múltiplos dias, usar médias diárias
        if dias_equip > 1:
            total_horas = round(total_horas / dias_equip, 4)
            manutencao = round(manutencao / dias_equip, 4)
            gps_horas = gps_horas / dias_equip
            print(f"Equipamento: {equipamento}, Dias efetivos: {dias_equip}")
        
        # A disponibilidade mecânica é o percentual de tempo fora de manutenção
        disp_mecanica = calcular_porcentagem(total_horas - manutencao, total_horas)
        
        # Calcular GPS como porcentagem das horas produtivas
        horas_produtivas = dados_produtivos['Diferença_Hora'].sum()
        if dias_equip > 1:
            horas_produtivas = horas_produtivas / dias_equip
        
        gps_porcentagem = calcular_porcentagem(gps_horas, horas_produtivas)
        
        # Coletar todas as frentes para este equipamento (para informação)
        frentes = sorted(dados_equip['Frente'].unique())
        frente_principal = frentes[0] if frentes else ''
        
        # Processado com sucesso
        
        resultados.append({
            'Frota': equipamento,
            'Frente': frente_principal,  # Manter compatibilidade com estrutura existente
            'Disponibilidade': disp_mecanica,
            'GPS': gps_porcentagem
        })
    
    # Criar DataFrame e ordenar por frente e disponibilidade
    df_resultado = pd.DataFrame(resultados)
    
    # Salvar para debug
    try:
        import os
        from datetime import datetime
        
        # Criar pasta de debug se não existir
        pasta_debug = 'temp_excel_debug'
        if not os.path.exists(pasta_debug):
            os.makedirs(pasta_debug)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"{timestamp}_disponibilidade_mecanica_colheita.xlsx"
        caminho_debug = os.path.join(pasta_debug, nome_arquivo)
        
        # Salvar Excel
        with pd.ExcelWriter(caminho_debug, engine='openpyxl') as writer:
            df_resultado.to_excel(writer, sheet_name='1_Disponibilidade Mecânica', index=False)
        
        print(f"Debug: Arquivo salvo em {caminho_debug}")
        
        # Limpeza automática de arquivos antigos (mais de 1 dia)
        import glob
        import time
        arquivos_debug = glob.glob(os.path.join(pasta_debug, "*_disponibilidade_mecanica_colheita.xlsx"))
        tempo_atual = time.time()
        for arquivo in arquivos_debug:
            if tempo_atual - os.path.getmtime(arquivo) > 86400:  # 1 dia em segundos
                os.remove(arquivo)
                print(f"Debug: Arquivo antigo removido: {arquivo}")
                
    except Exception as e:
        print(f"Erro ao salvar debug: {e}")
    
    return df_resultado.sort_values(['Frente', 'Disponibilidade'], ascending=[True, False])

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

def calcular_motor_ocioso(base_calculo, df_base):
    """
    Calcula o percentual de motor ocioso por operador usando os dados da Base Calculo.
    Agrega os dados por operador, calculando a média quando um operador aparece em múltiplas frotas.
    Inclui as frotas utilizadas no nome do operador no formato: ID - NOME (frota1, frota2)
    
    Regras de cálculo (Método Avançado):
    1. Existe uma tolerância de 1 minuto para operações de "Parada com motor ligado" (valor 1)
    2. Se uma operação tem "Parada com motor ligado = 1" e dura menos de 1 minuto, ela é desconsiderada se:
       - A próxima operação tem "Parada com motor ligado = 0" e dura mais de 1 minuto
    3. Se existem duas ou mais operações com "Parada com motor ligado = 1" em sequência (ou com outras operações entre elas que duram menos de 1 minuto):
       - Somamos o tempo total dessas operações
       - Subtraímos 1 minuto do total
    
    Args:
        base_calculo (DataFrame): Tabela Base Calculo
        df_base (DataFrame): DataFrame base para aplicar filtros de operações
    
    Returns:
        DataFrame: Percentual de motor ocioso por operador (agregado)
    """
    # Caso o DataFrame bruto esteja disponível, utilizar para cálculo mais preciso
    if df_base is not None:
        resultados = []
        # Filtrar operadores inválidos
        df_filtrado = df_base[~df_base['Operador'].isin(OPERADORES_EXCLUIR)]

        for operador in df_filtrado['Operador'].unique():
            # Dados completos do operador (todas as frotas)
            dados_op = df_filtrado[df_filtrado['Operador'] == operador]

            # Frotas usadas
            frotas = sorted([str(eq) for eq in dados_op['Equipamento'].unique()])

            # Total de horas com motor ligado
            motor_ligado_total = dados_op[dados_op['Motor Ligado'] == 1]['Diferença_Hora'].sum()

            # Total de horas ociosas já calculadas pela coluna Motor Ocioso
            tempo_ocioso_total = dados_op['Motor Ocioso'].sum()

            # Dias efetivamente trabalhados
            dias_efetivos = max(1, dados_op['Data'].nunique()) if 'Data' in dados_op.columns else 1

            # Médias diárias corretas
            tempo_ligado_media = round(motor_ligado_total / dias_efetivos, 2)
            tempo_ocioso_media = round(tempo_ocioso_total / dias_efetivos, 2)

            porcentagem = tempo_ocioso_media / tempo_ligado_media if tempo_ligado_media > 0 else 0

            operador_com_frotas = f"{operador} ({', '.join(frotas)})" if frotas else operador

            resultados.append({
                'Operador': operador_com_frotas,
                'Porcentagem': porcentagem,
                'Tempo Ligado': tempo_ligado_media,
                'Tempo Ocioso': tempo_ocioso_media
            })

        return pd.DataFrame(resultados)

    # Fallback quando df_base não é fornecido – agrega usando médias em vez de soma para evitar duplicação
    resultados = []
    for operador in base_calculo['Operador'].unique():
        dados_operador = base_calculo[base_calculo['Operador'] == operador]

        frotas = sorted([str(eq) for eq in dados_operador['Equipamento'].unique()])

        tempo_ligado_media = dados_operador['Motor Ligado'].mean()
        tempo_ocioso_media = dados_operador['Parado Com Motor Ligado'].mean()

        porcentagem = tempo_ocioso_media / tempo_ligado_media if tempo_ligado_media > 0 else 0

        operador_com_frotas = f"{operador} ({', '.join(frotas)})" if frotas else operador

        resultados.append({
            'Operador': operador_com_frotas,
            'Porcentagem': porcentagem,
            'Tempo Ligado': tempo_ligado_media,
            'Tempo Ocioso': tempo_ocioso_media
        })

    return pd.DataFrame(resultados)

def calcular_eficiencia_energetica(base_calculo, df_base=None):
    """
    Calcula a eficiência energética por operador para colhedoras.
    CORREÇÃO CRÍTICA: Calcula médias corretas quando operador trabalha em múltiplas frotas.
    Inclui as frotas utilizadas no nome do operador no formato: ID - NOME (frota1, frota2)
    
    Args:
        base_calculo (DataFrame): Tabela Base Calculo (fallback)
        df_base (DataFrame): DataFrame base para cálculos corretos por operador
    
    Returns:
        DataFrame: Eficiência energética por operador (agregado)
    """
    # CORREÇÃO CRÍTICA: Usar df_base para cálculo correto quando disponível
    if df_base is not None:
        # Filtrar operadores excluídos
        df_filtrado = df_base[~df_base['Operador'].isin(OPERADORES_EXCLUIR)]
        
        resultados = []
        
        for operador in df_filtrado['Operador'].unique():
            # Filtrar dados do operador atual
            dados_operador = df_filtrado[df_filtrado['Operador'] == operador]
            
            # Coletar todas as frotas que este operador utilizou
            frotas = sorted([str(eq) for eq in dados_operador['Equipamento'].unique()])
            
            # CÁLCULO CORRETO: Total absoluto dividido por dias únicos
            if len(dados_operador) > 0:
                # Total de horas elevador e motor ligado (todas as frotas)
                horas_elevador_total = dados_operador[
                    (dados_operador['Esteira Ligada'] == 1) & 
                    (dados_operador['Pressao de Corte'] > 400)
                ]['Diferença_Hora'].sum()
                
                motor_ligado_total = dados_operador[
                    dados_operador['Motor Ligado'] == 1
                ]['Diferença_Hora'].sum()
                
                # Dias únicos trabalhados pelo operador (em todas as frotas)
                dias_unicos = dados_operador['Data'].nunique() if 'Data' in dados_operador.columns else 1
                
                # Médias diárias corretas
                horas_elevador_media = horas_elevador_total / dias_unicos
                motor_ligado_media = motor_ligado_total / dias_unicos
                
                # Calcular eficiência usando médias corretas
                eficiencia = horas_elevador_media / motor_ligado_media if motor_ligado_media > 0 else 0
                
                # Garantir que não ultrapasse 100%
                eficiencia = min(eficiencia, 1.0)
                
                # Montar o nome do operador com as frotas
                if len(frotas) > 0:
                    frotas_str = ', '.join(map(str, frotas))
                    operador_com_frotas = f"{operador} ({frotas_str})"
                else:
                    operador_com_frotas = operador
                
                resultados.append({
                    'Operador': operador_com_frotas,
                    'Eficiência': eficiencia
                })
        
        return pd.DataFrame(resultados)
    
    # FALLBACK: Usar base_calculo quando df_base não disponível (MÉTODO ANTIGO)
    else:
        # Agrupar por operador e coletar equipamentos
        resultados = []
        
        for operador in base_calculo['Operador'].unique():
            # Filtrar dados do operador atual
            dados_operador = base_calculo[base_calculo['Operador'] == operador]
            
            # Coletar todas as frotas (equipamentos) que este operador utilizou e converter para string
            frotas = sorted([str(eq) for eq in dados_operador['Equipamento'].unique()])
            
            # Calcular totais para o operador
            horas_elevador_total = dados_operador['Horas elevador'].sum()
            motor_ligado_total = dados_operador['Motor Ligado'].sum()
            
            # Calcular eficiência
            eficiencia = horas_elevador_total / motor_ligado_total if motor_ligado_total > 0 else 0
            
            # Garantir que não ultrapasse 100%
            eficiencia = min(eficiencia, 1.0)
            
            # Montar o nome do operador com as frotas
            if len(frotas) > 0:
                frotas_str = ', '.join(map(str, frotas))
                operador_com_frotas = f"{operador} ({frotas_str})"
            else:
                operador_com_frotas = operador
            
            resultados.append({
                'Operador': operador_com_frotas,
                'Eficiência': eficiencia
            })
        
        return pd.DataFrame(resultados)

def calcular_hora_elevador(df_base, base_calculo):
    """
    Calcula as horas de elevador por operador.
    CORREÇÃO CRÍTICA: Calcula médias corretas quando operador trabalha em múltiplas frotas.
    Inclui as frotas utilizadas no nome do operador no formato: ID - NOME (frota1, frota2)
    
    Args:
        df_base: DataFrame base para cálculos corretos por operador
        base_calculo (DataFrame): Tabela Base Calculo (fallback)
    
    Returns:
        DataFrame: Horas de elevador por operador (agregado)
    """
    # CORREÇÃO CRÍTICA: Usar df_base para cálculo correto quando disponível
    if df_base is not None:
        # Filtrar operadores excluídos
        df_filtrado = df_base[~df_base['Operador'].isin(OPERADORES_EXCLUIR)]
        
        resultados = []
        
        for operador in df_filtrado['Operador'].unique():
            # Filtrar dados do operador atual
            dados_operador = df_filtrado[df_filtrado['Operador'] == operador]
            
            # Coletar todas as frotas que este operador utilizou
            frotas = sorted([str(eq) for eq in dados_operador['Equipamento'].unique()])
            
            # CÁLCULO CORRETO: Total absoluto dividido por dias únicos
            if len(dados_operador) > 0:
                # Total de horas de elevador (todas as frotas)
                horas_elevador_total = dados_operador[
                    (dados_operador['Esteira Ligada'] == 1) & 
                    (dados_operador['Pressao de Corte'] > 400)
                ]['Diferença_Hora'].sum()
                
                # Dias únicos trabalhados pelo operador (em todas as frotas)
                dias_unicos = dados_operador['Data'].nunique() if 'Data' in dados_operador.columns else 1
                
                # Média diária correta
                horas_elevador_media = round(horas_elevador_total / dias_unicos, 2)
                
                # Montar o nome do operador com as frotas
                if len(frotas) > 0:
                    frotas_str = ', '.join(map(str, frotas))
                    operador_com_frotas = f"{operador} ({frotas_str})"
                else:
                    operador_com_frotas = operador
                
                resultados.append({
                    'Operador': operador_com_frotas,
                    'Horas': horas_elevador_media
                })
        
        return pd.DataFrame(resultados)
    
    # FALLBACK: Usar base_calculo quando df_base não disponível (MÉTODO ANTIGO)
    else:
        # Agrupar por operador e coletar equipamentos
        resultados = []
        
        for operador in base_calculo['Operador'].unique():
            # Filtrar dados do operador atual
            dados_operador = base_calculo[base_calculo['Operador'] == operador]
            
            # Coletar todas as frotas (equipamentos) que este operador utilizou e converter para string
            frotas = sorted([str(eq) for eq in dados_operador['Equipamento'].unique()])
            
            # Calcular total de horas de elevador
            horas_elevador_total = round(dados_operador['Horas elevador'].sum(), 2)
            
            # Montar o nome do operador com as frotas
            if len(frotas) > 0:
                frotas_str = ', '.join(map(str, frotas))
                operador_com_frotas = f"{operador} ({frotas_str})"
            else:
                operador_com_frotas = operador
            
            resultados.append({
                'Operador': operador_com_frotas,
                'Horas': horas_elevador_total
            })
        
        return pd.DataFrame(resultados)

def calcular_uso_gps(df_base, base_calculo):
    """
    Calcula o uso de GPS por operador.
    CORREÇÃO CRÍTICA: Calcula médias corretas quando operador trabalha em múltiplas frotas.
    Inclui as frotas utilizadas no nome do operador no formato: ID - NOME (frota1, frota2)
    
    Args:
        df_base: DataFrame base para cálculos corretos por operador
        base_calculo (DataFrame): Tabela Base Calculo (fallback)
    
    Returns:
        DataFrame: Percentual de uso de GPS por operador (agregado)
    """
    # CORREÇÃO CRÍTICA: Usar df_base para cálculo correto quando disponível
    if df_base is not None:
        # Filtrar operadores excluídos
        df_filtrado = df_base[~df_base['Operador'].isin(OPERADORES_EXCLUIR)]
        
        resultados = []
        
        for operador in df_filtrado['Operador'].unique():
            # Filtrar dados do operador atual
            dados_operador = df_filtrado[df_filtrado['Operador'] == operador]
            
            # Coletar todas as frotas que este operador utilizou
            frotas = sorted([str(eq) for eq in dados_operador['Equipamento'].unique()])
            
            # CÁLCULO CORRETO: Total absoluto dividido por dias únicos
            if len(dados_operador) > 0:
                # Total RTK e horas produtivas (todas as frotas)
                rtk_total = dados_operador[
                    (dados_operador['Grupo Operacao'] == 'Produtiva') &
                    (dados_operador['Pressao de Corte'] >= 400) &
                    (dados_operador['RTK (Piloto Automatico)'] == 1) &
                    (dados_operador['Esteira Ligada'] == 1)
                ]['Diferença_Hora'].sum()
                
                horas_produtivas_total = dados_operador[
                    dados_operador['Grupo Operacao'] == 'Produtiva'
                ]['Diferença_Hora'].sum()
                
                # Dias únicos trabalhados pelo operador (em todas as frotas)
                dias_unicos = dados_operador['Data'].nunique() if 'Data' in dados_operador.columns else 1
                
                # Médias diárias corretas
                rtk_media = rtk_total / dias_unicos
                horas_produtivas_media = horas_produtivas_total / dias_unicos
                
                # Calcular porcentagem usando médias corretas
                porcentagem = rtk_media / horas_produtivas_media if horas_produtivas_media > 0 else 0
                
                # Montar o nome do operador com as frotas
                if len(frotas) > 0:
                    frotas_str = ', '.join(map(str, frotas))
                    operador_com_frotas = f"{operador} ({frotas_str})"
                else:
                    operador_com_frotas = operador
                
                resultados.append({
                    'Operador': operador_com_frotas,
                    'Porcentagem': porcentagem
                })
        
        return pd.DataFrame(resultados)
    
    # FALLBACK: Usar base_calculo quando df_base não disponível (MÉTODO ANTIGO)  
    else:
        # Agrupar por operador e coletar equipamentos
        resultados = []
        
        for operador in base_calculo['Operador'].unique():
            # Filtrar dados do operador atual
            dados_operador = base_calculo[base_calculo['Operador'] == operador]
            
            # Coletar todas as frotas (equipamentos) que este operador utilizou e converter para string
            frotas = sorted([str(eq) for eq in dados_operador['Equipamento'].unique()])
            
            # Calcular a média ponderada
            rtk_total = dados_operador['RTK'].sum()
            horas_produtivas_total = dados_operador['Horas Produtivas'].sum()
            
            porcentagem = rtk_total / horas_produtivas_total if horas_produtivas_total > 0 else 0
            
            # Montar o nome do operador com as frotas
            if len(frotas) > 0:
                frotas_str = ', '.join(map(str, frotas))
                operador_com_frotas = f"{operador} ({frotas_str})"
            else:
                operador_com_frotas = operador
            
            resultados.append({
                'Operador': operador_com_frotas,
                'Porcentagem': porcentagem
            })

def calcular_media_velocidade(df):
    """
    Calcula a média de velocidade para cada operador considerando apenas registros produtivos e deslocamentos.
    Inclui as frotas utilizadas no nome do operador no formato: ID - NOME (frota1, frota2)
    
    Args:
        df (DataFrame): DataFrame processado
    
    Returns:
        DataFrame: DataFrame com a média de velocidade por operador
    """
    # Filtramos os dados excluindo os operadores da lista de exclusão
    df_filtrado = df[~df['Operador'].isin(OPERADORES_EXCLUIR)]
    
    # Identificar apenas registros produtivos ─ conforme requisito, utilizar
    # exclusivamente a velocidade de linhas cujo Grupo Operacao seja 'Produtiva'.
    # Para evitar divisão por zero e ruído de registros parados, mantemos apenas
    # velocidades estritamente positivas.
    registros_produtivos = (
        (df_filtrado['Grupo Operacao'] == 'Produtiva') &
        (df_filtrado['Velocidade'] > 0)
    )

    df_velocidade = df_filtrado[registros_produtivos]
    
    # Agrupar por operador e coletar equipamentos
    resultados = []
    
    for operador in df_filtrado['Operador'].unique():
        # Filtrar dados para este operador
        dados_op = df_velocidade[df_velocidade['Operador'] == operador]
        
        # Coletar todas as frotas (equipamentos) que este operador utilizou
        frotas = sorted(df_filtrado[df_filtrado['Operador'] == operador]['Equipamento'].unique())
        
        # Se não houver dados válidos para este operador, adicionar com velocidade zero
        if len(dados_op) == 0:
            velocidade_media = 0
        else:
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
        
        # Montar o nome do operador com as frotas
        if len(frotas) > 0:
            frotas_str = ', '.join(map(str, frotas))
            operador_com_frotas = f"{operador} ({frotas_str})"
        else:
            operador_com_frotas = operador
        
        resultados.append({
            'Operador': operador_com_frotas,
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
                # Normalizar nome para comparação (maiúsculo e sem espaços extras)
                nome_normalizado = nome_parte.upper().strip()
                if nome_normalizado not in nomes_para_ids:
                    nomes_para_ids[nome_normalizado] = []
                nomes_para_ids[nome_normalizado].append(op)
            except:
                continue
    
    # Encontrar nomes com múltiplas IDs
    duplicidades = []
    mapeamento = {}
    
    for nome, ids in nomes_para_ids.items():
        if len(ids) > 1:
            print(f"Encontrado operador duplicado: {nome} com {len(ids)} IDs diferentes")
            
            # Separar IDs que começam com '133' e têm 7 dígitos
            ids_suspeitas = [id_op for id_op in ids if ' - ' in id_op and id_op.split(' - ')[0].startswith('133') and len(id_op.split(' - ')[0]) == 7]
            ids_normais = [id_op for id_op in ids if id_op not in ids_suspeitas]
            
            # Se temos IDs suspeitas e normais, considerar a suspeita como incorreta
            if ids_suspeitas and ids_normais:
                for id_suspeita in ids_suspeitas:
                    # Usar a ID normal mais curta como destino (geralmente a correta)
                    id_correta = min(ids_normais, key=lambda x: len(x.split(' - ')[0]) if ' - ' in x else float('inf'))
                    
                    # Adicionar ao mapeamento
                    mapeamento[id_suspeita] = id_correta
                    
                    # Extrair as partes para o relatório
                    id_incorreta_parte = id_suspeita.split(' - ')[0]
                    id_correta_parte = id_correta.split(' - ')[0]
                    
                    print(f"  - Mapeando: {id_suspeita} -> {id_correta}")
                    
                    # Adicionar à lista de duplicidades para o relatório
                    duplicidades.append({
                        'ID Incorreta': id_suspeita,
                        'ID Correta': id_correta,
                        'Nome': nome
                    })
            
            # Caso especial: todas as IDs são suspeitas ou todas são normais
            # Neste caso, apresentamos no relatório mas não fazemos substituição automática
            else:
                print(f"  - Múltiplas IDs do mesmo tipo encontradas para {nome}, sem ação automática")
                # Ainda assim, adicionar ao relatório para conhecimento
                for i, id1 in enumerate(ids):
                    for id2 in ids[i+1:]:
                        duplicidades.append({
                            'ID Incorreta': id1, 
                            'ID Correta': id2,
                            'Nome': nome,
                            'Observação': "Duplicidade detectada, verificar manualmente"
                        })
    
    print(f"Encontrados {len(duplicidades)} operadores com IDs duplicadas.")
    return mapeamento, pd.DataFrame(duplicidades)

def calcular_horas_motor_ligado_total(df):
    """
    Calcula o total de horas com motor ligado por frota durante todo o período,
    e também a média diária.
    Usa a coluna 'Diferença_Hora' para calcular o tempo real com motor ligado.
    
    Args:
        df (DataFrame): DataFrame com os dados de operação
        
    Returns:
        DataFrame: DataFrame com o total de horas com motor ligado por frota e a média diária
    """
    try:
        # Verificar se as colunas necessárias existem
        if 'Data' not in df.columns:
            print("Aviso: Coluna 'Data' não encontrada. Usando o número total de registros como divisor.")
            # Criar uma coluna temporária para calcular as horas com motor ligado
            df_temp = df.copy()
            df_temp['Horas_Motor_Ligado'] = df_temp.apply(
                lambda row: row['Diferença_Hora'] if row['Motor Ligado'] == 1 else 0, 
                axis=1
            )
            
            # Agrupa por frota e soma as horas com motor ligado
            df_horas_motor = df_temp.groupby('Equipamento').agg({
                'Horas_Motor_Ligado': 'sum'
            }).reset_index()
            
            # Renomeia a coluna para maior clareza
            df_horas_motor.columns = ['Frota', 'Total Horas Motor Ligado']
            
            # Ordena pelo total de horas (decrescente)
            df_horas_motor = df_horas_motor.sort_values('Total Horas Motor Ligado', ascending=False)
            
            return df_horas_motor
        
        # Criar uma coluna temporária para calcular as horas com motor ligado
        df_temp = df.copy()
        df_temp['Horas_Motor_Ligado'] = df_temp.apply(
            lambda row: row['Diferença_Hora'] if row['Motor Ligado'] == 1 else 0, 
            axis=1
        )
        
        # Agrupa por frota e calcula o total de horas com motor ligado e o número de dias
        df_horas_motor = df_temp.groupby('Equipamento').agg({
            'Horas_Motor_Ligado': 'sum',
            'Data': 'nunique'  # Conta o número de dias únicos para cada frota
        }).reset_index()
        
        # Renomeia as colunas para maior clareza
        df_horas_motor.columns = ['Frota', 'Total Horas Motor Ligado', 'Dias Registrados']
        
        # Calcula a média diária de horas com motor ligado
        df_horas_motor['Horas Motor Ligado por Dia'] = df_horas_motor['Total Horas Motor Ligado'] / df_horas_motor['Dias Registrados']
        
        # Ordena pelo total de horas (decrescente)
        df_horas_motor = df_horas_motor.sort_values('Total Horas Motor Ligado', ascending=False)
        
        # Mantém todas as colunas relevantes
        df_horas_motor = df_horas_motor[['Frota', 'Total Horas Motor Ligado', 'Horas Motor Ligado por Dia', 'Dias Registrados']]
        
        return df_horas_motor
        
    except Exception as e:
        print(f"Erro ao calcular horas totais de motor ligado: {str(e)}")
        return pd.DataFrame(columns=['Frota', 'Total Horas Motor Ligado', 'Horas Motor Ligado por Dia', 'Dias Registrados'])

def criar_planilha_tdh(df):
    """
    Cria uma planilha vazia para TDH, contendo apenas as frotas encontradas.
    
    Args:
        df (DataFrame): DataFrame com os dados
        
    Returns:
        DataFrame: DataFrame vazio com as colunas 'Frota' e 'TDH'
    """
    # Obter todas as frotas únicas
    frotas = df['Equipamento'].unique()
    
    # Criar DataFrame vazio com as frotas
    df_tdh = pd.DataFrame({'Frota': frotas, 'TDH': ''})
    
    return df_tdh

def criar_planilha_diesel(df):
    """
    Cria uma planilha vazia para Diesel, contendo apenas as frotas encontradas.
    
    Args:
        df (DataFrame): DataFrame com os dados
        
    Returns:
        DataFrame: DataFrame vazio com as colunas 'Frota' e 'Diesel'
    """
    # Obter todas as frotas únicas
    frotas = df['Equipamento'].unique()
    
    # Criar DataFrame vazio com as frotas
    df_diesel = pd.DataFrame({'Frota': frotas, 'Diesel': ''})
    
    return df_diesel

def criar_planilha_impureza(df):
    """
    Cria uma planilha vazia para Impureza Vegetal, contendo apenas as frotas encontradas.
    
    Args:
        df (DataFrame): DataFrame com os dados
        
    Returns:
        DataFrame: DataFrame vazio com as colunas 'Frota' e 'Impureza'
    """
    # Obter todas as frotas únicas
    frotas = df['Equipamento'].unique()
    
    # Criar DataFrame vazio com as frotas
    df_impureza = pd.DataFrame({'Frota': frotas, 'Impureza': ''})
    
    return df_impureza

def criar_planilha_coordenadas(df_base):
    """
    Cria e retorna DataFrame de coordenadas (Equipamento, Hora, Latitude, Longitude, RTK)
    já ordenado e pronto para ser escrito tanto no Excel quanto em CSV.
    """
    colunas_necessarias = ['Equipamento', 'Hora', 'Latitude', 'Longitude']
    colunas_rtk = ['Velocidade', 'Pressao de Corte', 'RTK (Piloto Automatico)']

    # Verificar se todas as colunas necessárias existem
    for coluna in colunas_necessarias:
        if coluna not in df_base.columns:
            print(f"⚠️ Coluna '{coluna}' não encontrada – planilha de coordenadas vazia.")
            return pd.DataFrame(columns=colunas_necessarias + ['RTK'])

    # Verificar se as colunas para RTK existem
    colunas_rtk_existentes = [col for col in colunas_rtk if col in df_base.columns]
    if len(colunas_rtk_existentes) < len(colunas_rtk):
        print(f"⚠️ Colunas RTK faltando: {set(colunas_rtk) - set(colunas_rtk_existentes)}")

    df_coordenadas = df_base[colunas_necessarias + colunas_rtk_existentes].copy()

    # Criar coluna RTK baseada nos critérios:
    # RTK = "Sim" quando: Velocidade > 0 E Pressao de Corte >= 400 E RTK (Piloto Automatico) = 1
    # Caso contrário: RTK = "Não"
    if all(col in df_coordenadas.columns for col in colunas_rtk):
        df_coordenadas['RTK'] = df_coordenadas.apply(
            lambda row: "Sim" if (
                pd.notna(row['Velocidade']) and float(row['Velocidade']) > 0 and
                pd.notna(row['Pressao de Corte']) and float(row['Pressao de Corte']) >= 400 and
                pd.notna(row['RTK (Piloto Automatico)']) and int(row['RTK (Piloto Automatico)']) == 1
            ) else "Não",
            axis=1
        )
        print(f"✅ Coluna RTK criada com critérios: Velocidade > 0, Pressão >= 400, Piloto Automático = 1")
    else:
        # Se não tiver todas as colunas necessárias, criar coluna RTK com "Não"
        df_coordenadas['RTK'] = "Não"
        print(f"⚠️ Coluna RTK criada com valor padrão 'Não' (colunas faltando)")

    # Remover colunas auxiliares de RTK do resultado final
    colunas_finais = ['Equipamento', 'Hora', 'Latitude', 'Longitude', 'RTK']
    df_coordenadas = df_coordenadas[colunas_finais].copy()

    # --- Sanitização de coordenadas --------------------------------------
    import re

    def _fix_coord(val: str):
        """Remove pontos extras, troca vírgula por ponto e garante formato numérico válido."""
        if pd.isna(val):
            return val
        s = str(val).strip()
        s = s.replace(',', '.')  # vírgulas → ponto decimal
        # remover qualquer caractere não numérico (exceto ponto e sinal)
        s = re.sub(r'[^0-9.\-]', '', s)
        # se houver mais de um ponto, manter somente o primeiro
        if s.count('.') > 1:
            partes = s.split('.')
            s = partes[0] + '.' + ''.join(partes[1:])
        return s

    for col in ['Latitude', 'Longitude']:
        df_coordenadas[col] = df_coordenadas[col].apply(_fix_coord)

    # Ordenação por Equipamento e Hora (se possível)
    try:
        df_coordenadas['Hora_temp'] = pd.to_datetime(df_coordenadas['Hora'], format='%H:%M:%S', errors='coerce')
        df_coordenadas = df_coordenadas.sort_values(['Equipamento', 'Hora_temp'])
        df_coordenadas.drop('Hora_temp', axis=1, inplace=True)
    except Exception:
        df_coordenadas = df_coordenadas.sort_values(['Equipamento', 'Hora'])

    # Garantir que Latitude/Longitude sejam numéricas e remover inválidos
    df_coordenadas['Latitude'] = pd.to_numeric(df_coordenadas['Latitude'], errors='coerce')
    df_coordenadas['Longitude'] = pd.to_numeric(df_coordenadas['Longitude'], errors='coerce')
    df_coordenadas = df_coordenadas.dropna(subset=['Latitude', 'Longitude'])

    return df_coordenadas

def calcular_ofensores(df):
    """
    Calcula os top 5 ofensores por frente.
    Agrupa por Frente e Operacao onde Estado Operacional é 'PARADA',
    soma a Diferença_Hora, classifica do maior para o menor.
    
    Args:
        df (DataFrame): DataFrame com os dados
        
    Returns:
        DataFrame: DataFrame com os ofensores por frente
    """
    # Função auxiliar para extrair a frente do grupo
    def extrair_frente(grupo):
        """Extrai a frente do campo 'Grupo Equipamento/Frente' - versão para ofensores"""
        if pd.isna(grupo):
            return ''
        grupo_str = str(grupo).lower()
        
        # MAPEAMENTO ESPECÍFICO PARA ZIRLENO - CORRETO
        if 'zirleno' in grupo_str:
            return 'zirleno'
        
        # Extrair a última palavra do grupo (comportamento original)
        ultima_palavra = grupo.split()[-1] if ' ' in grupo else grupo
        
        # Tentar extrair número da última palavra
        import re
        match = re.search(r'([0-9]+)', ultima_palavra)
        if match:
            numero = match.group(1)
            # MAPEAMENTO CORRETO baseado na operação real
            if numero in ['03', '3']:
                return '3'    # frente3 (Alexandrita) ✅
            elif numero in ['08', '8']:
                return '8'    # frente8 (CMAA Canápolis) ✅
            elif numero in ['04', '4', '05', '5']:
                return '5'    # frente5 (BP Ituiutaba) ✅
            else:
                return numero
        
        return ultima_palavra
    
    # Verificar se existe a coluna 'Frente'
    if 'Frente' not in df.columns:
        df['Frente'] = df['Grupo Equipamento/Frente'].apply(extrair_frente)
    
    # Filtrar apenas as operações em parada (Estado Operacional = 'PARADA')
    df_parada = df[df['Estado Operacional'] == 'PARADA'].copy()
    
    if df_parada.empty:
        return pd.DataFrame(columns=['Operacao', 'Tempo', 'Porcentagem'])
    
    # Calcular o tempo total de parada
    tempo_total_parada = df_parada['Diferença_Hora'].sum()
    
    # Agrupar por Operacao e somar as diferenças de hora
    ofensores = df_parada.groupby('Operacao')['Diferença_Hora'].sum().reset_index()
    
    # Calcular a porcentagem de cada operação em relação ao tempo total de parada
    ofensores['Porcentagem'] = (ofensores['Diferença_Hora'] / tempo_total_parada)
    
    # Renomear colunas para o formato esperado
    ofensores.columns = ['Operacao', 'Tempo', 'Porcentagem']
    
    # Ordenar por tempo em ordem decrescente e pegar apenas os top 5
    ofensores = ofensores.sort_values('Tempo', ascending=False).head(5)
    
    return ofensores

def processar_arquivo(caminho_arquivo, diretorio_saida):
    """
    Processa um único arquivo e gera o Excel de saída.
    
    Args:
        caminho_arquivo (str): Caminho do arquivo a ser processado
        diretorio_saida (str): Diretório onde o arquivo de saída será salvo
    """
    # Obter apenas o nome do arquivo (sem caminho e sem extensão)
    nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
    
    # Nome de saída igual ao original com extensão .xlsx
    arquivo_saida = os.path.join(diretorio_saida, f"{nome_base}.xlsx")
    
    print(f"\nProcessando arquivo: {os.path.basename(caminho_arquivo)}")
    print(f"Arquivo de saída: {os.path.basename(arquivo_saida)}")
    
    try:
        # Processar o arquivo base
        df_base = processar_arquivo_base(caminho_arquivo)
        if df_base is None:
            print(f"Erro ao processar {os.path.basename(caminho_arquivo)}.")
            return None
        
        # Identificar operadores duplicados antes de aplicar as substituições manuais
        mapeamento_duplicados, df_duplicados = identificar_operadores_duplicados(df_base)
        
        # Carregar e aplicar substituições de operadores (manuais + automáticas)
        substituicoes = carregar_substituicoes_operadores()
        substituicoes_horario = carregar_substituicoes_operadores_horario()
        
        # Combinar as substituições manuais com as automáticas (automáticas têm precedência)
        substituicoes_combinadas = {**substituicoes, **mapeamento_duplicados}
        
        print("\n=== APLICANDO SUBSTITUIÇÕES DE OPERADORES ===")
        if substituicoes_combinadas or substituicoes_horario:
            df_base, df_substituicoes = aplicar_substituicao_operadores(df_base, substituicoes_combinadas, substituicoes_horario)
        else:
            df_substituicoes = pd.DataFrame(columns=['ID Original', 'Nome Original', 'ID Nova', 'Nome Novo', 'Registros Afetados'])
        print("=== FIM DAS SUBSTITUIÇÕES ===\n")
        
        # Se o DataFrame estiver vazio, gerar apenas a planilha BASE
        if len(df_base) == 0:
            with pd.ExcelWriter(arquivo_saida, engine='openpyxl') as writer:
                df_base.to_excel(writer, sheet_name='BASE', index=False)
                if not df_duplicados.empty:
                    df_duplicados.to_excel(writer, sheet_name='IDs Duplicadas', index=False)
            print(f"Arquivo {arquivo_saida} gerado com apenas a planilha BASE (sem dados).")
            return arquivo_saida
        
        # ORDENAR o DataFrame base por Equipamento e depois por Hora
        if 'Data' in df_base.columns:
            df_base = df_base.sort_values(by=['Equipamento', 'Data', 'Hora'])
        else:
            df_base = df_base.sort_values(by=['Equipamento', 'Hora'])
        
        # Calcular a Base Calculo com os operadores já substituídos
        print("Calculando Base Calculo com operadores consolidados...")
        base_calculo = calcular_base_calculo(df_base)
        
        # Calcular as métricas auxiliares
        print("Calculando métricas auxiliares com operadores consolidados...")
        disp_mecanica = calcular_disponibilidade_mecanica(df_base)
        eficiencia_energetica = calcular_eficiencia_energetica(base_calculo, df_base)
        hora_elevador = calcular_hora_elevador(df_base, base_calculo)
        motor_ocioso = calcular_motor_ocioso(base_calculo, df_base)
        uso_gps = calcular_uso_gps(df_base, base_calculo)
        horas_por_frota = calcular_horas_por_frota(df_base)
        
        # Calcular média de velocidade por operador
        media_velocidade = calcular_media_velocidade(df_base)
        
        # Calcular médias de manobras (operador / frota)
        df_manobras_operador, df_manobras_frota = calcular_manobras(df_base)
        
        # Criar o arquivo Excel com todas as planilhas
        criar_excel_com_planilhas(
            df_base, base_calculo, disp_mecanica, eficiencia_energetica,
            hora_elevador, motor_ocioso, uso_gps, horas_por_frota, arquivo_saida,
            df_duplicados,  # Adicionar a tabela de IDs duplicadas
            media_velocidade,  # Adicionar a tabela de média de velocidade
            df_substituicoes,  # Adicionar a tabela de IDs substituídas
            df_manobras_operador,  # Nova planilha – manobras por operador
            df_manobras_frota  # Nova planilha – manobras por frota
        )
        
        # Criar planilha de coordenadas
        df_coordenadas = criar_planilha_coordenadas(df_base)

        # Salvar CSV de coordenadas para consumo do gerarMapas.py
        if not df_coordenadas.empty:
            try:
                output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output'))
                os.makedirs(output_dir, exist_ok=True)
                base_name = os.path.splitext(os.path.basename(arquivo_saida))[0]
                csv_nome = f"{base_name}.csv"
                caminho_csv = os.path.join(output_dir, csv_nome)
                # Garantir ponto decimal e 9 casas (evita perda de precisão)
                df_coordenadas.to_csv(
                    caminho_csv,
                    sep=';',
                    index=False,
                    float_format='%.9f',  # -19.679629644 → -19.679629644
                    encoding='utf-8'
                )
                print(f"💾 CSV coordenadas salvo: {csv_nome}")
                
            except Exception as e:
                print(f"⚠️ Não foi possível salvar CSV de coordenadas: {e}")
        
        print(f"Arquivo {arquivo_saida} gerado com sucesso!")
        return arquivo_saida
        
    except Exception as e:
        print(f"Erro ao processar arquivo {caminho_arquivo}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Limpar arquivo de entrada se necessário
        if LIMPAR_ARQUIVOS and os.path.exists(caminho_arquivo):
            try:
                os.remove(caminho_arquivo)
                print(f"Arquivo de entrada removido: {caminho_arquivo}")
            except Exception as e:
                print(f"Erro ao remover arquivo de entrada {caminho_arquivo}: {str(e)}")

def processar_arquivo_zip(caminho_zip, diretorio_saida):
    """
    Processa um arquivo ZIP contendo dados de colhedoras.
    
    Args:
        caminho_zip (str): Caminho do arquivo ZIP
        diretorio_saida (str): Diretório onde salvar o arquivo Excel resultante
        
    Returns:
        str: Caminho do arquivo Excel gerado ou None em caso de erro
    """
    print(f"\nProcessando arquivo ZIP: {os.path.basename(caminho_zip)}")
    
    try:
        # Extrair arquivo ZIP para pasta temporária
        arquivos_extraidos, pasta_temp = extrair_arquivo_zip(caminho_zip)
        
        if not arquivos_extraidos:
            print(f"Nenhum arquivo TXT ou CSV encontrado no ZIP {os.path.basename(caminho_zip)}")
            return None
        
        # Processar o primeiro arquivo extraído (assumindo que só há um)
        arquivo_processado = arquivos_extraidos[0]
        resultado = processar_arquivo(arquivo_processado, diretorio_saida)
        
        return resultado
        
    except Exception as e:
        print(f"Erro ao processar arquivo ZIP {caminho_zip}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Limpar arquivos temporários e ZIP original se necessário
        if pasta_temp:
            try:
                shutil.rmtree(pasta_temp)
                print(f"Pasta temporária removida: {pasta_temp}")
            except Exception as e:
                print(f"Erro ao remover pasta temporária {pasta_temp}: {str(e)}")
        
        if LIMPAR_ARQUIVOS and os.path.exists(caminho_zip):
            try:
                os.remove(caminho_zip)
                print(f"Arquivo ZIP removido: {caminho_zip}")
            except Exception as e:
                print(f"Erro ao remover arquivo ZIP {caminho_zip}: {str(e)}")

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
                print(f"Removendo pasta temporária: {pasta_temp}")
                shutil.rmtree(pasta_temp)
                print(f"Pasta temporária removida com sucesso")
            except Exception as e:
                print(f"Erro ao remover pasta temporária {pasta_temp}: {str(e)}")
        return [], None

def processar_todos_arquivos():
    """
    Processa todos os arquivos TXT, CSV ou ZIP de colhedoras na pasta dados.
    Ignora arquivos que contenham "transbordo" no nome.
    """
    print("\nIniciando processamento de arquivos...")
    
    # Obter o diretório onde está o script
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    print(f"Diretório do script: {diretorio_script}")
    
    # Diretório raiz do projeto (4 níveis acima: novo-fluxo -> processors -> app -> backend -> raiz)
    diretorio_raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(diretorio_script))))
    print(f"Diretório raiz: {diretorio_raiz}")
    
    # Diretórios para dados de entrada e saída
    diretorio_dados = os.path.join(diretorio_raiz, "dados")
    diretorio_saida = os.path.join(diretorio_raiz, "output")
    print(f"Diretório de dados: {diretorio_dados}")
    print(f"Diretório de saída: {diretorio_saida}")
    
    # Verificar se os diretórios existem, caso contrário criar
    if not os.path.exists(diretorio_dados):
        print(f"Criando diretório de dados: {diretorio_dados}")
        os.makedirs(diretorio_dados)
    if not os.path.exists(diretorio_saida):
        print(f"Criando diretório de saída: {diretorio_saida}")
        os.makedirs(diretorio_saida)
    
    # Encontrar todos os arquivos TXT/CSV/ZIP de colhedoras
    arquivos = []
    arquivos_zip = []
    
    # Adicionar arquivos TXT sempre
    arquivos += glob.glob(os.path.join(diretorio_dados, "RV Colhedora*.txt"))
    arquivos += glob.glob(os.path.join(diretorio_dados, "*colhedora*.txt"))
    arquivos += glob.glob(os.path.join(diretorio_dados, "colhedora*.txt"))
    
    # Adicionar arquivos CSV apenas se processCsv for True
    if processCsv:
        arquivos += glob.glob(os.path.join(diretorio_dados, "RV Colhedora*.csv"))
        arquivos += glob.glob(os.path.join(diretorio_dados, "*colhedora*.csv"))
        arquivos += glob.glob(os.path.join(diretorio_dados, "colhedora*.csv"))
    
    # Adicionar arquivos ZIP
    arquivos_zip += glob.glob(os.path.join(diretorio_dados, "RV Colhedora*.zip"))
    arquivos_zip += glob.glob(os.path.join(diretorio_dados, "*colhedora*.zip"))
    arquivos_zip += glob.glob(os.path.join(diretorio_dados, "colhedora*.zip"))
    
    print("\nArquivos encontrados antes da filtragem:")
    print(f"TXT/CSV: {[os.path.basename(a) for a in arquivos]}")
    print(f"ZIP: {[os.path.basename(a) for a in arquivos_zip]}")
    
    # Filtrar arquivos que contenham "transbordo" no nome (case insensitive)
    arquivos = [arquivo for arquivo in arquivos if "transbordo" not in os.path.basename(arquivo).lower()]
    arquivos_zip = [arquivo for arquivo in arquivos_zip if "transbordo" not in os.path.basename(arquivo).lower()]
    
    # Remover possíveis duplicatas
    arquivos = list(set(arquivos))
    arquivos_zip = list(set(arquivos_zip))
    
    print("\nArquivos encontrados após a filtragem:")
    print(f"TXT/CSV: {[os.path.basename(a) for a in arquivos]}")
    print(f"ZIP: {[os.path.basename(a) for a in arquivos_zip]}")
    
    if not arquivos and not arquivos_zip:
        print("Nenhum arquivo de colhedoras encontrado na pasta dados!")
        return
    
    print(f"\nEncontrados {len(arquivos)} arquivos de colhedoras (TXT/CSV) para processar.")
    print(f"Encontrados {len(arquivos_zip)} arquivos ZIP de colhedoras para processar.")
    
    # Processar cada arquivo TXT/CSV
    for arquivo in arquivos:
        print(f"\nProcessando arquivo TXT/CSV: {os.path.basename(arquivo)}")
        processar_arquivo(arquivo, diretorio_saida)
    
    # Processar cada arquivo ZIP
    for arquivo_zip in arquivos_zip:
        print(f"\nProcessando arquivo ZIP: {os.path.basename(arquivo_zip)}")
        
        # Extrair arquivo ZIP para pasta temporária
        print(f"Extraindo arquivo ZIP: {arquivo_zip}")
        arquivos_extraidos, pasta_temp = extrair_arquivo_zip(arquivo_zip)
        
        if not arquivos_extraidos:
            print(f"Nenhum arquivo TXT ou CSV encontrado no ZIP {os.path.basename(arquivo_zip)}")
            continue
        
        print(f"Extraídos {len(arquivos_extraidos)} arquivos do ZIP:")
        for arquivo in arquivos_extraidos:
            print(f"  - {os.path.basename(arquivo)}")
        
        # Processar cada arquivo extraído
        for arquivo_extraido in arquivos_extraidos:
            # Filtrar arquivos que contenham "transbordo" no nome
            if "transbordo" not in os.path.basename(arquivo_extraido).lower():
                print(f"\nProcessando arquivo extraído: {os.path.basename(arquivo_extraido)}")
                processar_arquivo(arquivo_extraido, diretorio_saida)
        
        # Limpar pasta temporária se foi criada
        if pasta_temp:
            try:
                print(f"Removendo pasta temporária: {pasta_temp}")
                shutil.rmtree(pasta_temp)
                print(f"Pasta temporária removida com sucesso")
            except Exception as e:
                print(f"Erro ao remover pasta temporária {pasta_temp}: {str(e)}")
    
    print("\nProcessamento de todos os arquivos concluído!")

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
    
    # Diretório raiz do projeto (4 níveis acima)
    diretorio_raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(diretorio_script))))
    
    # Caminho para o arquivo de substituição
    arquivo_substituicao = os.path.join(diretorio_raiz, "config", "substituiroperadores.json")
    
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

def carregar_substituicoes_operadores_horario():
    """
    Carrega o arquivo substituiroperadores_horario.json que contém os mapeamentos 
    de substituição de operadores com intervalos de horário.
    
    Returns:
        list: Lista de dicionários com mapeamentos 
              {operador_origem, operador_destino, hora_inicio, hora_fim, frota_origem}
        ou lista vazia se o arquivo não existir ou for inválido.
        O campo frota_origem é opcional:
        - Se presente e não vazio, a substituição é aplicada apenas a registros daquela frota específica
        - Se ausente ou vazio, a substituição é aplicada a todos os registros do operador
    """
    # Obter o diretório onde está o script
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    
    # Diretório raiz do projeto (4 níveis acima)
    diretorio_raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(diretorio_script))))
    
    # Caminho para o arquivo de substituição
    arquivo_substituicao = os.path.join(diretorio_raiz, "config", "substituiroperadores_horario.json")
    
    # Verificar se o arquivo existe
    if not os.path.exists(arquivo_substituicao):
        print(f"Arquivo de substituição de operadores com horário não encontrado: {arquivo_substituicao}")
        return []
    
    try:
        # Carregar o arquivo JSON
        with open(arquivo_substituicao, 'r', encoding='utf-8') as f:
            substituicoes = json.load(f)
        
        # Converter strings de hora para objetos datetime.time
        for item in substituicoes:
            if 'hora_inicio' in item and isinstance(item['hora_inicio'], str):
                hora_str = item['hora_inicio']
                # Adicionar segundos se não estiverem presentes
                if len(hora_str.split(':')) == 2:
                    hora_str += ':00'
                item['hora_inicio_obj'] = datetime.strptime(hora_str, '%H:%M:%S').time()
            
            if 'hora_fim' in item and isinstance(item['hora_fim'], str):
                hora_str = item['hora_fim']
                # Adicionar segundos se não estiverem presentes
                if len(hora_str.split(':')) == 2:
                    hora_str += ':00'
                item['hora_fim_obj'] = datetime.strptime(hora_str, '%H:%M:%S').time()
        
        print(f"Carregadas {len(substituicoes)} substituições de operadores com intervalos de horário.")
        return substituicoes
        
    except Exception as e:
        print(f"Erro ao carregar arquivo de substituição de operadores com horário: {str(e)}")
        return []

def aplicar_substituicao_operadores(df, mapeamento_substituicoes, mapeamento_horario=None):
    """
    Aplica as substituições de operadores no DataFrame.
    
    Args:
        df (DataFrame): DataFrame a ser processado
        mapeamento_substituicoes (dict): Dicionário com mapeamento {operador_origem: operador_destino}
        mapeamento_horario (list, optional): Lista de dicionários com mapeamentos
            {operador_origem, operador_destino, hora_inicio, hora_fim, frota_origem}.
            O campo frota_origem é opcional:
            - Se presente e não vazio, a substituição é aplicada apenas a registros daquela frota específica
            - Se ausente ou vazio, a substituição é aplicada a todos os registros do operador
    
    Returns:
        tuple: (DataFrame com substituições aplicadas, DataFrame com registro das substituições)
    """
    if (not mapeamento_substituicoes and not mapeamento_horario) or 'Operador' not in df.columns:
        return df, pd.DataFrame(columns=['ID Original', 'Nome Original', 'ID Nova', 'Nome Novo', 'Registros Afetados'])
    
    # Criar uma cópia para não alterar o DataFrame original
    df_modificado = df.copy()
    
    # Lista para armazenar as substituições realizadas
    substituicoes_realizadas = []
    total_registros_substituidos = 0
    
    # Verificar operadores antes da substituição para relatório
    operadores_antes = df_modificado['Operador'].unique()
    print(f"\nOperadores antes da substituição: {len(operadores_antes)}")
    
    # Aplicar as substituições por horário se disponíveis e se o DataFrame tiver coluna de data/hora
    if mapeamento_horario and 'Data' in df_modificado.columns and 'Hora' in df_modificado.columns:
        # Criar uma cópia backup dos operadores originais
        df_modificado['Operador_Original'] = df_modificado['Operador'].copy()
        
        # Para cada linha no DataFrame
        for idx, row in df_modificado.iterrows():
            # Tenta extrair a hora do registro
            try:
                if isinstance(row['Hora'], str):
                    hora_registro = datetime.strptime(row['Hora'], '%H:%M:%S').time()
                elif isinstance(row['Hora'], datetime.time):
                    hora_registro = row['Hora']
                else:
                    continue  # Pula se não conseguir converter
                
                operador = row['Operador']
                
                # Verificar todas as regras de substituição por horário
                for regra in mapeamento_horario:
                    # Verificar se a condição básica é atendida: operador de origem correto e horário dentro do intervalo
                    condicao_basica = (operador == regra['operador_origem'] and 
                                      regra['hora_inicio_obj'] <= hora_registro <= regra['hora_fim_obj'])
                    
                    # Verificar condição de frota se ela existir na regra
                    condicao_frota = True
                    if 'frota_origem' in regra and regra['frota_origem'] and 'Equipamento' in df_modificado.columns:
                        condicao_frota = (row['Equipamento'] == regra['frota_origem'])
                    # Caso contrário, aplica a todos os registros do operador
                    
                    # Aplicar substituição apenas se ambas condições forem atendidas
                    if condicao_basica and condicao_frota:
                        # Aplicar a substituição
                        df_modificado.at[idx, 'Operador'] = regra['operador_destino']
                        break
            except Exception as e:
                print(f"Erro ao processar substituição com horário para linha {idx}: {str(e)}")
        
        # Contar substituições realizadas por horário
        substituicoes_contagem = {}
        for idx, row in df_modificado[df_modificado['Operador'] != df_modificado['Operador_Original']].iterrows():
            origem = row['Operador_Original']
            destino = row['Operador']
            chave = (origem, destino)
            if chave in substituicoes_contagem:
                substituicoes_contagem[chave] += 1
            else:
                substituicoes_contagem[chave] = 1
        
        # Adicionar as substituições com horário à lista de substituições realizadas
        for (origem, destino), count in substituicoes_contagem.items():
            total_registros_substituidos += count
            id_original = origem.split(' - ')[0] if ' - ' in origem else origem
            nome_original = origem.split(' - ')[1] if ' - ' in origem else ''
            id_nova = destino.split(' - ')[0] if ' - ' in destino else destino
            nome_novo = destino.split(' - ')[1] if ' - ' in destino else ''
            
            substituicoes_realizadas.append({
                'ID Original': id_original,
                'Nome Original': nome_original,
                'ID Nova': id_nova,
                'Nome Novo': nome_novo,
                'Registros Afetados': count,
                'Por Horário': True
            })
            print(f"Operador '{origem}' substituído por '{destino}' em {count} registros (por horário)")
        
        # Remover a coluna temporária
        df_modificado.drop('Operador_Original', axis=1, inplace=True)
    
    # Contar operadores e registros antes da substituição padrão
    contagem_antes = df_modificado['Operador'].value_counts().to_dict()
    
    # Aplicar as substituições padrão (sem horário)
    for origem, destino in mapeamento_substituicoes.items():
        # Verificar se o operador de origem existe no DataFrame
        registros_afetados = df_modificado[df_modificado['Operador'] == origem].shape[0]
        
        if registros_afetados > 0:
            # Substituir o operador
            df_modificado.loc[df_modificado['Operador'] == origem, 'Operador'] = destino
            
            total_registros_substituidos += registros_afetados
            
            # Extrair IDs e nomes
            id_original = origem.split(' - ')[0] if ' - ' in origem else origem
            nome_original = origem.split(' - ')[1] if ' - ' in origem else ''
            id_nova = destino.split(' - ')[0] if ' - ' in destino else destino
            nome_novo = destino.split(' - ')[1] if ' - ' in destino else ''
            
            substituicoes_realizadas.append({
                'ID Original': id_original,
                'Nome Original': nome_original,
                'ID Nova': id_nova, 
                'Nome Novo': nome_novo,
                'Registros Afetados': registros_afetados,
                'Por Horário': False
            })
            print(f"Operador '{origem}' substituído por '{destino}' em {registros_afetados} registros")
    
    # Verificar operadores após substituição
    operadores_depois = df_modificado['Operador'].unique()
    print(f"Operadores após substituição: {len(operadores_depois)}")
    print(f"Total de registros substituídos: {total_registros_substituidos}")
    
    # Criar DataFrame com as substituições realizadas
    df_substituicoes = pd.DataFrame(substituicoes_realizadas)
    
    return df_modificado, df_substituicoes

def criar_excel_com_planilhas(df_base, base_calculo, disp_mecanica, eficiencia_energetica,
                            hora_elevador, motor_ocioso, uso_gps, horas_por_frota, caminho_saida,
                            df_duplicados=None, media_velocidade=None, df_substituicoes=None,
                            df_manobras_operador=None, df_manobras_frota=None):
    """
    Cria um arquivo Excel com todas as planilhas necessárias.
    """
    # Definir função de ajuste de largura de colunas
    def ajustar_largura_colunas(worksheet):
        """Ajusta a largura das colunas da planilha"""
        for col in worksheet.columns:
            max_length = 10
            column = col[0].column_letter
            header_text = str(col[0].value)
            if header_text:
                max_length = max(max_length, len(header_text) + 2)
            for cell in col[1:min(20, len(col))]:
                if cell.value:
                    cell_text = str(cell.value)
                    max_length = max(max_length, len(cell_text) + 2)
            max_length = min(max_length, 40)
            worksheet.column_dimensions[column].width = max_length
    
    # Calcular horas totais de motor ligado por frota
    df_horas_motor_total = calcular_horas_motor_ligado_total(df_base)
    
    # Criar planilhas adicionais
    df_tdh = criar_planilha_tdh(df_base)
    df_diesel = criar_planilha_diesel(df_base)
    df_impureza = criar_planilha_impureza(df_base)
    
    # Criar planilha de coordenadas
    df_coordenadas = criar_planilha_coordenadas(df_base)
    
    # Calcular os top 5 ofensores
    df_ofensores = calcular_ofensores(df_base)
    
    with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
        # Salvar cada DataFrame em uma planilha separada
        df_base.to_excel(writer, sheet_name='BASE', index=False)
        base_calculo.to_excel(writer, sheet_name='Base Calculo', index=False)
        disp_mecanica.to_excel(writer, sheet_name='1_Disponibilidade Mecânica', index=False)
        eficiencia_energetica.to_excel(writer, sheet_name='2_Eficiência Energética', index=False)
        hora_elevador.to_excel(writer, sheet_name='3_Hora Elevador', index=False)
        
        # Garantir que os valores numéricos do motor_ocioso sejam mantidos como números
        motor_ocioso['Tempo Ligado'] = pd.to_numeric(motor_ocioso['Tempo Ligado'], errors='coerce')
        motor_ocioso['Tempo Ocioso'] = pd.to_numeric(motor_ocioso['Tempo Ocioso'], errors='coerce')
        motor_ocioso['Porcentagem'] = pd.to_numeric(motor_ocioso['Porcentagem'], errors='coerce')
        motor_ocioso.to_excel(writer, sheet_name='4_Motor Ocioso', index=False)
        
        uso_gps.to_excel(writer, sheet_name='5_Uso GPS', index=False)
        horas_por_frota.to_excel(writer, sheet_name='Horas por Frota', index=False)
        
        # Adicionar a nova planilha com horas totais de motor ligado
        df_horas_motor_total.to_excel(writer, sheet_name='Horas Motor', index=False)
        
        # Adicionar novas planilhas
        df_tdh.to_excel(writer, sheet_name='TDH', index=False)
        df_diesel.to_excel(writer, sheet_name='Diesel', index=False)
        df_impureza.to_excel(writer, sheet_name='Impureza Vegetal', index=False)
        
        # Adicionar planilha de coordenadas
        df_coordenadas.to_excel(writer, sheet_name='Coordenadas', index=False)
        
        # Adicionar planilha de ofensores
        df_ofensores.to_excel(writer, sheet_name='Ofensores', index=False)
        
        # ---------------- Planilhas de Média Velocidade -----------------
        if media_velocidade is None:
            media_velocidade = pd.DataFrame(columns=['Operador', 'Velocidade'])
        media_velocidade.to_excel(writer, sheet_name='Média Velocidade', index=False)
        
        # ---------------- Planilhas de Manobras -----------------
        if df_manobras_operador is None:
            df_manobras_operador = pd.DataFrame(columns=['Operador', 'Tempo Médio Manobras'])
        if df_manobras_frota is None:
            df_manobras_frota = pd.DataFrame(columns=['Frota', 'Tempo Médio Manobras'])

        df_manobras_operador.to_excel(writer, sheet_name='Manobras Operador', index=False)
        df_manobras_frota.to_excel(writer, sheet_name='Manobras Frotas', index=False)
        
        # IDs duplicadas e substituídas
        if df_duplicados is not None and not df_duplicados.empty:
            df_duplicados.to_excel(writer, sheet_name='IDs Encontradas', index=False)
        if df_substituicoes is not None and not df_substituicoes.empty:
            df_substituicoes.to_excel(writer, sheet_name='IDs Substituídas', index=False)
        
        # Formatar cada planilha
        workbook = writer.book
        for sheet_name in workbook.sheetnames:
            worksheet = workbook[sheet_name]
            ajustar_largura_colunas(worksheet)
            
            if sheet_name == '1_Disponibilidade Mecânica':
                for row in range(2, worksheet.max_row + 1):
                    cell = worksheet.cell(row=row, column=2)  # Coluna B (Disponibilidade)
                    cell.number_format = '0.00%'
                    cell = worksheet.cell(row=row, column=3)  # Coluna C (GPS)
                    cell.number_format = '0.00%'  # Formato percentual para GPS
            
            elif sheet_name == '2_Eficiência Energética':
                for row in range(2, worksheet.max_row + 1):
                    cell = worksheet.cell(row=row, column=2)  # Coluna B (Eficiência)
                    cell.number_format = '0.00%'
            
            elif sheet_name == '3_Hora Elevador':
                for row in range(2, worksheet.max_row + 1):
                    cell = worksheet.cell(row=row, column=2)  # Coluna B (Horas)
                    cell.number_format = '0.00'
            
            elif sheet_name == '4_Motor Ocioso':
                for row in range(2, worksheet.max_row + 1):
                    cell = worksheet.cell(row=row, column=2)  # Coluna B (Porcentagem)
                    cell.number_format = '0.00%'
                    cell = worksheet.cell(row=row, column=3)  # Coluna C (Tempo Ligado)
                    cell.number_format = '0.00'
                    cell = worksheet.cell(row=row, column=4)  # Coluna D (Tempo Ocioso)
                    cell.number_format = '0.00'
            
            elif sheet_name == '5_Uso GPS':
                for row in range(2, worksheet.max_row + 1):
                    cell = worksheet.cell(row=row, column=2)  # Coluna B (Porcentagem)
                    cell.number_format = '0.00%'
            
            elif sheet_name == 'Média Velocidade':
                for row in range(2, worksheet.max_row + 1):
                    cell = worksheet.cell(row=row, column=2)  # Coluna B (Velocidade)
                    cell.number_format = '0.00'
            
            elif sheet_name == 'Horas por Frota':
                for row in range(2, worksheet.max_row + 1):
                    for col in range(2, worksheet.max_column + 1):  # Todas as colunas de tempo
                        cell = worksheet.cell(row=row, column=col)
                        cell.number_format = '0.00'

# ============================================================================
# NOVA MÉTRICA: MANOBRAS
# ============================================================================

def calcular_manobras(df_base):
    """Calcula médias de manobras por Operador e por Frota.

    Retorna (df_manobras_operador, df_manobras_frota). Se não houver dados de
    manobra, devolve DataFrames vazios com colunas apropriadas.
    """
    # Precisa das colunas Estado e Diferença_Hora
    if {'Estado', 'Diferença_Hora'}.issubset(df_base.columns):
        df_man = df_base[df_base['Estado'] == 'MANOBRA'].copy()
    else:
        df_man = pd.DataFrame()

    # Média por Operador
    if not df_man.empty and 'Operador' in df_man.columns:
        df_op = (
            df_man.groupby('Operador')['Diferença_Hora']
            .mean()
            .reset_index()
            .rename(columns={'Diferença_Hora': 'Tempo Médio Manobras'})
            .sort_values('Tempo Médio Manobras', ascending=False)
        )
        def _op_with_frotas(op):
            frotas = sorted(df_man[df_man['Operador'] == op]['Equipamento'].astype(str).unique())
            return f"{op} ({', '.join(frotas)})" if frotas else op
        df_op['Operador'] = df_op['Operador'].apply(_op_with_frotas)
    else:
        df_op = pd.DataFrame(columns=['Operador', 'Tempo Médio Manobras'])

    # Média por Frota
    if not df_man.empty and 'Equipamento' in df_man.columns:
        df_frota = (
            df_man.groupby('Equipamento')['Diferença_Hora']
            .mean()
            .reset_index()
            .rename(columns={'Equipamento': 'Frota', 'Diferença_Hora': 'Tempo Médio Manobras'})
            .sort_values('Tempo Médio Manobras', ascending=False)
        )
    else:
        df_frota = pd.DataFrame(columns=['Frota', 'Tempo Médio Manobras'])

    return df_op, df_frota

def aplicar_correcao_intervalos_inteligente(df, tipo_operacao='colheita'):
    """
    FUNÇÃO PRINCIPAL: Aplica correção inteligente de intervalos
    
    Args:
        df: DataFrame com colunas Hora, Diferença_Hora já calculadas
        tipo_operacao: 'colheita' ou 'transbordo'
    
    Returns:
        DataFrame com coluna Diferença_Hora corrigida
    """
    
    print(f"🎯 Aplicando correção inteligente de intervalos ({tipo_operacao})")
    
    if len(df) < 10:
        print("   ⚠️  Poucos dados para aplicar correção")
        return df
    
    # Identificar operações produtivas e aplicar correção
    df_processado = identificar_e_corrigir_produtivos(df.copy(), OPERACOES_PRODUTIVAS_COLHEITA)
    
    return df_processado

def identificar_e_corrigir_produtivos(df, operacoes_produtivas):
    """
    Identifica operações produtivas e aplica correção baseada na média
    """
    
    # Verificar se temos coluna de operação/status
    colunas_operacao = []
    for col in df.columns:
        col_lower = col.lower()
        if any(palavra in col_lower for palavra in 
               ['operacao', 'operation', 'status', 'atividade', 'activity', 'estado', 'grupo operacao']):
            colunas_operacao.append(col)
    
    # Marcar como produtivo
    if colunas_operacao:
        coluna_op = colunas_operacao[0]
        print(f"   - Detectada coluna de operação: {coluna_op}")
        
        df['Eh_Produtivo'] = False
        for palavra in operacoes_produtivas:
            mask = df[coluna_op].astype(str).str.lower().str.contains(palavra, na=False)
            df.loc[mask, 'Eh_Produtivo'] = True
        
        # Verificar se temos coluna 'Grupo Operacao' e marcar produtivos
        if 'Grupo Operacao' in df.columns:
            mask_produtiva = df['Grupo Operacao'].astype(str).str.lower().str.contains('produtiva', na=False)
            df.loc[mask_produtiva, 'Eh_Produtivo'] = True
        
        produtivos = df['Eh_Produtivo'].sum()
        print(f"   - Operações produtivas: {produtivos}/{len(df)} ({produtivos/len(df)*100:.1f}%)")
    else:
        print("   - Coluna de operação não encontrada, assumindo todos como produtivos")
        df['Eh_Produtivo'] = True
        produtivos = len(df)
    
    if produtivos == 0:
        print("   ⚠️  Nenhuma operação produtiva encontrada")
        return df
    
    # Calcular média dos intervalos normais (apenas produtivos)
    df_produtivos = df[df['Eh_Produtivo'] == True].copy()
    media_intervalo = calcular_media_intervalos_normais_otimizada(df_produtivos)
    
    # Aplicar correções
    df_corrigido = aplicar_correcoes_inteligentes(df.copy(), media_intervalo)
    
    return df_corrigido

def calcular_media_intervalos_normais_otimizada(df_produtivos):
    """
    Calcula média otimizada dos intervalos normais em operações produtivas
    """
    
    if 'Diferença_Hora' not in df_produtivos.columns:
        print("   ❌ Coluna Diferença_Hora não encontrada")
        return 5.0 / 60  # Default 5 minutos
    
    # Converter para minutos
    df_produtivos['Diff_Minutos'] = df_produtivos['Diferença_Hora'] * 60
    
    # Filtrar intervalos normais (3-12 minutos)
    intervalos_normais = df_produtivos[
        (df_produtivos['Diff_Minutos'] >= INTERVALO_NORMAL_MIN) & 
        (df_produtivos['Diff_Minutos'] <= INTERVALO_NORMAL_MAX) &
        (df_produtivos['Diff_Minutos'] > 0)  # Excluir zeros
    ]
    
    if len(intervalos_normais) < 3:
        print("   ⚠️  Poucos intervalos normais, usando default: 5min")
        return 5.0 / 60
    
    # Calcular média, removendo outliers (usar mediana para ser mais robusto)
    media_minutos = intervalos_normais['Diff_Minutos'].median()
    media_horas = media_minutos / 60
    
    print(f"   - Intervalos normais analisados: {len(intervalos_normais)}")
    print(f"   - Média (mediana) calculada: {media_minutos:.1f}min ({media_horas:.3f}h)")
    
    return media_horas

def aplicar_correcoes_inteligentes(df, media_intervalo_horas):
    """
    Aplica correções apenas onde necessário
    """
    
    if 'Diferença_Hora' not in df.columns:
        print("   ❌ Coluna Diferença_Hora não encontrada")
        return df
    
    # Criar coluna corrigida (cópia da original)
    df['Diferença_Hora_Corrigida'] = df['Diferença_Hora'].copy()
    df['Foi_Corrigido_Inteligente'] = False
    
    correcoes = 0
    tempo_antes = 0.0
    tempo_depois = 0.0
    
    # Aplicar correção apenas em produtivos com intervalos anômalos
    for idx in df.index:
        eh_produtivo = df.loc[idx, 'Eh_Produtivo']
        intervalo_original = df.loc[idx, 'Diferença_Hora']
        intervalo_minutos = intervalo_original * 60
        
        # Corrigir se: é produtivo E tem intervalo anômalo (>30min)
        if eh_produtivo and intervalo_minutos > INTERVALO_ANOMALO_MIN:
            
            # Substituir pela média calculada
            df.loc[idx, 'Diferença_Hora_Corrigida'] = media_intervalo_horas
            df.loc[idx, 'Foi_Corrigido_Inteligente'] = True
            
            correcoes += 1
            tempo_antes += intervalo_original
            tempo_depois += media_intervalo_horas
            
            if correcoes <= 5:  # Mostrar apenas primeiras 5 correções
                print(f"   ⚡ Correção #{correcoes}: {intervalo_minutos:.1f}min → {media_intervalo_horas*60:.1f}min")
    
    # Estatísticas finais
    if correcoes > 0:
        print(f"✅ Correções aplicadas: {correcoes}")
        print(f"   - Tempo total recuperado: {tempo_antes - tempo_depois:.2f}h")
        print(f"   - Soma antes: {df['Diferença_Hora'].sum():.2f}h")
        print(f"   - Soma depois: {df['Diferença_Hora_Corrigida'].sum():.2f}h")
        
        # Substituir coluna original pela corrigida
        df['Diferença_Hora'] = df['Diferença_Hora_Corrigida']
    else:
        print("   ✅ Nenhuma correção necessária")
    
    return df

if __name__ == "__main__":
    print("="*80)
    print("Iniciando processamento de arquivos de colhedoras...")
    print(f"Processamento de arquivos CSV: {'ATIVADO' if processCsv else 'DESATIVADO'}")
    print("Este script processa arquivos de colhedoras e gera planilhas Excel com métricas")
    print("Suporta arquivos TXT, CSV e ZIP")
    print("Ignorando arquivos que contenham 'transbordo' no nome")
    print("="*50)
    print("USANDO MÉTODO AVANÇADO DE CÁLCULO DE MOTOR OCIOSO")
    print("- Tolerância de 1 minuto é aplicada a cada sequência de paradas")
    print("- Sequências de paradas com menos de 1 minuto são ignoradas")
    print("- Paradas de motor com velocidade zero são agrupadas em intervalos")
    print("="*80)
    
    try:
        processar_todos_arquivos()
        print("\nProcessamento concluído com sucesso!")
    except Exception as e:
        print(f"\nErro durante o processamento: {str(e)}")
        print("Detalhes do erro:")
        import traceback
        traceback.print_exc() 
