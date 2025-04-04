# paginador.py
import time
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from config import TEMPO_PAUSA_CURTO_ENTRE_PAGINAS, TEMPO_FALLBACK_PAGINA

def extrair_blocos_da_pagina(driver, wait):
    """
    Retorna os blocos de processos da página atual.
    Levanta exceção se não encontrar blocos.
    """
    blocos = wait.until(EC.presence_of_all_elements_located(
        (By.CLASS_NAME, "clsListaProcessoFormatoVerticalLinha")
    ))

    if not blocos:
        raise NoSuchElementException("Nenhum bloco de processo encontrado.")

    return blocos

def processar_bloco(bloco, driver, wait, extrair_detalhes_processo):
    """
    Processa um único bloco de processo e retorna os dados extraídos, se for HC.
    """
    from selenium.webdriver.common.by import By
    resultado = None
    try:
        links = bloco.find_elements(By.TAG_NAME, "a")
        for link in links:
            texto = link.text.strip()
            if texto.startswith("HC ") and not texto.startswith("RHC "):
                href = link.get_attribute("href")
                if href and "javascript:ProcessoDetalhes()" not in href:
                    driver.execute_script("window.open(arguments[0], '_blank');", href)
                    wait.until(lambda d: len(d.window_handles) == 2)
                    driver.switch_to.window(driver.window_handles[-1])

                    resultado = extrair_detalhes_processo(driver, wait)

                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    time.sleep(0.5)
                    break
    except Exception:
        pass
    return resultado

def navegar_paginas_e_extrair(driver, wait, extrair_detalhes_processo):
    """
    Navega pelas páginas de resultados e extrai dados de HCs.
    Retorna:
      - resultados extraídos
      - relatório textual sobre cada página processada
    """
    resultados = []
    relatorio_paginas = []
    pagina = 1

    while True:
        relatorio_paginas.append(f"📄 Página {pagina}:")

        try:
            blocos = extrair_blocos_da_pagina(driver, wait)
            relatorio_paginas[-1] += f" {len(blocos)} blocos encontrados."
        except TimeoutException:
            time.sleep(TEMPO_FALLBACK_PAGINA)
            try:
                blocos = extrair_blocos_da_pagina(driver, wait)
                relatorio_paginas[-1] += f" Timeout inicial, mas blocos recuperados após {TEMPO_FALLBACK_PAGINA}s."
            except TimeoutException:
                relatorio_paginas[-1] += f" ❌ Falha após {TEMPO_FALLBACK_PAGINA}s. Encerrando aqui."
                break

        hc_na_pagina = 0
        for bloco in blocos:
            resultado = processar_bloco(bloco, driver, wait, extrair_detalhes_processo)
            if resultado:
                resultados.append(resultado)
                hc_na_pagina += 1

        relatorio_paginas[-1] += f" {hc_na_pagina} HCs extraídos."

        # Tentar passar para a próxima página
        try:
            proximo = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(@title, 'próxima página')]")
            ))
            driver.execute_script("arguments[0].click();", proximo)

            try:
                wait.until(EC.staleness_of(blocos[0]))
            except TimeoutException:
                time.sleep(TEMPO_PAUSA_CURTO_ENTRE_PAGINAS)

            pagina += 1
        except:
            relatorio_paginas.append("🚫 Nenhum botão de próxima página encontrado. Fim da navegação.")
            break

    return resultados, relatorio_paginas
