import os, re, shutil, json, zipfile
from PIL import Image, ImageDraw

# Sorgenti in _sorgenti/, app pubblicata nella radice del repository
SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(SRC)
VERSION = "v5-2026-11-04"

PAGES = [
    ("elettroliti.html", "Elettroliti in schema", "Na · K · Ca · Mg · P", "Iponatriemia per volemia, ipernatriemia, potassio con ECG, calcio, magnesio, fosfato", "#2B5FAE", "Na⁺"),
    ("acido-base.html", "Equilibrio acido-base", "EGA in 6 passi", "Compensi attesi, gap anionico, delta ratio, diagnosi differenziale", "#B0432B", "pH"),
    ("ecg.html", "ECG passo per passo", "9 passi · tracciati", "Ritmi, blocchi AV e di branca, ST-T, QT ed elettroliti, quadri clinici", "#0E6673", "ECG"),
    ("infezioni.html", "Infezioni nell'anziano", "Scelta dell'antibiotico", "Mappa dello spettro, dosi, sindromi, multiresistenti, durate, sicurezza", "#9A6410", "Rx"),
    ("neurocognitivo.html", "Delirium, demenze, psicosi", "Percorso acuto e sub-acuto", "4AT e CAM, cause del delirium, sottotipi di demenza, psicosi secondarie", "#6A4BA6", "4AT"),
    ("abcde.html", "Approccio ABCDE", "NEWS2 · consegna SBAR", "Paziente critico: valuta, tratta, chiama; NEWS2 calcolato e SBAR da copiare", "#B0432B", "ABC"),
    ("neuro-emergenza.html", "Esame neurologico in emergenza", "GCS · NIHSS · finestra ictus", "Primi 60 secondi, pupille, ictus, esame mirato, stato di male, meningite", "#2F7466", "GCS"),
    ("bls-als.html", "BLSD e ALS operativo", "Cronometro dell'arresto", "Algoritmi ERC 2025, ritmi, cause reversibili, post-ROSC, bradi e tachicardie", "#8A2B1E", "ALS"),
]

SYS_FONTS = """
  --f-display:-apple-system,BlinkMacSystemFont,"SF Pro Display","Segoe UI",system-ui,sans-serif;
  --f-body:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",system-ui,sans-serif;
  --f-mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;"""

