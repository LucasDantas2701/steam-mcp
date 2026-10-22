"""Testa o servidor da Steam fictícia SEM LLM, usando o cliente do FastMCP.

Rodar:  python teste_cliente.py
Se o servidor não funciona sozinho, o agente não vai funcionar.
"""
import asyncio
from pathlib import Path

from fastmcp import Client
from fastmcp.exceptions import ToolError

SERVIDOR = Path(__file__).parent / "servidor_steam.py"


async def main():
    async with Client(SERVIDOR) as client:
        tools = await client.list_tools()
        print("Tools:", [t.name for t in tools])

        r = await client.call_tool("buscar_jogos", {"termo": "neon"})
        print("\nbuscar_jogos('neon'):", r.data)

        r = await client.call_tool("jogos_por_genero", {"genero": "rpg"})
        print("\njogos_por_genero('rpg'):", [j["titulo"] for j in r.data])

        r = await client.call_tool("filtrar_jogos", {"plataforma": "Linux", "preco_maximo": 50})
        print("\nfiltrar_jogos(Linux, <= 50):", [(j["titulo"], j["preco"]) for j in r.data])

        conteudo = await client.read_resource("steam://promocoes")
        print("\nResource steam://promocoes:", conteudo[0].text)

        prompt = await client.get_prompt("recomendar_jogo", {"genero": "Terror", "plataforma": "Windows"})
        print("\nPrompt recomendar_jogo:", prompt.messages[0].content.text)

        try:
            await client.call_tool("jogos_por_genero", {"genero": "Futebol"})
        except ToolError as e:
            print("\nErro esperado (é isto que o modelo veria):", e)


asyncio.run(main())
