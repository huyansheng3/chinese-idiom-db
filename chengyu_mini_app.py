import requests
import json
import os
import base64
import time
import random  # 添加random模块导入
from urllib.parse import urlparse
import urllib3

class ChengyuCrawler:
    def __init__(self):
        # 创建保存图片的目录
        self.save_dir = "chengyu_mini_app_images"
        os.makedirs(self.save_dir, exist_ok=True)
        
        # 更新请求头，使用最新的用户ID和密钥
        self.headers = {
            "host": "wq.maimaigou.com",
            "xweb_xhr": "1",
            "x-wx-id": "oH1oM4xF0paWeEzN5eQ0DsW-M-o8",  # 从请求记录中获取的最新ID
            "x-wx-skey": "to7Rvpwe7+uxz3/McfGmgQ==",    # 从请求记录中获取的最新密钥
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
        
        # 添加用户信息
        self.user_info = {
            "userId": "862647",
            "oid": "oH1oM4xF0paWeEzN5eQ0DsW-M-o8",
            "rid": -1,
            "scene": 1089,
            "source": "",
            "ver": "1.2.12"
        }
        
        # 已下载的成语集合，避免重复下载
        self.downloaded_chengyu = set()
        
        # 如果有记录文件，加载已下载的成语
        self.record_file = os.path.join(self.save_dir, "downloaded.txt")
        if os.path.exists(self.record_file):
            with open(self.record_file, "r", encoding="utf-8") as f:
                self.downloaded_chengyu = set(line.strip() for line in f)
    
    def save_image(self, url, chengyu):
        """下载并保存图片"""
        try:
            # 检查是否已下载
            if chengyu in self.downloaded_chengyu:
                print(f"成语 '{chengyu}' 已下载，跳过")
                return True
            
            # 下载图片，禁用SSL证书验证
            response = requests.get(url, headers=self.headers, verify=False)
            if response.status_code != 200:
                print(f"下载图片失败: {url}, 状态码: {response.status_code}")
                return False
            
            # 保存图片，使用成语作为文件名
            file_ext = os.path.splitext(urlparse(url).path)[1] or ".png"
            filename = f"{chengyu}{file_ext}"
            file_path = os.path.join(self.save_dir, filename)
            
            with open(file_path, "wb") as f:
                f.write(response.content)
            
            # 记录已下载的成语
            self.downloaded_chengyu.add(chengyu)
            with open(self.record_file, "a", encoding="utf-8") as f:
                f.write(f"{chengyu}\n")
            
            print(f"成功下载: {chengyu} -> {filename}")
            return True
        
        except Exception as e:
            print(f"下载 '{chengyu}' 时出错: {e}")
            return False
    
    def simulate_game_progress(self, level):
        """模拟游戏进度，发送trace请求以避免被检测为爬虫"""
        try:
            url = "https://wq.maimaigou.com/app/index.php?i=41&t=41&v=1.0.19&from=wxapp&c=entry&a=wxapp&do=trace&m=aaa_chengyu&sign=e322c6f34a3043589cd76ee6bc6265f0"
            
            # 模拟完成游戏的请求
            game_time = random.randint(10000, 130000)  # 随机游戏时间
            app_time = random.randint(1200000, 1300000)  # 随机应用时间
            left_energy = random.randint(990, 995)  # 随机剩余能量
            
            payload = {
                "traces": [{
                    "event": "finish_game",
                    "subEvent": "",
                    "gameTime": game_time,
                    "appTime": app_time,
                    "op_result": -1,
                    "action": "trace",
                    "path": "pages/newGame/game",
                    "leftEnergy": left_energy
                }],
                "timestamp": int(time.time() * 1000),
                "scene": 1089,
                "source": "",
                "rid": -1,
                "userId": self.user_info["userId"],
                "oid": self.user_info["oid"],
                "ack": 1,
                "level": str(level),
                "sign": self.generate_sign(level),  # 这里需要实现签名生成函数
                "ver": self.user_info["ver"]
            }
            
            response = requests.post(url, headers=self.headers, json=payload, verify=False)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    print(f"成功模拟完成关卡 {level}")
                    return True
            
            return False
        except Exception as e:
            print(f"模拟游戏进度时出错: {e}")
            return False
    
    def generate_sign(self, level):
        """生成请求签名（这里需要根据实际算法实现）"""
        # 这只是一个占位函数，实际上需要分析请求中签名的生成算法
        # 可能需要反向工程小程序代码或分析更多请求样本
        return "f55908" + ''.join(random.choices('0123456789abcdef', k=26))
    
    def crawl_level(self, level):
        """爬取指定关卡的成语图片"""
        # 先模拟游戏进度，增加真实性
        self.simulate_game_progress(level)
        
        url = f"https://wq.maimaigou.com/app/index.php?i=41&t=41&v=1.0.19&from=wxapp&c=entry&a=wxapp&do=gameLevel&m=aaa_chengyu&sign=f970afcd4fb4f0721bdc0e5a187f7b3a&level={level}&ver=1.2.12"
        
        try:
            # 禁用SSL证书验证，解决证书验证失败问题
            response = requests.get(url, headers=self.headers, verify=False)
            if response.status_code != 200:
                print(f"请求关卡 {level} 失败，状态码: {response.status_code}")
                return False
            
            data = response.json()
            if data.get("code") != 0 or "data" not in data:
                print(f"获取关卡 {level} 数据失败: {data.get('msg', '未知错误')}")
                return False
            
            # 提取成语和图片URL
            questions = data["data"].get("question", [])
            if not questions:
                print(f"关卡 {level} 没有成语数据")
                return False
            
            success_count = 0
            for q in questions:
                chengyu = q.get("answer", "")
                image_url = q.get("path", "")
                
                if not chengyu or not image_url:
                    continue
                
                if self.save_image(image_url, chengyu):
                    success_count += 1
                
                # 添加延迟，避免请求过快
                time.sleep(0.5)
            
            print(f"关卡 {level} 完成，成功下载 {success_count}/{len(questions)} 个成语图片")
            
            # 添加随机延迟，模拟真实用户行为
            time.sleep(random.uniform(0.8, 2.5))
            
            return True
        
        except Exception as e:
            print(f"爬取关卡 {level} 时出错: {e}")
            return False
    
    def run(self, start_level=1, end_level=100):
        """运行爬虫，爬取指定范围的关卡"""
        print(f"开始爬取成语图片，关卡范围: {start_level} - {end_level}")
        
        # 添加SSL警告过滤，避免大量警告信息
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        for level in range(start_level, end_level + 1):
            print(f"\n正在爬取关卡 {level}...")
            success = self.crawl_level(level)
            
            if not success:
                print(f"关卡 {level} 爬取失败，尝试继续下一关")
            
            # 关卡之间添加随机延迟，更像真实用户
            time.sleep(random.uniform(1.5, 4.0))
        
        print(f"\n爬取完成！共下载 {len(self.downloaded_chengyu)} 个成语图片")
        print(f"图片保存在: {os.path.abspath(self.save_dir)}")

# 运行爬虫
if __name__ == "__main__":
    crawler = ChengyuCrawler()
    # 可以根据需要调整爬取的关卡范围
    crawler.run(start_level=1, end_level=50)