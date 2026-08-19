import asyncio, json
from playwright.async_api import async_playwright
BASE="" + (__import__("os").environ.get("BASE_URL") or "http://localhost:3000")
PAGES=["inscricao-acesso-direto.html","inscricao-multiprofissional.html","inscricao-prerequisito.html"]
async def main():
    out=[]
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(**p.devices["Pixel 7"])
        for pg in PAGES:
            page=await ctx.new_page()
            await page.goto(f"{BASE}/{pg}", wait_until="domcontentloaded", timeout=40000)
            await page.wait_for_timeout(2000)
            info=await page.evaluate("""() => {
                const nb=document.querySelector('button.navbar-toggler');
                const navHasHamb = nb ? !!nb.querySelector('svg path') : false;
                const navVisible = nb ? nb.getClientRects().length>0 : false;
                // accordion toggles: data-bs-toggle=collapse but NOT navbar-toggler
                const accs=[...document.querySelectorAll('[data-bs-toggle=collapse]')].filter(e=>!e.classList.contains('navbar-toggler'));
                const accWithStrayHamb = accs.filter(a => a.innerHTML.indexOf('M3 6h18M3 12h18M3 18h18')>=0).length;
                return {navVisible, navHasHamb, accordion_count:accs.length, accordion_with_stray_hamburger:accWithStrayHamb};
            }""")
            info["page"]=pg
            out.append(info)
            await page.close()
        await b.close()
    print(json.dumps(out, indent=2, ensure_ascii=False))
asyncio.run(main())
