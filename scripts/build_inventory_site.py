#!/usr/bin/env python3
"""Generate static inventory pages for stevengarcia.me from vAuto CSV exports.

Stage 1 guardrails:
- No calculated payments, finance approvals, or rebate assumptions.
- Price remains visible when available.
- Descriptions are grounded in the feed only.
"""
from __future__ import annotations

import csv
import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FEED_DIR = Path('/Users/aiden/.openclaw/workspace/inventory')
SITE = 'https://stevengarcia.me'
TODAY = date.today().isoformat()


def money(v):
    try:
        s = str(v or '').replace('$','').replace(',','').strip()
        return int(float(s)) if s else None
    except Exception:
        return None


def clean(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def slugify(s):
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s.lower()).strip('-')
    return s or 'vehicle'


def latest(kind):
    files = sorted(FEED_DIR.glob(f'*_MP5329_{kind}.csv'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError(f'No {kind} inventory CSV found in {FEED_DIR}')
    return files[0]


def split_features(raw):
    raw = clean(raw)
    if not raw:
        return []
    parts = re.split(r'\s*[|;,]\s*', raw)
    return [p for p in (clean(x) for x in parts) if p][:30]


def normalize(row, condition):
    year = clean(row.get('Year'))
    make = clean(row.get('Make')) or 'Kia'
    model = clean(row.get('Model'))
    series = clean(row.get('Series'))
    trim = clean(row.get('Series Detail')) or series
    vin = clean(row.get('VIN')).upper()
    stock = clean(row.get('Stock #'))
    photos = [u for u in clean(row.get('Photo Url List')).split('|') if u.startswith('http')]
    price = money(row.get('Price'))
    msrp = money(row.get('MSRP'))
    features = split_features(row.get('Features'))
    name = ' '.join(x for x in [year, make, model, trim] if x)
    suffix = vin[-8:] if vin else stock
    slug = slugify(' '.join(x for x in [condition, year, make, model, trim, suffix] if x))
    description_bits = []
    if clean(row.get('Description')):
        description_bits.append(clean(row.get('Description')))
    if features:
        description_bits.append('Highlights include ' + ', '.join(features[:8]) + '.')
    if clean(row.get('City MPG')) or clean(row.get('Highway MPG')):
        description_bits.append(f"EPA estimate listed in the feed: {clean(row.get('City MPG')) or 'N/A'} city / {clean(row.get('Highway MPG')) or 'N/A'} highway MPG.")
    if clean(row.get('Engine')) or clean(row.get('Fuel')):
        description_bits.append('Powertrain details from the feed: ' + ', '.join(x for x in [clean(row.get('Engine')), clean(row.get('Fuel')), clean(row.get('Drivetrain Desc'))] if x) + '.')
    desc = ' '.join(description_bits) or f'{name} available through Ancira Kia in San Antonio. Confirm current equipment, price, and availability before visiting.'
    return {
        'vin': vin, 'stock': stock, 'condition': condition, 'year': year, 'make': make, 'model': model,
        'trim': trim, 'series': series, 'name': name, 'slug': slug, 'url': f'/inventory/{slug}/',
        'body': clean(row.get('Body')), 'transmission': clean(row.get('Transmission')),
        'drivetrain': clean(row.get('Drivetrain Desc')), 'exteriorColor': clean(row.get('Colour')),
        'interiorColor': clean(row.get('Interior Color')), 'msrp': msrp, 'price': price,
        'inventoryDate': clean(row.get('Inventory Date')), 'certified': clean(row.get('Certified')),
        'description': desc, 'features': features, 'photos': photos,
        'cityMpg': clean(row.get('City MPG')), 'highwayMpg': clean(row.get('Highway MPG')),
        'photosLastModified': clean(row.get('Photos Last Modified Date')), 'engine': clean(row.get('Engine')),
        'fuel': clean(row.get('Fuel')), 'age': clean(row.get('Age')), 'odometer': clean(row.get('Odometer')),
        'dealerName': clean(row.get('Dealer Name')) or 'Ancira Kia', 'dealerAddress': clean(row.get('Dealer Address')),
        'dealerCity': clean(row.get('Dealer City')) or 'San Antonio', 'dealerPostalCode': clean(row.get('Dealer Postal Code')),
    }


def load_inventory():
    records = []
    for kind, condition in [('new','new'), ('used','used')]:
        with latest(kind).open(newline='', encoding='utf-8-sig', errors='replace') as f:
            for row in csv.DictReader(f):
                rec = normalize(row, condition)
                if rec['vin'] or rec['stock']:
                    records.append(rec)
    records.sort(key=lambda r: (r['condition'], r['model'], r['year'], r['stock']))
    return records


def e(s): return html.escape(str(s or ''), quote=True)

def fmt_price(p): return f'${p:,.0f}' if isinstance(p, int) else 'Call for price'


def css():
    return """
:root{--black:#0A0A0A;--white:#fff;--crimson:#C0392B;--mid:#999;--body:#cfcfcf;--border:#242424;--panel:#121212}*{box-sizing:border-box}body{margin:0;background:var(--black);color:var(--white);font-family:'DM Sans',Arial,sans-serif;line-height:1.55}a{color:inherit}.wrap{max-width:1180px;margin:0 auto;padding:36px 22px}.nav{border-top:2px solid var(--crimson);border-bottom:1px solid var(--border);padding:16px 22px;display:flex;justify-content:space-between;gap:16px;position:sticky;top:0;background:#0a0a0af5;backdrop-filter:blur(10px);z-index:2}.logo{font-family:'Barlow Condensed',Arial,sans-serif;font-weight:700;letter-spacing:.08em;text-transform:uppercase;text-decoration:none}.logo span,.accent{color:var(--crimson)}.nav a{font-size:12px;letter-spacing:.15em;text-transform:uppercase;text-decoration:none;color:var(--mid)}.hero{padding:70px 0 34px;border-bottom:1px solid var(--border)}h1,h2,h3{font-family:'Barlow Condensed',Arial,sans-serif;text-transform:uppercase;line-height:.95;letter-spacing:.03em}h1{font-size:clamp(48px,8vw,92px);margin:0 0 18px}h2{font-size:42px;margin:0 0 18px}.lede{font-size:20px;color:var(--body);max-width:780px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(285px,1fr));gap:18px}.card{background:var(--panel);border:1px solid var(--border);text-decoration:none;display:block}.card img,.photo-placeholder{width:100%;aspect-ratio:4/3;object-fit:cover;background:#181818}.photo-placeholder{display:flex;align-items:center;justify-content:center;color:var(--mid);font-size:12px;letter-spacing:.12em;text-transform:uppercase}.card-body{padding:16px}.price{font-size:24px;font-weight:700}.meta,.fine{color:var(--mid);font-size:13px}.btns{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}.btn{background:var(--crimson);color:#fff;text-decoration:none;padding:11px 14px;font-size:12px;letter-spacing:.12em;text-transform:uppercase;border:0}.btn.alt{background:transparent;border:1px solid var(--border)}.filters{display:grid;grid-template-columns:2fr repeat(4,1fr);gap:10px;margin:22px 0}.filters input,.filters select{background:#111;border:1px solid var(--border);color:#fff;padding:12px}.notice{border-left:3px solid var(--crimson);background:#111;padding:14px 16px;color:var(--body);margin:18px 0}.specs{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}.spec{background:#111;border:1px solid var(--border);padding:12px}.gallery{display:grid;grid-template-columns:2fr 1fr;gap:12px}.gallery img{width:100%;object-fit:cover;background:#181818}.gallery .main{aspect-ratio:4/3}.gallery .thumb{aspect-ratio:4/3;margin-bottom:12px}.features{columns:2;column-gap:28px;color:var(--body)}@media(max-width:760px){.filters{grid-template-columns:1fr}.gallery{grid-template-columns:1fr}h1{font-size:48px}.nav{position:static}.features{columns:1}}"""


def head(title, desc, canonical, extra=''):
    return f"""<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"><script async src=\"https://www.googletagmanager.com/gtag/js?id=G-XKFXV07FHV\"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-XKFXV07FHV');</script><title>{e(title)}</title><meta name=\"description\" content=\"{e(desc)}\"><link rel=\"canonical\" href=\"{SITE}{canonical}\"><meta property=\"og:title\" content=\"{e(title)}\"><meta property=\"og:description\" content=\"{e(desc)}\"><meta property=\"og:url\" content=\"{SITE}{canonical}\"><meta property=\"og:type\" content=\"website\"><link rel=\"preconnect\" href=\"https://fonts.googleapis.com\"><link href=\"https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&family=DM+Sans:wght@300;400;500;700&display=swap\" rel=\"stylesheet\"><style>{css()}</style>{extra}</head><body><nav class=\"nav\"><a class=\"logo\" href=\"/\">Steven<span>Garcia</span></a><div><a href=\"/inventory/\">Inventory</a> &nbsp; <a href=\"/blog/\">Blog</a> &nbsp; <a href=\"/ai-setup/\">AI Setup</a></div></nav>"""


def foot():
    return """<footer class=\"wrap\"><div class=\"notice fine\"><strong>Transparency note:</strong> Vehicle information comes from the dealer inventory feed and can change. Prices, equipment, incentives, photos, and availability must be verified with the dealership before purchase. Nothing on this page is a financing approval or offer to lend.</div><p class=\"fine\">© Steven Garcia. Inventory shown as a helpful shopping guide for vehicles available through Ancira Kia in San Antonio.</p></footer></body></html>"""


def write(path, content):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')


def card(rec):
    img = rec['photos'][0] if rec['photos'] else ''
    media = f'<img loading="lazy" src="{e(img)}" alt="{e(rec["name"])}">' if img else '<div class="photo-placeholder">Photos pending</div>'
    return f"""<a class="card vehicle-card" href="{e(rec['url'])}" data-year="{e(rec['year'])}" data-model="{e(rec['model'])}" data-price="{rec['price'] or 0}" data-color="{e(rec['exteriorColor'])}" data-drivetrain="{e(rec['drivetrain'])}" data-search="{e(' '.join([rec['year'],rec['make'],rec['model'],rec['trim'],rec['stock'],rec['vin'],rec['exteriorColor']]).lower())}">{media}<div class="card-body"><h3>{e(rec['name'])}</h3><div class="price">{fmt_price(rec['price'])}</div><p class="meta">Stock {e(rec['stock'])} · VIN {e(rec['vin'][-8:])}</p><p class="meta">{e(rec['exteriorColor'])} · {e(rec['drivetrain'])}</p></div></a>"""


def srp(title, desc, url, records):
    models = sorted({r['model'] for r in records if r['model']})
    years = sorted({r['year'] for r in records if r['year']}, reverse=True)
    body = head(title, desc, url)
    body += f"""<main><section class=\"hero\"><div class=\"wrap\"><p class=\"accent\">San Antonio Kia inventory</p><h1>{e(title)}</h1><p class=\"lede\">{e(desc)}</p><div class=\"notice\">Payment shopping is coming after compliance review. For now, every listing keeps the vehicle price visible and asks customers to verify current details.</div></div></section><section class=\"wrap\"><div class=\"filters\"><input id=\"q\" placeholder=\"Search model, stock, VIN, color\"><select id=\"model\"><option value=\"\">All models</option>{''.join(f'<option>{e(m)}</option>' for m in models)}</select><select id=\"year\"><option value=\"\">All years</option>{''.join(f'<option>{e(y)}</option>' for y in years)}</select><input id=\"maxPrice\" inputmode=\"numeric\" placeholder=\"Max price\"><select id=\"sort\"><option value=\"\">Sort</option><option value=\"price-asc\">Price low-high</option><option value=\"price-desc\">Price high-low</option><option value=\"year-desc\">Newest year</option></select></div><p class=\"meta\"><span id=\"count\">{len(records)}</span> vehicles shown</p><div class=\"grid\" id=\"grid\">{''.join(card(r) for r in records)}</div></section></main><script>
const cards=[...document.querySelectorAll('.vehicle-card')];
function apply(){{const q=document.getElementById('q').value.toLowerCase(),m=document.getElementById('model').value,y=document.getElementById('year').value,max=parseInt(document.getElementById('maxPrice').value||'0'),sort=document.getElementById('sort').value,grid=document.getElementById('grid');let shown=cards.filter(c=>(!q||c.dataset.search.includes(q))&&(!m||c.dataset.model===m)&&(!y||c.dataset.year===y)&&(!max||parseInt(c.dataset.price||'0')<=max));shown.sort((a,b)=>sort==='price-asc'?a.dataset.price-b.dataset.price:sort==='price-desc'?b.dataset.price-a.dataset.price:sort==='year-desc'?b.dataset.year-a.dataset.year:0);cards.forEach(c=>c.remove());shown.forEach(c=>grid.appendChild(c));document.getElementById('count').textContent=shown.length;}}
document.querySelectorAll('.filters input,.filters select').forEach(el=>el.addEventListener('input',apply));
</script>"""
    body += foot()
    write(url.strip('/') + '/index.html', body)


def jsonld(rec):
    data = {
        '@context':'https://schema.org','@type':'Vehicle','name':rec['name'],'brand':{'@type':'Brand','name':rec['make']},
        'model':rec['model'],'vehicleModelDate':rec['year'],'vehicleIdentificationNumber':rec['vin'],'sku':rec['stock'],
        'bodyType':rec['body'],'fuelType':rec['fuel'],'color':rec['exteriorColor'],'image':rec['photos'][:10],
        'description':rec['description'],'seller':{'@type':'AutoDealer','name':'Ancira Kia','address':rec['dealerAddress']},
        'url': SITE + rec['url']
    }
    if rec['odometer']:
        data['mileageFromOdometer']={'@type':'QuantitativeValue','value':rec['odometer'],'unitCode':'SMI'}
    if rec['price']:
        data['offers']={'@type':'Offer','price':rec['price'],'priceCurrency':'USD','availability':'https://schema.org/InStock','url':SITE+rec['url'],'seller':{'@type':'AutoDealer','name':'Ancira Kia'}}
    crumbs={'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Inventory','item':SITE+'/inventory/'},{'@type':'ListItem','position':2,'name':rec['name'],'item':SITE+rec['url']}]} 
    return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False)+'</script><script type="application/ld+json">'+json.dumps(crumbs,ensure_ascii=False)+'</script>'


