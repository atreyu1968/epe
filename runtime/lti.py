"""LTI Advantage 1.3: Moodle OIDC launch, RS256, roster/assignment and optional AGS.
No Moodle sub is ever treated as an EPE username without an explicit teacher binding.
"""
from __future__ import annotations
import base64, hashlib, hmac, html, json, os, secrets, sqlite3, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlencode
import httpx, jwt
from cryptography.hazmat.primitives import serialization
from fastapi import APIRouter, Depends, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response, FileResponse
from pydantic import BaseModel, Field
from . import course_core as core

router=APIRouter(prefix='/lti',tags=['LTI 1.3'])
LTI='https://purl.imsglobal.org/spec/lti/claim/'
AGS='https://purl.imsglobal.org/spec/lti-ags/scope/'
NRPS='https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly'
SCOPES=[AGS+'score',AGS+'lineitem',NRPS]
DB=core.DATA/'lti.sqlite'


def conf(key):return os.environ.get('EPE_LTI_'+key,'').strip()

def origin(value):
 p=urlsplit(value)
 return f'{p.scheme}://{p.netloc}' if p.scheme=='https' and p.netloc and not p.username and not p.password else ''

def settings():
 values={k:conf(k) for k in ('ISSUER','CLIENT_ID','AUTH_URL','JWKS_URL','TOKEN_URL','DEPLOYMENT_ID','PRIVATE_KEY_FILE')}
 values['PUBLIC_URL']=os.environ.get('EPE_PUBLIC_URL','').rstrip('/')
 if any(not v for v in values.values()):raise HTTPException(503,'LTI pendiente de configuración: consulta docs/LTI_CAMPUS.md')
 if (not origin(values['ISSUER']) or any(origin(values[k])!=origin(values['ISSUER']) for k in ('AUTH_URL','JWKS_URL','TOKEN_URL'))
     or not origin(values['PUBLIC_URL']) or not values['ISSUER']==origin(values['ISSUER'])):
  raise HTTPException(503,'Orígenes LTI incorrectos: URLs HTTPS del Campus, sin dominios ajenos')
 return values

def connection():
 c=sqlite3.connect(str(DB),timeout=15,isolation_level=None)
 c.row_factory=sqlite3.Row
 c.execute('PRAGMA busy_timeout=15000')
 return c

def init():
 DB.parent.mkdir(parents=True,exist_ok=True)
 with connection() as c:
  c.executescript('''
  CREATE TABLE IF NOT EXISTS oidc_state(state TEXT PRIMARY KEY, nonce TEXT NOT NULL, expiry INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS participants(id INTEGER PRIMARY KEY,issuer TEXT NOT NULL,client_id TEXT NOT NULL,deployment_id TEXT NOT NULL,subject TEXT NOT NULL,context_id TEXT NOT NULL,display TEXT NOT NULL,email TEXT,roles TEXT NOT NULL,seen INTEGER NOT NULL,UNIQUE(issuer,client_id,deployment_id,subject,context_id));
  CREATE TABLE IF NOT EXISTS bindings(participant_id INTEGER PRIMARY KEY REFERENCES participants(id),username TEXT NOT NULL,created_at INTEGER NOT NULL);
  CREATE UNIQUE INDEX IF NOT EXISTS one_lti_student_per_epe_account ON bindings(username);
  CREATE TABLE IF NOT EXISTS sessions(digest TEXT PRIMARY KEY,participant_id INTEGER NOT NULL REFERENCES participants(id),expiry INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS services(context_id TEXT PRIMARY KEY,lineitems TEXT,memberships TEXT,resource_link_id TEXT,service_versions TEXT,updated INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS grade_lines(context_id TEXT NOT NULL,unit INTEGER NOT NULL,kind TEXT NOT NULL,lineitem_url TEXT NOT NULL,PRIMARY KEY(context_id,unit,kind));
  ''')
init()


