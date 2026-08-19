import asyncio
from playwright.async_api import async_playwright
BASE="" + (__import__("os").environ.get("BASE_URL") or "http://localhost:3000")
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await b.new_context(); page=await ctx.new_page()
        await page.add_init_script("localStorage.setItem('enare_nome','MARCOS SILVA'); localStorage.setItem('enare_cpf','091.190.551-02'); localStorage.setItem('enare_inscricoes', JSON.stringify([{numero:'268987677904',tipo:'ENARE',residencia:'Anestesiologia',valor:'R$ 330,00',status:'Pagamento Pendente',cpf:'091.190.551-02',nome:'MARCOS SILVA'}]));")
        await page.goto(f"{BASE}/minhas-inscricoes.html", wait_until="domcontentloaded", timeout=40000)
        await page.wait_for_timeout(2500)
        info = await page.evaluate("""() => {
            const btn=document.querySelector('[data-testid="btn-pagar"]');
            if(!btn) return {found:false};
            const card=btn.closest('.card-ins, [class*=card]') || btn.parentElement.parentElement;
            const p=[...card.querySelectorAll('p')].find(x=>/comprovante de inscri/i.test(x.textContent));
            if(!p) return {found:false};
            const btnB=btn.getBoundingClientRect(), pB=p.getBoundingClientRect();
            return {found:true, text:p.textContent.trim(), fontSize:getComputedStyle(p).fontSize, below_buttons: pB.top >= btnB.top};
        }""")
        print(info)
        await b.close()
asyncio.run(main())
