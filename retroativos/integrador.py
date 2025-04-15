from datetime import datetime
from pathlib import Path
import pandas as pd
from retroativos.gerenciador_arquivos import listar_arquivos_resultados, obter_data_alvo_para_rechecagem, obter_caminho_resultado_hoje
from retroativos.verificador import comparar
from main import buscar_processos, gerar_componentes_email

def verificar_e_gerar_resultado_retroativo():
    """
    Roda a rechecagem retroativa, salva resultado e prepara e-mail (com ou sem anexos).
    """
    # Descobre qual a data a ser rechecada
    data_alvo = obter_data_alvo_para_rechecagem()  # Deve retornar string "dd/mm/aaaa"
    if not data_alvo:
        print("❌ Erro ao determinar data a ser rechecada retroativamente.")
        return

    print(f"🔁 Rechecando data retroativa: {data_alvo}")

    # Executa o scraper novamente para a data-alvo
    stats = buscar_processos(data_alvo, data_alvo)

    # Renomeia o arquivo gerado para indicar que é da rechecagem
    original_path = Path(stats.get("arquivo_gerado"))
    if original_path and original_path.exists():
        rechecado_path = original_path.with_stem(original_path.stem + "_rechecado")
        original_path.rename(rechecado_path)
        stats["arquivo_gerado"] = str(rechecado_path)
        print(f"📁 Resultado da rechecagem salvo como: {rechecado_path.name}")
    else:
        print("⚠️ Nenhum arquivo gerado na rechecagem.")

    # Verifica se há diferença em relação ao arquivo anterior
    arquivos = listar_arquivos_resultados()
    if len(arquivos) < 2:
        print("⚠️ Arquivos insuficientes para comparação retroativa.")
        retroativos = None
    else:
        arquivo_ontem = arquivos[-2]
        retroativos = comparar(Path(stats["arquivo_gerado"]), arquivo_ontem)

    # Se houver diferença, exporta e anexa
    if retroativos is not None and not retroativos.empty:
        diferenca_path = Path(f"retroativo_diferenca_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.xlsx")
        retroativos.to_excel(diferenca_path, index=False)
        print(f"📎 Arquivo de diferença salvo: {diferenca_path.name}")
        stats["arquivo_gerado"] = str(diferenca_path)
    else:
        print("ℹ️ Nenhuma diferença retroativa identificada.")
        stats["arquivo_gerado"] = ""  # Não anexar nada

    # Gera e salva componentes de e-mail específicos da rechecagem
    subject, body, attachment = gerar_componentes_email(stats)
    Path("email_retroativo_subject.txt").write_text(subject, encoding='utf-8')
    Path("email_retroativo.txt").write_text(body, encoding='utf-8')

    print("📨 Componentes de e-mail da rechecagem preparados.")

if __name__ == "__main__":
    verificar_e_gerar_resultado_retroativo()
