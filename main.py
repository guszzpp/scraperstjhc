# main.py
import sys
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from navegador import iniciar_navegador
from extrator import extrair_detalhes_processo
from exportador import exportar_resultados
from config import ONTEM

# Configuração do Logging
logging.basicConfig(filename='scraper.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

def buscar_processos(data_inicial, data_final):
    """
    Busca processos de Habeas Corpus (HC) no STJ originários do TJGO
    dentro de um intervalo de datas especificado.
    """
    resultados = []
    driver = None # Inicializa driver como None para o finally funcionar caso a inicialização falhe

    try:
        driver = iniciar_navegador()
        # Aumenta um pouco o timeout padrão para acomodar variações de rede/servidor
        wait = WebDriverWait(driver, 20)

        print("\n🔎 Iniciando busca de HCs no STJ...")
        print(f"🗓️  Intervalo de datas: {data_inicial} a {data_final}\n")
        logging.info(f"Iniciando busca. Intervalo de datas: {data_inicial} a {data_final}")

        # --- Acesso à página e preenchimento do formulário ---
        try:
            url = "https://processo.stj.jus.br/processo/pesquisa/?aplicacao=processos.ea"
            driver.get(url)
            logging.info(f"Acessando URL: {url}")
            # Espera um elemento principal da página carregar antes de prosseguir
            wait.until(EC.presence_of_element_located((By.ID, "idDataAutuacaoInicial")))

            campo_data_inicial = wait.until(EC.visibility_of_element_located((By.ID, "idDataAutuacaoInicial")))
            campo_data_inicial.clear()
            campo_data_inicial.send_keys(data_inicial)
            logging.info(f"Preenchendo data inicial: {data_inicial}")

            campo_data_final = wait.until(EC.visibility_of_element_located((By.ID, "idDataAutuacaoFinal")))
            campo_data_final.clear()
            campo_data_final.send_keys(data_final)
            logging.info(f"Preenchendo data final: {data_final}")

            # Garante que a seção do julgador esteja visível e clicável
            secao_julgador = wait.until(EC.element_to_be_clickable((By.ID, "idJulgadorOrigemTipoBlocoLabel")))
            # Scroll até o elemento pode ajudar em algumas resoluções
            driver.execute_script("arguments[0].scrollIntoView(true);", secao_julgador)
            time.sleep(0.5) # Pequena pausa após scroll
            secao_julgador.click()
            logging.info("Clicando na seção 'Órgão Julgador / Origem'")
            time.sleep(0.5) # Pausa para a seção abrir

            campo_origem = wait.until(EC.visibility_of_element_located((By.ID, "idOrgaosOrigemCampoParaPesquisar")))
            campo_origem.clear()
            campo_origem.send_keys("TJGO")
            logging.info("Preenchendo origem: TJGO")
            time.sleep(1) # Pausa para possível auto-complete ou validação

            botao_pesquisar = wait.until(EC.element_to_be_clickable((By.ID, "idBotaoPesquisarFormularioExtendido")))
            # Scroll até o botão pode ser útil
            driver.execute_script("arguments[0].scrollIntoView(true);", botao_pesquisar)
            time.sleep(0.5)
            botao_pesquisar.click()
            logging.info("Clicando no botão 'Pesquisar'")

            # Espera o carregamento dos resultados (a mensagem ou a lista de processos)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".clsMensagemLinha, .clsListaProcessoFormatoVerticalLinha")))
            logging.info("Pesquisa enviada, aguardando resultados...")
            time.sleep(2) # Pausa adicional para garantir a renderização completa

        except TimeoutException as e:
            print("⛔ Erro: Timeout ao tentar preencher ou enviar o formulário de pesquisa.")
            print(f"   Detalhe: {e}")
            logging.error(f"Timeout ao preencher/enviar formulário: {e}", exc_info=True)
            return # Retorna cedo se o formulário falhar
        except Exception as e:
            print(f"⛔ Erro inesperado ao interagir com o formulário: {e}")
            logging.error(f"Erro inesperado no formulário: {e}", exc_info=True)
            return

        # --- Verificação e Extração de Resultados ---
        try:
            total_element = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "clsMensagemLinha")))
            texto_total = total_element.text.strip()
            # Tratamento mais robusto para extrair o número
            partes_num = [s for s in texto_total.split() if s.isdigit()]
            if partes_num:
                qtd_total = int(partes_num[0])
                print(f"🔍 Pesquisa retornou {qtd_total} processos encontrados para os critérios.")
                logging.info(f"Pesquisa retornou {qtd_total} processos.")
            else:
                 # Verifica se há processos na lista, mesmo sem a mensagem de total
                 try:
                     driver.find_element(By.CLASS_NAME, "clsListaProcessoFormatoVerticalLinha")
                     print("⚠️ Não foi possível ler a quantidade total na mensagem, mas há processos na lista.")
                     logging.warning("Falha ao ler total de processos na mensagem, mas lista encontrada.")
                     qtd_total = -1 # Indica que há processos, mas o total é desconhecido
                 except NoSuchElementException:
                     print("✅ Pesquisa concluída. Nenhum processo encontrado para os critérios.")
                     logging.info("Nenhum processo encontrado.")
                     return # Sai se realmente não houver processos

        except TimeoutException:
             # Se a mensagem de total não aparecer, verifica se há lista de processos
             try:
                 driver.find_element(By.CLASS_NAME, "clsListaProcessoFormatoVerticalLinha")
                 print("⚠️ Mensagem com total de processos não encontrada, mas há processos na lista.")
                 logging.warning("Mensagem de total não encontrada, mas lista de processos presente.")
                 qtd_total = -1
             except NoSuchElementException:
                 print("✅ Pesquisa concluída. Nenhum processo encontrado para os critérios (verificação dupla).")
                 logging.info("Nenhum processo encontrado (verificação dupla).")
                 return
        except Exception as e:
            print(f"⚠️ Erro ao tentar ler a quantidade total de processos: {e}")
            logging.warning(f"Falha inesperada ao ler total de processos: {e}", exc_info=True)
            qtd_total = -1 # Assume que pode haver processos

        # --- Loop de Paginação e Extração ---
        pagina = 1
        processos_hc_encontrados_total = 0

        while True:
            logging.info(f"Iniciando processamento da página {pagina}")
            print(f"\n📄 Processando página {pagina}...")

            try:
                # Espera que os blocos da página atual estejam presentes
                blocos_atuais = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "clsListaProcessoFormatoVerticalLinha")))
                if not blocos_atuais:
                    if pagina == 1: # Se não há blocos na primeira página, mesmo após a verificação anterior
                         print("❌ Nenhum bloco de processo encontrado na página 1. Encerrando.")
                         logging.warning("Nenhum bloco encontrado na página 1 (pós-verificação inicial).")
                    else: # Se sumiram em páginas posteriores, pode ser um erro ou fim inesperado
                         print(f"⚠️ Nenhum bloco de processo encontrado na página {pagina}. Possível fim ou erro.")
                         logging.warning(f"Nenhum bloco encontrado na página {pagina}.")
                    break # Sai do loop while

                # Guarda referência a um elemento da página ATUAL para checar staleness DEPOIS de paginar
                # Usar o primeiro bloco é geralmente seguro
                elemento_referencia_pagina_atual = blocos_atuais[0]
                print(f"   Encontrados {len(blocos_atuais)} blocos de processo nesta página.")
                logging.info(f"Página {pagina}: Encontrados {len(blocos_atuais)} blocos.")

                processos_hc_pagina = 0
                # Itera sobre os blocos da página atual
                for bloco in blocos_atuais:
                    try:
                        # Encontra todos os links dentro do bloco
                        links = bloco.find_elements(By.TAG_NAME, "a")
                        link_processo = None
                        for link in links:
                            texto = link.text.strip()
                            # Condição específica para HC (não RHC)
                            if texto.startswith("HC ") and not texto.startswith("RHC "):
                                href = link.get_attribute("href")
                                if href and "javascript:ProcessoDetalhes()" not in href: # Ignora links internos da página
                                    link_processo = link
                                    break # Encontrou o link de HC desejado neste bloco

                        if link_processo:
                            href_processo = link_processo.get_attribute("href")
                            texto_processo = link_processo.text.strip()
                            logging.info(f"Encontrado link de HC: {texto_processo}")

                            try:
                                # Abre o link em uma nova aba
                                driver.execute_script("window.open(arguments[0], '_blank');", href_processo)
                                # Espera a nova aba abrir (agora tem 2 janelas/abas)
                                wait.until(EC.number_of_windows_to_be(2))
                                # Muda o foco para a nova aba (a última na lista)
                                driver.switch_to.window(driver.window_handles[-1])
                                logging.info(f"Abrindo detalhes de {texto_processo} em nova aba.")

                                # Extrai os detalhes da nova aba
                                resultado = extrair_detalhes_processo(driver, wait) # Passa o wait também
                                if resultado:
                                    resultados.append(resultado)
                                    processos_hc_pagina += 1
                                    processos_hc_encontrados_total += 1
                                    # Imprime detalhes básicos
                                    print(f"   ✔️ HC: {resultado.get('numero_processo', 'N/D')} (Total: {processos_hc_encontrados_total})")
                                    print(f"      Relator(a): {resultado.get('relator', 'N/D')}")
                                    # print(f"      Situação:  {resultado.get('situacao', 'N/D')}") # Descomente se precisar
                                    print("-" * 40)
                                    logging.info(f"Detalhes extraídos para {resultado.get('numero_processo', 'N/D')}")
                                else:
                                     logging.warning(f"Falha ao extrair detalhes para o link de {texto_processo}")

                            except TimeoutException as te:
                                print(f"   ⚠️ Timeout ao processar detalhes do HC {texto_processo}: {te}")
                                logging.error(f"Timeout ao processar detalhes de {texto_processo}: {te}", exc_info=True)
                            except Exception as e_detalhe:
                                print(f"   ⚠️ Erro ao processar detalhes do HC {texto_processo}: {e_detalhe}")
                                logging.error(f"Erro ao processar detalhes de {texto_processo}: {e_detalhe}", exc_info=True)
                            finally:
                                # Garante que feche a aba e volte para a principal
                                if len(driver.window_handles) > 1:
                                    driver.close()
                                    driver.switch_to.window(driver.window_handles[0])
                                    # Pequena pausa para estabilizar após fechar aba e trocar contexto
                                    time.sleep(0.5)

                    except Exception as e_bloco:
                        print(f"   ⚠️ Erro ao processar um bloco de processo na página {pagina}: {e_bloco}")
                        logging.error(f"Erro ao processar bloco na página {pagina}: {e_bloco}", exc_info=True)
                        # Continua para o próximo bloco

                print(f"   Processados {processos_hc_pagina} HCs nesta página.")
                logging.info(f"Página {pagina}: Processados {processos_hc_pagina} HCs.")

                # --- Lógica de Paginação: Clicar no Link "Próxima Página" ---
                try:
                    input_pag = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class,'classSpanPaginacaoPaginaTextoInterno')]/input")))
                    input_pag.clear()
                    input_pag.send_keys(str(pagina))
                    driver.execute_script("FNavegaProcessosPessoas(true, arguments[0]);", pagina - 1)
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "clsListaProcessoFormatoVerticalLinha")))
                    print(f"➡️ Indo para a página {pagina}...\n")
                    logging.info(f"Indo para a página {pagina}...")
                    time.sleep(1)
                except Exception as e:
                    print(f"⚠️ Elemento de input de paginação não encontrado. Tentando clicar no botão 'próxima página'...")
                    try:
                        proximo_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@title, 'próxima página')]")))
                        driver.execute_script("arguments[0].click();", proximo_link)
                        pagina += 1
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "clsListaProcessoFormatoVerticalLinha")))
                        print(f"➡️ Indo para a página {pagina}...\n")
                        logging.info(f"Indo para a página {pagina} (via botão)...")
                        time.sleep(1)
                    except Exception as ex:
                        print(f"⚠️ Erro ao tentar clicar no botão 'próxima página': {ex}")
                        logging.warning(f"Erro ao tentar clicar no botão 'próxima página': {ex}")
                        break

                    # Scroll até o botão antes de clicar (pode ajudar)
                    driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", botao_proxima)
                    time.sleep(0.5) # Pausa após scroll

                    # Clica para ir para a próxima página
                    botao_proxima.click()
                    pagina += 1 # Incrementa o contador de página APÓS o clique bem-sucedido
                    print(f"➡️ Clicado em 'Próxima'. Indo para a página {pagina}...")
                    logging.info(f"Clicado em 'Próxima'. Indo para a página {pagina}.")

                    # **** Espera Robusta: Chave para a paginação funcionar ****
                    logging.info(f"Aguardando staleness do elemento de referência da página {pagina-1}.")
                    wait.until(EC.staleness_of(elemento_referencia_pagina_atual))
                    logging.info(f"Staleness detectado. Página {pagina} deve estar carregando.")

                    # Pausa explícita para dar tempo ao servidor/navegador após carregar a nova página
                    tempo_pausa_entre_paginas = 10 # Ajuste conforme necessário (comece com 2 ou 3 segundos)
                    print(f"   ...aguardando {tempo_pausa_entre_paginas}s antes de processar a próxima página...")
                    time.sleep(tempo_pausa_entre_paginas)
                    logging.info(f"Pausa de {tempo_pausa_entre_paginas}s após carregar página {pagina}.")


                except TimeoutException:
                    # ... (código existente para fim da paginação) ...
                    break # Sai do loop while


            except TimeoutException as e_page_load:
                 # Timeout esperando os blocos no início do loop while
                 print(f"⚠️ Timeout ao esperar o carregamento dos blocos na página {pagina}: {e_page_load}")
                 logging.error(f"Timeout esperando blocos na página {pagina}: {e_page_load}", exc_info=True)
                 break # Interrompe se a página não carregar
            except Exception as e_page:
                print(f"⚠️ Erro inesperado durante o processamento da página {pagina}: {e_page}")
                logging.error(f"Erro inesperado na página {pagina}: {e_page}", exc_info=True)
                break # Interrompe em caso de erro grave na página

        # --- Fim do Loop ---
        print("\n✅ Fim da navegação por páginas.")
        print(f"\n📊 Total de HCs encontrados e processados: {processos_hc_encontrados_total}")
        if qtd_total != -1:
             print(f"   (Pesquisa inicial indicou {qtd_total} processos totais nos critérios)")
        logging.info(f"Fim da navegação. Total de HCs processados: {processos_hc_encontrados_total}. Páginas percorridas: {pagina-1}.")

    except WebDriverException as e:
        print(f"❌ Erro crítico do WebDriver/Navegador: {e}")
        logging.critical(f"Erro crítico do WebDriver: {e}", exc_info=True)
    except Exception as e:
        print(f"❌ Erro inesperado na função principal 'buscar_processos': {e}")
        logging.critical(f"Erro inesperado em buscar_processos: {e}", exc_info=True)

    finally:
        if driver:
            driver.quit()
            logging.info("Navegador fechado.")

    # --- Exportação dos Resultados ---
    if resultados:
        print(f"\n💾 Exportando {len(resultados)} resultados...")
        exportar_resultados(resultados, data_inicial, data_final)
        logging.info(f"Exportando {len(resultados)} resultados.")
    else:
        print("\n⚠️ Nenhum HC encontrado ou processado com sucesso. Nada para exportar.")
        logging.info("Nenhum resultado para exportar.")

# --- Execução Principal ---
if __name__ == "__main__":
    # Define as datas (usando ONTEM como padrão se nenhum argumento for passado)
    if len(sys.argv) == 3:
        data_ini, data_fim = sys.argv[1], sys.argv[2]
    elif len(sys.argv) == 2:
        data_ini = data_fim = sys.argv[1]
    else:
        # Certifique-se que ONTEM está definido corretamente em config.py
        # Exemplo: from datetime import date, timedelta; ONTEM = (date.today() - timedelta(days=1)).strftime('%d/%m/%Y')
        try:
            data_ini = data_fim = ONTEM
        except NameError:
            print("Erro: Variável ONTEM não definida em config.py. Use argumentos de data ou defina ONTEM.")
            sys.exit(1)
        except Exception as e_config:
            print(f"Erro ao usar data padrão de config.py: {e_config}")
            sys.exit(1)

    # Validação simples do formato da data (DD/MM/AAAA)
    import re
    date_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    if not date_pattern.match(data_ini) or not date_pattern.match(data_fim):
        print("Erro: Formato de data inválido. Use DD/MM/AAAA.")
        sys.exit(1)

    # Executa a função principal
    buscar_processos(data_ini, data_fim)
    print("\n🚀 Script concluído.")