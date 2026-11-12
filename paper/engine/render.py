"""Paper renderer: Markdown (+ front matter) -> HTML (serif, LaTeX-like, KaTeX) -> PDF via headless Edge.

Library API:  render(md_text, base_dir, out_pdf, generators=None, html_only=False) -> (html_path, pdf_path)
CLI:          python src/paper/build.py <paper.md> --out <pdf>          (see src/paper/README.md)

Markdown subset (also used by lanes' PAPER_SECTION.md):
  front matter between --- lines: title, subtitle, lab, date, period (or byline), id, slug (all optional)
  # Title   ## Section (auto-numbered; "Abstract"/"References" unnumbered; "Appendix ..." starts a new page)
  ### Subsection   paragraphs   - / 1. lists   **bold**  *italic*  `code`  [text](url)
  | pipe | table |  then a line "Table: caption"         ![caption](figures/x.png) -> numbered figure
  $inline$  and  $$display$$ ; "$$ ... $$ (eq:name)" numbers the equation; "(eq:name)" in text -> "(n)"
  [@R22] or [@R22, @R99]  cite entries of research/papers/REFERENCES.md, renumbered [1], [2]... in order of use
  {{references}}          the cited entries, in citation order
  {{csv:path.csv | caption}}   a CSV as a numbered table (path relative to the paper)
  {{trades:trades.csv}}        every row of a trades file as a compact appendix table
  {{generated:name}}           a block produced by a Python callable passed in `generators`
  ::subtitle text   ::byline text   (same as the front-matter fields)
  [TBD ...] paragraphs are printed in red italics so unfinished parts stay visible
"""
import html
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REFERENCES = HERE / "REFERENCES.md"
KATEX = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist"
EDGE = [Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")]


def _inline(text):
    parts = re.split(r"(\$\$.+?\$\$|\$[^$\n]+?\$)", text)       # leave math untouched for KaTeX
    out = []
    for p in parts:
        if p.startswith("$"):
            out.append(html.escape(p, quote=False))
            continue
        p = html.escape(p, quote=False)
        p = re.sub(r"`([^`]+)`", r"<code>\1</code>", p)
        p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p)
        p = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", p)
        p = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', p)
        out.append(p)
    return "".join(out)


def _front_matter(md):
    meta = {}
    if md.startswith("---"):
        end = md.find("\n---", 3)
        if end > 0:
            for line in md[3:end].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip().strip('"')
            md = md[end + 4:]
    return meta, md


def _master_refs():
    refs = {}
    if REFERENCES.exists():
        for line in REFERENCES.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\|\s*\[(\d+)\]\s*\|\s*(.+?)\s*\|[^|]*\|\s*$", line)
            if m:
                refs[int(m.group(1))] = m.group(2)
    return refs


