import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/research-map/scripts"))
import view_document
from view_reader import Reader as PolicyReader


class Reader:
    def __init__(self, denied=()):
        self.denied = set(denied)
        self.reads = []
        self.issues = []
        self.audience = "local"

    def read(self, path):
        assert self.permits(path)
        self.reads.append(path)
        return path.read_bytes()

    def permits(self, path):
        return path not in self.denied

    def partial(self, message):
        self.issues.append(message)


class DocumentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.doc = self.root / "article.md"
        self.review = self.root / "review.md"
        self.reader = Reader()

    def test_explicit_sections_and_claim_occurrences_are_versioned(self):
        self.doc.write_text("# Study\n## Question\nWhich districts participated?\n"
                            "## Results\nOne. <!-- claim:C1 result:R1 --> Two. <!-- claim:C1 result:R2 -->\n")
        entries = view_document.collect(self.reader, self.doc)
        question = next(item for item in entries if item["kind"] == "question")
        self.assertIn("article.md#question", question["aliases"])
        self.assertIn("Which districts", question["text"])
        claims = [item for item in entries if "C1" in item["aliases"]]
        self.assertEqual([item["text"] for item in claims], ["One.", "Two."])
        self.assertNotEqual(claims[0]["selector"], claims[1]["selector"])
        self.assertTrue(all(item["source"] == "article.md" for item in entries))
        old = {item["selector"] for item in entries}
        self.doc.write_text(self.doc.read_text() + "\n")
        self.assertTrue(old.isdisjoint(item["selector"] for item in view_document.collect(self.reader, self.doc)))

    def test_declared_bilingual_fields_and_anchors_exclude_fenced_examples(self):
        self.doc.write_text("## Desenho do estudo {#design}\nSeguimento prospectivo.\n"
                            "```example\nMétodo: HIDDEN\n## Uncertainty\nFAKE <!-- claim:C8 result:R3 -->\n```\n"
                            "## Hypotheses\nCounts will differ.\n"
                            "Incerteza decisiva: Cobertura em 2020.\nNext action: Read the survey manual.\n"
                            "## Results\nAll sampled authors mentioned delays.\n")
        entries = view_document.collect(self.reader, self.doc)
        design = next(e for e in entries if e["kind"] == "method")
        self.assertEqual(design["text"], "Seguimento prospectivo.")
        self.assertIn("article.md#design", design["aliases"])
        for kind, value in [("hypothesis", "Counts will differ."), ("uncertainty", "Cobertura em 2020."),
                            ("next_action", "Read the survey manual.")]:
            self.assertTrue(any(e["kind"] == kind and value == e["text"] for e in entries), kind)
        self.assertFalse(any(e["kind"] == "claim" for e in entries))
        self.assertNotIn("HIDDEN", repr(entries))
        self.assertNotIn("C8", repr(entries))

    def test_code_only_example_does_not_supply_documentary_text(self):
        self.doc.write_text("~~~\nQuestion: EXAMPLE ONLY\n~~~\n")
        entries = view_document.collect(self.reader, self.doc)
        self.assertEqual([e["kind"] for e in entries], ["document"])
        self.assertFalse(entries[0]["text"])

    def test_plain_text_field_on_separate_line_preserves_exact_value(self):
        self.doc.write_text("Pergunta:\nQuando ocorreu a mudança?\n**Método:** **Amostragem** simples\n"
                            "H1: _Incidência_ aumentará\n")
        entries = view_document.collect(self.reader, self.doc)
        actual = {e["kind"]: e["text"] for e in entries if e["kind"] != "document"}
        self.assertEqual(actual, {"question": "Quando ocorreu a mudança?",
                                  "method": "**Amostragem** simples", "hypothesis": "_Incidência_ aumentará"})

    def test_short_ids_address_heading_occurrences(self):
        self.doc.write_text("## C1 {#primary}\nFirst reported claim.\n## C1\nSecond reported claim.\n")
        claims = [e for e in view_document.collect(self.reader, self.doc) if "C1" in e["aliases"]]
        self.assertEqual([e["text"] for e in claims], ["First reported claim.", "Second reported claim."])
        self.assertNotEqual(claims[0]["selector"], claims[1]["selector"])

    def test_pdf_binding_hashes_exact_bytes_and_retains_page_in_separate_review(self):
        self.doc = self.doc.with_suffix(".pdf")
        self.doc.write_bytes(b"%PDF-1.7\r\nNO TEXT EXTRACTION\x00\xff")
        digest = hashlib.sha256(self.doc.read_bytes()).hexdigest()
        self.review.write_text(f"\nDocument-SHA256: {digest}\nPage 4: Reported sampling frame is unclear.\n")
        entries = view_document.collect(self.reader, self.doc, self.review)
        document, report = entries
        self.assertIn(digest, document["selector"])
        self.assertTrue(any("text" in issue.lower() for issue in self.reader.issues))
        self.assertNotIn("NO TEXT EXTRACTION", repr(entries))
        self.assertEqual(report["kind"], "review")
        self.assertEqual(report["details"]["binding"], "matched")
        self.assertIn(report["selector"], document["related"])
        self.assertIn("Page 4", report["text"])
        self.assertEqual(report["source"], "review.md")
        self.assertEqual(report["details"]["reported_document_locators"], ["page 4"])
        self.assertIn("article.pdf#page=4", report["aliases"])

    def test_explaining_document_or_passage_includes_the_matched_review_as_context(self):
        self.doc.write_text("Counts differed. <!-- claim:C1 result:R1 -->\n")
        digest = hashlib.sha256(self.doc.read_bytes()).hexdigest()
        self.review.write_text(f"Document-SHA256: {digest}\nPage 2: Unclear measurement.")
        cli = Path(view_document.__file__).with_name("research.py")
        for target in (self.doc.name, "C1"):
            result = subprocess.run([sys.executable, str(cli), "view", "explain", target,
                                     "--document", str(self.doc), "--review", str(self.review),
                                     "--format", "json"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            entries = json.loads(result.stdout)["entries"]
            report = next(e for e in entries if e["kind"] == "review")
            self.assertEqual(report["details"]["scope"], "document")
            self.assertIn("Unclear measurement", report["text"])
            self.assertFalse(report["related"])

    def test_stale_unbound_and_contradictory_reports_do_not_gain_a_current_link(self):
        self.doc.write_bytes(b"Question: Is it associated?\r\n")
        digest = hashlib.sha256(self.doc.read_bytes()).hexdigest()
        other = "0" * 64
        for preamble, binding in [(f"Document-SHA256: {other}", "stale"),
                                  ("No version given", "unbound"),
                                  (f"Document-SHA256: {digest}\nDocument-SHA256: {other}", "unbound")]:
            with self.subTest(binding=binding, preamble=preamble):
                self.review.write_text(preamble + "\nThe reviewer reports a discrepancy.")
                entries = view_document.collect(self.reader, self.doc, self.review)
                report = next(item for item in entries if item["kind"] == "review")
                self.assertEqual(report["details"]["binding"], binding)
                self.assertIn("reviewer reports", report["text"])
                self.assertTrue(all(report["selector"] not in item["related"] for item in entries))
                self.assertTrue(self.reader.issues)

    def test_each_policy_is_checked_before_copying_source_or_review_text(self):
        self.doc.write_text("## Private title\nRestricted quotation")
        outside = self.root / "other-project"
        outside.mkdir()
        report = outside / "review-with-quotation.txt"
        digest = hashlib.sha256(self.doc.read_bytes()).hexdigest()
        report.write_text(f"Document-SHA256: {digest}\nRestricted quotation")
        reader = Reader([self.doc])
        self.assertEqual(view_document.collect(reader, self.doc, report), [])
        self.assertFalse(reader.reads)
        output = repr(reader.issues)
        for hidden in ("Private title", "Restricted quotation", digest, self.doc.name, report.name):
            self.assertNotIn(hidden, output)
        reader = Reader([report])
        entries = view_document.collect(reader, self.doc, report)
        self.assertTrue(entries)
        self.assertFalse(any(item["kind"] == "review" for item in entries))
        self.assertEqual(reader.reads, [self.doc])

    def test_model_view_rechecks_both_projects_and_omits_unbound_quotations(self):
        manuscript = self.root / "author" / "manuscript.txt"
        report = self.root / "reviewer" / "review.txt"
        for path in (manuscript, report):
            (path.parent / ".research").mkdir(parents=True)

        def permission(path, allow):
            rule = {"version": 1, "resources": [{"match": path.name, "class": "restricted"}],
                    "rules": {"restricted": {"model_egress": allow, "network_egress": False}}}
            (path.parent / ".research/policy.json").write_text(json.dumps(rule))

        manuscript.write_bytes(b"Question: Which villages were sampled?\n")
        digest = hashlib.sha256(manuscript.read_bytes()).hexdigest()
        report.write_text(f"Document-SHA256: {digest}\nPage 4: REVIEW CANARY")
        permission(manuscript, False)
        permission(report, True)
        reader = PolicyReader("model")
        self.assertEqual(view_document.collect(reader, manuscript, report), [])
        self.assertNotIn("CANARY", repr(reader.issues))
        permission(manuscript, True)
        permission(report, False)
        entries = view_document.collect(PolicyReader("model"), manuscript, report)
        self.assertIn("villages", repr(entries))
        self.assertNotIn("CANARY", repr(entries))
        permission(report, True)
        entries = view_document.collect(PolicyReader("model"), manuscript, report)
        self.assertIn("REVIEW CANARY", repr(entries))
        report.write_text("Unbound quotation from another document: UNKNOWN CANARY")
        entries = view_document.collect(PolicyReader("model"), manuscript, report)
        self.assertNotIn("UNKNOWN CANARY", repr(entries))

    def test_model_formats_withhold_restricted_citations_and_their_copied_review(self):
        (self.root / ".research").mkdir()
        policy = {"version": 1, "resources": [{"match": path.name, "class": "public"}
                  for path in (self.doc, self.review)] + [{"match": "private.csv", "class": "restricted"}],
                  "rules": {"public": {"model_egress": True, "network_egress": False},
                            "restricted": {"model_egress": False, "network_egress": False}}}
        (self.root / ".research/policy.json").write_text(json.dumps(policy))
        cli = Path(view_document.__file__).with_name("research.py")
        cases = [
            ("## Private conclusion\nAUTHOR CANARY from [table](private.csv).", "Quoted AUTHOR CANARY"),
            ("## Private conclusion\nAUTHOR CANARY from `private.csv`.", "Quoted AUTHOR CANARY"),
            ("## Private conclusion\nAUTHOR CANARY <!-- claim:C876 result:R876 -->", "Quoted AUTHOR CANARY"),
            ("## Private conclusion\nAUTHOR CANARY from [source][t].\n\n[t]: private.csv", "Quoted AUTHOR CANARY"),
            ("", "## Private review\nREVIEW CANARY. See [table](private.csv)"),
        ]
        for passage, quote in cases:
            self.doc.write_text("# Question\nPUBLIC QUESTION\n" + passage)
            digest = hashlib.sha256(self.doc.read_bytes()).hexdigest()
            self.review.write_text(f"Document-SHA256: {digest}\n{quote}\n")
            for fmt in ("json", "markdown"):
                with self.subTest(passage=passage, quote=quote, format=fmt):
                    answer = subprocess.run([sys.executable, str(cli), "view", "status", "--audience", "model",
                                             "--document", str(self.doc), "--review", str(self.review),
                                             "--format", fmt], capture_output=True, text=True)
                    self.assertEqual(answer.returncode, 0, answer.stderr)
                    self.assertIn("PUBLIC QUESTION", answer.stdout)
                    for secret in ("CANARY", "private.csv", "Private conclusion", "Private review", "C876", "R876"):
                        self.assertNotIn(secret, answer.stdout + answer.stderr, secret)


if __name__ == "__main__":
    unittest.main()
