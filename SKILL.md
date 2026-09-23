---
name: xiumi-wechat-article
description: 生成并排版微信公众号推文（秀米）。当用户要写班级/党支部活动推文、新闻稿，或要求在秀米里完成排版时使用；涵盖素材提取、按学院投稿规范成稿、图片与封面处理、以及驱动本机浏览器在秀米中排版。仅需写纯文本稿件、不涉及秀米排版时无需本技能。
metadata:
  short-description: 秀米公众号推文成稿与排版
---

# 秀米公众号推文（成稿 + 排版）

## 何时用

- 用户给了活动素材（PPT / 图片 / 讲稿）并要"一篇公众号推文 / 新闻稿 / 秀米排版"。
- 需要按特定学院或单位的投稿规范成稿（标题格式、第三人称、图注、署名、退稿红线）。

## 先确定三件事

1. **交付到哪一步**：只出稿，还是出稿并**在秀米里排版**。
2. **署名与事实**：日期、地点、人名职务，文案/图片/排版/审核各写谁 —— 必须问用户，不要编。
3. **主体口径**：全文统一称"XX班"还是"XXXX党支部"。

## 成稿流程

1. 提取素材文字（`python-pptx` / `pypdf` / `python-docx`），另存成 `素材提取/*.txt` 便于核对。
2. 按 `references/ucas-cre-standards.md` 成稿；版式骨架、配色与可复用 HTML 片段见 `references/article-structure.md`。
3. 图片压到 1080px 宽并按叙述顺序编号；封面 900×383、分享小图 200×200；逐张自查（无半人头、旗帜拍全、党旗在左团旗在右）。
4. 交付物统一放一个新文件夹：校对稿、秀米粘贴版 HTML、图片/封面子目录、素材提取子目录、排版说明。

## 秀米排版流程

用 `scripts/layout.py`（纯 CDP 驱动本机已登录的 Chrome，**不需要 Playwright，沙箱内可直接跑**）：

```bash
python scripts/layout.py --draft <草稿ID> state        # 结构快照：组件/卡片/缎带/图片/空卡
python scripts/layout.py --draft <ID> activate 1       # 真实点击激活第 1 格
python scripts/layout.py --draft <ID> insert --cell 1 --card 03 --last --html-file 图.html
python scripts/layout.py --draft <ID> delete-comp 2    # 删掉第 2 个顶层组件
python scripts/layout.py --draft <ID> verify           # 保存+重载+复核（每次改动后必跑）
python scripts/layout.py --draft <ID> zero-padding 1   # 收敛跨组件空隙
```

先准备一个专用 Chrome（已登录秀米，Cookie 长期有效）：

```
chrome.exe --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=<专用目录> https://xiumi.us/
```

编辑器地址 `https://xiumi.us/studio/v5#/paper/for/<草稿ID>/cube/0`。选择器、登录、图片上传等细节见 `references/xiumi-ui-notes.md`。

### 铁律

1. **秀米保存的是它自己的模型，不是 DOM。** 直接 `remove()` / `insertAdjacentHTML()` / 改 style 只会骗过眼睛，**保存后重载即还原**。
2. **落库只能用编辑器命令，且必须先把目标格"激活"。** 用真实鼠标事件在目标格内点一下，再 `document.execCommand('insertHTML', false, html)` 或 `document.execCommand('delete')`。在未激活的格上执行 = 假改动 —— 用户看到的"图片不入库"多数就是这个原因。
3. **别用空插入来删除**：`execCommand('insertHTML', false, '')` 会触发整篇按模型重建，把尚未落库的改动一起冲掉。删块用 `execCommand('delete')`，替换就给一段非空 HTML（例如 12px 空段）。
4. **只认"保存 → 重载 → 读 DOM"。** 保存前的 DOM 可能是假象，每次改动后跑 `verify`。
5. **不要截图问用户**；截图只给自己做视觉复核，判断一律读 DOM。

### 常见版式事故与处置

- **小节标题跑到框外**（标题缎带自成一张卡）：一个小节必须是**一张卡**，标题、正文、图片、图注、分隔线同框。把标题插回正文卡开头，再删掉多余的空标题卡。
- **图片被抽成独立组件 / 图注单独成格**：把 `<p><img …></p>` 与图注 `<p>` 一起 `insert` 进目标卡（选中卡内最后一个空段再插），再 `delete-comp` 删掉多余的独立组件与空卡。
- **跨组件空隙过大（约 50px，像"空白单元格"）**：正文被拆成多个顶层组件，每个自带 `padding:16px 12px 20px 12px`，相接处叠加。用 `zero-padding` 把相邻面的 padding 归零。
- **`setStartBefore/…/setEndAfter` + insertHTML 合并相邻块会吞掉后一块的首段**（实测把下一节标题卷进了前一卡）。合并后必须核对，必要时把误并的标题插回原卡再删。
- **末尾 26px 的"空白单元格"**：那是编辑器的快速输入块 `.tn-quick-input-block`，不属于正文，不用处理。

## 收尾与投稿

- 文末按规范署名：`图片|` `文案|` `排版|` `审核|` `责编|`（图文同一人可写"图文|"）。
- 定稿后另存到指定秀米账号（学院要求存到 `<学院新媒体秀米账号邮箱>`），并在宣委群告知。
- 新闻稿投 `<学院新闻投稿邮箱>`，需"图文分离稿 + 审核稿"两份、图片按出现顺序命名、整体打包。
- 群发到公众号必须在微信公众平台后台由管理员完成（秀米只负责排版与另存）。
- 若用了用户的账号密码登录，提醒其事后修改密码；**不要把密码写进任何文件或命令**，用环境变量 `XIUMI_PW`。

## 参考

- `references/ucas-cre-standards.md` —— 学院投稿规范（称呼、日期、图注、署名、红线）。
- `references/article-structure.md` —— 版式骨架、党旗红配色、可直接复用的 HTML 片段、秀米归一化规则。
- `references/xiumi-ui-notes.md` —— 秀米编辑器选择器速查、落库规则、图片与封面、其它实测坑。