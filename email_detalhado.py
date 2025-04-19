import pandas as pd
from datetime import date, timedelta
from pathlib import Path
import logging

from retroativos.gerenciador_arquivos import obter_nome_arquivo_rechecagem


def preparar_email_alerta_retroativos(df_retroativos: pd.DataFrame):
    """
    Prepara os arquivos necessários para envio de e-mail de alerta de HCs retroativos.
    Gera:
      - email_subject.txt
      - email_body.txt
      - attachment.txt
    """
    hoje = date.today()
    anteontem = hoje - timedelta(days=2)

    try:
        if df_retroativos.empty:
            subject = (
                f"ℹ️ Nenhum NOVO HC detectado para o dia {hoje.strftime('%d/%m/%Y')}"
            )
            body = (
                f"Prezado(a),\n\n"
                f"Nenhum novo Habeas Corpus retroativo (autuado em data anterior, mas só detectado hoje) "
                f"foi localizado no STJ com origem no TJGO, na rechecagem realizada em "
                f"{hoje.strftime('%d/%m/%Y')} para o dia {anteontem.strftime('%d/%m/%Y')}.\n\n"
                f"Essa rechecagem visa identificar inserções tardias pelo sistema do STJ — e hoje, "
                f"nenhuma nova inserção desse tipo foi identificada.\n\n"
                f"Atenciosamente,\n"
                f"Sistema automatizado"
            )
            attachment = ""
        else:
            subject = (
                f"[ALERTA] Novos HCs retroativos detectados – {hoje.strftime('%d/%m/%Y')}"
            )
            html = (
                "<p>Foram detectados novos Habeas Corpus com datas de julgamento "
                "anteriores à última execução automatizada:</p>"
                "<table border='1' cellpadding='5' cellspacing='0'>"
                "<tr><th>Número do Processo</th><th>Data de Julgamento</th>"
                "<th>Órgão Julgador</th><th>Relator</th></tr>"
            )
            for _, row in df_retroativos.iterrows():
                html += (
                    "<tr>"
                    f"<td>{row.get('numero_processo', '')}</td>"
                    f"<td>{row.get('data_julgamento', '')}</td>"
                    f"<td>{row.get('orgao_julgador', '')}</td>"
                    f"<td>{row.get('relator', '')}</td>"
                    "</tr>"
                )
            html += "</table><p>Recomenda-se verificação manual para confirmação.</p>"

            body = html
            attachment = obter_nome_arquivo_rechecagem()

        Path("email_subject.txt").write_text(subject, encoding="utf-8")
        Path("email_body.txt").write_text(body, encoding="utf-8")
        Path("attachment.txt").write_text(attachment, encoding="utf-8")
        logging.info("Arquivos de e-mail gerados com sucesso")

    except Exception as e:
        logging.error("Erro ao preparar arquivos de e-mail: %s", e, exc_info=True)
        # Fallback de emergência
        Path("email_subject.txt").write_text("🛑 Erro ao gerar e-mail de rechecagem", encoding="utf-8")
        Path("email_body.txt").write_text(
            "A rechecagem foi executada, mas houve falha ao gerar os arquivos de e-mail. Verifique os logs.",
            encoding="utf-8"
        )
        Path("attachment.txt").write_text("", encoding="utf-8")
