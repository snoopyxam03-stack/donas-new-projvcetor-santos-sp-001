import asyncio, json
from playwright.async_api import async_playwright

BASE = "" + (__import__("os").environ.get("BASE_URL") or "http://localhost:3000")
PAGES = ["home.html", "cronograma.html"]
DEVICES = ["iPhone 13", "Pixel 7"]

async def check(context, dev, pg):
    page = await context.new_page()
    res = {"page": pg, "device": dev}
    try:
        await page.goto(f"{BASE}/{pg}", wait_until="domcontentloaded", timeout=40000)
        await page.wait_for_timeout(1500)
        # horizontal overflow?
        res["overflow"] = await page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 2")
        btn = page.locator('button[aria-label="Abrir menu de navegação"]')
        res["btn_visible"] = await btn.is_visible()
        # aside hidden before
        aside = page.locator('aside').first
        box_before = await aside.bounding_box()
        res["aside_x_before"] = round(box_before["x"],1) if box_before else None
        # click menu
        await btn.click(timeout=8000)
        await page.wait_for_timeout(600)
        box_after = await aside.bounding_box()
        res["aside_x_after"] = round(box_after["x"],1) if box_after else None
        res["aside_w_after"] = round(box_after["width"],1) if box_after else None
        # nav links visible & count
        links = await page.evaluate("""() => { const a=document.querySelector('aside'); if(!a) return 0; return [...a.querySelectorAll('a')].filter(x=>x.getClientRects().length>0).length; }""")
        res["nav_links_visible"] = links
        # open => x should be ~0 ; closed before => x negative (off-canvas)
        res["PASS"] = (res["btn_visible"] and res["aside_x_after"] is not None and res["aside_x_after"] > -5 and res["aside_x_after"] < 5 and links >= 4 and not res["overflow"])
    except Exception as e:
        res["error"] = str(e)
        res["PASS"] = False
    await page.close()
    return res

async def main():
    out = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for dev in DEVICES:
            context = await browser.new_context(**p.devices[dev])
            for pg in PAGES:
                out.append(await check(context, dev, pg))
            await context.close()
        await browser.close()
    print(json.dumps(out, indent=2, ensure_ascii=False))

asyncio.run(main())
