# 老年人回忆录 AI 助手

帮助用户通过文字和语音整理个人回忆录，并提供文字润色、章节管理、语音能力与图片相关功能。

## 本地启动

需要 Python 3.10 或更高版本，并准备 DashScope API 密钥。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DASHSCOPE_KEY = '你的 DashScope API Key'
python app.py
```

本地访问地址：<http://127.0.0.1:7860>

## Docker 启动

```powershell
docker build -t memoir-assistant .
docker run --rm -p 7860:7860 -e DASHSCOPE_KEY='你的 DashScope API Key' memoir-assistant
```

## 配置、数据与隐私

- 模型能力通过 `DASHSCOPE_KEY` 环境变量配置；不要把密钥写进文件或提交到 Git。
- 应用运行时会创建 `uploads/`、`data/`、`audio/`、`images/` 等目录，其中可能包含用户上传内容、音频和个人回忆录数据。
- 这些运行时数据已列入 `.gitignore`，应单独备份并控制访问权限。
- `wechat-share-manual/` 保存微信分享相关说明；部署时请按实际域名和配置检查。

## 目录说明

| 位置 | 用途 |
| --- | --- |
| `app.py` | Flask 服务和回忆录核心逻辑 |
| `dist/` | 已构建的前端资源 |
| `deploy/` | 部署参考 |
| `wechat-share-manual/` | 微信分享配置说明 |
| `Dockerfile` | 容器化运行配置 |

## 检查与发布

- `.github/workflows/verify.yml` 会在推送或创建合并请求时安装依赖并检查 Python 语法。
- 重要更新在 [CHANGELOG.md](CHANGELOG.md) 中记录，并在发布前创建可回退标签。
- 应用涉及个人回忆与音频等隐私内容，测试或截图前必须使用脱敏数据。
