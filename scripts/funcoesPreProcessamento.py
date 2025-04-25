import json
import os
from datetime import datetime

def processar_substituicoes(substituicoes_json):
    """
    Processa o arquivo JSON de substituições e retorna os mapeamentos.
    
    Args:
        substituicoes_json (str): Caminho para o arquivo JSON.
        
    Returns:
        dict: Dicionário com mapeamento de substituições.
    """
    if not substituicoes_json or not os.path.exists(substituicoes_json):
        return {}, None
    
    try:
        with open(substituicoes_json, 'r', encoding='utf-8') as file:
            substituicoes = json.load(file)
        
        mapeamento_substituicoes = {}
        mapeamento_horario = []
        
        for substituicao in substituicoes:
            operador_origem = substituicao.get('operador_origem', '')
            operador_destino = substituicao.get('operador_destino', '')
            
            if not operador_origem or not operador_destino:
                continue
            
            # Verifica se há informações de horário
            hora_inicio = substituicao.get('hora_inicio')
            hora_fim = substituicao.get('hora_fim')
            
            if hora_inicio and hora_fim:
                # Adiciona ao mapeamento por horário
                try:
                    # Converte as strings de horário para objetos time
                    hora_inicio_obj = datetime.strptime(hora_inicio, '%H:%M').time()
                    hora_fim_obj = datetime.strptime(hora_fim, '%H:%M').time()
                    
                    mapeamento_horario.append({
                        'operador_origem': operador_origem,
                        'operador_destino': operador_destino,
                        'hora_inicio': hora_inicio,
                        'hora_fim': hora_fim,
                        'hora_inicio_obj': hora_inicio_obj,
                        'hora_fim_obj': hora_fim_obj
                    })
                    
                    print(f"Adicionado mapeamento por horário: {operador_origem} -> {operador_destino} ({hora_inicio} - {hora_fim})")
                except Exception as e:
                    print(f"Erro ao processar horário para {operador_origem} -> {operador_destino}: {str(e)}")
            else:
                # Adiciona ao mapeamento padrão (sem horário)
                mapeamento_substituicoes[operador_origem] = operador_destino
                print(f"Adicionado mapeamento: {operador_origem} -> {operador_destino}")
        
        return mapeamento_substituicoes, mapeamento_horario if mapeamento_horario else None
    except Exception as e:
        print(f"Erro ao processar arquivo de substituições: {str(e)}")
        return {}, None 