class Doc:
    def __init__(self, base_dir, generators=None):
        self.base = Path(base_dir)
        self.gen = generators or {}
        self.sec = [0, 0]
        self.fig = self.tab = self.eq = 0
        self.appendix = False
        self.eq_labels = {}
        self.cited = []                                           # master reference numbers in citation order

    # ---- citations
    def cite(self, md):
        def repl(m):
            local = []
            for key in re.findall(r"@R(\d+)", m.group(0)):
                k = int(key)
                if k not in self.cited:
                    self.cited.append(k)
                local.append(self.cited.index(k) + 1)
            return "[" + ", ".join(str(x) for x in sorted(local)) + "]"
        return re.sub(r"\[@R\d+(?:\s*[,;]\s*@R\d+)*\]", repl, md)

    def references(self):
        master = _master_refs()
        lines = [f"[{i + 1}] {master.get(k, f'[missing reference R{k} in paper_engine/REFERENCES.md]')}"
                 for i, k in enumerate(self.cited)]
        return "\n\n".join(lines) if lines else "[TBD: no [@Rn] citations yet]"

    # ---- blocks
    def convert(self, md):
        lines, out, i = md.splitlines(), [], 0
        while i < len(lines):
            ln = lines[i].rstrip()
            if not ln.strip():
                i += 1
                continue
            if ln.startswith("$$"):
                block = ln
                while block.count("$$") < 2 and i + 1 < len(lines):
                    i += 1
                    block += "\n" + lines[i].rstrip()
                m = re.search(r"\(eq:([\w-]+)\)\s*$", block)
                tex = block[block.index("$$") + 2: block.rindex("$$")].strip()
                num = ""
                if m:
                    self.eq += 1
                    self.eq_labels[m.group(1)] = self.eq
                    num = f'<span class="eqno">({self.eq})</span>'
                out.append(f'<div class="eq">{html.escape("$$" + tex + "$$", quote=False)}{num}</div>')
                i += 1
                continue
            if ln.startswith("#"):
                out.append(self._heading(ln))
                i += 1
                continue
            if ln.startswith("::: "):                       # framed block: "::: box Title" ... ":::"
                title = ln[4:].strip()
                title = title[4:].strip() if title.lower().startswith("box") else title
                inner = []
                i += 1
                while i < len(lines) and lines[i].strip() != ":::":
                    inner.append(lines[i])
                    i += 1
                i += 1
                head = f'<div class="boxtitle">{_inline(title)}</div>' if title else ""
                out.append(f'<div class="box">{head}{self.convert(chr(10).join(inner))}</div>')
                continue
            if ln.startswith("::subtitle ") or ln.startswith("::byline "):
                kind, text = ln[2:].split(" ", 1)
                out.append(f'<p class="{kind}">{_inline(text)}</p>')
                i += 1
                continue
            if ln.startswith("{{") and ln.rstrip().endswith("}}"):
                out.append(self._directive(ln.strip()[2:-2].strip()))
                i += 1
                continue
            if ln.startswith("!["):
                m = re.match(r"!\[(.*)\]\((.+)\)", ln)
                self.fig += 1
                out.append(f'<figure><img src="{m.group(2)}"><figcaption><b>Figure {self.fig}:</b> '
                           f"{_inline(m.group(1))}</figcaption></figure>")
                i += 1
                continue
            if ln.startswith("|"):
                rows = []
                while i < len(lines) and lines[i].startswith("|"):
                    rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                    i += 1
                j = i
                while j < len(lines) and not lines[j].strip():
                    j += 1
                caption = ""
                if j < len(lines) and lines[j].startswith("Table:"):
                    caption, i = lines[j][6:].strip(), j + 1
                out.append(self._table(rows[0], [r for r in rows[1:] if not all(set(c) <= set(":- ") for c in r)],
                                       caption))
                continue
            if re.match(r"^\s*([-*]|\d+\.)\s", ln):
                ordered = bool(re.match(r"^\s*\d+\.", ln))
                items = []
                while i < len(lines) and (re.match(r"^\s*([-*]|\d+\.)\s", lines[i]) or
                                          (items and re.match(r"^\s{2,}\S", lines[i]))):
                    s = lines[i]
                    if re.match(r"^\s{0,3}([-*]|\d+\.)\s", s):
                        items.append(re.sub(r"^\s*([-*]|\d+\.)\s", "", s))
                    else:
                        items[-1] += " " + s.strip()
                    i += 1
                tag = "ol" if ordered else "ul"
                out.append(f"<{tag}>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + f"</{tag}>")
                continue
            para = [ln]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(
                    r"^(#|\||!\[|\$\$|\s*[-*]\s|\s*\d+\.\s|\{\{|::)", lines[i]):
                para.append(lines[i].strip())
                i += 1
            cls = ' class="todo"' if para[0].startswith("[TBD") else ""
            out.append(f"<p{cls}>{_inline(' '.join(para))}</p>")
        return "\n".join(out)

    def _heading(self, ln):
        level = len(ln) - len(ln.lstrip("#"))
        title = ln.lstrip("#").strip()
        if level == 1:
            return f"<h1>{_inline(title)}</h1>"
        if level == 2:
            if title.lower().startswith("appendix"):
                self.appendix = True
                return f'<h2 class="appendix">{_inline(title)}</h2>'
            if title.lower() in ("abstract", "references"):
                return f'<h2 class="unnumbered">{_inline(title)}</h2>'
            self.sec = [self.sec[0] + 1, 0]
            return f'<h2><span class="secno">{self.sec[0]}</span>{_inline(title)}</h2>'
        self.sec[1] += 1
        no = "" if self.appendix else f'<span class="secno">{self.sec[0]}.{self.sec[1]}</span>'
        return f"<h3>{no}{_inline(title)}</h3>"

    def _directive(self, d):
        kind, _, arg = d.partition(":")
        kind = kind.strip()
        if kind == "flow":                                  # {{flow: Title | text ;; Title | text ;; ...}}
            steps = [s.strip() for s in arg.split(";;") if s.strip()]
            cells = []
            for k, s in enumerate(steps, 1):
                t, _, txt = s.partition("|")
                cells.append(f'<div class="step"><div class="stepno">{k}</div><div class="steptitle">{_inline(t.strip())}'
                             f'</div><div class="steptext">{_inline(txt.strip())}</div></div>')
            return '<div class="flow">' + '<div class="arrow">&#8594;</div>'.join(cells) + "</div>"
        if kind == "references":
            return "\n".join(f'<p class="ref">{_inline(r)}</p>' for r in self.references().split("\n\n"))
        if kind == "generated":
            name = arg.strip()
            return self.convert(self.cite(self.gen[name]())) if name in self.gen else \
                f"<p class='todo'>[missing generated block {html.escape(name)}]</p>"
        if kind in ("csv", "trades"):
            path, _, caption = arg.partition("|")
            p = (self.base / path.strip()).resolve()
            if not p.exists():
                return f"<p class='todo'>[missing file {html.escape(path.strip())}]</p>"
            df = pd.read_csv(p, dtype=str, keep_default_na=False)
            return self._table(list(df.columns), df.values.tolist(), caption.strip(),
                               css="trades" if kind == "trades" else "")
        return f"<p class='todo'>[unknown directive {html.escape(d)}]</p>"

    def _table(self, head, body, caption, css=""):
        num = lambda c: re.fullmatch(r"[−+\-]?[\d.,]+%?×?|[−+\-]?\d[\d.,]*\s*(bp|x)?", str(c).replace("**", "")) is not None  # noqa: E731
        h = "".join(f'<th class="{"num" if body and all(num(r[k]) for r in body if k < len(r) and r[k]) else ""}">'
                    f"{_inline(c)}</th>" for k, c in enumerate(head))
        b = "".join("<tr>" + "".join(f'<td class="{"num" if num(c) else ""}">{_inline(str(c))}</td>' for c in r)
                    + "</tr>" for r in body)
        cap = ""
        if caption:
            self.tab += 1
            cap = f"<caption><b>Table {self.tab}:</b> {_inline(caption)}</caption>"
        cls = f' class="{css}"' if css else ""
        return f"<table{cls}>{cap}<thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


def to_html(md, base_dir, generators=None, title=None):
    meta, body_md = _front_matter(md)
    doc = Doc(base_dir, generators)
    head = []
    if meta.get("title"):
        head.append(f"# {meta['title']}")
    if not meta.get("byline"):
        parts = [meta.get(k) for k in ("lab", "date", "period") if meta.get(k)]
        if parts:
            meta["byline"] = " · ".join(parts)
    for k in ("subtitle", "byline"):
        if meta.get(k):
            head.append(f"::{k} {meta[k]}")
    full = "\n\n".join(head + [body_md])
    body = doc.convert(doc.cite(full))
    for name, n in doc.eq_labels.items():
        body = body.replace(f"(eq:{name})", f"({n})")
    css = (HERE / "paper.css").read_text(encoding="utf-8")
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(title or meta.get('title', 'paper'))}</title>
<base href="{Path(base_dir).resolve().as_uri()}/">
<link rel="stylesheet" href="{KATEX}/katex.min.css">
<style>{css}</style>
<script defer src="{KATEX}/katex.min.js"></script>
<script defer src="{KATEX}/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body, {{delimiters: [{{left: '$$', right: '$$', display: true}},
  {{left: '$', right: '$', display: false}}], throwOnError: false}});"></script>
