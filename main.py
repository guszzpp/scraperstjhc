import sys
import logging
from datetime import datetime
from selenium.common.exceptions import TimeoutException
from navegador import iniciar_navegador
from extrator import extrair_detalhes_processo
from exportador import exportar_resultados
from paginador import navegar_paginas_e_extrair
from formulario import preencher_formulario
from config import ORGAO_ORIGEM, URL_PESQUISA
from retroativos.integrador import obter_retroativos
from retroativos.notificador import notificar_resultados

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def main(data_referencia: str):
    logging.info("Data de referência para o scraper: %s", data_referencia)
    logging.info("Iniciando scraper de HCs STJ (Origem TJGO)")

    try:
        navegador = iniciar_navegador()
        navegador.get(URL_PESQUISA)

        preencher_formulario(navegador, data_referencia, ORGAO_ORIGEM)
        resultados_brutos = navegar_paginas_e_extrair(navegador)
        resultados_completos = []

        for idx, item in enumerate(resultados_brutos):
            try:
                detalhes = extrair_detalhes_processo(navegador, item)
                if detalhes:
                    resultados_completos.append(detalhes)
                else:
                    logging.warning("❗ Registro nulo na posição %d. Ignorado.", idx)
            except Exception as e:
                logging.warning("⚠️ Erro ao extrair dados de Processo: %s", e)

        exportar_resultados(resultados_completos, data_referencia)
        navegador.quit()

        # Comparar retroativos e gerar notificação
        try:
            df_retroativos = obter_retroativos()
        except Exception as e:
            logging.error("Erro ao verificar retroativos: %s", e)
            df_retroativos = None

        notificar_resultados(data_referencia, resultados_completos, df_retroativos)

    except TimeoutException:
        logging.error("Erro: Timeout durante a execução")
    except Exception as e:
        logging.error("Erro inesperado: %s", e)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python main.py <data no formato DD/MM/AAAA>")
        sys.exit(1)
    main(sys.argv[1])
