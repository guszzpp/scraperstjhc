import pandas as pd
from datetime import date, timedelta
from pathlib import Path
import logging
import os
from textwrap import dedent
from retroativos.gerenciador_arquivos import obter_nome_arquivo_rechecagem


def preparar_email_alerta_retroativos(df_novos):
    from util.envia_email_html import enviar_email

    hoje = datetime.now().strftime("%d/%m/%Y")
    anteontem = (datetime.now() - timedelta(days=2)).strftime("%d/%m/%Y")
    assunto = f"[STJ - RECHECAGEM] Resultado para o dia {anteontem}"

    if df_novos is not None and not df_novos.empty:
        corpo_html = f"""
        <p>Foram localizados novos Habeas Corpus retroativos autuados anteriormente, mas detectados apenas hoje.</p>
        <p>Data da rechecagem: <b>{hoje}</b><br>
        Data alvo (autuação dos retroativos): <b>{anteontem}</b></p>
        <br>
        <p>Confira os novos HCs detectados:</p>
        {df_novos.to_html(index=False, border=1)}
        <br>
        <p>O arquivo em anexo contém os mesmos dados exibidos acima.</p>
        """
        anexo = "dados_diarios/rechecagem_hc_tjgo_" + datetime.now().strftime("%d-%m-%Y") + ".xlsx"
    else:
        corpo_html = f"""
        <p>Nenhum novo Habeas Corpus retroativo (autuado em data anterior, mas só detectado hoje) foi localizado no STJ com origem no TJGO, na rechecagem realizada em <b>{hoje}</b> para o dia <b>{anteontem}</b>.</p>
        <br>
        <p>Este e-mail foi gerado automaticamente.</p>
        """
        anexo = None

    enviar_email(assunto=assunto, corpo_html=corpo_html, anexo=anexo)

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
        Path("email_body.txt").write_text(body, encoding="utf-8")
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
