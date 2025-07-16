import os
import glob
from datetime import datetime
from typing import List, Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ====================================================================
# BLOCO DE CONFIGURAÇÃO – altere aqui o layout como desejar
# ====================================================================
CONFIG = {
    # Tamanho da figura (largura, altura)
    # Altura foi reduzida para 1/3 da original (original ≈ 8)
    'FIG_SIZE': (16, 8 /2),

    # Altura das barras horizontais no gráfico de Gantt
    # Original = 0.6 → agora 1/3
    'BAR_HEIGHT': 0.6 / 2,

    # Cores das barras por tipo de intervalo
    'COLORS': {
        'Produtivo': '#51CF66',   # Verde
        'Disponível': '#74C0FC', # Azul claro
        'Manutenção': '#FF6B6B'  # Vermelho
    },

    # Posições verticais (y) das barras
    'Y_POS': {
        'Produtivo': 1,   # Linha superior
        'Disponível': 0,  # Linha central
        'Manutenção': -1  # Linha inferior
    },

    # Intervalo entre marcas principais da régua inferior (em horas)
    'MAIN_TICK_INTERVAL_H': 1,

    # Formato do rótulo da régua inferior
    'MAIN_TICK_LABEL_FMT': '{:02d}',

    # Rotação dos rótulos da régua superior (início/fim de manutenções)
    'TOP_TICK_ROTATION': 0,

    # Offset vertical (pt) da régua de manutenção; valor negativo aproxima da barra
    'MAINT_TICK_OFFSET_PT': -50,

    # Transforma durações maiores que este limiar (min) em texto dentro da barra
    'LABEL_THRESHOLD_MIN': 60,

    # Diretório onde os gráficos serão salvos
    'OUTPUT_DIR': os.path.join('output', 'graficos')
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

    if df_plot.empty:
        print('Sem dados para plotar.')
        return

    # Conversões
    df_plot['inicio_min'] = df_plot['Início'].apply(hora_str_para_minutos)
    df_plot['duracao_min'] = df_plot['Duração (horas)'] * 60

    # Figura
    fig, ax = plt.subplots(figsize=CONFIG['FIG_SIZE'])

    # Barras
    for _, row in df_plot.iterrows():
        tipo = row['Tipo']
        cor = CONFIG['COLORS'].get(tipo, '#808080')
        y = CONFIG['Y_POS'].get(tipo, 0)
        ax.barh(y, row['duracao_min'], left=row['inicio_min'], height=CONFIG['BAR_HEIGHT'],
                 color=cor, edgecolor='black', linewidth=0.4, alpha=0.9, zorder=3)
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
        V_OFFSET_PT = -10           # deslocamento vertical entre labels (pontos)

        # Estrutura para formar clusters de posições próximas
        pontos = []  # (pos, label)
        for _, r in manut.iterrows():
            ini = r['inicio_min']
            fim = r['inicio_min'] + r['duracao_min']
            ini_str = f"{int(ini//60):02d}:{int(ini%60):02d}"
            fim_str = f"{int(fim//60):02d}:{int(fim%60):02d}"
            if r['duracao_min'] < 60:
                pontos.append((ini, f"{ini_str}\n{fim_str}"))
            else:
                pontos.extend([(ini, ini_str), (fim, fim_str)])

        # Ordenar por posição
        pontos = sorted(pontos, key=lambda x: x[0])

        # Criar clusters
        clusters: List[List[tuple]] = []
        for pos, lbl in pontos:
            if not clusters or pos - clusters[-1][-1][0] > OVERLAP_THRESHOLD_MIN:
                clusters.append([(pos, lbl)])
            else:
                clusters[-1].append((pos, lbl))

        # Desenhar ticks e anotações sem label na própria tick para evitar sobreposição
        ax_mid.set_xticks([p for p, _ in pontos])
        ax_mid.set_xticklabels([''] * len(pontos))

        for cluster in clusters:
            for idx, (pos, lbl) in enumerate(cluster):
                # Offset vertical por índice dentro do cluster
                offset = idx * V_OFFSET_PT
                ax_mid.annotate(lbl,
                                 xy=(pos, 0),
                                 xycoords=('data', 'axes fraction'),
                                 xytext=(0, offset),
                                 textcoords='offset points',
                                 ha='center', va='top', fontsize=7, linespacing=0.9)
        ax_mid.set_xlabel('')

    # Config Y
    ax.set_yticks(list(CONFIG['Y_POS'].values()))
    ax.set_yticklabels([])  # Remove textos laterais
    ax.set_ylim(min(CONFIG['Y_POS'].values()) - 1, max(CONFIG['Y_POS'].values()) + 1)

    # Grade
    ax.grid(True, axis='x', linestyle='--', alpha=0.3, zorder=0)

    # Legenda (horizontal)
    legend_elems = [Patch(facecolor=c, label=t) for t, c in CONFIG['COLORS'].items()]
    ax.legend(handles=legend_elems, loc='upper center', bbox_to_anchor=(0.5, 1.08),
              ncol=len(legend_elems), frameon=False, fontsize=9)

    # Título personalizado
    title_parts = ['Linha do Tempo Operacional']
    if equipamento: title_parts.append(str(equipamento))
    if data: title_parts.append(str(data))
    ax.set_title(' | '.join(title_parts), fontweight='bold', pad=15)

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
    for arq in arquivos:
        print('Processando', arq)
        processar_arquivo_excel(arq)

if __name__ == '__main__':
    main() 