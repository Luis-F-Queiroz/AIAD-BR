#!/usr/bin/env python3
"""
D5 — the accrual table (guide Analysis 5, H4 "who captured the gains").

Design fixed in Data/METHODS.md decisions #18-#21 (2026-07-08). Window locked
2012-2024, base 2012 = 100. Headline verdict is GAP-ONLY; the labor share is a
non-load-bearing supplement (2012-2021, the verified extent of the definitive
TRU income components).

Inputs (all snapshotted under Data/raw/scn/ — see SOURCES.txt — plus built D1/D2):
  productivity numerator (real VAB growth by activity)
    - Data/raw/scn/tab09.xls        SCN sinotica 9, annual, 2011-2023 (primary)
    - Data/raw/scn/t5932_2024.json  quarterly acum-ano Q4 2024 (extends to 2024)
    - Data/raw/scn/t5932_2223.json  quarterly 2022-2023 (cross-check only)
  productivity denominator (employment)
    - Data/d2_ibge_pnad_activity_panel.csv  employed_thousands (PNAD 47947/47950)
  banking headline productivity (backdrop — decision #19)
    - Data/d1_worldbank_sector_panel.csv    services va_per_worker
  real wage (all sectors)
    - Data/d2_ibge_pnad_activity_panel.csv  mean_real_income_brl
  labor share + narrow-finance supplement (decision #21)
    - Data/raw/scn/nivel_12_2000_2022_xls.zip  TRU 12_tab2_YYYY.xls sheet "VA":
      Remuneracoes / VAB and Fator trabalho (ocupacoes), 2012-2021

Activity <-> sector mapping (boundary notes in METHODS #18/#19/#21):
  agribusiness              SCN "Agropecuaria"              <-> PNAD 47947
  retail_customer_service   SCN "Comercio"                  <-> PNAD 47950
  banking_financial         headline: WDI services backdrop <-> PNAD 56624 wage;
                            supplement: SCN "Atividades financeiras" (narrow)

Outputs:
  Data/d5_productivity_wage_series.csv  indexed series 2012=100 (feeds F1)
  Data/d5_accrual_by_sector.csv         headline accrual table (feeds T3)
  Data/d5_labor_share_by_sector.csv     supplement, 2012-2021 (feeds T3 note/appendix)

Requires: xlrd (legacy .xls). Run from anywhere; paths resolve from this file.
"""
import csv, json, os, sys, zipfile

import xlrd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, ".."))
RAW = os.path.join(DATA, "raw", "scn")

BASE_YEAR = 2012
END_YEAR = 2024
LS_END_YEAR = 2021  # verified wall: TRU rem/ocup empty from 2022 on

# activity labels as they appear in tab09 col 1 / TRU header row 3
SCN_ACT = {
    "agribusiness": "Agropecu",
    "retail_customer_service": "Comércio",
    "banking_financial": "financeiras",
}
SECTORS = ["banking_financial", "retail_customer_service", "agribusiness"]

# Verdict rule (METHODS decision #23, replacing the origin notebook's arbitrary
# +6/+3 endpoint band). Adjudicate on the PERSISTENT SIGN of the year-by-year
# productivity-wage gap, not an endpoint magnitude threshold: divider if the gap
# is positive in a supermajority of window years AND positive at the endpoint;
# equalizer if non-positive in a supermajority; else mixed. The raw positive-year
# count is written to the CSV so the verdict is transparent (no hidden cut-point).
SUPERMAJORITY = 2.0 / 3.0


def read_tab09_growth():
    """Real VAB growth (%) by activity-year, 2012-2023, from sinotica tab09."""
    sh = xlrd.open_workbook(os.path.join(RAW, "tab09.xls")).sheets()[0]
    # header row 4 holds year labels in merged pairs: year at col 2,4,6,...
    year_col = {}
    for c in range(2, sh.ncols):
        v = sh.cell_value(3, c) or sh.cell_value(4, c)
        if isinstance(v, float) and 2000 < v < 2100:
            year_col[int(v)] = c  # "Variacao (%)" column of the pair
    growth = {}
    for r in range(sh.nrows):
        label = str(sh.cell_value(r, 1))
        for sector, key in SCN_ACT.items():
            if key in label:
                growth[sector] = {y: float(sh.cell_value(r, c))
                                  for y, c in year_col.items()
                                  if isinstance(sh.cell_value(r, c), float)}
    missing = [s for s in SECTORS if s not in growth]
    if missing:
        sys.exit(f"tab09: activities not found for {missing}")
    return growth


def read_quarterly_growth(fname):
    """Annual real VAB growth from t5932 var 6563 Q4 values: {sector: {year: pct}}."""
    with open(os.path.join(RAW, fname)) as f:
        payload = json.load(f)
    out = {s: {} for s in SECTORS}
    for var in payload:
        for res in var.get("resultados", []):
            cat = " ".join(str(v) for c in res.get("classificacoes", [])
                           for v in c.get("categoria", {}).values())
            sector = next((s for s, k in SCN_ACT.items() if k in cat), None)
            if not sector:
                continue
            for s in res.get("series", []):
                for period, val in s.get("serie", {}).items():
                    out[sector][int(period[:4])] = float(val)
    return out


