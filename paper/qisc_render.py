"""QISC strategy paper renderer: single-column working-paper format.

    python qisc_render.py example/manuscript.md "<output pdf path>"

Adapted from the two-column journal renderer used for the CDS lead-lag paper.

Reuses paper_engine/render.py for the Markdown subset and adds:
  - title block, author/affiliation lines, ARTICLE INFO | ABSTRACT panel, highlights (from front matter)
  - Elsevier numbering: "1. Introduction", "1.1. Data", "Appendix A. ...", Table/Fig. A.1 inside appendices
  - "Table 1" captions above tables, "Fig. 1." captions below figures, "Note:" lines as table notes
  - "Panel A: ..." rows inside tables spanning all columns
  - two-column body, tables and figures spanning both columns
"""
import html
import re
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent / "engine"
sys.path.insert(0, str(ENGINE))
import render as R  # noqa: E402

UNNUMBERED = ("references", "statement of originality", "code and data availability", "acknowledg")


class JDoc(R.Doc):
    def __init__(self, base_dir):
        super().__init__(base_dir)
        self.letter = None
        self.app_fig = self.app_tab = 0

    def _heading(self, ln):
        level = len(ln) - len(ln.lstrip("#"))
        title = ln.lstrip("#").strip()
        if level == 2:
            low = title.lower()
            if low.startswith("appendix"):
                m = re.match(r"appendix\s+([A-Z])[.:]?\s*(.*)", title, re.I)
                self.appendix = True
                self.letter = m.group(1).upper() if m else "A"
                self.sec = [self.sec[0], 0]
                self.app_fig = self.app_tab = 0
                rest = m.group(2) if m else ""
                return f'<h2 class="appendix">Appendix {self.letter}. {R._inline(rest)}</h2>'
            if low.startswith("references"):
                return f'<h2 class="unnumbered refhead">{R._inline(title)}</h2>'
            if low.startswith(UNNUMBERED):
                return f'<h2 class="unnumbered">{R._inline(title)}</h2>'
            self.sec = [self.sec[0] + 1, 0]
            return f'<h2><span class="secno">{self.sec[0]}.</span> {R._inline(title)}</h2>'
        self.sec[1] += 1
        no = f"{self.letter}.{self.sec[1]}." if self.appendix and self.letter else f"{self.sec[0]}.{self.sec[1]}."
        return f'<h3><span class="secno">{no}</span> {R._inline(title)}</h3>'

    def _numfig(self):
        if self.appendix and self.letter:
            self.app_fig += 1
            return f"{self.letter}.{self.app_fig}"
        self.fig += 1
        return str(self.fig)

    def _numtab(self):
        if self.appendix and self.letter:
            self.app_tab += 1
            return f"{self.letter}.{self.app_tab}"
        self.tab += 1
        return str(self.tab)

    def convert(self, md):
        # figures and table notes are handled here; everything else by the base converter
        out, buf = [], []
        lines = md.splitlines()

        def flush():
            if buf:
                out.append(super(JDoc, self).convert("\n".join(buf)))
                buf.clear()
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln.startswith("!["):
                flush()
                m = re.match(r"!\[(.*)\]\((.+?)\)(\{wide\})?", ln)
                n = self._numfig()
                out.append(f'<figure><img src="{m.group(2)}"><figcaption><b>Figure {n}.</b> {R._inline(m.group(1))}</figcaption></figure>')
            elif ln.startswith("$$"):
                flush()
                block = ln
                while block.count("$$") < 2 and i + 1 < len(lines):
                    i += 1
                    block += "\n" + lines[i]
                m = re.search(r"\(eq:([\w-]+)\)\s*$", block)
                tex = block[block.index("$$") + 2: block.rindex("$$")].strip()
                num = ""
                if m:
                    self.eq += 1
                    self.eq_labels[m.group(1)] = self.eq
                    num = f'<span class="eqno">({self.eq})</span>'
                out.append(f'<div class="eq"><div class="eqm">{html.escape("$$" + tex + "$$", quote=False)}</div>{num}</div>')
            elif re.match(r"^Notes?:", ln):
                flush()
                note = f'<p class="tnote">{R._inline(ln)}</p>'
                if out and out[-1].rstrip().endswith("</table></div>"):
                    out[-1] = out[-1].rstrip()[:-len("</div>")] + note + "</div>"
                else:
                    out.append(note)
            elif ln.startswith("REF: "):
                flush()
                refs = []
                while i < len(lines) and (lines[i].startswith("REF: ") or not lines[i].strip()):
                    if lines[i].startswith("REF: "):
                        refs.append(f'<p class="ref">{R._inline(lines[i][5:])}</p>')
                    i += 1
                i -= 1
                out.append('<div class="refs">' + "".join(refs) + "</div>")
            else:
                buf.append(ln)
            i += 1
        flush()
        return "\n".join(out)

    def _table(self, head, body, caption, css=""):
        ncol = len(head)
        data = [list(r) + [""] * (ncol - len(r)) for r in body]
        data = [r for r in data if not (r[0].strip("* ").lower().startswith("panel") and all(not x.strip() for x in r[1:]))]
        def is_text(k):
            cells = [r[k] for r in data if k < len(r) and r[k].strip()]
            if not cells:
                return False
            return sum(bool(re.search(r"[A-Za-z]{3,}", re.sub(r"(bp|sd|per|of|to|and|day|days)", "", c))) for c in cells) / len(cells) > 0.5
        align = ["left"] + ["left" if is_text(k) else "center" for k in range(1, ncol)]
        h = "".join(f'<th style="text-align:{align[k]}">{R._inline(c)}</th>' for k, c in enumerate(head))
        rows = []
        for r in body:
            r = list(r) + [""] * (ncol - len(r))
            if r[0].strip("* ").lower().startswith("panel") and all(not x.strip() for x in r[1:]):
                rows.append(f'<tr class="panel"><td colspan="{ncol}">{R._inline(r[0])}</td></tr>')
                continue
            rows.append("<tr>" + "".join(f'<td style="text-align:{align[k]}{"" if align[k] == "left" else ";white-space:nowrap"}">{R._inline(str(c))}</td>' for k, c in enumerate(r)) + "</tr>")
        cap = ""
        if caption:
            n = self._numtab()
            cap = f'<caption><span class="tabno">Table {n}.</span> {R._inline(caption)}</caption>'
        cls = f' class="{css}"' if css else ""
        blk = "tblock long" if css == "trades" else "tblock"
        return f'<div class="{blk}"><table{cls}>{cap}<thead><tr>{h}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def front(meta):
    kw = "; ".join(html.escape(k.strip()) for k in meta.get("keywords", "").split(";") if k.strip())
    authors = re.sub(r"\^([\w,*]+)", r"<sup>\1</sup>", html.escape(meta.get("authors", "")))
    affs = [a.strip() for a in meta.get("affiliations", "").split("||") if a.strip()]
    aff_html = "".join('<div class="aff">' + re.sub(r"^(\w)\s", r"<sup>\1</sup>", html.escape(a)) + "</div>" for a in affs)
    kw_html = f'<p class="kw"><i>Keywords:</i> {kw}</p>' if kw else ""
    return f"""
<header class="front">
  <div class="kicker">{R._inline(meta.get('kicker', ''))}</div>
  <h1 class="title">{R._inline(meta.get('title', ''))}</h1>
  <div class="authors">{authors}</div>
  <div class="affs">{aff_html}</div>
  <div class="meta">{R._inline(meta.get('meta', ''))}</div>
  <div class="abstract">
    <div class="abshead">Abstract</div>
    <p>{R._inline(meta.get('abstract', ''))}</p>
    {kw_html}
  </div>
  <div class="titlenote">{R._inline(meta.get('titlenote', ''))}</div>
</header>"""


