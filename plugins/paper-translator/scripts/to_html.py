"""Convert translated.md to standalone HTML with inlined images and
spatial layout reconstruction.

Fallback for environments without pandoc.

Features:
- TOC, CSS, base64-inlined images (single-file portable HTML)
- Detects consecutive image runs in markdown and re-renders them with
  CSS Grid layout matching the original PDF spatial arrangement
  (reads bbox info from figures_index.json)

Usage:
    python to_html.py <output_dir>
"""
import sys, re, base64, json, pathlib, mimetypes
import markdown

out_dir = pathlib.Path(sys.argv[1])
md_path = out_dir / "translated.md"
html_path = out_dir / "translated.html"
css_path = pathlib.Path(__file__).parent / "paper.css"
idx_path = out_dir / "figures_index.json"

src = md_path.read_text(encoding="utf-8")
idx_by_file = {}
if idx_path.exists():
    for e in json.loads(idx_path.read_text(encoding="utf-8")):
        idx_by_file[e["file"]] = e


IMG_LINE_RE = re.compile(r"^!\[([^\]]*)\]\(figures/(fig-\d+\.png)\)\s*$")


def detect_grid(files):
    """Given a list of image filenames, infer (rows, cols) layout from bbox.

    Returns (rows, cols) or None if uniform layout can't be detected.
    All files must be on the same page for grid layout.
    """
    bboxes = []
    pages = set()
    for f in files:
        e = idx_by_file.get(f)
        if not e or not e.get("bbox"):
            return None
        bboxes.append((f, e["bbox"], e["page"]))
        pages.add(e["page"])
    if len(pages) != 1:
        return None

    y_tol, x_tol = 40, 40
    y_clusters = []
    for _, bb, _ in bboxes:
        y0 = bb[1]
        for cluster in y_clusters:
            if abs(cluster[0] - y0) <= y_tol:
                cluster.append(y0)
                cluster[0] = sum(cluster[1:]) / (len(cluster) - 1)
                break
        else:
            y_clusters.append([y0, y0])
    n_rows = len(y_clusters)

    x_clusters = []
    for _, bb, _ in bboxes:
        x0 = bb[0]
        for cluster in x_clusters:
            if abs(cluster[0] - x0) <= x_tol:
                cluster.append(x0)
                cluster[0] = sum(cluster[1:]) / (len(cluster) - 1)
                break
        else:
            x_clusters.append([x0, x0])
    n_cols = len(x_clusters)

    if n_rows * n_cols < len(files):
        n_cols = max(1, len(files) // n_rows)

    return (n_rows, n_cols)


def transform_image_blocks(md_text):
    """Find runs of consecutive image lines and replace with HTML grid wrappers."""
    lines = md_text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        if IMG_LINE_RE.match(lines[i]):
            run_start = i
            run = []
            while i < len(lines) and IMG_LINE_RE.match(lines[i]):
                m = IMG_LINE_RE.match(lines[i])
                run.append((m.group(1), m.group(2)))
                i += 1
            if len(run) <= 1:
                out.extend(lines[run_start:i])
                continue
            files = [f for _, f in run]
            grid = detect_grid(files)
            if grid is None:
                out.extend(lines[run_start:i])
                continue
            rows, cols = grid
            cls = f"fig-grid cols-{cols}"
            out.append("")
            out.append(f'<div class="{cls}">')
            for alt, f in run:
                out.append(
                    f'<figure class="fig-cell">'
                    f'<img alt="{alt}" src="figures/{f}">'
                    f'<figcaption>{alt}</figcaption>'
                    f'</figure>'
                )
            out.append("</div>")
            out.append("")
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out)


src = transform_image_blocks(src)

title_match = re.search(r"^#\s+(.+)$", src, re.M)
title = title_match.group(1) if title_match else "Translation"

md = markdown.Markdown(
    extensions=[
        "extra",          # tables, fenced_code, etc.
        "toc",
        "sane_lists",
        "codehilite",
    ],
    extension_configs={
        "toc": {"toc_depth": "2-3", "permalink": False},
        "codehilite": {"guess_lang": False, "noclasses": True},
    },
)

html_body = md.convert(src)
toc = md.toc


def inline_image(match):
    alt, rel = match.group(1), match.group(2)
    img = (out_dir / rel).resolve()
    if not img.exists():
        return match.group(0)
    mime, _ = mimetypes.guess_type(str(img))
    mime = mime or "image/png"
    data = base64.b64encode(img.read_bytes()).decode("ascii")
    return f'<img alt="{alt}" src="data:{mime};base64,{data}">'


html_body = re.sub(r'<img alt="([^"]*)" src="([^"]+)"\s*/?>', inline_image, html_body)

css = css_path.read_text(encoding="utf-8") if css_path.exists() else """
body{font-family:"Yu Gothic",sans-serif;max-width:860px;margin:2em auto;padding:0 1em;line-height:1.75}
img{max-width:100%;height:auto;display:block;margin:1em auto;border:1px solid #ddd;border-radius:4px}
table{border-collapse:collapse;width:100%;margin:1em 0}
th,td{border:1px solid #ddd;padding:.4em .7em}
th{background:#f7f9fc}
pre{background:#f4f4f4;padding:.8em;overflow-x:auto;border-radius:4px}
code{background:#f4f4f4;padding:0 .3em;border-radius:3px}
h1{border-bottom:2px solid #0b5cad;padding-bottom:.3em}
h2{border-bottom:1px solid #e0e0e0;padding-bottom:.25em;margin-top:2em}
h3{color:#0b5cad}
"""

html = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>{css}
nav.toc{{background:#f7f9fc;border:1px solid #e0e0e0;border-radius:6px;padding:1em 1.5em;margin:1em 0 2em}}
nav.toc > ul{{margin:0}}
</style>
</head>
<body>
<nav class="toc"><strong>目次</strong>{toc}</nav>
{html_body}
</body>
</html>
"""

html_path.write_text(html, encoding="utf-8")
print(f"[ok] wrote {html_path} ({html_path.stat().st_size / 1024:.0f} KB)")
