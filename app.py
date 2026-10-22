"""App HTTP da Steam fictícia: o MESMO servidor MCP de servidor_steam.py, publicado na web.

Local:   python app.py   ->   frontend em http://127.0.0.1:8080  |  MCP em http://127.0.0.1:8080/mcp
Vercel:  detecta este arquivo (app.py) e a variável `app` automaticamente.

Rotas:
  /mcp                 -> endpoint MCP (Streamable HTTP, stateless: necessário em serverless)
  /api/...             -> ponte JSON para o frontend; cada chamada passa pelo servidor MCP (Client em memória)
  /                    -> frontend (na Vercel, public/index.html é servido direto pela CDN)
"""
from pathlib import Path

from fastmcp import Client
from fastmcp.exceptions import ToolError
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse

from servidor_steam import mcp

INDEX = Path(__file__).parent / "public" / "index.html"


@mcp.custom_route("/", methods=["GET"], include_in_schema=False)
async def pagina(request: Request):
    return FileResponse(INDEX)


@mcp.custom_route("/api/tools", methods=["GET"])
async def listar_tools(request: Request):
    async with Client(mcp) as client:
        tools = await client.list_tools()
    return JSONResponse(
        [{"nome": t.name, "descricao": t.description, "schema": t.inputSchema} for t in tools]
    )


@mcp.custom_route("/api/tools/{nome}", methods=["POST"])
async def chamar_tool(request: Request):
    nome = request.path_params["nome"]
    argumentos = await request.json() if await request.body() else {}
    try:
        async with Client(mcp) as client:
            resultado = await client.call_tool(nome, argumentos)
    except ToolError as e:
        return JSONResponse({"erro": str(e)}, status_code=400)
    return JSONResponse({"resultado": resultado.data})


@mcp.custom_route("/api/promocoes", methods=["GET"])
async def ler_promocoes(request: Request):
    try:
        async with Client(mcp) as client:
            conteudo = await client.read_resource("steam://promocoes")
    except Exception as e:
        return JSONResponse({"erro": str(e)}, status_code=500)
    return JSONResponse({"texto": conteudo[0].text})


@mcp.custom_route("/api/prompt/recomendar_jogo", methods=["POST"])
async def prompt_recomendar(request: Request):
    argumentos = await request.json()
    async with Client(mcp) as client:
        prompt = await client.get_prompt("recomendar_jogo", argumentos)
    return JSONResponse(
        {"mensagens": [{"papel": m.role, "texto": m.content.text} for m in prompt.messages]}
    )


app = mcp.http_app(
    path="/mcp",
    stateless_http=True,  # cada requisição é independente (a Vercel não mantém sessão entre chamadas)
    json_response=True,
    # Libera clientes MCP rodando no navegador (ex.: MCP Inspector) a chamar o endpoint público.
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["mcp-session-id", "mcp-protocol-version"],
        )
    ],
)

if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", 8080)))
