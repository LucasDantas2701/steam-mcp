"""Carrega o catálogo da Steam fictícia no Supabase (tabelas + capas no Storage).

Pré-requisitos:
  1. Ter rodado supabase/schema.sql no SQL Editor do Supabase.
  2. .env com SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY (chave SECRETA, só na sua máquina).

Rodar (de dentro de steam_ficticia/):  python scripts/seed.py
Pode rodar de novo: atualiza os jogos e regera histórico e promoções (relativas à data de hoje).
"""
import os
import random
import sys
import unicodedata
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).parent.parent / ".env")

BUCKET = "capas"
HOJE = date.today()
TODAS = ["Windows", "macOS", "Linux", "Steam Deck"]

GENEROS = ["RPG", "Ação", "Aventura", "Corrida", "Simulação", "Estratégia",
           "Terror", "Indie", "Puzzle", "Esportes", "Plataforma"]

# (título, desenvolvedora, publicadora, lançamento, preço base, nota, classificação, gêneros, plataformas, descrição)
CATALOGO = [
    ("Cavaleiros de Aurora", "Estúdio Boreal", "Boreal Publishing", "2024-03-14", 89.90, 9.1, "14",
     ["RPG", "Aventura"], ["Windows", "Linux", "Steam Deck"],
     "RPG de fantasia em mundo aberto onde cada aurora muda as regras do reino."),
    ("Neon Drift 2077", "Pixel Turbo", "Pixel Turbo", "2025-06-05", 79.90, 8.4, "10",
     ["Corrida", "Ação"], ["Windows", "Steam Deck"],
     "Corridas ilegais numa megacidade cyberpunk, com drift e combate entre carros."),
    ("Fazendinha do Vale", "Coruja Games", "Coruja Games", "2023-02-09", 24.99, 9.4, "L",
     ["Simulação", "Indie"], TODAS,
     "Cuide de uma fazenda, faça amizade com a vila e descubra os segredos do vale."),
    ("Ecos da Mansão Vazia", "Sombra Interativa", "Noite Eterna", "2022-10-28", 39.90, 7.8, "16",
     ["Terror", "Aventura"], ["Windows"],
     "Terror psicológico numa mansão que reorganiza seus cômodos a cada visita."),
    ("Impérios de Ferro", "Legião Studios", "Atlas Entertainment", "2025-01-22", 129.90, 8.7, "12",
     ["Estratégia"], ["Windows", "macOS"],
     "Estratégia 4X: conduza um império da idade do bronze à era industrial."),
    ("Cubo Quântico", "Mente Leve", "Mente Leve", "2021-05-18", 14.90, 8.9, "L",
     ["Puzzle", "Indie"], ["Windows", "macOS", "Linux"],
     "Quebra-cabeças em que cada face do cubo existe numa linha do tempo diferente."),
    ("Lendas do Abismo", "Forja Digital", "Atlas Entertainment", "2026-02-26", 199.90, 9.0, "16",
     ["RPG", "Ação"], ["Windows", "Steam Deck"],
     "RPG de ação sombrio, com combate exigente e chefes colossais."),
    ("Pequeno Astronauta", "Órbita Zero", "Órbita Zero", "2024-08-01", 19.90, 8.2, "L",
     ["Aventura", "Indie", "Puzzle"], TODAS,
     "Um astronauta mirim explora planetas minúsculos, cada um com a sua própria gravidade."),
    ("Caminhoneiro Amazônico", "BR-319 Games", "BR-319 Games", "2023-11-07", 49.90, 7.5, "L",
     ["Simulação", "Corrida"], ["Windows", "Linux"],
     "Entregue cargas pela BR-319 enfrentando lama, chuva e travessias de balsa."),
    ("Torre dos Mil Andares", "Masmorra Indie", "Masmorra Indie", "2022-04-12", 34.90, 8.8, "12",
     ["RPG", "Estratégia", "Indie"], ["Windows", "Linux", "Steam Deck"],
     "Roguelike de cartas: suba a torre montando seu baralho a cada andar."),
    ("Hospital Abandonado VR", "Sombra Interativa", "Noite Eterna", "2021-10-15", 29.90, 6.9, "18",
     ["Terror"], ["Windows"],
     "Explore um hospital desativado onde as luzes só acendem quando você não está olhando."),
    ("Comandante Galáctico", "Nebulosa Soft", "Nebulosa Soft", "2026-04-09", 69.90, 8.1, "12",
     ["Estratégia", "Simulação"], ["Windows", "macOS", "Linux"],
     "Comande uma frota estelar, negocie com facções alienígenas e colonize sistemas."),
    ("Futebol de Várzea Manager", "Bola Murcha Studio", "Bola Murcha Studio", "2024-05-30", 39.90, 8.0, "L",
     ["Esportes", "Simulação"], TODAS,
     "Gerencie um time de várzea do campo de terra até a primeira divisão."),
    ("Saltimbanco", "Trupe Pixel", "Trupe Pixel", "2020-09-03", 27.90, 9.2, "L",
     ["Plataforma", "Indie"], TODAS,
     "Plataforma de precisão estrelado por um acrobata de circo em fuga."),
    ("Operação Tempestade", "Brigada 7", "Atlas Entertainment", "2025-10-16", 249.90, 7.9, "18",
     ["Ação"], ["Windows"],
     "Tiro tático em equipe com destruição de cenário e missões cooperativas."),
    ("Cozinha Caótica", "Panela de Pressão", "Coruja Games", "2023-07-20", 32.90, 8.6, "L",
     ["Simulação", "Indie"], ["Windows", "macOS", "Steam Deck"],
     "Cozinha cooperativa para até quatro jogadores, com pedidos cada vez mais absurdos."),
    ("Reino de Areia", "Estúdio Boreal", "Boreal Publishing", "2019-11-21", 59.90, 8.3, "12",
     ["RPG", "Estratégia"], ["Windows", "macOS", "Linux"],
     "RPG tático num deserto de cidades-oásis em guerra pela água."),
    ("Skate Urbano 3", "Pixel Turbo", "Pixel Turbo", "2022-08-25", 59.90, 7.7, "L",
     ["Esportes"], ["Windows", "Steam Deck"],
     "Manobras, pistas criadas pela comunidade e campeonatos pelas ruas da cidade."),
    ("Labirinto de Espelhos", "Mente Leve", "Mente Leve", "2025-03-04", 22.90, 9.0, "L",
     ["Puzzle"], TODAS,
     "Guie feixes de luz por labirintos de espelhos que se movem com você."),
    ("Noite no Farol", "Sombra Interativa", "Noite Eterna", "2024-10-31", 44.90, 8.5, "16",
     ["Terror", "Aventura", "Indie"], ["Windows", "Linux", "Steam Deck"],
     "Uma faroleira isolada precisa manter a luz acesa até o amanhecer."),
    ("Piratas do Rio Negro", "Boto Studios", "Boreal Publishing", "2021-03-23", 74.90, 8.1, "12",
     ["Aventura", "Ação"], ["Windows", "Steam Deck"],
     "Navegue pelos rios da Amazônia atrás de tesouros e lendas ribeirinhas."),
    ("Rali dos Sertões", "BR-319 Games", "BR-319 Games", "2026-07-14", 89.90, 8.3, "L",
     ["Corrida", "Esportes"], ["Windows", "Linux", "Steam Deck"],
     "Rali off-road atravessando o sertão, com clima dinâmico e etapas de vários dias."),
    ("Cidade em Blocos", "Nebulosa Soft", "Nebulosa Soft", "2018-06-12", 49.90, 8.9, "L",
     ["Simulação", "Estratégia"], ["Windows", "macOS", "Linux"],
     "Construa e administre uma metrópole, do trânsito ao saneamento."),
    ("Ninja de Papel", "Trupe Pixel", "Trupe Pixel", "2023-04-27", 19.90, 8.4, "10",
     ["Plataforma", "Ação", "Indie"], TODAS,
     "Um ninja de origami corta, dobra e desliza por fases desenhadas à mão."),
    ("Crônicas de Vidro", "Forja Digital", "Atlas Entertainment", "2020-12-10", 119.90, 8.6, "14",
     ["RPG", "Aventura"], ["Windows", "macOS"],
     "RPG narrativo em que cada escolha racha ou restaura um mundo feito de vidro."),
    ("Detetive de Bairro", "Coruja Games", "Coruja Games", "2025-08-21", 29.90, 8.7, "10",
     ["Aventura", "Puzzle", "Indie"], TODAS,
     "Resolva os pequenos mistérios da vizinhança interrogando moradores e juntando pistas."),
    ("Arena dos Titãs", "Brigada 7", "Atlas Entertainment", "2024-01-18", 59.90, 7.2, "14",
     ["Ação", "Estratégia"], ["Windows"],
     "Batalhas 5 contra 5 entre titãs com habilidades que mudam a arena."),
    ("Jardim Zen", "Mente Leve", "Mente Leve", "2019-02-14", 12.90, 8.0, "L",
     ["Simulação", "Puzzle", "Indie"], TODAS,
     "Monte jardins tranquilos combinando pedras, água e plantas, sem pressa."),
    ("Último Trem", "Sombra Interativa", "Noite Eterna", "2026-09-18", 64.90, 8.8, "16",
     ["Terror", "Ação"], ["Windows", "Steam Deck"],
     "Sobreviva à viagem no último trem da noite, vagão por vagão."),
    ("Motoboy Simulator", "Panela de Pressão", "Coruja Games", "2022-02-03", 24.90, 7.4, "L",
     ["Simulação", "Corrida", "Indie"], ["Windows", "Linux", "Steam Deck"],
     "Faça entregas pela cidade, desvie do trânsito e mantenha a avaliação nas alturas."),
]

