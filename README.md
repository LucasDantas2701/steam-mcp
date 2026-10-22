# Steam Fictícia — servidor MCP (FastMCP) de jogos, gêneros e plataformas

Mesma estrutura do exercício principal: um servidor FastMCP, um teste sem LLM, um agente LangChain
e, para teste manual, um frontend web.

## Preparação

```bash
# a partir da pasta "exercicio - aulos", com o venv ativado (Windows: venv\Scripts\activate)
pip install -r steam_ficticia/requirements.txt
cd steam_ficticia
```

## Arquivos

| Arquivo | O que é |
|---|---|
| `servidor_steam.py` | Servidor MCP `steam`: 7 tools, 1 resource (`steam://promocoes`) e 1 prompt (`recomendar_jogo`) |
| `teste_cliente.py` | Testa tudo **sem LLM** com `fastmcp.Client` |
| `frontend.py` + `static/index.html` | Página web para testar manualmente (cada clique chama o servidor MCP de verdade) |
| `agente_steam.py` | Agente LangChain ligado ao servidor via `MultiServerMCPClient` (stdio) |
| `modelo.py` | `carregar_modelo()` (variável `MODELO`) e `mostrar_trace()` |

### Tools

| Tool | Argumentos |
|---|---|
| `buscar_jogos` | `termo` (parte do título) |
| `detalhes_jogo` | `jogo_id` |
| `listar_generos` / `listar_plataformas` | nenhum |
| `jogos_por_genero` | `genero` |
| `jogos_por_plataforma` | `plataforma` |
| `filtrar_jogos` | `genero`, `plataforma`, `preco_maximo` (todos opcionais) |

Gênero ou plataforma inválidos levantam `ValueError` com a lista de valores válidos, para o modelo conseguir se corrigir.

## Como testar

1. **Linha de comando:**
   `fastmcp list servidor_steam.py` e `fastmcp call servidor_steam.py jogos_por_genero genero=RPG`
2. **Script sem LLM:** `python teste_cliente.py`
3. **Frontend (teste manual):** `python frontend.py` e abra http://127.0.0.1:8080
   - Busca por título, filtros por gênero, plataforma e preço, e detalhes ao clicar no card.
   - Painéis com o resource de promoções e o texto gerado pelo prompt.
   - **Console MCP:** escolha qualquer tool, preencha os argumentos (o formulário vem do `inputSchema`) e veja o JSON bruto ou o erro.
4. **Agente:** defina `MODELO` (ex.: `openai:gpt-4.1`) e a chave do provedor, depois rode `python agente_steam.py`.

## Problemas comuns

- **Nunca use `print()` no servidor** (em stdio, o stdout é o canal do protocolo).
- **Erro do `langchain-mcp-adapters` com `mcp` 2.x**: use `fastmcp<4` em um venv limpo (ver o README da pasta acima).
- **Argumentos de prompt são sempre strings**.
- **Porta 8080 ocupada**: troque a porta no fim do `frontend.py`.
