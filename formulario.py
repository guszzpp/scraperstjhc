# formulario.py

import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from config import URL_PESQUISA, ORGAO_ORIGEM

# Definição da função click_and_wait
def click_and_wait(driver, wait, button_locator, result_locator, retries=3, delay=5):
    """
    Tenta clicar em um botão e esperar por um resultado, com N tentativas.
    Args:
        driver: Instância do WebDriver.
        wait: Instância do WebDriverWait JÁ CONFIGURADA com o timeout desejado.
        button_locator: Tupla (By, "valor") para localizar o botão.
        result_locator: Tupla (By, "valor") para localizar o elemento de resultado.
        retries: Número máximo de tentativas.
        delay: Tempo de espera entre tentativas (segundos).
    Returns:
        True se sucesso, False se falhar após todas as tentativas.
    """
    last_exception = None # Guarda a última exceção para log
    for i in range(retries):
        try:
            logging.info(f"click_and_wait: Tentativa {i+1}/{retries} de encontrar e clicar no botão ({button_locator})...")
            # Espera o botão ser clicável antes de tentar (wait curto aqui)
            button_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(button_locator)
            )
            # Scroll pode ser útil aqui também
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button_element)
            time.sleep(0.5) # Pequena pausa antes do clique

            button_element.click()
            logging.info("click_and_wait: Botão clicado. Aguardando carregamento dos resultados...")

            # Usa o objeto 'wait' passado como argumento diretamente.
            wait.until(
                 EC.presence_of_element_located(result_locator)
            )

            logging.info(f"click_and_wait: Elemento de resultado ({result_locator}) encontrado com sucesso.")
            return True # Sucesso!

        except (WebDriverException, TimeoutException) as e: # Captura erros comuns do Selenium
            logging.warning(f"click_and_wait: Erro Selenium/Timeout na tentativa {i+1}: {type(e).__name__} - {e}")
            last_exception = e # Guarda a exceção
            if i < retries - 1:
                 logging.info(f"Aguardando {delay}s antes da próxima tentativa...")
                 time.sleep(delay)
            else:
                 logging.error(f"click_and_wait: Falha após {retries} tentativas devido a {type(e).__name__}.")
        except Exception as e: # Captura outros erros inesperados
            logging.warning(f"click_and_wait: Erro inesperado na tentativa {i+1}: {type(e).__name__} - {e}")
            last_exception = e # Guarda a exceção
            if i < retries - 1:
                logging.info(f"Aguardando {delay}s antes da próxima tentativa...")
                time.sleep(delay)
            else:
                logging.error(f"click_and_wait: Falha após {retries} tentativas devido a erro inesperado.")

    logging.error(f"click_and_wait: Todas as tentativas falharam. Último erro: {last_exception}")
    return False # Falhou após todas as tentativas


def preencher_formulario(driver, wait, data_inicial, data_final):
    """
    Acessa a página de pesquisa do STJ e preenche os campos do formulário.
    """
    logging.info("Acessando URL de pesquisa...")
    driver.get(URL_PESQUISA)
    
    # Aguardar página carregar completamente
    logging.info("Aguardando carregamento da página...")
    time.sleep(3)  # Pausa inicial para carregamento
    
    # Tentar múltiplas estratégias para detectar se a página carregou
    try:
        # Estratégia 1: Elemento principal do formulário
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "idDataAutuacaoInicial")))
        logging.info("✅ Página carregada (estratégia 1).")
    except TimeoutException:
        try:
            # Estratégia 2: Verificar se a página tem conteúdo
            WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")
            logging.info("✅ Página carregada (estratégia 2 - readyState).")
        except TimeoutException:
            try:
                # Estratégia 3: Verificar título da página
                WebDriverWait(driver, 10).until(lambda d: "STJ" in d.title)
                logging.info("✅ Página carregada (estratégia 3 - título).")
            except TimeoutException:
                logging.error("❌ Falha ao carregar página após múltiplas tentativas.")
                # Capturar screenshot para debug
                try:
                    screenshot_path = f"error_screenshot_{int(time.time())}.png"
                    driver.save_screenshot(screenshot_path)
                    logging.info(f"📸 Screenshot salvo: {screenshot_path}")
                    logging.info(f"📄 Título da página: {driver.title}")
                    logging.info(f"🌐 URL atual: {driver.current_url}")
                except Exception as e:
                    logging.error(f"❌ Erro ao capturar screenshot: {e}")
                raise TimeoutException("Página não carregou no tempo esperado")
    
    logging.info("Página carregada. Preenchendo datas...")

    # Datas
    campo_data_inicial = wait.until(EC.visibility_of_element_located((By.ID, "idDataAutuacaoInicial")))
    campo_data_inicial.clear()
    campo_data_inicial.send_keys(data_inicial)

    campo_data_final = wait.until(EC.visibility_of_element_located((By.ID, "idDataAutuacaoFinal")))
    campo_data_final.clear()
    campo_data_final.send_keys(data_final)
    logging.info("Datas preenchidas.")

    # Expandir seção do órgão julgador
    logging.info("Expandindo seção do órgão de origem...")
    try:
        secao_julgador = wait.until(EC.element_to_be_clickable((By.ID, "idJulgadorOrigemTipoBlocoLabel")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", secao_julgador)
        time.sleep(0.5)
        secao_julgador.click()
        time.sleep(0.5)
    except Exception as e:
         logging.error(f"Erro ao expandir seção órgão julgador: {e}")
         raise

    # Campo de órgão de origem
    logging.info("Preenchendo órgão de origem...")
    try:
        campo_origem = wait.until(EC.visibility_of_element_located((By.ID, "idOrgaosOrigemCampoParaPesquisar")))
        campo_origem.clear()
        campo_origem.send_keys(ORGAO_ORIGEM)
        time.sleep(1)
    except Exception as e:
         logging.error(f"Erro ao preencher campo órgão de origem: {e}")
         raise

    # Definição dos localizadores para botão e resultados esperados
    botao_pesquisar_locator = (By.ID, "idBotaoPesquisarFormularioExtendido")
    # Espera por MENSAGEM, LISTA ou DETALHES (pelo ID do span da classe)
    resultado_locator = (By.CSS_SELECTOR, ".clsMensagemLinha, .clsListaProcessoFormatoVerticalLinha, #idSpanClasseDescricao")

    logging.info("Tentando clicar em 'Pesquisar' e aguardar resultados com retentativas...")
    # Chama a função de clique com retentativas
    if not click_and_wait(driver, wait, botao_pesquisar_locator, resultado_locator, retries=3, delay=5):
        # Se a função retornar False (falhou após retentativas), levanta uma exceção
        logging.error("Falha crítica ao clicar em pesquisar e aguardar resultados após múltiplas tentativas.")
        raise TimeoutException("Falha ao clicar em Pesquisar e obter resultados após múltiplas tentativas.")

    logging.info("Preenchimento do formulário e espera pós-pesquisa concluídos.")
