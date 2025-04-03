import requests
import json
import os
import time
import random
import base64
from urllib.parse import urlparse
import urllib3

class ChengyuCrawler:
    def __init__(self):
        # 禁用SSL警告
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 创建保存图片的目录
        self.save_dir = "chengyu_images"
        os.makedirs(self.save_dir, exist_ok=True)
        
        # 记录已下载的成语，避免重复
        self.downloaded_chengyu = set()
        
        # 请求头，从抓包记录中提取
        self.headers = {
            "host": "wq.maimaigou.com",
            "xweb_xhr": "1",
            "x-wx-id": "oH1oM4xF0paWeEzN5eQ0DsW-M-o8",  # 从抓包记录中获取
            "x-wx-skey": "to7Rvpwe7+uxz3/McfGmgQ==",    # 从抓包记录中获取
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 MicroMessenger/6.8.0(0x16080000) NetType/WIFI MiniProgramEnv/Mac MacWechat/WMPF MacWechat/3.8.6(0x13080610) XWEB/1156",
            "content-type": "application/json",
            "accept": "*/*",
            "sec-fetch-site": "cross-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://servicewechat.com/wxde8c5fa1fa1993ba/2/page-frame.html",
            "accept-encoding": "gzip",
            "accept-language": "zh-CN,zh;q=0.9"
        }
        
        # 用户信息，用于构造请求
        self.user_info = {
            "userId": "862647",
            "oid": "oH1oM4xF0paWeEzN5eQ0DsW-M-o8",
            "rid": -1,
            "scene": 1089,
            "source": "",
            "ver": "1.2.12"
        }
        
        # 当前能量值，模拟游戏状态
        self.energy = 995
        
        # 记录游戏时间
        self.start_app_time = int(time.time() * 1000) - 1200000  # 模拟已经使用了一段时间
    
    def get_app_time(self):
        """获取应用使用时间"""
        return int(time.time() * 1000) - self.start_app_time
    
    def get_game_time(self):
        """获取游戏时间，随机生成一个合理的值"""
        return random.randint(10000, 130000)
    
    def send_trace_request(self, event, level, path="pages/newGame/game", sub_event=""):
        """发送行为跟踪请求"""
        url = "https://wq.maimaigou.com/app/index.php?i=41&t=41&v=1.0.19&from=wxapp&c=entry&a=wxapp&do=trace&m=aaa_chengyu&sign=e322c6f34a3043589cd76ee6bc6265f0"
        
        # 构造请求体
        payload = {
            "traces": [{
                "event": event,
                "subEvent": sub_event,
                "appTime": self.get_app_time(),
                "gameTime": self.get_game_time() if event == "finish_game" else -1,
                "op_result": -1,
                "action": "trace",
                "path": path,
                "leftEnergy": self.energy
            }],
            "timestamp": int(time.time() * 1000),
            "scene": 1089,
            "source": "",
            "rid": -1,
            "userId": self.user_info["userId"],
            "oid": self.user_info["oid"],
            "ack": 1,
            "level": str(level),
            "sign": "a529ab1ea362345fcd9780372cd807b2",  # 固定签名，实际应该动态生成
            "ver": self.user_info["ver"]
        }
        
        try:
            # 添加当前时间戳到请求头
            self.headers["ct"] = str(int(time.time() * 1000))
            
            response = requests.post(url, headers=self.headers, json=payload, verify=False)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"发送trace请求出错: {e}")
            return None
    
    def get_level_data(self, level):
        """获取关卡数据"""
        url = f"https://wq.maimaigou.com/app/index.php?i=41&t=41&v=1.0.19&from=wxapp&c=entry&a=wxapp&do=gameLevel&m=aaa_chengyu&sign=f970afcd4fb4f0721bdc0e5a187f7b3a&level={level}&ver=1.2.12"
        
        try:
            # 添加当前时间戳到请求头
            self.headers["ct"] = str(int(time.time() * 1000))
            
            response = requests.get(url, headers=self.headers, verify=False)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"获取关卡数据出错: {e}")
            return None
    
    def download_image(self, url, chengyu, level):
        """下载成语图片"""
        try:
            # 创建关卡目录
            level_dir = os.path.join(self.save_dir, f"level_{level}")
            os.makedirs(level_dir, exist_ok=True)
            
            # 提取文件名
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            
            # 构造保存路径
            save_path = os.path.join(level_dir, f"{chengyu}_{filename}")
            
            # 检查文件是否已存在
            if os.path.exists(save_path):
                print(f"图片已存在: {save_path}")
                return True
            
            # 下载图片
            response = requests.get(url, verify=False)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                print(f"成功下载图片: {save_path}")
                return True
            
            print(f"下载图片失败: {url}")
            return False
        except Exception as e:
            print(f"下载图片出错: {e}")
            return False
    
    def simulate_game_completion(self, level):
        """模拟完成游戏"""
        # 1. 发送游戏完成请求
        self.send_trace_request("finish_game", level)
        time.sleep(random.uniform(0.5, 1.5))
        
        # 2. 发送页面卸载请求
        self.send_trace_request("page_unload", level)
        time.sleep(random.uniform(0.5, 1.5))
        
        # 3. 发送页面加载请求（结果页面）
        extra_data = {
            "level": str(level),
            "date": time.strftime("%Y%m%d"),
            "passTime": str(random.randint(300, 600))
        }
        self.send_trace_request(
            "page_load", 
            level, 
            path="pages/finish/finish", 
            sub_event=time.strftime("%Y%m%d%H%M%S")
        )
        
        # 减少能量值
        self.energy -= 1
        if self.energy < 990:
            self.energy = 995  # 模拟能量恢复
    
    def crawl_level(self, level):
        """爬取指定关卡的成语图片"""
        print(f"正在爬取第 {level} 关的成语图片...")
        
        # 获取关卡数据
        level_data = self.get_level_data(level)
        if not level_data or level_data.get("code") != 0:
            print(f"获取第 {level} 关数据失败")
            return False
        
        # 提取成语题目
        questions = level_data.get("data", {}).get("question", [])
        if not questions:
            print(f"第 {level} 关没有成语题目")
            return False
        
        success = True
        for question in questions:
            chengyu = question.get("answer", "")
            image_url = question.get("path", "")
            
            if not chengyu or not image_url:
                continue
            
            # 记录已下载的成语
            self.downloaded_chengyu.add(chengyu)
            
            # 下载图片
            if not self.download_image(image_url, chengyu, level):
                success = False
        
        # 模拟完成游戏
        self.simulate_game_completion(level)
        
        return success
    
    def run(self, start_level=1, end_level=100):
        """运行爬虫，爬取指定范围的关卡"""
        print(f"开始爬取成语图片，关卡范围: {start_level} - {end_level}")
        
        for level in range(start_level, end_level + 1):
            success = self.crawl_level(level)
            
            # 添加随机延迟，模拟真实用户行为
            delay = random.uniform(2.0, 5.0)
            print(f"等待 {delay:.2f} 秒后继续...")
            time.sleep(delay)
        
        print(f"\n爬取完成！共下载 {len(self.downloaded_chengyu)} 个成语图片")
        print(f"图片保存在: {os.path.abspath(self.save_dir)}")


if __name__ == "__main__":
    # 创建爬虫实例
    crawler = ChengyuCrawler()
    
    # 设置爬取的关卡范围
    start_level = 1
    end_level = 30
    
    # 运行爬虫
    crawler.run(start_level, end_level)