import asyncio, json
from playwright.async_api import async_playwright

BASE = "" + (__import__("os").environ.get("BASE_URL") or "http://localhost:3000")
DEVICES = ["iPhone 13", "Pixel 7"]

async def check(context, dev):
    page = await context.new_page()
    res = {"device": dev}
    try:
        await page.add_init_script("localStorage.setItem('enare_nome','THAIS VILHENA RODRIGUES'); localStorage.setItem('enare_cpf','072.978.992-67');")
        await page.goto(f"{BASE}/minhas-inscricoes.html", wait_until="domcontentloaded", timeout=40000)
        await page.wait_for_timeout(1800)
        res["overflow"] = await page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 2")
        nameBtn = page.locator('#enareUserName')
        res["name_btn_visible"] = await nameBtn.is_visible()
        res["name_text"] = (await nameBtn.inner_text()).strip()[:30]
        await nameBtn.click(timeout=8000)
        await page.wait_for_timeout(500)
        info = await page.evaluate("""() => {
            const m=document.getElementById('enareUserMenu'); if(!m) return {open:false};
            const r=m.getBoundingClientRect();
            const sair=document.getElementById('enareMenuSair');
            return {open: getComputedStyle(m).display==='block', left:Math.round(r.left), right:Math.round(r.right), vw:window.innerWidth, sairVisible: sair? sair.getClientRects().length>0 : false};
        }""")
        res.update(info)
        res["within_viewport"] = (info.get("left",-1) >= -2 and info.get("right",99999) <= info.get("vw",0)+2)
        res["PASS"] = (res["name_btn_visible"] and info.get("open") and info.get("sairVisible") and res["within_viewport"] and not res["overflow"])
    except Exception as e:
        res["error"]=str(e); res["PASS"]=False
    await page.close()
    return res

async def main():
    out=[]
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for dev in DEVICES:
            ctx=await b.new_context(**p.devices[dev])
            out.append(await check(ctx, dev))
            await ctx.close()
        await b.close()
    print(json.dumps(out, indent=2, ensure_ascii=False))

asyncio.run(main())
