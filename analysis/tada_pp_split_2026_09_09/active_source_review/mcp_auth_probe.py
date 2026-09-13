"""Verify the user-approved isolated ADC against the official BigQuery MCP.
Never prints or writes tokens, credentials, cookies, or request headers.
"""
from pathlib import Path
import json
import google.auth
from google.auth.transport.requests import AuthorizedSession

P=Path(__file__).resolve().parent
ENDPOINT='https://bigquery.googleapis.com/mcp'
CREDENTIALS='/Users/robin/.config/gcloud-waje-readonly/application_default_credentials.json'
def unpack(response):
    if 'text/event-stream' in response.headers.get('content-type',''):
        events=[json.loads(line[5:].strip()) for line in response.text.splitlines() if line.startswith('data:')]
        return next((e for e in reversed(events) if 'result' in e or 'error' in e),{})
    try:return response.json()
    except ValueError:return {'unparsed_response':response.text[:500]}
def main():
    creds,_=google.auth.load_credentials_from_file(CREDENTIALS)
    session=AuthorizedSession(creds)
    identity=session.get('https://www.googleapis.com/oauth2/v2/userinfo',timeout=30)
    if identity.status_code!=200:raise RuntimeError('Google identity verification failed')
    email=identity.json().get('email','')
    if email!='robin@afuruika.net':raise RuntimeError('Authorized identity is not the designated enterprise account')
    headers={'Accept':'application/json, text/event-stream','x-goog-user-project':'wajenigeria'}
    def rpc(method,params,rid):
        res=session.post(ENDPOINT,json={'jsonrpc':'2.0','id':rid,'method':method,'params':params},headers=headers,timeout=45)
        if res.headers.get('Mcp-Session-Id'):headers['Mcp-Session-Id']=res.headers['Mcp-Session-Id']
        return res.status_code,unpack(res)
    status,init=rpc('initialize',{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'waje-readonly-verification','version':'1.0'}},1)
    receipt={'identity_verified':True,'principal_domain':'afuruika.net','endpoint':ENDPOINT,'initialize_http_status':status,'initialize':init,'business_queries':0}
    if status==200 and 'result' in init:
        headers['MCP-Protocol-Version']=init['result'].get('protocolVersion','2025-03-26')
        session.post(ENDPOINT,json={'jsonrpc':'2.0','method':'notifications/initialized'},headers=headers,timeout=30)
        code,tools=rpc('tools/list',{},2);receipt.update(tools_http_status=code,tool_names=[t['name'] for t in tools.get('result',{}).get('tools',[])])
        if 'result' in tools:(P/'mcp-tools.json').write_text(json.dumps(tools['result'],ensure_ascii=False,indent=2))
        else:receipt['tools_error']=tools
    (P/'mcp-auth-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
    print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
