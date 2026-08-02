from __future__ import annotations

import csv
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CanonicalPublicationTests(unittest.TestCase):
    def test_component_lock_is_valid_and_pinned(self) -> None:
        path = ROOT / "ecosystem" / "components.lock.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        components = payload["components"]
        ids = [component["id"] for component in components]

        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(components), 4)

        for component in components:
            self.assertRegex(component["commit"], r"^[0-9a-f]{40}$")
            self.assertTrue(component["clone_url"].startswith("https://github.com/Darkem0/"))
            self.assertTrue(component["clone_url"].endswith(".git"))

    def test_bootstrap_script_compiles(self) -> None:
        path = ROOT / "scripts" / "bootstrap_public_ecosystem.py"
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")

    def test_authoritative_phone_summary(self) -> None:
        path = ROOT / "public" / "metrics" / "authoritative_phone_summary.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        self.assertGreaterEqual(len(rows), 7)
        a7_phone = next(
            row
            for row in rows
            if row["model"] == "A7" and row["dataset"] == "mediaspeech_phone"
        )
        self.assertAlmostEqual(float(a7_phone["normalized_wer"]), 0.15428452289943706)
        self.assertEqual(a7_phone["checkpoint"], "step-200")

    def test_a7_metric_grid_is_complete(self) -> None:
        path = ROOT / "public" / "metrics" / "a7_checkpoint_metrics.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        regular = [row for row in rows if row["dataset"] != "robustness_proxy"]
        robustness = [row for row in rows if row["dataset"] == "robustness_proxy"]

        self.assertEqual(len(regular), 28)
        self.assertEqual(len(robustness), 4)
        self.assertEqual({row["checkpoint"] for row in regular}, {
            "step-050",
            "step-100",
            "step-150",
            "step-200",
        })

        for row in regular:
            self.assertRegex(row["prediction_sha256"], r"^[0-9a-f]{64}$")

    def test_readme_local_links_exist(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme)
        local_links = [
            link.split("#", 1)[0]
            for link in links
            if not link.startswith(("http://", "https://", "mailto:"))
        ]
        missing = [link for link in local_links if link and not (ROOT / link).exists()]
        self.assertEqual(missing, [])

    def test_manuscripts_state_proxy_limit(self) -> None:
        for relative in (
            "paper/final_manuscript_tr.md",
            "paper/final_manuscript_en.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8").lower()
            self.assertIn("proxy", text)
            self.assertIn("0.1542845", text)


if __name__ == "__main__":
    unittest.main()
