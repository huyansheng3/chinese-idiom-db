import requests
import os
import time
import json
import random
import hashlib
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ChengyuCrawler:
    """看图猜成语小游戏爬虫 - 完全基于mini_api.json的API格式"""
    
    def __init__(self):
        # 创建保存图片的目录
        self.save_dir = "chengyu_mini_app_images"
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            
        # 创建元数据目录，用于保存成语释义等信息
        self.meta_dir = os.path.join(self.save_dir, "metadata")
        if not os.path.exists(self.meta_dir):
            os.makedirs(self.meta_dir)
            
        # 基础URL和参数 - 完全基于抓包数据
        self.base_url = "https://wq.maimaigou.com/app/index.php"
        self.common_params = {
            "i": "41",
            "t": "41",
            "v": "1.0.19",
            "from": "wxapp", 
            "c": "entry",
            "a": "wxapp",
            "m": "aaa_chengyu",
            "ver": "1.2.12"
        }
        
        # 完全匹配抓包中的请求头格式
        self.headers = {
            "host": "wq.maimaigou.com",
            "xweb_xhr": "1",
            "x-wx-id": "",  # 将在运行时更新
            "x-wx-skey": "",  # 将在运行时更新
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 MicroMessenger/6.8.0(0x16080000) NetType/WIFI MiniProgramEnv/Mac MacWechat/WMPF MacWechat/3.8.6(0x13080610) XWEB/1156",
            "ct": "",  # 将在每次请求时更新
            "content-type": "application/json",
            "accept": "*/*",
            "sec-fetch-site": "cross-site",
            "sec-fetch-mode": "cors", 
            "sec-fetch-dest": "empty",
            "referer": "https://servicewechat.com/wxde8c5fa1fa1993ba/2/page-frame.html",
            "accept-encoding": "gzip",
            "accept-language": "zh-CN,zh;q=0.9"
        }
        
        # 使用会话保持cookie
        self.session = requests.Session()
        
        # 已下载的成语集合，避免重复
        self.downloaded_chengyu = set()
        
        # 游戏状态信息
        self.current_level = 1
        self.user_id = ""
        self.max_retries = 3
        
        # 凭证文件
        self.credentials_file = "wx_credentials.json"
        self.load_wx_credentials()
        
    def load_wx_credentials(self):
        """加载保存的微信凭证"""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, "r", encoding="utf-8") as f:
                    credentials = json.load(f)
                    
                self.headers["x-wx-id"] = credentials.get("wx_id", "")
                self.headers["x-wx-skey"] = credentials.get("wx_skey", "")
                print(f"已从文件加载微信凭证: ID={self.headers['x-wx-id']}")
                return True
            return False
        except Exception as e:
            print(f"加载微信凭证失败: {e}")
            return False
            
    def save_wx_credentials(self, wx_id, wx_skey):
        """保存微信凭证到文件"""
        try:
            credentials = {
                "wx_id": wx_id,
                "wx_skey": wx_skey,
                "update_time": time.time()
            }
            
            with open(self.credentials_file, "w", encoding="utf-8") as f:
                json.dump(credentials, f, ensure_ascii=False, indent=2)
                
            print("微信凭证已保存到文件")
            return True
        except Exception as e:
            print(f"保存微信凭证失败: {e}")
            return False
    
    def set_wx_credentials(self, wx_id, wx_skey):
        """设置微信凭证"""
        self.headers["x-wx-id"] = wx_id
        self.headers["x-wx-skey"] = wx_skey
        
        # 保存凭证到文件
        self.save_wx_credentials(wx_id, wx_skey)
    
    def generate_sign(self, params):
        """
        生成请求签名 - 根据抓包数据和微信小程序惯例
        签名通常是对所有参数按字母排序后拼接，再加上密钥后计算MD5
        """
        # 按字母顺序排序参数
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        
        # 构建参数字符串
        param_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        # 添加密钥 (通常是小程序的AppSecret或者自定义字符串)
        secret_key = "aaa_chengyu_token"  # 猜测的密钥，实际可能不同
        sign_str = param_str + secret_key
        
        # 计算MD5
        sign = hashlib.md5(sign_str.encode()).hexdigest()
        return sign
    
    def make_request(self, action, extra_params=None, method="GET", data=None):
        """发送请求到服务器 - 完全匹配抓包格式"""
        # 构建请求参数
        params = self.common_params.copy()
        params["do"] = action
        
        if extra_params:
            params.update(extra_params)
        
        # 更新时间戳 - 确保与抓包格式一致
        current_time = str(int(time.time() * 1000))
        self.headers["ct"] = current_time
        
        # 生成签名
        params["sign"] = self.generate_sign(params)
        
        # 打印详细信息便于调试
        if action == "login":
            print(f"\n请求URL: {self.base_url}")
            print(f"请求参数: {params}")
            print(f"x-wx-id: {self.headers['x-wx-id']}")
            print(f"x-wx-skey: {self.headers['x-wx-skey']}")
        
        # 尝试发送请求
        retries = 0
        while retries < self.max_retries:
            try:
                if method.upper() == "GET":
                    response = self.session.get(
                        self.base_url, 
                        params=params, 
                        headers=self.headers, 
                        verify=False,
                        timeout=10
                    )
                else:  # POST
                    response = self.session.post(
                        self.base_url, 
                        params=params, 
                        headers=self.headers, 
                        json=data,
                        verify=False,
                        timeout=10
                    )
                
                response.raise_for_status()
                
                # 尝试解析JSON响应
                try:
                    result = response.json()
                    if action == "login":
                        print(f"响应状态码: {response.status_code}")
                        print(f"响应内容: {response.text[:300]}")
                    
                    if result.get("code") != 0:
                        error_msg = result.get("msg", "未知错误")
                        print(f"请求失败，错误码: {result.get('code')}, 消息: {error_msg}")
                        
                        # 特别处理微信验证失败的情况
                        if result.get("code") == 202:
                            print("微信验证失败 - 可能需要更新凭证")
                            return None
                    
                    return result
                except json.JSONDecodeError:
                    print(f"无法解析JSON响应: {response.text[:100]}...")
                    return None
                    
            except requests.exceptions.RequestException as e:
                retries += 1
                wait_time = 2 ** retries
                print(f"请求失败 ({retries}/{self.max_retries}): {e}")
                print(f"{wait_time}秒后重试...")
                time.sleep(wait_time)
        
        print(f"请求 {action} 失败，已达到最大重试次数")
        return None
    
    def login(self):
        """登录获取用户信息"""
        print("开始登录...")
        
        # 登录请求 - 完全基于抓包数据
        login_result = self.make_request("login", extra_params={"platform": "mac", "wxVersion": "3.8.6"})
        
        if login_result and login_result.get("code") == 0:
            user_info = login_result.get("data", {}).get("userInfo", {})
            self.user_id = user_info.get("id", "")
            self.house_level = user_info.get("houseLevel", 0)
            self.house_name = user_info.get("houseName", "")
            
            print(f"登录成功！用户ID: {self.user_id}")
            print(f"当前房屋等级: {self.house_level} ({self.house_name})")
            return True
        elif login_result and login_result.get("code") == 202:
            print("\n========================")
            print("微信验证失败！")
            print("原因: 您的微信凭证已过期或无效")
            print("解决方法:")
            print("1. 使用Charles/Fiddler等抓包工具")
            print("2. 打开微信小程序「看图猜成语」")
            print("3. 找到发往 wq.maimaigou.com 的请求")
            print("4. 从请求头中复制 x-wx-id 和 x-wx-skey 的值")
            print("5. 重新运行此脚本并输入这些值")
            print("========================\n")
            return False
        else:
            error_code = login_result.get("code", "未知") if login_result else "未知"
            error_msg = login_result.get("msg", "未知错误") if login_result else "未知错误"
            print(f"登录失败，错误码: {error_code}, 消息: {error_msg}")
            return False
    
    def init_game(self):
        """初始化游戏环境"""
        print("初始化游戏环境...")
        
        # 获取声音配置
        sound_config = self.make_request("soundConfig")
        if sound_config and sound_config.get("code") == 0:
            print("成功获取声音配置")
        
        # 获取统计配置
        ald_config = self.make_request("aldConfig")
        if ald_config and ald_config.get("code") == 0:
            print("成功获取统计配置")
            
        # 获取热门词
        hot_word = self.make_request("hotWord")
        if hot_word and hot_word.get("code") == 0:
            print("成功获取热门词配置")
            
        # 获取新手引导
        guide_list = self.make_request("guideList")
        if guide_list and guide_list.get("code") == 0:
            print("成功获取新手引导")
            
        # 获取关卡预览
        preview_level = self.make_request("previewLevel")
        if preview_level and preview_level.get("code") == 0:
            print("成功获取关卡预览")
        
        # 上传表单ID - 模拟小程序行为
        self.upload_form_id()
        
        print("游戏环境初始化完成")
        return True
    
    def get_current_level_data(self, level=None):
        """获取当前关卡数据"""
        target_level = level if level is not None else self.current_level
        print(f"获取第{target_level}关数据...")
        
        # 根据抓包格式请求关卡数据
        level_data = self.make_request("gameLevel", extra_params={"level": target_level})
        
        if level_data and level_data.get("code") == 0:
            return level_data.get("data", {})
        else:
            print("获取关卡数据失败")
            return None
    
    def upload_form_id(self):
        """上传表单ID - 模拟小程序行为"""
        # 构建形如抓包中的formId
        form_id = f"requestFormId:fail deprecated"
        extra_params = {
            "formId": form_id,
            "userId": self.user_id
        }
        
        result = self.make_request("uploadFormId", extra_params=extra_params)
        return result and result.get("code") == 0
    
    def download_image(self, image_url, chengyu, level, index):
        """下载图片并保存"""
        print(f"下载图片: {chengyu}")
        
        # 检查是否已下载
        if chengyu in self.downloaded_chengyu:
            print(f"成语 '{chengyu}' 已下载，跳过")
            return True
        
        try:
            # 发送请求下载图片
            response = requests.get(image_url, timeout=10, verify=False)
            response.raise_for_status()
            
            # 创建当前关卡目录
            level_dir = os.path.join(self.save_dir, f"level_{level}")
            if not os.path.exists(level_dir):
                os.makedirs(level_dir)
            
            # 保存图片
            file_name = f"{level}_{index}_{chengyu}.jpg"
            file_path = os.path.join(level_dir, file_name)
            
            with open(file_path, "wb") as f:
                f.write(response.content)
            
            print(f"图片已保存: {file_path}")
            
            # 添加到已下载集合
            self.downloaded_chengyu.add(chengyu)
            return True
            
        except Exception as e:
            print(f"下载图片失败: {e}")
            return False
    
    def save_metadata(self, level_data, level):
        """保存成语相关的元数据"""
        try:
            # 创建元数据目录
            level_meta_dir = os.path.join(self.meta_dir, f"level_{level}")
            if not os.path.exists(level_meta_dir):
                os.makedirs(level_meta_dir)
            
            # 保存成语元数据
            idioms = level_data.get("idioms", [])
            metadata = {
                "level": level,
                "idioms": idioms,
                "timestamp": time.time(),
                "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            file_path = os.path.join(level_meta_dir, f"level_{level}_metadata.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"元数据已保存: {file_path}")
            return True
        except Exception as e:
            print(f"保存元数据失败: {e}")
            return False
    
    def pass_level(self, level):
        """模拟通过关卡"""
        print(f"尝试通过第{level}关...")
        
        # 模拟游戏时间 - 不宜太短
        pass_time = random.randint(15, 60)
        
        # 根据抓包格式构建请求参数
        extra_params = {
            "level": level,
            "passTime": pass_time,
            "code": "0", # 验证码，通常是0或者其他值
            "platform": "mac", 
            "wxVersion": "3.8.6"
        }
        
        result = self.make_request("pass", extra_params=extra_params)
        
        if result and result.get("code") == 0:
            print(f"成功通过第{level}关！")
            
            # 上传表单ID - 模拟小程序行为
            self.upload_form_id()
            
            # 提取并打印升级信息
            upgrade_info = result.get("data", {}).get("upgrade", False)
            upgrade_tip = result.get("data", {}).get("tip", "")
            
            if upgrade_info:
                print(f"恭喜！您的房屋已升级！")
            
            if upgrade_tip:
                print(f"提示: {upgrade_tip}")
                
            return True
        else:
            error_code = result.get("code", "未知") if result else "未知"
            error_msg = result.get("msg", "未知错误") if result else "请求失败"
            print(f"通过关卡失败，错误码: {error_code}, 消息: {error_msg}")
            return False
    
    def crawl_as_player(self, start_level=1):
        """模拟玩家方式爬取成语"""
        print(f"准备从第{start_level}关开始爬取...")
        
        # 登录游戏
        if not self.login():
            print("登录失败，无法继续爬取")
            return False
        
        # 初始化游戏环境
        if not self.init_game():
            print("初始化游戏环境失败，无法继续爬取")
            return False
        
        # 设置起始关卡
        self.current_level = start_level
        
        # 开始爬取循环
        crawl_count = 0
        fail_count = 0
        
        while True:
            try:
                # 获取当前关卡数据
                level_data = self.get_current_level_data(self.current_level)
                
                if not level_data:
                    fail_count += 1
                    if fail_count >= 3:
                        print(f"连续{fail_count}次获取关卡数据失败，停止爬取")
                        break
                    print(f"获取第{self.current_level}关数据失败，稍后重试...")
                    time.sleep(5)
                    continue
                
                # 重置失败计数
                fail_count = 0
                
                # 保存成语元数据
                self.save_metadata(level_data, self.current_level)
                
                # 下载成语图片
                idioms = level_data.get("idioms", [])
                if not idioms:
                    print(f"第{self.current_level}关没有成语数据，尝试下一关")
                    self.current_level += 1
                    continue
                
                print(f"第{self.current_level}关有{len(idioms)}个成语")
                
                # 下载每个成语的图片
                for i, idiom in enumerate(idioms):
                    chengyu = idiom.get("name", "")
                    image_url = idiom.get("img", "")
                    
                    if chengyu and image_url:
                        self.download_image(image_url, chengyu, self.current_level, i+1)
                        
                        # 随机等待，模拟人类行为
                        wait_time = random.uniform(0.5, 2.0)
                        time.sleep(wait_time)
                    else:
                        print(f"成语 #{i+1} 数据不完整，跳过")
                
                # 记录爬取数量
                crawl_count += len(idioms)
                print(f"已爬取 {crawl_count} 个成语")
                
                # 模拟通过当前关卡
                if self.pass_level(self.current_level):
                    print(f"成功通过第{self.current_level}关")
                    # 进入下一关
                    self.current_level += 1
                    
                    # 显示进度
                    print(f"即将进入第{self.current_level}关...")
                    
                    # 保存进度
                    self.save_progress()
                    
                    # 适当休息，避免请求过于频繁
                    wait_time = random.uniform(3, 8)
                    print(f"休息 {wait_time:.1f} 秒...")
                    time.sleep(wait_time)
                else:
                    print(f"通过第{self.current_level}关失败，重试...")
                    time.sleep(5)
            except KeyboardInterrupt:
                print("\n用户中断爬取")
                break
            except Exception as e:
                print(f"爬取过程中发生错误: {e}")
                print("等待5秒后继续...")
                time.sleep(5)
        
        return True
    
    def save_progress(self):
        """保存爬取进度"""
        try:
            progress = {
                "current_level": self.current_level,
                "downloaded_chengyu": list(self.downloaded_chengyu),
                "timestamp": time.time(),
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open("chengyu_crawler_progress.json", "w", encoding="utf-8") as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
                
            print(f"进度已保存，当前关卡: {self.current_level}, 已下载: {len(self.downloaded_chengyu)} 个成语")
        except Exception as e:
            print(f"保存进度失败: {e}")
    
    def load_progress(self):
        """加载爬取进度"""
        try:
            if os.path.exists("chengyu_crawler_progress.json"):
                with open("chengyu_crawler_progress.json", "r", encoding="utf-8") as f:
                    progress = json.load(f)
                
                self.current_level = progress.get("current_level", 1)
                saved_chengyu = set(progress.get("downloaded_chengyu", []))
                self.downloaded_chengyu.update(saved_chengyu)
                
                print(f"已加载进度，当前关卡: {self.current_level}, 已下载: {len(self.downloaded_chengyu)} 个成语")
                return self.current_level
            else:
                print("未找到进度文件，将从第1关开始爬取")
                return 1
        except Exception as e:
            print(f"加载进度失败: {e}")
            return 1

# 运行爬虫
if __name__ == "__main__":
    crawler = ChengyuCrawler()
    
    # 提示用户输入微信凭证
    print("\n===== 看图猜成语小程序爬虫 =====")
    print("提示: 需要提供有效的微信凭证才能爬取数据")
    
    # 检查是否有已保存的凭证
    has_saved_credentials = crawler.headers["x-wx-id"] and crawler.headers["x-wx-skey"]
    
    if has_saved_credentials:
        print(f"\n已保存的凭证:")
        print(f"x-wx-id: {crawler.headers['x-wx-id']}")
        print(f"x-wx-skey: {crawler.headers['x-wx-skey']}")
        
        use_saved = input("使用已保存的凭证? (y/n): ").lower() == 'y'
        if not use_saved:
            has_saved_credentials = False
    
    if not has_saved_credentials:
        print("\n请从抓包工具中获取以下信息:")
        print("1. 找到发往 wq.maimaigou.com 的请求")
        print("2. 从请求头中复制 x-wx-id 和 x-wx-skey 的值")
        
        wx_id = input("\n请输入x-wx-id: ")
        wx_skey = input("请输入x-wx-skey: ")
        
        if not wx_id or not wx_skey:
            print("错误: 凭证不能为空")
            exit(1)
            
        crawler.set_wx_credentials(wx_id, wx_skey)
    
    print("\n准备开始爬取...")
    
    # 加载之前的进度
    start_level = crawler.load_progress()
    
    try:
        # 使用模拟玩家方式爬取
        crawler.crawl_as_player(start_level=start_level)
    except KeyboardInterrupt:
        print("\n用户中断爬取")
    except Exception as e:
        print(f"爬取过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 保存进度
        crawler.save_progress()
        print("爬虫已退出")