-- Esquema da Steam fictícia. Rode no Supabase: SQL Editor -> New query -> cole e execute.
-- Pode rodar de novo: apaga e recria tudo (os dados voltam com  python scripts/seed.py).

drop view if exists jogos_completos;
drop table if exists promocoes, historico_precos, jogos_plataformas, jogos_generos, jogos, plataformas, generos cascade;

create table generos (
  id   smallint primary key,
  nome text not null unique
);

create table plataformas (
  id   smallint primary key,
  nome text not null unique
);

create table jogos (
  id               integer primary key,
  titulo           text not null,
  descricao        text not null,
  desenvolvedora   text not null,
  publicadora      text not null,
  data_lancamento  date not null,
  preco_base       numeric(8, 2) not null,  -- preço cheio atual (sem promoção)
  nota             numeric(3, 1) not null check (nota between 0 and 10),
  classificacao    text not null,           -- L, 10, 12, 14, 16, 18
  capa_url         text
);

create table jogos_generos (
  jogo_id   integer  references jogos (id) on delete cascade,
  genero_id smallint references generos (id) on delete cascade,
  primary key (jogo_id, genero_id)
);

create table jogos_plataformas (
  jogo_id       integer  references jogos (id) on delete cascade,
  plataforma_id smallint references plataformas (id) on delete cascade,
  primary key (jogo_id, plataforma_id)
);

-- Cada linha é uma mudança de preço (lançamento, promoções, fim de promoção, reduções).
create table historico_precos (
  id      bigint generated always as identity primary key,
  jogo_id integer not null references jogos (id) on delete cascade,
  data    date not null,
  preco   numeric(8, 2) not null,
  evento  text not null
);
create index on historico_precos (jogo_id, data);

create table promocoes (
  id           bigint generated always as identity primary key,
  jogo_id      integer not null references jogos (id) on delete cascade,
  nome         text not null,
  desconto_pct smallint not null check (desconto_pct between 1 and 99),
  inicio       date not null,
  fim          date not null
);

-- Visão "pronta para consumo": gêneros/plataformas como listas, promoção vigente e preço atual.
create view jogos_completos with (security_invoker = on) as
select
  j.*,
  coalesce((select array_agg(g.nome order by g.nome)
              from jogos_generos jg join generos g on g.id = jg.genero_id
             where jg.jogo_id = j.id), '{}') as generos,
  coalesce((select array_agg(p.nome order by p.nome)
              from jogos_plataformas jp join plataformas p on p.id = jp.plataforma_id
             where jp.jogo_id = j.id), '{}') as plataformas,
  coalesce(pr.desconto_pct, 0) as desconto_pct,
  pr.nome as promocao,
  pr.fim  as promocao_ate,
  round(j.preco_base * (100 - coalesce(pr.desconto_pct, 0)) / 100.0, 2) as preco_atual,
  least(
    (select min(h.preco) from historico_precos h where h.jogo_id = j.id),
    round(j.preco_base * (100 - coalesce(pr.desconto_pct, 0)) / 100.0, 2)
  ) as menor_preco_historico
from jogos j
left join lateral (
  select p.desconto_pct, p.nome, p.fim
    from promocoes p
   where p.jogo_id = j.id and current_date between p.inicio and p.fim
   order by p.desconto_pct desc
   limit 1
) pr on true;

-- Segurança: qualquer pessoa pode LER (chave pública/anon); só a chave secreta (seed) escreve.
alter table generos           enable row level security;
alter table plataformas       enable row level security;
alter table jogos             enable row level security;
alter table jogos_generos     enable row level security;
alter table jogos_plataformas enable row level security;
alter table historico_precos  enable row level security;
alter table promocoes         enable row level security;

create policy "leitura publica" on generos           for select using (true);
create policy "leitura publica" on plataformas       for select using (true);
create policy "leitura publica" on jogos             for select using (true);
create policy "leitura publica" on jogos_generos     for select using (true);
create policy "leitura publica" on jogos_plataformas for select using (true);
create policy "leitura publica" on historico_precos  for select using (true);
create policy "leitura publica" on promocoes         for select using (true);

grant select on all tables in schema public to anon, authenticated;
grant select on jogos_completos to anon, authenticated;
