(function () {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const fa = (n) => String(n).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]);
  const csrf = () => (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || ($("[name=csrfmiddlewaretoken]") || {}).value || "";
  const store = {
    get: (k) => { try { return localStorage.getItem(k); } catch (_) { return null; } },
    set: (k, v) => { try { localStorage.setItem(k, v); } catch (_) { } },
  };

  const root = document.documentElement;
  $("[data-theme-toggle]")?.addEventListener("click", () => {
    const t = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = t; store.set("mirana-panel-theme", t);
  });
  $("[data-collapse]")?.addEventListener("click", () => {
    document.body.classList.toggle("side-mini");
    store.set("mirana-side-mini", document.body.classList.contains("side-mini") ? "1" : "0");
  });
  if (store.get("mirana-side-mini") === "1") document.body.classList.add("side-mini");
  $("[data-menu]")?.addEventListener("click", () => document.body.classList.add("side-open"));
  $(".backdrop")?.addEventListener("click", () => document.body.classList.remove("side-open"));

  const ICON = { success: '<path d="m5 12 5 5L20 7"/>', error: '<path d="M6 6l12 12M18 6 6 18"/>', info: '<path d="M12 8h.01M12 12v4"/>', warning: '<path d="M12 8v4M12 16h.01"/>' };
  function toast(msg, type = "success") {
    const box = $(".toasts");
    const t = document.createElement("div");
    t.className = "toast " + type;
    t.innerHTML = `<span class="t-ic"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round">${ICON[type] || ICON.info}</svg></span><span></span>`;
    t.lastChild.textContent = msg;
    box.appendChild(t);
    setTimeout(() => { t.classList.add("hide"); setTimeout(() => t.remove(), 400); }, 3800);
  }
  window.toast = toast;
  $$(".django-message").forEach((m, i) => setTimeout(() => toast(m.dataset.text, m.dataset.type), 200 + i * 150));

  async function post(url, data) {
    const r = await fetch(url, { method: "POST", body: data, headers: { "X-CSRFToken": csrf(), "X-Requested-With": "fetch" }, credentials: "same-origin" });
    return r.json();
  }

  $$("[data-count-to]").forEach((el) => {
    const to = parseInt(el.dataset.countTo, 10) || 0;
    const dur = 1100, start = performance.now();
    const step = (now) => {
      const p = Math.min(1, (now - start) / dur), e = 1 - Math.pow(1 - p, 3);
      el.textContent = fa(Math.round(to * e).toLocaleString("en-US").replace(/,/g, "٬"));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  });
  setTimeout(() => {
    $$(".chart .bar[data-h]").forEach((b, i) => setTimeout(() => (b.style.height = Math.max(2, b.dataset.h) + "%"), i * 40));
    $$("[data-w]").forEach((b) => (b.style.width = b.dataset.w + "%"));
  }, 150);

  $$("[data-toggle-url]").forEach((sw) => sw.addEventListener("change", async () => {
    const fd = new FormData(); fd.append("field", sw.dataset.field || "is_active");
    try {
      const r = await post(sw.dataset.toggleUrl, fd);
      sw.checked = r.value; toast(r.value ? "فعال شد" : "غیرفعال شد", "success");
    } catch (_) { sw.checked = !sw.checked; toast("خطا در ذخیره", "error"); }
  }));

  $$(".stock-input").forEach((inp) => {
    let old = inp.value;
    const save = async () => {
      if (inp.value === old) return;
      const fd = new FormData(); fd.append("kind", inp.dataset.kind); fd.append("value", inp.value);
      try {
        const r = await post(inp.dataset.url, fd);
        if (r.ok) { old = inp.value = r.value; inp.classList.remove("saved"); void inp.offsetWidth; inp.classList.add("saved"); toast("موجودی ذخیره شد"); }
      } catch (_) { toast("خطا در ذخیره موجودی", "error"); }
    };
    inp.addEventListener("change", save);
    inp.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); inp.blur(); } });
  });

  const modal = $("#confirm-modal");
  let pendingForm = null;
  document.addEventListener("submit", (e) => {
    const f = e.target;
    if (f.dataset.confirm && !f.dataset.confirmed) {
      e.preventDefault();
      pendingForm = f;
      $("#confirm-text").textContent = f.dataset.confirm;
      modal.classList.add("open");
    }
  }, true);
  $("[data-modal-ok]")?.addEventListener("click", () => {
    if (pendingForm) { pendingForm.dataset.confirmed = "1"; modal.classList.remove("open"); pendingForm.requestSubmit ? pendingForm.requestSubmit() : pendingForm.submit(); }
  });
  $$("[data-modal-cancel]").forEach((b) => b.addEventListener("click", () => { modal.classList.remove("open"); pendingForm = null; }));
  modal?.addEventListener("click", (e) => { if (e.target === modal) modal.classList.remove("open"); });

  document.addEventListener("click", (e) => {
    const img = e.target.closest("[data-lightbox]");
    if (!img) return;
    const lb = document.createElement("div");
    lb.className = "lightbox"; lb.innerHTML = `<img src="${img.dataset.lightbox || img.src}" alt="">`;
    lb.onclick = () => lb.remove();
    document.body.appendChild(lb);
  });

  document.addEventListener("click", async (e) => {
    const b = e.target.closest("[data-copy]");
    if (!b) return;
    try { await navigator.clipboard.writeText(b.dataset.copy); toast("کپی شد"); } catch (_) { toast("کپی نشد", "error"); }
  });

  function previewInput(input, target) {
    input.addEventListener("change", () => {
      const f = input.files && input.files[0];
      if (!f || !target) return;
      const url = URL.createObjectURL(f);
      target.innerHTML = `<img src="${url}" alt="">`;
    });
  }
  $$("[data-preview]").forEach((inp) => previewInput(inp, $(inp.dataset.preview)));
  $$(".dropzone").forEach((dz) => {
    ["dragenter", "dragover"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("drag"); }));
    ["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, () => dz.classList.remove("drag")));
  });

  const bulk = $("#gallery-bulk");
  if (bulk) {
    bulk.addEventListener("change", () => {
      const box = $("#bulk-preview"); box.innerHTML = "";
      Array.from(bulk.files).forEach((f) => {
        const d = document.createElement("div"); d.className = "g-item";
        d.innerHTML = `<img src="${URL.createObjectURL(f)}" alt=""><div class="g-tools"><span class="chip ok">جدید</span></div>`;
        box.appendChild(d);
      });
    });
  }
  document.addEventListener("change", (e) => {
    const cb = e.target.closest("input[type=checkbox][name$='-DELETE']");
    if (!cb) return;
    cb.closest(".g-item, .var-row")?.classList.toggle("deleted", cb.checked);
  });

  const vt = $("#variant-body");
  if (vt) {
    const total = $("#id_var-TOTAL_FORMS");
    const tpl = $("#variant-template").innerHTML;
    const addRow = (vals = {}) => {
      const i = parseInt(total.value, 10);
      const tmp = document.createElement("tbody");
      tmp.innerHTML = tpl.replace(/__prefix__/g, i);
      const row = tmp.firstElementChild;
      Object.entries(vals).forEach(([k, v]) => { const el = row.querySelector(`[name="var-${i}-${k}"]`); if (el) el.value = v; });
      vt.appendChild(row);
      total.value = i + 1;
      $("#var-empty")?.remove();
      return row;
    };
    $("[data-add-variant]")?.addEventListener("click", () => addRow().querySelector("input")?.focus());
    $("[data-bulk-variants]")?.addEventListener("click", () => {
      const sizes = $("#bulk-sizes").value.split(/[,،\s]+/).filter(Boolean);
      const colors = $("#bulk-colors").value.split(/[,،]+/).map((s) => s.trim()).filter(Boolean);
      const stock = $("#bulk-stock").value || "0";
      const colorList = colors.length ? colors : [""];
      const sizeList = sizes.length ? sizes : [""];
      let n = 0;
      colorList.forEach((c) => {
        const [name, hex] = c.split(":").map((x) => x && x.trim());
        sizeList.forEach((s) => { addRow({ color: name || "", color_hex: hex || "#000000", size: s, stock }); n++; });
      });
      toast(`${fa(n)} تنوع اضافه شد؛ برای ثبت، محصول را ذخیره کنید.`, "info");
    });
    $$("[data-size-preset]").forEach((b) => b.addEventListener("click", () => ($("#bulk-sizes").value = b.dataset.sizePreset)));
  }

  const badgeUrl = document.body.dataset.badges;
  if (badgeUrl) {
    let lastPending = null;
    const tick = async () => {
      try {
        const r = await (await fetch(badgeUrl, { credentials: "same-origin" })).json();
        $$("[data-badge=pending]").forEach((b) => { b.textContent = fa(r.pending); b.dataset.n = r.pending; });
        $$("[data-badge=messages]").forEach((b) => { b.textContent = fa(r.messages); b.dataset.n = r.messages; });
        if (lastPending !== null && r.pending > lastPending) toast("پیش‌سفارش جدید ثبت شد! 🛍️", "info");
        lastPending = r.pending;
      } catch (_) { }
    };
    tick(); setInterval(tick, 60000);
  }

  $$("form[data-once]").forEach((f) => f.addEventListener("submit", () => {
    setTimeout(() => f.querySelectorAll("[type=submit]").forEach((b) => b.classList.add("loading")), 0);
  }));
})();
