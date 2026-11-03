"""Slash commands are discoverable, correctly routed, documented, and in sync with data/commands.json."""
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

from helpers import ROOT, tmpdir

CLAUDE_AI_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


def frontmatter(path):
    text = open(path, encoding="utf8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    assert m, f"{path} has no frontmatter"
    fm = dict(re.findall(r"^([\w-]+):\s*(.*)$", m.group(1), re.M))
    return fm, m.group(2)


class Commands(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "data", "commands.json"), encoding="utf8") as f:
            cls.cmds = json.load(f)["commands"]
        with open(os.path.join(ROOT, "SKILL.md"), encoding="utf8") as f:
            cls.skill = f.read()

    def test_proposed_commands_all_exist(self):
        proposed = {"hero-shot", "ugc-video", "faceless-video", "ad-multiplier", "cinematic-video", "image-to-video", "character-studio",
                    "product-commercial", "storyboard", "camera-movement", "architecture-film", "scene-builder", "prompt-enhancer",
                    "campaign-studio", "style-transfer", "video-director"}
        names = {c["name"] for c in self.cmds}
        self.assertTrue(proposed <= names, proposed - names)
        self.assertIn("motion-film", names)            # the original CATANA capability, exposed as a command
        self.assertEqual(len(names), len(self.cmds))   # no duplicates

    def test_every_command_file_is_well_formed_and_routed(self):
        files = sorted(f for f in os.listdir(os.path.join(ROOT, "commands")) if f.endswith(".md"))
        self.assertEqual(files, sorted(c["name"] + ".md" for c in self.cmds))
        for c in self.cmds:
            fm, body = frontmatter(os.path.join(ROOT, "commands", c["name"] + ".md"))
            self.assertEqual(fm.get("description"), c["purpose"])
            self.assertTrue(fm.get("argument-hint"))
            self.assertEqual(fm.get("disable-model-invocation"), "true")
            self.assertIn("$ARGUMENTS", body)
            self.assertIn(f"**{c['mode']}** mode", body)
            for r in c["reads"]:
                self.assertIn("${CLAUDE_PLUGIN_ROOT}/" + r, body)
            for field in ("purpose", "argument_hint", "parameters", "examples", "behavior", "limitations", "reads"):
                self.assertTrue(c[field], f"{c['name']}.{field}")

    def test_routing_table_covers_every_command_and_mode(self):
        for c in self.cmds:
            self.assertIn(f"`/catana:{c['name']}`", self.skill, c["name"])
            self.assertRegex(self.skill, rf"\|[^|\n]*\b{re.escape(c['mode'])} · `/catana:{re.escape(c['name'])}`")

    def test_every_referenced_file_exists(self):
        refs = set()
        for c in self.cmds:
            refs |= set(c["reads"])
        refs |= set(re.findall(r"\b((?:docs|references)/[\w./-]+\.md)", self.skill))
        missing = sorted(r for r in refs if not os.path.exists(os.path.join(ROOT, r)))
        self.assertEqual(missing, [], f"referenced but missing: {missing}")

    def test_skill_frontmatter_is_claude_ai_compatible(self):
        fm, body = frontmatter(os.path.join(ROOT, "SKILL.md"))
        self.assertEqual(fm["name"], "catana")
        self.assertTrue(set(fm) <= CLAUDE_AI_KEYS, set(fm) - CLAUDE_AI_KEYS)
        self.assertLessEqual(len(fm["description"]), 1024)
        for word in ("katana", "storyboard", "UGC", "product", "architectur", "camera"):
            self.assertIn(word.lower(), fm["description"].lower())

    def test_plugin_and_marketplace_manifests(self):
        with open(os.path.join(ROOT, ".claude-plugin", "plugin.json")) as f:
            plugin = json.load(f)
        with open(os.path.join(ROOT, ".claude-plugin", "marketplace.json")) as f:
            market = json.load(f)
        self.assertEqual(plugin["name"], "catana")
        self.assertIn("./", plugin["skills"])
        self.assertEqual(market["plugins"][0]["name"], plugin["name"])
        self.assertEqual(market["plugins"][0]["source"], "./")
        self.assertTrue(os.path.exists(os.path.join(ROOT, plugin["icon"])))

    def test_generated_docs_are_in_sync(self):
        """`catana.py docs` output in a scratch copy must equal the committed files (edit data/, then regenerate)."""
        d = tmpdir()
        for sub in ("scripts", "engine", "data"):
            shutil.copytree(os.path.join(ROOT, sub), os.path.join(d, sub), ignore=shutil.ignore_patterns("__pycache__"))
        os.makedirs(os.path.join(d, "docs"))
        r = subprocess.run([sys.executable, os.path.join(d, "scripts", "catana.py"), "docs"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        for rel in ["docs/COMMANDS.md", "docs/CAMERA_MOVEMENTS.md"] + [f"commands/{c['name']}.md" for c in self.cmds]:
            with open(os.path.join(d, rel), encoding="utf8") as a, open(os.path.join(ROOT, rel), encoding="utf8") as b:
                self.assertEqual(a.read(), b.read(), f"{rel} is stale — run `python scripts/catana.py docs`")

    def test_docs_document_every_command(self):
        with open(os.path.join(ROOT, "docs", "COMMANDS.md"), encoding="utf8") as f:
            doc = f.read()
        for c in self.cmds:
            sec = doc.split(f'<a id="{c["name"]}"></a>')[1].split("<a id=")[0]
            for heading in ("**Purpose.**", "**Syntax.**", "**Parameters.**", "**Examples.**", "**Expected behaviour.**", "**Limitations.**"):
                self.assertIn(heading, sec, f"{c['name']} lacks {heading}")


class CLI(unittest.TestCase):
    def run_cli(self, *a):
        return subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "catana.py"), *a], capture_output=True, text=True)

    def test_help_and_exit_codes(self):
        self.assertEqual(self.run_cli("--help").returncode, 0)
        self.assertEqual(self.run_cli("enhance", "a red apple on slate").returncode, 0)
        self.assertEqual(self.run_cli("camera", "show", "dolly in").returncode, 0)
        self.assertEqual(self.run_cli("camera", "check", "dolly_in", "dolly_out").returncode, 1)
        self.assertEqual(self.run_cli("camera", "show", "moonwalk").returncode, 2)
        self.assertEqual(self.run_cli("select", "--op", "teleport").returncode, 2)
        self.assertEqual(self.run_cli("lint", "/nonexistent.json").returncode, 2)
        self.assertEqual(self.run_cli("enhance", "x", "--platform", "myspace").returncode, 2)
        r = self.run_cli("log", "--file", os.path.join(tmpdir(), "r.jsonl"), "--provider", "runway", "--op", "t2v", "--status", "succeeded")
        self.assertEqual(r.returncode, 2)
        self.assertIn("refusing", r.stderr)

    def test_lint_spec_file(self):
        d = tmpdir()
        p = os.path.join(d, "spec.json")
        with open(p, "w") as f:
            json.dump({"subject": "thing", "modality": "video"}, f)
        r = self.run_cli("lint", p)
        self.assertEqual(r.returncode, 1)
        self.assertFalse(json.loads(r.stdout)["ready"])


if __name__ == "__main__":
    unittest.main()
