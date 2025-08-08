#!/usr/bin/env python3
"""
Teste rápido para debug dos dados de manobras.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

# Simular dados de teste
def criar_dados_manobras_teste():
    """Cria dados simulados da planilha de manobras."""
    
    df_manobras_frota = pd.DataFrame({
        'Frota': [7032, 7034, 7036],
        'Intervalos Válidos': [45, 56, 38],
        'Tempo Total': [0.025, 0.030277777777777776, 0.019],
        'Tempo Médio': [0.000556, 0.0005406746031746032, 0.0005]
    })
    
    print("📊 DADOS DE TESTE - PLANILHA MANOBRAS:")
    print(df_manobras_frota)
    print()
    
    return df_manobras_frota

def testar_mapeamento_colunas():
    """Testa o mapeamento de colunas de manobras."""
    
    df_manobras = criar_dados_manobras_teste()
    frota_teste = 7034
    
    print(f"🧪 TESTANDO MAPEAMENTO PARA FROTA {frota_teste}")
    print("="*50)
    
    # Simular o código de mapeamento
    linha_frota = df_manobras[df_manobras.iloc[:, 0] == frota_teste]
    
    if not linha_frota.empty:
        print(f"✅ Frota {frota_teste} encontrada")
        print(f"Colunas: {list(linha_frota.columns)}")
        print(f"Valores: {linha_frota.iloc[0].to_dict()}")
        print()
        
        intervalos_manobras = 0
        tempo_total_manobras = 0
        tempo_medio_manobras = 0
        
        for col in linha_frota.columns:
            print(f"Analisando coluna: '{col}'")
            
            if any(palavra in col.lower() for palavra in ['intervalos', 'válidos']):
                intervalos_manobras = pd.to_numeric(linha_frota[col].iloc[0], errors='coerce') or 0
                print(f"  ✅ INTERVALOS encontrado: {intervalos_manobras}")
                
            elif any(palavra in col.lower() for palavra in ['total', 'tempo']) and 'médio' not in col.lower():
                tempo_total_manobras = pd.to_numeric(linha_frota[col].iloc[0], errors='coerce') or 0
                print(f"  ✅ TEMPO TOTAL encontrado: {tempo_total_manobras}")
                
            elif any(palavra in col.lower() for palavra in ['médio', 'medio', 'média']):
                tempo_medio_manobras = pd.to_numeric(linha_frota[col].iloc[0], errors='coerce') or 0
                print(f"  ✅ TEMPO MÉDIO encontrado: {tempo_medio_manobras}")
            else:
                print(f"  ⚪ Coluna ignorada")
        
        print()
        print("📋 RESULTADO FINAL:")
        print(f"   Intervalos: {intervalos_manobras}")
        print(f"   Tempo Total: {tempo_total_manobras} horas = {tempo_total_manobras*60:.2f} min")
        print(f"   Tempo Médio: {tempo_medio_manobras} horas = {tempo_medio_manobras*60:.4f} min = {tempo_medio_manobras*3600:.2f} seg")
        
        # Verificar se o tempo médio está correto
        tempo_medio_calculado = tempo_total_manobras / intervalos_manobras if intervalos_manobras > 0 else 0
        print()
        print("🔍 VERIFICAÇÃO:")
        print(f"   Tempo médio da planilha: {tempo_medio_manobras}")
        print(f"   Tempo médio calculado: {tempo_medio_calculado}")
        
        if abs(tempo_medio_manobras - tempo_medio_calculado) < 0.0001:
            print("   ✅ Valores coincidem!")
        else:
            print("   ⚠️ DIFERENÇA detectada!")
            
    else:
        print(f"❌ Frota {frota_teste} NÃO encontrada")

def main():
    """Executa o teste de debug."""
    print("🔍 DEBUG - DADOS DE MANOBRAS")
    print("="*60)
    print("Investigando por que manobras_tempo_medio está chegando como 0")
    print("="*60)
    
    testar_mapeamento_colunas()
    
    print("\n" + "="*60)
    print("📋 CONCLUSÃO:")
    print("Se os valores aparecem corretos aqui, o problema está")
    print("na busca da frota ou no mapeamento das colunas no código real.")

if __name__ == "__main__":
    main()
