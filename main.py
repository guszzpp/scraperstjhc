# main.py
import sys
import re
import time
import logging
from datetime import datetime
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from pathlib import Path # Usar Path para lidar com arquivos
from textwrap import dedent # Útil para strings multi-linhas
# import math # Removido, pois não usamos mais math.ceil

# Certifique-se que os outros arquivos .py estão na mesma pasta
from navegador import iniciar_navegador
from extrator import extrair_detalhes_processo
from exportador import exportar_resultados
from paginador import navegar_paginas_e_extrair
from formulario import preencher_formulario
from config import ONTEM, ORGAO_ORIGEM, URL_PESQUISA

# Configuração do Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout) # Garante output no console/log do Actions
    ]
)

# --- Função buscar_processos (COM AJUSTE FINO NA CONTAGEM DE PÁGINAS) ---
def buscar_processos(data_inicial, data_final):
    """
    Executa o fluxo de busca e retorna estatísticas e nome do arquivo gerado.
    """
    resultados = []
    total_resultados_site = -1 # -1 indica que não foi possível obter ou erro
    total_paginas_calculado = 0 # Será baseado nas páginas processadas
    paginas_processadas = 0
    relatorio_paginas = []
    erro_critico = None
    nome_arquivo_gerado = None
    driver = None # Inicializa driver como None
    horario_inicio = datetime.now()

    logging.info(f"🟡 Iniciando busca de HCs no STJ — {data_inicial} até {data_final}")
    logging.info(f"   URL: {URL_PESQUISA}")
    logging.info(f"   Órgão Origem: {ORGAO_ORIGEM}")

    try:
        driver = iniciar_navegador()
        wait = WebDriverWait(driver, 20) # Aumentar wait pode ajudar

        preencher_formulario(driver, wait, data_inicial, data_final)
        logging.info("✅ Formulário preenchido.")

        # Espera pela mensagem OU pela lista como indicador de carga
        wait.until(lambda d: d.find_element(By.CLASS_NAME, "clsMensagemLinha") or d.find_element(By.CLASS_NAME, "clsListaProcessoFormatoVerticalLinha"))
        time.sleep(1) # Pequena pausa

        # Captura do total de resultados (opcional, trata erro)
        try:
            mensagem = driver.find_element(By.CLASS_NAME, "clsMensagemLinha")
            texto = mensagem.text.strip()
            match = re.search(r'(\d+)', texto)
            if match:
                total_resultados_site = int(match.group(1))
                logging.info(f"📊 Site reportou {total_resultados_site} resultados totais.")
            else:
                 logging.warning(f"⚠️ Não foi possível extrair número da mensagem: '{texto}'")
                 # Se não achou número, mas há resultados, total é desconhecido mas > 0
                 if driver.find_elements(By.CLASS_NAME, "clsListaProcessoFormatoVerticalLinha"):
                     total_resultados_site = -2 # Indica desconhecido mas > 0
                     logging.info("Número não extraído da msg, mas blocos de resultados encontrados.")
                 else:
                     total_resultados_site = 0 # Realmente não achou nada
                     logging.info("Nenhuma mensagem de contagem e nenhum bloco de resultados encontrado inicialmente.")
        except NoSuchElementException: # Se o elemento da mensagem não for encontrado
            logging.warning(f"ℹ️ Elemento clsMensagemLinha não encontrado.")
            # Verifica se há resultados mesmo sem a mensagem
            try:
                 if driver.find_elements(By.CLASS_NAME, "clsListaProcessoFormatoVerticalLinha"):
                      total_resultados_site = -2 # Indica desconhecido mas > 0
                      logging.info("Msg não encontrada, mas blocos de resultados encontrados.")
                 else:
                     total_resultados_site = 0 # Realmente não achou nada
                     logging.info("Nenhuma mensagem de contagem e nenhum bloco de resultados encontrado.")
            except Exception as e_check: # Captura qualquer erro aqui também
                 total_resultados_site = 0
                 logging.warning(f"Erro ao verificar blocos de resultados após falha na leitura da mensagem: {e_check}")
        except Exception as e: # Captura outros erros ao tentar ler a mensagem
            logging.warning(f"ℹ️ Não foi possível capturar o total de registros da mensagem (erro geral): {e}")
            total_resultados_site = -1 # Indica erro/não obtido


        # Inicializa contagens antes da navegação
        paginas_processadas = 0
        total_paginas_calculado = 0

        # Só navega se o site indicou resultados ou status desconhecido (>0 ou -2)
        # Se for -1 (erro ao obter), ainda tenta navegar por precaução
        if total_resultados_site != 0:
             logging.info("🔍 Iniciando navegação (se houver páginas)...")
             resultados, relatorio_paginas = navegar_paginas_e_extrair(driver, wait, extrair_detalhes_processo, data_inicial)

             # Lógica refinada para contagem de páginas baseada nas iterações reais do paginador
             paginas_loop_iterations = len(relatorio_paginas) # Quantas vezes o loop WHILE rodou

             if paginas_loop_iterations == 0 and total_resultados_site != 0:
                 # Caso estranho: esperava resultados, mas paginador não rodou o loop?
                 # Pode acontecer se a primeira página carregar mas não tiver blocos ou botão próximo
                 # Se encontrou HCs, considera 1 página. Senão, 0.
                 if len(resultados) > 0:
                      paginas_processadas = 1
                      total_paginas_calculado = 1
                      logging.warning("Paginador não gerou relatórios, mas HCs foram encontrados. Reportando 1 página.")
                 else:
                      paginas_processadas = 0
                      total_paginas_calculado = 0
                      logging.warning("Paginador não gerou relatórios, apesar de resultados esperados/desconhecidos. Reportando 0 páginas.")
             elif paginas_loop_iterations == 1:
                 # Loop rodou apenas uma vez = Só a primeira página foi relevante.
                 paginas_processadas = 1
                 total_paginas_calculado = 1
                 logging.info(f"Loop do paginador executado 1 vez. Páginas reportadas: {paginas_processadas} de {total_paginas_calculado}")
             elif paginas_loop_iterations > 1:
                 # Loop rodou mais de uma vez = Clicou em "Próximo" pelo menos uma vez.
                 paginas_processadas = paginas_loop_iterations
                 total_paginas_calculado = paginas_loop_iterations # O total é o número de iterações
                 logging.info(f"Loop do paginador executado {paginas_loop_iterations} vezes. Páginas reportadas: {paginas_processadas} de {total_paginas_calculado}")
             # else: # paginas_loop_iterations == 0 e total_resultados_site era 0 (implícito)
                 # paginas_processadas e total_paginas_calculado permanecem 0 (definidos antes do if)

        else: # Caso total_resultados_site == 0
             logging.info("Site reportou 0 resultados. Nenhuma página será processada.")
             paginas_processadas = 0
             total_paginas_calculado = 0
        # Fim da lógica de navegação e contagem de páginas

    except TimeoutException as e:
        erro_critico = f"Timeout ({type(e).__name__}): {str(e)}"
        logging.error(f"❌ Erro crítico (Timeout): {erro_critico}", exc_info=True)
    except WebDriverException as e:
         erro_critico = f"WebDriver Error ({type(e).__name__}): {str(e)}"
         logging.error(f"❌ Erro crítico (WebDriver): {erro_critico}", exc_info=True)
    except Exception as e:
        erro_critico = f"Erro Inesperado ({type(e).__name__}): {str(e)}"
        logging.error(f"❌ Erro inesperado: {erro_critico}", exc_info=True)

    finally:
        if driver:
            try:
                driver.quit()
                logging.info("🔻 Navegador fechado.")
            except Exception as e:
                logging.warning(f"⚠️ Erro ao fechar navegador: {e}")

    qtd_hcs_extraidos = len(resultados)

    if resultados:
        logging.info(f"📊 Total de HCs extraídos: {qtd_hcs_extraidos}")
        try:
            nome_arquivo_gerado = exportar_resultados(resultados, data_inicial, data_final)
        except Exception as e:
             logging.error(f"❌ Erro ao exportar resultados para Excel: {e}")
             erro_critico = erro_critico or f"Erro ao exportar Excel: {e}"
    elif not erro_critico:
        logging.info("✅ Nenhum Habeas Corpus encontrado ou extraído com sucesso.")
    else:
         logging.warning("⚠️ Extração interrompida por erro, nenhum HC foi extraído.")

    if relatorio_paginas:
        logging.info("📄 Relatório de páginas processadas:")
        for linha in relatorio_paginas:
            logging.info(f"   - {linha}")
    # Condição ligeiramente ajustada para logar ausência de páginas processadas
    elif not erro_critico and total_paginas_calculado == 0 and total_resultados_site != 0:
         logging.warning("⚠️ Nenhuma página foi efetivamente processada (apesar de resultados esperados/desconhecidos).")
    elif not erro_critico and total_resultados_site == 0:
         pass # Não avisa se 0 resultados era esperado

    horario_finalizacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    duracao = (datetime.now() - horario_inicio).total_seconds()
    logging.info(f"✅ Execução finalizada às {horario_finalizacao} (Duração: {duracao:.2f}s)")

    # Compila as estatísticas
    stats = {
        "data_inicial": data_inicial,
        "data_final": data_final,
        "orgao_origem": ORGAO_ORIGEM,
        "qtd_resultados_site": str(total_resultados_site) if total_resultados_site >= 0 else "Desconhecido (>0)" if total_resultados_site == -2 else "Erro/Não obtido",
        "qtd_hcs": qtd_hcs_extraidos,
        "paginas_total": total_paginas_calculado, # Usa a variável ajustada
        "paginas_processadas": paginas_processadas, # Usa a variável ajustada
        "horario_finalizacao": horario_finalizacao,
        "duracao_segundos": round(duracao, 2),
        "erro_critico": erro_critico,
        "arquivo_gerado": nome_arquivo_gerado # Nome do .xlsx ou None
    }

    return stats # Retorna apenas o dicionário de estatísticas

