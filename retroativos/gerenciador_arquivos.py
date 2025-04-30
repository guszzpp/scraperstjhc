# retroativos/gerenciador_arquivos.py
import os
import requests
import pandas as pd
from datetime import date
from pathlib import Path
import logging
import tempfile

# Obter variáveis de ambiente
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET")

def obter_caminho_resultado_por_data(data_ref: date) -> str:
    """
    Baixa o arquivo Excel do Supabase para a data especificada.
    Retorna o caminho do arquivo temporário.
    """
    # Verifica se as variáveis de ambiente estão disponíveis
    if not all([SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET]):
        logging.error("Variáveis de ambiente do Supabase não configuradas")
        return ""
    
    # Cria diretório temporário para armazenar os arquivos baixados
    temp_dir = Path(tempfile.gettempdir()) / "scraper_stj_temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Formata a data para buscar o arquivo no Supabase
    data_fmt = data_ref.strftime("%d-%m-%Y")
    
    # Nome do arquivo no Supabase
    nome_arquivo_supabase = f"hc_tjgo_{data_fmt}.xlsx"
    
    # Caminho onde será salvo temporariamente o arquivo Excel
    caminho_excel_temp = temp_dir / nome_arquivo_supabase
    
    try:
        # URL para o arquivo no Supabase
        url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{nome_arquivo_supabase}"
        
        logging.info(f"Tentando baixar arquivo: {url}")
        
        # Baixa o arquivo
        headers = {"apikey": SUPABASE_KEY}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            # Salva o arquivo Excel localmente
            with open(caminho_excel_temp, 'wb') as f:
                f.write(response.content)
            
            logging.info(f"Arquivo {nome_arquivo_supabase} baixado com sucesso do Supabase")
            return str(caminho_excel_temp)
        else:
            logging.warning(f"Arquivo {nome_arquivo_supabase} não encontrado no Supabase. Status: {response.status_code}")
    except Exception as e:
        logging.error(f"Erro ao tentar baixar o arquivo do Supabase: {str(e)}")
    
    # Se chegou até aqui, não foi possível obter o arquivo
    return ""

def salvar_csv_resultado(df: pd.DataFrame, data_ref: date) -> str:
    """
    Salva o DataFrame como Excel no diretório de dados diários.
    Retorna o caminho do arquivo salvo.
    """
    data_fmt = data_ref.strftime("%d-%m-%Y")
    nome_arquivo = f"hc_tjgo_{data_fmt}.xlsx"
    caminho = Path("dados_diarios") / nome_arquivo
    
    # Garante que o diretório existe
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    
    # Salva o DataFrame como Excel
    df.to_excel(caminho, index=False)
    
    logging.info(f"Arquivo Excel de resultados salvo em: {caminho}")
    
    return str(caminho)
