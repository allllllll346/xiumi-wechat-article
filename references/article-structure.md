# 版式骨架与可复用 HTML 片段（党团活动 · 党旗红）

## 骨架（自上而下）

1. 顶部标识：`党 团 活 动` 两侧短发丝线 + 一条全宽红线
2. 标题卡（红边框）：主标题 + 副标题 + 全宽红线 + 单位 / 班级两行灰字
3. 活动概况卡：缎带标题「活动概况」+ 正文 + 现场照片 + 图注
4. 小节卡 01 / 02 / 03：缎带标题 + 正文 + （图片 + 图注）+ 卡末分隔线
5. 口号条（红边框、浅黄底）
6. `— END —`
7. 署名（顶部虚线）

一个小节 = **一张卡**。标题、正文、图片、图注、分隔线必须在同一个卡片 `div` 里，否则会出现"标题在框外"的观感。

## 配色

| 用途 | 值 |
| --- | --- |
| 党团活动主色（党旗红） | `rgb(199, 0, 11)` / `#c7000b` |
| 浅黄底（口号条） | `#fff8e8` |
| 卡片底色 | `#ffffff` |
| 页面底色 | `#fdf8eb` |
| 卡片描边 | `#f0e0c0` |
| 图注灰 | `#a0a0a0` / `rgb(160, 160, 160)` |
| 副标题金 | `rgb(184, 135, 60)` |
| 标题卡描边 | `#c7000b` |

非党团主题（节日、科普等）按活动性质换主色，但同一篇只用一套主色。

## 尺寸

- 秀米图文正文宽 **343px**（单栏）。
- 组件外层 wrapper：`background-color:#fdf8eb;padding:16px 12px 20px 12px;`
- 卡片：`background-color:#ffffff;border:1px solid #f0e0c0;padding:18px 14px 10px 14px;margin:0 0 14px 0;`
- 卡内可用宽 = 343 − 24（外层左右） − 2（边框） − 28（卡内左右） = **289px**，所以卡内图片一律 `width:100%`。
- 正文 `line-height:1.8; text-indent:2em;`，字间距 1，两端对齐（规范见 `ucas-cre-standards.md`）。

## 片段

### 缎带小标题

```html
<p style="text-align: center;"><span style="display: inline-block; width: 8px; height: 26px; vertical-align: top; border-top: 13px solid rgb(199, 0, 11); border-bottom: 13px solid rgb(199, 0, 11); border-left: 8px solid transparent; font-size: 12px; line-height: 1px;">&nbsp;</span><span style="display: inline-block; height: 26px; line-height: 26px; padding: 0px 12px; font-size: 16px; background-color: rgb(199, 0, 11); color: rgb(255, 255, 255); font-weight: bold; letter-spacing: 2px; vertical-align: top;">01&nbsp;&nbsp;领学导学</span><span style="display: inline-block; width: 8px; height: 26px; vertical-align: top; border-top: 13px solid rgb(199, 0, 11); border-bottom: 13px solid rgb(199, 0, 11); border-right: 8px solid transparent; font-size: 12px; line-height: 1px;">&nbsp;</span></p>
```

### 12px 空段（标题与正文之间）

```html
<p style="height: 12px; font-size: 12px; line-height: 1px;">&nbsp;</p>
```

### 图片 + 图注

```html
<p style="text-align: center;"><img src="//img.xiumi.us/xmi/ua/XXXX/i/xxxxxxxx.jpg?x-oss-process=style/xmwebp" style="width:100%;vertical-align:middle;"></p>
<p style="font-size: 12px; color: rgb(160, 160, 160); text-align: center; letter-spacing: 0px; line-height: 1.6;">8xx班开展民族团结教育主题党团日活动</p>
```

### 卡末分隔线（全宽红线 + ◆ + 全宽红线）

```html
<p style="text-align: center; line-height: 1px; font-size: 12px;"><span style="display: inline-block; width: 100%; height: 1px; background-color: rgb(199, 0, 11); vertical-align: middle; line-height: 1px;">&nbsp;</span></p>
<p style="text-align: center;"><span style="display: inline-block; width: 44px; height: 1px; background-color: rgb(199, 0, 11); vertical-align: middle; font-size: 12px; line-height: 1px;">&nbsp;</span><span style="color: rgb(199, 0, 11); font-size: 12px; padding: 0px 8px; vertical-align: middle; line-height: 1px;">◆</span><span style="display: inline-block; width: 44px; height: 1px; background-color: rgb(199, 0, 11); vertical-align: middle; font-size: 12px; line-height: 1px;">&nbsp;</span></p>
<p style="text-align: center; line-height: 1px; font-size: 12px;"><span style="display: inline-block; width: 100%; height: 1px; background-color: rgb(199, 0, 11); vertical-align: middle; line-height: 1px;">&nbsp;</span></p>
```

### 口号条

```html
<div style="border:1px solid #c7000b;background-color:#fff8e8;padding:14px 10px;text-align:center;margin:0 0 14px 0;"><p style="font-weight: bold; color: rgb(199, 0, 11); letter-spacing: 3px;">手足相亲 &nbsp;守望相助 &nbsp;团结一心 &nbsp;共同奋斗</p></div>
```

### END 与署名

```html
<p style="text-align: center; font-size: 20px; font-weight: bold; color: rgb(199, 0, 11); letter-spacing: 5px;">— END —</p>
<div style="border-top:1px dashed #e7d6b6;padding-top:12px;text-align:center;">
<p style="font-size: 13px; color: rgb(122, 122, 122); line-height: 2;">图片|张三、李四</p>
<p style="font-size: 13px; color: rgb(122, 122, 122); line-height: 2;">文案|张三</p>
<p style="font-size: 13px; color: rgb(122, 122, 122); line-height: 2;">排版|张三</p>
<p style="font-size: 13px; color: rgb(122, 122, 122); line-height: 2;">责编|党建中心</p>
<p style="font-size: 13px; color: rgb(122, 122, 122); line-height: 2;">审核|责任老师</p>
</div>
```

## 秀米归一化（写 HTML 时注意）

- 字号会被转成百分比：`15px→80%`、`16px→106.667%`、`20px→133.333%`；写 `px` 即可，秀米自己换算。
- `background-image: linear-gradient()` 会被丢弃；空 `<span></span>` 会被丢弃，装饰元素必须塞 `&nbsp;`。
- `<p>` 最小高度约 12px，所以 1px 细线必须写成 `display:inline-block;width:100%;height:1px;background-color:…` 的 `span`。
- 卡片宽度不能靠 `width` 撑，统一 `width:100%` 让秀米按 289px 排版。