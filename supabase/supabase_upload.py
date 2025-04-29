import requests
import os
import time
import sys

# Carregar variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def upload_xlsx(filepath, filename_in_bucket, retries=3, delay=5):
    # Verificação se os parâmetros foram passados corretamente
    print(f"Arquivo local: {filepath}")
    print(f"Nome do arquivo no Supabase: {filename_in_bucket}")
    
    if not filepath or not filename_in_bucket:
        raise ValueError("Caminho do arquivo ou nome do arquivo no bucket não foram fornecidos.")
    
    # Verificar se as variáveis de ambiente estão configuradas corretamente
    if not SUPABASE_URL or not SUPABASE_BUCKET or not SUPABASE_KEY:
        raise ValueError("As variáveis de ambiente SUPABASE_URL, SUPABASE_BUCKET e SUPABASE_KEY não estão configuradas.")

    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename_in_bucket}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    for attempt in range(retries):
        with open(filepath, 'rb') as file:
            response = requests.put(url, headers=headers, data=file)

        if response.ok:
            print(f"Arquivo enviado com sucesso: {filename_in_bucket}")
            return response
        elif response.status_code >= 500:  # Erro 5xx, que indica problemas no servidor
            print(f"Tentativa {attempt + 1} de {retries} falhou com erro {response.status_code}. Tentando novamente...")
            time.sleep(delay)  # Espera antes de tentar novamente
        else:
            # Se não for um erro 5xx, não faz retry
            raise Exception(f"Erro ao enviar arquivo para o Supabase: {response.status_code} - {response.text}")

    raise Exception(f"Falha ao enviar arquivo após {retries} tentativas.")

# Exemplo de uso:
if __name__ == "__main__":
    try:
        # Certifique-se de passar os parâmetros na execução
        filepath = sys.argv[1]
        filename_in_bucket = sys.argv[2]
        upload_xlsx(filepath, filename_in_bucket)
    except IndexError:
        raise ValueError("Caminho do arquivo ou nome do arquivo no bucket não foram fornecidos.")
    except ValueError as e:
        print(e)