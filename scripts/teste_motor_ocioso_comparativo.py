#!/usr/bin/env python3
"""
Script comparativo para testar os 3 métodos de cálculo de motor ocioso:
1. Método Atual (complexo com Parada com Motor Ligado)
2. Método Simples (Motor Ligado == 1 e Estado == PARADA sem filtros)
3. Método Correto (filtros + intervalos sequenciais - 1 minuto)
"""

import pandas as pd
import sys
import os
import glob
import importlib.util

# Importar o módulo principal
spec = importlib.util.spec_from_file_location("processador", "1_ProcessadorColhedorasMaq.py")
processador = importlib.util.module_from_spec(spec)
spec.loader.exec_module(processador)

def comparar_todos_metodos():
    """Compara os 3 métodos de cálculo de motor ocioso."""
    
    print("="*80)
    print("COMPARATIVO: MÉTODOS DE CÁLCULO DE MOTOR OCIOSO")
    print("="*80)
    
    # Buscar arquivos
    diretorio_dados = "../dados"
    arquivos = glob.glob(os.path.join(diretorio_dados, "*colhedora*.zip"))
    
    if not arquivos:
        print(f"Nenhum arquivo encontrado em {diretorio_dados}")
        return
    
    # Pegar o primeiro arquivo para teste
    arquivo_teste = arquivos[0]
    print(f"Testando com arquivo: {os.path.basename(arquivo_teste)}")
    
    try:
        # Processar arquivo
        print("\nProcessando arquivo...")
        df = processador.processar_arquivo_base(arquivo_teste)
        
        if df is None or df.empty:
            print("Erro ao processar arquivo ou arquivo vazio")
            return
            
        print(f"Arquivo processado: {len(df)} registros")
        
        # Verificar colunas necessárias
        colunas_necessarias = ['Motor Ligado', 'Estado Operacional', 'Diferença_Hora', 'Equipamento', 'Grupo Operacao']
        faltando = [col for col in colunas_necessarias if col not in df.columns]
        
        if faltando:
            print(f"Colunas faltando: {faltando}")
            return
        
        print("\n" + "="*80)
        print("APLICANDO OS 3 MÉTODOS...")
        print("="*80)
        
        # MÉTODO 1: Atual (complexo)
        print("\n" + "="*60)
        print("MÉTODO 1: ATUAL (Complexo)")
        print("="*60)
        
        df_metodo1 = df.copy()
        df_metodo1 = processador.calcular_motor_ocioso_novo(df_metodo1)
        resultado1 = processador.calcular_motor_ocioso_maquina(df_metodo1)
        
        # MÉTODO 2: Simples (sem filtros)
        print("\n" + "="*60)
        print("MÉTODO 2: SIMPLES (Sem Filtros)")
        print("="*60)
        
        df_metodo2 = df.copy()
        df_metodo2 = processador.calcular_motor_ocioso_simples(df_metodo2)
        resultado2 = processador.calcular_motor_ocioso_maquina_simples(df_metodo2)
        
        # MÉTODO 3: Correto (filtros + intervalos sequenciais)
        print("\n" + "="*60)
        print("MÉTODO 3: CORRETO (Filtros + Intervalos Sequenciais)")
        print("="*60)
        
        df_metodo3 = df.copy()
        df_metodo3 = processador.calcular_motor_ocioso_correto(df_metodo3)
        resultado3 = processador.calcular_motor_ocioso_maquina_correto(df_metodo3)
        
        # COMPARAÇÃO FINAL
        print("\n" + "="*80)
        print("COMPARAÇÃO FINAL DOS RESULTADOS")
        print("="*80)
        
        print(f"{'MÉTODO':<30} | {'%':<8} | {'TEMPO OCIOSO':<12} | {'HORAS MOTOR':<12}")
        print("-" * 70)
        
        # Para cada equipamento, comparar os resultados
        equipamentos = set()
        if not resultado1.empty:
            equipamentos.update(resultado1['Frota'].values)
        if not resultado2.empty:
            equipamentos.update(resultado2['Frota'].values)
        if not resultado3.empty:
            equipamentos.update(resultado3['Frota'].values)
        
        for equipamento in sorted(equipamentos):
            print(f"\n--- EQUIPAMENTO {equipamento} ---")
            
            # Método 1
            row1 = resultado1[resultado1['Frota'] == equipamento]
            if not row1.empty:
                row1 = row1.iloc[0]
                print(f"{'1. Atual (Complexo)':<30} | {row1['Porcentagem']*100:6.2f}% | {row1['Tempo Ocioso']:10.4f}h | {row1['Horas Motor']:10.4f}h")
            
            # Método 2
            row2 = resultado2[resultado2['Frota'] == equipamento]
            if not row2.empty:
                row2 = row2.iloc[0]
                print(f"{'2. Simples (Sem Filtros)':<30} | {row2['Porcentagem']*100:6.2f}% | {row2['Tempo Ocioso']:10.4f}h | {row2['Horas Motor']:10.4f}h")
            
            # Método 3
            row3 = resultado3[resultado3['Frota'] == equipamento]
            if not row3.empty:
                row3 = row3.iloc[0]
                print(f"{'3. Correto (Intervalos)':<30} | {row3['Porcentagem']*100:6.2f}% | {row3['Tempo Ocioso']:10.4f}h | {row3['Horas Motor']:10.4f}h")
            
            # Calcular diferenças
            if not row1.empty and not row3.empty:
                diff_percentual = (row3['Porcentagem'] - row1['Porcentagem']) * 100
                diff_tempo = row3['Tempo Ocioso'] - row1['Tempo Ocioso']
                print(f"{'   DIFERENÇA (3-1)':<30} | {diff_percentual:+6.2f}pp| {diff_tempo:+10.4f}h |")
        
        # ANÁLISE DETALHADA DOS DADOS
        print("\n" + "="*80)
        print("ANÁLISE DETALHADA DOS DADOS")
        print("="*80)
        
        # Contar registros por condição
        total_registros = len(df)
        motor_ligado = len(df[df['Motor Ligado'] == 1])
        estado_parada = len(df[df['Estado Operacional'] == 'PARADA'])
        grupo_manutencao = len(df[df['Grupo Operacao'] == 'Manutenção'])
        
        # Condições para cada método
        condicao_metodo2 = (df['Motor Ligado'] == 1) & (df['Estado Operacional'] == 'PARADA')
        registros_metodo2 = len(df[condicao_metodo2])
        
        condicao_metodo3 = (df['Motor Ligado'] == 1) & (df['Estado Operacional'] == 'PARADA') & (df['Grupo Operacao'] != 'Manutenção')
        registros_metodo3 = len(df[condicao_metodo3])
        
        print(f"Total de registros: {total_registros}")
        print(f"Motor Ligado == 1: {motor_ligado} ({motor_ligado/total_registros*100:.1f}%)")
        print(f"Estado == PARADA: {estado_parada} ({estado_parada/total_registros*100:.1f}%)")
        print(f"Grupo == Manutenção: {grupo_manutencao} ({grupo_manutencao/total_registros*100:.1f}%)")
        print(f"\nRegistros considerados por método:")
        print(f"Método 2 (Simples): {registros_metodo2} registros")
        print(f"Método 3 (Correto): {registros_metodo3} registros")
        print(f"Diferença (filtro Manutenção): {registros_metodo2 - registros_metodo3} registros")
        
        # Tempo total em cada condição
        tempo_motor_ligado = df[df['Motor Ligado'] == 1]['Diferença_Hora'].sum()
        tempo_metodo2 = df[condicao_metodo2]['Diferença_Hora'].sum()
        tempo_metodo3 = df[condicao_metodo3]['Diferença_Hora'].sum()
        
        print(f"\nTempo total por condição:")
        print(f"Motor Ligado == 1: {tempo_motor_ligado:.4f} horas")
        print(f"Método 2 (sem filtros): {tempo_metodo2:.4f} horas")
        print(f"Método 3 (com filtros): {tempo_metodo3:.4f} horas")
        print(f"Tempo filtrado (Manutenção): {tempo_metodo2 - tempo_metodo3:.4f} horas")
        
    except Exception as e:
        print(f"Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    comparar_todos_metodos() 