from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/research-map/scripts"
sys.path.insert(0, str(SCRIPTS))
from view_reader import Reader, journal_entries


class ViewReaderTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.paper = self.root / "paper.md"
        self.paper.write_text("original")

    def policy(self, allowed):
        policy = self.root / ".research/policy.json"
        policy.parent.mkdir(exist_ok=True)
        policy.write_text(json.dumps({
            "version": 1, "resources": [{"match": "paper.md", "class": "public"}],
            "rules": {"public": {"model_egress": allowed, "network_egress": False}}
        }))
        return policy

    def test_changed_source_and_new_directory_member_invalidate_read(self):
        reader = Reader()
        self.assertEqual(reader.read(self.paper), b"original")
        self.assertEqual(reader.watch_dir(self.root, "*.md"), [self.paper])
        self.assertTrue(reader.stable())
        self.paper.write_text("changed!")
        self.assertFalse(reader.stable())
        self.paper.write_text("original")
        reader = Reader()
        reader.watch_dir(self.root, "*.md")
        (self.root / "second.md").touch()
        self.assertFalse(reader.stable())

    def test_missing_file_and_new_policy_invalidate_read(self):
        reader = Reader("model")
        reader.watch_file(self.root / "future.md")
        self.assertTrue(reader.permits(self.paper))
        self.policy(False)
        self.assertFalse(reader.stable())
        reader = Reader()
        reader.watch_file(self.root / "future.md")
        (self.root / "future.md").touch()
        self.assertFalse(reader.stable())

    def test_egress_for_loose_file_invalid_limit_and_symlinks(self):
        parent = self.policy(False)
        reader = Reader("model")
        self.assertFalse(reader.permits(self.paper))
        with self.assertRaises(PermissionError):
            reader.read(self.paper)
        self.assertTrue(Reader("local").permits(self.paper))
        self.policy(True)
        reader = Reader("model")
        self.assertEqual(reader.read(self.paper), b"original")
        unmatched = self.root / "appendix.md"
        unmatched.write_text("secret data")
        self.assertFalse(reader.permits(unmatched))
        alias = self.root / "alias"
        alias.symlink_to(unmatched)
        self.assertFalse(reader.permits(alias))
        self.assertFalse(Reader("local").permits(alias))
        parent.write_text("{")
        self.assertFalse(Reader("model").permits(self.paper))

    def test_journals_include_terminal_failure_and_never_emit_payload(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        reader = Reader()
        self.assertIsNone(reader.watch_git(self.root))
        runtime = self.root / ".git/research/runtime"
        before = list((self.root / ".git").iterdir())
        self.assertEqual(journal_entries(reader, self.root), [])
        self.assertEqual(before, list((self.root / ".git").iterdir()))
        self.assertFalse(runtime.exists())
        cases = [
            ("EXECUTION_STARTED", None),
            ("completed", {"effect": "executed", "disposition": "BLOCK"}),
            ("completed", {"effect": "executed", "disposition": "ALLOW"}),
        ]
        for stage, result in cases:
            op = str(uuid4())
            folder = runtime / op
            folder.mkdir(parents=True)
            (folder / "operation.json").write_text(json.dumps({
                "operation_id": op, "request": {"action": "FIT_CONFIRMATORY", "target": "sensitive phrase"},
                "stage": stage, "result": result, "exposure": "sensitive phrase",
            }))
            (folder / "stdout.bin").write_text("sensitive output")
        self.assertFalse(reader.stable())
        entries = journal_entries(Reader(), self.root)
        self.assertEqual(len(entries), 3)
        self.assertEqual(len({e["text"] for e in entries}), 3)
        self.assertNotIn("sensitive", json.dumps(entries))
        self.policy(True)
        model = Reader("model")
        self.assertEqual(journal_entries(model, self.root), [])
        self.assertTrue(model.issues)

    def test_model_with_policy_watches_private_head_and_anchor_for_drift(self):
        def git(*args):
            return subprocess.check_output([
                "git", "-C", str(self.root), "-c", "user.name=Fixture",
                "-c", "user.email=test@example.org", *args
            ], text=True).strip()

        git("init", "-q")
        git("commit", "--allow-empty", "-m", "initial")
        revision = git("rev-parse", "HEAD")
        self.assertEqual(Reader("model").watch_git(self.root), revision)
        self.policy(True)
        self.assertEqual(Reader("local").watch_git(self.root), revision)
        model = Reader("model")
        self.assertIsNone(model.watch_git(self.root))
        before = model.snapshot_id()
        self.assertTrue(model.stable())
        git("commit", "--allow-empty", "-m", "private change")
        self.assertFalse(model.stable())
        after = Reader("model")
        self.assertIsNone(after.watch_git(self.root))
        self.assertEqual(after.snapshot_id(), before)
        anchor = self.root / ".git/research/runtime/anchor.json"
        anchor.parent.mkdir(parents=True)
        anchor.write_text('{"head": "private"}')
        self.assertFalse(after.stable())
        anchored = Reader("model")
        self.assertIsNone(anchored.watch_git(self.root))
        self.assertEqual(anchored.snapshot_id(), before)
        self.assertTrue(anchored.stable())

    def test_snapshot_digest_covers_only_visible_files_and_members(self):
        self.policy(True)
        secret = self.root / "secret.md"
        secret.write_text("first")

        def observe():
            reader = Reader("model")
            reader.watch_dir(self.root, "*.md")
            reader.read(self.paper)
            self.assertEqual(len(reader.issues), 1)
            self.assertNotIn("secret.md", reader.issues[0])
            self.assertNotIn("hidden.md", reader.issues[0])
            return reader.snapshot_id()

        first = observe()
        self.assertEqual(first, observe())
        secret.write_text("second")
        self.assertEqual(first, observe())
        (self.root / "hidden.md").touch()
        self.assertEqual(first, observe())
        self.paper.write_text("longer visible content")
        self.assertNotEqual(first, observe())

    def test_only_local_journal_is_inspected_in_linked_worktree(self):
        def git(*args, root=None):
            return subprocess.check_output(["git", "-C", str(root or self.root), *args], text=True).strip()

        git("init", "-q")
        git("-c", "user.name=Fixture", "-c", "user.email=test@example.org", "commit", "--allow-empty", "-m", "fixture")
        with tempfile.TemporaryDirectory() as parent:
            other = Path(parent) / "alternate"
            git("worktree", "add", "--quiet", "--detach", str(other))
            reader = Reader()
            self.assertEqual(reader.watch_git(other), git("rev-parse", "HEAD"))
            journal_entries(reader, other)
            (self.root / ".git/research/runtime").mkdir(parents=True)
            self.assertTrue(reader.stable())
            directory = Path(git("rev-parse", "--absolute-git-dir", root=other))
            (directory / "research/runtime").mkdir(parents=True)
            (directory / "research/runtime/anchor.json").write_text("{}")
            self.assertFalse(reader.stable())


if __name__ == "__main__":
    unittest.main()
