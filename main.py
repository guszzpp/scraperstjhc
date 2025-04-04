# main.py
import sys
import re
import time
import json
import logging
from datetime import datetime
from selenium.common.exceptions import TimeoutException, WebDriverException

from navegador import iniciar_navegador
from extrator import extrair_detalhes_processo
from exportador import exportar_resultados
from paginador import navegar_paginas_e_extrair, obter_total_paginas
from formulario import preencher_formulario_busca
from config import ONTEM, URL_PESQUISA

# Configuração do logging
logging.basicConfig(filename="scraper.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def buscar_processos(data_inicial, data_final):
    resultados = []
    total_resultados = 0
    total_paginas = 0
    ultima_pagina_processada = 0
    driver = None

    try:
        driver = iniciar_navegador()
        logging.info(f"Iniciando busca: {data_inicial} a {data_final}")

        total_resultados = preencher_formulario_busca(driver, data_inicial, data_final)
        total_paginas = obter_total_paginas(driver)

        resultados, ultima_pagina_processada = navegar_paginas_e_extrair(driver, extrair_detalhes_processo)

    except (TimeoutException, WebDriverException) as e:
        logging.error(f"Erro crítico: {e}")
    finally:
        if driver:
            driver.quit()
            logging.info("Navegador fechado.")

    qtd_hcs = len(resultados)

    if qtd_hcs > 0:
        exportar_resultados(resultados, data_inicial, data_final)
    else:
        with open("resultados_vazio.txt", "w", encoding="utf-8") as f:
            f.write("Nenhum HC encontrado.")

    # Gera arquivo info_execucao.json
    info = {
        "data_inicial": data_inicial,
        "data_final": data_final,
        "qtd_resultados": total_resultados,
        "qtd_hcs": qtd_hcs,
        "paginas_total": total_paginas,
        "paginas_processadas": ultima_pagina_processada,
        "horario_finalizacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    with open("info_execucao.json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    print("✅ Execução finalizada.")

# Execução principal
if __name__ == "__main__":
    if len(sys.argv) == 3:
        data_ini, data_fim = sys.argv[1], sys.argv[2]
    elif len(sys.argv) == 2:
        data_ini = data_fim = sys.argv[1]
    else:
        data_ini = data_fim = ONTEM

    date_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    if not date_pattern.match(data_ini) or not date_pattern.match(data_fim):
        print("❌ Formato inválido. Use DD/MM/AAAA.")
        sys.exit(1)

    buscar_processos(data_ini, data_fim)