def reject(message='Acceso LTI no válido',status=403):raise HTTPException(status,message)

def current_identity(request:Request):
 t=request.cookies.get('epe_lti_session','')
 if len(t)<30:reject('Abre primero la herramienta desde tu curso de Campus',401)
 with connection() as db:
  r=db.execute('''SELECT p.*,b.username FROM sessions s JOIN participants p ON p.id=s.participant_id
     LEFT JOIN bindings b ON b.participant_id=p.id WHERE s.digest=? AND s.expiry>?''',(hashlib.sha256(t.encode()).hexdigest(),int(time.time()))).fetchone()
 if not r:reject('Sesión LTI caducada: vuelve a abrir desde Campus',401)
 return dict(r)

def csrf_check(request:Request,identity):
 # The launch produces a cookie-based session. Mutations must require a same-origin custom header.
 value=request.headers.get('x-epe-lti-csrf','')
 secret=request.cookies.get('epe_lti_session','')
 expected=hmac.new(secret.encode(),b'epe-lti-csrf-v1',hashlib.sha256).hexdigest()
 if not hmac.compare_digest(value,expected):reject('Verificación de solicitud LTI fallida')
 if request.headers.get('origin') and request.headers['origin'].rstrip('/') != settings()['PUBLIC_URL']:
  reject('Origen de la solicitud no autorizado')


def validate_token(id_token,state):
 cfg=settings()
 with connection() as db:
  r=db.execute('SELECT nonce,expiry FROM oidc_state WHERE state=?',(state,)).fetchone()
  if not r or r['expiry']<int(time.time()):reject('El inicio de sesión ha caducado')
  # State is one-use, including when token validation subsequently fails.
  db.execute('DELETE FROM oidc_state WHERE state=?',(state,))
 try:
  header=jwt.get_unverified_header(id_token)
  if header.get('alg')!='RS256' or not header.get('kid'):reject('Firma de Campus no admitida')
  res=httpx.get(cfg['JWKS_URL'],timeout=8,follow_redirects=False)
  res.raise_for_status();jwks=res.json().get('keys',[])
  candidates=[k for k in jwks if k.get('kid')==header['kid'] and k.get('kty')=='RSA' and k.get('use','sig')=='sig']
  if len(candidates)!=1:reject('No se encuentra la clave pública de Campus')
  public=jwt.PyJWK.from_dict(candidates[0],algorithm='RS256').key
  claims=jwt.decode(id_token,public,algorithms=['RS256'],audience=cfg['CLIENT_ID'],issuer=cfg['ISSUER'],options={'require':['iss','sub','aud','iat','exp','nonce']},leeway=60)
 except HTTPException:raise
 except Exception:reject('No se puede verificar criptográficamente el lanzamiento de Campus')
 if claims.get('nonce')!=r['nonce'] or claims.get(LTI+'deployment_id')!=cfg['DEPLOYMENT_ID']:
  reject('Nonce o despliegue LTI incorrecto')
 if claims.get(LTI+'version')!='1.3.0' or claims.get(LTI+'message_type')!='LtiResourceLinkRequest':reject('Mensaje LTI no reconocido')
 if not claims.get(LTI+'resource_link',{}).get('id') or not claims.get(LTI+'context',{}).get('id'):
  reject('Campus no ha identificado el curso y la actividad')
 if claims.get('azp',cfg['CLIENT_ID'])!=cfg['CLIENT_ID']:reject('Cliente autorizado no coincide')
 if claims.get('https://purl.imsglobal.org/spec/lti/claim/target_link_uri')!=cfg['PUBLIC_URL']+'/lti/launch':
  reject('Dirección de lanzamiento distinta de la registrada')
 return claims

@router.get('/health')
def lti_health():
 return {'configured':bool(conf('CLIENT_ID') and conf('DEPLOYMENT_ID') and os.environ.get('EPE_PUBLIC_URL')),'protocol':'LTI 1.3','components':['OIDC','NRPS','AGS']}

