# Agent Insight

AI Engineering Radar — 监控 OpenAI Engineering、Anthropic Engineering、Karpathy 的技术动态。

## 数据源

| 来源 | 方式 | URL |
|------|------|-----|
| OpenAI | RSS (Engineering) | `https://openai.com/news/rss.xml` |
| Anthropic | 页面抓取 | `https://www.anthropic.com/engineering` |
| Karpathy Blog | RSS | `https://karpathy.github.io/feed.xml` |
| Karpathy X | Nitter RSS | `https://nitter.net/karpathy/rss` |

## 使用

```bash
./run.sh          # 启动 → http://localhost:8080
python3 fetcher.py  # 手动刷新数据
```

每天 08:00 自动刷新（cron: `515382dfac03`）。
