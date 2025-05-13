#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import zipfile

def verificar_zip():
    # Caminho para o arquivo ZIP
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(script_dir)
    arquivo_zip = os.path.join(workspace_dir, "dados", "manobrasTeste.zip")
    
    print(f"Verificando arquivo: {arquivo_zip}")
    
    with zipfile.ZipFile(arquivo_zip, 'r') as z:
        # Listar arquivos
        print("\nArquivos no ZIP:")
        for arquivo in z.namelist():
            print(f"- {arquivo}")
        
        # Ler primeiras linhas do primeiro arquivo
        primeiro_arquivo = z.namelist()[0]
        print(f"\nPrimeiras linhas de {primeiro_arquivo}:")
        with z.open(primeiro_arquivo) as f:
            # Ler as primeiras 5 linhas
            linhas = []
            for i, linha in enumerate(f):
                if i >= 5:
                    break
                linhas.append(linha.decode('latin1').strip())
                print(f"Linha {i+1}: {linhas[-1]}")

if __name__ == "__main__":
    verificar_zip() 