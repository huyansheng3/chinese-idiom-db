import os
import time
import random
import requests
import json
import re
import hashlib
from urllib.parse import urlparse
import concurrent.futures
from typing import Tuple, Optional, List, Dict, Set
from dataclasses import dataclass
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chengyu_crawler.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 常量定义
SAVE_DIR = "chengyu_images"
RECORD_FILE = "downloaded_idioms.txt"
HASH_FILE = "image_hashes.json"
REQUEST_TIMEOUT = 10  # 请求超时时间（秒）
MAX_WORKERS = 4  # 最大线程数

@dataclass
class ApiResult:
    """API结果数据类"""
    img_url: Optional[str]
    idiom: Optional[str]
    api_name: str
    success: bool = True

class ChengYuCrawler:
    """成语爬虫类"""
    
    def __init__(self):
        """初始化爬虫"""
        # 创建保存图片的目录
        os.makedirs(SAVE_DIR, exist_ok=True)
        
        # 初始化数据结构
        self.downloaded_idioms: Set[str] = set()
        self.image_hashes: Dict[str, Set[str]] = {}
        self.idiom_counts: Dict[str, int] = {}
        
        # 加载已有数据
        self._load_downloaded_idioms()
        self._load_image_hashes()
        self._initialize_idiom_counts()
        
        # 定义API函数列表
        self.api_functions = [
            (self.crawl_beichen_api, "北辰API"),
            (self.crawl_daxiong_api, "大熊API"),
            (self.crawl_lingku_api, "灵酷API"),
            (self.crawl_muming_api, "慕名API")
        ]
    
    def _load_downloaded_idioms(self) -> None:
        """加载已下载的成语记录"""
        if os.path.exists(RECORD_FILE):
            try:
                with open(RECORD_FILE, "r", encoding="utf-8") as f:
                    self.downloaded_idioms = set(line.strip() for line in f)
                logger.info(f"已加载 {len(self.downloaded_idioms)} 个已下载成语记录")
            except Exception as e:
                logger.error(f"加载成语记录失败: {e}")
                self.downloaded_idioms = set()
    
    def _load_image_hashes(self) -> None:
        """加载图片哈希记录"""
        if os.path.exists(HASH_FILE):
            try:
                with open(HASH_FILE, "r", encoding="utf-8") as f:
                    hash_data = json.load(f)
                    # 将字典中的列表转回集合
                    self.image_hashes = {idiom: set(hashes) for idiom, hashes in hash_data.items()}
                logger.info(f"已加载 {len(self.image_hashes)} 个成语的图片哈希记录")
            except Exception as e:
                logger.error(f"加载图片哈希记录失败: {e}")
                self.image_hashes = {}
    
    def _initialize_idiom_counts(self) -> None:
        """初始化成语计数"""
        for idiom in self.downloaded_idioms:
            # 计算当前成语的最大编号
            max_num = 0
            prefix = f"{idiom}_"
            for filename in os.listdir(SAVE_DIR):
                if filename.startswith(prefix):
                    try:
                        num = int(os.path.splitext(filename)[0].split('_')[1])
                        max_num = max(max_num, num)
                    except (IndexError, ValueError):
                        pass
            self.idiom_counts[idiom] = max_num
        logger.info(f"已初始化 {len(self.idiom_counts)} 个成语的计数")
    
    def record_idiom(self, idiom: str) -> None:
        """记录新下载的成语"""
        if idiom not in self.downloaded_idioms:
            self.downloaded_idioms.add(idiom)
            try:
                with open(RECORD_FILE, "a", encoding="utf-8") as f:
                    f.write(idiom + "\n")
            except Exception as e:
                logger.error(f"记录成语 '{idiom}' 失败: {e}")
    
    def save_image_hashes(self) -> None:
        """保存图片哈希记录"""
        try:
            # 将集合转换为列表以便JSON序列化
            serializable_hashes = {idiom: list(hashes) for idiom, hashes in self.image_hashes.items()}
            with open(HASH_FILE, "w", encoding="utf-8") as f:
                json.dump(serializable_hashes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存图片哈希记录失败: {e}")
    
    @staticmethod
    def calculate_image_hash(image_data: bytes) -> str:
        """计算图片的哈希值"""
        return hashlib.md5(image_data).hexdigest()
    
    @staticmethod
    def get_extension_from_url(url: str) -> str:
        """从URL中获取文件扩展名"""
        parsed = urlparse(url)
        path = parsed.path
        ext = os.path.splitext(path)[1].lower()
        
        # 处理常见图片格式
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        if not ext or ext not in valid_extensions:
            return '.jpg'  # 默认扩展名
        return ext
    
    def crawl_beichen_api(self) -> ApiResult:
        """北辰API爬取函数"""
        url = "https://api.txqq.pro/api/LookIdiom.php"
        api_name = "北辰API"
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                content = response.text
                # 提取图片URL
                img_match = re.search(r'±img=(.*?)±', content)
                if img_match:
                    img_url = img_match.group(1)
                    
                    # 提取成语
                    answer_match = re.search(r'答案：(.*?)\n', content)
                    if answer_match:
                        idiom = answer_match.group(1).strip()
                        return ApiResult(img_url, idiom, api_name)
            
            logger.warning(f"{api_name}请求失败: {response.status_code}")
            return ApiResult(None, None, api_name, False)
        except Exception as e:
            logger.error(f"{api_name}请求异常: {e}")
            return ApiResult(None, None, api_name, False)
    
    def crawl_daxiong_api(self) -> ApiResult:
        """大熊API爬取函数"""
        url = "http://tool.wyuuu.cn/api/kdiom.php"
        api_name = "大熊API"
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                content = response.text
                
                # 提取图片URL
                img_match = re.search(r'±img=(.*?)±', content)
                
                if img_match:
                    img_url = img_match.group(1)
                    
                    # 修改正则表达式以匹配实际返回格式
                    answer_match = re.search(r'答案：(.*?)(?:\n|$)', content)
                    if answer_match:
                        idiom = answer_match.group(1).strip()
                        return ApiResult(img_url, idiom, api_name)
            
            logger.warning(f"{api_name}请求失败: {response.status_code}")
            return ApiResult(None, None, api_name, False)
        except Exception as e:
            logger.error(f"{api_name}请求异常: {e}")
            return ApiResult(None, None, api_name, False)
    
    def crawl_lingku_api(self) -> ApiResult:
        """灵酷API爬取函数"""
        url = "https://api.ilingku.com/int/v1/ktccy"
        api_name = "灵酷API"
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 1:
                    img_url = data.get("imgurl")
                    idiom = data.get("answer")
                    return ApiResult(img_url, idiom, api_name)
            
            logger.warning(f"{api_name}请求失败: {response.status_code}")
            return ApiResult(None, None, api_name, False)
        except Exception as e:
            logger.error(f"{api_name}请求异常: {e}")
            return ApiResult(None, None, api_name, False)
    
    def crawl_muming_api(self) -> ApiResult:
        """慕名API爬取函数"""
        api_name = "慕名API"
        # 生成随机ID，模拟不同用户
        random_id = str(random.randint(10000000, 99999999))
        url = f"https://xiaoapi.cn/API/game_ktccy.php?msg=开始游戏&id={random_id}"
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    # 获取图片URL
                    img_url = data.get("data", {}).get("pic")
                    # 直接从第一次请求中获取答案
                    idiom = data.get("data", {}).get("answer")
                    if img_url and idiom:
                        return ApiResult(img_url, idiom, api_name)
            
            logger.warning(f"{api_name}请求失败: {response.status_code}")
            return ApiResult(None, None, api_name, False)
        except Exception as e:
            logger.error(f"{api_name}请求异常: {e}")
            return ApiResult(None, None, api_name, False)
    
    def download_image(self, img_url: str, idiom: str, api_name: str) -> bool:
        """下载图片"""
        if not img_url or not idiom:
            return False
        
        try:
            # 下载图片
            img_response = requests.get(img_url, timeout=REQUEST_TIMEOUT)
            if img_response.status_code != 200:
                logger.warning(f"图片下载失败: {img_response.status_code}")
                return False
            
            # 计算图片哈希值
            image_data = img_response.content
            image_hash = self.calculate_image_hash(image_data)
            
            # 初始化成语的哈希集合（如果不存在）
            if idiom not in self.image_hashes:
                self.image_hashes[idiom] = set()
                self.idiom_counts[idiom] = 0
            
            # 检查图片是否已存在（通过哈希值）
            if image_hash in self.image_hashes[idiom]:
                logger.info(f"成语 '{idiom}' 的图片已存在（相同哈希值），跳过")
                return False
            
            # 获取图片扩展名
            ext = self.get_extension_from_url(img_url)
            
            # 确定文件名
            if idiom not in self.downloaded_idioms:
                # 第一次下载这个成语，直接使用成语名
                filename = f"{idiom}{ext}"
                self.idiom_counts[idiom] = 0
            else:
                # 已有这个成语，使用编号
                self.idiom_counts[idiom] += 1
                filename = f"{idiom}_{self.idiom_counts[idiom]}{ext}"
            
            # 构建保存路径
            save_path = os.path.join(SAVE_DIR, filename)
            
            # 保存图片
            with open(save_path, "wb") as f:
                f.write(image_data)
            
            # 记录成语和图片哈希
            self.record_idiom(idiom)
            self.image_hashes[idiom].add(image_hash)
            self.save_image_hashes()
            
            logger.info(f"成功下载: {idiom} -> {save_path} (来源: {api_name})")
            return True
        except Exception as e:
            logger.error(f"下载图片异常: {e}")
            return False
    
    def crawl(self, target_count: int) -> None:
        """主爬取函数"""
        success_count = 0
        
        logger.info(f"开始爬取，目标数量: {target_count}")
        logger.info(f"已有成语数量: {len(self.downloaded_idioms)}")
        
        while success_count < target_count:
            # 使用线程池并发请求所有API
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # 提交所有API请求任务
                future_to_api = {executor.submit(func): name for func, name in self.api_functions}
                
                # 获取所有API的结果
                current_batch_success = 0
                for future in concurrent.futures.as_completed(future_to_api):
                    try:
                        result = future.result()
                        if result.success and result.img_url and result.idiom:
                            logger.info(f"从 {result.api_name} 获取到成语: {result.idiom}")
                            if self.download_image(result.img_url, result.idiom, result.api_name):
                                success_count += 1
                                current_batch_success += 1
                                logger.info(f"总进度: {success_count}/{target_count}")
                                
                                # 如果已达到目标数量，提前退出
                                if success_count >= target_count:
                                    break
                    except Exception as e:
                        api_name = future_to_api[future]
                        logger.error(f"{api_name} 执行异常: {e}")
            
            # 本轮没有成功下载任何图片时，增加等待时间
            if current_batch_success == 0:
                delay = random.uniform(4, 6)
                logger.info(f"本轮未获取到有效结果，等待 {delay:.2f} 秒...")
            else:
                delay = random.uniform(2, 4)
                logger.info(f"本轮成功获取 {current_batch_success} 个结果，等待 {delay:.2f} 秒...")
            
            time.sleep(delay)
        
        logger.info(f"爬取完成，共下载 {success_count} 个成语图片")

def main():
    """主函数"""
    try:
        crawler = ChengYuCrawler()
        target_count = int(input("请输入要爬取的成语数量: "))
        crawler.crawl(target_count)
    except KeyboardInterrupt:
        logger.info("用户中断爬取")
    except Exception as e:
        logger.error(f"程序异常: {e}")

if __name__ == "__main__":
    main() 