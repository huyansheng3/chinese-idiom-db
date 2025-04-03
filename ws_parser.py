import json
import base64
import binascii
import struct
import sys
import time
import logging
import re
from typing import Dict, List, Any, Callable, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ws_parser")

def try_multiple_encodings(text: str) -> Dict[str, Any]:
    """
    尝试多种编码组合来解码文本
    """
    result = {
        "original": text,
        "decoded": None,
        "encoding_used": None
    }
    
    # 尝试的编码组合列表 (源编码, 目标编码)
    encoding_pairs = [
        ('gbk', 'utf-8'),       # GBK误解码为UTF-8的情况
        ('utf-8', 'gbk'),       # UTF-8误解码为GBK的情况
        ('big5', 'utf-8'),      # BIG5误解码为UTF-8的情况
        ('gb18030', 'utf-8'),   # GB18030误解码为UTF-8的情况
        ('utf-16', 'utf-8'),    # UTF-16误解码为UTF-8的情况
        ('utf-8', 'utf-16'),    # UTF-8误解码为UTF-16的情况
        ('latin1', 'utf-8'),    # Latin1误解码为UTF-8的情况
        ('utf-8', 'latin1')     # UTF-8误解码为Latin1的情况
    ]
    
    # 对于短文本，尝试直接解码
    if len(text) <= 5:
        try:
            # 尝试将文本视为十六进制字符串
            if all(c in '0123456789abcdefABCDEF' for c in text):
                try:
                    hex_bytes = bytes.fromhex(text)
                    for encoding in ['utf-8', 'gbk', 'gb18030', 'big5', 'utf-16', 'latin1']:
                        try:
                            decoded = hex_bytes.decode(encoding)
                            if any('\u4e00' <= char <= '\u9fff' for char in decoded):
                                result["decoded"] = decoded
                                result["encoding_used"] = f"hex->{encoding}"
                                return result
                        except:
                            continue
                except:
                    pass
        except:
            pass
    
    # 尝试各种编码组合
    for src_encoding, dst_encoding in encoding_pairs:
        try:
            # 尝试将文本编码为源编码字节序列
            src_bytes = text.encode(src_encoding, errors='ignore')
            
            # 然后以目标编码解码
            decoded = src_bytes.decode(dst_encoding, errors='ignore')
            
            # 检查解码结果是否包含中文
            if any('\u4e00' <= char <= '\u9fff' for char in decoded):
                result["decoded"] = decoded
                result["encoding_used"] = f"{src_encoding}->{dst_encoding}"
                return result
        except Exception:
            continue
    
    # 尝试直接解码二进制数据
    try:
        # 移除不可打印字符，保留可能的中文字符
        cleaned_text = ''.join(c for c in text if ord(c) > 127 or c.isprintable())
        if cleaned_text and cleaned_text != text:
            for encoding in ['utf-8', 'gbk', 'gb18030']:
                try:
                    decoded = cleaned_text.encode(encoding).decode('utf-8')
                    if any('\u4e00' <= char <= '\u9fff' for char in decoded):
                        result["decoded"] = decoded
                        result["encoding_used"] = f"cleaned->{encoding}->utf-8"
                        return result
                except:
                    continue
    except:
        pass
    
    # 尝试处理混合了转义字符的文本
    try:
        # 查找形如 \uXXXX 的Unicode转义序列
        unicode_pattern = r'\\u([0-9a-fA-F]{4})'
        if re.search(unicode_pattern, text):
            # 将 \uXXXX 转换为实际的Unicode字符
            decoded = re.sub(
                unicode_pattern,
                lambda m: chr(int(m.group(1), 16)),
                text
            )
            if any('\u4e00' <= char <= '\u9fff' for char in decoded):
                result["decoded"] = decoded
                result["encoding_used"] = "unicode_escape"
                return result
    except:
        pass
    
    return result

