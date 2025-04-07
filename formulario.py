# formulario.py

import time # <<< ADICIONAR import time >>>
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException # <<< ADICIONAR WebDriverException >>>
from config import URL_PESQUISA, ORGAO_ORIGEM

# <<< ADIÇÃO: Definição da função click_and_wait >>>
# Function to attempt click and wait with retries
def click_and_wait(driver, wait, button_locator, result_locator, retries=3, delay=5):
    """
    Tenta clicar em um botão e esperar por um resultado, com N tentativas.
    Args:
        driver: Instância do WebDriver.
        wait: Instância do WebDriverWait (para espera do resultado).
        button_locator: Tupla (By, "valor") para localizar o botão.
        result_locator: Tupla (By, "valor") para localizar o elemento de resultado.
        retries: Número máximo de tentativas.
        delay: Tempo de espera entre tentativas (segundos).
    Returns:
        True se sucesso, False se falhar após todas as tentativas.
    """
    for i in range(retries):
        try:
            logging.info(f"click_and_wait: Tentativa {i+1}/{retries} de encontrar e clicar no botão ({button_locator})...")
            # Espera o botão ser clicável antes de tentar
            button_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(button_locator)
            )
            # Scroll pode ser útil aqui também
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button_element)
            time.sleep(0.5) # Pequena pausa antes do clique

            button_element.click()
            logging.info("click_and_wait: Botão clicado. Aguardando carregamento dos resultados...")

            # Espera principal pelo resultado (usa o 'wait' principal passado para a função)
            wait.until(EC.presence_of_element_located(result_locator))
            logging.info(f"click_and_wait: Elemento de resultado ({result_locator}) encontrado com sucesso.")
            return True # Sucesso!

        except WebDriverException as e: # Captura erros mais específicos do Selenium/WebDriver
            logging.warning(f"click_and_wait: Erro de WebDriver na tentativa {i+1}: {type(e).__name__} - {e}")
            if i < retries - 1:
                 logging.info(f"Aguardando {delay}s antes da próxima tentativa...")
                 time.sleep(delay)
            else:
                 logging.error(f"click_and_wait: Falha após {retries} tentativas devido a erro de WebDriver.")
        except TimeoutException as e: # Captura Timeouts específicos
             logging.warning(f"click_and_wait: Timeout na tentativa {i+1} ao esperar pelo resultado: {e}")
             if i < retries - 1:
                  logging.info(f"Aguardando {delay}s antes da próxima tentativa...")
                  time.sleep(delay)
             else:
                  logging.error(f"click_and_wait: Falha após {retries} tentativas devido a Timeout.")
        except Exception as e: # Captura outros erros inesperados
            logging.warning(f"click_and_wait: Erro inesperado na tentativa {i+1}: {type(e).__name__} - {e}")
            if i < retries - 1:
                logging.info(f"Aguardando {delay}s antes da próxima tentativa...")
                time.sleep(delay)
            else:
                logging.error(f"click_and_wait: Falha após {retries} tentativas devido a erro inesperado.")

    logging.error("click_and_wait: Todas as tentativas falharam.")
    return False # Falhou após todas as tentativas


def preencher_formulario(driver, wait, data_inicial, data_final):
    """
    Acessa a página de pesquisa do STJ e preenche os campos do formulário.
    """
    logging.info("Acessando URL de pesquisa...")
    driver.get(URL_PESQUISA)
    # Usar um wait mais curto para o primeiro elemento, a página deve carregar rápido
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "idDataAutuacaoInicial")))
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

    # <<< ALTERAÇÃO: Substituir o bloco de clique e espera pelo botão Pesquisar >>>

    # Defina os localizadores corretos aqui
    # Localizador do botão "Pesquisar" que você já usava
    botao_pesquisar_locator = (By.ID, "idBotaoPesquisarFormularioExtendido")
    # Localizador do elemento de resultado que você já usava
    resultado_locator = (By.CSS_SELECTOR, ".clsMensagemLinha, .clsListaProcessoFormatoVerticalLinha")

    logging.info("Tentando clicar em 'Pesquisar' e aguardar resultados com retentativas...")
    # Chama a função de clique com retentativas
    # Passa o 'wait' principal para que ele use o timeout configurado em main.py
    if not click_and_wait(driver, wait, botao_pesquisar_locator, resultado_locator, retries=3, delay=5):
        # Se a função retornar False (falhou após retentativas), levanta uma exceção
        logging.error("Falha crítica ao clicar em pesquisar e aguardar resultados após múltiplas tentativas.")
        # Levanta TimeoutException para ser tratado como erro crítico no main.py
        raise TimeoutException("Falha ao clicar em Pesquisar e obter resultados após múltiplas tentativas.")

    # <<< FIM DA ALTERAÇÃO >>>

    # O código não precisa mais da espera explícita aqui, pois click_and_wait já fez isso.
    # Removido o wait antigo que estava aqui.

    logging.info("Preenchimento do formulário e espera pós-pesquisa concluídos.")
