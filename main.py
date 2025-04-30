import sys
import logging
import pandas as pd
from datetime import datetime
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from navegador import iniciar_navegador
from extrator import extrair_detalhes_processo
from exportador import exportar_resultados  # Usando a versão melhorada
from paginador import navegar_paginas_e_extrair
from formulario import preencher_formulario
from config import ORGAO_ORIGEM, URL_PESQUISA
from retroativos.integrador import obter_retroativos
from retroativos.gerenciador_arquivos import salvar_csv_resultado
from email_detalhado import preparar_email_relatorio_diario
from pathlib import Path

# Configurar logging com formato colorido e data/hora
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def main(data_referencia: str):
    erros = []
    inicio = datetime.now()
    
    try:
        logging.info("🚀 Iniciando scraper de HCs STJ (Origem TJGO)")
        logging.info(f"📅 Data de referência: {data_referencia}")
        logging.info(f"🏛️ Órgão de origem: {ORGAO_ORIGEM}")
        
        # Criar pasta de dados se não existir
        Path("dados_diarios").mkdir(exist_ok=True)

        # Iniciar navegador e configurar wait
        logging.info("🌐 Iniciando navegador...")
        navegador = iniciar_navegador()
        wait = WebDriverWait(navegador, 30)  # Timeout de 30 segundos

        try:
            # Preencher formulário com data de referência
            logging.info("📝 Preenchendo formulário de pesquisa...")
            preencher_formulario(navegador, wait, data_referencia, data_referencia)
            
            # Obter resultados
            logging.info("🔍 Navegando pelas páginas e extraindo dados...")
            resultados, paginas_info = navegar_paginas_e_extrair(
                navegador, 
                wait, 
                extrair_detalhes_processo, 
                data_referencia
            )
            
            # Log de informações sobre páginas
            for info in paginas_info:
                logging.info(info)
                
            # Exportar para Excel
            logging.info("💾 Exportando resultados para Excel...")
            caminho_excel = exportar_resultados(resultados, data_referencia, data_referencia)
            
            if resultados:
                logging.info(f"✅ {len(resultados)} HCs encontrados e exportados com sucesso.")
                
                # Preparar dados para CSV (mantido para compatibilidade com sistema de retroativos)
                df = pd.DataFrame(resultados)
                caminho_csv = salvar_csv_resultado(df, data_referencia)
                logging.info(f"💾 Dados salvos no formato CSV em: {caminho_csv}")
                
                # Mensagem de status para o e-mail
                mensagem_status = f"Foram encontrados {len(resultados)} Habeas Corpus no STJ com origem no TJGO para a data {data_referencia}."
            else:
                logging.info("ℹ️ Nenhum HC encontrado para a data de referência.")
                mensagem_status = f"Nenhum Habeas Corpus foi encontrado no STJ com origem no TJGO para a data {data_referencia}."
                
        except Exception as e:
            logging.error(f"❌ Erro durante a execução do scraper: {e}", exc_info=True)
            erros.append(f"Erro na execução: {str(e)}")
            caminho_excel = None
            mensagem_status = f"Ocorreu um erro durante a execução do scraper: {str(e)}"
        finally:
            # Fechar navegador
            try:
                navegador.quit()
                logging.info("🔒 Navegador encerrado.")
            except Exception as e:
                logging.error(f"❌ Erro ao fechar navegador: {e}")
                erros.append(f"Erro ao fechar navegador: {str(e)}")
        
        # Calcular tempo de execução
        fim = datetime.now()
        duracao = fim - inicio
        logging.info(f"⏱️ Tempo de execução: {duracao}")
        
        # Preparar e-mail de status
        logging.info("📧 Preparando e-mail de status...")
        preparar_email_relatorio_diario(
            data_busca=data_referencia,
            caminho_arquivo=caminho_excel,
            mensagem_status=mensagem_status,
            erros=erros if erros else None
        )
        
        logging.info("✅ Scraper concluído com sucesso.")
        
    except Exception as e:
        logging.error(f"❌ Erro crítico: {e}", exc_info=True)
        erros.append(f"Erro crítico: {str(e)}")
        
        # Mesmo em caso de erro crítico, tenta preparar o e-mail
        try:
            preparar_email_relatorio_diario(
                data_busca=data_referencia,
                caminho_arquivo=None,
                mensagem_status="Ocorreu um erro crítico durante a execução do scraper.",
                erros=erros
            )
        except Exception as email_error:
            logging.error(f"❌ Não foi possível preparar o e-mail de erro: {email_error}")

    # Retornar código de saída baseado na presença de erros
    return 1 if erros else 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("🚫 Erro: Data não informada")
        print("Uso: python main.py <data no formato DD/MM/AAAA>")
        sys.exit(1)
        
    codigo_saida = main(sys.argv[1])
    sys.exit(codigo_saida)