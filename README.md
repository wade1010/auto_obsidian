# Auto Obsidian - AI学习笔记自动生成器

自动使用AI生成学习笔记，保存为Markdown格式到Obsidian，并自动提交到Git仓库。

## 功能特性

- **多种AI支持**: ChatGLM (智谱AI)、OpenAI、Claude
- **手动生成**: 输入主题即可生成详细的学习笔记
- **定时任务**: 支持每天、每小时、自定义间隔自动生成
- **批量生成**: 每次可生成多篇笔记
- **自动化流程**: 生成 → 保存 → Git提交 → 推送
- **图形界面**: 基于PyQt6的友好GUI界面

## 安装

### 1. 克隆或下载项目

```bash
cd auto_obsidian
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置系统

编辑 `config/config.yaml`，或使用GUI界面配置：

```yaml
ai:
  provider: "chatglm"  # 选择AI服务商
  api_key: "your-api-key"  # 填写API密钥
  model: "glm-4"  # 选择模型

obsidian:
  save_dir: "D:/my_notes/AI技术笔记"  # 笔记保存目录
```

## 使用方法

### 方式一：直接运行Python

```bash
python main.py
```

### 方式二：打包成EXE

```bash
# Windows
build.bat

# 或手动打包
pyinstaller build_spec.py
```

打包完成后，运行 `dist/AutoObsidian.exe`

## 配置说明

### AI配置

支持以下AI服务：

| 服务商 | provider | 模型示例 |
|--------|----------|----------|
| ChatGLM (智谱AI) | `chatglm` | glm-4, glm-4-plus, glm-4-flash |
| OpenAI | `openai` | gpt-4, gpt-3.5-turbo |

获取API Key:
- ChatGLM: https://open.bigmodel.cn/
- OpenAI: https://platform.openai.com/

### 定时任务配置

支持三种模式：
- **每天执行**: 每天在指定时间生成
- **每小时执行**: 每小时生成一次
- **自定义间隔**: 每N小时生成一次

### Git配置

自动执行以下操作：
```bash
git add .
git commit -m "docs: 自动生成AI学习笔记"
git push
```

请确保：
1. 保存目录是Git仓库
2. 已配置远程仓库
3. 已设置Git凭据

## 项目结构

```
auto_obsidian/
├── config/              # 配置文件
│   ├── config.yaml      # 主配置
│   └── topics.yaml      # 预设主题
├── src/                 # 核心模块
│   ├── ai_providers/    # AI提供者
│   ├── note_generator.py
│   ├── file_manager.py
│   ├── git_manager.py
│   └── scheduler.py
├── gui/                 # GUI界面
│   ├── main_window.py
│   ├── config_panel.py
│   ├── note_panel.py
│   └── scheduler_panel.py
├── main.py              # 程序入口
├── requirements.txt
└── build_spec.py        # 打包配置
```

## 注意事项

1. **API密钥安全**: 请妥善保管API密钥，不要泄露
2. **网络连接**: 需要稳定的网络连接访问AI服务
3. **Git配置**: 首次使用需配置Git用户信息和SSH密钥
4. **定时任务**: 程序需要保持运行状态才能执行定时任务

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
