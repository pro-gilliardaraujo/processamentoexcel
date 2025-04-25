from utils.constantes import ARQUIVO_SUBSTITUICOES, DEBUG, ARQUIVO_MATRIZ_OT, FILTRO_COLHEDORAS, FILTRO_TRANSBORDOS, FILTRO_TALHOES, UTILIZAR_MATRIZ_OT, ARQUIVO_EXCECOES_OT
from utils.funcoesOT import validar_registros
from utils.logger import setup_logger
from scripts.colhedorasMinOcioso import processar_dados_colhedoras
from scripts.transbordosMinOcioso import processar_dados_transbordos
from scripts.funcoesPreProcessamento import processar_substituicoes

def main():
    # Configuração do logger
    logger = setup_logger()
    logger.info("Iniciando processamento dos dados")

    # Processa as substituições
    mapeamento_substituicoes, mapeamento_horario = processar_substituicoes(ARQUIVO_SUBSTITUICOES)
    
    # Processa os dados das colhedoras
    dfs_colhedoras = processar_dados_colhedoras(
        filtro_colhedoras=FILTRO_COLHEDORAS, 
        mapeamento_substituicoes=mapeamento_substituicoes,
        mapeamento_horario=mapeamento_horario,
        validar_ot=(UTILIZAR_MATRIZ_OT == 'S'),
        matriz_ot_file=ARQUIVO_MATRIZ_OT if UTILIZAR_MATRIZ_OT == 'S' else None,
        excecoes_ot_file=ARQUIVO_EXCECOES_OT if UTILIZAR_MATRIZ_OT == 'S' else None
    )
    
    # Processa os dados dos transbordos
    dfs_transbordos = processar_dados_transbordos(
        filtro_transbordos=FILTRO_TRANSBORDOS,
        mapeamento_substituicoes=mapeamento_substituicoes,
        mapeamento_horario=mapeamento_horario,
        validar_ot=(UTILIZAR_MATRIZ_OT == 'S'),
        matriz_ot_file=ARQUIVO_MATRIZ_OT if UTILIZAR_MATRIZ_OT == 'S' else None,
        excecoes_ot_file=ARQUIVO_EXCECOES_OT if UTILIZAR_MATRIZ_OT == 'S' else None
    ) 