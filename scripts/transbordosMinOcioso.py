"""
Script para processamento completo de dados de monitoramento de transbordos.
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

# Configurações
processCsv = True  # Altere para True quando quiser processar arquivos CSV

# Constantes
COLUNAS_REMOVER = [
    'Latitude',
    'Longitude',
    'Regional',
    'Unidade',
    'Centro de Custo',
    'Fazenda', 
    'Zona', 
    'Talhao'
]

COLUNAS_DESEJADAS = [
    'Data', 'Hora', 'Equipamento', 'Descricao Equipamento', 'Estado', 'Estado Operacional',
    'Grupo Equipamento/Frente', 'Grupo Operacao', 'Horimetro', 'Motor Ligado', 'Operacao', 'Operador',
    'RPM Motor', 'Tipo de Equipamento', 'Velocidade', 'Parado com motor ligado',
    'Diferença_Hora', 'Horas Produtivas', 'GPS', 'Motor Ocioso'
]

# Valores a serem filtrados
OPERADORES_EXCLUIR = ["9999 - TROCA DE TURNO"]

def calcular_motor_ocioso_novo(df):
    """
    Extrai os dados de motor ocioso da Base Calculo.
    Esta função não faz cálculos adicionais, apenas formata os dados
    já calculados na Base Calculo para exibição na planilha auxiliar.
    Os dados são agregados por operador calculando a média quando o mesmo 
    operador aparece em diferentes equipamentos/grupos.
    
    Args:
        df (DataFrame): Base Calculo com os dados já processados
        
    Returns:
        DataFrame: DataFrame com as colunas 'Operador', 'Porcentagem', 'Tempo Ligado', 'Tempo Ocioso'
    """
    # Agrupar por operador e calcular as médias
    agrupado = df.groupby('Operador').agg({
        'Motor Ligado': 'mean',  # Média do tempo ligado
        'Parado com motor ligado': 'mean',  # Média do tempo ocioso
        'Equipamento': 'count'  # Conta quantas vezes o operador aparece
    })
    
    resultado_motor_ocioso = []
    
    print("\n=== DETALHAMENTO DO MOTOR OCIOSO (DADOS DA BASE CALCULO) ===")
    
    # Para cada operador na Base Calculo
    for operador, row in agrupado.iterrows():
        tempo_ligado = row['Motor Ligado']
        tempo_ocioso = row['Parado com motor ligado']
        ocorrencias = row['Equipamento']  # Número de vezes que o operador aparece
        
        # Calcular a porcentagem usando os valores médios
        porcentagem = tempo_ocioso / tempo_ligado if tempo_ligado > 0 else 0
        
        print(f"\nOperador: {operador} (média de {ocorrencias} registros)")
        print(f"Tempo Ligado (média): {tempo_ligado:.6f}")
        print(f"Tempo Ocioso (média): {tempo_ocioso:.6f}")
        print(f"Porcentagem: {porcentagem:.6f}")
        print("-" * 50)
        
        resultado_motor_ocioso.append({
            'Operador': operador,
            'Porcentagem': porcentagem,
            'Tempo Ligado': tempo_ligado,
            'Tempo Ocioso': tempo_ocioso
        })
    
    # Retornar DataFrame formatado para a planilha
    return pd.DataFrame(resultado_motor_ocioso)

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
                ],
                "operadores_excluidos": []
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
                ],
                "operadores_excluidos": []
            },
            "equipamentos_excluidos": []
        }
    }
    
    print("Usando configurações embutidas no código, ignorando o arquivo calculos_config.json")
    return config

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
    
    # Diretório raiz do projeto
    diretorio_raiz = os.path.dirname(diretorio_script)
    
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

def aplicar_substituicao_operadores(df, mapeamento_substituicoes=None, mapeamento_horario=None):
    """
    Aplica as substituições de operadores no DataFrame.
    
    Args:
        df (DataFrame): DataFrame a ser processado
        mapeamento_substituicoes (dict, optional): Dicionário com mapeamento {operador_origem: operador_destino}
        mapeamento_horario (list, optional): Lista de dicionários com mapeamentos
            {operador_origem, operador_destino, hora_inicio, hora_fim, frota_origem}
    
    Returns:
        tuple: (DataFrame com substituições aplicadas, DataFrame com registro das substituições)
    """
    # Se mapeamento_substituicoes não foi fornecido, tenta carregar do arquivo
    if mapeamento_substituicoes is None:
        mapeamento_substituicoes = carregar_substituicoes_operadores()
    
    # Se mapeamento_horario não foi fornecido, tenta carregar do arquivo
    if mapeamento_horario is None:
        mapeamento_horario = carregar_substituicoes_operadores_horario()
    
    if (not mapeamento_substituicoes and not mapeamento_horario) or 'Operador' not in df.columns:
        return df, pd.DataFrame(columns=['ID Original', 'Nome Original', 'ID Nova', 'Nome Novo', 'Registros Afetados'])
    
    # Criar uma cópia para não alterar o DataFrame original
    df_modificado = df.copy()
    base_calculo = None
    
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
        
        # Garantir que a coluna Hora seja datetime
        if df_modificado['Hora'].dtype != 'datetime64[ns]':
            df_modificado['Hora'] = pd.to_datetime(df_modificado['Hora'], format='%H:%M:%S', errors='coerce')
        
        # Para cada linha no DataFrame
        for idx, row in df_modificado.iterrows():
            # Tenta extrair a hora do registro
            try:
                hora_registro = row['Hora'].time() if hasattr(row['Hora'], 'time') else row['Hora']
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
        
        total_horas = dados_equip['Diferença_Hora'].sum()
        
        # Calcular horas de manutenção
        manutencao = dados_equip[dados_equip['Grupo Operacao'] == 'Manutenção']['Diferença_Hora'].sum()
        
        # Se houver múltiplos dias, usar médias diárias
        if dias_equip > 1:
            total_horas = total_horas / dias_equip
            manutencao = manutencao / dias_equip
            print(f"Equipamento: {equipamento}, Dias efetivos: {dias_equip}, Média diária: {total_horas:.6f} horas")
        
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
        
        total_horas = dados_equip['Diferença_Hora'].sum()
        
        # Se houver múltiplos dias, usar média diária
        if dias_equip > 1:
            total_horas = total_horas / dias_equip
        
        # Calcular a diferença para 24 horas
        diferenca_24h = max(24 - total_horas, 0)
        
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
                horas_dia = dados_dia['Diferença_Hora'].sum()
                
                # Calcular a diferença para 24 horas neste dia
                diferenca_dia = max(24 - horas_dia, 0)
                
                # Adicionar ao resultado apenas se houver falta (diferença > 0)
                if diferenca_dia > 0:
                    resultado[f'Falta {dia}'] = diferenca_dia
                else:
                    resultado[f'Falta {dia}'] = 0.0
        
        resultados.append(resultado)
    
    return pd.DataFrame(resultados)

def calcular_eficiencia_energetica(base_calculo):
    """
    Extrai e agrega a eficiência energética por operador da tabela Base Calculo.
    Não realiza novos cálculos, apenas agrupa os valores já calculados por operador.
    
    Args:
        base_calculo (DataFrame): Tabela Base Calculo
    
    Returns:
        DataFrame: Eficiência energética por operador (agregado)
    """
    # Selecionar apenas as colunas relevantes
    df_temp = base_calculo[['Operador', 'Horas Produtivas', 'Horas totais']].copy()
    
    # Agrupar por operador e calcular a soma
    agrupado = df_temp.groupby('Operador').sum().reset_index()
    
    # Calcular eficiência a partir dos valores agrupados
    agrupado['Eficiência'] = agrupado.apply(
        lambda row: row['Horas Produtivas'] / row['Horas totais'] if row['Horas totais'] > 0 else 0,
        axis=1
    )
    
    # Retornar apenas as colunas necessárias
    return agrupado[['Operador', 'Eficiência']]

def calcular_motor_ocioso(base_calculo, df_base=None):
    """
    Extrai o percentual de motor ocioso por operador da Base Calculo, sem realizar novos cálculos.
    Agrega os dados por operador, calculando a média quando um operador aparece em múltiplas frotas.
    
    Args:
        base_calculo (DataFrame): Tabela Base Calculo
        df_base (DataFrame): DataFrame base (não usado mais, mantido para compatibilidade)
    
    Returns:
        DataFrame: Percentual de motor ocioso por operador (agregado)
    """
    # Selecionar apenas as colunas relevantes
    df_temp = base_calculo[['Operador', 'Motor Ligado', 'Parado com motor ligado', '% Parado com motor ligado']].copy()
    
    # Agrupar por operador
    agrupado = df_temp.groupby('Operador').agg({
        'Motor Ligado': 'sum',
        'Parado com motor ligado': 'sum',
        '% Parado com motor ligado': 'mean'  # Média ponderada do percentual
    }).reset_index()
    
    # Renomear as colunas para o formato esperado no relatório
    agrupado.rename(columns={
        '% Parado com motor ligado': 'Porcentagem',
        'Parado com motor ligado': 'Tempo Ocioso',
        'Motor Ligado': 'Tempo Ligado'
    }, inplace=True)
    
    # Colunas de saída no formato esperado
    resultado = agrupado[['Operador', 'Porcentagem', 'Tempo Ligado', 'Tempo Ocioso']]
    
    print("\n=== DETALHAMENTO DO MOTOR OCIOSO (EXTRAÍDO DA BASE CALCULO) ===")
    for _, row in resultado.iterrows():
        print(f"\nOperador: {row['Operador']}")
        print(f"Tempo Ocioso = {row['Tempo Ocioso']:.6f} horas")
        print(f"Tempo Ligado = {row['Tempo Ligado']:.6f} horas")
        print(f"Porcentagem = {row['Porcentagem']:.6f} ({row['Porcentagem']*100:.2f}%)")
        print("-" * 60)
    
    return resultado

def calcular_falta_apontamento(base_calculo):
    """
    Extrai o percentual de falta de apontamento por operador da Base Calculo, sem realizar novos cálculos.
    Agrega os dados por operador, calculando a média quando um operador aparece em múltiplas frotas.
    
    Args:
        base_calculo (DataFrame): Tabela Base Calculo
    
    Returns:
        DataFrame: Percentual de falta de apontamento por operador (agregado)
    """
    # Selecionar apenas as colunas relevantes
    df_temp = base_calculo[['Operador', '% Falta de Apontamento']].copy()
    
    # Agrupar por operador e calcular a média
    agrupado = df_temp.groupby('Operador')['% Falta de Apontamento'].mean().reset_index()
    
    # Renomear a coluna para o formato esperado no relatório
    agrupado.rename(columns={'% Falta de Apontamento': 'Porcentagem'}, inplace=True)
    
    print("\n=== DETALHAMENTO DE FALTA DE APONTAMENTO (EXTRAÍDO DA BASE CALCULO) ===")
    for _, row in agrupado.iterrows():
        print(f"Operador: {row['Operador']}, Porcentagem: {row['Porcentagem']:.6f}")
    print("-" * 60)
    
    return agrupado

def calcular_uso_gps(base_calculo):
    """
    Extrai o percentual de uso de GPS por operador da Base Calculo, sem realizar novos cálculos.
    Agrega os dados por operador, calculando a média quando um operador aparece em múltiplas frotas.
    
    Args:
        base_calculo (DataFrame): Tabela Base Calculo
    
    Returns:
        DataFrame: Percentual de uso de GPS por operador (agregado)
    """
    # Selecionar apenas as colunas relevantes
    df_temp = base_calculo[['Operador', '% Utilização GPS']].copy()
    
    # Agrupar por operador e calcular a média ponderada
    agrupado = df_temp.groupby('Operador')['% Utilização GPS'].mean().reset_index()
    
    # Renomear a coluna para o formato esperado no relatório
    agrupado.rename(columns={'% Utilização GPS': 'Porcentagem'}, inplace=True)
    
    print("\n=== DETALHAMENTO DE UTILIZAÇÃO DE GPS (EXTRAÍDO DA BASE CALCULO) ===")
    for _, row in agrupado.iterrows():
        print(f"Operador: {row['Operador']}, Porcentagem: {row['Porcentagem']:.6f}")
    print("-" * 60)
    
    return agrupado

def calcular_media_velocidade(df):
    """
    Calcula a média de velocidade para cada operador.
    
    Args:
        df (DataFrame): DataFrame com os dados
        
    Returns:
        DataFrame: DataFrame com a média de velocidade por operador
    """
    # Filtrar operadores excluídos
    df = df[~df['Operador'].isin(OPERADORES_EXCLUIR)]
    
    # Identificar registros válidos para cálculo de velocidade
    # Usar 'Grupo Operacao' == 'Produtiva' em vez de 'Produtivo' == 1
    registros_validos = (df['Grupo Operacao'] == 'Produtiva') & (df['Velocidade'] > 0)
    
    # Se a coluna 'Movimento' existir, adicionar à condição
    if 'Movimento' in df.columns:
        registros_validos = registros_validos & (df['Movimento'] == 1)
    
    # Calcular média de velocidade por operador
    media_velocidade = df[registros_validos].groupby('Operador')['Velocidade'].mean().reset_index()
    
    # Garantir que todos os operadores estejam no resultado, mesmo sem velocidade
    todos_operadores = df['Operador'].unique()
    for operador in todos_operadores:
        if operador not in media_velocidade['Operador'].values:
            media_velocidade = pd.concat([
                media_velocidade,
                pd.DataFrame({'Operador': [operador], 'Velocidade': [0]})
            ], ignore_index=True)
    
    # Ordenar por operador
    media_velocidade = media_velocidade.sort_values('Operador')
    
    return media_velocidade

def identificar_operadores_duplicados(df, substituicoes=None):
    """
    Identifica operadores que começam com '133' e têm 7 dígitos.
    Verifica se já existe uma substituição no arquivo JSON, caso contrário, registra como ID encontrada.
    
    Args:
        df (DataFrame): DataFrame com os dados dos operadores
        substituicoes (dict): Dicionário com as substituições do arquivo JSON
    
    Returns:
        dict: Dicionário com mapeamento {id_incorreta: id_correta}
        DataFrame: DataFrame com as IDs encontradas para relatório
    """
    if 'Operador' not in df.columns or len(df) == 0:
        return {}, pd.DataFrame(columns=['ID Encontrada', 'Nome', 'Status', 'ID Substituição'])
    
    # Extrair operadores únicos
    operadores = df['Operador'].unique()
    
    # Lista para armazenar as IDs encontradas
    ids_encontradas = []
    mapeamento = {}
    
    for op in operadores:
        if ' - ' in op:
            try:
                id_parte, nome_parte = op.split(' - ', 1)
                # Verificar se a ID começa com 133 e tem 7 dígitos
                if id_parte.startswith('133') and len(id_parte) == 7:
                    # Verificar se existe uma substituição no arquivo JSON
                    if substituicoes and op in substituicoes:
                        status = "Substituição encontrada"
                        id_substituicao = substituicoes[op].split(' - ')[0] if ' - ' in substituicoes[op] else substituicoes[op]
                        mapeamento[op] = substituicoes[op]
                    else:
                        status = "Sem substituição definida"
                        id_substituicao = ""
                    
                    # Adicionar à lista de IDs encontradas, mesmo se for "NAO CADASTRADO"
                    ids_encontradas.append({
                        'ID Encontrada': id_parte,
                        'Nome': nome_parte,
                        'Status': status,
                        'ID Substituição': id_substituicao
                    })
                    
                    print(f"ID encontrada: {id_parte} - {nome_parte}")
            except Exception as e:
                print(f"Erro ao processar operador {op}: {str(e)}")
                continue
    
    print(f"Encontradas {len(ids_encontradas)} IDs começando com 133 e 7 dígitos.")
    for id_enc in ids_encontradas:
        print(f"  - {id_enc['ID Encontrada']} - {id_enc['Nome']} ({id_enc['Status']})")
    
    # Criar o DataFrame e ordenar por ID Encontrada
    df_encontradas = pd.DataFrame(ids_encontradas)
    if not df_encontradas.empty:
        df_encontradas = df_encontradas.sort_values('ID Encontrada')
    
    return mapeamento, df_encontradas

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

def criar_excel_com_planilhas(df_base, base_calculo, disp_mecanica, eficiencia_energetica,
                            motor_ocioso, falta_apontamento, uso_gps, horas_por_frota, caminho_saida,
                            df_duplicados=None, media_velocidade=None, df_substituicoes=None):
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
    
    # Criar planilhas adicionais
    df_tdh = criar_planilha_tdh(df_base)
    df_diesel = criar_planilha_diesel(df_base)
    df_impureza = criar_planilha_impureza(df_base)
    
    with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
        # Salvar cada DataFrame em uma planilha separada
        df_base.to_excel(writer, sheet_name='BASE', index=False)
        base_calculo.to_excel(writer, sheet_name='Base Calculo', index=False)
        disp_mecanica.to_excel(writer, sheet_name='1_Disponibilidade Mecânica', index=False)
        eficiencia_energetica.to_excel(writer, sheet_name='2_Eficiência Energética', index=False)
        motor_ocioso.to_excel(writer, sheet_name='3_Motor Ocioso', index=False)
        falta_apontamento.to_excel(writer, sheet_name='4_Falta Apontamento', index=False)
        uso_gps.to_excel(writer, sheet_name='5_Uso GPS', index=False)
        horas_por_frota.to_excel(writer, sheet_name='Horas por Frota', index=False)
        
        # Adicionar novas planilhas
        df_tdh.to_excel(writer, sheet_name='TDH', index=False)
        df_diesel.to_excel(writer, sheet_name='Diesel', index=False)
        df_impureza.to_excel(writer, sheet_name='Impureza Vegetal', index=False)
        
        if media_velocidade is None:
            media_velocidade = pd.DataFrame(columns=['Operador', 'Velocidade'])
        media_velocidade.to_excel(writer, sheet_name='Média Velocidade', index=False)
        
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
            
            elif sheet_name == '2_Eficiência Energética':
                for row in range(2, worksheet.max_row + 1):
                    cell = worksheet.cell(row=row, column=2)  # Coluna B (Eficiência)
                    cell.number_format = '0.00%'
            
            elif sheet_name == '3_Motor Ocioso':
                for row in range(2, worksheet.max_row + 1):
                    cell = worksheet.cell(row=row, column=2)  # Coluna B (Porcentagem)
                    cell.number_format = '0.00%'
                    cell = worksheet.cell(row=row, column=3)  # Coluna C (Tempo Ligado)
                    cell.number_format = '0.00'  # Formato decimal
                    cell = worksheet.cell(row=row, column=4)  # Coluna D (Tempo Ocioso)
                    cell.number_format = '0.00'  # Formato decimal
            
            elif sheet_name == '4_Falta Apontamento':
                for row in range(2, worksheet.max_row + 1):
                    cell = worksheet.cell(row=row, column=2)  # Coluna B (Porcentagem)
                    cell.number_format = '0.00%'
            
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
                        cell.number_format = '0.00'  # Formato decimal
                        
            elif sheet_name == 'TDH':
                for row in range(2, worksheet.max_row + 1):
                    cell = worksheet.cell(row=row, column=2)  # Coluna B (TDH)
                    cell.number_format = '0.0000'  # 4 casas decimais
            
            elif sheet_name == 'Diesel':
                for row in range(2, worksheet.max_row + 1):
                    cell = worksheet.cell(row=row, column=2)  # Coluna B (Diesel)
                    cell.number_format = '0.0000'  # 4 casas decimais
            
            elif sheet_name == 'Impureza Vegetal':
                for row in range(2, worksheet.max_row + 1):
                    cell = worksheet.cell(row=row, column=2)  # Coluna B (Impureza)
                    cell.number_format = '0.00'  # 2 casas decimais
            
            elif sheet_name == 'Base Calculo':
                colunas_porcentagem = ['% Parado com motor ligado', '% Utilização GPS', '% Falta de Apontamento']
                colunas_tempo = ['Horas totais', 'Motor Ligado', 'Parado com motor ligado', 'GPS', 'Horas Produtivas', 'Falta de Apontamento']
                
                for row in range(2, worksheet.max_row + 1):
                    for col in range(1, worksheet.max_column + 1):
                        header = worksheet.cell(row=1, column=col).value
                        cell = worksheet.cell(row=row, column=col)
                        
                        if header in colunas_porcentagem:
                            cell.number_format = '0.00%'
                        elif header in colunas_tempo:
                            cell.number_format = '0.00'

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
    Processa todos os arquivos TXT, CSV ou ZIP de transbordos nas pastas dados e dados/transbordos.
    Busca arquivos que começam com "RV Transbordo", "frente" e "transbordos" com extensão .csv, .txt ou .zip.
    Ignora arquivos que contenham "colhedora" no nome.
    """
    # Obter o diretório onde está o script
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    
    # Diretório raiz do projeto
    diretorio_raiz = os.path.dirname(diretorio_script)
    
    # Diretórios para dados de entrada e saída
    diretorio_dados = os.path.join(diretorio_raiz, "dados")
    diretorio_transbordos = os.path.join(diretorio_raiz, "dados", "transbordos")
    diretorio_saida = os.path.join(diretorio_raiz, "output")
    
    # Verificar se os diretórios existem, caso contrário criar
    if not os.path.exists(diretorio_dados):
        os.makedirs(diretorio_dados)
    if not os.path.exists(diretorio_transbordos):
        os.makedirs(diretorio_transbordos)
    if not os.path.exists(diretorio_saida):
        os.makedirs(diretorio_saida)
    
    # Lista de diretórios para buscar arquivos
    diretorios_busca = [diretorio_dados, diretorio_transbordos]
    
    # Encontrar todos os arquivos TXT/CSV/ZIP de transbordos em ambos os diretórios
    arquivos = []
    arquivos_zip = []
    
    for diretorio in diretorios_busca:
        # Adicionar arquivos TXT sempre
        arquivos += glob.glob(os.path.join(diretorio, "RV Transbordo*.txt"))
        arquivos += glob.glob(os.path.join(diretorio, "*transbordo*.txt"))
        arquivos += glob.glob(os.path.join(diretorio, "frente*transbordos*.txt"))
        arquivos += glob.glob(os.path.join(diretorio, "transbordo*.txt"))
        
        # Adicionar arquivos CSV apenas se processCsv for True
        if processCsv:
            arquivos += glob.glob(os.path.join(diretorio, "RV Transbordo*.csv"))
            arquivos += glob.glob(os.path.join(diretorio, "*transbordo*.csv"))
            arquivos += glob.glob(os.path.join(diretorio, "frente*transbordos*.csv"))
            arquivos += glob.glob(os.path.join(diretorio, "transbordo*.csv"))
        
        # Adicionar arquivos ZIP
        arquivos_zip += glob.glob(os.path.join(diretorio, "RV Transbordo*.zip"))
        arquivos_zip += glob.glob(os.path.join(diretorio, "*transbordo*.zip"))
        arquivos_zip += glob.glob(os.path.join(diretorio, "frente*transbordos*.zip"))
        arquivos_zip += glob.glob(os.path.join(diretorio, "transbordo*.zip"))
    
    # Filtrar arquivos que contenham "colhedora" no nome (case insensitive)
    arquivos = [arquivo for arquivo in arquivos if "colhedora" not in os.path.basename(arquivo).lower()]
    arquivos_zip = [arquivo for arquivo in arquivos_zip if "colhedora" not in os.path.basename(arquivo).lower()]
    
    # Remover possíveis duplicatas
    arquivos = list(set(arquivos))
    arquivos_zip = list(set(arquivos_zip))
    
    if not arquivos and not arquivos_zip:
        print("Nenhum arquivo de transbordos encontrado nas pastas dados ou dados/transbordos!")
        return
    
    print(f"Encontrados {len(arquivos)} arquivos de transbordos (TXT/CSV) para processar.")
    print(f"Encontrados {len(arquivos_zip)} arquivos ZIP de transbordos para processar.")
    
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
            # Filtrar arquivos que contenham "colhedora" no nome
            if "colhedora" not in os.path.basename(arquivo_extraido).lower():
                processar_arquivo(arquivo_extraido, diretorio_saida)
        
        # Limpar pasta temporária se foi criada
        if pasta_temp:
            try:
                shutil.rmtree(pasta_temp)
                print(f"Pasta temporária removida: {pasta_temp}")
            except Exception as e:
                print(f"Erro ao remover pasta temporária {pasta_temp}: {str(e)}")

