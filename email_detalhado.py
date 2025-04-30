import pandas as pd
from datetime import date, timedelta
from pathlib import Path
import logging
import os

from retroativos.gerenciador_arquivos import obter_nome_arquivo_rechecagem


def preparar_email_alerta_retroativos(df_retroativos: pd.DataFrame):
    hoje = date.today()
    anteontem = hoje - timedelta(days=2)

    try:
        if df_retroativos is None or df_retroativos.empty:
            logging.info("Nenhum HC retroativo encontrado.")
            subject = f"ℹ️ Sem divergências na rechecagem STJ/TJGO - {anteontem.strftime('%d/%m/%Y')}"
            body = (
                f"<p>Prezado(a),</p>"
                f"<p>Informamos que não foram encontradas divergências na rechecagem dos HCs do STJ com origem no TJGO realizada em "
                f"{hoje.strftime('%d/%m/%Y')} para o dia {anteontem.strftime('%d/%m/%Y')}.</p>"
                f"<p>Essa rechecagem visa identificar inserções tardias pelo sistema do STJ — e hoje não foi identificada nenhuma inserção desse tipo.</p>"
                f"<br>"
                f"<p style='color: #777; font-size: 12px;'>Este e-mail foi gerado automaticamente pelo sistema "
                f"de rechecagem. Em caso de dúvidas, entre em contato com o administrador do sistema.</p>"
                f"<p style='color: #777; font-size: 12px;'>© {hoje.year} - Sistema Automatizado de Monitoramento de HCs STJ/TJGO</p>"
            )
            attachment = ""
        else:
            num_hcs = len(df_retroativos)
            subject = f"🚨 ALERTA: {num_hcs} HC(s) encontrados na rechecagem STJ/TJGO - {anteontem.strftime('%d/%m/%Y')}"
            body = (
                f"<p>Prezado(a),</p>"
                f"<p><strong>🚨 ALERTA: Divergência na rechecagem - {anteontem.strftime('%d/%m/%Y')}</strong></p>"
                f"<p>Foram detectados {num_hcs} Habeas Corpus com datas anteriores à rechecagem:</p>"
                f"<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse; width: 100%; margin: auto;'>"
                f"<tr style='background-color: #1F4E78; color: #FFFFFF;'>"
                f"<th>Número do Processo</th><th>Relator</th><th>Situação</th><th>Data de Autuação</th></tr>"
            )

            cor_linha = True
            for _, row in df_retroativos.iterrows():
                estilo = "background-color: #f9f9f9;" if cor_linha else ""
                body += (
                    f"<tr style='{estilo}'>"
                    f"<td>{row.get('numero_processo', '')}</td>"
                    f"<td>{row.get('relator', '')}</td>"
                    f"<td>{row.get('situacao', '')}</td>"
                    f"<td>{row.get('data_autuacao', '')}</td>"
                    f"</tr>"
                )
                cor_linha = not cor_linha

            body += (
                f"</table>"
                f"<p><strong>Atenção:</strong> Recomenda-se verificação manual para confirmação.</p>"
                f"<p>O arquivo anexo contém os detalhes completos de todos os processos retroativos detectados.</p>"
                f"<br>"
                f"<p style='color: #777; font-size: 12px;'>Este e-mail foi gerado automaticamente pelo sistema "
                f"de rechecagem. Em caso de dúvidas, entre em contato com o administrador do sistema.</p>"
                f"<p style='color: #777; font-size: 12px;'>© {hoje.year} - Sistema Automatizado de Monitoramento de HCs STJ/TJGO</p>"
            )

            attachment = obter_nome_arquivo_rechecagem()
            try:
                excel_path = Path(attachment)
                df_retroativos["Detectado_Em"] = hoje.strftime('%d/%m/%Y')
                df_retroativos["Obs"] = "Processo detectado retroativamente"
                df_retroativos.to_excel(excel_path, index=False, engine='openpyxl')

                try:
                    from openpyxl import load_workbook
                    from openpyxl.styles import PatternFill, Font, Alignment

                    wb = load_workbook(excel_path)
                    ws = wb.active

                    fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
                    font = Font(color="FFFFFF", bold=True)

                    for cell in ws[1]:
                        cell.fill = fill
                        cell.font = font
                        cell.alignment = Alignment(horizontal='center', vertical='center')

                    for column in ws.columns:
                        max_length = max((len(str(cell.value)) for cell in column if cell.value), default=0)
                        ws.column_dimensions[column[0].column_letter].width = max(10, min(max_length + 2, 50))

                    wb.save(excel_path)
                except Exception as e:
                    logging.warning(f"Não foi possível aplicar formatação avançada: {e}")
            except Exception as e:
                logging.error(f"Erro ao salvar Excel de retroativos: {e}")
                attachment = ""

        Path("email_subject.txt").write_text(subject, encoding="utf-8")
        Path("email_body.txt").write_text(body, encoding="utf-8")
        Path("attachment.txt").write_text(attachment if attachment and os.path.exists(attachment) else "", encoding="utf-8")

    except Exception as e:
        logging.error("Erro ao preparar arquivos de e-mail: %s", e, exc_info=True)
        Path("email_subject.txt").write_text("🛑 Erro ao gerar e-mail de rechecagem", encoding="utf-8")
        Path("email_body.txt").write_text(
            "<p><strong>🛑 ERRO NO SISTEMA</strong></p>"
            "<p>A rechecagem foi executada, mas houve falha ao gerar os arquivos de e-mail. Verifique os logs.</p>",
            encoding="utf-8"
        )
        Path("attachment.txt").write_text("", encoding="utf-8")


