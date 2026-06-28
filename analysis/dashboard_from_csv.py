#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dashboard_from_csv.py — gera um carrossel de imagens (PNG) para publicação no
LinkedIn a partir de um CSV exportado do Jupyter Notebook.

Narrativa: "Skills x Senioridade" — como o conjunto de skills mais pedidas muda
entre júnior, pleno e sênior (o que estudar para subir de nível).
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from unidecode import unidecode
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

_root = Path(__file__).resolve().parent.parent
OUTPUT_DIR = _root / "output" / "carousel"
CSV_PATH = _root / "data" / "skills_standardized.csv"

# ---------------------------------------------------------------------------
# Configurações Globais
# ---------------------------------------------------------------------------
LEVEL_LABELS = {
    "estagio": "Estágio",
    "junior": "Júnior",
    "pleno": "Pleno",
    "senior": "Sênior",
    "nao_especificado": "Não especificado",
}

LEVEL_ORDER = ["estagio", "junior", "pleno", "senior"]

EXCLUDED_POSITIONS = {"Not Data Role", "Data Talent Pool"}

# Nomes canônicos (soft skills) apenas para exibição correta
_DISPLAY = {
    "comunicacao": "Comunicação",
    "trabalho em equipe": "Trabalho em Equipe",
    "proatividade": "Proatividade",
    "resolucao de problemas": "Resolução de Problemas",
    "pensamento analitico": "Pensamento Analítico",
    "organizacao": "Organização",
    "autonomia": "Autonomia",
    "lideranca": "Liderança",
    "curiosidade": "Curiosidade",
    "storytelling": "Storytelling",
    "visao estrategica": "Visão Estratégica",
    "ingles": "Inglês", 
    "estatistica": "Estatística"
}

def _pretty(skill) -> str:
    """Rótulo de exibição para a skill."""
    # O CSV já vem com skill_grouped formatado como Title Case pelo notebook.
    # Mas usamos _DISPLAY caso haja algum override específico.
    return _DISPLAY.get(unidecode(str(skill)).lower(), str(skill))

# ---------------------------------------------------------------------------
# Leitura e Filtros
# ---------------------------------------------------------------------------
def load_from_csv() -> pd.DataFrame:
    """Lê o CSV salvo pelo notebook e aplica os filtros finais."""
    if not CSV_PATH.exists():
        print(f"Erro: Arquivo {CSV_PATH} não encontrado. Rode o notebook primeiro!")
        sys.exit(1)
        
    df = pd.read_csv(CSV_PATH)
    
    # Foca em carreira de dados (ignora Not Data Role etc)
    df = df[~df["position_group"].isin(EXCLUDED_POSITIONS)].reset_index(drop=True)
    
    return df

