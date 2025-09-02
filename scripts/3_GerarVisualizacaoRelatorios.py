import os
import glob
from datetime import datetime
from typing import List, Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator

# ====================================================================
# BLOCO DE CONFIGURAÇÃO – altere aqui o layout como desejar
# ====================================================================
CONFIG = {
    # Tamanho da figura (largura, altura)
    # Altura foi reduzida para 1/3 da original (original ≈ 8)
    'FIG_SIZE': (15, 10 /2.5),

    # Altura das barras horizontais no gráfico de Gantt
    # Original = 0.6 → agora 1/3
    'BAR_HEIGHT': (0.3),

    # Cores das barras por tipo de intervalo
    'COLORS': {
        'Produtivo': '#51CF66',   # Verde
        'Disponível': '#74C0FC', # Azul claro
        'Manutenção': '#FF6B6B',  # Vermelho
        'Falta de Informação': '#FFFFFF' # Branco
    },

    # Posições verticais das barras: deslocadas +0.5 para criar folga inferior
    'Y_POS': {
        'Produtivo': 2.5,    # Linha superior (antes 1)
        'Disponível': 2.0,   # Linha central (antes 0)
        'Manutenção': 1.5,   # Linha inferior (antes -1)
        'Falta de Informação': 0.5 # Linha inferior para falta de informação
    },

    # Deslocamento vertical aplicado a TODAS as barras
    # Aumente para mover tudo para cima e criar espaço abaixo
    'Y_SHIFT': 4,

    # Intervalo entre marcas principais da régua inferior (em horas)
    'MAIN_TICK_INTERVAL_H': 1,

    # Formato do rótulo da régua inferior
    'MAIN_TICK_LABEL_FMT': '{:02d}',

    # Rotação dos rótulos da régua superior (início/fim de manutenções)
    'TOP_TICK_ROTATION': 0,

    # Offset da régua de manutenção (negativo empurra para baixo); -10 ≈ colado à barra
    'MAINT_TICK_OFFSET_PT': -10,

    # Offset vertical entre rótulos em um mesmo cluster (pontos, positivo sobe)
    'LABEL_CLUSTER_OFFSET_PT': 10,
    # Fração vertical (0–1) do eixo para posicionar texto de início/fim de manutenção
    # Pequeno valor eleva o texto próximo à barra.
    'MAINT_LABEL_Y_FRAC': 0.30,

    # Transforma durações maiores que este limiar (min) em texto dentro da barra
    'LABEL_THRESHOLD_MIN': 60,

    # Diretório onde os gráficos serão salvos (mesmo local que os outros arquivos gerados)
    'OUTPUT_DIR': os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output', 'graficos')),

    # Ajuste vertical da legenda (fração fora do eixo). Menor → legenda mais próxima do gráfico
    'LEGEND_Y': 1.0,

    # Exibir prévia na tela? False por padrão
    'VER_PREVIA': True,

    # Intervalo das sublinhas (minutos)
    'SUB_TICK_INTERVAL_MIN': 15,
    # Opacidade das sublinhas (0–1). 0.4 deixa bem visível sem poluir
    'SUB_TICK_ALPHA': 0.2,
}
# ====================================================================

# ----------------------------------------------------------------------------
# Funções utilitárias
# ----------------------------------------------------------------------------

def hora_str_para_minutos(hora: str) -> float:
    """Converte 'HH:MM:SS' → minutos desde 00:00."""
    try:
        if pd.isna(hora) or hora in ("", "N/A"):
            return 0.0
        h, m, *s = hora.strip().split(':')
        s = int(s[0]) if s else 0
        return int(h) * 60 + int(m) + s / 60
    except Exception:
        return 0.0

# ----------------------------------------------------------------------------
# Função principal de plotagem
# ----------------------------------------------------------------------------

