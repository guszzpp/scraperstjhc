#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar melhorias contra Cloudflare
"""

import logging
import time
from selenium.webdriver.support.ui import WebDriverWait
from navegador import iniciar_navegador
from formulario import tentar_acesso_multiplo, aguardar_pos_challenge

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def testar_acesso_stj():
    """
    Testa o acesso ao site do STJ com as novas melhorias
    """
    logging.info("🧪 Iniciando teste de acesso ao STJ...")
    
    try:
        # Iniciar navegador em modo headful para debug
        logging.info("🔧 Iniciando navegador...")
        driver = iniciar_navegador(headless=False)  # Modo headful para debug
        wait = WebDriverWait(driver, 30)
        
        # Testar função de acesso múltiplo
        logging.info("🌐 Testando função de acesso múltiplo...")
        sucesso = tentar_acesso_multiplo(driver, wait, max_tentativas=2)
        
        if sucesso:
            logging.info("✅ Teste de acesso bem-sucedido!")
            
            # Aguardar um pouco para verificar se a página está funcionando
            time.sleep(10)
            
            # Verificar se conseguimos interagir com a página
            try:
                titulo = driver.title
                url_atual = driver.current_url
                logging.info(f"📄 Título da página: {titulo}")
                logging.info(f"🔗 URL atual: {url_atual}")
                
                # Tentar encontrar elementos básicos da página
                elementos = driver.find_elements("tag name", "input")
                logging.info(f"📝 Encontrados {len(elementos)} campos de input")
                
                if len(elementos) > 0:
                    logging.info("✅ Página carregada e interativa!")
                else:
                    logging.warning("⚠️ Página carregada mas sem elementos de input encontrados")
                    
            except Exception as e:
                logging.error(f"❌ Erro ao verificar elementos da página: {e}")
        else:
            logging.error("❌ Teste de acesso falhou")
            
    except Exception as e:
        logging.error(f"❌ Erro durante o teste: {e}")
        
    finally:
        try:
            if 'driver' in locals():
                logging.info("🔒 Encerrando navegador...")
                driver.quit()
        except Exception as e:
            logging.error(f"❌ Erro ao encerrar navegador: {e}")

if __name__ == "__main__":
    testar_acesso_stj()
