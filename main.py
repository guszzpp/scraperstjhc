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

        Path("dados_diarios").mkdir(exist_ok=True)

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

            caminho_excel = exportar_resultados(resultados, data_referencia, data_referencia)

            if resultados:
                logging.info(f"✅ {len(resultados)} HCs encontrados.")
                df = pd.DataFrame(resultados)
                caminho_csv = salvar_csv_resultado(df, data_referencia)
                logging.info(f"💾 CSV salvo em: {caminho_csv}")
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
        total_site = len(resultados)
        total_extraidos = len(resultados)
        paginas_processadas = len(paginas_info)
        paginas_total = len(paginas_info)
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

        # ─── Enviar o e-mail ───────────────────────────────────────────
        try:
            remetente = os.getenv("EMAIL_USUARIO")
            senha = os.getenv("EMAIL_SENHA")
            destinatarios = os.getenv("EMAIL_DESTINATARIO", "").split(",")

            if not remetente or not senha or not destinatarios:
                logging.error("❌ Variáveis de e-mail não definidas corretamente.")
            else:
                assunto = Path("email_subject.txt").read_text(encoding="utf-8").strip()
                corpo = Path("email_body.txt").read_text(encoding="utf-8").strip()
                anexo_path = Path("attachment.txt").read_text(encoding="utf-8").strip()

                msg = MIMEMultipart()
                msg["From"] = remetente
                msg["To"] = ", ".join(destinatarios)
                msg["Subject"] = assunto
                msg.attach(MIMEText(corpo, "html"))

                if anexo_path and Path(anexo_path).exists():
                    with open(anexo_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=Path(anexo_path).name)
                        part["Content-Disposition"] = f'attachment; filename="{Path(anexo_path).name}"'
                        msg.attach(part)

                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(remetente, senha)
                    server.sendmail(remetente, destinatarios, msg.as_string())
                    logging.info("📨 E-mail enviado com sucesso.")

        except Exception as envio_erro:
            logging.error(f"❌ Erro ao enviar e-mail: {envio_erro}")

        # ─── Copiar para dados_hoje ───────────────────────────────────
        try:
            if caminho_excel and Path(caminho_excel).exists():
                Path("dados_hoje").mkdir(exist_ok=True)
                destino = Path("dados_hoje") / Path(caminho_excel).name
                Path(caminho_excel).replace(destino)
                logging.info(f"📤 Arquivo copiado para rechecagem: {destino}")
        except Exception as e:
            logging.error(f"❌ Erro ao copiar arquivo para dados_hoje: {e}")

        # ─── DEBUG ls -la ──────────────────────────────────────────────
        listar_arquivos_com_detalhes("dados_diarios")

        # ─── Gravar attachment.txt ─────────────────────────────────────
        try:
            if caminho_excel and Path(caminho_excel).exists():
                with open("attachment.txt", "w", encoding="utf-8") as f:
                    f.write(str(Path(caminho_excel)))
                logging.info("📎 attachment.txt gerado com o nome do anexo.")
        except Exception as e:
            logging.error(f"❌ Erro ao criar attachment.txt: {e}")

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
