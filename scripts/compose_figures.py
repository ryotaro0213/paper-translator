"""Compose per-Figure combined images by cropping source PDF pages.

For each captioned Figure in figure_plan.json, compute the union bbox of
all sub-panels on the page, expand to include the caption area, and
render that region from the original PDF at high DPI. This preserves
the exact spatial layout of the original paper.

Output: figures/figure-NN.png (one image per captioned Figure)

Usage:
    python compose_figures.py <output_dir>
"""
import sys, json, re, pathlib
import fitz


def find_caption_bbox(page, figure_num, kind="Figure"):
    """Locate the 'Figure N.' / 'Table N.' caption text block; return bbox or None."""
    pat = re.compile(rf"^{kind}\s+{figure_num}\.")
    for b in page.get_text("blocks"):
        x0, y0, x1, y1, txt = b[0], b[1], b[2], b[3], b[4]
        first_line = txt.strip().splitlines()[0] if txt.strip() else ""
        if pat.match(first_line):
            return (x0, y0, x1, y1)
    return None


def find_table_header_bbox(page, table_num):
    """Locate 'Table N.' text block (usually above the images)."""
    return find_caption_bbox(page, table_num, kind="Table")


def compose_table_region(page, page_num, table_num, all_page_images, idx_by_file):
    """Compose a single image for a Table that has image-grid content.

    Looks for the 'Table N.' header on this page; collects all page images
    that appear below the header (with no captioned Figure between them);
    renders the union region.
    """
    header_bb = find_table_header_bbox(page, table_num)
    if not header_bb:
        return None
    grid_files = []
    for e in all_page_images:
        if e["page"] != page_num:
            continue
        if not e.get("bbox"):
            continue
        if e["bbox"][1] < header_bb[1]:
            continue
        if e.get("caption_hint"):
            continue
        grid_files.append(e)
    if len(grid_files) < 2:
        return None
    panel_union = union_bbox([tuple(e["bbox"]) for e in grid_files])
    combined = union_bbox([header_bb, panel_union])
    return combined, [e["file"] for e in grid_files]


def union_bbox(bboxes):
    x0 = min(b[0] for b in bboxes)
    y0 = min(b[1] for b in bboxes)
    x1 = max(b[2] for b in bboxes)
    y1 = max(b[3] for b in bboxes)
    return (x0, y0, x1, y1)


def main():
    out_dir = pathlib.Path(sys.argv[1])
    pdf_path = out_dir / "original.pdf"
    plan = json.loads((out_dir / "figure_plan.json").read_text(encoding="utf-8"))
    idx = json.loads((out_dir / "figures_index.json").read_text(encoding="utf-8"))
    idx_by_file = {e["file"]: e for e in idx}

    fig_dir = out_dir / "figures"
    fig_dir.mkdir(exist_ok=True)

    doc = fitz.open(str(pdf_path))
    composed = []

    for p in plan:
        fn = p["figure_num"]
        if fn is None:
            continue

        page_num = p["page"]
        if page_num < 1 or page_num > doc.page_count:
            continue
        page = doc[page_num - 1]
        page_rect = page.rect

        panel_bboxes = []
        for f in p["files"]:
            e = idx_by_file.get(f)
            if e and e.get("bbox"):
                panel_bboxes.append(tuple(e["bbox"]))
        if not panel_bboxes:
            continue

        panel_union = union_bbox(panel_bboxes)
        caption_bb = find_caption_bbox(page, fn)

        if caption_bb:
            combined = union_bbox([panel_union, caption_bb])
        else:
            combined = (
                panel_union[0], panel_union[1],
                panel_union[2], panel_union[3] + 50,
            )

        pad = 6
        x0 = max(0, combined[0] - pad)
        y0 = max(0, combined[1] - pad)
        x1 = min(page_rect.x1, combined[2] + pad)
        y1 = min(page_rect.y1, combined[3] + pad)
        clip = fitz.Rect(x0, y0, x1, y1)

        pix = page.get_pixmap(clip=clip, dpi=180)
        out_file = fig_dir / f"figure-{fn:02d}.png"
        pix.save(str(out_file))
        pix = None
        composed.append({
            "figure_num": fn,
            "page": page_num,
            "file": out_file.name,
            "clip": [x0, y0, x1, y1],
            "has_caption": caption_bb is not None,
        })

    tables_composed = []
    import re as _re
    full_text = (out_dir / "extracted_text.md").read_text(encoding="utf-8") \
        if (out_dir / "extracted_text.md").exists() else ""
    table_refs = set(int(m.group(1)) for m in _re.finditer(r"Table\s+(\d+)\.", full_text))
    for tn in sorted(table_refs):
        for page_num_i in range(1, doc.page_count + 1):
            page = doc[page_num_i - 1]
            result = compose_table_region(page, page_num_i, tn, idx, idx_by_file)
            if not result:
                continue
            combined, member_files = result
            pad = 6
            page_rect = page.rect
            clip = fitz.Rect(
                max(0, combined[0] - pad),
                max(0, combined[1] - pad),
                min(page_rect.x1, combined[2] + pad),
                min(page_rect.y1, combined[3] + pad),
            )
            pix = page.get_pixmap(clip=clip, dpi=180)
            out_file = fig_dir / f"table-{tn:02d}.png"
            pix.save(str(out_file))
            pix = None
            tables_composed.append({
                "table_num": tn,
                "page": page_num_i,
                "file": out_file.name,
                "member_files": member_files,
            })
            break

    (out_dir / "figures_composed.json").write_text(
        json.dumps({"figures": composed, "tables": tables_composed},
                   ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[ok] composed {len(composed)} figures, {len(tables_composed)} tables")
    for c in composed:
        cap = "w/caption" if c["has_caption"] else "no caption"
        print(f"  Figure {c['figure_num']:2d} p.{c['page']} -> {c['file']} ({cap})")
    for t in tables_composed:
        print(f"  Table  {t['table_num']:2d} p.{t['page']} -> {t['file']} ({len(t['member_files'])} panels)")


if __name__ == "__main__":
    main()
