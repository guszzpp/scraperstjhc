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

    while True:
        relatorio = f"📄 Página {pagina}: "

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

    return resultados, relatorio_paginas
