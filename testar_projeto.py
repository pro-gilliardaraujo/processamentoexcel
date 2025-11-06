#!/usr/bin/env python3
"""
Script para testar se o projeto de colhedoras está funcionando corretamente.
"""

import sys
import os
from pathlib import Path

def testar_importacoes():
    """Testa se todas as importações necessárias funcionam."""
    print("🔍 Testando importações...")
    
    try:
        import pandas as pd
        print("  ✓ pandas importado com sucesso")
    except ImportError as e:
        print(f"  ✗ Erro ao importar pandas: {e}")
        return False
    
    try:
        import numpy as np
        print("  ✓ numpy importado com sucesso")
    except ImportError as e:
        print(f"  ✗ Erro ao importar numpy: {e}")
        return False
    
    try:
        import openpyxl
        print("  ✓ openpyxl importado com sucesso")
    except ImportError as e:
        print(f"  ✗ Erro ao importar openpyxl: {e}")
        return False
    
    return True

def testar_estrutura_projeto():
    """Testa se a estrutura do projeto está correta."""
    print("\n🔍 Testando estrutura do projeto...")
    
    # Diretório atual
    diretorio_atual = Path.cwd()
    print(f"  Diretório atual: {diretorio_atual}")
    
    # Verificar se estamos no diretório correto
    arquivos_esperados = [
        "scripts/colhedorasMinOcioso.py",
        "requirements.txt",
        "dados",
        "output"
    ]
    
    for arquivo in arquivos_esperados:
        caminho = diretorio_atual / arquivo
        if caminho.exists():
            print(f"  ✓ {arquivo} encontrado")
        else:
            print(f"  ✗ {arquivo} não encontrado")
            if arquivo in ["dados", "output"]:
                print(f"    Criando diretório {arquivo}...")
                caminho.mkdir(exist_ok=True)
                print(f"    ✓ Diretório {arquivo} criado")
    
    return True

def testar_script_principal():
    """Testa se o script principal pode ser importado."""
    print("\n🔍 Testando script principal...")
    
    try:
        # Adicionar o diretório scripts ao path
        sys.path.insert(0, str(Path.cwd() / "scripts"))
        
        # Tentar importar o módulo principal
        import colhedorasMinOcioso
        print("  ✓ Script principal importado com sucesso")
        
        # Verificar se as funções principais existem
        funcoes_esperadas = [
            "processar_arquivo_base",
            "calcular_base_calculo", 
            "calcular_disponibilidade_mecanica",
            "calcular_motor_ocioso_novo"
        ]
        
        for funcao in funcoes_esperadas:
            if hasattr(colhedorasMinOcioso, funcao):
                print(f"  ✓ Função {funcao} encontrada")
            else:
                print(f"  ✗ Função {funcao} não encontrada")
        
        return True
        
    except ImportError as e:
        print(f"  ✗ Erro ao importar script principal: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Erro inesperado: {e}")
        return False

def main():
    """Função principal de teste."""
    print("=" * 60)
    print("TESTE DO PROJETO - PROCESSAMENTO DE COLHEDORAS")
    print("=" * 60)
    
    # Executar testes
    teste1 = testar_importacoes()
    teste2 = testar_estrutura_projeto()
    teste3 = testar_script_principal()
    
    print("\n" + "=" * 60)
    print("RESULTADO DOS TESTES:")
    print("=" * 60)
    
    if teste1 and teste2 and teste3:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ O projeto está pronto para uso.")
        print("\n🚀 Para executar o processamento:")
        print("   python scripts/colhedorasMinOcioso.py")
        print("\n📁 Coloque seus arquivos de dados na pasta 'dados/'")
        print("📊 Os resultados serão salvos na pasta 'output/'")
        return 0
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print("🔧 Verifique as dependências e a estrutura do projeto.")
        print("\nPara instalar dependências:")
        print("   python -m pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
