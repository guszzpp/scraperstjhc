# main.py
import sys
import re
import time
import logging
from datetime import datetime
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
import json # <--- IMPORTADO

# Certifique-se que os outros arquivos .py estão na mesma pasta
from navegador import iniciar_navegador
from extrator import extrair_detalhes_processo
from exportador import exportar_resultados
from paginador import navegar_paginas_e_extrair
from formulario import preencher_formulario
from config import ONTEM, ORGAO_ORIGEM, URL_PESQUISA # Importa URL também

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def buscar_processos(data_inicial, data_final):
    """
    Executa o fluxo de busca e retorna estatísticas e nome do arquivo gerado.
    """
    resultados = []
    total_resultados_site = -1 # -1 indica que não foi possível obter
    total_paginas = 0
    paginas_processadas = 0
    relatorio_paginas = []
    erro_critico = None
    nome_arquivo_gerado = None
    driver = None # Inicializa driver como None
    horario_inicio = datetime.now()

    logging.info(f"🟡 Iniciando busca de HCs no STJ — {data_inicial} até {data_final}")
    logging.info(f"   URL: {URL_PESQUISA}")
    logging.info(f"   Órgão Origem: {ORGAO_ORIGEM}")

    try:
        driver = iniciar_navegador()
        # Aumentar um pouco o wait principal pode ajudar em GHA
        wait = WebDriverWait(driver, 20)

        preencher_formulario(driver, wait, data_inicial, data_final)
        logging.info("✅ Formulário preenchido.")

        # 🔎 Captura do total de resultados do site
        try:
            # Espera pela mensagem OU pela lista de resultados como indicador de carga
            wait.until(lambda d: d.find_element("class name", "clsMensagemLinha") or d.find_element("class name", "clsListaProcessoFormatoVerticalLinha"))
            time.sleep(1) # Pequena pausa após carregar

            # Tenta pegar a mensagem especificamente
            mensagem = driver.find_element("class name", "clsMensagemLinha")
            texto = mensagem.text.strip()
            match = re.search(r'(\d+)', texto)
            if match:
                total_resultados_site = int(match.group(1))
                logging.info(f"📊 Site reportou {total_resultados_site} resultados totais.")
            else:
                 logging.warning(f"⚠️ Não foi possível extrair número da mensagem: '{texto}'")
        except Exception as e:
            # Se a mensagem não aparecer (pode ir direto para resultados), não é erro fatal
            logging.warning(f"ℹ️ Não foi possível capturar o total de registros da mensagem (pode não haver mensagem): {e}")

        logging.info("🔍 Iniciando navegação nas páginas de resultados...")
        # Passar data_inicial para ser usada como 'data_autuacao' padrão nos resultados
        resultados, relatorio_paginas = navegar_paginas_e_extrair(driver, wait, extrair_detalhes_processo, data_inicial)

        paginas_processadas = len(relatorio_paginas)
        # A melhor estimativa para total_paginas é o número de páginas processadas
        total_paginas = paginas_processadas

    except TimeoutException as e:
        erro_critico = f"Timeout ({type(e).__name__}): {str(e)}"
        logging.error(f"❌ Erro crítico (Timeout): {erro_critico}", exc_info=True)
    except WebDriverException as e:
         erro_critico = f"WebDriver Error ({type(e).__name__}): {str(e)}"
         logging.error(f"❌ Erro crítico (WebDriver): {erro_critico}", exc_info=True)
    except Exception as e:
        erro_critico = f"Erro Inesperado ({type(e).__name__}): {str(e)}"
        logging.error(f"❌ Erro inesperado: {erro_critico}", exc_info=True)

    finally:
        if driver:
            try:
                driver.quit()
                logging.info("🔻 Navegador fechado.")
            except Exception as e:
                logging.warning(f"⚠️ Erro ao fechar navegador: {e}")

    qtd_hcs_extraidos = len(resultados)

    if resultados:
        logging.info(f"📊 Total de HCs extraídos: {qtd_hcs_extraidos}")
        try:
            nome_arquivo_gerado = exportar_resultados(resultados, data_inicial, data_final)
        except Exception as e:
             logging.error(f"❌ Erro ao exportar resultados para Excel: {e}")
             erro_critico = erro_critico or f"Erro ao exportar Excel: {e}" # Adiciona ou substitui erro
    elif not erro_critico:
        logging.info("✅ Nenhum Habeas Corpus encontrado ou extraído com sucesso.")
    else: # Se houve erro crítico e não há resultados
         logging.warning("⚠️ Extração interrompida por erro, nenhum HC foi extraído.")


    if relatorio_paginas:
        logging.info("📄 Relatório de páginas processadas:")
        for linha in relatorio_paginas:
            logging.info(f"   - {linha}")
    elif not erro_critico:
        logging.info("⚠️ Nenhuma página foi processada (talvez nenhum resultado encontrado).")

    horario_finalizacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    duracao = (datetime.now() - horario_inicio).total_seconds()
    logging.info(f"✅ Execução finalizada às {horario_finalizacao} (Duração: {duracao:.2f}s)")

    # Cria o dicionário com as informações para o JSON
    stats = {
        "data_inicial": data_inicial,
        "data_final": data_final,
        "orgao_origem": ORGAO_ORIGEM,
        "qtd_resultados_site": total_resultados_site, # Quantos o site disse ter encontrado
        "qtd_hcs": qtd_hcs_extraidos,         # Quantos HCs foram efetivamente extraídos
        "paginas_total": total_paginas,           # Melhor estimativa do total de páginas
        "paginas_processadas": paginas_processadas, # Quantas páginas foram de fato iteradas
        "horario_finalizacao": horario_finalizacao,
        "duracao_segundos": round(duracao, 2),
        "erro_critico": erro_critico, # Será None se não houver erro crítico
        "arquivo_gerado": nome_arquivo_gerado # Nome do arquivo .xlsx se foi gerado
    }

    # Retorna o dicionário de estatísticas e o nome do arquivo
    return stats, nome_arquivo_gerado


