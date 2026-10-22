# Steam Fictícia: servidor MCP (FastMCP) de jogos, gêneros, plataformas e preços

Um servidor MCP que consulta uma loja de jogos fictícia. Os dados (30 jogos, capas, histórico
de preços e promoções) ficam no **Supabase**. O servidor fica publicado na **Vercel**, para
qualquer pessoa usar pelo navegador ou conectar o MCP no VS Code, Claude e outros clientes.

```
navegador ──► Vercel: app.py ──┬─ /       frontend (public/index.html)
                               ├─ /api/*  ponte JSON ──► servidor MCP (em memória)
VS Code / agente ──────────────┴─ /mcp    servidor MCP (Streamable HTTP) ──► Supabase (Postgres + Storage)
```

## Arquivos

| Arquivo | O que é |
|---|---|
| `servidor_steam.py` | Servidor MCP `steam`: 9 tools, o resource `steam://promocoes` e o prompt `recomendar_jogo` |
| `app.py` | Publica o mesmo servidor via HTTP (`/mcp`) mais o frontend. É o ponto de entrada da Vercel |
| `public/index.html` | Loja com capas, filtros, detalhes, gráfico do histórico de preços e o Console MCP |
| `supabase/schema.sql` | Tabelas, a visão `jogos_completos` e as regras de leitura pública (RLS) |
| `scripts/seed.py` | Gera e carrega o catálogo: jogos, capas no Storage, histórico e promoções |
| `teste_cliente.py` | Testa o servidor **sem LLM** (local ou pela URL publicada) |
| `agente_steam.py` + `modelo.py` | Agente LangChain (stdio local ou `MCP_URL` remoto) |

### Tools

| Tool | Argumentos |
|---|---|
| `buscar_jogos` | `termo` (parte do título) |
| `detalhes_jogo` | `jogo_id`: devolve descrição, lançamento, desenvolvedora, publicadora, capa, promoção, menor preço e histórico |
| `historico_precos` | `jogo_id` |
| `listar_generos` / `listar_plataformas` / `jogos_em_promocao` | nenhum |
| `jogos_por_genero` / `jogos_por_plataforma` | `genero` / `plataforma` |
| `filtrar_jogos` | `genero`, `plataforma`, `preco_maximo`, `ano_minimo`, `desenvolvedora`, `apenas_promocao`, `ordenar_por`, `limite` (todos opcionais) |

Gênero ou plataforma inválidos levantam `ValueError` com a lista de válidos, para o modelo conseguir se corrigir.

## 1. Supabase (banco e capas)

1. Crie um projeto em https://supabase.com (o plano grátis basta).
2. Abra **SQL Editor → New query**, cole o conteúdo de `supabase/schema.sql` e clique em **Run**.
3. Em **Project Settings → API Keys**, copie a chave pública (*anon* / *publishable*) e a chave secreta (*service_role* / *secret*). A URL do projeto fica em **Data API**.
4. Copie `.env.example` para `.env` e preencha as três variáveis.
5. Carregue os dados:
   ```powershell
   pip install -r requirements.txt
   python scripts/seed.py
   ```
   O script cria o bucket público `capas`, envia as 30 capas e preenche as tabelas.
   As promoções são criadas relativas à data de hoje e valem por 7 dias. Para renová-las, rode o script de novo.

A chave pública só consegue **ler** (RLS). A chave secreta fica apenas no seu `.env`, que está no `.gitignore`.

## 2. Testar localmente

```powershell
python teste_cliente.py           # testa o servidor sem LLM (stdio)
python app.py                     # frontend em http://127.0.0.1:8080, MCP em http://127.0.0.1:8080/mcp
$env:PORT="8090"; python app.py   # se a porta 8080 estiver ocupada
```

## 3. Publicar na Vercel

1. Crie um repositório no GitHub com o **conteúdo desta pasta** na raiz (o `app.py` precisa ficar na raiz do repositório).
2. Na Vercel: **Add New → Project**, importe o repositório e deixe o Framework Preset como está (a Vercel detecta o `app.py` sozinha).
3. Em **Environment Variables**, adicione **só** `SUPABASE_URL` e `SUPABASE_KEY` (a chave pública). Clique em **Deploy**.
4. Teste: abra `https://SEU-PROJETO.vercel.app` e rode `python teste_cliente.py https://SEU-PROJETO.vercel.app/mcp`.

Cada `git push` na branch principal gera um deploy novo.

## 4. Usar o MCP publicado

- **VS Code** (`.vscode/mcp.json`):
  ```json
  { "servers": { "steam": { "type": "http", "url": "https://SEU-PROJETO.vercel.app/mcp" } } }
  ```
- **Agente LangChain:** `pip install -r requirements-agente.txt`, defina `MODELO`, a chave do provedor e `MCP_URL=https://SEU-PROJETO.vercel.app/mcp`, depois rode `python agente_steam.py`.
- **Claude Code:** `claude mcp add --transport http steam https://SEU-PROJETO.vercel.app/mcp`

## Problemas comuns

- **`Servidor sem SUPABASE_URL/SUPABASE_KEY`**: falta o `.env` (local) ou as variáveis de ambiente na Vercel. Na Vercel, faça **Redeploy** depois de adicionar as variáveis.
- **Lista vazia**: o `seed.py` não rodou, ou rodou num projeto Supabase diferente do `SUPABASE_URL`.
- **`permission denied` no Supabase**: rode o `schema.sql` de novo (ele recria as permissões de leitura).
- **Nunca use `print()` no servidor** (em stdio, o stdout é o canal do protocolo).
- **`fastmcp<4`**: necessário para o `langchain-mcp-adapters` (ver o README da pasta acima).
