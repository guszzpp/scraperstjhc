# integrador.py

import logging
from datetime import date, timedelta
import pandas as pd
from pathlib import Path

from retroativos.gerenciador_arquivos import obter_caminho_resultado_por_data

def obter_retroativos() -> pd.DataFrame:
    """
    Compara o CSV de resultados de hoje com o de anteontem e retorna um DataFrame
    contendo apenas os HCs que aparecem em hoje mas não em anteontem.

    - Se faltar qualquer um dos arquivos, faz log de warning e retorna DataFrame vazio.
    - Se a coluna 'numero_processo' estiver ausente, faz log de error e retorna vazio.
    """
    hoje = date.today()
    anteontem = hoje - timedelta(days=2)

    caminho_hoje = obter_caminho_resultado_por_data(hoje)
    caminho_anteontem = obter_caminho_resultado_por_data(anteontem)

    # Verifica existência dos arquivos CSV
    if not Path(caminho_hoje).is_file() or not Path(caminho_anteontem).is_file():
        logging.warning(
            "⚠️ Arquivos insuficientes para comparação retroativa; "
            "não foram encontrados os arquivos para %s e/ou %s",
            anteontem.strftime('%d/%m/%Y'),
            hoje.strftime('%d/%m/%Y')
        )
        return pd.DataFrame()

    # Carrega os dados
    df_hoje = pd.read_csv(caminho_hoje)
    df_anteontem = pd.read_csv(caminho_anteontem)

    coluna = 'numero_processo'
    if coluna not in df_hoje.columns or coluna not in df_anteontem.columns:
        logging.error("Coluna '%s' não encontrada nos arquivos de comparação", coluna)
        return pd.DataFrame()

    # Identifica retroativos: processos em df_hoje que não estão em df_anteontem
    df_retroativos = (
        df_hoje[~df_hoje[coluna].isin(df_anteontem[coluna])]
        .reset_index(drop=True)
    )

    # Log do resultado
    if df_retroativos.empty:
        logging.info(
            "Nenhum HC retroativo detectado na comparação de %s com %s",
            hoje.strftime('%d/%m/%Y'),
            anteontem.strftime('%d/%m/%Y')
        )
    else:
        logging.info(
            "Foram detectados %d HCs retroativos na comparação de %s com %s",
            len(df_retroativos),
            hoje.strftime('%d/%m/%Y'),
            anteontem.strftime('%d/%m/%Y')
        )

    return df_retroativos
