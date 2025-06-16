# navegador.py

import undetected_chromedriver as uc
import logging
import os
import shutil
import subprocess

def iniciar_navegador():
    logging.info("Verificando ambiente para inicialização do Chrome...")
    try:
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

    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    try:
        driver = uc.Chrome(options=options)
        logging.info("Navegador Chrome (undetected) iniciado com sucesso!")
        return driver
    except Exception as e:
        logging.error(f"Erro ao iniciar o ChromeDriver ou abrir o navegador: {e}")
        raise
