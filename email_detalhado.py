import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
from datetime import datetime

def enviar_email_alerta_novos_retroativos(retroativos: pd.DataFrame):
    """
    Envia um e-mail de alerta com os HCs detectados com data de julgamento
    anterior à última execução.
    """
    if retroativos.empty:
        return

    # Variáveis de ambiente (injetadas via GitHub Secrets)
    remetente = os.getenv("EMAIL_USUARIO")
    destinatarios_raw = os.getenv("EMAIL_DESTINATARIO", "")
    senha = os.getenv("EMAIL_SENHA")

    if not remetente or not senha or not destinatarios_raw:
        print("❌ Variáveis de ambiente não definidas corretamente.")
        return

    destinatarios = [email.strip() for email in destinatarios_raw.split(",") if email.strip()]

    assunto = f"[ALERTA] Novos HCs retroativos detectados – {datetime.now().strftime('%d/%m/%Y')}"

    corpo = "<p>Foram detectados novos Habeas Corpus com datas de julgamento anteriores à última execução automatizada:</p>"
    corpo += "<table border='1' cellpadding='5' cellspacing='0'>"
    corpo += "<tr><th>Número do Processo</th><th>Data de Julgamento</th><th>Órgão Julgador</th><th>Relator</th></tr>"

    for _, row in retroativos.iterrows():
        corpo += (
            f"<tr>"
            f"<td>{row.get('numero_processo', '')}</td>"
            f"<td>{row.get('data_julgamento', '')}</td>"
            f"<td>{row.get('orgao_julgador', '')}</td>"
            f"<td>{row.get('relator', '')}</td>"
            f"</tr>"
        )
    corpo += "</table><p>Recomenda-se verificação manual para confirmação.</p>"

    # Montar o e-mail
    msg = MIMEMultipart()
    msg["From"] = remetente
    msg["To"] = ", ".join(destinatarios)
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo, "html"))

    # Enviar
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(remetente, senha)
            server.sendmail(remetente, destinatarios, msg.as_string())
            print("✅ Alerta de retroativos enviado com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail de retroativos: {e}")
