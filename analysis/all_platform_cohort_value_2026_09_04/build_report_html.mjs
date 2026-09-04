// Package the canonical report reader with the user's requested reference theme.
// No data or chart rendering logic is duplicated here.
import {readFileSync, writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname, resolve} from 'node:path';
import {buildPortableArtifact} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/build_portable_artifact.mjs';
import {verifyPortableArtifactStructure, verifyPortableArtifact} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/verify_portable_artifact.mjs';

const base = dirname(fileURLToPath(import.meta.url));
const artifactPath = resolve(base, 'artifact.json');
const htmlPath = resolve(base, '../../output/html/Waje-全平台用户生命周期与付费价值分析-H5自然新增重点-2026-09-04.html');
const artifact = JSON.parse(readFileSync(artifactPath, 'utf8'));
const css = readFileSync(resolve(base, 'report_theme.css'), 'utf8');
let html = buildPortableArtifact(artifact);
html = html.replace('<html lang="en"', '<html lang="zh-CN"');
html = html.replace('</head>', `<style data-waje-reference-theme="true">${css}</style></head>`);
writeFileSync(htmlPath, html);
console.log(JSON.stringify(verifyPortableArtifactStructure({artifactPath, htmlPath})));
const verification = await verifyPortableArtifact({artifactPath, htmlPath});
writeFileSync(resolve(base, 'browser_verification.json'), JSON.stringify(verification, null, 2) + '\n');
console.log(JSON.stringify(verification));
