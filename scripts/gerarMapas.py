# ====================================================================================
# IMPORTAÇÕES
# ====================================================================================

import os
import pandas as pd
import folium
import glob
import datetime
import math
from sklearn.cluster import DBSCAN  # usado em funções mais abaixo (mantido)
import numpy as np
import colorsys

# ====================================================================================
# BLOCO DE CUSTOMIZAÇÕES (edite conforme necessidade)
# ====================================================================================

CONFIG = {
    # Zoom inicial do mapa
    'zoom_start': 16,
    # Tile base (folium aceita 'OpenStreetMap', 'Stamen Terrain', etc.)
    'base_tile': 'OpenStreetMap',
    # Adicionar camada Satélite (True/False)
    'satellite_layer': True,
    # Espessura da linha
    'line_weight': 2,
    # Opacidade da linha
    'line_opacity': 0.75,
    # Lista de cores para equipamentos (será usada ciclicamente)
    'cores_equipamentos': [
        'red', 'blue', 'green', 'purple', 'orange',
        'darkred', 'darkblue', 'darkgreen', 'pink', 'gray'
    ],
    # Mostrar marcadores de início/fim (True/False)
    'marcadores_inicio_fim': True,
    
    # Controle de saída
    'saida': {
        'html': False,                     # Gerar arquivo HTML
        'png': True,                      # Gerar arquivo PNG
        'limpar_pasta': True,            # Limpar pasta de mapas antes de gerar novos
        'prefixo_arquivo': '',            # Prefixo opcional para nomes de arquivos
        'formato_nome': '{nome}_{tipo}_{timestamp}'  # Formato do nome do arquivo
    },
    
    # Configurações da legenda
    'legenda': {
        'mostrar': True,                   # Exibir legenda
        'posicao': 'bottom-right',         # 'top-left', 'top-right', 'bottom-left', 'bottom-right'
        # Estilo do container branco
        'largura': 150,                    # Largura da legenda (em pixels)
        'padding': '12px 16px',            # Padding interno (top/bottom left/right)
        'borda': '1px solid #ddd',         # Estilo da borda
        'fundo': 'white',                  # Cor de fundo (branco sólido)
        'raio_borda': 8,                   # Arredondamento dos cantos (em pixels)
        'sombra': '0 0 10px rgba(0,0,0,0.15)', # Sombra para destacar
        # Estilo dos itens
        'tamanho_circulo': 26,             # Diâmetro dos círculos coloridos
        'tamanho_fonte': 30,               # Tamanho da fonte
        'espaco_itens': 12,                # Espaço vertical entre itens
        'espaco_horizontal': 16,           # Espaço entre círculo e texto
        'negrito': True                    # Texto em negrito
    },
}

# ====================================================================================
# FIM DAS CUSTOMIZAÇÕES
# ====================================================================================

