#!/usr/bin/env python3
"""
Script de teste simples para verificar se a página do STJ carrega corretamente
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_stj_page():
    """
    Testa se a página do STJ carrega e se os elementos do formulário estão presentes
    """
    logging.info("🚀 Iniciando teste da página do STJ")
    
    # Configurar Chrome
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
    
    # Opções para evitar detecção de bot
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        # Iniciar navegador
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 30)
        
        logging.info("✅ Navegador iniciado com sucesso")
        
        # Acessar página
        url = "https://processo.stj.jus.br/processo/pesquisa/?aplicacao=processos.ea"
        logging.info(f"🌐 Acessando: {url}")
        driver.get(url)
        
        # Aguardar carregamento
        logging.info("⏳ Aguardando carregamento da página...")
        time.sleep(5)
        
        # Verificar informações básicas
        logging.info(f"📄 Título da página: {driver.title}")
        logging.info(f"🌐 URL atual: {driver.current_url}")
        logging.info(f"📊 ReadyState: {driver.execute_script('return document.readyState')}")
        
        # Verificar se há iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        logging.info(f"🖼️ Iframes encontrados: {len(iframes)}")
        
        # Tentar encontrar elementos do formulário
        elementos_teste = [
            "idDataAutuacaoInicial",
            "idDataAutuacaoFinal",
            "idBotaoPesquisarFormularioExtendido",
            "idOrgaosOrigemCampoParaPesquisar"
        ]
        
        logging.info("🔍 Verificando elementos do formulário...")
        for elemento_id in elementos_teste:
            try:
                elemento = driver.find_element(By.ID, elemento_id)
                logging.info(f"✅ {elemento_id}: ENCONTRADO")
                logging.info(f"   - Visível: {elemento.is_displayed()}")
                logging.info(f"   - Habilitado: {elemento.is_enabled()}")
                logging.info(f"   - Tag: {elemento.tag_name}")
                logging.info(f"   - Type: {elemento.get_attribute('type')}")
                logging.info(f"   - Name: {elemento.get_attribute('name')}")
            except NoSuchElementException:
                logging.error(f"❌ {elemento_id}: NÃO ENCONTRADO")
        
        # Tentar encontrar por name
        logging.info("🔍 Verificando elementos por name...")
        names_teste = ["dataAutuacaoInicial", "dataAutuacaoFinal"]
        for name in names_teste:
            try:
                elemento = driver.find_element(By.NAME, name)
                logging.info(f"✅ {name}: ENCONTRADO por name")
            except NoSuchElementException:
                logging.error(f"❌ {name}: NÃO ENCONTRADO por name")
        
        # Verificar se há formulários
        forms = driver.find_elements(By.TAG_NAME, "form")
        logging.info(f"📝 Formulários encontrados: {len(forms)}")
        
        # Verificar inputs
        inputs = driver.find_elements(By.TAG_NAME, "input")
        logging.info(f"⌨️ Inputs encontrados: {len(inputs)}")
        
        # Listar alguns inputs para debug
        for i, input_elem in enumerate(inputs[:10]):  # Primeiros 10 inputs
            try:
                input_id = input_elem.get_attribute('id')
                input_name = input_elem.get_attribute('name')
                input_type = input_elem.get_attribute('type')
                logging.info(f"   Input {i+1}: id='{input_id}', name='{input_name}', type='{input_type}'")
            except Exception as e:
                logging.error(f"   Erro ao verificar input {i+1}: {e}")
        
        # Capturar screenshot
        screenshot_path = f"teste_stj_{int(time.time())}.png"
        driver.save_screenshot(screenshot_path)
        logging.info(f"📸 Screenshot salvo: {screenshot_path}")
        
        # Tentar aguardar elemento específico
        logging.info("⏳ Tentando aguardar elemento idDataAutuacaoInicial...")
        try:
            elemento = wait.until(EC.visibility_of_element_located((By.ID, "idDataAutuacaoInicial")))
            logging.info("✅ Elemento idDataAutuacaoInicial encontrado e visível!")
        except TimeoutException:
            logging.error("❌ Timeout ao aguardar elemento idDataAutuacaoInicial")
        
        logging.info("✅ Teste concluído")
        
    except Exception as e:
        logging.error(f"❌ Erro durante o teste: {e}")
        raise
    finally:
        try:
            driver.quit()
            logging.info("🔒 Navegador fechado")
        except:
            pass

if __name__ == "__main__":
    test_stj_page()
