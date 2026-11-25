<div align="center">

# 老年人回忆录 AI 助手

<p align="center">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/Python-3.10%2B-green.svg" alt="Python">
  <img src="https://github.com/beatricezhu6-byte/memoir/actions/workflows/verify.yml/badge.svg" alt="CI">
</p>

**口述人生故事，AI 整理成书。**

</div>

---

一个面向长者的回忆录工具：录音或打字讲述往事，AI 自动润色、分章节、配照片，最后导出成一本可打印的纪念册。本地运行，数据不上传。

## 功能

| 分类 | 能力 |
| --- | --- |
| 记录 | 语音口述、文字输入、老照片上传 |
| 整理 | AI 润色、标题生成、章节智能排序、大事年表 |
| 互动 | AI 陪伴对话、话题推荐、语音朗读 |
| 趣味 | 照片描述、年龄形象预测 |
| 输出 | 可打印的回忆录纪念册 |
| 分享 | 微信分享配置（见 `wechat-share-manual/`） |

## 快速开始

```powershell
git clone https://github.com/beatricezhu6-byte/memoir.git
cd memoir
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DASHSCOPE_KEY = "你的 DashScope API Key"
python app.py
```

启动后在浏览器打开 `http://localhost:8000`。Windows 下也可直接双击 `启动.bat`。

Docker 方式：

```bash
docker build -t memoir-assistant .
docker run --rm -p 8000:8000 -e DASHSCOPE_KEY="你的 Key" memoir-assistant
```

> 端口默认 8000，可通过环境变量 `MEMOIR_PORT` 修改。密钥只在环境变量里读取，仓库中不含任何 Key。

## 它怎么工作

浏览器前端把录音/文字送到 Flask 后端，后端调用 DashScope 的千问模型做识别、润色与生成，结果写进本地 `data/memoir.json`。没有数据库，所有数据留在你自己的电脑上。

```
浏览器 → Flask (app.py) → DashScope API → 本地 JSON
```

## 项目结构

```
.
├── app.py                 后端与全部 26 个 API 路由
├── dist/                  已构建前端，无需编译
├── deploy/                systemd / nginx / 环境变量样例
├── wechat-share-manual/   微信分享配置说明
├── LICENSE / NOTICE       开源许可与上游署名
└── 配置说明.txt           面向非技术用户的运行说明
```

## 配置与隐私

- 只需一个环境变量 `DASHSCOPE_KEY`，所有 AI 功能共用
- `uploads/`、`data/`、`audio/`、`images/` 含个人回忆数据，已加入 `.gitignore`
- 部署样例在 `deploy/`，正式使用前请按实际环境修改

## 技术栈

Python · Flask · DashScope（qwen-plus / qwen3-asr-flash / qwen-vl / qwen-image）· 原生前端

## 许可与致谢

Apache License 2.0。本项目基于 ModelScope 社区开源回忆录项目二次开发，详见 [NOTICE](NOTICE)。
