"""Build the static Building Ideas Centre site from scraped/ into site/."""
import html
import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "scraped" / "raw_images"
SRC = ROOT / "site_src"
OUT = ROOT / "site"
IMG = OUT / "assets" / "img"
IMG.mkdir(parents=True, exist_ok=True)
(OUT / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
DATA = json.loads((ROOT / "scraped" / "site.json").read_text(encoding="utf-8"))

# Set to False at launch: removes the preview strip and lets search engines index the site.
PREVIEW = True
DOMAIN = "https://buildingideascentre.com.au"
BUILT_BY_URL = "https://launchpilotdigital.com.au/"  # LaunchPilot Digital website; the footer credit becomes a link once this is set

ADDRESS = "279 Grote Street, Adelaide SA 5000"
MAPS = "https://www.google.com/maps/dir/?api=1&destination=279+Grote+Street+Adelaide+SA+5000"
MAP_EMBED = "https://maps.google.com/maps?q=279%20Grote%20Street%2C%20Adelaide%2C%20SA%205000&t=m&z=15&output=embed&iwloc=near"
TOUR = "https://calendly.com/buildingideascentre/30min"
REGISTER = "https://docs.google.com/forms/d/e/1FAIpQLSe8lZPWy8g_dWtIFv_uzAXG3ILXYmDjTXlD-H7_mrbxPZ6IdQ/viewform"
FACEBOOK = "https://www.facebook.com/people/Building-Ideas-Centre/61556464688634/"
INSTAGRAM = "https://www.instagram.com/buildingideascentre"
EXPO_START = "2026-11-21T10:00:00+10:30"
EXPO_END = "2026-11-21T16:00:00+10:30"
SEAN = ("Sean Li", "0452 060 686")
SCOTT = ("Scott Phillips", "0448 124 518")  # spelling to be confirmed by the client

CATS = {
    "kitchen": "Kitchen",
    "bathroom": "Bathroom",
    "build": "Building &amp; Renovating",
    "roofing": "Roofing, Cladding &amp; Decking",
    "windows": "Windows, Doors &amp; Blinds",
    "climate": "Heating, Cooling &amp; Solar",
    "lighting": "Lighting &amp; Home Automation",
    "interiors": "Interiors &amp; Surfaces",
    "outdoor": "Outdoor &amp; Landscaping",
    "living": "Home Comfort &amp; Storage",
}
CAT_IMG = {
    "kitchen": "2025_06_50a51b0c4145101b30c8eafbf8e5324-scaled.jpg",
    "bathroom": "2025_06_Image_20250224160110-scaled.jpg",
    "build": "2025_06_Money-3-min.png",
    "roofing": "2025_06_Image_20250224160143-scaled.jpg",
    "windows": "2025_06_Image_20250225153607-Copy-scaled.jpg",
    "climate": "2025_06_Image_20250224160129-scaled.jpg",
    "lighting": "2025_06_DSC3947-scaled.jpg",
    "interiors": "2025_06_Image_20250225153621-scaled.jpg",
    "outdoor": "2026_09_NsYBv9WOiL-uW9qGg1rUW.jpg",
    "living": "2026_09_xvyMOLfB_pvOJz7BRa-Lxe-1024x683.jpg",
}

# key = original site slug: (new slug, display name, categories)
EX = {
    "kozco": ("1komma5", "1KOMMA5°", ["climate"]),
    "2-net-blinds-and-curtains": ("2-net-blinds-and-curtains", "2 Net Blinds and Curtains", ["windows", "lighting", "interiors"]),
    "ag-roofing": ("ag-roofing", "AG Roofing", ["roofing"]),
    "alu-colour": ("alu-colour", "Alu Colour", ["windows", "build"]),
    "austaron": ("austaron-surfaces", "Austaron Surfaces", ["interiors", "kitchen"]),
    "bic-tiles": ("bic-tiles", "BIC Tiles", ["bathroom", "interiors"]),
    "1804": ("dornford-group", "Dornford Group", ["build"]),
    "easy-living-home-elevators": ("easy-living-home-elevators", "Easy Living Home Elevators", ["living"]),
    "gree-australia": ("gree-australia", "Gree Australia", ["climate"]),
    "gutter-knight": ("gutter-knight", "Gutter Knight", ["roofing"]),
    "harlen": ("harlen", "HARLEN", ["bathroom"]),
    "haute-kitchen": ("haute-kitchens", "Haute Kitchens", ["kitchen", "bathroom"]),
    "homex-construction": ("homex-construction", "HomeX Construction", ["build"]),
    "irelax-adelaide": ("irelax-adelaide", "Irelax Adelaide", ["living"]),
    "jt-heating": ("jt-heating", "JT Heating", ["climate", "outdoor"]),
    "kitchen-scene": ("kitchen-scene", "Kitchen Scene", ["kitchen"]),
    "knotwood": ("knotwood", "Knotwood", ["roofing", "outdoor"]),
    "m-terra": ("m-terra", "M Terra", ["interiors"]),
    "max-aluminium-windows-doors": ("max-aluminium-windows-doors", "MAX Aluminium Windows &amp; Doors", ["windows"]),
    "momo": ("momo", "Momo", ["kitchen", "bathroom", "interiors"]),
    "moon-design-group": ("moon-design-group", "Moon Design Group", ["outdoor"]),
    "nero-tapware": ("nero-tapware", "Nero Tapware", ["bathroom", "kitchen"]),
    "nook-sauna": ("nook-sauna", "Nook Sauna", ["living"]),
    "over-car": ("over-car", "Over Car", ["living"]),
    "robam": ("robam", "Robam", ["kitchen"]),
    "roof-render": ("roof-and-render", "Roof &amp; Render", ["roofing"]),
    "sa-building-designers": ("sa-building-designers", "SA Building Designers", ["build"]),
    "simply-shutters-and-shades": ("simply-shutters-and-shades", "Simply Shutters and Shades", ["windows"]),
    "stylux-interiors": ("stylux-interiors", "Stylux Interiors", ["interiors"]),
    "tf-art-wall": ("tf-feature-wall", "TF Feature Wall", ["interiors"]),
    "the-fan-light-shop": ("the-fan-and-light-shop", "The Fan &amp; Light Shop", ["lighting", "climate"]),
    "the-pool-tile-company": ("the-pool-tile-company", "The Pool Tile Company", ["outdoor"]),
    "toto-toilets": ("toto-toilets", "TOTO Toilets", ["bathroom"]),
    "touch-handles": ("touch-handles", "Touch Handles", ["kitchen", "interiors"]),
}
WEBSITE_OVERRIDE = {"austaron": "https://austaronsurfaces.com/", "max-aluminium-windows-doors": None}

COPY_FIXES = [
    ("damaged faded &outdated", "damaged, faded and outdated"),
    ("in south Australia", "in South Australia"),
    ("our siter company", "our sister company"),
    ("are specialist in", "are specialists in"),
    ("products form energy", "products from energy"),
    ("aluminium thats greener", "aluminium that’s greener"),
    ("homes and business against", "homes and businesses against"),
    ("polishing, The beauty", "polishing. The beauty"),
    ("a reality …….. on time", "a reality, on time"),
    ("From providing design inspiration to customizing the perfect design. We will also help", "From design inspiration to customising the perfect design, we will also help"),
    (" We partner and work closely with leading suppliers to ensure that we deliver the quality product and materials our customers deserve in everything we do.", ""),
    ("100 years experience", "100 years’ experience"),
    ("grace-Mehak", "grace, Mehak"),
    ("Haute Kitchens sets", "Haute Kitchens sets"),
    ("prioritize", "prioritise"), ("specialize", "specialise"), ("specialized", "specialised"),
    ("personalized", "personalised"), ("customizing", "customising"), ("cozy", "cosy"),
]
IRELAX = [
    ("OGAWA BIOVIS 5D AI Massage Chair", "$29,800"),
    ("OGAWA Master Drive 2.0 4D", "Was $19,800, now $13,500"),
    ("OGAWA Sonic-X", "$6,800"),
    ("OGAWA Deluxe", "$5,850"),
    ("OGAWA Reluxe", "Was $7,999, now $4,850"),
    ("Sensei Master", "Was $14,800, now $8,950"),
    ("Master Drive AI 2.0", "$15,800"),
    ("Neuhaus Luna Recliner Massage Chair", "$6,400"),
]

e = html.escape


# ---------- images ----------
def web(src, width, name=None, keep_alpha=False, q=78):
    """Write a resized WebP and return (assets path, w, h)."""
    base = name or re.sub(r"[^a-z0-9]+", "-", Path(src).stem.lower()).strip("-")[:70]
    dest = IMG / f"{base}-{width}.webp"
    if dest.exists():
        with Image.open(dest) as im:
            return f"assets/img/{dest.name}", *im.size
    im = ImageOps.exif_transpose(Image.open(RAW / src))
    has_alpha = im.mode in ("RGBA", "LA", "P")
    im = im.convert("RGBA" if (keep_alpha and has_alpha) else "RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dest, "WEBP", quality=q, method=6)
    return f"assets/img/{dest.name}", *im.size


def picture(root, src, alt, widths=(640, 1280), sizes="100vw", cls="", lazy=True, name=None):
    parts = [web(src, w, name) for w in widths]
    srcset = ", ".join(f"{root}{p} {min(w, pw)}w" for (p, pw, _), w in zip(parts, widths))
    p, w, h = parts[-1]
    load = 'loading="lazy" decoding="async"' if lazy else 'fetchpriority="high"'
    c = f' class="{cls}"' if cls else ""
    return f'<img{c} src="{root}{p}" srcset="{srcset}" sizes="{sizes}" width="{w}" height="{h}" alt="{alt}" {load}>'


def fname(url):
    from urllib.parse import unquote, urlparse
    return unquote(urlparse(url.split("?")[0]).path.split("/uploads/")[-1]).replace("/", "_")


def norm(f):
    return re.sub(r"(-\d+x\d+|-scaled)(?=\.\w+$)", "", f)


def tel(n):
    return re.sub(r"[^\d+]", "", n)


def pretty_phone(n):
    n = n.strip()
    d = tel(n)
    if " " in n:
        return n
    if d.startswith("04") and len(d) == 10:
        return f"{d[:4]} {d[4:7]} {d[7:]}"
    return n


# ---------- exhibitors ----------
def paragraphs(c):
    rows, seen = [], set()
    source = c["paras"]
    has_p = any(t in ("P", "LI") for t, _ in source)
    stopped = False
    for t, x in source:
        if t == "H2" and re.match(r"(Product Gallery|Products)$", x):
            stopped = True
        if stopped or t == "H2" or x == "Similar Displays":
            continue
        if has_p and t not in ("P", "LI", "H3", "H4", "H5"):
            continue
        if re.match(r"(Display \w+|Call Now|Message|Visit Website|Download Brochure)$", x) or x in seen:
            continue
        seen.add(x)
        for a, b in COPY_FIXES:
            x = x.replace(a, b)
        rows.append(("li" if t == "LI" else "p", x))
    return rows


exhibitors, ideas = [], {}
for c in DATA["exhibitors"]:
    old = c["url"].rstrip("/").split("/")[-1]
    slug, name, cats = EX[old]
    main = [i for i in c["imgs"] if i.get("file")]
    logo = main[0]["file"] if main else None
    hero = main[1]["file"] if len(main) > 1 else main[0]["file"]
    seen = {norm(logo), norm(hero)}
    gallery = []
    for u in c.get("gallery_dom", []):
        f = fname(u)
        k = norm(f)
        if k in seen or not (RAW / f).exists():
            continue
        seen.add(k)
        with Image.open(RAW / f) as im:
            if im.width < 300 or im.height < 200:
                continue
        gallery.append(f)
    website = WEBSITE_OVERRIDE.get(old, c.get("website"))
    x = dict(old=old, slug=slug, name=name, cats=cats, number=c["number"], tagline=c["tagline"], phone=pretty_phone(c["phone"] or ""),
             website=website, brochure=c.get("brochure"), logo=logo, hero=hero, gallery=gallery, copy=paragraphs(c))
    exhibitors.append(x)
    if old == "tf-art-wall":
        x["tagline"] = "South Australia’s Feature Wall &amp; Venetian Plaster Specialists"
    x["ideas"] = []
    for n, f in enumerate([hero] + gallery, 1):
        iid = f"{slug}-{n}"
        thumb = web(f, 640, f"idea-{iid}")
        full = web(f, 1600, f"idea-{iid}", q=74)
        ideas[iid] = dict(id=iid, ex=x, thumb=thumb, full=full)
        x["ideas"].append(iid)

exhibitors.sort(key=lambda x: re.sub(r"^The ", "", html.unescape(x["name"])).lower())
BY_SLUG = {x["slug"]: x for x in exhibitors}
print("exhibitors", len(exhibitors), "ideas", len(ideas))
print("copy check:", [x["name"] for x in exhibitors if not x["copy"]])
cat_counts = {k: sum(k in x["cats"] for x in exhibitors) for k in CATS}


# ---------- shared markup ----------
def logo_tag(root, dark=False, h=44):
    f = "logo-white.svg" if dark else "logo.svg"
    return f'<img src="{root}assets/{f}" alt="Building Ideas Centre" width="{round(h*4.55)}" height="{h}">'


NAV = [("ideas/", "Ideas"), ("displays/", "Displays"), ("events/", "Events"), ("exhibit-with-us/", "Exhibit With Us"), ("about/", "About"), ("contact/", "Visit &amp; Contact")]


def expo_bar(root):
    return f"""<div class="expo-bar" data-until="{EXPO_END}"><div class="wrap"><span><b>Building Ideas Expo</b>, Saturday 21 November, 10am to 4pm</span><a href="{root}events/building-ideas-expo-2026/">See what's on</a></div></div>"""


def page(path, title, desc, body, schema=None, extra_js=""):
    depth = path.count("/") if path else 0
    root = "../" * depth
    nav = "".join(f'<a href="{root}{p}"{" aria-current=page" if path.startswith(p) else ""}>{t}</a>' for p, t in NAV)
    canon = f"{DOMAIN}/{path}"
    robots = '<meta name="robots" content="noindex,nofollow">' if PREVIEW else ""
    ld = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>' if schema else ""
    concept = '<div class="concept">Design preview by LaunchPilot Digital. Not the official website. Forms do not send.</div>' if PREVIEW else ""
    built_by = f'<a class="link" href="{BUILT_BY_URL}" rel="noopener">LaunchPilot Digital</a>' if BUILT_BY_URL else "LaunchPilot Digital"
    full_title = f"{title} | Building Ideas Centre" if path else title
    doc = f"""<!DOCTYPE html>
<html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">{robots}
<meta property="og:type" content="website"><meta property="og:site_name" content="Building Ideas Centre"><meta property="og:title" content="{full_title}"><meta property="og:description" content="{desc}"><meta property="og:url" content="{canon}"><meta property="og:image" content="{DOMAIN}/assets/og.jpg"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{root}assets/favicon.png">
<link rel="preload" href="{root}assets/fonts/bricolage.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{root}assets/styles.css">{ld}
</head><body>
<a class="skip" href="#main">Skip to content</a>
{concept}
{expo_bar(root)}
<header class="top"><div class="wrap">
<a class="logo" href="{root or './'}" aria-label="Building Ideas Centre home">{logo_tag(root)}</a>
<nav class="nav" aria-label="Main">{nav}</nav>
<a class="board-link" href="{root}my-ideas/">My Ideas <span class="count" data-count>0</span></a>
<button class="menu-btn" type="button" aria-expanded="false">Menu</button>
</div></header>
<main id="main">{body}</main>
<footer class="foot"><div class="wrap">
<div class="foot-grid">
<div>{logo_tag(root, True, 48)}<p>Adelaide's premier showroom for building, renovation and design ideas, all under one roof.</p></div>
<div><h2>Visit</h2><ul><li>279 Grote Street,<br>Adelaide SA 5000</li><li><a class="link" href="{MAPS}">Get directions</a></li><li>Free car parking</li></ul></div>
<div><h2>Open 7 days</h2><ul><li>Monday to Friday<br>9:00am to 5:00pm</li><li>Saturday and Sunday<br>10:00am to 4:00pm</li></ul></div>
<div><h2>Talk to us</h2><ul><li>{SEAN[0]}: <a class="tel" href="tel:{tel(SEAN[1])}">{SEAN[1]}</a></li><li>{SCOTT[0]}: <a class="tel" href="tel:{tel(SCOTT[1])}">{SCOTT[1]}</a></li><li><a href="{root}contact/">Contact us</a></li><li><a href="{FACEBOOK}">Facebook</a> · <a href="{INSTAGRAM}">Instagram</a></li></ul></div>
</div>
<div class="legal"><span>© <span data-year>2026</span> Building Ideas Centre</span><a href="{root}privacy/">Privacy policy</a><span>Built by {built_by}</span></div>
</div></footer>
<nav class="dock" aria-label="Quick actions"><a href="tel:{tel(SEAN[1])}">Call</a><a href="{MAPS}">Directions</a><a href="{root}my-ideas/">My Ideas (<span data-count>0</span>)</a></nav>
<dialog class="lb" id="lb" aria-label="Idea viewer"><div class="lb-in"><img id="lb-img" alt=""><div class="lb-bar"><div class="who"><a id="lb-name" href="#"></a><span id="lb-num"></span></div><div class="lb-ctl"><button type="button" id="lb-prev" aria-label="Previous idea">&larr;</button><button type="button" id="lb-next" aria-label="Next idea">&rarr;</button><button type="button" class="save" id="lb-save" data-id="">+ Save idea</button><button type="button" id="lb-close">Close</button></div></div></div></dialog>
{extra_js}<script src="{root}assets/main.js" defer></script>
</body></html>"""
    d = OUT / path
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(doc, encoding="utf-8")
    return root


def idea_html(root, iid, sizes="(max-width:600px) 50vw, 25vw"):
    i = ideas[iid]
    x = i["ex"]
    p, w, h = i["thumb"]
    fp = i["full"][0]
    label = CATS[x["cats"][0]]
    alt = f"{label} idea from {x['name']}, Display {x['number']}"
    return f"""<article class="idea" data-cats="{' '.join(x['cats'])}" data-q="{e(html.unescape(x['name']).lower(), True)}">
<button class="open" type="button" data-full="{root}{fp}" data-id="{iid}" data-name="{x['name']}" data-num="{x['number']}" data-href="{root}displays/{x['slug']}/" aria-label="View larger: {alt}"><img src="{root}{p}" width="{w}" height="{h}" alt="{alt}" loading="lazy" decoding="async"></button>
<button class="save" type="button" data-id="{iid}" aria-pressed="false">+ Save idea</button>
<div class="cap"><a href="{root}displays/{x['slug']}/">{x['name']}</a><span>Display {x['number']}</span></div></article>"""


def card_html(root, x):
    img = picture(root, x["hero"], f"{x['name']} display at Building Ideas Centre", (480, 800), "(max-width:600px) 100vw, 25vw", name=f"card-{x['slug']}")
    return f"""<a class="card" href="{root}displays/{x['slug']}/" data-cats="{' '.join(x['cats'])}" data-q="{e((html.unescape(x['name']) + ' ' + html.unescape(x['tagline']) + ' display ' + x['number']).lower(), True)}"><div class="ph">{img}<span class="tag">Display {x['number']}</span></div><div class="bd"><h3>{x['name']}</h3><p>{x['tagline']}</p></div></a>"""


def visit_block(root):
    return f"""<section class="visit" aria-labelledby="visit-h"><div>
<div><p class="eyebrow">Open 7 days</p><h2 id="visit-h">Come and touch it, compare it, ask about it</h2></div>
<div class="facts">
<div><h3>Where</h3><p>279 Grote Street, Adelaide SA 5000<br>Free on-site parking</p></div>
<div><h3>When</h3><p>Monday to Friday: 9:00am to 5:00pm<br>Saturday and Sunday: 10:00am to 4:00pm</p></div>
<div><h3>Who to call</h3><p>{SEAN[0]}: <a class="tel" href="tel:{tel(SEAN[1])}">{SEAN[1]}</a><br>{SCOTT[0]}: <a class="tel" href="tel:{tel(SCOTT[1])}">{SCOTT[1]}</a></p></div>
</div>
<div class="actions"><a class="btn red" href="{MAPS}">Get directions</a><a class="btn line" href="{TOUR}">Book a tour</a></div>
</div><iframe src="{MAP_EMBED}" title="Map showing Building Ideas Centre at 279 Grote Street, Adelaide" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></section>"""


def form_html(prefix, audience, company=False, subject=""):
    co = f'<label for="{prefix}-co">Company name<input id="{prefix}-co" name="company" autocomplete="organization" required></label>' if company else ""
    return f"""<form class="form" data-preview="{audience}">{co}
<label for="{prefix}-name">Your name<input id="{prefix}-name" name="name" autocomplete="name" required></label>
<label for="{prefix}-email">Email<input id="{prefix}-email" name="email" type="email" autocomplete="email" required></label>
<label for="{prefix}-phone">Phone <small>(optional)</small><input id="{prefix}-phone" name="phone" type="tel" autocomplete="tel"></label>
<label for="{prefix}-msg">Message<textarea id="{prefix}-msg" name="message" required>{subject}</textarea></label>
<div class="actions"><button class="btn red" type="submit">Send message</button></div>
<p class="note">We only use your details to reply to your enquiry. See our <a href="{'../' * (2 if prefix == 'ex' else 1)}privacy/">privacy policy</a>.</p>
<p class="done" hidden></p></form>"""


BUSINESS = {
    "@context": "https://schema.org", "@type": "HomeAndConstructionBusiness", "name": "Building Ideas Centre", "url": DOMAIN + "/",
    "description": "Adelaide showroom bringing building, renovation and design brands under one roof.",
    "image": DOMAIN + "/assets/og.jpg", "telephone": "+61452060686",
    "address": {"@type": "PostalAddress", "streetAddress": "279 Grote Street", "addressLocality": "Adelaide", "addressRegion": "SA", "postalCode": "5000", "addressCountry": "AU"},
    "openingHoursSpecification": [
        {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "opens": "09:00", "closes": "17:00"},
        {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Saturday", "Sunday"], "opens": "10:00", "closes": "16:00"}],
    "sameAs": [FACEBOOK, INSTAGRAM],
}
EVENT = {
    "@context": "https://schema.org", "@type": "Event", "name": "Building Ideas Expo 2026", "startDate": EXPO_START, "endDate": EXPO_END,
    "eventStatus": "https://schema.org/EventScheduled", "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
    "location": {"@type": "Place", "name": "Building Ideas Centre", "address": BUSINESS["address"]},
    "image": DOMAIN + "/assets/og.jpg", "description": "Meet local businesses, connect with industry professionals and explore products and services for your building or renovation project.",
    "organizer": {"@type": "Organization", "name": "Building Ideas Centre", "url": DOMAIN + "/"},
}


# ---------- home ----------
def home():
    root = ""
    tiles = [
        ("2025_02_main.png", "Inside the Building Ideas Centre showroom", "displays/", "Inside the showroom", (640, 1200), "(max-width:860px) 66vw, 36vw"),
        ("2025_06_Image_20250224160110-scaled.jpg", "Bathroom displays with Nero tapware", "ideas/?c=bathroom", "Bathroom", (480,), "20vw"),
        ("2025_06_50a51b0c4145101b30c8eafbf8e5324-scaled.jpg", "Kitchen display with black cabinetry", "ideas/?c=kitchen", "Kitchen", (480,), "20vw"),
        ("2025_06_Image_20250225153621-scaled.jpg", "Knotwood aluminium cladding display", "ideas/?c=roofing", "Cladding", (480,), "20vw"),
        ("2025_06_DSC3947-scaled.jpg", "Lighting and ceiling fan display", "ideas/?c=lighting", "Lighting", (480,), "20vw"),
        ("2025_06_Image_20250224160129-scaled.jpg", "Wood heater display", "ideas/?c=climate", "Heating", (480,), "20vw"),
    ]
    mosaic = "".join(
        f'<a href="{h}">{picture(root, f, a, w, s, lazy=n > 0)}<span>{t}</span></a>' for n, (f, a, h, t, w, s) in enumerate(tiles)
    )
    plans = [("Building a new home", "build"), ("Renovating a kitchen", "kitchen"), ("Updating a bathroom", "bathroom"),
             ("Creating outdoor living", "outdoor"), ("Saving on energy and comfort", "climate"), ("Adding finishing touches", "interiors")]
    plan_html = "".join(f'<a class="plan" href="ideas/?c={c}">{t}<i aria-hidden="true">&rarr;</i></a>' for t, c in plans)
    stats = [("60+", "Display modules"), ("5,000+", "Products to touch and compare"), ("50+", "Free car parks"), ("7", "Days a week you can visit")]
    stat_html = "".join(f'<div class="stat"><b>{a}</b><span>{b}</span></div>' for a, b in stats)
    picks = []
    for x in exhibitors:
        if len(x["ideas"]) > 1:
            picks.append(x["ideas"][1])
    pick_order = ["kitchen-scene", "harlen", "knotwood", "dornford-group", "nero-tapware", "the-pool-tile-company", "stylux-interiors", "haute-kitchens", "moon-design-group", "the-fan-and-light-shop", "simply-shutters-and-shades", "austaron-surfaces"]
    wall = []
    for s in pick_order:
        ii = BY_SLUG[s]["ideas"]
        wall.append(ii[1] if len(ii) > 1 else ii[0])
    wall_html = "".join(idea_html(root, i) for i in wall)
    cats = "".join(
        f'<a class="cat" href="displays/?c={k}">{picture(root, CAT_IMG[k], "", (480,), "(max-width:560px) 50vw, 20vw")}<div><b>{v}</b><span>{cat_counts[k]} display{"s" if cat_counts[k] != 1 else ""}</span></div></a>'
        for k, v in CATS.items())
    expo_img = picture(root, "2026_09_sI9gbHXu-O-5iejhFuUj37.jpg", "An exhibitor showing a customer air conditioning products at Building Ideas Centre", (960,), "(max-width:820px) 100vw, 50vw")
    body = f"""
<div class="wrap hero">
<div><p class="eyebrow">Adelaide's premier building and renovation showroom</p>
<h1><span>Discover.</span><span>Design.</span><span>Build.</span></h1>
<p class="lede">With so many choices, it's easy to feel overwhelmed. Find your ideas here, then come and see them in person, with leading brands under one roof.</p>
<div class="actions"><a class="btn red" href="ideas/">Browse ideas</a><a class="btn line" href="contact/">Plan your visit</a></div></div>
<div class="mosaic">{mosaic}</div>
</div>
<section class="dark section on-dark" aria-labelledby="plan-h"><div class="wrap">
<div class="head"><div><h2 id="plan-h">What are you planning?</h2><p class="lede">Start with your project and we'll show you ideas from the exhibitors who can help.</p></div></div>
<div class="plans">{plan_html}</div>
</div></section>
<section class="expo" data-until="{EXPO_END}" aria-labelledby="expo-h">
<div><p class="days" data-days-to="{EXPO_START}">Saturday 21 November</p><h2 id="expo-h">Building Ideas Expo 2026</h2>
<p class="when">Saturday 21 November, 10am to 4pm<br>279 Grote Street, Adelaide</p>
<p>Meet local businesses, connect with industry professionals and explore 40+ exhibitors, whether you're building, renovating or updating a space.</p>
<div class="actions"><a class="btn" href="{REGISTER}">Register now</a><a class="btn line" href="events/building-ideas-expo-2026/">See what's on</a></div></div>
{expo_img}
</section>
<div class="wrap"><div class="stats">{stat_html}</div></div>
<section class="section" aria-labelledby="wall-h"><div class="wrap" data-lb-scope>
<div class="head"><div><p class="eyebrow">The ideas wall</p><h2 id="wall-h">See something you like? Save it.</h2><p class="lede">Every idea comes from an exhibitor in the showroom. Save your favourites and we'll turn them into a visit list with display numbers.</p></div></div>
<div class="wall">{wall_html}</div>
<div class="more actions"><a class="btn" href="ideas/">See all {len(ideas)} ideas</a><a class="btn line" href="my-ideas/">Open My Ideas</a></div>
</div></section>
<section class="section" style="background:var(--wash)" aria-labelledby="cat-h"><div class="wrap">
<div class="head"><div><p class="eyebrow">{len(exhibitors)} exhibitors listed</p><h2 id="cat-h">Explore the displays</h2></div><a class="btn line" href="displays/">View all displays</a></div>
<div class="cats">{cats}</div>
</div></section>
<section class="section" aria-labelledby="how-h"><div class="wrap">
<div class="head"><div><h2 id="how-h">From first idea to the right people</h2></div></div>
<div class="steps">
<div class="step"><h3>Collect ideas</h3><p>Browse by project or category and save what catches your eye.</p></div>
<div class="step"><h3>Take your list</h3><p>My Ideas groups your favourites by exhibitor, with display numbers and phone numbers.</p></div>
<div class="step"><h3>See it in person</h3><p>Walk through real displays and compare the products side by side.</p></div>
<div class="step"><h3>Talk to the experts</h3><p>Speak directly with suppliers, with on-site showroom consultants to help you.</p></div>
</div></div></section>
{visit_block(root)}
"""
    page("", "Building Ideas Centre | Adelaide Building and Renovation Showroom",
         "Discover ideas for your build or renovation at Adelaide's premier showroom. 60+ displays, 5,000+ products and free parking at 279 Grote Street. Open 7 days.",
         body, BUSINESS)


# ---------- ideas ----------
def chips(items, label_all="All"):
    h = f'<button class="chip" type="button" data-c="all" aria-pressed="true">{label_all}</button>'
    for k, (v, n) in items.items():
        h += f'<button class="chip" type="button" data-c="{k}" aria-pressed="false">{v} <small>{n}</small></button>'
    return f'<div class="chips" role="group" aria-label="Filter by category">{h}</div>'


def ideas_page():
    root = "../"
    counts = {k: (v, sum(k in i["ex"]["cats"] for i in ideas.values())) for k, v in CATS.items()}
    order = sorted(ideas, key=lambda i: (int(i.rsplit("-", 1)[1]), BY_SLUG[ideas[i]["ex"]["slug"]]["name"]))
    wall = "".join(idea_html(root, i) for i in order)
    body = f"""<div class="wrap intro"><h1>Ideas</h1><p class="lede">Real products and projects from the exhibitors at Building Ideas Centre. Save the ones you like, and take your list to the showroom.</p></div>
<div class="wrap section tight" style="padding-top:0" data-filter-root data-noun="idea" data-nouns="ideas" data-lb-scope>
{chips(counts)}<p class="result" id="result" aria-live="polite">{len(ideas)} ideas</p>
<div class="wall">{wall}</div></div>"""
    page("ideas/", "Ideas for Your Build or Renovation", f"Browse {len(ideas)} kitchen, bathroom, outdoor and home ideas from Adelaide suppliers. Save your favourites and find them at Building Ideas Centre.", body)


# ---------- displays ----------
def displays_page():
    root = "../"
    counts = {k: (v, cat_counts[k]) for k, v in CATS.items()}
    cards = "".join(card_html(root, x) for x in exhibitors)
    body = f"""<div class="wrap intro"><h1>Displays</h1><p class="lede">Discover top brands and innovative products, all in one place. Choose a category, or search by business, product or display number.</p></div>
<div class="wrap section tight" style="padding-top:0" data-filter-root data-noun="display" data-nouns="displays">
<div class="toolbar"><label for="search" class="sr" style="position:absolute;left:-9999px">Search displays</label><input class="search" id="search" type="search" placeholder="Search, for example: tiles, solar or 51"></div>
{chips(counts)}<p class="result" id="result" aria-live="polite">{len(exhibitors)} displays</p>
<div class="cards">{cards}</div></div>"""
    page("displays/", "Displays and Exhibitors", "Find kitchen, bathroom, roofing, window, heating and design suppliers on display at Building Ideas Centre in Adelaide.", body)


def exhibitor_page(x, n):
    root = "../../"
    blocks, ul = [], []
    def flush():
        if ul:
            blocks.append("<ul>" + "".join(f"<li>{e(i)}</li>" for i in ul) + "</ul>")
            ul.clear()
    for t, tx in x["copy"]:
        if t == "li":
            ul.append(tx)
        else:
            flush()
            cls = ' class="sub"' if tx.endswith(":") and len(tx) < 40 else ""
            blocks.append(f"<p{cls}>{e(tx)}</p>")
    flush()
    website = f'<a class="btn line" href="{e(x["website"], True)}" rel="noopener">Visit website</a>' if x["website"] else ""
    brochure = f'<a class="btn line" href="{e(x["brochure"], True)}" rel="noopener">Download brochure</a>' if x["brochure"] else ""
    logo = ""
    if x["logo"]:
        is_svg = x["logo"].lower().endswith(".svg")
        if not is_svg:
            lp, lw, lh = web(x["logo"], 360, f"logo-{x['slug']}", keep_alpha=True, q=85)
            dark = "white" in x["logo"].lower()
            logo = f'<div class="ex-logo{" darkbg" if dark else ""}"><img src="{root}{lp}" width="{lw}" height="{lh}" alt="{x["name"]} logo" loading="lazy"></div>'
    hero = picture(root, x["hero"], f"{x['name']} at Building Ideas Centre", (640, 1000), "(max-width:860px) 100vw, 45vw", lazy=False, name=f"hero-{x['slug']}")
    gal = ""
    extras = x["ideas"][1:]
    if extras:
        gal = f'<section class="section tight" style="background:var(--wash)" aria-labelledby="gal-h"><div class="wrap" data-lb-scope><div class="head"><h2 id="gal-h">Ideas from {x["name"]}</h2></div><div class="gallery">{"".join(idea_html(root, i) for i in extras)}</div></div></section>'
    price = ""
    if x["old"] == "irelax-adelaide":
        rows = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in IRELAX)
        price = f'<section class="section tight" aria-labelledby="price-h"><div class="wrap"><div class="head"><h2 id="price-h">Massage chairs on display</h2></div><table class="price"><thead><tr><th scope="col">Model</th><th scope="col">Price</th></tr></thead><tbody>{rows}</tbody></table></div></section>'
    others = [o for o in exhibitors if o is not x and set(o["cats"]) & set(x["cats"])]
    others = (others[n % max(len(others), 1):] + others[:n % max(len(others), 1)])[:4]
    sim = ""
    if others:
        sim = f'<section class="section tight" aria-labelledby="sim-h"><div class="wrap"><div class="head"><h2 id="sim-h">Similar displays</h2></div><div class="cards">{"".join(card_html(root, o) for o in others)}</div></div></section>'
    cat_links = " ".join(f'<a class="chip" href="{root}displays/?c={c}">{CATS[c]}</a>' for c in x["cats"])
    first_id = x["ideas"][0]
    body = f"""<div class="wrap crumb"><a href="{root}displays/">Displays</a> / {x['name']}</div>
<div class="wrap ex"><div>
<span class="tag">Display {x['number']}</span><h1>{x['name']}</h1><p class="tagline">{x['tagline']}</p>
<div class="copy">{''.join(blocks)}</div>
<div class="actions"><a class="btn red" href="tel:{tel(x['phone'])}">Call {x['phone']}</a><a class="btn" href="#message">Send a message</a>{website}{brochure}</div>
<div class="actions" style="margin-top:18px">{cat_links}</div>
</div>
<div class="ex-side">{logo}{hero}
<div class="where"><b>Display {x['number']}</b><span>Find it in the showroom at 279 Grote Street. Open 7 days.</span></div>
<button class="save inline" type="button" data-id="{first_id}" aria-pressed="false">+ Save idea</button>
</div></div>
{gal}{price}
<section class="section tight" id="message" aria-labelledby="msg-h"><div class="wrap split"><div><h2 id="msg-h">Ask {x['name']} a question</h2><p class="lede" style="margin-top:12px">Send a message, or call <a class="tel" href="tel:{tel(x['phone'])}">{x['phone']}</a>.</p></div>{form_html("ex", x["name"])}</div></section>
{sim}"""
    desc = html.unescape(x["tagline"]).replace('"', "")[:110]
    page(f"displays/{x['slug']}/", f"{html.unescape(x['name'])}, Display {x['number']}", e(f"{desc}. See {html.unescape(x['name'])} at Display {x['number']}, Building Ideas Centre, 279 Grote Street, Adelaide.", True), body)


# ---------- my ideas ----------
def board_page():
    data = dict(root="../", ideas={k: dict(s=v["ex"]["slug"], t=v["thumb"][0]) for k, v in ideas.items()},
                ex={x["slug"]: dict(n=html.unescape(x["name"]), d=x["number"], p=x["phone"], t=tel(x["phone"])) for x in exhibitors})
    (OUT / "assets" / "ideas-data.js").write_text("window.BIC_IDEAS=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";", encoding="utf-8")
    body = f"""<div class="wrap intro"><h1>My Ideas</h1><p class="lede" id="board-sum">Your saved ideas, ready for your showroom visit.</p></div>
<div class="wrap section tight" style="padding-top:0">
<div id="board-tools" class="actions no-print" style="margin-bottom:26px" hidden><button class="btn red" id="print" type="button">Print my visit list</button><button class="btn line" id="copy" type="button">Copy a link to share</button><button class="btn line" id="clear" type="button">Clear all</button><p id="copied" aria-live="polite" style="flex-basis:100%;overflow-wrap:anywhere"></p></div>
<div id="board"></div>
<div id="board-empty" class="empty"><h2>Nothing saved yet</h2><p class="lede">Press Save idea on anything you like and it will appear here, grouped by exhibitor with display numbers and phone numbers.</p><a class="btn red" href="../ideas/">Browse ideas</a></div>
<div class="no-print" style="margin-top:30px"><p>Saved on this device only. No account needed.</p></div>
</div>"""
    page("my-ideas/", "My Ideas", "Your saved ideas from Building Ideas Centre, grouped by exhibitor with display numbers for your showroom visit.", body, extra_js='<script src="../assets/ideas-data.js"></script>')


# ---------- events ----------
EXPO_PHOTOS = [("2026_09_NsYBv9WOiL-uW9qGg1rUW.jpg", "Outdoor living area with blinds and ceiling fans"), ("2026_09_atIKHqoQpmDSJXblGu5jXr-1024x683.jpg", "HARLEN bathroom vanity display"),
               ("2026_09_f3odfwTFMgIb7RUCHHOPtR-1-1024x683.jpg", "Roof tile and brick display"), ("2026_09_lhmDqyL82oXw2jzo2jsvFv.webp", "Bedroom interior"),
               ("2026_09_qu6dSMUfeu_SCkeUrqiJcm.webp", "Modern kitchen interior"), ("2026_09_sI9gbHXu-O-5iejhFuUj37.jpg", "Air conditioning display with exhibitor and customer"),
               ("2026_09_xvyMOLfB_pvOJz7BRa-Lxe-1024x683.jpg", "Home sauna display"), ("2026_09_r7esk8Z98IrqAXj0xgm9vz-768x1024.jpg", "Timber-look aluminium samples")]


def events_page():
    root = "../"
    img = picture(root, "2026_09_sI9gbHXu-O-5iejhFuUj37.jpg", "An exhibitor showing a customer air conditioning products", (960,), "(max-width:860px) 100vw, 50vw")
    body = f"""<div class="wrap intro"><h1>Events</h1><p class="lede">Expos, workshops and chances to meet the people behind the products.</p></div>
<div class="wrap section tight" style="padding-top:0"><article class="split">{img}<div style="display:grid;gap:14px">
<p class="tag" style="width:max-content" data-days-to="{EXPO_START}">Upcoming</p><h2>Building Ideas Expo 2026</h2>
<p class="lede" style="color:var(--ink)"><b>Saturday 21 November 2026, 10am to 4pm</b><br>279 Grote Street, Adelaide SA 5000</p>
<p>Meet local businesses, connect with industry professionals and explore the products and services that can help bring your project to life.</p>
<div class="actions"><a class="btn red" href="{REGISTER}">Register now</a><a class="btn line" href="building-ideas-expo-2026/">See what's on</a></div></div></article></div>"""
    page("events/", "Events", "Upcoming events at Building Ideas Centre in Adelaide, including the Building Ideas Expo on Saturday 21 November 2026.", body)

    root = "../../"
    photos = "".join(picture(root, f, a, (640,), "(max-width:600px) 100vw, 25vw") for f, a in EXPO_PHOTOS)
    body = f"""<div class="wrap crumb"><a href="../">Events</a> / Building Ideas Expo 2026</div>
<div class="wrap intro"><h1>Building Ideas Expo 2026</h1>
<p class="lede" style="color:var(--ink)"><b>Saturday 21 November 2026, 10am to 4pm</b><br>279 Grote Street, Adelaide SA 5000</p>
<div class="actions"><a class="btn red" href="{REGISTER}">Register now</a><a class="btn line" href="{MAPS}">Get directions</a></div></div>
<div class="wrap section tight" style="padding-top:12px"><div class="prose">
<h2>Everything you need for your project</h2>
<p>Adelaide, get ready! On Saturday, 21 November, join us at the Building Ideas Expo and discover everything you need to take your next project to the next level. Whether you are building a new home, renovating or updating a space, meet local businesses, connect with industry professionals and explore the products and services that can help bring your project to life.</p></div>
<div class="grid3" style="margin-top:34px">
<div><h3>Discover</h3><p>Explore 40+ exhibitors showcasing products, materials, services and expertise for building, renovating and creating your home.</p></div>
<div><h3>Connect</h3><p>Meet the businesses and industry professionals behind the products. Ask questions, discuss your project, get expert advice and connect with the right people for your needs.</p></div>
<div><h3>Find what you need</h3><p>See products in person, discover new businesses and find the products, services and industry connections you can take into your own project.</p></div>
</div>
<div class="prose" style="margin-top:34px"><h2>Meet the businesses behind your next project</h2><p>From products and materials to trades, services and specialist expertise, connect directly with the businesses at BIC and discover how they can help with your next project.</p></div>
<div class="expo-grid" style="margin-top:28px">{photos}</div>
<div class="actions" style="margin-top:28px"><a class="btn red" href="{REGISTER}">Register now</a></div>
</div>"""
    page("events/building-ideas-expo-2026/", "Building Ideas Expo 2026", "Saturday 21 November 2026, 10am to 4pm at 279 Grote Street, Adelaide. Explore 40+ exhibitors and meet local building and renovation businesses.", body, EVENT)


# ---------- about, exhibit, contact, privacy, 404 ----------
def about_page():
    root = "../"
    img = picture(root, "2025_02_main-image3.jpg", "The Building Ideas Centre building on Grote Street, Adelaide", (800, 1400), "100vw", lazy=False)
    body = f"""<div class="wrap intro"><h1>About us</h1><p class="lede">Bringing homeowners, builders and designers together in one premier showroom. See, touch and compare the latest in home innovation.</p></div>
<div class="wrap">{img.replace('<img', '<img class="banner"', 1)}</div>
<section class="section"><div class="wrap split"><div><h2>A one-stop showroom for building, renovating and design inspiration</h2></div><div class="prose"><p>The Building Ideas Centre is South Australia's leading showroom for building and renovation products. Designed for homeowners, builders and designers, our space brings together top brands, innovative materials and expert advice, all under one roof.</p><p>Whether you're planning a new build, a renovation, or simply looking for inspiration, we provide the perfect environment to explore, compare and connect with industry professionals.</p></div></div></section>
<section class="section" style="background:var(--wash)"><div class="wrap"><div class="head"><h2>What you'll find here</h2></div><div class="grid3">
<div><h3>Building and renovation products</h3><p>See the latest in kitchens, bathrooms, flooring and more.</p></div>
<div><h3>Expert exhibitors</h3><p>Connect with leading suppliers showcasing innovative solutions.</p></div>
<div><h3>Inspiration and innovation</h3><p>Explore cutting-edge trends and interactive displays.</p></div>
<div><h3>Events and workshops</h3><p>Gain insights from industry experts and product specialists.</p></div></div></div></section>
<section class="section"><div class="wrap"><div class="head"><div><h2>Why visit?</h2><p class="lede">A hands-on experience where you can explore, compare and connect with top suppliers, all under one roof.</p></div></div><div class="grid3">
<div><h3>See and compare in person</h3><p>Walk through real-life displays and interact with products.</p></div>
<div><h3>Connect with trusted suppliers</h3><p>Speak directly with experts and get the best advice.</p></div>
<div><h3>Get inspired by real displays</h3><p>Find the latest trends and innovative solutions.</p></div>
<div><h3>Plan with confidence</h3><p>Make informed decisions with access to industry professionals.</p></div></div>
<div class="actions" style="margin-top:32px"><a class="btn red" href="../contact/">Plan your visit</a><a class="btn line" href="../ideas/">Browse ideas</a></div></div></section>"""
    page("about/", "About Us", "Building Ideas Centre is South Australia's leading showroom for building and renovation products, bringing top brands and expert advice under one roof.", body)


def exhibit_page():
    root = "../"
    img = picture(root, "2026_08_DJI_20260304130036_0213_D.jpg", "Aerial view of Building Ideas Centre and its car park", (800, 1024), "(max-width:860px) 100vw, 50vw", lazy=False)
    benefits = [("Prime location and exposure", "A permanent showroom space open 7 days a week, ensuring steady visitor traffic."),
                ("Lead generation", "Customer enquiries are collected via QR codes and immediately sent to exhibitors by our concierge team."),
                ("60 stylish display modules", "Showcase your products in a premium, professionally designed setting."),
                ("Custom display spaces", "Choose from small (14 sqm), medium (24 sqm) or large (80 to 100 sqm) walled-off spaces."),
                ("Dedicated customer service", "Visitors are assisted by two on-site showroom consultants, ensuring a smooth experience."),
                ("Conference and meeting rooms", "Meeting rooms available for business meetings and product presentations."),
                ("Free on-site parking", "Hassle-free access for exhibitors and visitors alike."),
                ("Brand visibility", "Advertise on Adelaide's largest 3D LED screen and with in-centre promotions.")]
    grid = "".join(f"<div><h3>{a}</h3><p>{b}</p></div>" for a, b in benefits)
    body = f"""<div class="wrap section tight"><div class="split"><div style="display:grid;gap:18px"><h1 style="font-size:clamp(42px,5.4vw,76px)">Exhibit with us</h1><p class="lede">Display and sell your products to homeowners, builders and designers actively looking for solutions, in a 3,800 sqm high-exposure showroom.</p><div class="actions"><a class="btn red" href="#enquire">Enquire now</a><a class="btn line" href="{TOUR}">Book a tour</a></div></div>{img}</div></div>
<section class="section" style="background:var(--wash)"><div class="wrap"><div class="head"><h2>Benefits for your business and customers</h2></div><div class="grid3">{grid}</div></div></section>
<section class="section" id="enquire"><div class="wrap split"><div style="display:grid;gap:14px"><h2>Interested in showcasing your brand?</h2><p class="lede">Join leading suppliers and take advantage of Adelaide's top building and renovation showroom.</p><p><a class="link" href="../displays/">See who's already exhibiting</a></p></div>{form_html("co", "the Building Ideas Centre team", company=True)}</div></section>"""
    page("exhibit-with-us/", "Exhibit With Us", "Showcase your business in a 3,800 sqm Adelaide building showroom, open 7 days, with lead generation, on-site consultants and free parking.", body)


def contact_page():
    body = f"""<div class="wrap intro"><h1>Visit and contact</h1><p class="lede">Open 7 days at 279 Grote Street, Adelaide, with free on-site parking. Call us, send a message or book a tour.</p></div>
{visit_block("../").replace("<h2 id", "<h2 style='display:block' id", 1)}
<section class="section"><div class="wrap split"><div style="display:grid;gap:14px"><h2>Send us a message</h2><p class="lede">For general enquiries, fill in this form and we'll get back to you.</p><p>Thinking of exhibiting? <a class="link" href="../exhibit-with-us/#enquire">Enquire about a display</a></p></div>{form_html("gen", "the Building Ideas Centre team")}</div></section>"""
    page("contact/", "Visit and Contact", "Find Building Ideas Centre at 279 Grote Street, Adelaide. Open 7 days with free parking. Call Sean or Scott, send a message or book a tour.", body, BUSINESS)


def privacy_page():
    body = """<div class="wrap intro"><h1>Privacy policy</h1></div><div class="wrap section tight" style="padding-top:0"><div class="prose">
<p class="draft">Draft for review. Building Ideas Centre should have this checked and completed before the site goes live.</p>
<h2>What we collect</h2><p>When you send an enquiry, we collect the name, email address, phone number and message you provide.</p>
<h2>How we use it</h2><p>We use your details to respond to your enquiry. If you ask about a particular exhibitor, we pass your enquiry to that exhibitor so they can reply.</p>
<h2>Your saved ideas</h2><p>My Ideas is stored in your own browser on your own device. We don't receive it unless you choose to share it.</p>
<h2>Contact us</h2><p>To ask about or correct the information we hold about you, contact us at 279 Grote Street, Adelaide SA 5000, or on the numbers shown on our contact page.</p></div></div>"""
    page("privacy/", "Privacy Policy", "How Building Ideas Centre handles the details you provide through this website.", body)


def not_found():
    body = """<div class="wrap section"><div style="display:grid;gap:18px;justify-items:start"><h1>That page isn't here</h1><p class="lede">It may have moved. Try one of these instead.</p><div class="actions"><a class="btn red" href="/">Home</a><a class="btn line" href="/ideas/">Ideas</a><a class="btn line" href="/displays/">Displays</a><a class="btn line" href="/contact/">Contact</a></div></div></div>"""
    page("404-build/", "Page Not Found", "This page could not be found.", body)
    t = (OUT / "404-build" / "index.html").read_text(encoding="utf-8").replace('href="../', 'href="/').replace('src="../', 'src="/')
    (OUT / "404.html").write_text(t, encoding="utf-8")
    shutil.rmtree(OUT / "404-build")


# ---------- static files ----------
def statics():
    a = OUT / "assets"
    shutil.copy(SRC / "styles.css", a / "styles.css")
    shutil.copy(SRC / "main.js", a / "main.js")
    shutil.copy(RAW / "2025_02_Mobile-Logo.svg", a / "logo.svg")
    shutil.copy(RAW / "2025_02_Asset-3.svg", a / "logo-white.svg")
    Image.open(RAW / "2025_02_Group-31.png").convert("RGBA").save(a / "favicon.png")
    im = ImageOps.fit(Image.open(RAW / "2025_02_main.png").convert("RGB"), (1200, 630))
    im.save(a / "og.jpg", quality=80)
    fonts = {"bricolage.woff2": "https://fonts.gstatic.com/s/bricolagegrotesque/v9/3y9K6as8bTXq_nANBjzKo3IeZx8z6up5BeSl9D4dj_x9PpZBMlGIInE.woff2",
             "figtree.woff2": "https://fonts.gstatic.com/s/figtree/v9/_Xms-HUzqDCFdgfMm4S9DQ.woff2"}
    for n, u in fonts.items():
        if not (a / "fonts" / n).exists():
            urllib.request.urlretrieve(u, a / "fonts" / n)
    urls = ["", "ideas/", "displays/", "events/", "events/building-ideas-expo-2026/", "exhibit-with-us/", "about/", "contact/", "privacy/"] + [f"displays/{x['slug']}/" for x in exhibitors]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{DOMAIN}/{u}</loc></url>" for u in urls) + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(("User-agent: *\nDisallow: /\n" if PREVIEW else f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n"), encoding="utf-8")
    # keep old addresses working after launch
    old = {"about-us": "/about/", "exhibitors": "/displays/", "contact_us": "/contact/"}
    old.update({f"display/{x['old']}": f"/displays/{x['slug']}/" for x in exhibitors})
    (OUT / "_redirects").write_text("".join(f"/{k}/ {v} 301\n" for k, v in old.items()), encoding="utf-8")


home(); ideas_page(); displays_page(); board_page(); events_page(); about_page(); exhibit_page(); contact_page(); privacy_page(); not_found()
for n, x in enumerate(exhibitors):
    exhibitor_page(x, n)
statics()
size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
print("site", round(size / 1e6, 1), "MB,", sum(1 for _ in OUT.rglob("index.html")), "pages")
