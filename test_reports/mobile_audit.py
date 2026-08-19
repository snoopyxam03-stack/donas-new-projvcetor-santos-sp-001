"""Mobile responsive audit for Prefeitura Campo Alegre-AL public site."""
import asyncio, json, time, os
from playwright.async_api import async_playwright

BASE = "https://alegra-sandbox.preview.emergentagent.com"
PAGES = [
    ("/inicio.html", "inicio"),
    ("/inscricao.html", "inscricao"),
    ("/confirmacao.html", "confirmacao"),
    ("/inscricao-realizada", "inscricao-realizada"),
    ("/pagamento-pix", "pagamento-pix"),
    ("/termos.html", "termos"),
]

VIEWPORTS = [
    {"name": "iPhone_SE", "width": 375, "height": 667, "dsf": 2, "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Mobile/15E148 Safari/604.1"},
    {"name": "iPhone_13_Pro", "width": 390, "height": 844, "dsf": 3, "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Mobile/15E148 Safari/604.1"},
    {"name": "Pixel_5", "width": 393, "height": 851, "dsf": 2.75, "ua": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36"},
    {"name": "Galaxy_S8plus", "width": 360, "height": 740, "dsf": 3, "ua": "Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36"},
]

SHOT_DIR = "/app/test_reports/screenshots/mobile"
os.makedirs(SHOT_DIR, exist_ok=True)

AUDIT_JS = """
(() => {
  const vw = window.innerWidth;
  const issues = [];
  // horizontal overflow
  const bodySW = document.body.scrollWidth;
  const docSW = document.documentElement.scrollWidth;
  if (bodySW > vw + 2) issues.push({type:'horizontal_overflow', body_scrollWidth: bodySW, viewport: vw});
  if (docSW > vw + 2) issues.push({type:'doc_overflow', doc_scrollWidth: docSW, viewport: vw});

  // critical overflowing elements
  const critical = document.querySelectorAll('button, a, input, select, textarea, [data-testid]');
  const overflows = [];
  critical.forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return;
    if (r.right > vw + 5) {
      overflows.push({
        tag: el.tagName,
        testid: el.getAttribute('data-testid'),
        text: (el.innerText||el.value||'').slice(0,40),
        right: Math.round(r.right),
        width: Math.round(r.width),
      });
    }
  });

  // touch targets on data-testid buttons/links
  const smallTargets = [];
  document.querySelectorAll('[data-testid]').forEach(el => {
    const tag = el.tagName.toLowerCase();
    if (!['button','a','input'].includes(tag)) return;
    const r = el.getBoundingClientRect();
    if (r.width === 0) return;
    if (r.width < 90 || r.height < 40) {
      smallTargets.push({testid: el.getAttribute('data-testid'), tag, w: Math.round(r.width), h: Math.round(r.height)});
    }
  });

  // IGEDUC logo overflow
  const logo = document.querySelector('img[alt*="IGEDUC" i], img[src*="igeduc" i], .igeduc-logo, [class*="logo"] img');
  let logoInfo = null;
  if (logo) {
    const r = logo.getBoundingClientRect();
    logoInfo = {w: Math.round(r.width), h: Math.round(r.height), right: Math.round(r.right)};
  }

  // page loader still visible?
  const loader = document.querySelector('#__page_loader');
  const loaderVisible = loader ? (getComputedStyle(loader).opacity !== '0' && getComputedStyle(loader).display !== 'none') : null;

  // Área do Candidato
  const areaCand = Array.from(document.querySelectorAll('a,button')).find(el => /área do candidato/i.test(el.textContent||''));
  let areaCandInfo = null;
  if (areaCand) {
    const r = areaCand.getBoundingClientRect();
    areaCandInfo = {visible: r.width>0 && r.height>0, w:Math.round(r.width), h:Math.round(r.height), right:Math.round(r.right)};
  }

  return {
    viewport: vw,
    body_scrollWidth: bodySW,
    doc_scrollWidth: docSW,
    issues, overflows: overflows.slice(0,20), smallTargets: smallTargets.slice(0,20),
    logoInfo, loaderVisible, areaCandInfo,
  };
})();
"""

async def run():
    results = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for vp in VIEWPORTS:
            ctx = await browser.new_context(
                viewport={"width": vp["width"], "height": vp["height"]},
                device_scale_factor=vp["dsf"], is_mobile=True, has_touch=True,
                user_agent=vp["ua"],
            )
            page = await ctx.new_page()
            for path, name in PAGES:
                url = f"{BASE}{path}?_={int(time.time()*1000)}"
                key = f"{vp['name']}__{name}"
                entry = {"url": url}
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                    await page.wait_for_timeout(1200)  # loader fade
                    audit = await page.evaluate(AUDIT_JS)
                    entry["audit"] = audit
                    shot = f"{SHOT_DIR}/{key}.png"
                    try:
                        await page.screenshot(path=shot, full_page=True)
                        entry["screenshot"] = shot
                    except Exception as e:
                        entry["screenshot_err"] = str(e)
                except Exception as e:
                    entry["error"] = str(e)
                results[key] = entry
                print(f"[{key}] issues={len(entry.get('audit',{}).get('issues',[]))} overflows={len(entry.get('audit',{}).get('overflows',[]))} small={len(entry.get('audit',{}).get('smallTargets',[]))}")
            await ctx.close()
        await browser.close()
    with open("/app/test_reports/mobile_audit_raw.json","w") as f:
        json.dump(results, f, indent=2, default=str)
    print("SAVED /app/test_reports/mobile_audit_raw.json")

asyncio.run(run())
