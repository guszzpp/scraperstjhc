import sys
import logging
import math
import pandas as pd

from datetime import datetime
from pathlib import Path
from selenium.webdriver.support.ui import WebDriverWait

from config import (
    ONTEM as CONFIG_ONTEM,
    ORGAO_ORIGEM,
    URL_PESQUISA,
    TEMPO_PAUSA_CURTO_ENTRE_PAGINAS,
)

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


def salvar_arquivos_email(seguro=True, assunto=None, corpo=None, anexo=None):
    assunto = assunto or "🛑 Falha na execução do scraper"
    corpo = corpo or (
        "O scraper foi executado, mas ocorreu uma falha antes da conclusão.\n\n"
        "Verifique os logs de execução e o repositório para mais informações."
    )
    anexo = anexo or ""

    Path("email_subject.txt").write_text(assunto, encoding="utf-8")
    Path("email_body.txt").write_text(corpo, encoding="utf-8")
    Path("attachment.txt").write_text(anexo, encoding="utf-8")


def main(ontem_str: str = None):
    data_ontem = ontem_str or CONFIG_ONTEM
    logging.info("Data de referência para o scraper: %s", data_ontem)

    logging.info("Iniciando scraper de HCs STJ (Origem %s)", ORGAO_ORIGEM)
    driver = iniciar_navegador()
    try:
        wait = WebDriverWait(driver, TEMPO_PAUSA_CURTO_ENTRE_PAGINAS)
        preencher_formulario(driver, wait, data_ontem, data_ontem)
        logging.info("Formulário preenchido")

        resultados_brutos = navegar_paginas_e_extrair(
            driver, wait, extrair_detalhes_processo, data_ontem
        )
        logging.info("Extração bruta concluída: %d itens", len(resultados_brutos))

        resultados = [extrair_detalhes_processo(item, wait) for item in resultados_brutos]
        logging.info("Detalhes de processos extraídos")

        df = pd.DataFrame(resultados)
        csv_path = salvar_csv_resultado(df, data_ontem)
        logging.info("CSV de resultados salvo em %s", csv_path)

        exportar_resultados(resultados, data_ontem, data_ontem)
        logging.info("Excel de resultados exportado")

        try:
            df_retro = obter_retroativos(data_ontem)
            preparar_email_alerta_retroativos(df_retro)
            logging.info("Rechecagem retroativa executada e e‑mail preparado")
        except Exception as e:
            logging.error(f"Erro ao verificar retroativos: {e}")

        # Criar arquivo sentinela para garantir persistência do cache
        try:
            Path("dados_diarios/.timestamp").write_text(f"{datetime.now()}")
            logging.info("Arquivo .timestamp criado para forçar salvamento do cache.")
        except Exception as e:
            logging.warning(f"Não foi possível criar .timestamp: {e}")

    except Exception as e:
        logging.error("Erro durante execução: %s", e, exc_info=True)
        salvar_arquivos_email()

    finally:
        driver.quit()
        logging.info("Navegador encerrado")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(arg)