def extract_potential_chinese(data_str: str) -> List[Dict[str, Any]]:
    """
    从数据字符串中提取可能的中文文本段落并尝试多种编码解码
    """
    if not data_str:
        return []
    
    results = []
    
    # 使用正则表达式查找可能的中文字符序列和其他非ASCII字符
    # 这个模式匹配连续的非ASCII字符，包括更短的序列
    pattern = r'[^\x00-\x7F]{2,}'  # 至少2个连续的非ASCII字符
    matches = re.finditer(pattern, data_str)
    
    for match in matches:
        segment = match.group(0)
        # 尝试多种编码组合
        decode_result = try_multiple_encodings(segment)
        
        if decode_result["decoded"]:
            results.append({
                "original": segment,
                "decoded": decode_result["decoded"],
                "encoding_used": decode_result["encoding_used"],
                "position": match.span()
            })
    
    # 如果没有找到匹配，尝试处理整个字符串
    if not results and any(ord(c) > 127 for c in data_str):
        decode_result = try_multiple_encodings(data_str)
        if decode_result["decoded"]:
            results.append({
                "original": data_str,
                "decoded": decode_result["decoded"],
                "encoding_used": decode_result["encoding_used"],
                "position": (0, len(data_str))
            })
    
    # 尝试处理可能包含二进制数据的字符串
    if not results and '\u0000' in data_str:
        # 按空字符分割
        parts = data_str.split('\u0000')
        for part in parts:
            if part and any(ord(c) > 127 for c in part):
                decode_result = try_multiple_encodings(part)
                if decode_result["decoded"]:
                    results.append({
                        "original": part,
                        "decoded": decode_result["decoded"],
                        "encoding_used": decode_result["encoding_used"],
                        "position": (data_str.find(part), data_str.find(part) + len(part))
                    })
    
    return results

def parse_data_field(data_str: str) -> Dict[str, Any]:
    """
    直接解析data字段中的内容
    """
    if not data_str:
        return {"original": "", "decoded": None, "chinese_texts": []}
    
    result = {
        "original": data_str,
        "decoded": None,
        "chinese_texts": []
    }
    
    # 提取可能的中文文本并尝试多种编码解码
    chinese_texts = extract_potential_chinese(data_str)
    
    if chinese_texts:
        result["chinese_texts"] = chinese_texts
        
        # 将所有解码后的中文文本合并为一个字符串
        decoded_texts = [item["decoded"] for item in chinese_texts]
        result["decoded"] = " | ".join(decoded_texts)
    
    return result

def parse_ws_frame(frame: Dict[str, Any]) -> Dict[str, Any]:
    """解析单个WebSocket帧"""
    result = {
        "frameId": frame.get("frameId", "unknown"),
        "length": frame.get("length", 0),
        "opcode": frame.get("opcode", None),
        "mask": frame.get("mask", False),
        "time": frame.get("time", ""),
        "title": frame.get("title", "")
    }
    
    # 解析data字段
    data = frame.get("data", "")
    if data:
        data_analysis = parse_data_field(data)
        result["data_analysis"] = data_analysis
    
    # 解析base64字段
    base64_data = frame.get("base64", "")
    if base64_data:
        try:
            # 解码base64数据
            binary_data = base64.b64decode(base64_data)
            result["binary_length"] = len(binary_data)
            
            # 尝试解析二进制数据中的字符串
            try:
                # 尝试UTF-8解码
                utf8_text = binary_data.decode('utf-8', errors='ignore')
                if utf8_text.strip():
                    result["utf8_decoded"] = utf8_text
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"解析base64数据失败: {str(e)}")
    
    return result

