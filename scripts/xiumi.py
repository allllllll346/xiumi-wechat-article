# -*- coding: utf-8 -*-
"""秀米排版助手：Playwright 经 CDP 接管本机已登录的 Chrome。

用法示例见 SKILL.md。所有写操作前先 status 记录状态，出错可回退。
"""
import argparse, base64, json, os, subprocess, sys, time, urllib.request

from playwright.sync_api import sync_playwright

CHROME_DEFAULT = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 9222
CANVAS = '[contenteditable="true"]'


def cdp_alive(port=PORT):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=3).read()
        return True
    except Exception:
        return False


def launch_chrome(profile_dir, url="https://xiumi.us/#/", port=PORT, chrome=CHROME_DEFAULT):
    subprocess.Popen([chrome, f"--remote-debugging-port={port}", "--remote-allow-origins=*",
                      f"--user-data-dir={profile_dir}", "--no-first-run", "--no-default-browser-check", url])
    for _ in range(25):
        time.sleep(1)
        if cdp_alive(port):
            return True
    return False


class Xiumi:
    def __init__(self, port=PORT):
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        self.ctx = self.browser.contexts[0]

    def close(self):
        try:
            self.browser.close()
        finally:
            self._pw.stop()

    def page(self, substr="studio/v5"):
        cands = [p for p in self.ctx.pages if substr in p.url]
        for p in cands:                       # 优先真正的图文编辑器（URL 带 paper）
            if "paper" in p.url:
                return p
        if cands:
            return cands[0]
        raise RuntimeError(f"no tab matching {substr!r}; open tabs: {[p.url[:60] for p in self.ctx.pages]}")

    def close_junk_tabs(self, keep=("xiumi.us",)):
        for p in list(self.ctx.pages):
            if not any(k in p.url for k in keep):
                p.close()

    # ---------- 打开 / 登录 ----------
    def open_home(self):
        return self.ctx.new_page() if False else self.ctx.pages[0]

    def open_new_paper(self, page=None):
        """在首页点'新建一个图文'，返回编辑器 page。"""
        page = page or self.ctx.new_page()
        page.goto("https://xiumi.us/#/", wait_until="load")
        page.wait_for_timeout(4000)
        page.locator("text=新建一个图文").last.click()
        for _ in range(20):
            page.wait_for_timeout(1500)
            for p in self.ctx.pages:
                if "studio/v5" in p.url and "paper" in p.url:
                    p.wait_for_timeout(3000)
                    return p
        raise RuntimeError("editor tab did not appear")

    def login(self, user, password):
        page = self.ctx.new_page()
        page.goto("https://xiumi.us/#/", wait_until="load")
        page.wait_for_timeout(3000)
        if page.locator("text=退出登录").count() or page.locator("text=账号设置").count():
            page.close()
            return "already-logged-in"
        page.locator("a.usr-sign-in, text=登录").first.click()
        page.wait_for_timeout(4000)
        page.fill('input[type="text"]', user)
        page.fill('input[type="password"]', password)
        cb = page.locator('input[type="checkbox"]').first
        if not cb.is_checked():
            cb.click()
        box = page.locator("text=登录").last.bounding_box()
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.wait_for_timeout(8000)
        page.close()
        return "ok"

    # ---------- 状态 ----------
    def status(self):
        page = self.page()
        return page.evaluate("""() => {
          const cells = [...document.querySelectorAll('[contenteditable="true"]')]
              .map((el,i) => ({i, len: (el.innerText||'').replace(/\\s+/g,' ').length}));
          const all = document.body.innerText.replace(/\\s+/g,' ');
          return {url: location.href, cells,
                  markers: (all.match(/▲IMG\\d▲/g)||[]),
                  title: (document.querySelector('input[placeholder*="标题"]')||{}).value,
                  format: (all.match(/基础格式[^默]*默认图/)||[''])[0],
                  images: [...new Set([...document.querySelectorAll('img')].map(i=>i.src).filter(s=>/xmi\\/ua/.test(s)))].length};
        }""")

    # ---------- 标题 / 基础格式 ----------
    def set_title(self, text):
        page = self.page()
        page.eval_on_selector('input[placeholder*="标题"]',
                              """(el, v) => { const s = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el),'value').set;
                                 s.call(el, v);
                                 el.dispatchEvent(new Event('input',{bubbles:true}));
                                 el.dispatchEvent(new Event('change',{bubbles:true}));
                                 el.dispatchEvent(new Event('blur',{bubbles:true})); }""", text)
        return text

    def set_format(self, size="15", line="1.75", spacing="1", para="10", margin="20"):
        """点画布下方'基础格式'再设参数。"""
        page = self.page()
        page.locator("text=基础格式").last.click()
        page.wait_for_timeout(1500)
        ok = page.evaluate("""(vals) => {
          const setVal = (el, v) => { const s = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el),'value').set;
            s.call(el, v); el.dispatchEvent(new Event('input',{bubbles:true}));
            el.dispatchEvent(new Event('change',{bubbles:true})); el.dispatchEvent(new Event('blur',{bubbles:true})); };
          const vis = el => { const r = el.getBoundingClientRect(); return r.width>0 && r.height>0 && r.top>100; };
          const ins = [...document.querySelectorAll('input[type=text]')].filter(vis)
                        .filter(el => !(el.placeholder||'').includes('标题'));
          const size = ins.find(el => ['12','14','15','16','17','18'].includes(el.value));
          const line = ins.find(el => /^\\d\\.\\d+$/.test(el.value));
          const zeros = ins.filter(el => el.value === '0' || el.value === '');
          if (size) setVal(size, vals[0]);
          if (line) setVal(line, vals[1]);
          if (zeros[0]) setVal(zeros[0], vals[2]);
          if (zeros[1]) setVal(zeros[1], vals[3]);
          if (zeros[2]) setVal(zeros[2], vals[4]);
          return [size && size.value, line && line.value];
        }""", [size, line, spacing, para, margin])
        page.wait_for_timeout(1200)
        return ok

    # ---------- 粘贴富文本 ----------
    def clipboard_copy(self, html_path):
        """用临时页把富文本写进系统剪贴板。"""
        page = self.ctx.new_page()
        page.goto("file:///" + os.path.abspath(html_path).replace("\\", "/"))
        page.wait_for_timeout(2500)
        ok = page.evaluate("""() => { const r = document.createRange(); r.selectNodeContents(document.body);
            const s = window.getSelection(); s.removeAllRanges(); s.addRange(r); return document.execCommand('copy'); }""")
        page.close()
        return ok

    def paste_into_canvas(self, html_path, position="append"):
        """position='empty-cell' 用于空画布；'after-last' 追加。"""
        self.clipboard_copy(html_path)
        page = self.page()
        cell = page.locator(CANVAS).first
        cell.scroll_into_view_if_needed()
        box = cell.bounding_box()
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.wait_for_timeout(500)
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)  # 进编辑态
        page.wait_for_timeout(800)
        page.keyboard.press("Control+A")
        page.wait_for_timeout(400)
        page.keyboard.press("Control+V")
        page.wait_for_timeout(8000)
        return self.status()

    # ---------- 图片 ----------
    def upload_images(self, files, page=None):
        """走秀米上传控件：先点'上传'触发文件选择框，再提交文件。"""
        page = page or self.page()
        try:
            with page.expect_file_chooser(timeout=15000) as fc:
                page.locator("text=上传").first.click()
            fc.value.set_files(files)
            page.wait_for_timeout(15000)
            return "chooser"
        except Exception as e:
            return f"chooser-failed: {type(e).__name__}"

    def insert_from_gallery(self, nth=0, page=None):
        page = page or self.page()
        page.locator(".tn-image-gallery img, img").nth(nth).click()
        page.wait_for_timeout(2000)
        return self.status()

    def delete_selected(self, page=None):
        page = page or self.page()
        page.keyboard.press("Delete")
        page.wait_for_timeout(1500)
        return self.status()

    def save(self, page=None):
        page = page or self.page()
        page.locator("text=保存").first.click()
        page.wait_for_timeout(3000)
        return self.status()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "login", "paste", "format", "upload", "save", "new"])
    ap.add_argument("--html"); ap.add_argument("--title")
    ap.add_argument("--user"); ap.add_argument("--files", nargs="*")
    ap.add_argument("--size", default="15"); ap.add_argument("--line", default="1.75")
    ap.add_argument("--spacing", default="1"); ap.add_argument("--para", default="10"); ap.add_argument("--margin", default="20")
    ap.add_argument("--profile", default=".xiumi-chrome-profile")
    a = ap.parse_args()

    if not cdp_alive():
        if not launch_chrome(os.path.abspath(a.profile)):
            sys.exit("无法启动带调试端口的 Chrome")

    x = Xiumi()
    try:
        if a.cmd == "status":
            print(json.dumps(x.status(), ensure_ascii=False, indent=1))
        elif a.cmd == "login":
            print(x.login(a.user, os.environ["XIUMI_PW"]))
        elif a.cmd == "new":
            p = x.open_new_paper(); print(json.dumps(x.status(), ensure_ascii=False))
        elif a.cmd == "format":
            print(x.set_format(a.size, a.line, a.spacing, a.para, a.margin))
        elif a.cmd == "paste":
            if a.title:
                x.set_title(a.title)
            print(json.dumps(x.paste_into_canvas(a.html), ensure_ascii=False, indent=1))
        elif a.cmd == "upload":
            print(x.upload_images(a.files))
        elif a.cmd == "save":
            print(json.dumps(x.save(), ensure_ascii=False, indent=1))
    finally:
        x.close()


if __name__ == "__main__":
    main()
