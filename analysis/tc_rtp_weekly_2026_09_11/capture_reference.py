#!/usr/bin/env python3
"""Capture the exact Lark reference revision without storing credentials."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
URL="https://ksg964l11fam.sg.larksuite.com/wiki/O4wuw0DsxiACgxkf5XAl6RTHgYO?from=from_copylink"
env={"LARKSUITE_CLI_NO_UPDATE_NOTIFIER":"1","LARKSUITE_CLI_NO_SKILLS_NOTIFIER":"1"}
base=["/Users/robin/.local/node/bin/lark-cli"]
node=subprocess.run(base+["wiki","+node-get","--node-token",URL,"--as","user","--format","json"],capture_output=True,text=True,check=True,env={**__import__('os').environ,**env})
doc=subprocess.run(base+["docs","+fetch","--doc",URL,"--doc-format","xml","--detail","simple","--as","user","--format","json"],capture_output=True,text=True,check=True,env={**__import__('os').environ,**env})
node_text=node.stdout[node.stdout.find('{'):]
node_json=json.loads(node_text);doc_json=json.loads(doc.stdout)
(ROOT/"reference").mkdir(parents=True,exist_ok=True)
(ROOT/"reference"/"wiki-node.json").write_text(json.dumps(node_json,ensure_ascii=False,indent=2))
(ROOT/"reference"/"report-revision-48.json").write_text(json.dumps(doc_json,ensure_ascii=False,indent=2))
content=doc_json["data"]["document"]["content"]
manifest={"captured_at":datetime.now(timezone.utc).isoformat(),"url":URL,"node_token":node_json["data"]["node_token"],"document_id":doc_json["data"]["document"]["document_id"],"revision_id":doc_json["data"]["document"]["revision_id"],"title":node_json["data"]["title"],"content_sha256":hashlib.sha256(content.encode()).hexdigest()}
(ROOT/"reference"/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps(manifest,ensure_ascii=False))
