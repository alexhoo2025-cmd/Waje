"""Bounded resident worker transport. Input disabled unless explicitly requested."""
import json,selectors,subprocess,uuid
from pathlib import Path

class Session:
    def __init__(self,allow_input=False):
        self.allow_input=allow_input
        self.p=subprocess.Popen([str(Path(__file__).with_name('native_fast'))]+(['--allow-input'] if allow_input else []),stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
        self.sel=selectors.DefaultSelector();self.sel.register(self.p.stdout,selectors.EVENT_READ)
    def call(self,op,**kw):
        if op in ('click','click_recovery','type_text','press_return') and not self.allow_input:raise PermissionError('input_disabled')
        rid=uuid.uuid4().hex
        self.p.stdin.write(json.dumps(dict(op=op,request_id=rid,**kw))+'\n');self.p.stdin.flush()
        if not self.sel.select(8):raise RuntimeError('native_timeout')
        r=json.loads(self.p.stdout.readline())
        if r.get('request_id')!=rid or r.get('status')!='ok':raise RuntimeError(r.get('reason','invalid_reply'))
        return r
    def close(self):
        self.p.terminate()
        try:self.p.wait(timeout=3)
        except subprocess.TimeoutExpired:self.p.kill();self.p.wait()
        self.sel.close()
