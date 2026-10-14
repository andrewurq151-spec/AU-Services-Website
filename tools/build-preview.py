"""
Dev-only tool — NOT part of the deployed site.

Flattens the 5 real, independent pages (index/services/about/reviews/
contact.html) into a single scrolling HTML file with anchor sections
(#home #services #about #reviews #contact), so it can be published as
a single-page preview (e.g. via a Claude/Cowork Artifact, whose CSP
blocks the Tabler Icons CDN stylesheet and hotlinked images). It:

  - pulls the shared <nav> and <footer> out of index.html
  - rewrites *.html hrefs to #anchor hrefs
  - converts every Tabler <i class="ti ti-X"> icon to an inline SVG
    <use> referencing a hand-maintained icon sprite (add any new
    icon used on the site to ICON_SPRITE below)
  - embeds every assets/img/... image as a base64 data: URI
  - appends a small scroll-spy script so the nav's active-state
    follows scroll position (the real multi-page site doesn't need
    this — each page already hardcodes its own class="active")

Run with: python3 tools/build-preview.py
Then publish the resulting au-website-preview.html file.
"""
import re, base64, mimetypes, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path("/home/claude/au-website-preview.html")

def read(p):
    return (ROOT / p).read_text(encoding="utf-8")

index = read("index.html")
services = read("services.html")
about = read("about.html")
reviews = read("reviews.html")
contact = read("contact.html")
css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")

def extract(src, start_marker, end_marker, start_offset=0, include_start=False, include_end=False):
    si = src.index(start_marker)
    if include_start:
        s = si
    else:
        s = si + (0 if start_offset else len(start_marker))
        s += start_offset
    ei = src.index(end_marker, s)
    e = ei + len(end_marker) if include_end else ei
    return src[s:e]

# NAV: from "<!-- NAV -->" to "<!-- HERO -->" (exclude the HERO marker)
nav = extract(index, "<!-- NAV -->", "<!-- HERO -->").strip()
nav = nav[len("<!-- NAV -->"):].strip() if nav.startswith("<!-- NAV -->") else nav

# Actually simpler: locate substrings directly.
def between(src, a, b):
    s = src.index(a) + len(a)
    e = src.index(b, s)
    return src[s:e].strip()

nav = between(index, "<!-- NAV -->", "<!-- HERO -->")
footer = index[index.index("<!-- FOOTER -->"):index.index("</html>")]
footer = footer[len("<!-- FOOTER -->"):].strip()
# trim footer to end at </footer>
footer = footer[:footer.index("</footer>") + len("</footer>")]

def page_body(src):
    # from end of </nav> to start of <!-- FOOTER -->
    s = src.index("</nav>") + len("</nav>")
    e = src.index("<!-- FOOTER -->")
    return src[s:e].strip()

body_home = page_body(index)
body_services = page_body(services)
body_about = page_body(about)
body_reviews = page_body(reviews)
body_contact = page_body(contact)

def fix_hrefs(s):
    # Deep links into a specific services.html section (e.g. the homepage
    # "What we do" cards linking to services.html#service-02) resolve to
    # that same id inside the flattened preview's #services block, so this
    # has to run BEFORE the bare "services.html" -> "#services" rewrite
    # below or the fragment gets clobbered.
    s = re.sub(r'href="services\.html#([^"]+)"', r'href="#\1"', s)
    s = s.replace('href="index.html"', 'href="#home"')
    s = s.replace('href="services.html"', 'href="#services"')
    s = s.replace('href="about.html"', 'href="#about"')
    s = s.replace('href="reviews.html"', 'href="#reviews"')
    s = s.replace('href="contact.html"', 'href="#contact"')
    return s

ICON_TAG_RE = re.compile(r'<i\s+([^>]*?)\s*></i>')
ATTR_RE = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)="([^"]*)"')

def fix_icons(s):
    def repl(m):
        attrs_str = m.group(1)
        attrs = ATTR_RE.findall(attrs_str)
        d = dict(attrs)
        classes = d.get("class", "").split()
        icon_name = None
        remaining = []
        for c in classes:
            if c == "ti":
                continue
            if c.startswith("ti-"):
                icon_name = c[3:]
                continue
            remaining.append(c)
        remaining.append("i")
        new_class = " ".join(remaining)
        other_attrs = []
        for k, v in attrs:
            if k == "class":
                continue
            other_attrs.append(f'{k}="{v}"')
        attr_str = " ".join(['class="' + new_class + '"'] + other_attrs)
        return f'<svg {attr_str}><use href="#i-{icon_name}"></use></svg>'
    return ICON_TAG_RE.sub(repl, s)