def calcular_distancia(lat1, lng1, lat2, lng2):
    """Calcula distância entre dois pontos em metros usando fórmula de Haversine"""
    R = 6371000  # Raio da Terra em metros
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lng/2) * math.sin(delta_lng/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def buscar_arquivos_csv():
    """Busca arquivos CSV com coordenadas na pasta output"""
    caminho_csv = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', '*.csv')
    arquivos = glob.glob(caminho_csv)
    return arquivos

def ler_coordenadas(arquivo):
    """Lê o arquivo CSV e retorna DataFrame com coordenadas"""
    try:
        print(f"Lendo arquivo: {os.path.basename(arquivo)}")
        df = pd.read_csv(arquivo, sep=';')
        
        print(f"Colunas: {list(df.columns)}")
        print(f"Total de linhas: {len(df)}")
        
        # Verifica colunas necessárias
        if 'Latitude' not in df.columns or 'Longitude' not in df.columns:
            print("Colunas Latitude/Longitude não encontradas")
            return None
        
        # Limpa e converte coordenadas
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        df = df.dropna(subset=['Latitude', 'Longitude'])
        
        print(f"Coordenadas válidas: {len(df)}")
        print(f"Primeira coordenada: Lat={df.iloc[0]['Latitude']}, Lng={df.iloc[0]['Longitude']}")
        
        return df
    except Exception as e:
        print(f"Erro: {e}")
        return None

def detectar_areas_trabalho(dados_equip, eps_metros=100):
    """
    Detecta áreas de trabalho usando clustering DBSCAN
    eps_metros: raio em metros para considerar pontos do mesmo cluster
    """
    if len(dados_equip) < 10:
        return None
    
    # Converte coordenadas para array numpy
    coords = dados_equip[['Latitude', 'Longitude']].values
    
    # Converte eps de metros para graus (aproximação)
    # 1 grau ≈ 111km, então eps_graus = eps_metros / 111000
    eps_graus = eps_metros / 111000
    
    # Aplica DBSCAN
    clustering = DBSCAN(eps=eps_graus, min_samples=5).fit(coords)
    
    # Adiciona labels dos clusters ao dataframe
    dados_equip_copy = dados_equip.copy()
    dados_equip_copy['cluster'] = clustering.labels_
    
    # Filtra apenas pontos que pertencem a clusters (remove ruído)
    dados_clustered = dados_equip_copy[dados_equip_copy['cluster'] != -1]
    
    print(f"  Detectados {len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)} clusters")
    print(f"  Pontos em clusters: {len(dados_clustered)} de {len(dados_equip)}")
    
    return dados_clustered

def calcular_trajeto_otimizado(dados_clustered):
    """
    Calcula trajeto otimizado conectando clusters de forma lógica
    """
    if dados_clustered is None or len(dados_clustered) == 0:
        return []
    
    # Ordena por hora se disponível
    if 'Hora' in dados_clustered.columns:
        try:
            dados_clustered = dados_clustered.sort_values('Hora').reset_index(drop=True)
            print(f"  Dados ordenados por hora")
        except:
            print(f"  Mantendo ordem original")
    
    # Agrupa por cluster e calcula centro de cada cluster
    clusters_info = []
    for cluster_id in sorted(dados_clustered['cluster'].unique()):
        cluster_data = dados_clustered[dados_clustered['cluster'] == cluster_id]
        
        # Centro do cluster (média das coordenadas)
        centro_lat = cluster_data['Latitude'].mean()
        centro_lng = cluster_data['Longitude'].mean()
        
        # Primeira e última hora do cluster
        if 'Hora' in cluster_data.columns:
            primeira_hora = cluster_data['Hora'].min()
            ultima_hora = cluster_data['Hora'].max()
        else:
            primeira_hora = cluster_data.index.min()
            ultima_hora = cluster_data.index.max()
        
        clusters_info.append({
            'id': cluster_id,
            'centro': [centro_lat, centro_lng],
            'primeira_hora': primeira_hora,
            'ultima_hora': ultima_hora,
            'pontos': len(cluster_data)
        })
    
    # Ordena clusters por primeira hora de atividade
    clusters_info.sort(key=lambda x: x['primeira_hora'])
    
    print(f"  Clusters ordenados por tempo:")
    for cluster in clusters_info:
        print(f"    Cluster {cluster['id']}: {cluster['pontos']} pontos, centro: {cluster['centro']}")
    
    # Conecta centros dos clusters em ordem temporal
    trajeto_otimizado = [cluster['centro'] for cluster in clusters_info]
    
    return trajeto_otimizado

def criar_trajeto_detalhado_por_cluster(dados_clustered):
    """
    Cria trajeto detalhado passando por todos os pontos, mas organizados por cluster
    """
    if dados_clustered is None or len(dados_clustered) == 0:
        return []
    
    trajetos = []
    
    # Processa cada cluster separadamente
    for cluster_id in sorted(dados_clustered['cluster'].unique()):
        cluster_data = dados_clustered[dados_clustered['cluster'] == cluster_id].copy()
        
        # Ordena pontos do cluster por hora
        if 'Hora' in cluster_data.columns:
            try:
                cluster_data = cluster_data.sort_values('Hora')
            except:
                pass
        
        # Converte para lista de coordenadas
        coords_cluster = []
        for _, row in cluster_data.iterrows():
            coords_cluster.append([float(row['Latitude']), float(row['Longitude'])])
        
        if len(coords_cluster) >= 2:
            trajetos.append(coords_cluster)
    
    return trajetos

def criar_mapa_inteligente_agricola(dados):
    """Cria mapa otimizado para equipamentos agrícolas"""
    if dados.empty:
        print("Sem dados para criar mapa")
        return None
    
    # Centro do mapa
    lat_centro = dados['Latitude'].mean()
    lng_centro = dados['Longitude'].mean()
    
    print(f"Centro: {lat_centro}, {lng_centro}")
    
    # Cria mapa básico
    mapa = folium.Map(
        location=[lat_centro, lng_centro],
        zoom_start=16,
        tiles='OpenStreetMap'
    )
    
    # Processa por equipamento
    equipamentos = dados['Equipamento'].unique() if 'Equipamento' in dados.columns else ['Único']
    cores = ['red', 'blue', 'green', 'purple', 'orange']
    
    print(f"Equipamentos: {equipamentos}")
    
    for i, equipamento in enumerate(equipamentos):
        cor = cores[i % len(cores)]
        
        if 'Equipamento' in dados.columns:
            dados_equip = dados[dados['Equipamento'] == equipamento].copy()
        else:
            dados_equip = dados.copy()
        
        print(f"\nProcessando equipamento {equipamento}: {len(dados_equip)} pontos")
        
        # Detecta áreas de trabalho
        dados_clustered = detectar_areas_trabalho(dados_equip, eps_metros=80)
        
        if dados_clustered is not None and len(dados_clustered) > 0:
            # Opção 1: Trajeto otimizado (conecta centros dos clusters)
            trajeto_otimizado = calcular_trajeto_otimizado(dados_clustered)
            
            if len(trajeto_otimizado) >= 2:
                folium.PolyLine(
                    locations=trajeto_otimizado,
                    color=cor,
                    weight=4,
                    opacity=0.8,
                    popup=f"Trajeto Otimizado - {equipamento}",
                    dash_array='10,5'
                ).add_to(mapa)
            
            # Opção 2: Trajetos detalhados por cluster
            trajetos_detalhados = criar_trajeto_detalhado_por_cluster(dados_clustered)
            
            for j, trajeto in enumerate(trajetos_detalhados):
                if len(trajeto) >= 2:
                    folium.PolyLine(
                        locations=trajeto,
                        color=cor,
                        weight=2,
                        opacity=0.6,
                        popup=f"Área de Trabalho {j+1} - {equipamento}"
                    ).add_to(mapa)
            
            # Adiciona marcadores para centros dos clusters
            for cluster_id in dados_clustered['cluster'].unique():
                cluster_data = dados_clustered[dados_clustered['cluster'] == cluster_id]
                centro_lat = cluster_data['Latitude'].mean()
                centro_lng = cluster_data['Longitude'].mean()
                
                folium.CircleMarker(
                    location=[centro_lat, centro_lng],
                    radius=8,
                    color=cor,
                    fill=True,
                    fill_color=cor,
                    fill_opacity=0.7,
                    popup=f"Área {cluster_id} - {equipamento}<br>{len(cluster_data)} pontos"
                ).add_to(mapa)
        
        # Marcadores início/fim geral
        if len(dados_equip) > 0:
            primeiro = dados_equip.iloc[0]
            ultimo = dados_equip.iloc[-1]
            
            folium.Marker(
                location=[primeiro['Latitude'], primeiro['Longitude']],
                popup=f"INÍCIO - {equipamento}",
                icon=folium.Icon(color=cor, icon='play', prefix='fa')
            ).add_to(mapa)
            
            folium.Marker(
                location=[ultimo['Latitude'], ultimo['Longitude']],
                popup=f"FIM - {equipamento}",
                icon=folium.Icon(color=cor, icon='stop', prefix='fa')
            ).add_to(mapa)
    
    return mapa

def detectar_padrao_fileiras(dados_equip, tolerancia_metros=50):
    """
    Detecta padrão de movimento em fileiras (vai-e-vem)
    Agrupa pontos em fileiras paralelas e conecta de forma lógica
    """
    if len(dados_equip) < 20:
        return None
    
    print(f"  Analisando padrão de fileiras...")
    
    # Ordena por hora
    if 'Hora' in dados_equip.columns:
        try:
            dados_equip = dados_equip.sort_values('Hora').reset_index(drop=True)
        except:
            pass
    
    # Converte coordenadas para arrays numpy
    coords = dados_equip[['Latitude', 'Longitude']].values
    
    # Detecta direção principal do movimento
    # Calcula diferenças entre pontos consecutivos
    diffs = np.diff(coords, axis=0)
    
    # Calcula ângulos de movimento
    angulos = np.arctan2(diffs[:, 1], diffs[:, 0])  # lng, lat
    
    # Agrupa ângulos similares (fileiras paralelas)
    from sklearn.cluster import DBSCAN
    angulos_reshape = angulos.reshape(-1, 1)
    
    # Clustering dos ângulos (direções)
    clustering_angulos = DBSCAN(eps=0.3, min_samples=10).fit(angulos_reshape)
    
    # Encontra direção principal (cluster com mais pontos)
    labels_angulos = clustering_angulos.labels_
    if len(set(labels_angulos)) > 1:
        # Conta pontos por cluster
        unique_labels, counts = np.unique(labels_angulos[labels_angulos != -1], return_counts=True)
        if len(unique_labels) > 0:
            direcao_principal = unique_labels[np.argmax(counts)]
            angulo_principal = np.mean(angulos[labels_angulos == direcao_principal])
            print(f"  Direção principal detectada: {np.degrees(angulo_principal):.1f}°")
        else:
            angulo_principal = np.mean(angulos)
    else:
        angulo_principal = np.mean(angulos)
    
    # Projeta pontos na direção perpendicular (para detectar fileiras)
    # Rotaciona coordenadas para alinhar com direção principal
    cos_ang = np.cos(angulo_principal + np.pi/2)  # perpendicular
    sin_ang = np.sin(angulo_principal + np.pi/2)
    
    # Projeta na direção perpendicular (posição da fileira)
    projecoes = coords[:, 0] * cos_ang + coords[:, 1] * sin_ang
    
    # Converte tolerância de metros para graus (aproximação)
    tolerancia_graus = tolerancia_metros / 111000
    
    # Clustering das projeções (fileiras)
    projecoes_reshape = projecoes.reshape(-1, 1)
    clustering_fileiras = DBSCAN(eps=tolerancia_graus, min_samples=5).fit(projecoes_reshape)
    
    # Adiciona informações de fileira aos dados
    dados_com_fileiras = dados_equip.copy()
    dados_com_fileiras['fileira'] = clustering_fileiras.labels_
    dados_com_fileiras['projecao'] = projecoes
    
    # Remove ruído
    dados_fileiras = dados_com_fileiras[dados_com_fileiras['fileira'] != -1]
    
    num_fileiras = len(set(dados_fileiras['fileira'].unique()))
    print(f"  Detectadas {num_fileiras} fileiras de trabalho")
    print(f"  Pontos em fileiras: {len(dados_fileiras)} de {len(dados_equip)}")
    
    return dados_fileiras, angulo_principal

def criar_trajeto_por_fileiras(dados_fileiras, angulo_principal):
    """
    Cria trajeto conectando fileiras de forma lógica (vai-e-vem)
    """
    if dados_fileiras is None or len(dados_fileiras) == 0:
        return []
    
    trajetos = []
    
    # Ordena fileiras por posição (projeção)
    fileiras_ordenadas = sorted(dados_fileiras['fileira'].unique(), 
                               key=lambda f: dados_fileiras[dados_fileiras['fileira'] == f]['projecao'].mean())
    
    print(f"  Processando {len(fileiras_ordenadas)} fileiras...")
    
    for i, fileira_id in enumerate(fileiras_ordenadas):
        dados_fileira = dados_fileiras[dados_fileiras['fileira'] == fileira_id].copy()
        
        # Ordena pontos da fileira por hora
        if 'Hora' in dados_fileira.columns:
            try:
                dados_fileira = dados_fileira.sort_values('Hora')
            except:
                pass
        
        # Projeta na direção principal para ordenar pontos ao longo da fileira
        cos_ang = np.cos(angulo_principal)
        sin_ang = np.sin(angulo_principal)
        
        projecao_principal = (dados_fileira['Latitude'].values * cos_ang + 
                            dados_fileira['Longitude'].values * sin_ang)
        
        # Para fileiras ímpares, inverte ordem (efeito vai-e-vem)
        if i % 2 == 1:
            indices_ordenados = np.argsort(-projecao_principal)  # ordem inversa
        else:
            indices_ordenados = np.argsort(projecao_principal)   # ordem normal
        
        dados_fileira_ordenados = dados_fileira.iloc[indices_ordenados]
        
        # Converte para coordenadas
        coords_fileira = []
        for _, row in dados_fileira_ordenados.iterrows():
            coords_fileira.append([float(row['Latitude']), float(row['Longitude'])])
        
        if len(coords_fileira) >= 2:
            trajetos.append(coords_fileira)
            print(f"    Fileira {i+1}: {len(coords_fileira)} pontos")
    
    return trajetos

def conectar_fileiras(trajetos):
    """
    Conecta o final de uma fileira com o início da próxima
    """
    if len(trajetos) < 2:
        return trajetos
    
    conexoes = []
    
    for i in range(len(trajetos) - 1):
        # Final da fileira atual
        fim_atual = trajetos[i][-1]
        # Início da próxima fileira
        inicio_proximo = trajetos[i + 1][0]
        
        # Cria conexão
        conexoes.append([fim_atual, inicio_proximo])
    
    return trajetos, conexoes

def criar_mapa_padrao_agricola(dados):
    """Cria mapa seguindo padrões de movimento agrícola (fileiras)"""
    if dados.empty:
        print("Sem dados para criar mapa")
        return None
    
    # Centro do mapa
    lat_centro = dados['Latitude'].mean()
    lng_centro = dados['Longitude'].mean()
    
    print(f"Centro: {lat_centro}, {lng_centro}")
    
    # Cria mapa básico
    mapa = folium.Map(
        location=[lat_centro, lng_centro],
        zoom_start=17,
        tiles='OpenStreetMap'
    )
    
    # Adiciona camadas de mapa
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satélite'
    ).add_to(mapa)
    
    # Processa por equipamento
    equipamentos = dados['Equipamento'].unique() if 'Equipamento' in dados.columns else ['Único']
    cores = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen']
    
    print(f"Equipamentos: {equipamentos}")
    
    for i, equipamento in enumerate(equipamentos):
        cor = cores[i % len(cores)]
        
        if 'Equipamento' in dados.columns:
            dados_equip = dados[dados['Equipamento'] == equipamento].copy()
        else:
            dados_equip = dados.copy()
        
        print(f"\nProcessando equipamento {equipamento}: {len(dados_equip)} pontos")
        
        # Detecta padrão de fileiras
        resultado_fileiras = detectar_padrao_fileiras(dados_equip, tolerancia_metros=30)
        
        if resultado_fileiras is not None:
            dados_fileiras, angulo_principal = resultado_fileiras
            
            # Cria trajetos por fileiras
            trajetos_fileiras = criar_trajeto_por_fileiras(dados_fileiras, angulo_principal)
            
            # Conecta fileiras
            if len(trajetos_fileiras) > 1:
                trajetos_fileiras, conexoes = conectar_fileiras(trajetos_fileiras)
                
                # Adiciona conexões entre fileiras (linhas tracejadas)
                for conexao in conexoes:
                    folium.PolyLine(
                        locations=conexao,
                        color=cor,
                        weight=2,
                        opacity=0.5,
                        dash_array='5,10',
                        popup=f"Conexão - {equipamento}"
                    ).add_to(mapa)
            
            # Adiciona trajetos das fileiras
            for j, trajeto in enumerate(trajetos_fileiras):
                if len(trajeto) >= 2:
                    folium.PolyLine(
                        locations=trajeto,
                        color=cor,
                        weight=3,
                        opacity=0.8,
                        popup=f"Fileira {j+1} - {equipamento}"
                    ).add_to(mapa)
            
            # Marcadores para início e fim de cada fileira
            for j, trajeto in enumerate(trajetos_fileiras):
                if len(trajeto) >= 2:
                    # Início da fileira
                    folium.CircleMarker(
                        location=trajeto[0],
                        radius=5,
                        color=cor,
                        fill=True,
                        fill_color='white',
                        fill_opacity=0.8,
                        popup=f"Início Fileira {j+1} - {equipamento}"
                    ).add_to(mapa)
                    
                    # Fim da fileira
                    folium.CircleMarker(
                        location=trajeto[-1],
                        radius=5,
                        color=cor,
                        fill=True,
                        fill_color=cor,
                        fill_opacity=0.8,
                        popup=f"Fim Fileira {j+1} - {equipamento}"
                    ).add_to(mapa)
        
        # Marcadores gerais início/fim
        if len(dados_equip) > 0:
            primeiro = dados_equip.iloc[0]
            ultimo = dados_equip.iloc[-1]
            
            folium.Marker(
                location=[primeiro['Latitude'], primeiro['Longitude']],
                popup=f"INÍCIO GERAL - {equipamento}",
                icon=folium.Icon(color=cor, icon='play', prefix='fa')
            ).add_to(mapa)
            
            folium.Marker(
                location=[ultimo['Latitude'], ultimo['Longitude']],
                popup=f"FIM GERAL - {equipamento}",
                icon=folium.Icon(color=cor, icon='stop', prefix='fa')
            ).add_to(mapa)
    
    # Adiciona controle de camadas
    folium.LayerControl().add_to(mapa)
    
    # Adiciona controle de tela cheia
    from folium.plugins import Fullscreen
    Fullscreen().add_to(mapa)
    
    return mapa

