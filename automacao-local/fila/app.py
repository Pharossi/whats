import datetime, hmac, json, os, re, threading, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from rules import classify, permitted

def db():
    return psycopg.connect(os.environ['DATABASE_URL'],row_factory=dict_row)

SCHEMA='''
CREATE TABLE IF NOT EXISTS contacts (
 id bigserial PRIMARY KEY, cnpj text NOT NULL, company text NOT NULL, city text NOT NULL,
 phone text NOT NULL CHECK (phone ~ '^55[0-9]{10,11}$'), source text NOT NULL,
 draft text NOT NULL DEFAULT '', reviewed boolean NOT NULL DEFAULT false,
 consent_source text NOT NULL DEFAULT '', consent_at timestamptz,
 paused boolean NOT NULL DEFAULT false, opted_out boolean NOT NULL DEFAULT false,
 classification text NOT NULL DEFAULT 'INCONCLUSIVO', UNIQUE(cnpj,phone));
CREATE TABLE IF NOT EXISTS blocked_phones (phone text PRIMARY KEY, created_at timestamptz DEFAULT now());
CREATE TABLE IF NOT EXISTS messages (
 id bigserial PRIMARY KEY, instance text NOT NULL, event_id text NOT NULL,
 phone text NOT NULL, text text NOT NULL, classification text NOT NULL,
 created_at timestamptz DEFAULT now(), UNIQUE(instance,event_id));
CREATE TABLE IF NOT EXISTS dispatches (
 id bigserial PRIMARY KEY, phone text NOT NULL UNIQUE, contact_id bigint NOT NULL REFERENCES contacts(id),
 text text NOT NULL, status text NOT NULL DEFAULT 'RESERVED', external_id text,
 created_at timestamptz DEFAULT now());
CREATE TABLE IF NOT EXISTS simulations (id bigserial PRIMARY KEY, contact_id bigint REFERENCES contacts(id), created_at timestamptz DEFAULT now());
'''

def init():
    with db() as c:
        c.execute(SCHEMA)
        with open('/data/contatos.json',encoding='utf-8') as f: rows=json.load(f)
        for row in rows:
            c.execute('INSERT INTO contacts(cnpj,company,city,phone,source) VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',
                (row['cnpj'],row['company'],row['city'],row['phone'],row['source']))

def inbound(payload):
    if payload.get('event') not in ('messages.upsert','MESSAGES_UPSERT'): return {'ignored':True}
    if payload.get('instance')!=os.environ.get('EVOLUTION_INSTANCE','crescer'): return {'ignored':True}
    data=payload.get('data',{})
    if not isinstance(data,dict): return {'ignored':True}
    key=data.get('key',{}); jid=key.get('remoteJid','')
    if key.get('fromMe') or not jid.endswith('@s.whatsapp.net') or not key.get('id'): return {'ignored':True}
    phone=jid.split('@')[0]
    if not re.fullmatch(r'55\d{10,11}',phone): return {'ignored':True}
    msg=data.get('message',{})
    text=msg.get('conversation') or msg.get('extendedTextMessage',{}).get('text') or '[Mídia ou mensagem sem texto — revisar]'
    classification=classify(text)
    with db() as c:
        added=c.execute('INSERT INTO messages(instance,event_id,phone,text,classification) VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id',
            (payload['instance'],key['id'],phone,text,classification)).fetchone()
        if not added:return {'duplicate':True}
        c.execute('UPDATE contacts SET paused=true,classification=%s WHERE phone=%s',(classification,phone))
        if classification=='OPT_OUT':
            c.execute('INSERT INTO blocked_phones(phone) VALUES (%s) ON CONFLICT DO NOTHING',(phone,))
            c.execute('UPDATE contacts SET opted_out=true WHERE phone=%s',(phone,))
    return {'classification':classification,'paused':True}

