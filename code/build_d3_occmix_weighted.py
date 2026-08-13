#!/usr/bin/env python3
"""
D3 refinement — occupation-mix-weighted AI exposure per sector (guide Analysis 2).

Combines:
  - Brazil occupation mix within each sector (PNADC 2024 microdata, weighted;
    from build_d3_occmix_pass.py -> data/raw/pnadc_micro/occmix_2024.json)
  - Felten et al. AIOE, aggregated to ISCO-08 major groups via US SOC major groups

sector_exposure = sum_g ( share of ISCO group g in the sector ) x AIOE(g)

This is the guide's preferred mapping ("map the exposure index to each sector via
its occupation mix"), using BRAZIL's own occupation weights rather than US
industry weights (as AIIE does). See README for caveats.
"""
import csv, glob, json
from statistics import mean
import openpyxl

DATA = "data"
occmix = json.load(open(f"{DATA}/raw/pnadc_micro/occmix_2024.json"))

# --- mean AIOE by US SOC major group (2-digit), computed from Appendix A ---
appx = sorted(glob.glob(f"{DATA}/raw/AIOE_DataAppendix_*.xlsx"))[-1]
wb = openpyxl.load_workbook(appx, read_only=True, data_only=True)
soc = {}
for i, r in enumerate(wb["Appendix A"].iter_rows(values_only=True)):
    if i < 1 or r[0] is None:
        continue
    if isinstance(r[2], (int, float)):
        soc.setdefault(str(r[0]).strip()[:2], []).append(r[2])
wb.close()
soc_mean = {k: mean(v) for k, v in soc.items()}

# --- ISCO-08 major group -> representative US SOC major group(s) (documented bridge) ---
# Labels are the full official ISCO-08 major-group titles (match T1, tab:isco08_groups).
ISCO = {
 "0": ("Armed forces occupations",                       ["33"]),
 "1": ("Managers",                                       ["11"]),
 "2": ("Professionals",                                  ["13","15","17","19","21","23","25","27","29"]),
 "3": ("Technicians and associate professionals",        ["13","15","17","27","29"]),
 "4": ("Clerical support workers",                       ["43"]),
 "5": ("Service and sales workers",                      ["31","33","35","39","41"]),
 "6": ("Skilled agricultural, forestry and fishery workers",["45"]),
 "7": ("Craft and related trades workers",               ["47","49","51"]),
 "8": ("Plant and machine operators, and assemblers",    ["51","53"]),
 "9": ("Elementary occupations",                         ["35","37","45","53"]),
}
isco_aioe = {g: round(mean(soc_mean[s] for s in socs), 3) for g,(nm,socs) in ISCO.items()}

# --- write the ISCO-group AIOE profile ---
with open(f"{DATA}/d3_isco_group_aioe_profile.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["isco_major_group","label","aioe","soc_groups_used"])
    for g,(nm,socs) in ISCO.items():
        w.writerow([g, nm, isco_aioe[g], "+".join(socs)])

# --- occupation mix + weighted exposure per sector ---
NAMES={g:nm for g,(nm,_) in ISCO.items()}
mix_rows=[]; summary=[]
for s, mix in occmix["mix"].items():
    tot=sum(mix.values())
    exposure=0.0
    for g in sorted(mix):
        share=mix[g]/tot
        contrib=share*isco_aioe[g]
        exposure+=contrib
        mix_rows.append({"study_sector":s,"isco_major_group":g,"label":NAMES[g],
                         "employed_thousands":round(mix[g]/1000,1),
                         "share_pct":round(100*share,2),"aioe_group":isco_aioe[g],
                         "contribution":round(contrib,4)})
    summary.append({"study_sector":s,"employed_thousands":round(tot/1000,1),
                    "occmix_weighted_aioe":round(exposure,3)})

with open(f"{DATA}/d3_occupation_mix_by_sector.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(mix_rows[0].keys())); w.writeheader(); w.writerows(mix_rows)

summary.sort(key=lambda r:-r["occmix_weighted_aioe"])
with open(f"{DATA}/d3_occmix_weighted_exposure.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0].keys())); w.writeheader(); w.writerows(summary)

print("ISCO major-group AIOE profile:")
for g,(nm,socs) in ISCO.items():
    print(f"  {g} {nm:34} AIOE={isco_aioe[g]:+.3f}  (SOC {'+'.join(socs)})")
print("\nOccupation-mix-weighted exposure per sector (Brazil weights x US AIOE):")
for r in summary:
    print(f"  {r['study_sector']:24} {r['employed_thousands']:>9.0f}k   exposure={r['occmix_weighted_aioe']:+.3f}")