# --- Função para gerar componentes do e-mail ---
def gerar_componentes_email(stats):
    """
    Gera o assunto, corpo e nome do anexo do e-mail com base nas estatísticas.
    """
    # Extrai dados das estatísticas com valores padrão seguros
    erro = stats.get("erro_critico")
    data_ini = stats.get("data_inicial", "N/A")
    data_fim = stats.get("data_final", "N/A")
    orgao = stats.get("orgao_origem", "N/A")
    qtd_site = stats.get("qtd_resultados_site", "?")
    qtd_hcs = stats.get("qtd_hcs", 0)
    pags_total = stats.get("paginas_total", 0) # Pega o valor ajustado
    pags_ok = stats.get("paginas_processadas", 0) # Pega o valor ajustado
    horario = stats.get("horario_finalizacao", "N/A")
    duracao = stats.get("duracao_segundos", "?")
    arquivo_gerado = stats.get("arquivo_gerado") # Pode ser None

    subject = ""
    body = ""
    attachment_name = "" # Vazio por padrão

    gha_link_text = "" # Mantido vazio

    # Lógica para definir Subject, Body e Attachment Name
    if erro:
        # CENÁRIO 1: Erro crítico
        subject = f"❌ ERRO no Scraper STJ - {data_ini}"
        body = dedent(f"""\
            Prezado(a),

            Ocorreu um erro crítico durante a execução do scraper de HCs no STJ (origem {orgao}) para o período de {data_ini} a {data_fim}.

            O erro reportado pelo script foi:
            {erro}

            Detalhes da execução (podem estar incompletos):
            - Resultados encontrados pelo site: {qtd_site}
            - HCs efetivamente extraídos: {qtd_hcs}
            - Páginas processadas: {pags_ok} de {pags_total}
            - Script finalizado em: {horario} (Duração: {duracao}s)

            Nenhum relatório em anexo devido ao erro.

            Recomenda-se verificar manualmente no site do STJ:
            {URL_PESQUISA}

            {gha_link_text}

            Atenciosamente,
            Sistema automatizado
        """)
        attachment_name = ""

    elif qtd_hcs > 0 and arquivo_gerado and Path(arquivo_gerado).is_file():
        # CENÁRIO 2: Sucesso com HCs e arquivo existe
        subject = f"✅ Relatório HCs STJ (Origem {orgao}) - {data_ini}"
        body = dedent(f"""\
            Prezado(a),

            Segue em anexo o relatório de Habeas Corpus (HCs) autuados no STJ, com origem no {orgao}, referente ao período de {data_ini} a {data_fim}.

            Resumo da execução:
            - Resultados encontrados pelo site: {qtd_site}
            - HCs efetivamente extraídos: {qtd_hcs} (detalhes no anexo)
            - Páginas processadas: {pags_ok} de {pags_total}
            - Script finalizado em: {horario} (Duração: {duracao}s)

            O arquivo '{arquivo_gerado}' está anexado a este e-mail.

            Esta automação tem como objetivo auxiliar no acompanhamento processual, mas **não substitui a conferência manual nos canais oficiais do STJ**.

            {gha_link_text}

            Atenciosamente,
            Sistema automatizado
        """)
        attachment_name = arquivo_gerado

    else:
        # CENÁRIO 3: Sucesso sem HCs ou arquivo não gerado/encontrado
        subject = f"ℹ️ Nenhum HC encontrado STJ (Origem {orgao}) - {data_ini}"
        body = dedent(f"""\
            Prezado(a),

            Nenhum Habeas Corpus (HC) com origem no {orgao} foi localizado ou extraído com sucesso no STJ para o período de {data_ini} a {data_fim}.

            Resumo da execução:
            - Resultados encontrados pelo site: {qtd_site}
            - HCs efetivamente extraídos: {qtd_hcs}
            - Páginas processadas: {pags_ok} de {pags_total}
            - Script finalizado em: {horario} (Duração: {duracao}s)

            Nenhum arquivo foi gerado ou anexado.

            Esta automação tem como objetivo auxiliar no acompanhamento processual, mas **não substitui a conferência manual nos canais oficiais do STJ**.

            {gha_link_text}

            Atenciosamente,
            Sistema automatizado
        """)
        attachment_name = ""

    return subject, body, (attachment_name or "") # Garante string vazia se for None

