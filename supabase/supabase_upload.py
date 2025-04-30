import requests
import os
import time
import sys
import logging
from pathlib import Path

def upload_xlsx(filepath, filename_in_bucket, retries=3, delay=5):
    """
    Faz upload de um arquivo para o Supabase Storage com retry automático.
    
    Args:
        filepath (str): Caminho local do arquivo a ser enviado.
        filename_in_bucket (str): Nome que o arquivo terá no bucket do Supabase.
        retries (int): Número máximo de tentativas em caso de falha.
        delay (int): Tempo de espera entre tentativas (segundos).
        
    Returns:
        bool: True se o upload foi bem sucedido, False caso contrário.
    """
    # Verificação se os parâmetros foram passados corretamente
    logging.info(f"📤 Preparando upload para o Supabase...")
    logging.info(f"   - Arquivo local: {filepath}")
    logging.info(f"   - Nome no bucket: {filename_in_bucket}")
    
    if not filepath or not filename_in_bucket:
        logging.error("❌ Erro: Caminho do arquivo ou nome do arquivo no bucket não foram fornecidos.")
        return False
        
    # Verificar se o arquivo existe
    if not Path(filepath).is_file():
        logging.error(f"❌ Erro: Arquivo local '{filepath}' não encontrado.")
        return False
    
    # Carregar variáveis de ambiente
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # Verificar se as variáveis de ambiente estão configuradas corretamente
    if not SUPABASE_URL or not SUPABASE_BUCKET or not SUPABASE_KEY:
        logging.error("❌ Erro: As variáveis de ambiente SUPABASE_URL, SUPABASE_BUCKET e SUPABASE_KEY não estão configuradas.")
        return False

    # Construir URL
    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename_in_bucket}"
    
    # Detectar tipo de conteúdo baseado na extensão
    content_type = "application/octet-stream"  # Padrão
    if filepath.lower().endswith(".xlsx"):
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif filepath.lower().endswith(".csv"):
        content_type = "text/csv"
    elif filepath.lower().endswith(".txt"):
        content_type = "text/plain"
    elif filepath.lower().endswith(".json"):
        content_type = "application/json"
    
    # Configurar headers
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": content_type,
    }

    # Tentativas com retry
    for attempt in range(retries):
        try:
            # Adicionar número da tentativa se não for a primeira
            if attempt > 0:
                logging.info(f"⏳ Tentativa {attempt+1}/{retries}...")
            
            # Abrir e ler o arquivo
            with open(filepath, 'rb') as file:
                file_data = file.read()
                
                # Exibir tamanho do arquivo
                file_size_kb = len(file_data) / 1024
                logging.info(f"   - Tamanho do arquivo: {file_size_kb:.2f} KB")
                
                # Fazer o request
                response = requests.put(url, headers=headers, data=file_data, timeout=60)

            # Verificar o resultado
            if response.ok:
                logging.info(f"✅ Arquivo '{filename_in_bucket}' enviado com sucesso!")
                return True
            elif response.status_code >= 500:  # Erro 5xx, que indica problemas no servidor
                logging.warning(f"⚠️ Tentativa {attempt + 1} de {retries} falhou com erro {response.status_code}.")
                
                # Tentar obter detalhes do erro
                try:
                    error_details = response.json()
                    logging.warning(f"   - Detalhes: {error_details}")
                except:
                    logging.warning(f"   - Resposta: {response.text[:200]}...")
                
                if attempt < retries - 1:
                    logging.info(f"⏳ Aguardando {delay}s antes da próxima tentativa...")
                    time.sleep(delay)
                else:
                    logging.error(f"❌ Todas as tentativas falharam com erro de servidor.")
                    return False
            else:
                # Se não for um erro 5xx, obtém mais informações
                logging.error(f"❌ Erro {response.status_code} ao enviar arquivo para o Supabase.")
                
                # Tentar obter detalhes do erro
                try:
                    error_details = response.json()
                    logging.error(f"   - Detalhes: {error_details}")
                except:
                    logging.error(f"   - Resposta: {response.text[:200]}...")
                
                # Verificar casos especiais
                if response.status_code == 401 or response.status_code == 403:
                    logging.error("❌ Erro de autenticação. Verifique a chave de API do Supabase.")
                    return False
                elif response.status_code == 404:
                    logging.error(f"❌ Bucket '{SUPABASE_BUCKET}' não encontrado.")
                    return False
                elif response.status_code == 409:
                    logging.warning(f"⚠️ O arquivo '{filename_in_bucket}' já existe no bucket.")
                    
                    # Tentar upsert (deletar e recriar)
                    logging.info("🔄 Tentando substituir o arquivo existente...")
                    
                    # Excluir o arquivo existente
                    delete_url = url
                    delete_response = requests.delete(delete_url, headers=headers)
                    
                    if delete_response.ok:
                        logging.info("✅ Arquivo existente excluído. Tentando upload novamente...")
                        
                        # Novo upload
                        with open(filepath, 'rb') as file:
                            upload_response = requests.put(url, headers=headers, data=file.read())
                            
                        if upload_response.ok:
                            logging.info(f"✅ Arquivo '{filename_in_bucket}' substituído com sucesso!")
                            return True
                        else:
                            logging.error(f"❌ Falha ao reenviar após exclusão. Código: {upload_response.status_code}")
                    else:
                        logging.error(f"❌ Falha ao excluir arquivo existente. Código: {delete_response.status_code}")
                
                # Se não for um caso especial e não for a última tentativa, tenta novamente
                if attempt < retries - 1:
                    logging.info(f"⏳ Aguardando {delay}s antes da próxima tentativa...")
                    time.sleep(delay)
                else:
                    logging.error(f"❌ Falha ao enviar arquivo após {retries} tentativas.")
                    return False
                    
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Erro de conexão: {str(e)}")
            
            if attempt < retries - 1:
                logging.info(f"⏳ Aguardando {delay}s antes da próxima tentativa...")
                time.sleep(delay)
            else:
                logging.error(f"❌ Falha após {retries} tentativas devido a erros de conexão.")
                return False
        except Exception as e:
            logging.error(f"❌ Erro inesperado: {str(e)}")
            
            if attempt < retries - 1:
                logging.info(f"⏳ Aguardando {delay}s antes da próxima tentativa...")
                time.sleep(delay)
            else:
                logging.error(f"❌ Falha após {retries} tentativas devido a erros inesperados.")
                return False

    # Se chegou aqui sem retornar, é porque todas as tentativas falharam
    return False

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Verificar argumentos da linha de comando
    if len(sys.argv) < 3:
        logging.error("❌ Erro: Argumentos insuficientes.")
        print("Uso: python supabase_upload.py <filepath> <filename_in_bucket>")
        sys.exit(1)
    
    try:
        filepath = sys.argv[1]
        filename_in_bucket = sys.argv[2]
        
        sucesso = upload_xlsx(filepath, filename_in_bucket)
        sys.exit(0 if sucesso else 1)
        
    except ValueError as e:
        logging.error(f"❌ Erro de valor: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"❌ Erro inesperado: {e}")
        sys.exit(1)