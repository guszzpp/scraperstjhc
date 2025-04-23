from datetime import date
from pathlib import Path

from retroativos.gerenciador_arquivos import obter_caminho_resultado_hoje, listar_arquivos_resultados
from retroativos.verificador import comparar
from email_detalhado import enviar_email_alerta_novos_retroativos  # Essa função precisa estar implementada
 
def verificar_e_enviar_alerta():
    """
    Executa a lógica de verificação de processos retroativos e envia alerta por e-mail se necessário.
    """
    arquivos = listar_arquivos_resultados()

    if len(arquivos) < 2:
        print("Ainda não há arquivos suficientes para comparação.")
        return

    arquivo_hoje = obter_caminho_resultado_hoje()
    arquivo_ontem = arquivos[-2]

    if not arquivo_hoje.exists() or not arquivo_ontem.exists():
        print("Arquivos do dia ou do dia anterior não encontrados.")
        return

    retroativos = comparar(arquivo_hoje, arquivo_ontem)

    if retroativos is None:
        print("Nenhum processo retroativo detectado.")
        return

    print(f"{len(retroativos)} processos retroativos encontrados.")
    # Chamar o módulo de envio de e-mail com DataFrame dos retroativos
    enviar_email_alerta_novos_retroativos(retroativos)

if __name__ == "__main__":
    verificar_e_enviar_alerta()
