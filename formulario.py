# formulario.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
import logging
import time
import os
import sys

from config import URL_PESQUISA, ORGAO_ORIGEM

def aguardar_pos_challenge(driver, timeout=180):
    """
    Aguarda até que o título da página não contenha "Just a moment..." (case insensitive).
    Implementa estratégias adicionais para contornar proteções do Cloudflare.
    
    Args:
        driver: Instância do WebDriver
        timeout: Timeout em segundos (padrão 180 - aumentado de 90)
    
    Returns:
        bool: True se a página passou do desafio, False se o tempo estourar
    """
    logging.info(f"🔄 Aguardando resolução do desafio de carregamento (timeout: {timeout}s)...")
    
    start_time = time.time()
    check_interval = 5  # Verificar a cada 5 segundos
    
    # Estratégias adicionais para contornar Cloudflare
    strategies_applied = False
    
    while (time.time() - start_time) < timeout:
        try:
            current_title = driver.title
            current_url = driver.current_url
            logging.info(f"   Título atual: '{current_title}'")
            logging.info(f"   URL atual: {current_url}")
            
            # Verificar se o título contém "Just a moment..."
            if "just a moment" not in current_title.lower():
                elapsed_time = time.time() - start_time
                logging.info(f"✅ Desafio resolvido em {elapsed_time:.1f}s - Título: '{current_title}'")
                return True
            
            # Aplicar estratégias adicionais após 30 segundos se ainda não aplicadas
            if not strategies_applied and (time.time() - start_time) > 30:
                logging.info("🔧 Aplicando estratégias adicionais para contornar Cloudflare...")
                
                try:
                    # Estratégia 1: Recarregar a página
                    logging.info("   Estratégia 1: Recarregando página...")
                    driver.refresh()
                    time.sleep(10)
                    
                    # Estratégia 2: Tentar navegar para uma URL diferente e voltar
                    if "just a moment" in driver.title.lower():
                        logging.info("   Estratégia 2: Navegando para URL alternativa...")
                        driver.get("https://www.stj.jus.br")
                        time.sleep(5)
                        driver.get(URL_PESQUISA)
                        time.sleep(10)
                    
                    # Estratégia 3: Executar JavaScript para simular interação humana
                    if "just a moment" in driver.title.lower():
                        logging.info("   Estratégia 3: Executando JavaScript para simular interação...")
                        driver.execute_script("""
                            // Simular movimento do mouse
                            var event = new MouseEvent('mousemove', {
                                'view': window,
                                'bubbles': true,
                                'cancelable': true,
                                'clientX': Math.random() * window.innerWidth,
                                'clientY': Math.random() * window.innerHeight
                            });
                            document.dispatchEvent(event);
                            
                            // Simular scroll
                            window.scrollTo(0, Math.random() * 100);
                            
                            // Simular clique
                            var clickEvent = new MouseEvent('click', {
                                'view': window,
                                'bubbles': true,
                                'cancelable': true
                            });
                            document.body.dispatchEvent(clickEvent);
                        """)
                        time.sleep(5)
                    
                    strategies_applied = True
                    logging.info("✅ Estratégias adicionais aplicadas")
                    
                except Exception as e:
                    logging.warning(f"   Erro ao aplicar estratégias adicionais: {e}")
                    strategies_applied = True  # Marcar como aplicadas para não tentar novamente
            
            # Aguardar antes da próxima verificação
            time.sleep(check_interval)
            
        except Exception as e:
            logging.warning(f"   Erro ao verificar título: {e}")
            time.sleep(check_interval)
    
    # Timeout atingido
    elapsed_time = time.time() - start_time
    logging.error(f"❌ Timeout após {elapsed_time:.1f}s - Desafio de carregamento não resolvido")
    logging.error(f"   Título final: '{driver.title}'")
    logging.error(f"   URL final: {driver.current_url}")
    return False

