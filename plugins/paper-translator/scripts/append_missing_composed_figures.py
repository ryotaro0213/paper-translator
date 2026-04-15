"""Append any missing composed figures to translated.md as a fallback gallery.

This prevents composed images from being silently dropped when the translation
does not yet contain explicit in-text anchors for every figure.

Usage:
    python append_missing_composed_figures.py <output_dir>
"""
import sys, json, pathlib, re


def main():
    out_dir = pathlib.Path(sys.argv[1])
    md_path = out_dir / "translated.md"
    plan_path = out_dir / "figure_plan.json"
    composed_path = out_dir / "figures_composed.json"

    if not md_path.exists() or not composed_path.exists() or not plan_path.exists():
        raise SystemExit("[error] required files are missing")

    md = md_path.read_text(encoding="utf-8")
    composed = json.loads(composed_path.read_text(encoding="utf-8"))
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan_by_num = {p["figure_num"]: p for p in plan if p["figure_num"] is not None}

    existing = set(
        int(m.group(1))
        for m in re.finditer(r"figures/figure-(\d+)\.png", md, re.IGNORECASE)
    )

    missing = []
    for item in composed.get("figures", []):
        num = item["figure_num"]
        if num in existing:
            continue
        caption = plan_by_num.get(num, {}).get("caption_hint", f"Figure {num}")
        missing.append((num, item["file"], caption))

    if not missing:
        print("[ok] no missing composed figures")
        return

    blocks = [
        "",
        "## 図版一覧（自動補完）",
        "",
        "本文アンカーに未挿入だった図を、欠落防止のためここにまとめて補完する。",
        "",
    ]
    for num, fname, caption in missing:
        blocks.append(f"### 図 {num}")
        blocks.append("")
        blocks.append(f"![Figure {num}. {caption}](figures/{fname})")
        blocks.append("")

    md_path.write_text(md.rstrip() + "\n" + "\n".join(blocks), encoding="utf-8")
    print(f"[ok] appended {len(missing)} missing composed figures to {md_path}")


if __name__ == "__main__":
    main()
