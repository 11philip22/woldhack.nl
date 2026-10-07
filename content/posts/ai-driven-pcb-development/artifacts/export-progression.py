"""Export the three historical blog image sets using native KiCad rendering.

Run with a Python environment containing pcbnew, pymupdf and Pillow.
Snapshots and visualization boards live in tmp/blog-progression; the editable
project and the existing blog images are never overwritten.
"""

from pathlib import Path
import hashlib
import io
import json
import re
import shutil
import subprocess
import tarfile
import zipfile

import pymupdf as fitz
import pcbnew as p
from PIL import Image, ImageDraw, ImageFont


BLOG = Path(__file__).resolve().parent
ROOT = BLOG.parent.parent
DEST = BLOG / "progression"
WORK = ROOT / "tmp/blog-progression"
COMMITS = [
    ("a627b29d680920cf5b9b6f76a6aed861810e8d70", "Initial design"),
    ("8680d73865f22a1943d15248e457bbbdaa7a60de", "AI grouping"),
    ("da82a7a92dbb23ac15a034e49343de3bbd02c816", "Manual fixes"),
]
MODEL = BLOG / "models/YAAJ_BluePill_PinHeaders_H_SWD_cp.wrl"
IMAGES = ["bluepill-tilted", "bluepill-top-down", "pcb-layout", "schematic"]


def run(*args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"{' '.join(map(str, args))}\n{result.stdout}\n{result.stderr}")
    return result.stdout.strip()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(commit):
    source = WORK / commit[:7]
    source.mkdir(parents=True, exist_ok=True)
    archive = subprocess.check_output(
        ["git", "archive", commit, "bluepill-vbus-switch.kicad_pcb",
         "bluepill-vbus-switch.kicad_sch", "bluepill-vbus-switch.kicad_pro",
         "library", "fp-lib-table", "sym-lib-table"], cwd=ROOT,
    )
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(source, filter="data")
    return source


def assembly(source):
    render = source / "render"
    render.mkdir(exist_ok=True)
    target = render / "bluepill-assembled.kicad_pcb"
    target.write_text(
        (source / "bluepill-vbus-switch.kicad_pcb").read_text()
        .replace("${KIPRJMOD}", source.as_posix())
    )
    board = p.LoadBoard(str(target))
    # Same visualization-only model, position and elevation as prepare-render.py.
    module = p.FOOTPRINT(board)
    module.SetReference("BLUEPILL")
    module.SetValue("Blue Pill - visualization only")
    module.Reference().SetVisible(False)
    module.Value().SetVisible(False)
    module.SetPosition(p.VECTOR2I(p.FromMM(102.37), p.FromMM(99.12)))
    module.SetOrientationDegrees(90)
    model = p.FP_3DMODEL()
    model.m_Filename = MODEL.as_posix()
    model.m_Offset = p.VECTOR3D(0, 0, 8.5)
    model.m_Scale = p.VECTOR3D(1, 1, 1)
    model.m_Rotation = p.VECTOR3D(0, 0, 0)
    module.Models().push_back(model)
    board.Add(module)
    p.SaveBoard(str(target), board)
    shutil.copyfile(source / "bluepill-vbus-switch.kicad_pro", target.with_suffix(".kicad_pro"))
    return target


def rasterize(source, target, width):
    with fitz.open(source) as doc:
        page = doc[0]
        scale = width / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        pix.save(target)


def drawings(source, output):
    raw = source / "render/pcb-layout-source.svg"
    run("kicad-cli", "pcb", "export", "svg", "--layers", "F.Cu,B.Cu,F.SilkS,Edge.Cuts",
        "--mode-single", "--page-size-mode", "2", "--exclude-drawing-sheet",
        "--output", str(raw), str(source / "bluepill-vbus-switch.kicad_pcb"))
    svg = raw.read_text()
    x, y, width, height = map(float, re.search(r'viewBox="([^"]+)"', svg)[1].split())
    margin = 2
    view = f"{x-margin} {y-margin} {width+2*margin} {height+2*margin}"
    svg = re.sub(r'viewBox="[^"]+"', f'viewBox="{view}"', svg, count=1)
    svg = re.sub(r'width="[\d.]+mm" height="[\d.]+mm"',
                 f'width="{width+2*margin}mm" height="{height+2*margin}mm"', svg, count=1)
    end = svg.index(">", svg.index("<svg")) + 1
    background = (f'\n<rect x="{x-margin}" y="{y-margin}" width="{width+2*margin}" '
                  f'height="{height+2*margin}" fill="#161a20"/>\n')
    (output / "pcb-layout.svg").write_text(svg[:end] + background + svg[end:])
    sch_dir = source / "render/schematic-source"
    run("kicad-cli", "sch", "export", "svg", "--output", str(sch_dir),
        str(source / "bluepill-vbus-switch.kicad_sch"))
    shutil.copyfile(sch_dir / "bluepill-vbus-switch.svg", output / "schematic.svg")
    rasterize(output / "pcb-layout.svg", output / "pcb-layout.png", 2800)
    rasterize(output / "schematic.svg", output / "schematic.png", 3600)