def preparar_email_relatorio_diario(data_busca, caminho_arquivo=None, mensagem_status=None, erros=None):
    hoje = date.today()

    try:
        tem_anexo = caminho_arquivo and os.path.exists(caminho_arquivo)

        if erros:
            subject = f"⚠️ Alerta: Erros na checagem de HCs STJ/TJGO - {data_busca}"
        elif tem_anexo:
            subject = f"✅ Resultados da checagem de HCs STJ/TJGO - {data_busca}"
        else:
            subject = f"ℹ️ Nenhum HC encontrado na checagem STJ/TJGO - {data_busca}"

        body = (
            f"<p>Prezado(a),</p>"
            f"<p>Segue em anexo o relatório de Habeas Corpus (HCs) autuados no STJ com origem no TJGO, referente à data <strong>{data_busca}</strong>.</p>"
            f"<br>"
            f"<p><strong>Resumo da execução:</strong></p>"
            f"<ul>"
            f"<li><strong>Data de busca:</strong> {data_busca}</li>"
            f"<li><strong>Data de execução:</strong> {hoje.strftime('%d/%m/%Y')}</li>"
            f"<li><strong>Origem:</strong> TJGO</li>"
            f"</ul>"
        )

        if erros:
            body += f"<li><strong>⚠️ Erros detectados:</strong></li><ul>"
            for erro in erros:
                body += f"<li>{erro}</li>"
            body += "</ul>"
        elif mensagem_status:
            body += f"<li><strong>Status:</strong> {mensagem_status}</li>"
        elif tem_anexo:
            body += f"<li><strong>Status:</strong> HCs localizados – detalhes no anexo.</li>"
        else:
            body += f"<li><strong>Status:</strong> Nenhum HC localizado.</li>"

        body += (
            f"<br>"
            f"<p><strong>Observação:</strong> Esta automação tem como objetivo auxiliar no acompanhamento processual, mas "
            f"<strong>não substitui a conferência manual nos canais oficiais do STJ</strong>.</p>"
            f"<br>"
            f"<p style='color: #777; font-size: 12px;'>Este e-mail foi gerado automaticamente pelo sistema de monitoramento de HCs.</p>"
            f"<p style='color: #777; font-size: 12px;'>© {hoje.year} - Sistema Automatizado STJ/TJGO</p>"
        )

        Path("email_subject.txt").write_text(subject, encoding="utf-8")
        Path("email_body.txt").write_text(body, encoding="utf-8")
        Path("attachment.txt").write_text(caminho_arquivo if tem_anexo else "", encoding="utf-8")

        logging.info("Arquivos de e-mail para relatório diário gerados com sucesso")

    except Exception as e:
        logging.error("Erro ao preparar arquivos de e-mail para relatório diário: %s", e, exc_info=True)
        Path("email_subject.txt").write_text("🛑 Erro ao gerar e-mail de relatório diário", encoding="utf-8")
        Path("email_body.txt").write_text(
            "<p><strong>🛑 ERRO NO SISTEMA</strong></p>"
            "<p>O scraper foi executado, mas houve falha ao gerar os arquivos de e-mail. Verifique os logs.</p>",
            encoding="utf-8"
        )
        Path("attachment.txt").write_text("", encoding="utf-8")
