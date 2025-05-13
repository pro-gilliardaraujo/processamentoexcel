#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
from datetime import datetime
import sys
import traceback

def processar_arquivo_csv(caminho_arquivo, caminho_saida=None):
    """
    Processa um arquivo CSV de manobras, calculando a diferença temporal entre registros consecutivos.
    
    Args:
        caminho_arquivo (str): Caminho do arquivo CSV a ser processado
        caminho_saida (str, opcional): Caminho do arquivo Excel de saída. Se não fornecido,
                                      será gerado um nome com base no arquivo de entrada.
    
    Returns:
        str: Caminho do arquivo Excel gerado
    """
    print(f"Processando arquivo: {caminho_arquivo}")
    print(f"O arquivo existe? {os.path.exists(caminho_arquivo)}")
    print(f"É um arquivo? {os.path.isfile(caminho_arquivo)}")
    print(f"Tamanho: {os.path.getsize(caminho_arquivo) if os.path.exists(caminho_arquivo) else 'N/A'} bytes")
    
    # Gerar caminho de saída se não fornecido
    if caminho_saida is None:
        diretorio = os.path.dirname(caminho_arquivo)
        nome_base = os.path.basename(caminho_arquivo).replace('.csv', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        caminho_saida = os.path.join(diretorio, f"{nome_base}_processado_{timestamp}.xlsx")
    
    print(f"Caminho de saída: {caminho_saida}")
    
    # Ler o arquivo CSV
    try:
        # Ler primeiramente apenas algumas linhas para diagnóstico
        print("\nTentando ler as primeiras 5 linhas para diagnóstico:")
        try:
            df_amostra = pd.read_csv(caminho_arquivo, sep=';', encoding='latin1', nrows=5)
            print("Leitura de amostra bem-sucedida!")
            print(f"Colunas disponíveis na amostra: {df_amostra.columns.tolist()}")
        except Exception as e:
            print(f"Erro ao ler amostra: {str(e)}")
            
            # Tentar outros separadores
            for sep in [',', '\t', '|']:
                try:
                    print(f"Tentando com separador '{sep}':")
                    df_amostra = pd.read_csv(caminho_arquivo, sep=sep, encoding='latin1', nrows=5)
                    if len(df_amostra.columns) > 1:
                        print(f"Separador '{sep}' funcionou! Número de colunas: {len(df_amostra.columns)}")
                        break
                except:
                    print(f"Separador '{sep}' falhou")
        
        # Agora ler o arquivo completo
        print("\nLendo arquivo completo:")
        df = pd.read_csv(caminho_arquivo, sep=';', encoding='latin1', low_memory=False)
        print(f"Arquivo lido com sucesso: {len(df)} linhas, {len(df.columns)} colunas")
        
        # Mostrar as primeiras linhas para verificação
        print("\nPrimeiras linhas do DataFrame:")
        print(df.head(3).to_string())
        
        # Mostrar informações sobre as colunas
        print("\nInformações sobre as colunas:")
        for col in df.columns:
            print(f"- {col}: {df[col].dtype}")
        
        # Verificar dados na coluna 'Data/Hora'
        if 'Data/Hora' in df.columns:
            print("\nExemplos de valores da coluna 'Data/Hora':")
            print(df['Data/Hora'].head(3).tolist())
            
            # Converter Data/Hora para datetime
            try:
                df['Data/Hora'] = pd.to_datetime(df['Data/Hora'], format='%d/%m/%Y %H:%M')
                print("Coluna 'Data/Hora' convertida para formato datetime")
            except Exception as e:
                print(f"Erro ao converter 'Data/Hora': {str(e)}")
                try:
                    # Tentar inferir formato
                    df['Data/Hora'] = pd.to_datetime(df['Data/Hora'])
                    print("Coluna 'Data/Hora' convertida usando formato inferido")
                except Exception as e:
                    print(f"Segunda tentativa falhou: {str(e)}")
                    print("A coluna 'Data/Hora' permanecerá como está")
        else:
            print("\nAVISO: Coluna 'Data/Hora' não encontrada!")
            similar_cols = [col for col in df.columns if 'data' in col.lower() or 'hora' in col.lower() or 'time' in col.lower() or 'date' in col.lower()]
            if similar_cols:
                print(f"Colunas similares encontradas: {similar_cols}")
        
        # Verificar e remover linhas vazias (todas as colunas vazias ou nulas)
        linhas_antes = len(df)
        df = df.dropna(how='all')
        print(f"\nLinhas removidas por estarem vazias: {linhas_antes - len(df)}")
        
        # Ordenar por Equipamento e Data/Hora (se disponível)
        colunas_ordenar = []
        if 'Equipamento' in df.columns:
            colunas_ordenar.append('Equipamento')
            # Verificar valores únicos de equipamento
            equips = df['Equipamento'].unique()
            print(f"Valores únicos de Equipamento (primeiros 10): {equips[:10]}")
        else:
            print("AVISO: Coluna 'Equipamento' não encontrada!")
            
        if 'Data/Hora' in df.columns:
            colunas_ordenar.append('Data/Hora')
        
        if colunas_ordenar:
            df = df.sort_values(by=colunas_ordenar).reset_index(drop=True)
            print(f"Dados ordenados por: {', '.join(colunas_ordenar)}")
        
        # Calcular diferença de tempo entre registros consecutivos (para o mesmo equipamento)
        if 'Equipamento' in df.columns and 'Data/Hora' in df.columns:
            # Verificar se Data/Hora está em formato datetime
            is_datetime = pd.api.types.is_datetime64_any_dtype(df['Data/Hora'])
            print(f"Coluna Data/Hora está em formato datetime? {is_datetime}")
            
            if is_datetime:
                # Inicializar coluna de diferença com zero
                df['Diferença_Hora'] = 0.0
                
                # Processar cada equipamento separadamente
                equipamentos = df['Equipamento'].unique()
                print(f"\nCalculando diferenças de tempo para {len(equipamentos)} equipamentos...")
                
                for i, equipamento in enumerate(equipamentos):
                    if i < 5 or i == len(equipamentos) - 1:  # Mostrar apenas os primeiros 5 e o último
                        print(f"Processando equipamento: {equipamento}")
                    elif i == 5:
                        print("... (mais equipamentos sendo processados)")
                    
                    if pd.isna(equipamento) or equipamento == '':
                        continue
                        
                    mask = df['Equipamento'] == equipamento
                    df_equip = df.loc[mask].copy()
                    
                    if len(df_equip) > 1:
                        # Calcular diferença em horas
                        df_equip['Diferença_Hora'] = df_equip['Data/Hora'].diff().dt.total_seconds() / 3600
                        # Substituir o resultado no DataFrame original
                        df.loc[mask, 'Diferença_Hora'] = df_equip['Diferença_Hora']
                        
                # Verificar valores extremos
                max_diff = df['Diferença_Hora'].max()
                avg_diff = df['Diferença_Hora'].mean()
                print(f"Diferença máxima: {max_diff:.2f} horas")
                print(f"Diferença média: {avg_diff:.2f} horas")
                
                # Mostrar alguns exemplos
                print("\nExemplos de registros com diferenças calculadas:")
                exemplo = df[df['Diferença_Hora'] > 0].head(3)
                if not exemplo.empty:
                    for _, row in exemplo.iterrows():
                        print(f"Equipamento {row['Equipamento']}: {row['Data/Hora']} - Diferença: {row['Diferença_Hora']:.2f} horas")
            else:
                print("AVISO: Não foi possível calcular diferenças porque a coluna Data/Hora não está em formato datetime")
        else:
            print("\nAVISO: Não foi possível calcular diferenças de tempo!")
            if 'Equipamento' not in df.columns:
                print("- Coluna 'Equipamento' não encontrada")
            if 'Data/Hora' not in df.columns:
                print("- Coluna 'Data/Hora' não encontrada")
        
        # Salvar resultado como Excel
        print(f"\nSalvando resultado em: {caminho_saida}")
        df.to_excel(caminho_saida, index=False)
        print(f"Arquivo Excel gerado com sucesso!")
        
        return caminho_saida
    
    except Exception as e:
        print(f"\nERRO CRÍTICO ao processar o arquivo: {str(e)}")
        traceback.print_exc()
        return None

def main():
    print("\nIniciando processamento...")
    print(f"Diretório atual: {os.getcwd()}")
    
    # Obter caminho do arquivo CSV
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(script_dir)
    dados_dir = os.path.join(workspace_dir, "dados")
    
    print(f"Pasta scripts: {script_dir}")
    print(f"Pasta workspace: {workspace_dir}")
    print(f"Pasta dados: {dados_dir}")
    print(f"Pasta dados existe? {os.path.exists(dados_dir)}")
    
    # Listar conteúdo da pasta de dados
    if os.path.exists(dados_dir):
        print("\nConteúdo da pasta dados:")
        for item in os.listdir(dados_dir):
            item_path = os.path.join(dados_dir, item)
            tipo = 'Arquivo' if os.path.isfile(item_path) else 'Pasta'
            tamanho = os.path.getsize(item_path) if os.path.isfile(item_path) else 'N/A'
            print(f"- {tipo}: {item} ({tamanho} bytes)")
    
    # Definir caminho do arquivo
    arquivo_csv = os.path.join(dados_dir, "manobrasCSV.csv")
    
    # Se houver um argumento na linha de comando, usar como caminho do arquivo
    if len(sys.argv) > 1:
        arquivo_csv = sys.argv[1]
    
    # Verificar se o arquivo existe
    if not os.path.isfile(arquivo_csv):
        print(f"ERRO: Arquivo não encontrado: {arquivo_csv}")
        # Tentar buscar o arquivo manualmente
        for root, dirs, files in os.walk(workspace_dir):
            for file in files:
                if 'manobras' in file.lower() and file.lower().endswith('.csv'):
                    arquivo_encontrado = os.path.join(root, file)
                    print(f"Encontrado possível arquivo: {arquivo_encontrado}")
                    arquivo_csv = arquivo_encontrado
                    break
        
        if not os.path.isfile(arquivo_csv):
            return
    
    # Criar pasta output se não existir
    pasta_output = os.path.join(workspace_dir, "output")
    os.makedirs(pasta_output, exist_ok=True)
    print(f"Pasta de saída: {pasta_output}")
    
    # Definir caminho de saída
    caminho_saida = os.path.join(pasta_output, f"manobras_processado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    
    # Processar o arquivo
    processar_arquivo_csv(arquivo_csv, caminho_saida)

if __name__ == "__main__":
    print("=" * 60)
    print("PROCESSADOR SIMPLES DE MANOBRAS")
    print("=" * 60)
    main()
    print("\nProcessamento concluído!") 