CSS = r"""
@page { size: A4; margin: 25mm 25mm 24mm 25mm;
  @bottom-left { content: "__FOOTER__"; font: 8.5pt "STIX Two Text", Cambria, serif; color: #555;
                 border-top: 0.5px solid #999; padding-top: 2mm; vertical-align: top; }
  @bottom-right { content: counter(page); font: 8.5pt "STIX Two Text", Cambria, serif; color: #555;
                  border-top: 0.5px solid #999; padding-top: 2mm; vertical-align: top; } }
@page :first { @bottom-left { content: none; border: 0; } @bottom-right { content: none; border: 0; } }
html { font-size: 11pt; }
body { margin: 0; color: #111; font-family: "STIX Two Text", Cambria, "Times New Roman", serif; line-height: 1.45;
       hyphens: auto; -webkit-hyphens: auto; text-rendering: optimizeLegibility; }

/* title page */
.front { break-after: page; position: relative; height: 246mm; }
.kicker { font-size: 8.5pt; letter-spacing: .12em; text-transform: uppercase; color: #444; text-align: center; padding-top: 18mm; }
h1.title { font-size: 19pt; font-weight: 600; line-height: 1.25; text-align: center; margin: 12mm 6mm 9mm; }
.authors { text-align: center; font-size: 12pt; line-height: 1.5; }
.authors sup, .aff sup { font-size: 0.7em; padding: 0 0.1em; }
.affs { margin-top: 2.5mm; }
.aff { text-align: center; font-size: 9.5pt; font-style: italic; color: #333; line-height: 1.45; }
.meta { text-align: center; font-size: 10pt; color: #333; margin-top: 5mm; }
.abstract { margin: 16mm 9mm 0; }
.abshead { text-align: center; font-weight: 700; font-size: 10pt; letter-spacing: .08em; text-transform: uppercase; margin-bottom: 2.5mm; }
.abstract p { font-size: 10pt; line-height: 1.45; text-align: justify; text-indent: 0; margin: 0; }
.abstract p.kw { margin-top: 3mm; font-size: 9.5pt; }
.titlenote { position: absolute; bottom: 0; left: 0; right: 0; font-size: 8.5pt; line-height: 1.4; color: #333;
             border-top: 0.6px solid #777; padding-top: 2mm; width: 55%; }

/* body */
p { margin: 0; text-align: justify; text-indent: 1.5em; orphans: 2; widows: 2; }
h2 + p, h3 + p, .tblock + p, figure + p, .eq + p, ul + p, ol + p, .tnote + p { text-indent: 0; }
h2 { font-size: 12.5pt; font-weight: 700; margin: 8mm 0 2.5mm; break-after: avoid; }
h2 .secno { display: inline-block; min-width: 7mm; }
h2.unnumbered { margin-top: 8mm; }
h2.appendix { break-before: page; margin-top: 0; }
h3 { font-size: 11pt; font-weight: 700; font-style: italic; margin: 5mm 0 1.6mm; break-after: avoid; }
h3 .secno { display: inline-block; min-width: 9mm; font-style: normal; }
ul, ol { margin: 1.5mm 0 2.5mm; padding-left: 1.6em; }
li { margin: 0.6mm 0; text-align: justify; }
.eq { display: flex; align-items: center; margin: 3mm 0; break-inside: avoid; }
.eqm { flex: 1 1 auto; min-width: 0; text-align: center; }
.eqm .katex-display { margin: 0; }
.eqno { flex: none; padding-left: 3mm; }
.katex { font-size: 1.0em; }

/* tables: booktabs style */
.tblock { break-inside: avoid; width: 100%; margin: 6mm 0; }
.tblock.long { break-inside: auto; width: 100%; }
table { border-collapse: collapse; width: 100%; margin: 0; font-size: 9pt; break-inside: avoid;
        border-top: 1px solid #111; border-bottom: 1px solid #111; line-height: 1.3; }
caption { caption-side: top; text-align: left; font-size: 10pt; padding-bottom: 2mm; line-height: 1.35; }
caption .tabno { font-weight: 700; }
thead th { border-bottom: 0.6px solid #111; font-weight: 600; padding: 1.4mm 2mm; text-align: left; vertical-align: bottom; }
td { padding: 1mm 2mm; vertical-align: top; font-variant-numeric: tabular-nums; }
tr.panel td { font-style: italic; padding-top: 2mm; border-bottom: 0.4px solid #999; }
.tnote { font-size: 8.8pt; text-indent: 0; margin: 1.6mm 0 0; line-height: 1.35; color: #222; width: 0; min-width: 100%; }
table.trades { font-size: 8pt; break-inside: auto; }
table.trades td { padding: 0.45mm 2mm; }
.usd { font-style: normal; }

/* figures */
figure { margin: 6mm 0; break-inside: avoid; text-align: left; }
figure img { display: block; width: 100%; height: auto; }
figcaption { text-align: justify; font-size: 9.5pt; margin: 2.5mm 0 0; line-height: 1.4; }
figcaption b { font-weight: 700; }

a { color: inherit; text-decoration: none; }
code { font-family: Consolas, monospace; font-size: 0.86em; }
h2.refhead { break-before: page; margin-top: 0; }
p.ref { text-indent: -1.5em; padding-left: 1.5em; font-size: 10pt; text-align: left; margin-bottom: 1.4mm; line-height: 1.35; }
h2.unnumbered + p, h2 + p, h3 + p { text-indent: 0; }
"""