def otimizar_rota_temporal(dados_equip, janela_tempo_minutos=30):
    """
    Otimiza rota conectando pontos próximos no tempo e espaço
    Evita cruzamentos desnecessários usando janela temporal
    """
    if len(dados_equip) < 10:
        return []
    
    print(f"  Otimizando rota temporal...")
    
    # Ordena por hora
    if 'Hora' in dados_equip.columns:
        try:
            # Converte hora para datetime se necessário
            if dados_equip['Hora'].dtype == 'object':
                dados_equip['Hora'] = pd.to_datetime(dados_equip['Hora'], errors='coerce')
            dados_equip = dados_equip.sort_values('Hora').reset_index(drop=True)
            print(f"  Dados ordenados por hora")
        except:
            print(f"  Usando ordem original")
    
    # Converte para lista de pontos com informações
    pontos = []
    for i, row in dados_equip.iterrows():
        pontos.append({
            'lat': float(row['Latitude']),
            'lng': float(row['Longitude']),
            'hora': row.get('Hora', i),
            'index': i
        })
    
    # Algoritmo de otimização: conecta pontos próximos temporalmente
    # mas verifica se não há cruzamentos desnecessários
    rota_otimizada = []
    pontos_visitados = set()
    
    # Inicia com o primeiro ponto
    ponto_atual = pontos[0]
    rota_otimizada.append([ponto_atual['lat'], ponto_atual['lng']])
    pontos_visitados.add(0)
    
    while len(pontos_visitados) < len(pontos):
        # Encontra próximos candidatos (janela temporal)
        candidatos = []
        
        for i, ponto in enumerate(pontos):
            if i in pontos_visitados:
                continue
            
            # Calcula distância temporal (se disponível)
            if 'Hora' in dados_equip.columns and ponto_atual['hora'] is not None:
                try:
                    if isinstance(ponto_atual['hora'], (int, float)):
                        diff_tempo = abs(ponto['index'] - ponto_atual['index'])
                    else:
                        diff_tempo = abs((ponto['hora'] - ponto_atual['hora']).total_seconds() / 60)
                except:
                    diff_tempo = abs(ponto['index'] - ponto_atual['index'])
            else:
                diff_tempo = abs(ponto['index'] - ponto_atual['index'])
            
            # Calcula distância espacial
            dist_espacial = calcular_distancia(
                ponto_atual['lat'], ponto_atual['lng'],
                ponto['lat'], ponto['lng']
            )
            
            # Score combinado (temporal + espacial)
            # Favorece pontos próximos no tempo e espaço
            score = dist_espacial + (diff_tempo * 10)  # peso temporal
            
            candidatos.append({
                'index': i,
                'ponto': ponto,
                'score': score,
                'dist_espacial': dist_espacial,
                'diff_tempo': diff_tempo
            })
        
        if not candidatos:
            break
        
        # Ordena candidatos por score (menor = melhor)
        candidatos.sort(key=lambda x: x['score'])
        
        # Escolhe o melhor candidato
        melhor = candidatos[0]
        
        # Adiciona à rota
        rota_otimizada.append([melhor['ponto']['lat'], melhor['ponto']['lng']])
        pontos_visitados.add(melhor['index'])
        ponto_atual = melhor['ponto']
    
    print(f"  Rota otimizada com {len(rota_otimizada)} pontos")
    return rota_otimizada

def detectar_e_corrigir_cruzamentos(rota):
    """
    Detecta e corrige cruzamentos óbvios na rota
    """
    if len(rota) < 4:
        return rota
    
    print(f"  Verificando cruzamentos...")
    
    rota_corrigida = rota.copy()
    cruzamentos_corrigidos = 0
    
    # Verifica cada par de segmentos
    for i in range(len(rota_corrigida) - 3):
        for j in range(i + 2, len(rota_corrigida) - 1):
            # Segmento 1: i -> i+1
            # Segmento 2: j -> j+1
            
            p1 = rota_corrigida[i]
            p2 = rota_corrigida[i + 1]
            p3 = rota_corrigida[j]
            p4 = rota_corrigida[j + 1]
            
            # Verifica se os segmentos se cruzam
            if segmentos_se_cruzam(p1, p2, p3, p4):
                # Corrige invertendo a ordem entre os pontos
                if j - i > 2:  # Só corrige se há pontos suficientes entre eles
                    # Inverte a ordem dos pontos entre i+1 e j
                    rota_corrigida[i+1:j+1] = rota_corrigida[i+1:j+1][::-1]
                    cruzamentos_corrigidos += 1
    
    if cruzamentos_corrigidos > 0:
        print(f"  Corrigidos {cruzamentos_corrigidos} cruzamentos")
    
    return rota_corrigida

