import concurrent.futures as cf
import collections, datetime, html, json, re, pathlib, unicodedata
import urllib.request, urllib.parse, urllib.error
import openpyxl

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / 'outputs' / 'pesquisa_whatsapp'
OUT.mkdir(parents=True, exist_ok=True)
CITIES = 'Curitiba|Adrianópolis|Agudos do Sul|Almirante Tamandaré|Araucária|Balsa Nova|Bocaiúva do Sul|Campina Grande do Sul|Campo do Tenente|Campo Largo|Campo Magro|Cerro Azul|Colombo|Contenda|Doutor Ulysses|Fazenda Rio Grande|Itaperuçu|Lapa|Mandirituba|Piên|Pinhais|Piraquara|Quatro Barras|Rio Branco do Sul|Rio Negro|São José dos Pinhais|Quitandinha|Tijucas do Sul|Tunas do Paraná'.split('|')
def broken(s):
    return ''.join(c if ord(c)<128 else '\ufffd' for c in s)
CITYMAP = {v:c for c in CITIES for v in (c,broken(c))}
def digits(v): return re.sub(r'\D','',str(v or ''))
def phone(v):
    n=digits(v)
    if len(n) in (10,11): n='55'+n
    if len(n) not in (12,13) or not n.startswith('55'): return None
    if n[2:4] not in '11 12 13 14 15 16 17 18 19 21 22 24 27 28 31 32 33 34 35 37 38 41 42 43 44 45 46 47 48 49 51 53 54 55 61 62 63 64 65 66 67 68 69 71 73 74 75 77 79 81 82 83 84 85 86 87 88 89 91 92 93 94 95 96 97 98 99'.split(): return None
    if (len(n)==13 and n[4]!='9') or (len(n)==12 and n[4] not in '2345'): return None
    return n
def fetch(url):
    p=urllib.parse.urlparse(url)
    if p.scheme not in ('http','https') or not p.hostname or p.hostname in ('localhost','127.0.0.1'): raise ValueError('URL inválida')
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; BusinessContactResearch/1.0)'})
    with urllib.request.urlopen(req, timeout=9) as r:
        raw=r.read(1500000)
        return r.url, raw.decode(r.headers.get_content_charset() or 'utf-8',errors='replace')
def extract(text, source):
    text=html.unescape(text).replace('\\/','/')
    hits=[]
    for m in re.finditer(r'(?:https?://)?(?:wa\.me/|(?:api|web)\.whatsapp\.com/(?:send/?\?[^\s"<>]*?phone=)|whatsapp://send\?phone=)([+\d%(). -]{8,35})',text,re.I):
        n=phone(urllib.parse.unquote(m.group(1)))
        if n: hits.append({'numero':n,'fonte':source,'evidencia':m.group(0)[:240],'tipo':'Link explícito WhatsApp'})
    return list({(x['numero'],x['fonte']):x for x in hits}.values())
def crawl(site):
    if not site: return {'status':'Sem site na base','hits':[],'paginas':[]}
    url=str(site).strip()
    if not url.startswith(('http://','https://')): url='https://'+url
    pages=[]; hits=[]; errors=[]
    try:
        final,text=fetch(url); pages.append(final); hits.extend(extract(text,final))
    except Exception as e:
        return {'status':'Site inacessível','hits':[],'paginas':pages,'erro':type(e).__name__+': '+str(e)[:160]}
    # At most two contact pages on the same host; do not follow chat or send links.
    links=[]
    for href in re.findall(r'href\s*=\s*["\']([^"\']+)',text,re.I):
        target=urllib.parse.urljoin(final,html.unescape(href)).split('#')[0]
        if urllib.parse.urlparse(target).netloc==urllib.parse.urlparse(final).netloc and re.search(r'contat|contact|fale-conosco',target,re.I) and target not in links and target not in pages:
            links.append(target)
    for target in links[:2]:
        try:
            u,t=fetch(target); pages.append(u); hits.extend(extract(t,u))
        except Exception as e: errors.append(type(e).__name__)
    return {'status':'Link WhatsApp encontrado' if hits else 'Sem link explícito nas páginas consultadas','hits':list({(x['numero'],x['fonte']):x for x in hits}.values()),'paginas':pages,'erro':'; '.join(errors)}

def main():
    wb=openpyxl.load_workbook(next(ROOT.glob('*.xlsx')),read_only=True,data_only=True)
    rows=list(wb['Base Completa - Limpa'].values)
    leads=[]
    for i,r0 in enumerate(rows[1:],2):
        r=list(r0)+[None]*29
        if r[3] not in CITYMAP: continue
        leads.append({'linha':i,'cnpj':r[1],'empresa':r[2],'cidade_original':r[3],'cidade':CITYMAP[r[3]],'score':r[0],'telefone_maps':r[4],'telefone_receita':r[5],'whatsapp_original':r[6],'email':r[7],'status_ligacao':r[8],'site':r[16] or r[28],'endereco':r[21]})
    (OUT/'base_recorte.json').write_text(json.dumps(leads,ensure_ascii=False),encoding='utf-8')
    sites=list(dict.fromkeys(str(x['site']).strip() for x in leads if x['site']))
    checkpoint=OUT/'sites_pesquisados.jsonl'
    existing={}
    if checkpoint.exists():
        for l in checkpoint.read_text(encoding='utf-8').splitlines():
            d=json.loads(l); existing[d['site']]=d['resultado']
    pending=[s for s in sites if s not in existing]
    print(json.dumps({'base_total':len(rows)-1,'recorte':len(leads),'sites_unicos':len(sites),'pendentes':len(pending),'whatsapp_original':sum(bool(x['whatsapp_original']) for x in leads)},ensure_ascii=False),flush=True)
    with checkpoint.open('a',encoding='utf-8') as f, cf.ThreadPoolExecutor(max_workers=12) as pool:
        jobs={pool.submit(crawl,s):s for s in pending}
        for j,future in enumerate(cf.as_completed(jobs),1):
            s=jobs[future]; result=future.result(); existing[s]=result
            f.write(json.dumps({'site':s,'resultado':result},ensure_ascii=False)+'\n'); f.flush()
            if j%50==0: print('Sites pesquisados:',j,'/',len(pending),flush=True)
    for x in leads:
        x['pesquisa']=existing.get(str(x['site']).strip(),{'status':'Sem site na base','hits':[],'paginas':[]})
    (OUT/'resultados.json').write_text(json.dumps(leads,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'status':dict(collections.Counter(x['pesquisa']['status'] for x in leads)),'com_candidatos':sum(bool(x['pesquisa']['hits']) for x in leads)},ensure_ascii=False),flush=True)
if __name__=='__main__': main()
