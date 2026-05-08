#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量图片处理脚本
支持：批量 OCR、批量描述、结果导出为多种格式
"""

import argparse
import json
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入同级目录的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocr_extract import extract_with_paddleocr, extract_with_easyocr, extract_with_tesseract
from image_describe import describe_with_openai, describe_with_ollama, describe_with_qwen


def get_image_files(source: str, recursive: bool = False) -> list:
    """获取图片文件列表"""
    path = Path(source)
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    
    if path.is_file():
        return [str(path)] if path.suffix.lower() in image_extensions else []
    
    if path.is_dir():
        pattern = "**/*" if recursive else "*"
        return [
            str(f) for f in path.glob(pattern)
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
    
    return []


def process_single(args_tuple):
    """处理单张图片"""
    image_path, task, ocr_engine, describe_engine, prompt = args_tuple
    
    result = {"file": image_path, "task": task}
    
    try:
        if task in ("ocr", "both"):
            if ocr_engine == "auto":
                for candidate in ["paddleocr", "easyocr", "tesseract"]:
                    ocr_result = globals()[f"extract_with_{candidate}"](image_path)
                    if ocr_result["success"]:
                        break
            else:
                ocr_result = globals()[f"extract_with_{ocr_engine}"](image_path)
            result["ocr"] = ocr_result
        
        if task in ("describe", "both"):
            if describe_engine == "auto":
                for candidate in ["qwen", "openai", "ollama"]:
                    desc_result = globals()[f"describe_with_{candidate}"](image_path, prompt)
                    if desc_result["success"]:
                        break
            else:
                desc_result = globals()[f"describe_with_{describe_engine}"](image_path, prompt)
            result["describe"] = desc_result
            
    except Exception as e:
        result["error"] = str(e)
    
    return result


def export_results(results: list, output_path: str, fmt: str):
    """导出结果"""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    if fmt == "json":
        with open(output, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    elif fmt == "markdown":
        lines = ["# 图片识别结果\n"]
        for r in results:
            lines.append(f"## {Path(r['file']).name}\n")
            lines.append(f"**文件路径**: `{r['file']}`\n")
            
            if "ocr" in r and r["ocr"].get("success"):
                lines.append("### OCR 文字\n")
                lines.append(f"```\n{r['ocr']['text']}\n```\n")
            
            if "describe" in r and r["describe"].get("success"):
                lines.append("### 图像描述\n")
                lines.append(f"{r['describe']['description']}\n")
            
            if "error" in r:
                lines.append(f"**错误**: {r['error']}\n")
            
            lines.append("---\n")
        
        with open(output, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    
    elif fmt == "txt":
        lines = []
        for r in results:
            lines.append(f"===== {Path(r['file']).name} =====")
            
            if "ocr" in r and r["ocr"].get("success"):
                lines.append("[OCR]")
                lines.append(r["ocr"]["text"])
            
            if "describe" in r and r["describe"].get("success"):
                lines.append("[描述]")
                lines.append(r["describe"]["description"])
            
            lines.append("")
        
        with open(output, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    
    elif fmt == "csv":
        import csv
        with open(output, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["文件名", "文件路径", "OCR文字", "图像描述", "错误"])
            
            for r in results:
                ocr_text = r.get("ocr", {}).get("text", "") if r.get("ocr", {}).get("success") else ""
                desc_text = r.get("describe", {}).get("description", "") if r.get("describe", {}).get("success") else ""
                error = r.get("error", "")
                writer.writerow([
                    Path(r["file"]).name,
                    r["file"],
                    ocr_text,
                    desc_text,
                    error
                ])
    
    print(f"Results exported to: {output}")


def main():
    parser = argparse.ArgumentParser(description="批量图片处理")
    parser.add_argument("source", help="图片文件或目录路径")
    parser.add_argument(
        "--task",
        choices=["ocr", "describe", "both"],
        default="both",
        help="处理任务"
    )
    parser.add_argument("--ocr-engine", default="auto", help="OCR 引擎")
    parser.add_argument("--describe-engine", default="auto", help="描述引擎")
    parser.add_argument("--prompt", help="描述提示词")
    parser.add_argument("--recursive", "-r", action="store_true", help="递归子目录")
    parser.add_argument("--workers", "-w", type=int, default=4, help="并发数")
    parser.add_argument("--output", "-o", required=True, help="输出文件路径")
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "txt", "csv"],
        default="json",
        help="输出格式"
    )
    args = parser.parse_args()

    # 获取图片列表
    images = get_image_files(args.source, args.recursive)
    if not images:
        print("No image files found.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(images)} image(s) to process...")
    
    # 批量处理
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                process_single,
                (img, args.task, args.ocr_engine, args.describe_engine, args.prompt)
            ): img for img in images
        }
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"Processed: {Path(result['file']).name}")
    
    # 导出结果
    export_results(results, args.output, args.format)
    print(f"Done! Processed {len(results)} images.")


if __name__ == "__main__":
    main()
