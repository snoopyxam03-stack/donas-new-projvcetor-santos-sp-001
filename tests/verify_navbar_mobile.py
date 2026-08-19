import asyncio, json
from playwright.async_api import async_playwright

BASE = "" + (__import__("os").environ.get("BASE_URL") or "http://localhost:3000")
DEVICES = ["iPhone 13", "Pixel 7"]
PAGES = ["inscricoes.html", "minhas-inscricoes.html", "inscricao-acesso-direto.html"]

async def check(context, dev, pg):
    page = await context.new_page()
    res = {"device": dev, "page": pg}
    try:
        await page.add_init_script("localStorage.setItem('enare_nome','THAIS VILHENA RODRIGUES'); localStorage.setItem('enare_cpf','072.978.992-67');")
        await page.goto(f"{BASE}/{pg}", wait_until="domcontentloaded", timeout=40000)
        await page.wait_for_timeout(1800)
        res["overflow"] = await page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 2")
        tg = page.locator("button.navbar-toggler").first
        res["toggler_visible"] = await tg.is_visible()
        # links visible before
        before = await page.evaluate("""() => { const c=document.querySelector('.navbar-collapse'); if(!c) return 0; return [...c.querySelectorAll('a.nav-link')].filter(a=>a.getClientRects().length>0).length; }""")
        res["navlinks_before"] = before
        if res["toggler_visible"]:
            await tg.click(timeout=6000)
            await page.wait_for_timeout(500)
        after = await page.evaluate("""() => { const c=document.querySelector('.navbar-collapse'); if(!c) return 0; return [...c.querySelectorAll('a.nav-link')].filter(a=>a.getClientRects().length>0).length; }""")
        res["navlinks_after"] = after
        # candidate menu (only minhas-inscricoes)
        if pg == "minhas-inscricoes.html":
            nb = page.locator("#enareUserName")
            res["name_visible_after_expand"] = await nb.is_visible()
            if res["name_visible_after_expand"]:
                await nb.click(timeout=6000)
                await page.wait_for_timeout(400)
                res["sair_visible"] = await page.evaluate("() => { const s=document.getElementById('enareMenuSair'); return s? s.getClientRects().length>0 : false; }")
        res["PASS"] = res["toggler_visible"] and after >= 3 and not res["overflow"] and (pg != "minhas-inscricoes.html" or res.get("sair_visible"))
    except Exception as e:
        res["error"] = str(e); res["PASS"] = False
    await page.close()
    return res

async def main():
    out = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for dev in DEVICES:
            ctx = await b.new_context(**p.devices[dev])
            for pg in PAGES:
                out.append(await check(ctx, dev, pg))
            await ctx.close()
        await b.close()
    print(json.dumps(out, indent=2, ensure_ascii=False))

asyncio.run(main())
