#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste de parâmetros (tempo mínimo e velocidade mínima) em múltiplos arquivos
(colhedoras e/ou transbordos). O objetivo é encontrar combinações que atendam
simultaneamente às metas de manobras fornecidas para cada arquivo.

Uso rápido:
1. Coloque os arquivos na pasta "dados".
2. Ajuste o dicionário TARGETS no topo deste script com o nome-chave do
   arquivo (parte do nome) e o valor alvo de manobras.
3. Execute:  python teste_parametros_multifiles.py

Saída:
• Excel com todas as combinações testadas e as que obtiveram diferença zero
  para todos os arquivos.
• PNG com mapa de calor (maior diferença absoluta entre arquivos).
"""

import os
import sys
import glob
import zipfile
import tempfile
import shutil
import time
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ------------------ CONFIGURAÇÕES GERAIS ------------------ #
# Mapear parte do nome do arquivo -> meta de manobras
TARGETS = {
    "colhedorasFrente03": 216,
    "colhedorasFrente08": 259,
    "colhedorasZirleno": 171,
    "transbordosFrente03": 135,
    "transbordosFrente08": 222,
}

# Número mínimo de combinações exatas que queremos registrar antes de parar
MIN_COMBINACOES_EXATAS = 10

# Geração inicial de grid
TEMPOS_INICIAIS = np.arange(0, 61, 1)          # 0–60 s passo 1
VELOCIDADES_INICIAIS = np.arange(0, 10.01, 0.1)  # 0–10 km/h passo 0.1

# Após primeira varredura, se nada encontrado, refinamos passo
VELOCIDADE_PASSO_REFINO = 0.05

# Diretórios
DIR_RAIZ = Path(__file__).resolve().parents[1]
DIR_DADOS = DIR_RAIZ / "dados"
DIR_OUT = DIR_RAIZ / "output"
DIR_OUT.mkdir(exist_ok=True)

# ------------------ FUNÇÕES AUXILIARES ------------------ #

def localizar_arquivo(chave: str):
    """Procura arquivo na pasta dados contendo a chave no nome."""
    padrao = str(DIR_DADOS / f"*{chave}*.*")
    arquivos = glob.glob(padrao)
    if not arquivos:
        print(f"Arquivo com chave '{chave}' não encontrado em {DIR_DADOS}.")
        return None
    # Priorizar ZIP, depois CSV/TXT
    arquivos.sort(key=lambda x: (not x.lower().endswith('.zip'), x))
    return arquivos[0]

def extrair_se_necessario(caminho):
    """Se for ZIP extrai e devolve caminho do primeiro txt/csv."""
    if not caminho.lower().endswith('.zip'):
        return caminho, None
    tmp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(caminho, 'r') as zf:
        zf.extractall(tmp_dir)
    # pegar primeiro txt/csv
    arquivos = []
    for ext in ("*.txt", "*.csv"):
        arquivos += glob.glob(os.path.join(tmp_dir, ext))
    if not arquivos:
        raise FileNotFoundError("ZIP sem txt/csv válido")
    return arquivos[0], tmp_dir

def escolher_processador(caminho):
    """Importa função processar_arquivo_base correta."""
    nome = os.path.basename(caminho).lower()
    try:
        if "transbordo" in nome:
            from transbordosMinOcioso import processar_arquivo_base as _proc
        else:
            from colhedorasNovoRastros import processar_arquivo_base as _proc
    except ImportError:
        sys.path.append(str(Path(__file__).parent))
        if "transbordo" in nome:
            from transbordosMinOcioso import processar_arquivo_base as _proc
        else:
            from colhedorasNovoRastros import processar_arquivo_base as _proc
    return _proc

# ------------------ PRÉ-PROCESSAMENTO DOS ARQUIVOS ------------------ #
print("Processando arquivos alvo…")
registros = {}  # chave -> (df_manobras, alvo)
for chave, alvo in TARGETS.items():
    caminho = localizar_arquivo(chave)
    if not caminho:
        continue
    caminho_processar, pasta_tmp = extrair_se_necessario(caminho)
    proc = escolher_processador(caminho_processar)
    df_base = proc(caminho_processar)
    if df_base is None or df_base.empty:
        print(f"Arquivo {caminho} vazio ou erro no processamento.")
        continue
    df_mano = df_base[df_base["Estado"] == "MANOBRA"].copy()
    registros[chave] = (df_mano, alvo, pasta_tmp)

if not registros:
    print("Nenhum arquivo processado. Verifique TARGETS e pasta dados.")
    sys.exit(1)

print(f"{len(registros)} arquivos processados com sucesso.")

# ------------------ FUNÇÃO PARA CONTAGEM ------------------ #

def conta_manobras(df, tempo_s, vel_kmh):
    tempo_h = tempo_s / 3600
    return len(df[(df["Diferença_Hora"] >= tempo_h) & (df["Velocidade"] >= vel_kmh)])

# ------------------ BUSCA DE COMBINAÇÕES ------------------ #

def buscar_combinacoes(tempos, velocidades):
    resultados = []  # armazena tuplas (tempo, vel) com zero diff
    total_testes = 0
    for t in tempos:
        th = t / 3600
        for v in velocidades:
            total_testes += 1
            ok = True
            for chave, (df, alvo, _) in registros.items():
                if conta_manobras(df, t, v) != alvo:
                    ok = False
                    break
            if ok:
                resultados.append((t, v))
                if len(resultados) >= MIN_COMBINACOES_EXATAS:
                    return resultados, total_testes
    return resultados, total_testes

print("Buscando combinações…")
combos, testes = buscar_combinacoes(TEMPOS_INICIAIS, VELOCIDADES_INICIAIS)

# Refinar se necessário
if not combos:
    print("Nenhuma combinação na grade inicial. Refinando passo de velocidade…")
    velocidades_refino = np.arange(0, 10.01, VELOCIDADE_PASSO_REFINO)
    combos, testes = buscar_combinacoes(TEMPOS_INICIAIS, velocidades_refino)

# ------------------ RESULTADOS ------------------ #
print(f"Total de combinações testadas: {testes}")
print(f"Combinações exatas encontradas: {len(combos)}")
for t, v in combos[:10]:
    print(f"Tempo: {t}s | Velocidade: {v:.2f} km/h")

# Criar Excel
hoje = datetime.now().strftime("%Y%m%d_%H%M%S")
xl_path = DIR_OUT / f"teste_parametros_multi_{hoje}.xlsx"
with pd.ExcelWriter(xl_path) as writer:
    resumo = pd.DataFrame(combos, columns=["Tempo (s)", "Velocidade (km/h)"])
    resumo.to_excel(writer, sheet_name="Combos Exatos", index=False)
    meta_df = pd.DataFrame({
        "Arquivo": list(registros.keys()),
        "Meta": [v[1] for v in registros.values()],
        "Total Original": [len(v[0]) for v in registros.values()]
    })
    meta_df.to_excel(writer, sheet_name="Metas", index=False)
print(f"Excel salvo em {xl_path}")

# Criar mapa de calor da MAIOR diferença absoluta entre arquivos
matriz = np.zeros((len(TEMPOS_INICIAIS), len(VELOCIDADES_INICIAIS)))
for i, t in enumerate(TEMPOS_INICIAIS):
    for j, v in enumerate(VELOCIDADES_INICIAIS):
        diffs = [abs(conta_manobras(df, t, v) - alvo) for df, alvo, _ in registros.values()]
        matriz[i, j] = max(diffs)

plt.figure(figsize=(14, 10))
ax = sns.heatmap(matriz, xticklabels=np.round(VELOCIDADES_INICIAIS,1), yticklabels=TEMPOS_INICIAIS,
                 cmap="viridis_r", cbar_kws={"label":"Maior diferença absoluta"})
plt.xlabel("Velocidade mínima (km/h)")
plt.ylabel("Tempo mínimo (s)")
plt.title("Mapa – maior diferença absoluta entre arquivos")
plt.xticks(rotation=45)
plt.tight_layout()
img_path = DIR_OUT / f"mapa_parametros_multi_{hoje}.png"
plt.savefig(img_path, dpi=300)
print(f"Mapa salvo em {img_path}")

# Limpeza de temporários
for _, (_, _, tmp) in registros.items():
    if tmp and os.path.exists(tmp):
        shutil.rmtree(tmp, ignore_errors=True) 