# Eventos anuais de promoção: (mês, dia, nome, duração em dias)
EVENTOS = [(6, 26, "Promoção de Verão", 14), (11, 27, "Black Friday", 5), (12, 19, "Promoção de Inverno", 14)]
PROMO_ATUAL = "Festival de Outono"

CORES = {
    "RPG": ("#3a1c71", "#d76d77"), "Ação": ("#7f1d1d", "#f97316"), "Aventura": ("#064e3b", "#10b981"),
    "Corrida": ("#0f172a", "#06b6d4"), "Simulação": ("#14532d", "#a3e635"), "Estratégia": ("#1e3a8a", "#93c5fd"),
    "Terror": ("#0a0a0a", "#991b1b"), "Indie": ("#581c87", "#f472b6"), "Puzzle": ("#134e4a", "#fde047"),
    "Esportes": ("#1e40af", "#facc15"), "Plataforma": ("#9a3412", "#fde68a"),
}


def slug(titulo: str) -> str:
    s = unicodedata.normalize("NFKD", titulo).encode("ascii", "ignore").decode().lower()
    return "-".join("".join(c if c.isalnum() else " " for c in s).split())


def gerar_capa(titulo: str, dev: str, genero: str, rnd: random.Random) -> bytes:
    """Capa 460x215 (formato 'header' da Steam) em SVG, com gradiente pela cor do gênero principal."""
    c1, c2 = CORES[genero]
    linhas, atual = [], ""
    for palavra in titulo.upper().split():
        if len(atual) + len(palavra) > 16 and atual:
            linhas.append(atual)
            atual = palavra
        else:
            atual = f"{atual} {palavra}".strip()
    linhas.append(atual)
    circulos = "".join(
        f'<circle cx="{rnd.randint(0, 460)}" cy="{rnd.randint(0, 215)}" r="{rnd.randint(20, 110)}" '
        f'fill="#fff" opacity="{rnd.uniform(0.03, 0.12):.2f}"/>'
        for _ in range(7)
    )
    y0 = 108 - (len(linhas) - 1) * 21
    textos = "".join(
        f'<text x="24" y="{y0 + i * 42}" font-size="36" font-weight="800">{escape(l)}</text>'
        for i, l in enumerate(linhas)
    )
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="460" height="215" viewBox="0 0 460 215">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
        f'<rect width="460" height="215" fill="url(#g)"/>{circulos}'
        '<g font-family="Segoe UI, Arial, sans-serif" fill="#fff">'
        f'{textos}<text x="24" y="196" font-size="13" opacity=".8" letter-spacing="2">{escape(dev.upper())}</text>'
        "</g></svg>"
    )
    return svg.encode()