IMG_SRC_RE = re.compile(r'assets/img/([A-Za-z0-9_\-.]+)')

def embed_images(s):
    def repl(m):
        fname = m.group(1)
        fpath = ROOT / "assets/img" / fname
        if not fpath.exists():
            return m.group(0)
        mime = mimetypes.guess_type(fname)[0] or "application/octet-stream"
        data = base64.b64encode(fpath.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{data}"
    return IMG_SRC_RE.sub(repl, s)

# External hotlinked photos (e.g. Unsplash) can't be embedded — this sandbox's
# outbound network is policy-blocked for arbitrary hosts, so there's no way to
# fetch the bytes server-side, and the Artifact viewer's CSP blocks the
# hotlink itself at view time. They work fine on the real deployed site (a
# normal browser, no sandbox), so leave the real .html files alone — this only
# swaps the *preview's* copy for a tasteful navy/gold gradient placeholder so
# it doesn't render as a broken image.
EXTERNAL_IMG_RE = re.compile(r'https://images\.unsplash\.com/[^"\']*')
_PLACEHOLDER_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' width='800' height='600'>"
    "<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
    "<stop offset='0' stop-color='%230A1F44'/>"
    "<stop offset='0.6' stop-color='%230d2450'/>"
    "<stop offset='1' stop-color='%23142c5c'/>"
    "</linearGradient></defs>"
    "<rect width='800' height='600' fill='url(%23g)'/>"
    "<circle cx='680' cy='80' r='140' fill='rgba(212,175,55,0.09)'/>"
    "</svg>"
)
# Note: single-quoted SVG attributes so the data URI never contains a literal
# double quote (this gets embedded inside an HTML src="..." attribute).
PLACEHOLDER_DATA_URI = "data:image/svg+xml," + _PLACEHOLDER_SVG.replace("#", "%23").replace(" ", "%20")

def placeholder_external_images(s):
    return EXTERNAL_IMG_RE.sub(PLACEHOLDER_DATA_URI, s)

# Local <script src="assets/js/...."> tags (form-submit.js, year.js,
# reviews-filter.js, etc.) sit after <!-- FOOTER --> in each real page, so
# page_body()/the shared footer extraction above never carry them into the
# flattened preview — they were previously just silently dropped, meaning
# none of that JS ever actually ran in the Cowork preview (a real gap: e.g.
# the Reviews page's rating filter/summary needs its script to do anything).
# Fix: scan the raw page sources for every local script tag, dedupe by
# filename (several pages share form-submit.js/year.js), and inline each
# file's contents once near the end of the flattened document — same
# execution-order guarantee as the real pages (DOM already present).
LOCAL_SCRIPT_RE = re.compile(r'<script src="assets/js/([A-Za-z0-9_\-.]+)"></script>')

def collect_local_scripts(*sources):
    names = []
    for src in sources:
        for m in LOCAL_SCRIPT_RE.finditer(src):
            name = m.group(1)
            if name not in names:
                names.append(name)
    return names

def process(s):
    s = fix_hrefs(s)
    s = fix_icons(s)
    s = embed_images(s)
    s = placeholder_external_images(s)
    return s

nav = process(nav)
footer = process(footer)
body_home = process(body_home)
body_services = process(body_services)
body_about = process(body_about)
body_reviews = process(body_reviews)
body_contact = process(body_contact)

