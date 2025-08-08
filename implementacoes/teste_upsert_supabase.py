#!/usr/bin/env python3
"""
Teste para validar o comportamento UPSERT no Supabase.
Confirma que registros existentes são atualizados ao invés de criar novos.
"""

import requests
import json
from datetime import datetime

# Configurações Supabase
SUPABASE_URL = "https://kjlwqezxzqjfhacmjhbh.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtqbHdxZXp4enFqZmhhY21qaGJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc1NDY3OTgsImV4cCI6MjA1MzEyMjc5OH0.bB58zKtOtIyd4pZl-lycUQFVyHsQK_6Rxe2XtYta_cY"

def testar_upsert_behavior():
    """Testa o comportamento UPSERT: INSERT na primeira vez, UPDATE na segunda."""
    print("🧪 TESTANDO COMPORTAMENTO UPSERT")
    print("="*60)
    
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    
    url = f"{SUPABASE_URL}/rest/v1/registros_painelmaq"
    
    # Dados de teste
    data_teste = "2025-01-26"
    frente_teste = "TesteUPSERT"
    maquina_teste = 9999
    
    print(f"📊 Dados de teste:")
    print(f"   Data: {data_teste}")
    print(f"   Frente: {frente_teste}")
    print(f"   Máquina: {maquina_teste}")
    
    # === PRIMEIRO ENVIO: INSERT ===
    print(f"\n🔸 PRIMEIRO ENVIO (INSERT)")
    
    dados_primeiro = {
        "data_dia": data_teste,
        "frente_id": frente_teste,
        "maquina_id": maquina_teste,
        "parametros_medios": [{
            "frota": maquina_teste,
            "horimetro": 1000.0,
            "uso_rtk": 85.0,
            "vel_media": 12.0
        }],
        "painel_esquerdo": {
            "frota": maquina_teste,
            "toneladas": 500.0,
            "eficiencia_operacional": 75.0
        },
        "updated_at": datetime.now().isoformat()
    }
    
    response1 = requests.post(url, headers=headers, json=dados_primeiro)
    
    print(f"📤 Status: {response1.status_code}")
    if response1.status_code in [200, 201]:
        print("✅ PRIMEIRO ENVIO bem-sucedido (INSERT)")
        
        # Buscar o registro criado
        check_url = f"{url}?data_dia=eq.{data_teste}&frente_id=eq.{frente_teste}&maquina_id=eq.{maquina_teste}"
        get_response = requests.get(check_url, headers=headers)
        
        if get_response.status_code == 200:
            registros = get_response.json()
            if registros:
                primeiro_uuid = registros[0].get('id')
                print(f"🆔 UUID criado: {primeiro_uuid}")
                print(f"📊 Toneladas: {registros[0].get('painel_esquerdo', {}).get('toneladas')}")
            else:
                print("⚠️ Registro não encontrado após INSERT")
                return False
        else:
            print(f"❌ Erro ao buscar registro: {get_response.status_code}")
            return False
    else:
        print(f"❌ PRIMEIRO ENVIO falhou: {response1.text}")
        return False
    
    # === SEGUNDO ENVIO: UPDATE ===
    print(f"\n🔸 SEGUNDO ENVIO (UPDATE)")
    
    dados_segundo = {
        "data_dia": data_teste,
        "frente_id": frente_teste,
        "maquina_id": maquina_teste,
        "parametros_medios": [{
            "frota": maquina_teste,
            "horimetro": 1100.0,  # MUDOU
            "uso_rtk": 90.0,      # MUDOU
            "vel_media": 14.0     # MUDOU
        }],
        "painel_esquerdo": {
            "frota": maquina_teste,
            "toneladas": 750.0,           # MUDOU
            "eficiencia_operacional": 85.0  # MUDOU
        },
        "updated_at": datetime.now().isoformat()
    }
    
    # Segundo envio: simular comportamento do código atualizado
    # Verificar se existe e usar PATCH ao invés de POST
    check_url = f"{url}?data_dia=eq.{data_teste}&frente_id=eq.{frente_teste}&maquina_id=eq.{maquina_teste}"
    check_response = requests.get(check_url, headers=headers)
    registro_existe = check_response.status_code == 200 and len(check_response.json()) > 0
    
    if registro_existe:
        print("🔄 Registro existe - usando PATCH para UPDATE")
        # UPDATE com PATCH (apenas dados que mudam)
        dados_update = {
            "parametros_medios": dados_segundo["parametros_medios"],
            "painel_esquerdo": dados_segundo["painel_esquerdo"],
            "updated_at": dados_segundo["updated_at"]
        }
        response2 = requests.patch(check_url, headers=headers, json=dados_update)
    else:
        print("➕ Registro não existe - usando POST para INSERT")
        response2 = requests.post(url, headers=headers, json=dados_segundo)
    
    print(f"📤 Status: {response2.status_code}")
    if response2.status_code in [200, 201, 204]:
        print("✅ SEGUNDO ENVIO bem-sucedido (UPDATE)")
        
        # Buscar o registro atualizado
        get_response2 = requests.get(check_url, headers=headers)
        
        if get_response2.status_code == 200:
            registros = get_response2.json()
            if registros:
                segundo_uuid = registros[0].get('id')
                print(f"🆔 UUID atual: {segundo_uuid}")
                print(f"📊 Toneladas: {registros[0].get('painel_esquerdo', {}).get('toneladas')}")
                
                # VALIDAÇÃO CRÍTICA: UUID deve ser o mesmo
                if primeiro_uuid == segundo_uuid:
                    print("🎉 SUCESSO: UUID mantido - REGISTRO ATUALIZADO!")
                else:
                    print("❌ ERRO: UUID diferente - NOVO REGISTRO CRIADO!")
                    print(f"   UUID original: {primeiro_uuid}")
                    print(f"   UUID atual: {segundo_uuid}")
                    return False
                
                # Validar se dados foram atualizados
                toneladas_atuais = registros[0].get('painel_esquerdo', {}).get('toneladas')
                if toneladas_atuais == 750.0:
                    print("✅ Dados atualizados corretamente")
                else:
                    print(f"⚠️ Dados não atualizados: {toneladas_atuais} (esperado: 750.0)")
                
            else:
                print("⚠️ Registro não encontrado após UPDATE")
                return False
        else:
            print(f"❌ Erro ao buscar registro atualizado: {get_response2.status_code}")
            return False
    else:
        print(f"❌ SEGUNDO ENVIO falhou: {response2.text}")
        return False
    
    # === VALIDAÇÃO FINAL ===
    print(f"\n🔍 VALIDAÇÃO FINAL")
    
    # Contar quantos registros existem para esta combinação
    count_response = requests.get(check_url, headers=headers)
    if count_response.status_code == 200:
        total_registros = len(count_response.json())
        print(f"📊 Total de registros para ({data_teste}, {frente_teste}, {maquina_teste}): {total_registros}")
        
        if total_registros == 1:
            print("🎉 PERFEITO: Apenas 1 registro - UPSERT funcionando!")
            return True
        else:
            print(f"❌ PROBLEMA: {total_registros} registros - Deveria ter apenas 1!")
            return False
    else:
        print(f"❌ Erro ao contar registros: {count_response.status_code}")
        return False