def click_and_wait(driver, wait, botao_locator, resultado_locator, retries=3, delay=5):
    """
    Clica no botão e aguarda resultado com retentativas.
    """
    logging.info(f"click_and_wait: Iniciando com {retries} tentativas...")
    
    for i in range(retries):
        try:
            logging.info(f"click_and_wait: Tentativa {i+1}/{retries}")
            
            # Tentar clicar no botão
            botao = wait.until(EC.element_to_be_clickable(botao_locator))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao)
            time.sleep(0.5)
            
            # Tentar clicar de diferentes formas
            try:
                botao.click()
                logging.info("click_and_wait: Clique direto bem-sucedido")
            except ElementClickInterceptedException:
                logging.info("click_and_wait: Clique direto falhou, tentando JavaScript...")
                driver.execute_script("arguments[0].click();", botao)
                logging.info("click_and_wait: Clique JavaScript bem-sucedido")
            
            # Aguardar resultado
            logging.info("click_and_wait: Aguardando resultado...")
            resultado = wait.until(EC.any_of(
                EC.presence_of_element_located(resultado_locator),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".clsMensagemLinha")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".clsListaProcessoFormatoVerticalLinha")),
                EC.presence_of_element_located((By.ID, "idSpanClasseDescricao"))
            ))
            
            logging.info(f"click_and_wait: ✅ Resultado encontrado: {resultado.tag_name}")
            return True
            
        except TimeoutException as e:
            logging.warning(f"click_and_wait: Timeout na tentativa {i+1}: {e}")
            if i < retries - 1:
                logging.info(f"Aguardando {delay}s antes da próxima tentativa...")
                time.sleep(delay)
            else:
                logging.error(f"click_and_wait: Falha após {retries} tentativas por timeout.")
        except Exception as e:
            logging.warning(f"click_and_wait: Erro inesperado na tentativa {i+1}: {type(e).__name__} - {e}")
            if i < retries - 1:
                logging.info(f"Aguardando {delay}s antes da próxima tentativa...")
                time.sleep(delay)
            else:
                logging.error(f"click_and_wait: Falha após {retries} tentativas devido a erro inesperado.")

    logging.error(f"click_and_wait: Todas as tentativas falharam.")
    return False

def debug_page_state(driver, wait, step_name):
    """
    Função para debug do estado da página
    """
    try:
        logging.info(f"🔍 DEBUG [{step_name}]:")
        logging.info(f"   URL: {driver.current_url}")
        logging.info(f"   Título: {driver.title}")
        logging.info(f"   ReadyState: {driver.execute_script('return document.readyState')}")
        
        # Verificar se há iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        logging.info(f"   Iframes encontrados: {len(iframes)}")
        
        # Tentar encontrar elementos comuns
        common_elements = [
            "idDataAutuacaoInicial",
            "idDataAutuacaoFinal", 
            "idBotaoPesquisarFormularioExtendido",
            "idOrgaosOrigemCampoParaPesquisar"
        ]
        
        for element_id in common_elements:
            try:
                element = driver.find_element(By.ID, element_id)
                logging.info(f"   ✅ {element_id}: encontrado")
            except NoSuchElementException:
                logging.info(f"   ❌ {element_id}: não encontrado")
        
        # Capturar screenshot para debug
        screenshot_path = f"debug_{step_name}_{int(time.time())}.png"
        driver.save_screenshot(screenshot_path)
        logging.info(f"   📸 Screenshot salvo: {screenshot_path}")
        
    except Exception as e:
        logging.error(f"❌ Erro no debug: {e}")