def segmentos_se_cruzam(p1, p2, p3, p4):
    """
    Verifica se dois segmentos de linha se cruzam
    """
    def orientacao(p, q, r):
        val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
        if val == 0:
            return 0  # colinear
        return 1 if val > 0 else 2  # horário ou anti-horário
    
    def no_segmento(p, q, r):
        return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
                q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))
    
    o1 = orientacao(p1, p2, p3)
    o2 = orientacao(p1, p2, p4)
    o3 = orientacao(p3, p4, p1)
    o4 = orientacao(p3, p4, p2)
    
    # Caso geral
    if o1 != o2 and o3 != o4:
        return True
    
    # Casos especiais (colineares)
    if (o1 == 0 and no_segmento(p1, p3, p2)) or \
       (o2 == 0 and no_segmento(p1, p4, p2)) or \
       (o3 == 0 and no_segmento(p3, p1, p4)) or \
       (o4 == 0 and no_segmento(p3, p2, p4)):
        return True
    
    return False

def criar_mapa_rota_otimizada(dados):
    """Cria mapa com rota otimizada evitando cruzamentos"""
    if dados.empty:
        print("Sem dados para criar mapa")
        return None
    
    # Centro do mapa
    lat_centro = dados['Latitude'].mean()
    lng_centro = dados['Longitude'].mean()
    
    print(f"Centro: {lat_centro}, {lng_centro}")
    
    # Cria mapa básico
    mapa = folium.Map(
        location=[lat_centro, lng_centro],
        zoom_start=17,
        tiles='OpenStreetMap'
    )
    
    # Adiciona camadas de mapa
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satélite'
    ).add_to(mapa)
    
    # Processa por equipamento
    equipamentos = dados['Equipamento'].unique() if 'Equipamento' in dados.columns else ['Único']
    cores = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen']
    
    print(f"Equipamentos: {equipamentos}")
    
    for i, equipamento in enumerate(equipamentos):
        cor = cores[i % len(cores)]
        
        if 'Equipamento' in dados.columns:
            dados_equip = dados[dados['Equipamento'] == equipamento].copy()
        else:
            dados_equip = dados.copy()
        
        print(f"\nProcessando equipamento {equipamento}: {len(dados_equip)} pontos")
        
        # Otimiza rota temporal
        rota_otimizada = otimizar_rota_temporal(dados_equip)
        
        if len(rota_otimizada) >= 2:
            # Corrige cruzamentos
            rota_final = detectar_e_corrigir_cruzamentos(rota_otimizada)
            
            # Adiciona rota principal
            folium.PolyLine(
                locations=rota_final,
                color=cor,
                weight=4,
                opacity=0.9,
                popup=f"Rota Otimizada - {equipamento}",
                tooltip=f"Equipamento {equipamento}"
            ).add_to(mapa)
            
            # Adiciona pontos de interesse (início, meio, fim)
            total_pontos = len(rota_final)
            
            # Início
            folium.Marker(
                location=rota_final[0],
                popup=f"INÍCIO - {equipamento}",
                icon=folium.Icon(color=cor, icon='play', prefix='fa')
            ).add_to(mapa)
            
            # Meio (se houver pontos suficientes)
            if total_pontos > 10:
                meio = total_pontos // 2
                folium.CircleMarker(
                    location=rota_final[meio],
                    radius=6,
                    color=cor,
                    fill=True,
                    fill_color='yellow',
                    fill_opacity=0.8,
                    popup=f"MEIO - {equipamento}"
                ).add_to(mapa)
            
            # Fim
            folium.Marker(
                location=rota_final[-1],
                popup=f"FIM - {equipamento}",
                icon=folium.Icon(color=cor, icon='stop', prefix='fa')
            ).add_to(mapa)
            
            # Adiciona alguns pontos intermediários para referência
            step = max(1, len(rota_final) // 20)  # Mostra ~20 pontos
            for idx in range(0, len(rota_final), step):
                if idx > 0 and idx < len(rota_final) - 1:  # Não duplica início/fim
                    folium.CircleMarker(
                        location=rota_final[idx],
                        radius=3,
                        color=cor,
                        fill=True,
                        fill_color=cor,
                        fill_opacity=0.6,
                        popup=f"Ponto {idx+1} - {equipamento}"
                    ).add_to(mapa)
    
    # Adiciona controle de camadas
    folium.LayerControl().add_to(mapa)
    
    # Adiciona controle de tela cheia
    from folium.plugins import Fullscreen
    Fullscreen().add_to(mapa)
    
    return mapa

def analisar_padrao_movimento(dados_equip):
    """
    Analisa padrão de movimento para detectar direção, velocidade e tendências
    """
    if len(dados_equip) < 5:
        return None
    
    # Ordena por hora
    if 'Hora' in dados_equip.columns:
        try:
            dados_equip = dados_equip.sort_values('Hora').reset_index(drop=True)
        except:
            pass
    
    coords = dados_equip[['Latitude', 'Longitude']].values
    
    # Calcula vetores de movimento entre pontos consecutivos
    vetores = []
    for i in range(len(coords) - 1):
        lat1, lng1 = coords[i]
        lat2, lng2 = coords[i + 1]
        
        # Vetor de movimento
        delta_lat = lat2 - lat1
        delta_lng = lng2 - lng1
        
        # Distância
        distancia = calcular_distancia(lat1, lng1, lat2, lng2)
        
        # Ângulo de movimento
        angulo = math.atan2(delta_lng, delta_lat)
        
        vetores.append({
            'delta_lat': delta_lat,
            'delta_lng': delta_lng,
            'distancia': distancia,
            'angulo': angulo,
            'ponto_origem': [lat1, lng1],
            'ponto_destino': [lat2, lng2]
        })
    
    return vetores

def detectar_trajetos_incompletos(dados_equip, threshold_distancia=200):
    """
    Detecta trajetos que terminam abruptamente (possível perda de dados)
    """
    if len(dados_equip) < 10:
        return []
    
    print(f"  Analisando trajetos incompletos...")
    
    vetores = analisar_padrao_movimento(dados_equip)
    if not vetores:
        return []
    
    trajetos_incompletos = []
    
    # Analisa os últimos movimentos para detectar paradas abruptas
    ultimos_vetores = vetores[-5:]  # Últimos 5 movimentos
    
    # Calcula distância média dos últimos movimentos
    distancias = [v['distancia'] for v in ultimos_vetores if v['distancia'] > 0]
    if not distancias:
        return []
    
    distancia_media = sum(distancias) / len(distancias)
    
    # Verifica se o último movimento é muito menor que a média
    ultimo_movimento = vetores[-1]
    
    # Se a última distância é muito pequena comparada à média, pode ser incompleto
    if ultimo_movimento['distancia'] < distancia_media * 0.3:
        print(f"  Possível trajeto incompleto detectado")
        print(f"  Distância média: {distancia_media:.1f}m, Última: {ultimo_movimento['distancia']:.1f}m")
        
        trajetos_incompletos.append({
            'ponto_final': ultimo_movimento['ponto_destino'],
            'vetores_recentes': ultimos_vetores,
            'distancia_media': distancia_media
        })
    
    return trajetos_incompletos

def predizer_coordenadas_faltantes(trajeto_incompleto, num_predicoes=10):
    """
    Prediz coordenadas faltantes baseado no padrão de movimento
    """
    vetores_recentes = trajeto_incompleto['vetores_recentes']
    ponto_final = trajeto_incompleto['ponto_final']
    distancia_media = trajeto_incompleto['distancia_media']
    
    if len(vetores_recentes) < 3:
        return []
    
    print(f"  Predizendo {num_predicoes} coordenadas faltantes...")
    
    # Analisa tendência de direção dos últimos movimentos
    angulos_recentes = [v['angulo'] for v in vetores_recentes[-3:]]
    
    # Calcula ângulo médio (considerando circularidade)
    sin_medio = sum(math.sin(a) for a in angulos_recentes) / len(angulos_recentes)
    cos_medio = sum(math.cos(a) for a in angulos_recentes) / len(angulos_recentes)
    angulo_tendencia = math.atan2(sin_medio, cos_medio)
    
    # Calcula variação do ângulo (curvatura)
    if len(angulos_recentes) >= 2:
        variacao_angulo = (angulos_recentes[-1] - angulos_recentes[0]) / len(angulos_recentes)
    else:
        variacao_angulo = 0
    
    print(f"  Direção da tendência: {math.degrees(angulo_tendencia):.1f}°")
    print(f"  Curvatura: {math.degrees(variacao_angulo):.2f}°/ponto")
    
    # Gera predições
    coordenadas_preditas = []
    ponto_atual = ponto_final.copy()
    angulo_atual = angulo_tendencia
    
    # Converte distância média para graus (aproximação)
    delta_graus = distancia_media / 111000  # 1 grau ≈ 111km
    
    for i in range(num_predicoes):
        # Aplica curvatura gradual
        angulo_atual += variacao_angulo
        
        # Calcula próximo ponto
        delta_lat = delta_graus * math.cos(angulo_atual)
        delta_lng = delta_graus * math.sin(angulo_atual)
        
        novo_ponto = [
            ponto_atual[0] + delta_lat,
            ponto_atual[1] + delta_lng
        ]
        
        coordenadas_preditas.append(novo_ponto)
        ponto_atual = novo_ponto
    
    return coordenadas_preditas

def analisar_coordenadas_vizinhas(dados_todos, equipamento_atual, raio_busca=500):
    """
    Analisa coordenadas de equipamentos vizinhos para melhorar predições
    """
    if 'Equipamento' not in dados_todos.columns:
        return None
    
    # Dados do equipamento atual
    dados_atual = dados_todos[dados_todos['Equipamento'] == equipamento_atual]
    if len(dados_atual) == 0:
        return None
    
    # Último ponto do equipamento atual
    ultimo_ponto = dados_atual.iloc[-1]
    lat_ref, lng_ref = ultimo_ponto['Latitude'], ultimo_ponto['Longitude']
    
    # Busca equipamentos vizinhos
    outros_equipamentos = dados_todos[dados_todos['Equipamento'] != equipamento_atual]
    
    coordenadas_vizinhas = []
    
    for _, row in outros_equipamentos.iterrows():
        distancia = calcular_distancia(lat_ref, lng_ref, row['Latitude'], row['Longitude'])
        
        if distancia <= raio_busca:
            coordenadas_vizinhas.append({
                'equipamento': row['Equipamento'],
                'coordenada': [row['Latitude'], row['Longitude']],
                'distancia': distancia,
                'hora': row.get('Hora', None)
            })
    
    if coordenadas_vizinhas:
        print(f"  Encontradas {len(coordenadas_vizinhas)} coordenadas vizinhas")
        
        # Ordena por distância
        coordenadas_vizinhas.sort(key=lambda x: x['distancia'])
        
        return coordenadas_vizinhas[:10]  # Retorna as 10 mais próximas
    
    return None

def criar_mapa_com_predicoes(dados):
    """Cria mapa com predições de coordenadas faltantes"""
    if dados.empty:
        print("Sem dados para criar mapa")
        return None
    
    # Centro do mapa
    lat_centro = dados['Latitude'].mean()
    lng_centro = dados['Longitude'].mean()
    
    print(f"Centro: {lat_centro}, {lng_centro}")
    
    # Cria mapa básico
    mapa = folium.Map(
        location=[lat_centro, lng_centro],
        zoom_start=17,
        tiles='OpenStreetMap'
    )
    
    # Adiciona camadas de mapa
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satélite'
    ).add_to(mapa)
    
    # Processa por equipamento
    equipamentos = dados['Equipamento'].unique() if 'Equipamento' in dados.columns else ['Único']
    cores = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen']
    
    print(f"Equipamentos: {equipamentos}")
    
    for i, equipamento in enumerate(equipamentos):
        cor = cores[i % len(cores)]
        
        if 'Equipamento' in dados.columns:
            dados_equip = dados[dados['Equipamento'] == equipamento].copy()
        else:
            dados_equip = dados.copy()
        
        print(f"\nProcessando equipamento {equipamento}: {len(dados_equip)} pontos")
        
        # Otimiza rota temporal (dados reais)
        rota_real = otimizar_rota_temporal(dados_equip)
        
        if len(rota_real) >= 2:
            # Adiciona rota real
            folium.PolyLine(
                locations=rota_real,
                color=cor,
                weight=4,
                opacity=0.9,
                popup=f"Rota Real - {equipamento}",
                tooltip=f"Equipamento {equipamento} - Dados Reais"
            ).add_to(mapa)
            
            # Detecta trajetos incompletos
            trajetos_incompletos = detectar_trajetos_incompletos(dados_equip)
            
            for j, trajeto_incompleto in enumerate(trajetos_incompletos):
                # Prediz coordenadas faltantes
                coordenadas_preditas = predizer_coordenadas_faltantes(trajeto_incompleto, num_predicoes=15)
                
                if coordenadas_preditas:
                    # Adiciona trajeto predito (linha tracejada)
                    folium.PolyLine(
                        locations=coordenadas_preditas,
                        color=cor,
                        weight=3,
                        opacity=0.7,
                        dash_array='10,5',
                        popup=f"Trajeto Predito - {equipamento}",
                        tooltip=f"Predição baseada em padrão de movimento"
                    ).add_to(mapa)
                    
                    # Marca início da predição
                    folium.CircleMarker(
                        location=trajeto_incompleto['ponto_final'],
                        radius=8,
                        color=cor,
                        fill=True,
                        fill_color='yellow',
                        fill_opacity=0.8,
                        popup=f"Início da Predição - {equipamento}"
                    ).add_to(mapa)
                    
                    # Marca fim da predição
                    folium.CircleMarker(
                        location=coordenadas_preditas[-1],
                        radius=8,
                        color=cor,
                        fill=True,
                        fill_color='orange',
                        fill_opacity=0.8,
                        popup=f"Fim da Predição - {equipamento}"
                    ).add_to(mapa)
                    
                    print(f"  ✅ Predição criada: {len(coordenadas_preditas)} pontos")
                
                # Analisa coordenadas vizinhas
                vizinhas = analisar_coordenadas_vizinhas(dados, equipamento, raio_busca=300)
                if vizinhas:
                    # Adiciona marcadores para coordenadas vizinhas
                    for vizinha in vizinhas[:5]:  # Mostra apenas as 5 mais próximas
                        folium.CircleMarker(
                            location=vizinha['coordenada'],
                            radius=4,
                            color='gray',
                            fill=True,
                            fill_color='lightgray',
                            fill_opacity=0.6,
                            popup=f"Vizinho: {vizinha['equipamento']}<br>Dist: {vizinha['distancia']:.0f}m"
                        ).add_to(mapa)
            
            # Marcadores gerais
            if len(rota_real) > 0:
                # Início
                folium.Marker(
                    location=rota_real[0],
                    popup=f"INÍCIO - {equipamento}",
                    icon=folium.Icon(color=cor, icon='play', prefix='fa')
                ).add_to(mapa)
                
                # Fim dos dados reais
                folium.Marker(
                    location=rota_real[-1],
                    popup=f"FIM DOS DADOS - {equipamento}",
                    icon=folium.Icon(color=cor, icon='stop', prefix='fa')
                ).add_to(mapa)
    
    # Adiciona controle de camadas
    folium.LayerControl().add_to(mapa)
    
    # Adiciona controle de tela cheia
    from folium.plugins import Fullscreen
    Fullscreen().add_to(mapa)
    
    return mapa

