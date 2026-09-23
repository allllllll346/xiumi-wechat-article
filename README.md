# 秀米公众号推文 Skill（xiumi-wechat-article）

一个给 Codex / Claude 等编码 Agent 用的 **技能包（Skill）**：把一次班级或党支部活动，从散乱的素材变成一篇**符合投稿规范、并且在秀米里真正排版落地**的微信公众号推文。

它解决的不是"怎么写文案"这一个问题，而是**整条流水线**：

1. 从 PPT / PDF / Word / 图片里提取素材文字；
2. 按单位投稿规范成稿（标题格式、第三人称、语言红线、图注、署名）；
3. 处理图片与封面尺寸；
4. **用纯 CDP 驱动本机已登录的浏览器，在秀米编辑器里完成排版并保存落库**；
5. 交稿前的自查清单与投稿流程。

> 本技能源自一次真实实践：中国科学院大学资源与环境学院 2026 级某班"民族团结教育"主题党团日活动的公众号推文（成稿 + 秀米排版 + 定稿另存）。文中的学院规范已抽成独立参考文件，**换单位只需替换该文件**。

## 目录结构

```
xiumi-wechat-article/
├── SKILL.md                        # 技能主文件：判定入口、成稿流程、排版流程、五条铁律
├── references/
│   ├── ucas-cre-standards.md       # 投稿与排版规范要点（示例：国科大资环学院，可替换）
│   ├── article-structure.md        # 版式骨架、党旗红配色表、可直接复用的 HTML 片段
│   └── xiumi-ui-notes.md           # 秀米编辑器选择器速查、落库规则、实测踩坑
└── scripts/
    ├── cdp.py                      # 极简 CDP 客户端（连接本机 Chrome 调试端口）
    ├── xm.py                       # CDP 公共动作（点击、输入、剪贴板、粘贴）
    ├── layout.py                   # 排版操作台：state / activate / insert / delete-comp / verify / zero-padding
    └── xiumi.py                    # 旧路径（Playwright）：登录、图库上传、封面
```

## 安装

把整个 `xiumi-wechat-article/` 目录放进 Agent 的 Skills 根目录：

```bash
cp -r xiumi-wechat-article ~/.codex/skills/     # Codex
cp -r xiumi-wechat-article ~/.claude/skills/    # Claude Code
```

Windows PowerShell：

```powershell
Copy-Item -Recurse .\xiumi-wechat-article "$env:USERPROFILE\.codex\skills\"
```

重启 Agent 会话后，说出类似"帮我把这次党团活动做成公众号推文并排版"即可触发。

## 依赖

排版主路径只需要两个纯 Python 库，**不需要 Playwright**：

```bash
pip install requests websocket-client
```

只有旧的 `scripts/xiumi.py`（自动登录、图库上传）需要 Playwright，且通常需要提权运行。

## 快速开始

**(1) 准备一个专用 Chrome**（人工登录一次，Cookie 长期有效）：

```bash
chrome.exe --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="<专用目录>" https://xiumi.us/
```

**(2) 用 `layout.py` 操作编辑器**（`--draft` 为秀米草稿 ID）：

```bash
python scripts/layout.py --draft <草稿ID> state          # 结构快照：组件 / 卡片 / 缎带 / 图片 / 空卡
python scripts/layout.py --draft <草稿ID> activate 1     # 真实点击激活第 1 格
python scripts/layout.py --draft <草稿ID> insert --cell 1 --card 03 --last --html-file 图.html
python scripts/layout.py --draft <草稿ID> delete-comp 2  # 删掉第 2 个顶层组件
python scripts/layout.py --draft <草稿ID> zero-padding 1 # 收敛跨组件空隙
python scripts/layout.py --draft <草稿ID> verify         # 保存 → 重载 → 读 DOM 复核（每次改动后必跑）
```

## 五条铁律（这个技能最值钱的部分）

1. **秀米保存的是它自己的模型，不是 DOM。** 直接 `remove()` / `insertAdjacentHTML()` / 改 `style` 只会骗过眼睛，保存后重载即还原。
2. **落库只能用编辑器命令，且必须先把目标格"激活"。** 用真实鼠标事件在该格内点一下，再 `document.execCommand('insertHTML', false, html)` 或 `document.execCommand('delete')`。在未激活的格上执行 = 假改动 —— 用户看到的"图片不入库"绝大多数就是这个原因。
3. **别用空插入来删除。** `execCommand('insertHTML', false, '')` 会触发整篇按模型重建，把尚未落库的改动一起冲掉。
4. **只认"保存 → 重载 → 读 DOM"。** 保存前的 DOM 可能是假象。
5. **不要截图问用户**，截图只给自己做视觉复核，判断一律读 DOM。

## 已覆盖的典型版式事故

- 小标题缎带脱离卡片，观感上"标题跑到框外" → 整卡合并。
- 图片被抽成独立组件、图注单独成格 → 图片与图注成组回插。
- 跨组件 50px"空白单元格" → 相邻面 padding 归零。
- 相邻块合并时吞掉后一块首段 → 合并后必须核对并反向修回。
- 编辑器末尾 26px 的"空单元格"其实是 `.tn-quick-input-block`，不用处理。

## 注意

- 技能内含的是**方法**，不含任何真实活动素材、真实姓名或照片。
- `references/ucas-cre-standards.md` 是某学院的规范示例，**换单位请整体替换**，不要沿用。
- 请遵守秀米与微信公众号平台的服务条款；账号密码只通过环境变量传入（如 `XIUMI_PW`），**不要写进任何文件或命令**。

## License

MIT