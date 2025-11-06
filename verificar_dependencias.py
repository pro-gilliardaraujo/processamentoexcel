#!/usr/bin/env python3
"""
Script para verificar se todas as dependências do projeto estão instaladas corretamente.
"""

import sys
import importlib

def verificar_dependencia(nome, versao_minima=None):
    """
    Verifica se uma dependência está instalada e opcionalmente sua versão.
    
    Args:
        nome (str): Nome do módulo
        versao_minima (str, optional): Versão mínima esperada
    
    Returns:
        tuple: (bool, str) - (sucesso, mensagem)
    """
    try:
        modulo = importlib.import_module(nome)
        versao = getattr(modulo, '__version__', 'desconhecida')
        
        if versao_minima:
            # Comparação simples de versão (pode ser melhorada)
            if versao != 'desconhecida':
                versao_numeros = [int(x) for x in versao.split('.') if x.isdigit()]
                versao_min_numeros = [int(x) for x in versao_minima.split('.') if x.isdigit()]
                
                if versao_numeros < versao_min_numeros:
                    return False, f"Versão {versao} é menor que a mínima {versao_minima}"
        
        return True, f"✓ {nome} v{versao}"
    except ImportError:
        return False, f"✗ {nome} não encontrado"

def main():
    """Função principal para verificar todas as dependências."""
    print("=" * 60)
    print("VERIFICAÇÃO DE DEPENDÊNCIAS - PROJETO COLHEDORAS")
    print("=" * 60)
    
    # Dependências obrigatórias
    dependencias_obrigatorias = [
        ("pandas", "1.5.0"),
        ("numpy", "1.21.0"),
        ("openpyxl", "3.1.0"),
    ]
    
    # Dependências opcionais
    dependencias_opcionais = [
        ("plotly", "5.13.0"),
        ("dash", "2.8.0"),
        ("dash_bootstrap_components", "1.3.0"),
        ("xlrd", "2.0.0"),
        ("xlsxwriter", "3.0.0"),
        ("dateutil", "2.8.0"),
        ("pytz", "2022.1"),
    ]
    
    # Bibliotecas padrão do Python (não precisam ser instaladas)
    bibliotecas_padrao = [
        "os", "glob", "zipfile", "tempfile", "shutil", "json", 
        "pathlib", "datetime", "sys"
    ]
    
    print("\n🔍 VERIFICANDO DEPENDÊNCIAS OBRIGATÓRIAS:")
    print("-" * 40)
    
    obrigatorias_ok = True
    for nome, versao_min in dependencias_obrigatorias:
        sucesso, mensagem = verificar_dependencia(nome, versao_min)
        print(f"  {mensagem}")
        if not sucesso:
            obrigatorias_ok = False
    
    print("\n🔍 VERIFICANDO DEPENDÊNCIAS OPCIONAIS:")
    print("-" * 40)
    
    opcionais_ok = 0
    for nome, versao_min in dependencias_opcionais:
        sucesso, mensagem = verificar_dependencia(nome, versao_min)
        print(f"  {mensagem}")
        if sucesso:
            opcionais_ok += 1
    
    print("\n🔍 VERIFICANDO BIBLIOTECAS PADRÃO:")
    print("-" * 40)
    
    padrao_ok = True
    for nome in bibliotecas_padrao:
        sucesso, mensagem = verificar_dependencia(nome)
        if not sucesso:
            print(f"  ✗ {nome} - ERRO: Biblioteca padrão não encontrada!")
            padrao_ok = False
        else:
            print(f"  ✓ {nome}")
    
    print("\n" + "=" * 60)
    print("RESUMO DA VERIFICAÇÃO:")
    print("=" * 60)
    
    if obrigatorias_ok and padrao_ok:
        print("✅ DEPENDÊNCIAS OBRIGATÓRIAS: OK")
        print("✅ BIBLIOTECAS PADRÃO: OK")
        print(f"📊 DEPENDÊNCIAS OPCIONAIS: {opcionais_ok}/{len(dependencias_opcionais)} instaladas")
        
        if opcionais_ok == len(dependencias_opcionais):
            print("🎉 TODAS AS DEPENDÊNCIAS ESTÃO INSTALADAS!")
            print("   O projeto está pronto para uso.")
        else:
            print("⚠️  Algumas dependências opcionais não estão instaladas.")
            print("   O projeto funcionará, mas algumas funcionalidades podem não estar disponíveis.")
        
        print("\n🚀 Para executar o projeto:")
        print("   python scripts/colhedorasMinOcioso.py")
        
    else:
        print("❌ DEPENDÊNCIAS OBRIGATÓRIAS: FALTANDO")
        print("❌ BIBLIOTECAS PADRÃO: ERRO")
        print("\n🔧 Para instalar as dependências faltantes:")
        print("   Execute: install_dependencies.bat (Windows CMD)")
        print("   Ou: .\\install_dependencies.ps1 (Windows PowerShell)")
        print("   Ou: python -m pip install -r requirements_complete.txt")
        
        return 1
    
    print("\n" + "=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
