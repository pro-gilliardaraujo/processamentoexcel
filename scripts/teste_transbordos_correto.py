#!/usr/bin/env python3
"""
Teste rápido do método correto de motor ocioso para TRANSBORDOS
"""

import pandas as pd
import os
import glob
import importlib.util

# Importar o módulo de transbordos
spec = importlib.util.spec_from_file_location("processador_tt", "2_ProcessadorTransbordosMaq.py")
processador_tt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(processador_tt)

def teste_rapido_transbordos():
    """Teste rápido do método correto para transbordos."""
    
    print("="*70)
    print("TESTE RÁPIDO: MÉTODO CORRETO DE MOTOR OCIOSO - TRANSBORDOS")
    print("="*70)
    
    # Buscar arquivos de transbordos
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
    
    # Mostrar algumas características dos dados de transbordos
    print(f"\nCaracterísticas dos dados:")
    if 'Motor Ligado' in df.columns:
        valores_motor = df['Motor Ligado'].value_counts()
        print(f"Valores Motor Ligado: {dict(valores_motor)}")
    
    if 'Estado Operacional' in df.columns:
        valores_estado = df['Estado Operacional'].value_counts()
        print(f"Estados Operacionais: {dict(valores_estado)}")
    
    # Aplicar método correto
    df = processador_tt.calcular_motor_ocioso_correto(df)
    resultado = processador_tt.calcular_motor_ocioso_maquina_correto(df)
    
    # Mostrar resultado
    print("\nRESULTADO FINAL:")
    if not resultado.empty:
        for _, row in resultado.iterrows():
            print(f"Frota {row['Frota']}: {row['Porcentagem']*100:.2f}% ({row['Tempo Ocioso']:.4f}h de {row['Horas Motor']:.4f}h)")
    else:
        print("Nenhum resultado encontrado")

if __name__ == "__main__":
    teste_rapido_transbordos() 