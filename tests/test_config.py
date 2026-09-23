try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLES = {
    "luna_explorer": "read-only",
    "luna_executor": "workspace-write",
    "luna_tester": "workspace-write",
}

class CodexConductorConfigTests(unittest.TestCase):
    def test_role_configuration(self):
        for name, sandbox in ROLES.items():
            with self.subTest(role=name):
                agent = tomllib.loads((ROOT / "codex-agents" / f"{name}.toml").read_text())
                self.assertEqual(agent["name"], name)
                self.assertEqual(agent["model"], "gpt-6-luna")
                self.assertEqual(agent["model_reasoning_effort"], "medium")
                self.assertEqual(agent["sandbox_mode"], sandbox)
                self.assertTrue(agent["developer_instructions"].strip())
                self.assertIn("Do not spawn agents", agent["developer_instructions"])

    def test_skill_metadata_and_routing(self):
        skill = (ROOT / "SKILL.md").read_text()
        readme = (ROOT / "README.md").read_text()
        self.assertIn("name: codex-conductor", skill.split("---", 2)[1])
        self.assertIn("gpt-6-luna", skill)
        self.assertIn("GPT-6 Sol", skill)
        self.assertIn('default_subagent_model = "gpt-6-luna"', readme)
        self.assertNotIn("gpt-5.6-luna", skill.lower())
        self.assertNotIn("gpt-5.6-luna", readme.lower())
        for role in ROLES:
            self.assertIn(role, skill)
            self.assertIn(role, readme)

    def test_skill_has_no_mandatory_role_pipeline(self):
        skill = (ROOT / "SKILL.md").read_text()
        self.assertIn("No mandatory", skill)
        self.assertIn("ACCEPT", skill)
        self.assertIn("CORRECT", skill)
        self.assertIn("REPLAN", skill)

    def test_agent_ui(self):
        ui = (ROOT / "agents" / "openai.yaml").read_text()
        self.assertIn("$codex-conductor", ui)
        self.assertIn("GPT-6 Sol", ui)
        self.assertIn("GPT-6 Luna", ui)

if __name__ == "__main__":
    unittest.main()
