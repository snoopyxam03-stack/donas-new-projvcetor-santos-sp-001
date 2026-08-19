import asyncio
from playwright.async_api import async_playwright
BASE="" + (__import__("os").environ.get("BASE_URL") or "http://localhost:3000")
PAGES=["inscricoes.html","minhas-inscricoes.html"]
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
                const tg=document.querySelector('button.navbar-toggler');
                if(!tg) return {found:false};
                const hasSvg=!!tg.querySelector('svg path');
                const cs=getComputedStyle(tg);
                return {found:true, visible: tg.getClientRects().length>0, hasHamburgerSvg:hasSvg, border:cs.borderStyle};
            }""")
            # click & check menu opens
            try:
                await page.locator('button.navbar-toggler').first.click(timeout=6000)
                await page.wait_for_timeout(400)
                opened=await page.evaluate("() => { const c=document.querySelector('.navbar-collapse'); return c? [...c.querySelectorAll('a.nav-link')].filter(a=>a.getClientRects().length>0).length : 0; }")
            except Exception as e:
                opened=f"ERR:{e}"
            info["nav_links_after_click"]=opened
            info["page"]=pg
            out.append(info)
            await page.close()
        await b.close()
    import json; print(json.dumps(out, indent=2, ensure_ascii=False))
asyncio.run(main())
