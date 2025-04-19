# main.py

import sys
import re
import time
import logging
from datetime import datetime
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pathlib import Path
from textwrap import dedent
import math  # Mantido para cálculo de páginas em caso de múltiplos resultados

import pandas as pd
from retroativos.gerenciador_arquivos import salvar_csv_resultado
from retroativos.integrador import obter_retroativos
from email_detalhado import preparar_email_alerta_retroativos

# Certifique-se que os outros arquivos .py estão na mesma pasta
from navegador import iniciar_navegador
from extrator import extrair_detalhes_processo
from exportador import exportar_resultados
from paginador import navegar_paginas_e_extrair  # Retorna 2 valores
from formulario import preencher_formulario
from config import ONTEM, ORGAO_ORIGEM, URL_PESQUISA

# Configuração do Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def main():
    logging.info("Iniciando scraper de HCs STJ (Origem TJGO)")
    driver = iniciar_navegador()

    try:
        # 1. Preencher formulário de pesquisa
        preencher_formulario(driver)
        logging.info("Formulário preenchido")

        # 2. Navegar páginas e extrair resultados brutos
        resultados_brutos = navegar_paginas_e_extrair(driver)
        logging.info("Extração bruta concluída: %d itens", len(resultados_brutos))

        # 3. Extrair detalhes de cada processo
        resultados = [
            extrair_detalhes_processo(item) for item in resultados_brutos
        ]
        logging.info("Detalhes de processos extraídos")

        # 4. Gerar CSV para comparação retroativa
        df = pd.DataFrame(resultados)
        csv_path = salvar_csv_resultado(df)
        logging.info("CSV de resultados salvo em %s", csv_path)

        # 5. Exportar resultados principais para Excel
        exportar_resultados(resultados)
        logging.info("Excel de resultados exportado")

        # 6. Rechecagem retroativa e preparação de e-mail
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
