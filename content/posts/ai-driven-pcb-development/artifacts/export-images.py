"""Rasterize native KiCad vector exports for the blog."""
from pathlib import Path
import re
import fitz

dest = Path(__file__).resolve().parent
svg = (dest / 'pcb-layout-source.svg').read_text()
# Native SVG styling: give the editor's pale silk colour a dark canvas.
width, height = map(float, re.search(r'viewBox="0\.0000 0\.0000 ([\d.]+) ([\d.]+)"', svg).groups())
margin = 2
svg = re.sub(r'viewBox="[^"]+"', f'viewBox="{-margin} {-margin} {width+2*margin} {height+2*margin}"', svg, count=1)
svg = re.sub(r'width="[\d.]+mm" height="[\d.]+mm"', f'width="{width+2*margin}mm" height="{height+2*margin}mm"', svg, count=1)
end = svg.index('>', svg.index('<svg'))+1
svg = svg[:end] + f'\n<rect x="{-margin}" y="{-margin}" width="{width+2*margin}" height="{height+2*margin}" fill="#161a20"/>\n' + svg[end:]
(dest / 'pcb-layout.svg').write_text(svg)
schematic = (dest / 'schematic-source/bluepill-vbus-switch.svg').read_bytes()
(dest / 'schematic.svg').write_bytes(schematic)
for name, pixels in [('pcb-layout', 2800), ('schematic', 3600)]:
    doc = fitz.open(dest / f'{name}.svg')
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(pixels/page.rect.width, pixels/page.rect.width), alpha=False)
    pix.save(dest / f'{name}.png')
    print(name, pix.width, pix.height)
