# retroativos/rechecagem.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import os
import pandas as pd
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
load_dotenv()

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)

def log(msg):
    logging.info(msg)

def carregar_arquivo(path):
    try:
        if path.endswith('.xlsx'):
            return pd.read_excel(path)
        elif path.endswith('.csv'):
            return pd.read_csv(path)
        else:
            log(f"Formato de arquivo não suportado: {path}")
            return pd.DataFrame()
    except Exception as e:
        log(f"Erro ao carregar {path}: {e}")
        return pd.DataFrame()

def rechecagem_retroativa(data_referencia_str):
    """
    Executa rechecagem retroativa comparando:
    - Arquivo de D+1 (primeira raspagem)
    - Arquivo de D+2 (segunda raspagem)
    
    A rechecagem deve ser executada em D+2 para comparar com D+1
    """
    data_ref = datetime.strptime(data_referencia_str, "%d/%m/%Y")
    nome_data = data_ref.strftime("%d-%m-%Y")
    
    # Data de D+1 (primeira raspagem)
    data_d1 = data_ref - timedelta(days=1)
    nome_data_d1 = data_d1.strftime("%d-%m-%Y")
    
    # Caminhos dos arquivos
    arquivo_d1_xlsx = f"dados_diarios/hc_tjgo_{nome_data_d1}.xlsx"
    arquivo_d1_csv = f"dados_diarios/resultados_{nome_data_d1}.csv"
    arquivo_d2_xlsx = f"dados_diarios/hc_tjgo_{nome_data}.xlsx"
    arquivo_d2_csv = f"dados_diarios/resultados_{nome_data}.csv"
    
    log(f"🔍 Iniciando rechecagem retroativa para {data_referencia_str}")
    log(f"📁 Arquivo D+1 (primeira raspagem): {arquivo_d1_xlsx}")
    log(f"📁 Arquivo D+2 (segunda raspagem): {arquivo_d2_xlsx}")
    
    # 1. Carregar arquivo de D+1 (primeira raspagem)
    df_d1 = pd.DataFrame()
    if os.path.exists(arquivo_d1_xlsx):
        df_d1 = carregar_arquivo(arquivo_d1_xlsx)
        log(f"✅ Arquivo D+1 carregado: {len(df_d1)} registros")
    elif os.path.exists(arquivo_d1_csv):
        df_d1 = carregar_arquivo(arquivo_d1_csv)
        log(f"✅ Arquivo D+1 (CSV) carregado: {len(df_d1)} registros")
    else:
        log(f"❌ Arquivo D+1 não encontrado: {arquivo_d1_xlsx} ou {arquivo_d1_csv}")
        df_d1 = pd.DataFrame(columns=[
            "Número do Processo", "Classe", "Data Autuação", "Origem",
            "Relator", "Órgão Julgador", "Data Julgamento", "Data Publicação"
        ])
    
    # 2. Carregar arquivo de D+2 (segunda raspagem)
    df_d2 = pd.DataFrame()
    if os.path.exists(arquivo_d2_xlsx):
        df_d2 = carregar_arquivo(arquivo_d2_xlsx)
        log(f"✅ Arquivo D+2 carregado: {len(df_d2)} registros")
    elif os.path.exists(arquivo_d2_csv):
        df_d2 = carregar_arquivo(arquivo_d2_csv)
        log(f"✅ Arquivo D+2 (CSV) carregado: {len(df_d2)} registros")
    else:
        log(f"❌ Arquivo D+2 não encontrado: {arquivo_d2_xlsx} ou {arquivo_d2_csv}")
        df_d2 = pd.DataFrame(columns=[
            "Número do Processo", "Classe", "Data Autuação", "Origem",
            "Relator", "Órgão Julgador", "Data Julgamento", "Data Publicação"
        ])
    
    # 3. Verificar se ambos os arquivos estão vazios
    if df_d1.empty and df_d2.empty:
        log("⚠️ Ambos os arquivos estão vazios. Nenhum HC detectado em nenhuma das raspagens.")
        preparar_email_vazio(data_ref)
        with open("attachment.txt", "w", encoding="utf-8") as f:
            f.write("")
        return
    
    # 4. Normalizar nomes das colunas para comparação
    coluna_processo = None
    for col in ["Número do Processo", "numero_processo", "processo"]:
        if col in df_d1.columns and col in df_d2.columns:
            coluna_processo = col
            break
    
    if not coluna_processo:
        log("❌ Coluna de número do processo não encontrada em ambos os arquivos")
        preparar_email_vazio(data_ref)
        with open("attachment.txt", "w", encoding="utf-8") as f:
            f.write("")
        return
    
    # 5. Identificar novos HCs (presentes em D+2 mas não em D+1)
    novos_hcs = df_d2[~df_d2[coluna_processo].isin(df_d1[coluna_processo])]
    
    # 6. Identificar HCs que desapareceram (presentes em D+1 mas não em D+2)
    hcs_removidos = df_d1[~df_d1[coluna_processo].isin(df_d2[coluna_processo])]
    
    # 7. Identificar alterações em HCs existentes
    alteracoes = []
    processos_comuns = set(df_d2[coluna_processo]).intersection(df_d1[coluna_processo])
    
    for processo in processos_comuns:
        linha_d2 = df_d2[df_d2[coluna_processo] == processo].iloc[0]
        linha_d1 = df_d1[df_d1[coluna_processo] == processo].iloc[0]
        
        for coluna in df_d2.columns:
            if coluna in df_d1.columns:
                if str(linha_d2[coluna]) != str(linha_d1[coluna]):
                    alteracoes.append({
                        "Processo": processo,
                        "Coluna": coluna,
                        "Valor D+1": linha_d1[coluna],
                        "Valor D+2": linha_d2[coluna]
                    })
    
    # 8. Gerar relatório
    tem_divergencia = not novos_hcs.empty or not hcs_removidos.empty or alteracoes
    
    log(f"📊 Resultados da rechecagem:")
    log(f"   - Novos HCs: {len(novos_hcs)}")
    log(f"   - HCs removidos: {len(hcs_removidos)}")
    log(f"   - Alterações: {len(alteracoes)}")
    
    if tem_divergencia:
        log("🚨 Divergências detectadas!")
        
        if not novos_hcs.empty:
            log(f"   📄 Salvando {len(novos_hcs)} novos HCs retroativos")
            novos_hcs.to_excel("novos_retroativos.xlsx", index=False)
        
        if not hcs_removidos.empty:
            log(f"   📄 Salvando {len(hcs_removidos)} HCs removidos")
            hcs_removidos.to_excel("hcs_removidos.xlsx", index=False)
        
        if alteracoes:
            log(f"   📄 Salvando {len(alteracoes)} alterações")
            pd.DataFrame(alteracoes).to_excel("hcs_alterados.xlsx", index=False)
        
        preparar_email_com_divergencia(data_ref, novos_hcs)
        with open("attachment.txt", "w", encoding="utf-8") as f:
            f.write("novos_retroativos.xlsx" if not novos_hcs.empty else "")
    else:
        log("✅ Nenhuma divergência detectada. Todos os HCs são consistentes entre D+1 e D+2.")
        preparar_email_vazio(data_ref)
        with open("attachment.txt", "w", encoding="utf-8") as f:
            f.write("")

