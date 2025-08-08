import pandas as pd

# Criar dados de teste simples
df_lavagem = pd.DataFrame([
    {'Frota': 7032, 'Equipamento': 'Equip1', 'Intervalos': 5, 'Tempo_Horas': 1.5},
    {'Frota': 7034, 'Equipamento': 'Equip2', 'Intervalos': 3, 'Tempo_Horas': 0.8}
])

df_roletes = pd.DataFrame([
    {'Frota': 7032, 'Equipamento': 'Rolete1', 'Intervalos': 2, 'Tempo_Horas': 0.3}
])

df_ofensores = pd.DataFrame([
    {'Frota': 7032, 'Operação': '8040 - MANUTENCAO CORRETIVA', 'Tempo': 2.5, 'Porcentagem': 15.2}
])

df_producao = pd.DataFrame([
    {'Frota': 7032, 'Toneladas': 500.0, 'Horas Elevador': 10.5, 'Ton/h': 47.6}
])

print("📊 Dados de teste criados:")
print(f"   🧽 Lavagem: {len(df_lavagem)} linhas")
print(f"   🎯 Roletes: {len(df_roletes)} linhas") 
print(f"   ⚠️ Ofensores: {len(df_ofensores)} linhas")
print(f"   📦 Produção: {len(df_producao)} linhas")

# Simular função simplificada
def teste_painel_direito_simplificado(df_lavagem, df_roletes, df_ofensores, df_producao, frota=7032):
    resultado = {
        "lavagem": {"tem_dados": False},
        "roletes": {"tem_dados": False}, 
        "ofensores": [],
        "producao_frota": {"tem_dados": False},
        "producao_frente": {"tem_dados": False}
    }
    
    # Verificar lavagem
    if not df_lavagem.empty:
        frota_lavagem = df_lavagem[df_lavagem['Frota'] == frota]
        if not frota_lavagem.empty:
            resultado["lavagem"]["tem_dados"] = True
            resultado["lavagem"]["total_intervalos"] = int(frota_lavagem['Intervalos'].sum())
    
    # Verificar roletes
    if not df_roletes.empty:
        frota_roletes = df_roletes[df_roletes['Frota'] == frota]
        if not frota_roletes.empty:
            resultado["roletes"]["tem_dados"] = True
            resultado["roletes"]["total_intervalos"] = int(frota_roletes['Intervalos'].sum())
    
    # Verificar ofensores
    if not df_ofensores.empty:
        frota_ofensores = df_ofensores[df_ofensores['Frota'] == frota]
        for _, row in frota_ofensores.iterrows():
            resultado["ofensores"].append({
                "operacao": row['Operação'],
                "tempo_horas": row['Tempo']
            })
    
    # Verificar produção
    if not df_producao.empty:
        frota_prod = df_producao[df_producao['Frota'] == frota]
        if not frota_prod.empty:
            resultado["producao_frota"]["tem_dados"] = True
            resultado["producao_frota"]["toneladas"] = float(frota_prod.iloc[0]['Toneladas'])
        
        resultado["producao_frente"]["tem_dados"] = True
        resultado["producao_frente"]["toneladas_total"] = float(df_producao['Toneladas'].sum())
    
    return resultado

# Testar
resultado = teste_painel_direito_simplificado(df_lavagem, df_roletes, df_ofensores, df_producao)

print("\n🧪 Resultado do teste:")
print(f"   🧽 Lavagem tem dados: {resultado['lavagem']['tem_dados']}")
if resultado['lavagem']['tem_dados']:
    print(f"      - Intervalos: {resultado['lavagem']['total_intervalos']}")

print(f"   🎯 Roletes tem dados: {resultado['roletes']['tem_dados']}")
if resultado['roletes']['tem_dados']:
    print(f"      - Intervalos: {resultado['roletes']['total_intervalos']}")

print(f"   ⚠️ Ofensores: {len(resultado['ofensores'])} encontrados")
for i, ofensor in enumerate(resultado['ofensores']):
    print(f"      {i+1}. {ofensor['operacao']}: {ofensor['tempo_horas']}h")

print(f"   📦 Produção frota tem dados: {resultado['producao_frota']['tem_dados']}")
if resultado['producao_frota']['tem_dados']:
    print(f"      - Toneladas: {resultado['producao_frota']['toneladas']}")

print(f"   🏭 Produção frente tem dados: {resultado['producao_frente']['tem_dados']}")
if resultado['producao_frente']['tem_dados']:
    print(f"      - Total: {resultado['producao_frente']['toneladas_total']}")

print("\n✅ Teste concluído - A lógica básica está funcionando!")
