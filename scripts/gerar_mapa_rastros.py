"""
Script para gerar mapas PNG com rastros das colhedoras sobre imagem de satélite.
Lê as coordenadas dos arquivos Excel gerados pelo script principal e cria mapas coloridos.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import ListedColormap
import contextily as ctx
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString, MultiPoint
from shapely.ops import unary_union
import os
import glob
from pathlib import Path
import warnings
from math import radians, cos, sin, asin, sqrt
from scipy import interpolate
import random
import colorsys
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURAÇÕES DO GERADOR DE MAPAS
# ============================================================================
CONFIGURACOES = {
    # Algoritmo de conexão - voltar ao sequencial mais simples
    'ALGORITMO_CONEXAO': 'sequencial',    # 'clustering' (mais inteligente) ou 'sequencial' (simples)
    'DISTANCIA_MAXIMA_CLUSTER': 120,      # Distância máxima para formar clusters (metros)
    'TAMANHO_MINIMO_TRAJETO': 3,          # Mínimo de pontos para formar um trajeto válido (menor)
    
    # Filtros de qualidade dos dados GPS - mais restritivos
    'DISTANCIA_MAXIMA_LIGACAO': 175,      # Voltar a distância menor para evitar linhas atravessadas
    'FILTRO_OUTLIERS_IQR': 10,           # Voltar ao padrão
    'USAR_FILTRO_DIRECAO': False,         # Manter desabilitado
    'MUDANCA_DIRECAO_MAXIMA': 60,        # Mais restritivo
    'PONTOS_MINIMOS_CALCULO_DIRECAO': 4,  # Manter
    
    # Suavização das linhas - MUITO reduzida
    'SUAVIZAR_LINHAS': True,              # Manter habilitado
    'FATOR_SUAVIZACAO': 0.0,              # Muito menos suave (era 5)
    'TIPO_SUAVIZACAO': 'linear',          # Mudar para linear (mais realista)
    'SIGMA_GAUSSIANO': 0.0,               # Reduzir drasticamente (era 2.0)
    
    # Aparência das linhas e pontos
    'ESPESSURA_LINHA': 1,                 # Reduzir espessura
    'TAMANHO_PONTOS_GPS': 2,              # Pontos menores
    'TRANSPARENCIA_LINHA': 1.0,           # Mais transparente
    'TRANSPARENCIA_PONTOS': 0.3,          # Mais transparente
    
    # Configurações do mapa de fundo
    'PROVEDOR_MAPA': 'Esri_WorldImagery',     # Manter Esri que está funcionando
    'MARGEM_MAPA_PERCENT': 8,             # Margem maior (era 3)
    'TRANSPARENCIA_SATELITE': 1.0,        # Transparência da imagem de satélite
    
    # Configurações da legenda
    'TAMANHO_FONTE_LEGENDA': 10,          # Tamanho da fonte da legenda
    'MOSTRAR_LEGENDA': True,              # True/False para mostrar/ocultar legenda
}
# ============================================================================

def gerar_cores_aleatorias_unicas(num_cores):
    """
    Gera cores aleatórias únicas e bem distintas para cada frota.
    
    Args:
        num_cores (int): Número de cores a gerar
        
    Returns:
        list: Lista de cores em formato hexadecimal
    """
    cores = []
    
    # Se precisar de poucas cores, usar cores predefinidas bem contrastantes
    cores_predefinidas = [
        '#00FF00',  # Verde
        '#0000FF',  # Azul
        '#FFFF00',  # Amarelo
        '#FF00FF',  # Magenta
        '#00FFFF',  # Ciano
        '#FFA500',  # Laranja
        '#800080',  # Roxo
        '#FFC0CB',  # Rosa
        '#808080',  # Cinza
        '#000000',  # Preto
    ]
    
    if num_cores <= len(cores_predefinidas):
        return cores_predefinidas[:num_cores]
    
    # Para muitas cores, gerar usando HSV para garantir boa distribuição
    for i in range(num_cores):
        # Distribuir matizes uniformemente
        hue = i / num_cores
        
        # Variar saturação e valor para mais contraste
        saturation = 0.7 + (i % 3) * 0.1  # 0.7, 0.8, 0.9
        value = 0.8 + (i % 2) * 0.2       # 0.8, 1.0
        
        # Converter HSV para RGB
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        
        # Converter para hexadecimal
        hex_color = '#%02x%02x%02x' % (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        cores.append(hex_color)
    
    # Embaralhar para melhor distribuição visual
    random.shuffle(cores)
    return cores

def ler_coordenadas_excel(caminho_excel):
    """
    Lê as coordenadas da planilha 'Coordenadas' do arquivo Excel.
    
    Args:
        caminho_excel (str): Caminho para o arquivo Excel
        
    Returns:
        DataFrame: DataFrame com as coordenadas ou None se não encontrar
    """
    try:
        # Tentar ler a planilha Coordenadas
        df = pd.read_excel(caminho_excel, sheet_name='Coordenadas')
        
        # Verificar se as colunas necessárias existem
        colunas_necessarias = ['Equipamento', 'Latitude', 'Longitude', 'Hora']
        for col in colunas_necessarias:
            if col not in df.columns:
                print(f"Coluna '{col}' não encontrada na planilha")
                return None
        
        # Remover registros com coordenadas inválidas
        df = df.dropna(subset=['Latitude', 'Longitude'])
        
        if len(df) == 0:
            print("Nenhuma coordenada válida encontrada")
            return None
            
        print(f"Carregadas {len(df)} coordenadas de {df['Equipamento'].nunique()} equipamentos")
        return df
        
    except Exception as e:
        print(f"Erro ao ler arquivo Excel: {e}")
        return None

def criar_poligonos_frota(df_frota, buffer_metros=10):
    """
    Cria polígonos das áreas percorridas por uma frota.
    
    Args:
        df_frota (DataFrame): DataFrame com coordenadas de uma frota
        buffer_metros (float): Buffer em metros para criar as áreas
        
    Returns:
        Polygon: Polígono da área percorrida ou None
    """
    try:
        # Criar pontos geográficos
        pontos = [Point(lon, lat) for lon, lat in zip(df_frota['Longitude'], df_frota['Latitude'])]
        
        if len(pontos) < 3:
            # Se menos de 3 pontos, criar buffer ao redor dos pontos
            multi_point = MultiPoint(pontos)
            return multi_point.buffer(buffer_metros / 111320)  # Conversão aproximada metros para graus
        
        # Criar hull convexo dos pontos
        hull_convexo = MultiPoint(pontos).convex_hull
        
        # Aplicar buffer para criar área
        poligono_area = hull_convexo.buffer(buffer_metros / 111320)
        
        return poligono_area
        
    except Exception as e:
        print(f"Erro ao criar polígono: {e}")
        return None

def filtrar_outliers_gps(df_coords):
    """
    Remove pontos GPS que parecem ser erros (muito distantes dos demais).
    
    Args:
        df_coords (DataFrame): DataFrame com coordenadas
        
    Returns:
        DataFrame: DataFrame filtrado sem outliers
    """
    try:
        # Calcular quartis para latitude e longitude
        lat_q1 = df_coords['Latitude'].quantile(0.25)
        lat_q3 = df_coords['Latitude'].quantile(0.75)
        lon_q1 = df_coords['Longitude'].quantile(0.25)
        lon_q3 = df_coords['Longitude'].quantile(0.75)
        
        # Calcular IQR (Interquartile Range)
        lat_iqr = lat_q3 - lat_q1
        lon_iqr = lon_q3 - lon_q1
        
        # Definir limites para outliers (1.5 * IQR)
        lat_lower = lat_q1 - CONFIGURACOES['FILTRO_OUTLIERS_IQR'] * lat_iqr
        lat_upper = lat_q3 + CONFIGURACOES['FILTRO_OUTLIERS_IQR'] * lat_iqr
        lon_lower = lon_q1 - CONFIGURACOES['FILTRO_OUTLIERS_IQR'] * lon_iqr
        lon_upper = lon_q3 + CONFIGURACOES['FILTRO_OUTLIERS_IQR'] * lon_iqr
        
        # Filtrar outliers
        df_filtrado = df_coords[
            (df_coords['Latitude'] >= lat_lower) & 
            (df_coords['Latitude'] <= lat_upper) &
            (df_coords['Longitude'] >= lon_lower) & 
            (df_coords['Longitude'] <= lon_upper)
        ]
        
        pontos_removidos = len(df_coords) - len(df_filtrado)
        if pontos_removidos > 0:
            print(f"  → Removidos {pontos_removidos} pontos GPS outliers")
        
        return df_filtrado
        
    except Exception as e:
        print(f"Erro ao filtrar outliers: {e}")
        return df_coords

def determinar_orientacao_mapa(df_coords):
    """
    Determina orientação A4: retrato (210x297mm) ou paisagem (297x210mm).
    
    Args:
        df_coords (DataFrame): DataFrame com coordenadas
        
    Returns:
        str: 'horizontal' ou 'vertical'
    """
    # Calcular extensão das coordenadas
    lat_range = df_coords['Latitude'].max() - df_coords['Latitude'].min()
    lon_range = df_coords['Longitude'].max() - df_coords['Longitude'].min()
    
    # Se a extensão em longitude for maior, usar formato horizontal (A4 paisagem)
    # Se a extensão em latitude for maior, usar formato vertical (A4 retrato)
    if lon_range > lat_range:
        return 'horizontal'  # A4 paisagem
    else:
        return 'vertical'  # A4 retrato

def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Calcula a distância entre duas coordenadas usando a fórmula de Haversine.
    
    Args:
        lat1, lon1: Latitude e longitude do primeiro ponto
        lat2, lon2: Latitude e longitude do segundo ponto
    
    Returns:
        float: Distância em metros
    """
    # Converter graus para radianos
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Fórmula de Haversine
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Raio da Terra em metros
    r = 6371000
    
    return c * r

