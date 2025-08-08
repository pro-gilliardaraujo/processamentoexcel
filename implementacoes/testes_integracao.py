#!/usr/bin/env python3
"""
Testes de integração para validar o funcionamento da integração com Supabase.

Este arquivo contém testes práticos para verificar se a implementação está
funcionando corretamente em diferentes cenários.
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import time

# Configurações Supabase (mesmas do sistema principal)
SUPABASE_URL = "https://kjlwqezxzqjfhacmjhbh.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtqbHdxZXp4enFqZmhhY21qaGJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc1NDY3OTgsImV4cCI6MjA1MzEyMjc5OH0.bB58zKtOtIyd4pZl-lycUQFVyHsQK_6Rxe2XtYta_cY"

class TestesIntegracaoSupabase:
    """Classe para executar testes de integração com Supabase."""
    
    def __init__(self):
        self.headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
        self.base_url = f"{SUPABASE_URL}/rest/v1/registros_painelmaq"
        self.resultados_testes = []
    
    def log_resultado(self, teste, sucesso, mensagem=""):
        """Registra o resultado de um teste."""
        resultado = {
            "teste": teste,
            "sucesso": sucesso,
            "mensagem": mensagem,
            "timestamp": datetime.now().isoformat()
        }
        self.resultados_testes.append(resultado)
        
        status = "✅ PASSOU" if sucesso else "❌ FALHOU"
        print(f"{status} | {teste}")
        if mensagem:
            print(f"         {mensagem}")
    
    def teste_1_conexao_basica(self):
        """Teste 1: Verificar se conseguimos conectar ao Supabase."""
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            sucesso = response.status_code == 200
            mensagem = f"Status: {response.status_code}"
            
            if sucesso:
                data = response.json()
                mensagem += f" | {len(data)} registros encontrados"
            
            self.log_resultado("Conexão Básica", sucesso, mensagem)
            return sucesso
            
        except Exception as e:
            self.log_resultado("Conexão Básica", False, f"Erro: {str(e)}")
            return False
    
    def teste_2_conversao_chaves(self):
        """Teste 2: Verificar conversão de chaves snake_case."""
        try:
            from conversao_chaves_snake_case import converter_chaves_snake_case
            
            # Dados de teste
            dados_originais = {
                "Frota": 9999,
                "Uso RTK (%)": 99.99,
                "Velocidade Media (km/h)": 15.5
            }
            
            dados_convertidos = converter_chaves_snake_case(dados_originais)
            
            # Verificações
            verificacoes = [
                ("frota" in dados_convertidos, "Chave 'frota' existe"),
                ("uso_rtk" in dados_convertidos, "Chave 'uso_rtk' existe"),
                ("vel_media" in dados_convertidos, "Chave 'vel_media' existe"),
                (dados_convertidos["frota"] == 9999, "Valor frota preservado"),
                (dados_convertidos["uso_rtk"] == 99.99, "Valor uso_rtk preservado")
            ]
            
            todas_passou = all(check for check, _ in verificacoes)
            falhas = [desc for check, desc in verificacoes if not check]
            
            mensagem = "Todas as verificações passaram" if todas_passou else f"Falhas: {', '.join(falhas)}"
            self.log_resultado("Conversão Snake_Case", todas_passou, mensagem)
            return todas_passou
            
        except ImportError:
            self.log_resultado("Conversão Snake_Case", False, "Erro: Não foi possível importar módulo de conversão")
            return False
        except Exception as e:
            self.log_resultado("Conversão Snake_Case", False, f"Erro: {str(e)}")
            return False
    
    def teste_3_insercao_registro(self):
        """Teste 3: Inserir um registro de teste no Supabase."""
        try:
            # Dados de teste
            dados_teste = {
                "data_dia": "2025-01-24",
                "frente_id": "TesteIntegracao",
                "maquina_id": 9999,
                "parametros_medios": [{
                    "frota": 9999,
                    "horimetro": 1000.00,
                    "uso_rtk": 95.5,
                    "horas_elevador": 8.0,
                    "horas_motor": 9.0,
                    "vel_media": 13.5,
                    "rpm_motor_media": 2100.0,
                    "rpm_extrator_media": 850.0,
                    "pressao_corte_media": 450.0,
                    "corte_base_auto": 98.0
                }],
                "updated_at": datetime.now().isoformat()
            }
            
            headers_upsert = self.headers.copy()
            headers_upsert["Prefer"] = "resolution=merge-duplicates"
            
            response = requests.post(
                self.base_url,
                headers=headers_upsert,
                json=dados_teste,
                timeout=10
            )
            
            sucesso = response.status_code in [200, 201]
            mensagem = f"Status: {response.status_code}"
            
            if not sucesso:
                mensagem += f" | Erro: {response.text[:100]}"
            
            self.log_resultado("Inserção de Registro", sucesso, mensagem)
            return sucesso
            
        except Exception as e:
            self.log_resultado("Inserção de Registro", False, f"Erro: {str(e)}")
            return False
    
    def teste_4_consulta_registro(self):
        """Teste 4: Consultar o registro inserido."""
        try:
            params = {
                "data_dia": "eq.2025-01-24",
                "frente_id": "eq.TesteIntegracao",
                "maquina_id": "eq.9999"
            }
            
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            sucesso = response.status_code == 200
            mensagem = f"Status: {response.status_code}"
            
            if sucesso:
                data = response.json()
                if data:
                    registro = data[0]
                    params_medios = registro.get("parametros_medios", [])
                    if params_medios:
                        frota = params_medios[0].get("frota")
                        vel_media = params_medios[0].get("vel_media")
                        mensagem += f" | Frota: {frota}, Velocidade: {vel_media}"
                    else:
                        mensagem += " | Sem parâmetros médios"
                else:
                    mensagem += " | Registro não encontrado"
                    sucesso = False
            
            self.log_resultado("Consulta de Registro", sucesso, mensagem)
            return sucesso
            
        except Exception as e:
            self.log_resultado("Consulta de Registro", False, f"Erro: {str(e)}")
            return False
    
    def teste_5_atualizacao_registro(self):
        """Teste 5: Atualizar o registro existente (UPSERT)."""
        try:
            # Dados atualizados
            dados_atualizados = {
                "data_dia": "2025-01-24",
                "frente_id": "TesteIntegracao",
                "maquina_id": 9999,
                "parametros_medios": [{
                    "frota": 9999,
                    "horimetro": 1100.00,  # Valor atualizado
                    "uso_rtk": 96.5,       # Valor atualizado
                    "horas_elevador": 8.5,
                    "horas_motor": 9.5,
                    "vel_media": 14.0,     # Valor atualizado
                    "rpm_motor_media": 2150.0,
                    "rpm_extrator_media": 875.0,
                    "pressao_corte_media": 460.0,
                    "corte_base_auto": 99.0
                }],
                "updated_at": datetime.now().isoformat()
            }
            
            headers_upsert = self.headers.copy()
            headers_upsert["Prefer"] = "resolution=merge-duplicates"
            
            response = requests.post(
                self.base_url,
                headers=headers_upsert,
                json=dados_atualizados,
                timeout=10
            )
            
            sucesso = response.status_code in [200, 201]
            mensagem = f"Status: {response.status_code}"
            
            # Verificar se foi realmente atualizado
            if sucesso:
                time.sleep(1)  # Aguardar propagação
                params = {
                    "data_dia": "eq.2025-01-24",
                    "frente_id": "eq.TesteIntegracao",
                    "maquina_id": "eq.9999"
                }
                
                check_response = requests.get(self.base_url, headers=self.headers, params=params)
                if check_response.status_code == 200:
                    data = check_response.json()
                    if data:
                        novo_horimetro = data[0]["parametros_medios"][0]["horimetro"]
                        if novo_horimetro == 1100.00:
                            mensagem += " | Atualização confirmada"
                        else:
                            mensagem += f" | Horimetro: {novo_horimetro} (esperado: 1100.00)"
            
            self.log_resultado("Atualização de Registro", sucesso, mensagem)
            return sucesso
            
        except Exception as e:
            self.log_resultado("Atualização de Registro", False, f"Erro: {str(e)}")
            return False
    
    def teste_6_multiplas_frotas(self):
        """Teste 6: Inserir múltiplas frotas para a mesma data/frente."""
        try:
            frotas_teste = [9991, 9992, 9993]
            sucessos = 0
            
            for frota in frotas_teste:
                dados_frota = {
                    "data_dia": "2025-01-24",
                    "frente_id": "TesteMultiplas",
                    "maquina_id": frota,
                    "parametros_medios": [{
                        "frota": frota,
                        "horimetro": 1000.00 + frota,
                        "uso_rtk": 90.0 + (frota % 10),
                        "horas_elevador": 8.0,
                        "horas_motor": 9.0,
                        "vel_media": 12.0 + (frota % 5),
                        "rpm_motor_media": 2100.0,
                        "rpm_extrator_media": 850.0,
                        "pressao_corte_media": 450.0,
                        "corte_base_auto": 95.0
                    }],
                    "updated_at": datetime.now().isoformat()
                }
                
                headers_upsert = self.headers.copy()
                headers_upsert["Prefer"] = "resolution=merge-duplicates"
                
                response = requests.post(
                    self.base_url,
                    headers=headers_upsert,
                    json=dados_frota,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    sucessos += 1
                
                time.sleep(0.5)  # Evitar rate limiting
            
            sucesso = sucessos == len(frotas_teste)
            mensagem = f"{sucessos}/{len(frotas_teste)} frotas inseridas com sucesso"
            
            self.log_resultado("Múltiplas Frotas", sucesso, mensagem)
            return sucesso
            
        except Exception as e:
            self.log_resultado("Múltiplas Frotas", False, f"Erro: {str(e)}")
            return False
    
    def teste_7_consulta_agregada(self):
        """Teste 7: Fazer consulta agregada dos dados de teste."""
        try:
            params = {
                "data_dia": "eq.2025-01-24",
                "frente_id": "eq.TesteMultiplas"
            }
            
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            sucesso = response.status_code == 200
            mensagem = f"Status: {response.status_code}"
            
            if sucesso:
                data = response.json()
                total_frotas = len(data)
                
                if total_frotas > 0:
                    velocidades = []
                    usos_rtk = []
                    
                    for registro in data:
                        params_medios = registro.get("parametros_medios", [])
                        if params_medios:
                            velocidades.append(params_medios[0].get("vel_media", 0))
                            usos_rtk.append(params_medios[0].get("uso_rtk", 0))
                    
                    vel_media = sum(velocidades) / len(velocidades) if velocidades else 0
                    rtk_medio = sum(usos_rtk) / len(usos_rtk) if usos_rtk else 0
                    
                    mensagem += f" | {total_frotas} frotas | Vel.Média: {vel_media:.1f} | RTK.Médio: {rtk_medio:.1f}%"
                else:
                    mensagem += " | Nenhuma frota encontrada"
                    sucesso = False
            
            self.log_resultado("Consulta Agregada", sucesso, mensagem)
            return sucesso
            
        except Exception as e:
            self.log_resultado("Consulta Agregada", False, f"Erro: {str(e)}")
            return False
    
    def limpeza_dados_teste(self):
        """Limpar dados de teste inseridos."""
        print("\n🧹 LIMPEZA DE DADOS DE TESTE")
        print("="*50)
        
        try:
            # Buscar registros de teste
            params = {
                "data_dia": "eq.2025-01-24",
                "or": "(frente_id.eq.TesteIntegracao,frente_id.eq.TesteMultiplas)"
            }
            
            response = requests.get(self.base_url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                registros = response.json()
                print(f"📊 Encontrados {len(registros)} registros de teste")
                
                # Para cada registro, fazer DELETE
                removidos = 0
                for registro in registros:
                    delete_params = {
                        "data_dia": f"eq.{registro['data_dia']}",
                        "frente_id": f"eq.{registro['frente_id']}",
                        "maquina_id": f"eq.{registro['maquina_id']}"
                    }
                    
                    delete_response = requests.delete(
                        self.base_url,
                        headers=self.headers,
                        params=delete_params
                    )
                    
                    if delete_response.status_code in [200, 204]:
                        removidos += 1
                        print(f"   ✅ Removido: {registro['frente_id']} - Frota {registro['maquina_id']}")
                    else:
                        print(f"   ❌ Erro ao remover: {registro['frente_id']} - Frota {registro['maquina_id']}")
                
                print(f"📋 Resumo: {removidos}/{len(registros)} registros removidos")
            else:
                print("⚠️ Erro ao buscar registros de teste para remoção")
                
        except Exception as e:
            print(f"❌ Erro durante limpeza: {str(e)}")
    
    def executar_todos_testes(self, limpar_depois=True):
        """Executa todos os testes em sequência."""
        print("🧪 EXECUTANDO TESTES DE INTEGRAÇÃO SUPABASE")
        print("="*60)
        
        testes = [
            self.teste_1_conexao_basica,
            self.teste_2_conversao_chaves,
            self.teste_3_insercao_registro,
            self.teste_4_consulta_registro,
            self.teste_5_atualizacao_registro,
            self.teste_6_multiplas_frotas,
            self.teste_7_consulta_agregada
        ]
        
        for i, teste in enumerate(testes, 1):
            print(f"\n{i}/7 - Executando {teste.__doc__.split(':')[1].strip()}...")
            teste()
            time.sleep(1)  # Pausa entre testes
        
        # Relatório final
        self.gerar_relatorio_final()
        
        # Limpeza opcional
        if limpar_depois:
            self.limpeza_dados_teste()
    
    def gerar_relatorio_final(self):
        """Gera relatório final dos testes."""
        print("\n" + "="*60)
        print("📊 RELATÓRIO FINAL DOS TESTES")
        print("="*60)
        
        total_testes = len(self.resultados_testes)
        sucessos = sum(1 for r in self.resultados_testes if r["sucesso"])
        falhas = total_testes - sucessos
        
        print(f"📋 Total de testes: {total_testes}")
        print(f"✅ Sucessos: {sucessos}")
        print(f"❌ Falhas: {falhas}")
        print(f"📈 Taxa de sucesso: {(sucessos/total_testes)*100:.1f}%")
        
        if falhas > 0:
            print(f"\n❌ TESTES QUE FALHARAM:")
            for resultado in self.resultados_testes:
                if not resultado["sucesso"]:
                    print(f"   • {resultado['teste']}: {resultado['mensagem']}")
        
        print("\n" + "="*60)
        
        # Status geral
        if falhas == 0:
            print("🎉 TODOS OS TESTES PASSARAM! Integração funcionando perfeitamente.")
        elif falhas <= 2:
            print("⚠️ Alguns testes falharam. Verifique as configurações.")
        else:
            print("🚨 Muitos testes falharam. Revisar implementação necessário.")

def main():
    """Função principal para executar os testes."""
    print("🔧 TESTES DE INTEGRAÇÃO SUPABASE")
    print("Este script valida se a integração está funcionando corretamente.")
    print()
    
    testes = TestesIntegracaoSupabase()
    
    try:
        testes.executar_todos_testes(limpar_depois=True)
    except KeyboardInterrupt:
        print("\n\n⏹️ Testes interrompidos pelo usuário")
        print("🧹 Executando limpeza...")
        testes.limpeza_dados_teste()
    except Exception as e:
        print(f"\n❌ Erro inesperado durante execução dos testes: {e}")

if __name__ == "__main__":
    main()
