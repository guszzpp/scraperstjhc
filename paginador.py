# paginador.py

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from config import TEMPO_PAUSA_CURTO_ENTRE_PAGINAS
from selenium.common.exceptions import TimeoutException

def navegar_paginas_e_extrair(driver, wait, extrair_detalhes_processo, data_autuacao):
    resultados = []
    relatorio_paginas = []
    pagina = 1
    paginas_processadas = 0
    total_resultados_site = None
    paginas_total_previstas = None
    resultados_por_pagina = None

    while True:
        relatorio = f"📄 Página {pagina}: "

        # Na primeira página, tentar extrair o total de resultados do site
        if pagina == 1:
            try:
                # O texto costuma ser algo como: "Exibindo 1–10 de 15"
                info_element = driver.find_element(By.XPATH, "//*[contains(text(), 'Exibindo') and contains(text(), 'de')]")
                info_text = info_element.text.strip()
                import re
                match = re.search(r"Exibindo (\d+)[–-](\d+) de (\d+)", info_text)
                if match:
                    inicio, fim, total = map(int, match.groups())
                    total_resultados_site = total
                    resultados_por_pagina = fim - inicio + 1
                    # Cálculo do total de páginas previstas
                    paginas_total_previstas = (total + resultados_por_pagina - 1) // resultados_por_pagina
                else:
                    total_resultados_site = None
                    paginas_total_previstas = None
            except Exception:
                total_resultados_site = None
                paginas_total_previstas = None

        try:
            blocos = wait.until(EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "clsListaProcessoFormatoVerticalLinha")
            ))
        except TimeoutException:
            relatorio += "❌ Timeout ao tentar localizar blocos. Interrompendo."
            relatorio_paginas.append(relatorio)
            break

        hc_na_pagina = 0

        for bloco in blocos:
            links = bloco.find_elements(By.TAG_NAME, "a")
            for link in links:
                texto = link.text.strip()
                if texto.startswith("HC ") and not texto.startswith("RHC "):
                    href = link.get_attribute("href")
                    if href and "javascript:ProcessoDetalhes()" not in href:
                        try:
                            driver.execute_script("window.open(arguments[0]);", href)
                            wait.until(lambda d: len(d.window_handles) == 2)
                            driver.switch_to.window(driver.window_handles[-1])

                            resultado = extrair_detalhes_processo(driver, wait, texto, data_autuacao)
                            if resultado:
                                resultados.append(resultado)
                                hc_na_pagina += 1

                        except Exception as e:
                            print(f"⚠️ Erro ao processar link {href}: {e}")
                        finally:
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                            time.sleep(0.5)
                        break  # só processa um link HC por bloco

        relatorio += f"{len(blocos)} blocos analisados, {hc_na_pagina} HCs extraídos."
        relatorio_paginas.append(relatorio)
        paginas_processadas += 1

        # Próxima página
        try:
            botao_proximo = driver.find_element(By.LINK_TEXT, "Próximo")
            if "desabilitado" in botao_proximo.get_attribute("class").lower():
                relatorio_paginas.append("⏹️ Fim da navegação: botão 'Próximo' desabilitado.")
                break
            else:
                botao_proximo.click()
                time.sleep(TEMPO_PAUSA_CURTO_ENTRE_PAGINAS)
                pagina += 1
        except Exception:
            relatorio_paginas.append("⏹️ Fim da navegação: botão 'Próximo' não encontrado.")
            break

    # Garantir que os valores não fiquem None
    if total_resultados_site is None:
        total_resultados_site = len(resultados)
    if paginas_total_previstas is None:
        paginas_total_previstas = paginas_processadas

    return resultados, relatorio_paginas, total_resultados_site, paginas_total_previstas, paginas_processadas
