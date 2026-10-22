"""Agente LangChain ligado ao servidor MCP da Steam fictícia.

Mesmo padrão das Partes 4 e 5: as tools vivem em OUTRO processo (o servidor MCP).
Sem MCP_URL: sobe o servidor local por stdio.
Com MCP_URL (ex.: https://SEU-PROJETO.vercel.app/mcp): usa o servidor publicado, via HTTP.
"""
import asyncio
import os
import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.resources import load_mcp_resources

from modelo import carregar_modelo, mostrar_trace

SERVIDOR = str(Path(__file__).parent / "servidor_steam.py")
MCP_URL = os.environ.get("MCP_URL")


async def main():
    if MCP_URL:
        conexao = {"transport": "streamable_http", "url": MCP_URL}
    else:
        conexao = {"transport": "stdio", "command": sys.executable, "args": [SERVIDOR]}
    client = MultiServerMCPClient({"steam": conexao})
    tools = await client.get_tools()
    print("Tools:", [t.name for t in tools])

    # Resource -> contexto que a APLICAÇÃO escolhe injetar (não vira tool)
    async with client.session("steam") as session:
        blobs = await load_mcp_resources(session, uris=["steam://promocoes"])
        promocoes = blobs[0].as_string()

    agent = create_agent(carregar_modelo(), tools)
    pergunta = "Quais RPGs rodam no Steam Deck por menos de R$ 100? Algum está no menor preço histórico?"
    resultado = await agent.ainvoke(
        {
            "messages": [
                {"role": "system", "content": f"Informação da loja:\n{promocoes}"},
                {"role": "user", "content": pergunta},
            ]
        }
    )
    mostrar_trace(resultado)


asyncio.run(main())

# TODO 1: pergunte por um gênero que não existe ("jogos de futebol"). O modelo se corrige
#         com a lista de gêneros válidos que vem na mensagem do ValueError?
# TODO 2: pergunte "vale a pena comprar Lendas do Abismo agora ou esperar?". O modelo usa historico_precos?
# TODO 3: use o prompt "recomendar_jogo" (load_mcp_prompt) em vez da pergunta fixa.
#         Lembre: argumentos de prompt são sempre strings.
