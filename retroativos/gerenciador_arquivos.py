# retroativos/gerenciador_arquivos.py

import pandas as pd
from pathlib import Path
from datetime import datetime

PASTA_RESULTADOS = Path("dados_diarios")

def salvar_csv_resultado(df: pd.DataFrame, data_str: str) -> Path:
    """
    Salva o DataFrame na pasta de resultados usando a data_str (formato DD/MM/YYYY)
    para nomear o arquivo CSV como resultados_YYYY-MM-DD.csv.
    """
    data_obj = datetime.strptime(data_str, "%d/%m/%Y").date()
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    nome_arquivo = f"resultados_{data_obj.isoformat()}.csv"
    caminho = PASTA_RESULTADOS / nome_arquivo
    df.to_csv(caminho, index=False)
    return caminho

def obter_caminho_resultado_por_data(data_obj) -> Path:
    """
    Retorna o Path do arquivo CSV de resultados para a data fornecida.
    data_obj pode ser objeto date ou string ISO 'YYYY-MM-DD'.
    """
    if not PASTA_RESULTADOS.exists():
        PASTA_RESULTADOS.mkdir(exist_ok=True)
    if isinstance(data_obj, str):
        data_iso = data_obj
    else:
        data_iso = data_obj.isoformat()
    return PASTA_RESULTADOS / f"resultados_{data_iso}.csv"

def obter_nome_arquivo_rechecagem() -> str:
    """
    Retorna o nome do arquivo Excel gerado na rechecagem retroativa,
    no formato hc_tjgo_DD-MM-YYYY_rechecado.xlsx.
    """
    from datetime import date
    hoje = date.today().strftime("%d-%m-%Y")
    return f"hc_tjgo_{hoje}_rechecado.xlsx"
