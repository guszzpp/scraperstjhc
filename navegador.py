# navegador.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import subprocess
import logging
import os
import shutil

def iniciar_navegador(headless=True):
    """
    Inicia o navegador Chrome com configurações otimizadas.
    
    Args:
        headless: Se True, executa em modo headless. Se False, executa em modo headful.
    """
    logging.info("Verificando ambiente para inicialização do Chrome...")
    
    try:
        # procura o binário certo: primeiro google-chrome (Ubuntu/Actions), senão chrome.exe (Win)
        chrome_cmd = (
            shutil.which('google-chrome') or
            shutil.which('chrome') or
            shutil.which('chrome.exe')
        )
        if not chrome_cmd:
            logging.error("Chrome não encontrado no PATH.")
            # Tentar instalar Chrome automaticamente no Linux
            if os.name == 'posix':
                logging.info("Tentando instalar Chrome automaticamente...")
                try:
                    subprocess.run(['sudo', 'apt-get', 'update'], check=True)
                    subprocess.run(['sudo', 'apt-get', 'install', '-y', 'wget', 'gnupg2'], check=True)
                    subprocess.run(['wget', '-q', '-O', '-', 'https://dl.google.com/linux/linux_signing_key.pub'], 
                                 stdout=subprocess.PIPE, check=True)
                    subprocess.run(['sudo', 'apt-key', 'add', '-'], input=subprocess.run(
                        ['wget', '-q', '-O', '-', 'https://dl.google.com/linux/linux_signing_key.pub'], 
                        capture_output=True, text=True, check=True).stdout.encode(), check=True)
                    subprocess.run(['echo', 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main'], 
                                 stdout=open('/etc/apt/sources.list.d/google-chrome.list', 'w'), check=True)
                    subprocess.run(['sudo', 'apt-get', 'update'], check=True)
                    subprocess.run(['sudo', 'apt-get', 'install', '-y', 'google-chrome-stable'], check=True)
                    chrome_cmd = shutil.which('google-chrome')
                    if chrome_cmd:
                        logging.info("Chrome instalado com sucesso!")
                    else:
                        raise Exception("Falha na instalação automática do Chrome")
                except Exception as install_error:
                    logging.error(f"Erro na instalação automática: {install_error}")
                    raise Exception("Chrome não está instalado ou não pode ser executado")
            else:
                raise Exception("Chrome não está instalado ou não pode ser executado")

        chrome_version = subprocess.check_output([chrome_cmd, '--version'], stderr=subprocess.STDOUT)
        logging.info(f"Chrome instalado: {chrome_version.decode().strip()!r}")

    except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
        logging.error(f"Chrome não está instalado ou não pode ser executado: {e}")
        logging.info("Por favor, instale o Google Chrome antes de continuar.")
        raise

    options = Options()
    
    # Configurar modo headless/headful
    if headless:
        options.add_argument("--headless")
        logging.info("🔧 Modo headless ativado")
    else:
        logging.info("🔧 Modo headful ativado")
    
    # Opções básicas
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--window-size=1920,1080")
    
    # User agent mais realista para contornar Cloudflare
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")
    
    # Opções adicionais para contornar detecção de bot
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Opções adicionais para GitHub Actions
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-sync")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-component-extensions-with-background-pages")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-hang-monitor")
    options.add_argument("--disable-prompt-on-repost")
    options.add_argument("--disable-domain-reliability")
    options.add_argument("--disable-component-update")
    options.add_argument("--disable-features=AudioServiceOutOfProcess")
    options.add_argument("--force-color-profile=srgb")
    options.add_argument("--metrics-recording-only")
    
    # Opções adicionais para evitar detecção de bot
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-images")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-java")
    options.add_argument("--disable-flash")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-save-password-bubble")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-sync")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-component-extensions-with-background-pages")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-hang-monitor")
    options.add_argument("--disable-prompt-on-repost")
    options.add_argument("--disable-domain-reliability")
    options.add_argument("--disable-component-update")
    options.add_argument("--disable-features=AudioServiceOutOfProcess")
    
    # Opções específicas para Cloudflare
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-features=VizDisplayCompositor")
    
    # User-Agent mais realista
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        service = Service(ChromeDriverManager().install())
        logging.info(f"ChromeDriver instalado em: {service.path}")
        
        if os.path.exists(service.path):
            is_exec = os.access(service.path, os.X_OK)
            logging.info(f"ChromeDriver executável: {is_exec}")
            if not is_exec:
                os.chmod(service.path, 0o755)
                logging.info("Permissão de execução adicionada ao ChromeDriver")
        
        driver = webdriver.Chrome(service=service, options=options)
        
        # Executar scripts para remover propriedades de automação e contornar Cloudflare
        driver.execute_script("""
            // Remover propriedades que indicam automação
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en']});
            
            // Simular propriedades de navegador real
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
            Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'});
            
            // Remover propriedades de automação do Chrome
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """)
        
        logging.info("Navegador Chrome iniciado com sucesso!")
        return driver

    except Exception as e:
        logging.error(f"Erro ao iniciar o ChromeDriver ou abrir o navegador: {e}")
        # Se quiser diagnosticar dependências no Linux:
        try:
            ldd_out = subprocess.check_output(['ldd', service.path], stderr=subprocess.STDOUT).decode()
            logging.error(f"Dependências do ChromeDriver:\n{ldd_out}")
        except Exception:
            logging.error("Não foi possível verificar as dependências do ChromeDriver")
        raise
