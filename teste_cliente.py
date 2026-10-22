"""Testa o servidor da Steam fictícia SEM LLM, usando o cliente do FastMCP.

Local (stdio):     python teste_cliente.py
Publicado (HTTP):  python teste_cliente.py https://SEU-PROJETO.vercel.app/mcp
Se o servidor não funciona sozinho, o agente não vai funcionar.
"""
import asyncio
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.exceptions import ToolError

ALVO = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "servidor_steam.py"


async def main():
    async with Client(ALVO) as client:
        tools = await client.list_tools()
        print("Tools:", [t.name for t in tools])

        r = await client.call_tool("buscar_jogos", {"termo": "neon"})
        print("\nbuscar_jogos('neon'):", [j["titulo"] for j in r.data])

        r = await client.call_tool("jogos_por_genero", {"genero": "rpg"})
        print("\njogos_por_genero('rpg'):", [j["titulo"] for j in r.data])

        r = await client.call_tool("filtrar_jogos", {"plataforma": "Steam Deck", "preco_maximo": 50, "ordenar_por": "preco"})
        print("\nfiltrar_jogos(Steam Deck, <= 50):", [(j["titulo"], j["preco_atual"]) for j in r.data])

        r = await client.call_tool("detalhes_jogo", {"jogo_id": 1})
        j = r.data
        print(f"\ndetalhes_jogo(1): {j['titulo']} | lançado em {j['data_lancamento']} | {j['desenvolvedora']}"
              f" | R$ {j['preco_atual']} (menor: R$ {j['menor_preco_historico']}) | {len(j['historico_precos'])} preços")

        conteudo = await client.read_resource("steam://promocoes")
        print("\nResource steam://promocoes:\n" + conteudo[0].text)

        prompt = await client.get_prompt("recomendar_jogo", {"genero": "Terror", "plataforma": "Windows"})
        print("\nPrompt recomendar_jogo:", prompt.messages[0].content.text)

        try:
            await client.call_tool("jogos_por_genero", {"genero": "Futebol"})
        except ToolError as e:
            print("\nErro esperado (é isto que o modelo veria):", e)


asyncio.run(main())
