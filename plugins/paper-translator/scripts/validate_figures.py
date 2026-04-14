"""Validate figure placement in translated.md against figure_plan.json.

Checks:
  [C1] Coverage        : every Figure N in the plan appears in translated.md
  [C2] Order           : figures appear in same order as in the plan
  [C3] Caption match   : each embedded fig-NN sits near a 「図 N」/「Figure N」
                         reference whose number matches the plan
  [C4] Duplication     : no fig-NN used in more than one location
  [C5] Subfig cluster  : files for same Figure N appear contiguously
  [C6] Orphan refs     : 「図 N」 in translation has no accompanying image
  [C7] Unknown images  : embedded fig-NN not in figures_index
  [C8] Unused images   : fig-NN in figures_index but never embedded
                         (often sub-panels of multi-image figures)
  [C9] Alt-text mismatch : embedded image's alt-text says "Figure N" but
                           the planned figure_num differs
  [C10] Subpanel order  : sub-panel files within a Figure must appear in
                          the same order as in the spatially-sorted plan

Exits 0 if clean, 1 if warnings only, 2 if errors. Writes validation report
to <out_dir>/figure_validation.md and summary to stdout.

Usage:
    python validate_figures.py <output_dir>
"""
import sys, re, json, pathlib
from collections import defaultdict, OrderedDict

out_dir = pathlib.Path(sys.argv[1])
md_path = out_dir / "translated.md"
plan = json.loads((out_dir / "figure_plan.json").read_text(encoding="utf-8"))
idx = json.loads((out_dir / "figures_index.json").read_text(encoding="utf-8"))
md = md_path.read_text(encoding="utf-8")

idx_by_file = {e["file"]: e for e in idx}
plan_figs = [p for p in plan if p["figure_num"] is not None]
known_files = set(idx_by_file)

composed_path = out_dir / "figures_composed.json"
composed_fig_nums = set()
composed_table_nums = set()
composed_member_files = set()
if composed_path.exists():
    cdata = json.loads(composed_path.read_text(encoding="utf-8"))
    cfigs = cdata.get("figures", []) if isinstance(cdata, dict) else cdata
    ctabs = cdata.get("tables", []) if isinstance(cdata, dict) else []
    for c in cfigs:
        composed_fig_nums.add(c["figure_num"])
        known_files.add(c["file"])
    for t in ctabs:
        composed_table_nums.add(t["table_num"])
        known_files.add(t["file"])
        for mf in t.get("member_files", []):
            composed_member_files.add(mf)

plan_fig_nums = {p["figure_num"] for p in plan_figs}
plan_files_for_fig = {p["figure_num"]: set(p["files"]) for p in plan_figs}

IMG_RE = re.compile(r"!\[([^\]]*)\]\(figures/((?:fig|figure|table)-\d+\.png)\)")
COMPOSED_RE = re.compile(r"^(figure|table)-(\d+)\.png$")
FIGREF_RE = re.compile(r"(?:図|Figure)\s*(\d+)")


def extract_fig_num_local(caption_hint: str):
    m = re.search(r"Figure\s+(\d+)", caption_hint or "")
    return int(m.group(1)) if m else None

embeds = []
for m in IMG_RE.finditer(md):
    pos = m.start()
    alt = m.group(1)
    fname = m.group(2)
    window_before = md[max(0, pos - 400): pos]
    window_after = md[pos: pos + 400]
    ctx = window_before + window_after
    refs = [int(r) for r in FIGREF_RE.findall(ctx)]
    alt_fn_match = re.search(r"(?:Figure|図)\s*(\d+)", alt)
    alt_fn = int(alt_fn_match.group(1)) if alt_fn_match else None
    embeds.append({
        "file": fname,
        "alt": alt,
        "alt_fig_num": alt_fn,
        "pos": pos,
        "nearby_refs": refs,
        "caption_hint": idx_by_file.get(fname, {}).get("caption_hint", ""),
    })

errors, warnings, info = [], [], []

embedded_figure_nums = []
embedded_file_to_fignum = {}
for p in plan_figs:
    for f in p["files"]:
        embedded_file_to_fignum[f] = p["figure_num"]
for fn in composed_fig_nums:
    embedded_file_to_fignum[f"figure-{fn:02d}.png"] = fn

file_positions = defaultdict(list)
for e in embeds:
    file_positions[e["file"]].append(e["pos"])
for f, positions in file_positions.items():
    if len(positions) > 1:
        errors.append(f"[C4] duplicate: {f} embedded {len(positions)} times")

for e in embeds:
    if e["file"] not in known_files:
        errors.append(f"[C7] unknown image: {e['file']} not in figures_index.json")

planned_nums = [p["figure_num"] for p in plan_figs]
embedded_nums_ordered = []
seen = set()
for e in embeds:
    fn = embedded_file_to_fignum.get(e["file"])
    if fn is None:
        continue
    if fn not in seen:
        embedded_nums_ordered.append(fn)
        seen.add(fn)

