# main.py
import sys
import re
import time
import logging
from datetime import datetime
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

from navegador import iniciar_navegador
from extrator import extrair_detalhes_processo
from exportador import exportar_resultados
from paginador import navegar_paginas_e_extrair
from formulario import preencher_formulario
from email_detalhado import gerar_corpo_email
from config import ONTEM, ORGAO_ORIGEM

logging.basicConfig(level=logging.INFO, format="%(message)s")

def buscar_processos(data_inicial, data_final):
    resultados = []
    total_resultados = 0
    total_paginas = 0
    paginas_processadas = 0
    relatorio_paginas = []
    erro_critico = None

    try:
        driver = iniciar_navegador()
        wait = WebDriverWait(driver, 15)

        print(f"🟡 Iniciando busca de HCs no STJ — {data_inicial} até {data_final}")

        preencher_formulario(driver, wait, data_inicial, data_final)

        # 🔎 Captura do total de resultados
        try:
            mensagem = wait.until(lambda d: d.find_element("class name", "clsMensagemLinha"))
            texto = mensagem.text.strip()
            match = re.search(r'(\d+)', texto)
            if match:
                total_resultados = int(match.group(1))
        except:
            print("⚠️ Não foi possível capturar o total de registros retornados.")

        print("🔍 Formulário preenchido. Iniciando navegação nas páginas de resultados...")

        resultados, relatorio_paginas = navegar_paginas_e_extrair(driver, wait, extrair_detalhes_processo, data_inicial)
        paginas_processadas = len(relatorio_paginas)
        total_paginas = paginas_processadas  # são equivalentes no modelo atual

    except (TimeoutException, WebDriverException) as e:
        erro_critico = str(e)
        print(f"❌ Erro crítico: {erro_critico}")

    except Exception as e:
        erro_critico = str(e)
        print(f"❌ Erro inesperado: {erro_critico}")

    finally:
        if 'driver' in locals():
            driver.quit()
            print("🔻 Navegador fechado.")

    if resultados:
        nome_arquivo = exportar_resultados(resultados, data_inicial, data_final)
    else:
        nome_arquivo = None
        print("\n⚠️ Nenhum dado a exportar. Nenhum arquivo será gerado.")

    if not resultados:
        print("\n⚠️ Nenhum Habeas Corpus encontrado.")
    else:
        print(f"\n📊 Total de HCs extraídos: {len(resultados)}")

    if relatorio_paginas:
        print("\n📄 Relatório de páginas processadas:")
        for linha in relatorio_paginas:
            print(f"- {linha}")
    else:
        print("\n⚠️ Nenhuma página foi processada.")

    horario_finalizacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"\n✅ Execução finalizada às {horario_finalizacao}")

    # Gera corpo do e-mail
    corpo_email = gerar_corpo_email(
        data_inicial=data_inicial,
        data_final=data_final,
        total_resultados=total_resultados,
        total_paginas=total_paginas,
        paginas_processadas=paginas_processadas,
        qtd_hcs=len(resultados),
        horario_finalizacao=horario_finalizacao,
        erro_critico=erro_critico
    )

    print("\n📝 Corpo do e-mail:\n")
    print(corpo_email)

    return corpo_email, nome_arquivo


# Execução principal
if __name__ == "__main__":
    if len(sys.argv) == 3:
        data_ini, data_fim = sys.argv[1], sys.argv[2]
    elif len(sys.argv) == 2:
        data_ini = data_fim = sys.argv[1]
    else:
        data_ini = data_fim = ONTEM

    date_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    if not date_pattern.match(data_ini) or not date_pattern.match(data_fim):
        print("❌ Formato inválido. Use DD/MM/AAAA.")
        sys.exit(1)

    buscar_processos(data_ini, data_fim)
