(async function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  let data;
  try {
    data = await (await fetch("challenges.json", { cache: "no-store" })).json();
  } catch (e) {
    $("loaderr").hidden = false; $("loaderr").textContent = "Could not load challenges.json: " + e; return;
  }
  let cur = null;
  const tbody = document.querySelector("#list tbody");
  for (const ch of data.challenges) {
    const tr = document.createElement("tr");
    for (const v of [ch.id, ch.bits, ch.digits, ch.created.slice(0, 10)]) {
      const td = document.createElement("td"); td.textContent = v; tr.appendChild(td);
    }
    const td = document.createElement("td"); const b = document.createElement("button");
    b.textContent = "Open"; b.onclick = () => show(ch); td.appendChild(b); tr.appendChild(td);
    tbody.appendChild(tr);
  }
  function show(ch) {
    cur = ch; $("detail").hidden = false;
    $("d-title").textContent = ch.id + " (" + ch.bits + " bits, " + ch.digits + " digits)";
    $("d-n").textContent = ch.n; $("d-e").textContent = ch.e; $("d-c").textContent = ch.c;
    $("d-fh").textContent = ch.factors_sha256; $("d-ph").textContent = ch.plaintext_sha256;
    result(null); location.hash = ch.id;
  }
  function result(r) {
    const el = $("result");
    if (!r) { el.textContent = ""; el.className = ""; return; }
    el.textContent = (r.ok ? "✅ " : "❌ ") + r.msg; el.className = r.ok ? "ok" : "fail";
  }
  const on = (id, fn) => $(id).addEventListener("submit", async (ev) => {
    ev.preventDefault(); result({ ok: false, msg: "checking…" }); result(await fn(new FormData(ev.target)));
  });
  on("f-factors", (f) => RSAVerify.verifyFactors(cur, f.get("p"), f.get("q")));
  on("f-d", (f) => RSAVerify.verifyD(cur, f.get("d")));
  on("f-pt", (f) => RSAVerify.verifyPlaintext(cur, f.get("pt")));
  const pre = data.challenges.find((c) => c.id === decodeURIComponent(location.hash.slice(1)));
  if (pre) show(pre);
})();
