from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DiscoveryMetadataTests(unittest.TestCase):
    def test_required_discovery_files_exist(self) -> None:
        required = [
            "llms.txt",
            "codemeta.json",
            "docs/index.md",
            "docs/_config.yml",
            "docs/what_worked_what_failed_simple.md",
            "docs/a7_real_data_fast_path.md",
            "paper/publication_package.md",
        ]
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_codemeta_is_valid_and_canonical(self) -> None:
        payload = json.loads((ROOT / "codemeta.json").read_text(encoding="utf-8"))
        self.assertEqual(
            payload["codeRepository"],
            "https://github.com/Darkem0/whisper-turkish-domain-adaptation",
        )
        self.assertIn("Turkish ASR", payload["keywords"])
        self.assertIn("telephone speech", payload["keywords"])

    def test_llms_index_preserves_result_and_scope(self) -> None:
        text = (ROOT / "llms.txt").read_text(encoding="utf-8")
        self.assertIn("0.15428452289943706", text)
        self.assertIn("open-data proxy results", text)
        self.assertIn("not verified operational call-center performance", text)

    def test_simple_guide_contains_actionable_sections(self) -> None:
        text = (ROOT / "docs/what_worked_what_failed_simple.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("## 1. En hızlı özet", text)
        self.assertIn("## 5. Gerçek veri için hızlı A7 başlangıç tarifi", text)
        self.assertIn("A0 base", text)
        self.assertIn("A4", text)
        self.assertIn("A7", text)

    def test_publication_files_do_not_contain_local_paths(self) -> None:
        public_files = [
            "llms.txt",
            "codemeta.json",
            "docs/index.md",
            "docs/what_worked_what_failed_simple.md",
            "docs/a7_real_data_fast_path.md",
            "paper/publication_package.md",
        ]
        forbidden = ["C:\\Users\\", "/home/", "192.168.", "10.0.0."]
        for relative in public_files:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for pattern in forbidden:
                self.assertNotIn(pattern, text, f"{pattern} in {relative}")


if __name__ == "__main__":
    unittest.main()