def calcular_azimute(lat1, lon1, lat2, lon2):
    """
    Calcula o azimute/direção entre dois pontos GPS.
    
    Args:
        lat1, lon1: Latitude e longitude do primeiro ponto
        lat2, lon2: Latitude e longitude do segundo ponto
    
    Returns:
        float: Azimute em graus (0-360)
    """
    # Converter para radianos
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Calcular diferença de longitude
    dlon = lon2 - lon1
    
    # Calcular azimute
    y = sin(dlon) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    
    # Converter para graus e normalizar para 0-360
    azimute = np.degrees(np.arctan2(y, x))
    return (azimute + 360) % 360

def calcular_diferenca_angular(angulo1, angulo2):
    """
    Calcula a menor diferença angular entre dois ângulos.
    
    Args:
        angulo1, angulo2: Ângulos em graus
    
    Returns:
        float: Diferença angular em graus (0-180)
    """
    diff = abs(angulo1 - angulo2)
    return min(diff, 360 - diff)

def conectar_trajetos_inteligente(df_frota):
    """
    Conecta pontos GPS usando algoritmo inteligente baseado em clustering temporal-espacial.
    
    Args:
        df_frota (DataFrame): DataFrame com coordenadas de uma frota
        
    Returns:
        list: Lista de trajetos conectados
    """
    try:
        from sklearn.cluster import DBSCAN
        from scipy.spatial.distance import pdist, squareform
        from scipy.ndimage import gaussian_filter1d
        
        if len(df_frota) < CONFIGURACOES['TAMANHO_MINIMO_TRAJETO']:
            return [df_frota] if len(df_frota) >= 2 else []
        
        # Ordenar por tempo
        if 'Hora' in df_frota.columns:
            df_frota = df_frota.sort_values('Hora').reset_index(drop=True)
        
        # Converter coordenadas para UTM aproximado (metros)
        coords_utm = []
        base_lat = df_frota['Latitude'].mean()
        base_lon = df_frota['Longitude'].mean()
        
        for _, row in df_frota.iterrows():
            # Conversão aproximada lat/lon para metros
            x = (row['Longitude'] - base_lon) * 111320 * np.cos(np.radians(base_lat))
            y = (row['Latitude'] - base_lat) * 111320
            coords_utm.append([x, y])
        
        coords_utm = np.array(coords_utm)
        
        # Usar DBSCAN para identificar clusters de movimento
        eps_metros = CONFIGURACOES['DISTANCIA_MAXIMA_CLUSTER']  # metros
        dbscan = DBSCAN(eps=eps_metros, min_samples=3)
        clusters = dbscan.fit_predict(coords_utm)
        
        # Agrupar pontos por cluster e tempo
        trajetos = []
        for cluster_id in np.unique(clusters):
            if cluster_id == -1:  # Pontos de ruído
                continue
                
            indices_cluster = np.where(clusters == cluster_id)[0]
            df_cluster = df_frota.iloc[indices_cluster].copy()
            
            if len(df_cluster) >= CONFIGURACOES['TAMANHO_MINIMO_TRAJETO']:
                # Ordenar por tempo novamente dentro do cluster
                if 'Hora' in df_cluster.columns:
                    df_cluster = df_cluster.sort_values('Hora')
                trajetos.append(df_cluster)
        
        # Se não conseguiu formar clusters, usar abordagem sequencial melhorada
        if not trajetos:
            return criar_trajeto_sequencial_melhorado(df_frota)
        
        print(f"  → {len(trajetos)} trajetos inteligentes identificados")
        return trajetos
        
    except ImportError:
        print("  → sklearn não disponível, usando método sequencial")
        return criar_trajeto_sequencial_melhorado(df_frota)
    except Exception as e:
        print(f"  → Erro no clustering: {e}, usando método sequencial")
        return criar_trajeto_sequencial_melhorado(df_frota)

