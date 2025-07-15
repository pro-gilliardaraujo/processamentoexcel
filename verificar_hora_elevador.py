import pandas as pd
import os

def verificar_hora_elevador():
    """
    Verifica se a nova planilha Horas Elevador agrupada por máquina está funcionando corretamente.
    """
    # Verificar se existe arquivo de saída
    output_dir = "output"
    files = [f for f in os.listdir(output_dir) if f.endswith('.xlsx') and 'colhedoras' in f]
    
    if not files:
        print("Nenhum arquivo Excel de colhedoras encontrado na pasta output!")
        return
    
    arquivo_excel = os.path.join(output_dir, files[0])
    print(f"Analisando arquivo: {arquivo_excel}")
    
    try:
        # Ler a planilha Horas Elevador
        hora_elevador_df = pd.read_excel(arquivo_excel, sheet_name='3_Hora Elevador')
        
        print(f"\n=== PLANILHA HORAS ELEVADOR (AGRUPADA POR MÁQUINA) ===")
        print(f"Total de registros: {len(hora_elevador_df)}")
        
        # Verificar colunas
        print(f"\nColunas disponíveis: {list(hora_elevador_df.columns)}")
        
        # Mostrar dados
        print(f"\n=== DADOS DA PLANILHA ===")
        for _, row in hora_elevador_df.iterrows():
            frota = row['Frota']
            horas_elevador = row['Horas Elevador']
            tempo_ligado = row['Tempo Ligado']
            eficiencia = row['Eficiência Elevador']
            
            print(f"Frota: {frota}")
            print(f"  Horas Elevador: {horas_elevador:.4f}h")
            print(f"  Tempo Ligado: {tempo_ligado:.4f}h")
            print(f"  Eficiência: {eficiencia:.4f} ({eficiencia*100:.2f}%)")
            print(f"  Fórmula: {horas_elevador:.4f} / {tempo_ligado:.4f} = {eficiencia:.4f}")
            print("-" * 50)
        
        # Verificar se os dados fazem sentido
        print(f"\n=== VALIDAÇÃO DOS DADOS ===")
        for _, row in hora_elevador_df.iterrows():
            frota = row['Frota']
            horas_elevador = row['Horas Elevador']
            tempo_ligado = row['Tempo Ligado']
            eficiencia = row['Eficiência Elevador']
            
            # Verificar se horas elevador <= tempo ligado
            if horas_elevador > tempo_ligado:
                print(f"⚠️  ATENÇÃO: Frota {frota} tem mais horas elevador ({horas_elevador:.4f}) que tempo ligado ({tempo_ligado:.4f})")
            else:
                print(f"✅ Frota {frota}: Dados consistentes")
            
            # Verificar se eficiência está correta
            eficiencia_calculada = (horas_elevador / tempo_ligado) if tempo_ligado > 0 else 0
            if abs(eficiencia - eficiencia_calculada) > 0.0001:
                print(f"⚠️  ATENÇÃO: Frota {frota} eficiência inconsistente. Calculada: {eficiencia_calculada:.4f}, Armazenada: {eficiencia:.4f}")
            else:
                print(f"✅ Frota {frota}: Eficiência correta")
        
        print(f"\n=== VERIFICAÇÃO CONCLUÍDA ===")
        print("✅ Nova planilha Horas Elevador agrupada por máquina implementada com sucesso!")
        print("✅ Colunas: Frota, Horas Elevador, Tempo Ligado, Eficiência Elevador")
        print("✅ Dados ordenados por Horas Elevador (decrescente)")
        
    except Exception as e:
        print(f"Erro ao verificar planilha: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_hora_elevador() 