import pandas as pd
from datetime import timedelta
import matplotlib.pyplot as plt
import os
from datetime import datetime
import matplotlib.patches as mpatches
import numpy as np
import zipfile
import tempfile
import re

def encontrar_arquivos_zip_monit(pasta_dados):
    """
    Encontra arquivos ZIP que contenham 'monit' no nome.
    """
    arquivos_zip = []
    for arquivo in os.listdir(pasta_dados):
        if 'monit' in arquivo.lower() and arquivo.endswith('.zip'):
            arquivos_zip.append(os.path.join(pasta_dados, arquivo))
    return arquivos_zip

def corrigir_encoding_colunas(df):
    """
    Corrige problemas de encoding em colunas de texto, especialmente
    para palavras com 'ã' e 'ç' que podem aparecer como 'Ã£' e 'Ã§'.
    """
    print("Corrigindo problemas de encoding nos dados...")
    
    # Lista de colunas de texto para verificar
    colunas_texto = ['Grupo Operacao', 'Grupo', 'Estado', 'Equipamento']
    colunas_para_verificar = [col for col in colunas_texto if col in df.columns]
    
    # Mapeamento de correções específicas
    correcoes = {
        r'ManutenÃ§Ã£o': 'Manutenção',
        r'InaptidÃ£o': 'Inaptidão',
        r'AutomaÃ§Ã£o': 'Automação',
        r'OperaÃ§Ã£o': 'Operação',
        r'ManutencÃ£o': 'Manutenção'
    }
    
    # Padrões genéricos para detectar problemas comuns
    padroes_genericos = [
        (r'Ã§Ã£o\b', 'ção'),  # final "ção"
        (r'Ã£o\b', 'ão'),     # final "ão"
        (r'Ã§', 'ç'),         # "ç" isolado
        (r'Ã£', 'ã')          # "ã" isolado
    ]
    
    # Aplicar correções nas colunas de texto
    for coluna in colunas_para_verificar:
        # Primeiro aplicar correções específicas
        for padrao, correcao in correcoes.items():
            df[coluna] = df[coluna].astype(str).str.replace(padrao, correcao, regex=True)
        
        # Depois aplicar padrões genéricos
        for padrao, correcao in padroes_genericos:
            df[coluna] = df[coluna].astype(str).str.replace(padrao, correcao, regex=True)
    
    print("Correção de encoding concluída.")
    return df

def processar_csv_do_zip(arquivo_zip):
    """
    Extrai e processa os arquivos CSV de dentro do ZIP.
    """
    print(f"\nProcessando arquivo ZIP: {arquivo_zip}")
    dfs = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
            # Listar todos os arquivos no ZIP
            arquivos_csv = [f for f in zip_ref.namelist() if f.lower().endswith('.csv') or f.lower().endswith('.txt')]
            print(f"Arquivos CSV/TXT encontrados no ZIP: {len(arquivos_csv)}")
            
            if not arquivos_csv:
                print("Nenhum arquivo CSV/TXT encontrado no ZIP.")
                return None
                
            for csv_file in arquivos_csv:
                print(f"\nExtraindo e processando: {csv_file}")
                zip_ref.extract(csv_file, temp_dir)
                
                # Ler o CSV
                caminho_csv = os.path.join(temp_dir, csv_file)
                try:
                    # Tentar diferentes encodings se necessário
                    encodings = ['latin1', 'utf-8', 'cp1252']
                    df = None
                    
                    for encoding in encodings:
                        try:
                            df = pd.read_csv(caminho_csv, sep=';', encoding=encoding)
                            print(f"Arquivo lido com sucesso usando encoding {encoding}: {len(df)} linhas")
                            break
                        except UnicodeDecodeError:
                            print(f"Erro de decodificação com encoding {encoding}, tentando outro...")
                        except Exception as e:
                            print(f"Erro ao ler com encoding {encoding}: {str(e)}")
                    
                    if df is None:
                        print(f"Não foi possível ler o arquivo com nenhum encoding.")
                        continue
                    
                    # Aplicar correções de encoding
                    df = corrigir_encoding_colunas(df)
                    
                    # Converter Data/Hora para datetime e separar em duas colunas
                    if 'Data/Hora' in df.columns:
                        try:
                            # Converter para datetime
                            df['Data/Hora'] = pd.to_datetime(df['Data/Hora'], format='%d/%m/%Y %H:%M:%S')
                        except ValueError:
                            try:
                                df['Data/Hora'] = pd.to_datetime(df['Data/Hora'], format='%d/%m/%Y %H:%M')
                            except ValueError as e:
                                print(f"Erro ao converter datas: {str(e)}")
                                print("Tentando inferir formato...")
                                df['Data/Hora'] = pd.to_datetime(df['Data/Hora'])
                    
                    # Ordenar por Equipamento e Data/Hora
                    if 'Equipamento' in df.columns and 'Data/Hora' in df.columns:
                        df = df.sort_values(['Equipamento', 'Data/Hora']).reset_index(drop=True)
                        print("Dados ordenados por Equipamento e Data/Hora")
                    
                    dfs.append(df)
                    print(f"Arquivo processado e adicionado ao conjunto de dados")
                except Exception as e:
                    print(f"Erro ao processar {csv_file}: {str(e)}")
                    continue
    
    if dfs:
        # Concatenar todos os DataFrames
        df_final = pd.concat(dfs, ignore_index=True)
        print(f"\nTotal de registros após concatenação: {len(df_final)}")
        
        # Ordenar novamente após a concatenação
        if 'Equipamento' in df_final.columns and 'Data/Hora' in df_final.columns:
            df_final = df_final.sort_values(['Equipamento', 'Data/Hora']).reset_index(drop=True)
            print("Dados finais ordenados por Equipamento e Data/Hora")
        
        return df_final
    return None

