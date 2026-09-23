# -*- coding: utf-8 -*-
"""CDP 驱动秀米编辑器的公共函数"""
import json, time
import cdp

MOD_CTRL = 2

def connect(sub):
    return cdp.connect(sub)

def front(tab):
    try:
        tab.send("Page.bringToFront")
    except Exception as e:
        print("bringToFront fail:", e)

def grant_clipboard(tab, origin="https://xiumi.us"):
    try:
        tab.send("Browser.grantPermissions", origin=origin,
                 permissions=["clipboardReadWrite", "clipboardSanitizedWrite"])
        return "granted"
    except Exception as e:
        return "grant-fail: %s" % e

def write_clipboard(tab, html, text=None):
    if text is None:
        text = html
    js = ("(async () => { try { const it = new ClipboardItem({"
          "'text/html': new Blob([%s], {type:'text/html'}),"
          "'text/plain': new Blob([%s], {type:'text/plain'})});"
          "await navigator.clipboard.write([it]); return 'ok'; }"
          "catch (e) { return 'ERR:' + e.message; } })()"
          % (json.dumps(html), json.dumps(text)))
    return tab.eval(js, await_promise=True)

def key(tab, keyname, code, vk, mods=0):
    for t in ("keyDown", "keyUp"):
        tab.send("Input.dispatchKeyEvent", type=t, modifiers=mods, key=keyname,
                 code=code, windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)

def ctrl(tab, keyname, code, vk):
    key(tab, keyname, code, vk, mods=MOD_CTRL)

def paste(tab, wait=6.0):
    ctrl(tab, "v", "KeyV", 86)
    time.sleep(wait)

def click_xy(tab, x, y):
    for t in ("mousePressed", "mouseReleased"):
        tab.send("Input.dispatchMouseEvent", type=t, x=x, y=y, button="left",
                 clickCount=1, buttons=1 if t == "mousePressed" else 0)
    time.sleep(0.4)

def click_el(tab, selector, idx=0):
    r = tab.eval("(() => { const e = document.querySelectorAll(%s)[%d];"
                 "if(!e) return null; const b = e.getBoundingClientRect();"
                 "return {x: b.x + b.width/2, y: b.y + Math.min(b.height/2, 30)}; })()"
                 % (json.dumps(selector), idx))
    if not r:
        return None
    click_xy(tab, r["x"], r["y"])
    return r

def editor_cells(tab):
    return tab.eval("""JSON.stringify([...document.querySelectorAll('.tn-editing-block .tn-cell-inner, .tn-editing-block .tn-cell')]
      .filter(() => true).map((c,i) => ({i, ce: c.getAttribute('contenteditable'),
        cls: (c.className||'').toString().replace('ng-scope','').trim().slice(0,60),
        len: (c.innerText||'').length})), null, 0)""")

def cell_html(tab, idx):
    return tab.eval("(() => { const c = [...document.querySelectorAll('.tn-cell-text')][%d];"
                    "return c ? c.innerHTML : ''; })()" % idx)
