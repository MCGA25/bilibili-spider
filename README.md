# B站视频爬虫系统

一个基于Flask的Web应用，支持输入关键词自动搜索并下载B站视频。

## 功能特点

- 🎯 **关键词搜索**：支持输入多个关键词，按顺序优先级爬取
- 📥 **自动下载**：搜索到视频后自动下载到本地
- 🎨 **美观界面**：响应式设计，支持PC和移动设备
- 📁 **自定义路径**：支持指定视频保存路径
- 🎬 **视频管理**：只保留视频文件，自动清理音频和辅助文件
- 🔄 **多策略下载**：自动尝试不同的下载策略，提高下载成功率

## 技术栈

- **后端**：Python 3, Flask
- **前端**：HTML5, Tailwind CSS, JavaScript
- **爬虫**：requests, BeautifulSoup4, you-get
- **部署**：Vercel

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
python app.py
```

### 3. 访问应用

在浏览器中打开：http://127.0.0.1:5000

## 使用方法

1. **输入关键词**：在搜索框中输入关键词，多个关键词用空格或逗号分隔
2. **设置下载数量**：输入每个关键词的最大下载数量
3. **指定保存路径**：输入视频保存的本地路径
4. **点击下载**：系统会自动搜索并下载视频
5. **查看结果**：下载完成后会显示下载结果

## 项目结构

```
bilibili-spider/
├── app.py              # Flask应用主文件
├── bilibili_spider.py  # B站爬虫核心代码
├── requirements.txt    # 依赖包配置
├── .gitignore         # Git忽略文件
├── README.md          # 项目说明
├── templates/         # 前端模板
│   └── index.html     # 主页面
├── downloads/         # 默认下载目录
└── uploads/           # 上传目录
```

## 部署到Vercel

### 步骤1：创建GitHub仓库

1. 登录GitHub账号
2. 点击"New Repository"
3. 填写仓库名称（如 `bilibili-spider`）
4. 选择"Public"或"Private"
5. 点击"Create Repository"

### 步骤2：上传代码

```bash
# 初始化Git仓库
git init

# 添加文件
git add .

# 提交代码
git commit -m "Initial commit"

# 关联GitHub仓库
git remote add origin https://github.com/yourusername/bilibili-spider.git

# 推送代码
git push -u origin main
```

### 步骤3：部署到Vercel

1. 登录Vercel账号
2. 点击"New Project"
3. 选择"Import from Git Repository"
4. 选择刚刚创建的GitHub仓库
5. 点击"Import"
6. 配置部署选项：
   - **Framework Preset**: Flask
   - **Build Command**: 留空
   - **Output Directory**: 留空
   - **Root Directory**: 留空
7. 点击"Deploy"

### 步骤4：配置环境

部署完成后，Vercel会生成一个URL，您可以通过这个URL访问应用。

## 注意事项

1. **网络连接**：确保网络连接正常，尤其是访问B站的网络
2. **下载速度**：下载速度取决于网络状况和B站服务器响应
3. **文件大小**：视频文件可能较大，请确保磁盘空间充足
4. **使用规范**：请遵守B站的使用规范，不要滥用此工具
5. **仅供学习**：此项目仅供学习和研究使用

## 常见问题

### Q: 下载失败怎么办？
A: 系统会自动尝试不同的下载策略，如果所有策略都失败，会跳过此视频并继续下载其他视频。

### Q: 为什么只下载了部分视频？
A: 可能是因为网络问题、B站限制或视频格式不支持。系统会尽可能下载可用的视频。

### Q: 视频保存在哪里？
A: 默认保存在 `downloads` 目录，您也可以在界面上指定自定义路径。

### Q: 如何停止下载？
A: 在服务器端按 `Ctrl+C` 停止应用运行。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

---

**提示**：此项目仅供学习使用，请遵守相关法律法规。
