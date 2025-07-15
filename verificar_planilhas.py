import pandas as pd
import os

def verificar_planilhas():
    """
    Verifica quais planilhas existem no arquivo Excel.
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
        # Ler todas as planilhas
        excel_file = pd.ExcelFile(arquivo_excel)
        planilhas = excel_file.sheet_names
        
        print(f"\n=== PLANILHAS DISPONÍVEIS ===")
        for i, planilha in enumerate(planilhas, 1):
            print(f"{i}. {planilha}")
        
        # Verificar se existe planilha de Hora Elevador
        hora_elevador_sheets = [s for s in planilhas if 'Hora' in s or 'Elevador' in s]
        if hora_elevador_sheets:
            print(f"\n=== PLANILHAS RELACIONADAS A HORA ELEVADOR ===")
            for sheet in hora_elevador_sheets:
                print(f"- {sheet}")
                
                # Tentar ler a planilha
                try:
                    df = pd.read_excel(arquivo_excel, sheet_name=sheet)
                    print(f"  Colunas: {list(df.columns)}")
                    print(f"  Registros: {len(df)}")
                    if len(df) > 0:
                        print(f"  Primeira linha: {df.iloc[0].to_dict()}")
                except Exception as e:
                    print(f"  Erro ao ler: {e}")
        else:
            print(f"\n⚠️  Nenhuma planilha de Hora Elevador encontrada!")
        
    except Exception as e:
        print(f"Erro ao verificar planilhas: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_planilhas() 