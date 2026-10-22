// End-to-end check of site/verify.js using a local secrets dir:
//   node scripts/e2e_verify.mjs <challenges.json> <secrets/ID.json>
import { createRequire } from "module"; import fs from "fs";
const V = createRequire(import.meta.url)("../site/verify.js");
const [pubPath, secPath] = process.argv.slice(2);
const sec = JSON.parse(fs.readFileSync(secPath, "utf8"));
const ch = JSON.parse(fs.readFileSync(pubPath, "utf8")).challenges.find((c) => c.id === sec.id);
const checks = [
  ["factors", await V.verifyFactors(ch, sec.p, sec.q), true],
  ["factors swapped", await V.verifyFactors(ch, sec.q, sec.p), true],
  ["d", await V.verifyD(ch, sec.d), true],
  ["plaintext", await V.verifyPlaintext(ch, sec.plaintext), true],
  ["bad factors", await V.verifyFactors(ch, "1", ch.n), false],
  ["bad d", await V.verifyD(ch, "12345"), false],
  ["bad plaintext", await V.verifyPlaintext(ch, "nope"), false],
];
let bad = 0;
for (const [name, r, want] of checks) { const pass = r.ok === want; bad += !pass; console.log(pass ? "PASS" : "FAIL", ch.id, name, "-", r.msg.replace(sec.plaintext, "<plaintext>")); }
process.exit(bad ? 1 : 0);
