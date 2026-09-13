"""Cloud BigQuery API metadata inventory after the user's Google authorization.
No SQL, table data, IAM changes, credentials, or row-level records are exported.
"""
from pathlib import Path
from datetime import datetime,timezone
import json,re,subprocess
import google.auth
from google.auth.transport.requests import AuthorizedSession
from google.cloud import bigquery

P=Path(__file__).resolve().parent;PROJECT='wajenigeria'

def main():
    credentials,_=google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform','https://www.googleapis.com/auth/userinfo.email'])
    session=AuthorizedSession(credentials)
    response=session.get('https://www.googleapis.com/oauth2/v2/userinfo',timeout=30)
    if response.status_code!=200:raise RuntimeError('ADC identity verification failed')
    account=response.json().get('email','')
    active=subprocess.run(['gcloud','auth','list','--filter=status:ACTIVE','--format=value(account)'],capture_output=True,text=True,check=True).stdout.strip()
    if not account.endswith('@afuruika.net') or account!=active:
        raise RuntimeError('ADC and designated active enterprise account do not match')
    client=bigquery.Client(project=PROJECT,credentials=credentials)
    datasets=list(client.list_datasets(project=PROJECT))
    if not datasets:raise RuntimeError('No datasets returned; independent project/IAM verification required')
    inventory=[];table_inventory=[];field_inventory=[];errors=[]
    for item in datasets:
        ds=client.get_dataset(item.reference)
        inventory.append({'project':PROJECT,'dataset':ds.dataset_id,'location':ds.location})
        try:tables=list(client.list_tables(ds.reference))
        except Exception as e:
            errors.append({'dataset':ds.dataset_id,'stage':'list_tables','error_type':type(e).__name__});continue
        for t in tables:
            table_inventory.append({'dataset':ds.dataset_id,'table':t.table_id,'type':t.table_type})
            if ds.dataset_id!='origin_hfyl' or not re.search(r'(game|bet|reward|event|user|order|pay|withdraw|asset)',t.table_id,re.I):continue
            try:detail=client.get_table(t.reference)
            except Exception as e:
                errors.append({'dataset':ds.dataset_id,'table':t.table_id,'stage':'get_table','error_type':type(e).__name__});continue
            def fields(ff,prefix=''):
                for f in ff:
                    name=prefix+f.name
                    field_inventory.append({'dataset':ds.dataset_id,'table':t.table_id,'field_path':name,'type':f.field_type,'mode':f.mode})
                    fields(f.fields,name+'.')
            fields(detail.schema)
    receipt={'collected_at':datetime.now(timezone.utc).isoformat(),'project':PROJECT,'principal_domain':'afuruika.net','enterprise_identity_matched':True,'method':'Cloud BigQuery API; dataset/table metadata only','business_queries':0,'datasets':inventory,'tables':table_inventory,'fields':field_inventory,'access_issues':errors}
    path=P/'metadata-inventory.json'
    if path.exists():raise RuntimeError('Metadata snapshot already exists; choose a dated new run rather than overwrite')
    path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
    print(json.dumps({'status':'metadata_collected','datasets':len(inventory),'tables':len(table_inventory),'field_records':len(field_inventory),'access_issues':len(errors)}))

if __name__=='__main__':main()
