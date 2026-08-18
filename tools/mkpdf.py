# -*- coding: utf-8 -*-
import io, re, html

SRC = "/home/user/American-Injustice/manuscript-exports/American_Injustice_FULL.md"
OUT = "/home/user/American-Injustice/manuscript-exports/American_Injustice_ebook.pdf"

import os, glob as _glob
COVER = None
for _pat in ("/home/user/American-Injustice/manuscript-exports/cover.*",
             "/home/user/American-Injustice/cover.*",
             "/home/user/American-Injustice/art/cover.*"):
    _hits = [f for f in _glob.glob(_pat)
             if f.rsplit(".", 1)[-1].lower() in ("jpg", "jpeg", "png", "webp", "tif", "tiff")]
    if _hits:
        COVER = sorted(_hits)[0]
        break

import sys; sys.path.insert(0, "/tmp/claude-0/-home-user/bb9b3891-5cc9-5d86-9295-b7ae9ed35788/scratchpad")
from prep import load
md, PART_AT, TITLES, FRONT = load()
def _norm(x):
    return re.sub(r"[^a-z0-9]+", "", x.lower())
FRONT_MAP = {_norm(f): f for f in FRONT}
_ROMAN = re.compile(r"^[IVXLC]+$")
def _prettypart(t):
    out = []
    for w in t.split():
        out.append(w if _ROMAN.match(w.upper()) and w.upper() != "I" or _ROMAN.match(w)
                   else w.title())
    # restore roman numerals exactly as written in the source
    src = t.split()
    for k, w in enumerate(src):
        if _ROMAN.match(w):
            out[k] = w
    return " ".join(out)
lines = md.split("\n")
PART_AT[9999] = "PART VI \u00b7 SYSTEMIC ANALYSIS"

