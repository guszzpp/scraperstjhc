# main.py
import sys
import re
import time
import logging
from datetime import datetime
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException # <<< ADIÇÃO >>> (Para verificar elementos)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By # <<< ADIÇÃO >>> (Necessário para By.CLASS_NAME)
from pathlib import Path # Usar Path para lidar com arquivos
from textwrap import dedent # Útil para strings multi-linhas
import math # <<< ADIÇÃO >>>

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

# --- Função buscar_processos (COM ALTERAÇÕES) ---
def buscar_processos(data_inicial, data_final):
    """
    Executa o fluxo de busca e retorna estatísticas e nome do arquivo gerado.
    """
    resultados = []
    total_resultados_site = -1 # -1 indica que não foi possível obter
    # total_paginas = 0 # <<< REMOÇÃO >>>
    total_paginas_calculado = 0 # <<< ADIÇÃO >>>
    paginas_processadas = 0
    resultados_por_pagina = 0 # <<< ADIÇÃO >>>
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

        # <<< ALTERAÇÃO/ADIÇÃO >>> Bloco inteiro para obter total_resultados_site com mais robustez
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
                 # Verifica se há blocos de resultados para confirmar
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
            # Tenta verificar os blocos como fallback
            try:
                 if driver.find_elements(By.CLASS_NAME, "clsListaProcessoFormatoVerticalLinha"):
                      total_resultados_site = -2 # Indica desconhecido mas > 0
                      logging.info("Erro na msg, mas blocos de resultados encontrados.")
                 else:
                     total_resultados_site = 0
                     logging.info("Erro na msg e nenhum bloco de resultados encontrado.")
            except Exception as e_check2:
                 total_resultados_site = 0
                 logging.warning(f"Erro ao verificar blocos de resultados como fallback: {e_check2}")


        # <<< ALTERAÇÃO/ADIÇÃO >>> Lógica de cálculo de páginas movida para após a navegação
        if total_resultados_site != 0: # Só navega se houver ou puder haver resultados
             logging.info("🔍 Iniciando navegação nas páginas de resultados...")
             resultados, relatorio_paginas = navegar_paginas_e_extrair(driver, wait, extrair_detalhes_processo, data_inicial)
             paginas_processadas = len(relatorio_paginas)

             # <<< ALTERAÇÃO/ADIÇÃO >>> Tenta calcular resultados por página
             if relatorio_paginas:
                 primeiro_relatorio = relatorio_paginas[0]
                 match_blocos = re.search(r'(\d+)\s+blocos\s+analisados', primeiro_relatorio)
                 if match_blocos:
                     resultados_por_pagina = int(match_blocos.group(1))
                     # Evita RPP 0 se a primeira página não tiver blocos por algum motivo
                     if resultados_por_pagina == 0 and total_resultados_site > 0:
                         resultados_por_pagina = 10 # Assume um padrão se blocos for 0
                         logging.warning(f"⚠️ Primeira página reportou 0 blocos. Usando RPP padrão ({resultados_por_pagina}).")
                     elif resultados_por_pagina > 0:
                         logging.info(f"🔢 Resultados por página (baseado na pág 1): {resultados_por_pagina}")
                     # Se resultados_por_pagina ainda for 0, será tratado abaixo
                 else:
                     logging.warning(f"⚠️ Não foi possível extrair contagem de blocos do relatório: '{primeiro_relatorio}'")
                     # Fallback se não conseguir extrair (usando qtd_hcs que será calculado depois)
                     qtd_hcs_temp = len(resultados) # Pega a contagem atual de HCs
                     if paginas_processadas == 1 and qtd_hcs_temp > 0:
                          resultados_por_pagina = qtd_hcs_temp
                          logging.warning(f"⚠️ Usando HCs extraídos ({resultados_por_pagina}) como RPP (fallback).")
                     elif total_resultados_site > 0: # Se sabe que tem resultado, chuta um valor
                          resultados_por_pagina = 10 # Último recurso: chutar um valor comum
                          logging.warning(f"⚠️ Usando RPP padrão ({resultados_por_pagina}).")
                     # Se resultados_por_pagina for 0, o cálculo do total não funcionará, ok.

             # <<< ALTERAÇÃO/ADIÇÃO >>> Calcular total de páginas real
             if total_resultados_site > 0 and resultados_por_pagina > 0:
                 total_paginas_calculado = math.ceil(total_resultados_site / resultados_por_pagina)
                 logging.info(f"🔢 Total de páginas calculado: {total_paginas_calculado}")
             elif total_resultados_site == -2 and paginas_processadas > 0:
                 total_paginas_calculado = paginas_processadas # Melhor estimativa possível
                 logging.warning(f"⚠️ Total de resultados desconhecido. Total de páginas = páginas processadas ({total_paginas_calculado}).")
             elif total_resultados_site == -2 and paginas_processadas == 0 and len(resultados) > 0:
                 total_paginas_calculado = 1
                 logging.warning("⚠️ Total de resultados/páginas desconhecido, mas HCs foram encontrados. Assumindo 1 página.")
             else:
                 # Se total_resultados_site for 0 ou -1, e não processou páginas
                 total_paginas_calculado = 0

        else: # Caso total_resultados_site == 0
             logging.info("Site reportou 0 resultados. Nenhuma página será processada.")
             paginas_processadas = 0
             total_paginas_calculado = 0
        # Fim do bloco if total_resultados_site != 0

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

    # Este cálculo agora pode usar o fallback de RPP calculado anteriormente
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
    elif not erro_critico and total_resultados_site != 0: # Só avisa se esperava páginas
        logging.info("⚠️ Nenhuma página foi processada (apesar de resultados esperados?).")
    elif not erro_critico and total_resultados_site == 0:
         pass # Não avisa se 0 resultados era esperado


    horario_finalizacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    duracao = (datetime.now() - horario_inicio).total_seconds()
    logging.info(f"✅ Execução finalizada às {horario_finalizacao} (Duração: {duracao:.2f}s)")

    # Compila as estatísticas (COM ALTERAÇÕES)
    stats = {
        "data_inicial": data_inicial,
        "data_final": data_final,
        "orgao_origem": ORGAO_ORIGEM,
        # <<< ALTERAÇÃO >>> Melhor descrição para qtd_resultados_site
        "qtd_resultados_site": str(total_resultados_site) if total_resultados_site >= 0 else "Desconhecido (>0)" if total_resultados_site == -2 else "Erro/Não obtido",
        "qtd_hcs": qtd_hcs_extraidos,
        # <<< ALTERAÇÃO >>> Usa a variável calculada
        "paginas_total": total_paginas_calculado,
        "paginas_processadas": paginas_processadas,
        "horario_finalizacao": horario_finalizacao,
        "duracao_segundos": round(duracao, 2),
        "erro_critico": erro_critico,
        "arquivo_gerado": nome_arquivo_gerado # Nome do .xlsx ou None
    }

    return stats # Retorna apenas o dicionário de estatísticas

