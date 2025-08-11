# retroativos/rechecagem_simples.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import os
import csv
from datetime import datetime, timedelta
import logging

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)

def log(msg):
    logging.info(msg)

def carregar_csv(path):
    """Carrega arquivo CSV sem pandas"""
    try:
        dados = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                dados.append(row)
        return dados
    except Exception as e:
        log(f"Erro ao carregar {path}: {e}")
        return []

def rechecagem_simples(data_referencia_str):
    """
    Versão simplificada da rechecagem que não depende de pandas
    """
    data_ref = datetime.strptime(data_referencia_str, "%d/%m/%Y")
    nome_data = data_ref.strftime("%d-%m-%Y")
    
    # Data de D+1 (primeira raspagem)
    data_d1 = data_ref - timedelta(days=1)
    nome_data_d1 = data_d1.strftime("%d-%m-%Y")
    
    # Caminhos dos arquivos CSV
    arquivo_d1_csv = f"dados_diarios/resultados_{nome_data_d1}.csv"
    arquivo_d2_csv = f"dados_diarios/resultados_{nome_data}.csv"
    
    log(f"🔍 Iniciando rechecagem simples para {data_referencia_str}")
    log(f"📁 Arquivo D+1: {arquivo_d1_csv}")
    log(f"📁 Arquivo D+2: {arquivo_d2_csv}")
    
    # 1. Carregar arquivo de D+1
    dados_d1 = []
    if os.path.exists(arquivo_d1_csv):
        dados_d1 = carregar_csv(arquivo_d1_csv)
        log(f"✅ Arquivo D+1 carregado: {len(dados_d1)} registros")
    else:
        log(f"❌ Arquivo D+1 não encontrado: {arquivo_d1_csv}")
    
    # 2. Carregar arquivo de D+2
    dados_d2 = []
    if os.path.exists(arquivo_d2_csv):
        dados_d2 = carregar_csv(arquivo_d2_csv)
        log(f"✅ Arquivo D+2 carregado: {len(dados_d2)} registros")
    else:
        log(f"❌ Arquivo D+2 não encontrado: {arquivo_d2_csv}")
    
    # 3. Verificar se ambos os arquivos estão vazios
    if not dados_d1 and not dados_d2:
        log("⚠️ Ambos os arquivos estão vazios. Nenhum HC detectado.")
        preparar_email_vazio_simples(data_ref)
        with open("attachment.txt", "w", encoding="utf-8") as f:
            f.write("")
        return
    
    # 4. Identificar coluna de número do processo
    coluna_processo = None
    if dados_d1 and dados_d2:
        for col in ["numero_processo", "numero_cnj", "Número do Processo", "processo"]:
            if col in dados_d1[0] and col in dados_d2[0]:
                coluna_processo = col
                break
    elif dados_d2:
        # Se só temos dados_d2, usar a primeira coluna disponível
        for col in ["numero_processo", "numero_cnj", "Número do Processo", "processo"]:
            if col in dados_d2[0]:
                coluna_processo = col
                break
    
    if not coluna_processo:
        log("❌ Coluna de número do processo não encontrada")
        preparar_email_vazio_simples(data_ref)
        with open("attachment.txt", "w", encoding="utf-8") as f:
            f.write("")
        return
    
    # 5. Identificar novos HCs
    processos_d1 = set(d[coluna_processo] for d in dados_d1)
    processos_d2 = set(d[coluna_processo] for d in dados_d2)
    
    novos_hcs = [d for d in dados_d2 if d[coluna_processo] not in processos_d1]
    hcs_removidos = [d for d in dados_d1 if d[coluna_processo] not in processos_d2]
    
    # 6. Gerar relatório
    tem_divergencia = novos_hcs or hcs_removidos
    
    log(f"📊 Resultados da rechecagem:")
    log(f"   - Novos HCs: {len(novos_hcs)}")
    log(f"   - HCs removidos: {len(hcs_removidos)}")
    
    if tem_divergencia:
        log("🚨 Divergências detectadas!")
        
        if novos_hcs:
            log(f"   📄 Salvando {len(novos_hcs)} novos HCs retroativos")
            # Salvar como CSV simples
            with open("novos_retroativos.csv", "w", encoding="utf-8", newline="") as f:
                if novos_hcs:
                    writer = csv.DictWriter(f, fieldnames=novos_hcs[0].keys())
                    writer.writeheader()
                    writer.writerows(novos_hcs)
        
        if hcs_removidos:
            log(f"   📄 Salvando {len(hcs_removidos)} HCs removidos")
            with open("hcs_removidos.csv", "w", encoding="utf-8", newline="") as f:
                if hcs_removidos:
                    writer = csv.DictWriter(f, fieldnames=hcs_removidos[0].keys())
                    writer.writeheader()
                    writer.writerows(hcs_removidos)
        
        preparar_email_com_divergencia_simples(data_ref, novos_hcs)
        with open("attachment.txt", "w", encoding="utf-8") as f:
            f.write("novos_retroativos.csv" if novos_hcs else "")
    else:
        log("✅ Nenhuma divergência detectada. Todos os HCs são consistentes entre D+1 e D+2.")
        preparar_email_vazio_simples(data_ref)
        with open("attachment.txt", "w", encoding="utf-8") as f:
            f.write("")

def preparar_email_com_divergencia_simples(data_ref, novos_hcs):
    data_formatada = data_ref.strftime("%d/%m/%Y")
    hoje = datetime.today().strftime("%d/%m/%Y")

    with open("email_subject.txt", "w", encoding="utf-8") as f:
        f.write(f"[RECHECAGEM RETROATIVA] Novos HCs detectados para {data_formatada}")

    with open("email_body.txt", "w", encoding="utf-8") as f:
        f.write(
            f"⚖️ Foram detectados {len(novos_hcs)} novos Habeas Corpus retroativos — "
            f"autuados originalmente em {data_formatada}, mas não detectados na primeira raspagem (D+1).\n\n"
            f"A rechecagem foi realizada hoje, {hoje}, comparando D+1 vs D+2."
        )

def preparar_email_vazio_simples(data_ref):
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
        print("Uso: python rechecagem_simples.py <data>")
        print("Exemplo: python rechecagem_simples.py 02/05/2025")
        print("Nota: A data deve ser D+2 (quando a rechecagem é executada)")
        sys.exit(1)
    rechecagem_simples(sys.argv[1])