def comparisons():
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    for name in IMAGES:
        tile_width, tile_height, header, margin = 1000, 800, 100, 30
        canvas = Image.new("RGB", (tile_width * len(COMMITS), tile_height + header), "#f5f4ef")
        draw = ImageDraw.Draw(canvas)
        frames = [Image.open(DEST / commit[:7] / f"{name}.png").convert("RGBA")
                  for commit, _ in COMMITS]
        # Remove the render canvas padding with one shared crop, keeping all
        # three boards at the same origin and scale in the comparison.
        if name.startswith("bluepill-"):
            bounds = [frame.getbbox() for frame in frames]
            crop = (max(0, min(b[0] for b in bounds)-60),
                    max(0, min(b[1] for b in bounds)-60),
                    min(frames[0].width, max(b[2] for b in bounds)+60),
                    min(frames[0].height, max(b[3] for b in bounds)+60))
            frames = [frame.crop(crop) for frame in frames]
        for index, (commit, title) in enumerate(COMMITS):
            left = index * tile_width
            draw.text((left+margin, 18), title, font=font, fill="#161a20")
            draw.text((left+margin, 58), commit[:7], font=small, fill="#515967")
            im = frames[index]
            im.thumbnail((tile_width-2*margin, tile_height-2*margin), Image.Resampling.LANCZOS)
            canvas.paste(im, (left+(tile_width-im.width)//2, header+(tile_height-im.height)//2), im)
        canvas.save(DEST / f"progression-{name}.png")


def bundle():
    # Bundle only publishing assets; the native project snapshots stay in tmp.
    with zipfile.ZipFile(BLOG.parent / "blog-progression-images.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(DEST.rglob("*")):
            if path.is_file() and path.suffix in {".png", ".svg", ".json"}:
                archive.write(path, path.relative_to(BLOG))


def main():
    if not MODEL.is_file():
        raise FileNotFoundError(MODEL)
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = {
        "renderer": run("kicad-cli", "version"),
        "camera": {"width": 2600, "height": 1800, "zoom": 0.7,
                   "projection": "orthographic", "tilt_degrees": -40,
                   "background": "transparent", "quality": "basic"},
        "module_model": {"path": str(MODEL.relative_to(ROOT)), "sha256": sha256(MODEL),
                         "offset_mm": [0, 0, 8.5]},
        "stages": [],
    }
    for commit, title in COMMITS:
        print(f"Exporting {commit[:7]}: {title}", flush=True)
        source = snapshot(commit)
        output = DEST / commit[:7]
        output.mkdir(exist_ok=True)
        board = assembly(source)
        for name, rotation in [("bluepill-tilted", "320,0,0"), ("bluepill-top-down", "0,0,0")]:
            run("kicad-cli", "pcb", "render", "--output", str(output / f"{name}.png"),
                "--width", "2600", "--height", "1800", "--side", "top",
                "--background", "transparent", "--quality", "basic", "--zoom", "0.7",
                "--rotate", rotation, str(board))
        drawings(source, output)
        manifest["stages"].append({
            "commit": commit, "title": title,
            "subject": run("git", "show", "-s", "--format=%s", commit),
            "source_sha256": {name: sha256(source / name) for name in
                              ["bluepill-vbus-switch.kicad_pcb", "bluepill-vbus-switch.kicad_sch"]},
            "images": {name: {"file": f"{commit[:7]}/{name}.png",
                              "size": list(Image.open(output / f"{name}.png").size)} for name in IMAGES},
        })
        print(f"Finished {commit[:7]}", flush=True)
    comparisons()
    (DEST / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    bundle()
    print(f"Images: {DEST}\nBundle: {BLOG.parent / 'blog-progression-images.zip'}", flush=True)


if __name__ == "__main__":
    main()
