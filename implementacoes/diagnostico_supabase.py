#!/usr/bin/env python3
"""
Script de diagnóstico para identificar e resolver o problema de constraint
no Supabase que está impedindo o envio de múltiplas frotas.
"""

import requests
import json

# Configurações Supabase
SUPABASE_URL = "https://kjlwqezxzqjfhacmjhbh.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtqbHdxZXp4enFqZmhhY21qaGJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc1NDY3OTgsImV4cCI6MjA1MzEyMjc5OH0.bB58zKtOtIyd4pZl-lycUQFVyHsQK_6Rxe2XtYta_cY"

def diagnosticar_problema():
    """Diagnostica o problema de constraint no Supabase."""
    
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }
    
    print("🔍 DIAGNÓSTICO DO PROBLEMA SUPABASE")
    print("="*50)
    
    # 1. Verificar registros existentes para a data problemática
    print("\n1️⃣ Verificando registros existentes para 2025-08-07:")
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/registros_painelmaq"
        params = {"data_dia": "eq.2025-08-07"}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            registros = response.json()
            print(f"   📊 Total de registros encontrados: {len(registros)}")
            
            if registros:
                print("   📋 Registros existentes:")
                for registro in registros:
                    print(f"      • {registro['data_dia']} | {registro['frente_id']} | Máquina: {registro['maquina_id']}")
            else:
                print("   ⚠️ Nenhum registro encontrado para esta data")
        else:
            print(f"   ❌ Erro ao consultar: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro na consulta: {e}")
    
    # 2. Tentar inserir um registro de teste
    print("\n2️⃣ Testando inserção de registro:")
    
    dados_teste = {
        "data_dia": "2025-08-07",
        "frente_id": "TesteConstraint",
        "maquina_id": 9999,
        "parametros_medios": [{"frota": 9999, "teste": True}],
    }
    
    try:
        response = requests.post(url, headers=headers, json=dados_teste)
        
        print(f"   📊 Status da inserção: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("   ✅ Inserção bem-sucedida!")
        elif response.status_code == 409:
            error_data = response.json()
            print(f"   ❌ Conflict (409): {error_data.get('message', 'Unknown error')}")
            
            if "uniq_registro_dia" in str(error_data):
                print("   🎯 PROBLEMA IDENTIFICADO: Constraint 'uniq_registro_dia'")
                print("      Esta constraint impede múltiplos registros por data")
                print("      Solução: Remover o índice único 'uniq_registro_dia'")
        else:
            print(f"   ❌ Erro: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Erro na inserção: {e}")
    
    # 3. Sugestões de correção
    print("\n3️⃣ SOLUÇÕES RECOMENDADAS:")
    print("="*50)
    
    print("✅ SOLUÇÃO 1 - Remover constraint via SQL (RECOMENDADO):")
    print("   1. Acesse o Supabase Dashboard")
    print("   2. Vá em 'SQL Editor'")
    print("   3. Execute: DROP INDEX IF EXISTS public.uniq_registro_dia;")
    print("   4. Execute novamente o processamento")
    
    print("\n✅ SOLUÇÃO 2 - Verificar schema da tabela:")
    print("   1. Confirme que a chave primária é (data_dia, frente_id, maquina_id)")
    print("   2. Remova qualquer índice único apenas em 'data_dia'")
    
    print("\n✅ SOLUÇÃO 3 - Usando nossa função de limpeza:")
    print("   1. Execute: limpar_registros_data('2025-08-07')")
    print("   2. Tente novamente o processamento")

def limpar_registros_data(data_dia):
    """Remove todos os registros de uma data específica."""
    
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🧹 LIMPANDO REGISTROS DA DATA: {data_dia}")
    print("="*50)
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/registros_painelmaq"
        params = {"data_dia": f"eq.{data_dia}"}
        
        # Primeiro, ver quantos registros existem
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            registros = response.json()
            print(f"📊 Registros encontrados: {len(registros)}")
            
            if registros:
                # Deletar todos os registros desta data
                response_delete = requests.delete(url, headers=headers, params=params)
                
                if response_delete.status_code in [200, 204]:
                    print(f"✅ {len(registros)} registros removidos com sucesso!")
                    print("   Agora você pode tentar processar novamente")
                else:
                    print(f"❌ Erro ao deletar: {response_delete.status_code}")
            else:
                print("ℹ️ Nenhum registro encontrado para deletar")
        else:
            print(f"❌ Erro ao consultar registros: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro durante limpeza: {e}")

def testar_multiplas_frotas():
    """Testa inserção de múltiplas frotas para a mesma data."""
    
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    
    print("\n🧪 TESTANDO MÚLTIPLAS FROTAS:")
    print("="*50)
    
    frotas_teste = [
        {"data_dia": "2025-01-25", "frente_id": "TesteMultiplas", "maquina_id": 8001, "parametros_medios": [{"frota": 8001}]},
        {"data_dia": "2025-01-25", "frente_id": "TesteMultiplas", "maquina_id": 8002, "parametros_medios": [{"frota": 8002}]},
        {"data_dia": "2025-01-25", "frente_id": "TesteMultiplas", "maquina_id": 8003, "parametros_medios": [{"frota": 8003}]},
    ]
    
    url = f"{SUPABASE_URL}/rest/v1/registros_painelmaq"
    sucessos = 0
    
    for i, frota in enumerate(frotas_teste, 1):
        try:
            response = requests.post(url, headers=headers, json=frota)
            
            if response.status_code in [200, 201]:
                print(f"   ✅ Frota {i}/3 inserida com sucesso")
                sucessos += 1
            else:
                error_data = response.json() if response.content else {}
                print(f"   ❌ Frota {i}/3 falhou: {response.status_code}")
                print(f"      Erro: {error_data.get('message', 'Unknown')}")
                
        except Exception as e:
            print(f"   ❌ Frota {i}/3 erro: {e}")
    
    print(f"\n📊 Resultado: {sucessos}/3 frotas inseridas")
    
    if sucessos == 3:
        print("🎉 SUCESSO! O problema foi resolvido!")
    elif sucessos == 0:
        print("🚨 PROBLEMA PERSISTE! Execute a correção SQL")
    else:
        print("⚠️ PROBLEMA PARCIAL! Verifique configurações")

if __name__ == "__main__":
    print("🔧 DIAGNÓSTICO E CORREÇÃO - PROBLEMA SUPABASE")
    print("Este script identifica e ajuda a resolver o problema de constraint")
    print()
    
    # Executar diagnóstico
    diagnosticar_problema()
    
    # Perguntar se quer limpar dados de teste
    print("\n" + "="*60)
    resposta = input("Deseja limpar registros da data 2025-08-07? (s/N): ").lower()
    
    if resposta in ['s', 'sim', 'y', 'yes']:
        limpar_registros_data("2025-08-07")
    
    # Testar múltiplas frotas
    print("\n" + "="*60)
    resposta2 = input("Deseja testar inserção de múltiplas frotas? (s/N): ").lower()
    
    if resposta2 in ['s', 'sim', 'y', 'yes']:
        testar_multiplas_frotas()
    
    print("\n✅ Diagnóstico concluído!")
    print("📋 Próximos passos:")
    print("   1. Execute a correção SQL no Supabase Dashboard")
    print("   2. Execute novamente o processamento de arquivos")
    print("   3. Verifique se os dados são inseridos corretamente")
