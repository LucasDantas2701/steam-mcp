"""Frontend simples para testar o servidor da Steam fictícia manualmente, no navegador.

Rodar:  python frontend.py   ->   http://127.0.0.1:8080

Este app é só uma "ponte": o navegador chama /api/..., e cada chamada passa pelo
servidor MCP de verdade (fastmcp.Client via stdio). Nada da lógica da loja é copiado aqui.
"""
from pathlib import Path

import uvicorn
from fastmcp import Client
from fastmcp.exceptions import ToolError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

PASTA = Path(__file__).parent
SERVIDOR = PASTA / "servidor_steam.py"


def novo_cliente() -> Client:
    # Um cliente por requisição: simples e suficiente para teste manual.
    return Client(SERVIDOR)


async def pagina(request: Request):
    return FileResponse(PASTA / "static" / "index.html")


async def listar_tools(request: Request):
    async with novo_cliente() as client:
        tools = await client.list_tools()
    return JSONResponse(
        [{"nome": t.name, "descricao": t.description, "schema": t.inputSchema} for t in tools]
    )


async def chamar_tool(request: Request):
    nome = request.path_params["nome"]
    argumentos = await request.json() if await request.body() else {}
    try:
        async with novo_cliente() as client:
            resultado = await client.call_tool(nome, argumentos)
    except ToolError as e:
        return JSONResponse({"erro": str(e)}, status_code=400)
    return JSONResponse({"resultado": resultado.data})


async def promocoes(request: Request):
    async with novo_cliente() as client:
        conteudo = await client.read_resource("steam://promocoes")
    return JSONResponse({"texto": conteudo[0].text})


async def prompt_recomendar(request: Request):
    argumentos = await request.json()
    async with novo_cliente() as client:
        prompt = await client.get_prompt("recomendar_jogo", argumentos)
    return JSONResponse(
        {"mensagens": [{"papel": m.role, "texto": m.content.text} for m in prompt.messages]}
    )


app = Starlette(
    routes=[
        Route("/", pagina),
        Route("/api/tools", listar_tools),
        Route("/api/tools/{nome}", chamar_tool, methods=["POST"]),
        Route("/api/promocoes", promocoes),
        Route("/api/prompt/recomendar_jogo", prompt_recomendar, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
