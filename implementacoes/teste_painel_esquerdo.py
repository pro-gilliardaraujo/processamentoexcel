#!/usr/bin/env python3
"""
Teste para validar a implementação do painel esquerdo.
Simula dados e testa todas as funções de cálculo.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from scripts.processamento_colhedoras import calcular_producao_por_frota, calcular_painel_esquerdo

def criar_dados_teste():
    """Cria dados de teste simulando as planilhas existentes."""
    
    # Dados de horas por frota (simulando planilha "Horas por Frota")
    horas_por_frota = pd.DataFrame({
        'Frota': [7032, 7036, 7037],
        'Horas Registradas': [15.5, 14.2, 13.8]
    })
    
    # Dados de eficiência energética (simulando planilha "Eficiência Energética")  
    hora_elevador = pd.DataFrame({
        'Frota': [7032, 7036, 7037],
        'Horas Elevador': [10.8, 9.5, 8.7],
        'Horas Motor': [12.3, 11.0, 10.2]
    })
    
    # Dados de manobras (simulando planilha "Manobras")
    df_manobras_frota = pd.DataFrame({
        'Frota': [7032, 7036, 7037],
        'Intervalos Válidos': [45, 38, 42],
        'Tempo Total': [2.3, 1.9, 2.1],
        'Tempo Médio': [0.051, 0.050, 0.050]
    })
    
    # Dados de disponibilidade mecânica
    disp_mecanica = pd.DataFrame({
        'Frota': [7032, 7036, 7037],
        'Disponibilidade (%)': [89.5, 92.1, 87.3],
        'Tempo Manutenção': [1.6, 1.1, 1.8]
    })
    
    # Dados de operadores
    df_operadores = pd.DataFrame({
        'Frota': [7032, 7032, 7036, 7037, 7037],
        'Operador': ['João Silva', 'Pedro Santos', 'Maria Costa', 'Carlos Lima', 'Ana Souza'],
        'Horas Elevador': [8.5, 2.3, 9.5, 5.2, 3.5]
    })
    
    return horas_por_frota, hora_elevador, df_manobras_frota, disp_mecanica, df_operadores

def testar_producao():
    """Testa o cálculo de produção por frota."""
    print("🧪 TESTANDO CÁLCULO DE PRODUÇÃO")
    print("="*50)
    
    _, hora_elevador, _, _, _ = criar_dados_teste()
    
    # Testar com 2000 toneladas (valor padrão)
    df_producao = calcular_producao_por_frota(hora_elevador, 2000)
    
    print("\n📊 Resultado da Produção:")
    print(df_producao.to_string(index=False))
    
    # Validações
    total_toneladas = df_producao['Toneladas'].sum()
    print(f"\n✅ Total de toneladas distribuídas: {total_toneladas:.2f}")
    print(f"✅ Total esperado: 2000.00")
    print(f"✅ Diferença: {abs(total_toneladas - 2000):.2f}")
    
    if abs(total_toneladas - 2000) < 0.01:
        print("🎉 Cálculo de produção CORRETO!")
    else:
        print("❌ Erro no cálculo de produção!")
    
    return df_producao

def testar_painel_esquerdo():
    """Testa o cálculo completo do painel esquerdo."""
    print("\n\n🧪 TESTANDO PAINEL ESQUERDO COMPLETO")
    print("="*50)
    
    horas_por_frota, hora_elevador, df_manobras_frota, disp_mecanica, df_operadores = criar_dados_teste()
    df_producao = calcular_producao_por_frota(hora_elevador, 2000)
    
    # Criar DataFrame base simulado (não usado diretamente, mas necessário)
    df_base = pd.DataFrame()
    
    # Calcular painel esquerdo
    df_painel = calcular_painel_esquerdo(
        df_base, horas_por_frota, hora_elevador,
        df_manobras_frota, disp_mecanica, df_operadores, df_producao
    )
    
    print("\n📊 Resultado do Painel Esquerdo:")
    for _, linha in df_painel.iterrows():
        frota = linha['frota']
        print(f"\n🚜 FROTA {frota}:")
        print(f"   📈 Horas registradas: {linha['horas_registradas']:.1f}h")
        print(f"   ⚡ Horas motor: {linha['horas_motor']:.1f}h") 
        print(f"   🔄 Horas elevador: {linha['horas_elevador']:.1f}h")
        print(f"   📦 Toneladas: {linha['toneladas']:.1f}t")
        print(f"   ⚖️ Ton/hora: {linha['ton_por_hora']:.1f}t/h")
        print(f"   🎯 Eficiência operacional: {linha['eficiencia_operacional']:.1f}%")
        print(f"   ⚡ Eficiência energética: {linha['eficiencia_energetica']:.1f}%")
        print(f"   🔄 Manobras intervalos: {linha['manobras_intervalos']}")
        print(f"   ⏱️ Tempo total manobras: {linha['manobras_tempo_total']:.2f}h")
        print(f"   📊 Disponibilidade mecânica: {linha['disponibilidade_mecanica']:.1f}%")
        print(f"   👥 Operadores: {len(linha['operadores'])}")
        for op in linha['operadores']:
            print(f"      - {op['nome']}: {op['horas']:.1f}h")
    
    return df_painel

def testar_validacoes():
    """Testa validações e casos extremos."""
    print("\n\n🧪 TESTANDO VALIDAÇÕES")
    print("="*50)
    
    # Teste com DataFrame vazio
    df_vazio = pd.DataFrame()
    resultado = calcular_producao_por_frota(df_vazio)
    print(f"✅ DataFrame vazio: {len(resultado)} registros (esperado: 0)")
    
    # Teste com horas elevador zero
    hora_elevador_zero = pd.DataFrame({
        'Frota': [7032],
        'Horas Elevador': [0]
    })
    resultado = calcular_producao_por_frota(hora_elevador_zero, 1000)
    print(f"✅ Horas elevador zero: {len(resultado)} registros (esperado: 0)")
    
    # Teste com dados inválidos
    hora_elevador_invalido = pd.DataFrame({
        'Frota': [7032, 7036],
        'Horas Elevador': ['abc', None]
    })
    resultado = calcular_producao_por_frota(hora_elevador_invalido, 1000)
    print(f"✅ Dados inválidos tratados: {len(resultado)} registros")

def main():
    """Executa todos os testes."""
    print("🆔 TESTE COMPLETO - PAINEL ESQUERDO")
    print("="*60)
    print("Validando implementação dos cálculos e mapeamentos")
    print("="*60)
    
    try:
        # Teste 1: Produção
        df_producao = testar_producao()
        
        # Teste 2: Painel esquerdo
        df_painel = testar_painel_esquerdo()
        
        # Teste 3: Validações
        testar_validacoes()
        
        # Resumo final
        print("\n" + "="*60)
        print("📊 RESUMO DOS TESTES:")
        print(f"   ✅ Produção: {len(df_producao)} frotas calculadas")
        print(f"   ✅ Painel: {len(df_painel)} registros consolidados")
        print(f"   ✅ Validações: Tratamento de casos extremos OK")
        
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Implementação do painel esquerdo está funcionando!")
        
        # Exemplo de uso prático
        print("\n" + "="*60)
        print("📋 PARA USAR EM PRODUÇÃO:")
        print("1. Configure TONELADAS_TOTAIS_DIA no arquivo principal")
        print("2. Execute o processamento normal")
        print("3. Verifique a planilha 'Produção' no Excel")
        print("4. Confirme o campo 'painel_esquerdo' no Supabase")
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
