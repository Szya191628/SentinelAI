# SentinelAI — 多引擎舆情分析平台

> 基于大语言模型的全栈舆情分析平台，通过多智能体协作实现深度舆情洞察、媒体传播分析、智能问答与报告生成。

## 项目简介

SentinelAI 是一个面向舆情分析场景的多引擎智能平台，采用 **FastAPI + LangGraph** 构建后端多智能体工作流，**Vue 3 + TypeScript + Element Plus** 构建前端交互界面，支持 Docker Compose 一键部署。

平台核心包含五个分析引擎，各司其职：

| 引擎 | 功能 | 推荐模型 |
|------|------|----------|
| **InsightEngine** | 深度洞察 — 多轮反思式舆情分析 | Kimi K2 |
| **MediaEngine** | 媒体分析 — 社交媒体传播链路分析 | Gemini 2.5 Pro |
| **QueryEngine** | 智能问答 — 快速舆情检索与回答 | DeepSeek |
| **ReportEngine** | 报告生成 — 可视化舆情报告输出 | Gemini 2.5 Pro |
| **ForumEngine** | 多角色讨论 — AI 模拟多方观点辩论 | Qwen3 |

## 技术架构

```
┌─────────────────────────────────────────────────┐
│                   Vue 3 Frontend                │
│        (Element Plus / Pinia / Vue Router)      │
└──────────────────────┬──────────────────────────┘
                       │ HTTP / SSE
┌──────────────────────▼──────────────────────────┐
│                 FastAPI Backend                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Routers  │ │ Services │ │   Event Bus      │ │
│  └────┬─────┘ └────┬─────┘ └────────┬─────────┘ │
│       │            │                │           │
│  ┌────▼────────────▼────────────────▼─────────┐ │
│  │            LangGraph Engines               │ │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────────┐ │ │
│  │  │ Insight │ │  Media  │ │    Query     │ │ │
│  │  ├─────────┤ ├─────────┤ ├──────────────┤ │ │
│  │  │ Report  │ │  Forum  │ │    Common    │ │ │
│  │  └─────────┘ └─────────┘ └──────────────┘ │ │
│  └────────────────────────────────────────────┘ │
│       │            │                │           │
│  ┌────▼─────┐ ┌────▼─────┐ ┌───────▼────────┐  │
│  │ LLM APIs │ │ Search   │ │   Database     │  │
│  │(多模型)   │ │(Tavily等) │ │  (MySQL/SQLite)│  │
│  └──────────┘ └──────────┘ └────────────────┘  │
└─────────────────────────────────────────────────┘
```

## 核心特性

- **多引擎协作**：五个独立引擎各负其责，通过统一调度实现端到端分析
- **LangGraph 工作流**：基于状态图的复杂工作流编排，支持条件分支与循环
- **反思机制**：InsightEngine 内置 Reflection Loop，多轮迭代提升分析深度
- **多模型适配**：统一 LLM Client 层，灵活对接 Kimi、Gemini、DeepSeek、Qwen 等
- **多源搜索**：集成 Tavily、博查、Anspire 等搜索工具，内置关键词优化器
- **实时推送**：SSE（Server-Sent Events）实现分析进度实时推送
- **情感分析**：内置多语言情感分析模型，自动标注舆情倾向
- **聚类去重**：基于 Sentence-Transformers 的搜索结果聚类，去除冗余信息

## 技术栈

### 后端

- **框架**：FastAPI + Uvicorn
- **工作流**：LangGraph（LangChain 生态）
- **数据库**：SQLAlchemy + MySQL / SQLite
- **LLM**：OpenAI SDK（兼容多厂商 API）
- **NLP**：sentence-transformers、scikit-learn
- **报告**：matplotlib、wordcloud、WeasyPrint

### 前端

- **框架**：Vue 3 + TypeScript
- **UI 库**：Element Plus
- **状态管理**：Pinia
- **路由**：Vue Router
- **构建**：Vite
- **Markdown 渲染**：marked

### 部署

- Docker Compose（MySQL + Backend + Frontend + Nginx）

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0（或使用 SQLite 模式）

### 1. 克隆项目

```bash
git clone https://github.com/your-username/sentinelai.git
cd sentinelai
```

