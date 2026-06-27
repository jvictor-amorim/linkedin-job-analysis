#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dashboard_linkedin.py — gera um carrossel de imagens (PNG) para publicação no
LinkedIn a partir das vagas de Dados armazenadas no PostgreSQL.

Narrativa: "Skills x Senioridade" — como o conjunto de skills mais pedidas muda
entre júnior, pleno e sênior (o que estudar para subir de nível).

Fonte: tabelas `jobs` e `job_skills` (ver sql/schema.sql). A senioridade NÃO
existe no banco; é derivada do título da vaga em `detect_seniority`.

Uso:
    python analysis/dashboard_linkedin.py            # gera os PNGs
    python analysis/dashboard_linkedin.py --validate # só inspeciona os dados

Pré-requisitos: Postgres no ar (credenciais DB_* via .env/ambiente) e os pacotes
unidecode, matplotlib, pandas, psycopg2.
"""

import argparse
import re
import sys
import warnings
from pathlib import Path

import pandas as pd
from unidecode import unidecode

# pd.read_sql avisa que prefere SQLAlchemy; com psycopg2 funciona bem. Silencia.
warnings.filterwarnings("ignore", message=".*only supports SQLAlchemy.*")

# Bootstrap: coloca a raiz do repo no sys.path para importar `common`.
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from common import db  # noqa: E402

OUTPUT_DIR = _root / "output" / "carousel"

# ---------------------------------------------------------------------------
# Soft skills (mesmo conjunto usado no notebook). Tudo que não estiver aqui é
# considerado skill técnica.
# ---------------------------------------------------------------------------
SOFT_SKILLS = {
    "Comunicação",
    "Trabalho em Equipe",
    "Proatividade",
    "Resolução de Problemas",
    "Pensamento Analítico",
    "Organização",
    "Autonomia",
    "Liderança",
    "Curiosidade",
    "Storytelling",
    "Visão Estratégica",
}
# Versão sem acento para casar com o que vem do banco, seja qual for a grafia.
_SOFT_SKILLS_NORM = {unidecode(s).lower() for s in SOFT_SKILLS}

# Nomes canônicos no banco vêm sem acento; recupera a grafia bonita para exibir.
_DISPLAY = {unidecode(s).lower(): s for s in SOFT_SKILLS}
_DISPLAY.update({"ingles": "Inglês", "estatistica": "Estatística"})


def _pretty(skill) -> str:
    """Rótulo de exibição (acentuado) para a skill canônica do banco."""
    return _DISPLAY.get(unidecode(str(skill)).lower(), str(skill))

# Cargos que NÃO entram na análise de carreira de dados.
EXCLUDED_POSITIONS = {"Not Data Role", "Data Talent Pool"}

CATEGORIAS = {
    "Data Analyst", "Data Engineer", "BI Analyst", "Data Intern",
    "Analytics Engineer", "Data Scientist", "Data Architect",
    "Data Leadership", "Data Product", "Data Governance",
    "Data Talent Pool", "Not Data Role",
}


def remover_acentos(texto: str) -> str:
    return unidecode(str(texto))


def normalize_position(position):
    """Agrupa o título da vaga em uma das 12 categorias de cargo de dados.

    Portado do notebooks/index.ipynb (célula aee414ce) — versão com fallback
    conservador para "Not Data Role".
    """
    if str(position) in CATEGORIAS:
        return str(position)

    p = remover_acentos(str(position).lower().strip())
    p = re.sub(r"[()/|.,]", " ", p)
    p = re.sub(r"\s+", " ", p).strip()

    if "banco de talentos" in p:
        return "Data Talent Pool"

    if any(x in p for x in [
        "analista de ia", "consultor ti - ia", "consultor ti ia",
        "analista de monitoramento", "prevencao de perdas",
        "analista de sustentabilidade", "analista administrativo",
        "relacoes institucionais", "analista de melhoria continua",
        "analista de gestao", "analista sistema de gestao",
        "analista de controle e gestao", "analista de cadastro",
        "analista nto", "engenheiro de sistemas", "analista de sistemas jr",
        "coletor de dados", "bolsista de inovacao", "assistente de qualidade",
        "analista de atrativos", "analista jr de projetos de engenharia",
        "servicos externos",
    ]):
        return "Not Data Role"

    if any(x in p for x in [
        "gerente de dados", "lead dados", "lead de dados", "data lead",
        "head of data", "tech lead", "data engineering lead",
        "data analytics coordinator", "data science coordinator",
        "coordenador de dados", "coordenador de dados de mercado",
        "engineering manager", "data leadership",
    ]):
        return "Data Leadership"

    if any(x in p for x in [
        "data product owner", "data product manager", "data products specialist",
    ]):
        return "Data Product"

    if any(x in p for x in [
        "data architect", "cloud data architect", "arquiteto de dados",
    ]):
        return "Data Architect"

    if any(x in p for x in [
        "governanca de dados", "data governance",
        "commercial data governance analyst",
    ]):
        return "Data Governance"

    if any(x in p for x in [
        "data scientist", "staff data scientist", "data science",
        "cientista de dados", "cientista dados", "ciencia de dados",
        "machine learning", "mlops", "artificial intelligence",
        "inteligencia artificial", "genai", "generative ai", "ai engineer",
        "especialista em ciencia de dados", "forward deployed data scientist",
        "python engineer - machine learning focus", "analista data science dados",
    ]):
        return "Data Scientist"

    if any(x in p for x in [
        "analytics engineer", "analytics engineer iii", "analytics engineer junior",
        "staff analytics engineer", "senior analytics engineer",
        "data analytics engineer", "data analyst engineer",
        "engenharia de analytics", "engenheiro de analytics",
        "engenharia de dados & analytics", "engenharia de dados e analytics",
        "plataforma de analytics",
    ]):
        return "Analytics Engineer"

    if any(x in p for x in [
        "data engineer", "senior data engineer", "junior data engineer",
        "staff data engineer", "data engineer specialist",
        "data engineer consultant", "data engineer trainee",
        "engenheiro de dados", "engenheira de dados", "engenheiro a de dados",
        "engenharia de dados", "eng de dados", "engenheiro de banco de dados",
        "engenheiro de dados azure", "engenheiro de dados azure databricks",
        "engenheiro solucoes dados", "data solutions",
        "engenheiro de confiabilidade de banco de dados", "etl engineer",
        "etl data engineer", "desenvolvimento de etl", "dados e etl",
        "snowflake engineer", "data platform engineer",
        "senior data platform engineer", "plataforma de dados",
        "dataops engineer", "database reliability engineer",
        "senior database reliability engineer", "big data engineer",
        "data quality engineer", "data solutions engineer",
        "data management engineer", "data engineering specialist",
        "especialista engenharia de dados", "especialista engenharia dados",
        "especialista em engenharia de dados", "suporte de banco de dados",
        "suporte de banco dados", "dev banco dados", "dev banco de dados",
        "databricks",
    ]):
        return "Data Engineer"

    if any(x in p for x in [
        "business intelligence", "business intelligence analyst",
        "business intelligence specialist", " bi ", "de bi", "a bi",
        "power bi", "desenvolvedor de bi", "inteligencia comercial",
        "inteligencia de mercado", "inteligencia de negocios",
        "inteligencia competitiva", "inteligencia operacional",
        "people analytics", "data analytics", "data & analytics",
        "data visualization", "data visualization specialist",
        "consultor dados business intelligence", "martech analyst",
        "analytics intern", "specialista em analytics", "indicadores",
    ]):
        return "BI Analyst"

    if any(x in p for x in [
        "analista de dados", "analista dados", "analistas de dados",
        "data analyst", "data & ai analyst", "finance data analyst",
        "fraud data analyst", "industrial data analyst", "business data analyst",
        "hr data analyst", "etl data analyst", "datahub analyst",
        "data migration analyst", "data automation analyst",
        "data development analyst", "data intelligence analyst",
        "market intelligence analyst", "senior data analyst", "dados junior",
        "dados pleno", "dados senior", "pleno de dados", "senior de dados",
        "junior de dados", "planejamento dados", "planejamento e dados",
        "operacoes de dados", "projetos de dados", "projetos e dados",
        "validacao de dados", "migracao de dados", "inteligencia de dados",
        "especialista dados", "especialista em dados", "especialista de dados",
        "finance data specialist", "analista de modelagem de dados",
        "analista de base de dados", "analista de governanca de dados",
        "analista de dados dba", "coordenador de dados de mercado", "ti e dados",
        "logistico de dados", "analise de dados", "foco em dados", "data & ai",
    ]):
        return "Data Analyst"

    if any(x in p for x in ["intern", "estagi", "stagiaire", "trainee"]):
        return "Data Intern"

    return "Not Data Role"


# ---------------------------------------------------------------------------
# Senioridade — NÃO existe no banco; derivada do título.
# ---------------------------------------------------------------------------
LEVEL_LABELS = {
    "estagio": "Estágio",
    "junior": "Júnior",
    "pleno": "Pleno",
    "senior": "Sênior",
    "nao_especificado": "Não especificado",
}

# Ordem de carreira (para gráficos).
LEVEL_ORDER = ["estagio", "junior", "pleno", "senior"]

_LEVEL_PATTERNS = [
    ("estagio", r"\bestagi|\btrainee\b|\bintern\b|interns?hip|\bstagiaire\b"),
    ("junior", r"\bjr\b|\bjunior\b|\bjr\.|j[uú]nior"),
    ("pleno", r"\bpl\b|\bpl\.|\bpleno\b|\bplena\b|midlevel|mid-level|mid level|\bintermediate\b|intermediari[oa]"),
    ("senior", r"\bsr\b|\bsr\.|s[eê]nior\b|\bstaff\b"),
]


def detect_seniority(title) -> list:
    """Retorna a lista de níveis de senioridade detectados no título.

    Um título pode casar com mais de um nível (ex.: "Pleno/Sênior") — nesse caso
    a vaga conta em todos os níveis detectados. Sem nenhum marcador explícito,
    retorna ["nao_especificado"].
    """
    p = unidecode(str(title).lower())
    p = re.sub(r"[/|]", " ", p)  # "pleno/senior" -> "pleno senior"
    found = [lvl for lvl, pat in _LEVEL_PATTERNS if re.search(pat, p)]
    return found or ["nao_especificado"]


def _classify_skill_type(skill: str) -> str:
    return "soft" if unidecode(str(skill)).lower() in _SOFT_SKILLS_NORM else "tecnica"


def load_from_db() -> pd.DataFrame:
    """Lê jobs + job_skills do Postgres e devolve um DataFrame tidy.

    Uma linha por (vaga × skill × nível detectado). Colunas:
      job_id, title, work_mode, skill, position_group, level, tipo_skill
    """
    query = """
        SELECT j.job_id, j.title, j.work_mode, s.skill
        FROM jobs j
        JOIN job_skills s USING (job_id)
    """
    conn = db.get_connection()
    try:
        df = pd.read_sql(query, conn)
    finally:
        conn.close()

    df["position_group"] = df["title"].apply(normalize_position)
    df["tipo_skill"] = df["skill"].apply(_classify_skill_type)

    # Senioridade: explode a lista de níveis detectados em linhas.
    df["level"] = df["title"].apply(detect_seniority)
    df = df.explode("level", ignore_index=True)

    # Foca em carreira de dados.
    df = df[~df["position_group"].isin(EXCLUDED_POSITIONS)].reset_index(drop=True)
    return df


def skill_share_by_level(df: pd.DataFrame, level: str, tipo: str | None = None) -> pd.DataFrame:
    """% de vagas daquele nível que pedem cada skill (normalizado por job_id único)."""
    sub = df[df["level"] == level]
    if tipo is not None:
        sub = sub[sub["tipo_skill"] == tipo]
    total_jobs = sub["job_id"].nunique()
    if total_jobs == 0:
        return pd.DataFrame(columns=["skill", "n_jobs", "pct"])
    g = (
        sub.groupby("skill")["job_id"].nunique()
        .reset_index(name="n_jobs")
        .sort_values("n_jobs", ascending=False)
    )
    g["pct"] = 100 * g["n_jobs"] / total_jobs
    return g


def _validate(df: pd.DataFrame) -> None:
    print("\n=== Vagas por senioridade (job_id único) ===")
    lvl = df.groupby("level")["job_id"].nunique().sort_values(ascending=False)
    total = df["job_id"].nunique()
    for k, v in lvl.items():
        print(f"  {LEVEL_LABELS.get(k, k):20s} {v:5d}  ({100*v/total:4.1f}% das vagas)")
    print(f"  {'TOTAL (distinct)':20s} {total:5d}")

    print("\n=== detect_seniority em títulos de teste ===")
    for t in [
        "ANALISTA DE DADOS PL", "Engenheiro de Dados Jr.",
        "Engenheiro de Dados Pleno/Sênior", "Estágio - Dados",
        "Midlevel Analytics Engineer", "Analista de Dados",
        "Engenharia de Dados & Analytics Senior",
    ]:
        print(f"  {t:42s} -> {detect_seniority(t)}")

    print("\n=== Vagas por cargo (após filtro de carreira de dados) ===")
    print(df.groupby("position_group")["job_id"].nunique().sort_values(ascending=False).to_string())

    print("\n=== Top 8 skills Júnior vs Sênior (% das vagas do nível) ===")
    for lv in ("junior", "senior"):
        top = skill_share_by_level(df, lv, tipo="tecnica").head(8)
        print(f"\n  [{LEVEL_LABELS[lv]}]")
        for _, r in top.iterrows():
            print(f"    {r['skill']:22s} {r['pct']:4.0f}%  ({int(r['n_jobs'])})")

    print("\n=== Proximidade das vagas 'Não especificadas' ===")
    tops = {lv: set(skill_share_by_level(df, lv, "tecnica").head(10)["skill"]) 
            for lv in ("junior", "pleno", "senior")}
    df_ne = df[(df["level"] == "nao_especificado") & (df["tipo_skill"] == "tecnica")]
    jobs = df_ne.groupby("job_id")["skill"].apply(set)
    scores = {"junior": 0, "pleno": 0, "senior": 0}
    for skills in jobs:
        for lv in ("junior", "pleno", "senior"):
            scores[lv] += len(skills & tops[lv])
    total_scores = sum(scores.values())
    if total_scores > 0:
        for lv in ("junior", "pleno", "senior"):
            print(f"  {LEVEL_LABELS[lv]}: {scores[lv]/total_scores*100:.1f}%")


# ===========================================================================
# Plotagem — carrossel de PNGs (1080x1350 px, retrato 4:5)
# ===========================================================================
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

# Paleta de marca.
BG = "#0E1726"          # fundo (azul-petróleo escuro, premium no feed)
INK = "#F2F5FA"         # texto principal
MUTED = "#8FA1B6"       # texto secundário
BASE = "#2D6BF0"        # azul base das barras
HILITE = "#FF8A3D"      # laranja de destaque (#1 / skill-chave)
GRID = "#22304A"

# Cores por senioridade (gráficos comparativos).
LEVEL_COLORS = {
    "estagio": "#64D2A6",
    "junior": "#36C28B",
    "pleno": "#2D6BF0",
    "senior": "#9B7BFF",
    "nao_especificado": "#5A6B82",
}

DPI = 150
FIGSIZE = (10.8, 9.0)   # 10.8*150 x 9.0*150 = 1620 x 1350 (Mais larga)
HANDLE = "Dados coletados do LinkedIn"


def _new_fig():
    fig = plt.figure(figsize=FIGSIZE, dpi=DPI)
    fig.patch.set_facecolor(BG)
    return fig


def _header(fig, kicker, title, subtitle=None, title_fs=26):
    """Cabeçalho padrão: tarja superior + kicker + título + subtítulo."""
    fig.text(0.07, 0.945, kicker.upper(), color=HILITE, fontsize=13,
             fontweight="bold", family="DejaVu Sans")
    fig.text(0.07, 0.90, title, color=INK, fontsize=title_fs, fontweight="bold",
             family="DejaVu Sans", va="top")
    if subtitle:
        fig.text(0.07, 0.815, subtitle, color=MUTED, fontsize=13.5,
                 family="DejaVu Sans", va="top")


def _footer(fig):
    fig.text(0.07, 0.035, HANDLE, color=MUTED, fontsize=10.5,
             family="DejaVu Sans")


def _axes(fig, rect=(0.30, 0.10, 0.63, 0.62)):
    ax = fig.add_axes(rect)
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    return ax


def _barh(ax, labels, values, colors, value_fmt="{:.0f}%"):
    """Barras horizontais com rótulo de valor, melhor no topo."""
    y = range(len(labels))
    ax.barh(y, values, color=colors, height=0.66, zorder=3)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, color=INK, fontsize=13.5)
    ax.invert_yaxis()
    ax.set_xticks([])
    xmax = max(values) if len(values) else 1
    ax.set_xlim(0, xmax * 1.16)
    for yi, v in zip(y, values):
        ax.text(v + xmax * 0.02, yi, value_fmt.format(v), va="center",
                ha="left", color=INK, fontsize=12.5, fontweight="bold")


def _save(fig, name):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    fig.savefig(path, facecolor=BG, dpi=DPI)
    plt.close(fig)
    print(f"  ✓ {path.relative_to(_root)}")
    return path


# ---------------------------------------------------------------------------
# Slides
# ---------------------------------------------------------------------------
def slide_capa(df):
    fig = _new_fig()
    n_jobs = df["job_id"].nunique()
    fig.text(0.07, 0.78, "SKILLS × SENIORIDADE", color=HILITE, fontsize=15,
             fontweight="bold")
    fig.text(0.07, 0.70, "O que o mercado de\nDados pede em cada\nsenioridade?",
             color=INK, fontsize=40, fontweight="bold", va="top", linespacing=1.05)
    fig.text(0.07, 0.36,
             f"Uma análise de {n_jobs:,} vagas de Dados\n"
             "publicadas no LinkedIn (Brasil).".replace(",", "."),
             color=MUTED, fontsize=17, va="top", linespacing=1.4)
    fig.text(0.07, 0.20, "Arrasta para o lado  →", color=HILITE, fontsize=15,
             fontweight="bold")
    _footer(fig)
    return _save(fig, "01_capa.png")


def slide_amostra(df):
    fig = _new_fig()
    counts = (df.groupby("level")["job_id"].nunique())
    order = ["estagio", "junior", "pleno", "senior", "nao_especificado"]
    labels = [LEVEL_LABELS[k] for k in order]
    values = [int(counts.get(k, 0)) for k in order]
    colors = [LEVEL_COLORS[k] for k in order]
    total = df["job_id"].nunique()
    pct_ne = 100 * counts.get("nao_especificado", 0) / total

    _header(fig, "A amostra", "De onde vêm os números",
            f"{total} vagas de carreira em Dados, classificadas pela\n"
            "senioridade declarada no título da vaga.")
    ax = _axes(fig, rect=(0.30, 0.22, 0.63, 0.50))
    _barh(ax, labels, values, colors, value_fmt="{:.0f}")
    fig.text(0.07, 0.145,
             f"⚠  {pct_ne:.0f}% das vagas não trazem o nível no título "
             "(“Não especificado”).\nNo próximo slide analisamos o perfil dessas vagas.",
             color=MUTED, fontsize=11.5, va="top", linespacing=1.4)
    _footer(fig)
    return _save(fig, "02_amostra.png")


def slide_nao_especificado(df):
    """Analisa as vagas sem senioridade e calcula a proximidade com os outros níveis."""
    fig = _new_fig()
    
    tops = {lv: set(skill_share_by_level(df, lv, "tecnica").head(10)["skill"]) 
            for lv in ("junior", "pleno", "senior")}
            
    df_ne = df[(df["level"] == "nao_especificado") & (df["tipo_skill"] == "tecnica")]
    jobs = df_ne.groupby("job_id")["skill"].apply(set)
    
    scores = {"junior": 0, "pleno": 0, "senior": 0}
    for skills in jobs:
        for lv in ("junior", "pleno", "senior"):
            scores[lv] += len(skills & tops[lv])
            
    total = sum(scores.values())
    pcts = {lv: (scores[lv] / total * 100) if total > 0 else 0 for lv in ("junior", "pleno", "senior")}
    
    _header(fig, "Nível Oculto", "Perfil das vagas sem senioridade",
            f"Analisando o match das skills nas {len(jobs)} vagas \"Não especificadas\"\n"
            "com o Top 10 técnico de cada nível. Com quem elas mais parecem?")
            
    ax = _axes(fig, rect=(0.30, 0.22, 0.63, 0.50))
    
    order = ["junior", "pleno", "senior"]
    labels = [LEVEL_LABELS[lv] for lv in order]
    vals = [pcts[lv] for lv in order]
    colors = [LEVEL_COLORS[lv] for lv in order]
    
    _barh(ax, labels, vals, colors, value_fmt="{:.1f}%")
    
    fig.text(0.07, 0.145,
             "O percentual reflete a similaridade das exigências técnicas com o\n"
             "perfil padrão (Top 10) de cada senioridade no mercado.",
             color=MUTED, fontsize=11.5, va="top", linespacing=1.4)
             
    _footer(fig)
    return _save(fig, "03_nao_especificado.png")


def _slide_top_skills(df, level, idx):
    fig = _new_fig()
    top = skill_share_by_level(df, level, tipo="tecnica").head(10)
    n = df[df["level"] == level]["job_id"].nunique()
    colors = [HILITE if i == 0 else BASE for i in range(len(top))]
    _header(fig, f"Nível {LEVEL_LABELS[level]}",
            f"Top 10 skills — {LEVEL_LABELS[level]}",
            f"% das {n} vagas de {LEVEL_LABELS[level].lower()} que pedem cada skill técnica.")
    ax = _axes(fig)
    _barh(ax, [_pretty(s) for s in top["skill"]], top["pct"].tolist(), colors)
    _footer(fig)
    return _save(fig, f"{idx:02d}_top_{level}.png")


def slide_nucleo(df):
    """Skills que estão no top 10 técnico dos TRÊS níveis (o núcleo estável)."""
    fig = _new_fig()
    tops = {lv: set(skill_share_by_level(df, lv, "tecnica").head(10)["skill"])
            for lv in ("junior", "pleno", "senior")}
    core = tops["junior"] & tops["pleno"] & tops["senior"]
    # Ordena pelo % médio entre níveis.
    rows = []
    for sk in core:
        pcts = {lv: float(skill_share_by_level(df, lv, "tecnica")
                          .set_index("skill")["pct"].get(sk, 0))
                for lv in ("junior", "pleno", "senior")}
        rows.append((sk, pcts))
    rows.sort(key=lambda r: sum(r[1].values()), reverse=True)

    _header(fig, "O núcleo", "Sempre no top 10",
            "5 skills que aparecem no top 10 de júnior, pleno E sênior —\n"
            "a base inegociável de qualquer carreira em Dados.")
    ax = _axes(fig)
    labels = [_pretty(r[0]) for r in rows]
    y = range(len(labels))
    bar_h = 0.26
    for i, lv in enumerate(("junior", "pleno", "senior")):
        vals = [r[1][lv] for r in rows]
        offs = [yi + (i - 1) * bar_h for yi in y]
        ax.barh(offs, vals, height=bar_h, color=LEVEL_COLORS[lv],
                label=LEVEL_LABELS[lv], zorder=3)
        for off, v in zip(offs, vals):
            ax.text(v + 1.5, off, f"{v:.0f}%", va="center", ha="left",
                    color=INK, fontsize=8.5)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, color=INK, fontsize=13.5)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_xlim(0, 100)
    ax.legend(loc="lower right", frameon=False, labelcolor=INK, fontsize=11.5)
    _footer(fig)
    return _save(fig, "07_nucleo.png")


def slide_diferencia(df):
    """Skills que mais crescem de júnior -> sênior (incluindo pleno)."""
    fig = _new_fig()
    jr = skill_share_by_level(df, "junior", "tecnica").set_index("skill")["pct"]
    sr = skill_share_by_level(df, "senior", "tecnica").set_index("skill")["pct"]
    pl = skill_share_by_level(df, "pleno", "tecnica").set_index("skill")["pct"]
    
    skills = sorted(set(jr.index) | set(sr.index) | set(pl.index))
    diff = pd.DataFrame({
        "skill": skills,
        "junior": [jr.get(s, 0) for s in skills],
        "pleno": [pl.get(s, 0) for s in skills],
        "senior": [sr.get(s, 0) for s in skills],
    })
    diff["delta"] = diff["senior"] - diff["junior"]
    # Considera só skills com presença relevante no sênior.
    diff = diff[diff["senior"] >= 15].sort_values("delta", ascending=False).head(10)

    _header(fig, "A virada", "O que diferencia o Sênior",
            "Evolução da demanda das skills que mais saltam de Júnior → Sênior.\n"
            "Acompanhe também a transição no nível Pleno.")
    ax = _axes(fig, rect=(0.30, 0.18, 0.63, 0.58))
    labels = [_pretty(s) for s in diff["skill"]]
    y = range(len(labels))
    bar_h = 0.26
    
    levels = ("junior", "pleno", "senior")
    xmax = max((diff[lv].max() for lv in levels), default=1)
    
    for i, lv in enumerate(levels):
        vals = diff[lv].tolist()
        offs = [yi + (i - 1) * bar_h for yi in y]
        ax.barh(offs, vals, height=bar_h, color=LEVEL_COLORS[lv],
                label=LEVEL_LABELS[lv], zorder=3)
        for off, v in zip(offs, vals):
            ax.text(v + xmax * 0.015, off, f"{v:.0f}%", va="center", ha="left",
                    color=INK, fontsize=8.5)
            
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, color=INK, fontsize=13.5)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_xlim(0, xmax * 1.18)
    ax.legend(loc="lower right", frameon=False, labelcolor=INK, fontsize=11.5)
    
    fig.text(0.07, 0.115,
             "Engenharia, cloud e governança é o que separa o sênior:\n"
             "menos relatório, mais arquitetura de dados.",
             color=MUTED, fontsize=11.5, va="top", linespacing=1.4)
    _footer(fig)
    return _save(fig, "08_diferencia.png")


def slide_soft(df):
    """Top soft skills e como a demanda cresce com a senioridade."""
    fig = _new_fig()
    levels = ("junior", "pleno", "senior")
    # Top soft skills por presença total nos 3 níveis.
    soft = df[(df["tipo_skill"] == "soft") & (df["level"].isin(levels))]
    top_soft = (soft.groupby("skill")["job_id"].nunique()
                .sort_values(ascending=False).head(3).index.tolist())
    rows = []
    for sk in top_soft:
        pcts = {lv: float(skill_share_by_level(df, lv, "soft")
                          .set_index("skill")["pct"].get(sk, 0)) for lv in levels}
        rows.append((sk, pcts))

    _header(fig, "Soft skills", "Não é só técnica",
            "% das vagas de cada nível que citam a soft skill. Autonomia,\n"
            "trabalho em equipe e liderança crescem com a senioridade.")
    ax = _axes(fig)
    labels = [_pretty(r[0]) for r in rows]
    y = range(len(labels))
    bar_h = 0.26
    xmax = max((r[1][lv] for r in rows for lv in levels), default=1)
    for i, lv in enumerate(levels):
        vals = [r[1][lv] for r in rows]
        offs = [yi + (i - 1) * bar_h for yi in y]
        ax.barh(offs, vals, height=bar_h, color=LEVEL_COLORS[lv],
                label=LEVEL_LABELS[lv], zorder=3)
        for off, v in zip(offs, vals):
            ax.text(v + xmax * 0.015, off, f"{v:.0f}%", va="center", ha="left",
                    color=INK, fontsize=8.5)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, color=INK, fontsize=13.5)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_xlim(0, xmax * 1.18)
    ax.legend(loc="lower right", frameon=False, labelcolor=INK, fontsize=11.5)
    _footer(fig)
    return _save(fig, "09_soft.png")


def slide_conclusao(df):
    fig = _new_fig()
    n = df["job_id"].nunique()
    fig.text(0.07, 0.90, "CONCLUSÃO", color=HILITE, fontsize=14, fontweight="bold",
             va="top")
    fig.text(0.07, 0.85, "O caminho até o Sênior", color=INK, fontsize=30,
             fontweight="bold", va="top")
    bullets = [
        ("SQL + Python", "a base inegociável em todos os níveis."),
        ("Júnior", "domine Power BI, Excel e dashboards."),
        ("Pleno → Sênior", "migre para pipelines, ETL e cloud (AWS/Databricks)."),
        ("Governança de dados", "é o que separa o sênior do resto."),
    ]
    yb = 0.70
    for head, txt in bullets:
        fig.text(0.07, yb, "→", color=HILITE, fontsize=16, fontweight="bold")
        fig.text(0.12, yb, head, color=INK, fontsize=16, fontweight="bold")
        fig.text(0.12, yb - 0.032, txt, color=MUTED, fontsize=13.5)
        yb -= 0.105

    fig.text(0.07, 0.205,
             f"Metodologia: {n} vagas de Dados coletadas do LinkedIn (BR).\n"
             "Senioridade inferida do título; 52% das vagas não a declaram e\n"
             "ficaram fora da comparação por nível. Skills extraídas por\n"
             "dicionário (regex) da descrição da vaga.",
             color=MUTED, fontsize=10.5, va="top", linespacing=1.45)
    fig.text(0.07, 0.05, "Salvou? Comenta qual skill te surpreendeu ↓",
             color=HILITE, fontsize=13.5, fontweight="bold")
    return _save(fig, "09_conclusao.png")


def build_slides(df):
    print("Gerando carrossel em", OUTPUT_DIR.relative_to(_root), "…")
    slide_capa(df)
    slide_amostra(df)
    slide_nao_especificado(df)
    _slide_top_skills(df, "junior", 4)
    _slide_top_skills(df, "pleno", 5)
    _slide_top_skills(df, "senior", 6)
    slide_nucleo(df)
    slide_diferencia(df)
    # slide_soft(df)
    slide_conclusao(df)
    print("Carrossel completo.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true",
                        help="apenas inspeciona os dados, sem gerar imagens")
    args = parser.parse_args()

    df = load_from_db()
    if args.validate:
        _validate(df)
        return

    build_slides(df)


if __name__ == "__main__":
    main()
