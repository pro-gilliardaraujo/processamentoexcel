#!/usr/bin/env python3
"""
Teste da conversão de chaves para snake_case.
"""

def converter_chaves_snake_case(dados_dict):
    """
    Converte as chaves do dicionário para snake_case, removendo espaços, 
    parênteses e caracteres especiais para facilitar uso em código Python.
    """
    mapeamento_chaves = {
        'Frota': 'frota',
        'Horimetro': 'horimetro',
        'Uso RTK (%)': 'uso_rtk',
        'Horas Elevador': 'horas_elevador',
        'Horas Motor': 'horas_motor',
        'Velocidade Media (km/h)': 'vel_media',
        'RPM Motor Media': 'rpm_motor_media',
        'RPM Extrator Media': 'rpm_extrator_media',
        'Pressao Corte Media (psi)': 'pressao_corte_media',
        'Corte Base Auto (%)': 'corte_base_auto'
    }
    
    dados_convertidos = {}
    for chave_original, valor in dados_dict.items():
        chave_nova = mapeamento_chaves.get(chave_original, chave_original.lower().replace(' ', '_'))
        dados_convertidos[chave_nova] = valor
    
    return dados_convertidos

def teste_conversao():
    """Testa a conversão das chaves."""
    
    # Dados originais
    dados_originais = {
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
    }
    
    print("🔧 TESTE DE CONVERSÃO DE CHAVES")
    print("="*60)
    
    print("\n📋 DADOS ORIGINAIS:")
    import json
    print(json.dumps(dados_originais, indent=2, ensure_ascii=False))
    
    # Converter
    dados_convertidos = converter_chaves_snake_case(dados_originais)
    
    print("\n✨ DADOS CONVERTIDOS (snake_case):")
    print(json.dumps(dados_convertidos, indent=2, ensure_ascii=False))
    
    print("\n📊 COMPARAÇÃO CHAVE POR CHAVE:")
    print("-" * 60)
    for original, convertido in zip(dados_originais.keys(), dados_convertidos.keys()):
        print(f"'{original}' → '{convertido}'")
    
    print("\n✅ VANTAGENS DAS CHAVES CONVERTIDAS:")
    print("   • Sem espaços: facilita acesso obj.frota")
    print("   • Sem parênteses: evita problemas de parsing")
    print("   • Snake_case: padrão Python")
    print("   • Mais curtas: vel_media vs Velocidade Media (km/h)")
    
    # Demonstrar uso em código
    print("\n💻 EXEMPLO DE USO EM CÓDIGO PYTHON:")
    print("="*60)
    print("# ANTES (problemático):")
    print("# valor = dados['Velocidade Media (km/h)']  # Aspas obrigatórias")
    print("# valor = dados['Uso RTK (%)']              # Caracteres especiais")
    print()
    print("# DEPOIS (limpo):")
    print("valor = dados['vel_media']     # Simples e claro")
    print("valor = dados['uso_rtk']       # Sem caracteres especiais")
    print("valor = dados['frota']         # Direto")
    
    return dados_convertidos

if __name__ == "__main__":
    teste_conversao()