# Execução principal
if __name__ == "__main__":
    if len(sys.argv) == 3:
        data_ini_arg, data_fim_arg = sys.argv[1], sys.argv[2]
        logging.info(f"Datas recebidas via argumento: INI={data_ini_arg}, FIM={data_fim_arg}")
    elif len(sys.argv) == 2:
        data_ini_arg = data_fim_arg = sys.argv[1]
        logging.info(f"Data recebida via argumento: {data_ini_arg}")
    else:
        data_ini_arg = data_fim_arg = ONTEM
        logging.info(f"Nenhuma data fornecida, usando data padrão (ontem): {ONTEM}")

    # Validação do formato da data
    date_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    if not date_pattern.match(data_ini_arg) or not date_pattern.match(data_fim_arg):
        logging.error(f"❌ Formato de data inválido. Recebido: INI='{data_ini_arg}', FIM='{data_fim_arg}'. Use DD/MM/AAAA.")
        # Cria um JSON de erro para o workflow saber o que aconteceu
        error_stats = {
            "data_inicial": data_ini_arg, "data_final": data_fim_arg, "orgao_origem": ORGAO_ORIGEM,
            "qtd_resultados_site": -1, "qtd_hcs": 0, "paginas_total": 0, "paginas_processadas": 0,
            "horario_finalizacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "duracao_segundos": 0,
            "erro_critico": "Formato de data inválido recebido.", "arquivo_gerado": None
        }
        try:
            with open("info_execucao.json", "w", encoding="utf-8") as f:
                json.dump(error_stats, f, ensure_ascii=False, indent=4)
            logging.info("ℹ️ Informações de erro (data inválida) salvas em info_execucao.json")
        except Exception as e:
             logging.error(f"⚠️ Erro crítico ao salvar JSON de erro de data: {e}")
        sys.exit(1) # Sai com erro

    # Chama a função principal
    execution_stats, result_filename = buscar_processos(data_ini_arg, data_fim_arg)

    # Salva as estatísticas no arquivo JSON esperado pelo workflow
    try:
        with open("info_execucao.json", "w", encoding="utf-8") as f:
            json.dump(execution_stats, f, ensure_ascii=False, indent=4)
        logging.info("✅ Informações de execução salvas em info_execucao.json")
    except Exception as e:
        logging.error(f"❌ Erro crítico ao salvar info_execucao.json: {e}")
        # Se não conseguir salvar o JSON, o workflow não terá os dados.
        # É importante sair com erro para indicar a falha.
        sys.exit(1)

    # Opcional: Sair com código de erro se houve erro crítico durante a busca
    # Isso fará o passo 'Rodar o scraper' no GHA falhar explicitamente.
    if execution_stats.get("erro_critico"):
       logging.error("Finalizando com status de erro devido a erro crítico durante a execução.")
       sys.exit(1)
    else:
         logging.info("Finalizando com status de sucesso.")
         sys.exit(0) # Sai com sucesso