def processar_arquivo(caminho_arquivo, diretorio_saida):
    """
    Processa um arquivo de transbordos e gera um arquivo Excel com as métricas calculadas.
    
    Args:
        caminho_arquivo (str): Caminho do arquivo a ser processado
        diretorio_saida (str): Diretório onde o arquivo de saída será salvo
    """
    # Obter apenas o nome do arquivo (sem caminho e sem extensão)
    nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
    
    # Nome de saída igual ao original, mas com sufixo "_min" e extensão .xlsx na pasta output
    arquivo_saida = os.path.join(diretorio_saida, f"{nome_base}_min.xlsx")
    
    print(f"\nProcessando arquivo: {os.path.basename(caminho_arquivo)}")
    print(f"Arquivo de saída: {os.path.basename(arquivo_saida)}")
    
    # Processar o arquivo base
    df_base = processar_arquivo_base(caminho_arquivo)
    if df_base is None:
        print(f"Erro ao processar {os.path.basename(caminho_arquivo)}. Pulando para o próximo arquivo.")
        return
    
    # Identificar operadores com IDs que começam com 133 e têm 7 dígitos
    mapeamento_substituicoes = carregar_substituicoes_operadores()
    mapeamento_duplicados, df_duplicados = identificar_operadores_duplicados(df_base, mapeamento_substituicoes)
    
    # Combinar mapeamentos de substituição
    mapeamento_completo = {**mapeamento_substituicoes, **mapeamento_duplicados}
    
    # Carregar substituições baseadas em horário
    mapeamento_horario = carregar_substituicoes_operadores_horario()
    
    # Aplicar as substituições usando a nova função
    print("\nAplicando substituições de operadores...")
    df_base, df_substituicoes = aplicar_substituicao_operadores(df_base, mapeamento_completo, mapeamento_horario)
    
    # Se o DataFrame estiver vazio, gerar apenas a planilha BASE
    if len(df_base) == 0:
        writer = pd.ExcelWriter(arquivo_saida, engine='openpyxl')
        df_base.to_excel(writer, sheet_name='BASE', index=False)
        if not df_duplicados.empty:
            df_duplicados.to_excel(writer, sheet_name='IDs Encontradas', index=False)
        writer.close()
        print(f"Arquivo {arquivo_saida} gerado com apenas a planilha BASE (sem dados).")
        return
    
    # Primeiro, aplicar o novo cálculo de motor ocioso no DataFrame
    # Esta função modifica o df_base adicionando a coluna 'Motor Ocioso' e também retorna um DataFrame formatado para a planilha
    df_base_com_motor_ocioso = calcular_motor_ocioso_para_base(df_base)
    
    # Agora calculamos a Base Calculo
    base_calculo = calcular_base_calculo(df_base_com_motor_ocioso)
    
    # Calcular as métricas auxiliares
    disp_mecanica = calcular_disponibilidade_mecanica(df_base_com_motor_ocioso)
    eficiencia_energetica = calcular_eficiencia_energetica(base_calculo)
    motor_ocioso = calcular_motor_ocioso(base_calculo, df_base_com_motor_ocioso)
    falta_apontamento = calcular_falta_apontamento(base_calculo)
    uso_gps = calcular_uso_gps(base_calculo)
    horas_por_frota = calcular_horas_por_frota(df_base_com_motor_ocioso)
    
    # Calcular média de velocidade por operador
    media_velocidade = calcular_media_velocidade(df_base_com_motor_ocioso)
    
    # Criar o arquivo Excel com todas as planilhas
    criar_excel_com_planilhas(
        df_base_com_motor_ocioso, base_calculo, disp_mecanica, eficiencia_energetica,
        motor_ocioso, falta_apontamento, uso_gps, horas_por_frota, arquivo_saida,
        df_duplicados,  # Adicionar a tabela de IDs duplicadas
        media_velocidade,  # Adicionar a tabela de média de velocidade
        df_substituicoes  # Adicionar a tabela de IDs substituídas
    )
    
    print(f"Arquivo {arquivo_saida} gerado com sucesso!")

