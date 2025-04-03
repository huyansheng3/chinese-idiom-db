import re
import json
import binascii
import struct
from io import BytesIO

def extract_readable_text(data_str):
    """从数据字符串中提取可读的文本"""
    # 使用正则表达式匹配中文字符和常见的英文单词
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
    english_pattern = re.compile(r'[a-zA-Z]{3,}')
    
    chinese_matches = chinese_pattern.findall(data_str)
    english_matches = english_pattern.findall(data_str)
    
    return {
        "中文文本": chinese_matches,
        "英文文本": english_matches
    }

def try_decode_binary(data_str):
    """尝试将转义序列转换为二进制数据"""
    try:
        # 替换常见的转义序列
        binary_str = data_str.replace('\\u0000', '\x00')
        binary_str = re.sub(r'\\u([0-9a-fA-F]{4})', 
                           lambda m: chr(int(m.group(1), 16)), 
                           binary_str)
        
        # 只处理ASCII范围内的字符
        filtered_bytes = bytearray()
        for char in binary_str:
            if ord(char) < 256:  # 只保留可以用latin1编码的字符
                filtered_bytes.append(ord(char))
        
        return bytes(filtered_bytes)
    except Exception as e:
        print(f"二进制解码错误: {e}")
        return None

def extract_urls(data_str):
    """从数据中提取URL"""
    # 匹配URL模式
    url_pattern = re.compile(r'https?://[^\s\\\"\'\u0000-\u001F\u007F-\u009F]{10,}')
    urls = url_pattern.findall(data_str)
    
    # 清理URL，去除可能的二进制数据
    cleaned_urls = []
    for url in urls:
        # 在遇到转义字符或控制字符时截断URL
        clean_url = re.sub(r'[\\"\'\u0000-\u001F\u007F-\u009F].*$', '', url)
        if len(clean_url) > 10 and '.' in clean_url:  # 确保URL有效
            cleaned_urls.append(clean_url)
    
    return cleaned_urls

def analyze_binary_structure(binary_data):
    """分析二进制数据的结构"""
    if not binary_data:
        return {}
    
    result = {}
    
    # 检查文件头部特征
    if len(binary_data) >= 4:
        magic_bytes = binascii.hexlify(binary_data[:4]).decode('ascii')
        result["文件头"] = magic_bytes
    
    # 提取可能的字符串表
    strings = []
    current_string = ""
    for i, byte in enumerate(binary_data):
        if 32 <= byte <= 126:  # 可打印ASCII字符
            current_string += chr(byte)
        else:
            if current_string and len(current_string) >= 3:
                strings.append(current_string)
            current_string = ""
    
    if current_string and len(current_string) >= 3:
        strings.append(current_string)
    
    # 添加找到的字符串
    if strings:
        result["字符串表"] = strings
    
    # 查找可能的长度前缀结构
    length_prefixed_structures = []
    for i in range(len(binary_data) - 4):
        try:
            length = int.from_bytes(binary_data[i:i+2], byteorder='little')
            if 10 <= length <= 1000 and i + 2 + length <= len(binary_data):
                data = binary_data[i+2:i+2+length]
                # 检查数据是否包含可打印字符
                printable_chars = sum(1 for b in data if 32 <= b <= 126)
                if printable_chars > len(data) * 0.3:  # 至少30%是可打印字符
                    preview = ""
                    for b in data[:min(40, len(data))]:
                        if 32 <= b <= 126:
                            preview += chr(b)
                        else:
                            preview += "."
                    length_prefixed_structures.append({
                        "位置": i,
                        "长度": length,
                        "数据": preview
                    })
        except Exception:
            continue
    
    if length_prefixed_structures:
        result["长度前缀结构"] = length_prefixed_structures
    
    return result

def parse_data_chunk(data_chunk):
    """解析单个数据块"""
    data_str = data_chunk.get("data", "")
    
    # 提取可读文本
    readable_text = extract_readable_text(data_str)
    
    # 提取URL
    urls = extract_urls(data_str)
    
    # 尝试解码二进制数据
    binary_data = try_decode_binary(data_str)
    binary_analysis = {}
    if binary_data:
        binary_analysis = analyze_binary_structure(binary_data)
    
    # 构建结果
    result = {
        "可读文本": readable_text,
        "数据结构分析": {}
    }
    
    # 添加URL
    if urls:
        result["数据结构分析"]["URL"] = urls
    
    # 添加二进制分析
    if binary_analysis:
        result["二进制分析"] = binary_analysis
    
    return result

def print_data_chunk_result(index, result):
    """打印单个数据块的解析结果"""
    print(f"\n===== 数据块 #{index} =====")
    
    # 打印中文文本
    if result["可读文本"]["中文文本"]:
        print("\n中文文本:")
        for text in result["可读文本"]["中文文本"]:
            if len(text) > 0:
                print(f"- {text}")
    
    # 打印英文文本
    if result["可读文本"]["英文文本"]:
        print("\n英文文本:")
        for text in result["可读文本"]["英文文本"]:
            if len(text) > 0:
                print(f"- {text}")
    
    # 打印URL
    if "URL" in result["数据结构分析"]:
        print("\nURL:")
        for url in result["数据结构分析"]["URL"]:
            print(f"- {url}")
    
    # 打印二进制分析结果
    if "二进制分析" in result:
        print("\n二进制数据分析:")
        for key, value in result["二进制分析"].items():
            print(f"\n{key}:")
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            print(f"  - {k}: {v}")
                    else:
                        print(f"  - {item}")
            else:
                print(f"  {value}")

# 主函数
def main():
    # 将您提供的数据转换为列表格式
    data_chunks = []
    
    print("请将数据保存到data.txt文件中，每行一个data字段")
    print("例如: \"data\": \"瘌唩t狰\",")
    
    try:
        with open("data.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("\"data\""):
                    # 提取引号中的内容
                    match = re.search(r'"data": "(.*?)"', line)
                    if match:
                        data_chunks.append({"data": match.group(1)})
        
        # 逐个处理每个数据块
        for i, chunk in enumerate(data_chunks):
            result = parse_data_chunk(chunk)
            print_data_chunk_result(i+1, result)
            
    except FileNotFoundError:
        print("未找到data.txt文件，请先创建该文件并填入数据")
    except Exception as e:
        print(f"处理过程中出错: {e}")

# 示例使用
if __name__ == "__main__":
    main()