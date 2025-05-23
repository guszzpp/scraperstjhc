import os
import smtplib
from datetime import date, datetime, timedelta
from pathlib import Path
from email.message import EmailMessage
from email.mime.application import MIMEApplication
from textwrap import dedent
import logging
import pandas as pd

def enviar_email(assunto, corpo_html, anexo=None):
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    DESTINATARIO = os.getenv("EMAIL_DESTINATARIO_TESTE")

    if not (EMAIL_USER and EMAIL_PASS and DESTINATARIO):
        raise ValueError("Credenciais ou destinatário de e-mail não definidos nas variáveis de ambiente.")

    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = EMAIL_USER
    msg["To"] = DESTINATARIO
    msg.set_content("Este e-mail requer um cliente compatível com HTML.")
    body_formatado = corpo_html.replace("\n", "<br>")
    msg.add_alternative(body_formatado, subtype='html')
    if anexo and os.path.exists(anexo):
        with open(anexo, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(anexo))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(anexo)}"'
        msg.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

    print(f"E-mail enviado para {DESTINATARIO}")


def preparar_email_relatorio_diario(
    data_busca,
    caminho_arquivo=None,
    mensagem_status=None,
    erros=None,
    total_site=0,
    total_extraidos=0,
    paginas_processadas=0,
    paginas_total=0,
    horario_finalizacao="",
    duracao_segundos=0.0,
    nome_arquivo=""
):
    hoje = date.today()

    try:
        tem_anexo = bool(caminho_arquivo and os.path.exists(caminho_arquivo))

        if erros:
            erros_str = "\n".join(f"- {e}" for e in erros)
            subject = f"⚠️ Alerta: Erros na checagem de HCs STJ/TJGO - {data_busca}"
            body = dedent(f"""
                Prezado(a),

                Tivemos erros na execução para {data_busca}:

                {erros_str}

                Atenciosamente,
                Sistema automatizado
            """)

        elif tem_anexo:
            subject = f"✅ Resultados da checagem de HCs STJ/TJGO - {data_busca}"
            body = dedent(f"""
                Prezado(a),

                Segue em anexo o relatório de Habeas Corpus (HCs) autuados no STJ,
                com origem no TJGO, referente a {data_busca}.

                Resumo da execução:
                - Resultados encontrados pelo site: {total_site}
                - HCs efetivamente extraídos: {total_extraidos}
                - Páginas processadas: {paginas_processadas} de {paginas_total}
                - Script finalizado em: {horario_finalizacao} (duração {duracao_segundos:.2f}s)

                O arquivo '{nome_arquivo}' está anexado a este e-mail.

                Atenciosamente,
                Sistema automatizado
            """)

        else:
            subject = f"ℹ️ Nenhum HC encontrado na checagem STJ/TJGO - {data_busca}"
            body = dedent(f"""
                Prezado(a),

                Nenhum Habeas Corpus foi encontrado no STJ com origem no TJGO
                para a data {data_busca}.

                Resumo da execução:
                - Resultados encontrados pelo site: {total_site}
                - HCs efetivamente extraídos: {total_extraidos}
                - Páginas processadas: {paginas_processadas} de {paginas_total}
                - Script finalizado em: {horario_finalizacao} (duração {duracao_segundos:.2f}s)

                Atenciosamente,
                Sistema automatizado
            """)

        # --- gravação dos arquivos que serão lidos pelo main.py ---
        Path("email_subject.txt").write_text(subject, encoding="utf-8")
        Path("email_body.txt").write_text(body.replace("\n", "<br>"), encoding="utf-8")
        Path("attachment.txt").write_text(caminho_arquivo if tem_anexo else "", encoding="utf-8")

    except Exception as e:
        logging.error("Erro ao preparar arquivos de e-mail para relatório diário", exc_info=True)
        Path("email_subject.txt").write_text("🛑 Erro ao gerar e-mail de relatório diário", encoding="utf-8")
        Path("email_body.txt").write_text(
            "<p><strong>🛑 ERRO NO SISTEMA</strong></p>"
            "<p>O scraper foi executado, mas houve falha ao gerar os arquivos de e-mail. Verifique os logs.</p>",
            encoding="utf-8"
        )
        Path("attachment.txt").write_text("", encoding="utf-8")