# --- Função para gerar componentes do e-mail (COM ALTERAÇÕES) ---
def gerar_componentes_email(stats):
    """
    Gera o assunto, corpo e nome do anexo do e-mail com base nas estatísticas.
    """
    # Extrai dados das estatísticas com valores padrão seguros
    erro = stats.get("erro_critico")
    data_ini = stats.get("data_inicial", "N/A")
    data_fim = stats.get("data_final", "N/A")
    orgao = stats.get("orgao_origem", "N/A")
    qtd_site = stats.get("qtd_resultados_site", "?") # Já vem formatado de 'stats'
    qtd_hcs = stats.get("qtd_hcs", 0)
    pags_total = stats.get("paginas_total", 0) # Pega o valor calculado de 'stats'
    pags_ok = stats.get("paginas_processadas", 0)
    horario = stats.get("horario_finalizacao", "N/A")
    duracao = stats.get("duracao_segundos", "?")
    arquivo_gerado = stats.get("arquivo_gerado") # Pode ser None

    subject = ""
    body = ""
    attachment_name = "" # Vazio por padrão

    gha_link_text = "" # Mantido vazio por simplicidade

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
            # <<< ALTERAÇÃO >>> Removido (estimado)
            - Páginas processadas: {pags_ok} de {pags_total}
            - Script finalizado em: {horario} (Duração: {duracao}s)

            Nenhum relatório em anexo devido ao erro.

            Recomenda-se verificar manualmente no site do STJ:
            {URL_PESQUISA}

            {gha_link_text}

            Atenciosamente,
            Sistema automatizado
        """)
        attachment_name = "" # Garante que não tenta anexar

    elif qtd_hcs > 0 and arquivo_gerado and Path(arquivo_gerado).is_file():
        # CENÁRIO 2: Sucesso com HCs e arquivo existe
        subject = f"✅ Relatório HCs STJ (Origem {orgao}) - {data_ini}"
        body = dedent(f"""\
            Prezado(a),

            Segue em anexo o relatório de Habeas Corpus (HCs) autuados no STJ, com origem no {orgao}, referente ao período de {data_ini} a {data_fim}.

            Resumo da execução:
            - Resultados encontrados pelo site: {qtd_site}
            - HCs efetivamente extraídos: {qtd_hcs} (detalhes no anexo)
            # <<< ALTERAÇÃO >>> Removido (estimado)
            - Páginas processadas: {pags_ok} de {pags_total}
            - Script finalizado em: {horario} (Duração: {duracao}s)

            O arquivo '{arquivo_gerado}' está anexado a este e-mail.

            Esta automação tem como objetivo auxiliar no acompanhamento processual, mas **não substitui a conferência manual nos canais oficiais do STJ**.

            {gha_link_text}

            Atenciosamente,
            Sistema automatizado
        """)
        attachment_name = arquivo_gerado # Define o nome do anexo

    else:
        # CENÁRIO 3: Sucesso sem HCs ou arquivo não gerado/encontrado
        subject = f"ℹ️ Nenhum HC encontrado STJ (Origem {orgao}) - {data_ini}"
        body = dedent(f"""\
            Prezado(a),

            Nenhum Habeas Corpus (HC) com origem no {orgao} foi localizado ou extraído com sucesso no STJ para o período de {data_ini} a {data_fim}.

            Resumo da execução:
            - Resultados encontrados pelo site: {qtd_site}
            - HCs efetivamente extraídos: {qtd_hcs}
            # <<< ALTERAÇÃO >>> Removido (estimado)
            - Páginas processadas: {pags_ok} de {pags_total}
            - Script finalizado em: {horario} (Duração: {duracao}s)

            Nenhum arquivo foi gerado ou anexado.

            Esta automação tem como objetivo auxiliar no acompanhamento processual, mas **não substitui a conferência manual nos canais oficiais do STJ**.

            {gha_link_text}

            Atenciosamente,
            Sistema automatizado
        """)
        attachment_name = "" # Garante que não tenta anexar

    return subject, body, (attachment_name or "") # Garante string vazia se for None

# --- Execução Principal ---
if __name__ == "__main__":
    # ... (Nenhuma alteração necessária aqui, a lógica existente já chama as funções modificadas) ...
    # ... (Argumentos, Validação, Chamada buscar_processos, Chamada gerar_componentes_email, Salvar .txt, sys.exit) ...

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
        sys.exit(1)

    execution_stats = buscar_processos(data_ini_arg, data_fim_arg)

    logging.info("⚙️ Gerando componentes do e-mail...")
    email_subject, email_body, email_attachment = gerar_componentes_email(execution_stats)

    try:
        Path("email_subject.txt").write_text(email_subject, encoding='utf-8')
        logging.info(f"✅ Assunto do e-mail salvo em email_subject.txt")

        Path("email_body.txt").write_text(email_body, encoding='utf-8')
        logging.info(f"✅ Corpo do e-mail salvo em email_body.txt")

        Path("attachment.txt").write_text(email_attachment, encoding='utf-8')
        logging.info(f"✅ Nome do anexo salvo em attachment.txt (conteúdo: '{email_attachment}')")

    except Exception as e_write:
        logging.error(f"❌ Erro crítico ao salvar arquivos de componentes do e-mail: {e_write}")
        sys.exit(1)

    if execution_stats.get("erro_critico"):
       logging.error("Finalizando com status de erro devido a erro crítico durante a execução.")
       sys.exit(1)
    else:
         logging.info("Finalizando com status de sucesso.")
         sys.exit(0)
