import os
import requests
import sys # Importar sys se for pegar args da linha de comando aqui

def download_from_supabase(supabase_url, bucket_name, file_name, destination_path):
    """
    Baixa um arquivo do Supabase Storage.

    Args:
        supabase_url (str): A URL base do projeto Supabase (ex: https://xyz.supabase.co).
        bucket_name (str): O nome do bucket no Supabase Storage.
        file_name (str): O nome (e caminho, se houver) do arquivo dentro do bucket.
        destination_path (str): O caminho local onde salvar o arquivo.
    """
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_key:
        raise ValueError("Variável de ambiente SUPABASE_KEY não definida.")

    # --- Construção CORRETA da URL ---
    url = f"{supabase_url}/storage/v1/object/{bucket_name}/{file_name}"
    # ----------------------------------

    headers = {
        "Authorization": f"Bearer {supabase_key}",
        "apikey": supabase_key # Adicionar apikey é uma boa prática
    }

    print(f"Tentando baixar de: {url}") # Ajuda no debug
    response = requests.get(url, headers=headers, stream=True) # stream=True para arquivos maiores

    if response.status_code == 200:
        try:
            # Garante que o diretório de destino existe
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            print(f"[DEBUG] Vai salvar arquivo em: {destination_path}")
            with open(destination_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            exists = os.path.exists(destination_path)
            size = os.path.getsize(destination_path) if exists else 0
            print(f"[DEBUG] Gravação concluída: exists={exists}, size={size} bytes")
            print(f"Arquivo '{file_name}' baixado com sucesso para '{destination_path}'.")
        except Exception as e:
             raise Exception(f"Erro ao salvar o arquivo '{destination_path}': {e}")
    elif response.status_code == 404:
        print(f"Arquivo '{file_name}' não encontrado no Supabase (404). Isso pode ser esperado se não houve resultado na data.")
        sys.exit(0)
    else:
        # Imprimir mais detalhes do erro
        print(f"Erro {response.status_code} ao tentar baixar {file_name}.")
        print(f"URL tentada: {url}")
        print(f"Headers enviados (exceto Auth): {{'apikey': '***'}}")
        print(f"Resposta do servidor: {response.text}")
        raise Exception(f"Falha ao baixar arquivo {file_name}: {response.status_code}, {response.text}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Uso: python supabase_download.py <supabase_url> <bucket_name> <file_name> <destination_path>")
        sys.exit(1)
    download_from_supabase(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
