#!/usr/bin/env python3
"""
Utilitário para conversão de chaves para snake_case.

Este módulo contém as funções de conversão utilizadas na integração com Supabase
para garantir que as chaves estejam em formato amigável para código Python/JavaScript.
"""

def converter_chaves_snake_case(dados_dict):
    """
    Converte as chaves do dicionário para snake_case, removendo espaços, 
    parênteses e caracteres especiais para facilitar uso em código Python.
    
    Args:
        dados_dict (dict): Dicionário com chaves originais
        
    Returns:
        dict: Dicionário com chaves convertidas para snake_case
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
    """Testa a conversão das chaves com dados de exemplo."""
    
    # Dados originais (formato Excel)
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
    
    print("\n📋 DADOS ORIGINAIS (Excel):")
    import json
    print(json.dumps(dados_originais, indent=2, ensure_ascii=False))
    
    # Converter
    dados_convertidos = converter_chaves_snake_case(dados_originais)
    
    print("\n✨ DADOS CONVERTIDOS (snake_case):")
    print(json.dumps(dados_convertidos, indent=2, ensure_ascii=False))
    
    print("\n📊 MAPEAMENTO DETALHADO:")
    print("-" * 60)
    for original, convertido in zip(dados_originais.keys(), dados_convertidos.keys()):
        print(f"'{original}' → '{convertido}'")
    
    print("\n✅ VANTAGENS DAS CHAVES CONVERTIDAS:")
    print("   • Sem espaços: facilita acesso obj.frota")
    print("   • Sem parênteses: evita problemas de parsing")
    print("   • Snake_case: padrão Python (PEP 8)")
    print("   • Mais concisas: vel_media vs 'Velocidade Media (km/h)'")
    print("   • Acesso direto: obj.frota vs obj['Frota']")
    
    # Demonstrar uso em código
    print("\n💻 COMPARAÇÃO DE USO EM CÓDIGO:")
    print("="*60)
    print("# ANTES (problemático):")
    print("valor = dados['Velocidade Media (km/h)']  # Aspas obrigatórias")
    print("valor = dados['Uso RTK (%)']              # Caracteres especiais")
    print("valor = dados['RPM Motor Media']          # Espaços problemáticos")
    print()
    print("# DEPOIS (limpo e direto):")
    print("valor = dados['vel_media']      # Simples e claro")
    print("valor = dados['uso_rtk']        # Sem caracteres especiais")
    print("valor = dados['rpm_motor_media'] # Consistente")
    print()
    print("# Em JavaScript/TypeScript (acesso direto):")
    print("const velocidade = dados.vel_media;")
    print("const usoRtk = dados.uso_rtk;")
    print("const rpmMotor = dados.rpm_motor_media;")
    
    return dados_convertidos

def tabela_comparativa():
    """Mostra tabela comparativa das conversões."""
    print("\n📋 TABELA DE CONVERSÕES:")
    print("="*80)
    
    conversoes = [
        ("Frota", "frota"),
        ("Horimetro", "horimetro"), 
        ("Uso RTK (%)", "uso_rtk"),
        ("Horas Elevador", "horas_elevador"),
        ("Horas Motor", "horas_motor"),
        ("Velocidade Media (km/h)", "vel_media"),
        ("RPM Motor Media", "rpm_motor_media"),
        ("RPM Extrator Media", "rpm_extrator_media"),
        ("Pressao Corte Media (psi)", "pressao_corte_media"),
        ("Corte Base Auto (%)", "corte_base_auto")
    ]
    
    print("| Chave Original | Chave Snake_Case | Caracteres Removidos |")
    print("|----------------|------------------|---------------------|")
    
    for original, convertida in conversoes:
        removidos = []
        if '(' in original or ')' in original:
            removidos.append("parênteses")
        if '%' in original:
            removidos.append("símbolos")
        if ' ' in original:
            removidos.append("espaços")
        
        removidos_str = ", ".join(removidos) if removidos else "nenhum"
        print(f"| {original:<26} | {convertida:<16} | {removidos_str} |")

def exemplos_uso():
    """Exemplos práticos de uso das chaves convertidas."""
    print("\n🚀 EXEMPLOS PRÁTICOS DE USO:")
    print("="*60)
    
    print("1. 📊 Em Dashboards React/Vue:")
    print("""
// Muito mais limpo e legível
const FrotaCard = ({ dados }) => (
  <div>
    <h3>Frota {dados.frota}</h3>
    <p>Velocidade: {dados.vel_media} km/h</p>
    <p>RTK: {dados.uso_rtk}%</p>
    <p>Motor: {dados.horas_motor}h</p>
  </div>
);
""")
    
    print("2. 🔍 Em Consultas SQL/NoSQL:")
    print("""
-- PostgreSQL JSONB queries
SELECT maquina_id, 
       parametros_medios->'frota' as frota,
       parametros_medios->'vel_media' as velocidade
FROM registros_painelmaq
WHERE parametros_medios->>'uso_rtk' > '80';
""")
    
    print("3. 🐍 Em Análises Python:")
    print("""
import pandas as pd

# Converter para DataFrame facilmente
df = pd.DataFrame([dados.parametros_medios[0] for dados in registros])

# Análises diretas
media_velocidade = df['vel_media'].mean()
frotas_rtk_alto = df[df['uso_rtk'] > 80]['frota'].tolist()
""")

if __name__ == "__main__":
    print("🔧 UTILITÁRIO DE CONVERSÃO SNAKE_CASE")
    print("="*60)
    print("Este módulo demonstra a conversão de chaves para formato")
    print("amigável para desenvolvimento de código.")
    print()
    
    teste_conversao()
    tabela_comparativa()
    exemplos_uso()
    
    print("\n✅ CONVERSÃO IMPLEMENTADA COM SUCESSO!")
    print("As chaves agora estão em formato padronizado e acessível.")