def gerar_historico(lancamento: date, preco_base: float, rnd: random.Random) -> list[dict]:
    """Gera o histórico de preços. Jogos antigos podem ter sido lançados mais caros e baixado de preço."""
    preco_lancamento = preco_base
    data_reducao = None
    if (HOJE - lancamento).days > 2 * 365 and rnd.random() < 0.5:
        preco_lancamento = int(preco_base * rnd.choice([1.25, 1.5])) + 0.90  # ex.: 112,90
        data_reducao = lancamento + timedelta(days=rnd.randint(500, 700))

    historico = [{"data": lancamento, "preco": preco_lancamento, "evento": "Lançamento"}]
    if data_reducao:
        historico.append({"data": data_reducao, "preco": preco_base, "evento": "Redução permanente de preço"})

    for ano in range(lancamento.year, HOJE.year + 1):
        for mes, dia, nome, duracao in EVENTOS:
            inicio, fim = date(ano, mes, dia), date(ano, mes, dia) + timedelta(days=duracao)
            if inicio < lancamento + timedelta(days=60) or fim >= HOJE or rnd.random() > 0.6:
                continue
            vigente = preco_base if data_reducao is None or inicio >= data_reducao else preco_lancamento
            # quanto mais velho o jogo, maior o desconto
            idade = (inicio - lancamento).days / 365
            desconto = rnd.choice([10, 15, 20, 25] if idade < 1 else [25, 33, 40, 50, 60, 75])
            historico.append({"data": inicio, "preco": round(vigente * (100 - desconto) / 100, 2),
                              "evento": f"{nome} (-{desconto}%)"})
            historico.append({"data": fim, "preco": vigente, "evento": "Fim da promoção"})

    historico.sort(key=lambda h: h["data"])
    return historico


