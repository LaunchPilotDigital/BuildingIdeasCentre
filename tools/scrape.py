"""Capture content from the live Building Ideas Centre site into scraped/."""
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, unquote

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "scraped"
RAW = OUT / "raw_images"
RAW.mkdir(parents=True, exist_ok=True)
H = "https://buildingideascentre.com.au/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

CARDS = """() => [...document.querySelectorAll('.e-loop-item')].filter(e => e.getBoundingClientRect().height > 0).map(e => {
  const a = e.querySelector('a[href*="/display/"]');
  const t = e.innerText.split('\\n').map(s => s.trim()).filter(Boolean);
  const img = e.querySelector('img');
  return {url: a ? a.href : null, number: (t[0]||'').replace('Display ',''), name: t[1]||'', tagline: t.slice(2).join(' '), card_img: img ? (img.currentSrc||img.src) : null};
})"""

DETAIL = """() => {
  const clean = s => s.replace(/\\s+/g,' ').trim();
  const loopEls = new Set([...document.querySelectorAll('.e-loop-item, .e-loop-item *')]);
  const inLoop = e => loopEls.has(e);
  const popups = e => e.closest('.elementor-location-popup,.elementor-popup-modal');
  const header = e => e.closest('header,.elementor-location-header,footer,.elementor-location-footer');
  const sim = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].find(h => /similar displays/i.test(h.innerText));
  const stopY = sim ? sim.getBoundingClientRect().top + scrollY : 1e9;
  const before = e => (e.getBoundingClientRect().top + scrollY) < stopY;
  const imgs = [...document.images].filter(i => !inLoop(i) && !header(i) && !popups(i) && before(i))
     .map(i => ({src: i.currentSrc||i.src, full: (i.closest('a')&&/\\.(jpe?g|png|webp)/i.test(i.closest('a').href)) ? i.closest('a').href : null,
                 alt: i.alt, w: i.naturalWidth, h: i.naturalHeight, y: Math.round(i.getBoundingClientRect().top+scrollY), x: Math.round(i.getBoundingClientRect().left), sw: Math.round(i.getBoundingClientRect().width)}));
  const bg = [...document.querySelectorAll('.swiper-slide [style*="background-image"], [data-background]')].filter(e=>!inLoop(e)&&before(e))
     .map(e => (e.getAttribute('data-background') || (e.style.backgroundImage.match(/url\\(["']?(.*?)["']?\\)/)||[])[1])).filter(Boolean);
  const paras = [...document.querySelectorAll('p,li,h2,h3,h4,h5,.elementor-widget-text-editor div')]
     .filter(e => !inLoop(e) && !header(e) && !popups(e) && before(e) && e.getBoundingClientRect().height>0 && clean(e.innerText))
     .map(e => [e.tagName, clean(e.innerText)]);
  const links = [...document.querySelectorAll('a[href]')].filter(a=>!inLoop(a)&&!header(a)&&!popups(a)&&before(a));
  const by = re => { const a = links.find(l => re.test(l.innerText)); return a ? a.href : null; };
  return {imgs, bg, paras, website: by(/visit website/i), brochure: by(/brochure/i),
          extra: links.filter(l=>l.innerText.trim()&&!/call now|^message|visit website|brochure/i.test(l.innerText)).map(l=>[clean(l.innerText).slice(0,120), l.href]),
          fullText: document.body.innerText};
}"""


def goto(p, url, tries=4):
    for t in range(tries):
        try:
            return p.goto(url, wait_until="load", timeout=60000)
        except Exception as e:
            print("  retry", url, str(e)[:70], flush=True)
            time.sleep(20 * (t + 1))
    raise RuntimeError("could not load " + url)


def walk(p):
    h = p.evaluate("document.documentElement.scrollHeight")
    for y in range(0, h + 500, 500):
        p.evaluate(f"window.scrollTo(0,{y})")
        p.wait_for_timeout(180)
    p.wait_for_timeout(1000)
    p.evaluate("window.scrollTo(0,0)")
    p.wait_for_timeout(250)


def fetch(ctx, url, seen):
    url = url.split("?")[0]
    if url in seen or not url.startswith("http") or "buildingideascentre" not in url:
        return seen.get(url)
    # strip WordPress size suffix to reach the original upload where it exists
    name = unquote(urlparse(url).path.split("/uploads/")[-1]).replace("/", "_")
    dest = RAW / name
    if not dest.exists():
        for t in range(4):
            try:
                r = ctx.request.get(url, timeout=60000)
                break
            except Exception as e:
                print("  retry image", url[-50:], str(e)[:60], flush=True)
                time.sleep(15 * (t + 1))
        else:
            seen[url] = None
            return None
        if r.status != 200:
            print("  FAILED", r.status, url)
            seen[url] = None
            return None
        dest.write_bytes(r.body())
        time.sleep(0.25)
    seen[url] = dest.name
    return dest.name


