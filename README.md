# Image Recognition Skill

基于 OpenClaw 的图片内容识别 Skill，支持 OCR 文字提取、图像智能描述和批量处理。

## 功能特性

- **OCR 文字提取**：支持 Tesseract / PaddleOCR / EasyOCR 多引擎
- **图像内容描述**：支持 OpenAI / 通义千问 / Ollama 本地模型
- **批量处理**：支持文件夹批量处理，导出 JSON / Markdown / CSV / TXT
- **Claude 视觉回退**：脚本不可用时自动回退到 Claude 自带视觉能力

## 快速开始

### 安装依赖

```bash
# 基础依赖
pip install pillow

# OCR 引擎（三选一）
pip install pytesseract          # Tesseract（需额外安装二进制）
pip install paddleocr            # PaddleOCR（中文最优）
pip install easyocr              # EasyOCR（多语言支持）

# 图像描述（按需选择）
pip install openai               # OpenAI 兼容 API
pip install requests             # 通义千问 / Ollama
```

### 配置 API Key（可选）

```bash
# 通义千问（阿里云）
set DASHSCOPE_API_KEY=your-key

# OpenAI 或兼容 API
set OPENAI_API_KEY=your-key
set OPENAI_BASE_URL=https://api.openai.com/v1

# Ollama 本地服务
set OLLAMA_HOST=http://localhost:11434
```

## 使用示例

### 单张图片 OCR

```bash
python scripts/ocr_extract.py image.png
python scripts/ocr_extract.py image.png --engine paddleocr --json
```

### 单张图片描述

```bash
python scripts/image_describe.py image.png
python scripts/image_describe.py image.png --engine openai -p "提取图中所有文字"
```

### 批量处理

```bash
# 批量 OCR + 描述，输出 Markdown
python scripts/batch_process.py ./photos -o report.md --format markdown

# 仅 OCR，输出 CSV
python scripts/batch_process.py ./scans --task ocr -o data.csv --format csv

# 递归处理子目录
python scripts/batch_process.py ./album -r -o result.json
```

## 文件结构

```
image-recognition/
├── SKILL.md                      # Skill 定义文件
├── README.md                     # 项目说明
├── requirements.txt              # Python 依赖
├── .gitignore                    # Git 忽略规则
├── LICENSE                       # 开源许可证
└── scripts/
    ├── ocr_extract.py            # OCR 文字提取
    ├── image_describe.py         # 图像内容描述
    └── batch_process.py          # 批量处理
```

## 许可证

MIT License