def main():
    print("\nIniciando processamento MTBF e MTTR...")
    
    # Obter diretório de dados
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(script_dir)
    dados_dir = os.path.join(workspace_dir, "dados")
    output_dir = os.path.join(workspace_dir, "output")
    
    # Criar diretório de saída se não existir
    os.makedirs(output_dir, exist_ok=True)
    
    # Encontrar arquivos ZIP de monitoramento
    arquivos_zip = encontrar_arquivos_zip_monit(dados_dir)
    
    if not arquivos_zip:
        print("Nenhum arquivo ZIP de monitoramento encontrado!")
        return
    
    print(f"Arquivos ZIP encontrados: {len(arquivos_zip)}")
    
    # Processar cada arquivo ZIP
    for arquivo_zip in arquivos_zip:
        try:
            # Processar o ZIP
            df = processar_csv_do_zip(arquivo_zip)
            
            if df is not None:
                print(f"Processando arquivo: {arquivo_zip}")
                processar_mtbf_mttr(df, output_dir, arquivo_zip)
            else:
                print(f"Nenhum dado válido encontrado em: {arquivo_zip}")
        
        except Exception as e:
            print(f"Erro ao processar {arquivo_zip}: {str(e)}")
            continue

def processar_mtbf_mttr(df, output_dir, arquivo_zip):
    # Converter a coluna Data/Hora para datetime já foi feita na importação
    # Ordenar por Equipamento, Grupo Operacao e Data/Hora
    if 'Grupo Operacao' not in df.columns and 'Grupo' in df.columns:
        df['Grupo Operacao'] = df['Grupo']
    
    df = df.sort_values(by=['Equipamento', 'Grupo Operacao', 'Data/Hora']).reset_index(drop=True)

    resultados = []
    seq_id = 1

    # Percorrer por equipamento
    for equipamento, df_equip in df.groupby('Equipamento'):
        df_equip = df_equip.sort_values(by=['Data/Hora']).reset_index(drop=True)
        grupo_atual = None
        inicio_seq = None
        fim_seq = None
        grupo_operacao_atual = None
        for idx, linha in df_equip.iterrows():
            grupo_operacao = linha['Grupo Operacao']
            data_hora = linha['Data/Hora']
            if grupo_operacao != grupo_operacao_atual:
                # Se não é a primeira, salva a sequência anterior
                if grupo_operacao_atual is not None:
                    duracao = (fim_seq - inicio_seq).total_seconds() / 60
                    resultados.append({
                        'Nº Sequência': seq_id,
                        'Equipamento': equipamento,
                        'Grupo Operacao': grupo_operacao_atual,
                        'Início': inicio_seq,
                        'Fim': fim_seq,
                        'Duração (minutos)': round(duracao, 2)
                    })
                    seq_id += 1
                # Inicia nova sequência
                grupo_operacao_atual = grupo_operacao
                inicio_seq = data_hora
            fim_seq = data_hora
        # Salva a última sequência do equipamento
        if grupo_operacao_atual is not None:
            duracao = (fim_seq - inicio_seq).total_seconds() / 60
            resultados.append({
                'Nº Sequência': seq_id,
                'Equipamento': equipamento,
                'Grupo Operacao': grupo_operacao_atual,
                'Início': inicio_seq,
                'Fim': fim_seq,
                'Duração (minutos)': round(duracao, 2)
            })
            seq_id += 1

    # Gerar DataFrame com os resultados
    resultados_df = pd.DataFrame(resultados)
    
    if resultados_df.empty:
        print("Nenhum resultado gerado após processamento.")
        return

    # Formatar datas para o padrão brasileiro
    resultados_df['Início'] = resultados_df['Início'].dt.strftime('%d/%m/%Y %H:%M:%S')
    resultados_df['Fim'] = resultados_df['Fim'].dt.strftime('%d/%m/%Y %H:%M:%S')

    # Filtrar apenas sequências de MANUTENÇÃO (ignorando maiúsculas/minúsculas e espaços)
    # Ajustar para buscar também variações com problemas de encoding
    manutencao_filtro = resultados_df['Grupo Operacao'].str.upper().str.strip().isin([
        'MANUTENÇÃO', 'MANUTENCAO', 'MANUTENÇÃO', 'MANUTENÇAO'
    ])
    manutencao_df = resultados_df[manutencao_filtro]
    
    if manutencao_df.empty:
        print("Nenhuma sequência de MANUTENÇÃO encontrada nos dados.")
        return
    
    resultados_df = manutencao_df

    # Trocar a coluna de duração para horas (duas casas decimais)
    resultados_df['Duração (horas)'] = (
        pd.to_datetime(resultados_df['Fim'], format='%d/%m/%Y %H:%M:%S') -
        pd.to_datetime(resultados_df['Início'], format='%d/%m/%Y %H:%M:%S')
    ).dt.total_seconds() / 3600
    resultados_df['Duração (horas)'] = resultados_df['Duração (horas)'].round(2)

    # Corrigir a sequência
    resultados_df = resultados_df.reset_index(drop=True)
    resultados_df['Nº Sequência'] = resultados_df.index + 1

    # Selecionar e reordenar as colunas
    colunas = ['Nº Sequência', 'Equipamento', 'Grupo Operacao', 'Início', 'Fim', 'Duração (horas)']
    resultados_df = resultados_df[colunas]

    # Renomear colunas para padrão ABNT 2
    colunas_abnt = {
        'Nº Sequência': 'SEQUENCIA',
        'Equipamento': 'EQUIPAMENTO',
        'Grupo Operacao': 'GRUPO_OPERACAO',
        'Início': 'INICIO',
        'Fim': 'FIM',
        'Duração (horas)': 'DURACAO_HORAS'
    }
    resultados_df = resultados_df.rename(columns=colunas_abnt)

    # Gerar nome do arquivo de saída (mesmo nome do ZIP)
    nome_arquivo = os.path.basename(arquivo_zip)
    nome_base = os.path.splitext(nome_arquivo)[0]
    # Adicionar um timestamp ao nome do arquivo para evitar conflitos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Salvar o resultado em CSV na pasta de saída
    csv_output_path = os.path.join(output_dir, f"{nome_base}_resultado_manutencao_{timestamp}.csv")
    resultados_df.to_csv(csv_output_path, index=False, sep=';', decimal=',', encoding='utf-8')
    print(f"Arquivo de resultado salvo como '{csv_output_path}'")

    # Função para converter string de hora para minutos desde 00:00
    def hora_para_minutos(hora_str):
        return int(datetime.strptime(hora_str, '%d/%m/%Y %H:%M:%S').hour) * 60 + int(datetime.strptime(hora_str, '%d/%m/%Y %H:%M:%S').minute)

    # Geração dos gráficos individuais por equipamento (visual moderno)
    for equipamento, grupo in resultados_df.groupby('EQUIPAMENTO'):
        grupo = grupo.sort_values('INICIO')
        manutencoes = [
            (hora_para_minutos(row['INICIO']), hora_para_minutos(row['FIM']))
            for _, row in grupo.iterrows()
        ]
        livre = []
        inicio = 0
        for ini, fim in manutencoes:
            if ini > inicio:
                livre.append((inicio, ini))
            inicio = fim
        if inicio < 24*60:
            livre.append((inicio, 24*60))

        # Cálculo dos tempos e quantidades (deve estar dentro do loop)
        mtbf_duracoes = [(fim - ini) / 60 for ini, fim in livre if (fim - ini) > 0]
        mttr_duracoes = [(fim - ini) / 60 for ini, fim in manutencoes if (fim - ini) > 0]
        qtd_mtbf = len(mtbf_duracoes)
        media_mtbf = sum(mtbf_duracoes) / qtd_mtbf if qtd_mtbf > 0 else 0
        qtd_mttr = len(mttr_duracoes)
        media_mttr = sum(mttr_duracoes) / qtd_mttr if qtd_mttr > 0 else 0

        resumo_texto = (
            f"Tempo Médio Entre Quebras: {media_mtbf:.2f}h\n"
            f"Tempo Médio Para Reparo: {media_mttr:.2f}h\n"
            f"Quantidade de Quebras: {qtd_mtbf}"
        )

        fig, ax = plt.subplots(figsize=(16, 5))
        ax.set_facecolor('#f7f9fa')
        fig.patch.set_facecolor('#f7f9fa')

        # Alternância de posições para textos de duração
        y_texts_mtbf = [1.18, 1.28, 1.08, 1.38, 0.98]
        y_texts_mttr = [-1.18, -1.28, -1.08, -1.38, -0.98]
        last_x_mtbf = -999
        last_x_mttr = -999
        y_idx_mtbf = 0
        y_idx_mttr = 0

        # MTBF (verde)
        for ini, fim in livre:
            ax.hlines(1, ini, fim, color='#27ae60', linewidth=12, zorder=2, alpha=0.85)
            ax.fill_between([ini, fim], 0.85, 1.15, color='#27ae60', alpha=0.10, zorder=1)
            duracao_horas = (fim - ini) / 60
            x_centro = (ini + fim) / 2
            if duracao_horas > 0.01:
                if abs(x_centro - last_x_mtbf) < 80:
                    y_idx_mtbf = (y_idx_mtbf + 1) % len(y_texts_mtbf)
                else:
                    y_idx_mtbf = 0
                ax.text(x_centro, y_texts_mtbf[y_idx_mtbf], f'{duracao_horas:.2f}h', color='#27ae60', fontsize=10, ha='center', va='bottom',
                        fontweight='bold', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))
                last_x_mtbf = x_centro

        # MTTR (vermelho)
        for ini, fim in manutencoes:
            ax.hlines(-1, ini, fim, color='#e74c3c', linewidth=12, zorder=2, alpha=0.85)
            ax.fill_between([ini, fim], -1.15, -0.85, color='#e74c3c', alpha=0.10, zorder=1)
            duracao_horas = (fim - ini) / 60
            x_centro = (ini + fim) / 2
            if duracao_horas > 0.01:
                if abs(x_centro - last_x_mttr) < 80:
                    y_idx_mttr = (y_idx_mttr + 1) % len(y_texts_mttr)
                else:
                    y_idx_mttr = 0
                ax.text(x_centro, y_texts_mttr[y_idx_mttr], f'{duracao_horas:.2f}h', color='#222', fontsize=10, ha='center', va='top',
                        fontweight='bold', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))
                last_x_mttr = x_centro

        # Grid e eixos
        xticks = np.arange(0, 25) * 60
        ax.set_xticks(xticks)
        ax.set_xticklabels([str(int(x//60)) for x in xticks], fontsize=10, color='#444')
        ax.set_yticks([])
        ax.set_ylim(-1.7, 1.7)
        ax.set_xlim(0, 24*60)
        ax.set_title(f'Equipamento {equipamento} - Tempo Médio Disponivel e Manutenção', fontsize=14, pad=25, color='#222', fontweight='bold')
        ax.grid(axis='x', color='#d0d7de', linestyle='--', linewidth=1, alpha=0.7, zorder=0)
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Resumo em caixa destacada
        plt.tight_layout(rect=[0, 0, 0.93, 1])
        plt.subplots_adjust(bottom=0.45)

        # Resumo em caixa destacada
        ax.text(
            0.5, -0.30, resumo_texto,
            fontsize=10, color='#222', ha='center', va='top', fontweight='bold',
            transform=ax.transAxes, clip_on=False, linespacing=1.7,
            bbox=dict(facecolor='#eaf6f0', alpha=0.7, edgecolor='#27ae60', boxstyle='round,pad=0.5')
        )

        # Legenda customizada bem abaixo do resumo
        mtbf_patch = mpatches.Patch(color='#27ae60', label='Tempo Entre Quebras (MTBF)')
        mttr_patch = mpatches.Patch(color='#e74c3c', label='Tempo Para Reparo (MTTR)')
        ax.legend(
            handles=[mtbf_patch, mttr_patch],
            loc='lower center',
            bbox_to_anchor=(0.5, -0.999),  # bem abaixo do resumo
            ncol=2, fontsize=10, frameon=False
        )

        grafico_path = os.path.join(output_dir, f"{nome_base}_grafico_{equipamento}_{timestamp}.png")
        plt.savefig(grafico_path, dpi=120)
        plt.close()
        print(f'Gráfico salvo: {grafico_path}')

if __name__ == "__main__":
    print("=" * 60)
    print("PROCESSADOR DE MTBF E MTTR")
    print("=" * 60)
    main()
    print("\nProcessamento concluído!")