def read_d2():
    """PNAD employment (thousands) and real wage by study sector-year."""
    emp, wage = {}, {}
    with open(os.path.join(DATA, "d2_ibge_pnad_activity_panel.csv")) as f:
        for row in csv.DictReader(f):
            s, y = row["study_sector"], int(row["year"])
            if s in SECTORS and BASE_YEAR <= y <= END_YEAR:
                emp[(s, y)] = float(row["employed_thousands"])
                wage[(s, y)] = float(row["mean_real_income_brl"])
    return emp, wage


def read_d1_services():
    """WDI services va_per_worker (constant 2015 US$) by year — banking backdrop."""
    out = {}
    with open(os.path.join(DATA, "d1_worldbank_sector_panel.csv")) as f:
        for row in csv.DictReader(f):
            if row["sector"] == "services" and BASE_YEAR <= int(row["year"]) <= END_YEAR:
                out[int(row["year"])] = float(row["va_per_worker"])
    return out


def read_tru_income():
    """TRU 12_tab2 VA sheet: VAB, Remuneracoes, ocupacoes per sector-year 2012-2021."""
    zf = zipfile.ZipFile(os.path.join(RAW, "nivel_12_2000_2022_xls.zip"))
    out = {}  # (sector, year) -> dict(vab, rem, ocup)
    for y in range(BASE_YEAR, LS_END_YEAR + 1):
        wb = xlrd.open_workbook(file_contents=zf.read(f"12_tab2_{y}.xls"))
        sh = wb.sheet_by_name("VA")
        hdr = [str(sh.cell_value(3, c)).replace("\n", " ") for c in range(sh.ncols)]
        cols = {}
        for sector, key in SCN_ACT.items():
            cols[sector] = next((c for c, h in enumerate(hdr) if key in h), None)
            if cols[sector] is None:
                sys.exit(f"TRU {y}: column for {sector} not found")
        rows = {}
        for r in range(sh.nrows):
            lab = str(sh.cell_value(r, 0)).strip()
            if lab.startswith("Valor adicionado bruto"):
                rows["vab"] = r
            elif lab == "Remunerações":
                rows["rem"] = r
            elif lab.startswith("Fator trabalho"):
                rows["ocup"] = r
        for sector, c in cols.items():
            rec = {k: float(sh.cell_value(r, c)) for k, r in rows.items()}
            if rec["rem"] <= 0 or rec["vab"] <= 0 or rec["ocup"] <= 0:
                sys.exit(f"TRU {y} {sector}: empty income component — "
                         f"labor-share wall moved? re-verify decision #21")
            out[(sector, y)] = rec
    return out


def chain_index(growth_by_year, years):
    """Chain %-growth rates into an index with index[BASE_YEAR] = 100."""
    idx = {BASE_YEAR: 100.0}
    for y in years:
        if y <= BASE_YEAR:
            continue
        g = growth_by_year.get(y)
        if g is None:
            sys.exit(f"missing growth for year {y}")
        idx[y] = idx[y - 1] * (1.0 + g / 100.0)
    return idx


