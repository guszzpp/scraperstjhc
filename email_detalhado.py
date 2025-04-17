import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
from datetime import date, timedelta
from pathlib import Path

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

def enviar_email_alerta_novos_retroativos(df_retroativos: pd.DataFrame):
    hoje = date.today()
    anteontem = hoje - timedelta(days=2)

    if df_retroativos.empty:
        subject = f"ℹ️ Nenhum NOVO HC detectado para o dia {hoje.strftime('%d/%m/%Y')}"
        body = f"""Prezado(a),

Nenhum novo Habeas Corpus retroativo (autuado em data anterior, mas só detectado hoje) foi localizado no STJ com origem no TJGO, na rechecagem realizada em {hoje.strftime('%d/%m/%Y')} para o dia {anteontem.strftime('%d/%m/%Y')}.

Essa rechecagem visa identificar inserções tardias pelo sistema do STJ — e hoje, nenhuma nova inserção desse tipo foi identificada.

Atenciosamente,
Sistema automatizado
"""
        Path("email_subject.txt").write_text(subject, encoding="utf-8")
        Path("email_body.txt").write_text(body, encoding="utf-8")
        Path("attachment.txt").write_text("", encoding="utf-8")
        return

    # Se houver retroativos:
    subject = f"[ALERTA] Novos HCs retroativos detectados – {hoje.strftime('%d/%m/%Y')}"

    body = "<p>Foram detectados novos Habeas Corpus com datas de julgamento anteriores à última execução automatizada:</p>"
    body += "<table border='1' cellpadding='5' cellspacing='0'>"
    body += "<tr><th>Número do Processo</th><th>Data de Julgamento</th><th>Órgão Julgador</th><th>Relator</th></tr>"

    for _, row in df_retroativos.iterrows():
        body += (
            f"<tr>"
            f"<td>{row.get('numero_processo', '')}</td>"
            f"<td>{row.get('data_julgamento', '')}</td>"
            f"<td>{row.get('orgao_julgador', '')}</td>"
            f"<td>{row.get('relator', '')}</td>"
            f"</tr>"
        )

    body += "</table><p>Recomenda-se verificação manual para confirmação.</p>"

    Path("email_subject.txt").write_text(subject, encoding="utf-8")
    Path("email_body.txt").write_text(body, encoding="utf-8")
    Path("attachment.txt").write_text("hc_tjgo_retroativos.xlsx", encoding="utf-8")

    # Geração do arquivo Excel é presumida como existente no fluxo anterior.
