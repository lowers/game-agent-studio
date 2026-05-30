# Game Agent Studio

基于多Agent架构的游戏开发平台，AI驱动的HTML5小游戏生成系统。

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![Vue3](https://img.shields.io/badge/Vue3-3.4-green)

## 项目简介

通过多个AI Agent分工协作（策划、美术、程序），自动生成HTML5小游戏原型。支持游戏创意生成、代码生成、预览测试等全流程。

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端 | Python、FastAPI、LangChain、LangGraph |
| 前端 | Vue3、HTML5 Canvas |
| AI模型 | DeepSeek、Qwen |
| 协议 | Function Calling、MCP |

## 功能特性

- 🎮 **多Agent协作** - 策划Agent、美术Agent、程序Agent分工协作
- 🎨 **AI创意生成** - 自动生成游戏创意和关卡设计
- 💻 **代码生成** - 基于LLM自动生成HTML5游戏代码
- 🔄 **实时预览** - 生成后立即预览测试

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 项目结构

```
game-agent-studio/
├── backend/          # FastAPI后端
│   ├── app/
│   │   ├── api/     # API路由
│   │   ├── core/    # 核心配置
│   │   └── services/# 业务逻辑
│   └── requirements.txt
├── frontend/         # Vue3前端
├── docs/             # 项目文档
└── README.md
```

## 作者

**张立** - AI应用开发工程师

- GitHub: [@lowers](https://github.com/lowers)
- 专注AI应用开发，擅长RAG、Agent、多Agent协作系统

## License

MIT License