def preparar_email_com_divergencia(data_ref, df_novos):
    data_formatada = data_ref.strftime("%d/%m/%Y")
    hoje = datetime.today().strftime("%d/%m/%Y")

    with open("email_subject.txt", "w", encoding="utf-8") as f:
        f.write(f"[RECHECAGEM RETROATIVA] Novos HCs detectados para {data_formatada}")

    with open("email_body.txt", "w", encoding="utf-8") as f:
        f.write(
            f"⚖️ Foram detectados {len(df_novos)} novos Habeas Corpus retroativos — "
            f"autuados originalmente em {data_formatada}, mas não detectados na primeira raspagem (D+1).\n\n"
            f"A rechecagem foi realizada hoje, {hoje}, comparando D+1 vs D+2."
        )

def preparar_email_vazio(data_ref):
    data_formatada = data_ref.strftime("%d/%m/%Y")
    hoje = datetime.today().strftime("%d/%m/%Y")

    with open("email_subject.txt", "w", encoding="utf-8") as f:
        f.write("Nenhum novo HC retroativo detectado")

    with open("email_body.txt", "w", encoding="utf-8") as f:
        f.write(
            f"Nenhum novo Habeas Corpus retroativo foi localizado no STJ com origem no TJGO, "
            f"na rechecagem realizada em {hoje} para o dia {data_formatada} "
            f"(comparação D+1 vs D+2)."
        )

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python rechecagem.py <data>")
        print("Exemplo: python rechecagem.py 02/05/2025")
        print("Nota: A data deve ser D+2 (quando a rechecagem é executada)")
        sys.exit(1)
    rechecagem_retroativa(sys.argv[1])
