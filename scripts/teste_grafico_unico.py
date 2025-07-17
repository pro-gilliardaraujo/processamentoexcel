import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def converter_hora_para_minutos(hora_str):
    """
    Converte string de hora (HH:MM:SS) para minutos desde 00:00:00
    """
    try:
        if pd.isna(hora_str) or hora_str == "" or hora_str == "N/A":
            return 0
        
        hora_str = str(hora_str).strip()
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
        
        total_minutos = horas * 60 + minutos + segundos / 60
        return total_minutos
    
    except Exception as e:
        print(f"Erro ao converter hora '{hora_str}': {e}")
        return 0

def criar_grafico_gantt_equipamento(caminho_excel, equipamento_nome):
    """
    Cria um gráfico de Gantt para um equipamento específico
    """
    try:
        # Ler planilha de Intervalos
        df_intervalos = pd.read_excel(caminho_excel, sheet_name='Intervalos')
        
        # Filtrar por equipamento
        df_equip = df_intervalos[df_intervalos['Equipamento'] == equipamento_nome]
        
        if len(df_equip) == 0:
            print(f"Equipamento {equipamento_nome} não encontrado")
            return
        
        print(f"Equipamento {equipamento_nome}: {len(df_equip)} intervalos encontrados")
        
        # Converter horários para minutos
        df_equip['Inicio_min'] = df_equip['Início'].apply(converter_hora_para_minutos)
        df_equip['Fim_min'] = df_equip['Fim'].apply(converter_hora_para_minutos)
        df_equip['Duracao_min'] = df_equip['Duração (horas)'] * 60
        
        # Configurar cores e posições
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
        plt.figure(figsize=(16, 8))
        ax = plt.gca()
        
        # Plotar cada intervalo
        for idx, row in df_equip.iterrows():
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
        ax.set_title(f'Gráfico de Gantt - Intervalos Operacionais - {equipamento_nome}', 
                     fontsize=14, fontweight='bold', pad=20)
        
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
        
        # Salvar gráfico
        nome_arquivo = f'gantt_{equipamento_nome}_teste.png'
        plt.savefig(nome_arquivo, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo como: {nome_arquivo}")
        
        # Exibir gráfico
        plt.show()
        
    except Exception as e:
        print(f"Erro: {e}")

# Teste com o primeiro arquivo
caminho_teste = 'output/colhedorasFrente03_15072025_processado.xlsx'
equipamento_teste = 7042

print("Testando gráfico de Gantt...")
criar_grafico_gantt_equipamento(caminho_teste, equipamento_teste) 