### 2. 配置环境变量

复制并编辑 `.env` 文件：

```bash
cp .env.example .env
```

核心配置项：

```env
# 数据库（sqlite 模式无需安装 MySQL）
DB_DIALECT=sqlite
DB_NAME=media_crawler

# LLM API（以 DeepSeek 为例）
INSIGHT_ENGINE_API_KEY=your-api-key
INSIGHT_ENGINE_BASE_URL=https://api.deepseek.com
INSIGHT_ENGINE_MODEL_NAME=deepseek-chat

# 搜索工具
TAVILY_API_KEY=your-tavily-key
SEARCH_TOOL_TYPE=TavilyAPI
```

### 3. 启动后端

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动
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

服务启动后：
- 前端界面：`http://localhost:80`
- 后端 API：`http://localhost:5000`
- 数据库：`localhost:3306`

## 项目结构

```
sentinelai/
├── app/                          # FastAPI 后端应用
│   ├── main.py                   # 应用入口
│   ├── config.py                 # 全局配置（pydantic-settings）
│   ├── routers/                  # API 路由
│   │   ├── search.py             # 搜索接口
│   │   ├── report.py             # 报告接口
│   │   ├── events.py             # SSE 事件流
│   │   ├── forum.py              # 论坛接口
│   │   └── config.py             # 配置管理接口
│   ├── services/                 # 业务逻辑层
│   │   ├── search_service.py     # 搜索调度
│   │   ├── report_service.py     # 报告生成
│   │   ├── event_bus.py          # 事件总线
│   │   └── forum_service.py      # 论坛服务
│   └── schemas/                  # 数据模型定义
│
├── engines/                      # 分析引擎
│   ├── common/                   # 公共模块
│   │   ├── llm_client.py         # 统一 LLM 客户端
│   │   └── structured_output.py  # 结构化输出
│   ├── InsightEngine/            # 深度洞察引擎
│   │   ├── graph.py              # LangGraph 工作流定义
│   │   ├── nodes/                # 工作流节点
│   │   ├── tools/                # 搜索、聚类、情感分析工具
│   │   └── prompts/              # Prompt 模板
│   ├── MediaEngine/              # 媒体分析引擎
│   ├── QueryEngine/              # 智能问答引擎
│   ├── ReportEngine/             # 报告生成引擎
│   └── ForumEngine/              # 多角色讨论引擎
│
├── frontend/                     # Vue 3 前端
│   ├── src/
│   │   ├── views/                # 页面视图
│   │   │   ├── Dashboard.vue     # 主面板
│   │   │   ├── InsightTab.vue    # 深度洞察
│   │   │   ├── MediaTab.vue      # 媒体分析
│   │   │   ├── QueryTab.vue      # 智能问答
│   │   │   ├── ReportTab.vue     # 报告生成
│   │   │   └── ForumTab.vue      # 多角色讨论
│   │   ├── components/           # 组件
│   │   ├── stores/               # Pinia 状态管理
│   │   ├── api/                  # API 封装
│   │   └── composables/          # 组合式函数
│   └── package.json
│
├── data/                         # 数据文件
├── tools/                        # 工具脚本（情感分析模型等）
├── tests/                        # 测试
├── docker-compose.yaml           # Docker 编排
├── Dockerfile.backend            # 后端镜像
├── Dockerfile.frontend           # 前端镜像
├── requirements.txt              # Python 依赖
└── main.py                       # 启动入口
```

## 引擎工作流（InsightEngine）

InsightEngine 采用 LangGraph 编排的多轮反思式分析流程：

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

每个段落经历「搜索 → 摘要 → 反思 → 补充搜索」的循环，确保分析的深度与全面性。

## 支持的 LLM 模型

| 厂商 | 模型 | 用途 |
|------|------|------|
| Moonshot | Kimi K2 | InsightEngine 推荐 |
| Google | Gemini 2.5 Pro | MediaEngine / ReportEngine 推荐 |
| DeepSeek | DeepSeek Chat | QueryEngine 推荐 |
| 阿里云 | Qwen3 | ForumEngine / KeywordOptimizer 推荐 |

所有引擎均支持通过 `.env` 灵活切换模型和 API 端点。

## 许可证

MIT License