def main(md_path, out_pdf):
    md_path = Path(md_path).resolve()
    md = md_path.read_text(encoding="utf-8")
    md = re.sub(r"\$(?=\d)", "@@USD@@", md)          # currency, not math: "$1" must not open KaTeX
    meta, body_md = R._front_matter(md)
    doc = JDoc(md_path.parent)
    body = doc.convert(body_md)
    for name, n in doc.eq_labels.items():
        body = body.replace(f"(eq:{name})", f"({n})")
    css = CSS.replace("__FOOTER__", meta.get("footer", "").replace('"', "'"))
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(meta.get('title', 'manuscript'))}</title>
<base href="{md_path.parent.resolve().as_uri()}/">
<link rel="stylesheet" href="{R.KATEX}/katex.min.css">
<link href="https://fonts.googleapis.com/css2?family=STIX+Two+Text:ital,wght@0,400;0,600;0,700;1,400;1,700&display=swap" rel="stylesheet">
<style>{css}</style>
<script defer src="{R.KATEX}/katex.min.js"></script>
<script defer src="{R.KATEX}/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body, {{delimiters: [{{left: '$$', right: '$$', display: true}},
  {{left: '$', right: '$', display: false}}], throwOnError: false}});"></script>
</head><body>
{front(meta)}
<main>
{body}
</main>
</body></html>"""
    out_pdf = Path(out_pdf)
    html_path = md_path.with_suffix(".html")
    page = page.replace("@@USD@@", '<span class="usd">$</span>')
    html_path.write_text(page, encoding="utf-8")
    pdf_tmp = md_path.parent / "_render_tmp.pdf"
    R.print_pdf(html_path, pdf_tmp)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    out_pdf.write_bytes(pdf_tmp.read_bytes())
    print(f"{doc.sec[0]} sections, {doc.fig} figures, {doc.tab} tables, {doc.eq} equations -> {out_pdf} ({out_pdf.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
