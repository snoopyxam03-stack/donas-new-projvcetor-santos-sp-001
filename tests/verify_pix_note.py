import asyncio
from playwright.async_api import async_playwright
BASE="" + (__import__("os").environ.get("BASE_URL") or "http://localhost:3000")
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await b.new_context(); page=await ctx.new_page()
        await page.add_init_script("localStorage.setItem('enare_nome','MARCOS SILVA'); localStorage.setItem('enare_cpf','091.190.551-02'); localStorage.setItem('enare_inscricoes', JSON.stringify([{numero:'268987677904',tipo:'ENARE',residencia:'Anestesiologia',valor:'R$ 330,00',status:'Pagamento Pendente',cpf:'091.190.551-02',nome:'MARCOS SILVA'}]));")
        await page.goto(f"{BASE}/minhas-inscricoes.html", wait_until="domcontentloaded", timeout=40000)
        await page.wait_for_timeout(2000)
        await page.locator('[data-testid="btn-pagar"]').first.click(timeout=8000, force=True)
        await page.wait_for_timeout(2500)
        note = await page.evaluate("() => { const ps=[...document.querySelectorAll('p')]; const n=ps.find(p=>/comprovante de inscri/i.test(p.textContent)); return n? n.textContent.trim() : 'NOT FOUND'; }")
        fs = await page.evaluate("() => { const ps=[...document.querySelectorAll('p')]; const n=ps.find(p=>/comprovante de inscri/i.test(p.textContent)); return n? getComputedStyle(n).fontSize : ''; }")
        print("NOTE:", note)
        print("FONT-SIZE:", fs)
        await b.close()
asyncio.run(main())
