import pandas as pd
from pathlib import Path
from typing import Optional

def obter_arquivo_anterior(hoje: str, pasta: str = "dados_diarios") -> Optional[Path]:
    """
    Retorna o penúltimo arquivo de resultados, anterior ao arquivo do dia atual.
    Assumimos que os arquivos estão nomeados como: resultados_YYYY-MM-DD.csv
    """
    arquivos = sorted(Path(pasta).glob("resultados_*.csv"))
    
    if len(arquivos) < 2:
        return None

    # Retorna o penúltimo arquivo (o último deve ser o de hoje)
    return arquivos[-2]

def comparar(arquivo_hoje: Path, arquivo_ontem: Path) -> Optional[pd.DataFrame]:
    """
    Compara os dois arquivos e retorna um DataFrame com os processos que:
    - têm data de julgamento anterior ao maior valor do arquivo de ontem;
    - não estavam no arquivo de ontem.
    """
    try:
        df_hoje = pd.read_csv(arquivo_hoje, dtype=str, parse_dates=["data_julgamento"])
        df_ontem = pd.read_csv(arquivo_ontem, dtype=str, parse_dates=["data_julgamento"])
    except Exception as e:
        print(f"Erro ao ler arquivos: {e}")
        return None

    # Garantir que os campos esperados existem
    if "data_julgamento" not in df_hoje.columns or "numero_processo" not in df_hoje.columns:
        print("Colunas esperadas não encontradas nos arquivos.")
        return None

    data_limite = df_ontem["data_julgamento"].max()

    # Seleciona novos processos com data anterior
    retroativos = df_hoje[
        (df_hoje["data_julgamento"] < data_limite) &
        (~df_hoje["numero_processo"].isin(df_ontem["numero_processo"]))
    ]

    return retroativos if not retroativos.empty else None