def wait_for_page_load(driver, wait, max_attempts=5):
    """
    Função melhorada para aguardar carregamento da página
    """
    logging.info("🔄 Aguardando carregamento da página...")
    
    for attempt in range(max_attempts):
        try:
            logging.info(f"   Tentativa {attempt + 1}/{max_attempts}")
            
            # Estratégia 1: Elemento específico do formulário
            try:
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "idDataAutuacaoInicial")))
                logging.info("✅ Página carregada (estratégia 1 - elemento específico)")
                return True
            except TimeoutException:
                logging.info("   Estratégia 1 falhou")
            
            # Estratégia 2: ReadyState
            try:
                WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")
                logging.info("✅ Página carregada (estratégia 2 - readyState)")
                return True
            except TimeoutException:
                logging.info("   Estratégia 2 falhou")
            
            # Estratégia 3: Título da página
            try:
                WebDriverWait(driver, 15).until(lambda d: "STJ" in d.title or "processo" in d.title.lower())
                logging.info("✅ Página carregada (estratégia 3 - título)")
                return True
            except TimeoutException:
                logging.info("   Estratégia 3 falhou")
            
            # Estratégia 4: Qualquer elemento de formulário
            try:
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "form")))
                logging.info("✅ Página carregada (estratégia 4 - formulário)")
                return True
            except TimeoutException:
                logging.info("   Estratégia 4 falhou")
            
            # Estratégia 5: Aguardar um pouco mais e tentar novamente
            if attempt < max_attempts - 1:
                logging.info(f"   Aguardando 5s antes da próxima tentativa...")
                time.sleep(5)
                
        except Exception as e:
            logging.error(f"   Erro na tentativa {attempt + 1}: {e}")
            if attempt < max_attempts - 1:
                time.sleep(5)
    
    logging.error("❌ Falha ao carregar página após múltiplas tentativas")
    debug_page_state(driver, wait, "page_load_failed")
    return False

