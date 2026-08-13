#!/usr/bin/env python3
"""
D3 - AI-exposure scores (Felten, Raj & Seamans 2021), mapped to the 3 sectors.

Route: PUBLISHED values + GENERATIVE-AI supplement (no O*NET recompute).

Reads the peer-reviewed AIOE/AIIE appendix and the authors' Language-Modeling
and Image-Generation supplements (downloaded from github.com/AIOE-Data/AIOE),
then maps the rows to the three study sectors, preserving sector-internal
structure (e.g. retail stores vs. customer-service work) rather than averaging
it away.

Exposure is US-derived and is POTENTIAL exposure, NOT adoption (keep separate
from D4). Scores are z-standardized (mean 0, SD 1) across occupations/industries.

Inputs (data/raw/, downloaded 2026-07-01, repo commit adca5fc2cd):
  AIOE_DataAppendix_2026-07-01.xlsx   -> Appendix A (AIOE occ), Appendix B (AIIE ind)
  AIOE_LanguageModeling_2026-07-01.xlsx -> LM AIOE / LM AIIE
  AIOE_ImageGeneration_2026-07-01.xlsx  -> IG AIOE / IG AIIE

Outputs (data/):
  d3_aiie_industry_mapping.csv     - each mapped NAICS industry row
  d3_aioe_occupation_mapping.csv   - each mapped SOC occupation row
  d3_sector_exposure_summary.csv   - per sector/level/subset summary (long)
"""
import csv
import glob
import openpyxl
from pathlib import Path
from statistics import mean

DATA = Path(__file__).resolve().parent.parent / "data"
RAW = DATA / "raw"


def find(pattern):
    hits = sorted(glob.glob(str(RAW / pattern)))
    if not hits:
        raise FileNotFoundError(pattern)
    return hits[-1]


def load(path, sheet, four_digit=False):
    """Return {code: (title, value)}; codes as strings; NAICS optionally -> 4-digit."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet]
    out = {}
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        if i < 1 or r[0] is None:
            continue
        code = str(r[0]).strip()
        if four_digit:
            code = code[:4]
        out[code] = (str(r[1]).strip(), r[2])
    wb.close()
    return out


APP = find("AIOE_DataAppendix_*.xlsx")
LMF = find("AIOE_LanguageModeling_*.xlsx")
IGF = find("AIOE_ImageGeneration_*.xlsx")

# --- industry (AIIE), keyed on 4-digit NAICS ---
aiie = load(APP, "Appendix B", four_digit=True)
aiie_lm = load(LMF, "LM AIIE", four_digit=True)
aiie_ig = load(IGF, "IG AIIE", four_digit=True)
# --- occupation (AIOE), keyed on 6-digit SOC ---
aioe = load(APP, "Appendix A")
aioe_lm = load(LMF, "LM AIOE")
aioe_ig = load(IGF, "IG AIOE")


def by_prefix(table, prefixes):
    return sorted(k for k in table if any(k.startswith(p) for p in prefixes))


# ---- sector -> industry mapping (subset = sector-internal grouping) ----
# Selected by NAICS prefix from the actual appendix rows (transparent, complete).
INDUSTRY_MAP = [
    ("banking_financial", "finance (NAICS 52)", by_prefix(aiie, ["52"])),
    ("retail_customer_service", "retail stores (NAICS 44-45)", by_prefix(aiie, ["44", "45"])),
    ("retail_customer_service", "customer-service / back-office proxy",
        ["5182", "5611", "5614"]),
    ("agribusiness", "agricultural support & logging (NAICS 11)", ["1133", "1151", "1152"]),
    ("agribusiness", "food & beverage manufacturing (NAICS 311-312)",
        by_prefix(aiie, ["311", "312"])),
]

# ---- sector -> occupation mapping (representative, validated to exist) ----
OCC_MAP = [
    ("banking_financial", "finance occupations",
        ["11-3031", "13-2011", "13-2041", "13-2051", "13-2052",
         "13-2061", "13-2072", "41-3031", "43-3071"]),
    ("retail_customer_service", "retail-store occupations",
        ["41-1011", "41-2011", "41-2031"]),
    ("retail_customer_service", "customer-service occupations",
        ["43-4051", "41-9041", "43-3011"]),
    ("agribusiness", "agribusiness occupations",
        ["11-9013", "45-1011", "45-2011", "45-2041", "45-2091",
         "45-2092", "45-2093", "51-3021", "51-3092", "19-1013"]),
]


def num(x):
    return round(x, 3) if isinstance(x, (int, float)) else ""


# ---- write industry mapping ----
ind_rows = []
for sector, basis, codes in INDUSTRY_MAP:
    for c in codes:
        if c not in aiie:
            continue
        title, b = aiie[c]
        ind_rows.append({
            "study_sector": sector, "mapping_basis": basis, "naics": c,
            "industry_title": title, "aiie": num(b),
            "aiie_language_modeling": num(aiie_lm.get(c, ("", None))[1]),
            "aiie_image_generation": num(aiie_ig.get(c, ("", None))[1]),
        })
with (DATA / "d3_aiie_industry_mapping.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(ind_rows[0].keys()))
    w.writeheader(); w.writerows(ind_rows)

# ---- write occupation mapping ----
occ_rows = []
for sector, basis, codes in OCC_MAP:
    for c in codes:
        if c not in aioe:
            continue
        title, b = aioe[c]
        occ_rows.append({
            "study_sector": sector, "mapping_basis": basis, "soc": c,
            "occupation_title": title, "aioe": num(b),
            "aioe_language_modeling": num(aioe_lm.get(c, ("", None))[1]),
            "aioe_image_generation": num(aioe_ig.get(c, ("", None))[1]),
        })
with (DATA / "d3_aioe_occupation_mapping.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(occ_rows[0].keys()))
    w.writeheader(); w.writerows(occ_rows)

# ---- summary (long format): per sector x level x subset x measure ----
def summarize(rows, level, valcols):
    out = []
    groups = {}
    for r in rows:
        groups.setdefault((r["study_sector"], r["mapping_basis"]), []).append(r)
    for (sector, basis), rs in groups.items():
        for measure, col in valcols:
            vals = [r[col] for r in rs if isinstance(r[col], (int, float))]
            if not vals:
                continue
            out.append({
                "study_sector": sector, "level": level, "subset": basis,
                "measure": measure, "n": len(vals),
                "mean": round(mean(vals), 3),
                "min": round(min(vals), 3), "max": round(max(vals), 3),
            })
    return out


summary = []
summary += summarize(ind_rows, "industry_AIIE", [
    ("baseline", "aiie"), ("language_modeling", "aiie_language_modeling"),
    ("image_generation", "aiie_image_generation")])
summary += summarize(occ_rows, "occupation_AIOE", [
    ("baseline", "aioe"), ("language_modeling", "aioe_language_modeling"),
    ("image_generation", "aioe_image_generation")])
with (DATA / "d3_sector_exposure_summary.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["study_sector", "level", "subset", "measure",
                                      "n", "mean", "min", "max"])
    w.writeheader(); w.writerows(summary)

print(f"Wrote {len(ind_rows)} industry rows, {len(occ_rows)} occupation rows.")
print("\nBaseline exposure by sector (mean of mapped rows):")
for s in summary:
    if s["measure"] == "baseline":
        print(f"  {s['study_sector']:24} {s['level']:15} {s['subset'][:38]:38} "
              f"n={s['n']:<2} mean={s['mean']:+.3f}  [{s['min']:+.2f},{s['max']:+.2f}]")
