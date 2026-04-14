"""Extract text and figures from a PDF for translation.

Usage:
    python extract.py <pdf_path> <out_dir>

Produces:
    <out_dir>/figures/fig-NN.png     embedded images
    <out_dir>/figures/page-NNN.png   page renders (for vector figure review)
    <out_dir>/extracted_text.md      page-separated text dump
    <out_dir>/figures_index.json     per-image metadata (page, bbox, caption hint)
"""
import sys, io, os, json, pathlib, re
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

pdf_path = sys.argv[1]
out_dir = pathlib.Path(sys.argv[2])
fig_dir = out_dir / "figures"
fig_dir.mkdir(parents=True, exist_ok=True)

doc = fitz.open(pdf_path)

text_lines = []
fig_index = []
seen_xrefs = set()
fig_counter = 0

for pno, page in enumerate(doc, start=1):
    text = page.get_text("text")
    text_lines.append(f"\n\n===== PAGE {pno} =====\n\n{text}")

    # Embedded raster images
    for img in page.get_images(full=True):
        xref = img[0]
        if xref in seen_xrefs:
            continue
        seen_xrefs.add(xref)
        try:
            pix = fitz.Pixmap(doc, xref)
            if pix.n - pix.alpha > 3:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            fig_counter += 1
            fname = f"fig-{fig_counter:02d}.png"
            pix.save(str(fig_dir / fname))
            # caption hint: text block whose bbox top is near image bottom
            bboxes = page.get_image_rects(xref)
            bbox = bboxes[0] if bboxes else None
            caption = ""
            if bbox:
                for b in page.get_text("blocks"):
                    bx0, by0, bx1, by1, btxt = b[0], b[1], b[2], b[3], b[4]
                    if by0 > bbox.y1 - 5 and by0 < bbox.y1 + 80 and btxt.strip().lower().startswith(("figure", "fig.")):
                        caption = btxt.strip().replace("\n", " ")
                        break
            fig_index.append({
                "file": fname,
                "page": pno,
                "xref": xref,
                "bbox": [bbox.x0, bbox.y0, bbox.x1, bbox.y1] if bbox else None,
                "caption_hint": caption,
            })
            pix = None
        except Exception as e:
            print(f"[warn] page {pno} xref {xref}: {e}")

    # Also render whole page at low dpi for vector-figure fallback reference
    pm = page.get_pixmap(dpi=110)
    pm.save(str(fig_dir / f"page-{pno:03d}.png"))
    pm = None

(out_dir / "extracted_text.md").write_text("".join(text_lines), encoding="utf-8")
(out_dir / "figures_index.json").write_text(json.dumps(fig_index, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"pages: {doc.page_count}")
print(f"embedded figures saved: {fig_counter}")
print(f"text: {out_dir / 'extracted_text.md'}")