def preencher_formulario(driver, wait, data_inicial, data_final):
    """
    Acessa a página de pesquisa do STJ e preenche os campos do formulário.
    """
    logging.info("🌐 Tentando acessar site do STJ...")
    
    # Tentar múltiplas estratégias de acesso
    if not tentar_acesso_multiplo(driver, wait, max_tentativas=3):
        logging.error("❌ Falha em todas as tentativas de acesso ao site")
        sys.exit(1)
    
    # Aguardar página carregar completamente
    if not wait_for_page_load(driver, wait):
        raise TimeoutException("Página não carregou no tempo esperado")
    
    # Debug do estado inicial da página
    debug_page_state(driver, wait, "after_page_load")
    
    logging.info("📝 Página carregada. Preenchendo datas...")

    # Tentar diferentes estratégias para encontrar os campos de data
    data_inicial_found = False
    data_final_found = False
    
    # Estratégia 1: IDs originais com timeout maior
    try:
        logging.info("🔍 Tentando encontrar campo data inicial (ID original)...")
        campo_data_inicial = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, "idDataAutuacaoInicial")))
        campo_data_inicial.clear()
        campo_data_inicial.send_keys(data_inicial)
        data_inicial_found = True
        logging.info("✅ Campo data inicial preenchido (ID original)")
    except TimeoutException:
        logging.warning("❌ Campo data inicial não encontrado com ID original")
    
    try:
        logging.info("🔍 Tentando encontrar campo data final (ID original)...")
        campo_data_final = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, "idDataAutuacaoFinal")))
        campo_data_final.clear()
        campo_data_final.send_keys(data_final)
        data_final_found = True
        logging.info("✅ Campo data final preenchido (ID original)")
    except TimeoutException:
        logging.warning("❌ Campo data final não encontrado com ID original")
    
    # Estratégia 2: Buscar por campos de input com placeholder ou name relacionados a data
    if not data_inicial_found or not data_final_found:
        logging.info("🔍 Tentando estratégia alternativa para campos de data...")
        try:
            # Aguardar um pouco mais para garantir que a página carregou completamente
            time.sleep(3)
            
            # Buscar por inputs que contenham "data" no placeholder ou name
            data_inputs = driver.find_elements(By.CSS_SELECTOR, "input[placeholder*='data'], input[name*='data'], input[id*='data']")
            logging.info(f"   Encontrados {len(data_inputs)} campos de input relacionados a data")
            
            for i, input_field in enumerate(data_inputs):
                try:
                    input_field.clear()
                    if i == 0 and not data_inicial_found:
                        input_field.send_keys(data_inicial)
                        data_inicial_found = True
                        logging.info(f"✅ Campo data inicial preenchido (estratégia alternativa - campo {i+1})")
                    elif i == 1 and not data_final_found:
                        input_field.send_keys(data_final)
                        data_final_found = True
                        logging.info(f"✅ Campo data final preenchido (estratégia alternativa - campo {i+1})")
                except Exception as e:
                    logging.warning(f"   Erro ao preencher campo {i+1}: {e}")
        except Exception as e:
            logging.error(f"❌ Erro na estratégia alternativa: {e}")
    
    # Estratégia 3: Buscar por name específicos
    if not data_inicial_found or not data_final_found:
        logging.info("🔍 Tentando estratégia por name específicos...")
        try:
            # Buscar por name específicos
            if not data_inicial_found:
                try:
                    campo_data_inicial = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.NAME, "dataAutuacaoInicial")))
                    campo_data_inicial.clear()
                    campo_data_inicial.send_keys(data_inicial)
                    data_inicial_found = True
                    logging.info("✅ Campo data inicial preenchido (por name)")
                except TimeoutException:
                    logging.warning("❌ Campo data inicial não encontrado por name")
            
            if not data_final_found:
                try:
                    campo_data_final = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.NAME, "dataAutuacaoFinal")))
                    campo_data_final.clear()
                    campo_data_final.send_keys(data_final)
                    data_final_found = True
                    logging.info("✅ Campo data final preenchido (por name)")
                except TimeoutException:
                    logging.warning("❌ Campo data final não encontrado por name")
        except Exception as e:
            logging.error(f"❌ Erro na estratégia por name: {e}")
    
    if not data_inicial_found or not data_final_found:
        logging.error("❌ Não foi possível encontrar e preencher os campos de data")
        debug_page_state(driver, wait, "data_fields_not_found")
        raise TimeoutException("Campos de data não encontrados")
    
    logging.info("✅ Datas preenchidas com sucesso.")

    # Expandir seção do órgão julgador
    logging.info("🔽 Expandindo seção do órgão de origem...")
    try:
        # Tentar diferentes seletores para a seção
        secao_selectors = [
            (By.ID, "idJulgadorOrigemTipoBlocoLabel"),
            (By.CSS_SELECTOR, "[id*='julgador'][id*='origem']"),
            (By.CSS_SELECTOR, "[id*='Julgador'][id*='Origem']"),
            (By.XPATH, "//*[contains(@id, 'julgador') and contains(@id, 'origem')]")
        ]
        
        secao_julgador = None
        for selector in secao_selectors:
            try:
                secao_julgador = wait.until(EC.element_to_be_clickable(selector))
                logging.info(f"✅ Seção encontrada com seletor: {selector}")
                break
            except TimeoutException:
                continue
        
        if secao_julgador:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", secao_julgador)
            time.sleep(0.5)
            secao_julgador.click()
            time.sleep(0.5)
            logging.info("✅ Seção do órgão julgador expandida")
        else:
            logging.warning("⚠️ Seção do órgão julgador não encontrada, continuando...")
            
    except Exception as e:
        logging.warning(f"⚠️ Erro ao expandir seção órgão julgador: {e}")

    # Campo de órgão de origem
    logging.info("🏛️ Preenchendo órgão de origem...")
    try:
        # Tentar diferentes seletores para o campo de origem
        origem_selectors = [
            (By.ID, "idOrgaosOrigemCampoParaPesquisar"),
            (By.CSS_SELECTOR, "input[id*='orgao'][id*='origem']"),
            (By.CSS_SELECTOR, "input[id*='Orgao'][id*='Origem']"),
            (By.XPATH, "//input[contains(@id, 'orgao') and contains(@id, 'origem')]")
        ]
        
        campo_origem = None
        for selector in origem_selectors:
            try:
                campo_origem = wait.until(EC.visibility_of_element_located(selector))
                logging.info(f"✅ Campo origem encontrado com seletor: {selector}")
                break
            except TimeoutException:
                continue
        
        if campo_origem:
            campo_origem.clear()
            campo_origem.send_keys(ORGAO_ORIGEM)
            time.sleep(1)
            logging.info("✅ Campo órgão de origem preenchido")
        else:
            logging.error("❌ Campo órgão de origem não encontrado")
            debug_page_state(driver, wait, "origem_field_not_found")
            raise TimeoutException("Campo órgão de origem não encontrado")
            
    except Exception as e:
        logging.error(f"❌ Erro ao preencher campo órgão de origem: {e}")
        raise

    # Definição dos localizadores para botão e resultados esperados
    botao_pesquisar_locator = (By.ID, "idBotaoPesquisarFormularioExtendido")
    # Espera por MENSAGEM, LISTA ou DETALHES (pelo ID do span da classe)
    resultado_locator = (By.CSS_SELECTOR, ".clsMensagemLinha, .clsListaProcessoFormatoVerticalLinha, #idSpanClasseDescricao")

    logging.info("🔍 Tentando clicar em 'Pesquisar' e aguardar resultados com retentativas...")
    # Chama a função de clique com retentativas
    if not click_and_wait(driver, wait, botao_pesquisar_locator, resultado_locator, retries=3, delay=5):
        # Se a função retornar False (falhou após retentativas), levanta uma exceção
        logging.error("❌ Falha crítica ao clicar em pesquisar e aguardar resultados após múltiplas tentativas.")
        debug_page_state(driver, wait, "search_button_failed")
        raise TimeoutException("Falha ao clicar em Pesquisar e obter resultados após múltiplas tentativas.")

    logging.info("✅ Preenchimento do formulário e espera pós-pesquisa concluídos.")

