// CI self-test for site/verify.js: generates nothing secret; uses a fixed toy key (p=61,q=53 style but bigger).
// CI self-test for site/verify.js: generates throwaway challenges in a temp dir, verifies them, deletes them.
const dir = fs.mkdtempSync(path.join(os.tmpdir(), "rsa-js-"));
execFileSync("python3", ["-m", "rsa_challenge", "--public", path.join(dir, "c.json"), "--secrets", path.join(dir, "s"), "generate", "--bits", "64", "512"], { stdio: "inherit" });
let fail = 0;
for (const f of fs.readdirSync(path.join(dir, "s"))) {
  try { execFileSync("node", ["scripts/e2e_verify.mjs", path.join(dir, "c.json"), path.join(dir, "s", f)], { stdio: "inherit" }); }
  catch { fail++; }
}
fs.rmSync(dir, { recursive: true, force: true });
process.exit(fail ? 1 : 0);
