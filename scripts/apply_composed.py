"""Rewrite translated.md to use composed per-Figure images.

Replaces each consecutive block of ![...](figures/fig-NN.png) lines that
all belong to the same captioned Figure with a single
![Figure N ...](figures/figure-NN.png) reference.

Usage:
    python apply_composed.py <output_dir>
"""
import sys, re, json, pathlib


def main():
    out_dir = pathlib.Path(sys.argv[1])
    md_path = out_dir / "translated.md"
    plan = json.loads((out_dir / "figure_plan.json").read_text(encoding="utf-8"))

    file_to_fig = {}
    fig_to_caption = {}
    for p in plan:
        fn = p["figure_num"]
        if fn is None:
            continue
        for f in p["files"]:
            file_to_fig[f] = fn
        fig_to_caption[fn] = p.get("caption_hint", "") or f"Figure {fn}"

    src = md_path.read_text(encoding="utf-8")
    lines = src.split("\n")
    out = []
    i = 0
    IMG = re.compile(r"^!\[([^\]]*)\]\(figures/(fig-\d+\.png)\)\s*$")

    while i < len(lines):
        m = IMG.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        run = []
        while i < len(lines):
            mm = IMG.match(lines[i])
            if not mm:
                break
            run.append((mm.group(1), mm.group(2)))
            i += 1
        fignums = {file_to_fig.get(f) for _, f in run}
        fignums.discard(None)
        if len(fignums) == 1:
            fn = next(iter(fignums))
            alt = f"Figure {fn}"
            out.append(f"![{alt}](figures/figure-{fn:02d}.png)")
        else:
            for alt, f in run:
                out.append(f"![{alt}](figures/{f})")

    md_path.write_text("\n".join(out), encoding="utf-8")
    print(f"[ok] rewrote {md_path}")


if __name__ == "__main__":
    main()
