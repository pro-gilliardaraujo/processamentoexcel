#!/usr/bin/env python3
"""
Script de teste para comparar os métodos de cálculo de motor ocioso:
- Método Atual (complexo com intervalos)
- Método Simples (Motor Ligado == 1 e Estado == PARADA)
"""

import pandas as pd
import sys
import os
import glob

# Adicionar o diretório scripts ao path
sys.path.append(os.path.join(os.path.dirname(__file__)))

import importlib.util

# Importar o módulo que começa com número usando importlib
spec = importlib.util.spec_from_file_location("processador", "1_ProcessadorColhedorasMaq.py")
processador = importlib.util.module_from_spec(spec)
spec.loader.exec_module(processador)

# Aliases para as funções
processar_arquivo_base = processador.processar_arquivo_base
calcular_motor_ocioso_maquina = processador.calcular_motor_ocioso_maquina
calcular_motor_ocioso_simples = processador.calcular_motor_ocioso_simples
calcular_motor_ocioso_maquina_simples = processador.calcular_motor_ocioso_maquina_simples

def testar_metodos_motor_ocioso():
    """Testa e compara os dois métodos de cálculo de motor ocioso."""
    
    print("="*80)
    print("TESTE DE COMPARAÇÃO: MÉTODOS DE CÁLCULO DE MOTOR OCIOSO")
    print("="*80)
    
    # Buscar arquivos de dados
    diretorio_dados = "../dados"
    arquivos = []
    
    # Buscar arquivos de colhedoras (incluindo ZIPs)
    patterns = ["*colhedora*.txt", "*colhedora*.csv", "*colhedora*.zip"]
    for pattern in patterns:
        arquivos.extend(glob.glob(os.path.join(diretorio_dados, pattern)))
    
    if not arquivos:
        print(f"Nenhum arquivo encontrado em {diretorio_dados}")
        return
    
    # Pegar o primeiro arquivo para teste
    arquivo_teste = arquivos[0]
    print(f"Testando com arquivo: {os.path.basename(arquivo_teste)}")
    
    try:
        # Processar arquivo
        print("\nProcessando arquivo...")
        
        # Se for arquivo ZIP, extrair primeiro
        temp_dir = None
        if arquivo_teste.endswith('.zip'):
            print("Arquivo ZIP detectado, extraindo...")
            from zipfile import ZipFile
            import tempfile
            
            temp_dir = tempfile.mkdtemp()
            with ZipFile(arquivo_teste, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                
            # Buscar arquivo TXT/CSV extraído
            extracted_files = []
            for ext in ['*.txt', '*.csv']:
                extracted_files.extend(glob.glob(os.path.join(temp_dir, ext)))
            
            if extracted_files:
                arquivo_teste = extracted_files[0]
                print(f"Arquivo extraído: {os.path.basename(arquivo_teste)}")
            else:
                print("Nenhum arquivo TXT/CSV encontrado no ZIP")
                if temp_dir:
                    import shutil
                    shutil.rmtree(temp_dir)
                return
        
        df = processar_arquivo_base(arquivo_teste)
        
        # Limpar diretório temporário se foi criado
        if temp_dir:
            import shutil
            shutil.rmtree(temp_dir)
        
        if df is None or df.empty:
            print("Erro ao processar arquivo ou arquivo vazio")
            return
            
        print(f"Arquivo processado: {len(df)} registros")
        
        # Verificar se as colunas necessárias existem
        colunas_necessarias = ['Motor Ligado', 'Estado Operacional', 'Diferença_Hora', 'Equipamento']
        faltando = [col for col in colunas_necessarias if col not in df.columns]
        
        if faltando:
            print(f"Colunas faltando: {faltando}")
            print(f"Colunas disponíveis: {list(df.columns)}")
            return
        
        print("\n" + "="*60)
        print("MÉTODO ATUAL (Complexo)")
        print("="*60)
        
        # Método atual
        resultado_atual = calcular_motor_ocioso_maquina(df)
        print("\nResultados do método atual:")
        print(resultado_atual.to_string(index=False))
        
        print("\n" + "="*60)
        print("MÉTODO SIMPLES (Proposto)")
        print("="*60)
        
        # Método simples
        df_simples = calcular_motor_ocioso_simples(df.copy())
        resultado_simples = calcular_motor_ocioso_maquina_simples(df_simples)
        print("\nResultados do método simples:")
        print(resultado_simples.to_string(index=False))
        
        print("\n" + "="*60)
        print("COMPARAÇÃO DOS RESULTADOS")
        print("="*60)
        
        # Comparar resultados
        if not resultado_atual.empty and not resultado_simples.empty:
            print("\nComparação por equipamento:")
            for _, row_atual in resultado_atual.iterrows():
                frota = row_atual['Frota']
                row_simples = resultado_simples[resultado_simples['Frota'] == frota]
                
                if not row_simples.empty:
                    row_simples = row_simples.iloc[0]
                    
                    print(f"\n--- {frota} ---")
                    print(f"Método Atual  : {row_atual['Porcentagem']*100:.2f}% ({row_atual['Tempo Ocioso']:.4f}h de {row_atual['Horas Motor']:.4f}h)")
                    print(f"Método Simples: {row_simples['Porcentagem']*100:.2f}% ({row_simples['Tempo Ocioso']:.4f}h de {row_simples['Horas Motor']:.4f}h)")
                    
                    diferenca = abs(row_atual['Porcentagem'] - row_simples['Porcentagem']) * 100
                    print(f"Diferença     : {diferenca:.2f} pontos percentuais")
                    
                    if diferenca > 1:  # Diferença significativa
                        print("⚠️  DIFERENÇA SIGNIFICATIVA DETECTADA!")
        
        # Análise detalhada de alguns registros
        print("\n" + "="*60)
        print("ANÁLISE DETALHADA DOS DADOS")
        print("="*60)
        
        # Contar registros por condição
        total_registros = len(df)
        motor_ligado = len(df[df['Motor Ligado'] == 1])
        estado_parada = len(df[df['Estado Operacional'] == 'PARADA'])
        motor_ligado_e_parada = len(df[(df['Motor Ligado'] == 1) & (df['Estado Operacional'] == 'PARADA')])
        
        print(f"Total de registros: {total_registros}")
        print(f"Motor Ligado == 1: {motor_ligado} ({motor_ligado/total_registros*100:.1f}%)")
        print(f"Estado == PARADA: {estado_parada} ({estado_parada/total_registros*100:.1f}%)")
        print(f"Motor Ligado == 1 E Estado == PARADA: {motor_ligado_e_parada} ({motor_ligado_e_parada/total_registros*100:.1f}%)")
        
        # Tempo total em cada condição
        tempo_motor_ligado = df[df['Motor Ligado'] == 1]['Diferença_Hora'].sum()
        tempo_motor_ocioso_simples = df[(df['Motor Ligado'] == 1) & (df['Estado Operacional'] == 'PARADA')]['Diferença_Hora'].sum()
        
        print(f"\nTempo total com motor ligado: {tempo_motor_ligado:.4f} horas")
        print(f"Tempo total motor ocioso (método simples): {tempo_motor_ocioso_simples:.4f} horas")
        print(f"Porcentagem geral (método simples): {tempo_motor_ocioso_simples/tempo_motor_ligado*100:.2f}%")
        
    except Exception as e:
        print(f"Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_metodos_motor_ocioso() 