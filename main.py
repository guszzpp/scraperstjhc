# main.py
import sys
import re
import time
import logging
from datetime import datetime
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pathlib import Path
from textwrap import dedent
import math # Mantido para cálculo de páginas em caso de múltiplos resultados

# Certifique-se que os outros arquivos .py estão na mesma pasta
from navegador import iniciar_navegador
from extrator import extrair_detalhes_processo
from exportador import exportar_resultados
from paginador import navegar_paginas_e_extrair # Retorna 2 valores
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

# --- Função buscar_processos (COM LÓGICA PARA PÁGINA ÚNICA) ---
def buscar_processos(data_inicial, data_final):
    """
    Executa o fluxo de busca e retorna estatísticas e nome do arquivo gerado.
    """
    resultados = []
    total_resultados_site = -1 # -1 = Erro/Não obtido; -2 = Desconhecido(>0)
    total_paginas_site = 0 # Calculado a partir dos dados da página 1, ou -1 se não calculável
    paginas_processadas_ok = 0 # Contagem real de páginas processadas com sucesso
    relatorio_paginas = []
    erro_critico = None
    nome_arquivo_gerado = None
    driver = None
    horario_inicio = datetime.now()
    is_single_result_page = False # Flag para página única

    logging.info(f"🟡 Iniciando busca de HCs no STJ — {data_inicial} até {data_final}")
    logging.info(f"   URL: {URL_PESQUISA}")
    logging.info(f"   Órgão Origem: {ORGAO_ORIGEM}")

    try:
        driver = iniciar_navegador()
        wait = WebDriverWait(driver, 20)

        preencher_formulario(driver, wait, data_inicial, data_final)
        logging.info("✅ Formulário preenchido e resultado inicial carregado.")

        # Verifica em qual tipo de página estamos após o preenchimento e clique
        try:
            # Tenta encontrar o elemento chave da página de DETALHES
            driver.find_element(By.ID, "idSpanClasseDescricao")
            logging.info("Detectada página de detalhes (resultado único).")
            is_single_result_page = True
            total_resultados_site = 1 # Se estamos nos detalhes, é 1 resultado
            total_paginas_site = 1
            paginas_processadas_ok = 1 # Consideramos a página de detalhes como 1 processada
        except NoSuchElementException:
            # Não está na página de detalhes, verificar mensagem ou lista
            logging.info("Não é página de detalhes. Verificando mensagem ou lista...")
            is_single_result_page = False

            # Obter Total de Resultados do Site (da mensagem)
            try:
                mensagem = driver.find_element(By.CLASS_NAME, "clsMensagemLinha")
                texto = mensagem.text.strip()
                match = re.search(r'(\d+)', texto)
                if match:
                    total_resultados_site = int(match.group(1))
                    logging.info(f"📊 Site reportou {total_resultados_site} resultados totais (da mensagem).")
                else:
                    logging.warning(f"⚠️ Não foi possível extrair número da mensagem: '{texto}'")
                    if driver.find_elements(By.CLASS_NAME, "clsListaProcessoFormatoVerticalLinha"): total_resultados_site = -2 # Desconhecido > 0
                    else: total_resultados_site = 0
            except NoSuchElementException:
                 logging.warning("ℹ️ Elemento clsMensagemLinha não encontrado.")
                 try: # Verifica se tem blocos mesmo sem mensagem
                      if driver.find_elements(By.CLASS_NAME, "clsListaProcessoFormatoVerticalLinha"): total_resultados_site = -2
                      else: total_resultados_site = 0
                 except Exception: total_resultados_site = 0 # Assume 0 em caso de erro
            except Exception as e:
                logging.warning(f"ℹ️ Não foi possível capturar o total de registros da mensagem (erro geral): {e}")
                total_resultados_site = -1 # Indica erro/não obtido

            # Calcular total_paginas_site baseado em total_resultados_site e contagem de blocos na pag 1
            if total_resultados_site != 0: # Só calcula se espera resultados
                resultados_por_pagina_site = 0
                try:
                    blocos_pagina1 = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "clsListaProcessoFormatoVerticalLinha")))
                    resultados_por_pagina_site = len(blocos_pagina1)
                    logging.info(f"🔢 Resultados por página (contados na Pág 1): {resultados_por_pagina_site}")
                    if total_resultados_site > 0 and resultados_por_pagina_site > 0:
                        total_paginas_site = math.ceil(total_resultados_site / resultados_por_pagina_site)
                        logging.info(f"🔢 Total de páginas calculado (site): {total_paginas_site}")
                    elif total_resultados_site > 0: # RPP não calculado, mas tem resultados
                         total_paginas_site = -1 # Desconhecido
                         logging.warning("Total de páginas do site não pôde ser calculado (RPP=0?).")
                    else: # Nao tem resultados
                         total_paginas_site = 0
                except TimeoutException:
                    logging.warning("Nenhum bloco de resultado encontrado na Página 1 (Timeout).")
                    if total_resultados_site > 0:
                        total_paginas_site = 1 # Se tem resultado mas não blocos, assume 1 pag? Ou desconhecido?
                        logging.warning("Assumindo Total de páginas = 1 (resultados > 0, mas sem blocos na P1).")
                    elif total_resultados_site == -2: # Desconhecido > 0
                         total_paginas_site = -1 # Realmente desconhecido
                         logging.warning("Total de páginas desconhecido (sem blocos na P1).")
                    else: total_paginas_site = 0
                except Exception as e_count:
                     logging.error(f"Erro ao contar resultados/página na Pág 1: {e_count}")
                     total_paginas_site = -1 # Erro ao calcular
            else:
                 total_paginas_site = 0
                 logging.info("Total de páginas do site: 0 (baseado em 0 resultados).")
        # Fim da verificação de tipo de página

        # Navegar ou extrair diretamente
        if is_single_result_page:
            logging.info("Extraindo dados diretamente da página de detalhes...")
            try:
                 titulo_hc_element = driver.find_element(By.ID, "idSpanClasseDescricao")
                 titulo_hc = titulo_hc_element.text.strip() if titulo_hc_element else "HC Único"
            except:
                 titulo_hc = "HC Único (erro ao pegar título)"
            resultado_unico = extrair_detalhes_processo(driver, wait, titulo_hc, data_inicial)
            if resultado_unico:
                resultados.append(resultado_unico)
            # paginas_processadas_ok já foi definido como 1 neste cenário
        elif total_resultados_site != 0:
            # Cenário de múltiplas páginas (ou múltiplas na pág 1)
            logging.info("🔍 Iniciando navegação e extração (múltiplos resultados/páginas)...")
            resultados, relatorio_paginas = navegar_paginas_e_extrair(driver, wait, extrair_detalhes_processo, data_inicial)
            # Calcular Páginas Processadas com Sucesso
            relatorios_validos = [r for r in relatorio_paginas if r.strip().startswith("📄 Página")]
            paginas_processadas_ok = len(relatorios_validos)
            logging.info(f"✅ Número de páginas com relatório de processamento válido: {paginas_processadas_ok}")
            # Ajusta o total se for desconhecido, baseado no processado
            if total_paginas_site == -1:
                 total_paginas_site = paginas_processadas_ok if paginas_processadas_ok > 0 else 1
                 logging.info(f"Total de páginas definido para {total_paginas_site} (baseado nas processadas).")

        else: # total_resultados_site == 0
            logging.info("Nenhuma navegação necessária (0 resultados).")
            paginas_processadas_ok = 0
            total_paginas_site = 0

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
             erro_critico = erro_critico or f"Erro ao exportar Excel: {e}" # Adiciona erro se já não houver um
    elif not erro_critico:
        logging.info("✅ Nenhum Habeas Corpus encontrado ou extraído com sucesso.")
    else: # Se houve erro E não há resultados
         logging.warning("⚠️ Extração interrompida por erro, nenhum HC foi extraído.")


    # Logging do relatório de páginas (se houver)
    if relatorio_paginas:
        logging.info("📄 Relatório detalhado de páginas (do paginador):")
        for linha in relatorio_paginas:
            logging.info(f"   - {linha}")
    # Log mais informativo sobre páginas processadas
    if not erro_critico:
        logging.info(f"📈 Páginas efetivamente processadas (contagem final): {paginas_processadas_ok}")


    horario_finalizacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    duracao = (datetime.now() - horario_inicio).total_seconds()
    logging.info(f"✅ Execução finalizada às {horario_finalizacao} (Duração: {duracao:.2f}s)")

    # Compila as estatísticas FINAIS
    stats = {
        "data_inicial": data_inicial,
        "data_final": data_final,
        "orgao_origem": ORGAO_ORIGEM,
        "qtd_resultados_site": str(total_resultados_site) if total_resultados_site >= 0 else "Desconhecido (>0)" if total_resultados_site == -2 else "Erro/Não obtido",
        "qtd_hcs": qtd_hcs_extraidos,
        "paginas_total": str(total_paginas_site) if total_paginas_site >= 0 else "Desconhecido",
        "paginas_processadas": paginas_processadas_ok,
        "horario_finalizacao": horario_finalizacao,
        "duracao_segundos": round(duracao, 2),
        "erro_critico": erro_critico,
        "arquivo_gerado": nome_arquivo_gerado
    }

    return stats

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
    pags_total_str = stats.get("paginas_total", "0") # Pega o valor (pode ser "Desconhecido")
    pags_ok = stats.get("paginas_processadas", 0)
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
            - Páginas processadas: {pags_ok} de {pags_total_str}
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
            - Páginas processadas: {pags_ok} de {pags_total_str}
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
            - Páginas processadas: {pags_ok} de {pags_total_str}
            - Script finalizado em: {horario} (Duração: {duracao}s)

            Nenhum arquivo foi gerado ou anexado.

            Esta automação tem como objetivo auxiliar no acompanhamento processual, mas **não substitui a conferência manual nos canais oficiais do STJ**.

            {gha_link_text}

            Atenciosamente,
            Sistema automatizado
        """)
        attachment_name = ""

    return subject, body, (attachment_name or "")

# --- Execução Principal ---
if __name__ == "__main__":
    # Validação de argumentos e datas
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
        # Prepara um e-mail de erro específico para data inválida
        error_stats = {
            "data_inicial": data_ini_arg, "data_final": data_fim_arg, "orgao_origem": ORGAO_ORIGEM,
            "horario_finalizacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "erro_critico": "Formato de data inválido recebido nos argumentos."
            # Adiciona contagens zeradas para consistência no template de email
            ,"paginas_total": "0", "paginas_processadas": 0, "qtd_resultados_site": "N/A", "qtd_hcs": 0
        }
        email_subject, email_body, email_attachment = gerar_componentes_email(error_stats)
        # Tenta salvar os arquivos de email mesmo em erro, para notificar
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