</head><body><main>
{body}
</main></body></html>"""
    return page, meta, doc


def print_pdf(html_path, pdf_path, timeout=180):
    edge = next((p for p in EDGE if p.exists()), None)
    if edge is None:
        raise RuntimeError("msedge not found")
    profile = tempfile.mkdtemp(prefix="paper_edge_")              # own profile: never attach to the user's Edge
    pdf_path = Path(pdf_path)
    if pdf_path.exists():
        pdf_path.unlink()
    cmd = [str(edge), "--headless", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf-no-header",
           f"--user-data-dir={profile}", "--no-first-run", "--disable-extensions", "--virtual-time-budget=20000",
           "--run-all-compositor-stages-before-draw", f"--print-to-pdf={pdf_path}", Path(html_path).resolve().as_uri()]
    res = subprocess.run(cmd, timeout=timeout, capture_output=True, text=True)
    t0, last = time.time(), -1                                   # msedge.exe can return before its child writes
    while time.time() - t0 < timeout:
        size = pdf_path.stat().st_size if pdf_path.exists() else -1
        if size > 0 and size == last:
            return pdf_path
        last = size
        time.sleep(1.0)
    raise RuntimeError(f"Edge produced no PDF (exit {res.returncode}): {res.stderr[-600:]}")


def render(md, base_dir, out_pdf, generators=None, html_only=False):
    """Render Markdown text to <out_pdf> (the HTML is written next to it as <stem>.html)."""
    page, meta, doc = to_html(md, base_dir, generators)
    out_pdf = Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    html_path = out_pdf.with_suffix(".html")
    html_path.write_text(page, encoding="utf-8")
    pdf = None if html_only else print_pdf(html_path, out_pdf)
    print(f"{html_path.name}: {doc.sec[0]} sections, {doc.fig} figures, {doc.tab} tables, {doc.eq} equations, "
          f"{len(doc.cited)} references" + (f" -> {pdf} ({pdf.stat().st_size / 1e3:.0f} kB)" if pdf else ""))
    return html_path, pdf


if __name__ == "__main__":
    sys.exit("use src/paper/build.py")
