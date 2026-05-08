---
name: image-recognition
description: |
  图片内容识别与理解 Skill。支持 OCR 文字提取、图像内容描述、批量处理。
  触发场景：
  1. 用户要求识别图片中的文字（OCR）
  2. 用户要求描述/分析图片内容
  3. 用户要求提取图片信息、转录图片文字
  4. 用户要求批量处理图片文件夹
  5. 用户发送图片并询问"这是什么"、"图里有什么"
  6. 任何涉及图片内容理解、图像分析的需求
  compatibility: |
    Python 3.8+, 可选依赖：paddleocr/easyocr/pytesseract（OCR 三选一）,
    openai/requests（描述功能可选）。Claude 自带视觉能力可作为 fallback。
---

# Image Recognition Skill

图片内容识别与理解，提供 OCR 文字提取和图像智能描述两大核心能力。

## 执行策略（重要）

### 单张图片处理流程

当用户发送单张图片并要求识别/描述时，按以下优先级执行：

1. **Claude 自带视觉能力（首选）**
   - 直接读取图片文件，使用内置视觉模型分析
   - 优点：无需额外依赖，即时响应，对自然图像理解准确
   - 适用：内容描述、场景分析、文字较少的图片

2. **OCR 脚本（文字提取时）**
   - 当用户明确要求"提取文字"、"OCR"、"转录"时，尝试调用 `ocr_extract.py`
   - 如果引擎未安装，回退到 Claude 视觉能力读取文字

3. **批量处理脚本（文件夹时）**
   - 用户指定文件夹路径时，调用 `batch_process.py`
   - 如果依赖未安装，逐张使用 Claude 视觉能力处理

### 批量处理策略

- 少量图片（<10张）：直接用 Claude 视觉能力逐张分析
- 大量图片/需结构化输出：尝试脚本，失败则分批处理
- 用户要求特定格式（CSV/JSON）：优先脚本，或手动格式化输出

## 核心能力

### 1. OCR 文字提取 (`scripts/ocr_extract.py`)

从图片中提取文字，支持多引擎自动选择：

```bash
# 单张图片 OCR
python scripts/ocr_extract.py image.png

# 指定引擎
python scripts/ocr_extract.py image.png --engine paddleocr

# 输出 JSON（含置信度、位置信息）
python scripts/ocr_extract.py image.png --json

# 保存到文件
python scripts/ocr_extract.py image.png -o result.txt
```

**引擎优先级**（`--engine auto`）：
1. **PaddleOCR** — 中文场景最优，支持倾斜文字
2. **EasyOCR** — 多语言支持好，安装简单
3. **Tesseract** — 经典开源，需单独安装

**环境变量**：`TESSDATA_PREFIX`（Tesseract 语言包路径）

### 2. 图像内容描述 (`scripts/image_describe.py`)

调用多模态大模型理解图片内容：

```bash
# 基础描述
python scripts/image_describe.py image.png

# 自定义提示词
python scripts/image_describe.py image.png -p "提取图中的所有文字并翻译"

# 指定模型
python scripts/image_describe.py image.png --engine openai --model gpt-4o

# 使用本地 Ollama
python scripts/image_describe.py image.png --engine ollama --model llava
```

**支持的引擎**：
- **通义千问 VL** (`qwen`) — 中文理解强，需 `DASHSCOPE_API_KEY`
- **OpenAI 兼容** (`openai`) — GPT-4o 等，需 `OPENAI_API_KEY`
- **Ollama 本地** (`ollama`) — 免费本地运行，需提前 `ollama pull llava`

### 3. 批量处理 (`scripts/batch_process.py`)

批量处理文件夹内所有图片：

```bash
# 批量 OCR + 描述，输出 Markdown
python scripts/batch_process.py ./photos -o report.md --format markdown

# 仅 OCR，输出 CSV
python scripts/batch_process.py ./scans --task ocr -o data.csv --format csv

# 递归处理子目录
python scripts/batch_process.py ./album -r -o result.json
```

**输出格式**：`json`（完整数据） | `markdown`（阅读友好） | `txt`（纯文本） | `csv`（表格）

## 快速开始

### 安装依赖

根据需求选择安装：

```bash
# OCR 基础（推荐 PaddleOCR，中文最优）
pip install paddleocr paddlepaddle

# 或 EasyOCR（安装更简单）
pip install easyocr

# 或 Tesseract（需额外安装二进制）
pip install pytesseract pillow
# 并安装 Tesseract: https://github.com/UB-Mannheim/tesseract/wiki

# 图像描述（按需选择）
pip install openai          # OpenAI 兼容 API
pip install requests        # 通义千问 / Ollama
```

### 配置 API Key（可选）

```bash
# 通义千问（阿里云）
set DASHSCOPE_API_KEY=your-key

# OpenAI 或兼容 API
set OPENAI_API_KEY=your-key
set OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，用于第三方代理

# Ollama 本地服务
set OLLAMA_HOST=http://localhost:11434
```

## 使用模式

### 模式 A：用户上传单张图片（最常用）

**首选：Claude 自带视觉能力**

直接读取图片文件，分析后回复用户：

```
1. 使用 read 工具读取图片路径
2. 分析图片内容
3. 根据用户问题组织回答
```

**辅助：OCR 脚本（文字提取场景）**

当用户明确要求提取文字时，先尝试脚本，失败则回退到视觉能力：

- "提取图中文字" → 尝试 `ocr_extract.py` → 失败则用 Claude 读文字
- "描述这张图片" → 直接用 Claude 视觉能力
- "分析这张图" → 直接用 Claude 视觉能力 + 分析框架

### 模式 B：批量处理

用户指定文件夹时：

1. 先尝试 `batch_process.py`
2. 如果依赖未安装，使用 Claude 视觉能力逐张处理
3. 按用户要求的格式组织输出

### 模式 C：集成到工作流

脚本设计为命令行工具，可与其他工具链集成：

```bash
# 示例：监控文件夹自动 OCR
python scripts/ocr_extract.py input.png -o output.txt && cat output.txt | next-command
```

## 注意事项

1. **Claude 视觉能力优先**：单张图片直接读取分析，无需等待脚本安装
2. **中文 OCR**：优先使用 PaddleOCR，对中文排版、竖排文字支持更好
3. **手写识别**：PaddleOCR 手写模型需额外配置，或尝试 EasyOCR
4. **大图片**：超过 4096px 的图片建议先压缩，提升处理速度
5. **隐私敏感**：涉及隐私图片建议使用本地 Ollama 模型，不上传云端
6. **批量并发**：默认 4 线程，可通过 `--workers` 调整，注意 API 速率限制
7. **脚本 fallback**：当脚本不可用时，Claude 视觉能力是可靠后备方案

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| `paddleocr` 导入慢 | 首次使用会下载模型，等待完成即可 |
| Tesseract 找不到语言包 | 设置 `TESSDATA_PREFIX` 环境变量 |
| Ollama 连接失败 | 确认 `ollama serve` 已启动 |
| API 返回 429 | 降低 `--workers` 并发数，或升级套餐 |
| 图片格式不支持 | 转换为 PNG/JPG 后重试 |
