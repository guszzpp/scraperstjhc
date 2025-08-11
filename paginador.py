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
                import re
                # 1. Tenta extrair pelo padrão "Exibindo X–Y de Z" (abrange todos os casos com mais de 1 resultado)
                try:
                    info_element = driver.find_element(By.XPATH, "//*[contains(text(), 'Exibindo') and contains(text(), 'de')]")
                    info_text = info_element.text.strip()
                    print(f"[DEBUG] Texto de info de resultados extraído: '{info_text}'")
                    match = re.search(r"Exibindo (\d+)[–\-—](\d+) de (\d+)", info_text)
                    if match:
                        inicio, fim, total = map(int, match.groups())
                        total_resultados_site = total
                        resultados_por_pagina = fim - inicio + 1
                        paginas_total_previstas = (total + resultados_por_pagina - 1) // resultados_por_pagina
                        print(f"[DEBUG] Regex principal capturou: inicio={inicio}, fim={fim}, total={total}")
                    else:
                        match_total = re.search(r"de (\d+)", info_text)
                        if match_total:
                            total = int(match_total.group(1))
                            total_resultados_site = total
                            print(f"[DEBUG] Regex alternativo capturou total_resultados_site={total_resultados_site}")
                        else:
                            print(f"[ERRO] Regex não capturou total de resultados no texto: '{info_text}'")
                            total_resultados_site = None
                            paginas_total_previstas = None
                except Exception as e:
                    print(f"[DEBUG] 'Exibindo ... de ...' não encontrado ou erro: {e}")

                # 2. Se não achou, tenta o padrão "Pesquisa resultou em <b>1</b> registro(s)!"
                if total_resultados_site is None:
                    try:
                        mensagem_element = driver.find_element(By.CSS_SELECTOR, ".clsMensagemLinha")
                        mensagem_html = mensagem_element.get_attribute("innerHTML")
                        print(f"[DEBUG] HTML de .clsMensagemLinha: '{mensagem_html}'")
                        match_registros = re.search(r"Pesquisa resultou em <b>(\d+)</b> registro", mensagem_html)
                        if match_registros:
                            total_resultados_site = int(match_registros.group(1))
                            print(f"[DEBUG] Capturado total_resultados_site={total_resultados_site} via .clsMensagemLinha")
                            paginas_total_previstas = 1
                        else:
                            print(f"[DEBUG] .clsMensagemLinha presente mas regex não bateu: '{mensagem_html}'")
                    except Exception as e:
                        print(f"[DEBUG] .clsMensagemLinha não encontrada ou erro: {e}")

                # 3. Se ainda não achou, pode ser o caso de cair direto na página de detalhes de 1 resultado
                if total_resultados_site is None:
                    print("[DEBUG] Nenhum total de resultados encontrado, assumindo 1 resultado (página de detalhe única)")
                    total_resultados_site = 1
                    paginas_total_previstas = 1
            except Exception as e:
                print(f"[ERRO] Falha inesperada ao extrair total de resultados do site: {e}")
                total_resultados_site = 1
                paginas_total_previstas = 1

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
        print(f"[ERRO] total_resultados_site ficou None, usando fallback len(resultados)={len(resultados)}")
        total_resultados_site = len(resultados)
    if paginas_total_previstas is None:
        paginas_total_previstas = paginas_processadas

    return resultados, relatorio_paginas, total_resultados_site, paginas_total_previstas, paginas_processadas
