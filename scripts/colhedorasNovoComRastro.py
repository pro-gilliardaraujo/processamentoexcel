"""
Script para processamento completo de dados de monitoramento de colhedoras (com rastro de Latitude e Longitude).
Lê arquivos TXT ou CSV na pasta raiz, processa-os e gera arquivos Excel com planilhas auxiliares prontas.
Também processa arquivos ZIP contendo TXT ou CSV.
"""
# Constantes
COLUNAS_REMOVER = [
    'Justificativa Corte Base Desligado',
    # 'Latitude',  # Removido para manter Latitude
    # 'Longitude', # Removido para manter Longitude
    'Regional',
    'Tipo de Equipamento',
    'Unidade',
    'Centro de Custo',
    'Trabalhando em File',
    'Trabalhando Frente Dividida',
    'Trabalhando em Fila'
] 

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
    df_temp = base_calculo[['Operador', '% Eficiência Elevador']].copy()
    
    # Agrupar por operador e calcular a média (ponderada se houver múltiplas entradas)
    agrupado = df_temp.groupby('Operador')['% Eficiência Elevador'].mean().reset_index()
    
    # Renomear a coluna para o formato esperado no relatório
    agrupado.rename(columns={'% Eficiência Elevador': 'Eficiência'}, inplace=True)
    
    return agrupado 

def calcular_hora_elevador(df_base, base_calculo):
    """
    Extrai as horas de elevador da Base Calculo, sem realizar novos cálculos.
    Agrega os dados por operador, somando quando um operador aparece em múltiplas frotas.
    
    Args:
        df_base: Não usado mais, mantido para compatibilidade
        base_calculo (DataFrame): Tabela Base Calculo
    
    Returns:
        DataFrame: Horas de elevador por operador (agregado)
    """
    # Selecionar apenas as colunas relevantes
    df_temp = base_calculo[['Operador', 'Horas elevador']].copy()
    
    # Agrupar por operador e somar as horas
    agrupado = df_temp.groupby('Operador')['Horas elevador'].sum().reset_index()
    
    # Renomear a coluna para o formato esperado no relatório
    agrupado.rename(columns={'Horas elevador': 'Horas'}, inplace=True)
    
    return agrupado 

def calcular_motor_ocioso(base_calculo, df_base):
    """
    Extrai o percentual de motor ocioso por operador da Base Calculo, sem realizar novos cálculos.
    Agrega os dados por operador, calculando a média quando um operador aparece em múltiplas frotas.
    
    Args:
        base_calculo (DataFrame): Tabela Base Calculo
        df_base (DataFrame): DataFrame base, mantido para compatibilidade
    
    Returns:
        DataFrame: Percentual de motor ocioso por operador (agregado)
    """
    # Selecionar apenas as colunas relevantes
    df_temp = base_calculo[['Operador', 'Motor Ligado', 'Parado Com Motor Ligado', '% Parado com motor ligado']].copy()
    
    # Agrupar por operador
    agrupado = df_temp.groupby('Operador').agg({
        'Motor Ligado': 'sum',
        'Parado Com Motor Ligado': 'sum',
        '% Parado com motor ligado': 'mean'  # Média ponderada do percentual
    }).reset_index()
    
    # Renomear a coluna para o formato esperado no relatório
    agrupado.rename(columns={'% Parado com motor ligado': 'Porcentagem'}, inplace=True)
    
    # Colunas de saída no formato esperado
    resultado = agrupado[['Operador', 'Porcentagem', 'Motor Ligado', 'Parado Com Motor Ligado']]
    resultado.rename(columns={'Parado Com Motor Ligado': 'Tempo Ocioso', 'Motor Ligado': 'Tempo Ligado'}, inplace=True)
    
    print("\n=== DETALHAMENTO DO MOTOR OCIOSO (EXTRAÍDO DA BASE CALCULO) ===")
    for _, row in resultado.iterrows():
        print(f"\nOperador: {row['Operador']}")
        print(f"Tempo Ocioso = {row['Tempo Ocioso']:.6f} horas")
        print(f"Tempo Ligado = {row['Tempo Ligado']:.6f} horas")
        print(f"Porcentagem = {row['Porcentagem']:.6f} ({row['Porcentagem']*100:.2f}%)")
        print("-" * 60)
    
    return resultado

def calcular_uso_gps(df_base, base_calculo):
    """
    Extrai o uso de GPS da Base Calculo, sem realizar novos cálculos.
    Agrega os dados por operador, calculando a média ponderada quando um operador aparece em múltiplas frotas.
    
    Args:
        df_base: Não usado mais, mantido para compatibilidade
        base_calculo (DataFrame): Tabela Base Calculo
    
    Returns:
        DataFrame: Percentual de uso de GPS por operador (agregado)
    """
    # Selecionar apenas as colunas relevantes
    df_temp = base_calculo[['Operador', '% Utilização RTK']].copy()
    
    # Agrupar por operador e calcular a média ponderada
    agrupado = df_temp.groupby('Operador')['% Utilização RTK'].mean().reset_index()
    
    # Renomear a coluna para o formato esperado no relatório
    agrupado.rename(columns={'% Utilização RTK': 'Porcentagem'}, inplace=True)
    
    return agrupado

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
    
    # Verificar se existem operadores duplicados e alertar
    operadores_unicos = df['Operador'].unique()
    print(f"Total de operadores únicos na base: {len(operadores_unicos)}")
    for op in operadores_unicos:
        print(f"  - {op}")
    
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
            (dados_filtrados['Operacao'] == '7290 - COLHEITA CANA MECANIZADA') &
            (dados_filtrados['Pressao de Corte'] > 300) &
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
        
        # Debug para verificar os valores
        print(f"\nOperador: {operador} em {equipamento}")
        print(f"Motor Ligado: {motor_ligado:.6f}")
        print(f"Parado com Motor Ligado (método avançado): {parado_motor_ligado:.6f}")
        print(f"% Parado com motor ligado: {percent_parado_motor:.6f}")
        
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