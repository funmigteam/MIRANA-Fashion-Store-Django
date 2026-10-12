(function () {
  "use strict";

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const fa = (n) => String(n).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]);
  const money = (n) => fa(Number(n).toLocaleString("en-US").replace(/,/g, "٬"));
  const csrf = () => (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || ($("[name=csrfmiddlewaretoken]") || {}).value || "";
  window.Mirana = { fa, money };

  window.addEventListener("load", () => setTimeout(() => $(".page-loader")?.classList.add("done"), 250));
  setTimeout(() => $(".page-loader")?.classList.add("done"), 2500);

  const ICON = {
    success: '<path d="m5 12 5 5L20 7"/>', error: '<path d="M6 6l12 12M18 6 6 18"/>',
    info: '<path d="M12 8h.01M12 12v4"/>', warning: '<path d="M12 8v4M12 16h.01"/>',
  };
  function toast(msg, type = "success", ms = 3800) {
    let box = $(".toasts");
    if (!box) { box = document.createElement("div"); box.className = "toasts"; document.body.appendChild(box); }
    const t = document.createElement("div");
    t.className = "toast " + type;
    t.innerHTML = `<span class="t-ic"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round">${ICON[type] || ICON.info}</svg></span><span></span><button aria-label="بستن"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6 6 18"/></svg></button>`;
    t.children[1].textContent = msg;
    const close = () => { t.classList.add("hide"); setTimeout(() => t.remove(), 400); };
    t.querySelector("button").onclick = close;
    box.appendChild(t);
    setTimeout(close, ms);
  }
  window.toast = toast;
  $$(".django-message").forEach((m, i) => setTimeout(() => toast(m.dataset.text, m.dataset.type), 300 + i * 150));

  const header = $(".header");
  const toTop = $(".to-top");
  const onScroll = () => {
    const y = window.scrollY;
    header?.classList.toggle("scrolled", y > 10);
    toTop?.classList.toggle("show", y > 600);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  toTop?.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

  const body = document.body;
  $$("[data-drawer-open]").forEach((b) => b.addEventListener("click", () => body.classList.add("drawer-open")));
  $$("[data-drawer-close], .drawer-backdrop").forEach((b) =>
    b.addEventListener("click", () => body.classList.remove("drawer-open", "filters-open")));
  $$("[data-filters-open]").forEach((b) => b.addEventListener("click", () => body.classList.add("filters-open")));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") body.classList.remove("drawer-open", "filters-open"); });

  $(".fab-main")?.addEventListener("click", () => $(".fab").classList.toggle("open"));

  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    $$(".reveal, .reveal-stagger").forEach((el) => {
      if (el.getBoundingClientRect().top < window.innerHeight) el.classList.add("in");
      else io.observe(el);
    });
    setTimeout(() => $$(".reveal:not(.in), .reveal-stagger:not(.in)").forEach((el) => {
      if (el.getBoundingClientRect().top < window.innerHeight * 1.5) el.classList.add("in");
    }), 1500);
  } else {
    $$(".reveal, .reveal-stagger").forEach((el) => el.classList.add("in"));
  }

  const slider = $(".slider");
  if (slider) {
    const slides = $$(".slide", slider);
    const dots = $$(".slider-dots button", slider);
    let i = 0, timer;
    const go = (n) => {
      slides[i]?.classList.remove("active"); dots[i]?.classList.remove("active");
      i = (n + slides.length) % slides.length;
      slides[i]?.classList.add("active"); dots[i]?.classList.add("active");
      const dark = slides[i]?.classList.contains("theme-dark");
      slider.style.color = dark ? "#f8efe4" : "";
    };
    const play = () => { clearInterval(timer); if (slides.length > 1) timer = setInterval(() => go(i + 1), 6000); };
    dots.forEach((d, n) => d.addEventListener("click", () => { go(n); play(); }));
    $("[data-prev]", slider)?.addEventListener("click", () => { go(i - 1); play(); });
    $("[data-next]", slider)?.addEventListener("click", () => { go(i + 1); play(); });
    let sx = null;
    slider.addEventListener("touchstart", (e) => (sx = e.touches[0].clientX), { passive: true });
    slider.addEventListener("touchend", (e) => {
      if (sx === null) return;
      const dx = e.changedTouches[0].clientX - sx;
      if (Math.abs(dx) > 50) { go(dx > 0 ? i + 1 : i - 1); play(); }
      sx = null;
    });
    go(0); play();
  }

  async function post(url, data) {
    const res = await fetch(url, {
      method: "POST", body: data,
      headers: { "X-CSRFToken": csrf(), "X-Requested-With": "fetch" }, credentials: "same-origin",
    });
    let json = {};
    try { json = await res.json(); } catch (_) { }
    json.status = res.status;
    return json;
  }
  function setCartCount(n) {
    $$("[data-cart-count]").forEach((b) => {
      b.textContent = fa(n); b.dataset.count = n;
      b.classList.remove("bump"); void b.offsetWidth; b.classList.add("bump");
    });
  }

  function flyToCart(fromEl) {
    const target = $(".header [data-cart-icon]");
    if (!fromEl || !target) return;
    const a = fromEl.getBoundingClientRect(), b = target.getBoundingClientRect();
    const ghost = fromEl.cloneNode(true);
    Object.assign(ghost.style, {
      position: "fixed", left: a.left + "px", top: a.top + "px", width: a.width + "px", height: a.height + "px",
      zIndex: 9999, borderRadius: "18px", objectFit: "cover", pointerEvents: "none",
      transition: "all .85s cubic-bezier(.6,-0.1,.3,1)", opacity: ".9",
    });
    document.body.appendChild(ghost);
    requestAnimationFrame(() => {
      Object.assign(ghost.style, {
        left: b.left + b.width / 2 - 15 + "px", top: b.top + b.height / 2 - 15 + "px",
        width: "30px", height: "30px", opacity: ".3", borderRadius: "50%",
      });
    });
    setTimeout(() => ghost.remove(), 900);
  }

  $$("form[data-ajax-cart]").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = form.querySelector("[type=submit]");
      if (form.dataset.needVariant === "1" && !form.querySelector("[name=variant]").value) {
        toast("لطفاً سایز / رنگ را انتخاب کنید.", "warning");
        $(".opt-group")?.animate([{ transform: "translateX(0)" }, { transform: "translateX(-8px)" }, { transform: "translateX(8px)" }, { transform: "translateX(0)" }], { duration: 350 });
        return;
      }
      btn?.classList.add("loading");
      try {
        const r = await post(form.action, new FormData(form));
        if (r.ok) {
          setCartCount(r.count);
          flyToCart(form.closest(".product-card, .pd")?.querySelector("img"));
        }
        toast(r.message || "خطا در ارتباط", r.ok ? "success" : "error");
      } catch (_) {
        toast("خطا در ارتباط با سرور", "error");
      } finally { btn?.classList.remove("loading"); }
    });
  });

  document.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-wish]");
    if (!btn) return;
    e.preventDefault();
    const r = await post(btn.dataset.wish, new FormData());
    if (r.login) { toast(r.message, "info"); setTimeout(() => (location.href = "/accounts/login/?next=" + encodeURIComponent(location.pathname)), 900); return; }
    if (r.ok) {
      $$(`[data-wish="${btn.dataset.wish}"]`).forEach((b) => {
        b.classList.toggle("active", r.active); b.classList.remove("pop"); void b.offsetWidth; b.classList.add("pop");
      });
      toast(r.message, "success");
      if (!r.active && btn.dataset.removeCard) {
        const card = btn.closest(".product-card");
        card.style.transition = "all .4s"; card.style.opacity = 0; card.style.transform = "scale(.9)";
        setTimeout(() => card.remove(), 400);
      }
    }
  });

  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-qty]");
    if (!b) return;
    const input = b.closest(".qty").querySelector("input");
    const max = parseInt(input.max || "999", 10), min = parseInt(input.min || "1", 10);
    const v = Math.min(max, Math.max(min, (parseInt(input.value, 10) || 1) + parseInt(b.dataset.qty, 10)));
    if (v !== parseInt(input.value, 10)) { input.value = v; input.dispatchEvent(new Event("change", { bubbles: true })); }
  });

  const cartPage = $("[data-cart-page]");
  if (cartPage) {
    let t;
    cartPage.addEventListener("change", (e) => {
      const input = e.target.closest(".cart-item input[name=qty]");
      if (!input) return;
      clearTimeout(t);
      t = setTimeout(async () => {
        const item = input.closest(".cart-item");
        const fd = new FormData(); fd.append("key", item.dataset.key); fd.append("qty", input.value);
        await post(cartPage.dataset.updateUrl, fd);
        location.reload();
      }, 450);
    });
    cartPage.addEventListener("click", async (e) => {
      const b = e.target.closest("[data-remove]");
      if (!b) return;
      const item = b.closest(".cart-item");
      item.classList.add("removing");
      const fd = new FormData(); fd.append("key", item.dataset.key);
      const r = await post(cartPage.dataset.removeUrl, fd);
      setCartCount(r.count || 0);
      setTimeout(() => location.reload(), 380);
    });
  }

  const vData = $("#variants-data");
  if (vData) {
    const variants = JSON.parse(vData.textContent);
    const form = $("form[data-ajax-cart]");
    const vInput = form.querySelector("[name=variant]");
    const qtyInput = form.querySelector("[name=qty]");
    const priceEl = $("[data-price]");
    const stockEl = $("[data-stock]");
    const colorLabel = $("[data-color-label]");
    let color = null, size = null;
    const hasColors = variants.some((v) => v.color), hasSizes = variants.some((v) => v.size);

    function refresh() {
      $$(".size-btn").forEach((b) => {
        const ok = variants.some((v) => v.size === b.dataset.size && (!hasColors || !color || v.color === color) && v.stock > 0);
        b.classList.toggle("disabled", !ok);
        if (!ok && size === b.dataset.size) { size = null; b.classList.remove("active"); }
      });
      const match = variants.find((v) => (!hasColors || v.color === color) && (!hasSizes || v.size === size));
      vInput.value = match ? match.id : "";
      if (match) {
        if (priceEl) priceEl.textContent = money(match.price);
        qtyInput.max = Math.max(1, match.stock);
        if (+qtyInput.value > match.stock) qtyInput.value = Math.max(1, match.stock);
        if (stockEl) {
          stockEl.innerHTML = match.stock <= 0 ? '<i class="dot out"></i> ناموجود'
            : match.stock <= 3 ? `<i class="dot low"></i> فقط ${fa(match.stock)} عدد باقی مانده`
            : '<i class="dot"></i> موجود در انبار';
        }
      }
    }
    $$(".swatch").forEach((s) => s.addEventListener("click", () => {
      $$(".swatch").forEach((x) => x.classList.remove("active")); s.classList.add("active");
      color = s.dataset.color; if (colorLabel) colorLabel.textContent = color; refresh();
    }));
    $$(".size-btn").forEach((b) => b.addEventListener("click", () => {
      $$(".size-btn").forEach((x) => x.classList.remove("active")); b.classList.add("active");
      size = b.dataset.size; refresh();
    }));
    const sw = $$(".swatch"); if (sw.length === 1) sw[0].click();
    const sz = $$(".size-btn:not(.disabled)"); if (sz.length === 1) sz[0].click();
    refresh();
  }

  const gMain = $(".gallery-main");
  if (gMain) {
    const img = gMain.querySelector("img");
    $$(".gallery-thumbs button").forEach((b) => b.addEventListener("click", () => {
      $$(".gallery-thumbs button").forEach((x) => x.classList.remove("active")); b.classList.add("active");
      img.style.opacity = 0;
      setTimeout(() => { img.src = b.dataset.src; img.style.opacity = 1; }, 180);
    }));
    if (window.matchMedia("(hover: hover)").matches) {
      gMain.addEventListener("mouseenter", () => gMain.classList.add("zoom"));
      gMain.addEventListener("mouseleave", () => { gMain.classList.remove("zoom"); img.style.transformOrigin = "center"; });
      gMain.addEventListener("mousemove", (e) => {
        const r = gMain.getBoundingClientRect();
        img.style.transformOrigin = `${((e.clientX - r.left) / r.width) * 100}% ${((e.clientY - r.top) / r.height) * 100}%`;
      });
    }
  }

  $$(".tabs").forEach((tabs) => {
    const btns = $$(".tab-nav button", tabs), panels = $$(".tab-panel", tabs);
    btns.forEach((b, n) => b.addEventListener("click", () => {
      btns.forEach((x) => x.classList.remove("active")); panels.forEach((x) => x.classList.remove("active"));
      b.classList.add("active"); panels[n].classList.add("active");
    }));
  });

  async function copyText(text) {
    try { await navigator.clipboard.writeText(text); return true; } catch (_) {
      const ta = document.createElement("textarea"); ta.value = text; ta.style.position = "fixed"; ta.style.opacity = 0;
      document.body.appendChild(ta); ta.select();
      let ok = false; try { ok = document.execCommand("copy"); } catch (_) { }
      ta.remove(); return ok;
    }
  }
  window.copyText = copyText;
  document.addEventListener("click", async (e) => {
    const b = e.target.closest("[data-copy]");
    if (!b) return;
    const src = b.dataset.copy.startsWith("#") ? $(b.dataset.copy) : null;
    const text = src ? (src.value || src.innerText) : b.dataset.copy;
    if (await copyText(text.trim())) {
      toast(b.dataset.copyMsg || "کپی شد ✓", "success", 2500);
      b.classList.add("copied");
    } else toast("کپی انجام نشد؛ متن را دستی انتخاب کنید.", "error");
  });

  $$("[data-copy-then-open]").forEach((a) => a.addEventListener("click", async () => {
    const src = $(a.dataset.copyThenOpen);
    if (src && (await copyText(src.innerText.trim()))) toast("پیام کپی شد؛ در گفتگو Paste کنید و بفرستید.", "success", 4500);
  }));

  $$(".progress-steps").forEach((p) => {
    const step = parseInt(p.dataset.step, 10);
    const fill = p.querySelector(".fill");
    if (fill && step >= 0) setTimeout(() => (fill.style.width = (step / 4) * 80 + "%"), 300);
  });
  $$(".bar i[data-w]").forEach((b) => setTimeout(() => (b.style.width = b.dataset.w + "%"), 300));

  document.addEventListener("input", (e) => {
    const el = e.target;
    if (el.matches("input[inputmode=numeric], input[inputmode=tel], input[type=number]")) {
      const v = el.value.replace(/[۰-۹]/g, (d) => "۰۱۲۳۴۵۶۷۸۹".indexOf(d)).replace(/[٠-٩]/g, (d) => "٠١٢٣٤٥٦٧٨٩".indexOf(d));
      if (v !== el.value) el.value = v;
    }
  });

  $$("form[data-once]").forEach((f) => f.addEventListener("submit", () => {
    const b = f.querySelector("[type=submit]"); if (b) { b.classList.add("loading"); }
  }));

  document.addEventListener("submit", (e) => {
    const msg = e.target.dataset.confirm;
    if (msg && !confirm(msg)) e.preventDefault();
  }, true);
})();
