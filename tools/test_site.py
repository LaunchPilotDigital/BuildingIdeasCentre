"""Serve site/ locally and check it in Chrome against the error report."""
import http.server
import json
import re
import socketserver
import sys
import threading
from functools import partial
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SHOTS = Path(sys.argv[1])
SHOTS.mkdir(exist_ok=True)


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = socketserver.ThreadingTCPServer(("127.0.0.1", 8123), partial(Q, directory=str(SITE)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
B = "http://127.0.0.1:8123/"
paths = sorted(str(p.parent.relative_to(SITE)).replace("\\", "/") for p in SITE.rglob("index.html"))
paths = [("" if p == "." else p + "/") for p in paths]

fails = []
def bad(*a):
    fails.append(" ".join(map(str, a)))

TYPOS = r"Bathoom|Rennovation|Ideas Center\b|© 2025|enquires|your are|siter|&outdated|south Australia|are specialist in|products form|thats greener|homes and business\b|polishing, The|……|grace-Mehak|years experience|was Now|was now|was:|prioritize|specializ|customiz|personaliz|Philips"
weights = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome")
    for vp, opts in {"desktop": dict(viewport={"width": 1440, "height": 900}), "mobile": dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)}.items():
        ctx = b.new_context(**opts)
        p = ctx.new_page()
        errs, missing = [], []
        p.on("pageerror", lambda e: errs.append(str(e)))
        p.on("console", lambda m: errs.append(m.text) if m.type == "error" and "ERR_" not in m.text else None)
        p.on("response", lambda r: missing.append(r.url) if r.status >= 400 and "127.0.0.1" in r.url else None)
        seen = set()
        for path in paths:
            r = p.goto(B + path, wait_until="load")
            if r.status != 200:
                bad(vp, path, "status", r.status)
            info = p.evaluate("""() => ({h1: document.querySelectorAll('h1').length, desc: (document.querySelector('meta[name=description]')||{}).content||'',
              title: document.title, sw: document.documentElement.scrollWidth, iw: innerWidth, noalt: [...document.images].filter(i=>i.getAttribute('alt')===null).map(i=>i.src),
              text: document.body.innerText, links: [...document.querySelectorAll('a[href]')].map(a=>a.href), dead: [...document.querySelectorAll('a[href="#"]')].filter(a=>a.id!=='lb-name').length, tel: document.querySelectorAll('a[href^="tel:"]').length})""")
            if info["h1"] != 1: bad(vp, path, "h1 count", info["h1"])
            if not info["desc"]: bad(vp, path, "no description")
            if info["sw"] > info["iw"]: bad(vp, path, "overflow", info["sw"], info["iw"])
            if info["noalt"]: bad(vp, path, "no alt", info["noalt"][:2])
            if info["dead"]: bad(vp, path, "dead links", info["dead"])
            if info["tel"] < 2: bad(vp, path, "tel links", info["tel"])
            m = re.findall(TYPOS, info["text"])
            if m: bad(vp, path, "typo", set(m))
            if vp == "desktop":
                for l in info["links"]:
                    if l.startswith(B): seen.add(l.split("#")[0].split("?")[0])
        print(vp, "errors:", sorted(set(errs))[:5], "missing:", sorted(set(missing))[:8])
        if errs or missing: bad(vp, "console/missing", len(errs), len(missing))
        if vp == "desktop":
            for l in sorted(seen):
                rr = ctx.request.get(l)
                if rr.status != 200: bad("broken link", l, rr.status)
            print("internal links checked", len(seen))
        ctx.close()

    # page weight after scrolling, fresh cache
    for path in ["", "ideas/", "displays/", "displays/robam/", "displays/the-pool-tile-company/", "events/building-ideas-expo-2026/"]:
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, device_scale_factor=2)
        p = ctx.new_page()
        tot = [0]
        p.on("response", lambda r: tot.__setitem__(0, tot[0] + int(r.headers.get("content-length", 0))) if "127.0.0.1" in r.url else None)
        p.goto(B + path, wait_until="load")
        h = p.evaluate("document.documentElement.scrollHeight")
        if path != "ideas/":
            for y in range(0, h, 500):
                p.evaluate(f"window.scrollTo(0,{y})")
                p.wait_for_timeout(40)
            p.wait_for_timeout(300)
        weights[path or "home"] = round(tot[0] / 1e6, 2)
        ctx.close()
    print("MB (phone, scrolled):", weights)

    # customer journey
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    p = ctx.new_page()
    p.goto(B, wait_until="load")
    p.get_by_role("link", name="Renovating a kitchen").click()
    p.wait_for_load_state("load")
    vis = p.evaluate("[...document.querySelectorAll('.idea')].filter(e=>!e.hidden).length")
    allc = p.evaluate("document.querySelectorAll('.idea').length")
    print("planner -> ideas:", p.url, vis, "of", allc)
    if not 0 < vis < allc: bad("planner filter")
    btns = p.locator(".idea:not([hidden]) .save")
    for i in (0, 1, 5):
        btns.nth(i).click()
    print("count after 3 saves:", p.locator(".board-link [data-count]").inner_text())
    if p.locator(".board-link [data-count]").inner_text() != "3": bad("save count")
    p.locator(".idea:not([hidden]) .open").first.click()
    p.wait_for_timeout(400)
    print("lightbox open:", p.evaluate("document.querySelector('#lb').open"), p.locator("#lb-name").inner_text())
    p.keyboard.press("ArrowRight"); p.wait_for_timeout(200)
    p.screenshot(path=SHOTS / "lightbox.png")
    p.locator("#lb-close").click()
    p.goto(B + "my-ideas/", wait_until="load")
    p.wait_for_timeout(500)
    print("board:", p.locator("#board-sum").inner_text(), "| groups", p.locator(".board-group").count())
    if p.locator(".board-group").count() < 1: bad("board empty")
    p.screenshot(path=SHOTS / "board.png", full_page=True)
    p.goto(B + "displays/?c=roofing", wait_until="load")
    names = p.evaluate("[...document.querySelectorAll('.card')].filter(c=>!c.hidden).map(c=>c.querySelector('h3').innerText)")
    print("roofing:", names)
    if "AG Roofing" not in names: bad("AG Roofing filter")
    p.fill("#search", "51")
    print("search 51:", p.evaluate("[...document.querySelectorAll('.card')].filter(c=>!c.hidden).map(c=>c.querySelector('h3').innerText)"))
    p.goto(B + "contact/", wait_until="load")
    p.fill("#gen-name", "Test"); p.fill("#gen-email", "not-an-email"); p.fill("#gen-msg", "Hi")
    p.locator("form button[type=submit]").click()
    if p.locator(".done").is_visible(): bad("email validation did not stop submit")
    p.fill("#gen-email", "test@example.com")
    p.locator("form button[type=submit]").click()
    print("form:", p.locator(".done").inner_text())
    # expo should vanish after the event
    ctx.add_init_script("const _n=Date.now;Date.now=()=>new Date('2026-12-01').getTime();")
    q = ctx.new_page()
    q.goto(B, wait_until="load")
    q.wait_for_timeout(300)
    print("expo visible after event:", q.locator(".expo").is_visible(), q.locator(".expo-bar").is_visible())
    if q.locator(".expo").is_visible(): bad("expo did not hide")
    ctx.close()

    # screenshots
    for vp, opts in {"d": dict(viewport={"width": 1440, "height": 900}), "m": dict(viewport={"width": 390, "height": 844}, device_scale_factor=1, is_mobile=True, has_touch=True)}.items():
        ctx = b.new_context(**opts)
        p = ctx.new_page()
        for name, path in {"home": "", "ideas": "ideas/", "displays": "displays/", "ex": "displays/kitchen-scene/", "ex2": "displays/irelax-adelaide/", "contact": "contact/", "expo": "events/building-ideas-expo-2026/", "exhibit": "exhibit-with-us/", "about": "about/", "events": "events/"}.items():
            p.goto(B + path, wait_until="load")
            if name != "ideas":
                h = p.evaluate("document.documentElement.scrollHeight")
                for y in range(0, h, 500):
                    p.evaluate(f"window.scrollTo(0,{y})")
                    p.wait_for_timeout(50)
                p.evaluate("window.scrollTo(0,0)")
            p.wait_for_timeout(500)
            p.screenshot(path=SHOTS / f"{vp}_{name}.png", full_page=name != "ideas")
        ctx.close()
    b.close()
srv.shutdown()
print("FAILS", len(fails))
for f in fails[:50]:
    print(" -", f[:220])