def salvar_planilha_base(df, caminho_saida):
    """
    Salva o DataFrame em um arquivo Excel, aplicando formatação adequada.
    
    Args:
        df (DataFrame): DataFrame a ser salvo
        caminho_saida (str): Caminho do arquivo Excel de saída
    """
    try:
        # Criar uma cópia do DataFrame para não modificar o original
        df_copy = df.copy()
        
        # Identificar colunas de tempo
        colunas_tempo = ['Diferença_Hora', 'Horas Produtivas']
        
        # Criar arquivo Excel
        writer = pd.ExcelWriter(caminho_saida, engine='openpyxl')
        
        # Salvar DataFrame
        df_copy.to_excel(writer, index=False)
        
        # Ajustar largura das colunas e aplicar formatação
        worksheet = writer.book.active
        
        # Ajustar largura das colunas
        for idx, col in enumerate(df_copy.columns):
            max_length = max(
                df_copy[col].astype(str).apply(len).max(),
                len(str(col))
            )
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[get_column_letter(idx + 1)].width = adjusted_width
            
            # Aplicar formatação de tempo
            if col in colunas_tempo:
                for row in range(2, worksheet.max_row + 1):
                    cell = worksheet.cell(row=row, column=idx + 1)
                    cell.number_format = '0.00'  # Formato decimal
        
        # Salvar arquivo
        writer.close()
        print(f"Arquivo {caminho_saida} gerado com sucesso!")
        
    except Exception as e:
        print(f"Erro ao gerar arquivo {caminho_saida}: {str(e)}")
        print(f"Arquivo {caminho_saida} não foi gerado.")

