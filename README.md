# WeChat Content Pipeline

微信公众号内容生产流水线 —— AI 驱动的自动化内容创作系统。

## 架构

topic-editor → deep-researcher → writer ⇄ quality-reviewer → designer → publisher

## 部署

运行目录：`/home/lw/wechat_publisher/`（数据目录）
脚本路径：`/home/lw/wechat-content-pipeline/`（代码仓库）

```bash
# 采集
python3 step1_采集.py --column frontier-news
python3 step2_选题.py --column frontier-news
```
