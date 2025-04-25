import pandas as pd
import numpy as np

# Criar um DataFrame de teste com diferentes valores possíveis para RTK
test_data = [
    {'RTK (Piloto Automatico)': 'SIM'},
    {'RTK (Piloto Automatico)': 'Sim'},
    {'RTK (Piloto Automatico)': 'sim'},
    {'RTK (Piloto Automatico)': 'VERDADEIRO'},
    {'RTK (Piloto Automatico)': 'TRUE'},
    {'RTK (Piloto Automatico)': 'LIGADO'},
    {'RTK (Piloto Automatico)': 1},
    {'RTK (Piloto Automatico)': '1'},
    {'RTK (Piloto Automatico)': True},
    {'RTK (Piloto Automatico)': 'NAO'},
    {'RTK (Piloto Automatico)': 'Não'},
    {'RTK (Piloto Automatico)': 'FALSO'},
    {'RTK (Piloto Automatico)': 'FALSE'},
    {'RTK (Piloto Automatico)': 'DESLIGADO'},
    {'RTK (Piloto Automatico)': 0},
    {'RTK (Piloto Automatico)': '0'},
    {'RTK (Piloto Automatico)': False}
]

df = pd.DataFrame(test_data)

print("Valores originais:")
print(df)

# Teste 1: Mapeamento usando apply com lista de valores
print("\nTeste 1: Mapeamento usando apply com lista de valores:")
df['RTK Mapeado 1'] = df['RTK (Piloto Automatico)'].apply(lambda x: 
    1 if x in [1, '1', 'SIM', 'Sim', 'sim', 'VERDADEIRO', 'TRUE', 'True', 'LIGADO', True] 
    else 0
)
print(df[['RTK (Piloto Automatico)', 'RTK Mapeado 1']])

# Teste 2: Mapeamento usando str.upper() para padronização
print("\nTeste 2: Mapeamento usando str.upper() para padronização:")
df['RTK Mapeado 2'] = df['RTK (Piloto Automatico)'].apply(lambda x: 
    1 if str(x).upper() in ['1', 'SIM', 'VERDADEIRO', 'TRUE', 'LIGADO', 'S'] or x is True
    else 0
)
print(df[['RTK (Piloto Automatico)', 'RTK Mapeado 2']])

# Teste 3: Mapeamento direto usando replace
print("\nTeste 3: Mapeamento direto usando replace:")
valores_sim = ['SIM', 'Sim', 'sim', 'VERDADEIRO', 'TRUE', 'True', 'LIGADO', 1, '1', True]
valores_nao = ['NAO', 'Não', 'não', 'FALSO', 'FALSE', 'False', 'DESLIGADO', 0, '0', False]

mapeamento = {valor: 1 for valor in valores_sim}
mapeamento.update({valor: 0 for valor in valores_nao})

df['RTK Mapeado 3'] = df['RTK (Piloto Automatico)'].map(mapeamento).fillna(0).astype(int)
print(df[['RTK (Piloto Automatico)', 'RTK Mapeado 3']])

# Verificar se algum valor não foi mapeado corretamente
print("\nValores com mapeamento diferente entre os métodos:")
df_diff = df[
    (df['RTK Mapeado 1'] != df['RTK Mapeado 2']) | 
    (df['RTK Mapeado 2'] != df['RTK Mapeado 3'])
]
if len(df_diff) > 0:
    print(df_diff)
else:
    print("Todos os métodos mapearam os valores da mesma forma.")

# Encontrar a melhor estratégia
print("\nMelhor estratégia para mapeamento em transbordos:")
print("""
def mapear_rtk(valor):
    if isinstance(valor, bool):
        return 1 if valor else 0
    
    if isinstance(valor, (int, float)):
        return 1 if valor == 1 else 0
    
    if isinstance(valor, str):
        valor_upper = valor.upper().strip()
        return 1 if valor_upper in ['1', 'SIM', 'S', 'VERDADEIRO', 'TRUE', 'LIGADO'] else 0
    
    return 0
""") 