def tentar_acesso_multiplo(driver, wait, max_tentativas=3):
    """
    Tenta acessar o site do STJ usando múltiplas estratégias para contornar proteções.
    
    Args:
        driver: Instância do WebDriver
        wait: Instância do WebDriverWait
        max_tentativas: Número máximo de tentativas
    
    Returns:
        bool: True se conseguiu acessar, False caso contrário
    """
    urls_alternativas = [
        URL_PESQUISA,
        "https://www.stj.jus.br",
        "https://processo.stj.jus.br",
        "https://processo.stj.jus.br/processo/",
        "https://processo.stj.jus.br/processo/pesquisa/"
    ]
    
    for tentativa in range(max_tentativas):
        logging.info(f"🔄 Tentativa {tentativa + 1}/{max_tentativas} de acesso ao site...")
        
        for i, url in enumerate(urls_alternativas):
            try:
                logging.info(f"   Tentando URL {i + 1}/{len(urls_alternativas)}: {url}")
                driver.get(url)
                
                # Aguardar carregamento inicial
                time.sleep(5)
                
                # Verificar se passou do Cloudflare
                if aguardar_pos_challenge(driver, timeout=120):
                    logging.info(f"✅ Acesso bem-sucedido via {url}")
                    
                    # Se não estamos na URL de pesquisa, navegar para ela
                    if url != URL_PESQUISA:
                        logging.info("   Navegando para URL de pesquisa...")
                        driver.get(URL_PESQUISA)
                        time.sleep(3)
                        
                        if aguardar_pos_challenge(driver, timeout=60):
                            logging.info("✅ Navegação para pesquisa bem-sucedida")
                            return True
                        else:
                            logging.warning("❌ Falha na navegação para pesquisa")
                            continue
                    else:
                        return True
                
                else:
                    logging.warning(f"❌ Falha no acesso via {url}")
                    
            except Exception as e:
                logging.warning(f"   Erro ao acessar {url}: {e}")
                continue
        
        # Se chegou aqui, todas as URLs falharam nesta tentativa
        if tentativa < max_tentativas - 1:
            logging.info(f"   Aguardando 30s antes da próxima tentativa...")
            time.sleep(30)
    
    logging.error("❌ Todas as tentativas de acesso falharam")
    return False
