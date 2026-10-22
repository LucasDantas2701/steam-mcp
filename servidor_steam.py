"""Servidor MCP da "Steam fictícia": consulta jogos, gêneros e plataformas.

Rodar (stdio, padrão):  python servidor_steam.py
Testar sem LLM:         fastmcp list servidor_steam.py
                        fastmcp call servidor_steam.py jogos_por_genero genero=RPG

ATENÇÃO: em stdio, nunca use print() aqui (stdout é o canal do protocolo).
"""
from fastmcp import FastMCP

mcp = FastMCP("steam")

GENEROS = ["RPG", "Ação", "Aventura", "Corrida", "Simulação", "Estratégia", "Terror", "Indie", "Puzzle"]
PLATAFORMAS = ["Windows", "macOS", "Linux", "Steam Deck"]

JOGOS: dict[int, dict] = {
    1: {"titulo": "Cavaleiros de Aurora", "generos": ["RPG", "Aventura"],
        "plataformas": ["Windows", "Linux", "Steam Deck"], "preco": 59.90, "nota": 9.1,
        "ano": 2024, "desenvolvedora": "Estúdio Boreal"},
    2: {"titulo": "Neon Drift 2077", "generos": ["Corrida", "Ação"],
        "plataformas": ["Windows", "Steam Deck"], "preco": 79.90, "nota": 8.4,
        "ano": 2025, "desenvolvedora": "Pixel Turbo"},
    3: {"titulo": "Fazendinha do Vale", "generos": ["Simulação", "Indie"],
        "plataformas": ["Windows", "macOS", "Linux", "Steam Deck"], "preco": 24.99, "nota": 9.4,
        "ano": 2023, "desenvolvedora": "Coruja Games"},
    4: {"titulo": "Ecos da Mansão Vazia", "generos": ["Terror", "Aventura"],
        "plataformas": ["Windows"], "preco": 39.90, "nota": 7.8,
        "ano": 2022, "desenvolvedora": "Sombra Interativa"},
    5: {"titulo": "Impérios de Ferro", "generos": ["Estratégia"],
        "plataformas": ["Windows", "macOS"], "preco": 99.90, "nota": 8.7,
        "ano": 2025, "desenvolvedora": "Legião Studios"},
    6: {"titulo": "Cubo Quântico", "generos": ["Puzzle", "Indie"],
        "plataformas": ["Windows", "macOS", "Linux"], "preco": 14.90, "nota": 8.9,
        "ano": 2021, "desenvolvedora": "Mente Leve"},
    7: {"titulo": "Lendas do Abismo", "generos": ["RPG", "Ação"],
        "plataformas": ["Windows", "Steam Deck"], "preco": 129.90, "nota": 9.0,
        "ano": 2026, "desenvolvedora": "Forja Digital"},
    8: {"titulo": "Pequeno Astronauta", "generos": ["Aventura", "Indie", "Puzzle"],
        "plataformas": ["Windows", "macOS", "Linux", "Steam Deck"], "preco": 19.90, "nota": 8.2,
        "ano": 2024, "desenvolvedora": "Órbita Zero"},
    9: {"titulo": "Caminhoneiro Amazônico", "generos": ["Simulação", "Corrida"],
        "plataformas": ["Windows", "Linux"], "preco": 49.90, "nota": 7.5,
        "ano": 2023, "desenvolvedora": "BR-319 Games"},
    10: {"titulo": "Torre dos Mil Andares", "generos": ["RPG", "Estratégia", "Indie"],
         "plataformas": ["Windows", "Linux", "Steam Deck"], "preco": 34.90, "nota": 8.8,
         "ano": 2022, "desenvolvedora": "Masmorra Indie"},
    11: {"titulo": "Hospital Abandonado VR", "generos": ["Terror"],
         "plataformas": ["Windows"], "preco": 29.90, "nota": 6.9,
         "ano": 2021, "desenvolvedora": "Sombra Interativa"},
    12: {"titulo": "Comandante Galáctico", "generos": ["Estratégia", "Simulação"],
         "plataformas": ["Windows", "macOS", "Linux"], "preco": 69.90, "nota": 8.1,
         "ano": 2026, "desenvolvedora": "Nebulosa Soft"},
}


