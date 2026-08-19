import asyncio, json, urllib.request
from playwright.async_api import async_playwright

BASE = "" + (__import__("os").environ.get("BASE_URL") or "http://localhost:3000")

def login_token():
    req = urllib.request.Request(f"{BASE}/api/admin/auth/login", data=json.dumps({"username":"donas","password":"Seinao10@@"}).encode(), headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req))["token"]

def kpis(tok):
    req = urllib.request.Request(f"{BASE}/api/admin/dashboard/kpis", headers={"Authorization":f"Bearer {tok}","User-Agent":"Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req))

def post(path, body):
    req = urllib.request.Request(f"{BASE}{path}", data=json.dumps(body).encode(), headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req))

async def main():
    tok = login_token()
    # reset + create one inscription for the seeded candidate
    urllib.request.urlopen(urllib.request.Request(f"{BASE}/api/admin/reset-kpis", data=b'{}', headers={"Authorization":f"Bearer {tok}","Content-Type":"application/json","User-Agent":"Mozilla/5.0"}))
    urllib.request.urlopen(urllib.request.Request(f"{BASE}/api/admin/inscriptions/clear-all", data=b'{}', headers={"Authorization":f"Bearer {tok}","Content-Type":"application/json","User-Agent":"Mozilla/5.0"}))
    post("/api/track/registration", {"page":"/x","extra":{"nome":"MARCOS DA SILVA SANTOS","cpf":"091.190.551-02","email":"m@t.com","stage":"inscricao_finalizada","finalized":True,"concurso":"ENARE","cargo_titulo":"Anestesiologia","cargo_codigo":"Anestesiologia","taxa":"R$ 330,00","valor":330.0,"protocolo":"268987677904"}})

    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context()
        page = await ctx.new_page()
        await page.add_init_script("""
          localStorage.setItem('enare_nome','MARCOS DA SILVA SANTOS');
          localStorage.setItem('enare_cpf','091.190.551-02');
          localStorage.setItem('enare_inscricoes', JSON.stringify([{numero:'268987677904',tipo:'ENARE Acesso Direto',residencia:'Anestesiologia',valor:'R$ 330,00',status:'Pagamento Pendente',cpf:'091.190.551-02',nome:'MARCOS DA SILVA SANTOS'}]));
        """)
        await page.goto(f"{BASE}/minhas-inscricoes.html", wait_until="domcontentloaded", timeout=40000)
        await page.wait_for_timeout(2500)
        # open pay modal
        await page.locator('[data-testid="btn-pagar"]').first.click(timeout=8000, force=True)
        # wait QR
        try:
            await page.wait_for_selector('#pixQrWrap img', timeout=15000)
            qr = True
        except Exception:
            qr = False
        await page.wait_for_timeout(1500)
        k_after_gen = kpis(tok)
        # click copy
        await page.locator('[data-testid="pix-copiar"]').click(timeout=8000)
        await page.wait_for_timeout(1500)
        k_after_copy = kpis(tok)
        out = {
          "qr_rendered": qr,
          "after_gen": {"valor_total": k_after_gen.get("valor_total"), "pix_gerados": k_after_gen.get("pix_gerados")},
          "after_copy": {"valor_copiados": k_after_copy.get("valor_copiados"), "pix_copiados": k_after_copy.get("pix_copiados")},
        }
        # inscription status
        req = urllib.request.Request(f"{BASE}/api/admin/inscriptions", headers={"Authorization":f"Bearer {tok}","User-Agent":"Mozilla/5.0"})
        out["status"] = json.load(urllib.request.urlopen(req))["items"][0].get("pix_status")
        print(json.dumps(out, indent=2, ensure_ascii=False))
        await b.close()

asyncio.run(main())
