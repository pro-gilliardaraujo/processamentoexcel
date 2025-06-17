#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para testar diferentes combinações de tempo mínimo e velocidade mínima
para filtrar manobras e encontrar os valores que resultam em 216 manobras.
"""

import os
import glob
import sys
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path
import zipfile

# Importar funções necessárias do script original
# Assumindo que estamos no mesmo diretório que o script original
# A função de processamento (colhedoras ou transbordos) será escolhida
# dinamicamente durante a execução. Não fazemos import fixo aqui.

# Número alvo de manobras que queremos alcançar
MANOBRAS_ALVO = 259

# Limite de tempo para o teste (em segundos)
LIMITE_TEMPO = 0  # 0 desativa limite de tempo

# Número mínimo de combinações exatas a encontrar
MIN_COMBINACOES_EXATAS = 25

def testar_combinacoes(arquivo_entrada, arquivo_saida_excel, arquivo_saida_mapa, tempos_minimos=None, velocidades_minimas=None):
    """
    Testa diferentes combinações de tempo mínimo e velocidade mínima
    e registra os resultados em um arquivo Excel.
    
    Args:
        arquivo_entrada (str): Caminho para o arquivo de dados de colhedoras
        arquivo_saida_excel (str): Caminho para salvar o arquivo Excel com resultados
        arquivo_saida_mapa (str): Caminho para salvar o mapa visual (PNG)
    """
    print(f"Iniciando teste com arquivo: {arquivo_entrada}")
    
    # Verificar se é um arquivo ZIP
    arquivo_para_processar = arquivo_entrada
    pasta_temp = None
    
    if arquivo_entrada.lower().endswith('.zip'):
        print("Arquivo ZIP detectado. Extraindo...")
        try:
            # Criar pasta temporária para extração
            import tempfile
            pasta_temp = tempfile.mkdtemp()
            
            # Extrair arquivo ZIP
            with zipfile.ZipFile(arquivo_entrada, 'r') as zip_ref:
                zip_ref.extractall(pasta_temp)
            
            # Encontrar arquivos TXT ou CSV extraídos
            arquivos_extraidos = []
            for ext in ['.txt', '.csv']:
                arquivos_extraidos.extend(glob.glob(os.path.join(pasta_temp, f"*{ext}")))
            
            if not arquivos_extraidos:
                print("Nenhum arquivo TXT ou CSV encontrado dentro do ZIP.")
                return
            
            # Usar o primeiro arquivo encontrado
            arquivo_para_processar = arquivos_extraidos[0]
            print(f"Usando arquivo extraído: {os.path.basename(arquivo_para_processar)}")
        
        except Exception as e:
            print(f"Erro ao extrair arquivo ZIP: {str(e)}")
            return
    
    # Selecionar dinamicamente a função de processamento adequada
    nome_arquivo_lower = os.path.basename(arquivo_para_processar).lower()
    try:
        if 'transbordo' in nome_arquivo_lower:
            from transbordosMinOcioso import processar_arquivo_base as _processar
        else:
            from colhedorasNovoRastros import processar_arquivo_base as _processar
    except ImportError:
        # Tentar novamente adicionando o diretório atual ao sys.path
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        if 'transbordo' in nome_arquivo_lower:
            from transbordosMinOcioso import processar_arquivo_base as _processar
        else:
            from colhedorasNovoRastros import processar_arquivo_base as _processar

    df_base = _processar(arquivo_para_processar)
    
    # Limpar pasta temporária se foi criada
    if pasta_temp:
        try:
            import shutil
            shutil.rmtree(pasta_temp)
            print("Pasta temporária removida.")
        except:
            print("Não foi possível remover a pasta temporária.")
    
    if df_base is None or len(df_base) == 0:
        print("Erro ao processar o arquivo de entrada ou arquivo vazio.")
        return
    
    # Filtrar apenas registros com Estado = 'MANOBRA'
    df_manobras_total = df_base[df_base['Estado'] == 'MANOBRA']
    total_manobras_original = len(df_manobras_total)
    
    print(f"Total de manobras no arquivo original: {total_manobras_original}")
    print(f"Alvo de manobras a encontrar: {MANOBRAS_ALVO}")
    
    # Definir ranges para os parâmetros a testar
    if tempos_minimos is None:
        tempos_minimos = np.concatenate([
            np.arange(1.0, 4.1, 0.1),     # 1-4 segundos em passos de 0.1
            np.array([2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4, 3.6, 3.8, 4.0])
        ])

    if velocidades_minimas is None:
        velocidades_minimas = np.arange(0, 10.01, 0.1)
    
    # Lista para armazenar resultados
    resultados = []
    
    # Contadores
    combinacoes_testadas = 0
    combinacoes_exatas = 0
    
    # Tempo inicial
    tempo_inicio = time.time()
    
    # Matriz para o mapa de calor
    mapa_resultados = np.zeros((len(tempos_minimos), len(velocidades_minimas)))
    
    print(f"Testando combinações até encontrar pelo menos {MIN_COMBINACOES_EXATAS} resultados exatos (sem limite de tempo)...")
    
    # Testar cada combinação
    for i, tempo_minimo in enumerate(tempos_minimos):
        for j, velocidade_minima in enumerate(velocidades_minimas):
            # Verificar limite de tempo
            if LIMITE_TEMPO and time.time() - tempo_inicio > LIMITE_TEMPO:
                print(f"Limite de tempo atingido ({LIMITE_TEMPO} segundos).")
                break
            
            # Converter tempo para horas
            tempo_minimo_horas = tempo_minimo / 3600
            
            # Aplicar filtros
            df_manobras_filtrado = df_manobras_total[
                (df_manobras_total['Diferença_Hora'] >= tempo_minimo_horas) & 
                (df_manobras_total['Velocidade'] >= velocidade_minima)
            ]
            
            # Contar manobras após filtro
            total_manobras_filtrado = len(df_manobras_filtrado)
            
            # Calcular diferença do alvo
            diferenca = total_manobras_filtrado - MANOBRAS_ALVO
            
            # Armazenar resultado
            resultados.append({
                'Tempo Mínimo (s)': tempo_minimo,
                'Velocidade Mínima (km/h)': velocidade_minima,
                'Manobras': total_manobras_filtrado,
                'Diferença': diferenca,
                'Diferença Absoluta': abs(diferenca)
            })
            
            # Atualizar matriz do mapa de calor
            mapa_resultados[i, j] = abs(diferenca)
            
            # Incrementar contador
            combinacoes_testadas += 1
            
            # Se encontrou uma combinação exata
            if diferenca == 0:
                combinacoes_exatas += 1
                print(f"Combinação exata encontrada: Tempo={tempo_minimo}s, Velocidade={velocidade_minima:.2f}km/h")
                
                # Se encontramos o número mínimo de combinações exatas, podemos parar
                if combinacoes_exatas >= MIN_COMBINACOES_EXATAS:
                    print(f"Encontradas {combinacoes_exatas} combinações exatas. Parando busca.")
                    break
        
        # Verificar novamente após cada linha da matriz
        if (LIMITE_TEMPO and time.time() - tempo_inicio > LIMITE_TEMPO) or combinacoes_exatas >= MIN_COMBINACOES_EXATAS:
            break
    
    # Tempo total
    tempo_total = time.time() - tempo_inicio
    
    print(f"Teste concluído em {tempo_total:.2f} segundos.")
    print(f"Combinações testadas: {combinacoes_testadas}")
    print(f"Combinações exatas encontradas: {combinacoes_exatas}")
    
    # Criar DataFrame com resultados
    df_resultados = pd.DataFrame(resultados)
    
    # Ordenar por diferença absoluta (menor primeiro)
    df_resultados = df_resultados.sort_values('Diferença Absoluta')
    
    # Adicionar metadados
    metadados = pd.DataFrame([{
        'Arquivo de Entrada': arquivo_entrada,
        'Total Manobras Original': total_manobras_original,
        'Manobras Alvo': MANOBRAS_ALVO,
        'Combinações Testadas': combinacoes_testadas,
        'Combinações Exatas': combinacoes_exatas,
        'Tempo de Execução (s)': tempo_total,
        'Data/Hora': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }])
    
    # Salvar resultados em Excel
    with pd.ExcelWriter(arquivo_saida_excel) as writer:
        metadados.to_excel(writer, sheet_name='Metadados', index=False)
        df_resultados.to_excel(writer, sheet_name='Resultados', index=False)
        
        # Se houver combinações exatas, criar uma planilha específica
        if combinacoes_exatas > 0:
            df_exatas = df_resultados[df_resultados['Diferença'] == 0]
            df_exatas.to_excel(writer, sheet_name='Combinações Exatas', index=False)
    
    print(f"Resultados salvos em: {arquivo_saida_excel}")
    
    # Criar mapa de calor
    plt.figure(figsize=(12, 10))
    
    # Limitar a matriz aos valores realmente testados
    mapa_recortado = mapa_resultados[:i+1, :j+1]
    
    # Criar mapa de calor usando seaborn
    ax = sns.heatmap(
        mapa_recortado,
        xticklabels=np.round(velocidades_minimas[:j+1], 1),
        yticklabels=tempos_minimos[:i+1],
        cmap='viridis_r',  # Cores invertidas para que valores menores (melhores) sejam mais escuros
        cbar_kws={'label': 'Diferença Absoluta do Alvo'}
    )
    
    # Configurar rótulos
    plt.xlabel('Velocidade Mínima (km/h)')
    plt.ylabel('Tempo Mínimo (s)')
    plt.title(f'Mapa de Diferenças para Alvo de {MANOBRAS_ALVO} Manobras')
    
    # Ajustar rótulos para melhor visualização
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Salvar figura
    plt.savefig(arquivo_saida_mapa, dpi=300)
    print(f"Mapa visual salvo em: {arquivo_saida_mapa}")
    
    # Mostrar as melhores combinações
    print("\nMelhores combinações encontradas:")
    for _, row in df_resultados.head(5).iterrows():
        print(f"Tempo: {row['Tempo Mínimo (s)']:3.0f}s, Velocidade: {row['Velocidade Mínima (km/h)']:4.1f}km/h → "
              f"Manobras: {row['Manobras']:3.0f}, Diferença: {row['Diferença']:+3.0f}")

    if combinacoes_exatas < MIN_COMBINACOES_EXATAS:
        print("\nNenhuma combinação exata encontrada dentro da grade atual. Expandindo busca ...")
        # Expandir ranges e tentar novamente (apenas uma vez)
        if (len(tempos_minimos) < 121) or (velocidades_minimas[1]-velocidades_minimas[0] > 0.05):
            novos_tempos = np.arange(0, 121, 1)  # 0–120 s passo 1
            novos_velocidades = np.arange(0, 10.01, 0.05)  # passo 0.05 km/h
            return testar_combinacoes(arquivo_entrada, arquivo_saida_excel, arquivo_saida_mapa, novos_tempos, novos_velocidades)

def encontrar_arquivos_colhedoras():
    """
    Busca arquivos de colhedoras no diretório de dados.
    Retorna uma lista de caminhos de arquivos.
    """
    # Diretório raiz do projeto (assumindo que o script está em /scripts)
    diretorio_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    diretorio_dados = os.path.join(diretorio_raiz, "dados")
    
    # Padrões de arquivos de colhedoras
    padroes = [
        os.path.join(diretorio_dados, "*colhedora*.txt"),
        os.path.join(diretorio_dados, "*colhedora*.csv"),
        os.path.join(diretorio_dados, "colhedoras*.txt"),
        os.path.join(diretorio_dados, "colhedoras*.csv"),
        os.path.join(diretorio_dados, "*CD*.txt"),
        os.path.join(diretorio_dados, "*CD*.csv"),
        os.path.join(diretorio_dados, "colhedoras*.zip"),
        os.path.join(diretorio_dados, "*colhedora*.zip"),
        os.path.join(diretorio_dados, "*CD*.zip"),
        # Padrões de transbordos
        os.path.join(diretorio_dados, "*transbordo*.txt"),
        os.path.join(diretorio_dados, "*transbordo*.csv"),
        os.path.join(diretorio_dados, "transbordos*.txt"),
        os.path.join(diretorio_dados, "transbordos*.csv"),
        os.path.join(diretorio_dados, "*transbordo*.zip"),
        os.path.join(diretorio_dados, "transbordos*.zip"),
    ]
    
    # Encontrar todos os arquivos que correspondem aos padrões
    arquivos = []
    for padrao in padroes:
        arquivos.extend(glob.glob(padrao))
    
    # Remover duplicatas
    arquivos = list(set(arquivos))
    
    # Se não encontrou nenhum arquivo, adicionar manualmente o arquivo colhedorasFrente03.zip
    if not arquivos:
        arquivo_especifico = os.path.join(diretorio_dados, "colhedorasFrente03.zip")
        if os.path.exists(arquivo_especifico):
            arquivos.append(arquivo_especifico)
    
    return arquivos

if __name__ == "__main__":
    # Verificar dependências
    try:
        import matplotlib
        import seaborn
    except ImportError:
        print("Por favor, instale as dependências necessárias:")
        print("pip install matplotlib seaborn")
        sys.exit(1)
    
    # Encontrar arquivos de dados para teste (colhedoras ou transbordos)
    arquivos = encontrar_arquivos_colhedoras()
    
    if not arquivos:
        print("Nenhum arquivo de dados encontrado (colhedoras ou transbordos).")
        print("Por favor, coloque o arquivo desejado na pasta 'dados' com 'colhedoras' ou 'transbordos' no nome.")
        sys.exit(1)
    
    # Mostrar arquivos encontrados
    print(f"Encontrados {len(arquivos)} arquivos:")
    for i, arquivo in enumerate(arquivos):
        print(f"{i+1}. {os.path.basename(arquivo)}")
    
    # Selecionar arquivo para teste
    if len(arquivos) == 1:
        idx = 0
    else:
        idx = int(input(f"\nSelecione o arquivo para teste (1-{len(arquivos)}): ")) - 1
    
    arquivo_selecionado = arquivos[idx]
    
    # Criar diretório de saída se não existir
    diretorio_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    diretorio_saida = os.path.join(diretorio_raiz, "output")
    os.makedirs(diretorio_saida, exist_ok=True)
    
    # Definir nomes dos arquivos de saída
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_base = os.path.splitext(os.path.basename(arquivo_selecionado))[0]
    
    arquivo_saida_excel = os.path.join(diretorio_saida, f"teste_parametros_{nome_base}_{timestamp}.xlsx")
    arquivo_saida_mapa = os.path.join(diretorio_saida, f"mapa_parametros_{nome_base}_{timestamp}.png")
    
    # Executar teste
    testar_combinacoes(arquivo_selecionado, arquivo_saida_excel, arquivo_saida_mapa) 