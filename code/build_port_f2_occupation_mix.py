"""
Build F2 (pt-BR) — "Composição ocupacional dos três setores e exposição à IA de cada grupo".

Portuguese-language twin of build_f2_occupation_mix.py, for the Prêmio Jovem
Cientista submission (Miscellaneous/Paper/main-port.tex). Same data, same Option A
shaded-matrix design (rev 3), same palette, same row order; only the rendered text
is Portuguese, decimals follow the Brazilian convention (comma), and the output
stem carries the "port-" prefix.

The English script build_f2_occupation_mix.py stays the canonical one and is
untouched: both read the same CSVs, so the two figures always print identical values.

Two layout deltas, forced by the Portuguese ISCO-08 titles being much longer than
the English ones (group 7 in particular): the figure is slightly wider and the left
gutter slightly deeper, so the full official titles still fit without abbreviation.
Everything inside the matrix is unchanged.

Data (only sources; nothing hardcoded):
  Data/d3_occupation_mix_by_sector.csv      shares + per-group AIOE
  Data/d3_isco_group_aioe_profile.csv       AIOE cross-check (assert)

Run:  Miscellaneous/.venv/bin/python Data/scripts/build_port_f2_occupation_mix.py
"""

import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Rectangle

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
REPO_DIR = os.path.abspath(os.path.join(DATA_DIR, ".."))
OUT_DIR = os.path.join(REPO_DIR, "Miscellaneous", "outputs", "figures")
# pt-BR twin; the "_2" mirrors the filename main.tex/main-port.tex reference
OUT_STEM = os.path.join(OUT_DIR, "port-f2_occupation_mix_2")

MIX_CSV = os.path.join(DATA_DIR, "d3_occupation_mix_by_sector.csv")
PROFILE_CSV = os.path.join(DATA_DIR, "d3_isco_group_aioe_profile.csv")

# BeautifulFigures "Purple Teal tones" (as in build_f1_accrual.py)
PURPLE_D = "#6a408d"
PURPLE_L = "#9671bd"
TEAL_D = "#378d94"
TEAL_L = "#77b5b6"
GREY = "#8a8a8a"
INK = "#1a1a1a"

SECTORS = [
    ("banking_financial", "Bancos e\nfinanças"),
    ("retail_customer_service", "Varejo e\natend. cliente"),
    ("agribusiness", "Agronegócio"),
]
CLERICAL_GROUP = "4"

# Full official ISCO-08 major-group titles in Portuguese, ISCO 1-9 order (mirrors
# the table rows and matches tab:isco08_groups in main-port.tex exactly). No
# abbreviations; the longer titles carry an explicit line break so the left gutter
# stays legible (the code " (ISCO n)" reference attaches to the last line).
GROUP_LABEL = {
    "1": "Diretores e gerentes",
    "2": "Profissionais das ciências e intelectuais",
    "3": "Técnicos e profissionais de nível médio",
    "4": "Trabalhadores de apoio administrativo",
    "5": "Trabalhadores dos serviços, vendedores dos\ncomércios e mercados",
    "6": "Trabalhadores qualificados da agropecuária,\nflorestais, da caça e da pesca",
    "7": "Trabalhadores qualificados, operários e\nartesãos da construção, das artes\nmecânicas e outros ofícios",
    "8": "Operadores de instalações e máquinas\ne montadores",
    "9": "Ocupações elementares",
}


def br(x, decimals):
    """Brazilian decimal convention: comma, and an explicit sign for AIOE."""
    s = f"{x:+.{decimals}f}" if decimals == 2 else f"{x:.{decimals}f}"
    return s.replace(".", ",")


