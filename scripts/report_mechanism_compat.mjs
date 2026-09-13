// Project-scoped compatibility for evidence tables in qualitative mechanism reports.
// All upstream schema, provenance and reference checks remain active.
import {readFileSync} from 'node:fs';
import {createRequire, Module} from 'node:module';
import {resolve} from 'node:path';

export function enableMechanismTables(plugin, input) {
  if(input?.manifest?.reportContract?.type!=='mechanism') return false;
  const blocks=input.manifest.blocks||[];
  if(blocks.some(b=>b.type==='chart')||!blocks.some(b=>b.type==='table')||!blocks.some(b=>b.type==='markdown'))return false;
  const filename=resolve(plugin,'mcp/server.cjs');
  const require=createRequire(import.meta.url);
  const before='if (surface === "report" && !chartBlockCount) {';
  const after='if (surface === "report" && !chartBlockCount && !(manifest.reportContract?.type === "mechanism" && manifest.blocks.some(b => b.type === "table") && manifest.blocks.some(b => b.type === "markdown"))) {';
  const original=readFileSync(filename,'utf8');
  if(original.split(before).length!==2)throw new Error('Mechanism-report compatibility requires review for this plugin version.');
  const module=new Module(filename);
  module.filename=filename;
  module.paths=Module._nodeModulePaths(resolve(plugin,'mcp'));
  module._compile(original.replace(before,after),filename);
  module.loaded=true;
  require.cache[filename]=module;
  return true;
}
