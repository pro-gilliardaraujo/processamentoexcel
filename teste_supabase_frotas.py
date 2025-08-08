#!/usr/bin/env python3
"""
Teste da integração Supabase - um registro por frota.
"""

import pandas as pd
import requests
from datetime import datetime

# Configurações Supabase
SUPABASE_URL = "https://kjlwqezxzqjfhacmjhbh.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtqbHdxZXp4enFqZmhhY21qaGJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc1NDY3OTgsImV4cCI6MjA1MzEyMjc5OH0.bB58zKtOtIyd4pZl-lycUQFVyHsQK_6Rxe2XtYta_cY"

def criar_dados_teste_multiplas_frotas():
    """Cria dados de teste simulando múltiplas frotas."""
    dados_teste = [
        {
            "Frota": 7032,
            "Horimetro": 1234.50,
            "Uso RTK (%)": 85.67,
            "Horas Elevador": 8.25,
            "Horas Motor": 9.50,
            "Velocidade Media (km/h)": 12.30,
            "RPM Motor Media": 2100.00,
            "RPM Extrator Media": 850.00,
            "Pressao Corte Media (psi)": 450.00,
            "Corte Base Auto (%)": 95.25
        },
        {
            "Frota": 7042,
            "Horimetro": 1156.75,
            "Uso RTK (%)": 78.90,
            "Horas Elevador": 7.80,
            "Horas Motor": 8.90,
            "Velocidade Media (km/h)": 11.80,
            "RPM Motor Media": 2050.00,
            "RPM Extrator Media": 825.00,
            "Pressao Corte Media (psi)": 440.00,
            "Corte Base Auto (%)": 92.50
        },
        {
            "Frota": 7052,
            "Horimetro": 987.25,
            "Uso RTK (%)": 92.15,
            "Horas Elevador": 6.50,
            "Horas Motor": 7.75,
            "Velocidade Media (km/h)": 13.20,
            "RPM Motor Media": 2150.00,
            "RPM Extrator Media": 875.00,
            "Pressao Corte Media (psi)": 465.00,
            "Corte Base Auto (%)": 98.75
        }
    ]
    
    return pd.DataFrame(dados_teste)

def teste_envio_frotas_separadas():
    """Testa o envio de cada frota como registro separado."""
    try:
        df_teste = criar_dados_teste_multiplas_frotas()
        
        print("📊 Dados de teste - Múltiplas frotas:")
        print(df_teste.to_string(index=False))
        print("\n" + "="*60)
        
        # Simulação dos parâmetros
        data_dia = "2025-08-05"
        frente_id = "Frente03"
        
        # Headers
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/registros_painelmaq"
        
        print(f"📡 Enviando cada frota como registro separado...")
        print(f"📅 Data: {data_dia} | 🏭 Frente: {frente_id}")
        print(f"📊 Total de frotas: {len(df_teste)}")
        print("-" * 60)
        
        sucessos = 0
        erros = 0
        
        # Processar cada frota individualmente
        for index, linha in df_teste.iterrows():
            try:
                frota = int(linha['Frota'])
                maquina_id = frota  # Usar número da frota como maquina_id
                
                # Converter linha em dict
                parametros_frota = linha.to_dict()
                
                # Dados para esta frota específica
                dados_registro = {
                    "data_dia": data_dia,
                    "frente_id": frente_id,
                    "maquina_id": maquina_id,
                    "parametros_medios": [parametros_frota],
                    "updated_at": datetime.now().isoformat()
                }
                
                print(f"   🚜 Enviando frota {frota} (maquina_id: {maquina_id})...")
                
                response = requests.post(url, headers=headers, json=dados_registro)
                
                if response.status_code in [200, 201]:
                    print(f"      ✅ Frota {frota} enviada com sucesso")
                    sucessos += 1
                else:
                    print(f"      ❌ Erro frota {frota}: {response.status_code}")
                    print(f"         Resposta: {response.text[:200]}")
                    erros += 1
                    
            except Exception as e:
                print(f"      ❌ Erro ao processar frota {linha.get('Frota', 'N/A')}: {e}")
                erros += 1
        
        print("\n" + "="*60)
        print(f"📋 RESUMO DO TESTE:")
        print(f"   ✅ Sucessos: {sucessos}")
        print(f"   ❌ Erros: {erros}")
        print(f"   📊 Total processado: {len(df_teste)}")
        
        return sucessos > 0
        
    except Exception as e:
        print(f"❌ Erro geral no teste: {e}")
        return False

def verificar_registros_criados():
    """Verifica se os registros foram criados corretamente."""
    try:
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/registros_painelmaq"
        params = {
            "data_dia": "eq.2025-08-05",
            "frente_id": "eq.Frente03"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            registros = response.json()
            print(f"\n🔍 VERIFICAÇÃO DOS REGISTROS CRIADOS:")
            print(f"   📊 Total de registros encontrados: {len(registros)}")
            
            for registro in registros:
                maquina_id = registro['maquina_id']
                parametros = registro.get('parametros_medios', [])
                if parametros:
                    frota = parametros[0].get('Frota', 'N/A')
                    print(f"   🚜 Máquina ID: {maquina_id} | Frota: {frota}")
                else:
                    print(f"   🚜 Máquina ID: {maquina_id} | Sem parâmetros")
            
            return True
        else:
            print(f"❌ Erro ao verificar registros: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTE - UM REGISTRO POR FROTA")
    print("="*60)
    
    if teste_envio_frotas_separadas():
        verificar_registros_criados()
    else:
        print("❌ Teste falhou")
