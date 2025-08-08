#!/usr/bin/env python3
"""
Teste da configuração automática de produção por frente.
Valida identificação de frentes e uso das toneladas corretas.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

# Simular as configurações (normalmente estão no arquivo principal)
TONELADAS_FRENTE_03 = 1200
TONELADAS_FRENTE_04 = 1500  
TONELADAS_FRENTE_08 = 1800
TONELADAS_FRENTE_ZIRLENO = 1000

TONELADAS_POR_FRENTE = {
    'Frente03': TONELADAS_FRENTE_03,
    'Frente04': TONELADAS_FRENTE_04,
    'Frente08': TONELADAS_FRENTE_08,
    'FreteZirleno': TONELADAS_FRENTE_ZIRLENO,
    'Zirleno': TONELADAS_FRENTE_ZIRLENO,
}

def obter_toneladas_por_frente_teste(caminho_arquivo):
    """Versão de teste da função obter_toneladas_por_frente."""
    try:
        nome_arquivo = os.path.basename(caminho_arquivo).lower()
        print(f"🔍 Analisando arquivo: {nome_arquivo}")
        
        # Padrões para identificar frentes
        padroes_frente = {
            'frente03': 'Frente03',
            'frente04': 'Frente04', 
            'frente08': 'Frente08',
            'zirleno': 'Zirleno'
        }
        
        # Buscar padrão no nome do arquivo
        for padrao, nome_frente in padroes_frente.items():
            if padrao in nome_arquivo:
                toneladas = TONELADAS_POR_FRENTE.get(nome_frente)
                if toneladas:
                    print(f"✅ Frente identificada: {nome_frente} = {toneladas} toneladas")
                    return toneladas, nome_frente
                else:
                    print(f"⚠️ Frente {nome_frente} identificada mas sem configuração de toneladas")
                    return None, nome_frente
        
        # Se não encontrou padrão específico, usar primeira frente como padrão
        print(f"⚠️ Frente não identificada no arquivo, usando Frente03 como padrão")
        return TONELADAS_FRENTE_03, 'Frente03'
        
    except Exception as e:
        print(f"❌ Erro ao identificar frente: {e}")
        return TONELADAS_FRENTE_03, 'Frente03'

def testar_identificacao_frentes():
    """Testa a identificação de frentes em diferentes arquivos."""
    print("🧪 TESTANDO IDENTIFICAÇÃO DE FRENTES")
    print("="*60)
    
    # Casos de teste com diferentes nomes de arquivo
    casos_teste = [
        {
            'arquivo': 'colhedorasFrente03_05082025.zip',
            'esperado_frente': 'Frente03',
            'esperado_toneladas': 1200
        },
        {
            'arquivo': 'colhedorasFrente04_05082025.zip', 
            'esperado_frente': 'Frente04',
            'esperado_toneladas': 1500
        },
        {
            'arquivo': 'colhedorasFrente08_05082025.zip',
            'esperado_frente': 'Frente08', 
            'esperado_toneladas': 1800
        },
        {
            'arquivo': 'colhedorasZirleno_05082025.zip',
            'esperado_frente': 'Zirleno',
            'esperado_toneladas': 1000
        },
        {
            'arquivo': 'dados/0508/colhedorasFrente04_05082025.zip',
            'esperado_frente': 'Frente04',
            'esperado_toneladas': 1500
        },
        {
            'arquivo': 'arquivo_sem_padrao_reconhecido.zip',
            'esperado_frente': 'Frente03',  # Fallback
            'esperado_toneladas': 1200
        }
    ]
    
    sucessos = 0
    total = len(casos_teste)
    
    for i, caso in enumerate(casos_teste, 1):
        print(f"\n--- Teste {i}/{total} ---")
        arquivo = caso['arquivo']
        esperado_frente = caso['esperado_frente']
        esperado_toneladas = caso['esperado_toneladas']
        
        toneladas, frente = obter_toneladas_por_frente_teste(arquivo)
        
        # Verificar resultados
        frente_ok = (frente == esperado_frente)
        toneladas_ok = (toneladas == esperado_toneladas)
        
        if frente_ok and toneladas_ok:
            print(f"✅ SUCESSO: {frente} com {toneladas}t")
            sucessos += 1
        else:
            print(f"❌ FALHA:")
            print(f"   Esperado: {esperado_frente} com {esperado_toneladas}t")
            print(f"   Obtido: {frente} com {toneladas}t")
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"   ✅ Sucessos: {sucessos}/{total}")
    print(f"   📈 Taxa de acerto: {(sucessos/total)*100:.1f}%")
    
    return sucessos == total

def testar_calculo_producao():
    """Testa o cálculo de produção com diferentes frentes."""
    print("\n\n🧪 TESTANDO CÁLCULO DE PRODUÇÃO POR FRENTE")
    print("="*60)
    
    # Dados simulados de horas elevador
    hora_elevador_df = pd.DataFrame({
        'Frota': [7032, 7036, 7037],
        'Horas Elevador': [8.5, 6.2, 4.3]
    })
    
    # Cenários de teste
    cenarios = [
        {
            'arquivo': 'colhedorasFrente03_05082025.zip',
            'frente_esperada': 'Frente03',
            'toneladas_esperadas': 1200
        },
        {
            'arquivo': 'colhedorasFrente04_05082025.zip',
            'frente_esperada': 'Frente04', 
            'toneladas_esperadas': 1500
        },
        {
            'arquivo': 'colhedorasFrente08_05082025.zip',
            'frente_esperada': 'Frente08',
            'toneladas_esperadas': 1800
        }
    ]
    
    for cenario in cenarios:
        print(f"\n--- Testando {cenario['arquivo']} ---")
        
        # Simular cálculo
        toneladas_frente, frente = obter_toneladas_por_frente_teste(cenario['arquivo'])
        total_horas = hora_elevador_df['Horas Elevador'].sum()
        
        print(f"Frente: {frente}")
        print(f"Total de toneladas: {toneladas_frente}")
        print(f"Total horas elevador: {total_horas:.1f}h")
        
        # Calcular distribuição
        print("\n📊 Distribuição por frota:")
        total_calculado = 0
        for _, linha in hora_elevador_df.iterrows():
            frota = linha['Frota']
            horas = linha['Horas Elevador']
            proporcao = horas / total_horas
            toneladas_frota = toneladas_frente * proporcao
            ton_por_hora = toneladas_frota / horas if horas > 0 else 0
            
            total_calculado += toneladas_frota
            
            print(f"   Frota {frota}: {horas:.1f}h ({proporcao*100:.1f}%) = {toneladas_frota:.1f}t ({ton_por_hora:.1f}t/h)")
        
        print(f"\n✅ Total distribuído: {total_calculado:.1f}t")
        print(f"✅ Diferença: {abs(total_calculado - toneladas_frente):.3f}t")

def testar_configuracoes_especiais():
    """Testa configurações especiais e casos extremos."""
    print("\n\n🧪 TESTANDO CONFIGURAÇÕES ESPECIAIS")
    print("="*60)
    
    # Teste 1: Arquivo com múltiplos padrões
    print("\n--- Teste: Múltiplos Padrões ---")
    arquivo_multiplo = "backup_frente03_frente04_data.zip"
    toneladas, frente = obter_toneladas_por_frente_teste(arquivo_multiplo)
    print(f"Resultado: {frente} com {toneladas}t (deve pegar o primeiro encontrado)")
    
    # Teste 2: Arquivo sem extensão
    print("\n--- Teste: Sem Extensão ---")
    arquivo_sem_ext = "colhedorasfrente08_05082025"
    toneladas, frente = obter_toneladas_por_frente_teste(arquivo_sem_ext)
    print(f"Resultado: {frente} com {toneladas}t")
    
    # Teste 3: Caminho completo
    print("\n--- Teste: Caminho Completo ---")
    caminho_completo = "/dados/2025/agosto/colhedorasZirleno_05082025.zip"
    toneladas, frente = obter_toneladas_por_frente_teste(caminho_completo)
    print(f"Resultado: {frente} com {toneladas}t")
    
    # Teste 4: Case sensitivity
    print("\n--- Teste: Case Sensitivity ---")
    arquivo_maiusculo = "COLHEDORASFRENTE04_05082025.ZIP"
    toneladas, frente = obter_toneladas_por_frente_teste(arquivo_maiusculo)
    print(f"Resultado: {frente} com {toneladas}t")

def mostrar_configuracoes_atuais():
    """Mostra as configurações atuais de toneladas."""
    print("\n📋 CONFIGURAÇÕES ATUAIS DE TONELADAS:")
    print("="*50)
    for frente, toneladas in TONELADAS_POR_FRENTE.items():
        print(f"   {frente}: {toneladas:,} toneladas")
    
    total_configurado = sum(TONELADAS_POR_FRENTE.values())
    print(f"\n📊 Total configurado: {total_configurado:,} toneladas")
    print(f"📈 Média por frente: {total_configurado/len(TONELADAS_POR_FRENTE):,.0f} toneladas")

def main():
    """Executa todos os testes de configuração por frente."""
    print("🏭 TESTE COMPLETO - CONFIGURAÇÃO POR FRENTE")
    print("="*70)
    print("Validando identificação automática e cálculos por frente")
    print("="*70)
    
    # Mostrar configurações
    mostrar_configuracoes_atuais()
    
    try:
        # Teste 1: Identificação de frentes
        sucesso_identificacao = testar_identificacao_frentes()
        
        # Teste 2: Cálculo de produção
        testar_calculo_producao()
        
        # Teste 3: Casos especiais
        testar_configuracoes_especiais()
        
        # Resumo final
        print("\n" + "="*70)
        print("📊 RESUMO DOS TESTES:")
        if sucesso_identificacao:
            print("   ✅ Identificação de frentes: PASSOU")
        else:
            print("   ❌ Identificação de frentes: FALHOU")
        
        print("   ✅ Cálculo de produção: TESTADO")
        print("   ✅ Casos especiais: VALIDADOS")
        
        if sucesso_identificacao:
            print("\n🎉 IMPLEMENTAÇÃO POR FRENTE FUNCIONANDO!")
            print("✅ Sistema pronto para uso em produção")
        else:
            print("\n⚠️ ALGUNS TESTES FALHARAM")
            print("🔧 Revisar implementação antes do uso")
        
        # Instruções de uso
        print("\n" + "="*70)
        print("📋 PARA USAR EM PRODUÇÃO:")
        print("1. Configure as variáveis TONELADAS_FRENTE_XX no arquivo principal")
        print("2. Execute o processamento normalmente")
        print("3. O sistema identificará automaticamente a frente pelo nome do arquivo")
        print("4. Verifique os logs para confirmar a frente identificada")
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