def calcular_motor_ocioso_para_base(df):
    """
    Calcula o tempo de motor ocioso para cada registro no DataFrame original.
    Esta função é diferente de calcular_motor_ocioso_novo, pois processa os dados brutos,
    enquanto calcular_motor_ocioso_novo processa os dados já agregados na Base Calculo.
    
    Args:
        df (DataFrame): DataFrame original com os dados de operação
        
    Returns:
        DataFrame: DataFrame modificado com a coluna 'Motor Ocioso' preenchida
    """
    # Verificar se as colunas necessárias existem
    colunas_necessarias = ['Equipamento', 'Estado', 'Motor Ligado']
    for coluna in colunas_necessarias:
        if coluna not in df.columns:
            print(f"AVISO: Coluna {coluna} não encontrada. Adicionando com valores padrão.")
            if coluna == 'Motor Ligado':
                # Para transbordos, assumir que o motor está sempre ligado
                df[coluna] = 'LIGADO'
            else:
                df[coluna] = 'Desconhecido'
    
    # Inicializar coluna de Motor Ocioso se não existir
    if 'Motor Ocioso' not in df.columns:
        df['Motor Ocioso'] = 0
    
    # Para transbordos, consideramos motor ocioso quando:
    # 1. O motor está ligado (Motor Ligado = 'LIGADO')
    # 2. O veículo está parado (Estado = 'Parado')
    # 3. O tempo ocioso por registro é a Diferença_Hora correspondente
    
    # Verificar se possuímos a coluna Diferença_Hora
    if 'Diferença_Hora' not in df.columns:
        print("AVISO: Coluna Diferença_Hora não encontrada. Usando valor padrão.")
        df['Diferença_Hora'] = 0.5  # 30 minutos por padrão
    
    # Aplicar a regra de cálculo para cada registro
    df['Motor Ocioso'] = df.apply(
        lambda row: row['Diferença_Hora'] if row['Estado'] == 'Parado' and row['Motor Ligado'] == 'LIGADO' else 0,
        axis=1
    )
    
    # Garantir que o tempo de motor ocioso nunca seja maior que o tempo total
    df['Motor Ocioso'] = df.apply(
        lambda row: min(row['Motor Ocioso'], row['Diferença_Hora']),
        axis=1
    )
    
    print(f"Cálculo de Motor Ocioso concluído. Total de horas ociosas: {df['Motor Ocioso'].sum():.2f}")
    
    return df

