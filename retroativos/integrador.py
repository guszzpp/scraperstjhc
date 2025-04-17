from datetime import date
from pathlib import Path
import pandas as pd

from retroativos.gerenciador_arquivos import (
    obter_caminho_resultado_hoje,
    listar_arquivos_resultados,
    obter_caminho_arquivo_rechecagem,
    obter_data_alvo_para_rechecagem,
)
from retroativos.verificador import comparar
from email_detalhado import enviar_email_alerta_novos_retroativos


def verificar_e_enviar_alerta():
    """
    Executa a lógica de verificação de processos retroativos e envia alerta por e-mail,
    independentemente de haver novos resultados. Sempre salva a planilha de rechecagem.
    """
    arquivos = listar_arquivos_resultados()

    if len(arquivos) < 2:
        print("*⚠️ Arquivos insuficientes para comparação retroativa*. ")
        print("ℹ️ Nenhuma diferença retroativa identificada.")
        enviar_email_alerta_novos_retroativos(pd.DataFrame())
        return

    arquivo_hoje = obter_caminho_resultado_hoje()
    arquivo_ontem = arquivos[-2]

    if not arquivo_hoje.exists() or not arquivo_ontem.exists():
        print("Arquivos do dia ou do dia anterior não encontrados.")
        enviar_email_alerta_novos_retroativos(pd.DataFrame())
        return

    retroativos = comparar(arquivo_hoje, arquivo_ontem)

    # Salvar sempre o resultado da rechecagem, mesmo vazio
    caminho_rechecagem = obter_caminho_arquivo_rechecagem()
    if retroativos is None or retroativos.empty:
        retroativos = pd.DataFrame()  # Garante DataFrame vazio
    retroativos.to_excel(caminho_rechecagem, index=False)
    print(f"📁 Resultado da rechecagem salvo como: {caminho_rechecagem.name}")

    if retroativos.empty:
        print("ℹ️ Nenhuma diferença retroativa identificada.")
    else:
        print(f"✅ {len(retroativos)} processos retroativos encontrados.")

    print("📨 Componentes de e-mail da rechecagem preparados.")
    enviar_email_alerta_novos_retroativos(retroativos)


if __name__ == "__main__":
    verificar_e_enviar_alerta()
