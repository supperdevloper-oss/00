import glob, markdown, re, os, sys, time, pymupdf
os.chdir('/home/user/00/كتاب-تربية-الدواجن')
files=sorted(glob.glob('[0-9][0-9]_*.md'))
css='''
body{font-family:sans-serif;font-size:10.5pt;line-height:1.5;color:#111}
h1{font-size:20pt;color:#1f3d2b;border-bottom:2px solid #c8a951;padding-bottom:4pt;margin-top:0}
h2{font-size:14pt;color:#2e5a40;margin-top:14pt}
h3{font-size:12pt;color:#333}
h4{font-size:11pt}
table{border-collapse:collapse;width:100%;font-size:8.5pt;margin:6pt 0}
th,td{border:0.6pt solid #888;padding:3pt 4pt;text-align:right;vertical-align:top}
th{background-color:#e8efe9;font-weight:bold}
blockquote{border-right:3pt solid #c8a951;padding:2pt 8pt;margin:6pt 0;background-color:#fbf7ec}
ul,ol{margin:4pt 0} li{margin:1pt 0}
hr{border:0;border-top:0.5pt dashed #999}
'''
rect=pymupdf.paper_rect('a4'); where=rect+(50,50,-50,-55)
os.makedirs('/tmp/parts',exist_ok=True)
for i,f in enumerate(files):
    out=f'/tmp/parts/{i:02d}.pdf'
    if os.path.exists(out): continue
    t0=time.time()
    h=markdown.markdown(open(f,encoding='utf-8').read(),extensions=['tables','sane_lists'])
    story=pymupdf.Story(html='<html dir="rtl"><body>'+h+'</body></html>',user_css=css)
    w=pymupdf.DocumentWriter(out); more=True; n=0
    while more:
        dev=w.begin_page(rect); more,_=story.place(where); story.draw(dev); w.end_page(); n+=1
    w.close(); print(f, n, round(time.time()-t0,1), flush=True)
# merge + page numbers
final=pymupdf.open()
for i in range(len(files)):
    final.insert_pdf(pymupdf.open(f'/tmp/parts/{i:02d}.pdf'))
for pno,page in enumerate(final):
    if pno==0: continue
    page.insert_text((rect.width/2-8, rect.height-30), str(pno+1), fontsize=9, fontname='helv', color=(0.3,0.3,0.3))
final.set_metadata({'title':'دليل تربية الدواجن في المغرب — من الكتكوت إلى الإنتاج والبيع','author':'','subject':'تربية الدواجن'})
# outline
toc=[]; p=0
for i,f in enumerate(files):
    title=re.search(r'^# (.+)$',open(f,encoding='utf-8').read(),re.M).group(1)
    toc.append([1,title,p+1]); p+=pymupdf.open(f'/tmp/parts/{i:02d}.pdf').page_count
final.set_toc(toc)
final.save('/home/user/00/preview/دليل_تربية_الدواجن_في_المغرب.pdf', garbage=3, deflate=True)
print('DONE pages', final.page_count, flush=True)
