"""Tests use disposable SQLITE files. Never operate on course production databases."""
import os,sys,pathlib,tempfile,subprocess,unittest,json,base64
from fastapi.testclient import TestClient
ROOT=pathlib.Path(__file__).resolve().parents[1]
class IntegrationTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='epe-integration-test-')
  os.environ['EPE_COURSE_DATA']=cls.tmp.name
  os.environ['EPE_ADMIN_PASSWORD']='Test_Profesor_Unique_2233'
  os.environ['EPE_ALLOWED_ORIGINS']='http://testserver,http://localhost:8000'
  sys.path.insert(0,str(ROOT))
  from runtime import unified
  from runtime import manage
  cls.mod=unified
  args=type('Args',(),dict(equipos=2,tamano=4,tamanos='4,5',salida=str(pathlib.Path(cls.tmp.name)/'credentials.csv')))()
  manage.create(args)
  cls.client=TestClient(cls.mod.app,base_url="https://erp.ejemplo.org")
  with open(args.salida,encoding='utf-8-sig') as f:
   import csv
   cls.cred={r['Usuario']:r['Contraseña'] for r in csv.DictReader(f,delimiter=';')}
 def test_lti_signed_launch_mapping_and_session(self):
  """OIDC must check signatures, nonce, deployment and one-use state before company access."""
  import jwt,httpx,unittest.mock
  from cryptography.hazmat.primitives.asymmetric import rsa
  from cryptography.hazmat.primitives import serialization
  from urllib.parse import urlsplit,parse_qs
  key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
  path=pathlib.Path(self.tmp.name)/'lti-private.pem'
  path.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
  os.environ.update(EPE_LTI_ISSUER='https://campus.ejemplo.org',EPE_LTI_CLIENT_ID='client-123',
      EPE_LTI_DEPLOYMENT_ID='deployment-01',EPE_LTI_AUTH_URL='https://campus.ejemplo.org/mod/lti/auth.php',
      EPE_LTI_JWKS_URL='https://campus.ejemplo.org/mod/lti/certs.php',
      EPE_LTI_TOKEN_URL='https://campus.ejemplo.org/mod/lti/token.php',
      EPE_LTI_PRIVATE_KEY_FILE=str(path),EPE_PUBLIC_URL='https://erp.ejemplo.org',EPE_LTI_GRADE_MODE='disabled')
  from runtime import lti
  pub=json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
  pub.update(kid='moodle-test',use='sig',alg='RS256')
  def stub_get(url,*a,**k):
   return httpx.Response(200,json={'keys':[pub]},request=httpx.Request('GET',url))
  self.assertTrue(self.client.get('/lti/.well-known/jwks.json').json()['keys'])
  with unittest.mock.patch.object(lti.httpx,'get',side_effect=stub_get):
   req={'iss':'https://campus.ejemplo.org','login_hint':'opaque-hint','target_link_uri':'https://erp.ejemplo.org/lti/launch','client_id':'client-123'}
   r=self.client.post('/lti/login',data=req,follow_redirects=False)
   self.assertEqual(r.status_code,303,r.text)
   args=parse_qs(urlsplit(r.headers['location']).query)
   now=int(__import__('time').time())
   def payload(nonce,sub='student-001',dep='deployment-01'):
    return {'iss':req['iss'],'sub':sub,'aud':'client-123','iat':now,'exp':now+120,'nonce':nonce,
      lti.LTI+'deployment_id':dep,lti.LTI+'version':'1.3.0',lti.LTI+'message_type':'LtiResourceLinkRequest',
      lti.LTI+'resource_link':{'id':'resource-1'},lti.LTI+'context':{'id':'course-1'},
      lti.LTI+'roles':['http://purl.imsglobal.org/vocab/lis/v2/membership#Learner'],
      lti.LTI+'target_link_uri':'https://erp.ejemplo.org/lti/launch','name':'Alumno de prueba'}
   tok=jwt.encode(payload(args['nonce'][0]),key,algorithm='RS256',headers={'kid':'moodle-test'})
   result=self.client.post('/lti/launch',data={'state':args['state'][0],'id_token':tok},follow_redirects=False)
   self.assertEqual(result.status_code,303,result.text)
   self.assertIn('epe_lti_session',self.client.cookies)
   self.assertIn('pendiente',self.client.get('/lti/portal').text.lower())
   roster=self.client.get('/lti/admin/roster',headers={'Authorization':'Basic '+base64.b64encode(b'profesor:Test_Profesor_Unique_2233').decode()})
   self.assertEqual(roster.status_code,200,roster.text)
   identity=next(r for r in roster.json()['campus'] if r['subject']=='student-001')
   self.assertEqual(self.client.get('/lti/api/bootstrap?unit=1').status_code,403)
   teacher={'Authorization':'Basic '+base64.b64encode(b'profesor:Test_Profesor_Unique_2233').decode()}
   binding=self.client.post('/lti/admin/bind',headers=teacher,json={'participant_id':identity['id'],'username':'e01a01'})
   self.assertEqual(binding.status_code,200,binding.text)
   self.assertEqual(self.client.post('/lti/admin/bind',headers=teacher,json={'participant_id':identity['id'],'username':'e02a01'}).status_code,409)
   info=self.client.get('/lti/api/bootstrap?unit=1')
   self.assertEqual(info.status_code,200,info.text)
   auth={'Authorization':'Bearer '+info.json()['token']}
   self.assertEqual(self.client.get('/u1/api/me',headers=auth).json()['username'],'e01a01')
   for unit in range(1,8):
    config=self.client.get(f'/lti/app/u{unit}/portfolio/config.js')
    self.assertEqual(config.status_code,200)
    self.assertIn(f"apiBase:'/u{unit}'",config.text)
    self.assertIn('window.EPE_LTI_MODE=true',config.text)
    script=self.client.get(f'/lti/app/u{unit}/portfolio/app.js')
    self.assertEqual(script.status_code,200)
    self.assertIn('/lti/api/bootstrap',script.text)
    bridge=self.client.get(f'/lti/api/bootstrap?unit={unit}')
    self.assertEqual(bridge.status_code,200)
    student=self.client.get(f'/u{unit}/api/me',headers={'Authorization':'Bearer '+bridge.json()['token']}).json()
    self.assertEqual(student['username'],'e01a01')
    self.assertEqual(student['team_id'],1)
   self.assertEqual(self.client.get('/lti/app/u1/portfolio/../../servidor/answer_key.json').status_code,404)
   self.assertEqual(self.client.post('/lti/api/sync-portfolio?unit=1').status_code,403) # CSRF
   self.assertEqual(self.client.post('/lti/api/sync-portfolio?unit=1',headers={'X-EPE-LTI-CSRF':info.json()['csrf']}).json()['published'],False)
   self.assertEqual(self.client.post('/lti/launch',data={'state':args['state'][0],'id_token':tok}).status_code,403)
   badlogin=self.client.post('/lti/login',data=req,follow_redirects=False)
   args2=parse_qs(urlsplit(badlogin.headers['location']).query)
   bad=jwt.encode(payload(args2['nonce'][0],dep='wrong-deployment'),key,algorithm='RS256',headers={'kid':'moodle-test'})
   self.assertEqual(self.client.post('/lti/launch',data={'state':args2['state'][0],'id_token':bad}).status_code,403)

   # Moodle AGS: OAuth2 client assertion, line item and score are server-to-server.
   with lti.connection() as cx:
    cx.execute("""INSERT INTO services(context_id,lineitems,memberships,resource_link_id,service_versions,updated)
        VALUES(?,?,?,?,?,?)""",( 'course-1','https://campus.ejemplo.org/mod/lti/services.php/2/lineitems','', 'resource-1',
        json.dumps([lti.AGS+'score',lti.AGS+'lineitem']),now))
    who=dict(cx.execute('SELECT * FROM participants WHERE subject=?',('student-001',)).fetchone())
   sent=[]
   def mocked_post(url,*args,**kwargs):
    sent.append((url,kwargs.get('json'),kwargs.get('data')))
    request=httpx.Request('POST',url)
    if url.endswith('token.php'):return httpx.Response(200,json={'token_type':'Bearer','access_token':'test-oauth-access'},request=request)
    if url.endswith('/lineitems'):return httpx.Response(201,json={'id':url+'/99'},request=request)
    if url.endswith('/99/scores'):return httpx.Response(200,json={},request=request)
    return httpx.Response(400,json={},request=request)
   with unittest.mock.patch.object(lti.httpx,'post',side_effect=mocked_post):
    self.assertEqual(lti.send_grade(who,1,'portfolio',8.5),'https://campus.ejemplo.org/mod/lti/services.php/2/lineitems/99')
    self.assertEqual(lti.send_grade(who,1,'portfolio',9.0),'https://campus.ejemplo.org/mod/lti/services.php/2/lineitems/99')
   self.assertEqual(sum(x[0].endswith('/lineitems') for x in sent),1)
   self.assertEqual([x[1]['scoreGiven'] for x in sent if x[0].endswith('/scores')],[8.5,9.0])

 @classmethod
 def tearDownClass(cls):
  cls.client.close();cls.tmp.cleanup()
 def login(self,unit,username):
  r=self.client.post(f'/u{unit}/api/login',json={'username':username,'password':self.cred[username]})
  self.assertEqual(r.status_code,200,r.text)
  return {'Authorization':'Bearer '+r.json()['token']}
 def test_health_and_roster(self):
  r=self.client.get('/api/health');self.assertEqual(r.status_code,200);self.assertEqual(r.json()['roster']['students'],9)
  for n in range(1,8):self.assertEqual(self.client.get(f'/u{n}/api/health').status_code,200)
 def test_shared_company_and_no_grade_leaks(self):
  auth=self.login(4,'e01a01')
  renamed=self.client.post('/u4/api/company',headers=auth,json={'name':'Oficina Alfa Canarias, SL'})
  self.assertEqual(renamed.status_code,200,renamed.text)
  for u in range(1,8):
   r=self.client.get(f'/u{u}/api/me',headers=self.login(u,'e01a01'))
   self.assertEqual(r.json()['team'],'Oficina Alfa Canarias, SL')
  report=self.client.get('/u5/api/report',headers=self.login(5,'e01a01')).json()
  self.assertFalse(report['final_complete'])
 def test_documents_and_links_tenant_isolation(self):
  u4=self.mod.modules[4]
  auth4=self.login(4,'e01a01')
  auth5=self.login(5,'e01a02')
  # Complete guided activities server-side, not by spoofing the browser.
  for task in u4.TASKS['guided']:
   res=self.client.post('/u4/api/guided/'+task['id'],json={'answers':task['solutions']},headers=auth4)
   self.assertEqual(res.status_code,200,(task['id'],res.text))
  task=u4.TASKS['graded'][0]
  answers=u4.KEY['tasks'][task['id']]
  res=self.client.post(f'/u4/api/tasks/{task["id"]}/submit',headers=auth4,json={'answers':answers,'coverage':''})
  self.assertEqual(res.status_code,200,res.text);self.assertEqual(res.json()['score'],10)
  docs=self.client.get('/u5/api/erp/course-documents',headers=auth5)
  self.assertEqual(docs.status_code,200,docs.text)
  match=[d for d in docs.json()['documents'] if d['unit']==4 and d['task_id']==task['id']]
  self.assertEqual(len(match),1)
  target=self.mod.modules[5].TASKS['graded'][0]['id']
  payload={'source_doc_id':match[0]['doc_id'],'target_task_id':target}
  self.assertEqual(self.client.post('/u5/api/erp/course-links',headers=auth5,json=payload).status_code,200)
  linklist=self.client.get('/u5/api/erp/course-links',headers=auth5).json()['links']
  self.assertEqual(linklist[0]['source_doc_id'],payload['source_doc_id'])
  outsider=self.login(5,'e02a01')
  self.assertEqual(self.client.get('/u5/api/erp/course-documents',headers=outsider).json()['count'],0)
  self.assertEqual(self.client.get('/u5/api/erp/course-documents/'+payload['source_doc_id'],headers=outsider).status_code,404)
  self.assertEqual(self.client.post('/u5/api/erp/course-links',headers=outsider,json=payload).status_code,400)
  # Cross-unit report deliberately stays pending without examinations and teacher observations.
  teacher='Basic '+base64.b64encode(b'profesor:Test_Profesor_Unique_2233').decode()
  grade=self.client.get('/api/admin/course-report',headers={'Authorization':teacher})
  self.assertEqual(grade.status_code,200,grade.text);self.assertEqual(len(grade.json()['students']),9)
  self.assertIsNone(grade.json()['students'][0]['weighted_grade'])
  self.assertEqual(self.client.get('/api/admin/course-report').status_code,401)
 def test_mismatched_mapping_is_rejected(self):
  db=self.mod.modules[3].DB
  import sqlite3
  with sqlite3.connect(db) as cx:cx.execute('UPDATE users SET team_id=2 WHERE username="e01a01"')
  from runtime import course_core as core
  with self.assertRaisesRegex(ValueError,'Rosters incompatibles'):core.roster_check(True)
  with sqlite3.connect(db) as cx:cx.execute('UPDATE users SET team_id=1 WHERE username="e01a01"')
if __name__=='__main__':unittest.main(verbosity=2)
