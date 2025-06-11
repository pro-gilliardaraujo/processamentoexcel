# Gerador de Mapas de Rastros das Colhedoras

Este conjunto de scripts gera mapas PNG com rastros coloridos das colhedoras, similar à imagem de referência, baseado nas coordenadas GPS dos arquivos Excel gerados pelo script principal.

## Funcionalidades

- 🗺️ **Mapas coloridos**: Cada frota tem sua própria cor contrastante
- 📍 **Pontos GPS**: Pequenos pontos brancos mostrando as coordenadas
- 🔗 **Trajetórias**: Linhas conectando os pontos em ordem cronológica
- 🎨 **Áreas pintadas**: Polígonos coloridos das áreas percorridas
- 📊 **Legenda automática**: Identificação das frotas no canto inferior direito
- 📐 **Formato automático**: 16:9 (horizontal) ou 9:16 (vertical) baseado na extensão dos dados
- 🖼️ **Alta qualidade**: 300 DPI para impressão

## Duas Versões Disponíveis

### 1. Versão Completa (`gerar_mapa_rastros.py`)
- ✅ Background de imagem de satélite real
- ✅ Projeções geográficas precisas
- ❌ Requer bibliotecas geoespaciais complexas (geopandas, contextily)
- ❌ Instalação mais difícil

### 2. Versão Simples (`gerar_mapa_rastros_simples.py`) - **RECOMENDADA**
- ✅ Fundo escuro simulando satélite
- ✅ Apenas bibliotecas básicas (matplotlib, scipy)
- ✅ Instalação fácil
- ✅ Funciona bem na maioria dos casos

## Instalação

### Para a Versão Simples (Recomendada)
```bash
pip install -r requirements_mapas_simples.txt
```

### Para a Versão Completa
```bash
pip install -r requirements_mapas.txt
```

## Como Usar

### Passo 1: Gerar os Arquivos Excel
Primeiro, execute o script principal para gerar os arquivos Excel com as coordenadas:
```bash
python scripts/colhedorasNovoRastros.py
```

### Passo 2: Gerar os Mapas
Execute o script de geração de mapas:

**Versão Simples (recomendada):**
```bash
python scripts/gerar_mapa_rastros_simples.py
```

**Versão Completa:**
```bash
python scripts/gerar_mapa_rastros.py
```

## Estrutura de Pastas

```
projeto/
├── dados/                    # Arquivos TXT/CSV/ZIP de entrada
├── output/                   # Arquivos Excel gerados (-rastros.xlsx)
├── mapas/                    # Mapas PNG gerados (criado automaticamente)
├── scripts/
│   ├── colhedorasNovoRastros.py
│   ├── gerar_mapa_rastros.py
│   └── gerar_mapa_rastros_simples.py
└── requirements_mapas*.txt
```

## Resultado

Os mapas são salvos na pasta `mapas/` com o nome `{arquivo_original}_mapa_rastros.png`.

Exemplo: Se o arquivo Excel era `colhedora_01-rastros.xlsx`, o mapa será `colhedora_01_mapa_rastros.png`.

## Cores das Frotas

O script usa 12 cores contrastantes que se alternam automaticamente:
1. 🟢 Verde claro
2. 🟣 Roxo
3. 🔴 Vermelho
4. 🟠 Laranja
5. 🔵 Azul
6. 🟡 Ouro
7. 🩷 Rosa
8. 🔵 Turquesa
9. 🟢 Verde lima
10. 🟠 Vermelho laranja
11. 🟣 Roxo escuro
12. 🔷 Ciano

## Troubleshooting

### Erro: "Nenhuma coordenada válida encontrada"
- Verifique se a planilha "Coordenadas" existe no Excel
- Certifique-se de que há dados válidos de Latitude/Longitude
- Execute novamente o script principal para gerar os Excel

### Erro: "ModuleNotFoundError"
- Instale as dependências: `pip install -r requirements_mapas_simples.txt`

### Mapas vazios ou estranhos
- Verifique se as coordenadas estão em formato decimal (ex: -23.5505, -46.6333)
- Certifique-se de que os dados de GPS são válidos (não zeros)

### Problemas com a versão completa
- Use a versão simples se tiver problemas com geopandas/contextily
- A versão simples produz resultados muito similares

## Personalização

Você pode personalizar:
- **Cores**: Modifique a lista `CORES_MAQUINAS` no início do script
- **Tamanho dos pontos**: Altere o parâmetro `s` em `ax.scatter()`
- **Transparência**: Modifique o parâmetro `alpha`
- **Espessura das linhas**: Altere `linewidth`
- **Buffer das áreas**: Modifique `expansao` em `criar_poligono_expandido()`

## Suporte

Os scripts são compatíveis com:
- ✅ Windows 10/11
- ✅ Python 3.7+
- ✅ Arquivos Excel gerados pelo script principal
- ✅ Múltiplas frotas por arquivo

Para problemas ou sugestões, verifique os logs de erro no console. 