def plot_gantt(df: pd.DataFrame, equipamento: Optional[str] = None, data: Optional[str] = None,
               salvar_png: bool = True, exibir: bool = True):
    """Gera gráfico de Gantt conforme CONFIG."""

    df_plot = df.copy()
    if equipamento is not None:
        df_plot = df_plot[df_plot['Equipamento'] == equipamento]
    if data is not None and 'Data' in df_plot.columns:
        df_plot = df_plot[df_plot['Data'] == data]

    df_plot['inicio_min'] = df_plot['Início'].apply(hora_str_para_minutos)
    df_plot['duracao_min'] = df_plot['Duração (horas)'] * 60

    # Descarta intervalos de manutenção com duração zero (erro de apontamento)
    df_plot = df_plot[~((df_plot['Tipo'] == 'Manutenção') & (df_plot['duracao_min'] == 0))]

    if df_plot.empty:
        print('Sem dados válidos após remover intervalos de duração zero.')
        return

    # Figura
    fig, ax = plt.subplots(figsize=CONFIG['FIG_SIZE'])
    # Oculta a borda superior para não cruzar a legenda
    ax.spines['top'].set_visible(False)

    # Barras
    for _, row in df_plot.iterrows():
        tipo = row['Tipo']
        cor = CONFIG['COLORS'].get(tipo, '#808080')
        y = CONFIG['Y_POS'].get(tipo, 0) + CONFIG.get('Y_SHIFT', 0)
        # Barras sem contorno (edge) para visual mais limpo
        ax.barh(
            y,
            row['duracao_min'],
            left=row['inicio_min'],
            height=CONFIG['BAR_HEIGHT'],
            color=cor,
            edgecolor='none',  # remove borda
            linewidth=0,
            alpha=0.9,
            zorder=3,
        )
        if row['duracao_min'] >= CONFIG['LABEL_THRESHOLD_MIN']:
            ax.text(row['inicio_min'] + row['duracao_min'] / 2, y,
                    f"{row['duracao_min'] / 60:.1f}h", va='center', ha='center', fontsize=7, color='black')

    # --------------------------------------------------------------------
    # Régua inferior principais (00–24h)
    # --------------------------------------------------------------------
    total_horas = 24
    ticks_min = np.arange(0, total_horas + 1, CONFIG['MAIN_TICK_INTERVAL_H']) * 60
    tick_labels = [CONFIG['MAIN_TICK_LABEL_FMT'].format(int(t)) for t in np.arange(0, total_horas + 1)]
    ax.set_xlim(0, total_horas * 60)
    ax.set_xticks(ticks_min)
    ax.set_xticklabels(tick_labels)
    # Remover label do eixo X
    ax.set_xlabel('')

    # --------------------------------------------------------------------
    # Régua intermediária aprimorada: evita sobreposição de labels quando
    # existem vários intervalos próximos. Usa anotações com offsets verticais.
    # --------------------------------------------------------------------
    manut = df_plot[df_plot['Tipo'] == 'Manutenção']

    if not manut.empty:
        ax_mid = ax.twiny()
        ax_mid.set_xlim(ax.get_xlim())
        ax_mid.xaxis.set_ticks_position('bottom')
        ax_mid.xaxis.set_label_position('bottom')
        ax_mid.spines['bottom'].set_position(('outward', CONFIG['MAINT_TICK_OFFSET_PT']))
        ax_mid.set_frame_on(False)

        # Parâmetros de controle
        OVERLAP_THRESHOLD_MIN = 20  # diferença máx. p/ considerar labels próximas (minutos)
        V_OFFSET_PT = CONFIG.get('LABEL_CLUSTER_OFFSET_PT', 10)  # deslocamento vertical (pontos)

        # Posição base vertical das anotações
        base_y = CONFIG.get('MAINT_LABEL_Y_FRAC', 0)

        # Estrutura para formar clusters de posições próximas
        pontos = []  # (pos, label)
        manut_sorted = manut.sort_values('inicio_min').reset_index(drop=True)
        total_interv = len(manut_sorted)
        for idx_r, r in manut_sorted.iterrows():
            ini = r['inicio_min']
            fim = r['inicio_min'] + r['duracao_min']
            ini_str = f"{int(ini//60):02d}:{int(ini%60):02d}"
            fim_str = f"{int(fim//60):02d}:{int(fim%60):02d}"

            # Determinar distância para próximo intervalo (em minutos)
            prox_ini_dist = None
            if idx_r < total_interv - 1:
                prox_ini = manut_sorted.iloc[idx_r + 1]['inicio_min']
                prox_ini_dist = prox_ini - fim  # pode ser negativo se sobreposto

            if r['duracao_min'] < 60:
                # Intervalo curto → rótulo único/empilhado centralizado no meio do bloco
                centro = ini + r['duracao_min'] / 2
                pontos.append((centro, ini_str if ini_str == fim_str else f"{ini_str}\n{fim_str}"))
            else:
                # Intervalo longo (>1 h)
                pontos.append((ini, ini_str))
                # Só adiciona tick de fim se distante do próximo início
                if prox_ini_dist is None or prox_ini_dist >= OVERLAP_THRESHOLD_MIN:
                    pontos.append((fim, fim_str))

        # Ordenar por posição
        pontos = sorted(pontos, key=lambda x: x[0])

        # Criar clusters
        clusters: List[List[tuple]] = []
        for pos, lbl in pontos:
            if not clusters or pos - clusters[-1][-1][0] > OVERLAP_THRESHOLD_MIN:
                clusters.append([(pos, lbl)])
            else:
                clusters[-1].append((pos, lbl))

        # Definir posições dos rótulos (usado para anotações), mas ocultar as marcas visuais
        ax_mid.set_xticks([p for p, _ in pontos])
        ax_mid.set_xticklabels([''] * len(pontos))
        # Oculta as marcas (ticks) deixando apenas os textos de anotação
        ax_mid.tick_params(axis='x', which='both', length=0)

        for cluster in clusters:
            for idx, (pos, lbl) in enumerate(cluster):
                # Distribui rótulos alternando acima/abaixo da linha base para evitar sobreposição
                nivel = (idx // 2) + 1  # 1,1,2,2,3,3...
                direcao = -1 if idx % 2 == 0 else 1  # cima, baixo, cima, baixo...
                offset = direcao * nivel * V_OFFSET_PT

                ax_mid.annotate(lbl,
                                 xy=(pos, base_y),
                                 xycoords=('data', 'axes fraction'),
                                 xytext=(0, offset),
                                 textcoords='offset points',
                                 ha='center', va='top', fontsize=7, linespacing=0.9)
        ax_mid.set_xlabel('')

    # Config Y
    # Ajuste de eixos considerando o deslocamento
    y_vals = [v + CONFIG.get('Y_SHIFT', 0) for v in CONFIG['Y_POS'].values()]
    ax.set_yticks(y_vals)
    ax.set_yticklabels([])
    ax.set_ylim(min(y_vals) - 1, max(y_vals) + 1)

    # Grade maior (hora em hora) – linha contínua
    ax.grid(True, axis='x', linestyle='-', alpha=0.3, zorder=0, which='major')

    # Sublinhas a cada 15min
    sub_int = CONFIG.get('SUB_TICK_INTERVAL_MIN', 15)
    ax.xaxis.set_minor_locator(MultipleLocator(sub_int))
    # Oculta marcas/ticks menores; mantém apenas a grade
    ax.tick_params(axis='x', which='minor', length=0, labelbottom=False)
    # Grade menor (15 min) – tracejada
    ax.grid(True, axis='x', which='minor', linestyle='--', alpha=CONFIG.get('SUB_TICK_ALPHA', 0.4), zorder=0)

    # Legenda (horizontal)
    # Adiciona contorno preto a todos os patches da legenda –
    # facilita visualizar a cor branca ("Falta de Informação")
    legend_elems = [
        Patch(
            facecolor=c,
            edgecolor='black',      # contorno visível
            linewidth=0.8,
            label=t
        )
        for t, c in CONFIG['COLORS'].items()
    ]
    legend_y = CONFIG.get('LEGEND_Y', 1.08)
    ax.legend(handles=legend_elems, loc='upper center', bbox_to_anchor=(0.5, legend_y),
              ncol=len(legend_elems), frameon=False, fontsize=9)

    # Título: somente o equipamento (frota)
    title_txt = str(equipamento) if equipamento else ''

    ax.set_title(title_txt, fontweight='bold', pad=25)

    plt.tight_layout()

    if salvar_png:
        os.makedirs(CONFIG['OUTPUT_DIR'], exist_ok=True)
        fname = f"gantt_{equipamento or 'ALL'}_{data or 'all'}.png".replace('/', '-')
        plt.savefig(os.path.join(CONFIG['OUTPUT_DIR'], fname), dpi=300, bbox_inches='tight')
        print('Gráfico salvo em', os.path.join(CONFIG['OUTPUT_DIR'], fname))

    if exibir:
        plt.show()
    else:
        plt.close(fig)

# ====================================================================================
# FUNÇÃO PARA INTEGRAÇÃO COM SUPABASE - CHAMADA PELO FLUXO DE RELATÓRIOS
# ====================================================================================

def gerar_graficos_intervalos_para_relatorio(xlsx_file_path, report_id):
    """
    Função chamada pelo fluxo de relatórios para gerar gráficos de intervalos de um XLSX
    e fazer upload dos URLs para o Supabase no mesmo campo dos mapas.
    
    Args:
        xlsx_file_path: Caminho para o arquivo XLSX processado com planilha 'Intervalos'
        report_id: ID do relatório no Supabase para vincular os gráficos
    
    Returns:
        List[str]: Lista de URLs dos gráficos gerados
    """
    try:
        print(f"\n📊 === GERAÇÃO DE GRÁFICOS DE INTERVALOS PARA RELATÓRIO {report_id} ===")
        print(f"📁 Arquivo XLSX: {os.path.basename(xlsx_file_path)}")
        
        # Verificar se arquivo existe
        if not os.path.exists(xlsx_file_path):
            print(f"❌ Arquivo XLSX não encontrado: {xlsx_file_path}")
            return []
        
        # Tentar ler planilha 'Intervalos'
        try:
            df = pd.read_excel(xlsx_file_path, sheet_name='Intervalos')
            print(f"✅ Planilha 'Intervalos' carregada: {len(df)} registros")
        except Exception as e:
            print(f"❌ Erro ao ler planilha 'Intervalos': {e}")
            return []
        
        if df.empty:
            print(f"⚠️ Planilha 'Intervalos' está vazia")
            return []
        
        # Preparar diretório de gráficos
        graficos_dir = CONFIG['OUTPUT_DIR']
        os.makedirs(graficos_dir, exist_ok=True)
        
        # Lista para armazenar URLs dos gráficos
        urls_graficos = []
        
        # Configurar sistema de upload
        try:
            from app.database.supabase_client import create_admin_client
            admin_client = create_admin_client()
        except ImportError:
            # Fallback para estrutura de imports alternativos
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from app.database.supabase_client import create_admin_client
            admin_client = create_admin_client()
        
        BUCKET_NAME = 'mapas'
        SUBFOLDER = 'intervalos'
        SUPA_URL = os.environ.get('SUPABASE_URL', 'https://kjlwqezxzqjfhacmjhbh.supabase.co')
        
        def _upload_grafico_png(caminho_local: str, nome_arquivo: str):
            """Faz upload de um PNG de gráfico para o Supabase storage."""
            try:
                if not os.path.exists(caminho_local):
                    print(f"❌ Arquivo não encontrado: {caminho_local}")
                    return None
                
                storage_path = f"{SUBFOLDER}/{nome_arquivo}"
                
                # Ler arquivo
                with open(caminho_local, 'rb') as f:
                    data = f.read()
                
                # Criar bucket se necessário
                try:
                    buckets = admin_client.storage.list_buckets()
                    if not any(b.get('name') == BUCKET_NAME for b in buckets):
                        admin_client.storage.create_bucket(BUCKET_NAME, {'public': True})
                except Exception:
                    pass
                
                # Upload
                admin_client.storage.from_(BUCKET_NAME).upload(
                    storage_path, data, {
                        "contentType": "image/png",
                        "upsert": "true"
                    }
                )
                
                # Construir URL pública
                url = admin_client.storage.from_(BUCKET_NAME).get_public_url(storage_path)
                if not url:
                    url = f"{SUPA_URL}/storage/v1/object/public/{BUCKET_NAME}/{storage_path}"
                
                print(f"✅ Upload gráfico concluído: {nome_arquivo} -> {url}")
                return url
            except Exception as e:
                print(f"❌ Falha no upload de {nome_arquivo}: {e}")
                return None
        
        # Gerar gráfico para cada equipamento
        equipamentos = df['Equipamento'].unique()
        print(f"📈 Gerando gráficos para {len(equipamentos)} equipamento(s): {list(equipamentos)}")
        
        for equipamento in equipamentos:
            try:
                # Filtrar dados do equipamento
                df_equip = df[df['Equipamento'] == equipamento]
                
                # Determinar data (se disponível)
                data = None
                if 'Data' in df_equip.columns and not df_equip['Data'].empty:
                    data_values = df_equip['Data'].dropna().unique()
                    if len(data_values) > 0:
                        data = str(data_values[0])
                
                # Gerar nome do arquivo
                data_str = data.replace('/', '-') if data else 'all'
                nome_arquivo = f"gantt_{equipamento}_{data_str}.png"
                caminho_completo = os.path.join(graficos_dir, nome_arquivo)
                
                print(f"  📊 Gerando gráfico para equipamento {equipamento}...")
                
                # Gerar gráfico sem exibir (exibir=False) e salvar
                plot_gantt(df, equipamento=equipamento, data=data, salvar_png=True, exibir=False)
                
                # Verificar se arquivo foi gerado e fazer upload
                if os.path.exists(caminho_completo):
                    url_grafico = _upload_grafico_png(caminho_completo, nome_arquivo)
                    if url_grafico:
                        urls_graficos.append(url_grafico)
                        print(f"  ✅ Gráfico gerado e enviado: {nome_arquivo}")
                    else:
                        print(f"  ⚠️ Falha no upload do gráfico para {equipamento}")
                else:
                    print(f"  ⚠️ Gráfico não foi gerado para {equipamento}")
                    
            except Exception as e:
                print(f"  ❌ Erro ao gerar gráfico para equipamento {equipamento}: {e}")
                continue
        
        if not urls_graficos:
            print(f"❌ Nenhum gráfico foi gerado com sucesso")
            return []
        
        print(f"✅ Total de gráficos gerados: {len(urls_graficos)}")
        return urls_graficos
        
    except Exception as e:
        print(f"❌ Erro geral na geração de gráficos: {e}")
        return []

def atualizar_urls_graficos_no_supabase(report_id, urls_graficos):
    """
    Atualiza o campo url_mapa no Supabase adicionando os gráficos no container 'intervalos'.
    Preserva os dados existentes de outros containers.
    
    Args:
        report_id: ID do relatório no Supabase
        urls_graficos: Lista de URLs dos gráficos gerados
    
    Returns:
        bool: True se sucesso, False se erro
    """
    try:
        try:
            from app.database.supabase_client import create_admin_client
            admin_client = create_admin_client()
        except ImportError:
            # Fallback para estrutura de imports alternativos
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from app.database.supabase_client import create_admin_client
            admin_client = create_admin_client()
        
        # Primeiro, buscar dados existentes do relatório
        resultado_busca = admin_client.table('relatorios_diarios').select('url_mapa').eq('id', report_id).execute()
        
        if not resultado_busca.data:
            print(f"❌ Relatório {report_id} não encontrado no Supabase")
            return False
        
        # Obter dados existentes de url_mapa ou criar objeto vazio
        url_mapa_atual = resultado_busca.data[0].get('url_mapa', {})
        if url_mapa_atual is None:
            url_mapa_atual = {}
        
        # Adicionar container de intervalos preservando outros containers
        url_mapa_atual['intervalos'] = urls_graficos
        
        # Preparar dados para atualização
        update_data = {
            'url_mapa': url_mapa_atual
        }
        
        # Atualizar no Supabase
        resultado = admin_client.table('relatorios_diarios').update(update_data).eq('id', report_id).execute()
        
        if resultado.data:
            print(f"✅ URLs dos gráficos atualizados no Supabase para relatório {report_id}")
            print(f"📊 Container intervalos criado com {len(urls_graficos)} arquivo(s)")
            for i, url in enumerate(urls_graficos, 1):
                print(f"  intervalos[{i-1}]: {url}")
            return True
        else:
            print(f"❌ Falha ao atualizar URLs dos gráficos no Supabase")
            return False

    except Exception as e:
        print(f"❌ Erro ao atualizar Supabase com gráficos: {e}")
        return False

# ----------------------------------------------------------------------------
# Leitura de arquivo Excel
# ----------------------------------------------------------------------------

# --------------------------------------------
def processar_arquivo_excel(caminho: str, exibir: bool = True):
    """Lê planilha 'Intervalos' do arquivo e gera gráficos por equipamento."""
    df = pd.read_excel(caminho, sheet_name='Intervalos')
    equipamentos = df['Equipamento'].unique()
    for eq in equipamentos:
        datas = df[df['Equipamento'] == eq]['Data'].unique() if 'Data' in df.columns else [None]
        for d in datas:
            plot_gantt(df, equipamento=eq, data=d, exibir=exibir)

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main():
    output_dir = 'output'
    arquivos = glob.glob(os.path.join(output_dir, '*_processado.xlsx'))
    if not arquivos:
        print('Nenhum arquivo encontrado em output/*.xlsx')
        return
    ver_previa = CONFIG.get('VER_PREVIA', False)
    for arq in arquivos:
        print('Processando', arq)
        processar_arquivo_excel(arq, exibir=ver_previa)

if __name__ == '__main__':
    main() 