HEAD = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Schede">
<meta name="theme-color" content="#F3F6F6" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0E1619" media="(prefers-color-scheme: dark)">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="icon" type="image/png" href="icons/icon-192.png">
"""

BASE_CSS = """<style>
:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);-webkit-text-size-adjust:100%}
body{margin:0;font-size:14px;-webkit-tap-highlight-color:transparent}
img{max-width:100%}
[hidden]{display:none!important}
.homebar{display:inline-flex;align-items:center;gap:6px;text-decoration:none;font-family:var(--f-body);font-weight:600;font-size:.9rem;color:var(--accent);padding:6px 0}
.homebar:active{opacity:.6}
</style>
"""

SW_REG = """<script>
if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js').catch(function(){});});}
</script>
"""


def convert_page(html, standalone):
    # rimuove i font remoti e usa i font di sistema (offline, nativi su iPhone)
    html = re.sub(r'<link rel="preconnect"[^>]*>\n?', '', html)
    html = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\n?', '', html)
    html = re.sub(r'\n\s*--f-display:[^;]*;\n\s*--f-body:[^;]*;\n\s*--f-mono:[^;]*;', SYS_FONTS, html, count=1)
    # pulsante "torna alle schede" in testata
    html = html.replace('<header class="top">\n  <div class="wrap">\n',
                        '<header class="top">\n  <div class="wrap">\n    <a class="homebar" href="index.html" aria-label="Torna all\'elenco delle schede">&#8249; Schede</a>\n', 1)
    title = re.search(r'<title>(.*?)</title>', html).group(0)
    html = html.replace(title + '\n', '', 1)
    html = html.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '', 1)
    head = HEAD + title + "\n" + BASE_CSS + (SW_REG if standalone else "") + "</head>\n<body>\n"
    return head + html + "\n</body>\n</html>\n"


INDEX_BODY = """<title>Schede cliniche</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* Layout: schermata iniziale tipo app — testata, elenco a schede grandi, istruzioni di installazione */
:root{
  --bg:#F3F6F6; --surface:#FFFFFF; --sunk:#E8EEEF; --ink:#13232A; --muted:#55666D; --line:#CFDADC;
  --accent:#0E6673; --accent-soft:#D9ECEE;
  --f-display:-apple-system,BlinkMacSystemFont,"SF Pro Display","Segoe UI",system-ui,sans-serif;
  --f-body:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",system-ui,sans-serif;
  --f-mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#0E1619; --surface:#152126; --sunk:#1B2A30; --ink:#E2EBED; --muted:#98AAB0; --line:#2B3C43;
  --accent:#5BBCC8; --accent-soft:#16363C; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#0E1619; --surface:#152126; --sunk:#1B2A30; --ink:#E2EBED; --muted:#98AAB0; --line:#2B3C43;
  --accent:#5BBCC8; --accent-soft:#16363C; color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--f-body);font-size:16px;line-height:1.45}
.wrap{max-width:720px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:28px 40px;display:grid;gap:22px}
.eyebrow{font-family:var(--f-display);text-transform:uppercase;letter-spacing:.08em;font-size:.72rem;font-weight:600;color:var(--muted)}
h1{font-family:var(--f-display);font-size:2.1rem;font-weight:700;letter-spacing:-.01em;margin:4px 0 0;line-height:1.1}
.sub{color:var(--muted);margin:6px 0 0;font-size:.95rem}
.list{display:grid;gap:12px}
.tile{display:grid;grid-template-columns:56px 1fr 18px;gap:14px;align-items:center;text-decoration:none;color:inherit;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:14px 16px;min-width:0}
.tile:active{transform:scale(.985)}
.tile:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.glyph{width:56px;height:56px;border-radius:14px;display:grid;place-items:center;color:#fff;font-family:var(--f-mono);font-weight:600;font-size:1rem}
.tile h2{font-family:var(--f-display);font-size:1.08rem;font-weight:600;margin:0;line-height:1.2}
.tile .k{font-family:var(--f-mono);font-size:.75rem;color:var(--accent);margin-top:2px}
.tile p{margin:4px 0 0;font-size:.85rem;color:var(--muted);line-height:1.35}
.chev{color:var(--muted);font-size:1.4rem;line-height:1}
.install{background:var(--accent-soft);border:1.5px dashed var(--accent);border-radius:14px;padding:14px 16px;display:grid;gap:6px;font-size:.9rem}
.install b{font-family:var(--f-display)}
.install ol{margin:0;padding-left:1.2em;display:grid;gap:2px}
.foot{font-size:.8rem;color:var(--muted)}
.status{font-family:var(--f-mono);font-size:.72rem;color:var(--muted)}
</style>

<div class="wrap">
  <div>
    <span class="eyebrow">Ripasso clinico · geriatria e medicina interna</span>
    <h1>Schede cliniche</h1>
    <p class="sub">Schede di consultazione rapida con fonti. In ogni scheda, "Modalità ripasso" oscura le risposte per interrogarti.</p>
  </div>
  <nav class="list" aria-label="Schede">
__TILES__
  </nav>
  <div class="install" id="install">
    <b>Installala sull'iPhone</b>
    <ol>
      <li>Apri questa pagina in <b>Safari</b>.</li>
      <li>Tocca <b>Condividi</b> (il quadrato con la freccia).</li>
      <li>Scegli <b>Aggiungi alla schermata Home</b>.</li>
    </ol>
    <span>Si aprirà a schermo intero come un'app e, dopo la prima apertura, funzionerà anche senza connessione.</span>
  </div>
  <p class="status" id="status"></p>
  <p class="foot">Schede di studio: dosi, soglie e scelte empiriche vanno verificate sui protocolli locali e sull'antibiogramma del proprio ospedale.</p>
</div>
<script>
(function(){
  var standalone=(window.navigator.standalone===true)||(window.matchMedia&&window.matchMedia('(display-mode: standalone)').matches);
  if(standalone){document.getElementById('install').hidden=true;}
  var st=document.getElementById('status');
  if('serviceWorker' in navigator && location.protocol.indexOf('http')===0){
    navigator.serviceWorker.register('sw.js').then(function(){
      return navigator.serviceWorker.ready;
    }).then(function(){st.textContent='Disponibile offline · __VERSION__';}).catch(function(){st.textContent='';});
  }
})();
</script>
"""


def tiles():
    out = []
    for f, title, k, desc, color, glyph in PAGES:
        out.append(f'''    <a class="tile" href="{f}">
      <span class="glyph" style="background:{color}">{glyph}</span>
      <span><h2>{title}</h2><span class="k">{k}</span><p>{desc}</p></span>
      <span class="chev" aria-hidden="true">&#8250;</span>
    </a>''')
    return "\n".join(out)


def make_icon(size, path, pad_ratio=0.0):
    S = size * 4
    img = Image.new("RGB", (S, S), (14, 102, 115))
    d = ImageDraw.Draw(img)
    # griglia leggera tipo carta ECG
    step = S // 10
    for i in range(1, 10):
        d.line([(i * step, 0), (i * step, S)], fill=(31, 122, 135), width=max(1, S // 256))
        d.line([(0, i * step), (S, i * step)], fill=(31, 122, 135), width=max(1, S // 256))
    # tracciato PQRST bianco
    m = S * (0.14 + pad_ratio)
    w = S - 2 * m
    base = S * 0.58
    pts = [(0, 0), (0.18, 0), (0.24, -0.06), (0.30, 0), (0.38, 0), (0.42, 0.06), (0.48, -0.40), (0.54, 0.16), (0.58, 0), (0.68, 0), (0.76, -0.12), (0.84, 0), (1, 0)]
    xy = [(m + x * w, base + y * w) for x, y in pts]
    d.line(xy, fill=(255, 255, 255), width=int(S * 0.045), joint="curve")
    img = img.resize((size, size), Image.LANCZOS)
    img.save(path, "PNG")


def build():
    os.makedirs(os.path.join(OUT, "icons"), exist_ok=True)

    for f, *_ in PAGES:
        html = open(os.path.join(SRC, f), encoding="utf-8").read()
        open(os.path.join(OUT, f), "w", encoding="utf-8").write(convert_page(html, True))

    body = INDEX_BODY.replace("__TILES__", tiles()).replace("__VERSION__", VERSION)
    # versione PWA: documento completo
    pwa_index = HEAD + body.split("\n", 1)[0] + "\n</head>\n<body>\n" + body.split("\n", 2)[2] + "\n</body>\n</html>\n"
    pwa_index = pwa_index.replace("<style>", BASE_CSS.replace("<style>", "<style>").replace("</style>\n", "") + "\n", 1) if False else pwa_index
    pwa_index = pwa_index.replace("</head>", BASE_CSS + "</head>", 1)
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(pwa_index)

    for d in (OUT,):
        make_icon(180, os.path.join(d, "icons", "apple-touch-icon.png"))
        make_icon(192, os.path.join(d, "icons", "icon-192.png"))
        make_icon(512, os.path.join(d, "icons", "icon-512.png"))
        make_icon(512, os.path.join(d, "icons", "icon-maskable-512.png"), pad_ratio=0.08)

    manifest = {
        "name": "Schede cliniche",
        "short_name": "Schede",
        "description": "Schede cliniche di ripasso e supporto operativo con fonti: elettroliti, acido-base, ECG, antibiotici, delirium, esame neurologico, BLSD e ALS.",
        "lang": "it",
        "start_url": "./index.html",
        "scope": "./",
        "display": "standalone",
        "background_color": "#0E1619",
        "theme_color": "#0E6673",
        "icons": [
            {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    for d in (OUT,):
        json.dump(manifest, open(os.path.join(d, "manifest.webmanifest"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    files = ["./", "index.html"] + [p[0] for p in PAGES] + ["manifest.webmanifest", "icons/apple-touch-icon.png", "icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png"]
    sw = f"""// Service worker: cache-first per uso offline
const CACHE = 'schede-{VERSION}';
const FILES = {json.dumps(files)};
self.addEventListener('install', e => {{
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(FILES.map(f => c.add(f).catch(() => null)))).then(() => self.skipWaiting()));
}});
self.addEventListener('activate', e => {{
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
}});
self.addEventListener('fetch', e => {{
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request, {{ignoreSearch: true}}).then(hit => hit || fetch(e.request).then(res => {{
      const copy = res.clone();
      if (res.ok && new URL(e.request.url).origin === location.origin) caches.open(CACHE).then(c => c.put(e.request, copy));
      return res;
    }}).catch(() => caches.match('index.html')))
  );
}});
"""
    open(os.path.join(OUT, "sw.js"), "w", encoding="utf-8").write(sw)

    readme = """SCHEDE CLINICHE - web app per iPhone

