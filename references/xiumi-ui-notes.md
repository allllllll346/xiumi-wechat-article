# 秀米编辑器实测笔记

## 环境与连接

- 专用 Chrome（Cookie 长期有效，人工登录一次即可）：
  `chrome.exe --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=<专用目录> https://xiumi.us/`
- 连接用 `scripts/cdp.py`（`requests` + `websocket-client`，纯 CDP），配合 `scripts/layout.py`；**不需要 Playwright，沙箱内可直接跑**。
- 编辑器地址 `https://xiumi.us/studio/v5#/paper/for/<草稿ID>/cube/0`；预览 `https://v.xiumius.cn/board/v5/<短码>/<草稿ID>`（会 302 到 `c.xiumius.cn`）。
- 需要 Playwright 的只有老路径 `scripts/xiumi.py`（登录、图库上传），那一步在沙箱内会 PermissionError，需提权。

## 选择器速查

| 用途 | 选择器 / 做法 |
| --- | --- |
| 正文格 | `.tn-page-vessel .tn-cell-text`（**必须限定 `.tn-page-vessel`**：模板面板里也有 `.tn-cell-text`，不限定会把模板算进来） |
| 顶层组件 | 正文格所属 `.tn-group-box-wrapper` 的子元素（类名 `tn-comp-top-level`） |
| 卡片框 | `div[style*="border:1px solid #f0e0c0"]`；口号/标题卡是 `border:1px solid #c7000b` |
| 缎带标题 | `span[style*="border-top: 13px"]`，每个标题 2 个（左右三角），一段标题=2 |
| 组件工具条-删除 | `.dc-cp-delete button`。文档里有多个同名元素，**只取 rect 可见的那个**（隐藏 depot 里的 rect 为 0） |
| 保存按钮 | `.tn-op-btn-group` 里 `innerText === '保存'` 的元素（约 x=958,y=26） |
| 标题输入框 | `input[placeholder*="标题"]`，set value + input/change 事件 |
| 底部 26px 块 | `.tn-quick-input-block`（快速输入 UI，不是正文，不要试图删除） |

## 落库规则（最重要）

- 秀米保存的是**它自己的模型**。直接 `remove()`、`insertAdjacentHTML()`、改 `style` 在界面上生效，**保存后重载全部还原**。
- `document.execCommand('insertHTML' | 'delete')` **可以落库**，但前提是**目标格已被真实点击激活**：先 `Input.dispatchMouseEvent` 在格内 `mousePressed` + `mouseReleased`，再设 Range 执行命令。在未激活的格上执行 = 假改动（这就是"图片不入库"的最常见原因）。
- **不要用空插入删除**：`execCommand('insertHTML', false, '')` 会触发整篇按模型重建，把其它尚未落库的改动一并冲掉。删除用 `execCommand('delete')`；替换就给非空 HTML（常用 `<p style="height: 12px; font-size: 12px; line-height: 1px;">&nbsp;</p>`）。
- 纯样式修改（例如把 wrapper 的 `padding` 归零）：激活该格 → 改 style → 敲一次空格再退格（制造 input 事件让编辑器收下）→ 保存。实测可持久。
- **收尾一律 `save → reload → 读 DOM`**，保存前的 DOM 可能是假象。
- 一次 `Runtime.evaluate` 里做完一串 DOM 改动并不会"更可靠"，关键仍是激活格 + 编辑器命令。

## 图片

- 图片"入库"的本质：`<img src="//img.xiumi.us/xmi/ua/...">` 经 `insertHTML` 插进**已激活**的卡片内，保存后仍然存在。格未激活时它会静默消失。
- 上传新图：左侧「我的图库 → 上传图片(无水印)」。纯 CDP 可用 `Page.setInterceptFileChooserDialog` + `DOM.setFileInputFiles`；或直接用 `scripts/xiumi.py upload`（Playwright，需提权）。
- 实测 base64 粘贴导图不可靠（3 张只进 2 张）。
- 卡内图片统一 `style="width:100%;vertical-align:middle;"`（= 289px），不要写死像素宽。

## 结构类坑

- 画布正文宽 343px。每个顶层组件的 wrapper 都是 `background-color:#fdf8eb;padding:16px 12px 20px 12px;`，**两个组件相接时两层 padding 叠加，空隙约 50px**，用户会当成"空白单元格"。处置：把相邻面的 `paddingTop` / `paddingBottom` 归零；一件正文最好只保留少量顶层组件。
- 粘贴长文会被秀米拆成多个 cell；每个 cell 又是独立组件、各自带 padding，所以拆得越多，跨节空隙越多。
- 因标题缎带单独成卡导致"标题跑出框"时：把标题 `<p>` 插进正文卡开头（选中卡内首个 `12px` 空段替换为「标题 + 空段」），再删掉原来的空标题卡。
- `Range.setStartBefore(a) / setEndAfter(b)` + `insertHTML` 合并相邻块会**吞掉后一块的首段**（实测把下一节标题卷进前一卡）。合并后必须核对；误并了就反向修回来。

## 其它已实测

- 初次整篇投递：仍推荐"复制富文本 + 画布 `Ctrl+A` / `Ctrl+V`"（源页 `execCommand('copy')`）。秀米会按基础格式重排并拆成多个 cell，**先设基础格式再粘**。
- 顶部「更多」里有：导入公众号文章、导入 HTML 代码、另存一个图文、**另存图文给其他用户**（投稿另存到学院账号靠它）、收集图片、生成长图/PDF/视频、一键排版。
- 封面槽位 `.left-part`（`ng-click="onCoverEditingStart"`）的背景由 Angular `ng-style` 绑定，读 `style` 看不出，自动化点选不可靠 —— 封面留给人工两步操作，或在公众号后台选。
- 每次改结构前后都跑一次 `layout.py state` 做快照，出问题好定位。