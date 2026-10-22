import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from rsa_challenge import challenge, cli, core  # noqa: E402
import check_no_secrets  # noqa: E402


class TestCore(unittest.TestCase):
    def test_primes(self):
        self.assertTrue(core.is_probable_prime(2**127 - 1))
        self.assertFalse(core.is_probable_prime(561))  # Carmichael
        self.assertFalse(core.is_probable_prime((2**61 - 1) * (2**31 - 1)))

    def test_keypair_sizes(self):
        for bits in (64, 128, 256, 330, 512):
            n, p, q, d = core.generate_keypair(bits)
            self.assertEqual(n.bit_length(), bits)
            self.assertEqual(p * q, n)
            self.assertLess(p, q)
            self.assertEqual((core.E * d) % ((p - 1) * (q - 1)), 1)

    def test_digits(self):
        self.assertEqual(core.bits_for_digits(100), 330)  # RSA-100 is 330 bits

    def test_roundtrip(self):
        for bits in (64, 256, 1024):
            n, p, q, d = core.generate_keypair(bits)
            text = core.random_plaintext(bits)
            m = core.encode(text)
            self.assertLess(m, n)
            c = core.encrypt(m, core.E, n)
            self.assertEqual(core.decode(core.decrypt(c, d, n)), text)


class TestChallenge(unittest.TestCase):
    def setUp(self):
        self.pub, self.sec = challenge.make_challenge(128, "T")

    def test_public_has_no_secrets(self):
        self.assertEqual(set(self.pub), set(challenge.PUBLIC_KEYS))
        blob = json.dumps(self.pub)
        for k in ("p", "q", "d", "plaintext"):
            self.assertNotIn(self.sec[k], blob)

    def test_verify(self):
        V = challenge.verify
        self.assertTrue(V(self.pub, p=self.sec["p"], q=self.sec["q"])[0])
        self.assertTrue(V(self.pub, p=self.sec["q"], q=self.sec["p"])[0])
        self.assertTrue(V(self.pub, d=self.sec["d"])[0])
        self.assertTrue(V(self.pub, plaintext=self.sec["plaintext"])[0])
        self.assertFalse(V(self.pub, p="1", q=self.pub["n"])[0])
        self.assertFalse(V(self.pub, p="3", q="5")[0])
        self.assertFalse(V(self.pub, d="7")[0])
        self.assertFalse(V(self.pub, plaintext="x")[0])

    def test_cli_generate_verify(self):
        with tempfile.TemporaryDirectory() as t:
            pub, sec = Path(t, "c.json"), Path(t, "s")
            base = ["--public", str(pub), "--secrets", str(sec)]
            self.assertEqual(cli.main(base + ["generate", "--bits", "64", "--digits", "30"]), 0)
            data = json.loads(pub.read_text())
            ids = [c["id"] for c in data["challenges"]]
            self.assertEqual(ids, ["RSA-64b", "RSA-30"])
            self.assertEqual(data["challenges"][1]["digits"], 30)
            s = json.loads((sec / "RSA-64b.json").read_text())
            self.assertEqual(cli.main(base + ["verify", "RSA-64b", "--p", s["p"], "--q", s["q"]]), 0)
            self.assertEqual(cli.main(base + ["verify", "RSA-64b", "--plaintext", "wrong"]), 1)

    def test_solve_small(self):
        n = int(self.pub["n"])
        p = cli.pollard_rho(int(challenge.make_challenge(64, "x")[0]["n"]))
        self.assertGreater(p, 1)
        self.assertGreater(n, 0)


class TestNoSecrets(unittest.TestCase):
    def _repo(self, t):
        subprocess.run(["git", "init", "-q", t], check=True)
        return Path(t)

    def test_repo_is_clean(self):
        self.assertEqual(check_no_secrets.scan(ROOT, [ROOT / "secrets"]), [])

    def test_detects_leaks(self):
        with tempfile.TemporaryDirectory() as t:
            r = self._repo(t)
            pub, sec = challenge.make_challenge(64, "L")
            (r / "secrets").mkdir()
            (r / "secrets/L.json").write_text(json.dumps(sec))
            (r / "notes.txt").write_text("p is " + sec["p"])
            leaked = dict(pub, d=sec["d"])
            (r / "challenges").mkdir()
            (r / "challenges/challenges.json").write_text(json.dumps({"challenges": [leaked]}))
            subprocess.run(["git", "-C", t, "add", "-f", "."], check=True)
            errs = check_no_secrets.scan(r, [r / "secrets"])
            joined = "\n".join(errs)
            self.assertIn("tracked secret file", joined)
            self.assertIn("non-public keys", joined)
            self.assertIn("L.p", joined)
            self.assertIn("L.d", joined)

    def test_gitignore_covers_secrets(self):
        out = subprocess.run(["git", "check-ignore", "-q", "secrets/x.json"], cwd=ROOT)
        self.assertEqual(out.returncode, 0)


if __name__ == "__main__":
    unittest.main()
