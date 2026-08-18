# -*- coding: utf-8 -*-
import csv, io, re, os, collections

LED = '/home/user/americaninjustice/02_analysis/evidence_ledger/EVIDENCE_LEDGER.csv'
rows = list(csv.reader(io.open(LED, encoding='utf-8', newline='')))[1:]

BLOCK_IDS = {"P0726"}
SEALED = re.compile(r"seal(ed)?\b|6:25-cr-00227|surveillance footage|Farrish|gag order", re.I)
MINOR_MED = re.compile(r"ventilator|premature|C-section|Bipolar|Abilify|pregnan", re.I)

def keep(r):
    if r[0] in BLOCK_IDS or r[9].strip(): return False
    t = r[5].upper()
    if "RUMOR" in t or "MISFILED" in t or t.strip().startswith("N/A"): return False
    if not ("CONFIRMED" in t or "CORROBORATED" in t): return False
    if not r[7].strip() or r[7].strip().upper().startswith("N/A"): return False
    blob = " ".join(r)
    if SEALED.search(blob) or MINOR_MED.search(blob): return False
    META = re.compile(r"the manuscript|this book|this project|the ledger|currently printed|"
                      r"already logged|this row|earlier draft|acquisition target|"
                      r"source of the .{0,30}claim is located|the project|nearly left it|"
                      r"belong in the book|open ask|standing ask|the book should|"
                      r"drafting|this batch|in this archive|here the whole time|was already|flagged at p0", re.I)
    if META.search(r[4]): return False
    return len(claim(r)) >= 34

ACRONYMS = {"FBI","DUI","DWI","ADA","MBI","DOJ","OIG","BOLO","USMS","FOIA","CSU","OPC","AOT",
            "NCIC","EGA","GSA","MS","TX","UT","LA","US","USA","AUSA","DPS","PCR","R&R","CFR",
            "AR-15","ID","TV","PDF","ASR","IV","VI","II","III"}
EMOJI = re.compile(u"[\u2190-\u2BFF\u2600-\u27BF\uFE0F\u2b06\u26a0]+")
SCRUB = [
    (re.compile(r"\(file [A-Za-z0-9_-]{20,}\)"), ""),                 # drive file ids
    (re.compile(r"\b[A-Za-z0-9_-]{28,}\b"), "[file id]"),
    (re.compile(r"\b\d{1,5}\s+(?:CR|County Road|[NSEW]\.?\s)?[A-Za-z0-9 .]{0,24}?,?\s*"
                r"(?:Oxford|Bruce|Olive Branch|Galveston|Lafayette)\s*,?\s*[A-Z]{2}\s*\d{5}"),
     "[address withheld]"),
    (re.compile(r"\bGoogle Drive\s*>\s*[^,;]+"), "author's document archive"),
]
def strip_md(x):
    x = EMOJI.sub("", x.replace("**", "").replace("*", ""))
    for pat, rep in SCRUB:
        x = pat.sub(rep, x)
    return re.sub(r"\s+", " ", x).replace("|", "/").strip()

def sentence_case(s):
    """Ledger headlines are written in shouting caps as working notes; soften for print."""
    letters = [c for c in s if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) > 0.7:
        out, prev_end = [], True
        for w in s.split():
            core = w.strip("\u2018\u2019'\".,:;()")
            if core in ACRONYMS:
                out.append(w)
            elif prev_end:
                out.append(w.capitalize())
            else:
                out.append(w.lower())
            prev_end = w.endswith((".", ":", "?", "!"))
        s = " ".join(out)
        for nm in ("reardon", "east", "alcorn", "beavers", "kilpatrick", "tollison", "busby",
                   "luther", "smith", "crowder", "communicare", "lafayette", "mississippi",
                   "oxford", "galveston", "osteen", "foust", "arant", "little", "nugent"):
            s = re.sub(r"\b%s\b" % nm, nm.capitalize(), s)
        s = re.sub(r"\bi\b", "I", s)
    return s