ICON_SPRITE = '''<svg style="display:none" aria-hidden="true">
<symbol id="i-search" viewBox="0 0 24 24"><circle cx="10" cy="10" r="6"/><line x1="21" y1="21" x2="15.5" y2="15.5"/></symbol>
<symbol id="i-flame" viewBox="0 0 24 24"><path d="M12 2c1 3-2 4-2 7a4 4 0 1 0 8 0c0-1-.5-2-1-3 .8 3-1 4-2 4-1.5 0-2-1.5-1-3-2 .5-4 2.5-4 5a6 6 0 0 0 12 0c0-5-4-6-6-10z"/></symbol>
<symbol id="i-sparkles" viewBox="0 0 24 24"><path d="M12 3l1.6 4.9L18.5 9l-4.9 1.6L12 15.5l-1.6-4.9L5.5 9l4.9-1.6z"/><path d="M19 15l.7 2.1L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.9z"/></symbol>
<symbol id="i-trending-up" viewBox="0 0 24 24"><polyline points="3 17 9 11 13 15 21 6"/><polyline points="15 6 21 6 21 12"/></symbol>
<symbol id="i-file-text" viewBox="0 0 24 24"><path d="M6 3h8l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><line x1="8.5" y1="12" x2="15.5" y2="12"/><line x1="8.5" y1="16" x2="15.5" y2="16"/></symbol>
<symbol id="i-receipt-tax" viewBox="0 0 24 24"><path d="M6 2h12v20l-2.5-1.5L13 22l-2.5-1.5L8 22l-2-1.5z"/><line x1="9" y1="14.5" x2="15" y2="8.5"/><circle cx="9.3" cy="8.8" r="1"/><circle cx="14.7" cy="14.2" r="1"/></symbol>
<symbol id="i-calculator" viewBox="0 0 24 24"><rect x="5" y="2" width="14" height="20" rx="1.5"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="11" x2="8" y2="11.01"/><line x1="12" y1="11" x2="12" y2="11.01"/><line x1="16" y1="11" x2="16" y2="11.01"/><line x1="8" y1="15" x2="8" y2="15.01"/><line x1="12" y1="15" x2="12" y2="15.01"/><line x1="16" y1="15" x2="16" y2="18"/><line x1="8" y1="18" x2="12" y2="18"/></symbol>
<symbol id="i-chart-line" viewBox="0 0 24 24"><polyline points="4 19 4 5"/><polyline points="4 19 20 19"/><polyline points="7 15 11 10 14 13 19 7"/></symbol>
<symbol id="i-star" viewBox="0 0 24 24"><path d="M12 2.5l2.9 6 6.6.7-4.9 4.5 1.3 6.5L12 16.9l-5.9 3.3 1.3-6.5-4.9-4.5 6.6-.7z"/></symbol>
<symbol id="i-shield-check" viewBox="0 0 24 24"><path d="M12 2l8 3v6c0 5-3.5 8.5-8 11-4.5-2.5-8-6-8-11V5z"/><polyline points="8.5 12 11 14.5 15.5 9.5"/></symbol>
<symbol id="i-refresh" viewBox="0 0 24 24"><path d="M4 12a8 8 0 0 1 14-5.2M20 6v5h-5"/><path d="M20 12a8 8 0 0 1-14 5.2M4 18v-5h5"/></symbol>
<symbol id="i-scale" viewBox="0 0 24 24"><line x1="12" y1="3" x2="12" y2="21"/><line x1="5" y1="7" x2="19" y2="7"/><path d="M5 7l-3 6a3 3 0 0 0 6 0z"/><path d="M19 7l-3 6a3 3 0 0 0 6 0z"/></symbol>
<symbol id="i-check" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></symbol>
<symbol id="i-building" viewBox="0 0 24 24"><rect x="4" y="3" width="12" height="18"/><line x1="7" y1="7" x2="9" y2="7"/><line x1="11" y1="7" x2="13" y2="7"/><line x1="7" y1="11" x2="9" y2="11"/><line x1="11" y1="11" x2="13" y2="11"/><line x1="7" y1="15" x2="9" y2="15"/><line x1="11" y1="15" x2="13" y2="15"/><path d="M16 9h4v12h-4"/></symbol>
<symbol id="i-building-community" viewBox="0 0 24 24"><path d="M3 21V10l5-3.5V21"/><path d="M8 21V6l5 2.5V21"/><path d="M13 21V12l5 2v7"/><line x1="3" y1="21" x2="21" y2="21"/></symbol>
<symbol id="i-map-pin" viewBox="0 0 24 24"><path d="M12 21s7-7.2 7-12a7 7 0 0 0-14 0c0 4.8 7 12 7 12z"/><circle cx="12" cy="9" r="2.5"/></symbol>
<symbol id="i-phone" viewBox="0 0 24 24"><path d="M5 4h4l1.5 4.5-2 1.5a12 12 0 0 0 6 6l1.5-2 4.5 1.5v4a1.5 1.5 0 0 1-1.6 1.5A17 17 0 0 1 3.5 5.6 1.5 1.5 0 0 1 5 4z"/></symbol>
<symbol id="i-mail" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="1.5"/><polyline points="3.5 6 12 13 20.5 6"/></symbol>
<symbol id="i-users" viewBox="0 0 24 24"><circle cx="9" cy="7.5" r="3.2"/><path d="M2.5 20c0-3.6 2.9-6.2 6.5-6.2s6.5 2.6 6.5 6.2"/><path d="M16.2 4.8a3.2 3.2 0 0 1 0 6.3"/><path d="M18.7 13.9c2.6.5 4.3 2.7 4.3 6.1"/></symbol>
<symbol id="i-arrow-narrow-right" viewBox="0 0 24 24"><line x1="3" y1="12" x2="21" y2="12"/><polyline points="15 6 21 12 15 18"/></symbol>
<symbol id="i-menu-2" viewBox="0 0 24 24"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/></symbol>
<symbol id="i-x" viewBox="0 0 24 24"><line x1="6" y1="6" x2="18" y2="18"/><line x1="6" y1="18" x2="18" y2="6"/></symbol>
</svg>'''

