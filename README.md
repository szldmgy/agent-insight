# Agent Insight

AI Engineering Radar — 监控 OpenAI Engineering、Anthropic Engineering、Karpathy 的技术动态。

## 功能

- 三栏仪表盘：OpenAI Engineering / Anthropic Engineering / Karpathy（Blog + X）
- Anthropic 风格浅色主题，中文摘要，点击展开全文
- 页面 Refresh 按钮一键拉取最新数据
- 每天 08:00 cron 自动刷新
- 数据内嵌 HTML，也可用 `server.py` 支持实时刷新

## 项目结构

```
agent-insight/
├── index.html              # 前端仪表盘（自包含，含内嵌数据）
├── fetcher.py              # 数据采集脚本
├── build.py                # 翻译合并 + 数据嵌入
├── server.py               # HTTP 服务（支持 /api/refresh）
├── run.sh                  # 一键启动
├── data/
│   ├── insights.json       # 采集结果
│   └── translations.json   # 中文翻译缓存
└── README.md
```

## 数据源

| 来源 | 方式 | URL |
|------|------|-----|
| OpenAI | RSS (Engineering) | `https://openai.com/news/rss.xml` |
| Anthropic | 页面抓取 + 缓存 | `https://www.anthropic.com/engineering` |
| Karpathy Blog | RSS | `https://karpathy.github.io/feed.xml` |
| Karpathy X | Nitter RSS | `https://nitter.net/karpathy/rss` |

## 使用

```bash
./run.sh                        # 一键启动 → http://localhost:8080
python3 fetcher.py              # 手动抓取最新数据
python3 fetcher.py && python3 build.py  # 抓取并生成静态页面（双击 index.html 即可打开）
```

每天 08:00 cron 自动刷新（job: `515382dfac03`）。
