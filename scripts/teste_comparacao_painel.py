#!/usr/bin/env python3
"""
Script para comparar resultados com o painel da plataforma original.
Permite ajustar filtros e critérios até que os resultados batam com o painel.
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

def testar_motor_ocioso_custom(df, mostrar_detalhes=True):
    """Testa diferentes critérios de motor ocioso para comparar com o painel."""
    
    if mostrar_detalhes:
        print("\n" + "="*80)
        print("ANÁLISE DETALHADA DOS CRITÉRIOS")
        print("="*80)
    
    resultados = {}
    
    # 1. Método Original (atual no sistema)
    df_original = df.copy()
    df_original = processador.calcular_motor_ocioso_novo(df_original)
    tempo_ocioso_original = df_original['Motor Ocioso'].sum()
    
    # 2. Método Simples Básico
    tempo_ocioso_simples = df[(df['Motor Ligado'] == 1) & (df['Estado Operacional'] == 'PARADA')]['Diferença_Hora'].sum()
    
    # 3. Método com filtros adicionais - excluir operações específicas
    df_filtrado = df.copy()
    # Verificar se existe coluna de operações para filtrar
    if 'Operacao' in df.columns:
        operacoes_excluir = ['ABASTECIMENTO', 'MANUTENCAO', 'LAVAGEM']  # Ajustar conforme necessário
        df_filtrado = df_filtrado[~df_filtrado['Operacao'].isin(operacoes_excluir)]
    
    tempo_ocioso_filtrado = df_filtrado[(df_filtrado['Motor Ligado'] == 1) & (df_filtrado['Estado Operacional'] == 'PARADA')]['Diferença_Hora'].sum()
    
    # 4. Método com RPM mínimo (similar ao original mas simplificado)
    RPM_MINIMO = 300
    if 'RPM Motor' in df.columns:
        condicao_rpm = (df['Motor Ligado'] == 1) & (df['Estado Operacional'] == 'PARADA') & (df['RPM Motor'] >= RPM_MINIMO)
        tempo_ocioso_rpm = df[condicao_rpm]['Diferença_Hora'].sum()
    else:
        tempo_ocioso_rpm = tempo_ocioso_simples
    
    # 5. Método com velocidade zero
    if 'Velocidade' in df.columns:
        condicao_velocidade = (df['Motor Ligado'] == 1) & (df['Velocidade'] == 0) & (df['Estado Operacional'] == 'PARADA')
        tempo_ocioso_velocidade = df[condicao_velocidade]['Diferença_Hora'].sum()
    else:
        tempo_ocioso_velocidade = tempo_ocioso_simples
    
    # Calcular horas motor total
    horas_motor_total = df[df['Motor Ligado'] == 1]['Diferença_Hora'].sum()
    
    # Armazenar resultados
    resultados = {
        'Original (Complexo)': {'tempo': tempo_ocioso_original, 'percentual': tempo_ocioso_original/horas_motor_total*100},
        'Simples Básico': {'tempo': tempo_ocioso_simples, 'percentual': tempo_ocioso_simples/horas_motor_total*100},
        'Com Filtros': {'tempo': tempo_ocioso_filtrado, 'percentual': tempo_ocioso_filtrado/horas_motor_total*100},
        'Com RPM Mínimo': {'tempo': tempo_ocioso_rpm, 'percentual': tempo_ocioso_rpm/horas_motor_total*100},
        'Com Velocidade Zero': {'tempo': tempo_ocioso_velocidade, 'percentual': tempo_ocioso_velocidade/horas_motor_total*100}
    }
    
    if mostrar_detalhes:
        print(f"Horas Motor Total: {horas_motor_total:.4f} h")
        print(f"Total de registros: {len(df)}")
        print(f"Motor Ligado == 1: {len(df[df['Motor Ligado'] == 1])}")
        print(f"Estado == PARADA: {len(df[df['Estado Operacional'] == 'PARADA'])}")
        print(f"Motor Ligado == 1 E Estado == PARADA: {len(df[(df['Motor Ligado'] == 1) & (df['Estado Operacional'] == 'PARADA')])}")
        
        print("\n" + "="*80)
        print("COMPARAÇÃO DE MÉTODOS")
        print("="*80)
        
        for metodo, valores in resultados.items():
            print(f"{metodo:20}: {valores['percentual']:6.2f}% ({valores['tempo']:7.4f}h)")
    
    return resultados

def comparar_com_painel():
    """Função principal para comparar com o painel da plataforma."""
    
    print("="*80)
    print("COMPARAÇÃO COM PAINEL DA PLATAFORMA")
    print("="*80)
    
    # Buscar arquivos
    diretorio_dados = "../dados"
    arquivos = glob.glob(os.path.join(diretorio_dados, "*colhedora*.zip"))
    
    if not arquivos:
        print(f"Nenhum arquivo encontrado em {diretorio_dados}")
        return
    
    print(f"Arquivos encontrados: {[os.path.basename(a) for a in arquivos]}")
    
    # Processar cada arquivo
    for i, arquivo in enumerate(arquivos, 1):
        print(f"\n{'='*80}")
        print(f"ARQUIVO {i}: {os.path.basename(arquivo)}")
        print(f"{'='*80}")
        
        try:
            # Processar arquivo
            df = processador.processar_arquivo_base(arquivo)
            
            if df is None or df.empty:
                print("Erro ao processar arquivo")
                continue
            
            # Testar métodos
            resultados = testar_motor_ocioso_custom(df, mostrar_detalhes=True)
            
            # Solicitar input do usuário
            print(f"\n{'-'*60}")
            print("QUAL É O VALOR NO PAINEL DA PLATAFORMA?")
            print(f"{'-'*60}")
            
            try:
                valor_painel = input("Digite o % de motor ocioso mostrado no painel (apenas o número, ex: 4.5): ")
                if valor_painel.strip():
                    valor_painel = float(valor_painel)
                    
                    print(f"\n📊 VALOR DO PAINEL: {valor_painel:.2f}%")
                    print(f"📋 COMPARAÇÃO COM NOSSOS MÉTODOS:")
                    
                    melhor_metodo = None
                    menor_diferenca = float('inf')
                    
                    for metodo, valores in resultados.items():
                        diferenca = abs(valores['percentual'] - valor_painel)
                        status = "✅" if diferenca < 0.5 else "⚠️" if diferenca < 1.0 else "❌"
                        print(f"{status} {metodo:20}: {valores['percentual']:6.2f}% (dif: {diferenca:+.2f}pp)")
                        
                        if diferenca < menor_diferenca:
                            menor_diferenca = diferenca
                            melhor_metodo = metodo
                    
                    print(f"\n🎯 MELHOR MÉTODO: {melhor_metodo} (diferença: {menor_diferenca:.2f}pp)")
                    
                    if menor_diferenca > 1.0:
                        print("\n💡 SUGESTÕES PARA INVESTIGAR:")
                        print("- Verificar se há filtros específicos aplicados no painel")
                        print("- Confirmar definições de 'Motor Ligado' e 'Estado Operacional'")
                        print("- Verificar se há exclusão de períodos específicos (manutenção, etc.)")
                        print("- Confirmar se RPM mínimo é aplicado")
                        
            except ValueError:
                print("Valor inválido inserido")
            except KeyboardInterrupt:
                print("\nTeste interrompido pelo usuário")
                break
                
        except Exception as e:
            print(f"Erro ao processar {arquivo}: {e}")
            continue

if __name__ == "__main__":
    comparar_com_painel() 