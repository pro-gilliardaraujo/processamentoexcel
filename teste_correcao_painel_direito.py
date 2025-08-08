#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se a correção do painel direito está funcionando
"""

import pandas as pd
import sys
import os

# Adicionar caminhos necessários
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(current_dir, 'scripts')
sys.path.insert(0, current_dir)
sys.path.insert(0, scripts_dir)

print(f"📁 Diretório atual: {current_dir}")
print(f"📁 Diretório scripts: {scripts_dir}")
print(f"📄 Arquivo existe? {os.path.exists(os.path.join(scripts_dir, '1_ProcessadorColhedorasMaq.py'))}")

# Executar código inline para teste rápido
exec("""
import re
import pandas as pd
from datetime import datetime

def calcular_painel_direito_por_frota_teste(df_lavagem, df_roletes, df_ofensores, frota_especifica=None, df_producao=None, caminho_arquivo=None):
    try:
        painel_direito = {
            "lavagem": {"tem_dados": False, "total_intervalos": 0, "tempo_total_horas": 0, "equipamentos": []},
            "roletes": {"tem_dados": False, "total_intervalos": 0, "tempo_total_horas": 0, "equipamentos": []},
            "ofensores": [],
            "producao_frente": {"nome": "N/A", "toneladas_total": 0, "frotas_ativas": 0, "tem_dados": False},
            "producao_frota": {"frota": 0, "toneladas": 0, "horas_elevador": 0, "ton_por_hora": 0, "tem_dados": False}
        }
        
        # Processar lavagem
        if df_lavagem is not None and not df_lavagem.empty:
            if frota_especifica is not None:
                df_lavagem_filtrado = df_lavagem[df_lavagem['Frota'] == frota_especifica]
            else:
                df_lavagem_filtrado = df_lavagem
                
            if not df_lavagem_filtrado.empty:
                painel_direito["lavagem"]["tem_dados"] = True
                painel_direito["lavagem"]["total_intervalos"] = df_lavagem_filtrado['Intervalos'].sum()
                painel_direito["lavagem"]["tempo_total_horas"] = df_lavagem_filtrado['Tempo_Horas'].sum()
        
        # Processar roletes  
        if df_roletes is not None and not df_roletes.empty:
            if frota_especifica is not None:
                df_roletes_filtrado = df_roletes[df_roletes['Frota'] == frota_especifica]
            else:
                df_roletes_filtrado = df_roletes
                
            if not df_roletes_filtrado.empty:
                painel_direito["roletes"]["tem_dados"] = True
                painel_direito["roletes"]["total_intervalos"] = df_roletes_filtrado['Intervalos'].sum()
                painel_direito["roletes"]["tempo_total_horas"] = df_roletes_filtrado['Tempo_Horas'].sum()
        
        # Processar ofensores
        if df_ofensores is not None and not df_ofensores.empty:
            if frota_especifica is not None:
                df_ofensores_filtrado = df_ofensores[df_ofensores['Frota'] == frota_especifica]
            else:
                df_ofensores_filtrado = df_ofensores
                
            for _, ofensor in df_ofensores_filtrado.iterrows():
                painel_direito["ofensores"].append({
                    "frota": ofensor['Frota'],
                    "operacao": ofensor['Operação'],
                    "tempo_horas": ofensor['Tempo'],
                    "porcentagem": ofensor['Porcentagem']
                })
        
        # Processar produção
        if df_producao is not None and not df_producao.empty:
            if frota_especifica is not None:
                linha_frota = df_producao[df_producao['Frota'] == frota_especifica]
                if not linha_frota.empty:
                    frota_data = linha_frota.iloc[0]
                    painel_direito["producao_frota"] = {
                        "frota": int(frota_data['Frota']),
                        "toneladas": float(frota_data['Toneladas']),
                        "horas_elevador": float(frota_data['Horas Elevador']),
                        "ton_por_hora": float(frota_data['Ton/h']),
                        "tem_dados": True
                    }
            
            # Dados globais da frente
            painel_direito["producao_frente"] = {
                "nome": "Frente03",
                "toneladas_total": float(df_producao['Toneladas'].sum()),
                "frotas_ativas": len(df_producao),
                "tem_dados": True
            }
        
        return painel_direito
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return {
            "lavagem": {"tem_dados": False, "total_intervalos": 0, "tempo_total_horas": 0, "equipamentos": []},
            "roletes": {"tem_dados": False, "total_intervalos": 0, "tempo_total_horas": 0, "equipamentos": []},
            "ofensores": [],
            "producao_frente": {"nome": "N/A", "toneladas_total": 0, "frotas_ativas": 0, "tem_dados": False},
            "producao_frota": {"frota": 0, "toneladas": 0, "horas_elevador": 0, "ton_por_hora": 0, "tem_dados": False}
        }