def processar_arquivo_base(caminho_arquivo):
    """
    Processa um arquivo base (TXT ou CSV) e retorna um DataFrame pandas formatado.
    
    Args:
        caminho_arquivo (str): Caminho para o arquivo a ser processado
        
    Returns:
        DataFrame: DataFrame pandas com os dados processados ou None em caso de erro
    """
    try:
        print(f"Lendo arquivo: {os.path.basename(caminho_arquivo)}")
        
        # Verificar a extensão do arquivo
        extensao = os.path.splitext(caminho_arquivo)[1].lower()
        
        # Ler o arquivo conforme sua extensão
        if extensao == '.txt':
            # Tentar ler como TXT, tentando detectar o separador
            separadores = [';', ',', '\t']
            for sep in separadores:
                try:
                    df = pd.read_csv(caminho_arquivo, sep=sep, encoding='utf-8')
                    # Se chegou aqui, conseguiu ler o arquivo com este separador
                    print(f"Arquivo lido com sucesso usando separador: '{sep}'")
                    break
                except Exception:
                    continue
            else:
                # Se nenhum separador funcionou, tentar com encoding latin1
                for sep in separadores:
                    try:
                        df = pd.read_csv(caminho_arquivo, sep=sep, encoding='latin1')
                        print(f"Arquivo lido com sucesso usando separador: '{sep}' e encoding latin1")
                        break
                    except Exception:
                        continue
                else:
                    raise ValueError(f"Não foi possível ler o arquivo {caminho_arquivo} com nenhum separador.")
        
        elif extensao == '.csv':
            # Tentar ler como CSV
            try:
                df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8')
            except:
                try:
                    df = pd.read_csv(caminho_arquivo, sep=',', encoding='utf-8')
                except:
                    try:
                        df = pd.read_csv(caminho_arquivo, sep=';', encoding='latin1')
                    except:
                        df = pd.read_csv(caminho_arquivo, sep=',', encoding='latin1')
        else:
            raise ValueError(f"Extensão de arquivo não suportada: {extensao}")
        
        # Verificar se o DataFrame foi carregado corretamente
        if df.empty:
            print(f"O arquivo {os.path.basename(caminho_arquivo)} não contém dados.")
            return pd.DataFrame()
        
        print(f"Arquivo carregado com {len(df)} registros e {len(df.columns)} colunas.")
        
        # Normalizar nomes das colunas (remover espaços extras, converter para título)
        df.columns = [col.strip() for col in df.columns]
        
        # Verificar colunas essenciais
        colunas_essenciais = ['Equipamento', 'Operador', 'Estado', 'Hora']
        colunas_faltantes = [col for col in colunas_essenciais if col not in df.columns]
        
        if colunas_faltantes:
            print(f"AVISO: As colunas {colunas_faltantes} estão faltando no arquivo.")
            
            # Tentar encontrar alternativas para as colunas faltantes
            mapeamento_alternativo = {
                'Equipamento': ['Frota', 'ID Equipamento', 'ID_Equipamento'],
                'Operador': ['Motorista', 'Condutor', 'ID Operador'],
                'Estado': ['Status', 'Estado Operacional', 'Situacao'],
                'Hora': ['Horário', 'Time', 'Timestamp']
            }
            
            # Tentar encontrar e renomear as colunas alternativas
            for col_faltante in colunas_faltantes:
                for alt in mapeamento_alternativo.get(col_faltante, []):
                    if alt in df.columns:
                        print(f"Usando coluna alternativa: '{alt}' para '{col_faltante}'")
                        df.rename(columns={alt: col_faltante}, inplace=True)
                        break
        
        # Remover colunas não utilizadas, se existirem
        colunas_para_remover = [col for col in COLUNAS_REMOVER if col in df.columns]
        if colunas_para_remover:
            df = df.drop(columns=colunas_para_remover)
            print(f"Colunas removidas: {colunas_para_remover}")
        
        # Processar coluna Data e Hora
        if 'Data' in df.columns and 'Hora' in df.columns:
            # Converter Data para datetime
            try:
                df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
            except:
                try:
                    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
                except Exception as e:
                    print(f"Erro ao converter coluna Data: {str(e)}")
            
            # Converter Hora para datetime.time
            try:
                df['Hora'] = pd.to_datetime(df['Hora'], format='%H:%M:%S', errors='coerce').dt.time
            except Exception as e:
                print(f"Erro ao converter coluna Hora: {str(e)}")
                # Tentar outros formatos
                try:
                    df['Hora'] = pd.to_datetime(df['Hora'], errors='coerce').dt.time
                except:
                    pass
        
        # Calcular a diferença de horas entre registros consecutivos
        df = calcular_diferencas_hora(df)
        
        # Adicionar coluna de Horas Produtivas
        # Se 'Grupo Operacao' existe, considere 'Produtiva' quando for 'Produtiva'
        if 'Grupo Operacao' in df.columns:
            df['Horas Produtivas'] = df.apply(
                lambda row: row['Diferença_Hora'] if row['Grupo Operacao'] == 'Produtiva' else 0,
                axis=1
            )
        else:
            # Se não existir 'Grupo Operacao', assumir 0
            df['Horas Produtivas'] = 0
        
        # Adicionar coluna GPS 
        if 'GPS' not in df.columns:
            # Se 'Latitude' e 'Longitude' existirem, considerar GPS válido
            if 'Latitude' in df.columns and 'Longitude' in df.columns:
                df['GPS'] = df.apply(
                    lambda row: 1 if pd.notnull(row['Latitude']) and pd.notnull(row['Longitude']) else 0,
                    axis=1
                )
            else:
                # GPS desconhecido
                df['GPS'] = 0
        
        # Adicionar coluna de Parado com Motor Ligado se não existir
        if 'Parado com motor ligado' not in df.columns:
            if 'Estado' in df.columns and 'Motor Ligado' in df.columns:
                # Considerar parado com motor ligado quando Estado é 'Parado' e Motor Ligado é 'LIGADO'
                df['Parado com motor ligado'] = df.apply(
                    lambda row: 1 if row['Estado'] == 'Parado' and row['Motor Ligado'] == 'LIGADO' else 0,
                    axis=1
                )
            else:
                # Não é possível determinar, assumir 0
                df['Parado com motor ligado'] = 0
        
        # Retornar o DataFrame processado
        return df
    
    except Exception as e:
        print(f"Erro ao processar o arquivo {caminho_arquivo}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def calcular_diferencas_hora(df):
    """
    Calcula a diferença de horas entre registros consecutivos para cada equipamento.
    
    Args:
        df (DataFrame): DataFrame com os dados
        
    Returns:
        DataFrame: DataFrame com a coluna 'Diferença_Hora' adicionada
    """
    try:
        # Inicializar coluna de diferença com zero
        df['Diferença_Hora'] = 0.0
        
        # Se não tiver coluna Data ou Hora, não é possível calcular diferenças
        if 'Data' not in df.columns or 'Hora' not in df.columns:
            print("AVISO: Colunas 'Data' ou 'Hora' não encontradas. Não é possível calcular diferenças de hora.")
            return df
        
        # Converter Data e Hora para datetime
        df['DateTime'] = None
        for i, row in df.iterrows():
            try:
                # Combinar data e hora
                if pd.notnull(row['Data']) and pd.notnull(row['Hora']):
                    data = row['Data']
                    hora = row['Hora']
                    
                    # Se hora for um objeto time, converter para string
                    if hasattr(hora, 'strftime'):
                        hora_str = hora.strftime('%H:%M:%S')
                    else:
                        hora_str = str(hora)
                    
                    # Se data for um objeto datetime, converter para string
                    if hasattr(data, 'strftime'):
                        data_str = data.strftime('%Y-%m-%d')
                    else:
                        data_str = str(data)
                    
                    # Combinar e converter para datetime
                    df.at[i, 'DateTime'] = pd.to_datetime(f"{data_str} {hora_str}")
            except Exception as e:
                print(f"Erro ao converter data/hora na linha {i}: {str(e)}")
        
        # Agrupar por equipamento
        equipamentos = df['Equipamento'].unique()
        
        for equip in equipamentos:
            # Filtrar registros deste equipamento
            indices = df[df['Equipamento'] == equip].index
            
            if len(indices) <= 1:
                continue
            
            # Ordenar por DateTime
            if pd.notnull(df.loc[indices, 'DateTime']).all():
                indices_ordenados = df.loc[indices].sort_values('DateTime').index
                
                # Calcular diferenças
                for i in range(len(indices_ordenados) - 1):
                    idx_atual = indices_ordenados[i]
                    idx_proximo = indices_ordenados[i + 1]
                    
                    if pd.notnull(df.loc[idx_atual, 'DateTime']) and pd.notnull(df.loc[idx_proximo, 'DateTime']):
                        # Calcular diferença em horas
                        diferenca = (df.loc[idx_proximo, 'DateTime'] - df.loc[idx_atual, 'DateTime']).total_seconds() / 3600
                        
                        # Aplicar a diferença ao registro atual
                        df.at[idx_atual, 'Diferença_Hora'] = diferenca
                
                # Último registro: usar a média das diferenças anteriores ou um valor padrão
                if len(indices_ordenados) > 1:
                    diferencas = df.loc[indices_ordenados[:-1], 'Diferença_Hora']
                    media = diferencas.mean() if not diferencas.empty else 0.5  # Padrão: 30 minutos
                    df.at[indices_ordenados[-1], 'Diferença_Hora'] = media
        
        # Remover a coluna auxiliar
        df = df.drop('DateTime', axis=1)
        
        return df
    
    except Exception as e:
        print(f"Erro ao calcular diferenças de hora: {str(e)}")
        import traceback
        traceback.print_exc()
        return df

def calcular_base_calculo(df):
    """
    Calcula a tabela Base Calculo a partir dos dados do DataFrame base.
    Esta função agrega os dados por Operador e Equipamento, calculando métricas importantes.
    
    Args:
        df (DataFrame): DataFrame com os dados já processados
        
    Returns:
        DataFrame: DataFrame com a Base Calculo
    """
    # Verificar se o DataFrame está vazio
    if df.empty:
        return pd.DataFrame()
    
    # Garantir que temos as colunas necessárias
    colunas_necessarias = [
        'Operador', 'Equipamento', 'Diferença_Hora', 'Horas Produtivas',
        'GPS', 'Parado com motor ligado', 'Motor Ligado'
    ]
    
    colunas_faltantes = [col for col in colunas_necessarias if col not in df.columns]
    if colunas_faltantes:
        print(f"AVISO: Colunas necessárias para Base Calculo estão faltando: {colunas_faltantes}")
        # Adicionar colunas faltantes com valor 0
        for col in colunas_faltantes:
            df[col] = 0
    
    # Filtrar operadores excluídos
    df_filtrado = df[~df['Operador'].isin(OPERADORES_EXCLUIR)]
    
    # Agrupar por Operador e Equipamento
    base_calculo = df_filtrado.groupby(['Operador', 'Equipamento']).agg({
        'Diferença_Hora': 'sum',              # Total de horas
        'Horas Produtivas': 'sum',            # Horas produtivas
        'GPS': 'sum',                         # Tempo com GPS válido
        'Parado com motor ligado': 'sum',     # Tempo ocioso (parado com motor ligado)
        'Motor Ocioso': 'sum'                 # Tempo de motor ocioso calculado
    }).reset_index()
    
    # Renomear colunas
    base_calculo.rename(columns={
        'Diferença_Hora': 'Horas totais',
        'Motor Ocioso': 'Motor Ocioso Calculado'
    }, inplace=True)
    
    # Calcular métricas adicionais
    
    # 1. Tempo de motor ligado (considerar como igual a Horas totais para transbordo)
    base_calculo['Motor Ligado'] = base_calculo['Horas totais']
    
    # 2. Percentual de tempo ocioso (parado com motor ligado)
    base_calculo['% Parado com motor ligado'] = base_calculo.apply(
        lambda row: row['Parado com motor ligado'] / row['Motor Ligado'] 
                   if row['Motor Ligado'] > 0 else 0,
        axis=1
    )
    
    # 3. Percentual de utilização de GPS
    base_calculo['% Utilização GPS'] = base_calculo.apply(
        lambda row: row['GPS'] / row['Horas totais'] 
                   if row['Horas totais'] > 0 else 0,
        axis=1
    )
    
    # 4. Calcular Falta de Apontamento
    # Para transbordos, considerar falta de apontamento quando:
    # - Não está em horas produtivas
    # - Não está em tempo ocioso
    base_calculo['Falta de Apontamento'] = base_calculo.apply(
        lambda row: row['Horas totais'] - row['Horas Produtivas'] - row['Parado com motor ligado'],
        axis=1
    )
    
    # 5. Percentual de Falta de Apontamento
    base_calculo['% Falta de Apontamento'] = base_calculo.apply(
        lambda row: row['Falta de Apontamento'] / row['Horas totais'] 
                   if row['Horas totais'] > 0 else 0,
        axis=1
    )
    
    # 6. Calcular eficiência energética (Horas Produtivas / Horas totais)
    base_calculo['Eficiência Energética'] = base_calculo.apply(
        lambda row: row['Horas Produtivas'] / row['Horas totais']
                   if row['Horas totais'] > 0 else 0,
        axis=1
    )
    
    # Aplicar correções para valores negativos ou valores > 1
    colunas_porcentagem = ['% Parado com motor ligado', '% Utilização GPS', '% Falta de Apontamento']
    for col in colunas_porcentagem:
        base_calculo[col] = base_calculo[col].clip(0, 1)  # Limitar entre 0 e 1
    
    # Garantir que Falta de Apontamento não seja negativa
    base_calculo['Falta de Apontamento'] = base_calculo['Falta de Apontamento'].clip(0)
    
    return base_calculo

if __name__ == "__main__":
    print("="*80)
    print("Iniciando processamento de arquivos de transbordos...")
    print(f"Processamento de arquivos CSV: {'ATIVADO' if processCsv else 'DESATIVADO'}")
    print("Este script processa arquivos de transbordos e gera planilhas Excel com métricas")
    print("Suporta arquivos TXT, CSV e ZIP")
    print("Ignorando arquivos que contenham 'colhedora' no nome")
    print("="*80)
    processar_todos_arquivos()
    print("\nProcessamento concluído!") 