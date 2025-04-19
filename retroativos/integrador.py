# retroativos/integrador.py

import logging
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path

from config import ONTEM
from retroativos.gerenciador_arquivos import obter_caminho_resultado_por_data

def obter_retroativos() -> pd.DataFrame:
    """
    Compara o CSV de resultados de ONTEM com o de anteontem e retorna um DataFrame
    contendo apenas os HCs que aparecem em ONTEM mas não em anteontem.
    """
    try:
        data_ontem = datetime.strptime(ONTEM, "%d/%m/%Y").date()
    except ValueError:
        logging.error("Formato inválido de ONTEM em config.py: %s", ONTEM)
        return pd.DataFrame()

    data_anteontem = data_ontem - timedelta(days=1)

    caminho_hoje = obter_caminho_resultado_por_data(data_ontem)
    caminho_anteontem = obter_caminho_resultado_por_data(data_anteontem)

    if not Path(caminho_hoje).is_file() or not Path(caminho_anteontem).is_file():
        logging.warning(
            "⚠️ Arquivos insuficientes para comparação retroativa; não foram encontrados "
            "os arquivos para %s e/ou %s",
            data_anteontem.strftime("%d/%m/%Y"),
            data_ontem.strftime("%d/%m/%Y"),
        )
        return pd.DataFrame()

    df_hoje = pd.read_csv(caminho_hoje)
    df_anteontem = pd.read_csv(caminho_anteontem)
    coluna = "numero_processo"

    if coluna not in df_hoje.columns or coluna not in df_anteontem.columns:
        logging.error("Coluna '%s' não encontrada nos arquivos de comparação", coluna)
        return pd.DataFrame()

    df_retroativos = (
        df_hoje[~df_hoje[coluna].isin(df_anteontem[coluna])]
        .reset_index(drop=True)
    )

    if df_retroativos.empty:
        logging.info(
            "Nenhum HC retroativo detectado na comparação de %s com %s",
            data_ontem.strftime("%d/%m/%Y"),
            data_anteontem.strftime("%d/%m/%Y"),
        )
    else:
        logging.info(
            "Foram detectados %d HCs retroativos na comparação de %s com %s",
            len(df_retroativos),
            data_ontem.strftime("%d/%m/%Y"),
            data_anteontem.strftime("%d/%m/%Y"),
        )

    return df_retroativos