def dispatch(live=False):
    if live and os.getenv('LIVE_SEND_ENABLED')!='true': raise ValueError('Envio real desabilitado no .env')
    # Serializes dispatch and webhook writes within this single service process.
    with gate, db() as c:
        row=c.execute('''SELECT * FROM contacts c WHERE reviewed AND consent_source<>'' AND draft<>'' AND NOT paused AND NOT opted_out
            AND NOT EXISTS(SELECT 1 FROM blocked_phones b WHERE b.phone=c.phone)
            AND NOT EXISTS(SELECT 1 FROM dispatches d WHERE d.phone=c.phone) ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED''').fetchone()
        if not row:return {'status':'SEM_CONTATOS_LIBERADOS'}
        if not permitted(row,False):raise ValueError('Contato sem todos os requisitos de revisão')
        if not live:
            c.execute('INSERT INTO simulations(contact_id) VALUES (%s)',(row['id'],))
            return {'status':'SIMULACAO_SEM_ENVIO','contact_id':row['id'],'phone':row['phone'],'text':row['draft']}
        reserved=c.execute('INSERT INTO dispatches(phone,contact_id,text) VALUES (%s,%s,%s) RETURNING id',
            (row['phone'],row['id'],row['draft'])).fetchone()['id']
        c.commit()  # Persist before the network call; unknown outcomes must never be retried automatically.
        body=json.dumps({'number':row['phone'],'text':row['draft']}).encode()
        instance=os.environ.get('EVOLUTION_INSTANCE','crescer')
        request=urllib.request.Request(os.environ['EVOLUTION_URL']+'/message/sendText/'+instance,data=body,
            headers={'Content-Type':'application/json','apikey':os.environ['EVOLUTION_API_KEY']})
        try:
            with urllib.request.urlopen(request,timeout=25) as response: result=json.load(response)
            external=result.get('key',{}).get('id')
            status='ACCEPTED' if external else 'UNKNOWN'
        except Exception:
            external=None;status='UNKNOWN'
        c.execute('UPDATE dispatches SET status=%s,external_id=%s WHERE id=%s',(status,external,reserved))
        return {'status':status,'dispatch_id':reserved,'message_id':external}

gate=threading.RLock()
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass  # Do not log credentials, webhook paths or message contents.
    def reply(self,status,data):
        raw=json.dumps(data,ensure_ascii=False,default=str).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
    def do_GET(self): self.handle_request()
    def do_POST(self): self.handle_request()
    def handle_request(self):
        webhook='/webhook/'+os.environ['WEBHOOK_SECRET']
        if self.path=='/health' and self.command=='GET':
            try:
                with db() as c:c.execute('SELECT 1')
                return self.reply(200,{'status':'ok','live_send':os.getenv('LIVE_SEND_ENABLED')=='true'})
            except Exception:return self.reply(503,{'error':'Banco indisponível'})
        is_webhook=hmac.compare_digest(self.path,webhook) and self.command=='POST'
        if not is_webhook and not hmac.compare_digest(self.headers.get('X-Api-Key',''),os.environ['ADMIN_KEY']):return self.reply(401,{'error':'Não autorizado'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<0 or length>1000000:return self.reply(413,{'error':'Payload muito grande'})
            payload=json.loads(self.rfile.read(length)) if length else {}
            if is_webhook:
                with gate:result=inbound(payload)
                return self.reply(200,result)
            if self.command=='GET' and self.path=='/contacts':
                with db() as c: rows=c.execute('SELECT * FROM contacts ORDER BY reviewed,id LIMIT 100').fetchall()
                return self.reply(200,rows)
            if self.command=='GET' and self.path=='/inbox':
                with db() as c:rows=c.execute('SELECT * FROM messages ORDER BY id DESC LIMIT 100').fetchall()
                return self.reply(200,rows)
            if self.command=='POST' and self.path=='/review':
                if not payload.get('verified') or not str(payload.get('consent_source','')).strip() or not str(payload.get('draft','')).strip():raise ValueError('Confirme o número, informe a autorização e revise a mensagem')
                with gate,db() as c:
                    row=c.execute('''UPDATE contacts SET reviewed=true,consent_source=%s,consent_at=now(),draft=%s
                        WHERE id=%s AND NOT paused AND NOT opted_out AND NOT EXISTS(SELECT 1 FROM blocked_phones b WHERE b.phone=contacts.phone) RETURNING id''',
                        (payload['consent_source'],payload['draft'],int(payload['contact_id']))).fetchone()
                if not row:raise ValueError('Contato não localizado, pausado ou bloqueado')
                return self.reply(200,row)
            if self.command=='POST' and self.path=='/dispatch':return self.reply(200,dispatch(payload.get('live') is True))
            return self.reply(404,{'error':'Rota não encontrada'})
        except (ValueError,KeyError,TypeError) as e:return self.reply(400,{'error':str(e)})
        except Exception:return self.reply(500,{'error':'Falha interna; verificar o serviço sem repetir envio'})

if __name__=='__main__':
    init()
    ThreadingHTTPServer(('0.0.0.0',8000),Handler).serve_forever()