missing = [n for n in planned_nums if n not in seen]
for n in missing:
    p = next(p for p in plan_figs if p["figure_num"] == n)
    errors.append(f"[C1] missing: Figure {n} (files={p['files']}, page={p['page']}) not embedded")

if embedded_nums_ordered != [n for n in planned_nums if n in seen]:
    errors.append(
        f"[C2] order mismatch:\n"
        f"      plan order      = {planned_nums}\n"
        f"      embedded order  = {embedded_nums_ordered}"
    )

for e in embeds:
    fn = embedded_file_to_fignum.get(e["file"])
    if fn is None:
        continue
    if fn not in e["nearby_refs"]:
        warnings.append(
            f"[C3] caption mismatch: {e['file']} (Figure {fn}) embedded "
            f"near 図/Figure refs {e['nearby_refs'] or 'none'} at char {e['pos']}"
        )
    if e["alt_fig_num"] is not None and e["alt_fig_num"] != fn:
        errors.append(
            f"[C9] alt-text mismatch: {e['file']} alt=\"{e['alt']}\" "
            f"says Figure {e['alt_fig_num']} but plan expects Figure {fn}"
        )

by_fig = defaultdict(list)
for i, e in enumerate(embeds):
    fn = embedded_file_to_fignum.get(e["file"])
    if fn is not None:
        by_fig[fn].append((i, e["file"]))
for fn, pairs in by_fig.items():
    indices = [p[0] for p in pairs]
    if indices and (max(indices) - min(indices) + 1) != len(indices):
        errors.append(f"[C5] subfigure scatter: Figure {fn} files non-contiguous (embed indices {indices})")

plan_by_fignum = {p["figure_num"]: p["files"] for p in plan_figs}
for fn, pairs in by_fig.items():
    embedded_order = [p[1] for p in pairs]
    composed_name = f"figure-{fn:02d}.png"
    if embedded_order == [composed_name]:
        continue
    expected_order = plan_by_fignum.get(fn, [])
    embedded_subset = [f for f in expected_order if f in embedded_order]
    if embedded_order != embedded_subset:
        errors.append(
            f"[C10] subpanel order mismatch for Figure {fn}:\n"
            f"       embedded = {embedded_order}\n"
            f"       expected = {expected_order}"
        )

refs_in_body = set()
for m in FIGREF_RE.finditer(md):
    refs_in_body.add(int(m.group(1)))
planned_set = set(planned_nums)
for n in sorted(refs_in_body & planned_set):
    if n not in seen:
        info.append(f"[C6] figure ref 図{n} in text but image not embedded")

embedded_files = set(file_positions)
for entry in idx:
    f = entry["file"]
    if f in embedded_files:
        continue
    fn_from_caption = extract_fig_num_local(entry.get("caption_hint", ""))
    if fn_from_caption is None:
        for fn, members in plan_files_for_fig.items():
            if f in members:
                fn_from_caption = fn
                break
    if fn_from_caption in composed_fig_nums and f"figure-{fn_from_caption:02d}.png" in embedded_files:
        continue
    if f in composed_member_files:
        continue
    if fn_from_caption is not None:
        warnings.append(
            f"[C8] unused subpanel: {f} (page {entry['page']}, belongs to Figure {fn_from_caption}) "
            f"— likely a sub-panel that should also be embedded"
        )
    else:
        warnings.append(
            f"[C8] unused image: {f} (page {entry['page']}, no caption) "
            f"— review whether it should be embedded"
        )

lines = [f"# 図の配置検証レポート — {out_dir.name}", ""]
lines.append(f"- 計画された図: {len(plan_figs)}")
lines.append(f"- 埋め込み画像: {len(embeds)} (ユニーク {len(set(e['file'] for e in embeds))})")
lines.append(f"- エラー: {len(errors)} / 警告: {len(warnings)} / 情報: {len(info)}")
lines.append("")
if errors:
    lines.append("## エラー (要修正)")
    lines += [f"- {e}" for e in errors]
    lines.append("")
if warnings:
    lines.append("## 警告 (要確認)")
    lines += [f"- {w}" for w in warnings]
    lines.append("")
if info:
    lines.append("## 情報")
    lines += [f"- {i}" for i in info]
    lines.append("")
lines.append("## 計画と埋め込みの対応表")
lines.append("")
lines.append("| Figure | 計画ファイル | 埋め込み | ページ |")
lines.append("|---|---|---|---|")
for p in plan_figs:
    status = "✓" if p["figure_num"] in seen else "✗ 未配置"
    lines.append(f"| {p['figure_num']} | {', '.join(p['files'])} | {status} | p.{p['page']} |")

report = "\n".join(lines)
(out_dir / "figure_validation.md").write_text(report, encoding="utf-8")

print(f"[validate] figures={len(plan_figs)} embeds={len(embeds)} "
      f"errors={len(errors)} warnings={len(warnings)} info={len(info)}")
for e in errors[:10]:
    print("  ERROR:", e)
for w in warnings[:10]:
    print("  WARN :", w)
print(f"  report: {out_dir / 'figure_validation.md'}")

if errors:
    sys.exit(2)
if warnings:
    sys.exit(1)
sys.exit(0)
