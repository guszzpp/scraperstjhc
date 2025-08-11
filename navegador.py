# navegador.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import subprocess
import logging
import os
import shutil

def iniciar_navegador():
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
            raise Exception("Chrome não está instalado ou não pode ser executado")

        chrome_version = subprocess.check_output([chrome_cmd, '--version'], stderr=subprocess.STDOUT)
        logging.info(f"Chrome instalado: {chrome_version.decode().strip()!r}")

    except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
        logging.error(f"Chrome não está instalado ou não pode ser executado: {e}")
        logging.info("Por favor, instale o Google Chrome antes de continuar.")
        raise

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    
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
