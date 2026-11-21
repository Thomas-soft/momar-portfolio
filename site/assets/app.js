/* =====================================================================
   Momar Gaye — portfolio : comportement du site
   Pas de framework, pas de module, pas de compilation.
   Le contenu vient de content.js (window.SITE). Ne pas éditer ici pour
   changer un texte ou un projet : tout se fait dans content.js.
   ===================================================================== */
(function () {
  "use strict";

  var S = window.SITE || {};
  var D = document;
  var H = D.documentElement;

  /* ------------------------------------------------------------------
     Outils
     ------------------------------------------------------------------ */
  function $(s, r) { return (r || D).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || D).querySelectorAll(s)); }
  function el(tag, attrs, html) {
    var n = D.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (attrs[k] === null || attrs[k] === undefined || attrs[k] === false) continue;
      if (k === "class") n.className = attrs[k];
      else n.setAttribute(k, attrs[k] === true ? "" : attrs[k]);
    }
    if (html !== undefined) n.innerHTML = html;
    return n;
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function clamp(v, a, b) { return Math.min(b, Math.max(a, v)); }
  function pad2(n) { return (n < 10 ? "0" : "") + n; }
  function fmt(s) {
    if (!isFinite(s) || s < 0) s = 0;
    s = Math.floor(s);
    var h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = s % 60;
    return (h ? h + ":" + pad2(m) : m) + ":" + pad2(x);
  }
  function ratioCss(r) {
    var m = String(r || "16/9").match(/^\s*([\d.]+)\s*[/:x]\s*([\d.]+)\s*$/);
    return m ? m[1] + " / " + m[2] : "16 / 9";
  }
  function ratioNum(r) {
    var m = String(r || "16/9").match(/^\s*([\d.]+)\s*[/:x]\s*([\d.]+)\s*$/);
    return m ? (parseFloat(m[1]) / parseFloat(m[2])) : 16 / 9;
  }
  function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function safe(name, fn) {
    try { fn(); } catch (e) { if (window.console) console.warn("[portfolio] " + name, e); }
  }

  var mqReduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  var mqHover = window.matchMedia("(hover: hover) and (pointer: fine)");
  var conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  var saveData = !!(conn && conn.saveData);
  var lowEnd = saveData || (typeof navigator.deviceMemory === "number" && navigator.deviceMemory <= 2);
  function reduce() { return mqReduce.matches; }

  var ICON = {
    play: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 4.5v15l13-7.5z"/></svg>',
    pause: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="4.5" width="3.6" height="15"/><rect x="14.4" y="4.5" width="3.6" height="15"/></svg>',
    vol: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z" fill="currentColor" stroke="none"/><path d="M15.5 9a4.2 4.2 0 0 1 0 6M18.2 6.4a8 8 0 0 1 0 11.2"/></svg>',
    muted: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z" fill="currentColor" stroke="none"/><path d="M16 9.5l5 5M21 9.5l-5 5"/></svg>',
    fs: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>',
    fsExit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5"/></svg>',
    chevL: '<svg viewBox="0 0 7 12" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M6 1L1 6l5 5"/></svg>',
    chevR: '<svg viewBox="0 0 7 12" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M1 1l5 5-5 5"/></svg>',
    arrL: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><path d="M10 3L5 8l5 5"/></svg>',
    arrR: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><path d="M6 3l5 5-5 5"/></svg>'
  };

  /* ------------------------------------------------------------------
     Langue (FR / EN)
     ------------------------------------------------------------------ */
  var LANG_KEY = "momar-lang";
  var lang = detectLang();
  var langHooks = [];

  function detectLang() {
    var q = null;
    try { q = new URLSearchParams(location.search).get("lang"); } catch (e) {}
    if (q === "fr" || q === "en") return q;
    try {
      var s = localStorage.getItem(LANG_KEY);
      if (s === "fr" || s === "en") return s;
    } catch (e) {}
    var n = (navigator.languages && navigator.languages[0]) || navigator.language || "fr";
    return /^fr\b/i.test(n) ? "fr" : "en";
  }
  function t(k) {
    var u = S.ui || {};
    return (u[lang] && u[lang][k] != null) ? u[lang][k] : ((u.fr && u.fr[k]) || "");
  }
  function L(v) {
    if (v == null) return "";
    if (typeof v === "string" || typeof v === "number") return String(v);
    return v[lang] || v.fr || v.en || "";
  }
  function filled(v) { return L(v).trim() !== ""; }
  function onLang(fn) { langHooks.push(fn); fn(); }

  function setLang(l, remember) {
    if (l !== "fr" && l !== "en") return;
    lang = l;
    H.lang = l;
    if (remember) {
      try { localStorage.setItem(LANG_KEY, l); } catch (e) {}
      try {
        var u = new URL(location.href);
        if (u.searchParams.has("lang")) {
          u.searchParams.set("lang", l);
          history.replaceState(history.state, "", u.pathname + u.search + u.hash);
        }
      } catch (e) {}
    }
    applyStatic();
    langHooks.forEach(function (fn) { safe("lang", fn); });
  }

  function applyStatic() {
    $$("[data-i18n]").forEach(function (n) { var v = t(n.getAttribute("data-i18n")); if (v) n.textContent = v; });
    $$("[data-i18n-aria]").forEach(function (n) { var v = t(n.getAttribute("data-i18n-aria")); if (v) n.setAttribute("aria-label", v); });
    $$("[data-lang]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-lang") === lang)); });
    if (!project.open) D.title = t("metaTitle") || D.title;
    var md = $('meta[name="description"]');
    if (md && t("metaDesc")) md.setAttribute("content", t("metaDesc"));
  }

  function categoryLabel(c) {
    var list = Array.isArray(c) ? c : (c ? [c] : []);
    var map = { filmmaking: "catFilmmaking", editing: "catEditing", color: "catColor", "color grading": "catColor" };
    return list.filter(Boolean).map(function (x) {
      var k = map[String(x).toLowerCase()];
      return k ? t(k) : L(x);
    }).join(" · ");
  }
  function projectById(id) {
    var P = S.projets || [];
    for (var i = 0; i < P.length; i++) if (P[i].id === id) return P[i];
    return null;
  }

  /* ------------------------------------------------------------------
     Masquer le reste de la page sous un calque (accessibilité)
     ------------------------------------------------------------------ */
  var inertCount = 0;
  function setBackgroundInert(on) {
    inertCount = Math.max(0, inertCount + (on ? 1 : -1));
    var v = inertCount > 0;
    ["#contenu", ".foot", ".skip", "#nav"].forEach(function (s) {
      var n = $(s);
      if (!n) return;
      if (v) n.setAttribute("inert", ""); else n.removeAttribute("inert");
    });
  }
  var scrollLocks = 0;
  var lenis = null; // défilement fluide (Lenis), null quand il est éteint
  function lockScroll(on) {
    scrollLocks = Math.max(0, scrollLocks + (on ? 1 : -1));
    H.classList.toggle("no-scroll", scrollLocks > 0);
    // Calque ouvert (page projet, visionneuse, comparateur agrandi, menu) : page figée.
    if (lenis) { if (scrollLocks > 0) lenis.stop(); else lenis.start(); }
  }

  /* ------------------------------------------------------------------
     Défilement fluide (Lenis, copié dans assets/vendor/, licence MIT)
     Molette et pavé : défilement doux. Au doigt : défilement natif.
     Éteint avec « réduire les animations » (même si la préférence change en cours
     de visite) ou avec smoothScroll: false dans content.js.
     ------------------------------------------------------------------ */
  function initSmoothScroll() {
    if (S.smoothScroll === false || typeof window.Lenis !== "function") return;
    var mq = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;
    var raf = 0;
    function loop(time) {
      if (!lenis) return;
      lenis.raf(time);
      raf = requestAnimationFrame(loop);
    }
    function start() {
      if (lenis || (mq && mq.matches)) return;
      lenis = new window.Lenis({ lerp: 0.1, smoothWheel: true, syncTouch: false, wheelMultiplier: 1 });
      if (scrollLocks > 0) lenis.stop();
      raf = requestAnimationFrame(loop);
    }
    function stop() {
      if (!lenis) return;
      cancelAnimationFrame(raf);
      lenis.destroy();
      lenis = null;
    }
    start();
    if (mq) {
      var change = function () { if (mq.matches) stop(); else start(); };
      if (mq.addEventListener) mq.addEventListener("change", change);
      else if (mq.addListener) mq.addListener(change);
    }

    // Liens vers les sections (#realisations, #contact…) : défilement doux, menu déduit.
    // Les adresses #/projet/<id> restent au routeur ; le lien d'évitement reste natif.
    D.addEventListener("click", function (e) {
      if (!lenis || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var a = e.target.closest ? e.target.closest('a[href^="#"]') : null;
      if (!a || a.classList.contains("skip")) return;
      var href = a.getAttribute("href");
      if (href.length < 2 || href.charAt(1) === "/") return;
      var target = D.getElementById(decodeURIComponent(href.slice(1)));
      if (!target) return;
      e.preventDefault();
      var offset = parseFloat(getComputedStyle(H).scrollPaddingTop) || 0; // hauteur du menu + marge
      lenis.scrollTo(target, { offset: -offset });
      if (location.hash !== href) { try { history.pushState(null, "", href); } catch (err) {} }
      if (e.detail === 0) { // activé au clavier : le focus suit, comme un lien normal
        if (!target.hasAttribute("tabindex")) { target.setAttribute("tabindex", "-1"); target.setAttribute("data-cible-lien", ""); }
        target.focus({ preventScroll: true });
      }
    });
  }

  /* ------------------------------------------------------------------
     Plein écran : API standard, préfixe WebKit, sinon calque de secours
     ------------------------------------------------------------------ */
  function fsElement() { return D.fullscreenElement || D.webkitFullscreenElement || null; }
  function canFs(node) { return !!(node.requestFullscreen || node.webkitRequestFullscreen); }
  function enterFs(node) {
    var fn = node.requestFullscreen || node.webkitRequestFullscreen;
    try {
      var r = fn.call(node);
      return (r && r.then) ? r : Promise.resolve();
    } catch (e) { return Promise.reject(e); }
  }
  function exitFs() {
    var fn = D.exitFullscreen || D.webkitExitFullscreen;
    if (fn && fsElement()) { try { var r = fn.call(D); if (r && r.catch) r.catch(function () {}); } catch (e) {} }
  }
  var pseudoStack = []; // calques « plein écran » de secours ouverts (fermés par Échap)

  /* ------------------------------------------------------------------
     Menu
     ------------------------------------------------------------------ */
  function initNav() {
    var nav = $("#nav");
    var burger = $(".nav__burger");
    var menu = $("#menu-mobile");

    $$("[data-lang]").forEach(function (b) {
      b.addEventListener("click", function () { setLang(b.getAttribute("data-lang"), true); });
    });

    function burgerText(key) {
      var tx = $(".nav__burger-txt", burger);
      tx.setAttribute("data-i18n", key);
      tx.textContent = t(key);
    }
    function openMenu() {
      menu.hidden = false;
      burger.setAttribute("aria-expanded", "true");
      burgerText("close");
      lockScroll(true);
      ["#contenu", ".foot"].forEach(function (s) { $(s).setAttribute("inert", ""); });
      requestAnimationFrame(function () { menu.classList.add("is-open"); });
      var first = $("a", menu); if (first) first.focus({ preventScroll: true });
    }
    function closeMenu(focusBurger) {
      if (menu.hidden) return;
      menu.classList.remove("is-open");
      burger.setAttribute("aria-expanded", "false");
      burgerText("menu");
      lockScroll(false);
      ["#contenu", ".foot"].forEach(function (s) { if (!inertCount) $(s).removeAttribute("inert"); });
      setTimeout(function () { menu.hidden = true; }, 300);
      if (focusBurger) burger.focus({ preventScroll: true });
    }
    burger.addEventListener("click", function () {
      if (menu.hidden) openMenu(); else closeMenu(true);
    });
    $$("a", menu).forEach(function (a) { a.addEventListener("click", function () { closeMenu(false); }); });
    initNav.closeMenu = closeMenu;
    window.addEventListener("resize", function () { if (window.innerWidth > 860) closeMenu(false); });

    var ticking = false;
    function onScroll() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        nav.classList.toggle("is-scrolled", window.scrollY > 40);
        ticking = false;
      });
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    if ("IntersectionObserver" in window) {
      var links = $$(".nav__links a");
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          links.forEach(function (a) { a.classList.toggle("is-current", a.getAttribute("href") === "#" + e.target.id); });
        });
      }, { rootMargin: "-45% 0px -50% 0px" });
      ["accueil", "showreel", "realisations", "etalonnage", "apropos", "contact"].forEach(function (id) {
        var s = D.getElementById(id); if (s) io.observe(s);
      });
    }
  }

  /* ------------------------------------------------------------------
     Accueil : nom qui s'assemble, vidéo de fond, parallaxe légère
     ------------------------------------------------------------------ */
  function buildName() {
    var h = $("#hero-name");
    var name = S.nom || h.textContent.trim();
    h.textContent = "";
    h.appendChild(el("span", { class: "sr-only" }, esc(name)));
    // Une seule police (Garamond), un mot par bloc : l'approche des lettres reste intacte.
    name.split(/\s+/).forEach(function (word) {
      h.appendChild(el("span", { class: "w", "aria-hidden": "true" }, esc(word)));
    });
    var roles = $("#hero-roles");
    if (roles && Array.isArray(S.roles) && S.roles.length) {
      roles.innerHTML = S.roles.map(function (r) { return "<span>" + esc(r) + "</span>"; }).join(" ");
    }
  }

  function animateName() {
    // Apparition sobre, une seule fois : chaque mot monte légèrement en fondu.
    // Durée totale ≤ 1,8 s (cahier §2 et §9). Aucune animation avec « réduire les animations ».
    var words = $$("#hero-name .w");
    if (!words.length || !words[0].animate || reduce()) return;
    words.forEach(function (w, i) {
      w.animate([
        { transform: "translateY(0.22em)", opacity: 0, letterSpacing: "0.04em" },
        { transform: "none", opacity: 1, letterSpacing: "-0.01em" }
      ], { duration: 1300, delay: 120 + i * 260, easing: "cubic-bezier(.2,.7,.1,1)", fill: "backwards" });
    });
  }

  function initHero() {
    buildName();
    var hero = $(".hero");
    var name = $("#hero-name");
    var a = S.accueil || {};
    var poster = $(".hero__poster");
    var small = Math.min(window.innerWidth, (screen && screen.width) || 9999) < 1000;
    if (a.poster && poster.getAttribute("src") !== a.poster) poster.src = a.poster;
    if (a.poster && a.poster720) {
      var ss = a.poster720 + " 1280w, " + a.poster + " 1920w";
      if (poster.getAttribute("srcset") !== ss) poster.setAttribute("srcset", ss);
    } else if (!a.poster720) poster.removeAttribute("srcset");
    poster.addEventListener("error", function () { poster.style.visibility = "hidden"; });

    var started = false;
    function go() {
      if (started) return;
      started = true;
      name.classList.add("is-ready");
      safe("name", animateName);
      setTimeout(function () {
        hero.classList.add("is-in");
        H.classList.add("is-in-nav");
      }, reduce() ? 0 : 650);
    }
    // On attend la police du nom (EB Garamond), 900 ms au plus, pour ne pas l'animer dans une autre police.
    var fontsReady = (D.fonts && D.fonts.load)
      ? D.fonts.load('500 100px "EB Garamond"').then(function () { return D.fonts.ready; })
      : Promise.resolve();
    Promise.race([fontsReady, wait(900)]).then(go, go);

    // Vidéo de fond : jamais avec « réduire les animations » ou « économie de données ».
    var v = $(".hero__video");
    var src = small ? (a.video720 || a.video1080) : (a.video1080 || a.video720);
    if (src && !reduce() && !saveData) {
      v.muted = true;
      v.setAttribute("muted", "");
      v.setAttribute("autoplay", "");
      var vp = (small && a.poster720) ? a.poster720 : a.poster;
      if (vp) v.poster = vp;
      v.addEventListener("playing", function () { v.classList.add("is-ready"); });
      v.addEventListener("error", function () { v.classList.remove("is-ready"); v.removeAttribute("src"); }, true);
      v.src = src;
      var p = v.play(); if (p && p.catch) p.catch(function () {});
      if ("IntersectionObserver" in window) {
        new IntersectionObserver(function (es) {
          es.forEach(function (e) {
            if (!v.getAttribute("src")) return;
            if (e.isIntersecting) { var q = v.play(); if (q && q.catch) q.catch(function () {}); }
            else v.pause();
          });
        }, { threshold: 0.01 }).observe(hero);
      }
      mqReduce.addEventListener && mqReduce.addEventListener("change", function () { if (reduce()) v.pause(); });
    }

    // Parallaxe très légère du titre (désactivée avec « réduire les animations »).
    var content = $(".hero__content");
    var tick = false;
    window.addEventListener("scroll", function () {
      if (tick || reduce()) return;
      tick = true;
      requestAnimationFrame(function () {
        var y = window.scrollY, hh = hero.offsetHeight;
        if (y <= hh) {
          content.style.transform = "translate3d(0," + (y * 0.22).toFixed(1) + "px,0)";
          content.style.opacity = String(clamp(1 - y / (hh * 0.85), 0, 1));
        }
        tick = false;
      });
    }, { passive: true });
  }

  /* ------------------------------------------------------------------
     Lecteur vidéo maison
     ------------------------------------------------------------------ */
  function createPlayer(opts) {
    opts = opts || {};
    var root = el("div", { class: "player" });
    root.innerHTML =
      '<div class="player__stage">' +
        '<video playsinline preload="none" disablepictureinpicture></video>' +
        '<div class="player__spin" aria-hidden="true"></div>' +
        '<button class="player__big" type="button">' + ICON.play + "</button>" +
        '<div class="player__msg" hidden></div>' +
      "</div>" +
      '<div class="pbar">' +
        '<button class="pbar__btn pb-play" type="button">' + ICON.play + "</button>" +
        '<span class="pbar__time" aria-hidden="true">0:00 / 0:00</span>' +
        '<div class="prog" role="slider" tabindex="0" aria-valuemin="0" aria-valuemax="0" aria-valuenow="0"><div class="prog__buf"></div><div class="prog__fill"></div></div>' +
        '<button class="pbar__btn pb-mute" type="button">' + ICON.vol + "</button>" +
        '<button class="pbar__btn pb-fs" type="button">' + ICON.fs + "</button>" +
      "</div>";
    var stage = $(".player__stage", root);
    var v = $("video", root);
    var big = $(".player__big", root);
    var msg = $(".player__msg", root);
    var bPlay = $(".pb-play", root), bMute = $(".pb-mute", root), bFs = $(".pb-fs", root);
    var time = $(".pbar__time", root), prog = $(".prog", root);
    var fill = $(".prog__fill", root), buf = $(".prog__buf", root);
    var raf = 0, idleT = 0, dragging = false, pseudo = false, label = "", forcedMute = false;

    function labels() {
      big.setAttribute("aria-label", t("play") + (label ? " — " + label : ""));
      bPlay.setAttribute("aria-label", v.paused ? t("play") : t("pause"));
      bMute.setAttribute("aria-label", v.muted ? t("unmute") : t("mute"));
      bFs.setAttribute("aria-label", isFs() ? t("exitFullscreen") : t("fullscreen"));
      prog.setAttribute("aria-label", t("seek"));
      if (!msg.hidden) msg.textContent = t("videoError");
    }
    onLang(labels);

    function isFs() { return fsElement() === root || pseudo; }
    function ui() {
      var d = v.duration || 0, c = v.currentTime || 0;
      fill.style.width = d ? (c / d * 100) + "%" : "0";
      time.textContent = fmt(c) + " / " + fmt(d);
      prog.setAttribute("aria-valuemax", String(Math.floor(d)));
      prog.setAttribute("aria-valuenow", String(Math.floor(c)));
      prog.setAttribute("aria-valuetext", fmt(c) + " / " + fmt(d));
      try {
        if (d && v.buffered.length) buf.style.width = (v.buffered.end(v.buffered.length - 1) / d * 100) + "%";
      } catch (e) {}
    }
    function loop() { ui(); if (!v.paused) raf = requestAnimationFrame(loop); }
    function showError() {
      msg.hidden = false;
      msg.textContent = t("videoError");
      root.classList.add("has-started");
      root.classList.remove("is-waiting");
    }
    function play() {
      if (!v.getAttribute("src")) { showError(); return; }
      root.classList.add("has-started");
      var p = v.play();
      if (p && p.catch) p.catch(function (err) {
        if (err && err.name === "NotAllowedError") root.classList.remove("has-started");
      });
    }
    function toggle() { if (v.paused || v.ended) play(); else v.pause(); }
    function seek(s) { if (v.duration) { v.currentTime = clamp(s, 0, v.duration); ui(); } }
    function setPseudo(on) {
      if (pseudo === on) return;
      pseudo = on;
      root.classList.toggle("is-pseudo-fs", on);
      lockScroll(on);
      if (on) pseudoStack.push(api); else pseudoStack = pseudoStack.filter(function (x) { return x !== api; });
      labels();
    }
    function fullscreen() {
      if (fsElement() === root) { exitFs(); return; }
      if (pseudo) { setPseudo(false); return; }
      if (canFs(root)) { enterFs(root).catch(function () { setPseudo(true); }); return; }
      if (v.webkitEnterFullscreen) { // iPhone : lecteur natif plein écran
        try {
          if (v.readyState < 1) { play(); v.addEventListener("loadedmetadata", function f() { v.removeEventListener("loadedmetadata", f); try { v.webkitEnterFullscreen(); } catch (e) {} }); }
          else v.webkitEnterFullscreen();
          return;
        } catch (e) {}
      }
      setPseudo(true);
    }
    function idle() {
      root.classList.remove("is-idle");
      clearTimeout(idleT);
      if (!v.paused) idleT = setTimeout(function () { root.classList.add("is-idle"); }, 2600);
    }

    v.addEventListener("play", function () {
      root.classList.add("has-started");
      bPlay.innerHTML = ICON.pause; labels(); cancelAnimationFrame(raf); loop(); idle();
    });
    v.addEventListener("pause", function () { bPlay.innerHTML = ICON.play; labels(); ui(); idle(); });
    v.addEventListener("waiting", function () { root.classList.add("is-waiting"); });
    ["playing", "canplay", "pause", "error"].forEach(function (e) { v.addEventListener(e, function () { root.classList.remove("is-waiting"); }); });
    v.addEventListener("loadedmetadata", ui);
    v.addEventListener("progress", ui);
    v.addEventListener("timeupdate", function () { if (v.paused) ui(); });
    v.addEventListener("volumechange", function () { bMute.innerHTML = v.muted ? ICON.muted : ICON.vol; labels(); });
    v.addEventListener("error", function () { if (v.getAttribute("src")) showError(); });

    big.addEventListener("click", function (e) { e.stopPropagation(); play(); });
    stage.addEventListener("click", function (e) { if (e.target === big || big.contains(e.target)) return; toggle(); });
    stage.addEventListener("dblclick", fullscreen);
    bPlay.addEventListener("click", toggle);
    bMute.addEventListener("click", function () { v.muted = !v.muted; });
    bFs.addEventListener("click", fullscreen);
    root.addEventListener("pointermove", idle);
    D.addEventListener("fullscreenchange", function () { bFs.innerHTML = isFs() ? ICON.fsExit : ICON.fs; labels(); });
    D.addEventListener("webkitfullscreenchange", function () { bFs.innerHTML = isFs() ? ICON.fsExit : ICON.fs; labels(); });

    function seekFromEvent(e) {
      var r = prog.getBoundingClientRect();
      seek((e.clientX - r.left) / r.width * (v.duration || 0));
    }
    prog.addEventListener("pointerdown", function (e) {
      if (!v.duration) return;
      dragging = true;
      prog.classList.add("is-drag");
      try { prog.setPointerCapture(e.pointerId); } catch (x) {}
      seekFromEvent(e);
    });
    prog.addEventListener("pointermove", function (e) { if (dragging) seekFromEvent(e); });
    ["pointerup", "pointercancel"].forEach(function (n) {
      prog.addEventListener(n, function () { dragging = false; prog.classList.remove("is-drag"); });
    });

    root.addEventListener("keydown", function (e) {
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      var onBtn = e.target.tagName === "BUTTON";
      switch (e.key) {
        case " ": case "k": case "K":
          if (onBtn && e.key === " ") return;
          e.preventDefault(); toggle(); break;
        case "ArrowLeft": e.preventDefault(); seek(v.currentTime - 5); break;
        case "ArrowRight": e.preventDefault(); seek(v.currentTime + 5); break;
        case "j": case "J": seek(v.currentTime - 10); break;
        case "l": case "L": seek(v.currentTime + 10); break;
        case "Home": if (e.target === prog) { e.preventDefault(); seek(0); } break;
        case "End": if (e.target === prog) { e.preventDefault(); seek(v.duration); } break;
        case "m": case "M": if (!bMute.hidden) v.muted = !v.muted; break;
        case "f": case "F": e.preventDefault(); fullscreen(); break;
        default: return;
      }
      idle();
    });

    function load(o) {
      o = o || {};
      label = o.label || "";
      v.pause();
      root.classList.remove("has-started", "is-waiting", "is-idle");
      msg.hidden = true;
      root.style.setProperty("--ar", ratioCss(o.ratio));
      if (o.poster) v.poster = o.poster; else v.removeAttribute("poster");
      // Vidéo sans son : pas de bouton son.
      var noAudio = o.audio === false;
      bMute.hidden = noAudio;
      if (noAudio) { v.muted = true; forcedMute = true; }
      else if (forcedMute) { v.muted = false; forcedMute = false; }
      if (o.src) { v.src = o.src; v.preload = o.preload || "none"; }
      else { v.removeAttribute("src"); showError(); }
      try { v.load(); } catch (e) {}
      fill.style.width = "0"; buf.style.width = "0";
      time.textContent = "0:00 / 0:00";
      bPlay.innerHTML = ICON.play;
      labels();
    }
    var api = {
      root: root, video: v, load: load, play: play,
      pause: function () { v.pause(); },
      close: function () { v.pause(); if (pseudo) setPseudo(false); if (fsElement() === root) exitFs(); },
      collapse: function () { setPseudo(false); }
    };
    if (opts.src !== undefined) load(opts);
    return api;
  }

  /* ------------------------------------------------------------------
     Showreel
     ------------------------------------------------------------------ */
  function initShowreel() {
    var slot = $("#showreel-slot");
    var sr = S.showreel || {};
    if (sr.video) {
      var p = createPlayer({ src: sr.video, poster: sr.poster, ratio: sr.ratio, audio: sr.audio, label: "Showreel", preload: "none" });
      slot.appendChild(p.root);
      return;
    }
    var box = el("div", { class: "soon" });
    box.innerHTML =
      '<span class="soon__corner soon__corner--tl">' + esc(S.nom || "") + "</span>" +
      '<span class="soon__corner soon__corner--br" aria-hidden="true">00:00:00:00</span>' +
      '<div class="soon__inner"><div class="soon__ring" aria-hidden="true">' + ICON.play + '</div><p class="soon__text"></p></div>';
    slot.appendChild(box);
    onLang(function () { $(".soon__text", box).textContent = t("showreelSoon"); });
  }

  /* ------------------------------------------------------------------
     Réalisations
     ------------------------------------------------------------------ */
  function cardLayout(i, n) {
    if (i === 0) return "card--wide";
    var k = i - 1, pair = Math.floor(k / 2), first = k % 2 === 0;
    if (first && i === n - 1) return "card--wide";
    var bigFirst = pair % 2 === 0;
    return (first === bigFirst) ? "card--l" : "card--s";
  }

  var cards = [];
  function initWork() {
    var ul = $("#work-grid");
    var P = S.projets || [];
    P.forEach(function (p, i) {
      var layout = cardLayout(i, P.length);
      var li = el("li", { class: "card reveal " + layout });
      var a = el("a", { class: "card__link", href: "#/projet/" + encodeURIComponent(p.id), "data-id": p.id });
      var media = el("div", { class: "card__media" });
      // Vidéo à bandes noires latérales : la carte est recadrée sur l'image utile
      // (seules les bandes disparaissent). En grande carte : image à gauche, texte à droite.
      if (p.cadre) {
        media.style.aspectRatio = ratioCss(p.cadre);
        if (layout === "card--wide") li.classList.add("card--feature");
      }
      if (p.miniature) {
        var img = el("img", { decoding: "async", alt: "" });
        lazyImg(img, p.miniature);
        img.addEventListener("error", function () {
          img.remove();
          if (!$(".media-error", media)) media.insertBefore(el("div", { class: "media-error" }, esc(L(p.titre))), media.firstChild);
        });
        media.appendChild(img);
      } else {
        media.appendChild(el("div", { class: "media-error" }, esc(L(p.titre))));
      }
      var cue = el("span", { class: "card__cue", "aria-hidden": "true" });
      media.appendChild(cue);
      var body = el("div", { class: "card__body" });
      a.appendChild(media); a.appendChild(body);
      li.appendChild(a);
      ul.appendChild(li);
      a.addEventListener("click", function () { project.fromClick = true; project.opener = a; });
      cards.push({ li: li, a: a, media: media, cue: cue, body: body, p: p, i: i, video: null, failed: false });
    });
    onLang(function () {
      cards.forEach(function (c) {
        var p = c.p, html = "";
        html += '<span class="card__num">' + pad2(c.i + 1) + "</span>";
        html += '<h3 class="card__title">' + esc(L(p.titre)) + "</h3>";
        var meta = [];
        // Sur la carte : la catégorie seule (et l'année). Rôle et catégorie sont
        // détaillés avec leurs étiquettes dans la page projet.
        var cat = categoryLabel(p.categorie); if (cat) meta.push(cat);
        if (filled(p.annee)) meta.push(L(p.annee));
        if (meta.length) html += '<p class="card__meta">' + meta.map(function (m) { return "<span>" + esc(m) + "</span>"; }).join("") + "</p>";
        if (filled(p.description)) html += '<p class="card__desc">' + esc(L(p.description)) + "</p>";
        html += '<span class="card__more" aria-hidden="true"><i></i>' + esc(t("viewProject")) + "</span>";
        c.body.innerHTML = html;
        c.cue.innerHTML = ICON.play + "<span>" + esc(t("viewProject")) + "</span>";
      });
    });
    initPreviews();
  }

  function previewPlay(c) {
    if (!c.p.apercu || c.failed || saveData) return;
    if (!c.video) {
      var v = el("video", { muted: true, loop: true, playsinline: true, preload: "none", "aria-hidden": "true", tabindex: "-1", disablepictureinpicture: true });
      v.muted = true;
      v.addEventListener("playing", function () { if (c.want) c.li.classList.add("is-playing"); });
      v.addEventListener("error", function () { c.failed = true; c.li.classList.remove("is-playing"); v.remove(); c.video = null; });
      v.src = c.p.apercu;
      c.media.insertBefore(v, c.cue);
      c.video = v;
    }
    c.want = true;
    var pr = c.video.play();
    if (pr && pr.catch) pr.catch(function () {});
  }
  function previewStop(c) {
    c.want = false;
    c.li.classList.remove("is-playing");
    if (c.video) c.video.pause();
  }

  function initPreviews() {
    if (mqHover.matches) {
      cards.forEach(function (c) {
        c.a.addEventListener("mouseenter", function () { previewPlay(c); });
        c.a.addEventListener("mouseleave", function () { previewStop(c); });
        c.a.addEventListener("focus", function () { previewPlay(c); });
        c.a.addEventListener("blur", function () { previewStop(c); });
      });
      return;
    }
    // Téléphone et tablette : une seule carte joue, celle qui est au centre de l'écran.
    if (!("IntersectionObserver" in window)) return;
    var current = null;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var c = cards.filter(function (x) { return x.li === e.target; })[0];
        if (!c) return;
        if (e.isIntersecting) {
          if (reduce() || project.open) return;
          if (current && current !== c) previewStop(current);
          current = c; previewPlay(c);
        } else if (current === c) { previewStop(c); current = null; }
      });
    }, { rootMargin: "-42% 0px -42% 0px", threshold: 0 });
    cards.forEach(function (c) { io.observe(c.li); });
    initWork.stopAll = function () { if (current) { previewStop(current); current = null; } };
  }

  /* ------------------------------------------------------------------
     Page projet (calque plein écran, adresse #/projet/<id>)
     ------------------------------------------------------------------ */
  var project = { open: false, id: null, player: null, mode: "extrait", pushed: false, fromClick: false, opener: null, lastFocus: null };

  function route() {
    var m = location.hash.match(/^#\/projet\/([^/?#]+)/);
    if (m) {
      var id = decodeURIComponent(m[1]);
      if (projectById(id)) { openProject(id); return; }
      try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {}
    }
    if (project.open) closeProject();
  }

  function openProject(id) {
    var box = $("#project");
    var P = S.projets || [];
    var idx = P.map(function (p) { return p.id; }).indexOf(id);
    var p = P[idx];
    if (!p) return;
    var was = project.open;
    if (!was) {
      project.pushed = !!project.fromClick;
      project.lastFocus = project.opener || D.activeElement;
      box.hidden = false;
      lockScroll(true);
      setBackgroundInert(true);
      if (initWork.stopAll) initWork.stopAll();
      cards.forEach(previewStop);
      requestAnimationFrame(function () { box.classList.add("is-open"); });
    }
    var autoplay = project.fromClick && !reduce();
    project.fromClick = false;
    project.opener = null;
    if (was && project.id !== id) {
      box.classList.add("is-switching");
      if (project.player) project.player.pause();
      setTimeout(function () {
        renderProject(p, idx, false);
        $("#project-scroll").scrollTop = 0;
        box.classList.remove("is-switching");
        $("#project-title").focus({ preventScroll: true });
      }, reduce() ? 0 : 260);
    } else if (!was || project.id !== id) {
      renderProject(p, idx, autoplay);
      $("#project-scroll").scrollTop = 0;
    }
    project.open = true;
    project.id = id;
    if (!was) setTimeout(function () { $("#project-close").focus({ preventScroll: true }); }, 30);
  }

  function renderProject(p, idx, autoplay) {
    var P = S.projets || [];
    var n = P.length;
    project.mode = "extrait";
    $("#project-count").innerHTML = "<b>" + pad2(idx + 1) + "</b> / " + pad2(n);
    if (!project.player) {
      project.player = createPlayer();
      $("#project-player").appendChild(project.player.root);
    }
    loadProjectVideo(p, autoplay);
    renderProjectText(p, idx);
    D.title = L(p.titre) + " — " + (S.nom || "");
  }

  function loadProjectVideo(p, autoplay) {
    var src = project.mode === "integrale" && p.integrale ? p.integrale : p.extrait;
    project.player.load({ src: src, poster: p.poster || p.miniature, ratio: p.ratio, audio: p.audio, label: L(p.titre), preload: autoplay ? "auto" : "metadata" });
    if (autoplay) project.player.play();
  }

  function renderProjectText(p, idx) {
    var P = S.projets || [];
    var n = P.length;
    $("#project-title").textContent = L(p.titre);

    // Extrait / version intégrale (le bouton n'existe que si l'intégrale existe).
    var sw = $("#project-switch");
    sw.innerHTML = "";
    if (p.integrale) {
      sw.setAttribute("aria-label", t("projectFull"));
      [["extrait", t("projectExtract")], ["integrale", t("projectFull")]].forEach(function (m) {
        var b = el("button", { type: "button", "aria-pressed": String(project.mode === m[0]) }, esc(m[1]));
        b.addEventListener("click", function () {
          if (project.mode === m[0]) return;
          project.mode = m[0];
          $$("button", sw).forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
          loadProjectVideo(p, true);
        });
        sw.appendChild(b);
      });
    }

    var html = "";
    if (filled(p.description)) html += '<p class="project__desc">' + esc(L(p.description)) + "</p>";
    var rows = [];
    var cat = categoryLabel(p.categorie); if (cat) rows.push([t("projectCategory"), cat]);
    if (filled(p.role)) rows.push([t("projectRole"), L(p.role)]);
    if (filled(p.client)) rows.push([t("projectClient"), L(p.client)]);
    if (filled(p.annee)) rows.push([t("projectYear"), L(p.annee)]);
    (p.technique || []).forEach(function (r) { if (r && filled(r.label) && filled(r.valeur)) rows.push([L(r.label), L(r.valeur)]); });
    if (rows.length) {
      html += '<dl class="project__dl">' + rows.map(function (r) {
        return "<div><dt>" + esc(r[0]) + "</dt><dd>" + esc(r[1]) + "</dd></div>";
      }).join("") + "</dl>";
    }
    $("#project-meta").innerHTML = html;

    var nav = $("#project-nav");
    nav.innerHTML = "";
    nav.setAttribute("aria-label", t("navWork"));
    if (n > 1) {
      var prev = P[(idx - 1 + n) % n], next = P[(idx + 1) % n];
      [[prev, "projectPrev", "pnav--prev"], [next, "projectNext", "pnav--next"]].forEach(function (x) {
        var q = x[0];
        var a = el("a", { class: "pnav " + x[2], href: "#/projet/" + encodeURIComponent(q.id) });
        var img = q.miniature ? '<span class="pnav__img"' + (q.cadre ? ' style="aspect-ratio:' + esc(ratioCss(q.cadre)) + '"' : "") + '><img src="' + esc(q.miniature) + '" alt="" loading="lazy" decoding="async"></span>' : "";
        var txt = '<span class="pnav__txt"><small>' + esc(t(x[1])) + "</small><span>" + esc(L(q.titre)) + "</span></span>";
        a.innerHTML = x[2] === "pnav--next" ? txt + img : img + txt;
        var im = $("img", a); if (im) im.addEventListener("error", function () { im.parentNode.remove(); });
        a.addEventListener("click", function (e) {
          e.preventDefault();
          try { history.replaceState(null, "", "#/projet/" + encodeURIComponent(q.id)); } catch (err) {}
          project.fromClick = true;
          openProject(q.id);
        });
        nav.appendChild(a);
      });
    }
  }

  function requestCloseProject() {
    if (!project.open) return;
    if (project.pushed) { history.back(); return; }
    try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {}
    closeProject();
  }

  function closeProject() {
    if (!project.open) return;
    var box = $("#project");
    var id = project.id;
    project.open = false;
    project.pushed = false;
    if (project.player) project.player.close();
    box.classList.remove("is-open");
    setTimeout(function () { if (!project.open) box.hidden = true; }, reduce() ? 0 : 450);
    lockScroll(false);
    setBackgroundInert(false);
    D.title = t("metaTitle") || D.title;
    var back = project.lastFocus;
    if (!back || !D.body.contains(back) || back === D.body) {
      var c = cards.filter(function (x) { return x.p.id === id; })[0];
      back = c ? c.a : null;
    }
    if (back && back.focus) back.focus({ preventScroll: true });
    project.lastFocus = null;
  }

  function initProject() {
    $("#project-close").addEventListener("click", requestCloseProject);
    onLang(function () {
      if (!project.open) return;
      var P = S.projets || [];
      var idx = P.map(function (p) { return p.id; }).indexOf(project.id);
      if (idx > -1) { renderProjectText(P[idx], idx); D.title = L(P[idx].titre) + " — " + (S.nom || ""); }
    });
    window.addEventListener("hashchange", route);
    route();
  }

  /* ------------------------------------------------------------------
     Comparateur : curseur commun (souris, toucher, clavier)
     ------------------------------------------------------------------ */
  function bindCompare(stage, onChange) {
    var handle = $(".cmp__handle", stage);
    var pos = 50, animT = 0;
    var drag = null;

    function set(p, animate) {
      p = clamp(p, 0, 100);
      clearTimeout(animT);
      if (animate && !reduce()) {
        stage.classList.add("is-anim");
        animT = setTimeout(function () { stage.classList.remove("is-anim"); if (onChange) onChange(pos, false); }, 800);
      } else if (animate) {
        stage.classList.add("is-anim");
        animT = setTimeout(function () { stage.classList.remove("is-anim"); if (onChange) onChange(pos, false); }, 250);
      } else {
        stage.classList.remove("is-anim");
      }
      pos = p;
      stage.style.setProperty("--pos", p.toFixed(2) + "%");
      var r = Math.round(p);
      handle.setAttribute("aria-valuenow", String(r));
      handle.setAttribute("aria-valuetext", "LOG " + r + " % · GRADED " + (100 - r) + " %");
      stage.classList.toggle("hide-log", p < 7);
      stage.classList.toggle("hide-graded", p > 93);
      if (onChange) onChange(p, !!animate);
    }
    // Position réellement affichée (utile pendant l'animation CSS de --pos).
    function shown() {
      if (!stage.classList.contains("is-anim")) return pos;
      var v = parseFloat(getComputedStyle(stage).getPropertyValue("--pos"));
      return isFinite(v) ? v : pos;
    }
    function fromX(x) {
      var r = stage.getBoundingClientRect();
      return r.width ? (x - r.left) / r.width * 100 : pos;
    }

    stage.addEventListener("pointerdown", function (e) {
      if (e.target.closest && e.target.closest("button")) return;
      if (e.pointerType === "mouse" && e.button !== 0) return;
      drag = { id: e.pointerId, x: e.clientX, y: e.clientY, moved: false, type: e.pointerType };
      if (e.pointerType === "mouse") {
        e.preventDefault();
        try { stage.setPointerCapture(e.pointerId); } catch (x) {}
        stage.classList.add("is-drag");
        set(fromX(e.clientX));
        handle.focus({ preventScroll: true });
      }
    });
    stage.addEventListener("pointermove", function (e) {
      if (!drag || drag.id !== e.pointerId) return;
      if (drag.type !== "mouse" && !drag.moved) {
        // Au toucher : on ne prend la main que si le geste est horizontal
        // (le geste vertical reste un défilement de la page, touch-action: pan-y).
        if (Math.abs(e.clientX - drag.x) < 4) return;
        drag.moved = true;
        try { stage.setPointerCapture(e.pointerId); } catch (x) {}
        stage.classList.add("is-drag");
      }
      drag.moved = true;
      set(fromX(e.clientX));
    });
    function end(e) {
      if (!drag || drag.id !== e.pointerId) return;
      if (e.type === "pointerup" && drag.type !== "mouse" && !drag.moved) set(fromX(e.clientX), true); // simple toucher : la barre y glisse
      drag = null;
      stage.classList.remove("is-drag");
    }
    stage.addEventListener("pointerup", end);
    stage.addEventListener("pointercancel", function (e) { if (drag && drag.id === e.pointerId) { drag = null; stage.classList.remove("is-drag"); } });
    stage.addEventListener("dragstart", function (e) { e.preventDefault(); });

    handle.addEventListener("keydown", function (e) {
      var step = e.shiftKey ? 10 : 2, p = pos, anim = false;
      switch (e.key) {
        case "ArrowLeft": case "ArrowDown": p -= step; break;
        case "ArrowRight": case "ArrowUp": p += step; break;
        case "PageDown": p -= 10; break;
        case "PageUp": p += 10; break;
        case "Home": p = 0; anim = true; break;
        case "End": p = 100; anim = true; break;
        default: return;
      }
      e.preventDefault();
      set(p, anim);
    });

    set(50);
    return { set: set, get: function () { return pos; }, shown: shown, handle: handle };
  }

  function compareStageHTML(extra) {
    return (extra || "") +
      '<span class="cmp__label cmp__label--log" aria-hidden="true">LOG</span>' +
      '<span class="cmp__label cmp__label--graded" aria-hidden="true">GRADED</span>' +
      '<div class="cmp__bar" aria-hidden="true"></div>' +
      '<div class="cmp__handle" role="slider" tabindex="0" aria-valuemin="0" aria-valuemax="100" aria-valuenow="50">' + ICON.chevL + ICON.chevR + "</div>";
  }

  function segHTML() {
    return '<div class="seg" role="group">' +
      '<button type="button" data-pos="100">LOG</button>' +
      '<button type="button" data-pos="50">50 / 50</button>' +
      '<button type="button" data-pos="0">GRADED</button>' +
      "</div>";
  }
  function bindSeg(seg, ctl) {
    $$("button", seg).forEach(function (b) {
      b.addEventListener("click", function () { ctl.set(parseFloat(b.getAttribute("data-pos")), true); });
    });
    return function sync(p) {
      $$("button", seg).forEach(function (b) {
        b.setAttribute("aria-pressed", String(Math.abs(parseFloat(b.getAttribute("data-pos")) - p) < 0.5));
      });
    };
  }

  // Agrandir : plein écran natif, sinon calque fixe (iPhone).
  function bindExpand(wrap, btn, onToggle, iconOnly) {
    var pseudo = false;
    var api = { collapse: function () { setPseudo(false); } };
    function isOn() { return fsElement() === wrap || pseudo; }
    function render() {
      var on = isOn();
      if (iconOnly) {
        btn.innerHTML = on ? ICON.fsExit : ICON.fs;
        btn.setAttribute("aria-label", on ? t("exitFullscreen") : t("fullscreen"));
      } else {
        btn.innerHTML = (on ? ICON.fsExit : ICON.fs) + "<span>" + esc(on ? t("cmpShrink") : t("cmpExpand")) + "</span>";
      }
      btn.setAttribute("aria-pressed", String(on));
      if (onToggle) onToggle(on);
    }
    function setPseudo(on) {
      if (pseudo === on) return;
      pseudo = on;
      wrap.classList.toggle("is-expanded", on);
      lockScroll(on);
      if (on) pseudoStack.push(api); else pseudoStack = pseudoStack.filter(function (x) { return x !== api; });
      render();
    }
    btn.addEventListener("click", function () {
      if (fsElement() === wrap) { exitFs(); return; }
      if (pseudo) { setPseudo(false); return; }
      if (canFs(wrap)) enterFs(wrap).catch(function () { setPseudo(true); });
      else setPseudo(true);
    });
    D.addEventListener("fullscreenchange", render);
    D.addEventListener("webkitfullscreenchange", render);
    onLang(render);
    return api;
  }

  /* ------------------------------------------------------------------
     Comparateurs d'images LOG / GRADED
     ------------------------------------------------------------------ */
  function initImageCompare() {
    var host = $("#cmp-images");
    var items = ((S.comparateurs || {}).images || []).filter(function (x) { return x && x.log && x.graded; });
    if (!items.length) { host.hidden = true; host.previousElementSibling.hidden = true; return; }

    var wrap = el("div", { class: "cmpw" });
    var stage = el("div", { class: "cmp" });
    stage.innerHTML = compareStageHTML(
      '<img class="cmp__img cmp__graded" alt="" decoding="async" draggable="false">' +
      '<img class="cmp__img cmp__log" alt="" decoding="async" draggable="false">' +
      '<div class="cmp__spin" aria-hidden="true"></div>');
    var tools = el("div", { class: "cmp-tools" });
    tools.innerHTML = '<p class="cmp-caption" aria-live="polite"></p><div class="cmp-actions">' + segHTML() +
      '<button class="tbtn cmp-expand" type="button"></button></div>';
    var thumbs = el("div", { class: "thumbs", role: "group" });
    wrap.appendChild(stage); wrap.appendChild(tools); wrap.appendChild(thumbs);
    host.appendChild(wrap);

    var imgG = $(".cmp__graded", stage), imgL = $(".cmp__log", stage);
    var caption = $(".cmp-caption", tools);
    var seg = $(".seg", tools);
    var syncSeg;
    var ctl = bindCompare(stage, function (p) { if (syncSeg) syncSeg(p); });
    syncSeg = bindSeg(seg, ctl);
    syncSeg(ctl.get());
    bindExpand(wrap, $(".cmp-expand", tools));

    // Numérotation par projet : « Maroc 01 », « Maroc 02 », « Training 01 »…
    var counters = {};
    items.forEach(function (it) { counters[it.projet] = (counters[it.projet] || 0) + 1; it._n = counters[it.projet]; });
    var current = -1, token = 0;
    var thumbBtns = [];

    function projTitle(it) { var p = projectById(it.projet); return p ? L(p.titre) : (it.projet || ""); }
    function setCaption() {
      if (current < 0) return;
      var it = items[current];
      caption.innerHTML = "<b>" + esc(projTitle(it)) + "</b> — " + esc(t("cmpFrame")) + " " + pad2(it._n) + " / " + pad2(counters[it.projet]);
      imgG.alt = projTitle(it) + " — " + t("cmpFrame") + " " + it._n + " — GRADED";
      imgL.alt = projTitle(it) + " — " + t("cmpFrame") + " " + it._n + " — LOG";
    }
    function select(i) {
      if (i === current) return;
      var it = items[i];
      current = i;
      var my = ++token;
      thumbBtns.forEach(function (b, j) { b.setAttribute("aria-current", String(j === i)); });
      stage.style.setProperty("--ar", ratioCss(it.ratio));
      wrap.style.setProperty("--arn", String(ratioNum(it.ratio)));
      var err = $(".media-error", stage); if (err) err.remove();
      // Les deux images sont chargées et décodées AVANT d'être affichées ensemble :
      // jamais une version seule, jamais de décalage.
      var a = new Image(), b = new Image();
      a.decoding = "async"; b.decoding = "async";
      var pa = new Promise(function (res, rej) { a.onload = res; a.onerror = rej; });
      var pb = new Promise(function (res, rej) { b.onload = res; b.onerror = rej; });
      a.src = it.graded; b.src = it.log;
      stage.classList.remove("is-loaded");
      Promise.all([pa, pb]).then(function () {
        return Promise.all([a.decode ? a.decode().catch(function () {}) : 0, b.decode ? b.decode().catch(function () {}) : 0]);
      }).then(function () {
        if (my !== token) return;
        imgG.src = it.graded; imgL.src = it.log;
        stage.classList.add("is-loaded");
      }).catch(function () {
        if (my !== token) return;
        stage.classList.add("is-loaded");
        imgG.removeAttribute("src"); imgL.removeAttribute("src");
        stage.appendChild(el("div", { class: "media-error cmp__img", style: "opacity:1" }, esc(t("imageError"))));
      });
      setCaption();
    }

    // Vignettes groupées par projet
    var groups = {};
    var order = [];
    items.forEach(function (it, i) {
      if (!groups[it.projet]) { groups[it.projet] = el("div", { class: "thumbs__group" }); order.push(it.projet); }
      var b = el("button", { class: "thumb", type: "button", "aria-current": "false" });
      b.innerHTML = '<span class="thumb__img"><img src="' + esc(it.vignette || it.graded) + '" alt="" loading="lazy" decoding="async"></span><span class="thumb__label"></span>';
      var im = $("img", b);
      im.addEventListener("error", function () { im.remove(); });
      b.addEventListener("click", function () { select(i); });
      groups[it.projet].appendChild(b);
      thumbBtns.push(b);
    });
    order.forEach(function (k) { thumbs.appendChild(groups[k]); });
    if (items.length < 2) thumbs.hidden = true;

    onLang(function () {
      thumbs.setAttribute("aria-label", t("cmpChoose"));
      ctl.handle.setAttribute("aria-label", t("cmpSlider"));
      seg.setAttribute("aria-label", t("cmpSlider"));
      thumbBtns.forEach(function (b, i) {
        var it = items[i];
        $(".thumb__label", b).textContent = projTitle(it) + " " + pad2(it._n);
        b.setAttribute("aria-label", projTitle(it) + " — " + t("cmpFrame") + " " + it._n);
      });
      setCaption();
    });

    // Chargement seulement à l'approche de la section.
    lazyRun(host, function () { select(0); });
  }

  // Image chargée seulement à l'approche (300 px) : rien ne part au chargement de la page.
  var imgIO = null;
  function lazyImg(img, src) {
    if (!("IntersectionObserver" in window)) { img.src = src; return; }
    if (!imgIO) {
      imgIO = new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (!e.isIntersecting) return;
          imgIO.unobserve(e.target);
          e.target.src = e.target.getAttribute("data-src");
          e.target.removeAttribute("data-src");
        });
      }, { rootMargin: "300px 0px" });
    }
    img.setAttribute("data-src", src);
    imgIO.observe(img);
  }

  function lazyRun(node, fn) {
    if (!("IntersectionObserver" in window)) { fn(); return; }
    var io = new IntersectionObserver(function (es) {
      if (es.some(function (e) { return e.isIntersecting; })) { io.disconnect(); fn(); }
    }, { rootMargin: "600px 0px" });
    io.observe(node);
  }

  /* ------------------------------------------------------------------
     Comparateurs vidéo : un seul <video> empilé (LOG en haut, GRADED en
     bas), dessiné dans un <canvas>. Synchronisation parfaite par
     construction : c'est la même image vidéo.
     ------------------------------------------------------------------ */
  function initVideoCompare() {
    var host = $("#cmp-videos");
    var items = ((S.comparateurs || {}).videos || []).filter(function (x) { return x && x.src; });
    if (!items.length) { host.hidden = true; host.previousElementSibling.hidden = true; return; }

    var wrap = el("div", { class: "cmpw vcmp" });
    var tabs = null;
    if (items.length > 1) {
      tabs = el("div", { class: "vtabs", role: "tablist" });
      wrap.appendChild(tabs);
    }
    var stage = el("div", { class: "cmp" });
    stage.innerHTML = compareStageHTML(
      '<video class="cmp__video" playsinline muted loop preload="none" disablepictureinpicture tabindex="-1" aria-hidden="true"></video>' +
      '<canvas class="cmp__canvas" aria-hidden="true"></canvas>' +
      '<button class="vcmp__big" type="button">' + ICON.play + "<span></span></button>");
    var bar = el("div", { class: "pbar" });
    bar.innerHTML =
      '<button class="pbar__btn vc-play" type="button">' + ICON.play + "</button>" +
      '<span class="pbar__time" aria-hidden="true">0:00 / 0:00</span>' +
      '<div class="prog" role="slider" tabindex="0" aria-valuemin="0" aria-valuemax="0" aria-valuenow="0"><div class="prog__buf"></div><div class="prog__fill"></div></div>' +
      segHTML().replace('class="seg"', 'class="seg vcmp__cmp-seg"') +
      '<div class="seg vcmp__simple-seg" role="group"><button type="button" data-show="log">LOG</button><button type="button" data-show="graded">GRADED</button></div>' +
      '<button class="pbar__txt vc-mode" type="button"></button>' +
      '<button class="pbar__btn vc-fs" type="button"></button>';
    wrap.appendChild(stage); wrap.appendChild(bar);
    host.appendChild(wrap);

    var v = $("video", stage);
    var canvas = $("canvas", stage);
    var big = $(".vcmp__big", stage);
    var bPlay = $(".vc-play", bar), bMode = $(".vc-mode", bar), bFs = $(".vc-fs", bar);
    var time = $(".pbar__time", bar), prog = $(".prog", bar), fill = $(".prog__fill", bar), buf = $(".prog__buf", bar);
    var sseg = $(".vcmp__simple-seg", bar);
    var ctx = null;
    try { ctx = canvas.getContext("2d", { alpha: false }); } catch (e) { ctx = null; }
    var simple = lowEnd || !ctx;
    var showGraded = true;
    var current = -1, started = false, poster = null, posterOk = false;
    var hasRVFC = "requestVideoFrameCallback" in HTMLVideoElement.prototype;
    var frameReq = 0, animRaf = 0, uiRaf = 0;

    var syncSeg = null;
    var ctl = bindCompare(stage, function (p, animating) {
      if (syncSeg) syncSeg(p);
      if (animating) animateDraw(); else schedule();
    });
    var cseg = $(".vcmp__cmp-seg", bar);
    syncSeg = bindSeg(cseg, ctl);
    syncSeg(ctl.get());

    function band() { return (items[current] && items[current].bande) || 0; }
    function source() {
      if (started && v.readyState >= 2 && v.videoWidth) return { s: v, w: v.videoWidth, h: v.videoHeight };
      if (posterOk) return { s: poster, w: poster.naturalWidth, h: poster.naturalHeight };
      return null;
    }
    function draw() {
      if (simple || !ctx) return;
      var src = source();
      if (!src) return;
      var B = band();
      var half = (src.h - B) / 2;
      if (half <= 0) return;
      if (canvas.width !== src.w || canvas.height !== Math.round(half)) { canvas.width = src.w; canvas.height = Math.round(half); }
      var W = canvas.width, Hh = canvas.height;
      var p = ctl.shown() / 100;
      ctx.imageSmoothingEnabled = true;
      // GRADED (moitié basse) en entier, puis la partie LOG (moitié haute) à gauche de la barre.
      ctx.drawImage(src.s, 0, half + B, src.w, half, 0, 0, W, Hh);
      if (p > 0) ctx.drawImage(src.s, 0, 0, src.w * p, half, 0, 0, W * p, Hh);
    }
    var pending = false;
    function schedule() {
      if (pending) return;
      pending = true;
      requestAnimationFrame(function () { pending = false; draw(); });
    }
    function animateDraw() {
      cancelAnimationFrame(animRaf);
      var until = performance.now() + 850;
      (function step(now) {
        draw();
        if (now < until) animRaf = requestAnimationFrame(step);
      })(performance.now());
    }
    function frameLoop() {
      draw();
      if (v.paused || v.ended) return;
      frameReq = hasRVFC ? v.requestVideoFrameCallback(frameLoop) : requestAnimationFrame(frameLoop);
    }
    function ui() {
      var d = v.duration || 0, c = v.currentTime || 0;
      fill.style.width = d ? (c / d * 100) + "%" : "0";
      time.textContent = fmt(c) + " / " + fmt(d);
      prog.setAttribute("aria-valuemax", String(Math.floor(d)));
      prog.setAttribute("aria-valuenow", String(Math.floor(c)));
      prog.setAttribute("aria-valuetext", fmt(c) + " / " + fmt(d));
      try { if (d && v.buffered.length) buf.style.width = (v.buffered.end(v.buffered.length - 1) / d * 100) + "%"; } catch (e) {}
    }
    function uiLoop() { ui(); if (!v.paused) uiRaf = requestAnimationFrame(uiLoop); }

    function showError() {
      if ($(".media-error", stage)) return;
      stage.appendChild(el("div", { class: "media-error cmp__img", style: "opacity:1;z-index:3" }, esc(t("videoError"))));
      wrap.classList.add("has-started");
    }
    function select(i) {
      if (i === current) return;
      var it = items[i];
      current = i;
      v.pause();
      started = false;
      wrap.classList.remove("has-started");
      var err = $(".media-error", stage); if (err) err.remove();
      var ar = (it.largeur && it.hauteur) ? it.largeur + "/" + it.hauteur : "16/9";
      stage.style.setProperty("--ar", ratioCss(ar));
      wrap.style.setProperty("--arn", String(ratioNum(ar)));
      if (it.largeur && it.hauteur && ctx) { canvas.width = it.largeur; canvas.height = it.hauteur; ctx.fillStyle = "#000"; ctx.fillRect(0, 0, canvas.width, canvas.height); }
      v.removeAttribute("src");
      if (it.poster) v.poster = it.poster; else v.removeAttribute("poster");
      try { v.load(); } catch (e) {}
      fill.style.width = "0"; buf.style.width = "0"; time.textContent = "0:00 / 0:00";
      posterOk = false;
      if (it.poster) {
        poster = new Image();
        poster.decoding = "async";
        poster.onload = function () { if (items[current] === it) { posterOk = true; draw(); } };
        poster.src = it.poster;
      }
      if (tabs) $$("button", tabs).forEach(function (b, j) { b.setAttribute("aria-selected", String(j === i)); b.tabIndex = j === i ? 0 : -1; });
      labels();
    }
    function ensureSrc() {
      var it = items[current];
      if (!v.getAttribute("src")) { v.src = it.src; }
    }
    function play() {
      ensureSrc();
      wrap.classList.add("has-started");
      var p = v.play();
      if (p && p.catch) p.catch(function (e) { if (e && e.name === "NotAllowedError") wrap.classList.remove("has-started"); });
    }
    function toggle() { if (v.paused) play(); else v.pause(); }
    function seek(s) { if (v.duration) { v.currentTime = clamp(s, 0, v.duration); ui(); } }

    function setSimple(on) {
      simple = on || !ctx;
      wrap.classList.toggle("is-simple", simple);
      wrap.classList.toggle("show-graded", showGraded);
      if (!simple) draw();
      labels();
    }
    function labels() {
      $("span", big).textContent = t("play");
      bPlay.innerHTML = v.paused ? ICON.play : ICON.pause;
      bPlay.setAttribute("aria-label", v.paused ? t("play") : t("pause"));
      prog.setAttribute("aria-label", t("seek"));
      bMode.textContent = simple ? t("cmpFull") : t("cmpSimple");
      bMode.hidden = !ctx;
      bMode.setAttribute("aria-pressed", String(simple));
      ctl.handle.setAttribute("aria-label", t("cmpSlider"));
      sseg.setAttribute("aria-label", t("cmpSimpleHint"));
      cseg.setAttribute("aria-label", t("cmpSlider"));
      $$("button", sseg).forEach(function (b) {
        var g = b.getAttribute("data-show") === "graded";
        b.setAttribute("aria-pressed", String(g === showGraded));
      });
      if (tabs) {
        tabs.setAttribute("aria-label", t("cmpVideoTitle"));
        $$("button", tabs).forEach(function (b, j) { var p = projectById(items[j].projet); b.textContent = p ? L(p.titre) : items[j].projet; });
      }
      var e = $(".media-error", stage); if (e) e.textContent = t("videoError");
    }

    if (tabs) {
      items.forEach(function (it, i) {
        var b = el("button", { type: "button", role: "tab", "aria-selected": "false" });
        b.addEventListener("click", function () { select(i); });
        b.addEventListener("keydown", function (e) {
          var k = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
          if (!k) return;
          e.preventDefault();
          var j = (i + k + items.length) % items.length;
          select(j); tabs.children[j].focus();
        });
        tabs.appendChild(b);
      });
    }

    v.addEventListener("loadeddata", function () { draw(); });
    v.addEventListener("playing", function () { started = true; draw(); });
    v.addEventListener("play", function () {
      started = true;
      labels();
      cancelAnimationFrame(uiRaf); uiLoop();
      if (hasRVFC) { try { v.cancelVideoFrameCallback(frameReq); } catch (e) {} } else cancelAnimationFrame(frameReq);
      frameLoop();
    });
    v.addEventListener("pause", function () { labels(); ui(); draw(); });
    v.addEventListener("seeked", function () { draw(); ui(); });
    v.addEventListener("loadedmetadata", ui);
    v.addEventListener("progress", ui);
    v.addEventListener("error", function () { if (v.getAttribute("src")) showError(); });

    big.addEventListener("click", function (e) { e.stopPropagation(); play(); });
    bPlay.addEventListener("click", toggle);
    bMode.addEventListener("click", function () { setSimple(!simple); });
    $$("button", sseg).forEach(function (b) {
      b.addEventListener("click", function () {
        showGraded = b.getAttribute("data-show") === "graded";
        wrap.classList.toggle("show-graded", showGraded);
        labels();
      });
    });
    bindExpand(wrap, bFs, function () { setTimeout(draw, 60); }, true);

    function seekFromEvent(e) { var r = prog.getBoundingClientRect(); seek((e.clientX - r.left) / r.width * (v.duration || 0)); }
    var pd = false;
    prog.addEventListener("pointerdown", function (e) {
      if (!v.duration) return;
      pd = true; prog.classList.add("is-drag");
      try { prog.setPointerCapture(e.pointerId); } catch (x) {}
      seekFromEvent(e);
    });
    prog.addEventListener("pointermove", function (e) { if (pd) seekFromEvent(e); });
    ["pointerup", "pointercancel"].forEach(function (n) { prog.addEventListener(n, function () { pd = false; prog.classList.remove("is-drag"); }); });
    prog.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { e.preventDefault(); seek(v.currentTime - 2); }
      else if (e.key === "ArrowRight") { e.preventDefault(); seek(v.currentTime + 2); }
      else if (e.key === "Home") { e.preventDefault(); seek(0); }
      else if (e.key === "End") { e.preventDefault(); seek(v.duration); }
    });
    wrap.addEventListener("keydown", function (e) {
      if ((e.key === " " || e.key === "k" || e.key === "K") && e.target.tagName !== "BUTTON") {
        if (e.target.classList.contains("cmp__handle") || e.target === prog || e.target === wrap) { e.preventDefault(); toggle(); }
      }
    });
    window.addEventListener("resize", schedule);

    // Pause automatique quand le comparateur sort de l'écran.
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (!e.isIntersecting && !v.paused) v.pause(); });
      }, { threshold: 0 }).observe(wrap);
    }

    setSimple(simple);
    onLang(labels);
    lazyRun(host, function () { select(0); });
    initVideoCompare.api = { select: select, isSimple: function () { return simple; } };
  }

  /* ------------------------------------------------------------------
     Galerie d'étalonnage + visionneuse
     ------------------------------------------------------------------ */
  function galleryRows(n) {
    var spans = [], left = n, type = 2, twoFlip = false;
    if (n === 1) return [8];
    while (left > 0) {
      var take = type;
      if (left < take) take = left;
      if (left - take === 1) take = take === 2 ? 3 : 2;
      if (take > left) take = left;
      if (take === 2) { spans.push(twoFlip ? 5 : 7, twoFlip ? 7 : 5); twoFlip = !twoFlip; }
      else if (take === 3) spans.push(4, 4, 4);
      else spans.push(8);
      left -= take;
      type = type === 2 ? 3 : 2;
    }
    return spans;
  }

  var lb = { open: false, i: 0, items: [], last: null };
  function initGallery() {
    var ul = $("#gallery");
    var items = (S.galerie || []).filter(function (g) { return g && g.image; });
    if (!items.length) { ul.hidden = true; $(".sub--gallery").hidden = true; return; }
    lb.items = items;
    var spans = galleryRows(items.length);
    var btns = [];
    items.forEach(function (g, i) {
      var li = el("li", { class: "gallery__item reveal gallery__item--" + spans[i] });
      var b = el("button", { class: "gallery__btn", type: "button" });
      b.innerHTML = '<span class="gallery__img" style="--ar:' + esc(ratioCss(g.ratio)) + '"><img alt="" loading="lazy" decoding="async"></span><span class="gallery__cap"><b></b><span>' + pad2(i + 1) + "</span></span>";
      var img = $("img", b);
      img.addEventListener("load", function () { img.classList.add("is-loaded"); });
      img.addEventListener("error", function () {
        var box = img.parentNode; img.remove();
        box.appendChild(el("span", { class: "media-error", style: "position:absolute;inset:0" }, esc(t("imageError"))));
      });
      img.src = g.image;
      b.addEventListener("click", function () { openLightbox(i, b); });
      li.appendChild(b); ul.appendChild(li);
      btns.push(b);
    });
    onLang(function () {
      btns.forEach(function (b, i) {
        var g = items[i], p = projectById(g.projet), title = p ? L(p.titre) : "";
        $(".gallery__cap b", b).textContent = title;
        $("img", b) && ($("img", b).alt = title ? title + " — GRADED" : "GRADED");
        b.setAttribute("aria-label", t("galleryOpen") + (title ? " — " + title + " " + pad2(i + 1) : ""));
      });
      if (lb.open) renderLightbox();
    });

    $("#lb-prev").innerHTML = ICON.arrL;
    $("#lb-next").innerHTML = ICON.arrR;
    $("#lb-close").addEventListener("click", closeLightbox);
    $("#lb-prev").addEventListener("click", function () { stepLightbox(-1); });
    $("#lb-next").addEventListener("click", function () { stepLightbox(1); });
    var box = $("#lightbox");
    box.addEventListener("click", function (e) { if (e.target === box) closeLightbox(); });
    var sx = null;
    box.addEventListener("touchstart", function (e) { sx = e.touches[0].clientX; }, { passive: true });
    box.addEventListener("touchend", function (e) {
      if (sx === null) return;
      var dx = e.changedTouches[0].clientX - sx; sx = null;
      if (Math.abs(dx) > 50) stepLightbox(dx < 0 ? 1 : -1);
    });
    $("#lb-img").addEventListener("error", function () { $("#lb-img").alt = t("imageError"); });
  }
  function renderLightbox() {
    var g = lb.items[lb.i];
    var p = projectById(g.projet);
    var title = p ? L(p.titre) : "";
    var img = $("#lb-img");
    img.src = g.image;
    img.alt = title ? title + " — GRADED" : "GRADED";
    var parts = [];
    if (title) parts.push("<b>" + esc(title) + "</b>");
    [["lbCamera", g.camera], ["lbLog", g.profilLog], ["lbDirection", g.direction], ["lbSoftware", g.logiciel]].forEach(function (x) {
      if (filled(x[1])) parts.push("<span><em>" + esc(t(x[0])) + "</em>" + esc(L(x[1])) + "</span>");
    });
    parts.push("<span>" + pad2(lb.i + 1) + " / " + pad2(lb.items.length) + "</span>");
    $("#lb-caption").innerHTML = parts.join("");
    var many = lb.items.length > 1;
    $("#lb-prev").hidden = !many; $("#lb-next").hidden = !many;
  }
  function openLightbox(i, opener) {
    var box = $("#lightbox");
    lb.i = i; lb.last = opener; lb.open = true;
    renderLightbox();
    box.hidden = false;
    lockScroll(true);
    setBackgroundInert(true);
    requestAnimationFrame(function () { box.classList.add("is-open"); });
    $("#lb-close").focus({ preventScroll: true });
  }
  function stepLightbox(d) {
    if (!lb.open || lb.items.length < 2) return;
    lb.i = (lb.i + d + lb.items.length) % lb.items.length;
    renderLightbox();
  }
  function closeLightbox() {
    if (!lb.open) return;
    var box = $("#lightbox");
    lb.open = false;
    box.classList.remove("is-open");
    setTimeout(function () { if (!lb.open) box.hidden = true; }, reduce() ? 0 : 350);
    lockScroll(false);
    setBackgroundInert(false);
    if (lb.last) lb.last.focus({ preventScroll: true });
  }

  /* ------------------------------------------------------------------
     À propos
     ------------------------------------------------------------------ */
  function initAbout() {
    var body = $("#about-body");
    var ap = S.apropos || {};
    onLang(function () {
      var paras = (ap.texte && (ap.texte[lang] || ap.texte.fr)) || [];
      if (paras.length) body.innerHTML = paras.map(function (p) { return "<p>" + esc(p) + "</p>"; }).join("");
    });
    var sw = $("#about-software");
    if (S.logiciel) sw.textContent = S.logiciel; else sw.parentNode.hidden = true;

    var col = $("#about-collage");
    var imgs = (ap.images || []).filter(function (x) { return x && x.src; }).slice(0, 2);
    if (!imgs.length) { col.hidden = true; return; }
    var prints = imgs.map(function (im, i) {
      var f = el("figure", { class: "print print--" + (i + 1) });
      f.innerHTML = '<img alt="" loading="lazy" decoding="async">' + (filled(im.legende) ? "<figcaption>" + esc(L(im.legende)) + "</figcaption>" : "");
      var img = $("img", f);
      img.addEventListener("error", function () { f.remove(); });
      img.src = im.src;
      col.appendChild(f);
      return f;
    });
    // Parallaxe subtile du collage.
    var factors = [0.07, -0.05];
    var tick = false;
    function update() {
      tick = false;
      if (reduce()) { prints.forEach(function (f) { f.style.transform = ""; }); return; }
      var r = col.getBoundingClientRect();
      if (r.bottom < -200 || r.top > window.innerHeight + 200) return;
      var d = (r.top + r.height / 2) - window.innerHeight / 2;
      prints.forEach(function (f, i) {
        f.style.transform = "translate3d(0," + (d * factors[i]).toFixed(1) + "px,0) rotate(var(--r))";
      });
    }
    window.addEventListener("scroll", function () { if (!tick) { tick = true; requestAnimationFrame(update); } }, { passive: true });
    update();
  }

  /* ------------------------------------------------------------------
     Contact
     ------------------------------------------------------------------ */
  // Réseaux : chaque champ accepte une adresse ou une liste d'adresses.
  // Instagram affiche le @compte (utile quand il y en a plusieurs).
  function socialLinks(c) {
    var out = [];
    [["Instagram", c.instagram], ["Vimeo", c.vimeo], ["YouTube", c.youtube]].forEach(function (x) {
      var urls = Array.isArray(x[1]) ? x[1] : [x[1]];
      urls.forEach(function (u) {
        u = (u || "").trim();
        if (!/^https?:\/\//i.test(u)) return;
        var m = x[0] === "Instagram" && u.match(/instagram\.com\/([^\/?#]+)/i);
        out.push({ url: u, name: x[0], handle: m ? "@" + m[1] : "" });
      });
    });
    return out;
  }

  function initContact() {
    var c = S.contact || {};
    var email = c.email || "";
    var mail = $("#contact-email"), btn = $("#contact-button");
    function mailto(subject, body) {
      return "mailto:" + email + "?subject=" + encodeURIComponent(subject) + (body ? "&body=" + encodeURIComponent(body) : "");
    }
    if (email) {
      mail.textContent = email;
      mail.href = "mailto:" + email;
    } else {
      mail.hidden = true; mail.previousElementSibling.hidden = true; btn.hidden = true;
    }

    var social = $("#contact-social");
    var list = $("ul", social);
    var nets = socialLinks(c);
    if (nets.length) {
      var html = nets.map(function (x) {
        return '<li><a href="' + esc(x.url) + '" target="_blank" rel="noopener me">' + esc(x.name) +
          (x.handle ? ' <span class="handle">' + esc(x.handle) + "</span>" : "") + "</a></li>";
      }).join("");
      list.innerHTML = html;
      social.hidden = false;
      var foot = $("#foot-social");
      if (foot) { $("ul", foot).innerHTML = html; foot.hidden = false; }
    }

    var form = $("#contact-form");
    var status = $("#form-status");
    var submitLabel = $("#form-submit-label");
    var note = $("#form-note");
    var endpoint = (c.formEndpoint || "").trim();
    onLang(function () {
      if (email) btn.href = mailto(t("mailSubject"));
      submitLabel.textContent = endpoint ? t("formSend") : t("formSendMail");
      note.textContent = endpoint ? "" : t("formNoteMail");
      note.hidden = !!endpoint;
    });
    if (!email && !endpoint) { form.hidden = true; return; }

    function say(text, isError, withMail) {
      status.classList.toggle("is-error", !!isError);
      status.innerHTML = esc(text) + (withMail && email ? ' <a href="mailto:' + esc(email) + '">' + esc(email) + "</a>." : "");
    }
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var fName = form.elements.name, fMail = form.elements.email, fMsg = form.elements.message;
      var bad = [];
      [fName, fMsg].forEach(function (f) { if (!f.value.trim()) bad.push(f); });
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(fMail.value.trim())) bad.splice(1, 0, fMail);
      $$(".field", form).forEach(function (f) { f.classList.remove("is-invalid"); });
      [fName, fMail, fMsg].forEach(function (f) { f.removeAttribute("aria-invalid"); });
      if (bad.length) {
        bad.forEach(function (f) { f.parentNode.classList.add("is-invalid"); f.setAttribute("aria-invalid", "true"); });
        say(t("formRequired"), true);
        bad[0].focus();
        return;
      }
      var name = fName.value.trim(), from = fMail.value.trim(), msg = fMsg.value.trim();
      if (endpoint) {
        var sb = $('button[type="submit"]', form);
        sb.disabled = true;
        say(t("formSending"));
        var fd = new FormData(form);
        fd.append("_subject", t("mailSubject") + " — " + name);
        fetch(endpoint, { method: "POST", body: fd, headers: { Accept: "application/json" } })
          .then(function (r) {
            if (!r.ok) throw new Error("HTTP " + r.status);
            say(t("formOk"));
            form.reset();
          })
          .catch(function () { say(t("formError"), true, true); })
          .then(function () { sb.disabled = false; });
        return;
      }
      // Aucun service d'envoi configuré : on ouvre la messagerie du visiteur,
      // on le dit honnêtement, sans fausse confirmation d'envoi.
      var body = msg + "\n\n— " + name + "\n" + from;
      say(t("formOpening"), false, true);
      window.location.href = mailto(t("mailSubject") + " — " + name, body);
    });
  }

  /* ------------------------------------------------------------------
     Apparitions progressives
     ------------------------------------------------------------------ */
  function initReveal() {
    var nodes = $$(".reveal");
    if (!("IntersectionObserver" in window)) { nodes.forEach(function (n) { n.classList.add("is-in"); }); return; }
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    nodes.forEach(function (n) { io.observe(n); });
  }

  /* ------------------------------------------------------------------
     Clavier global : Échap ferme le calque du dessus
     ------------------------------------------------------------------ */
  function initKeys() {
    D.addEventListener("keydown", function (e) {
      if (e.key === "Escape" || e.key === "Esc") {
        if (fsElement()) return; // le navigateur quitte lui-même le plein écran
        if (pseudoStack.length) { pseudoStack[pseudoStack.length - 1].collapse(); e.preventDefault(); return; }
        if (lb.open) { closeLightbox(); e.preventDefault(); return; }
        var menu = $("#menu-mobile");
        if (menu && !menu.hidden && initNav.closeMenu) { initNav.closeMenu(true); e.preventDefault(); return; }
        if (project.open) { requestCloseProject(); e.preventDefault(); return; }
      }
      if (lb.open) {
        if (e.key === "ArrowLeft") { stepLightbox(-1); e.preventDefault(); }
        else if (e.key === "ArrowRight") { stepLightbox(1); e.preventDefault(); }
      }
    });
  }

  /* ------------------------------------------------------------------
     Démarrage
     ------------------------------------------------------------------ */
  function init() {
    H.lang = lang;
    var y = $("#year"); if (y) y.textContent = String(new Date().getFullYear());
    safe("smooth-scroll", initSmoothScroll);
    safe("nav", initNav);
    safe("hero", initHero);
    safe("showreel", initShowreel);
    safe("work", initWork);
    safe("compare-images", initImageCompare);
    safe("compare-videos", initVideoCompare);
    safe("gallery", initGallery);
    safe("about", initAbout);
    safe("contact", initContact);
    safe("keys", initKeys);
    safe("i18n", applyStatic);
    safe("project", initProject);
    safe("reveal", initReveal);
    // Filet de sécurité : le menu et l'accueil s'affichent quoi qu'il arrive.
    setTimeout(function () {
      H.classList.add("is-in-nav");
      var h = $(".hero"); if (h) h.classList.add("is-in");
      var n = $("#hero-name"); if (n) n.classList.add("is-ready");
    }, 2500);
  }

  if (D.readyState === "loading") D.addEventListener("DOMContentLoaded", init);
  else init();
})();
