"""Offline regression tests: never require credentials or make network requests."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import claude_bridge as cb
from tools import claude_pipeline as cp


def task(**overrides):
    t = {"goal": "summarize fixture", "role": "analyst", "parent_complexity": "complex", "delegation_reason": "独立核验复杂任务的一项结论", "window": "synthetic", "acceptance": ["引用原文"], "evidence": [{"id": "e1", "text": "这是完整的模拟证据，不代表生产数据。"}]}
    t.update(overrides)
    return t


def result(**overrides):
    r = {"status": "completed", "summary": "模拟结论", "findings": [{"text": "事实", "kind": "fact", "evidence_ids": ["e1"], "quote": "这是完整的模拟证据，不代表生产数据。"}], "patches": [], "assumptions": [], "checks": [], "open_questions": []}
    r.update(overrides)
    return r


class FakeProcess:
    pid = 987654
    returncode = 0

    def __init__(self, response=None, error="", code=0):
        self.response = response if response is not None else {"structured_output": result(), "usage": {"input_tokens": 10}, "modelUsage": {"fixture-model": {}}, "total_cost_usd": 0.01}
        self.error = error
        self.returncode = code

    def communicate(self, *a, **kw):
        return json.dumps(self.response), self.error


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = copy.deepcopy(cb.read(cb.CONFIG_PATH))
        self.b = cb.Bridge(Path(self.temp.name), self.config)

    def tearDown(self):
        self.temp.cleanup()

    def submit(self, **kw):
        return self.b.submit(task(**kw), background=False)

    def run_fake(self, tid, processes):
        with patch.object(cb, "credentials", return_value={"ANTHROPIC_BASE_URL":"https://fixture.invalid", "ANTHROPIC_AUTH_TOKEN":"fixture"}), patch.object(cb.subprocess, "Popen", side_effect=processes) as popen:
            self.b.run(tid)
        return popen

    def test_route_and_simple_skip(self):
        self.assertEqual(cb.route(task(role="organizer"), self.config), "haiku")
        self.assertEqual(cb.route(task(complexity="complex"), self.config), "opus")
        self.assertEqual(cb.route(task(risk="high"), self.config), "opus")
        self.assertIsNone(cb.route(task(complexity="simple",parent_complexity="simple"), self.config))
        self.assertEqual(self.b.get(self.submit(complexity="simple",parent_complexity="simple"))["status"], "skipped_direct")

    def test_routine_and_unspecified_never_dispatch(self):
        for kwargs in ({"origin":"scheduled"},{"workflow":"play_reviews"},{"workflow":"weekly_intelligence"},{"workflow":"meeting_minutes"},{"workflow":"config_changes"},{"parent_complexity":"normal"},{"delegation_reason":""},{"parent_complexity":"simple","force_delegate":True}):
            with patch.object(cb.subprocess,"Popen") as p:
                tid=self.submit(**kwargs)
            p.assert_not_called();self.assertEqual(self.b.get(tid)["status"],"skipped_direct")
        minimal=task();minimal.pop("parent_complexity");minimal.pop("delegation_reason")
        self.assertIsNone(cb.route(minimal,self.config))

    def test_disabled_and_dedup(self):
        tid = self.submit()
        self.assertEqual(tid, self.submit())
        self.config["enabled"] = False
        self.assertEqual(self.b.get(self.submit(goal="another"))["status"], "skipped_direct")

    def test_context_requirements_and_pii(self):
        for t in (task(acceptance=[]), task(evidence=[]), task(evidence=[{"id":"e1","text":"a@example.com"}]), task(targets=["../outside.py"]), task(evidence=[{"id":"e1","text":"a"},{"id":"e1","text":"b"}])):
            with self.assertRaises(ValueError): self.b.submit(t, background=False)
        cb.assert_safe("task-aaaaaaaaaaaaaaaaaaaa")

    def test_context_limit(self):
        with self.assertRaises(ValueError): self.submit(goal="x"*25000)

    def test_parallel_admission_and_target_ownership(self):
        a, b, c = [self.submit(goal=str(i)) for i in range(3)]
        self.assertTrue(self.b.claim(a)); self.assertTrue(self.b.claim(b)); self.assertFalse(self.b.claim(c))
        self.b.finish(a,"result_ready",{},result()); self.b.finish(b,"result_ready",{},result())
        self.assertTrue(self.b.claim(c))
        x = self.submit(goal="x", targets=["analysis/synthetic-no-file.py"])
        y = self.submit(goal="y", targets=["analysis/synthetic-no-file.py"])
        self.assertTrue(self.b.claim(x)); self.b.finish(x,"result_ready",{},result())
        self.assertFalse(self.b.claim(y))
        self.b.collect(x,"accepted","fixture review")
        self.assertTrue(self.b.claim(y))

    def test_maximum_four_when_healthy(self):
        for i in range(2):
            tid=self.submit(goal="healthy"+str(i)); self.b.finish(tid,"result_ready",{},result())
        ids=[self.submit(goal="parallel"+str(i)) for i in range(5)]
        self.assertEqual([self.b.claim(i) for i in ids],[True,True,True,True,False])

    def test_dependency_acceptance(self):
        a = self.submit(goal="first"); b = self.submit(goal="second",depends_on=[a])
        self.assertFalse(self.b.claim(b))
        self.b.finish(a,"result_ready",{},result()); self.assertFalse(self.b.claim(b))
        self.b.collect(a,"accepted","verified"); self.assertTrue(self.b.claim(b))

    def test_dependency_failure(self):
        a=self.submit(goal="first"); b=self.submit(goal="second",depends_on=[a]); self.b.finish(a,"failed",{})
        self.b.run(b); self.assertEqual(self.b.get(b)["status"],"blocked")

    def test_cancel_queued_and_running(self):
        a=self.submit(); self.b.cancel(a); self.b.run(a); self.assertEqual(self.b.get(a)["status"],"cancelled")
        b=self.submit(goal="running");self.b.claim(b);self.b.cancel(b)
        self.assertEqual(self.b.get(b)["status"],"running")
        self.b.finish(b,"result_ready",{},result()); self.assertEqual(self.b.get(b)["status"],"cancelled")

    def test_schema_and_evidence_validation(self):
        spec=cb.normalize_task(task(),self.config)
        for r in ({}, result(findings=[{"text":"bad","kind":"fact","evidence_ids":["e1"],"quote":"invented"}]), result(findings=[{"text":"bad","kind":"inference","evidence_ids":["unknown"],"quote":""}])):
            with self.assertRaises(ValueError):self.b.check_result(spec,r)

    def test_late_cancel_keeps_completed_result_available(self):
        tid=self.submit();self.b.finish(tid,"result_ready",{},result())
        self.b.cancel(tid);self.assertEqual(self.b.get(tid)["status"],"result_ready")
        self.b.collect(tid,"rejected","late result reviewed and rejected")

    def test_tool_free_success_and_usage(self):
        tid=self.submit(); popen=self.run_fake(tid,[FakeProcess()]); command=popen.call_args.args[0]
        self.assertIn("--safe-mode",command);self.assertEqual(command[command.index("--tools")+1],"")
        self.assertIn("--no-session-persistence",command);self.assertIn("--strict-mcp-config",command)
        self.assertNotIn("--fallback-model",command);self.assertNotIn("--max-budget-usd",command)
        self.assertEqual(self.b.get(tid)["status"],"result_ready")

    def test_auth_no_retry(self):
        tid=self.submit(); popen=self.run_fake(tid,[FakeProcess({"is_error":True,"result":"401 authentication rejected"},code=1)])
        self.assertEqual(popen.call_count,1);self.assertEqual(self.b.status(tid)["receipt"]["reason"],"auth_required")

    def test_transient_retry(self):
        tid=self.submit(); p=self.run_fake(tid,[FakeProcess({"is_error":True,"result":"503 unavailable"},code=1),FakeProcess()])
        self.assertEqual(p.call_count,2);self.assertEqual(self.b.get(tid)["status"],"result_ready")

    def test_capability_preserving_fallback(self):
        tid=self.submit();p=self.run_fake(tid,[FakeProcess({"is_error":True,"result":"model_not_found"},code=1),FakeProcess()])
        self.assertEqual(p.call_count,2);self.assertIn(self.config["models"]["opus"],p.call_args.args[0])

    def test_timeout_terminates_group(self):
        tid=self.submit(timeout_seconds=0.001)
        fake=FakeProcess(); fake.communicate=lambda *a,**kw: (_ for _ in ()).throw(subprocess.TimeoutExpired("fixture",0))
        with patch.object(cb,"credentials",return_value={"ANTHROPIC_BASE_URL":"https://fixture.invalid", "ANTHROPIC_AUTH_TOKEN":"fixture"}),patch.object(cb.subprocess,"Popen",return_value=fake),patch.object(cb.os,"killpg") as kill:
            self.b.run(tid)
        self.assertTrue(kill.called); self.assertEqual(self.b.get(tid)["status"],"failed")

    def test_needs_context_and_revision(self):
        a=self.submit(); self.run_fake(a,[FakeProcess({"structured_output":result(status="needs_context",open_questions=["补充窗口"] )})])
        self.assertEqual(self.b.get(a)["status"],"needs_context")
        with patch.object(cb.subprocess,"Popen",return_value=FakeProcess()):
            b=self.b.revise(a,{"message":"补充了窗口"})
        self.assertEqual(self.b.get(a)["status"],"handed_back"); self.assertEqual(self.b.get(b)["model"],"sonnet")
        self.b.finish(b,"result_ready",{},result())
        with patch.object(cb.subprocess,"Popen",return_value=FakeProcess()):
            c=self.b.revise(b,{"message":"仍需深入"})
        self.assertEqual(self.b.get(c)["model"],"opus")

    def test_stale_file_and_invalid_diff(self):
        tid=self.submit(targets=["config/agent_dispatch.json"]); self.b.finish(tid,"result_ready",{},result())
        with patch.object(cb,"digest",return_value="changed"):
            with self.assertRaises(ValueError):self.b.collect(tid,"accepted","checked")
        self.b.finish(tid,"result_ready",{},result(patches=[{"path":"config/agent_dispatch.json","base_sha256":json.loads(self.b.get(tid)["spec"])["base_hashes"]["config/agent_dispatch.json"],"diff":"bad diff"}]))
        with self.assertRaises(ValueError):self.b.collect(tid,"accepted","checked")

    def test_routine_compatibility_never_invokes_bridge(self):
        with patch.object(cp,"Bridge") as factory:
            for stage in self.config["excluded_workflows"]:
                out=cp.enrich(stage,task()["evidence"],"synthetic","ok")
                self.assertEqual(out["status"],"not_run")
                self.assertEqual(out["markdown"],"")
            factory.assert_not_called()

    def test_pipeline_skips_blocked_empty_disabled(self):
        for quality,sources in [("blocked",task()["evidence"]),("ok",[])]:
            with patch.object(cp,"Bridge") as b:
                self.assertEqual(cp.enrich("play_reviews",sources,"synthetic",quality)["status"],"not_run");b.assert_not_called()

    def test_routine_hooks_removed_from_scripts(self):
        for name in ("build_play_reviews_report.py","build_weekly_intelligence_report.py","run_lark_meeting_minutes_pipeline.py","waje_config_workbook.py"):
            source=(cb.ROOT/"scripts"/name).read_text()
            self.assertNotIn("claude_pipeline",source)
            self.assertNotIn("enrich(",source)

    def test_gemini_web_and_cli_have_separate_availability(self):
        c=cb.read(cb.ROOT/"config/gemini-enterprise.json")["execution_policy"]
        self.assertTrue(c["web_agent"]["enabled_for_complex_tasks"])
        self.assertEqual(c["web_agent"]["availability"],"user_confirmed_operational")
        self.assertFalse(c["cli_normal_invocation_enabled"])

    def test_worker_cannot_fallback_to_personal_oauth(self):
        tid=self.submit()
        with patch.object(cb,"credentials",return_value={}),patch.object(cb.subprocess,"Popen") as proc:
            self.b.run(tid)
        proc.assert_not_called();self.assertEqual(self.b.status(tid)["receipt"]["reason"],"proxy_auth_not_configured")

    def test_gemini_excluded_even_with_recovery_flag(self):
        from tools.gemini_bridge import run_task
        with patch("tools.gemini_bridge.subprocess.run") as run:
            for probe in (False,True):
                r=run_task("公开最小测试","web_research",output_dir=Path(self.temp.name)/"gemini",task_id="gate-test",recovery_probe=probe)
                self.assertEqual(r["status"],"blocked_cli_excluded")
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
