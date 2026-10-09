import unittest

from pr_contract import check_pr_text


class PRContractTests(unittest.TestCase):
    def test_complete_d2(self):
        body = (
            "Fixes #23\n**Änderungsklasse:** D2\n"
            "## Nachweis\n- Hosttests: PASS\n"
        )
        problems, kind = check_pr_text(body)
        self.assertEqual(problems, [])
        self.assertEqual(kind, "D2")

    def test_empty(self):
        problems, kind = check_pr_text("")
        self.assertEqual(kind, "unbekannt")
        self.assertEqual(len(problems), 4)

    def test_d3_without_safety_gates(self):
        body = "Fixes #2\n**Änderungsklasse:** D3\n## Tests\nPASS"
        problems, kind = check_pr_text(body)
        self.assertEqual(kind, "D3")
        self.assertEqual(len(problems), 2)

    def test_d3_safety_status(self):
        body = (
            "Befund: SCH26-01\n**Änderungsklasse:** D3\n"
            "## Tests\nT3: PASS. G2: NICHT AUSGEFÜHRT.\n"
            "Gefährdung: Lade-Wiederanlauf, noch ohne HiL."
        )
        problems, _ = check_pr_text(body)
        self.assertEqual(problems, [])

    def test_reference_without_class(self):
        problems, kind = check_pr_text("Resolves #10\n## Tests\nSKIP")
        self.assertEqual(kind, "unbekannt")
        self.assertEqual(len(problems), 1)


if __name__ == "__main__":
    unittest.main()
