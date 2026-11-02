(function () {
  "use strict";
  var KEY = "bic-my-ideas";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { return []; }
  }
  function store(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list)); } catch (e) { /* private browsing: list lasts for this page only */ }
  }
  var saved = load();

  function refresh() {
    $$("[data-count]").forEach(function (el) { el.textContent = saved.length; });
    $$(".save[data-id]").forEach(function (b) {
      var on = saved.indexOf(b.dataset.id) > -1;
      b.setAttribute("aria-pressed", on);
      b.innerHTML = on ? "&#10003; Saved" : "+ Save idea";
    });
  }
  function toggle(id) {
    var i = saved.indexOf(id);
    if (i > -1) saved.splice(i, 1); else saved.push(id);
    store(saved);
    refresh();
    if ($("#board")) renderBoard();
  }

  /* Menu */
  var mb = $(".menu-btn"), nav = $(".nav");
  if (mb) mb.addEventListener("click", function () {
    var open = nav.classList.toggle("open");
    mb.setAttribute("aria-expanded", open);
    mb.textContent = open ? "Close" : "Menu";
  });

  /* Anything about the expo disappears by itself once it has finished */
  var now = Date.now();
  $$("[data-until]").forEach(function (el) {
    if (now > new Date(el.dataset.until).getTime()) el.hidden = true;
  });
  $$("[data-days-to]").forEach(function (el) {
    var d = Math.ceil((new Date(el.dataset.daysTo).getTime() - now) / 864e5);
    if (d > 1) el.textContent = d + " days to go";
    else if (d === 1) el.textContent = "Tomorrow";
    else if (d === 0) el.textContent = "Today";
    else el.hidden = true;
  });
  $$("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });

  document.addEventListener("click", function (e) {
    var s = e.target.closest(".save[data-id]");
    if (s) { e.preventDefault(); toggle(s.dataset.id); return; }
    var o = e.target.closest(".open[data-full]");
    if (o) { openLb(o); }
  });

  /* Lightbox */
  var lb = $("#lb"), lbList = [], lbAt = 0;
  function showLb() {
    var o = lbList[lbAt], d = o.dataset;
    $("#lb-img").src = d.full;
    $("#lb-img").alt = $("img", o).alt;
    $("#lb-name").textContent = d.name;
    $("#lb-name").href = d.href;
    $("#lb-num").textContent = "Display " + d.num;
    $("#lb-save").dataset.id = d.id;
    refresh();
  }
  function openLb(o) {
    if (!lb || !lb.showModal) { window.location = o.dataset.full; return; }
    var scope = o.closest("[data-lb-scope]") || document;
    lbList = $$(".open[data-full]", scope).filter(function (x) { return !x.closest("[hidden]"); });
    lbAt = lbList.indexOf(o);
    showLb();
    lb.showModal();
  }
  function step(n) { lbAt = (lbAt + n + lbList.length) % lbList.length; showLb(); }
  if (lb) {
    $("#lb-prev").addEventListener("click", function () { step(-1); });
    $("#lb-next").addEventListener("click", function () { step(1); });
    $("#lb-close").addEventListener("click", function () { lb.close(); });
    lb.addEventListener("click", function (e) { if (e.target === lb) lb.close(); });
    lb.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") step(-1);
      if (e.key === "ArrowRight") step(1);
    });
  }

  /* Category filters and search, shared by Ideas and Displays */
  var filterRoot = $("[data-filter-root]");
  if (filterRoot) {
    var chips = $$(".chip[data-c]", filterRoot);
    var items = $$("[data-cats]");
    var search = $("#search");
    var out = $("#result");
    var noun = filterRoot.dataset.noun;
    var nouns = filterRoot.dataset.nouns;
    var cur = new URLSearchParams(location.search).get("c") || "all";
    if (!chips.some(function (c) { return c.dataset.c === cur; })) cur = "all";

    var apply = function (push) {
      var q = search ? search.value.trim().toLowerCase() : "";
      var n = 0;
      items.forEach(function (it) {
        var hit = (cur === "all" || it.dataset.cats.split(" ").indexOf(cur) > -1) &&
          (!q || it.dataset.q.indexOf(q) > -1);
        it.hidden = !hit;
        if (hit) n++;
      });
      chips.forEach(function (c) { c.setAttribute("aria-pressed", c.dataset.c === cur); });
      if (out) out.textContent = n + " " + (n === 1 ? noun : nouns);
      if (push && history.replaceState) {
        history.replaceState(null, "", cur === "all" ? location.pathname : location.pathname + "?c=" + cur);
      }
    };
    chips.forEach(function (c) {
      c.addEventListener("click", function () { cur = c.dataset.c; apply(true); });
    });
    if (search) search.addEventListener("input", function () {
      if (search.value.trim()) cur = "all";
      apply(true);
    });
    apply(false);
  }

  /* My Ideas */
  function renderBoard() {
    var box = $("#board"), data = window.BIC_IDEAS || {};
    var known = saved.filter(function (id) { return data.ideas[id]; });
    $("#board-empty").hidden = known.length > 0;
    $("#board-tools").hidden = known.length === 0;
    var groups = {};
    known.forEach(function (id) {
      var s = data.ideas[id].s;
      (groups[s] = groups[s] || []).push(id);
    });
    var slugs = Object.keys(groups).sort(function (a, b) {
      return data.ex[a].n.localeCompare(data.ex[b].n);
    });
    box.innerHTML = "";
    slugs.forEach(function (s) {
      var ex = data.ex[s], g = document.createElement("section");
      g.className = "board-group";
      var head = document.createElement("div");
      head.className = "board-head";
      var h = document.createElement("h2");
      var tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = "Display " + ex.d;
      var a = document.createElement("a");
      a.href = data.root + "displays/" + s + "/";
      a.textContent = ex.n;
      a.style.textDecoration = "none";
      h.appendChild(tag); h.appendChild(a);
      head.appendChild(h);
      if (ex.p) {
        var t = document.createElement("a");
        t.className = "link tel";
        t.href = "tel:" + ex.t;
        t.textContent = "Call " + ex.p;
        head.appendChild(t);
      }
      g.appendChild(head);
      var grid = document.createElement("div");
      grid.className = "board-grid";
      groups[s].forEach(function (id) {
        var item = document.createElement("div");
        item.className = "item";
        var img = document.createElement("img");
        img.src = data.root + data.ideas[id].t;
        img.alt = "Saved idea from " + ex.n;
        img.loading = "lazy";
        var b = document.createElement("button");
        b.className = "remove";
        b.type = "button";
        b.innerHTML = "&times;";
        b.setAttribute("aria-label", "Remove this idea");
        b.addEventListener("click", function () { toggle(id); });
        item.appendChild(img); item.appendChild(b);
        grid.appendChild(item);
      });
      g.appendChild(grid);
      box.appendChild(g);
    });
    var sum = $("#board-sum");
    if (sum) sum.textContent = known.length + (known.length === 1 ? " idea" : " ideas") + " from " + slugs.length + (slugs.length === 1 ? " display" : " displays");
  }
  if ($("#board")) {
    var share = location.hash.match(/^#share=(.+)$/);
    if (share) {
      share[1].split(",").forEach(function (id) { if (saved.indexOf(id) < 0) saved.push(id); });
      store(saved);
      history.replaceState(null, "", location.pathname);
    }
    renderBoard();
    $("#print").addEventListener("click", function () { window.print(); });
    $("#copy").addEventListener("click", function () {
      var url = location.origin + location.pathname + "#share=" + saved.join(",");
      var msg = $("#copied");
      var ok = function () { msg.textContent = "Link copied. Send it to anyone on your project."; };
      var no = function () { msg.textContent = url; };
      if (navigator.clipboard) navigator.clipboard.writeText(url).then(ok, no); else no();
    });
    $("#clear").addEventListener("click", function () {
      saved = []; store(saved); refresh(); renderBoard();
    });
  }

  /* Preview forms: validate properly, send nothing */
  $$("form[data-preview]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var d = $(".done", f);
      d.hidden = false;
      d.textContent = "This is a design preview, so your message was not sent. On the live site it would go straight to " + f.dataset.preview + ".";
      d.setAttribute("tabindex", "-1");
      d.focus();
    });
  });

  refresh();
})();
