"""Build a deterministic figure insertion plan BEFORE translation.

Reads figures_index.json + extracted_text.md and emits figure_plan.json:
a list of figures in original reading order, each with:
 - figure_num:  "Figure N" number (or null if uncaptioned)
 - files:       list of fig-NN.png files (subfigures grouped together)
 - page:        source page
 - anchor_text: the exact paragraph (final ~160 chars) after which the figure
                should be embedded. Translator must place image(s) right
                after the Japanese translation of this paragraph.

Usage:
    python plan_figures.py <output_dir>
"""
import sys, re, json, pathlib
from collections import OrderedDict


def _bbox_of(idx_by_file, fname):
    e = idx_by_file.get(fname)
    if not e or not e.get("bbox"):
        return (0, 0, 0, 0)
    return tuple(e["bbox"])


def reading_order_sort(files, idx_by_file, row_tol=40):
    """Sort image files by visual reading order (rows top-to-bottom,
    within each row left-to-right). row_tol is the y-coordinate tolerance
    for grouping into the same row (in PDF points; ~1pt = 1/72 inch).

    Returns the files in reading order. Files without a bbox come last,
    preserving their original order.
    """
    with_bbox, without_bbox = [], []
    for f in files:
        bb = _bbox_of(idx_by_file, f)
        if bb == (0, 0, 0, 0):
            without_bbox.append(f)
        else:
            with_bbox.append((f, bb))

    with_bbox.sort(key=lambda fb: fb[1][1])  # sort by y0 ascending

    rows, current_row, current_y = [], [], None
    for f, bb in with_bbox:
        y0 = bb[1]
        if current_y is None or abs(y0 - current_y) <= row_tol:
            current_row.append((f, bb))
            current_y = y0 if current_y is None else (current_y + y0) / 2
        else:
            current_row.sort(key=lambda fb: fb[1][0])  # by x0
            rows.append(current_row)
            current_row = [(f, bb)]
            current_y = y0
    if current_row:
        current_row.sort(key=lambda fb: fb[1][0])
        rows.append(current_row)

    ordered = [f for row in rows for f, _ in row]
    return ordered + without_bbox

out_dir = pathlib.Path(sys.argv[1])
idx = json.loads((out_dir / "figures_index.json").read_text(encoding="utf-8"))
txt = (out_dir / "extracted_text.md").read_text(encoding="utf-8")
idx_by_file = {e["file"]: e for e in idx}


FIG_RE = re.compile(r"\b(?:Fig(?:ure)?\.?)\s+(\d+)\b", re.IGNORECASE)


def extract_fig_num(caption_hint: str):
    m = FIG_RE.search(caption_hint or "")
    return int(m.group(1)) if m else None


page_to_figs = {}
for entry in idx:
    fnum = extract_fig_num(entry.get("caption_hint", ""))
    if fnum is not None:
        page_to_figs.setdefault(entry["page"], set()).add(fnum)

page_dominant_fig = {}
for page, nums in page_to_figs.items():
    if len(nums) == 1:
        page_dominant_fig[page] = next(iter(nums))

groups = OrderedDict()
for entry in idx:
    fnum = extract_fig_num(entry.get("caption_hint", ""))
    if fnum is None and entry["page"] in page_dominant_fig:
        fnum = page_dominant_fig[entry["page"]]
        inherited = True
    else:
        inherited = False
    key = ("F", fnum) if fnum is not None else ("P", entry["page"], entry["file"])
    groups.setdefault(key, {
        "figure_num": fnum,
        "page": entry["page"],
        "files": [],
        "caption_hint": entry.get("caption_hint", ""),
        "inherited_files": [],
    })
    groups[key]["files"].append(entry["file"])
    if inherited:
        groups[key]["inherited_files"].append(entry["file"])


def anchor_paragraph(page: int, figure_num):
    """Find the paragraph in extracted_text.md where this figure is first referenced.

    Strategy: look for the FIRST occurrence of 'Figure N' in page order, starting
    from page P and walking backwards to the section/paragraph that introduces it.
    Returns the last ~160 characters (trimmed paragraph tail) to use as a
    unique anchor string.
    """
    page_marker = f"===== PAGE {page} ====="
    pi = txt.find(page_marker)
    if pi < 0:
        return None

    if figure_num is None:
        after = txt[pi: pi + 2000]
        paras = [p.strip() for p in after.split("\n\n") if p.strip()]
        return (paras[0] if paras else "")[-160:]

    pat = re.compile(rf"Figure\s+{figure_num}\b")
    region = txt[:pi + 4000]
    m = None
    for mm in pat.finditer(region):
        m = mm
    if m is None:
        region2 = txt[pi:]
        m2 = pat.search(region2)
        if not m2:
            return None
        start = pi + m2.start()
    else:
        start = m.start()

    head = txt[:start]
    para_start = max(head.rfind("\n\n"), head.rfind("===== PAGE"))
    para = txt[para_start:start].strip()
    para = re.sub(r"\s+", " ", para)
    return para[-160:] if para else None


plan = []
for g in groups.values():
    ordered_files = reading_order_sort(g["files"], idx_by_file)
    plan.append({
        "figure_num": g["figure_num"],
        "files": ordered_files,
        "inherited_files": g.get("inherited_files", []),
        "page": g["page"],
        "caption_hint": g["caption_hint"],
        "anchor_text": anchor_paragraph(g["page"], g["figure_num"]),
    })


def sort_key(p):
    fn = p["figure_num"]
    return (0, fn, p["page"]) if fn is not None else (1, p["page"], p["files"][0])


plan.sort(key=sort_key)

out_path = out_dir / "figure_plan.json"
out_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[ok] wrote {out_path}")
print(f"  captioned figures: {sum(1 for p in plan if p['figure_num'] is not None)}")
print(f"  uncaptioned groups: {sum(1 for p in plan if p['figure_num'] is None)}")
print(f"  total image files:  {sum(len(p['files']) for p in plan)}")
missing = [p for p in plan if p["anchor_text"] is None]
if missing:
    print(f"[warn] {len(missing)} figure(s) have no anchor text (may be uncaptioned or caption not parsed):")
    for p in missing:
        print(f"   Figure {p['figure_num']} p.{p['page']} files={p['files']}")
