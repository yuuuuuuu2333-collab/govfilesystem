# 📊 智能瞭望数据分析处理系统

## 项目简介
“智能瞭望数据分析处理系统”是一个基于 Flask 框架开发的 Web 应用，旨在帮助用户进行数据采集、存储、AI 总结和报告生成。系统集成了百度搜索爬虫、数据仓库、AI 模型处理以及 PDF 报告导出等功能，为用户提供一站式的数据分析解决方案。

## 主要功能
*   **用户认证**：安全的登录和登出功能。
*   **数据采集**：通过关键词从百度等搜索引擎爬取相关数据（标题、URL、摘要）。
*   **数据仓库**：存储和管理已采集的数据，支持按关键词、日期范围进行筛选。
*   **AI 智能总结**：将选中的数据提交给 AI 模型（如 DeepSeek-R1）进行核心要点提炼和总结，生成简洁的报告。
*   **AI 报告管理**：查看所有生成的 AI 报告，并支持下载 PDF 格式的报告。
*   **响应式设计**：登录页已优化，适应不同屏幕尺寸的设备。

## 技术栈
*   **后端**：Python, Flask
*   **数据库**：SQLite3
*   **爬虫**：BeautifulSoup, requests
*   **AI 集成**：OpenAI API (通过 Siliconflow 平台调用 Qwen/DeepSeek-R1 模型)
*   **PDF 生成**：WeasyPrint
*   **前端**：HTML, CSS, JavaScript

## 安装与运行

### 1. 克隆仓库
```bash
git clone <您的仓库地址>
cd govfilesystem
```

### 2. 创建并激活虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或在 Windows 上: .\venv\Scripts\activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 初始化数据库
```bash
python3 init_db.py
```
这将创建 `database.db` 文件，并初始化 `users`, `crawled_data`, `ai_reports` 表，同时创建一个默认管理员用户 `admin`，密码为 `admin888`。

### 5. 配置 AI API 密钥
请确保您的环境中设置了 Qwen API 密钥。您可以在 `app.py` 中找到 `QWEN_API_KEY` 变量，并将其替换为您的实际密钥，或者通过环境变量设置。
```python
# app.py (示例)
QWEN_API_KEY = "sk-mkxlqmxarjfxxejptlrzyxhuiahzeghjgtkkyppruvjqtnxb" # 替换为您的实际密钥
```

### 6. 运行应用
```bash
python3 app.py
```
应用将在 `http://127.0.0.1:5001` 启动。

## 使用说明

### 1. 登录
访问 `http://127.0.0.1:5001`，使用默认账户 `admin` / `admin888` 登录。

### 2. 数据采集
在仪表盘页面，输入关键词，点击“提交”进行数据爬取。爬取结果将显示在搜索结果页。

### 3. 保存选中数据
在搜索结果页，勾选您感兴趣的数据，然后点击“保存选中数据”按钮，数据将存储到数据仓库。

### 4. 数据仓库
访问“数据仓库”页面，您可以查看所有已保存的数据，并可以根据关键词和日期进行筛选。

### 5. 提交给 AI 模型
在数据仓库页面，勾选您希望 AI 总结的数据，然后点击“提交给 AI 模型”按钮。AI 将对选中的数据进行总结，并生成一份报告。

### 6. AI 报告
访问“AI报告”页面，您可以查看所有 AI 生成的报告，并可以下载 PDF 格式的报告。

## 贡献
欢迎任何形式的贡献！如果您有任何建议或发现 Bug，请随时提出 Issue 或提交 Pull Request。
