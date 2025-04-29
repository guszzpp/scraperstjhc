import os
import requests
from datetime import datetime, timedelta
import pandas as pd
from supabase_download import download_from_supabase

def check_for_divergence(old_file_path, new_file_path):
    # Carregar os dois arquivos XLSX
    old_data = pd.read_excel(old_file_path)
    new_data = pd.read_excel(new_file_path)

    # Comparar as duas versões
    if not old_data.equals(new_data):
        print("Divergência detectada entre os arquivos.")
        return True
    return False

def send_email_with_attachment(subject, body, attachment_path):
    # Simulação de envio de email (você pode integrar com sua API de email)
    print(f"Enviando e-mail: {subject}")
    print(f"Corpo do email: {body}")
    print(f"Anexo: {attachment_path}")

def rechecagem():
    try:
        # Obter variáveis do ambiente
        supabase_url = os.environ['SUPABASE_URL']
        supabase_bucket = os.environ['SUPABASE_BUCKET'] # Precisa do nome do bucket

        # Calcular nomes de arquivo e caminhos
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%d-%m-%Y')
        anteontem_str = (datetime.now() - timedelta(days=2)).strftime('%d-%m-%Y')

        old_file_name = f"hc_tjgo_{anteontem_str}.xlsx"
        new_file_name = f"hc_tjgo_{yesterday_str}.xlsx"

        old_file_path = f"./dados_diarios/{old_file_name}"
        new_file_path = f"./dados_diarios/{new_file_name}"

        print(f"Tentando baixar arquivo de anteontem: {old_file_name}")
        download_from_supabase(supabase_url, supabase_bucket, old_file_name, old_file_path)

        print(f"Tentando baixar arquivo de ontem: {new_file_name}")
        download_from_supabase(supabase_url, supabase_bucket, new_file_name, new_file_path)

        # Verificar divergências (após downloads bem-sucedidos)
        if check_for_divergence(old_file_path, new_file_path):
            send_email_with_attachment(
                subject="Divergência detectada",
                body="Houve divergência entre o arquivo de ontem e o de anteontem.",
                attachment_path=new_file_path
            )
        else:
            print("Não houve divergências nos arquivos.")

    except KeyError as e:
         print(f"Erro: Variável de ambiente {e} não definida.")
         # Considerar sair com erro para o workflow falhar
         # import sys; sys.exit(1)
    except Exception as e:
        print(f"Erro durante a rechecagem: {e}")
        # Considerar sair com erro
        # import sys; sys.exit(1)

# Chamar a função de rechecagem
if __name__ == "__main__":
    rechecagem()