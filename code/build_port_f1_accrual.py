"""
Build F1 (pt-BR) — "Produtividade e salários reais, 2012-2024: os salários acompanharam?"

Portuguese-language twin of build_f1_accrual.py, for the Prêmio Jovem Cientista
submission (Miscellaneous/Paper/main-port.tex). Same data, same structure, same
palette, same series; only the rendered text is Portuguese, decimals follow the
Brazilian convention, and the output stem carries the "port-" prefix.

The English script build_f1_accrual.py stays the canonical one and is untouched:
both read the same CSV, so the two figures always plot identical numbers.

Data (only source):  Data/d5_productivity_wage_series.csv  (built by build_d5_accrual.py).

Run with the project venv:
    Miscellaneous/.venv/bin/python Data/scripts/build_port_f1_accrual.py
"""

import os
import csv
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator

# ---------------------------------------------------------------- paths (from script location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))                    # .../Data
REPO_DIR = os.path.abspath(os.path.join(DATA_DIR, ".."))                      # repo root
CSV_PATH = os.path.join(DATA_DIR, "d5_productivity_wage_series.csv")
OUT_DIR = os.path.join(REPO_DIR, "Miscellaneous", "outputs", "figures")
OUT_STEM = os.path.join(OUT_DIR, "port-f1_accrual")   # pt-BR twin of f1_accrual

# ---------------------------------------------------------------- BeautifulFigures "Purple Teal" palette
WAGE_COLOR = "#6a408d"   # purple line  -> real wage
PROD_COLOR = "#378d94"   # teal line    -> productivity
GREY = "#8a8a8a"         # neutral grey -> reference line + gap fill

# ---------------------------------------------------------------- panel definitions (structural reference)
# order = banking -> retail -> agribusiness (matches T1/T2 and the exposure ranking)
PANELS = [
    dict(key="banking_financial",       title="Bancos e finanças",
         ylim=(85, 110), show_yticklabels=True,  prod_backdrop=True),
    dict(key="retail_customer_service", title="Varejo e atend. ao cliente",
         ylim=(85, 110), show_yticklabels=False, prod_backdrop=False),
    dict(key="agribusiness",            title="Agronegócio",
         ylim=(95, 200), show_yticklabels=True,  prod_backdrop=False),
]


def load_series(path):
    """sector -> dict(years=[], prod=[], wage=[], source=str)."""
    data = defaultdict(lambda: {"years": [], "prod": [], "wage": [], "source": None})
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            s = data[row["sector"]]
            s["years"].append(int(row["year"]))
            s["prod"].append(float(row["productivity_index"]))
            s["wage"].append(float(row["real_wage_index"]))
            s["source"] = row["productivity_source"]
    return data


def verify(data):
    """Recompute endpoint %d and assert 2012 base = 100 for every series."""
    for sector, s in data.items():
        assert s["years"][0] == 2012 and s["years"][-1] == 2024, f"{sector}: window not 2012-2024"
        assert abs(s["prod"][0] - 100.0) < 1e-6 and abs(s["wage"][0] - 100.0) < 1e-6, \
            f"{sector}: series not indexed to 100 at 2012"
        gap = (s["prod"][-1] - 100.0) - (s["wage"][-1] - 100.0)
        print(f"  {sector:24s} prod {s['prod'][-1]-100:+6.1f}%  wage {s['wage'][-1]-100:+6.1f}%  gap {gap:+6.1f} pp")


