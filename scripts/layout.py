# -*- coding: utf-8 -*-
"""秀米图文（paper）排版操作台 —— 纯 CDP，不需要 Playwright。

落库铁律：秀米保存的是它自己的模型；只有「先真实点击激活目标格，再用
document.execCommand('insertHTML' | 'delete')」才会写进模型。
任何直接 DOM 改动（remove / insertAdjacentHTML / 改 style）保存后都会还原。

子命令：
  state              打印结构（组件/卡片/缎带/图片/尾串）
  activate N         真实点击激活第 N 个正文格
  insert             在目标格内插入 HTML（默认自动先激活该格）
  delete-comp N      删除第 N 个顶层组件
  zero-padding N     把第 N 个组件 wrapper 的上下 padding 归零（收敛跨组件空隙）
  save               点「保存」
  reload             重载编辑器并等就绪
  verify             save + reload + state（每次改动后必跑）
  shot               截图（自查用，不要拿截图去问用户）
"""
import argparse, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cdp, xm

CELL = ".tn-page-vessel .tn-cell-text"
CARD = "border:1px solid #f0e0c0"
SPACER = '<p style="height: 12px; font-size: 12px; line-height: 1px;">&nbsp;</p>'

STATE_JS = """(() => {
  const cs = [].slice.call(document.querySelectorAll('%s'));
  const cardSel = '%s';
  const cardsOf = function (el) {
    return [].slice.call(el.querySelectorAll('div')).filter(function (d) {
      const s = d.getAttribute('style') || '';
      return s.indexOf(cardSel) >= 0 || s.indexOf('border:1px solid #c7000b') >= 0;
    });
  };
  return JSON.stringify(cs.map(function (c, i) {
    const b = c.getBoundingClientRect();
    return {
      i: i,
      h: Math.round(b.height),
      图: c.querySelectorAll('img').length,
      缎带: c.querySelectorAll('span[style*="border-top: 13px"]').length / 2,
      卡: cardsOf(c).map(function (d) {
        const t = (d.innerText || '').replace(/\\s+/g, ' ').trim();
        return (t ? t.slice(0, 8) : '空') + '[' + d.querySelectorAll('img').length + ']';
      }),
      尾: (c.innerText || '').replace(/\\s+/g, ' ').trim().slice(-16)
    };
  }), null, 1);
})()""" % (CELL, CARD)

COMP_JS = """(() => {
  const cell = document.querySelector('%s');
  let box = cell;
  while (box && !box.classList.contains('tn-group-box-wrapper')) box = box.parentElement;
  return JSON.stringify([].slice.call(box.children).map(function (c, i) {
    const b = c.getBoundingClientRect();
    return {i: i, h: Math.round(b.height), 图: c.querySelectorAll('img').length,
      头: (c.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 16)};
  }));
})()""" % CELL


def connect(args):
    cdp.PORT = args.port
    cdp.BASE = "http://127.0.0.1:%d" % args.port
    draft = args.draft or os.environ.get("XIUMI_DRAFT", "")
    if not draft:
        raise SystemExit("需要 --draft <草稿ID>（或设环境变量 XIUMI_DRAFT）")
    t, url = cdp.connect("paper/for/%s" % draft)
    t.send("Emulation.setDeviceMetricsOverride", width=1600, height=950,
           deviceScaleFactor=1, mobile=False)
    return t


def wait_ready(t, timeout=90):
    js = "(() => document.querySelectorAll('%s').length >= 2)()" % CELL
    end = time.time() + timeout
    while time.time() < end:
        if t.eval(js):
            time.sleep(2.5)
            return True
        time.sleep(2)
    return False