EXTRA_CSS = '''
.i{width:1em;height:1em;stroke:currentColor;stroke-width:1.8;fill:none;stroke-linecap:round;stroke-linejoin:round;vertical-align:-0.15em;display:inline-block}
#home,#services,#about,#reviews,#contact{scroll-margin-top:71px}
[id^="service-"]{scroll-margin-top:90px}
.preview-banner{background:#fff8e1;border-bottom:1px solid rgba(212,175,55,.35);text-align:center;padding:9px 20px;font-size:12.5px;color:#6b5510}
.preview-banner strong{color:var(--n)}
'''

SCROLLSPY = '''<script>
(function(){
  var ids = ['home','services','about','reviews','contact'];
  var sections = ids.map(function(id){return document.getElementById(id);}).filter(Boolean);
  var links = Array.prototype.slice.call(document.querySelectorAll('.nav-links a[href^="#"]:not(.btn)'));
  var navEl = document.querySelector('.site-nav');
  function navHeight(){ return navEl ? navEl.offsetHeight : 70; }
  function setActive(id){
    links.forEach(function(a){
      a.classList.toggle('active', a.getAttribute('href') === '#' + id);
    });
  }
  function onScroll(){
    var offset = navHeight() + 12;
    var current = sections[0];
    for (var i = 0; i < sections.length; i++){
      if (sections[i].getBoundingClientRect().top - offset <= 0) current = sections[i];
    }
    if (current) setActive(current.id);
  }
  window.addEventListener('scroll', onScroll, {passive:true});
  window.addEventListener('resize', onScroll);
  onScroll();
})();
</script>'''

nav = fix_hrefs(nav)  # already processed but ensure brand href fixed too (index.html -> #home) already covered

local_script_names = collect_local_scripts(index, services, about, reviews, contact)
LOCAL_SCRIPTS_INLINE = "\n".join(
    "<script>\n" + (ROOT / "assets/js" / name).read_text(encoding="utf-8") + "\n</script>"
    for name in local_script_names
)

parts = []
# Without an explicit charset the browser has to guess one (this sandbox's
# plain `python3 -m http.server` sends no charset in its Content-Type
# header either), and can guess wrong — e.g. rendering an em dash as
# mojibake ("â€"") even though the file's actual bytes are correct UTF-8.
# Declare it explicitly so every non-ASCII character in the preview
# (em/en dashes, curly quotes, the © symbol, etc.) renders correctly.
parts.append('<meta charset="UTF-8">')
parts.append("<title>AU Accounting Services — Live Preview</title>")
parts.append("<style>")
parts.append(css)
parts.append(EXTRA_CSS)
parts.append("</style>")
parts.append(ICON_SPRITE)
parts.append('<div class="preview-banner"><strong>Live working preview</strong> — all five pages on one scrollable page. The real site (in your downloaded files / GitHub repo) is properly multi-page, and the hotlinked stock photos (shown here as navy placeholder blocks, since this sandbox can\'t load external images) will display normally there.</div>')
parts.append("")
parts.append(nav)
parts.append("")
parts.append('<div id="home">')
parts.append(body_home)
parts.append("</div>")
parts.append('<div id="about">')
parts.append(body_about)
parts.append("</div>")
parts.append('<div id="services">')
parts.append(body_services)
parts.append("</div>")
parts.append('<div id="reviews">')
parts.append(body_reviews)
parts.append("</div>")
parts.append('<div id="contact">')
parts.append(body_contact)
parts.append("</div>")
parts.append(footer)
parts.append("")
parts.append(LOCAL_SCRIPTS_INLINE)
parts.append("")
parts.append(SCROLLSPY)

out = "\n".join(parts)
OUT.write_text(out, encoding="utf-8")
print("Wrote", OUT, len(out), "bytes")
