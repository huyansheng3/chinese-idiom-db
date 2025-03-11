import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

# 设置请求头，模拟浏览器
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 图片保存根目录
SAVE_DIR = 'chengyu_images'

# 确保根目录存在
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def clean_chengyu(text):
    """清理成语文本，去除空白字符"""
    return text.strip()

def read_chengyu_file(file_path):
    """从文件中读取成语列表"""
    chengyu_list = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            chengyu = clean_chengyu(line)
            if chengyu and not chengyu.startswith('...'):  # 跳过省略行
                chengyu_list.append(chengyu)
    return chengyu_list

def get_processed_chengyu():
    """获取已经处理过的成语列表"""
    processed = []
    if os.path.exists(SAVE_DIR):
        # 遍历根目录下的所有子目录，每个子目录名即为已处理的成语
        for item in os.listdir(SAVE_DIR):
            item_path = os.path.join(SAVE_DIR, item)
            if os.path.isdir(item_path):
                # 检查目录中是否有图片，如果有则认为已处理成功
                if any(file.endswith(('.jpg', '.jpeg', '.png')) for file in os.listdir(item_path)):
                    processed.append(item)
    return processed

def create_chengyu_dir(chengyu):
    """为成语创建目录"""
    dir_path = os.path.join(SAVE_DIR, chengyu)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path

def download_image(url, save_path):
    """下载图片并保存到指定路径"""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        return False
    except Exception as e:
        print(f"下载图片失败: {url}, 错误: {e}")
        return False

def get_baidu_images(chengyu, save_dir, max_images=5):
    """从百度图片获取成语相关图片，优先获取看图猜成语类图片"""
    # 使用更精确的搜索词，增加"看图猜成语"关键词
    search_terms = [
        f"{chengyu} 看图猜成语",
        f"{chengyu} 猜成语",
        f"{chengyu} 成语图片",
        f"{chengyu} 成语故事",
        chengyu  # 最后尝试直接搜索成语
    ]
    
    count = 0
    for search_term in search_terms:
        if count >= max_images:
            break
            
        encoded_term = quote(search_term)
        url = f"https://image.baidu.com/search/index?tn=baiduimage&word={encoded_term}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                continue
            
            # 使用正则表达式提取图片URL
            img_urls = re.findall(r'"thumbURL":"(.*?)"', response.text)
            
            for i, img_url in enumerate(img_urls[:max_images-count]):
                img_path = os.path.join(save_dir, f"baidu_{search_terms.index(search_term)}_{i+1}.jpg")
                if download_image(img_url, img_path):
                    count += 1
                    if count >= max_images:
                        break
                        
        except Exception as e:
            print(f"百度图片爬取失败: {search_term}, 错误: {e}")
            continue
            
    return count

def get_bing_images(chengyu, save_dir, max_images=5):
    """从必应图片获取成语相关图片，优先获取看图猜成语类图片"""
    # 使用更精确的搜索词，增加"看图猜成语"关键词
    search_terms = [
        f"{chengyu} 看图猜成语",
        f"{chengyu} 猜成语",
        f"{chengyu} 成语图片",
        f"{chengyu} 成语故事",
        chengyu  # 最后尝试直接搜索成语
    ]
    
    count = 0
    for search_term in search_terms:
        if count >= max_images:
            break
            
        encoded_term = quote(search_term)
        url = f"https://cn.bing.com/images/search?q={encoded_term}&form=HDRSC2&first=1"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            img_elements = soup.select('.mimg')
            
            for i, img in enumerate(img_elements[:max_images-count]):
                if 'src' in img.attrs:
                    img_url = img['src']
                    img_path = os.path.join(save_dir, f"bing_{search_terms.index(search_term)}_{i+1}.jpg")
                    if download_image(img_url, img_path):
                        count += 1
                        if count >= max_images:
                            break
                    
        except Exception as e:
            print(f"必应图片爬取失败: {search_term}, 错误: {e}")
            continue
            
    return count