def click_xy(t, x, y, wait=1.3):
    x, y = int(x), int(y)
    t.send("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
    time.sleep(0.3)
    t.send("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, button="left", clickCount=1)
    time.sleep(0.1)
    t.send("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left", clickCount=1)
    time.sleep(wait)


def press(t, key, code, vk, text=None):
    p = dict(type="keyDown" if text else "rawKeyDown", key=key, code=code,
             windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)
    if text:
        p.update(text=text, unmodifiedText=text)
    t.send("Input.dispatchKeyEvent", **p)
    t.send("Input.dispatchKeyEvent", type="keyUp", key=key, code=code,
           windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)


def cell_pos(t, i):
    """把第 i 个格滚到视口内，返回 (x, y) —— 用格内第一段有字的文字，避免点到图片。"""
    js = """(() => {
      const c = [].slice.call(document.querySelectorAll('%s'))[%d];
      if (!c) return null;
      const ps = [].slice.call(c.querySelectorAll('p')).filter(function (p) {
        return (p.innerText || '').replace(/[\\u200b\\s]/g, '').length > 0 && !p.querySelector('img');
      });
      const tgt = ps[0] || c;
      tgt.scrollIntoView({block: 'center'});
      return 'ok';
    })()""" % (CELL, i)
    if t.eval(js) != "ok":
        return None
    time.sleep(1.3)
    p = t.eval("""(() => {
      const c = [].slice.call(document.querySelectorAll('%s'))[%d];
      const ps = [].slice.call(c.querySelectorAll('p')).filter(function (p) {
        return (p.innerText || '').replace(/[\\u200b\\s]/g, '').length > 0 && !p.querySelector('img');
      });
      const tgt = ps[0] || c;
      const b = tgt.getBoundingClientRect();
      return JSON.stringify({x: Math.round(b.x + 26), y: Math.round(b.y + b.height / 2)});
    })()""" % (CELL, i))
    if not p:
        return None
    d = json.loads(p)
    return d["x"], d["y"]


def activate(t, i):
    pos = cell_pos(t, i)
    if not pos:
        return "NO CELL %d" % i
    click_xy(t, pos[0], pos[1], 1.5)
    return t.eval("(() => String(document.activeElement.className || '').slice(0, 40))()")


def cmd_state(t, args):
    print(t.eval(STATE_JS))
    print("组件:", t.eval(COMP_JS))


def cmd_activate(t, args):
    print("activeElement:", activate(t, args.index))


def build_target_js(cell, card_kw, text_kw, which):
    """返回选择目标元素的 JS 片段（在指定格内）。"""
    if text_kw:
        return """(() => { const c = [].slice.call(document.querySelectorAll('%s'))[%d];
          return [].slice.call(c.querySelectorAll('p,div,span')).filter(function (e) {
            return (e.innerText || '').indexOf(%s) >= 0; })[0] || null; })()""" % (
            CELL, cell, json.dumps(text_kw))
    if card_kw:
        pick = {"self": "card", "last": "card.lastElementChild", "first": "card.firstElementChild"}[which]
        return """(() => { const c = [].slice.call(document.querySelectorAll('%s'))[%d];
          const cards = [].slice.call(c.querySelectorAll('div')).filter(function (d) {
            const s = d.getAttribute('style') || '';
            return s.indexOf('%s') >= 0 || s.indexOf('border:1px solid #c7000b') >= 0; });
          const card = cards.filter(function (d) { return (d.innerText || '').indexOf(%s) >= 0; })[0] || null;
          return card ? %s : null; })()""" % (CELL, cell, CARD, json.dumps(card_kw), pick)
    # 无定位参数：取该格最后一个空段，没有就用格的最后一个元素
    return """(() => { const c = [].slice.call(document.querySelectorAll('%s'))[%d];
      const ps = [].slice.call(c.querySelectorAll('p'));
      const blanks = ps.filter(function (p) { return !(p.innerText || '').replace(/[\\u200b\\s]/g, '').length && !p.querySelector('img'); });
      return blanks[blanks.length - 1] || c.lastElementChild; })()""" % (CELL, cell)


def cmd_insert(t, args):
    html = open(args.html_file, encoding="utf-8").read() if args.html_file else (args.html or "")
    if not html.strip():
        raise SystemExit("需要 --html-file 或 --html（不要用空内容，空插入会触发整篇重建）")
    if not args.no_activate:
        activate(t, args.cell)
    find = build_target_js(args.cell, args.card, args.text, args.which)
    js = """(() => {
      const tgt = %s;
      if (!tgt) return 'NO TARGET';
      const rg = document.createRange(); rg.selectNode(tgt);
      const s = window.getSelection(); s.removeAllRanges(); s.addRange(rg);
      const ok = document.execCommand('insertHTML', false, %s);
      return 'insertHTML=' + ok + ' | 插入后该格图数=' + [].slice.call(document.querySelectorAll('%s'))[%d].querySelectorAll('img').length;
    })()""" % (find, json.dumps(html), CELL, args.cell)
    print(t.eval(js))
    time.sleep(2.5)
    print("提示：改动后必须跑 verify 确认已落库")


def cmd_delete_comp(t, args):
    i = args.index
    for attempt in range(3):
        t.eval("""(() => {
          const cell = document.querySelector('%s');
          let box = cell;
          while (box && !box.classList.contains('tn-group-box-wrapper')) box = box.parentElement;
          if (box.children[%d]) box.children[%d].scrollIntoView({block: 'center'});
          return 1; })()""" % (CELL, i, i))
        time.sleep(1.3)
        p = t.eval("""(() => {
          const cell = document.querySelector('%s');
          let box = cell;
          while (box && !box.classList.contains('tn-group-box-wrapper')) box = box.parentElement;
          const c = box.children[%d];
          if (!c) return null;
          const b = c.getBoundingClientRect();
          return JSON.stringify({x: Math.round(b.x + b.width / 2), y: Math.round(b.y + Math.min(b.height, 300) / 2)});
        })()""" % (CELL, i))
        if not p:
            print("组件 %d 不存在" % i)
            return
        d = json.loads(p)
        click_xy(t, d["x"], d["y"], 1.5)
        r = t.eval("""(() => {
          const bs = [].slice.call(document.querySelectorAll('.dc-cp-delete button')).filter(function (b) {
            const r = b.getBoundingClientRect();
            return r.width > 6 && r.height > 6 && r.y > 0 && r.y < 940; });
          if (!bs.length) return 'NO BTN';
          const b = bs[bs.length - 1].getBoundingClientRect();
          return JSON.stringify({x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2)});
        })()""")
        if r == "NO BTN":
            print("第%d次：没找到可见的组件删除按钮，重试" % (attempt + 1))
            continue
        b = json.loads(r)
        click_xy(t, b["x"], b["y"], 2.0)
        print("已点组件删除；剩余组件数:", t.eval("""(() => {
          const cell = document.querySelector('%s');
          let box = cell;
          while (box && !box.classList.contains('tn-group-box-wrapper')) box = box.parentElement;
          return box.children.length; })()""" % CELL))
        return
    print("删除失败，请人工检查")


def cmd_zero_padding(t, args):
    activate(t, args.index)
    r = t.eval("""(() => {
      const c = [].slice.call(document.querySelectorAll('%s'))[%d];
      const w = c.firstElementChild;
      if (%s) w.style.paddingTop = '0px';
      if (%s) w.style.paddingBottom = '0px';
      return w.style.padding;
    })()""" % (CELL, args.index, "true" if args.top else "false", "true" if args.bottom else "false"))
    print("wrapper padding ->", r)
    press(t, " ", "Space", 32, text=" ")
    time.sleep(0.3)
    press(t, "Backspace", "Backspace", 8)
    time.sleep(1.5)
    print("提示：跑 verify 确认已落库")


def cmd_save(t, args):
    r = t.eval("""(() => {
      const el = [].slice.call(document.querySelectorAll('.tn-op-btn-group button, .tn-op-btn-group a, .tn-op-btn-group li'))
        .filter(function (e) { return (e.innerText || '').trim() === '保存'; })[0];
      if (!el) return null;
      const b = el.getBoundingClientRect();
      return JSON.stringify({x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2)});
    })()""")
    if not r:
        print("没找到保存按钮")
        return
    d = json.loads(r)
    click_xy(t, d["x"], d["y"], 2.0)
    print("已点保存，等待落库…")
    time.sleep(13)


def cmd_reload(t, args):
    t.send("Page.enable")
    t.eval("location.reload()")
    time.sleep(15)
    print("就绪:", wait_ready(t))


def cmd_verify(t, args):
    cmd_save(t, args)
    cmd_reload(t, args)
    cmd_state(t, args)


def cmd_shot(t, args):
    t.screenshot(args.out)
    print("已保存", args.out)


def main():
    ap = argparse.ArgumentParser(description="秀米图文排版操作台（CDP）")
    ap.add_argument("--draft", default="", help="草稿 ID，例如 123456789")
    ap.add_argument("--port", type=int, default=9222)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("state").set_defaults(fn=cmd_state)
    p = sub.add_parser("activate"); p.add_argument("index", type=int); p.set_defaults(fn=cmd_activate)

    p = sub.add_parser("insert")
    p.add_argument("--cell", type=int, required=True)
    p.add_argument("--card", default="", help="按卡片内文字定位（如 03）")
    p.add_argument("--text", default="", help="按元素文字定位")
    p.add_argument("--which", default="last", choices=["self", "last", "first"])
    p.add_argument("--html-file", default="")
    p.add_argument("--html", default="")
    p.add_argument("--no-activate", action="store_true")
    p.set_defaults(fn=cmd_insert)

    p = sub.add_parser("delete-comp"); p.add_argument("index", type=int); p.set_defaults(fn=cmd_delete_comp)

    p = sub.add_parser("zero-padding"); p.add_argument("index", type=int)
    p.add_argument("--top", action="store_true"); p.add_argument("--bottom", action="store_true")
    p.set_defaults(fn=cmd_zero_padding)

    sub.add_parser("save").set_defaults(fn=cmd_save)
    sub.add_parser("reload").set_defaults(fn=cmd_reload)
    sub.add_parser("verify").set_defaults(fn=cmd_verify)
    p = sub.add_parser("shot"); p.add_argument("--out", required=True); p.set_defaults(fn=cmd_shot)

    args = ap.parse_args()
    if args.cmd == "zero-padding" and not args.top and not args.bottom:
        args.top = args.bottom = True
    t = connect(args)
    try:
        args.fn(t, args)
    finally:
        t.close()


if __name__ == "__main__":
    main()