// Client-side verification, same rules as rsa_challenge/challenge.py verify().
// Works in browsers and Node >= 20 (uses globalThis.crypto.subtle + BigInt).
(function (root) {
  "use strict";
  const enc = new TextEncoder();

  async function sha256Hex(str) {
    const buf = await globalThis.crypto.subtle.digest("SHA-256", enc.encode(str));
    return Array.from(new Uint8Array(buf), (b) => b.toString(16).padStart(2, "0")).join("");
  }

  function parseBig(s) {
    s = String(s).trim().replace(/[\s_,]/g, "");
    if (!/^(0x[0-9a-fA-F]+|\d+)$/.test(s)) throw new Error("not an integer: " + s.slice(0, 20));
    return BigInt(s);
  }

  function modpow(b, e, m) {
    let r = 1n; b %= m;
    while (e > 0n) { if (e & 1n) r = (r * b) % m; b = (b * b) % m; e >>= 1n; }
    return r;
  }

  function bigToUtf8(m) {
    let hex = m.toString(16); if (hex.length % 2) hex = "0" + hex;
    const bytes = new Uint8Array(hex.length / 2);
    for (let i = 0; i < bytes.length; i++) bytes[i] = parseInt(hex.substr(i * 2, 2), 16);
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  }

  async function verifyFactors(ch, pStr, qStr) {
    let p, q;
    try { p = parseBig(pStr); q = parseBig(qStr); } catch (e) { return { ok: false, msg: e.message }; }
    if (p <= 1n || q <= 1n) return { ok: false, msg: "factors must be > 1" };
    if (p * q !== BigInt(ch.n)) return { ok: false, msg: "p × q ≠ N" };
    const [a, b] = p < q ? [p, q] : [q, p];
    if ((await sha256Hex(a + "," + b)) !== ch.factors_sha256)
      return { ok: false, msg: "p × q = N but factor hash mismatch" };
    return { ok: true, msg: "Correct factors! p × q = N and the commitment hash matches." };
  }

  async function verifyPlaintext(ch, text) {
    if ((await sha256Hex(text)) === ch.plaintext_sha256)
      return { ok: true, msg: "Correct plaintext — SHA-256 commitment matches." };
    return { ok: false, msg: "Plaintext hash does not match." };
  }

  async function verifyD(ch, dStr) {
    let d; try { d = parseBig(dStr); } catch (e) { return { ok: false, msg: e.message }; }
    if (d <= 1n) return { ok: false, msg: "d must be > 1" };
    let text;
    try { text = bigToUtf8(modpow(BigInt(ch.c), d, BigInt(ch.n))); }
    catch (e) { return { ok: false, msg: "c^d mod N is not valid UTF-8 — wrong d" }; }
    if ((await sha256Hex(text)) !== ch.plaintext_sha256)
      return { ok: false, msg: "Decryption with d does not match the plaintext hash." };
    return { ok: true, msg: "Correct private exponent! Decrypted plaintext: " + JSON.stringify(text) };
  }

  const api = { sha256Hex, parseBig, modpow, bigToUtf8, verifyFactors, verifyPlaintext, verifyD };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RSAVerify = api;
})(typeof self !== "undefined" ? self : this);
