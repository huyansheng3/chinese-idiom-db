import json
import base64
import sys
import re

def decode_base64(base64_str):
    """解码base64字符串并返回JSON对象"""
    try:
        decoded = base64.b64decode(base64_str).decode('utf-8')
        return json.loads(decoded)
    except:
        return None

def is_important_operation(operation):
    """判断操作是否重要"""
    # 定义不重要的操作列表
    unimportant_operations = [
        'trace', 'inviteFriendListV2', 'shareVideoRule', 'getShareResult', 'tipNumber', 'info', 'moreGame', 'getEnergy', 'makeEnergy', 'moreGameConfig', 'shopConfig', 'showOffReport',
        'ShareAddEnergyStrategy', 'figureConfig'
    ]
    
    return operation not in unimportant_operations

def extract_key_info(api_data):
    """从API数据中提取关键信息"""
    result = []
    
    # 遍历每个API请求
    for item in api_data:
        if not isinstance(item, dict):
            continue
            
        # 提取操作类型
        path = item.get("path", "")
        operation = None
        if path:
            match = re.search(r'do=([^&]+)', path)
            if match:
                operation = match.group(1)
        
        # 跳过不重要的操作
        if operation and not is_important_operation(operation):
            continue
            
        # 基本请求信息
        req_info = {
            "url": item.get("url", ""),
            "method": item.get("method", ""),
            "time": item.get("time", ""),
            "status": item.get("result", ""),
            "action": operation
        }
        
        # 解析请求体
        if "base64" in item.get("req", {}):
            req_body = decode_base64(item["req"]["base64"])
            if req_body:
                req_info["request_data"] = req_body
        
        # 解析响应体
        if "base64" in item.get("res", {}):
            res_body = decode_base64(item["res"]["base64"])
            if res_body:
                req_info["response_data"] = res_body
        
        result.append(req_info)
    
    return result

def format_output(info_list):
    """格式化输出结果"""
    output = []
    
    for i, info in enumerate(info_list, 1):
        output.append(f"请求 {i}:")
        output.append(f"  URL: {info.get('url', '')}")
        output.append(f"  方法: {info.get('method', '')}")
        output.append(f"  操作: {info.get('action', 'N/A')}")
        output.append(f"  状态: {info.get('status', '')}")
        output.append(f"  耗时: {info.get('time', '')}ms")
        
        # 请求数据 - 保留完整数据
        if "request_data" in info:
            output.append("  请求数据:")
            req_data = json.dumps(info["request_data"], ensure_ascii=False, indent=2)
            output.append(f"    {req_data}")
        
        # 响应数据 - 保留完整数据
        if "response_data" in info:
            output.append("  响应数据:")
            res_data = json.dumps(info["response_data"], ensure_ascii=False, indent=2)
            output.append(f"    {res_data}")
        
        output.append("")
    
    return "\n".join(output)

def main(file_path):
    """主函数"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 尝试直接解析完整JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # 如果不是完整JSON，尝试提取JSON部分
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except:
                    print("无法解析文件内容")
                    return
            else:
                print("无法找到JSON数据")
                return
        
        key_info = extract_key_info(data)
        formatted_output = format_output(key_info)
        
        print(formatted_output)
        
        # 可选：将结果写入文件
        with open('api_summary.txt', 'w', encoding='utf-8') as f:
            f.write(formatted_output)
            
        print(f"结果已保存到 api_summary.txt")
        
    except Exception as e:
        print(f"处理文件时出错: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("请提供JSON文件路径")
        print("用法: python script.py mini_api.json")
