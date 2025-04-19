from pathlib import Path
 import pandas as pd
 from datetime import date
 from typing import List
 
 PASTA_RESULTADOS = Path("dados_diarios")
 
 def listar_arquivos_resultados() -> List[Path]:
     """
     Retorna todos os arquivos de resultados disponíveis, ordenados por data.
     """
     return sorted(PASTA_RESULTADOS.glob("resultados_*.csv"))
 
 def salvar_csv_resultado(df: pd.DataFrame) -> Path:
     """
     Salva o DataFrame de resultados do dia em um novo arquivo nomeado por data.
     """
     PASTA_RESULTADOS.mkdir(exist_ok=True)
     nome_arquivo = f"resultados_{date.today().isoformat()}.csv"
     caminho = PASTA_RESULTADOS / nome_arquivo
     df.to_csv(caminho, index=False)
     return caminho
 
 def obter_caminho_resultado_hoje() -> Path:
     """
     Retorna o caminho esperado para o arquivo de hoje.
     """
     return PASTA_RESULTADOS / f"resultados_{date.today().isoformat()}.csv"
