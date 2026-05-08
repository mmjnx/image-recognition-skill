#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 文字提取脚本
支持：Tesseract (免费) / PaddleOCR (中文优化) / 云端 API (高精度)
"""

import argparse
import json
import os
import sys
from pathlib import Path


def extract_with_tesseract(image_path: str, lang: str = "chi_sim+eng") -> dict:
    """使用 Tesseract OCR 提取文字"""
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang=lang)
        return {
            "success": True,
            "engine": "tesseract",
            "text": text.strip(),
            "language": lang,
        }
    except ImportError:
        return {
            "success": False,
            "engine": "tesseract",
            "error": "pytesseract not installed. Run: pip install pytesseract pillow",
        }
    except Exception as e:
        return {"success": False, "engine": "tesseract", "error": str(e)}


def extract_with_paddleocr(image_path: str) -> dict:
    """使用 PaddleOCR 提取文字（中文场景更优）"""
    try:
        from paddleocr import PaddleOCR

        ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        result = ocr.ocr(image_path, cls=True)

        texts = []
        boxes = []
        if result and result[0]:
            for line in result[0]:
                if line:
                    bbox, (text, confidence) = line
                    texts.append(text)
                    boxes.append(
                        {
                            "text": text,
                            "confidence": float(confidence),
                            "bbox": bbox,
                        }
                    )

        return {
            "success": True,
            "engine": "paddleocr",
            "text": "\n".join(texts),
            "detailed": boxes,
        }
    except ImportError:
        return {
            "success": False,
            "engine": "paddleocr",
            "error": "paddleocr not installed. Run: pip install paddleocr",
        }
    except Exception as e:
        return {"success": False, "engine": "paddleocr", "error": str(e)}


def extract_with_easyocr(image_path: str, languages: list = None) -> dict:
    """使用 EasyOCR 提取文字"""
    try:
        import easyocr

        langs = languages or ["ch_sim", "en"]
        reader = easyocr.Reader(langs, gpu=False, verbose=False)
        result = reader.readtext(image_path)

        texts = []
        boxes = []
        for bbox, text, confidence in result:
            texts.append(text)
            boxes.append(
                {"text": text, "confidence": float(confidence), "bbox": bbox}
            )

        return {
            "success": True,
            "engine": "easyocr",
            "text": "\n".join(texts),
            "detailed": boxes,
        }
    except ImportError:
        return {
            "success": False,
            "engine": "easyocr",
            "error": "easyocr not installed. Run: pip install easyocr",
        }
    except Exception as e:
        return {"success": False, "engine": "easyocr", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="OCR 文字提取")
    parser.add_argument("image", help="图片路径")
    parser.add_argument(
        "--engine",
        choices=["tesseract", "paddleocr", "easyocr", "auto"],
        default="auto",
        help="OCR 引擎",
    )
    parser.add_argument(
        "--lang", default="chi_sim+eng", help="语言（tesseract 格式）"
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--output", "-o", help="输出文件路径")
    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"Error: File not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    # 自动选择引擎
    engine = args.engine
    if engine == "auto":
        # 优先尝试 paddleocr（中文好），然后 easyocr，最后 tesseract
        for candidate in ["paddleocr", "easyocr", "tesseract"]:
            if candidate == "tesseract":
                result = globals()[f"extract_with_{candidate}"](args.image, args.lang)
            else:
                result = globals()[f"extract_with_{candidate}"](args.image)
            if result["success"]:
                engine = candidate
                break
        else:
            result = {
                "success": False,
                "error": "No OCR engine available. Install one of: paddleocr, easyocr, pytesseract",
            }
    else:
        result = globals()[f"extract_with_{engine}"](args.image, args.lang)

    # 输出
    if args.json:
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        if result["success"]:
            output = result["text"]
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
