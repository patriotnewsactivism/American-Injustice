# -*- coding: utf-8 -*-
import io, re, collections
F="/home/user/American-Injustice/manuscript-exports/American_Injustice_FULL.md"
t=io.open(F,encoding="utf-8").read()
t=t[:t.index("# LEGAL ANALYSIS")]

parts=re.split(r"\n(?=# )", t)
chaps=[p for p in parts if re.match(r"# (CHAPTER|PROLOGUE|EPILOGUE)", p)]

TAG   = re.compile(r"\[(CONFIRMED|RECORDED|SELF-REPORTED|UNRESOLVED|CLAIM|ASR)[^\]]*\]", re.I)
ALLEG = re.compile(r"\b(lied|lying|perjur\w*|corrupt\w*|fabricat\w*|conspir\w*|retaliat\w*|framed|falsifi\w*)\b", re.I)
HEDGE = re.compile(r"\b(I cannot prove|does not prove|I am not (going to )?(asserting|claiming)|"
                   r"I only suspect|I believe|not evidence that|does not establish|"
                   r"I could not|remains? (my|his) (own )?(claim|belief|allegation)|unverified|"
                   r"I have not been able|the record does not)\b", re.I)
SELF  = re.compile(r"\b(I was wrong|my own conduct|does me no credit|I made it worse|"
                   r"I should have|I did not help|my fault|I gave it away|I was angry|"
                   r"I am not blameless|worse than I remembered)\b", re.I)
NAMES = re.compile(r"\b(East|Beavers|Kilpatrick|Tollison|Busby|Luther|Crowder|Osteen|Nugent|"
                   r"Alcorn|Little|Norman|Wilburn|Tannehill|Holladay|Edison)\b")

rows=[]
for c in chaps:
    title=c.split("\n",1)[0][2:].strip()
    w=len(c.split())
    rows.append(dict(
        title=title, words=w,
        tags=len(TAG.findall(c)), alleg=len(ALLEG.findall(c)),
        hedge=len(HEDGE.findall(c)), self=len(SELF.findall(c)),
        names=len(set(NAMES.findall(c))),
        tag_per_k=round(len(TAG.findall(c))/max(w,1)*1000,1),
        alleg_per_k=round(len(ALLEG.findall(c))/max(w,1)*1000,1)))

print("%-52s %6s %5s %5s %5s %5s %6s" % ("CHAPTER","words","tags","alleg","hedge","self","tag/1k"))
for r in rows:
    print("%-52s %6d %5d %5d %5d %5d %6.1f" % (r['title'][:52], r['words'], r['tags'], r['alleg'],
                                               r['hedge'], r['self'], r['tag_per_k']))
tot=sum(r['words'] for r in rows)
print("\nTOTAL narrative words: %d across %d chapters; median %d" %
      (tot, len(rows), sorted(r['words'] for r in rows)[len(rows)//2]))
