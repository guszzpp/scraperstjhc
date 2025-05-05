# main.py

import sys
import logging
import os
import pandas as pd
from datetime import datetime
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from navegador import iniciar_navegador
from extrator import extrair_detalhes_processo
from exportador import exportar_resultados
from paginador import navegar_paginas_e_extrair
from formulario import preencher_formulario
from config import ORGAO_ORIGEM, URL_PESQUISA
from retroativos.integrador import obter_retroativos
from retroativos.gerenciador_arquivos import salvar_csv_resultado
from email_detalhado import preparar_email_relatorio_diario
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
import stat
import time

# ─── LOGGING ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ─── FUNÇÃO DE DEBUG TIPO `ls -la` ───────────────────────────────────
def listar_arquivos_com_detalhes(pasta):
    logging.info(f"📁 Conteúdo da pasta {pasta}:")
    try:
        if not os.path.exists(pasta):
            logging.error(f"❌ Pasta {pasta} não existe!")
            return
            
        for entry in os.scandir(pasta):
            info = entry.stat()
            permissao = stat.filemode(info.st_mode)
            tamanho = info.st_size
            modificado = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(info.st_mtime))
            logging.info(f"{permissao} {tamanho:>10} {modificado} {entry.name}")
    except Exception as e:
        logging.error(f"❌ Erro ao listar arquivos: {e}")

# ─── FUNÇÃO PRINCIPAL ────────────────────────────────────────────────
def main(data_referencia: str):
    erros = []
    inicio = datetime.now()

    try:
        logging.info("🚀 Iniciando scraper de HCs STJ (Origem TJGO)")
        logging.info(f"📅 Data de referência: {data_referencia}")
        logging.info(f"🏛️ Órgão de origem: {ORGAO_ORIGEM}")

        # Garantir que o diretório de dados existe
        Path("dados_diarios").mkdir(exist_ok=True)
        listar_arquivos_com_detalhes(".")  # Mostrar diretório atual

        navegador = iniciar_navegador()
        wait = WebDriverWait(navegador, 30)

        try:
            preencher_formulario(navegador, wait, data_referencia, data_referencia)
            logging.info("📝 Formulário preenchido com sucesso.")

            resultados, paginas_info = navegar_paginas_e_extrair(
                navegador, wait, extrair_detalhes_processo, data_referencia
            )

            for info in paginas_info:
                logging.info(info)

            caminho_excel = None
            if resultados:
                logging.info(f"✅ {len(resultados)} HCs encontrados.")
                df = pd.DataFrame(resultados)
                caminho_csv = f"dados_diarios/resultados_{data_referencia.replace('/','-')}.csv"
                df.to_csv(caminho_csv, index=False)
                logging.info(f"💾 CSV salvo em: {caminho_csv}")
                
                # Criar o arquivo Excel
                caminho_excel = exportar_resultados(resultados, data_referencia, data_referencia)
                mensagem_status = f"Foram encontrados {len(resultados)} Habeas Corpus no STJ com origem no TJGO para a data {data_referencia}."
            else:
                logging.info("ℹ️ Nenhum HC encontrado.")
                mensagem_status = f"Nenhum Habeas Corpus foi encontrado no STJ com origem no TJGO para a data {data_referencia}."
                caminho_excel = None

        except Exception as e:
            logging.error(f"❌ Erro no scraper: {e}", exc_info=True)
            erros.append(str(e))
            caminho_excel = None
            mensagem_status = f"Ocorreu um erro durante a execução: {str(e)}"

        finally:
            try:
                navegador.quit()
                logging.info("🔒 Navegador encerrado.")
            except Exception as e:
                logging.error(f"❌ Erro ao fechar navegador: {e}")
                erros.append(str(e))

        fim = datetime.now()
        duracao = fim - inicio
        logging.info(f"⏱️ Tempo de execução: {duracao}")

        # ─── Métricas para e-mail ─────────────────────────────────────
        total_site = len(resultados) if resultados else 0
        total_extraidos = len(resultados) if resultados else 0
        paginas_processadas = len(paginas_info) if paginas_info else 0
        paginas_total = len(paginas_info) if paginas_info else 0
        horario_finalizacao = fim.strftime("%H:%M:%S")
        duracao_segundos = duracao.total_seconds()
        nome_arquivo = Path(caminho_excel).name if caminho_excel else ""

        # ─── Gerar HTML e arquivos auxiliares ─────────────────────────
        logging.info("📧 Preparando e-mail...")
        preparar_email_relatorio_diario(
            data_busca=data_referencia,
            caminho_arquivo=caminho_excel,
            mensagem_status=mensagem_status,
            erros=erros if erros else None,
            total_site=total_site,
            total_extraidos=total_extraidos,
            paginas_processadas=paginas_processadas,
            paginas_total=paginas_total,
            horario_finalizacao=horario_finalizacao,
            duracao_segundos=duracao_segundos,
            nome_arquivo=nome_arquivo
        )

        # ─── Gravar attachment.txt e verificar se o arquivo existe ─────────────────────────────────────
        try:
            if caminho_excel and os.path.exists(caminho_excel):
                # Salvar caminho absoluto, mais seguro
                caminho_absoluto = os.path.abspath(caminho_excel)
                with open("attachment.txt", "w", encoding="utf-8") as f:
                    f.write(caminho_absoluto)
                logging.info(f"📎 attachment.txt gerado com caminho absoluto: {caminho_absoluto}")
                if os.path.exists(caminho_absoluto):
                    logging.info(f"✅ Arquivo anexo verificado e existe: {caminho_absoluto}")
                    logging.info(f"   Tamanho do arquivo: {os.path.getsize(caminho_absoluto)} bytes")
                else:
                    logging.error(f"❌ ALERTA: O caminho do anexo existe mas o arquivo não: {caminho_absoluto}")
            else:
                logging.info("📎 Nenhum anexo para incluir no e-mail.")
                # Criar um arquivo vazio para attachment.txt para evitar erros
                with open("attachment.txt", "w", encoding="utf-8") as f:
                    f.write("")
        except Exception as e:
            logging.error(f"❌ Erro ao criar attachment.txt: {e}")
            # Garantir que o arquivo exista para evitar falhas no workflow
            with open("attachment.txt", "w", encoding="utf-8") as f:
                f.write("")

        # ─── DEBUG do ambiente ──────────────────────────────────────────
        logging.info("🔍 Verificando diretórios e arquivos:")
        listar_arquivos_com_detalhes(".")
        listar_arquivos_com_detalhes("dados_diarios")
        
        try:
            with open("attachment.txt", "r", encoding="utf-8") as f:
                anexo_path = f.read().strip()
                logging.info(f"📎 Conteúdo do attachment.txt: '{anexo_path}'")
                if anexo_path:
                    if os.path.exists(anexo_path):
                        logging.info(f"✅ Arquivo anexo existe: {anexo_path}")
                    else:
                        logging.error(f"❌ Arquivo anexo NÃO existe: {anexo_path}")
                else:
                    logging.info("📎 attachment.txt está vazio (sem anexo)")
        except Exception as e:
            logging.error(f"❌ Erro ao ler attachment.txt: {e}")

        logging.info("✅ Execução finalizada.")
        return 1 if erros else 0

    except Exception as e:
        logging.error(f"❌ Erro crítico: {e}", exc_info=True)
        return 1

# ─── CLI ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("🚫 Erro: Data não informada")
        print("Uso: python main.py <data no formato DD/MM/AAAA>")
        sys.exit(1)

    codigo_saida = main(sys.argv[1])
    sys.exit(codigo_saida)