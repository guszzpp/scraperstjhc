import pandas as pd
from datetime import date, timedelta
from pathlib import Path
import logging
import os

from retroativos.gerenciador_arquivos import obter_nome_arquivo_rechecagem


def preparar_email_alerta_retroativos(df_retroativos: pd.DataFrame):
    """
    Prepara os arquivos necessários para envio de e-mail de alerta de HCs retroativos.
    Gera:
      - email_subject.txt (para ser lido pelo GitHub Actions como outputs)
      - email_body.txt (para ser lido pelo GitHub Actions como env var)
      - attachment.txt (opcional, se houver anexo)
    """
    hoje = date.today()
    anteontem = hoje - timedelta(days=2)

    try:
        if df_retroativos is None or df_retroativos.empty:
            logging.info("Nenhum HC retroativo encontrado.")
            subject = f"ℹ️ Nenhum HC retroativo STJ/TJGO - {hoje.strftime('%d/%m/%Y')}"
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
            num_hcs = len(df_retroativos)
            subject = f"🚨 ALERTA: {num_hcs} HC(s) retroativo(s) STJ/TJGO - {hoje.strftime('%d/%m/%Y')}"
            
            # Criar corpo do email em HTML para facilitar visualização
            body = (
                f"<p>Prezado(a),</p>"
                f"<p><strong>Foram detectados {num_hcs} novos Habeas Corpus com datas anteriores à rechecagem:</strong></p>"
                f"<table border='1' cellpadding='5' cellspacing='0'>"
                f"<tr><th>Número do Processo</th><th>Relator</th><th>Situação</th><th>Data de Autuação</th></tr>"
            )
            
            for _, row in df_retroativos.iterrows():
                body += (
                    f"<tr>"
                    f"<td>{row.get('numero_processo', '')}</td>"
                    f"<td>{row.get('relator', '')}</td>"
                    f"<td>{row.get('situacao', '')}</td>"
                    f"<td>{row.get('data_autuacao', '')}</td>"
                    f"</tr>"
                )
            
            body += (
                f"</table>"
                f"<p>Recomenda-se verificação manual para confirmação.</p>"
                f"<p>Atenciosamente,<br>Sistema automatizado</p>"
            )
            
            # Nome do arquivo de anexo (será o Excel gerado)
            attachment = obter_nome_arquivo_rechecagem()
            
            # Salvar o DataFrame em Excel para anexar
            try:
                excel_path = Path(attachment)
                df_retroativos.to_excel(excel_path, index=False)
                logging.info(f"Arquivo Excel de retroativos gerado: {excel_path}")
            except Exception as e:
                logging.error(f"Erro ao salvar Excel de retroativos: {e}")
                attachment = ""  # Não anexar nada se falhar

        # Salvar os arquivos para uso pelo GitHub Actions
        Path("email_subject.txt").write_text(subject, encoding="utf-8")
        Path("email_body.txt").write_text(body, encoding="utf-8")
        
        # Salva o nome do anexo apenas se ele existir
        if attachment and os.path.exists(attachment):
            Path("attachment.txt").write_text(attachment, encoding="utf-8")
        else:
            # Se não houver anexo ou ele não existir, crie um arquivo vazio
            Path("attachment.txt").write_text("", encoding="utf-8")
            
        logging.info("Arquivos de e-mail gerados com sucesso")
        
        # Para debug nos logs do GitHub Actions
        logging.info(f"Assunto do email: {subject}")
        logging.info(f"Anexo: {attachment if attachment else 'Nenhum'}")

    except Exception as e:
        logging.error("Erro ao preparar arquivos de e-mail: %s", e, exc_info=True)
        # Fallback de emergência
        Path("email_subject.txt").write_text("🛑 Erro ao gerar e-mail de rechecagem", encoding="utf-8")
        Path("email_body.txt").write_text(
            "A rechecagem foi executada, mas houve falha ao gerar os arquivos de e-mail. Verifique os logs.",
            encoding="utf-8"
        )
        Path("attachment.txt").write_text("", encoding="utf-8")
