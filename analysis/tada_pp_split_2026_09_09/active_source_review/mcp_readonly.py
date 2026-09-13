"""Authenticated official-MCP transport, restricted to approved read-only tools.
Credentials remain in Google's isolated credential store and process memory.
"""
from pathlib import Path
import json,google.auth
from google.auth.transport.requests import AuthorizedSession
from mcp_auth_probe import unpack,CREDENTIALS,ENDPOINT
ALLOWED={'list_dataset_ids','get_dataset_info','list_table_ids','get_table_info','execute_sql_readonly'}
class Client:
 def __init__(self):
  credentials,_=google.auth.load_credentials_from_file(CREDENTIALS)
  self.session=AuthorizedSession(credentials);self.n=0
  r=self.session.get('https://www.googleapis.com/oauth2/v2/userinfo',timeout=30)
  if r.status_code!=200 or r.json().get('email')!='robin@afuruika.net':raise RuntimeError('enterprise identity verification failed')
 def call(self,name,args):
  if name not in ALLOWED or args.get('projectId')!='wajenigeria':raise ValueError('readonly project boundary')
  self.n+=1
  # Preserve the official advertised schema. Compatibility probes did not
  # resolve the endpoint's empty-project error; do not ship guessed aliases.
  wire=args
  r=self.session.post(ENDPOINT,headers={'Accept':'application/json, text/event-stream','x-goog-user-project':'wajenigeria','MCP-Protocol-Version':'2025-03-26'},json={'jsonrpc':'2.0','id':self.n,'method':'tools/call','params':{'name':name,'arguments':wire}},timeout=180)
  body=unpack(r)
  if r.status_code!=200 or 'error' in body:raise RuntimeError(json.dumps({'status':r.status_code,'body':body},ensure_ascii=False))
  result=body.get('result',{})
  if result.get('isError'):raise RuntimeError(json.dumps(result,ensure_ascii=False))
  if 'structuredContent' in result:return result['structuredContent']
  parts=[c.get('text','') for c in result.get('content',[]) if c.get('type')=='text']
  try:return json.loads('\n'.join(parts))
  except ValueError:return {'text':'\n'.join(parts)}

if __name__=='__main__':
 p=Path(__file__).resolve().parent;c=Client()
 datasets=c.call('list_dataset_ids',{'projectId':'wajenigeria','pageSize':50});(p/'live-datasets.json').write_text(json.dumps(datasets,ensure_ascii=False,indent=2));print('Dataset inventory succeeded')
 tables=c.call('list_table_ids',{'projectId':'wajenigeria','datasetId':'origin_hfyl','pageSize':5000});(p/'live-tables.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2));print('Table inventory succeeded')
 for name in ['realtime_edw_user_version_daily','view_user_version_daily','view_metaevent_active_events','user_xlid']:
  result=c.call('get_table_info',{'projectId':'wajenigeria','datasetId':'origin_hfyl','tableId':name});(p/(name+'.metadata.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2));print(name,json.dumps(result,ensure_ascii=False)[:11000])
