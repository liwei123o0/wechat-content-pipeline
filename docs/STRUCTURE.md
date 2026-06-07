# Project Structure

```
wechat-content-pipeline/
├── pipeline/                    # 核心流水线脚本（平铺，互相同级导入）
│   ├── collect/                 # 采集模块
│   │   ├── step1_采集.py
│   │   ├── step1a_采集_AI科技.py
│   │   └── aihot_collect.py
│   ├── topic/                   # 选题模块
│   │   ├── step2_选题.py
│   │   └── step2_选题_AI科技.py
│   ├── research/                # 研究模块
│   │   └── step3_深度搜索.py
│   ├── write/                   # 写作模块
│   │   └── step4_创作.py
│   ├── publish/                 # 发布模块
│   │   ├── step5_发布.py
│   │   ├── publish_designer_direct.py
│   │   ├── publish_v3.py
│   │   ├── publish_draft.py
│   │   └── publish_latest.py
│   ├── review/                  # 审核模块
│   │   └── review_article.py
│   ├── design/                  # 设计模块
│   │   ├── design_layout.py
│   │   ├── design_templates.py
│   │   ├── generate_article_covers.py
│   │   └── huashu_images.py
│   ├── export/                  # 导出模块
│   │   ├── export_docx.py
│   │   └── export_docx_simple.py
│   ├── utils/                   # 工具模块
│   │   ├── agent_comm.py
│   │   ├── column_config.py
│   │   ├── account_config.py
│   │   └── 发布历史_去重.py
│   ├── scripts/                 # 辅助脚本
│   └── __init__.py              # 模块入口，设置 sys.path
├── data/                        # 运行时数据
│   ├── 采集/
│   ├── 素材/
│   ├── 整理/
│   ├── 创作/
│   ├── 发布/
│   ├── 输出/
│   ├── 值得顶/
│   ├── 爆款文案库/
│   ├── agent_mailbox/
│   ├── 选题/
│   ├── 配置/
│   ├── 日志/
│   ├── 文章/
│   └── 重写_对比/
├── legacy/                      # 旧脚本归档
│   ├── batch_publish.py
│   ├── direct_publish_omni.py
│   ├── publisher_cron_publish.py
│   ├── quick_republish.py
│   ├── republish_articles.py
│   ├── reload_draft_desktop_agent.py
│   ├── reload_draft_desktop_agent_v2.py
│   ├── run_all.py
│   ├── run_all_columns.py
│   ├── run_pipeline.py
│   ├── rotate_pipeline.py
│   ├── update_draft.py
│   ├── publish_designer_v3.py
│   ├── 封面生成器.py
│   └── README.md
├── docs/                        # 文档
│   ├── README.md
│   ├── README_工作流.md
│   ├── Cron_Prompt_v3.md
│   ├── Cron_Prompt_v4.md
│   └── STRUCTURE.md
├── .gitignore
└── requirements.txt
```
