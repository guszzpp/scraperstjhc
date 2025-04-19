# main.py

import sys
import re
import time
import logging
from datetime import datetime
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pathlib import Path
from textwrap import dedent
import math

import pandas as pd
from config import ONTEM, ORGAO_ORIGEM, URL_PESQUISA, TEMPO_PAUSA_CURTO_ENTRE_PAGINAS
from retroativos.gerenciador_arquivos import salvar_csv_resultado
from retroativos.integrador import obter_retroativos
from email_detalhado import preparar_email_alerta_retroativos

from navegador import iniciar_navegador
from extrator import extrair_detalhes_processo
from exportador import exportar_resultados
from paginador import navegar_paginas_e_extrair
from formulario import preencher_formulario

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def main():
    logging.info("Iniciando scraper de HCs STJ (Origem %s)", ORGAO_ORIGEM)
    driver = iniciar_navegador()
    try:
        # preencher e extrair
        preencher_formulario(driver)
        logging.info("Formulário preenchido")

        resultados_brutos = navegar_paginas_e_extrair(driver)
        logging.info("Extração bruta concluída: %d itens", len(resultados_brutos))

        resultados = [extrair_detalhes_processo(item) for item in resultados_brutos]
        logging.info("Detalhes de processos extraídos")

        # gerar CSV com base em ONTEM
        df = pd.DataFrame(resultados)
        csv_path = salvar_csv_resultado(df, ONTEM)
        logging.info("CSV de resultados salvo em %s", csv_path)

        # exportar Excel
        exportar_resultados(resultados)
        logging.info("Excel de resultados exportado")

        # rechecagem retroativa e preparação de e-mail
        df_retro = obter_retroativos()
        preparar_email_alerta_retroativos(df_retro)
        logging.info("Rechecagem retroativa executada e e-mail preparado")

    except Exception as e:
        logging.error("Erro durante execução: %s", e, exc_info=True)
    finally:
        driver.quit()
        logging.info("Navegador encerrado")

if __name__ == "__main__":
    main()
