#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Painel Direito - Verificação da Integração
"""

import pandas as pd
import sys
import os

# Adicionar o diretório scripts ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from scripts.processamento_colhedoras import calcular_painel_direito

def teste_painel_direito_com_dados():
    """Teste com dados simulados de lavagem e ofensores"""
    
    print("=== TESTE 1: Painel Direito com Dados ===")
    
    # Dados simulados de lavagem
    df_lavagem = pd.DataFrame([
        {
            'Data': '2025-08-07',
            'Equipamento': 7032,
            'Intervalo': 1,
            'Início': '08:30:00',
            'Fim': '09:15:00',
            'Duração (horas)': 0.75,
            'Tempo Total do Dia': 1.5
        },
        {
            'Data': '2025-08-07',
            'Equipamento': 7032,
            'Intervalo': 2,
            'Início': '14:20:00',
            'Fim': '15:05:00',
            'Duração (horas)': 0.75,
            'Tempo Total do Dia': 1.5
        },
        {
            'Data': '2025-08-07',
            'Equipamento': 7036,
            'Intervalo': 1,
            'Início': '10:30:00',
            'Fim': '11:27:00',
            'Duração (horas)': 0.95,
            'Tempo Total do Dia': 0.95
        }
    ])
    
    # Dados simulados de ofensores (testando cenário problemático)
    df_ofensores = pd.DataFrame([
        {
            'Operação': '8040 - MANUTENCAO CORRETIVA',
            'Tempo': 45.67,
            'Porcentagem': '35.2%'
        },
        {
            'Operação': '8000 - DESLOCAMENTO',
            'Tempo': 38.92,
            'Porcentagem': '28.7%'
        },
        {
            'Operação': '8010 - PARADA TECNICA',
            'Tempo': 25.13,
            'Porcentagem': '18.5%'
        },
        {
            'Operação': '7032',  # Caso onde tem equipamento como string
            'Tempo': 15.8,
            'Porcentagem': '11.6%'
        },
        {
            'Operação': 7034,  # Caso onde tem equipamento como número
            'Tempo': 8.2,
            'Porcentagem': '6.0%'
        }
    ])
    
    # Executar o cálculo
    resultado = calcular_painel_direito(df_lavagem, df_ofensores)
    
    print("\n📊 RESULTADO DO TESTE:")
    print(f"Lavagem - Tem dados: {resultado['lavagem']['tem_dados']}")
    print(f"Lavagem - Total intervalos: {resultado['lavagem']['total_intervalos']}")
    print(f"Lavagem - Tempo total: {resultado['lavagem']['tempo_total_horas']:.2f}h")
    print(f"Lavagem - Equipamentos: {len(resultado['lavagem']['equipamentos'])}")
    
    for equip in resultado['lavagem']['equipamentos']:
        print(f"  🚜 Equipamento {equip['equipamento']}: {equip['intervalos']} intervalos, {equip['tempo_total_horas']:.2f}h")
    
    print(f"\nOfensores - Total registros: {len(resultado['ofensores'])}")
    for i, ofensor in enumerate(resultado['ofensores']):
        print(f"  ⚠️ Ofensor {i+1}: Equipamento {ofensor['equipamento']}, Operação: {ofensor.get('operacao', 'N/A')}")
    
    return resultado

def teste_painel_direito_sem_dados():
    """Teste com dados vazios/ausentes"""
    
    print("\n=== TESTE 2: Painel Direito Sem Dados ===")
    
    # DataFrame vazio de lavagem com mensagem informativa
    df_lavagem = pd.DataFrame([{
        'Data': 'N/A',
        'Equipamento': 'NÃO FORAM ENCONTRADOS DADOS DE LAVAGEM PARA A DATA INFORMADA',
        'Intervalo': 'N/A',
        'Início': 'N/A',
        'Fim': 'N/A',
        'Duração (horas)': 0,
        'Tempo Total do Dia': 0
    }])
    
    # DataFrame vazio de ofensores
    df_ofensores = pd.DataFrame()
    
    # Executar o cálculo
    resultado = calcular_painel_direito(df_lavagem, df_ofensores)
    
    print("\n📊 RESULTADO DO TESTE:")
    print(f"Lavagem - Tem dados: {resultado['lavagem']['tem_dados']}")
    print(f"Lavagem - Total intervalos: {resultado['lavagem']['total_intervalos']}")
    print(f"Lavagem - Tempo total: {resultado['lavagem']['tempo_total_horas']:.2f}h")
    print(f"Ofensores - Total registros: {len(resultado['ofensores'])}")
    
    return resultado

def teste_estrutura_json():
    """Teste da estrutura JSON final"""
    
    print("\n=== TESTE 3: Estrutura JSON Final ===")
    
    resultado1 = teste_painel_direito_com_dados()
    
    # Simular payload completo do Supabase
    payload_exemplo = {
        "data_dia": "2025-08-07",
        "frente_id": "Frente04",
        "maquina_id": 7032,
        "parametros_medios": [{"frota": 7032, "horimetro": 14067.9}],
        "painel_esquerdo": {"frota": 7032, "horas_registradas": 23.34},
        "painel_direito": resultado1,
        "updated_at": "2025-01-08T10:30:00"
    }
    
    print("\n🔍 PAYLOAD COMPLETO PARA SUPABASE:")
    import json
    print(json.dumps(payload_exemplo, indent=2, ensure_ascii=False))
    
    return payload_exemplo

if __name__ == "__main__":
    print("🧪 INICIANDO TESTES DO PAINEL DIREITO")
    print("="*50)
    
    try:
        # Teste 1: Com dados
        resultado1 = teste_painel_direito_com_dados()
        
        # Teste 2: Sem dados
        resultado2 = teste_painel_direito_sem_dados()
        
        # Teste 3: Estrutura JSON
        payload = teste_estrutura_json()
        
        print("\n✅ TODOS OS TESTES EXECUTADOS COM SUCESSO!")
        print("="*50)
        
        # Verificações
        assert resultado1['lavagem']['tem_dados'] == True
        assert resultado1['lavagem']['total_intervalos'] > 0
        assert len(resultado1['ofensores']) > 0
        
        assert resultado2['lavagem']['tem_dados'] == False
        assert resultado2['lavagem']['total_intervalos'] == 0
        assert len(resultado2['ofensores']) == 0
        
        print("✅ Todas as asserções passaram!")
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
