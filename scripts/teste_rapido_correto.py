#!/usr/bin/env python3
"""
Teste rápido do método correto de motor ocioso
"""

import pandas as pd
import os
import glob
import importlib.util

# Importar o módulo principal
spec = importlib.util.spec_from_file_location("processador", "1_ProcessadorColhedorasMaq.py")
processador = importlib.util.module_from_spec(spec)
spec.loader.exec_module(processador)

def teste_rapido():
    """Teste rápido do método correto."""
    
    print("="*60)
    print("TESTE RÁPIDO: MÉTODO CORRETO DE MOTOR OCIOSO")
    print("="*60)
    
    # Buscar arquivos
    diretorio_dados = "../dados"
    arquivos = glob.glob(os.path.join(diretorio_dados, "*colhedora*.zip"))
    
    if not arquivos:
        print("Nenhum arquivo encontrado")
        return
    
    arquivo = arquivos[0]
    print(f"Arquivo: {os.path.basename(arquivo)}")
    
    # Processar
    df = processador.processar_arquivo_base(arquivo)
    
    if df is None or df.empty:
        print("Erro ao processar arquivo")
        return
        
    print(f"Total de registros: {len(df)}")
    
    # Aplicar método correto
    df = processador.calcular_motor_ocioso_correto(df)
    resultado = processador.calcular_motor_ocioso_maquina_correto(df)
    
    # Mostrar resultado
    print("\nRESULTADO FINAL:")
    if not resultado.empty:
        for _, row in resultado.iterrows():
            print(f"Frota {row['Frota']}: {row['Porcentagem']*100:.2f}% ({row['Tempo Ocioso']:.4f}h de {row['Horas Motor']:.4f}h)")
    else:
        print("Nenhum resultado encontrado")

if __name__ == "__main__":
    teste_rapido() 