# Hello-Agents 答疑老师

> ⚠️ **克隆后须知**：本仓库的 `index.html` 里带的是**作者自己**云服务的
> `publishableKey`（仅标识应用、无权限，且服务端强制校验 Origin 必须匹配作者域名）。
> 你克隆后在本机打开是**调不通**的，需要自己开通一份云服务，并替换
> `index.html` 中 `PUBLIC_CONFIG` 里的 `endpoint` 和 `publishableKey`。

把《从零开始构建智能体》(Hello-Agents) 全 16 章知识内嵌进一个网页应用，
里面住着一位**专属答疑老师**——你问它答，答案严格基于教程原文。

**打开即用，无需任何 API Key。** 模型调用走云服务通道，31 个模型免密钥可选。

## 版权说明

- 本仓库的**应用代码**（`index.html` 及全部脚本）以 **MIT** 协议开源。
- `data/ch1.md` ~ `ch16.md` 为教程《从零开始构建智能体》原文，
  **版权归 [Datawhale 社区](https://github.com/datawhalechina/hello-agents) 所有**，
  此处仅作检索演示与知识库重建之用，遵循原仓库协议。
- `data/knowledge.json` 是从上述原文衍生的结构化摘要。

## 怎么用

```bash
cd C:/Users/16X/WorkBuddy/2026-10-09-10-33-22/hello-agents-tutor
"C:/Users/16X/.workbuddy/binaries/python/versions/3.13.12/python.exe" -m http.server 8787
```

浏览器打开 → http://127.0.0.1:8787

**不需要配置任何东西**——页面加载时会自动连上云服务、拉取模型列表。右上角状态标签
显示当前模型；点 **🎓 选择模型** 可以在 31 个模型间切换（GLM-5.3、Kimi-K3、
DeepSeek-V4、混元、MiniMax 等）。

越权演示：把 `index.html` 发给任何人，对方打开就能用，**不需要你的 Key**。

## 它是怎么工作的

```
你的问题
   ↓
关键词 2-gram/3-gram 分词 → 对 16 章知识库打分排序
   ↓
命中章节的【大纲 + 要点 + 关键术语 + 代码符号】拼成上下文
   ↓
连同答疑老师人格 System Prompt，经云服务转发给大模型（免密钥）
   ↓
流式返回答案 + 自动标注引用章节
```

**密钥在哪**：厂商密钥由云服务侧持有，前端只知道一个 `publishableKey`——
它只标识"哪个应用"，本身不带任何权限，服务端还会校验 Origin 必须精确匹配。
所以就算别人扒走它，也只能在你这个域名下调用。

## 额度与限流（付费模型保护）

页面内置了一套**付费模型防刷 + 免费模型兜底**机制，目的是让分享出去的链接不会被
陌生人无限消耗云服务额度：

| 规则 | 值 | 实现位置 |
|---|---|---|
| 付费模型累计可用次数 | **2 次** | 云端 `usage_limits` 表按设备计数 |
| 单次回答字数上限 | **约 1000 字** | System Prompt 约束 + `max_tokens` 兜底 + 前端硬截断 |
| 免费/付费判定 | 按模型 `credits` 倍率自动分 | `isFreeModel()` |
| 用尽后行为 | **静默切换**到免费模型，问答不中断 | `pickFreeModel()` |
| 调用失败 | **自动退还**该次付费额度 | `refundPaid()` → `refund_paid_usage` RPC |

**计数存哪儿**：访客设备号存在浏览器 localStorage，计数存在**云数据库**
（`usage_limits` 表 + RLS），钥匙是设备号。清缓存会换新设备号，但这是
"防无意滥用"级别的限流，不是账号体系。

**三个云端函数**（都在 `public` schema，`SECURITY DEFINER` 绕 RLS 原子计数）：

- `bump_paid_usage(p_device TEXT, p_limit INT)` → `TABLE(used_count INT, allowed BOOL)`
  用 `FOR UPDATE` 原子 +1，返回加完后的次数和是否放行。
- `get_paid_usage(p_device TEXT)` → `INT`，只读当前次数（前端开机同步用）。
- `refund_paid_usage(p_device TEXT)` → `TABLE(used_count INT)`，调用失败时退还 1 次，
  保证用户不因服务端报错白扣配额。

**免费模型可用性实测**：`hy3`(Hy3)、`hunyuan-chat`(Turbos) 正常产出；
`auto` 在本套流式链路上返回空文本，已加入黑名单 `FREE_MODEL_BLACKLIST` 并
按 `FREE_MODEL_PREFER` 偏好表优先选 `hy3`。

## 文件说明

| 文件 | 作用 |
|---|---|
| `index.html` | 整个应用（界面 + 检索 + 云服务调用），单文件 |
| `data/knowledge.json` | 16 章结构化知识库，173 KB，前端直接读 |
| `data/ch1.md` ~ `ch16.md` | 教程原文，留着备查/重建知识库用 |
| `verify_cloud.py` | 验证云服务免密钥链路（模型列表 + 流式问答） |
| `verify_quota.py` | 验证云端额度 RPC（bump / refund / get）走真实 HTTP 的行为 |
| `fetch_chapters.py` | 从 GitHub 下载 16 章原文 |
| `fetch_retry.py` | 下载失败时的重试（走 GitHub API 通道） |
| `build_knowledge.py` | 把原文压缩成 knowledge.json |
| `test_tutor.py` | 用外部 API 做对照测试（可选，需自备 Key） |

## 答疑老师的设定

- **先结论 → 再原理 → 最后代码**，概念题 200-400 字，实现题到 600 字带代码
- 严格以知识库为准，教程里没写的会明说"以下是我的补充"
- 会主动点出常见误区（框架封装掩盖循环逻辑 / RAG ≠ 记忆系统 / MCP 是接口规范不是模型能力）
- 拒绝"作为一个AI"这类话，始终以答疑老师身份说话

要改人格，编辑 `index.html` 里的 `systemPrompt()` 函数即可。
要调回答长度，改那段里的字数约定。

## 已验证

- ✅ 16 章原文全部下载成功（累计约 110 万字）
- ✅ 知识库生成：16 章 / 173 KB / 小节结构完整
- ✅ **云服务免密钥链路跑通**：模型列表返回 31 个模型；流式问答正常返回
  （实测 DeepSeek-V4-Flash 回答 ReAct 循环问题，188 字，正确标注章节）
- ✅ 端到端问答跑通：ReAct 对比、MCP 协议两问均正确引用章节
- ✅ 检索准确率抽查：15 个典型问题，首选项全部命中正确章节
- ✅ **额度限流链路实测**（真实 HTTP）：bump×2 → 第 3 次 denied → refund 回退 →
  退还后又能用，`used_count` / `allowed` 全部符合预期
- ✅ **免费模型兜底实测**：`hy3` 448 字、`hunyuan-chat` 362 字，均正确引用章节
- ✅ **1000 字上限实测**：付费模型 `hunyuan-2.0-thinking` 回答 830 字，在限内

## 注意

- **必须用本地服务器打开**，不能双击 html 文件（浏览器会拦住 knowledge.json 的加载）
- 知识库是**精简摘要**（大纲+要点+术语），不含原文全文。需要原文细节时
  让答疑老师说明，或直接查 `data/chN.md`
- 云服务额度属于本应用，**别把它当开放代理对外滥用**——页面对错误码做了
  分类提示，额度用尽会明确告知
- 全部内容版权归 Datawhale 社区所有，仓库：https://github.com/datawhalechina/hello-agents