def vdp(rec):
    title=f"{rec['name']} for Sale in San Antonio | Steven Garcia"
    desc=f"View photos, price, specs, and availability for this {rec['name']} at Ancira Kia in San Antonio. Stock {rec['stock']}."
    body=head(title, desc, rec['url'], jsonld(rec))
    thumbs=''.join(f'<img class="thumb" loading="lazy" src="{e(u)}" alt="{e(rec["name"])} photo">' for u in rec['photos'][1:4])
    main_img=rec['photos'][0] if rec['photos'] else ''
    main_media = f'<img class="main" src="{e(main_img)}" alt="{e(rec["name"])}">' if main_img else '<div class="photo-placeholder main">Photos pending</div>'
    facts=[('Price',fmt_price(rec['price'])),('MSRP',fmt_price(rec['msrp']) if rec['msrp'] else 'N/A'),('Stock',rec['stock']),('VIN',rec['vin']),('Mileage',rec['odometer'] or 'N/A'),('Exterior',rec['exteriorColor']),('Interior',rec['interiorColor']),('Drivetrain',rec['drivetrain']),('Engine',rec['engine']),('Fuel',rec['fuel']),('MPG',f"{rec['cityMpg'] or 'N/A'} city / {rec['highwayMpg'] or 'N/A'} hwy")]
    body+=f"""<main><section class=\"hero\"><div class=\"wrap\"><p class=\"accent\">{e(rec['condition'].title())} inventory · San Antonio</p><h1>{e(rec['name'])}</h1><p class=\"lede\">{e(rec['description'])}</p><div class=\"price\">{fmt_price(rec['price'])}</div><p class=\"fine\">Price and availability are subject to change. Confirm details with Ancira Kia before purchase.</p><div class=\"btns\"><a class=\"btn\" href=\"https://www.ancirakiasa.com/\" target=\"_blank\" rel=\"noopener\">Check availability with Ancira Kia</a><a class=\"btn alt\" href=\"https://www.ancirakiasa.com/\" target=\"_blank\" rel=\"noopener\">View on Ancira Kia</a><a class=\"btn alt\" href=\"https://www.linkedin.com/in/stevengarcia4/\" target=\"_blank\" rel=\"noopener\">Contact Steven</a><a class=\"btn alt\" href=\"/inventory/{'new-kia' if rec['condition']=='new' else 'used-cars'}/\">Back to {e(rec['condition'])} inventory</a></div></div></section><section class=\"wrap\"><div class=\"gallery\">{main_media}<div>{thumbs}</div></div></section><section class=\"wrap\"><h2>Vehicle details</h2><div class=\"specs\">{''.join(f'<div class="spec"><div class="meta">{e(k)}</div><strong>{e(v)}</strong></div>' for k,v in facts if v)}</div></section><section class=\"wrap\"><h2>Features from the feed</h2><ul class=\"features\">{''.join(f'<li>{e(f)}</li>' for f in rec['features'][:40]) or '<li>Feature list not available in the feed. Verify equipment with the dealer.</li>'}</ul><div class=\"notice\"><strong>Payment estimator status:</strong> Coming after compliance review. We will not show monthly payments until taxes, fees, APR assumptions, rebates, and disclosures are reviewed.</div></section></main>"""
    body+=foot()
    write(rec['url'].strip('/')+'/index.html', body)


