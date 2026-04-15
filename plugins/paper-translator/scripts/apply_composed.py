"""Place composed figure images into translated.md in a reproducible way.

This script is the final figure-placement step before validation.

Behavior:
- removes previously embedded composed figure/table images to avoid drift
- converts any remaining per-panel fig-NN runs into a single composed image
- inserts each composed figure after the first nearby `図 N` / `Figure N`
  textual reference in translated.md
- if a figure has no textual reference, appends it in a fallback section so
  validator coverage still stays explicit and reproducible

Usage:
    python apply_composed.py <output_dir>
"""
import json
import pathlib
import re
import sys


IMG_PANEL_RE = re.compile(r"^!\[([^\]]*)\]\(figures/(fig-\d+\.png)\)\s*$")
IMG_COMPOSED_RE = re.compile(
    r"^!\[[^\]]*\]\(figures/((?:figure|table)-\d+\.png)\)\s*$", re.IGNORECASE
)
REF_RE_TEMPLATE = r"(?:図|Figure)\s*{num}\b"
FALLBACK_HEADING = "## 図版一覧（自動補完）"


def load_plan(out_dir: pathlib.Path):
    plan = json.loads((out_dir / "figure_plan.json").read_text(encoding="utf-8"))
    composed = json.loads((out_dir / "figures_composed.json").read_text(encoding="utf-8"))
    placement_path = out_dir / "figure_placement.json"
    placement = {}
    if placement_path.exists():
        placement = json.loads(placement_path.read_text(encoding="utf-8"))
    return plan, composed, placement


def collapse_panel_runs(text: str, plan):
    file_to_fig = {}
    for p in plan:
        fn = p["figure_num"]
        if fn is None:
            continue
        for f in p["files"]:
            file_to_fig[f] = fn

    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        m = IMG_PANEL_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue

        run = []
        while i < len(lines):
            mm = IMG_PANEL_RE.match(lines[i])
            if not mm:
                break
            run.append((mm.group(1), mm.group(2)))
            i += 1

        fig_nums = {file_to_fig.get(fname) for _, fname in run}
        fig_nums.discard(None)
        if len(fig_nums) == 1:
            fn = next(iter(fig_nums))
            out.append(f"![Figure {fn}](figures/figure-{fn:02d}.png)")
        else:
            for alt, fname in run:
                out.append(f"![{alt}](figures/{fname})")

    return "\n".join(out)


def strip_old_composed_embeds(text: str):
    lines = []
    for line in text.splitlines():
        if IMG_COMPOSED_RE.match(line.strip()):
            continue
        lines.append(line)
    text = "\n".join(lines)
    if FALLBACK_HEADING in text:
        text = text.split(FALLBACK_HEADING, 1)[0].rstrip() + "\n"
    # Collapse any 3+ consecutive blank lines to 2 so repeated runs stay idempotent
    # (insertion leaves an extra blank that would otherwise accumulate).
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def paragraph_end(text: str, pos: int):
    end = text.find("\n\n", pos)
    if end == -1:
        return len(text)
    return end


def insert_after_marker(text: str, image_line: str, marker: str):
    idx = text.find(marker)
    if idx == -1:
        return text, False
    line_end = text.find("\n", idx)
    if line_end == -1:
        line_end = len(text)
    block = "\n\n" + image_line + "\n"
    return text[: line_end + 1] + block + text[line_end + 1 :], True


def insert_after_reference(text: str, image_line: str, figure_num: int):
    ref_re = re.compile(REF_RE_TEMPLATE.format(num=figure_num))
    match = ref_re.search(text)
    if not match:
        return text, False
    insert_at = paragraph_end(text, match.end())
    block = "\n" + image_line + "\n"
    return text[:insert_at] + block + text[insert_at:], True


def append_fallback(text: str, missing):
    if not missing:
        return text
    blocks = [
        "",
        FALLBACK_HEADING,
        "",
        "本文中に明示参照が見つからなかった図を、欠落防止のため末尾に配置する。",
        "",
    ]
    for num, image_line in missing:
        blocks.append(f"### 図 {num}")
        blocks.append("")
        blocks.append(image_line)
        blocks.append("")
    return text.rstrip() + "\n" + "\n".join(blocks)


def main():
    out_dir = pathlib.Path(sys.argv[1])
    md_path = out_dir / "translated.md"
    plan, composed, placement = load_plan(out_dir)
    plan_by_num = {p["figure_num"]: p for p in plan if p["figure_num"] is not None}

    text = md_path.read_text(encoding="utf-8")
    text = collapse_panel_runs(text, plan)
    text = strip_old_composed_embeds(text)

    missing = []
    inserted = 0
    for item in composed.get("figures", []):
        num = item["figure_num"]
        caption = plan_by_num.get(num, {}).get("caption_hint", f"Figure {num}")
        image_line = f"![Figure {num}. {caption}](figures/{item['file']})"
        ok = False
        explicit = placement.get(str(num)) or placement.get(num)
        if isinstance(explicit, dict) and explicit.get("after_heading"):
            text, ok = insert_after_marker(text, image_line, explicit["after_heading"])
        if not ok:
            text, ok = insert_after_reference(text, image_line, num)
        if ok:
            inserted += 1
        else:
            missing.append((num, image_line))

    text = append_fallback(text, missing)
    md_path.write_text(text, encoding="utf-8")
    print(
        f"[ok] placed composed figures into {md_path} "
        f"(inline={inserted}, fallback={len(missing)})"
    )


if __name__ == "__main__":
    main()