def criar_trajeto_sequencial_melhorado(df_frota):
    """
    Cria trajetos conectando pontos sequenciais com lógica melhorada.
    """
    try:
        if len(df_frota) < 2:
            return []
        
        # Ordenar por hora
        if 'Hora' in df_frota.columns:
            df_frota = df_frota.sort_values('Hora')
        
        trajetos = []
        trajeto_atual = [df_frota.iloc[0]]
        
        for i in range(1, len(df_frota)):
            ponto_anterior = df_frota.iloc[i-1]
            ponto_atual = df_frota.iloc[i]
            
            # Calcular distância
            distancia = calcular_distancia_haversine(
                ponto_anterior['Latitude'], ponto_anterior['Longitude'],
                ponto_atual['Latitude'], ponto_atual['Longitude']
            )
            
            # Conectar se distância for razoável
            if distancia <= CONFIGURACOES['DISTANCIA_MAXIMA_LIGACAO']:
                trajeto_atual.append(ponto_atual)
            else:
                # Salvar trajeto atual se tiver tamanho mínimo
                if len(trajeto_atual) >= CONFIGURACOES['TAMANHO_MINIMO_TRAJETO']:
                    trajetos.append(pd.DataFrame(trajeto_atual))
                trajeto_atual = [ponto_atual]
        
        # Adicionar último trajeto
        if len(trajeto_atual) >= CONFIGURACOES['TAMANHO_MINIMO_TRAJETO']:
            trajetos.append(pd.DataFrame(trajeto_atual))
        
        print(f"  → {len(trajetos)} trajetos sequenciais criados")
        return trajetos
        
    except Exception as e:
        print(f"Erro no trajeto sequencial: {e}")
        return [df_frota] if len(df_frota) >= 2 else []