def detectar_poligonos_fechados(dados_equip, tolerancia_metros=100, min_pontos=10):
    """
    Detecta polígonos fechados baseados em coordenadas que retornam próximo ao ponto inicial
    """
    if len(dados_equip) < min_pontos:
        return []
    
    print(f"  Detectando polígonos fechados...")
    
    # Ordena por hora
    if 'Hora' in dados_equip.columns:
        try:
            dados_equip = dados_equip.sort_values('Hora').reset_index(drop=True)
        except:
            pass
    
    coords = dados_equip[['Latitude', 'Longitude']].values
    poligonos = []
    pontos_usados = set()
    
    # Procura por fechamentos (pontos que retornam próximo a pontos anteriores)
    for i in range(min_pontos, len(coords)):
        if i in pontos_usados:
            continue
            
        ponto_atual = coords[i]
        
        # Verifica se o ponto atual está próximo de algum ponto anterior
        for j in range(max(0, i - 200), i - min_pontos):  # Busca nos últimos 200 pontos
            if j in pontos_usados:
                continue
                
            ponto_anterior = coords[j]
            distancia = calcular_distancia(
                ponto_atual[0], ponto_atual[1],
                ponto_anterior[0], ponto_anterior[1]
            )
            
            # Se encontrou um fechamento
            if distancia <= tolerancia_metros:
                # Cria polígono com os pontos entre j e i
                pontos_poligono = coords[j:i+1].tolist()
                
                if len(pontos_poligono) >= min_pontos:
                    # Calcula área do polígono (aproximada)
                    area = calcular_area_poligono(pontos_poligono)
                    
                    # Calcula centro do polígono
                    centro_lat = sum(p[0] for p in pontos_poligono) / len(pontos_poligono)
                    centro_lng = sum(p[1] for p in pontos_poligono) / len(pontos_poligono)
                    
                    poligono = {
                        'pontos': pontos_poligono,
                        'centro': [centro_lat, centro_lng],
                        'area': area,
                        'inicio_index': j,
                        'fim_index': i,
                        'distancia_fechamento': distancia
                    }
                    
                    poligonos.append(poligono)
                    
                    # Marca pontos como usados
                    for k in range(j, i+1):
                        pontos_usados.add(k)
                    
                    print(f"    Polígono detectado: {len(pontos_poligono)} pontos, área: {area:.0f}m²")
                    break
    
    print(f"  Total de polígonos detectados: {len(poligonos)}")
    return poligonos

def calcular_area_poligono(pontos):
    """
    Calcula área aproximada do polígono usando fórmula de Shoelace
    Converte coordenadas geográficas para metros aproximadamente
    """
    if len(pontos) < 3:
        return 0
    
    # Converte para metros (aproximação)
    pontos_metros = []
    lat_ref = pontos[0][0]
    lng_ref = pontos[0][1]
    
    for lat, lng in pontos:
        # Converte diferenças para metros
        x = (lng - lng_ref) * 111000 * math.cos(math.radians(lat_ref))
        y = (lat - lat_ref) * 111000
        pontos_metros.append([x, y])
    
    # Fórmula de Shoelace
    area = 0
    n = len(pontos_metros)
    
    for i in range(n):
        j = (i + 1) % n
        area += pontos_metros[i][0] * pontos_metros[j][1]
        area -= pontos_metros[j][0] * pontos_metros[i][1]
    
    return abs(area) / 2

