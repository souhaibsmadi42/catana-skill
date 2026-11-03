"""VoiceStudio client + adapter against a mock server implementing the user's OpenAPI (v0.5.7)."""
import json
import os
import subprocess
import sys
import unittest
import wave

from helpers import MockVoiceStudio, free_port_url, tmpdir, SCRIPTS
from catana_core.voice_studio import VoiceStudio, VoiceStudioError, split_text
from catana_core import providers as pv


class VoiceStudioClient(unittest.TestCase):
    def test_health_voices_and_speech(self):
        with MockVoiceStudio() as m:
            vs = VoiceStudio(base_url=m.url)
            self.assertTrue(vs.available())
            self.assertEqual(vs.voices()["voices"][0]["id"], "default")
            out = os.path.join(tmpdir(), "vo.wav")
            r = vs.speech("Modern living, redefined.", out, voice="narrator-m", instructions="warm, confident", speed=0.95)
            self.assertTrue(os.path.getsize(out) > 1000)
            with wave.open(out) as w:
                self.assertGreater(w.getnframes(), 0)
            sent = [b for (meth, path, b, _) in m.requests if path == "/v1/audio/speech"][0]
            self.assertEqual(sent["voice"], "narrator-m")
            self.assertEqual(sent["response_format"], "wav")
            self.assertEqual(sent["instructions"], "warm, confident")
            self.assertEqual(r["chunks"], 1)

    def test_long_script_is_chunked_and_joined(self):
        text = " ".join(["This sentence is part of a long voiceover script for the villa film."] * 120)  # ~8 000 chars
        self.assertGreater(len(text), 4096)
        with MockVoiceStudio() as m:
            out = os.path.join(tmpdir(), "long.wav")
            r = VoiceStudio(base_url=m.url).speech(text, out)
            self.assertGreaterEqual(r["chunks"], 2)
            for (_, path, body, _) in m.requests:
                if path == "/v1/audio/speech":
                    self.assertLessEqual(len(body["input"]), 4096)
            with wave.open(out) as w:
                self.assertAlmostEqual(w.getnframes() / w.getframerate(), 0.3 * r["chunks"], places=2)

    def test_long_script_needs_wav(self):
        with MockVoiceStudio() as m:
            with self.assertRaises(VoiceStudioError) as cm:
                VoiceStudio(base_url=m.url).speech("x. " * 3000, os.path.join(tmpdir(), "a.mp3"))
            self.assertEqual(cm.exception.category, "invalid_input")

    def test_split_text_respects_limit(self):
        chunks = split_text("Word " * 3000, 1000)
        self.assertTrue(all(len(c) <= 1000 for c in chunks))
        self.assertEqual(" ".join(chunks).split(), ("Word " * 3000).split())

    def test_invalid_inputs(self):
        with MockVoiceStudio() as m:
            vs = VoiceStudio(base_url=m.url)
            for kwargs in ({"text": "  "}, {"text": "hi", "speed": 9}, {"text": "hi", "response_format": "midi"}):
                text = kwargs.pop("text")
                with self.assertRaises(VoiceStudioError) as cm:
                    vs.speech(text, os.path.join(tmpdir(), "x.wav"), **kwargs)
                self.assertEqual(cm.exception.category, "invalid_input")

    def test_server_error_and_no_audio(self):
        for mode, cat in (("server", "server_error"), ("json", "server_error")):
            with MockVoiceStudio(fail=mode) as m:
                with self.assertRaises(VoiceStudioError) as cm:
                    VoiceStudio(base_url=m.url).speech("hello", os.path.join(tmpdir(), "x.wav"))
                self.assertEqual(cm.exception.category, cat)

    def test_unreachable_is_unavailable_not_success(self):
        vs = VoiceStudio(base_url=free_port_url(), timeout=3)
        self.assertFalse(vs.available())
        with self.assertRaises(VoiceStudioError) as cm:
            vs.speech("hello", os.path.join(tmpdir(), "x.wav"))
        self.assertEqual(cm.exception.category, "unavailable")
        self.assertIn("localhost", str(cm.exception))

    def test_missing_api_key_is_auth_error_and_key_is_sent(self):
        with MockVoiceStudio(api_key="secret") as m:
            with self.assertRaises(VoiceStudioError) as cm:
                VoiceStudio(base_url=m.url, api_key="").health()
            self.assertEqual(cm.exception.category, "auth")
            self.assertEqual(VoiceStudio(base_url=m.url, api_key="secret").health()["status"], "ok")

    def test_env_configuration(self):
        old = dict(os.environ)
        try:
            os.environ["CATANA_VOICE_STUDIO_URL"] = "http://10.0.0.5:3900/"
            os.environ["OMNIVOICE_API_KEY"] = "k"
            vs = VoiceStudio()
            self.assertEqual(vs.base_url, "http://10.0.0.5:3900")
            self.assertEqual(vs.api_key, "k")
        finally:
            os.environ.clear(); os.environ.update(old)

    def test_rate_fit_and_describe(self):
        with MockVoiceStudio() as m:
            vs = VoiceStudio(base_url=m.url)
            self.assertFalse(vs.rate_fit("one two three four five six seven eight nine ten eleven", 2)["fits"])
            self.assertEqual(vs.describe_voice("deep calm british male")["instruct"], "male, low pitch")