def main():
    url, chave = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not chave:
        sys.exit("Defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY no .env (veja o .env.example).")
    db = create_client(url, chave)

    try:
        db.storage.create_bucket(BUCKET, options={"public": True})
        print(f"Bucket '{BUCKET}' criado.")
    except Exception as e:
        if "exist" not in str(e).lower():
            raise
    storage = db.storage.from_(BUCKET)

    db.table("generos").upsert([{"id": i, "nome": g} for i, g in enumerate(GENEROS, 1)]).execute()
    db.table("plataformas").upsert([{"id": i, "nome": p} for i, p in enumerate(TODAS, 1)]).execute()

    rnd = random.Random(42)  # mesma semente -> mesmos dados toda vez
    jogos, generos, plataformas, historicos, promocoes = [], [], [], [], []
    ids_em_promocao = set(rnd.sample(range(1, len(CATALOGO) + 1), 9))

    for jogo_id, (titulo, dev, pub, lanc, preco, nota, classif, gens, plats, desc) in enumerate(CATALOGO, 1):
        lancamento = date.fromisoformat(lanc)
        arquivo = f"{slug(titulo)}.svg"
        storage.upload(arquivo, gerar_capa(titulo, dev, gens[0], rnd),
                       {"content-type": "image/svg+xml", "upsert": "true", "cache-control": "3600"})
        jogos.append({
            "id": jogo_id, "titulo": titulo, "descricao": desc, "desenvolvedora": dev, "publicadora": pub,
            "data_lancamento": lanc, "preco_base": preco, "nota": nota, "classificacao": classif,
            "capa_url": storage.get_public_url(arquivo).rstrip("?"),
        })
        generos += [{"jogo_id": jogo_id, "genero_id": GENEROS.index(g) + 1} for g in gens]
        plataformas += [{"jogo_id": jogo_id, "plataforma_id": TODAS.index(p) + 1} for p in plats]

        historico = gerar_historico(lancamento, preco, rnd)
        if jogo_id in ids_em_promocao and (HOJE - lancamento).days > 30:
            desconto = rnd.choice([20, 25, 33, 40, 50, 60])
            inicio = HOJE - timedelta(days=3)
            promocoes.append({"jogo_id": jogo_id, "nome": PROMO_ATUAL, "desconto_pct": desconto,
                              "inicio": inicio.isoformat(), "fim": (HOJE + timedelta(days=7)).isoformat()})
            historico.append({"data": inicio, "preco": round(preco * (100 - desconto) / 100, 2),
                              "evento": f"{PROMO_ATUAL} (-{desconto}%)"})
        historicos += [{"jogo_id": jogo_id, **h, "data": h["data"].isoformat()} for h in historico]
        print(f"  {jogo_id:2}. {titulo} ({len(historico)} preços)")

    ids = [j["id"] for j in jogos]
    db.table("jogos").upsert(jogos).execute()
    for tabela in ("jogos_generos", "jogos_plataformas", "historico_precos", "promocoes"):
        db.table(tabela).delete().in_("jogo_id", ids).execute()
    db.table("jogos_generos").insert(generos).execute()
    db.table("jogos_plataformas").insert(plataformas).execute()
    db.table("historico_precos").insert(historicos).execute()
    if promocoes:
        db.table("promocoes").insert(promocoes).execute()

    print(f"\nOK: {len(jogos)} jogos, {len(historicos)} registros de preço, {len(promocoes)} promoções ativas.")


if __name__ == "__main__":
    main()
