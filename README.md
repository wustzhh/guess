# 猜人物游戏

一个基于 AI 对话的猜人物小游戏，支持 Web 端在线玩耍和历史战绩持久化存储。

## 文件说明

| 文件/目录 | 说明 |
|-----------|------|
| `server/` | Web 服务端（Flask + SQLite） |
| `server/app.py` | Flask 应用入口，路由、登录、游戏逻辑 |
| `server/game_engine.py` | 角色数据库 + 问答引擎 |
| `server/templates/` | HTML 页面模板 |
| `server/static/style.css` | 全局样式（暗色主题） |
| `server/server_data.db` | 服务端数据库（用户 + 对局记录，首次运行自动创建） |
| `game_db.py` | 命令行版数据库管理脚本（CLI 游戏用） |
| `game_stats.db` | 命令行版数据库 |
| `stats.html` | 命令行版战绩展示页 |
| `guess-character/` | Agent 技能文件夹，可安装到 `.agents/skills/` |
| `requirements.txt` | Python 依赖 |

## 部署到服务器

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 注册用户

```bash
python server/app.py --create-user 用户名 密码
```

默认管理员账号 `admin` / `admin123`（首次运行自动创建）。

### 3. 启动服务

```bash
# 开发模式
python server/app.py --debug

# 生产模式（监听所有网络）
python server/app.py --host 0.0.0.0 --port 5000
```

### 4. 访问

浏览器打开 `http://服务器IP:5000`，登录后即可开始游戏。

### 5. 生产部署建议

```bash
# 使用 gunicorn（需先安装: pip install gunicorn）
gunicorn -w 2 -b 0.0.0.0:5000 server.app:app
```

或配合 nginx/Caddy 做反向代理。

## 游戏玩法

1. 登录后点击"三国人物"开始游戏
2. 系统暗选一个三国角色
3. 你通过输入问题来缩小范围
4. 系统只回答 **是**、**不是**、**是也不是**（附简短解释）
5. 猜中或放弃后查看科普生平
6. 战绩自动保存，随时可在"战绩"页面查看

## 命令行版（通过 AI Agent 玩耍）

对 AI 说"猜三国人物"，AI 会加载技能陪你玩，并在每局结束后自动保存战绩到 `game_stats.db`，浏览器打开 `stats.html` 即可查看。

也可以通过命令行手动操作：

```bash
# 查看当前战绩
python game_db.py stats

# 手动生成 HTML 报告
python game_db.py export
```

## 技术栈

- **Python 3 + Flask**：Web 框架
- **SQLite**：轻量级本地数据库
- **werkzeug**：密码哈希
- **纯 HTML/CSS/JS**：前端无外部依赖
