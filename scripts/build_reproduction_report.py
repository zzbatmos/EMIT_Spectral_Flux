"""Render the maintained Markdown guide and generated figures into a paginated PDF."""
import argparse
import html
import json
from pathlib import Path
import re
import unicodedata

import markdown
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/REPRODUCTION_GUIDE.md'
OUTPUT = ROOT / 'docs/EMIT_CERES_Reproduction_Guide.pdf'
CSS = '''
body { font-family: sans-serif; font-size: 10pt; line-height: 1.35; color: #233247; }
h1 { font-size: 25pt; color: #133c59; margin-bottom: 14pt; }
h2 { font-size: 16pt; color: #133c59; margin-top: 20pt; margin-bottom: 8pt; }
h3 { font-size: 12pt; color: #176c80; margin-top: 14pt; margin-bottom: 6pt; }
p { margin-top: 5pt; margin-bottom: 9pt; }
li { margin-bottom: 5pt; }
a { color: #176c80; }
code { font-family: monospace; font-size: 8pt; }
pre { font-family: monospace; font-size: 7.6pt; line-height: 1.25;
      white-space: pre-wrap; padding: 9pt; }
table { border-collapse: collapse; width: 100%; margin-top: 8pt; margin-bottom: 12pt;
        font-size: 8.4pt; }
th { color: #133c59; text-align: left; }
td, th { border: 0.5pt solid #c6d3dc; padding: 5pt; vertical-align: top; }
table code { font-size: 7.2pt; }
.figure { text-align: center; margin-top: 12pt; }
.caption { font-size: 9pt; color: #526172; }
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    verification = json.loads((ROOT / 'outputs/raw_reproduction/verification.json').read_text())
    if not verification.get('comparison_checked') or verification.get('verified_cases') != 577:
        raise RuntimeError('Run verify_reproduction.py --check-comparison before building the report')
    body = markdown.markdown(SOURCE.read_text(), extensions=['tables', 'fenced_code'])
    body = body.replace('<h2>10. Provenance', '<h2 style="page-break-before: always">10. Provenance')

    def image_tag(match):
        attrs = match.group(1)
        src = re.search(r'src="([^"]+)"', attrs).group(1)
        path = (SOURCE.parent / html.unescape(src)).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        relative = path.relative_to(ROOT).as_posix()
        width = 270 if 'collocation_map' in path.name else 490
        attrs = re.sub(r'src="[^"]+"', f'src="{relative}"', attrs)
        return f'<div class="figure"><img {attrs} width="{width}" /></div>'

    body = re.sub(r'<p><img\s+([^>]+?)/?></p>', image_tag, body)
    body = re.sub(r'<p><em>(Figure .*?)</em></p>', r'<p class="caption">\1</p>', body, flags=re.S)
    story = pymupdf.Story(html=body, user_css=CSS, archive=pymupdf.Archive(str(ROOT)))
    page_box = pymupdf.paper_rect('a4')
    content_box = pymupdf.Rect(48, 48, page_box.width - 48, page_box.height - 47)
    doc = story.write_with_links(lambda number, filled: (page_box, content_box, None))
    for i, page in enumerate(doc):
        page.insert_text((48, 27), 'EMIT / CERES  |  Reproduction and restart guide', fontsize=8, color=(.3, .4, .47))
        page.draw_line((48, page_box.height - 32), (page_box.width - 48, page_box.height - 32), color=(.75, .8, .84), width=.5)
        page.insert_text((48, page_box.height - 20), 'Verified baseline: 27 September 2026', fontsize=8, color=(.3, .4, .47))
        page.insert_text((page_box.width - 102, page_box.height - 20), f'{i + 1} / {len(doc)}', fontsize=8, color=(.3, .4, .47))
    doc.set_metadata({'title': 'EMIT–CERES spectral flux: reproduction guide',
                      'author': 'Project documentation for Zhibo and Qianqian',
                      'subject': 'April 2023 raw-observation reproduction, methods, scripts and validation',
                      'creator': 'scripts/build_reproduction_report.py / PyMuPDF'})
    bookmarks = []
    for heading in re.findall(r'^## (.+)$', SOURCE.read_text(), flags=re.M):
        for index, page in enumerate(doc):
            text = ' '.join(unicodedata.normalize('NFKC', page.get_text()).split())
            if heading in text:
                bookmarks.append([1, heading, index + 1])
                break
    doc.set_toc(bookmarks)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(args.output), garbage=4, deflate=True)
    print(f'Wrote {args.output} ({len(doc)} pages)')


if __name__ == '__main__':
    main()