@router.api_route('/login',methods=['GET','POST'])
async def oidc_login(request:Request):
 form=await request.form() if request.method=='POST' else request.query_params
 cfg=settings()
 issuer=form.get('iss')
 if issuer!=cfg['ISSUER']:reject('Emisor Moodle no reconocido')
 if form.get('client_id') and form.get('client_id')!=cfg['CLIENT_ID']:reject('Client ID inesperado')
 if form.get('target_link_uri')!=cfg['PUBLIC_URL']+'/lti/launch':reject('URL de destino no reconocida')
 hint=form.get('login_hint','')
 if not hint or len(hint)>2048:reject('Falta login_hint del LMS')
 state=secrets.token_urlsafe(30);nonce=secrets.token_urlsafe(30)
 with connection() as db:
  db.execute('DELETE FROM oidc_state WHERE expiry<?',(int(time.time()),))
  db.execute('INSERT INTO oidc_state(state,nonce,expiry) VALUES(?,?,?)',(state,nonce,int(time.time()+300)))
 params={'scope':'openid','response_type':'id_token','client_id':cfg['CLIENT_ID'],'redirect_uri':cfg['PUBLIC_URL']+'/lti/launch','login_hint':hint,'state':state,'nonce':nonce,'response_mode':'form_post','prompt':'none'}
 if form.get('lti_message_hint'):params['lti_message_hint']=form['lti_message_hint']
 response=RedirectResponse(cfg['AUTH_URL']+'?'+urlencode(params),status_code=303)
 response.set_cookie('epe_lti_state_'+hashlib.sha256(state.encode()).hexdigest()[:20],state,max_age=300,httponly=True,secure=True,samesite='none',path='/lti')
 response.headers['Cache-Control']='no-store'
 return response

@router.post('/launch')
async def oidc_launch(request:Request):
 form=await request.form();state=form.get('state','')
 if not state or len(state)>256 or not form.get('id_token') or len(form['id_token'])>16000:reject('Lanzamiento incompleto')
 cookie='epe_lti_state_'+hashlib.sha256(state.encode()).hexdigest()[:20]
 if not hmac.compare_digest(request.cookies.get(cookie,''),state):reject('No coincide la sesión del navegador. Abre la herramienta en ventana nueva desde Moodle.')
 claims=validate_token(form['id_token'],state)
 cfg=settings();ctx=claims[LTI+'context']['id'];sub=claims['sub'];roles=claims.get(LTI+'roles',[])
 if not all(isinstance(x,str) and len(x)<256 for x in (sub,ctx)) or not sub or not ctx:reject('Identidad de Campus inválida')
 display=str(claims.get('name') or claims.get('given_name') or 'Estudiante')[:150]
 with connection() as db:
  db.execute('''INSERT INTO participants(issuer,client_id,deployment_id,subject,context_id,display,email,roles,seen)
    VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(issuer,client_id,deployment_id,subject,context_id) DO UPDATE SET
    display=excluded.display,email=excluded.email,roles=excluded.roles,seen=excluded.seen''',
    (cfg['ISSUER'],cfg['CLIENT_ID'],cfg['DEPLOYMENT_ID'],sub,ctx,display,str(claims.get('email') or '')[:200],json.dumps(roles),int(time.time())))
  participant=db.execute('SELECT id FROM participants WHERE issuer=? AND client_id=? AND deployment_id=? AND subject=? AND context_id=?',(cfg['ISSUER'],cfg['CLIENT_ID'],cfg['DEPLOYMENT_ID'],sub,ctx)).fetchone()
  ep=claims.get(LTI+'ags',{})
  nr=claims.get(LTI+'namesroleservice',{})
  lineitems=ep.get('lineitems','') if AGS+'lineitem' in ep.get('scope',[]) else ''
  memberships=nr.get('context_memberships_url','') if nr.get('service_versions') and isinstance(nr.get('service_versions'),list) else ''
  if lineitems and not allowed_moodle_url(lineitems,cfg):lineitems=''
  if memberships and not allowed_moodle_url(memberships,cfg):memberships=''
  if lineitems or memberships:
   db.execute('''INSERT INTO services(context_id,lineitems,memberships,resource_link_id,service_versions,updated) VALUES(?,?,?,?,?,?)
     ON CONFLICT(context_id) DO UPDATE SET lineitems=excluded.lineitems,memberships=excluded.memberships,resource_link_id=excluded.resource_link_id,service_versions=excluded.service_versions,updated=excluded.updated''',
     (ctx,lineitems,memberships,claims[LTI+'resource_link']['id'],json.dumps(ep.get('scope',[])),int(time.time())))
  session=secrets.token_urlsafe(36)
  db.execute('INSERT INTO sessions(digest,participant_id,expiry) VALUES(?,?,?)',(hashlib.sha256(session.encode()).hexdigest(),participant['id'],int(time.time()+8*3600)))
 resp=RedirectResponse(cfg['PUBLIC_URL']+'/lti/portal',status_code=303)
 resp.set_cookie('epe_lti_session',session,max_age=8*3600,httponly=True,secure=True,samesite='none',path='/lti')
 resp.delete_cookie(cookie,path='/lti',secure=True,samesite='none')
 resp.headers['Cache-Control']='no-store'
 return resp