def main():
    data = load_series(CSV_PATH)
    print("F1 (pt) endpoint cross-check (should match d5_accrual_by_sector.csv):")
    verify(data)

    # -------------------------------------------------- rcParams (grounded in figures-guide technique)
    plt.rcParams.update({
        # authored AT the submission's final size, in a sans face matching the
        # Arial body (review panel: effective type was ~5-6.5pt under Courier)
        "font.family": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 9,
        "axes.titlesize": 10.5,
        "axes.labelsize": 9.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 7.8,
        "pdf.fonttype": 42,             # embed TrueType glyphs in the PDF
        "svg.fonttype": "path",         # text as vector paths in the SVG (portable)
    })

    # figsize == pjc-submission.tex textwidth (a4paper, 2.2cm margins ~ 6.54in),
    # so authored point sizes are the printed point sizes (no downscaling).
    fig, axes = plt.subplots(1, 3, figsize=(6.54, 2.45))

    for ax, p in zip(axes, PANELS):
        s = data[p["key"]]
        years, prod, wage = s["years"], s["prod"], s["wage"]

        # grid (figures-guide: major 0.75/0.25, minor 0.25/0.15, below data)
        ax.grid(True, which="major", linestyle="-", linewidth=0.75, alpha=0.25)
        ax.minorticks_on()
        ax.grid(True, which="minor", linestyle="-", linewidth=0.25, alpha=0.15)
        ax.set_axisbelow(True)

        # 2012 = 100 reference
        ax.axhline(100, color=GREY, linewidth=1.0, linestyle=(0, (1, 1)), alpha=0.7, zorder=1)

        # gap shading between the two lines (neutral grey, subtle)
        ax.fill_between(years, prod, wage, color=GREY, alpha=0.12, zorder=1.5)

        # productivity line: dashed for banking (WDI services backdrop), solid otherwise (SCN sector-exact)
        prod_style = (0, (6, 3)) if p["prod_backdrop"] else "-"
        ax.plot(years, prod, color=PROD_COLOR, linewidth=1.8, linestyle=prod_style, zorder=3)

        # real wage line: solid purple + circle markers (redundant encoding for CVD/grayscale safety)
        ax.plot(years, wage, color=WAGE_COLOR, linewidth=1.8, linestyle="-",
                marker="o", markersize=3.2, markerfacecolor=WAGE_COLOR,
                markeredgecolor=WAGE_COLOR, zorder=3.5)

        # endpoint value labels at 2024 (rounded index), nudged right of the last point
        _endpoint_label(ax, years[-1], prod[-1], f"{prod[-1]:.0f}", PROD_COLOR)
        _endpoint_label(ax, years[-1], wage[-1], f"{wage[-1]:.0f}", WAGE_COLOR)

        # axes cosmetics
        ax.set_title(p["title"], pad=8)
        ax.set_xlim(2012, 2025.4)                     # right headroom for endpoint labels
        ax.set_ylim(*p["ylim"])
        ax.xaxis.set_major_locator(MultipleLocator(4))   # 2012, 2016, 2020, 2024
        ax.xaxis.set_minor_locator(MultipleLocator(2))
        ax.set_xlabel("Ano")
        if not p["show_yticklabels"]:
            ax.tick_params(labelleft=False)
        # (productivity source is conveyed by the legend: solid = sector VAB/worker,
        #  dashed = services backdrop — banking; no redundant per-panel note.)

    axes[0].set_ylabel("Índice (2012 = 100)")
    # (the agribusiness wider-scale warning now lives in the LaTeX caption)

    # -------------------------------------------------- shared legend via proxy artists (above the row)
    proxies = [
        Line2D([0], [0], color=WAGE_COLOR, lw=1.8, marker="o", markersize=3.2, label="Salário real"),
        Line2D([0], [0], color=PROD_COLOR, lw=1.8, linestyle="-", label="Produtividade (VAB setorial/trab.)"),
        Line2D([0], [0], color=PROD_COLOR, lw=1.8, linestyle=(0, (6, 3)),
               label="Produtividade (pano de fundo serviços — bancos)"),
    ]
    fig.legend(handles=proxies, loc="upper center", bbox_to_anchor=(0.5, 1.02),
               ncol=3, frameon=False, handlelength=2.4, columnspacing=1.6)

    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.16, top=0.82, wspace=0.12)

    os.makedirs(OUT_DIR, exist_ok=True)
    fig.savefig(OUT_STEM + ".pdf")              # vector, for the manuscript
    fig.savefig(OUT_STEM + ".svg")              # vector, editable
    fig.savefig(OUT_STEM + ".png", dpi=200)     # raster preview
    print(f"\nwrote: {OUT_STEM}.pdf / .svg / .png")


def _endpoint_label(ax, x, y, text, color):
    ax.annotate(text, xy=(x, y), xytext=(2, 0), textcoords="offset points",
                fontsize=8, color=color, ha="left", va="center", clip_on=False)


if __name__ == "__main__":
    main()
