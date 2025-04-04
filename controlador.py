# controlador.py

import logging
from selenium.common.exceptions import TimeoutException, WebDriverException
from navegador import iniciar_navegador
from config import ORGAO_ORIGEM
from formulario import preencher_formulario
from paginador import navegar_paginas_e_extrair
from exportador import exportar_resultados
from extrator import extrair_detalhes_processo

def executar_busca(data_inicial, data_final):
    """
    Executa todo o fluxo: inicia navegador, preenche formulário, extrai dados e exporta.
    """
    driver = None
    resultados = []

    try:
        logging.info("Inicializando navegador...")
        driver = iniciar_navegador()
        wait_timeout = 20

        from selenium.webdriver.support.ui import WebDriverWait
        wait = WebDriverWait(driver, wait_timeout)

        logging.info(f"Iniciando busca para intervalo: {data_inicial} a {data_final}")
        preencher_formulario(driver, wait, data_inicial, data_final, ORGAO_ORIGEM)

        logging.info("Iniciando extração de dados paginados...")
        resultados = navegar_paginas_e_extrair(driver, wait, extrair_detalhes_processo)

    except TimeoutException as te:
        print(f"⛔ Timeout ao preencher formulário ou carregar páginas: {te}")
        logging.error(f"Timeout crítico: {te}", exc_info=True)
    except WebDriverException as we:
        print(f"❌ Erro no WebDriver: {we}")
        logging.critical(f"Erro no WebDriver: {we}", exc_info=True)
    except Exception as e:
        print(f"❌ Erro inesperado durante a execução: {e}")
        logging.critical(f"Erro inesperado: {e}", exc_info=True)
    finally:
        if driver:
            driver.quit()
            logging.info("Navegador fechado.")

    if resultados:
        logging.info(f"Exportando {len(resultados)} resultados.")
        exportador = exportar_resultados(resultados, data_inicial, data_final)
    else:
        logging.info("Nenhum resultado a exportar.")
        print("⚠️ Nenhum resultado encontrado para exportar.")

    return resultados
