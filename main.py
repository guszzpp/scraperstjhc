# main.py

import sys
import logging
import math
import pandas as pd

from datetime import datetime
from pathlib import Path

from config import ONTEM as CONFIG_ONTEM, ORGAO_ORIGEM, URL_PESQUISA, TEMPO_PAUSA_CURTO_ENTRE_PAGINAS
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


def main(ontem_str: str = None):
    """
    1) Recebe ontem_str no formato DD/MM/AAAA (workflow passa como argumento).
    2) Se não for fornecido, usa CONFIG_ONTEM de config.py.
    3) Gera CSV, Excel, faz comparação anteontem↔ontem e prepara e‑mail.
    """
    # Define a data que será usada
    data_ontem = ontem_str or CONFIG_ONTEM
    logging.info("Data de referência para o scraper: %s", data_ontem)

    logging.info("Iniciando scraper de HCs STJ (Origem %s)", ORGAO_ORIGEM)
    driver = iniciar_navegador()

    try:
        # 1. Preencher formulário de pesquisa
        preencher_formulario(driver)
        logging.info("Formulário preenchido")

        # 2. Navegar páginas e extrair resultados
        resultados_brutos = navegar_paginas_e_extrair(driver)
        logging.info("Extração bruta concluída: %d itens", len(resultados_brutos))

        # 3. Extrair detalhes de cada processo
        resultados = [extrair_detalhes_processo(item) for item in resultados_brutos]
        logging.info("Detalhes de processos extraídos")

        # 4. Gerar CSV para comparação retroativa (usa data_ontem)
        df = pd.DataFrame(resultados)
        csv_path = salvar_csv_resultado(df, data_ontem)
        logging.info("CSV de resultados salvo em %s", csv_path)

        # 5. Exportar resultados principais para Excel
        exportar_resultados(resultados)
        logging.info("Excel de resultados exportado")

        # 6. Rechecagem retroativa e preparação de e‑mail
        df_retro = obter_retroativos(data_ontem)
        preparar_email_alerta_retroativos(df_retro)
        logging.info("Rechecagem retroativa executada e e‑mail preparado")

    except Exception as e:
        logging.error("Erro durante execução: %s", e, exc_info=True)

    finally:
        driver.quit()
        logging.info("Navegador encerrado")


if __name__ == "__main__":
    # Workflow do GitHub passará a data de ontem no primeiro argumento
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(arg)