def hub(records):
    new=[r for r in records if r['condition']=='new']; used=[r for r in records if r['condition']=='used']
    models=sorted({r['model'] for r in records if r['model']})[:12]
    body=head('New and Used Kia Inventory in San Antonio', 'Browse a cleaner, transparent inventory guide for new Kia and used vehicles available through Ancira Kia in San Antonio.', '/inventory/')
    body+=f"""<main><section class=\"hero\"><div class=\"wrap\"><p class=\"accent\">Transparent inventory guide</p><h1>New and Used Kia Inventory in San Antonio</h1><p class=\"lede\">A cleaner shopping layer built from the dealer inventory feed. Prices stay visible, payments wait for compliance review, and every vehicle page is grounded in actual feed data.</p><div class=\"btns\"><a class=\"btn\" href=\"/inventory/new-kia/\">Shop new Kia ({len(new)})</a><a class=\"btn alt\" href=\"/inventory/used-cars/\">Shop used cars ({len(used)})</a></div></div></section><section class=\"wrap\"><h2>Shop by model</h2><div class=\"grid\">{''.join(f'<a class="card" href="/inventory/new-kia/?model={quote(m)}"><div class="card-body"><h3>{e(m)}</h3><p class="meta">View available inventory</p></div></a>' for m in models)}</div></section><section class=\"wrap\"><h2>Why this exists</h2><p class=\"lede\">Most dealer inventory pages make shoppers work too hard. This version is built to be faster, clearer, and easier to understand, without hiding the details that matter.</p><div class=\"notice\">No payment claims, approval language, or rebate assumptions are shown until they are reviewed. Transparency beats tricks.</div></section></main>"""
    body+=foot()
    write('inventory/index.html', body)


