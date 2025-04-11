import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
from datetime import datetime

# 🔐 CONFIGURAÇÕES SMTP (ajuste conforme seu ambiente)
REMETENTE = "seu-email@dominio"
DESTINATARIOS = ["destinatario1@dominio", "destinatario2@dominio"]
SERVIDOR_SMTP = "smtp.dominio.com"
PORTA_SMTP = 587
USUARIO_SMTP = "usuario@dominio"
SENHA_SMTP = "SENHA_AQUI"

def enviar_email_alerta_novos_retroativos(retroativos: pd.DataFrame):
    """
    Envia um e-mail de alerta com os HCs detectados com data de julgamento
    anterior à última execução.
    """
    if retroativos.empty:
        return  # segurança redundante

    hoje = datetime.now().strftime("%d/%m/%Y")
    assunto = f"[ALERTA] Novos HCs retroativos detectados – {hoje}"

    # Corpo HTML do e-mail
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

    # Montar e-mail
    msg = MIMEMultipart()
    msg["From"] = REMETENTE
    msg["To"] = ", ".join(DESTINATARIOS)
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo, "html"))

    # Enviar via SMTP
    try:
        with smtplib.SMTP(SERVIDOR_SMTP, PORTA_SMTP) as server:
            server.starttls()
            server.login(USUARIO_SMTP, SENHA_SMTP)
            server.sendmail(REMETENTE, DESTINATARIOS, msg.as_string())
            print("✅ Alerta de retroativos enviado com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail de retroativos: {e}")
