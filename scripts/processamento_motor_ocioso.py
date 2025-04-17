import csv
import datetime
import os
import sys

def converter_tempo_para_segundos(tempo_str):
    """Converte string de tempo (HH:MM:SS) para segundos"""
    try:
        h, m, s = map(int, tempo_str.strip().split(':'))
        return h * 3600 + m * 60 + s
    except:
        return 0

def converter_segundos_para_tempo(segundos):
    """Converte segundos para string de tempo (HH:MM:SS)"""
    horas = segundos // 3600
    segundos %= 3600
    minutos = segundos // 60
    segundos %= 60
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

def processar_arquivo_motor_ocioso(arquivo_entrada, arquivo_saida=None):
    """
    Processa um arquivo CSV com dados de motor ocioso e calcula os tempos.
    
    Args:
        arquivo_entrada: Caminho para o arquivo CSV de entrada
        arquivo_saida: Caminho para o arquivo de saída (opcional)
    
    Returns:
        Dicionário com os resultados do processamento
    """
    # Inicialização de variáveis
    iniciar_intervalo = False
    tempo_soma = 0
    tempo_total = 0
    intervalo_atual = []
    todos_intervalos = []
    
    # Abrir arquivo de entrada
    with open(arquivo_entrada, 'r', encoding='latin1') as f:
        leitor = csv.reader(f, delimiter=';')
        
        # Pular cabeçalho
        cabecalho = next(leitor)
        
        # Processar cada linha
        for i, linha in enumerate(leitor, start=2):  # Começar do 2 para considerar o cabeçalho
            if len(linha) < 9:  # Verificar se a linha tem dados suficientes
                continue
                
            # Extrair dados relevantes
            try:
                parada_motor_ligado = int(linha[5].strip()) if linha[5].strip() else 0
                tempo_str = linha[8].strip().replace(';', '')  # Remover ponto e vírgula extra se houver
                
                # Converter tempo para segundos
                tempo_segundos = converter_tempo_para_segundos(tempo_str)
                
                # Lógica de processamento
                if parada_motor_ligado == 1:
                    if not iniciar_intervalo:
                        iniciar_intervalo = True
                        tempo_soma = tempo_segundos
                        intervalo_atual = [(i, linha[0], linha[1], tempo_str, tempo_segundos)]
                    else:
                        tempo_soma += tempo_segundos
                        intervalo_atual.append((i, linha[0], linha[1], tempo_str, tempo_segundos))
                
                elif parada_motor_ligado == 0 and iniciar_intervalo:
                    if tempo_segundos > 60:  # Maior que 1 minuto
                        if tempo_soma > 60:  # Soma maior que 1 minuto
                            tempo_total += (tempo_soma - 60)
                            todos_intervalos.append({
                                'linhas': intervalo_atual,
                                'tempo_total': tempo_soma,
                                'tempo_apos_subtracao': tempo_soma - 60
                            })
                        iniciar_intervalo = False
                        tempo_soma = 0
                        intervalo_atual = []
                    # Se menor que 1 minuto, continua somando (não fecha o intervalo)
            except Exception as e:
                print(f"Erro ao processar linha {i}: {e}")
                continue
    
    # Verificar se há um intervalo aberto no final
    if iniciar_intervalo and tempo_soma > 60:
        tempo_total += (tempo_soma - 60)
        todos_intervalos.append({
            'linhas': intervalo_atual,
            'tempo_total': tempo_soma,
            'tempo_apos_subtracao': tempo_soma - 60
        })
    
    # Preparar resultado
    resultado = {
        'tempo_total_segundos': tempo_total,
        'tempo_total_formatado': converter_segundos_para_tempo(tempo_total),
        'intervalos': todos_intervalos
    }
    
    # Salvar resultado em arquivo se especificado
    if arquivo_saida:
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            f.write(f"Tempo Total de Motor Ocioso: {resultado['tempo_total_formatado']}\n\n")
            f.write("Detalhamento dos Intervalos:\n")
            for i, intervalo in enumerate(resultado['intervalos'], 1):
                f.write(f"\nIntervalo {i}:\n")
                f.write("  Linhas:\n")
                for linha in intervalo['linhas']:
                    f.write(f"    Linha {linha[0]}: Data={linha[1]}, Hora={linha[2]}, Tempo={linha[3]}\n")
                f.write(f"  Tempo Total: {converter_segundos_para_tempo(intervalo['tempo_total'])}\n")
                f.write(f"  Tempo Após Subtração: {converter_segundos_para_tempo(intervalo['tempo_apos_subtracao'])}\n")
    
    return resultado

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python processamento_motor_ocioso.py arquivo_entrada.csv [arquivo_saida.txt]")
        sys.exit(1)
    
    arquivo_entrada = sys.argv[1]
    arquivo_saida = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(arquivo_entrada):
        print(f"Erro: Arquivo {arquivo_entrada} não encontrado.")
        sys.exit(1)
    
    try:
        resultado = processar_arquivo_motor_ocioso(arquivo_entrada, arquivo_saida)
        print(f"\nTempo Total de Motor Ocioso: {resultado['tempo_total_formatado']}")
        print(f"Total de intervalos processados: {len(resultado['intervalos'])}")
        
        print("\nDetalhamento dos intervalos:")
        for i, intervalo in enumerate(resultado['intervalos'], 1):
            print(f"\nIntervalo {i}:")
            print(f"  Tempo Total: {converter_segundos_para_tempo(intervalo['tempo_total'])}")
            print(f"  Tempo Após Subtração: {converter_segundos_para_tempo(intervalo['tempo_apos_subtracao'])}")
            print("  Linhas:")
            for linha in intervalo['linhas']:
                print(f"    Linha {linha[0]}: Data={linha[1]}, Hora={linha[2]}, Tempo={linha[3]}")
    except Exception as e:
        print(f"Erro ao processar arquivo: {e}")
        sys.exit(1) 