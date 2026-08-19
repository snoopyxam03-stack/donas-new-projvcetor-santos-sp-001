import asyncio
from playwright.async_api import async_playwright
BASE="" + (__import__("os").environ.get("BASE_URL") or "http://localhost:3000")
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        # mobile
        m=await b.new_context(**p.devices["iPhone 13"]); pm=await m.new_page()
        await pm.goto(f"{BASE}/home.html", wait_until="domcontentloaded", timeout=40000); await pm.wait_for_timeout(1500)
        mob=await pm.evaluate("() => { const e=document.querySelector('[data-slot=popover-trigger]'); return e? e.getClientRects().length>0 : 'NF'; }")
        # desktop
        dctx=await b.new_context(viewport={"width":1366,"height":768}); pd=await dctx.new_page()
        await pd.goto(f"{BASE}/home.html", wait_until="domcontentloaded", timeout=40000); await pd.wait_for_timeout(1500)
        desk=await pd.evaluate("() => { const e=document.querySelector('[data-slot=popover-trigger]'); return e? e.getClientRects().length>0 : 'NF'; }")
        print({"mobile_visible": mob, "desktop_visible": desk})
        await b.close()
asyncio.run(main())
