# config.py

from datetime import date, timedelta

# 📅 Data padrão (ontem) — usada quando o usuário não fornece input
ONTEM = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")

# 🌐 URL de pesquisa do STJ
URL_PESQUISA = "https://processo.stj.jus.br/processo/pesquisa/?aplicacao=processos.ea"

# 🏛️ Tribunal de origem fixado
ORGAO_ORIGEM = "TJGO"

# ⏱️ Tempo de pausa entre trocas de páginas (em segundos)
TEMPO_PAUSA_CURTO_ENTRE_PAGINAS = 3