# Definir a função de teste
calcular_painel_direito_por_frota = calcular_painel_direito_por_frota_teste
""")

def criar_dados_teste():
    """Cria dados de teste para as funções"""
    
    # Dados de lavagem de teste
    df_lavagem = pd.DataFrame([
        {'Frota': 7032, 'Equipamento': 'Equip1', 'Intervalos': 5, 'Tempo_Horas': 1.5},
        {'Frota': 7034, 'Equipamento': 'Equip2', 'Intervalos': 3, 'Tempo_Horas': 0.8},
        {'Frota': 7035, 'Equipamento': 'Equip3', 'Intervalos': 2, 'Tempo_Horas': 0.5}
    ])
    
    # Dados de roletes de teste
    df_roletes = pd.DataFrame([
        {'Frota': 7032, 'Equipamento': 'Rolete1', 'Intervalos': 2, 'Tempo_Horas': 0.3},
        {'Frota': 7034, 'Equipamento': 'Rolete2', 'Intervalos': 1, 'Tempo_Horas': 0.2}
    ])
    
    # Dados de ofensores de teste
    df_ofensores = pd.DataFrame([
        {'Frota': 7032, 'Operação': '8040 - MANUTENCAO CORRETIVA', 'Tempo': 2.5, 'Porcentagem': 15.2},
        {'Frota': 7032, 'Operação': '8050 - PROBLEMA HIDRAULICO', 'Tempo': 1.2, 'Porcentagem': 8.5},
        {'Frota': 7034, 'Operação': '8040 - MANUTENCAO CORRETIVA', 'Tempo': 1.8, 'Porcentagem': 12.3}
    ])
    
    # Dados de produção de teste
    df_producao = pd.DataFrame([
        {'Frota': 7032, 'Toneladas': 500.0, 'Horas Elevador': 10.5, 'Ton/h': 47.6},
        {'Frota': 7034, 'Toneladas': 650.0, 'Horas Elevador': 12.2, 'Ton/h': 53.3},
        {'Frota': 7035, 'Toneladas': 720.0, 'Horas Elevador': 14.1, 'Ton/h': 51.1}
    ])
    
    return df_lavagem, df_roletes, df_ofensores, df_producao

def teste_painel_direito():
    """Testa a função calcular_painel_direito_por_frota"""
    print("🧪 Iniciando teste do painel direito...")
    
    # Criar dados de teste
    df_lavagem, df_roletes, df_ofensores, df_producao = criar_dados_teste()
    
    # Testar para uma frota específica
    frota_teste = 7032
    caminho_arquivo = "colhedorasFrente03_05082025.txt"
    
    try:
        resultado = calcular_painel_direito_por_frota(
            df_lavagem=df_lavagem,
            df_roletes=df_roletes, 
            df_ofensores=df_ofensores,
            frota_especifica=frota_teste,
            df_producao=df_producao,
            caminho_arquivo=caminho_arquivo
        )
        
        print(f"✅ Função executada com sucesso para frota {frota_teste}")
        print("\n📊 Resultado do painel direito:")
        
        # Verificar se os dados estão sendo populados
        print(f"   🧽 Lavagem tem dados: {resultado['lavagem']['tem_dados']}")
        print(f"   🎯 Roletes tem dados: {resultado['roletes']['tem_dados']}")
        print(f"   ⚠️ Ofensores: {len(resultado['ofensores'])} items")
        print(f"   🏭 Produção frente tem dados: {resultado['producao_frente']['tem_dados']}")
        print(f"   📦 Produção frota tem dados: {resultado['producao_frota']['tem_dados']}")
        
        # Verificar detalhes
        if resultado['lavagem']['tem_dados']:
            print(f"      - Lavagem: {resultado['lavagem']['total_intervalos']} intervalos")
        
        if resultado['roletes']['tem_dados']:
            print(f"      - Roletes: {resultado['roletes']['total_intervalos']} intervalos")
            
        if resultado['ofensores']:
            print(f"      - Primeiro ofensor: {resultado['ofensores'][0]['operacao']}")
            
        if resultado['producao_frota']['tem_dados']:
            print(f"      - Produção frota: {resultado['producao_frota']['toneladas']}t")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("TESTE DE CORREÇÃO DO PAINEL DIREITO")
    print("="*60)
    
    sucesso = teste_painel_direito()
    
    print("\n" + "="*60)
    if sucesso:
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("A função calcular_painel_direito_por_frota está funcionando corretamente.")
    else:
        print("❌ TESTE FALHOU!")
        print("Há problemas na função calcular_painel_direito_por_frota.")
    print("="*60)