def allowed_moodle_url(value,cfg):
 p=urlsplit(value)
 return p.scheme=='https' and origin(value)==origin(cfg['ISSUER']) and not p.username and not p.password

def page(title,body):
 return HTMLResponse('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+html.escape(title)+'</title><style>body{font:16px system-ui;color:#203047;background:#f2f6fa;max-width:950px;margin:5vh auto;padding:22px}main{background:white;border-radius:16px;padding:30px;box-shadow:0 3px 14px #0001}a{display:inline-block;padding:13px;margin:8px;background:#173c66;color:white;text-decoration:none;border-radius:8px}p{line-height:1.6}code{font-size:14px}small{color:#666}</style><main><h1>'+html.escape(title)+'</h1>'+body+'</main></html>',headers={'Cache-Control':'no-store','Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'self'"})

@router.get('/portal')
def portal(u=Depends(current_identity)):
 name=html.escape(u['display'])
 if not u['username']:
  return page('Empresa en el Aula · Acceso pendiente','<p>Hola, '+name+'. Campus ha autenticado correctamente tu identidad. <b>Tu profesor debe asignarte a una empresa</b> antes de que puedas trabajar.</p><p>Una vez asignado, abre otra vez esta herramienta en Campus. No necesitas ninguna contraseña adicional.</p>')
 links=''.join(f'<a href="/lti/app/u{n}/portfolio/">Unidad {n}: Mi empresa</a>' for n in range(1,8))
 return page('Empresa en el Aula · Mi empresa','<p>Hola, '+name+'. Accede a tu portafolio cooperativo. La identidad y el equipo se recuperan de la vinculación autorizada por el profesor.</p>'+links+'<p><small>El examen individual continúa en la actividad SCORM correspondiente de Campus.</small></p>')

@router.get('/api/bootstrap')
def bootstrap(unit:int,request:Request,u=Depends(current_identity)):
 if not 1<=unit<=7:reject('Unidad incorrecta',400)
 if not u['username']:reject('Pendiente de asignación a una empresa')
 from . import unified
 m=unified.modules[unit]
 with m.conn() as db:
  person=db.execute('SELECT id FROM users WHERE username=?',(u['username'],)).fetchone()
  if not person:reject('Usuario no encontrado en las siete unidades')
  token=secrets.token_urlsafe(32)
  db.execute('INSERT INTO sessions(digest,user_id,expires) VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),person['id'],int(time.time()+8*3600)))
 csrf=hmac.new(request.cookies['epe_lti_session'].encode(),b'epe-lti-csrf-v1',hashlib.sha256).hexdigest()
 return {'token':token,'csrf':csrf,'unit':unit,'username':u['username'],'grade_sync_enabled':os.environ.get('EPE_LTI_GRADE_MODE','disabled')=='portfolio'}

@router.get('/app/u{unit}/{mode}/{path:path}')
@router.get('/app/u{unit}/{mode}/')
def serve_app(unit:int,mode:str,path:str='index.html',u=Depends(current_identity)):
 if not u['username']:reject('El profesor todavía no te ha asignado una empresa')
 if not 1<=unit<=7 or mode!='portfolio':reject('Ruta no disponible',404)
 root=(core.HOME/'unidades'/f'U{unit}'/'scorm_portafolio').resolve()
 candidate=(root/path).resolve()
 if not candidate.is_relative_to(root) or not candidate.is_file():reject('Recurso inexistente',404)
 headers={'Cache-Control':'no-store' if path in ('index.html','app.js','config.js') else 'private, max-age=900','X-Content-Type-Options':'nosniff'}
 if path=='config.js':
  return Response(f"window.EPE_CONFIG={{apiBase:'/u{unit}'}};window.EPE_LTI_MODE=true;window.EPE_LTI_UNIT={unit};",media_type='application/javascript',headers=headers)
 if path=='lms.js':
  # No SCORM runtime in the LTI window; grades may be sent only through the authorized AGS service.
  return Response("window.EPE_LMS={init:()=>true,value:()=>'',save:()=>true,exit:()=>{window.location.href='/lti/portal'}};",media_type='application/javascript',headers=headers)
 if path=='app.js':
  source=candidate.read_text(encoding='utf-8')
  start=source.index('function start(){')
  end=source.index('\n',start)
  source=source[:start]+'''function start(){window.EPE_LMS.init();fetch('/lti/api/bootstrap?unit='+window.EPE_LTI_UNIT,{credentials:'same-origin',cache:'no-store'}).then(async r=>{if(!r.ok)throw Error('Vuelve a abrir Empresa en el Aula desde Campus');return r.json()}).then(async data=>{token=data.token;window.EPE_LTI_CSRF=data.csrf;await boot()}).catch(err=>node('<section class="panel"><h2>Acceso LTI</h2><p>'+h(err.message)+'</p><a href="/lti/portal">Volver</a></section>'));}
''' + source[end+1:]
  # Grade sync is explicit only when teacher enables it after QA. Never duplicate the separate SCORM exam.
  source+='''\nif(window.EPE_LTI_MODE && MODE==='portfolio'){
 const originalSync=syncPortfolioGrade;
 syncPortfolioGrade=function(){originalSync();if(report&&report.portfolio_complete){fetch('/lti/api/sync-portfolio?unit='+window.EPE_LTI_UNIT,{method:'POST',credentials:'same-origin',headers:{'X-EPE-LTI-CSRF':window.EPE_LTI_CSRF||''},cache:'no-store'}).catch(()=>{});}};
}\n'''
  return Response(source,media_type='application/javascript',headers=headers)
 return FileResponse(candidate,headers=headers)


def admin_auth(authorization:str|None=Header(None)):
 from .unified import admin_ok
 return admin_ok(authorization)

class Assignment(BaseModel):
 participant_id:int=Field(gt=0)
 username:str=Field(min_length=2,max_length=80)

@router.get('/admin/roster')
def teacher_roster(ok=Depends(admin_auth)):
 from . import unified
 with connection() as db:
  participants=[dict(r) for r in db.execute('''SELECT p.id,p.display,p.context_id,p.subject,p.seen,b.username FROM participants p LEFT JOIN bindings b ON b.participant_id=p.id ORDER BY p.context_id,p.display''')]
 with unified.modules[1].conn() as db:
  accounts=[dict(r) for r in db.execute('''SELECT u.username,u.display,t.name AS team FROM users u JOIN teams t ON t.id=u.team_id ORDER BY t.name,u.display''')]
 return {'campus':participants,'erp_accounts':accounts}

@router.post('/admin/bind')
def teacher_bind(data:Assignment,ok=Depends(admin_auth)):
 from . import unified
 account=data.username.strip().lower()
 with unified.modules[1].conn() as db:
  student=db.execute('SELECT id,lms_id FROM users WHERE username=?',(account,)).fetchone()
 if not student:reject('La cuenta EPE no existe',404)
 with connection() as db:
  p=db.execute('SELECT * FROM participants WHERE id=?',(data.participant_id,)).fetchone()
  if not p:reject('Este alumno no ha abierto todavía la herramienta desde Campus',404)
  if not any('Learner' in role for role in json.loads(p['roles'])):reject('Solo se pueden vincular identidades de estudiantes',403)
  current=db.execute('SELECT username FROM bindings WHERE participant_id=?',(data.participant_id,)).fetchone()
  if current and current['username']!=account:reject('La identidad ya está asignada; exige desvinculación administrativa expresa',409)
  existing=db.execute('SELECT participant_id FROM bindings WHERE username=?',(account,)).fetchone()
  if existing and existing['participant_id']!=data.participant_id:reject('La cuenta EPE ya pertenece a otra identidad de Campus',409)
  db.execute('INSERT OR IGNORE INTO bindings(participant_id,username,created_at) VALUES (?,?,?)',(data.participant_id,account,int(time.time())))
 return {'bound':True,'participant_id':data.participant_id,'username':account}

@router.get('/admin/',response_class=HTMLResponse)
def teacher_panel(ok=Depends(admin_auth)):
 html_page="""<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
 <title>Empresas EPE · Identidades LTI</title><style>body{font:16px system-ui;max-width:1100px;margin:auto;padding:24px;background:#f3f6fb;color:#193452}table{width:100%;border-collapse:collapse;background:white}th,td{border:1px solid #d9e1e8;padding:8px}select,button{padding:8px}button{background:#145d83;color:white;border:0;border-radius:5px}small{color:#536777}.panel{background:white;padding:18px;margin:18px 0;border-radius:12px}</style>
 <h1>Empresa en el Aula · Asignación de identidades LTI</h1>
 <p>Los alumnos deben abrir primero la herramienta desde Campus. Después selecciona la cuenta EPE del equipo que corresponda y pulsa <b>Vincular identidad</b>.</p>
 <p><small>Una vinculación no puede transferirse a otra identidad automáticamente. La pertenencia a los grupos Moodle no se importa de NRPS.</small></p>
 <div class="panel" id="status">Consultando las identidades y empresas…</div><div class="panel" id="table"></div>
 <script src="/lti/admin/panel.js" defer></script></html>"""
 return HTMLResponse(html_page,headers={'Cache-Control':'no-store','Content-Security-Policy':"default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'self'"})

@router.get('/admin/panel.js')
def teacher_script(ok=Depends(admin_auth)):
 js=r"""async function main(){const status=document.getElementById('status');const board=document.getElementById('table');
 const esc=x=>String(x??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
 async function draw(){const r=await fetch('/lti/admin/roster',{cache:'no-store'});if(!r.ok)throw Error('No hay autorización del panel docente');
 const data=await r.json();let used=new Set(data.campus.map(x=>x.username).filter(Boolean));
 board.innerHTML='<table><tr><th>Alumno de Campus</th><th>Curso</th><th>Cuenta ERP / Empresa</th><th>Acción</th></tr>'+data.campus.map(p=>'<tr><td>'+esc(p.display)+'</td><td>'+esc(p.context_id)+'</td><td>'+(p.username?esc(p.username):'<select data-id="'+p.id+'"><option value="">Elegir una cuenta sin asignar</option>'+data.erp_accounts.filter(x=>!used.has(x.username)).map(x=>'<option value="'+esc(x.username)+'">'+esc(x.team)+' · '+esc(x.display)+' ('+esc(x.username)+')</option>').join('')+'</select>')+'</td><td>'+(p.username?'Vinculada':'<button data-bind="'+p.id+'">Vincular identidad</button>')+'</td></tr>').join('')+'</table>';
 for(const button of board.querySelectorAll('button[data-bind]'))button.onclick=async()=>{const id=Number(button.dataset.bind);const select=board.querySelector('select[data-id="'+id+'"]');if(!select.value)return;
 const response=await fetch('/lti/admin/bind',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({participant_id:id,username:select.value})});
 const result=await response.json();status.textContent=response.ok?'Asignación registrada. El alumno ya puede reabrir EPE desde Campus.':('Error: '+JSON.stringify(result));if(response.ok)await draw();};
 status.textContent=data.campus.length?'Identidades de Campus reconocidas: '+data.campus.length+'. Cuentas ERP: '+data.erp_accounts.length+'.':'Todavía no se ha producido ningún lanzamiento LTI. Abre la herramienta con una cuenta de prueba.';}
 try{await draw()}catch(e){status.textContent=e.message;}}main();"""
 return Response(js,media_type='application/javascript',headers={'Cache-Control':'no-store'})


def private_key(cfg):
 p=Path(cfg['PRIVATE_KEY_FILE'])
 if not p.is_file():raise HTTPException(503,'Falta clave privada LTI; generar con openssl en /etc/epe')
 return serialization.load_pem_private_key(p.read_bytes(),password=None)

@router.get('/.well-known/jwks.json')
def jwks():
 from cryptography.hazmat.primitives.asymmetric import rsa
 from jwt.utils import base64url_encode
 cfg=settings();key=private_key(cfg).public_key()
 if not isinstance(key,rsa.RSAPublicKey):reject('Solo RSA para LTI',503)
 n=key.public_numbers()
 enc=lambda x:base64url_encode(x.to_bytes((x.bit_length()+7)//8,'big')).decode()
 return {'keys':[{'kty':'RSA','kid':'epe-lti-key-1','alg':'RS256','use':'sig','n':enc(n.n),'e':enc(n.e)}]}


def access_token(scope):
 cfg=settings();now=int(time.time())
 body={'iss':cfg['CLIENT_ID'],'sub':cfg['CLIENT_ID'],'aud':cfg['TOKEN_URL'],'iat':now,'exp':now+180,'jti':secrets.token_urlsafe(24)}
 assertion=jwt.encode(body,private_key(cfg),algorithm='RS256',headers={'kid':'epe-lti-key-1'})
 response=httpx.post(cfg['TOKEN_URL'],data={'grant_type':'client_credentials','client_assertion_type':'urn:ietf:params:oauth:client-assertion-type:jwt-bearer','client_assertion':assertion,'scope':scope},timeout=8,follow_redirects=False)
 response.raise_for_status();data=response.json()
 if data.get('token_type','').lower()!='bearer' or not data.get('access_token'):raise ValueError('Campus no ha entregado token de servicio')
 return data['access_token']

@router.get('/admin/remote-members')
def remote_members(context_id:str,ok=Depends(admin_auth)):
 cfg=settings()
 with connection() as db:r=db.execute('SELECT memberships FROM services WHERE context_id=?',(context_id,)).fetchone()
 if not r or not r['memberships']:reject('Campus no ha habilitado NRPS en ese curso')
 url=r['memberships']
 if not allowed_moodle_url(url,cfg):reject('Destino NRPS no autorizado')
 res=httpx.get(url,headers={'Authorization':'Bearer '+access_token(NRPS),'Accept':'application/vnd.ims.lti-nrps.v2.membershipcontainer+json'},timeout=10,follow_redirects=False)
 res.raise_for_status()
 return {'members':[{k:v for k,v in m.items() if k in ('user_id','name','given_name','family_name','roles','email')} for m in res.json().get('members',[])], 'note':'La pertenencia a grupos Moodle no está garantizada en NRPS; se asigna explícitamente en EPE.'}

@router.post('/api/sync-portfolio')
def sync_portfolio(request:Request,unit:int,u=Depends(current_identity)):
 csrf_check(request,u)
 if os.environ.get('EPE_LTI_GRADE_MODE','disabled')!='portfolio':return {'published':False,'reason':'La publicación de notas LTI está desactivada hasta superar el piloto'}
 if not u['username']:reject('Falta asignación de empresa')
 # LTI resource is course-level: create a separate Moodle column for each portfolio unit.
 # This endpoint is best effort; failures do not change local evidence or grades.
 if not 1<=unit<=7:reject('Unidad fuera de rango')
 from .unified import modules
 m=modules[unit]
 with m.conn() as db:
  student=db.execute('SELECT id,team_id FROM users WHERE username=?',(u['username'],)).fetchone()
  if not student:reject('Usuario sin empresa')
  score=m.scores(db,dict(student))
 if not score['portfolio_complete']:return {'published':False,'reason':'Portafolio pendiente'}
 result=send_grade(u,unit,'portfolio',score['portfolio'])
 return {'published':True,'grade':score['portfolio'],'lineitem':result}


def send_grade(u,unit,kind,score):
 cfg=settings();ctx=u['context_id']
 with connection() as db:
  service=db.execute('SELECT lineitems,service_versions,resource_link_id FROM services WHERE context_id=?',(ctx,)).fetchone()
  line=db.execute('SELECT lineitem_url FROM grade_lines WHERE context_id=? AND unit=? AND kind=?',(ctx,unit,kind)).fetchone()
 if not service or not service['lineitems']:reject('Campus no ha habilitado AGS en este curso')
 scopes=json.loads(service['service_versions'])
 if AGS+'score' not in scopes or AGS+'lineitem' not in scopes:reject('Campus no ha autorizado los servicios AGS necesarios')
 token=access_token(AGS+'score '+AGS+'lineitem')
 url=service['lineitems']
 if not allowed_moodle_url(url,cfg):reject('Dirección AGS no autorizada')
 if line:line_url=line['lineitem_url']
 else:
  data={'label':f'EPE · U{unit} · Portafolio LTI','scoreMaximum':10,'resourceId':f'epe-u{unit}-{kind}','tag':'epe-portfolio','resourceLinkId':service['resource_link_id']}
  res=httpx.post(url,json=data,headers={'Authorization':'Bearer '+token,'Content-Type':'application/vnd.ims.lis.v2.lineitem+json','Accept':'application/vnd.ims.lis.v2.lineitem+json'},timeout=10,follow_redirects=False)
  res.raise_for_status();line_url=res.json().get('id','')
  if not allowed_moodle_url(line_url,cfg):reject('Campus devolvió un identificador AGS no permitido')
  with connection() as db:
   db.execute('INSERT OR IGNORE INTO grade_lines(context_id,unit,kind,lineitem_url) VALUES(?,?,?,?)',(ctx,unit,kind,line_url))
 if not allowed_moodle_url(line_url,cfg):reject('Destino de notas no autorizado')
 payload={'timestamp':datetime.now(timezone.utc).isoformat(),'scoreGiven':score,'scoreMaximum':10,'activityProgress':'Completed','gradingProgress':'FullyGraded','userId':u['subject']}
 res=httpx.post(line_url.rstrip('/')+'/scores',json=payload,headers={'Authorization':'Bearer '+token,'Content-Type':'application/vnd.ims.lis.v1.score+json'},timeout=10,follow_redirects=False)
 res.raise_for_status()
 return line_url