data = {"pages": {}, "exhibitors": [], "categories": {}, "home_gallery": []}
seen = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome")
    ctx = b.new_context(user_agent=UA, viewport={"width": 1440, "height": 900}, locale="en-AU")
    p = ctx.new_page()

    goto(p, H + "exhibitors/")
    p.wait_for_timeout(2500)
    walk(p)
    cards = p.evaluate(CARDS)
    for n in p.evaluate("[...document.querySelectorAll('button.e-filter-item')].map(b=>b.innerText.trim())"):
        if n == "All":
            continue
        p.locator("button.e-filter-item", has_text=n).first.click()
        p.wait_for_timeout(1800)
        data["categories"][n] = [c["url"] for c in p.evaluate(CARDS)]
        print(n, len(data["categories"][n]))
    print("cards", len(cards))

    net = []
    p.on("response", lambda r: net.append(r.url) if "/wp-content/uploads/" in r.url and r.request.resource_type == "image" else None)
    CACHE = OUT / "exhibitors_cache"
    CACHE.mkdir(exist_ok=True)
    for c in cards:
        cf = CACHE / (urlparse(c["url"]).path.strip("/").split("/")[-1] + ".json")
        if cf.exists():
            data["exhibitors"].append(json.loads(cf.read_text(encoding="utf-8")))
            continue
        net.clear()
        goto(p, c["url"])
        p.wait_for_timeout(1500)
        walk(p)
        d = p.evaluate(DETAIL)
        c["gallery_dom"] = p.evaluate("""() => [...new Set([...document.querySelectorAll('[data-thumbnail],a[data-elementor-open-lightbox],.e-gallery-item')].map(e => e.getAttribute('data-thumbnail') || e.getAttribute('href')).filter(u => u && /uploads/.test(u)))]""")
        c["net"] = sorted(set(net))
        phone = None
        try:
            p.get_by_text("Call Now", exact=True).first.click(timeout=4000)
            p.wait_for_timeout(1000)
            phone = p.evaluate("(document.querySelector('.elementor-popup-modal a[href^=\"tel:\"]')||{}).innerText||null")
        except Exception as e:
            print("  no phone", c["name"], str(e)[:80])
        c.update(d, phone=phone)
        urls = [i["full"] or i["src"] for i in d["imgs"]] + d["bg"] + c["gallery_dom"] + c["net"]
        c["files"] = [f for f in (fetch(ctx, u, seen) for u in urls + [c["card_img"]]) if f]
        c["card_file"] = fetch(ctx, c["card_img"], seen) if c["card_img"] else None
        for i in c["imgs"]:
            i["file"] = fetch(ctx, i["full"] or i["src"], seen)
        data["exhibitors"].append(c)
        cf.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
        print(c["name"], "| net", len(c["net"]), "| dom", len(c["gallery_dom"]), "| phone", phone, "| imgs", len(d["imgs"]), "| bg", len(d["bg"]), "| brochure", bool(d["brochure"]))
        time.sleep(4)

    # core pages: every image the visitor can see, including CSS backgrounds
    BG = """() => { const out=new Set();
      document.querySelectorAll('*').forEach(e=>{ const m=getComputedStyle(e).backgroundImage.match(/url\\(["']?(.*?)["']?\\)/); if(m&&/uploads/.test(m[1])) out.add(m[1]); });
      document.querySelectorAll('img,source').forEach(i=>{ const s=i.currentSrc||i.src; if(s&&/uploads/.test(s)) out.add(s); });
      document.querySelectorAll('video').forEach(v=>out.add('VIDEO:'+(v.currentSrc||v.src)));
      return [...out]; }"""
    for path in ["", "about-us/", "events/", "events/building-ideas-expo-2026/", "exhibit-with-us/", "contact_us/"]:
        goto(p, H + path)
        time.sleep(3)
        p.wait_for_timeout(1500)
        walk(p)
        urls = p.evaluate(BG)
        files = [fetch(ctx, u, seen) for u in urls if not u.startswith("VIDEO:")]
        data["pages"][path or "home"] = dict(text=p.evaluate("document.body.innerText"), files=[f for f in files if f], videos=[u for u in urls if u.startswith("VIDEO:")])
        print(path or "home", len(files), [u for u in urls if u.startswith("VIDEO:")])

    # the logo is an inline SVG in the header
    goto(p, H)
    p.wait_for_timeout(1000)
    data["logo_svgs"] = p.evaluate("[...document.querySelectorAll('header svg, .elementor-location-header svg')].map(s=>s.outerHTML).filter(s=>s.length>1500)")
    data["favicon"] = p.evaluate("(document.querySelector('link[rel~=icon]')||{}).href||null")
    b.close()

(OUT / "site.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
print("saved", len(data["exhibitors"]), "exhibitors;", len(list(RAW.iterdir())), "images;", round(sum(f.stat().st_size for f in RAW.iterdir()) / 1e6), "MB")