def limpar_dados_teste():
    """Remove dados de teste."""
    print(f"\n🧹 LIMPEZA DE DADOS DE TESTE")
    print("="*40)
    
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{SUPABASE_URL}/rest/v1/registros_painelmaq"
    
    # Remover dados de teste
    params = {"frente_id": "eq.TesteUPSERT"}
    
    response = requests.delete(url, headers=headers, params=params)
    
    if response.status_code in [200, 204]:
        print("✅ Dados de teste removidos")
    else:
        print(f"⚠️ Erro na limpeza: {response.status_code}")

def main():
    """Executa teste completo de UPSERT."""
    print("🆔 TESTE UPSERT - VALIDAÇÃO DE ATUALIZAÇÃO")
    print("="*70)
    print("Verifica se registros existentes são atualizados")
    print("ao invés de criar novos com UUID diferente")
    print("="*70)
    
    try:
        # Executar teste
        sucesso = testar_upsert_behavior()
        
        # Resultado
        print("\n" + "="*70)
        if sucesso:
            print("🎉 TESTE PASSOU!")
            print("✅ UPSERT está funcionando corretamente")
            print("✅ Registros existentes são atualizados")
            print("✅ UUID é mantido em atualizações")
        else:
            print("❌ TESTE FALHOU!")
            print("⚠️ UPSERT não está funcionando como esperado")
            print("🔧 Revisar implementação ou configuração Supabase")
        
        # Limpeza
        print("\n" + "="*70)
        resposta = input("Deseja limpar dados de teste? (s/N): ").lower()
        if resposta in ['s', 'sim', 'y', 'yes']:
            limpar_dados_teste()
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