Contenuto: index.html (schermata iniziale), le schede, manifest, service worker (offline), icone.

PUBBLICAZIONE (una volta sola, gratis)
Opzione A - Netlify Drop
 1. Da computer apri https://app.netlify.com/drop e crea un account gratuito.
 2. Trascina nella pagina la cartella "schede-app" (non lo zip).
 3. Otterrai un indirizzo del tipo https://nome-casuale.netlify.app

Opzione B - GitHub Pages
 1. Crea un repository pubblico e carica il contenuto della cartella.
 2. Settings > Pages > Deploy from branch (main, /root).

INSTALLAZIONE SU IPHONE
 1. Apri l'indirizzo in Safari.
 2. Condividi > Aggiungi alla schermata Home.
 3. Aprila una volta con la connessione attiva: da quel momento funziona anche offline.

AGGIORNAMENTI
Se le schede cambiano, sostituisci i file e cambia la riga VERSION in sw.js:
alla successiva apertura con connessione l'app scarica la nuova versione.

Nota: il sito pubblicato e' pubblico (chi conosce l'indirizzo puo' aprirlo).
Le schede non contengono dati personali.
"""
    open(os.path.join(OUT, "LEGGIMI.txt"), "w", encoding="utf-8").write(readme)

    print("ok", OUT)


if __name__ == "__main__":
    build()
