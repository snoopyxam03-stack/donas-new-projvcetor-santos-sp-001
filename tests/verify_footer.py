import asyncio
from playwright.async_api import async_playwright
BASE="" + (__import__("os").environ.get("BASE_URL") or "http://localhost:3000")
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(**p.devices["Pixel 7"]); page=await ctx.new_page()
        await page.goto(f"{BASE}/inscricoes.html", wait_until="domcontentloaded", timeout=40000)
        await page.wait_for_timeout(2000)
        info=await page.evaluate("""() => {
            const f=document.getElementById('footerDiv');
            const pos=getComputedStyle(f).position;
            const fr=f.getBoundingClientRect();
            // any card overlapping footer's rect while footer was fixed? check cards bottom vs footer
            const cards=[...document.querySelectorAll('.card, [class*=card]')];
            return {position:pos, footer_top:Math.round(fr.top), footer_text:f.textContent.trim().slice(0,30), doc_h:document.documentElement.scrollHeight, win_h:window.innerHeight};
        }""")
        print(info)
        await b.close()
asyncio.run(main())
