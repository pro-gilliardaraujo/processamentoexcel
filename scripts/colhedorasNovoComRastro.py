"""
Script para processamento completo de dados de monitoramento de colhedoras (com rastro de Latitude e Longitude).
Lê arquivos TXT ou CSV na pasta raiz, processa-os e gera arquivos Excel com planilhas auxiliares prontas.
Também processa arquivos ZIP contendo TXT ou CSV.
"""
# Constantes
COLUNAS_REMOVER = [
    'Justificativa Corte Base Desligado',
    # 'Latitude',  # Removido para manter Latitude
    # 'Longitude', # Removido para manter Longitude
    'Regional',
    'Tipo de Equipamento',
    'Unidade',
    'Centro de Custo',
    'Trabalhando em File',
    'Trabalhando Frente Dividida',
    'Trabalhando em Fila'
] 