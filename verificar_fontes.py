import concurrent.futures as cf
import json, re, time
from pesquisar_whatsapp import OUT, fetch, digits

checkpoint=OUT/'sites_pesquisados.jsonl'
dest=OUT/'identidade_fontes.json'
checked=json.loads(dest.read_text(encoding='utf-8')) if dest.exists() else {}
def verify(url):
    try:
        final,text=fetch(url)
        ids=list(dict.fromkeys(digits(m) for m in re.findall(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b',text)))
        title=re.search(r'<title[^>]*>(.*?)</title>',text,re.I|re.S)
        return {'cnpjs':ids,'titulo':re.sub('<[^>]+>','',title.group(1)).strip()[:220] if title else '', 'url_final':final}
    except Exception as e: return {'cnpjs':[],'titulo':'','erro':type(e).__name__}
with cf.ThreadPoolExecutor(max_workers=8) as pool:
    while True:
        records=[json.loads(l) for l in checkpoint.read_text(encoding='utf-8').splitlines() if l.strip()]
        urls=list(dict.fromkeys(h['fonte'] for r in records for h in r['resultado']['hits'] if h['fonte'] not in checked))
        for url,result in zip(urls,pool.map(verify,urls)):
            checked[url]=result
        dest.write_text(json.dumps(checked,ensure_ascii=False),encoding='utf-8')
        print('Fontes verificadas:',len(checked),flush=True)
        if (OUT/'resultados.json').exists(): break
        time.sleep(15)
