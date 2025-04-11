import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import pandas as pd
from datetime import datetime

# Configurações comuns
REMETENTE = "seu-email@dominio"
DESTINATARIOS = ["destinatario@dominio"]
SMTP_SERVIDOR = "smtp.dominio.com"
SMTP_PORTA = 587
SMTP_USUARIO = "usuario@dominio"
SMTP_SENHA = "SENHA_AQUI"

def _enviar_email(msg: MIMEMultipart):
    try:
        with smtplib.SMTP(SMTP_SERVIDOR, SMTP_PORTA) as server:
            server.starttls()
            server.login(SMTP_USUARIO, SMTP_SENHA)
            server.sendmail(REMETENTE, DESTINATARIOS, msg.as_string())
            print("E-mail enviado com sucesso.")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

def enviar_email_resultado_ordinario(df_resultado: pd.DataFrame, caminho_arquivo_excel: str):
    """
    Envia o e-mail diário ordinário com o arquivo de resultados como anexo.
    """
    hoje = datetime.now().strftime("%d/%m/%Y")
    assunto = f"Resultados de HC do STJ – {hoje}"

    corpo = "<p>Segue em anexo o resultado da extração diária de Habeas Corpus com origem no TJGO.</p>"
    corpo += f"<p>Total de registros coletados: <strong>{len(df_resultado)}</strong>.</p>"

    msg = MIMEMultipart()
    msg['From'] = REMETENTE
    msg['To'] = ", ".join(DESTINATARIOS)
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'html'))

    # Anexar o arquivo Excel
    with open(caminho_arquivo_excel, "rb") as f:
        anexo = MIMEApplication(f.read(), _subtype="xlsx")
        anexo.add_header('Content-Disposition', 'attachment', filename=caminho_arquivo_excel.split("/")[-1])
        msg.attach(anexo)

    _enviar_email(msg)

def enviar_email_alerta_novos_retroativos(retroativos: pd.DataFrame):
    """
    Envia alerta se forem detectados novos HCs com data anterior à execução anterior.
    """
    if retroativos.empty:
        return

    hoje = datetime.now().strftime("%d/%m/%Y")
    assunto = f"[ALERTA] Novos HCs retroativos detectados – {hoje}"

    corpo = "<p>Foram detectados novos Habeas Corpus com datas de julgamento anteriores ao último rastreio automatizado:</p>"
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

    msg = MIMEMultipart()
    msg['From'] = REMETENTE
    msg['To'] = ", ".join(DESTINATARIOS)
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'html'))

    _enviar_email(msg)