INLINE = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`)", re.S)

def inline(t):
    out = []
    for tok in INLINE.split(t):
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            out.append("<strong>%s</strong>" % html.escape(tok[2:-2]))
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            out.append("<em>%s</em>" % html.escape(tok[1:-1]))
        elif tok.startswith("`") and tok.endswith("`") and len(tok) > 2:
            out.append("<code>%s</code>" % html.escape(tok[1:-1]))
        else:
            out.append(html.escape(tok))
    return "".join(out)

body, toc, i, n = [], [], 0, 0
first_para_pending = False

while i < len(lines):
    ln = lines[i].rstrip()

    # table
    if ln.startswith("|") and i + 1 < len(lines) and set(lines[i+1].replace("|", "").strip()) <= set("-: "):
        hdr = [c.strip() for c in ln.strip("|").split("|")]
        i += 2
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            rows.append([c.strip() for c in lines[i].strip("|").split("|")])
            i += 1
        t = ["<table><thead><tr>"] + ["<th>%s</th>" % inline(h) for h in hdr] + ["</tr></thead><tbody>"]
        for r in rows:
            t.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r[:len(hdr)]) + "</tr>")
        t.append("</tbody></table>")
        body.append("".join(t))
        continue

    if not ln.strip():
        i += 1
        continue

    if ln.startswith("# "):
        title = ln[2:].strip()
        if title.upper().startswith("AMERICAN INJUSTICE"):
            i += 1
            continue                                  # title page is built separately
        plain = re.sub(r"\*", "", title)
        cm = re.match(r"CHAPTER\s+(\d+)", plain, re.I)
        pnum = int(cm.group(1)) if cm else None
        if pnum in PART_AT:
            body.append('<section class="partpage"><p class="pt">%s</p></section>' % html.escape(PART_AT[pnum]))
            toc.append((None, _prettypart(PART_AT[pnum])))
        elif plain.strip().upper().startswith("LEGAL ANALYSIS"):
            body.append('<section class="partpage"><p class="pt">%s</p></section>' % html.escape(PART_AT[9999]))
            toc.append((None, _prettypart(PART_AT[9999])))
        n += 1
        cid = "sec%d" % n
        if pnum and pnum in TITLES:
            label = "%d \u00b7 %s" % (pnum, TITLES[pnum])
        else:
            label = FRONT_MAP.get(_norm(plain), plain.title())
        toc.append((cid, label))
        body.append('<section class="chap"><h1 id="%s">%s</h1>' % (cid, inline(title)))
        first_para_pending = True
    elif ln.startswith("## "):
        body.append("<h2>%s</h2>" % inline(ln[3:].strip()))
        first_para_pending = True
    elif ln.startswith("### "):
        body.append("<h3>%s</h3>" % inline(ln[4:].strip()))
        first_para_pending = True
    elif ln.strip() in ("---", "***", "___"):
        body.append('<p class="orn">⁂</p>')
        first_para_pending = True
    elif ln.startswith("> "):
        body.append("<blockquote>%s</blockquote>" % inline(ln[2:]))
    elif re.match(r"^[-*] ", ln):
        items = []
        while i < len(lines) and re.match(r"^[-*] ", lines[i].rstrip()):
            items.append("<li>%s</li>" % inline(re.sub(r"^[-*] ", "", lines[i].rstrip())))
            i += 1
        body.append("<ul>%s</ul>" % "".join(items))
        continue
    elif re.match(r"^\d+\. ", ln):
        items = []
        while i < len(lines) and re.match(r"^\d+\. ", lines[i].rstrip()):
            items.append("<li>%s</li>" % inline(re.sub(r"^\d+\. ", "", lines[i].rstrip())))
            i += 1
        body.append("<ol>%s</ol>" % "".join(items))
        continue
    else:
        cls = ""
        if first_para_pending:
            cls = ' class="first"'
            first_para_pending = False
        if ln.startswith("*") and ln.endswith("*") and not ln.startswith("**"):
            cls = ' class="note"'
        body.append("<p%s>%s</p>" % (cls, inline(ln)))
    i += 1

# close sections
htmlbody = "".join(body).replace('<section class="chap">', '</section><section class="chap">', 100000)
if htmlbody.startswith("</section>"):
    htmlbody = htmlbody[len("</section>"):]
htmlbody += "</section>"
htmlbody = htmlbody.replace('<section class="chap">', '<section class="chap bodystart">', 1)

toc_html = "".join(
    ('<p class="toc-part">%s</p>' % html.escape(t)) if cid is None else
    ('<p class="toc-line"><a href="#%s"><span class="t">%s</span></a></p>' % (cid, html.escape(t)))
    for cid, t in toc)

CSS = u"""
@page { size: 6in 9in; margin: 0.78in 0.57in 0.88in;
        @bottom-center { content: counter(page); font-family: "DejaVu Serif",serif;
                         font-size: 9pt; color:#444; }
        @top-center { content: string(runhead); font-family: "DejaVu Serif",serif;
                      font-size: 8pt; letter-spacing:.06em; color:#666; text-transform: uppercase; } }
@page :first { @bottom-center { content: none } @top-center { content: none } }
@page frontmatter { @top-center { content: none } }
@page cover { size: 6in 9in; margin: 0;
              @bottom-center { content: none } @top-center { content: none } }
.cover { page: cover; break-after: page; margin:0; padding:0; }
.cover img { display:block; width: 6in; height: 9in; object-fit: cover; }
@page nofolio { @bottom-center { content: none } @top-center { content: none } }
@page chapopen { @top-center { content: none } }
html { font-family: "DejaVu Serif","Liberation Serif",Charter,Georgia,serif;
       font-size: 12.5pt; line-height: 1.56; hyphens: auto;
       hyphenate-limit-chars: 10 5 4; hyphenate-limit-zone: 9%; }
body { margin:0; text-align: left; color:#111; }
.front { page: frontmatter; }
h1 { string-set: runhead content(text); font-size: 18pt; line-height:1.2; font-weight:600;
     margin: 0 0 1.6em; text-align:left; page: chapopen; break-after: avoid;
     letter-spacing:.01em; }
section.chap { break-before: page; }

section.chap > h1:first-child { padding-top: 1.1in; }
h2 { font-size: 13.5pt; font-weight:700; margin:1.7em 0 .5em; text-align:left; break-after: avoid; }
h3 { font-size: 13pt; font-weight:700; font-style:italic; margin:1.3em 0 .4em; text-align:left; break-after: avoid; }
p { margin:0 0 .95em; text-indent: 0; orphans:2; widows:2; }
p.first, p.note, p.orn, blockquote p { text-indent: 0; }
li { text-align: left; }
p.note { font-style: italic; color:#333; margin: 0 0 1em; }
p.orn { text-align:center; margin:1.1em 0; color:#888; text-indent:0; letter-spacing:.3em; }
blockquote { margin:.8em 1.3em; font-style:italic; }
ul,ol { margin:.6em 0 .8em 1.3em; padding:0; }
li { margin-bottom:.45em; text-align:left; }
code { font-family:"DejaVu Sans Mono",monospace; font-size:.86em; }
table { width:100%; border-collapse:collapse; margin:1em 0; font-size:10pt; break-inside:avoid; }
th,td { border:0.5pt solid #bbb; padding:4pt 5pt; text-align:left; vertical-align:top; hyphens:auto; }
th { background:#f0efec; font-weight:700; }
.titlepage { page:nofolio; text-align:center; break-after:page; hyphens:none; }
.titlepage .t { font-size:26pt; hyphens:none; white-space:nowrap; letter-spacing:.05em; margin-top:2.6in; font-weight:600; display:block; }
.titlepage .rule { width:34%; margin:.55in auto; border-bottom:0.8pt solid #333; }
.titlepage .a { font-size:13pt; letter-spacing:.16em; text-transform:uppercase; display:block; }
.copy { page:nofolio; break-after:page; font-size:9.5pt; color:#333; text-align:left;
        padding-top:2.55in; }
.copy p { text-indent:0; margin-bottom:.5em; }
.toc { page:frontmatter; break-after:page; }
.toc h1 { column-span:all; font-size:14pt; padding-top:.25in; margin-bottom:1.1em; text-align:center;
          string-set:none; page:frontmatter; break-before:auto; break-after:avoid; }
p.toc-line { text-indent:0; margin:.34em 0; text-align:left; }
p.toc-line a { text-decoration:none; color:#111; }
p.toc-part { text-indent:0; margin:.75em 0 .3em; font-size:7.6pt; font-style:italic;
             font-weight:400; letter-spacing:0; text-transform:none; color:#333;
             break-after:avoid; border-bottom:0.4pt solid #ddd; padding-bottom:.2em; }
p.toc-part:first-of-type { margin-top:.15em }
section.partpage { break-before:page; page:nofolio; text-align:center; }
section.partpage .pt { text-indent:0; padding-top:3.5in; font-size:15pt; font-weight:600;
                       letter-spacing:.12em; hyphens:none; }
.ded { page:nofolio; break-after:page; text-align:center; hyphens:none; }
.ded p { text-indent:0; margin:0 0 1.15em; font-size:12pt; line-height:1.5; }
.ded .top { padding-top:2.9in; }
.ded .sig { font-variant:small-caps; letter-spacing:.09em; margin-top:1.5em; }
.toc { font-size:8.0pt; line-height:1.38; column-count:2; column-gap:1.55em;
        column-rule:0.4pt solid #d8d8d8; }
p.toc-line { hyphens:none; margin:.2em 0; break-inside:avoid; padding-left:1.1em;
             text-indent:-1.1em; }
p.toc-line a::after { content: " " leader('.') "  " target-counter(attr(href), page);
                      color:#666; }
"""

DOC = u"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>American Injustice</title><style>%s</style></head><body>
%s<div class="titlepage"><span class="t">AMERICAN INJUSTICE</span>
<div class="rule"></div><span class="a">Don Matthews</span></div>
<div class="copy"><p>Copyright &copy; Matthew Oliver Reardon, writing as Don Matthews.</p>
<p>All rights reserved.</p>
<p>This is a work of nonfiction. Every factual claim is sourced to a primary document, a certified transcript, or a recording, and claims resting only on the author's account are identified as such in the text. Minors are not named. Certain individuals are described but not identified.</p>
<p>Discussion of testimony given in a sealed hearing in the author's federal criminal case is omitted in compliance with a court order. Where that dispute is described, it is described only from the public docket.</p>
<p>Nothing in this book is legal advice.</p></div>
<div class="ded">
<p class="top">For Lydia-Elise, Anna-Claire, McKenna-Rose,<br>Ethan-Oliver, and Meri-Emmelyn &mdash;<br>who never deserved any of this.</p>
<p>For Andy Arant &mdash;<br>attorney, friend, and mentor,<br>lost to cancer.</p>
<p>And for Bradley Foust,<br>where it all started.</p>
<p class="sig">Rest in peace. Semper Fi.</p></div>
<div class="toc"><h1>Contents</h1>%s</div>
%s</body></html>""" % (CSS,
        ('<div class="cover"><img src="file://%s" alt=""></div>' % COVER) if COVER else "",
        toc_html, htmlbody)

io.open("/tmp/claude-0/-home-user/bb9b3891-5cc9-5d86-9295-b7ae9ed35788/scratchpad/book.html", "w", encoding="utf-8").write(DOC)

from weasyprint import HTML
HTML(string=DOC, base_url="/home/user/American-Injustice/").write_pdf(OUT)
import os
print("wrote %s  (%.1f MB)  |  %d TOC entries" % (OUT, os.path.getsize(OUT)/1e6, len(toc)))
