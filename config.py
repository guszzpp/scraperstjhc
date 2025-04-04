from datetime import date, timedelta

# Datas úteis (padrão: ontem)
ONTEM = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")

# URL de pesquisa do STJ
URL_PESQUISA = "https://processo.stj.jus.br/processo/pesquisa/?aplicacao=processos.ea"

# Órgão de origem a ser pesquisado
ORGAO_ORIGEM = "TJGO"

# Pausa após clicar em "próxima página"
TEMPO_PAUSA_CURTO_ENTRE_PAGINAS = 15

# Tempo (em segundos) de fallback caso a próxima página demore a carregar
TEMPO_FALLBACK_PAGINA = 30
