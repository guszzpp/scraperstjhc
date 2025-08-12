#!/usr/bin/env python3
"""
Script de teste local para verificar se a página do STJ carrega corretamente
Foca apenas na primeira parte: checagem da página e elementos do formulário
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

# Configurar logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('teste_local.log', encoding='utf-8')
    ]
)

def test_stj_page_local():
    """
    Testa se a página do STJ carrega e se os elementos do formulário estão presentes
    """
    logging.info("🚀 Iniciando teste local da página do STJ")
    
    # Configurar Chrome com opções mínimas
    options = Options()
    # options.add_argument("--headless")  # Comentado para ver o navegador
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Opções para evitar detecção de bot
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    try:
        # Iniciar navegador
        logging.info("🔧 Iniciando Chrome...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 30)
        
        logging.info("✅ Navegador iniciado com sucesso")
        
        # Acessar página
        url = "https://processo.stj.jus.br/processo/pesquisa/?aplicacao=processos.ea"
        logging.info(f"🌐 Acessando: {url}")
        driver.get(url)
        
        # Aguardar carregamento inicial
        logging.info("⏳ Aguardando carregamento inicial da página...")
        time.sleep(3)
        
        # Verificar informações básicas
        logging.info("📊 Informações básicas da página:")
        logging.info(f"   Título: {driver.title}")
        logging.info(f"   URL atual: {driver.current_url}")
        logging.info(f"   ReadyState: {driver.execute_script('return document.readyState')}")
        
        # Verificar se há iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        logging.info(f"🖼️ Iframes encontrados: {len(iframes)}")
        
        # Verificar se há formulários
        forms = driver.find_elements(By.TAG_NAME, "form")
        logging.info(f"📝 Formulários encontrados: {len(forms)}")
        
        # Verificar inputs
        inputs = driver.find_elements(By.TAG_NAME, "input")
        logging.info(f"⌨️ Inputs encontrados: {len(inputs)}")
        
        # Listar todos os inputs para debug
        logging.info("🔍 Listando todos os inputs encontrados:")
        for i, input_elem in enumerate(inputs):
            try:
                input_id = input_elem.get_attribute('id')
                input_name = input_elem.get_attribute('name')
                input_type = input_elem.get_attribute('type')
                input_placeholder = input_elem.get_attribute('placeholder')
                logging.info(f"   Input {i+1}: id='{input_id}', name='{input_name}', type='{input_type}', placeholder='{input_placeholder}'")
            except Exception as e:
                logging.error(f"   Erro ao verificar input {i+1}: {e}")
        
        # Tentar encontrar elementos específicos do formulário
        elementos_teste = [
            "idDataAutuacaoInicial",
            "idDataAutuacaoFinal",
            "idBotaoPesquisarFormularioExtendido",
            "idOrgaosOrigemCampoParaPesquisar"
        ]
        
        logging.info("🎯 Verificando elementos específicos do formulário:")
        elementos_encontrados = 0
        for elemento_id in elementos_teste:
            try:
                elemento = driver.find_element(By.ID, elemento_id)
                logging.info(f"✅ {elemento_id}: ENCONTRADO")
                logging.info(f"   - Visível: {elemento.is_displayed()}")
                logging.info(f"   - Habilitado: {elemento.is_enabled()}")
                logging.info(f"   - Tag: {elemento.tag_name}")
                logging.info(f"   - Type: {elemento.get_attribute('type')}")
                logging.info(f"   - Name: {elemento.get_attribute('name')}")
                elementos_encontrados += 1
            except NoSuchElementException:
                logging.error(f"❌ {elemento_id}: NÃO ENCONTRADO")
        
        # Tentar encontrar por name
        logging.info("🔍 Verificando elementos por name:")
        names_teste = ["dataAutuacaoInicial", "dataAutuacaoFinal"]
        for name in names_teste:
            try:
                elemento = driver.find_element(By.NAME, name)
                logging.info(f"✅ {name}: ENCONTRADO por name")
            except NoSuchElementException:
                logging.error(f"❌ {name}: NÃO ENCONTRADO por name")
        
        # Tentar aguardar elemento específico com timeout
        logging.info("⏳ Tentando aguardar elemento idDataAutuacaoInicial com timeout...")
        try:
            elemento = wait.until(EC.visibility_of_element_located((By.ID, "idDataAutuacaoInicial")))
            logging.info("✅ Elemento idDataAutuacaoInicial encontrado e visível!")
        except TimeoutException:
            logging.error("❌ Timeout ao aguardar elemento idDataAutuacaoInicial")
        
        # Capturar screenshot
        screenshot_path = f"teste_local_{int(time.time())}.png"
        driver.save_screenshot(screenshot_path)
        logging.info(f"📸 Screenshot salvo: {screenshot_path}")
        
        # Resumo do teste
        logging.info("📋 RESUMO DO TESTE:")
        logging.info(f"   - Elementos específicos encontrados: {elementos_encontrados}/{len(elementos_teste)}")
        logging.info(f"   - Formulários: {len(forms)}")
        logging.info(f"   - Inputs: {len(inputs)}")
        logging.info(f"   - Iframes: {len(iframes)}")
        
        if elementos_encontrados >= 2:  # Pelo menos os campos de data
            logging.info("✅ TESTE PASSOU - Elementos principais encontrados")
            return True
        else:
            logging.error("❌ TESTE FALHOU - Elementos principais não encontrados")
            return False
        
    except Exception as e:
        logging.error(f"❌ Erro durante o teste: {e}")
        return False
    finally:
        if driver:
            try:
                # Manter o navegador aberto por alguns segundos para inspeção
                logging.info("🔍 Mantendo navegador aberto por 10 segundos para inspeção...")
                time.sleep(10)
                driver.quit()
                logging.info("🔒 Navegador fechado")
            except:
                pass

if __name__ == "__main__":
    sucesso = test_stj_page_local()
    if sucesso:
        print("\n🎉 Teste concluído com SUCESSO!")
    else:
        print("\n💥 Teste concluído com FALHA!")
    
    print("\n📄 Log detalhado salvo em: teste_local.log")
    print("📸 Screenshot salvo para análise")