def skill_share_by_level(df: pd.DataFrame, level: str, tipo: str = None) -> pd.DataFrame:
    """% de vagas daquele nível que pedem cada skill (normalizado por job_id único)."""
    sub = df[df["level"] == level]
    if tipo is not None:
        sub = sub[sub["tipo_skill"] == tipo]
        
    total_jobs = sub["job_id"].nunique()
    if total_jobs == 0:
        return pd.DataFrame(columns=["skill", "n_jobs", "pct"])
        
    # Agrupa pelo nome já unificado `skill_grouped`
    g = (
        sub.groupby("skill_grouped")["job_id"].nunique()
        .reset_index(name="n_jobs")
        .rename(columns={"skill_grouped": "skill"})
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

    print("\n=== Vagas por cargo (após filtro de carreira de dados) ===")
    print(df.groupby("position_group")["job_id"].nunique().sort_values(ascending=False).to_string())

    print("\n=== Top 8 skills Júnior vs Sênior (% das vagas do nível) ===")
    for lv in ("junior", "senior"):
        top = skill_share_by_level(df, lv, tipo="tecnica").head(8)
        print(f"\n  [{LEVEL_LABELS.get(lv, lv)}]")
        for _, r in top.iterrows():
            print(f"    {r['skill']:22s} {r['pct']:4.0f}%  ({int(r['n_jobs'])})")


# ===========================================================================
# Plotagem — carrossel de PNGs (1080x1350 px, retrato 4:5)
# ===========================================================================
BG = "#0E1726"          
INK = "#F2F5FA"         
MUTED = "#8FA1B6"       
BASE = "#2D6BF0"        
HILITE = "#FF8A3D"      
GRID = "#22304A"

LEVEL_COLORS = {
    "estagio": "#64D2A6",
    "junior": "#36C28B",
    "pleno": "#2D6BF0",
    "senior": "#9B7BFF",
    "nao_especificado": "#5A6B82",
}

DPI = 150
FIGSIZE = (10.8, 9.0)
HANDLE = "Dados coletados do LinkedIn"

def _new_fig():
    fig = plt.figure(figsize=FIGSIZE, dpi=DPI)
    fig.patch.set_facecolor(BG)
    return fig

def _header(fig, kicker, title, subtitle=None, title_fs=26):
    fig.text(0.07, 0.945, kicker.upper(), color=HILITE, fontsize=13,
             fontweight="bold", family="DejaVu Sans")
    fig.text(0.07, 0.90, title, color=INK, fontsize=title_fs, fontweight="bold",
             family="DejaVu Sans", va="top")
    if subtitle:
        fig.text(0.07, 0.815, subtitle, color=MUTED, fontsize=13.5,
                 family="DejaVu Sans", va="top")

def _footer(fig):
    fig.text(0.07, 0.035, HANDLE, color=MUTED, fontsize=10.5, family="DejaVu Sans")

def _axes(fig, rect=(0.30, 0.10, 0.63, 0.62)):
    ax = fig.add_axes(rect)
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    return ax

def _barh(ax, labels, values, colors, value_fmt="{:.0f}%"):
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
    fig.text(0.07, 0.78, "SKILLS × SENIORIDADE", color=HILITE, fontsize=15, fontweight="bold")
    fig.text(0.07, 0.70, "O que o mercado de\nDados pede em cada\nsenioridade?",
             color=INK, fontsize=40, fontweight="bold", va="top", linespacing=1.05)
    fig.text(0.07, 0.36,
             f"Uma análise de {n_jobs:,} vagas de Dados\n"
             "publicadas no LinkedIn (Brasil).".replace(",", "."),
             color=MUTED, fontsize=17, va="top", linespacing=1.4)
    fig.text(0.07, 0.20, "Arrasta para o lado  →", color=HILITE, fontsize=15, fontweight="bold")
    _footer(fig)
    return _save(fig, "01_capa.png")

def slide_amostra(df):
    fig = _new_fig()
    counts = (df.groupby("level")["job_id"].nunique())
    order = ["estagio", "junior", "pleno", "senior", "nao_especificado"]
    labels = [LEVEL_LABELS.get(k, k) for k in order]
    values = [int(counts.get(k, 0)) for k in order]
    colors = [LEVEL_COLORS.get(k, "#FFFFFF") for k in order]
    total = df["job_id"].nunique()
    pct_ne = 100 * counts.get("nao_especificado", 0) / total if total > 0 else 0

    _header(fig, "A amostra", "De onde vêm os números",
            f"{total} vagas de carreira em Dados, classificadas pela\n"
            "senioridade.")
    ax = _axes(fig, rect=(0.30, 0.22, 0.63, 0.50))
    _barh(ax, labels, values, colors, value_fmt="{:.0f}")
    fig.text(0.07, 0.145,
             f"⚠  {pct_ne:.0f}% das vagas não trazem informação sobre a senioridade.",
             color=MUTED, fontsize=11.5, va="top", linespacing=1.4)
    _footer(fig)
    return _save(fig, "02_amostra.png")

def slide_nao_especificado(df):
    fig = _new_fig()
    tops = {lv: set(skill_share_by_level(df, lv, "tecnica").head(10)["skill"]) 
            for lv in ("junior", "pleno", "senior")}
            
    df_ne = df[(df["level"] == "nao_especificado") & (df["tipo_skill"] == "tecnica")]
    jobs = df_ne.groupby("job_id")["skill_grouped"].apply(set)
    
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
    labels = [LEVEL_LABELS.get(lv, lv) for lv in order]
    vals = [pcts[lv] for lv in order]
    colors = [LEVEL_COLORS.get(lv, "#FFFFFF") for lv in order]
    
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
    lbl = LEVEL_LABELS.get(level, level)
    _header(fig, f"Nível {lbl}",
            f"Top 10 skills — {lbl}",
            f"% das {n} vagas de {lbl.lower()} que pedem cada skill técnica.")
    ax = _axes(fig)
    _barh(ax, [_pretty(s) for s in top["skill"]], top["pct"].tolist(), colors)
    _footer(fig)
    return _save(fig, f"{idx:02d}_top_{level}.png")

def slide_nucleo(df):
    fig = _new_fig()
    tops = {lv: set(skill_share_by_level(df, lv, "tecnica").head(10)["skill"])
            for lv in ("junior", "pleno", "senior")}
    core = tops["junior"] & tops["pleno"] & tops["senior"]
    
    rows = []
    for sk in core:
        pcts = {lv: float(skill_share_by_level(df, lv, "tecnica")
                          .set_index("skill")["pct"].get(sk, 0))
                for lv in ("junior", "pleno", "senior")}
        rows.append((sk, pcts))
    rows.sort(key=lambda r: sum(r[1].values()), reverse=True)

    _header(fig, "O núcleo", "Sempre no top 10",
            "Skills que aparecem no top 10 de júnior, pleno E sênior —\n"
            "a base inegociável de qualquer carreira em Dados.")
    ax = _axes(fig)
    labels = [_pretty(r[0]) for r in rows]
    y = range(len(labels))
    bar_h = 0.26
    for i, lv in enumerate(("junior", "pleno", "senior")):
        vals = [r[1][lv] for r in rows]
        offs = [yi + (i - 1) * bar_h for yi in y]
        ax.barh(offs, vals, height=bar_h, color=LEVEL_COLORS.get(lv, BASE),
                label=LEVEL_LABELS.get(lv, lv), zorder=3)
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
    diff = diff[diff["senior"] >= 15].sort_values("delta", ascending=False).head(10)

    _header(fig, "A virada", "O que diferencia o Sênior",
            "Evolução da demanda das skills que mais saltam de Júnior → Sênior.\n"
            "Acompanhe também a transição no nível Pleno.")
    
    ax = _axes(fig, rect=(0.27, 0.16, 0.68, 0.52))
    labels = [_pretty(s) for s in diff["skill"]]
    
    # ALTERAÇÃO AQUI: Multiplicamos por 1.5 (ou 1.8, 2.0) para empurrar os blocos para longe
    espaco_entre_skills = 3.5
    y = [i * espaco_entre_skills for i in range(len(labels))]
    
    # PROPORÇÃO PERFEITA:
    # Diminuindo esses valores, as 3 barras se agrupam fortemente 
    # e sobra um baita espaço vazio (vão) entre cada bloco de skill.
    bar_h = 0.9
    space_bloco = 0.9
    
    levels = ("junior", "pleno", "senior")
    xmax = max((diff[lv].max() for lv in levels), default=1)
    
    for i, lv in enumerate(levels):
        vals = diff[lv].tolist()
        offs = [yi + (i - 1) * space_bloco for yi in y]
        ax.barh(offs, vals, height=bar_h, color=LEVEL_COLORS.get(lv, BASE),
                label=LEVEL_LABELS.get(lv, lv), zorder=3)
        for off, v in zip(offs, vals):
            # Tamanho 9.0 garante leitura sem nenhuma chance de sobreposição
            ax.text(v + xmax * 0.015, off, f"{v:.0f}%", va="center", ha="left",
                    color=INK, fontsize=9.0)
            
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, color=INK, fontsize=13.5)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_xlim(0, xmax * 1.12)
    
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, 1.02), ncol=3, 
              frameon=False, labelcolor=INK, fontsize=11.5)
    
    fig.text(0.07, 0.10,
             "Engenharia, cloud e governança é o que separa o sênior:\n"
             "menos relatório, mais arquitetura de dados.",
             color=MUTED, fontsize=11.5, va="top", linespacing=1.4)
    _footer(fig)
    return _save(fig, "08_diferencia.png")

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
             "Senioridade: 52% das vagas não a declaram e\n"
             "ficaram fora da comparação por nível.\n",
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
    slide_conclusao(df)
    print("Carrossel completo.")

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true",
                        help="apenas inspeciona os dados, sem gerar imagens")
    args = parser.parse_args()

    df = load_from_csv()
    if args.validate:
        _validate(df)
        return

    build_slides(df)

if __name__ == "__main__":
    main()
