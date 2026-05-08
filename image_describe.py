#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像内容描述脚本
调用多模态大模型 API 对图片进行理解和描述
支持：OpenAI GPT-4V / Claude / 本地 Ollama 模型 / 其他兼容 OpenAI API 的模型
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
from pathlib import Path


def encode_image(image_path: str) -> tuple:
    """将图片编码为 base64，返回 (mime_type, base64_data)"""
    mime, _ = mimetypes.guess_type(image_path)
    if not mime:
        mime = "image/png"
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return mime, data


def describe_with_openai(image_path: str, prompt: str = None, api_key: str = None, base_url: str = None, model: str = "gpt-4o") -> dict:
    """使用 OpenAI 兼容 API 描述图片"""
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            base_url=base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )
        
        mime, b64 = encode_image(image_path)
        
        default_prompt = "请详细描述这张图片的内容，包括：画面主体、场景环境、文字内容（如有）、色彩风格、以及任何值得注意的细节。"
        user_prompt = prompt or default_prompt
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{b64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        return {
            "success": True,
            "engine": "openai",
            "model": model,
            "description": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    except ImportError:
        return {
            "success": False,
            "engine": "openai",
            "error": "openai package not installed. Run: pip install openai"
        }
    except Exception as e:
        return {"success": False, "engine": "openai", "error": str(e)}


def describe_with_ollama(image_path: str, prompt: str = None, model: str = "llava", host: str = None) -> dict:
    """使用本地 Ollama 模型描述图片"""
    try:
        import requests
        
        host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        default_prompt = "Describe this image in detail."
        user_prompt = prompt or default_prompt
        
        response = requests.post(
            f"{host}/api/generate",
            json={
                "model": model,
                "prompt": user_prompt,
                "images": [base64.b64encode(image_data).decode("utf-8")],
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        
        return {
            "success": True,
            "engine": "ollama",
            "model": model,
            "description": result.get("response", ""),
        }
    except ImportError:
        return {
            "success": False,
            "engine": "ollama",
            "error": "requests not installed. Run: pip install requests"
        }
    except Exception as e:
        return {"success": False, "engine": "ollama", "error": str(e)}


def describe_with_qwen(image_path: str, prompt: str = None, api_key: str = None) -> dict:
    """使用通义千问 VL 模型描述图片"""
    try:
        import requests
        
        api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            return {
                "success": False,
                "engine": "qwen-vl",
                "error": "DASHSCOPE_API_KEY not set"
            }
        
        mime, b64 = encode_image(image_path)
        
        default_prompt = "请详细描述这张图片的内容。"
        user_prompt = prompt or default_prompt
        
        response = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen-vl-plus",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime};base64,{b64}"}
                            }
                        ]
                    }
                ]
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        
        return {
            "success": True,
            "engine": "qwen-vl",
            "model": "qwen-vl-plus",
            "description": result["choices"][0]["message"]["content"]
        }
    except Exception as e:
        return {"success": False, "engine": "qwen-vl", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="图像内容描述")
    parser.add_argument("image", help="图片路径")
    parser.add_argument(
        "--engine",
        choices=["openai", "ollama", "qwen", "auto"],
        default="auto",
        help="描述引擎"
    )
    parser.add_argument("--prompt", "-p", help="自定义提示词")
    parser.add_argument("--model", help="模型名称")
    parser.add_argument("--api-key", help="API Key")
    parser.add_argument("--base-url", help="API Base URL")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--output", "-o", help="输出文件路径")
    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"Error: File not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    # 自动选择引擎
    engine = args.engine
    if engine == "auto":
        # 优先级：qwen -> openai -> ollama
        for candidate in ["qwen", "openai", "ollama"]:
            kwargs = {"image_path": args.image, "prompt": args.prompt}
            if candidate == "openai" and args.model:
                kwargs["model"] = args.model
            if candidate == "ollama" and args.model:
                kwargs["model"] = args.model
            result = globals()[f"describe_with_{candidate}"](**kwargs)
            if result["success"]:
                engine = candidate
                break
        else:
            result = {
                "success": False,
                "error": "No vision model available. Set DASHSCOPE_API_KEY, OPENAI_API_KEY, or run Ollama."
            }
    else:
        kwargs = {"image_path": args.image, "prompt": args.prompt}
        if args.api_key:
            kwargs["api_key"] = args.api_key
        if args.base_url:
            kwargs["base_url"] = args.base_url
        if args.model:
            kwargs["model"] = args.model
        result = globals()[f"describe_with_{engine}"](**kwargs)

    # 输出
    if args.json:
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        if result["success"]:
            output = result["description"]
        else:
            output = f"Error: {result.get('error', 'Unknown error')}"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Saved to: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
