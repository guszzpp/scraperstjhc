# retroativos/executor_rechecagem.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import os
import logging
from datetime import datetime, timedelta
from retroativos.rechecagem import rechecagem_retroativa

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)

def log(msg):
    logging.info(msg)

def executar_rechecagem_automatica():
    """
    Executa a rechecagem automaticamente baseada na data atual.
    
    Fluxo:
    - Se hoje é D+2, executa rechecagem comparando D+1 vs D+2
    - Se hoje é D+1, não executa rechecagem (ainda não há D+2 para comparar)
    """
    hoje = datetime.now()
    
    # Calcular datas relevantes
    data_d1 = hoje - timedelta(days=1)  # Ontem (primeira raspagem)
    data_d2 = hoje  # Hoje (segunda raspagem)
    
    # Verificar se existe arquivo de D+1 (primeira raspagem)
    nome_data_d1 = data_d1.strftime("%d-%m-%Y")
    arquivo_d1_xlsx = f"dados_diarios/hc_tjgo_{nome_data_d1}.xlsx"
    arquivo_d1_csv = f"dados_diarios/resultados_{nome_data_d1}.csv"
    
    # Verificar se existe arquivo de D+2 (segunda raspagem)
    nome_data_d2 = data_d2.strftime("%d-%m-%Y")
    arquivo_d2_xlsx = f"dados_diarios/hc_tjgo_{nome_data_d2}.xlsx"
    arquivo_d2_csv = f"dados_diarios/resultados_{nome_data_d2}.csv"
    
    log(f"🔍 Verificando arquivos para rechecagem automática:")
    log(f"   📁 D+1 ({data_d1.strftime('%d/%m/%Y')}): {arquivo_d1_xlsx}")
    log(f"   📁 D+2 ({data_d2.strftime('%d/%m/%Y')}): {arquivo_d2_xlsx}")
    
    # Verificar se ambos os arquivos existem
    arquivo_d1_existe = os.path.exists(arquivo_d1_xlsx) or os.path.exists(arquivo_d1_csv)
    arquivo_d2_existe = os.path.exists(arquivo_d2_xlsx) or os.path.exists(arquivo_d2_csv)
    
    if not arquivo_d1_existe:
        log(f"❌ Arquivo D+1 não encontrado. Rechecagem não pode ser executada.")
        log(f"   Execute primeiro: python main.py {data_d1.strftime('%d/%m/%Y')}")
        return False
    
    if not arquivo_d2_existe:
        log(f"❌ Arquivo D+2 não encontrado. Rechecagem não pode ser executada.")
        log(f"   Execute primeiro: python main.py {data_d2.strftime('%d/%m/%Y')}")
        return False
    
    # Executar rechecagem
    log(f"🚀 Executando rechecagem retroativa para {data_d2.strftime('%d/%m/%Y')}")
    try:
        rechecagem_retroativa(data_d2.strftime("%d/%m/%Y"))
        log(f"✅ Rechecagem executada com sucesso!")
        return True
    except Exception as e:
        log(f"❌ Erro ao executar rechecagem: {e}")
        return False

def executar_rechecagem_manual(data_referencia_str):
    """
    Executa rechecagem manual para uma data específica.
    
    Args:
        data_referencia_str: Data no formato DD/MM/AAAA (deve ser D+2)
    """
    log(f"🚀 Executando rechecagem manual para {data_referencia_str}")
    try:
        rechecagem_retroativa(data_referencia_str)
        log(f"✅ Rechecagem manual executada com sucesso!")
        return True
    except Exception as e:
        log(f"❌ Erro ao executar rechecagem manual: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Execução automática
        executar_rechecagem_automatica()
    elif len(sys.argv) == 2:
        # Execução manual com data específica
        data = sys.argv[1]
        executar_rechecagem_manual(data)
    else:
        print("Uso:")
        print("  python executor_rechecagem.py                    # Execução automática")
        print("  python executor_rechecagem.py DD/MM/AAAA        # Execução manual")
        print("Exemplo: python executor_rechecagem.py 02/05/2025")
        sys.exit(1)