def suavizar_linha_avancado(df_segmento):
    """
    Suavização simples e realista para manter a forma natural dos trajetos.
    """
    try:
        if not CONFIGURACOES['SUAVIZAR_LINHAS'] or len(df_segmento) < 3:
            return df_segmento['Longitude'].values, df_segmento['Latitude'].values
        
        lons_orig = df_segmento['Longitude'].values
        lats_orig = df_segmento['Latitude'].values
        
        # Se muito poucos pontos, retornar original
        if len(df_segmento) < 4:
            return lons_orig, lats_orig
        
        # Suavização muito sutil com filtro gaussiano
        try:
            from scipy.ndimage import gaussian_filter1d
            sigma = CONFIGURACOES.get('SIGMA_GAUSSIANO', 0.5)
            
            # Aplicar filtro gaussiano muito suave
            lons_suaves = gaussian_filter1d(lons_orig, sigma=sigma, mode='nearest')
            lats_suaves = gaussian_filter1d(lats_orig, sigma=sigma, mode='nearest')
            
            # Se fator de suavização for maior que 1, interpolar alguns pontos extras
            if CONFIGURACOES['FATOR_SUAVIZACAO'] > 1:
                fator = min(CONFIGURACOES['FATOR_SUAVIZACAO'], 2)  # Máximo 2x
                num_pontos = int(len(df_segmento) * fator)
                
                t_orig = np.arange(len(lons_suaves))
                t_novo = np.linspace(0, len(lons_suaves)-1, num_pontos)
                
                # Usar interpolação linear simples
                interp_lon = interpolate.interp1d(t_orig, lons_suaves, kind='linear')
                interp_lat = interpolate.interp1d(t_orig, lats_suaves, kind='linear')
                
                return interp_lon(t_novo), interp_lat(t_novo)
            else:
                return lons_suaves, lats_suaves
                
        except Exception:
            # Se der erro, usar interpolação linear simples
            if CONFIGURACOES['FATOR_SUAVIZACAO'] > 1:
                t_orig = np.arange(len(lons_orig))
                t_novo = np.linspace(0, len(lons_orig)-1, int(len(df_segmento) * 1.5))
                
                interp_lon = interpolate.interp1d(t_orig, lons_orig, kind='linear')
                interp_lat = interpolate.interp1d(t_orig, lats_orig, kind='linear')
                
                return interp_lon(t_novo), interp_lat(t_novo)
            else:
                return lons_orig, lats_orig
        
    except Exception as e:
        return df_segmento['Longitude'].values, df_segmento['Latitude'].values