def detectar_areas_concentracao(dados_equip, raio_metros=50, min_pontos=20):
    """
    Detecta áreas de concentração de pontos (onde o equipamento passou mais tempo)
    """
    if len(dados_equip) < min_pontos:
        return []
    
    print(f"  Detectando áreas de concentração...")
    
    coords = dados_equip[['Latitude', 'Longitude']].values
    areas_concentracao = []
    
    # Usa DBSCAN para encontrar clusters densos
    from sklearn.cluster import DBSCAN
    
    # Converte raio para graus
    eps_graus = raio_metros / 111000
    
    clustering = DBSCAN(eps=eps_graus, min_samples=min_pontos).fit(coords)
    labels = clustering.labels_
    
    # Processa cada cluster
    for cluster_id in set(labels):
        if cluster_id == -1:  # Ignora ruído
            continue
            
        # Pontos do cluster
        mask = labels == cluster_id
        pontos_cluster = coords[mask]
        
        if len(pontos_cluster) >= min_pontos:
            # Centro do cluster
            centro_lat = pontos_cluster[:, 0].mean()
            centro_lng = pontos_cluster[:, 1].mean()
            
            # Raio do cluster (distância máxima do centro)
            distancias = [calcular_distancia(centro_lat, centro_lng, p[0], p[1]) 
                         for p in pontos_cluster]
            raio_cluster = max(distancias)
            
            # Cria polígono circular aproximado
            poligono_circular = criar_poligono_circular(centro_lat, centro_lng, raio_cluster)
            
            area = {
                'pontos': pontos_cluster.tolist(),
                'centro': [centro_lat, centro_lng],
                'raio': raio_cluster,
                'poligono': poligono_circular,
                'densidade': len(pontos_cluster),
                'area': math.pi * (raio_cluster ** 2)
            }
            
            areas_concentracao.append(area)
            print(f"    Área de concentração: {len(pontos_cluster)} pontos, raio: {raio_cluster:.0f}m")
    
    print(f"  Total de áreas de concentração: {len(areas_concentracao)}")
    return areas_concentracao

def criar_poligono_circular(centro_lat, centro_lng, raio_metros, num_pontos=20):
    """
    Cria um polígono circular aproximado
    """
    pontos = []
    
    for i in range(num_pontos):
        angulo = 2 * math.pi * i / num_pontos
        
        # Converte raio para graus
        delta_lat = (raio_metros / 111000) * math.cos(angulo)
        delta_lng = (raio_metros / (111000 * math.cos(math.radians(centro_lat)))) * math.sin(angulo)
        
        lat = centro_lat + delta_lat
        lng = centro_lng + delta_lng
        
        pontos.append([lat, lng])
    
    # Fecha o polígono
    pontos.append(pontos[0])
    
    return pontos

def criar_mapa_poligonos(dados):
    """Cria mapa com polígonos fechados e áreas de concentração"""
    if dados.empty:
        print("Sem dados para criar mapa")
        return None
    
    # Centro do mapa
    lat_centro = dados['Latitude'].mean()
    lng_centro = dados['Longitude'].mean()
    
    print(f"Centro: {lat_centro}, {lng_centro}")
    
    # Cria mapa básico
    mapa = folium.Map(
        location=[lat_centro, lng_centro],
        zoom_start=17,
        tiles='OpenStreetMap'
    )
    
    # Adiciona camadas de mapa
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satélite'
    ).add_to(mapa)
    
    # Processa por equipamento
    equipamentos = dados['Equipamento'].unique() if 'Equipamento' in dados.columns else ['Único']
    cores = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen']
    
    print(f"Equipamentos: {equipamentos}")
    
    for i, equipamento in enumerate(equipamentos):
        cor = cores[i % len(cores)]
        cor_poligono = cores[(i + 1) % len(cores)]  # Cor diferente para polígonos
        
        if 'Equipamento' in dados.columns:
            dados_equip = dados[dados['Equipamento'] == equipamento].copy()
        else:
            dados_equip = dados.copy()
        
        print(f"\nProcessando equipamento {equipamento}: {len(dados_equip)} pontos")
        
        # Detecta polígonos fechados
        poligonos = detectar_poligonos_fechados(dados_equip, tolerancia_metros=80, min_pontos=15)
        
        # Adiciona polígonos fechados
        for j, poligono in enumerate(poligonos):
            # Polígono preenchido
            folium.Polygon(
                locations=poligono['pontos'],
                color=cor_poligono,
                weight=3,
                opacity=0.8,
                fill=True,
                fill_color=cor_poligono,
                fill_opacity=0.3,
                popup=f"Área de Trabalho {j+1} - {equipamento}<br>"
                      f"Pontos: {len(poligono['pontos'])}<br>"
                      f"Área: {poligono['area']:.0f}m²<br>"
                      f"Fechamento: {poligono['distancia_fechamento']:.1f}m"
            ).add_to(mapa)
            
            # Marca centro do polígono
            folium.CircleMarker(
                location=poligono['centro'],
                radius=8,
                color=cor_poligono,
                fill=True,
                fill_color='yellow',
                fill_opacity=0.8,
                popup=f"Centro Área {j+1} - {equipamento}"
            ).add_to(mapa)
            
            # Marca pontos de fechamento
            inicio = poligono['pontos'][0]
            fim = poligono['pontos'][-1]
            
            folium.CircleMarker(
                location=inicio,
                radius=6,
                color='green',
                fill=True,
                fill_color='lightgreen',
                fill_opacity=0.9,
                popup=f"Início do Polígono {j+1}"
            ).add_to(mapa)
            
            folium.CircleMarker(
                location=fim,
                radius=6,
                color='red',
                fill=True,
                fill_color='lightcoral',
                fill_opacity=0.9,
                popup=f"Fechamento do Polígono {j+1}"
            ).add_to(mapa)
        
        # Detecta áreas de concentração
        areas_concentracao = detectar_areas_concentracao(dados_equip, raio_metros=40, min_pontos=15)
        
        # Adiciona áreas de concentração
        for k, area in enumerate(areas_concentracao):
            # Polígono circular da área de concentração
            folium.Polygon(
                locations=area['poligono'],
                color=cor,
                weight=2,
                opacity=0.6,
                fill=True,
                fill_color=cor,
                fill_opacity=0.2,
                popup=f"Concentração {k+1} - {equipamento}<br>"
                      f"Densidade: {area['densidade']} pontos<br>"
                      f"Raio: {area['raio']:.0f}m<br>"
                      f"Área: {area['area']:.0f}m²"
            ).add_to(mapa)
            
            # Marca centro da concentração
            folium.CircleMarker(
                location=area['centro'],
                radius=5,
                color=cor,
                fill=True,
                fill_color='orange',
                fill_opacity=0.8,
                popup=f"Centro Concentração {k+1}"
            ).add_to(mapa)
        
        # Adiciona trajeto original (linha fina para referência)
        coords_originais = [[row['Latitude'], row['Longitude']] for _, row in dados_equip.iterrows()]
        if len(coords_originais) >= 2:
            folium.PolyLine(
                locations=coords_originais,
                color=cor,
                weight=1,
                opacity=0.4,
                popup=f"Trajeto Original - {equipamento}"
            ).add_to(mapa)
        
        # Marcadores gerais
        if len(dados_equip) > 0:
            primeiro = dados_equip.iloc[0]
            ultimo = dados_equip.iloc[-1]
            
            folium.Marker(
                location=[primeiro['Latitude'], primeiro['Longitude']],
                popup=f"INÍCIO GERAL - {equipamento}",
                icon=folium.Icon(color=cor, icon='play', prefix='fa')
            ).add_to(mapa)
            
            folium.Marker(
                location=[ultimo['Latitude'], ultimo['Longitude']],
                popup=f"FIM GERAL - {equipamento}",
                icon=folium.Icon(color=cor, icon='stop', prefix='fa')
            ).add_to(mapa)
    
    # Adiciona controle de camadas
    folium.LayerControl().add_to(mapa)
    
    # Adiciona controle de tela cheia
    from folium.plugins import Fullscreen
    Fullscreen().add_to(mapa)
    
    return mapa

# ===== NOVA FUNÇÃO: MAPA DE LINHAS COLORIDAS POR VELOCIDADE =====

