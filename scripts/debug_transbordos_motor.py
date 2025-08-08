#!/usr/bin/env python3
"""
Debug dos valores da coluna Motor Ligado em transbordos
"""

import pandas as pd
import os
import glob
import importlib.util

# Importar o módulo de transbordos
spec = importlib.util.spec_from_file_location("processador_tt", "2_ProcessadorTransbordosMaq.py")
processador_tt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(processador_tt)

def debug_motor_ligado():
    """Debug dos valores da coluna Motor Ligado."""
    
    print("="*60)
    print("DEBUG: VALORES DA COLUNA MOTOR LIGADO - TRANSBORDOS")
    print("="*60)
    
    # Buscar arquivos
    diretorio_dados = "../dados"
    arquivos = glob.glob(os.path.join(diretorio_dados, "*transbordo*.zip"))
    
    if not arquivos:
        print("Nenhum arquivo de transbordo encontrado")
        return
    
    arquivo = arquivos[0]
    print(f"Arquivo: {os.path.basename(arquivo)}")
    
    # Processar
    df = processador_tt.processar_arquivo_base(arquivo)
    
    if df is None or df.empty:
        print("Erro ao processar arquivo")
        return
        
    print(f"Total de registros: {len(df)}")
    
    # Debug detalhado da coluna Motor Ligado
    if 'Motor Ligado' in df.columns:
        print(f"\nVALORES ÚNICOS da coluna 'Motor Ligado':")
        valores_unicos = df['Motor Ligado'].unique()
        for valor in valores_unicos:
            count = len(df[df['Motor Ligado'] == valor])
            print(f"  '{valor}' ({type(valor).__name__}): {count} registros")
        
        # Verificar se há valores 1 ou 'LIGADO'
        ligado_1 = len(df[df['Motor Ligado'] == 1])
        ligado_str = len(df[df['Motor Ligado'] == 'LIGADO'])
        
        print(f"\nVerificações específicas:")
        print(f"  Motor Ligado == 1: {ligado_1} registros")
        print(f"  Motor Ligado == 'LIGADO': {ligado_str} registros")
    else:
        print("❌ Coluna 'Motor Ligado' não encontrada!")
    
    # Debug da coluna Estado Operacional
    if 'Estado Operacional' in df.columns:
        print(f"\nVALORES da coluna 'Estado Operacional':")
        valores_estado = df['Estado Operacional'].value_counts()
        for estado, count in valores_estado.items():
            print(f"  '{estado}': {count} registros")
        
        # Verificar registros PARADA
        parada_count = len(df[df['Estado Operacional'] == 'PARADA'])
        print(f"\nRegistros com Estado == 'PARADA': {parada_count}")
    else:
        print("❌ Coluna 'Estado Operacional' não encontrada!")
    
    # Mostrar algumas linhas de exemplo
    print(f"\n📋 EXEMPLO DE REGISTROS (primeiras 10 linhas):")
    colunas_debug = ['Motor Ligado', 'Estado Operacional', 'Diferença_Hora']
    colunas_existentes = [col for col in colunas_debug if col in df.columns]
    
    if colunas_existentes:
        print(df[colunas_existentes].head(10).to_string())
    else:
        print("Nenhuma das colunas de debug encontrada")

if __name__ == "__main__":
    debug_motor_ligado() 