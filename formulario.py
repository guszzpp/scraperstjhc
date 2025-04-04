# formulario.py

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from config import URL_PESQUISA, ORGAO_ORIGEM

def preencher_formulario(driver, wait, data_inicial, data_final):
    """
    Acessa a página de pesquisa do STJ e preenche os campos do formulário.
    """
    driver.get(URL_PESQUISA)
    wait.until(EC.presence_of_element_located((By.ID, "idDataAutuacaoInicial")))

    # Datas
    campo_data_inicial = wait.until(EC.visibility_of_element_located((By.ID, "idDataAutuacaoInicial")))
    campo_data_inicial.clear()
    campo_data_inicial.send_keys(data_inicial)

    campo_data_final = wait.until(EC.visibility_of_element_located((By.ID, "idDataAutuacaoFinal")))
    campo_data_final.clear()
    campo_data_final.send_keys(data_final)

    # Expandir seção do órgão julgador
    secao_julgador = wait.until(EC.element_to_be_clickable((By.ID, "idJulgadorOrigemTipoBlocoLabel")))
    driver.execute_script("arguments[0].scrollIntoView(true);", secao_julgador)
    time.sleep(0.5)
    secao_julgador.click()
    time.sleep(0.5)

    # Campo de órgão de origem
    campo_origem = wait.until(EC.visibility_of_element_located((By.ID, "idOrgaosOrigemCampoParaPesquisar")))
    campo_origem.clear()
    campo_origem.send_keys(ORGAO_ORIGEM)
    time.sleep(1)

    # Botão de pesquisar
    botao_pesquisar = wait.until(EC.element_to_be_clickable((By.ID, "idBotaoPesquisarFormularioExtendido")))
    driver.execute_script("arguments[0].scrollIntoView(true);", botao_pesquisar)
    time.sleep(0.5)
    botao_pesquisar.click()

    # Esperar o carregamento de alguma resposta (mensagem ou lista)
    wait.until(EC.presence_of_element_located((
        By.CSS_SELECTOR, ".clsMensagemLinha, .clsListaProcessoFormatoVerticalLinha"
    )))

    time.sleep(2)