def main():
    tab09 = read_tab09_growth()
    q2024 = read_quarterly_growth("t5932_2024.json")
    q2223 = read_quarterly_growth("t5932_2223.json")
    emp, wage = read_d2()
    wdi_srv = read_d1_services()
    tru = read_tru_income()

    # cross-check (decision #20): annual tab09 vs quarterly, 2022-2023
    print("cross-check tab09 (annual, used) vs t5932 (quarterly), real VAB growth %:")
    for s in SECTORS:
        for y in (2022, 2023):
            a, q = tab09[s].get(y), q2223[s].get(y)
            flag = "  <-- >1.0pp, annual kept (benchmark)" if a is not None and q is not None and abs(a - q) > 1.0 else ""
            print(f"  {s:24s} {y}: annual {a:+.1f} vs quarterly {q:+.1f}{flag}")

    years = list(range(BASE_YEAR, END_YEAR + 1))

    # --- productivity indexes ---
    prod_idx, prod_src = {}, {}
    for s in ("agribusiness", "retail_customer_service"):
        growth = dict(tab09[s])              # 2012-2023 annual (primary)
        growth[2024] = q2024[s][2024]        # 2024 quarterly extension
        vab_idx = chain_index(growth, years)
        prod_idx[s] = {y: 100.0 * (vab_idx[y] / 100.0) /
                          (emp[(s, y)] / emp[(s, BASE_YEAR)]) for y in years}
        prod_src[s] = "scn_real_vab_per_pnad_worker"
    prod_idx["banking_financial"] = {
        y: 100.0 * wdi_srv[y] / wdi_srv[BASE_YEAR] for y in years}
    prod_src["banking_financial"] = "wdi_services_backdrop"

    # --- wage indexes ---
    wage_idx = {s: {y: 100.0 * wage[(s, y)] / wage[(s, BASE_YEAR)] for y in years}
                for s in SECTORS}

    # --- supplement: labor share + coherent narrow-finance productivity ---
    fin_vab_idx = chain_index(dict(tab09["banking_financial"]),
                              list(range(BASE_YEAR, LS_END_YEAR + 1)))
    supp_rows = []
    for s in SECTORS:
        for y in range(BASE_YEAR, LS_END_YEAR + 1):
            rec = tru[(s, y)]
            ls = rec["rem"] / rec["vab"]
            if not (0.05 < ls < 0.85):
                sys.exit(f"labor share {ls:.2f} ({s} {y}) outside sane bounds — inspect TRU")
            if ls < 0.25:
                # expected in self-employment-heavy sectors (agribusiness):
                # smallholder labor income is mixed income (in EOB), not
                # Remuneracoes, so the employee-compensation share runs low —
                # documented caveat in METHODS §2.7
                print(f"  note: low employee-compensation share {ls:.2f} ({s} {y}) — "
                      "self-employment-heavy sector, see METHODS §2.7 caveat")
            row = {
                "sector": s, "year": y,
                "scn_activity": {"agribusiness": "Agropecuaria",
                                 "retail_customer_service": "Comercio",
                                 "banking_financial": "Atividades financeiras (narrow)"}[s],
                "remuneracoes_mrl_current": round(rec["rem"], 1),
                "vab_mrl_current": round(rec["vab"], 1),
                "labor_share": round(ls, 4),
                "ocupacoes": int(rec["ocup"]),
                "narrow_finance_real_prod_index_2012_100": "",
            }
            if s == "banking_financial":
                ocup_idx = rec["ocup"] / tru[(s, BASE_YEAR)]["ocup"]
                row["narrow_finance_real_prod_index_2012_100"] = round(
                    100.0 * (fin_vab_idx[y] / 100.0) / ocup_idx, 1)
            supp_rows.append(row)

    # --- write outputs ---
    p1 = os.path.join(DATA, "d5_productivity_wage_series.csv")
    with open(p1, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sector", "year", "productivity_index", "real_wage_index",
                    "productivity_source"])
        for s in SECTORS:
            for y in years:
                w.writerow([s, y, round(prod_idx[s][y], 2),
                            round(wage_idx[s][y], 2), prod_src[s]])

    p2 = os.path.join(DATA, "d5_accrual_by_sector.csv")
    with open(p2, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sector", "window", "productivity_growth_pct",
                    "real_wage_growth_pct", "prod_wage_gap_pp",
                    "gap_positive_years", "labor_share_2012", "labor_share_2021",
                    "labor_share_change_pp", "pattern", "productivity_source"])
        window = [y for y in years if y > BASE_YEAR]  # 2013..2024, the non-base years
        for s in SECTORS:
            pg = prod_idx[s][END_YEAR] - 100.0
            wg = wage_idx[s][END_YEAR] - 100.0
            gap = pg - wg
            # persistent-sign verdict (decision #23)
            yearly_gap = [prod_idx[s][y] - wage_idx[s][y] for y in window]
            n_pos = sum(1 for g in yearly_gap if g > 0)
            n = len(window)
            endpoint_pos = gap > 0
            if n_pos >= SUPERMAJORITY * n and endpoint_pos:
                pattern = "consistent with divider (gains to capital)"
            elif (n - n_pos) >= SUPERMAJORITY * n:
                pattern = "consistent with equalizer (wages kept pace or outpaced productivity)"
            else:
                pattern = "mixed (no persistent sign)"
            ls12 = tru[(s, BASE_YEAR)]["rem"] / tru[(s, BASE_YEAR)]["vab"]
            ls21 = tru[(s, LS_END_YEAR)]["rem"] / tru[(s, LS_END_YEAR)]["vab"]
            w.writerow([s, f"{BASE_YEAR}-{END_YEAR}", round(pg, 1), round(wg, 1),
                        round(gap, 1), f"{n_pos}/{n}", round(ls12, 4), round(ls21, 4),
                        round(100 * (ls21 - ls12), 1), pattern, prod_src[s]])

    p3 = os.path.join(DATA, "d5_labor_share_by_sector.csv")
    with open(p3, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(supp_rows[0].keys()))
        w.writeheader()
        w.writerows(supp_rows)

    print("\nwrote:")
    for p in (p1, p2, p3):
        print(" ", os.path.relpath(p, os.path.dirname(DATA)))
    print("\nheadline accrual (gap-only verdict; labor share is supplement):")
    with open(p2) as f:
        for line in f:
            print("  " + line.rstrip())


if __name__ == "__main__":
    main()
