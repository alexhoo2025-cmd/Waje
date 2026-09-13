import fs from "node:fs/promises";
try{
  const {FileBlob,SpreadsheetFile}=await import("@oai/artifact-tool");
  console.log("module-ok");
  for(const file of [
    "analysis/top30_tc_uidlog_2026_09_10/revisions/pre-remove-summary-scan/9月10日资产变动汇总_前30.xlsx",
    "outputs/019fc549-3241-7d52-90f5-0b39c2e03530/9月10日资产变动汇总_前30.xlsx"
  ]){
    try{const b=await FileBlob.load(file);console.log("blob-ok",file,(await fs.stat(file)).size);const w=await SpreadsheetFile.importXlsx(b);console.log("import-ok",file,w.worksheets.items.length);}
    catch(e){console.log("import-failed",file,e?.name,e?.message,String(e));}
  }
}catch(e){console.log("module-failed",e?.name,e?.message,String(e));}
