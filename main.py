import sys
import logging
import pandas as pd
from datetime import datetime
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from navegador import iniciar_navegador
from extrator import extrair_detalhes_processo
from exportador import exportar_resultados
from paginador import navegar_paginas_e_extrair
from formulario import preencher_formulario
from config import ORGAO_ORIGEM, URL_PESQUISA
from retroativos.integrador import obter_retroativos
from retroativos.gerenciador_arquivos import salvar_csv_resultado

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def main(data_referencia: str):
    logging.info("Data de referência para o scraper: %s", data_referencia)
    logging.info("Iniciando scraper de HCs STJ (Origem TJGO)")

    try:
        # Iniciar navegador e configurar wait
        navegador = iniciar_navegador()
        wait = WebDriverWait(navegador, 30)  # Timeout de 30 segundos

        # Preencher formulário com data de referência
        preencher_formulario(navegador, wait, data_referencia, data_referencia)
        
        # Obter resultados
        resultados, paginas_info = navegar_paginas_e_extrair(
            navegador, 
            wait, 
            extrair_detalhes_processo, 
            data_referencia
        )
        
        # Log de informações sobre páginas
        for info in paginas_info:
            logging.info(info)
            
        # Exportar para Excel
        caminho_excel = exportar_resultados(resultados, data_referencia, data_referencia)
        
        # Salvar CSV para sistema de retroativos
        if resultados:
            df = pd.DataFrame(resultados)
            caminho_csv = salvar_csv_resultado(df, data_referencia)
            logging.info(f"Dados salvos no formato CSV em: {caminho_csv}")
        else:
            logging.info("Nenhum resultado encontrado, CSV não gerado.")
            
        # Fechar navegador
        navegador.quit()
        
        logging.info("Scraper concluído com sucesso.")
        
    except TimeoutException:
        logging.error("Erro: Timeout durante a execução")
    except Exception as e:
        logging.error("Erro inesperado: %s", e, exc_info=True)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python main.py <data no formato DD/MM/AAAA>")
        sys.exit(1)
    main(sys.argv[1])
