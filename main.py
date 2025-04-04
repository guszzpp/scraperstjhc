import sys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from navegador import iniciar_navegador
from extrator import extrair_detalhes_processo
from exportador import exportar_resultados
from config import ONTEM, ORGAO_ORIGEM
from formulario import preencher_formulario
from paginador import navegar_paginas_e_extrair

def buscar_processos(data_inicial, data_final):
    driver = iniciar_navegador()
    wait = WebDriverWait(driver, 20)

    print("\n🔎 Iniciando execução...")
    preencher_formulario(driver, wait, data_inicial, data_final)

    # Coletar quantidade total de processos
    try:
        total_texto = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "clsMensagemLinha")
        )).text
        import re
        total_processos_encontrados = int(re.search(r"(\d+)", total_texto).group(1))
    except:
        total_processos_encontrados = "Não identificado"

    # Coletar quantidade de páginas (ex: "de 35 páginas")
    try:
        span = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "classSpanPaginacaoPaginaTextoInterno")
        ))
        match = re.search(r"de (\d+) página", span.text)
        numero_paginas = match.group(1) if match else "Não identificado"
    except:
        numero_paginas = "Não identificado"

    # Navegação e extração
    resultados, relatorio_paginas = navegar_paginas_e_extrair(driver, wait, extrair_detalhes_processo)
    driver.quit()

    if resultados:
        exportar_resultados(resultados, data_inicial, data_final)

    # Criar relatorio.txt
    with open("relatorio.txt", "w", encoding="utf-8") as f:
        f.write(f"📅 Data da execução: {ONTEM}\n")
        f.write("📥 Parâmetros utilizados:\n")
        f.write(f"   - Data inicial: {data_inicial}\n")
        f.write(f"   - Data final:   {data_final}\n")
        f.write(f"   - Órgão de origem: {ORGAO_ORIGEM}\n")
        f.write(f"\n🔢 Quantidade total de resultados na busca: {total_processos_encontrados}\n")
        f.write(f"📃 Total de páginas retornadas: {numero_paginas}\n")
        f.write(f"🧾 Quantidade total de HCs extraídos com sucesso: {len(resultados)}\n\n")
        f.write("📖 Status por página:\n")
        for linha in relatorio_paginas:
            f.write(f"{linha}\n")

    if not resultados:
        with open("resultados_vazio.txt", "w", encoding="utf-8") as vazio:
            vazio.write("Nenhum resultado coletado.\n")

# Execução principal
if __name__ == "__main__":
    if len(sys.argv) == 3:
        data_ini, data_fim = sys.argv[1], sys.argv[2]
    elif len(sys.argv) == 2:
        data_ini = data_fim = sys.argv[1]
    else:
        data_ini = data_fim = ONTEM

    buscar_processos(data_ini, data_fim)
    print("\n✅ Script finalizado.")
