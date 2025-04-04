# email_detalhado.py

from textwrap import dedent

def gerar_corpo_email(
    data_inicial,
    data_final,
    total_resultados,
    total_paginas,
    paginas_processadas,
    qtd_hcs,
    horario_finalizacao,
    erro_critico=None
):
    """
    Gera o corpo do e-mail a ser enviado com base nos parâmetros da execução.
    """

    if erro_critico:
        return dedent(f"""\
            Prezado(a),

            Ocorreu um erro crítico durante a execução do scraper de HCs no STJ para o intervalo de {data_inicial} até {data_final}.

            O erro foi:
            {erro_critico}

            O script foi encerrado às {horario_finalizacao}.

            Recomenda-se verificar manualmente no site do STJ:
            https://processo.stj.jus.br/processo/pesquisa/?aplicacao=processos.ea

            Atenciosamente,
            Sistema automatizado - GitHub Actions
        """)

    if qtd_hcs > 0:
        return dedent(f"""\
            Prezado(a),

            Segue em anexo o relatório de Habeas Corpus (HCs) autuados no STJ, com origem no TJGO, na data de {data_inicial}.
            Foram localizados {total_resultados} processos, dos quais ${qtd_hcs} são HCs, com base nos seguintes parâmetros de busca:
            - Data inicial: {data_inicial}
            - Data final: {data_final}
            - Tribunal de origem: TJGO
            - Páginas com resultados: {total_paginas}
            - Páginas em que foi possível fazer a conferência: {paginas_processadas}
            - O script foi finalizado em: {horario_finalizacao}

            Esta automação tem como objetivo auxiliar no acompanhamento processual, mas **não substitui a conferência manual nos canais oficiais do STJ**.

            Atenciosamente,
            Sistema automatizado - GitHub Actions
        """)
    else:
        return dedent(f"""\
            Prezado(a),

            Foram localizados {total_resultados} processos, mas nenhum Habeas Corpus com origem no TJGO foi autuado no STJ na data de {data_inicial}, com base nos seguintes parâmetros de busca:
            - Data inicial: {data_inicial}
            - Data final: {data_final}
            - Tribunal de origem: TJGO
            - Páginas com resultados: {total_paginas}
            - Páginas em que foi possível fazer a conferência: {paginas_processadas}
            - O script foi finalizado em: {horario_finalizacao}

            Esta automação tem como objetivo auxiliar no acompanhamento processual, mas **não substitui a conferência manual nos canais oficiais do STJ**.

            Atenciosamente,
            Sistema automatizado - GitHub Actions
        """)
