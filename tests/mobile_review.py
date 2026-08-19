"""
Mobile responsive review (iOS + Android) for Donas ENARE site (8 public pages).
Runs via Playwright. Outputs a JSON report under /app/test_reports/mobile_review.json
and screenshots under /app/test_reports/screenshots/.
"""
import asyncio, json, os
from playwright.async_api import async_playwright

BASE = "" + (__import__("os").environ.get("BASE_URL") or "http://localhost:3000")
PAGES = [
    "home.html",
    "cronograma.html",
    "inscricoes.html",
    "minhas-inscricoes.html",
    "inscricao.html",
    "inscricao-acesso-direto.html",
    "inscricao-multiprofissional.html",
    "inscricao-prerequisito.html",
]
OUT_DIR = "/app/test_reports/screenshots"
os.makedirs(OUT_DIR, exist_ok=True)


async def audit_page(context, device_name, page_file, report):
    page = await context.new_page()
    url = f"{BASE}/{page_file}"
    entry = {"page": page_file, "device": device_name, "issues": [], "info": {}}
    console_errors = []
    page.on("pageerror", lambda e: console_errors.append(str(e)))
    page.on("console", lambda m: m.type == "error" and console_errors.append(m.text))
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        await page.wait_for_timeout(1200)
    except Exception as e:
        entry["issues"].append(f"NAV_ERROR: {e}")
        report.append(entry)
        await page.close()
        return

    # 1) Horizontal overflow check
    metrics = await page.evaluate("""() => ({
        docW: document.documentElement.scrollWidth,
        winW: window.innerWidth,
        bodyW: document.body.scrollWidth,
        overflowEls: (() => {
            const arr=[]; const w=window.innerWidth;
            document.querySelectorAll('body *').forEach(el => {
                const r=el.getBoundingClientRect();
                if (r.right > w + 1 && r.width > 0 && r.height>0) {
                    const cs=getComputedStyle(el);
                    if (cs.position==='fixed') return;
                    arr.push({
                        tag: el.tagName.toLowerCase(),
                        cls: (el.className||'').toString().slice(0,80),
                        id: el.id || '',
                        right: Math.round(r.right),
                        width: Math.round(r.width)
                    });
                }
            });
            return arr.slice(0,8);
        })()
    })""")
    entry["info"]["viewport_w"] = metrics["winW"]
    entry["info"]["doc_w"] = metrics["docW"]
    if metrics["docW"] > metrics["winW"] + 1:
        entry["issues"].append(
            f"HORIZONTAL_OVERFLOW: docW={metrics['docW']} > winW={metrics['winW']}; offenders={metrics['overflowEls']}"
        )

    # 2) Sidebar / hamburger check (home + most pages have sidebar)
    sidebar_info = await page.evaluate("""() => {
        const sb = document.querySelector('#sidebar, aside, .sidebar');
        const ham = document.querySelector('#sidebarToggle, [data-testid*="sidebar"], button[aria-label*="menu" i], .hamburger, #menuToggle');
        return {
            hasSidebar: !!sb,
            sidebarVisible: sb ? !!(sb.offsetWidth && sb.offsetHeight) : null,
            sidebarClass: sb ? (sb.className||'').toString().slice(0,120) : null,
            hasHamburger: !!ham,
            hamburgerVisible: ham ? !!(ham.offsetWidth && ham.offsetHeight) : null,
            hamburgerId: ham ? (ham.id || ham.className) : null
        }
    }""")
    entry["info"]["sidebar"] = sidebar_info
    if sidebar_info["hasSidebar"]:
        if sidebar_info["sidebarVisible"] and not sidebar_info["hasHamburger"]:
            entry["issues"].append("SIDEBAR_NOT_COLLAPSED: sidebar visible on mobile and no hamburger toggle found")
        if sidebar_info["hasHamburger"] and not sidebar_info["hamburgerVisible"]:
            entry["issues"].append(f"HAMBURGER_HIDDEN: toggle exists ({sidebar_info['hamburgerId']}) but is not visible")

    # Try to open hamburger if present and visible
    if sidebar_info["hasHamburger"] and sidebar_info["hamburgerVisible"]:
        try:
            await page.click("#sidebarToggle, .hamburger, #menuToggle, button[aria-label*='menu' i]", force=True, timeout=2000)
            await page.wait_for_timeout(400)
            after = await page.evaluate("""() => {
                const sb=document.querySelector('#sidebar, aside, .sidebar');
                if(!sb) return null;
                const r=sb.getBoundingClientRect();
                return {visible: r.width>0 && r.height>0, leftInView: r.left>=-1, width: Math.round(r.width)};
            }""")
            entry["info"]["sidebar_after_toggle"] = after
            if after and not after["visible"]:
                entry["issues"].append("SIDEBAR_TOGGLE_NO_EFFECT: clicking hamburger did not open sidebar")
        except Exception as e:
            entry["info"]["hamburger_click_error"] = str(e)

    # 3) Candidate user menu (#enareUserName -> #enareUserMenu) — esp. minhas-inscricoes
    user_menu = await page.evaluate("""() => {
        const u=document.getElementById('enareUserName');
        const m=document.getElementById('enareUserMenu');
        return {hasName: !!u, hasMenu: !!m,
                nameRect: u? u.getBoundingClientRect(): null,
                menuRect: m? m.getBoundingClientRect(): null};
    }""")
    if user_menu["hasName"]:
        nr = user_menu["nameRect"]
        if nr and (nr["right"] > metrics["winW"] + 1 or nr["left"] < -1):
            entry["issues"].append(f"USER_NAME_CLIPPED: rect={nr}")
        # Try clicking to open menu
        try:
            await page.click("#enareUserName", force=True, timeout=2000)
            await page.wait_for_timeout(400)
            menu_after = await page.evaluate("""() => {
                const m=document.getElementById('enareUserMenu');
                if(!m) return null;
                const r=m.getBoundingClientRect();
                const cs=getComputedStyle(m);
                return {display: cs.display, visibility: cs.visibility,
                        left: Math.round(r.left), right: Math.round(r.right),
                        top: Math.round(r.top), width: Math.round(r.width), height: Math.round(r.height),
                        winW: window.innerWidth};
            }""")
            entry["info"]["user_menu_after"] = menu_after
            if menu_after and menu_after["display"] != "none":
                if menu_after["right"] > menu_after["winW"] + 1:
                    entry["issues"].append(f"USER_MENU_OVERFLOW_RIGHT: right={menu_after['right']} winW={menu_after['winW']}")
                if menu_after["left"] < 0:
                    entry["issues"].append(f"USER_MENU_OVERFLOW_LEFT: left={menu_after['left']}")
                if menu_after["width"] == 0 or menu_after["height"] == 0:
                    entry["issues"].append("USER_MENU_NOT_VISIBLE_AFTER_CLICK")
            elif menu_after and menu_after["display"] == "none":
                entry["issues"].append("USER_MENU_DID_NOT_OPEN")
        except Exception as e:
            entry["info"]["user_menu_click_error"] = str(e)

    # 4) PIX modal for minhas-inscricoes
    if page_file == "minhas-inscricoes.html":
        try:
            # find pay button by text
            btn = await page.query_selector("button:has-text('Pagar'), a:has-text('Pagar')")
            if btn:
                await btn.scroll_into_view_if_needed()
                await btn.click(force=True)
                await page.wait_for_timeout(1500)
                pix = await page.evaluate("""() => {
                    const m=document.querySelector('#pixModal, [id*="pix" i][class*="modal" i], .modal.show, [role="dialog"]');
                    const qr=document.getElementById('pixQrWrap');
                    const code=document.getElementById('pixCode');
                    const winW=window.innerWidth, winH=window.innerHeight;
                    function rect(el){ if(!el) return null; const r=el.getBoundingClientRect(); return {l:Math.round(r.left),r:Math.round(r.right),t:Math.round(r.top),b:Math.round(r.bottom),w:Math.round(r.width),h:Math.round(r.height)};}
                    return {modal: rect(m), qr: rect(qr), code: rect(code), winW, winH,
                            qrHasImg: qr ? !!qr.querySelector('img,canvas,svg') : false,
                            codeText: code ? (code.innerText||code.value||'').slice(0,40) : null};
                }""")
                entry["info"]["pix"] = pix
                if pix["modal"]:
                    if pix["modal"]["r"] > pix["winW"] + 1 or pix["modal"]["l"] < -1:
                        entry["issues"].append(f"PIX_MODAL_OVERFLOW: modal={pix['modal']} winW={pix['winW']}")
                    if pix["modal"]["w"] > pix["winW"]:
                        entry["issues"].append(f"PIX_MODAL_WIDER_THAN_VIEWPORT: w={pix['modal']['w']} winW={pix['winW']}")
                else:
                    entry["issues"].append("PIX_MODAL_NOT_FOUND_AFTER_CLICK")
                if pix["qr"] and not pix["qrHasImg"]:
                    entry["issues"].append("PIX_QR_EMPTY: #pixQrWrap has no img/canvas/svg")
                if pix["code"] and not pix["codeText"]:
                    entry["issues"].append("PIX_CODE_EMPTY")
                # screenshot of modal state
                await page.screenshot(path=f"{OUT_DIR}/{device_name}_{page_file}_pix.png", full_page=False, quality=40, type="jpeg")
            else:
                entry["issues"].append("PIX_PAY_BUTTON_NOT_FOUND")
        except Exception as e:
            entry["info"]["pix_error"] = str(e)
        # close modal if any
        try:
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(200)
        except Exception:
            pass

    # 5) Form controls usability on the 3 inscricao subpages
    if page_file in ("inscricao-acesso-direto.html", "inscricao-multiprofissional.html", "inscricao-prerequisito.html", "inscricao.html"):
        form_info = await page.evaluate("""() => {
            const ws=window.innerWidth;
            function chk(el){const r=el.getBoundingClientRect(); return {w:Math.round(r.width), r:Math.round(r.right), l:Math.round(r.left), overflow:(r.right>ws+1||r.left<-1), tooSmall:(r.width<40||r.height<24)};}
            const selects=[...document.querySelectorAll('select, .choices, .choices__inner')].slice(0,10).map(chk);
            const inputs=[...document.querySelectorAll('input[type=text], input[type=email], input[type=number], input:not([type])')].slice(0,10).map(chk);
            const radios=[...document.querySelectorAll('input[type=radio]')].slice(0,10).map(chk);
            const saveBtn=document.querySelector('button:not([disabled])'); // best-effort
            const allBtns=[...document.querySelectorAll('button')].map(b=>({txt:(b.innerText||'').trim().slice(0,30), disabled:b.disabled, ...chk(b)})).filter(x=>x.txt);
            return {selects, inputs, radios, allBtns: allBtns.slice(0,12), winW: ws};
        }""")
        entry["info"]["form"] = form_info
        bad_selects = [s for s in form_info["selects"] if s["overflow"]]
        bad_inputs = [s for s in form_info["inputs"] if s["overflow"]]
        bad_btns = [b for b in form_info["allBtns"] if b["overflow"]]
        if bad_selects: entry["issues"].append(f"FORM_SELECTS_OVERFLOW: {len(bad_selects)} elements outside viewport e.g. {bad_selects[:2]}")
        if bad_inputs: entry["issues"].append(f"FORM_INPUTS_OVERFLOW: {len(bad_inputs)} elements outside viewport e.g. {bad_inputs[:2]}")
        if bad_btns: entry["issues"].append(f"FORM_BUTTONS_OVERFLOW: {len(bad_btns)} buttons overflow e.g. {bad_btns[:2]}")

    # 6) Tables that overflow
    tbl = await page.evaluate("""() => {
        const ws=window.innerWidth, out=[];
        document.querySelectorAll('table').forEach(t=>{const r=t.getBoundingClientRect(); if(r.width>ws+1) out.push({w:Math.round(r.width), winW:ws});});
        return out;
    }""")
    if tbl: entry["issues"].append(f"TABLE_OVERFLOW: {tbl}")

    # Final screenshot
    try:
        await page.screenshot(path=f"{OUT_DIR}/{device_name}_{page_file}.png", full_page=True, quality=40, type="jpeg")
    except Exception as e:
        entry["info"]["screenshot_error"] = str(e)

    if console_errors:
        entry["info"]["console_errors"] = console_errors[:5]

    report.append(entry)
    await page.close()


async def main():
    report = []
    async with async_playwright() as p:
        devices_to_test = [
            ("iOS_iPhone13", p.devices["iPhone 13"]),
            ("Android_Pixel7", p.devices["Pixel 7"]),
        ]
        browser = await p.chromium.launch(headless=True)
        for dev_name, dev in devices_to_test:
            context = await browser.new_context(**dev)
            for page_file in PAGES:
                print(f"=== {dev_name} :: {page_file} ===")
                await audit_page(context, dev_name, page_file, report)
            await context.close()
        await browser.close()

    out = "/app/test_reports/mobile_review.json"
    with open(out, "w") as f:
        json.dump(report, f, indent=2, default=str)
    # Print compact summary
    for e in report:
        status = "PASS" if not e["issues"] else f"ISSUES({len(e['issues'])})"
        print(f"{e['device']:18s} | {e['page']:40s} | {status}")
        for i in e["issues"]:
            print(f"    - {i[:200]}")
    print(f"\nSaved: {out}")

if __name__ == "__main__":
    asyncio.run(main())
