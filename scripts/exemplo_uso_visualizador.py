"""
Exemplo de uso do Visualizador de Intervalos Operacionais

Este script demonstra como usar o visualizador de forma programática
para criar gráficos de Gantt personalizados.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from visualizador_intervalos import criar_grafico_gantt, processar_planilha_intervalos

def exemplo_basico():
    """
    Exemplo básico: Processar um arquivo específico
    """
    print("=== EXEMPLO BÁSICO ===")
    
    # Caminho para um arquivo Excel processado
    arquivo_excel = "output/colhedorasFrente03_15072025_processado.xlsx"
    
    if os.path.exists(arquivo_excel):
        print(f"Processando arquivo: {arquivo_excel}")
        processar_planilha_intervalos(arquivo_excel)
    else:
        print(f"Arquivo não encontrado: {arquivo_excel}")

def exemplo_equipamento_especifico():
    """
    Exemplo: Criar gráfico para um equipamento específico
    """
    print("\n=== EXEMPLO EQUIPAMENTO ESPECÍFICO ===")
    
    try:
        # Carregar dados
        arquivo_excel = "output/colhedorasFrente03_15072025_processado.xlsx"
        df_intervalos = pd.read_excel(arquivo_excel, sheet_name='Intervalos')
        
        # Listar equipamentos disponíveis
        equipamentos = df_intervalos['Equipamento'].unique()
        print(f"Equipamentos disponíveis: {equipamentos}")
        
        # Criar gráfico para o primeiro equipamento
        if len(equipamentos) > 0:
            equipamento_escolhido = equipamentos[0]
            print(f"Criando gráfico para equipamento: {equipamento_escolhido}")
            
            criar_grafico_gantt(df_intervalos, equipamento=equipamento_escolhido)
        
    except Exception as e:
        print(f"Erro: {e}")

def exemplo_analise_dados():
    """
    Exemplo: Análise dos dados antes de criar o gráfico
    """
    print("\n=== EXEMPLO ANÁLISE DE DADOS ===")
    
    try:
        # Carregar dados
        arquivo_excel = "output/colhedorasFrente03_15072025_processado.xlsx"
        df_intervalos = pd.read_excel(arquivo_excel, sheet_name='Intervalos')
        
        print(f"Total de intervalos: {len(df_intervalos)}")
        print(f"Equipamentos: {df_intervalos['Equipamento'].unique()}")
        
        # Análise por tipo de operação
        print("\nDistribuição por tipo:")
        tipo_counts = df_intervalos['Tipo'].value_counts()
        for tipo, count in tipo_counts.items():
            print(f"  {tipo}: {count} intervalos")
        
        # Análise de duração
        print("\nEstatísticas de duração (horas):")
        duracao_stats = df_intervalos['Duração (horas)'].describe()
        print(duracao_stats)
        
        # Duração total por tipo
        print("\nDuração total por tipo:")
        duracao_por_tipo = df_intervalos.groupby('Tipo')['Duração (horas)'].sum()
        for tipo, total in duracao_por_tipo.items():
            print(f"  {tipo}: {total:.2f} horas")
        
    except Exception as e:
        print(f"Erro: {e}")

def exemplo_grafico_customizado():
    """
    Exemplo: Criar gráfico com customizações
    """
    print("\n=== EXEMPLO GRÁFICO CUSTOMIZADO ===")
    
    try:
        # Carregar dados
        arquivo_excel = "output/colhedorasFrente03_15072025_processado.xlsx"
        df_intervalos = pd.read_excel(arquivo_excel, sheet_name='Intervalos')
        
        # Filtrar apenas intervalos longos (> 30 minutos)
        df_filtrado = df_intervalos[df_intervalos['Duração (horas)'] > 0.5]
        
        print(f"Intervalos filtrados (> 30 min): {len(df_filtrado)}")
        
        if len(df_filtrado) > 0:
            # Pegar primeiro equipamento
            equipamento = df_filtrado['Equipamento'].iloc[0]
            
            # Criar gráfico customizado
            criar_grafico_gantt(df_filtrado, equipamento=equipamento, salvar_arquivo=True)
        
    except Exception as e:
        print(f"Erro: {e}")

def exemplo_multiplos_equipamentos():
    """
    Exemplo: Criar gráficos para múltiplos equipamentos
    """
    print("\n=== EXEMPLO MÚLTIPLOS EQUIPAMENTOS ===")
    
    try:
        # Listar todos os arquivos processados
        import glob
        arquivos_excel = glob.glob("output/*_processado.xlsx")
        
        print(f"Encontrados {len(arquivos_excel)} arquivos:")
        
        for arquivo in arquivos_excel:
            print(f"\nProcessando: {os.path.basename(arquivo)}")
            
            try:
                df_intervalos = pd.read_excel(arquivo, sheet_name='Intervalos')
                equipamentos = df_intervalos['Equipamento'].unique()
                
                print(f"  Equipamentos: {equipamentos}")
                
                # Criar gráfico para cada equipamento
                for equipamento in equipamentos:
                    print(f"  Criando gráfico para: {equipamento}")
                    criar_grafico_gantt(df_intervalos, equipamento=equipamento)
                    
            except Exception as e:
                print(f"  Erro ao processar {arquivo}: {e}")
        
    except Exception as e:
        print(f"Erro: {e}")

def main():
    """
    Função principal - executar todos os exemplos
    """
    print("EXEMPLOS DE USO DO VISUALIZADOR DE INTERVALOS")
    print("=" * 60)
    
    # Escolher qual exemplo executar
    print("\nEscolha um exemplo:")
    print("1. Exemplo básico")
    print("2. Equipamento específico")
    print("3. Análise de dados")
    print("4. Gráfico customizado")
    print("5. Múltiplos equipamentos")
    print("6. Todos os exemplos")
    
    try:
        escolha = input("\nDigite o número (1-6): ").strip()
        
        if escolha == "1":
            exemplo_basico()
        elif escolha == "2":
            exemplo_equipamento_especifico()
        elif escolha == "3":
            exemplo_analise_dados()
        elif escolha == "4":
            exemplo_grafico_customizado()
        elif escolha == "5":
            exemplo_multiplos_equipamentos()
        elif escolha == "6":
            exemplo_basico()
            exemplo_equipamento_especifico()
            exemplo_analise_dados()
            exemplo_grafico_customizado()
            exemplo_multiplos_equipamentos()
        else:
            print("Opção inválida!")
            
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main() 