def claim(r):
    f = r[4]
    m = re.match(r"^\*\*(.{12,150}?[.:—])\*\*", f)          # leading bold headline
    s = m.group(1) if m else re.split(r"(?<=[a-z\)\"][.!?])\s(?=[A-Z])", strip_md(f))[0]
    s = sentence_case(strip_md(s)).rstrip(" .:\u2014")
    if len(s) > 155: s = s[:152].rsplit(" ", 1)[0] + "…"
    return s

def source(r):
    s = strip_md(r[1])
    s = re.sub(r"^(americaninjustice|American-Injustice) repo:\s*", "", s)
    s = re.sub(r"^(00_source_materials/)?legal_documents/by_date/\d{4}/", "", s)
    s = re.sub(r"^(cleaned_for_book|01_processed|02_analysis|Police Reports)[/:]\s*", "", s)
    s = s.strip("'\u2018\u2019\" ")
    # "2017-05-26 - Petition For Citation Of Contempt" -> "Petition for Citation of Contempt, 26 May 2017"
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})\s*-\s*(.+?)(\.pdf|\.txt|\.srt)?$", s, re.I)
    if m:
        import datetime
        try:
            d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            when = d.strftime("%-d %B %Y")
        except ValueError:
            when = m.group(1)
        title = re.sub(r"\s+", " ", m.group(4)).strip()
        small = {"of","for","the","and","to","in","on","a","an","v","vs","by","from","with"}
        title = " ".join(w.lower() if (w.lower() in small and i) else
                         (w if w.isupper() and len(w) <= 5 else w.capitalize())
                         for i, w in enumerate(title.split()))
        s = "%s, %s" % (title, when)
    s = re.sub(r"\.(pdf|txt|srt|vtt|md|json)\b", "", s, flags=re.I)
    s = re.sub(r"\s*[-\u2014]{1,2}\s*(direct read|read directly|retrieved and read|"
               r"ASR transcript|rough-cut transcript).*$", "", s, flags=re.I)
    s = s.split(" (approx")[0].split(", pp.")[0].split(", p.")[0]
    if len(s) > 92: s = s[:89].rsplit(" ", 1)[0] + "\u2026"
    return s.strip(" ,;\u2014-")

def tier(r):
    t = strip_md(r[5]).upper()
    if "CONFIRMED" in t and "CORROBORATED" in t: lab = "CONFIRMED"
    elif "CONFIRMED" in t: lab = "CONFIRMED"
    else: lab = "CORROBORATED"
    par = re.search(r"\(([^)]{3,44})\)", strip_md(r[5]))
    return lab + (" — %s" % par.group(1).lower() if par else "")

def year(r):
    m = re.search(r"(19|20)\d{2}", r[2])
    return m.group(0) if m else "undated"

sel = [r for r in rows if keep(r)]
by = collections.OrderedDict()
for r in sorted(sel, key=lambda r: (year(r), r[2], r[0])):
    by.setdefault(year(r), []).append(r)

out = [u"""
---

## J. EVIDENCE INDEX

*Every claim below is drawn from a working evidence ledger of 801 entries maintained alongside this
book, in which each fact is tied to the document, transcript, or recording it came from and assigned
a confidence tier. Reproduced here are the **%d entries rated CONFIRMED or CORROBORATED** — meaning a
primary document, a certified transcript, or a recording supports them.*

*Entries resting only on my own account are excluded, and so is anything touching the sealed federal
proceeding, minors' medical information, or allegations I have withdrawn. Those exclusions are not
cosmetic: **%d entries were removed by that filter**, and section F lists what this book does not have.*

*Grouped by the year of the underlying event. The reference number is the ledger row, so any entry
here can be traced back to its full working note.*
""" % (len(sel), len(rows) - len(sel))]

for y, items in by.items():
    out.append(u"\n### %s\n" % y)
    for r in items:
        out.append(u"**%s** \u2014 %s. *%s* \u2014 %s\n" % (r[0], claim(r), source(r), tier(r)))

txt = u"\n".join(out) + u"\n"
io.open('/tmp/claude-0/-home-user/bb9b3891-5cc9-5d86-9295-b7ae9ed35788/scratchpad/index.md', 'w', encoding='utf-8').write(txt)
print("entries: %d | years: %d | words: %d" % (len(sel), len(by), len(txt.split())))
print("\n".join(txt.split("\n")[14:20]))