def parse_ws_frames(ws_data: Any, progress_callback: Callable[[int, int], None] = None) -> List[Dict[str, Any]]:
    """解析WebSocket帧数据"""
    results = []
    
    # 检查数据结构
    if not ws_data:
        logger.warning("WebSocket数据为空")
        return results
    
    # 如果ws_data是列表但只有一个元素，且该元素包含frames字段
    if isinstance(ws_data, list) and len(ws_data) == 1 and "frames" in ws_data[0]:
        frames = ws_data[0]["frames"]
    elif isinstance(ws_data, list) and all(isinstance(item, dict) for item in ws_data):
        frames = ws_data
    else:
        logger.warning("无法识别的WebSocket数据结构")
        return results
    
    total_frames = len(frames)
    logger.info(f"开始解析 {total_frames} 个WebSocket帧...")
    
    for i, frame in enumerate(frames):
        try:
            if progress_callback:
                progress_callback(i + 1, total_frames)
            
            result = parse_ws_frame(frame)
            
            # 输出解析前后对比
            frame_id = result.get("frameId", f"unknown-{i}")
            logger.info(f"\n解析帧 {i+1}/{total_frames} (ID: {frame_id}):")
            
            data = frame.get("data", "")
            if data:
                logger.info(f"原始数据: {data[:100]}{'...' if len(data) > 100 else ''}")
                
                if "data_analysis" in result and result["data_analysis"].get("decoded"):
                    decoded = result["data_analysis"]["decoded"]
                    logger.info(f"解码结果: {decoded[:100]}{'...' if len(decoded) > 100 else ''}")
                    
                    # 输出中文文本对比
                    if result["data_analysis"].get("chinese_texts"):
                        logger.info("中文文本对比:")
                        for idx, text_item in enumerate(result["data_analysis"]["chinese_texts"], 1):
                            logger.info(f"  {idx}. 原文: {text_item['original']} -> 解码: {text_item['decoded']} (使用编码: {text_item.get('encoding_used', 'unknown')})")
                else:
                    logger.info("未找到可解码的中文内容")
            else:
                logger.info(f"无data数据")
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"解析帧 {i} 时出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            results.append({
                "frameId": frame.get("frameId", f"unknown-{i}"),
                "error": str(e)
            })
    
    return results

def print_progress(current, total):
    """打印进度条"""
    bar_length = 40
    progress = current / total
    block = int(round(bar_length * progress))
    progress_str = "[{0}] {1}/{2} ({3:.1f}%)".format(
        "#" * block + "-" * (bar_length - block), 
        current, total, 
        progress * 100
    )
    sys.stdout.write("\r" + progress_str)
    sys.stdout.flush()
    if current == total:
        print("\n")

def save_results(results: List[Dict[str, Any]], output_file: str):
    """保存结果到文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"解析结果已保存到: {output_file}")

def main(input_file: str, output_file: str = None):
    """主函数"""
    try:
        logger.info(f"开始处理WebSocket数据文件: {input_file}")
        start_time = time.time()
        
        # 读取输入文件
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.info(f"已读取文件, 大小: {len(content)/1024:.2f} KB")
            
            try:
                # 尝试解析为JSON
                ws_data = json.loads(content)
                logger.info(f"成功加载JSON数据")
                
                # 解析WebSocket帧
                results = parse_ws_frames(ws_data, progress_callback=print_progress)
                
                if not results:
                    logger.warning("未解析到任何WebSocket帧数据")
                    return
                
                # 找到包含礼包信息的帧
                gift_frames = []
                for result in results:
                    if "data_analysis" in result and "decoded" in result["data_analysis"]:
                        decoded = result["data_analysis"]["decoded"]
                        if decoded and "礼包" in decoded:
                            gift_frames.append(result)
                
                end_time = time.time()
                total_time = end_time - start_time
                logger.info(f"解析完成！共 {len(results)} 个帧，其中 {len(gift_frames)} 个帧包含礼包信息，总耗时: {total_time:.2f}秒")
                
                # 打印礼包信息
                if gift_frames:
                    logger.info("\n礼包信息摘要:")
                    for idx, frame in enumerate(gift_frames, 1):
                        logger.info(f"\n-- 礼包帧 {idx}/{len(gift_frames)} --")
                        logger.info(f"帧ID: {frame['frameId']}")
                        logger.info(f"长度: {frame.get('length', 0)} 字节")
                        logger.info(f"解码结果: {frame['data_analysis']['decoded']}")
                
                # 保存结果到文件
                if output_file:
                    logger.info(f"正在保存详细解析结果到: {output_file}")
                    save_results(results, output_file)
                
            except json.JSONDecodeError as e:
                logger.error(f"解析JSON失败: {str(e)}")
                return
    
    except Exception as e:
        logger.error(f"处理文件时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python ws_parser.py 输入文件 [输出文件]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    main(input_file, output_file)