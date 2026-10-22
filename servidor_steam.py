"""Servidor MCP da "Steam fictícia": consulta jogos, gêneros, plataformas e preços no Supabase.

Rodar local (stdio):  python servidor_steam.py
Testar sem LLM:       fastmcp list servidor_steam.py
                      fastmcp call servidor_steam.py jogos_por_genero genero=RPG
Versão HTTP/Vercel:   app.py (expõe este mesmo servidor em /mcp)

Precisa de SUPABASE_URL e SUPABASE_KEY (chave pública/anon) no ambiente ou no arquivo .env.
ATENÇÃO: em stdio, nunca use print() aqui (stdout é o canal do protocolo).
"""
import os
from functools import cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastmcp import FastMCP
from supabase import Client, create_client

load_dotenv(Path(__file__).parent / ".env")

mcp = FastMCP("steam")

CAMPOS_RESUMO = (
    "id, titulo, desenvolvedora, data_lancamento, generos, plataformas, "
    "preco_base, preco_atual, desconto_pct, nota, capa_url"
)
ORDENACAO = {
    "nota": ("nota", True),
    "preco": ("preco_atual", False),
    "lancamento": ("data_lancamento", True),
    "titulo": ("titulo", False),
    "desconto": ("desconto_pct", True),
}


@cache
def _db() -> Client:
    url, chave = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
    if not url or not chave:
        raise RuntimeError("Servidor sem SUPABASE_URL/SUPABASE_KEY configurados (veja o .env.example).")
    return create_client(url, chave)


def _nomes(tabela: str) -> list[str]:
    return [r["nome"] for r in _db().table(tabela).select("nome").order("id").execute().data]


def _normalizar(valor: str, tabela: str, tipo: str) -> str:
    """Devolve o nome oficial (ex.: 'rpg' -> 'RPG') ou levanta ValueError listando os válidos."""
    validos = _nomes(tabela)
    for v in validos:
        if v.lower() == valor.lower().strip():
            return v
    raise ValueError(f"{tipo} '{valor}' não existe. Válidos: {', '.join(validos)}.")


def _contem(coluna: str, valor: str) -> tuple[str, str, str]:
    # Filtro "array contém" do PostgREST; aspas para nomes com espaço (ex.: "Steam Deck").
    return coluna, "cs", '{"%s"}' % valor


@mcp.tool
def buscar_jogos(termo: str) -> list[dict]:
    """Busca jogos cujo título contém o termo (sem diferenciar maiúsculas/minúsculas)."""
    termo = termo.strip().replace("%", "")
    return (
        _db().table("jogos_completos").select(CAMPOS_RESUMO)
        .ilike("titulo", f"%{termo}%").order("titulo").execute().data
    )


@mcp.tool
def detalhes_jogo(jogo_id: int) -> dict:
    """Retorna todos os dados de um jogo pelo id: descrição, lançamento, desenvolvedora, publicadora,
    classificação, capa, preço atual, promoção vigente, menor preço histórico e histórico de preços."""
    linhas = _db().table("jogos_completos").select("*").eq("id", jogo_id).limit(1).execute().data
    if not linhas:
        raise ValueError(f"Jogo {jogo_id} não existe. Use buscar_jogos ou filtrar_jogos para achar o id.")
    jogo = linhas[0]
    jogo["historico_precos"] = historico_precos(jogo_id)
    return jogo


@mcp.tool
def historico_precos(jogo_id: int) -> list[dict]:
    """Lista as mudanças de preço de um jogo em ordem cronológica (lançamento, promoções, reduções)."""
    return (
        _db().table("historico_precos").select("data, preco, evento")
        .eq("jogo_id", jogo_id).order("data").execute().data
    )


@mcp.tool
def listar_generos() -> list[str]:
    """Lista os gêneros de jogos disponíveis na loja."""
    return _nomes("generos")


@mcp.tool
def listar_plataformas() -> list[str]:
    """Lista as plataformas suportadas pela loja."""
    return _nomes("plataformas")


@mcp.tool
def jogos_por_genero(genero: str) -> list[dict]:
    """Lista os jogos de um gênero (ex.: RPG, Terror). Falha se o gênero não existir."""
    return filtrar_jogos(genero=genero)


@mcp.tool
def jogos_por_plataforma(plataforma: str) -> list[dict]:
    """Lista os jogos que rodam numa plataforma (ex.: Linux, Steam Deck). Falha se a plataforma não existir."""
    return filtrar_jogos(plataforma=plataforma)


@mcp.tool
def jogos_em_promocao() -> list[dict]:
    """Lista os jogos com promoção vigente hoje, do maior para o menor desconto."""
    return filtrar_jogos(apenas_promocao=True, ordenar_por="desconto")


@mcp.tool
def filtrar_jogos(
    genero: str | None = None,
    plataforma: str | None = None,
    preco_maximo: float | None = None,
    ano_minimo: int | None = None,
    desenvolvedora: str | None = None,
    apenas_promocao: bool = False,
    ordenar_por: Literal["nota", "preco", "lancamento", "titulo", "desconto"] = "nota",
    limite: int = 50,
) -> list[dict]:
    """Filtra jogos combinando gênero, plataforma, preço máximo (em reais, já com desconto),
    ano mínimo de lançamento, desenvolvedora (parte do nome) e só promoções. Todos os filtros são opcionais."""
    consulta = _db().table("jogos_completos").select(CAMPOS_RESUMO)
    if genero:
        consulta = consulta.filter(*_contem("generos", _normalizar(genero, "generos", "Gênero")))
    if plataforma:
        consulta = consulta.filter(*_contem("plataformas", _normalizar(plataforma, "plataformas", "Plataforma")))
    if preco_maximo is not None:
        consulta = consulta.lte("preco_atual", preco_maximo)
    if ano_minimo is not None:
        consulta = consulta.gte("data_lancamento", f"{ano_minimo}-01-01")
    if desenvolvedora:
        consulta = consulta.ilike("desenvolvedora", f"%{desenvolvedora.strip()}%")
    if apenas_promocao:
        consulta = consulta.gt("desconto_pct", 0)
    coluna, desc = ORDENACAO[ordenar_por]
    return consulta.order(coluna, desc=desc).limit(max(1, min(limite, 100))).execute().data


@mcp.resource("steam://promocoes")
def promocoes() -> str:
    """Promoções vigentes na Steam fictícia."""
    jogos = jogos_em_promocao()
    if not jogos:
        return "Nenhuma promoção vigente hoje."
    linhas = [
        f"- {j['titulo']}: -{j['desconto_pct']}% (de R$ {j['preco_base']:.2f} por R$ {j['preco_atual']:.2f})"
        for j in jogos
    ]
    return "Promoções vigentes:\n" + "\n".join(linhas)


@mcp.prompt
def recomendar_jogo(genero: str, plataforma: str) -> str:
    """Pede uma recomendação de jogo de um gênero para uma plataforma."""
    return (
        f"Quero uma recomendação de jogo de {genero} que rode em {plataforma}. "
        "Use as ferramentas da loja para ver as opções, compare preço atual, menor preço histórico e nota, "
        "e indique o melhor custo-benefício explicando o porquê."
    )


if __name__ == "__main__":
    mcp.run()  # stdio (para HTTP, use app.py)
