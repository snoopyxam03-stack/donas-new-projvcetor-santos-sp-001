import asyncio, json
from playwright.async_api import async_playwright

BASE = "" + (__import__("os").environ.get("BASE_URL") or "http://localhost:3000")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context()
        page = await ctx.new_page()
        await page.goto(f"{BASE}/donaspainel/", wait_until="domcontentloaded", timeout=40000)
        await page.wait_for_timeout(2000)
        # login
        await page.locator('input').nth(0).fill('donas')
        await page.locator('input').nth(1).fill('Seinao10@@')
        await page.click('button:has-text("Entrar")')
        await page.wait_for_timeout(3000)
        # read realtime feed text
        txt = await page.evaluate("""() => {
            const el = [...document.querySelectorAll('*')].find(n => /Atividade em tempo real/i.test(n.textContent) && n.children.length < 40);
            return document.body.innerText;
        }""")
        found = 'Inscrição realizada' in txt and 'MARCOS DA SILVA SANTOS' in txt
        print(json.dumps({"feed_has_inscricao_realizada_with_name": found,
                          "snippet": [l for l in txt.split('\n') if 'MARCOS' in l or 'Inscrição realizada' in l][:5]}, ensure_ascii=False, indent=2))
        await b.close()

asyncio.run(main())
