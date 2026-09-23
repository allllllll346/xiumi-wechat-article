# -*- coding: utf-8 -*-
"""极简 Chrome DevTools Protocol 驱动（只用 requests + websocket-client）"""
import json, base64, time, itertools
import requests
import websocket

PORT = 9222
BASE = f"http://127.0.0.1:{PORT}"


class Tab:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=180, suppress_origin=True)
        self.ids = itertools.count(1)
        self.events = []
        self.msg_id = 0

    def send(self, method, **params):
        self.msg_id = next(self.ids)
        self.ws.send(json.dumps({"id": self.msg_id, "method": method, "params": params}))
        deadline = time.time() + 120
        while time.time() < deadline:
            raw = self.ws.recv()
            msg = json.loads(raw)
            if msg.get("id") == self.msg_id:
                if "error" in msg:
                    raise RuntimeError(f"{method} -> {msg['error']}")
                return msg.get("result", {})
            if "method" in msg:
                self.events.append(msg)
        raise TimeoutError(method)

    def wait_event(self, method, timeout=25):
        for i, e in enumerate(self.events):
            if e.get("method") == method:
                return self.events.pop(i).get("params", {})
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                raw = self.ws.recv()
            except Exception:
                break
            msg = json.loads(raw)
            if msg.get("method") == method:
                return msg.get("params", {})
            if "method" in msg:
                self.events.append(msg)
        return None

    def eval(self, expr, await_promise=False):
        r = self.send("Runtime.evaluate", expression=expr, returnByValue=True,
                      awaitPromise=await_promise, userGesture=True)
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"].get("text") + " | " + str(r["exceptionDetails"].get("exception", {}).get("description", "")))
        return r.get("result", {}).get("value")

    def goto(self, url, wait=3.0):
        self.send("Page.enable")
        self.send("Page.navigate", url=url)
        time.sleep(wait)

    def screenshot(self, path, full=False):
        r = self.send("Page.captureScreenshot", format="png", captureBeyondViewport=full)
        with open(path, "wb") as f:
            f.write(base64.b64decode(r["data"]))
        return path

    def set_file_input(self, node_id, files):
        self.send("DOM.setFileInputFiles", nodeId=node_id, files=files)

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def targets():
    return requests.get(BASE + "/json/list", timeout=10).json()


def new_tab(url="about:blank"):
    try:
        r = requests.put(BASE + f"/json/new?{url}", timeout=15)
    except Exception:
        r = requests.get(BASE + f"/json/new?{url}", timeout=15)
    return r.json()


def connect(url_substr=None, create=None):
    """连接第一个匹配的页面；没有就新建"""
    pages = [t for t in targets() if t.get("type") == "page"]
    if url_substr:
        pages = [t for t in pages if url_substr in t.get("url", "")]
    if not pages:
        if create is None:
            raise RuntimeError("no page target: " + json.dumps([t.get("url") for t in targets()], ensure_ascii=False))
        t = new_tab(create)
        time.sleep(3)
        pages = [t]
    return Tab(pages[0]["webSocketDebuggerUrl"]), pages[0].get("url", "")