def write_data(records):
    data_dir=ROOT/'inventory/data'; data_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in [('inventory',records),('new',[r for r in records if r['condition']=='new']),('used',[r for r in records if r['condition']=='used'])]:
        (data_dir/f'{name}.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    idx=[{k:r[k] for k in ['vin','stock','condition','year','make','model','trim','name','url','price']} for r in records]
    (data_dir/'search-index.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2),encoding='utf-8')


def update_sitemap(records):
    sm=ROOT/'sitemap.xml'
    text=sm.read_text(encoding='utf-8') if sm.exists() else '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>'
    ns={'sm':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    ET.register_namespace('', ns['sm'])
    root=ET.fromstring(text)
    existing={loc.text for loc in root.findall('sm:url/sm:loc', ns)}
    urls=['/inventory/','/inventory/new-kia/','/inventory/used-cars/']+[r['url'] for r in records]
    for u in urls:
        loc=SITE+u
        if loc in existing: continue
        el=ET.SubElement(root,'{http://www.sitemaps.org/schemas/sitemap/0.9}url')
        ET.SubElement(el,'{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text=loc
        ET.SubElement(el,'{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod').text=TODAY
        ET.SubElement(el,'{http://www.sitemaps.org/schemas/sitemap/0.9}changefreq').text='daily'
        ET.SubElement(el,'{http://www.sitemaps.org/schemas/sitemap/0.9}priority').text='0.7'
    ET.ElementTree(root).write(sm, encoding='utf-8', xml_declaration=True)


def update_llms(records):
    p=ROOT/'llms.txt'; txt=p.read_text(encoding='utf-8') if p.exists() else '# Steven Garcia\n'
    marker='\n## Inventory\n'
    inv=f"""
## Inventory
Steven Garcia publishes a transparent new and used vehicle inventory guide for vehicles available through Ancira Kia in San Antonio.
- Inventory hub: {SITE}/inventory/
- New Kia inventory: {SITE}/inventory/new-kia/
- Used cars: {SITE}/inventory/used-cars/
- Current generated inventory count: {len(records)} vehicles
- Vehicle pages are generated from the vAuto inventory feed and include price, photos, VIN, stock number, specs, and clear availability/pricing disclaimers.
- Payment estimates are intentionally withheld until compliance review confirms taxes, fees, APR assumptions, rebates, and finance disclosures.
"""
    if marker in txt:
        txt=txt.split(marker)[0]+inv
    else:
        txt=txt.rstrip()+"\n"+inv
    p.write_text(txt,encoding='utf-8')


def docs(records):
    write('inventory/README.md', f"""# Inventory Microsite

Generated by `python3 scripts/build_inventory_site.py` from the latest vAuto CSV files in `/Users/aiden/.openclaw/workspace/inventory`.

Generated on: {TODAY}  
Vehicle count: {len(records)}

## Compliance guardrails
- Price remains visible when available.
- No payment calculator is live in Stage 1.
- No financing approval language.
- No universal rebate assumptions.
- Descriptions are grounded in feed data only.
- Availability, pricing, equipment, and incentives must be verified with the dealer.

## Next stages
1. Human review of SRP/VDP copy and CTAs.
2. Dealer/legal review for payment estimator assumptions and disclaimers.
3. Add approved payment estimator inputs: down payment, credit range, term, APR table, taxes/fees, optional trade equity.
4. Add AI enrichment cache keyed by VIN and source-field hash.
5. Review Search Console indexing before expanding curated model/category pages.
""")


def main():
    records=load_inventory()
    out=ROOT/'inventory'
    if out.exists():
        import shutil; shutil.rmtree(out)
    hub(records)
    srp('New Kia Inventory in San Antonio', 'Browse new Kia vehicles from the current Ancira Kia inventory feed with photos, prices, specs, and clear availability notes.', '/inventory/new-kia/', [r for r in records if r['condition']=='new'])
    srp('Used Cars in San Antonio', 'Browse used vehicles from the current Ancira Kia inventory feed with photos, prices, specs, and clear availability notes.', '/inventory/used-cars/', [r for r in records if r['condition']=='used'])
    for r in records:
        vdp(r)
    write_data(records)
    docs(records)
    update_sitemap(records)
    update_llms(records)
    print(f'Generated {len(records)} inventory vehicles')

if __name__ == '__main__':
    main()