def criar_mapa_linhas_velocidade(dados):
    """Cria mapa mostrando apenas linhas, coloridas de acordo com a velocidade.
    Verde = ≤4 km/h (trabalho), Laranja = 4-10 km/h (manobra), Vermelho = >10 km/h (deslocamento)."""
    if dados.empty:
        print("Sem dados para criar mapa de linhas")
        return None

    lat_centro = dados['Latitude'].mean()
    lng_centro = dados['Longitude'].mean()

    print(f"Centro: {lat_centro}, {lng_centro}")

    mapa = folium.Map(location=[lat_centro, lng_centro], zoom_start=16, tiles='OpenStreetMap')

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='Satélite').add_to(mapa)

    equipamentos = dados['Equipamento'].unique() if 'Equipamento' in dados.columns else ['Único']
    cores_default = ['blue', 'purple', 'orange', 'darkred', 'darkgreen']

    for idx, equipamento in enumerate(equipamentos):
        if 'Equipamento' in dados.columns:
            df_equip = dados[dados['Equipamento'] == equipamento].copy()
        else:
            df_equip = dados.copy()

        print(f"Processando equipamento {equipamento}: {len(df_equip)} pontos")

        # Conversões seguras
        df_equip['Latitude'] = pd.to_numeric(df_equip['Latitude'], errors='coerce')
        df_equip['Longitude'] = pd.to_numeric(df_equip['Longitude'], errors='coerce')
        if 'Velocidade' in df_equip.columns:
            df_equip['Velocidade'] = pd.to_numeric(df_equip['Velocidade'], errors='coerce')

        # Ordena por hora se existir
        if 'Hora' in df_equip.columns:
            try:
                df_equip = df_equip.sort_values('Hora')
            except:
                pass

        # Remove coordenadas inválidas
        df_equip = df_equip.dropna(subset=['Latitude', 'Longitude'])

        coords = df_equip[['Latitude', 'Longitude']].values.tolist()

        # Se não há velocidade, desenha linha única
        if 'Velocidade' not in df_equip.columns or df_equip['Velocidade'].isna().all():
            cor = cores_default[idx % len(cores_default)]
            folium.PolyLine(coords, color=cor, weight=3, opacity=0.8,
                            popup=f"Rota {equipamento}").add_to(mapa)
        else:
            vels = df_equip['Velocidade'].values
            # Desenhar segmento a segmento
            for i in range(len(coords) - 1):
                v = vels[i+1] if i+1 < len(vels) else vels[i]
                if np.isnan(v):
                    cor = 'gray'
                elif v <= 4:
                    cor = 'green'
                elif v <= 10:
                    cor = 'orange'
                else:
                    cor = 'red'
                folium.PolyLine([coords[i], coords[i+1]], color=cor, weight=3, opacity=0.8).add_to(mapa)

        # Marcadores início / fim
        if coords:
            folium.Marker(coords[0], popup=f"INÍCIO - {equipamento}",
                          icon=folium.Icon(color='green', icon='play', prefix='fa')).add_to(mapa)
            folium.Marker(coords[-1], popup=f"FIM - {equipamento}",
                          icon=folium.Icon(color='red', icon='stop', prefix='fa')).add_to(mapa)

    folium.LayerControl().add_to(mapa)
    from folium.plugins import Fullscreen
    Fullscreen().add_to(mapa)
    return mapa

# ===== FUNÇÕES DE PREDIÇÃO BASEADA EM VELOCIDADE =====

def preencher_gaps_por_velocidade(df_equip, max_intervalo_seg=120):
    """Insere pontos preditos quando o intervalo de tempo entre registros excede max_intervalo_seg.
    Usa interpolação linear entre os pontos, preservando direção aproximada.
    Retorna (trajeto_completo, lista_preditos)"""
    if len(df_equip) < 2 or 'Hora' not in df_equip.columns:
        coords = df_equip[['Latitude', 'Longitude']].values.tolist()
        return coords, []

    # Certificar ordem temporal
    try:
        df_sorted = df_equip.sort_values('Hora').reset_index(drop=True)
    except:
        df_sorted = df_equip.copy().reset_index(drop=True)

    coords_result = []
    coords_pred = []

    for i in range(len(df_sorted) - 1):
        lat1, lng1 = df_sorted.loc[i, ['Latitude', 'Longitude']]
        lat2, lng2 = df_sorted.loc[i + 1, ['Latitude', 'Longitude']]

        hora1 = df_sorted.loc[i, 'Hora']
        hora2 = df_sorted.loc[i + 1, 'Hora']

        # Adiciona ponto original
        coords_result.append([lat1, lng1])

        try:
            dt = abs((hora2 - hora1).total_seconds())
        except:
            dt = 60  # fallback se hora não for datetime

        if dt > max_intervalo_seg and dt < 3600:  # ignora saltos enormes >1h
            # Número de pontos faltantes (assumindo 1 registro por minuto)
            n_missing = int(round(dt / 60)) - 1
            for k in range(1, n_missing + 1):
                frac = k / (n_missing + 1)
                lat_p = lat1 + frac * (lat2 - lat1)
                lng_p = lng1 + frac * (lng2 - lng1)
                coords_result.append([lat_p, lng_p])
                coords_pred.append([lat_p, lng_p])

    # Adiciona último ponto
    coords_result.append(df_sorted.iloc[-1][['Latitude', 'Longitude']].tolist())
    return coords_result, coords_pred

def criar_mapa_predicao_velocidade(dados):
    """Gera mapa com linhas suavizadas/preditas usando velocidade e hora para interpolar gaps."""
    if dados.empty:
        print("Sem dados para criar mapa.")
        return None

    lat_centro = dados['Latitude'].mean()
    lng_centro = dados['Longitude'].mean()

    mapa = folium.Map(location=[lat_centro, lng_centro], zoom_start=16, tiles='OpenStreetMap')

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='Satélite').add_to(mapa)

    equipamentos = dados['Equipamento'].unique() if 'Equipamento' in dados.columns else ['Único']
    cores = ['red', 'blue', 'green', 'purple', 'orange', 'darkred']

    for idx, equipamento in enumerate(equipamentos):
        if 'Equipamento' in dados.columns:
            df_equip = dados[dados['Equipamento'] == equipamento].copy()
        else:
            df_equip = dados.copy()

        # Conversões em lote
        df_equip['Latitude'] = pd.to_numeric(df_equip['Latitude'], errors='coerce')
        df_equip['Longitude'] = pd.to_numeric(df_equip['Longitude'], errors='coerce')

        # Converte Hora
        if 'Hora' in df_equip.columns and df_equip['Hora'].dtype == 'object':
            df_equip['Hora'] = pd.to_datetime(df_equip['Hora'], errors='coerce')

        # Remove inválidos
        df_equip = df_equip.dropna(subset=['Latitude', 'Longitude'])

        trajeto_completo, pontos_preditos = preencher_gaps_por_velocidade(df_equip)

        cor = cores[idx % len(cores)]

        # Desenha linha principal
        folium.PolyLine(trajeto_completo, color=cor, weight=4, opacity=0.85,
                        popup=f"Trajeto {equipamento}").add_to(mapa)

        # Desenha pontos preditos como tracejado
        if pontos_preditos:
            folium.PolyLine(pontos_preditos, color=cor, weight=2, opacity=0.6,
                            dash_array='5,10', popup='Pontos preditos').add_to(mapa)

        # Marcadores início/fim
        if trajeto_completo:
            folium.Marker(trajeto_completo[0], icon=folium.Icon(color='green', icon='play', prefix='fa'),
                          popup=f"INÍCIO - {equipamento}").add_to(mapa)
            folium.Marker(trajeto_completo[-1], icon=folium.Icon(color='red', icon='stop', prefix='fa'),
                          popup=f"FIM - {equipamento}").add_to(mapa)

    folium.LayerControl().add_to(mapa)
    from folium.plugins import Fullscreen
    Fullscreen().add_to(mapa)
    return mapa

