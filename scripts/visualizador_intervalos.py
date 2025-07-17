import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
import os
import glob

def converter_hora_para_minutos(hora_str):
    """
    Converte string de hora (HH:MM:SS) para minutos desde 00:00:00
    
    Args:
        hora_str (str): Hora no formato HH:MM:SS
    
    Returns:
        float: Minutos desde 00:00:00
    """
    try:
        if pd.isna(hora_str) or hora_str == "" or hora_str == "N/A":
            return 0
        
        # Remover espaços e converter para string se necessário
        hora_str = str(hora_str).strip()
        
        # Dividir a hora em componentes
        partes = hora_str.split(':')
        if len(partes) >= 3:
            horas = int(partes[0])
            minutos = int(partes[1])
            segundos = int(partes[2])
        elif len(partes) == 2:
            horas = int(partes[0])
            minutos = int(partes[1])
            segundos = 0
        else:
            return 0
        
        # Converter para minutos totais
        total_minutos = horas * 60 + minutos + segundos / 60
        return total_minutos
    
    except Exception as e:
        print(f"Erro ao converter hora '{hora_str}': {e}")
        return 0

def criar_grafico_gantt(df_intervalos, equipamento=None, data=None, salvar_arquivo=True):
    """
    Cria um gráfico de Gantt dos intervalos operacionais
    
    Args:
        df_intervalos (DataFrame): DataFrame com os intervalos
        equipamento (str, optional): Filtrar por equipamento específico
        data (str, optional): Filtrar por data específica
        salvar_arquivo (bool): Se deve salvar o arquivo
    
    Returns:
        None: Exibe o gráfico
    """
    # Filtrar dados se necessário
    df_plot = df_intervalos.copy()
    
    if equipamento:
        df_plot = df_plot[df_plot['Equipamento'] == equipamento]
    
    if data:
        df_plot = df_plot[df_plot['Data'] == data]
    
    if len(df_plot) == 0:
        print("Nenhum dado encontrado para os filtros especificados.")
        return
    
    # Converter horários para minutos
    df_plot['Inicio_min'] = df_plot['Início'].apply(converter_hora_para_minutos)
    df_plot['Fim_min'] = df_plot['Fim'].apply(converter_hora_para_minutos)
    df_plot['Duracao_min'] = df_plot['Duração (horas)'] * 60
    
    # Definir cores e posições Y para cada tipo
    cores = {
        'Manutenção': '#FF6B6B',    # Vermelho
        'Disponível': '#74C0FC',    # Azul claro
        'Produtivo': '#51CF66'      # Verde
    }
    
    posicoes_y = {
        'Manutenção': -1,    # Abaixo
        'Disponível': 0,     # Centro
        'Produtivo': 1       # Acima
    }
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Plotar cada intervalo
    for idx, row in df_plot.iterrows():
        tipo = row['Tipo']
        inicio = row['Inicio_min']
        duracao = row['Duracao_min']
        y_pos = posicoes_y.get(tipo, 0)
        cor = cores.get(tipo, '#808080')
        
        # Criar barra horizontal
        ax.barh(y_pos, duracao, left=inicio, height=0.6, 
                color=cor, alpha=0.8, edgecolor='black', linewidth=0.5)
        
        # Adicionar texto com duração se a barra for grande o suficiente
        if duracao > 60:  # Só mostrar texto se duração > 1 hora
            ax.text(inicio + duracao/2, y_pos, f'{duracao/60:.1f}h', 
                   ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Configurar eixos
    ax.set_xlim(0, 24*60)  # 24 horas em minutos
    ax.set_ylim(-1.5, 1.5)
    
    # Configurar eixo X (tempo)
    horas = np.arange(0, 25, 2)  # A cada 2 horas
    minutos_ticks = horas * 60
    labels_horas = [f'{int(h):02d}:00' for h in horas]
    ax.set_xticks(minutos_ticks)
    ax.set_xticklabels(labels_horas)
    ax.set_xlabel('Horário', fontsize=12, fontweight='bold')
    
    # Configurar eixo Y (tipos)
    ax.set_yticks([-1, 0, 1])
    ax.set_yticklabels(['Manutenção', 'Disponível', 'Produtivo'], fontsize=12)
    ax.set_ylabel('Tipo de Operação', fontsize=12, fontweight='bold')
    
    # Adicionar grade
    ax.grid(True, axis='x', alpha=0.3, linestyle='--')
    ax.grid(True, axis='y', alpha=0.3, linestyle='-')
    
    # Título
    titulo = f'Gráfico de Gantt - Intervalos Operacionais'
    if equipamento:
        titulo += f' - {equipamento}'
    if data:
        titulo += f' - {data}'
    
    ax.set_title(titulo, fontsize=14, fontweight='bold', pad=20)
    
    # Legenda
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=cores['Produtivo'], label='Produtivo'),
        Patch(facecolor=cores['Disponível'], label='Disponível'), 
        Patch(facecolor=cores['Manutenção'], label='Manutenção')
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1))
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar arquivo se solicitado
    if salvar_arquivo:
        diretorio_graficos = os.path.join(os.path.dirname(__file__), '..', 'output', 'graficos')
        if not os.path.exists(diretorio_graficos):
            os.makedirs(diretorio_graficos)
        
        nome_arquivo = f'gantt_intervalos'
        if equipamento:
            nome_arquivo += f'_{equipamento}'
        if data:
            nome_arquivo += f'_{data.replace("/", "-")}'
        nome_arquivo += '.png'
        
        caminho_arquivo = os.path.join(diretorio_graficos, nome_arquivo)
        plt.savefig(caminho_arquivo, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo em: {caminho_arquivo}")
    
    # Exibir gráfico
    plt.show()

def processar_planilha_intervalos(caminho_excel):
    """
    Lê a planilha de Intervalos de um arquivo Excel e cria o gráfico
    
    Args:
        caminho_excel (str): Caminho para o arquivo Excel
    """
    try:
        # Ler planilha de Intervalos
        df_intervalos = pd.read_excel(caminho_excel, sheet_name='Intervalos')
        
        print(f"Planilha carregada: {len(df_intervalos)} intervalos encontrados")
        print(f"Equipamentos: {df_intervalos['Equipamento'].unique()}")
        
        # Verificar se há coluna Data
        if 'Data' in df_intervalos.columns:
            print(f"Datas: {df_intervalos['Data'].unique()}")
        
        # Criar gráfico para cada equipamento
        for equipamento in df_intervalos['Equipamento'].unique():
            print(f"\nCriando gráfico para {equipamento}...")
            
            # Se há múltiplas datas, criar um gráfico por data
            if 'Data' in df_intervalos.columns:
                datas = df_intervalos[df_intervalos['Equipamento'] == equipamento]['Data'].unique()
                for data in datas:
                    print(f"  Data: {data}")
                    criar_grafico_gantt(df_intervalos, equipamento=equipamento, data=data)
            else:
                criar_grafico_gantt(df_intervalos, equipamento=equipamento)
    
    except Exception as e:
        print(f"Erro ao processar planilha: {e}")

def main():
    """
    Função principal - processa todos os arquivos Excel na pasta output
    """
    print("=== VISUALIZADOR DE INTERVALOS OPERACIONAIS ===")
    print("Criando gráficos de Gantt a partir das planilhas de Intervalos")
    print("="*60)
    
    # Diretório de saída
    diretorio_output = os.path.join(os.path.dirname(__file__), '..', 'output')
    
    # Encontrar arquivos Excel processados
    arquivos_excel = glob.glob(os.path.join(diretorio_output, "*_processado.xlsx"))
    
    if not arquivos_excel:
        print("Nenhum arquivo Excel processado encontrado na pasta output/")
        return
    
    print(f"Encontrados {len(arquivos_excel)} arquivos para processar:")
    for arquivo in arquivos_excel:
        print(f"  - {os.path.basename(arquivo)}")
    
    # Processar cada arquivo
    for arquivo in arquivos_excel:
        print(f"\n{'='*60}")
        print(f"Processando: {os.path.basename(arquivo)}")
        print(f"{'='*60}")
        
        try:
            processar_planilha_intervalos(arquivo)
        except Exception as e:
            print(f"Erro ao processar {arquivo}: {e}")
    
    print(f"\n{'='*60}")
    print("Processamento concluído!")
    print("Gráficos salvos na pasta: output/graficos/")
    print("="*60)

if __name__ == "__main__":
    main() 