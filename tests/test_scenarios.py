"""The 15 Phase-10 test scenarios, end to end through the engine (no paid generation: connectors are simulated)."""
import json
import os
import unittest

from helpers import tmpdir
from catana_core import prompt_engine as pe, qc, providers as pv, director, camera as cam
from catana_core.spec import ShotSpec, SpecError


class Scenarios(unittest.TestCase):
    # 1 -------------------------------------------------------------------------------------------
    def test_01_basic_image_generation(self):
        spec = pe.enhance("a ceramic coffee mug on a wooden table")
        self.assertEqual(spec.modality, "image")
        r = pe.render(spec)
        for f in ("composition", "camera", "lens", "lighting", "materials", "style", "color"):
            self.assertTrue(getattr(spec, f), f)
        self.assertIn("ceramic coffee mug", r["prompt"])
        self.assertIn("mm", r["prompt"])                       # a real lens instruction, not generic
        self.assertTrue(r["negative_prompt"])
        self.assertTrue(qc.lint(spec)["ready"])

    # 2 -------------------------------------------------------------------------------------------
    def test_02_advanced_image_multi_reference_and_style(self):
        spec = pe.enhance("editorial fashion photo of a model wearing the linen suit, golden hour on a Marrakech rooftop", modality="image")
        self.assertEqual(spec.domain, "fashion")
        self.assertEqual(spec.technical["time_of_day"], "golden_hour")
        spec.references = [{"source": "suit.jpg", "role": "product", "preserve": ["garment cut", "fabric pattern"]},
                           {"source": "moodboard.jpg", "role": "style"}]
        r = pe.render(spec)
        self.assertIn("Keep garment cut, fabric pattern exactly as in the product reference", r["prompt"])
        self.assertIn("style reference", r["prompt"])
        self.assertEqual(qc.needed_operation(spec), "multi_ref_image")
        self.assertEqual(len(r["params"]["references"]), 2)

    # 3 -------------------------------------------------------------------------------------------
    def test_03_image_to_video(self):
        spec = pe.enhance("animate this photo of a sailboat at sunset, slow push in", modality="video")
        spec.references = [{"source": "boat.jpg", "role": "first_frame"}]
        self.assertEqual(qc.needed_operation(spec), "i2v")
        r = pe.render(spec)
        self.assertTrue(r["prompt"].startswith("Slow subtle push in"))
        self.assertIn("Start from the first-frame image", r["prompt"])
        sel = pv.select("i2v", ["higgsfield", "runway"], duration=spec.technical["duration"], aspect="16:9")
        self.assertEqual(sel["ranked"][0]["provider"], "higgsfield")
        self.assertTrue(sel["ranked"][0]["requires_approval"])        # paid → ask first
        spec.modality = "image"
        self.assertFalse(qc.lint(spec)["ready"])                       # first_frame on a still is an error

    # 4 -------------------------------------------------------------------------------------------
    def test_04_text_to_video(self):
        spec = pe.enhance("10 second cinematic video of a lone astronaut walking across red dunes, tracking shot")
        self.assertEqual((spec.modality, spec.technical["duration"]), ("video", 10.0))
        self.assertEqual(spec.camera_moves[0]["id"], "tracking")
        r = pe.render(spec)
        self.assertIn("tracking shot moving alongside", r["prompt"].lower())
        self.assertIn("10-second shot", r["prompt"])
        self.assertTrue(qc.lint(spec)["ready"])

    # 5 -------------------------------------------------------------------------------------------
    def test_05_multi_scene_video(self):
        plan = director.new_plan("cinematic short film about a lighthouse keeper's last night", duration=60, domain="cinematic")
        shots = plan["scenes"][0]["shots"]
        self.assertAlmostEqual(sum(s["duration"] for s in shots), 60, delta=0.1)
        plan["scenes"] = [{"id": "SC1", "name": "dusk", "shots": shots[:6]}, {"id": "SC2", "name": "storm", "shots": shots[6:]}]
        comp = director.compile_plan(plan)
        self.assertEqual(len(comp["shots"]), len(shots))
        self.assertEqual(comp["edl"][-1]["out"], comp["total_seconds"])
        self.assertEqual({s["scene"] for s in comp["shots"]}, {"SC1", "SC2"})
        moves = [s["camera"][0] for s in comp["shots"]]
        self.assertGreater(len(set(moves)), 3)                          # the edit varies its camera
        md = director.to_markdown(plan, comp)
        for h in ("## Continuity bible", "## Shot list", "## Storyboard", "## Sound", "## Edit sequence"):
            self.assertIn(h, md)

    # 6 -------------------------------------------------------------------------------------------
    def test_06_character_consistency(self):
        bible = {"characters": {"maya": "Maya, a 30-year-old woman with a short black bob, olive skin, a small scar over her left eyebrow, "
                                        "wearing a mustard wool coat"}, "style": "cinematic film still, 35mm", "grade": "teal and amber"}
        shots = []
        for i, action in enumerate(["@maya waits on a rainy platform", "@maya boards the night train", "@maya reads a letter by the window"]):
            s = pe.enhance(action, domain="cinematic", modality="video")
            s.characters = ["maya"]
            shots.append(pe.apply_bible(s, bible))
        for s in shots:
            self.assertIn("small scar over her left eyebrow", s.subject)
            self.assertNotIn("@maya", s.subject)
            self.assertIn("identity drift", s.negative)
            self.assertEqual(s.style, "cinematic film still, 35mm")
        self.assertTrue(qc.lint_sequence(shots, bible=bible)["ready"])
        broken = shots[1].copy(); broken.subject = "a woman boards a train"
        self.assertFalse(qc.lint_sequence([shots[0], broken, shots[2]], bible=bible)["ready"])

    # 7 -------------------------------------------------------------------------------------------
    def test_07_product_advertisement(self):
        plan = director.new_plan("launch commercial for Aurora wireless earbuds", duration=15)
        self.assertEqual(plan["domain"], "product")
        comp = director.compile_plan(plan)
        beats = [s["beat"] for s in comp["shots"]]
        self.assertEqual(beats[0], "hook")
        self.assertEqual(beats[-1], "end_card")
        self.assertTrue(any("label" in s["negative_prompt"] for s in comp["shots"]))
        self.assertTrue(all(s["qc"]["ready"] for s in comp["shots"]))

    # 8 -------------------------------------------------------------------------------------------
    def test_08_ugc_production(self):
        plan = director.new_plan("UGC review of a vitamin C serum by a young woman at home", platform="tiktok")
        self.assertEqual((plan["domain"], plan["aspect_ratio"]), ("ugc", "9:16"))
        shots = plan["scenes"][0]["shots"]
        self.assertTrue(all(s["camera_moves"][0]["id"] == "handheld" for s in shots))
        shots[0]["vo"] = "Okay I was not expecting this serum to actually fade my dark spots in two weeks, honestly"
        shots[-1]["vo"] = "Link in bio."
        comp = director.compile_plan(plan)
        vo = comp["voiceover"]
        self.assertEqual(vo["provider"], "voice_studio")                 # free, user-preferred voice provider
        self.assertFalse(vo["lines"][0]["fits"])                         # 17 words in a ~3 s slot is flagged
        self.assertTrue(vo["lines"][1]["fits"])
        sel = pv.select("tts", ["voice_studio", "elevenlabs", "runway"])
        self.assertEqual(sel["policy"], "free_only")
        self.assertEqual([r["provider"] for r in sel["ranked"]], ["voice_studio", "prompt_only"])

    # 9 -------------------------------------------------------------------------------------------
    def test_09_architectural_cinematic(self):
        spec = pe.enhance("8 second architectural film of the villa from this render, slow dolly in, golden hour", modality="video")
        self.assertEqual(spec.domain, "architecture")
        spec.references = [{"source": "render.png", "role": "first_frame"}, {"source": "render.png", "role": "geometry", "preserve": ["roof"]}]
        issues = [i["message"] for i in qc.lint(spec)["issues"]]
        self.assertTrue(any("geometry preservation" in m for m in issues))
        spec.references[1]["preserve"] = ["building massing", "number of floors", "window layout", "roof form"]
        rep = qc.lint(spec)
        self.assertFalse(any("geometry preservation" in i["message"] for i in rep["issues"]))
        self.assertIn("warped or bent verticals", spec.negative)
        self.assertIn("Keep building massing, number of floors, window layout, roof form", pe.render(spec)["prompt"])

    # 10 ------------------------------------------------------------------------------------------
    def test_10_camera_movement(self):
        required = ["dolly_in", "dolly_out", "push_in", "pull_out", "tracking", "orbit_360", "arc", "crane_up", "crane_down", "pedestal",
                    "tilt_up", "tilt_down", "pan_left", "pan_right", "whip_pan", "zoom_in", "zoom_out", "fpv_drone", "aerial_reveal",
                    "top_down", "handheld", "steadicam", "bullet_time", "dutch_angle", "rack_focus", "parallax"]
        ids = [m["id"] for m in cam.all_moves()]
        for r in required:
            self.assertIn(r, ids)
        for m in cam.all_moves():
            for f in ("definition", "best_for", "camera_behavior", "subject_behavior", "example_prompt", "common_mistakes", "combos"):
                self.assertTrue(m[f], f"{m['id']}.{f}")
            for c in m["combos"] + m["conflicts"]:
                self.assertIsNotNone(cam.get(c), f"{m['id']} references unknown move {c}")
            self.assertNotIn(m["id"], m["combos"])
            self.assertFalse(set(m["combos"]) & set(m["conflicts"]), m["id"])
        found = [f["id"] for f in cam.find_in_text("a fast FPV drone dive then a slow crane up and a rack focus")]
        self.assertEqual(found, ["fpv_drone", "crane_up", "rack_focus"])
        self.assertEqual(cam.find_in_text("fast fpv dive")[0]["speed"], "fast")
        self.assertTrue(any(i["severity"] == "error" for i in cam.check_combo(["dolly_in", "dolly_out"])))
        self.assertEqual(cam.check_combo(["dolly_in", "rack_focus"], 4), [])
        self.assertIn("lens kept level", cam.phrase("pedestal", "slow", direction="up"))

    # 11 ------------------------------------------------------------------------------------------
    def test_11_prompt_enhancement(self):
        weak = ShotSpec(subject="nice car", style="amazing, 8k, masterpiece", modality="video")
        rep = qc.lint(weak)
        self.assertFalse(rep["ready"])
        self.assertLess(rep["score"], 40)
        self.assertTrue(all(i["fix"] for i in rep["issues"]))
        self.assertTrue(any("filler" in i["message"] for i in rep["issues"]))
        strong = pe.enhance("a vintage red Porsche 911 driving along a coastal cliff road, aerial reveal, 8 seconds")
        self.assertGreaterEqual(qc.lint(strong)["score"], 90)
        self.assertGreater(len(pe.render(strong)["prompt"]), 4 * len("a vintage red Porsche 911 driving along a coastal cliff road"))

    # 12 ------------------------------------------------------------------------------------------
    def test_12_provider_failure(self):
        ranked = pv.select("t2v", ["higgsfield", "runway"], approved_paid=True)["ranked"]
        a = [{"provider": "higgsfield", "status": "failed", "error_category": pv.classify_error("HTTP 503 Service Unavailable")}]
        self.assertEqual(pv.next_action(a, ranked)["action"], "fallback")
        a = [{"provider": "higgsfield", "status": "failed", "error_category": pv.classify_error("request timed out")}]
        step = pv.next_action(a, ranked)
        self.assertEqual((step["action"], step["provider"], step["wait"]), ("retry", "higgsfield", 4))
        a = a * 3
        self.assertEqual(pv.next_action(a, ranked)["action"], "fallback")
        a = [{"provider": "higgsfield", "status": "failed", "error_category": pv.classify_error("Insufficient credits for this generation")}]
        self.assertEqual(pv.next_action(a, ranked)["action"], "stop")   # billing never auto-switches to another paid provider

    # 13 ------------------------------------------------------------------------------------------
    def test_13_missing_api_keys(self):
        self.assertEqual(pv.classify_error("401 Unauthorized: missing API key"), "auth")
        ranked = pv.select("t2i", ["higgsfield", "runway"])["ranked"]
        step = pv.next_action([{"provider": "higgsfield", "status": "failed", "error_category": "auth"}], ranked)
        self.assertEqual((step["action"], step["provider"]), ("ask_approval", "runway"))
        step = pv.next_action([{"provider": "higgsfield", "status": "failed", "error_category": "auth"},
                               {"provider": "runway", "status": "failed", "error_category": "auth"}], ranked)
        self.assertEqual(step["action"], "prompt_only")
        d = tmpdir()
        with self.assertRaises(ValueError):
            pv.RunLog(os.path.join(d, "r.jsonl")).append("runway", "t2i", "succeeded")   # no asset → not a success

    # 14 ------------------------------------------------------------------------------------------
    def test_14_invalid_inputs(self):
        for bad in ({"modality": "hologram"}, {"technical": {"aspect_ratio": "7:3"}}, {"technical": {"duration": -2}},
                    {"references": [{"source": "a.png", "role": "vibes"}]}, {"camera_moves": [{"speed": "slow"}]}, {"colour": "red"}):
            with self.assertRaises(SpecError, msg=str(bad)):
                ShotSpec.from_dict(dict({"subject": "x"}, **bad))
        with self.assertRaises(ValueError):
            pe.enhance("   ")
        with self.assertRaises(ValueError):
            pe.enhance("a chair", domain="underwater_basket_weaving")
        with self.assertRaises(ValueError):
            pv.select("teleport", [])
        with self.assertRaises(ValueError):
            director.new_plan("a film", platform="myspace")
        step = pv.next_action([{"provider": "runway", "status": "failed", "error_category": pv.classify_error("422 validation error")}],
                              pv.select("t2v", ["runway"], approved_paid=True)["ranked"])
        self.assertEqual(step["action"], "fix_input")

    # 15 ------------------------------------------------------------------------------------------
    def test_15_workflow_fallback(self):
        sel = pv.select("t2v", [], policy="free_only")
        self.assertEqual([r["provider"] for r in sel["ranked"]], ["prompt_only"])
        d = tmpdir()
        log = pv.RunLog(os.path.join(d, "runs.jsonl"))
        spec = pe.enhance("8 second video of waves crashing on black sand, slow aerial reveal")
        r = pe.render(spec)
        orch = pv.Orchestrator({"prompt_only": pv.PromptOnlyAdapter(d)}, log, sleep=lambda s: None)
        res = orch.run({"id": "waves", "operation": "t2v", "prompt": r["prompt"], "negative_prompt": r["negative_prompt"], "params": r["params"]},
                       sel["ranked"])
        self.assertEqual(res["status"], "prompt_only")
        with open(os.path.join(d, "waves.md")) as f:
            md = f.read()
        self.assertIn("nothing was generated", md)
        self.assertIn(r["prompt"], md)
        self.assertEqual(log.records()[-1]["status"], "prompt_only")
        # a connector the orchestrator can't execute itself is skipped to the next option, never reported as success
        ranked = pv.select("t2v", ["higgsfield"], approved_paid=True)["ranked"]
        res = orch.run({"id": "waves2", "operation": "t2v", "prompt": r["prompt"]}, ranked)
        self.assertEqual(res["status"], "prompt_only")


if __name__ == "__main__":
    unittest.main()
