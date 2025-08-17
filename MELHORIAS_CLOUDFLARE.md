# Melhorias contra Cloudflare - Scraper STJ

## Problema Identificado

O scraper estava falhando devido ao timeout no desafio de carregamento do Cloudflare ("Just a moment..."). O site do STJ implementa proteções anti-bot que impedem o acesso automatizado.

## Melhorias Implementadas

### 1. Configurações do Chrome Aprimoradas (`navegador.py`)

#### User Agent Mais Realista
- Alterado de Linux para Windows para parecer mais humano
- Versão do Chrome atualizada para 139.0.0.0

#### Opções Anti-Detecção
```python
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
```

#### Scripts JavaScript Anti-Detecção
```javascript
// Remover propriedades que indicam automação
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en']});

// Simular propriedades de navegador real
Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'});

// Remover propriedades de automação do Chrome
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
```

### 2. Função de Aguardar Challenge Melhorada (`formulario.py`)

#### Timeout Aumentado
- De 90s para 180s para dar mais tempo ao Cloudflare

#### Estratégias Adicionais
Após 30 segundos, se o desafio persistir:
1. **Recarregar página**: `driver.refresh()`
2. **Navegação alternativa**: Acessar `stj.jus.br` primeiro, depois voltar
3. **Simulação de interação humana**: JavaScript para simular mouse e scroll

#### Logging Melhorado
- Mostra URL atual além do título
- Logs mais detalhados sobre as estratégias aplicadas

### 3. Função de Acesso Múltiplo (`formulario.py`)

#### URLs Alternativas
```python
urls_alternativas = [
    URL_PESQUISA,
    "https://www.stj.jus.br",
    "https://processo.stj.jus.br",
    "https://processo.stj.jus.br/processo/",
    "https://processo.stj.jus.br/processo/pesquisa/"
]
```

#### Múltiplas Tentativas
- Até 3 tentativas por URL
- Pausa de 30s entre tentativas
- Timeout de 120s por tentativa

### 4. Script de Teste (`teste_cloudflare.py`)

Criado para testar as melhorias localmente:
```bash
python teste_cloudflare.py
```

## Como Usar

### Teste Local
1. Execute o script de teste:
   ```bash
   python teste_cloudflare.py
   ```

2. Observe os logs para verificar se o acesso está funcionando

### GitHub Actions
As melhorias já estão integradas no workflow. O scraper agora:
- Tenta múltiplas estratégias de acesso
- Tem timeout maior para o Cloudflare
- Usa configurações mais realistas do Chrome

## Monitoramento

### Logs Importantes
- `🔄 Aguardando resolução do desafio de carregamento`
- `🔧 Aplicando estratégias adicionais para contornar Cloudflare`
- `🔄 Tentativa X/Y de acesso ao site`
- `✅ Acesso bem-sucedido via URL`

### Indicadores de Sucesso
- Título da página não contém "Just a moment..."
- URL final é a página de pesquisa do STJ
- Elementos de input encontrados na página

## Troubleshooting

### Se ainda falhar:
1. Verificar se o site do STJ mudou a proteção
2. Aumentar timeouts se necessário
3. Adicionar novas URLs alternativas
4. Verificar se o IP não está bloqueado

### Logs de Debug
Execute com modo headful para ver o que está acontecendo:
```python
driver = iniciar_navegador(headless=False)
```

## Próximos Passos

1. Monitorar a eficácia das melhorias
2. Ajustar timeouts conforme necessário
3. Adicionar mais estratégias se o Cloudflare evoluir
4. Considerar uso de proxy se necessário