def main():
    print("=== GERADOR DE MAPA SIMPLES POR EQUIPAMENTO ===")
    
    # Verifica se sklearn está disponível
    try:
        from sklearn.cluster import DBSCAN
        print("✅ Biblioteca sklearn disponível")
    except ImportError:
        print("❌ Biblioteca sklearn não encontrada. Instalando...")
        os.system("pip install scikit-learn")
        try:
            from sklearn.cluster import DBSCAN
            print("✅ sklearn instalado com sucesso")
        except ImportError:
            print("❌ Erro ao instalar sklearn. Usando método alternativo...")
            return
    
    # Busca arquivos
    arquivos = buscar_arquivos_csv()
    if not arquivos:
        print("Nenhum arquivo CSV encontrado!")
        return
    
    print(f"Arquivos encontrados: {len(arquivos)}")
    
    pasta_mapas = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'mapas')
    os.makedirs(pasta_mapas, exist_ok=True)
    
    # Limpa pasta de mapas se configurado
    if CONFIG['saida']['limpar_pasta']:
        print("\n🧹 Limpando pasta de mapas anteriores...")
        try:
            arquivos_antigos = glob.glob(os.path.join(pasta_mapas, "*"))
            contador = 0
            for arquivo in arquivos_antigos:
                if os.path.isfile(arquivo):
                    os.remove(arquivo)
                    contador += 1
            print(f"✅ {contador} arquivos removidos.")
        except Exception as e:
            print(f"⚠️ Erro ao limpar pasta: {e}")

    print("\n--- Gerando mapas individuais ---")

    for arquivo in arquivos:
        dados = ler_coordenadas(arquivo)
        if dados is None or dados.empty:
            print(f"⚠️  Dados vazios em {os.path.basename(arquivo)}, pulando.")
            continue

        mapa = criar_mapa_simples(dados)
        if mapa:
            base = os.path.splitext(os.path.basename(arquivo))[0]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Formatação do nome conforme configuração
            prefixo = CONFIG['saida']['prefixo_arquivo']
            formato = CONFIG['saida']['formato_nome']
            nome_base = formato.format(
                nome=base,
                tipo='mapa',
                timestamp=timestamp,
                prefixo=prefixo
            )
            
            # Salva HTML se configurado
            if CONFIG['saida']['html']:
                nome_html = f"{nome_base}.html"
                caminho_html = os.path.join(pasta_mapas, nome_html)
                mapa.save(caminho_html)
                print(f"✅ HTML gerado: {nome_html}")
            else:
                # Se PNG ativado mas HTML não, precisamos salvar um HTML temporário
                if CONFIG['saida']['png']:
                    nome_html = f"temp_{timestamp}.html"
                    caminho_html = os.path.join(pasta_mapas, nome_html)
                    mapa.save(caminho_html)
                
            # Salva PNG se configurado
            if CONFIG['saida']['png']:
                nome_png = f"{nome_base}.png"
                caminho_png = os.path.join(pasta_mapas, nome_png)
                salvar_screenshot(caminho_html, caminho_png)
                print(f"✅ PNG gerado: {nome_png}")
                
                # Remove HTML temporário se necessário
                if not CONFIG['saida']['html'] and os.path.exists(caminho_html):
                    try:
                        os.remove(caminho_html)
                    except:
                        pass
        else:
            print(f"❌ Falha ao gerar mapa para {os.path.basename(arquivo)}")

    print("\n🎯 Mapas individuais prontos na pasta output/mapas")

# ====================================================================================
# MAPA SIMPLES (LINHAS POR EQUIPAMENTO)
# ====================================================================================


def _cor_equip(idx: int) -> str:
    """Retorna cor única para o índice, sem repetir tons primários."""
    cores_base = CONFIG['cores_equipamentos']
    if idx < len(cores_base):
        return cores_base[idx]
    # Gera cor HSV -> HEX
    h = (idx / 20.0) % 1.0  # espaça a cada 20 itens para evitar proximidade
    r, g, b = colorsys.hsv_to_rgb(h, 0.8, 0.9)
    return '#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255))


def criar_mapa_simples(dados):
    """Cria mapa simples conectando pontos de cada equipamento por uma linha colorida."""
    if dados.empty:
        print("Sem dados para criar mapa simples!")
        return None

    lat_centro = dados['Latitude'].mean()
    lng_centro = dados['Longitude'].mean()

    mapa = folium.Map(
        location=[lat_centro, lng_centro],
        zoom_start=CONFIG['zoom_start'],
        tiles=CONFIG['base_tile']
    )

    if CONFIG['satellite_layer']:
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri', name='Satélite').add_to(mapa)

    equipamentos = dados['Equipamento'].unique() if 'Equipamento' in dados.columns else ['Único']

    # Inicializa listas para itens da legenda e limites de coordenadas
    legenda_items = []  # (nome, cor)
    all_coords_bounds = []  # lista de todas as coordenadas para ajustar o zoom

    for idx, equipamento in enumerate(equipamentos):
        if 'Equipamento' in dados.columns:
            df_equip = dados[dados['Equipamento'] == equipamento].copy()
        else:
            df_equip = dados.copy()

        # Limpar / ordenar
        df_equip['Latitude'] = pd.to_numeric(df_equip['Latitude'], errors='coerce')
        df_equip['Longitude'] = pd.to_numeric(df_equip['Longitude'], errors='coerce')
        if 'Hora' in df_equip.columns:
            try:
                df_equip = df_equip.sort_values('Hora')
            except:
                pass

        df_equip = df_equip.dropna(subset=['Latitude', 'Longitude'])

        coords = df_equip[['Latitude', 'Longitude']].values.tolist()
        if len(coords) < 2:
            continue

        cor = _cor_equip(idx)

        poly = folium.PolyLine(
            coords,
            color=cor,
            weight=CONFIG['line_weight'],
            opacity=CONFIG['line_opacity'],
            popup=f"Equipamento {equipamento}"
        )
        poly.add_to(mapa)

        # Adiciona marcadores de início/fim na mesma cor da linha
        if CONFIG['marcadores_inicio_fim'] and coords:
            # Marcador de início
            folium.Marker(
                location=coords[0],
                popup=f"INÍCIO - {equipamento}",
                icon=folium.Icon(color=cor, icon='play', prefix='fa')
            ).add_to(mapa)
            
            # Marcador de fim
            folium.Marker(
                location=coords[-1],
                popup=f"FIM - {equipamento}",
                icon=folium.Icon(color=cor, icon='stop', prefix='fa')
            ).add_to(mapa)

        # Adiciona legenda
        legenda_items.append((equipamento, cor))
        all_coords_bounds.extend(coords)

    # Ajusta zoom/centro para cobrir todos os pontos
    if all_coords_bounds:
        lats = [c[0] for c in all_coords_bounds]
        lngs = [c[1] for c in all_coords_bounds]
        mapa.fit_bounds([[min(lats), min(lngs)], [max(lats), max(lngs)]])

    # Adiciona legenda
    if legenda_items and CONFIG['legenda']['mostrar']:
        # Posicionamento da legenda
        posicao = CONFIG['legenda']['posicao']
        if posicao == 'top-left':
            pos_css = 'top: 20px; left: 10px;'
        elif posicao == 'top-right':
            pos_css = 'top: 20px; right: 10px;'
        elif posicao == 'bottom-left':
            pos_css = 'bottom: 20px; left: 10px;'
        else:  # bottom-right (padrão)
            pos_css = 'bottom: 20px; right: 10px;'
            
        # Estilo da legenda
        config_legenda = CONFIG['legenda']
        # Cria container branco (3× maior)
        legenda_html = f'<div style="position: fixed; {pos_css} ' \
                       f'z-index:9999; ' \
                       f'background: {config_legenda["fundo"]}; ' \
                       f'padding: {config_legenda["padding"]}; ' \
                       f'border: {config_legenda["borda"]}; ' \
                       f'font-size: {config_legenda["tamanho_fonte"]}px; ' \
                       f'line-height: {config_legenda["tamanho_fonte"] * 1.4}px; ' \
                       f'width: {config_legenda["largura"]}px; ' \
                       f'border-radius: {config_legenda["raio_borda"]}px; ' \
                       f'box-shadow: {config_legenda["sombra"]};' \
                       f'">'
                       
        # Texto em negrito se configurado
        estilo_texto = 'font-weight:bold;' if config_legenda.get('negrito', False) else ''
        
        for nome, cor in legenda_items:
            # Círculo colorido com tamanho configurado
            tam_circulo = config_legenda.get('tamanho_circulo', 16)
            espaco_h = config_legenda.get('espaco_horizontal', 10)
            espaco_v = config_legenda.get('espaco_itens', 12)
            
            # Cria item da legenda
            # Linha com circulo colorido + texto
            legenda_html += f'<div style="display:flex; align-items:center; ' \
                            f'margin-bottom:{espaco_v}px;">' \
                            f'<div style="width:{tam_circulo}px; height:{tam_circulo}px; ' \
                            f'border-radius:50%; background-color:{cor};"></div>' \
                            f'<div style="margin-left:{espaco_h}px; {estilo_texto}">' \
                            f'{nome}</div>' \
                            f'</div>'
                            
        legenda_html += '</div>'
        mapa.get_root().html.add_child(folium.Element(legenda_html))

    folium.LayerControl().add_to(mapa)
    from folium.plugins import Fullscreen
    Fullscreen().add_to(mapa)

    return mapa

# ====================================================================================
# UTILITÁRIO: SALVAR SCREENSHOT A4 DO MAPA (usa Selenium)
# ====================================================================================


def salvar_screenshot(html_path: str, png_path: str, width: int = 1240, height: int = 1754):
    """Gera captura PNG vertical (A4) do HTML usando Selenium headless.
    Requer chromedriver no PATH ou webdriver-gerenciado.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import time, pathlib

        opts = Options()
        opts.add_argument('--headless')
        opts.add_argument('--disable-gpu')
        opts.add_argument(f'--window-size={width},{height}')

        driver = webdriver.Chrome(options=opts)
        driver.get(pathlib.Path(html_path).as_uri())
        time.sleep(2)  # aguarda renderização
        driver.save_screenshot(png_path)
        driver.quit()
        print(f"🖼️  Screenshot salvo: {os.path.basename(png_path)}")
    except Exception as e:
        print(f"⚠️  Não foi possível gerar screenshot ({os.path.basename(png_path)}): {e}")

if __name__ == "__main__":
    main()