class VoiceStudioOrchestration(unittest.TestCase):
    def job(self):
        return {"id": "vo_S01", "operation": "tts", "text": "Welcome home.", "voice": "default", "format": "wav"}

    def test_orchestrator_succeeds_and_logs_asset(self):
        with MockVoiceStudio() as m:
            d = tmpdir()
            log = pv.RunLog(os.path.join(d, "runs.jsonl"))
            ranked = pv.select("tts", ["voice_studio"])["ranked"]
            self.assertEqual(ranked[0]["provider"], "voice_studio")
            orch = pv.Orchestrator({"voice_studio": pv.VoiceStudioAdapter(d, VoiceStudio(base_url=m.url)),
                                    "prompt_only": pv.PromptOnlyAdapter(d)}, log, sleep=lambda s: None)
            res = orch.run(self.job(), ranked)
            self.assertEqual(res["status"], "succeeded")
            rec = log.records()[-1]
            self.assertEqual(rec["status"], "succeeded")
            self.assertTrue(os.path.exists(rec["assets"][0]))

    def test_unavailable_falls_back_to_prompt_only_never_success(self):
        from catana_core.voice_studio import VoiceStudio as VS
        d = tmpdir()
        log = pv.RunLog(os.path.join(d, "runs.jsonl"))
        ranked = pv.select("tts", ["voice_studio"])["ranked"]
        orch = pv.Orchestrator({"voice_studio": pv.VoiceStudioAdapter(d, VS(base_url=free_port_url(), timeout=2)),
                                "prompt_only": pv.PromptOnlyAdapter(d)}, log, sleep=lambda s: None)
        res = orch.run(self.job(), ranked)
        self.assertEqual(res["status"], "prompt_only")
        statuses = [r["status"] for r in log.records()]
        self.assertEqual(statuses, ["failed", "prompt_only"])
        self.assertNotIn("succeeded", statuses)
        self.assertEqual(log.records()[0]["error_category"], "unavailable")

    def test_server_error_retries_then_falls_back(self):
        from catana_core.voice_studio import VoiceStudio as VS
        with MockVoiceStudio(fail="server") as m:
            d = tmpdir()
            waits = []
            log = pv.RunLog(os.path.join(d, "runs.jsonl"))
            ranked = pv.select("tts", ["voice_studio"])["ranked"]
            orch = pv.Orchestrator({"voice_studio": pv.VoiceStudioAdapter(d, VS(base_url=m.url)), "prompt_only": pv.PromptOnlyAdapter(d)},
                                   log, sleep=waits.append)
            res = orch.run(self.job(), ranked)
            self.assertEqual(res["status"], "prompt_only")
            self.assertEqual([r["provider"] for r in log.records()], ["voice_studio"] * 3 + ["prompt_only"])
            self.assertEqual(waits, [4, 15])


class VoiceCLI(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, os.path.join(SCRIPTS, "catana.py"), *args], capture_output=True, text=True)

    def test_cli_speak_and_plan(self):
        with MockVoiceStudio() as m:
            d = tmpdir()
            r = self.run_cli("voice", "speak", "Hello villa", "--out", os.path.join(d, "a.wav"), "--url", m.url, "--log", os.path.join(d, "runs.jsonl"))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(os.path.exists(os.path.join(d, "a.wav")))
            comp = {"voiceover": {"voice": "default", "direction": "warm", "lines": [
                {"shot": "S01", "start": 0.0, "text": "Modern living."}, {"shot": "S03", "start": 10.0, "text": "Redefined."}]}}
            cp = os.path.join(d, "compiled.json")
            with open(cp, "w") as f:
                json.dump(comp, f)
            r = self.run_cli("voice", "plan", cp, "--out-dir", os.path.join(d, "vo"), "--url", m.url)
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(os.path.join(d, "vo", "vo.json")) as f:
                cues = json.load(f)["cues"]
            self.assertEqual([c["t"] for c in cues], [0.15, 10.15])

    def test_cli_unavailable_exit_code(self):
        r = self.run_cli("voice", "health", "--url", free_port_url())
        self.assertEqual(r.returncode, 3)
        self.assertIn("unavailable", r.stderr)


if __name__ == "__main__":
    unittest.main()
