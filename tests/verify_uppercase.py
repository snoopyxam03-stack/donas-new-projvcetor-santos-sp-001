import asyncio, json
from playwright.async_api import async_playwright

BASE = "" + (__import__("os").environ.get("BASE_URL") or "http://localhost:3000")

async def main():
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context()
        page = await ctx.new_page()
        await page.goto(f"{BASE}/inscricao.html", wait_until="domcontentloaded", timeout=40000)
        await page.wait_for_timeout(1500)
        async def typeval(sel, text):
            try:
                el = page.locator(sel).first
                await el.scroll_into_view_if_needed(timeout=4000)
                await el.click(timeout=4000)
                await el.type(text, delay=10)
                await page.wait_for_timeout(150)
                return await el.input_value()
            except Exception as e:
                return f"ERR:{e}"
        out["nome"] = await typeval("#nome", "anthony kevin lima da silva")
        out["nomeMae"] = await typeval("#nomeMae", "maria exemplo da silva")
        out["email"] = await typeval("#email", "Teste.Email@Gmail.com")
        out["senha"] = await typeval("#senha", "MinhaSenha123")
        print(json.dumps(out, indent=2, ensure_ascii=False))
        await b.close()

asyncio.run(main())