def get_sogou_images(chengyu, save_dir, max_images=5):
    """从搜狗图片获取成语相关图片，优先获取看图猜成语类图片"""
    # 使用更精确的搜索词，增加"看图猜成语"关键词
    search_terms = [
        f"{chengyu} 看图猜成语",
        f"{chengyu} 猜成语",
        f"{chengyu} 成语图片",
        f"{chengyu} 成语故事",
        chengyu  # 最后尝试直接搜索成语
    ]
    
    count = 0
    for search_term in search_terms:
        if count >= max_images:
            break
            
        encoded_term = quote(search_term)
        url = f"https://pic.sogou.com/pics?query={encoded_term}&mode=1&start=0&reqType=ajax&reqFrom=result"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                continue
            
            # 使用正则表达式提取图片URL
            img_urls = re.findall(r'"thumbUrl":"(.*?)"', response.text)
            
            for i, img_url in enumerate(img_urls[:max_images-count]):
                img_path = os.path.join(save_dir, f"sogou_{search_terms.index(search_term)}_{i+1}.jpg")
                if download_image(img_url, img_path):
                    count += 1
                    if count >= max_images:
                        break
                    
        except Exception as e:
            print(f"搜狗图片爬取失败: {search_term}, 错误: {e}")
            continue
            
    return count

def is_relevant_image(img_path, chengyu):
    """判断图片是否与成语相关（简单实现，可以后续扩展）"""
    # 这里可以添加图像识别或OCR技术来判断图片是否相关
    # 简单实现：检查文件大小，太小的图片可能是无效的
    file_size = os.path.getsize(img_path)
    if file_size < 5000:  # 小于5KB的图片可能是无效的
        return False
    return True

def process_chengyu(chengyu):
    """处理单个成语，从多个来源爬取图片"""
    print(f"正在处理成语: {chengyu}")
    save_dir = create_chengyu_dir(chengyu)
    
    total_images = 0
    valid_images = 0
    
    # 从百度爬取图片
    baidu_count = get_baidu_images(chengyu, save_dir)
    total_images += baidu_count
    print(f"  - 百度图片: 获取了 {baidu_count} 张图片")
    
    # 随机延迟，避免请求过快
    time.sleep(random.uniform(1, 3))
    
    # 从必应爬取图片
    bing_count = get_bing_images(chengyu, save_dir)
    total_images += bing_count
    print(f"  - 必应图片: 获取了 {bing_count} 张图片")
    
    time.sleep(random.uniform(1, 3))
    
    # 从搜狗爬取图片
    sogou_count = get_sogou_images(chengyu, save_dir)
    total_images += sogou_count
    print(f"  - 搜狗图片: 获取了 {sogou_count} 张图片")
    
    # 过滤无关图片
    if total_images > 0:
        for file in os.listdir(save_dir):
            file_path = os.path.join(save_dir, file)
            if file.endswith(('.jpg', '.jpeg', '.png')):
                if is_relevant_image(file_path, chengyu):
                    valid_images += 1
                else:
                    os.remove(file_path)
                    print(f"  - 删除无关图片: {file}")
    
    print(f"成语 '{chengyu}' 处理完成，共获取 {total_images} 张图片，保留 {valid_images} 张相关图片")
    
    # 如果没有获取到任何相关图片，删除空目录
    if valid_images == 0:
        for file in os.listdir(save_dir):
            file_path = os.path.join(save_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(save_dir)
        print(f"  - 未获取到任何相关图片，已删除空目录")
    
    return valid_images

def main():
    # 读取成语文件
    chengyu_file = 'recommended_chengyu.txt'
    chengyu_list = read_chengyu_file(chengyu_file)
    
    # 获取已处理的成语列表
    processed_chengyu = get_processed_chengyu()
    print(f"已处理 {len(processed_chengyu)} 个成语")
    
    # 过滤出未处理的成语
    remaining_chengyu = [c for c in chengyu_list if c not in processed_chengyu]
    print(f"共读取到 {len(chengyu_list)} 个成语，还有 {len(remaining_chengyu)} 个成语需要处理")
    
    if not remaining_chengyu:
        print("所有成语已处理完毕！")
        return
    
    # 使用线程池并行处理剩余的成语
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(process_chengyu, remaining_chengyu))
    
    total_images = sum(results)
    print(f"爬取完成，共获取 {total_images} 张图片，覆盖 {sum(1 for r in results if r > 0)} 个成语")
    print(f"目前已处理成语总数: {len(processed_chengyu) + sum(1 for r in results if r > 0)}")

if __name__ == "__main__":
    main()
