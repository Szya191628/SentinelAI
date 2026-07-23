# SentinelAI

> 基于大语言模型的多引擎舆情分析平台，通过多智能体协作实现深度舆情洞察、媒体传播分析、智能问答与自动化报告生成。

---

## 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [技术架构](#技术架构)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [引擎详解](#引擎详解)
- [配置说明](#配置说明)
- [API 文档](#api-文档)
- [测试](#测试)
- [部署](#部署)
- [许可证](#许可证)

---

## 项目简介

SentinelAI 是一个面向舆情分析场景的多引擎智能平台。后端基于 **FastAPI + LangGraph** 构建多智能体工作流，前端基于 **Vue 3 + TypeScript + Element Plus** 构建交互界面，支持 Docker Compose 一键部署。

平台包含五个独立的分析引擎，各自承担不同的分析职责：

| 引擎 | 功能定位 | 推荐模型 |
|------|----------|----------|
| **InsightEngine** | 深度洞察 — 多轮反思式舆情分析 | Kimi K2 |
| **MediaEngine** | 媒体分析 — 社交媒体传播链路分析 | Gemini 2.5 Pro |
| **QueryEngine** | 智能问答 — 快速舆情检索与回答 | DeepSeek |
| **ReportEngine** | 报告生成 — 可视化舆情报告输出 | Gemini 2.5 Pro |
| **ForumEngine** | 多角色讨论 — AI 模拟多方观点辩论 | Qwen3 |

---

## 核心特性

- **多引擎协作** — 五个独立引擎各负其责，通过统一调度实现端到端分析
- **LangGraph 工作流** — 基于状态图的复杂工作流编排，支持条件分支与循环
- **反思机制** — InsightEngine 内置 Reflection Loop，多轮迭代提升分析深度
- **多模型适配** — 统一 LLM Client 层，灵活对接 Kimi、Gemini、DeepSeek、Qwen 等
- **多源搜索** — 集成 Tavily、博查、Anspire 等搜索工具，内置关键词优化器
- **实时推送** — SSE（Server-Sent Events）实现分析进度实时推送
- **情感分析** — 内置多语言情感分析模型（HuggingFace），自动标注舆情倾向
- **聚类去重** — 基于 Sentence-Transformers 的搜索结果聚类，去除冗余信息
- **可观测性** — 集成 LangFuse，支持全链路 Trace 追踪与调试
- **多源数据采集** — 内置 SentinelSpider 爬虫，覆盖微博、抖音、小红书、B站、知乎、贴吧、快手

---

## 技术架构

```
┌─────────────────────────────────────────────────────┐
│                    Vue 3 Frontend                   │
│           (Element Plus / Pinia / Vue Router)        │
└────────────────────────┬────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────▼────────────────────────────┐
│                   FastAPI Backend                    │
│  ┌───────────┐  ┌───────────┐  ┌──────────────────┐ │
│  │  Routers   │  │  Services │  │    Event Bus     │ │
│  └─────┬─────┘  └─────┬─────┘  └────────┬─────────┘ │
│        │              │                  │           │
│  ┌─────▼──────────────▼──────────────────▼─────────┐ │
│  │              LangGraph Engines                  │ │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────────┐  │ │
│  │  │ Insight  │ │  Media   │ │     Query      │  │ │
│  │  ├──────────┤ ├──────────┤ ├────────────────┤  │ │
│  │  │  Report  │ │  Forum   │ │ SentinelSpider │  │ │
│  │  └──────────┘ └──────────┘ └────────────────┘  │ │
│  └─────────────────────────────────────────────────┘ │
│        │              │                  │           │
│  ┌─────▼──────┐ ┌─────▼──────┐ ┌────────▼────────┐  │
│  │  LLM APIs  │ │  Search    │ │    Database     │  │
│  │ (多模型)    │ │ (Tavily等) │ │ (MySQL/SQLite)  │  │
│  └────────────┘ └────────────┘ └─────────────────┘  │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │           LangFuse Observability                │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

---

## 技术栈

### 后端

| 类别 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| 工作流引擎 | LangGraph（LangChain 生态） |
| LLM SDK | OpenAI SDK（兼容多厂商 API） |
| 数据库 | SQLAlchemy + MySQL / PostgreSQL / SQLite |
| NLP | sentence-transformers、scikit-learn |
| 情感分析 | PyTorch + HuggingFace Transformers |
| 报告渲染 | matplotlib、wordcloud、WeasyPrint |
| 可观测性 | LangFuse |
| 日志 | Loguru |

### 前端

| 类别 | 技术 |
|------|------|
| 框架 | Vue 3 + TypeScript |
| UI 库 | Element Plus |
| 状态管理 | Pinia |
| 路由 | Vue Router |
| 构建工具 | Vite |
| Markdown 渲染 | marked |
| HTTP 客户端 | Axios |

### 数据采集

| 类别 | 技术 |
|------|------|
| 爬虫框架 | MediaCrawler（定制版） |
| 支持平台 | 微博、抖音、小红书、B站、知乎、贴吧、快手 |
| 话题提取 | BroadTopicExtraction |
| 情感模型 | WeiboMultilingualSentiment |

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0（或使用 SQLite 模式，无需安装 MySQL）

### 1. 克隆项目

```bash
git clone https://github.com/your-username/sentinelai.git
cd sentinelai
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入必要的 API 密钥：

```env
# ── 数据库（SQLite 模式无需安装 MySQL）──
DB_DIALECT=sqlite
DB_NAME=media_crawler

# ── LLM API（至少配置一个引擎的密钥）──
INSIGHT_ENGINE_API_KEY=your-api-key
INSIGHT_ENGINE_BASE_URL=https://api.moonshot.cn/v1
INSIGHT_ENGINE_MODEL_NAME=kimi-k2-0711-preview

# ── 搜索工具 ──
TAVILY_API_KEY=your-tavily-key
SEARCH_TOOL_TYPE=TavilyAPI
```

### 3. 启动后端

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

后端默认运行在 `http://localhost:5000`，API 文档访问 `http://localhost:5000/docs`。

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`。

### 5. Docker 一键部署（可选）

```bash
docker-compose up -d
```

启动后访问：

| 服务 | 地址 |
|------|------|
| 前端界面 | `http://localhost:80` |
| 后端 API | `http://localhost:5000` |
| API 文档 | `http://localhost:5000/docs` |
| MySQL | `localhost:3306` |

---

## 项目结构

```
sentinelai/
├── app/                              # FastAPI 后端应用
│   ├── main.py                       # 应用入口 & SPA 托管
│   ├── config.py                     # 全局配置（pydantic-settings）
│   ├── routers/                      # API 路由层
│   │   ├── search.py                 #   搜索接口
│   │   ├── report.py                 #   报告接口
│   │   ├── events.py                 #   SSE 事件流
│   │   ├── forum.py                  #   论坛接口
│   │   ├── system.py                 #   系统状态接口
│   │   └── config.py                 #   配置管理接口
│   ├── services/                     # 业务逻辑层
│   │   ├── search_service.py         #   搜索调度
│   │   ├── report_service.py         #   报告生成
│   │   ├── forum_service.py          #   论坛服务
│   │   ├── system_service.py         #   系统服务
│   │   ├── event_bus.py              #   事件总线
│   │   └── event_types.py            #   事件类型定义
│   ├── schemas/                      # Pydantic 数据模型
│   └── utils/                        # 工具函数
│
├── engines/                          # 分析引擎（LangGraph 驱动）
│   ├── common/                       # 公共模块
│   │   ├── llm_client.py             #   统一 LLM 客户端
│   │   └── structured_output.py      #   结构化输出
│   ├── InsightEngine/                # 深度洞察引擎
│   │   ├── graph.py                  #   LangGraph 工作流定义
│   │   ├── agent.py                  #   引擎入口
│   │   ├── nodes/                    #   工作流节点
│   │   ├── tools/                    #   搜索、聚类、情感分析
│   │   ├── prompts/                  #   Prompt 模板
│   │   ├── llms/                     #   LLM 配置
│   │   └── state.py                  #   状态定义
│   ├── MediaEngine/                  # 媒体分析引擎
│   ├── QueryEngine/                  # 智能问答引擎
│   ├── ReportEngine/                 # 报告生成引擎
│   │   ├── core/                     #   核心：模板解析、章节拼接
│   │   ├── ir/                       #   中间表示（IR）层
│   │   ├── renderers/                #   渲染器：HTML / PDF / Markdown
│   │   ├── report_template/          #   报告模板（6 种场景）
│   │   └── scripts/                  #   工具脚本
│   └── ForumEngine/                  # 多角色讨论引擎
│
├── frontend/                         # Vue 3 前端
│   ├── src/
│   │   ├── views/                    #   页面视图
│   │   ├── components/               #   UI 组件
│   │   ├── stores/                   #   Pinia 状态管理
│   │   ├── api/                      #   后端 API 封装
│   │   ├── composables/              #   组合式函数（SSE、轮询）
│   │   └── router/                   #   路由配置
│   ├── package.json
│   └── vite.config.ts
│
├── tools/                            # 数据采集与分析工具
│   ├── SentinelSpider/               #   多平台爬虫
│   │   ├── BroadTopicExtraction/     #     热点话题提取
│   │   └── DeepSentimentCrawling/    #     深度情感爬取
│   │       └── MediaCrawler/         #       多平台媒体爬虫
│   └── SentimentAnalysisModel/       #   情感分析模型
│       └── WeiboMultilingualSentiment/
│
├── tests/                            # 测试目录
│   ├── test_app_*.py                 #   应用层单元测试
│   ├── test_crawler_*.py             #   爬虫模块测试
│   ├── test_*_engine_e2e.py          #   引擎 E2E 测试
│   └── run_tests.py                  #   测试运行器
│
├── scripts/                          # 辅助脚本
├── data/                             # 数据文件
├── docker-compose.yaml               # Docker 编排
├── Dockerfile.backend                # 后端镜像
├── Dockerfile.frontend               # 前端镜像
├── requirements.txt                  # Python 依赖
├── main.py                           # 启动入口
└── .env.example                      # 环境变量模板
```

---

## 引擎详解

### InsightEngine — 深度洞察

采用 LangGraph 编排的多轮反思式分析流程。每个段落经历「搜索 → 摘要 → 反思 → 补充搜索」的循环，确保分析的深度与全面性。

```
START
  │
  ▼
Generate Structure ──► Initial Search ──► Initial Summary
                                                │
                                                ▼
                                    Reflection Search ◄──┐
                                                │        │
                                                ▼        │
                                    Reflection Summary ──┘
                                         (loop N times)
                                                │
                                                ▼
                                    Format Report ──► Save Report
                                                         │
                                                         ▼
                                                        END
```

**核心工具**：聚类去重（Sentence-Transformers）、情感分析（HuggingFace）、关键词优化（LLM）

### MediaEngine — 媒体分析

专注于社交媒体传播链路分析，追踪信息在不同平台间的扩散路径与影响力。

### QueryEngine — 智能问答

快速舆情检索引擎，支持多源搜索、来源分类、结构化回答。

### ReportEngine — 报告生成

支持 6 种报告模板：

- 企业品牌声誉分析报告
- 市场竞争格局舆情分析报告
- 日常/定期舆情监测报告
- 特定政策/行业动态舆情分析报告
- 社会公共热点事件分析报告
- 突发事件与危机公关舆情报告

输出格式：HTML / PDF / Markdown

### ForumEngine — 多角色讨论

AI 模拟多方观点辩论，支持自定义角色参与讨论。

---

## 配置说明

所有配置通过环境变量或 `.env` 文件管理，详见 `app/config.py`。

### LLM 配置

每个引擎独立配置 API Key、Base URL 和模型名称：

```env
# Insight Engine（推荐 Kimi K2）
INSIGHT_ENGINE_API_KEY=sk-xxx
INSIGHT_ENGINE_BASE_URL=https://api.moonshot.cn/v1
INSIGHT_ENGINE_MODEL_NAME=kimi-k2-0711-preview

# Media Engine（推荐 Gemini 2.5 Pro）
MEDIA_ENGINE_API_KEY=sk-xxx
MEDIA_ENGINE_BASE_URL=https://aihubmix.com/v1
MEDIA_ENGINE_MODEL_NAME=gemini-2.5-pro

# Query Engine（推荐 DeepSeek）
QUERY_ENGINE_API_KEY=sk-xxx
QUERY_ENGINE_BASE_URL=https://api.deepseek.com
QUERY_ENGINE_MODEL_NAME=deepseek-chat

# Report Engine（推荐 Gemini 2.5 Pro）
REPORT_ENGINE_API_KEY=sk-xxx
REPORT_ENGINE_BASE_URL=https://aihubmix.com/v1
REPORT_ENGINE_MODEL_NAME=gemini-2.5-pro

# Forum Host（推荐 Qwen3）
FORUM_HOST_API_KEY=sk-xxx
FORUM_HOST_BASE_URL=https://api.siliconflow.cn/v1
FORUM_HOST_MODEL_NAME=qwen-plus
```

### 搜索工具配置

```env
# Tavily（默认，申请地址：https://www.tavily.com/）
SEARCH_TOOL_TYPE=TavilyAPI
TAVILY_API_KEY=tvly-xxx

# 博查（可选）
SEARCH_TOOL_TYPE=BochaAPI
BOCHA_WEB_SEARCH_API_KEY=your-key

# Anspire（可选）
SEARCH_TOOL_TYPE=AnspireAPI
ANSPIRE_API_KEY=your-key
```

### 数据库配置

```env
# SQLite（开发推荐，无需安装数据库）
DB_DIALECT=sqlite
DB_NAME=media_crawler

# MySQL（生产推荐）
DB_DIALECT=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=media_crawler
```

### LangFuse 可观测性（可选）

```env
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## API 文档

启动后端后访问 Swagger UI：

```
http://localhost:5000/docs
```

主要 API 路由：

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/search` | POST | 执行搜索分析 |
| `/api/report/generate` | POST | 生成报告 |
| `/api/report/stream` | GET | SSE 报告生成流 |
| `/api/forum/start` | POST | 启动论坛讨论 |
| `/api/events/stream` | GET | SSE 事件流 |
| `/api/config` | GET/PUT | 读取/更新配置 |
| `/api/system/status` | GET | 系统状态 |

---

## 测试

```bash
# 运行全部测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_app_services.py -v

# 运行 E2E 测试
python -m pytest tests/test_insight_engine_e2e.py -v

# 运行测试运行器
python tests/run_tests.py
```

测试覆盖：

| 测试类别 | 文件 | 说明 |
|----------|------|------|
| 应用层 | `test_app_*.py` | 服务、工具函数单元测试 |
| 爬虫 | `test_crawler_*.py` | 数据采集模块测试 |
| 引擎 E2E | `test_*_engine_e2e.py` | 各引擎端到端测试 |
| 报告引擎 | `test_report_engine_sanitization.py` | 输出清理测试 |

---

## 部署

### Docker Compose

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend

# 停止服务
docker-compose down
```

服务编排：

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend   │────▶│   Backend   │────▶│    MySQL    │
│  (Nginx:80)  │     │ (Uvicorn:5000)│    │  (3306)     │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 手动部署

```bash
# 后端
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5000

# 前端
cd frontend && npm run build
# 将 frontend/dist 部署到 Nginx 或由 FastAPI 自动托管
```

---

## 许可证

MIT License