def gerar_mapa_rastros(df_coords, caminho_saida, nome_arquivo):
    """
    Gera o mapa com rastros coloridos das frotas usando algoritmo melhorado.
    """
    try:
        # Filtrar outliers GPS (mais permissivo)
        df_coords = filtrar_outliers_gps(df_coords)
        
        # Obter equipamentos únicos
        equipamentos = df_coords['Equipamento'].unique()
        print(f"Gerando mapa para {len(equipamentos)} equipamentos: {list(equipamentos)}")
        
        # SEMPRE usar formato vertical (A4 retrato) independente da orientação dos dados
        fig, ax = plt.subplots(figsize=(8.27, 11.69))  # A4 retrato em polegadas
        
        # Definir limites do mapa
        min_lon = df_coords['Longitude'].min()
        max_lon = df_coords['Longitude'].max()
        min_lat = df_coords['Latitude'].min()
        max_lat = df_coords['Latitude'].max()
        
        # Adicionar margem maior para melhor aspecto visual
        margem_lon = (max_lon - min_lon) * CONFIGURACOES['MARGEM_MAPA_PERCENT'] / 100
        margem_lat = (max_lat - min_lat) * CONFIGURACOES['MARGEM_MAPA_PERCENT'] / 100
        
        ax.set_xlim(min_lon - margem_lon, max_lon + margem_lon)
        ax.set_ylim(min_lat - margem_lat, max_lat + margem_lat)
        
        # Criar GeoDataFrame para facilitar o plot
        gdf_pontos = gpd.GeoDataFrame(
            df_coords,
            geometry=gpd.points_from_xy(df_coords['Longitude'], df_coords['Latitude']),
            crs='EPSG:4326'
        )
        
        # Adicionar imagem de satélite de fundo
        try:
            provedor = obter_provedor_mapa(CONFIGURACOES['PROVEDOR_MAPA'])
            print(f"  → Carregando mapa de fundo: {CONFIGURACOES['PROVEDOR_MAPA']}")
            ctx.add_basemap(ax, crs=gdf_pontos.crs, source=provedor, 
                           alpha=CONFIGURACOES['TRANSPARENCIA_SATELITE'], attribution=False)
            print(f"  → Mapa de fundo carregado com sucesso")
        except Exception as e:
            print(f"  → Erro ao carregar mapa de fundo: {e}")
            ax.set_facecolor('#0d1b2a')
            fig.patch.set_facecolor('#0d1b2a')
        
        # Gerar cores aleatórias únicas para cada equipamento
        cores_equipamentos = gerar_cores_aleatorias_unicas(len(equipamentos))
        
        # Preparar lista para legenda
        elementos_legenda = []
        
        # Processar cada equipamento
        for i, equipamento in enumerate(equipamentos):
            df_equip = df_coords[df_coords['Equipamento'] == equipamento].copy()
            cor = cores_equipamentos[i]
            
            # Usar algoritmo inteligente de conexão
            if CONFIGURACOES['ALGORITMO_CONEXAO'] == 'clustering':
                trajetos_validos = conectar_trajetos_inteligente(df_equip)
            else:
                trajetos_validos = criar_trajeto_sequencial_melhorado(df_equip)
            
            # Plotar cada trajeto
            for trajeto in trajetos_validos:
                if len(trajeto) >= 2:
                    # Suavização avançada
                    lons_suaves, lats_suaves = suavizar_linha_avancado(trajeto)
                    
                    # Plotar linha suavizada
                    ax.plot(lons_suaves, lats_suaves, 
                           color=cor, linewidth=CONFIGURACOES['ESPESSURA_LINHA'], 
                           alpha=CONFIGURACOES['TRANSPARENCIA_LINHA'], 
                           solid_capstyle='round', solid_joinstyle='round',
                           zorder=1)
            
            # Plotar pontos GPS discretos
            if CONFIGURACOES['TAMANHO_PONTOS_GPS'] > 0:
                ax.scatter(df_equip['Longitude'], df_equip['Latitude'], 
                          color='white', s=CONFIGURACOES['TAMANHO_PONTOS_GPS'], 
                          alpha=CONFIGURACOES['TRANSPARENCIA_PONTOS'], 
                          edgecolors=cor, linewidth=0.5, zorder=2)
            
            # Adicionar à legenda usando Line2D para criar bolinha
            from matplotlib.lines import Line2D
            elementos_legenda.append(Line2D([0], [0], marker='o', color='w', 
                                          markerfacecolor=cor, markersize=8, 
                                          label=f'{equipamento}'))
        
        # Adicionar legenda com bolinhas
        if CONFIGURACOES['MOSTRAR_LEGENDA'] and elementos_legenda:
            legend = ax.legend(handles=elementos_legenda, loc='upper right', 
                             bbox_to_anchor=(0.98, 0.98), fontsize=CONFIGURACOES['TAMANHO_FONTE_LEGENDA'],
                             frameon=True, fancybox=True, shadow=True,
                             facecolor='white', edgecolor='black', framealpha=0.9)
        
        # Remover elementos desnecessários
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel('')
        ax.set_ylabel('')
        
        # Remover bordas
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Salvar o mapa
        caminho_completo = os.path.join(caminho_saida, nome_arquivo.replace('.xlsx', '_mapa_rastros.png'))
        plt.savefig(caminho_completo, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none', pad_inches=0)
        plt.close()
        
        print(f"✓ Mapa salvo: {caminho_completo}")
        return True
        
    except Exception as e:
        print(f"Erro ao gerar mapa: {e}")
        plt.close()
        return False

def processar_todos_arquivos_excel():
    """
    Processa todos os arquivos Excel na pasta output e gera mapas.
    """
    print("Iniciando geração de mapas de rastros...")
    
    # Obter diretório do script
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    diretorio_raiz = os.path.dirname(diretorio_script)
    
    # Diretórios
    diretorio_entrada = os.path.join(diretorio_raiz, "output")
    diretorio_saida = os.path.join(diretorio_raiz, "output", "mapas")
    
    # Criar diretório de saída se não existir
    if not os.path.exists(diretorio_saida):
        os.makedirs(diretorio_saida)
        print(f"Criado diretório: {diretorio_saida}")
    
    # Encontrar arquivos Excel com rastros
    arquivos_excel = glob.glob(os.path.join(diretorio_entrada, "*-rastros.xlsx"))
    
    if not arquivos_excel:
        print("Nenhum arquivo Excel com rastros encontrado na pasta output!")
        return
    
    print(f"Encontrados {len(arquivos_excel)} arquivos para processar")
    
    mapas_gerados = 0
    
    for arquivo_excel in arquivos_excel:
        print(f"\nProcessando: {os.path.basename(arquivo_excel)}")
        
        # Ler coordenadas
        df_coords = ler_coordenadas_excel(arquivo_excel)
        
        if df_coords is None or len(df_coords) == 0:
            print(f"Pulando {os.path.basename(arquivo_excel)} - sem coordenadas válidas")
            continue
        
        # Nome do arquivo de saída (remover -rastros.xlsx)
        nome_base = os.path.splitext(os.path.basename(arquivo_excel))[0]
        nome_base = nome_base.replace('-rastros', '')
        
        # Gerar mapa
        sucesso = gerar_mapa_rastros(df_coords, diretorio_saida, nome_base)
        
        if sucesso:
            mapas_gerados += 1
    
    print(f"\nProcessamento concluído!")
    print(f"Mapas gerados: {mapas_gerados}")
    print(f"Mapas salvos em: {diretorio_saida}")

def obter_provedor_mapa(nome_provedor):
    """
    Retorna o provedor de mapa baseado no nome configurado.
    
    Args:
        nome_provedor (str): Nome do provedor configurado
        
    Returns:
        Provider: Provedor do contextily ou fallback para Esri
    """
    try:
        if nome_provedor == 'Esri_WorldImagery':
            return ctx.providers.Esri.WorldImagery
        elif nome_provedor == 'Google_Satellite':
            # Usar string URL diretamente - contextily aceita URLs customizadas
            return 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
        elif nome_provedor == 'Google_Hybrid':
            return 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'
        elif nome_provedor == 'OSM':
            return ctx.providers.OpenStreetMap.Mapnik
        elif nome_provedor == 'CartoDB_Positron':
            return ctx.providers.CartoDB.Positron
        elif nome_provedor == 'CartoDB_DarkMatter':
            return ctx.providers.CartoDB.DarkMatter
        else:
            # Fallback seguro para Esri
            return ctx.providers.Esri.WorldImagery
    except:
        # Se der erro, usar Esri como fallback
        return ctx.providers.Esri.WorldImagery

if __name__ == "__main__":
    print("="*80)
    print("GERADOR DE MAPAS DE RASTROS DAS COLHEDORAS")
    print("="*80)
    print("Este script gera mapas PNG com rastros coloridos das colhedoras")
    print("sobre imagem de satélite, baseado nas coordenadas dos arquivos Excel.")
    print()
    print("Recursos:")
    print("- Fundo de satélite")
    print("- Rastros coloridos por frota")
    print("- Pontos GPS em branco")
    print("- Legenda automática")
    print("- Formato automático (16:9 ou 9:16)")
    print("- Alta qualidade (300 DPI)")
    print("="*80)
    
    try:
        processar_todos_arquivos_excel()
    except Exception as e:
        print(f"\nErro durante processamento: {str(e)}")
        import traceback
        traceback.print_exc() 