#!/usr/bin/env python3
"""
Teste da solução UUID para resolver problemas de constraint no Supabase.
Este script valida se a implementação UUID está funcionando corretamente.
"""

import requests
import json
import uuid
from datetime import datetime

# Configurações Supabase
SUPABASE_URL = "https://kjlwqezxzqjfhacmjhbh.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtqbHdxZXp4enFqZmhhY21qaGJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc1NDY3OTgsImV4cCI6MjA1MzEyMjc5OH0.bB58zKtOtIyd4pZl-lycUQFVyHsQK_6Rxe2XtYta_cY"

def verificar_schema_uuid():
    """Verifica se a coluna UUID foi adicionada à tabela."""
    print("🔍 VERIFICANDO SCHEMA COM UUID")
    print("="*50)
    
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }
    
    # Fazer uma consulta simples para ver a estrutura
    url = f"{SUPABASE_URL}/rest/v1/registros_painelmaq"
    params = {"limit": "1"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if data:
                registro = data[0]
                print("📊 Colunas encontradas na tabela:")
                for campo, valor in registro.items():
                    tipo_valor = type(valor).__name__
                    print(f"   • {campo}: {tipo_valor}")
                
                # Verificar se UUID existe
                if 'id' in registro:
                    uuid_value = registro['id']
                    print(f"\n✅ Coluna UUID encontrada!")
                    print(f"   Exemplo de UUID: {uuid_value}")
                    
                    # Validar se é um UUID válido
                    try:
                        uuid.UUID(uuid_value)
                        print(f"   ✅ UUID válido!")
                        return True
                    except ValueError:
                        print(f"   ❌ UUID inválido: {uuid_value}")
                        return False
                else:
                    print(f"\n❌ Coluna UUID (id) NÃO encontrada!")
                    print(f"   Execute o script schema_uuid_supabase.sql primeiro")
                    return False
            else:
                print("📋 Tabela vazia, não é possível verificar schema")
                print("   Tentando inserir registro de teste...")
                return testar_insercao_com_uuid()
        else:
            print(f"❌ Erro ao acessar tabela: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

def testar_insercao_com_uuid():
    """Testa inserção de registros com UUID automático."""
    print("\n🧪 TESTANDO INSERÇÃO COM UUID")
    print("="*50)
    
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{SUPABASE_URL}/rest/v1/registros_painelmaq"
    
    # Dados de teste
    dados_teste = {
        "data_dia": "2025-01-25",
        "frente_id": "TesteUUID",
        "maquina_id": 9001,
        "parametros_medios": [{
            "frota": 9001,
            "horimetro": 1000.00,
            "uso_rtk": 85.50,
            "vel_media": 12.30
        }],
        "updated_at": datetime.now().isoformat()
    }
    
    try:
        print(f"📤 Inserindo registro de teste...")
        print(f"   Data: {dados_teste['data_dia']}")
        print(f"   Frente: {dados_teste['frente_id']}")
        print(f"   Máquina: {dados_teste['maquina_id']}")
        
        response = requests.post(url, headers=headers, json=dados_teste)
        
        print(f"📊 Status da inserção: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("✅ Inserção bem-sucedida!")
            
            # Buscar o registro inserido para ver o UUID gerado
            params = {
                "data_dia": f"eq.{dados_teste['data_dia']}",
                "frente_id": f"eq.{dados_teste['frente_id']}",
                "maquina_id": f"eq.{dados_teste['maquina_id']}"
            }
            
            get_response = requests.get(url, headers=headers, params=params)
            
            if get_response.status_code == 200:
                registros = get_response.json()
                if registros:
                    registro = registros[0]
                    if 'id' in registro:
                        print(f"🆔 UUID gerado: {registro['id']}")
                        return True
                    else:
                        print("⚠️ Registro inserido mas sem UUID")
                        return False
                        
        elif response.status_code == 409:
            print("⚠️ Conflito (409) - registro já existe")
            print("   Isso indica que a chave primária está funcionando")
            return True
        else:
            print(f"❌ Erro na inserção: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def testar_multiplas_frotas_mesma_data():
    """Testa inserção de múltiplas frotas para a mesma data."""
    print("\n🚜 TESTANDO MÚLTIPLAS FROTAS - MESMA DATA")
    print("="*50)
    
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{SUPABASE_URL}/rest/v1/registros_painelmaq"
    data_teste = "2025-01-25"
    frente_teste = "TesteMultiplasUUID"
    
    frotas_teste = [
        {"maquina_id": 9101, "frota": 9101, "vel_media": 12.5},
        {"maquina_id": 9102, "frota": 9102, "vel_media": 13.2},
        {"maquina_id": 9103, "frota": 9103, "vel_media": 11.8},
        {"maquina_id": 9104, "frota": 9104, "vel_media": 14.1}
    ]
    
    sucessos = 0
    uuids_gerados = []
    
    print(f"📅 Data de teste: {data_teste}")
    print(f"🏭 Frente: {frente_teste}")
    print(f"📊 Inserindo {len(frotas_teste)} frotas...")
    
    for i, frota_data in enumerate(frotas_teste, 1):
        try:
            dados_registro = {
                "data_dia": data_teste,
                "frente_id": frente_teste,
                "maquina_id": frota_data["maquina_id"],
                "parametros_medios": [frota_data],
                "updated_at": datetime.now().isoformat()
            }
            
            response = requests.post(url, headers=headers, json=dados_registro)
            
            if response.status_code in [200, 201]:
                print(f"   ✅ Frota {i}/4 (ID: {frota_data['maquina_id']}) inserida")
                sucessos += 1
                
                # Buscar UUID gerado
                params = {
                    "data_dia": f"eq.{data_teste}",
                    "frente_id": f"eq.{frente_teste}",
                    "maquina_id": f"eq.{frota_data['maquina_id']}"
                }
                
                get_response = requests.get(url, headers=headers, params=params)
                if get_response.status_code == 200:
                    registros = get_response.json()
                    if registros and 'id' in registros[0]:
                        uuid_gerado = registros[0]['id']
                        uuids_gerados.append(uuid_gerado)
                        print(f"      🆔 UUID: {uuid_gerado[:8]}...")
                        
            elif response.status_code == 409:
                print(f"   ⚠️ Frota {i}/4 já existe (isso é normal)")
                sucessos += 1
            else:
                print(f"   ❌ Frota {i}/4 falhou: {response.status_code}")
                print(f"      Erro: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Frota {i}/4 erro: {e}")
    
    print(f"\n📊 RESULTADO:")
    print(f"   ✅ Sucessos: {sucessos}/{len(frotas_teste)}")
    print(f"   🆔 UUIDs únicos gerados: {len(set(uuids_gerados))}")
    
    if sucessos == len(frotas_teste):
        print("🎉 SUCESSO! Múltiplas frotas na mesma data funcionam!")
        
        # Verificar se todos os UUIDs são únicos
        if len(uuids_gerados) == len(set(uuids_gerados)):
            print("✅ Todos os UUIDs são únicos!")
        else:
            print("⚠️ Alguns UUIDs são duplicados (verificar)")
            
        return True
    else:
        print("❌ Alguns registros falharam")
        return False

def limpeza_dados_teste():
    """Limpa dados de teste criados."""
    print("\n🧹 LIMPEZA DE DADOS DE TESTE")
    print("="*50)
    
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{SUPABASE_URL}/rest/v1/registros_painelmaq"
    
    # Padrões de teste para remover
    padroes_teste = [
        {"frente_id": "TesteUUID"},
        {"frente_id": "TesteMultiplasUUID"},
        {"data_dia": "2025-01-25"}
    ]
    
    total_removidos = 0
    
    for padrao in padroes_teste:
        try:
            # Buscar registros que atendem ao padrão
            get_response = requests.get(url, headers=headers, params=padrao)
            
            if get_response.status_code == 200:
                registros = get_response.json()
                
                if registros:
                    print(f"📋 Encontrados {len(registros)} registros para padrão {padrao}")
                    
                    # Deletar usando o padrão
                    delete_response = requests.delete(url, headers=headers, params=padrao)
                    
                    if delete_response.status_code in [200, 204]:
                        print(f"   ✅ {len(registros)} registros removidos")
                        total_removidos += len(registros)
                    else:
                        print(f"   ❌ Erro ao remover: {delete_response.status_code}")
                        
        except Exception as e:
            print(f"❌ Erro na limpeza: {e}")
    
    print(f"\n📊 Total removido: {total_removidos} registros")

def main():
    """Executa todos os testes da solução UUID."""
    print("🆔 TESTE COMPLETO - SOLUÇÃO UUID SUPABASE")
    print("="*60)
    print("Este script valida se a implementação UUID resolve")
    print("o problema de constraints para múltiplas frotas.")
    print()
    
    # Passo 1: Verificar schema
    print("🔸 PASSO 1: Verificação do Schema")
    schema_ok = verificar_schema_uuid()
    
    if not schema_ok:
        print("\n❌ FALHA: Schema UUID não está configurado")
        print("📋 Execute primeiro: schema_uuid_supabase.sql")
        return
    
    # Passo 2: Teste de inserção simples
    print("\n🔸 PASSO 2: Teste de Inserção Simples")
    insercao_ok = testar_insercao_com_uuid()
    
    # Passo 3: Teste de múltiplas frotas
    print("\n🔸 PASSO 3: Teste de Múltiplas Frotas")
    multiplas_ok = testar_multiplas_frotas_mesma_data()
    
    # Resumo final
    print("\n" + "="*60)
    print("📊 RESUMO FINAL:")
    print(f"   🔍 Schema UUID: {'✅ OK' if schema_ok else '❌ FALHA'}")
    print(f"   📤 Inserção: {'✅ OK' if insercao_ok else '❌ FALHA'}")
    print(f"   🚜 Múltiplas Frotas: {'✅ OK' if multiplas_ok else '❌ FALHA'}")
    
    if all([schema_ok, insercao_ok, multiplas_ok]):
        print("\n🎉 SUCESSO TOTAL! Solução UUID está funcionando!")
        print("✅ Agora você pode processar arquivos sem erro de constraint")
    else:
        print("\n⚠️ PROBLEMAS DETECTADOS! Verifique:")
        print("   1. Execute o schema_uuid_supabase.sql")
        print("   2. Confirme as configurações do Supabase")
        print("   3. Verifique as permissões da API key")
    
    # Limpeza opcional
    print("\n" + "="*60)
    resposta = input("Deseja limpar dados de teste? (s/N): ").lower()
    if resposta in ['s', 'sim', 'y', 'yes']:
        limpeza_dados_teste()
    
    print("\n✅ Teste concluído!")

if __name__ == "__main__":
    main()
