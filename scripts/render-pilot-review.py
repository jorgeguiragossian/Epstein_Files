"""Optional local QA contact sheet. Requires pypdfium2 and Pillow."""
from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PICKS = [('ds03-EFTA00004105.pdf', 1), ('ds04-EFTA00005705.pdf', 0),
         ('ds06-EFTA00008529.pdf', 0), ('ds11-EFTA02212905.pdf', 0)]
canvas = Image.new('RGB', (1224, 1650), '#dddddd')
draw = ImageDraw.Draw(canvas)
for i, (name, page_index) in enumerate(PICKS):
    document = pdfium.PdfDocument(str(ROOT / 'data/pilot/2026-11-01/cache' / name))
    page = document[page_index]
    bitmap = page.render(scale=1.1)
    image = bitmap.to_pil().convert('RGB')
    image.thumbnail((600, 785))
    x, y = (i % 2) * 612, (i // 2) * 825
    canvas.paste(image, (x, y + 30))
    draw.text((x + 8, y + 8), f'{name} page {page_index + 1}', fill='black')
    bitmap.close()
    page.close()
    document.close()
folder = ROOT / 'tmp/pilot-review'
folder.mkdir(parents=True, exist_ok=True)
canvas.save(folder / 'review-sheet.png')
print(folder / 'review-sheet.png')
