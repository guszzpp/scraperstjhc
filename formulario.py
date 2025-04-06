# formulario.py
import time
import logging # Adicionar logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException # Importar explicitamente
from config import URL_PESQUISA, ORGAO_ORIGEM

def preencher_formulario(driver, wait, data_inicial, data_final):
    """
    Acessa a página de pesquisa do STJ e preenche os campos do formulário.
    """
    logging.info("Acessando URL de pesquisa...")
    driver.get(URL_PESQUISA)
    wait.until(EC.presence_of_element_located((By.ID, "idDataAutuacaoInicial")))
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
        # Scroll pode não ser necessário se o elemento for clicável, mas mantendo por segurança
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", secao_julgador)
        time.sleep(0.5) # Pequena pausa antes/depois de ações JS
        secao_julgador.click()
        time.sleep(0.5)
    except Exception as e:
         logging.error(f"Erro ao expandir seção órgão julgador: {e}")
         raise # Re-levanta a exceção para parar a execução

    # Campo de órgão de origem
    logging.info("Preenchendo órgão de origem...")
    try:
        campo_origem = wait.until(EC.visibility_of_element_located((By.ID, "idOrgaosOrigemCampoParaPesquisar")))
        campo_origem.clear()
        campo_origem.send_keys(ORGAO_ORIGEM)
        time.sleep(1) # Pausa para possível auto-complete ou validação
    except Exception as e:
         logging.error(f"Erro ao preencher campo órgão de origem: {e}")
         raise

    # Botão de pesquisar
    logging.info("Localizando e clicando no botão Pesquisar...")
    try:
        botao_pesquisar = wait.until(EC.element_to_be_clickable((By.ID, "idBotaoPesquisarFormularioExtendido")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_pesquisar)
        time.sleep(0.5)
        botao_pesquisar.click() # A linha que estava causando o timeout
        logging.info("Botão Pesquisar clicado. Aguardando carregamento dos resultados...")

        # **** ESPERA EXPLÍCITA APÓS O CLIQUE ****
        # Esperar por um indicador de que a pesquisa terminou (mensagem ou lista)
        # Usar um tempo maior aqui se necessário (ex: 30 ou 60 segundos)
        elemento_esperado = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, ".clsMensagemLinha, .clsListaProcessoFormatoVerticalLinha"
        )))
        logging.info(f"Carregamento pós-pesquisa detectado (elemento: {elemento_esperado.tag_name}).")
        # time.sleep(2) # Pausa adicional pode ser útil aqui também

    except TimeoutException as te:
         # Se o timeout ocorrer AQUI (na espera *após* o clique), é mais informativo
         logging.error(f"Timeout APÓS clicar em Pesquisar, esperando por resultados: {te}")
         raise
    except Exception as e:
        logging.error(f"Erro ao clicar em Pesquisar ou esperar resultados: {e}")
        raise

    # Removido o wait antigo que estava aqui, pois foi incorporado acima.
    logging.info("Preenchimento do formulário e espera pós-pesquisa concluídos.")