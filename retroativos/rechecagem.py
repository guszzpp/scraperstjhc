# retroativos/rechecagem.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import os
import pandas as pd
from datetime import datetime
from supabase.supabase_download import download_from_supabase
import logging

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)

def log(msg):
    logging.info(msg)

def carregar_arquivo(path):
    try:
        return pd.read_excel(path)
    except Exception as e:
        log(f"Erro ao carregar {path}: {e}")
        return pd.DataFrame()

def rechecagem_retroativa(data_referencia_str):
    data_ref = datetime.strptime(data_referencia_str, "%d/%m/%Y")
    nome_data = data_ref.strftime("%d-%m-%Y")

    nome_arquivo = f"hc_tjgo_{nome_data}.xlsx"
    caminho_local_antigo = f"dados_diarios/{nome_arquivo}"
    caminho_local_novo = f"dados_hoje/hc_tjgo_{nome_data}.xlsx"

    # 1. Baixar do Supabase o arquivo de D-2 gerado ontem (arquivo antigo)
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        if not supabase_url:
            log("Erro: SUPABASE_URL não definida nas variáveis de ambiente")
            supabase_url = "https://example.supabase.co"
        download_from_supabase(
            supabase_url=supabase_url,
            bucket_name="hctjgo",
            file_name=nome_arquivo,
            destination_path=caminho_local_antigo
        )
        log(f"Arquivo original encontrado no Supabase.")
        df_antigo = carregar_arquivo(caminho_local_antigo)
        motivo_ausencia = None
    except Exception as e:
        if "Object not found" in str(e) or "404" in str(e):
            log(f"Arquivo de D-2 não encontrado no Supabase: {nome_arquivo}. Considerando base antiga como vazia.")
            motivo_ausencia = f"[AVISO] Não foi possível baixar o arquivo de D-2 ({nome_arquivo}) do Supabase. Presumindo que ontem não havia HCs para essa data."
            df_antigo = pd.DataFrame(columns=[
                "Número do Processo", "Classe", "Data Autuação", "Origem",
                "Relator", "Órgão Julgador", "Data Julgamento", "Data Publicação"
            ])
        else:
            log(f"Erro ao baixar arquivo do Supabase: {str(e)}")
            motivo_ausencia = f"[ERRO] Falha ao baixar o arquivo de D-2 ({nome_arquivo}) do Supabase: {str(e)}"
            df_antigo = pd.DataFrame()

    # 2. Carrega o arquivo raspado hoje (rechecagem de D-2)
    df_novo = carregar_arquivo(caminho_local_novo)

    if df_novo.empty and df_antigo.empty:
        log("Ambos os arquivos estão vazios. Nenhum HC detectado. Nada será enviado.")
        preparar_email_vazio(data_ref)
        return

    chave = "Número do Processo"
    novos = df_novo[~df_novo[chave].isin(df_antigo[chave])]
    removidos = df_antigo[~df_antigo[chave].isin(df_novo[chave])]

    alteracoes = []
    processos_comuns = set(df_novo[chave]).intersection(df_antigo[chave])
    for processo in processos_comuns:
        linha_nova = df_novo[df_novo[chave] == processo].iloc[0]
        linha_antiga = df_antigo[df_antigo[chave] == processo].iloc[0]
        for coluna in df_novo.columns:
            if linha_nova[coluna] != linha_antiga[coluna]:
                alteracoes.append({
                    "Processo": processo,
                    "Coluna": coluna,
                    "Valor Antigo": linha_antiga[coluna],
                    "Valor Novo": linha_nova[coluna]
                })

    # 3. Geração de relatórios e e-mails
    tem_divergencia = not novos.empty or not removidos.empty or alteracoes

    if tem_divergencia:
        log("Divergências detectadas:")
        if motivo_ausencia:
            log(motivo_ausencia)
        if not novos.empty:
            log(f"- {len(novos)} novos HCs retroativos")
            novos.to_excel("novos_retroativos.xlsx", index=False)
        if not removidos.empty:
            log(f"- {len(removidos)} HCs desapareceram (erro de consistência?)")
            removidos.to_excel("hcs_removidos.xlsx", index=False)
        if alteracoes:
            log(f"- {len(alteracoes)} alterações em campos")
            pd.DataFrame(alteracoes).to_excel("hcs_alterados.xlsx", index=False)

        preparar_email_com_divergencia(data_ref, novos, motivo_ausencia)
        with open("attachment.txt", "w", encoding="utf-8") as f:
            f.write("novos_retroativos.xlsx" if not novos.empty else "")
    else:
        if motivo_ausencia:
            log(motivo_ausencia)
        log("Nenhuma divergência detectada.")
        preparar_email_vazio(data_ref, motivo_ausencia)
        with open("attachment.txt", "w", encoding="utf-8") as f:
            f.write("")

def preparar_email_com_divergencia(data_ref, df_novos, motivo_ausencia=None):
    data_formatada = data_ref.strftime("%d/%m/%Y")
    hoje = datetime.today().strftime("%d/%m/%Y")

    with open("email_subject.txt", "w", encoding="utf-8") as f:
        f.write(f"[RECHECAGEM RETROATIVA] Novos HCs detectados para {data_formatada}")

    with open("email_body.txt", "w", encoding="utf-8") as f:
        corpo = (
            f"⚖️ Foram detectados {len(df_novos)} novos Habeas Corpus retroativos — "
            f"autuados originalmente em {data_formatada}, mas não detectados na raspagem original.\n\n"
            f"A rechecagem foi realizada hoje, {hoje}."
        )
        if motivo_ausencia:
            corpo += f"\n\n{motivo_ausencia}"
        f.write(corpo)

def preparar_email_vazio(data_ref, motivo_ausencia=None):
    data_formatada = data_ref.strftime("%d/%m/%Y")
    hoje = datetime.today().strftime("%d/%m/%Y")

    with open("email_subject.txt", "w", encoding="utf-8") as f:
        f.write("Nenhum novo HC retroativo detectado")

    with open("email_body.txt", "w", encoding="utf-8") as f:
        corpo = (
            f"Nenhum novo Habeas Corpus retroativo (autuado em data anterior, mas só detectado hoje) "
            f"foi localizado no STJ com origem no TJGO, na rechecagem realizada em {hoje} para o dia {data_formatada}."
        )
        if motivo_ausencia:
            corpo += f"\n\n{motivo_ausencia}"
        f.write(corpo)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python rechecagem.py <data>")
        print("Exemplo: python rechecagem.py 02/05/2025")
        sys.exit(1)
    rechecagem_retroativa(sys.argv[1])