# --- Execução Principal ---
if __name__ == "__main__":
    # Validação de argumentos e datas (sem alterações)
    if len(sys.argv) == 3:
        data_ini_arg, data_fim_arg = sys.argv[1], sys.argv[2]
        logging.info(f"Datas recebidas via argumento: INI={data_ini_arg}, FIM={data_fim_arg}")
    elif len(sys.argv) == 2:
        data_ini_arg = data_fim_arg = sys.argv[1]
        logging.info(f"Data recebida via argumento: {data_ini_arg}")
    else:
        data_ini_arg = data_fim_arg = ONTEM
        logging.info(f"Nenhuma data fornecida, usando data padrão (ontem): {ONTEM}")

    date_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    if not date_pattern.match(data_ini_arg) or not date_pattern.match(data_fim_arg):
        logging.error(f"❌ Formato de data inválido. Recebido: INI='{data_ini_arg}', FIM='{data_fim_arg}'. Use DD/MM/AAAA.")
        error_stats = {
            "data_inicial": data_ini_arg, "data_final": data_fim_arg, "orgao_origem": ORGAO_ORIGEM,
            "horario_finalizacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "erro_critico": "Formato de data inválido recebido nos argumentos."
        }
        email_subject, email_body, email_attachment = gerar_componentes_email(error_stats)
        try:
            Path("email_subject.txt").write_text(email_subject, encoding='utf-8')
            Path("email_body.txt").write_text(email_body, encoding='utf-8')
            Path("attachment.txt").write_text(email_attachment, encoding='utf-8')
            logging.info("ℹ️ Componentes de e-mail de erro (data inválida) salvos.")
        except Exception as e_write:
            logging.error(f"⚠️ Erro crítico ao salvar arquivos de e-mail de erro de data: {e_write}")
        sys.exit(1) # Sai com erro

    # Chama a função principal para obter as estatísticas
    execution_stats = buscar_processos(data_ini_arg, data_fim_arg)

    # Gera os componentes do e-mail a partir das estatísticas
    logging.info("⚙️ Gerando componentes do e-mail...")
    email_subject, email_body, email_attachment = gerar_componentes_email(execution_stats)

    # Salva os componentes em arquivos de texto
    try:
        Path("email_subject.txt").write_text(email_subject, encoding='utf-8')
        logging.info(f"✅ Assunto do e-mail salvo em email_subject.txt")

        Path("email_body.txt").write_text(email_body, encoding='utf-8')
        logging.info(f"✅ Corpo do e-mail salvo em email_body.txt")

        Path("attachment.txt").write_text(email_attachment, encoding='utf-8')
        logging.info(f"✅ Nome do anexo salvo em attachment.txt (conteúdo: '{email_attachment}')")

    except Exception as e_write:
        logging.error(f"❌ Erro crítico ao salvar arquivos de componentes do e-mail: {e_write}")
        # Se não conseguir salvar os arquivos, o workflow não terá os dados.
        sys.exit(1) # Sai com erro para indicar falha grave

    # Verifica se houve erro crítico durante a busca para definir o status final
    if execution_stats.get("erro_critico"):
       logging.error("Finalizando com status de erro devido a erro crítico durante a execução.")
       sys.exit(1)
    else:
         logging.info("Finalizando com status de sucesso.")
         sys.exit(0) # Sai com sucesso