def load():
    mix = defaultdict(dict)   # group -> sector -> share
    aioe = {}                 # group -> aioe
    with open(MIX_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            g = r["isco_major_group"]
            mix[g][r["study_sector"]] = float(r["share_pct"])
            aioe[g] = float(r["aioe_group"])
    # verify against the documented bridge profile
    with open(PROFILE_CSV, newline="", encoding="utf-8") as f:
        prof = {r["isco_major_group"]: float(r["aioe"]) for r in csv.DictReader(f)}
    for g, v in aioe.items():
        assert abs(prof[g] - v) < 1e-9, f"AIOE mismatch for group {g}"
    # verify shares complete + sum to 100 (groups 1-9 = all employment; group 0 absent)
    for key, _ in SECTORS:
        s = sum(mix[g][key] for g in mix)
        assert abs(s - 100.0) < 0.05, f"{key}: shares sum to {s}"
        assert len([g for g in mix if key in mix[g]]) == 9
    print("verify: 27 shares, sums ~100, AIOE matches bridge profile — OK")
    return mix, aioe


SHARE_CMAP = LinearSegmentedColormap.from_list("teal_seq", ["#ffffff", TEAL_L, TEAL_D])
SHARE_VMAX = 60.0


def share_color(v):
    """Sequential teal ramp for cell fill; text flips to white on dark cells."""
    frac = min(v / SHARE_VMAX, 1.0)
    rgba = SHARE_CMAP(frac)
    text = "white" if frac > 0.55 else INK
    return rgba, text


def main():
    mix, aioe = load()
    groups = [str(i) for i in range(1, 10)]  # ISCO order, mirrors the table

    plt.rcParams.update({
        # authored AT the submission's final width in a sans face (see F1 twin)
        "font.family": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 8,
        "mathtext.default": "regular",
        "pdf.fonttype": 42,
        "svg.fonttype": "path",
    })

    n_rows = len(groups)
    GAP = 0.18                                   # gap between AIOE block and share block
    x_share0 = 1 + GAP                           # left edge of the contiguous share block
    x_right = x_share0 + len(SECTORS)            # right edge of the share block
    # figsize == pjc-submission.tex textwidth (~6.54in): authored size = printed
    # size. Deep left gutter so the full Portuguese ISCO-08 titles still fit.
    fig, ax = plt.subplots(figsize=(6.54, 3.5))
    ax.set_xlim(0, x_right)
    ax.set_ylim(0, n_rows)
    ax.invert_yaxis()
    ax.axis("off")

    col_x = {"aioe": 0.5, 0: x_share0 + 0.5, 1: x_share0 + 1.5, 2: x_share0 + 2.5}

    # column headers (spanning italic label sits ABOVE the three sector headers)
    ax.text(col_x["aioe"], -0.72, "AIOE", ha="center", va="center",
            fontsize=8.5, fontweight="bold", color=INK)
    for j, (_, name) in enumerate(SECTORS):
        ax.text(col_x[j], -0.72, name, ha="center", va="center",
                fontsize=8.5, fontweight="bold", color=INK)

    for i, g in enumerate(groups):
        y = i + 0.5
        emph = (g == CLERICAL_GROUP)
        w = "bold" if emph else "normal"

        # row label (left gutter); clerical carries the footnote superscript
        sup = "$^{a}$" if emph else ""
        ax.text(-0.12, y, f"{GROUP_LABEL[g]} (ISCO {g}){sup}", ha="right", va="center",
                fontsize=7.5, fontweight=w, color=INK, linespacing=1.05)

        # AIOE cell: purple tint above US average, grey tint below
        a = aioe[g]
        fill = PURPLE_L if a >= 0 else GREY
        alpha = 0.16 + 0.5 * min(abs(a), 1.1) / 1.1
        ax.add_patch(Rectangle((0.0, i), 1.0, 1.0,
                               facecolor=fill, alpha=alpha, edgecolor="none"))
        ax.text(col_x["aioe"], y, br(a, 2), ha="center", va="center",
                fontsize=8, fontweight=w, color=INK)

        # sector share cells: sequential teal + printed value
        for j, (key, _) in enumerate(SECTORS):
            v = mix[g][key]
            rgba, tcol = share_color(v)
            ax.add_patch(Rectangle((x_share0 + j, i), 1.0, 1.0,
                                   facecolor=rgba, edgecolor="none"))
            ax.text(col_x[j], y, br(v, 1), ha="center", va="center",
                    fontsize=8, fontweight=w, color=tcol)


    # colorbar (right): the share scale, confusion-matrix style
    sm = ScalarMappable(norm=Normalize(vmin=0, vmax=SHARE_VMAX), cmap=SHARE_CMAP)
    cbar = fig.colorbar(sm, ax=ax, fraction=0.035, pad=0.025)
    cbar.set_label("Parcela do emprego (%)", fontsize=8)
    cbar.ax.tick_params(labelsize=7.5)
    cbar.outline.set_edgecolor(GREY)
    cbar.outline.set_linewidth(0.8)

    # (the AIOE purple/grey key now lives in the LaTeX caption note)

    fig.subplots_adjust(left=0.42, right=0.90, top=0.90, bottom=0.04)
    os.makedirs(OUT_DIR, exist_ok=True)
    for ext in ("pdf", "svg", "png"):
        fig.savefig(f"{OUT_STEM}.{ext}", dpi=200 if ext == "png" else None)
    print(f"wrote: {OUT_STEM}.pdf / .svg / .png")


if __name__ == "__main__":
    main()
