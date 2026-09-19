#!/usr/bin/env python3
"""Export the current submission DOCX to a synchronized Markdown manuscript."""
from pathlib import Path
from docx import Document
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/PlantMR_submission_manuscript.docx'
OUT=ROOT/'docs/manuscript-draft.en.md'
FIGS={
    1:'figures/plantmr_workflow.png',
    2:'figures/gxe_simulation.png',
    3:'figures/gxe_ld_stress.png',
    4:'figures/arabidopsis_case.png',
}

def blocks(parent):
    for child in parent.element.body.iterchildren():
        if isinstance(child,CT_P): yield Paragraph(child,parent)
        elif isinstance(child,CT_Tbl): yield Table(child,parent)

def esc(s):
    return s.replace('|','\\|').replace('\n',' ')

def main():
    d=Document(DOC); out=[]; seen_fig=set()
    for b in blocks(d):
        if isinstance(b,Paragraph):
            text=b.text.strip()
            if not text: continue
            style=b.style.name if b.style else ''
            if text.startswith('Figure '):
                try: n=int(text.split()[1].rstrip('.'))
                except Exception: n=None
                if n in FIGS and n not in seen_fig:
                    out.append(f'![Figure {n}]({FIGS[n]})\n')
                    seen_fig.add(n)
                out.append(text+'\n')
            elif style.startswith('Heading'):
                try: level=int(style.rsplit(' ',1)[1])
                except Exception: level=2
                out.append('#'*level+' '+text+'\n')
            elif text.startswith('PlantMR |') or text.startswith('Page '):
                continue
            else:
                out.append(text+'\n')
        else:
            rows=[]
            for row in b.rows:
                rows.append([esc(c.text.strip()) for c in row.cells])
            if rows:
                out.append('| '+' | '.join(rows[0])+' |\n')
                out.append('| '+' | '.join(['---']*len(rows[0]))+' |\n')
                for row in rows[1:]: out.append('| '+' | '.join(row)+' |\n')
                out.append('\n')
    text='\n'.join(out)
    text=text.replace('Submission status\n','> Submission status\n')
    OUT.write_text(text,encoding='utf-8')
    print(OUT, 'chars',len(text), 'figures',len(seen_fig))

if __name__=='__main__': main()