def _com_id(jogo_id: int) -> dict:
    return {"id": jogo_id, **JOGOS[jogo_id]}


def _normalizar(valor: str, validos: list[str], tipo: str) -> str:
    """Devolve o nome oficial (ex.: 'rpg' -> 'RPG') ou levanta ValueError listando os válidos."""
    for v in validos:
        if v.lower() == valor.lower().strip():
            return v
    raise ValueError(f"{tipo} '{valor}' não existe. Válidos: {', '.join(validos)}.")


@mcp.tool
def buscar_jogos(termo: str) -> list[dict]:
    """Busca jogos cujo título contém o termo (sem diferenciar maiúsculas/minúsculas)."""
    termo = termo.lower().strip()
    return [_com_id(i) for i, j in JOGOS.items() if termo in j["titulo"].lower()]


@mcp.tool
def detalhes_jogo(jogo_id: int) -> dict:
    """Retorna todos os dados de um jogo pelo id. Falha se o id não existir."""
    if jogo_id not in JOGOS:
        raise ValueError(f"Jogo {jogo_id} não existe. Ids válidos: 1 a {max(JOGOS)}.")
    return _com_id(jogo_id)


@mcp.tool
def listar_generos() -> list[str]:
    """Lista os gêneros de jogos disponíveis na loja."""
    return GENEROS


@mcp.tool
def listar_plataformas() -> list[str]:
    """Lista as plataformas suportadas pela loja."""
    return PLATAFORMAS


@mcp.tool
def jogos_por_genero(genero: str) -> list[dict]:
    """Lista os jogos de um gênero (ex.: RPG, Terror). Falha se o gênero não existir."""
    genero = _normalizar(genero, GENEROS, "Gênero")
    return [_com_id(i) for i, j in JOGOS.items() if genero in j["generos"]]


@mcp.tool
def jogos_por_plataforma(plataforma: str) -> list[dict]:
    """Lista os jogos que rodam numa plataforma (ex.: Linux, Steam Deck). Falha se a plataforma não existir."""
    plataforma = _normalizar(plataforma, PLATAFORMAS, "Plataforma")
    return [_com_id(i) for i, j in JOGOS.items() if plataforma in j["plataformas"]]


@mcp.tool
def filtrar_jogos(
    genero: str | None = None,
    plataforma: str | None = None,
    preco_maximo: float | None = None,
) -> list[dict]:
    """Filtra jogos combinando gênero, plataforma e preço máximo (em reais). Todos os filtros são opcionais."""
    if genero:
        genero = _normalizar(genero, GENEROS, "Gênero")
    if plataforma:
        plataforma = _normalizar(plataforma, PLATAFORMAS, "Plataforma")
    return [
        _com_id(i) for i, j in JOGOS.items()
        if (not genero or genero in j["generos"])
        and (not plataforma or plataforma in j["plataformas"])
        and (preco_maximo is None or j["preco"] <= preco_maximo)
    ]


@mcp.resource("steam://promocoes")
def promocoes() -> str:
    """Promoções da semana na Steam fictícia."""
    return (
        "Promoções da semana: Lendas do Abismo com 30% de desconto; "
        "Impérios de Ferro com 50% de desconto; jogos Indie com 20% de desconto até domingo."
    )


@mcp.prompt
def recomendar_jogo(genero: str, plataforma: str) -> str:
    """Pede uma recomendação de jogo de um gênero para uma plataforma."""
    return (
        f"Quero uma recomendação de jogo de {genero} que rode em {plataforma}. "
        "Use as ferramentas da loja para ver as opções, compare preço e nota, "
        "e indique o melhor custo-benefício explicando o porquê."
    )


if __name__ == "__main__":
    mcp.run()  # stdio
    # Alternativa HTTP (como o servidor_reservas.py), em outra porta:
    # mcp.run(transport="http", host="127.0.0.1", port=8001)
