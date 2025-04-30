# navegador.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import subprocess
import logging
import os

def iniciar_navegador():
    # Verificar o ambiente
    logging.info("Verificando ambiente para inicialização do Chrome...")
    
    try:
        # Verificar se o Chrome está instalado
        chrome_version = subprocess.check_output(['google-chrome', '--version'], stderr=subprocess.STDOUT).decode('utf-8').strip()
        logging.info(f"Chrome instalado: {chrome_version}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.error(f"Chrome não está instalado ou não pode ser executado: {str(e)}")
        logging.info("Por favor, instale o Google Chrome antes de continuar.")
        raise Exception("Chrome não está instalado ou não pode ser executado")
    
    options = Options()
    options.add_argument("--headless=new")  # Modo headless
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    
    # Adicionar mais argumentos para diagnóstico
    options.add_argument("--disable-gpu")  # Desativar aceleração de GPU
    options.add_argument("--disable-extensions")  # Desativar extensões
    
    try:
        service = Service(ChromeDriverManager().install())
        logging.info(f"ChromeDriver instalado em: {service.path}")
        
        # Verificar permissões do ChromeDriver
        if os.path.exists(service.path):
            is_executable = os.access(service.path, os.X_OK)
            logging.info(f"ChromeDriver tem permissão de execução: {is_executable}")
            if not is_executable:
                os.chmod(service.path, 0o755)  # Dar permissão de execução
                logging.info("Permissão de execução adicionada ao ChromeDriver")
        
        driver = webdriver.Chrome(
            service=service,
            options=options
        )
        logging.info("Navegador Chrome iniciado com sucesso!")
        return driver
    except Exception as e:
        logging.error(f"Erro ao iniciar o Chrome: {str(e)}")
        # Tentar identificar melhor o erro
        try:
            ldd_output = subprocess.check_output(['ldd', service.path], stderr=subprocess.STDOUT).decode('utf-8')
            logging.error(f"Dependências do ChromeDriver: {ldd_output}")
        except:
            logging.error("Não foi possível verificar as dependências do ChromeDriver")
        raise