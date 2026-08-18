# -*- coding: utf-8 -*-
import io, re, html

SRC = "/home/user/American-Injustice/manuscript-exports/American_Injustice_FULL.md"
OUT = "/home/user/American-Injustice/manuscript-exports/American_Injustice_ebook.pdf"

import sys; sys.path.insert(0, "/tmp/claude-0/-home-user/bb9b3891-5cc9-5d86-9295-b7ae9ed35788/scratchpad")
from prep import load
md, PART_AT = load()
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
            toc.append((None, PART_AT[pnum]))
        elif plain.strip().upper().startswith("LEGAL ANALYSIS"):
            body.append('<section class="partpage"><p class="pt">%s</p></section>' % html.escape(PART_AT[9999]))
            toc.append((None, PART_AT[9999]))
        n += 1
        cid = "sec%d" % n
        label = re.sub(r'^CHAPTER\s+', '', plain)
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
@page { size: 6in 9in; margin: 0.8in 0.72in 0.9in;
        @bottom-center { content: counter(page); font-family: Charter,"Bitstream Charter",serif;
                         font-size: 9.5pt; color:#444; }
        @top-center { content: string(runhead); font-family: Charter,"Bitstream Charter",serif;
                      font-size: 8.5pt; letter-spacing:.06em; color:#666; text-transform: uppercase; } }
@page :first { @bottom-center { content: none } @top-center { content: none } }
@page frontmatter { @top-center { content: none } }
@page nofolio { @bottom-center { content: none } @top-center { content: none } }
@page chapopen { @top-center { content: none } }
html { font-family: Charter,"Bitstream Charter","Liberation Serif",Georgia,serif;
       font-size: 12pt; line-height: 1.42; hyphens: auto; }
body { margin:0; text-align: justify; color:#111; }
.front { page: frontmatter; }
h1 { string-set: runhead content(text); font-size: 17pt; line-height:1.2; font-weight:600;
     margin: 0 0 1.6em; text-align:left; page: chapopen; break-after: avoid;
     letter-spacing:.01em; }
section.chap { break-before: page; }

section.chap > h1:first-child { padding-top: 1.1in; }
h2 { font-size: 12.5pt; font-weight:700; margin:1.7em 0 .5em; text-align:left; break-after: avoid; }
h3 { font-size: 12pt; font-weight:700; font-style:italic; margin:1.3em 0 .4em; text-align:left; break-after: avoid; }
p { margin:0; text-indent: 1.15em; orphans:2; widows:2; }
p.first, p.note, p.orn, blockquote p { text-indent: 0; }
p.note { font-style: italic; color:#333; margin: 0 0 1em; }
p.orn { text-align:center; margin:1.1em 0; color:#888; text-indent:0; letter-spacing:.3em; }
blockquote { margin:.8em 1.3em; font-style:italic; }
ul,ol { margin:.6em 0 .8em 1.3em; padding:0; }
li { margin-bottom:.35em; text-align:justify; }
code { font-family:"DejaVu Sans Mono",monospace; font-size:.86em; }
table { width:100%; border-collapse:collapse; margin:1em 0; font-size:9.5pt; break-inside:avoid; }
th,td { border:0.5pt solid #bbb; padding:4pt 5pt; text-align:left; vertical-align:top; hyphens:auto; }
th { background:#f0efec; font-weight:700; }
.titlepage { page:nofolio; text-align:center; break-after:page; hyphens:none; }
.titlepage .t { font-size:26pt; hyphens:none; white-space:nowrap; letter-spacing:.05em; margin-top:2.6in; font-weight:600; display:block; }
.titlepage .rule { width:34%; margin:.55in auto; border-bottom:0.8pt solid #333; }
.titlepage .a { font-size:13pt; letter-spacing:.16em; text-transform:uppercase; display:block; }
.copy { page:nofolio; break-after:page; font-size:9.5pt; color:#333; text-align:left; padding-top:4.6in; }
.copy p { text-indent:0; margin-bottom:.5em; }
.toc { page:frontmatter; break-after:page; }
.toc h1 { column-span:all; font-size:14pt; padding-top:.25in; margin-bottom:1.1em; text-align:center;
          string-set:none; page:frontmatter; break-before:auto; break-after:avoid; }
p.toc-line { text-indent:0; margin:.34em 0; text-align:left; }
p.toc-line a { text-decoration:none; color:#111; }
p.toc-part { text-indent:0; margin:.8em 0 .25em; font-size:6.9pt; font-weight:700;
             letter-spacing:.13em; text-transform:uppercase; color:#555; break-after:avoid; }
p.toc-part:first-of-type { margin-top:0 }
section.partpage { break-before:page; page:nofolio; text-align:center; }
section.partpage .pt { text-indent:0; padding-top:3.5in; font-size:15pt; font-weight:600;
                       letter-spacing:.12em; hyphens:none; }
.toc { font-size:8.4pt; line-height:1.27; column-count:2; column-gap:1.7em;
        column-rule:0.4pt solid #ccc; }
p.toc-line { hyphens:none; margin:.13em 0; break-inside:avoid; }
p.toc-line a::after { content: leader('.') " " target-counter(attr(href), page); color:#555; }
"""

DOC = u"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>American Injustice</title><style>%s</style></head><body>
<div class="titlepage"><span class="t">AMERICAN INJUSTICE</span>
<div class="rule"></div><span class="a">Don Matthews</span></div>
<div class="copy"><p>Copyright &copy; Matthew Oliver Reardon, writing as Don Matthews.</p>
<p>All rights reserved.</p>
<p>This is a work of nonfiction. Every factual claim is sourced to a primary document, a certified transcript, or a recording, and claims resting only on the author's account are identified as such in the text. Minors are not named. Certain individuals are described but not identified.</p>
<p>Discussion of testimony given in a sealed hearing in the author's federal criminal case is omitted in compliance with a court order. Where that dispute is described, it is described only from the public docket.</p>
<p>Nothing in this book is legal advice.</p></div>
<div class="toc"><h1>Contents</h1>%s</div>
%s</body></html>""" % (CSS, toc_html, htmlbody)

io.open("/tmp/claude-0/-home-user/bb9b3891-5cc9-5d86-9295-b7ae9ed35788/scratchpad/book.html", "w", encoding="utf-8").write(DOC)

from weasyprint import HTML
HTML(string=DOC, base_url="/home/user/American-Injustice/").write_pdf(OUT)
import os
print("wrote %s  (%.1f MB)  |  %d TOC entries" % (OUT, os.path.getsize(OUT)/1e6, len(toc)))
