#!/usr/bin/env python3
"""Run offline regression plus read back real collaboration artifacts."""
import datetime as dt
import importlib
import inspect
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.claude_bridge import Bridge,read,write


def main():
    os.environ["WAJE_CLAUDE_DISABLE"]="1"
    suite=unittest.defaultTestLoader.loadTestsFromNames(["tests.test_claude_bridge","tests.test_waje_config_workbook","tests.test_lark_meeting_minutes","tests.test_weekly_intelligence_pipeline","tests.test_weekly_intelligence"])
    capture=io.StringIO(); tests=unittest.TextTestRunner(stream=capture).run(suite)
    if not tests.wasSuccessful():raise AssertionError(capture.getvalue())
    function_count=0
    for name in ("tests.test_gemini_bridge","tests.test_gemini_model_routing","tests.test_play_reviews_pipeline"):
        module=importlib.import_module(name)
        for fname,func in inspect.getmembers(module,inspect.isfunction):
            if fname.startswith("test_"):
                with tempfile.TemporaryDirectory() as tmp:
                    func(Path(tmp)) if "tmp_path" in inspect.signature(func).parameters else func()
                function_count+=1
    from analysis.agent_collaboration_validation_2026_09_04.cohort_fixture import retention
    assert retention(1,2)==.5 and retention(1,0) is None and retention(1,None) is None
    for n,d in [(-1,2),(3,2),(1,-1)]:
        try:retention(n,d)
        except ValueError:pass
        else:raise AssertionError("invalid cohort accepted")
    b=Bridge();directory=ROOT/"analysis/agent_collaboration_validation_2026_09_04"
    initial=[b.collect(t) for t in ["task-0d1310cce30362401f96","task-e444d5a15613facb70be","task-bcd21480b40879632032"]]
    final=[b.collect(t) for t in ["task-0d1310cce30362401f96","task-a1c79133d6c89946a96b","task-aa670c0fcd7e6e511966"]]
    assert all(t["status"]=="accepted" for t in final)
    baseline=read(directory/"benchmark/baseline.json")
    def timestamp(s):return dt.datetime.fromisoformat(s)
    span=(max(timestamp(t["receipt"]["finished_at"]) for t in initial)-min(timestamp(t["created_at"]) for t in initial)).total_seconds()
    final_elapsed=[{"task_id":t["task_id"],"elapsed_seconds":t["receipt"].get("elapsed_seconds"),"status":t["status"]} for t in final]
    latest=read(directory/"latest-pipeline-validation.json")
    fixture=Path(latest["fixture"])
    report=read(fixture/"data/outputs/play_reviews/2026-09-04/report-receipt.json")
    assert report["summary"]["new_count"]==4
    assert "协作重点摘录" in (fixture/report["html"]).read_text()
    publication=read(directory/"pipeline-review-publication.json")
    assert b.collect(publication["task_id"])["status"]=="accepted"
    assert (ROOT/publication["path"]).exists()
    data={"status":"passed","unit_tests":tests.testsRun,"function_tests":function_count,"cohort_fixture_checks":6,
        "models_live_verified":["haiku","sonnet","opus"],"initial_parallel_wall_seconds":round(span,3),
        "serial_sonnet_wall_seconds":baseline["elapsed_seconds"],"initial_parallel_rubric_passes":1,"serial_rubric_passes":2,
        "final_reviewed_tasks":final_elapsed,"pipeline_metrics_preserved":True,"pipeline_analysis_published":True,
        "comparison_limit":"Three synthetic cases only. Model mix and cache conditions differ; first-pass timing excludes revision and coordinator work. No Codex-only baseline or production speedup claim.",
        "coordinator_findings":["Both first code candidates had invalid diff/context, caught before apply", "Mixed-currency RTP range was invalid; corrected after feedback", "Coordinator initially omitted trailing blank line from code context; full context supplied on second revision"],
        "generated_at":dt.datetime.now(dt.timezone.utc).isoformat()}
    write(directory/"validation.json",data)
    body=f'''# Claude 协作机制历史验证报告

当前范围已调整：以下日常集成测试属于历史v1，日常调度钩子已撤销。现仅复杂交互任务协作；Gemini网页Agent可用，本地CLI排除。最新规则以AGENTS.md为准。

**桥接、三档模型、并行、返工、代码应用和报告消费已验证。**

- 离线回归：{tests.testsRun + function_count} 项通过；候选代码另通过6个函数检查。
- 三类样例：报告摘要、代码修复、复杂RTP诊断；最终均由主Agent核验并接受。
- 真实报告构建：隔离Play夹具4条，报告保留原始数字，包含协作重点摘录；分析另经主Agent接受并写入新交付文件。
- 两份未经验收的候选补丁未应用；首次RTP混算区间判断被退回修正。模型返回成功不等于验收通过。

## 单模型串行与分工并行对照

|范围|分工并行|Sonnet串行|
|---|---:|---:|
|相同三类模拟任务，首轮墙钟时间|{span:.2f}秒|{baseline['elapsed_seconds']:.2f}秒|
|主Agent首轮验收通过|1/3|2/3|

并行首轮较快，但初轮质量并未更好；返工和主Agent工作另计。这是小样本、模型与缓存条件不同的对照，不是生产任务提速承诺，也没有测量Codex单独完成同样工作的耗时。

## 据实调整

- 保持自动并行，但由主Agent按问题验收；复杂模型不自动获得可信结论地位。
- 开发交接必须含完整相关文件内容、尾部换行和真实指纹；候选补丁需通过可应用性检查。
- 缩短重复的模型交接文本，保留结论、关键证据、候选补丁与未决项。
- 程序从模型选中的来源ID恢复完整原文，避免局部摘录丢失限定条件；新增分析仍由主Agent审核。
- Gemini通用分派关闭，企业专项保持恢复门禁；单独评估见[Gemini报告](../gemini_usage_review_2026_09_04/reviewed-report.md)。

## 可回读工件

- [代码审查与交接](reviewed-code.md)
- [实际采用的候选代码](cohort_fixture.py)
- [RTP诊断修正版](reviewed-diagnosis.md)
- [日常报告分析验收版]({Path(publication['path']).relative_to(directory.relative_to(ROOT))})
- [机器回执](validation.json)

所有测试数据均为模拟夹具。未执行生产采集、外部发布、IAM修改或云端部署变更。
'''
    (directory/"validation-report.md").write_text(body,encoding="utf-8")
    print(json.dumps({"status":"passed","tests":tests.testsRun+function_count,"fixture_checks":6,"report":str(directory/"validation-report.md")},ensure_ascii=False))


if __name__=="__main__":main()
