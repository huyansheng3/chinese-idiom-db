import requests
import pandas as pd
import jieba
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import os
import math

class IdiomRanker:
    def __init__(self, idiom_list_path):
        """初始化成语排序器"""
        self.idioms = self._load_idioms(idiom_list_path)
        print("成语数量：", len(self.idioms))
        self.corpus_weight = 0.5  # 语料库权重
        self.search_weight = 0.3  # 搜索引擎权重
        self.education_weight = 0.2  # 教育分级权重
        
    def _load_idioms(self, file_path):
        """从文件加载成语列表"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"文件 {file_path} 不存在，使用示例成语列表")
            # 示例成语列表
            return ["一举两得", "守株待兔", "画蛇添足", "对牛弹琴", "入木三分", 
                    "望梅止渴", "纸上谈兵", "四面楚歌", "风和日丽", "万马奔腾"]
    
    def analyze_corpus_frequency(self, corpus_path=None):
        """分析语料库中成语出现频率"""
        print("正在分析语料库频率...")
        
        # 如果没有提供语料库，尝试从网络获取或使用示例文本
        if not corpus_path:
            corpus_text = self._get_corpus_text()
        else:
            try:
                # 处理大型语料库文件，使用分块读取避免内存问题
                corpus_text = self._read_large_corpus(corpus_path)
            except Exception as e:
                print(f"读取语料库文件出错: {e}")
                corpus_text = self._get_corpus_text()
        
        # 计算每个成语在语料中的出现次数
        idiom_counts = {}
        for idiom in self.idioms:
            count = len(re.findall(idiom, corpus_text))
            idiom_counts[idiom] = count
        
        # 标准化分数（0-100）
        max_count = max(idiom_counts.values()) if idiom_counts.values() else 1
        corpus_scores = {idiom: (count / max_count) * 100 for idiom, count in idiom_counts.items()}
        
        return corpus_scores
    
    def _get_corpus_text(self):
        """获取语料库文本，优先从网络获取，失败则使用示例文本"""
        try:
            # 尝试从多个来源获取语料
            corpus_text = self._fetch_online_corpus()
            print(f"成功获取在线语料，大小: {len(corpus_text)} 字符")
            return corpus_text
        except Exception as e:
            print(f"获取在线语料失败: {e}，使用示例语料")
            # 使用示例语料作为备选
            return """
            现代社会节奏快，人们往往争分夺秒。很多人做事一举两得，提高效率。
            然而有些人却守株待兔，不思进取。还有人做事画蛇添足，反而弄巧成拙。
            对牛弹琴的行为也很常见，沟通不到位导致误解。
            好的文章常常入木三分，让人印象深刻。
            望梅止渴只是一种心理安慰，不能解决实际问题。
            纸上谈兵不如实际行动来得重要。
            企业面临四面楚歌的局面需要团结一致。
            风和日丽的天气适合外出活动。
            改革开放以来，中国经济万马奔腾，蓬勃发展。
            """
    
    def _fetch_online_corpus(self):
        """从多个在线来源获取语料"""
        corpus_text = ""
        
        # 扩展语料来源，增加更多成语相关网站
        sources = [
            # 原有来源
            {"url": "https://www.thepaper.cn/", "encoding": "utf-8"},
            {"url": "https://www.chinadaily.com.cn/", "encoding": "utf-8"},
            {"url": "https://www.sina.com.cn/", "encoding": "utf-8"},
            {"url": "https://baike.baidu.com/item/成语故事/115151", "encoding": "utf-8"},
            {"url": "https://hanyu.baidu.com/s?wd=成语大全&from=zici", "encoding": "utf-8"},
            {"url": "https://www.gushiwen.cn/", "encoding": "utf-8"},  # 古诗文网
            
            # 新增成语专业网站
            {"url": "http://www.hydcd.com/cy/", "encoding": "gb2312"},  # 汉辞网成语大全
            {"url": "http://chengyu.t086.com/", "encoding": "utf-8"},  # 成语大全网
            {"url": "http://www.guoxuedashi.com/chengyu/", "encoding": "utf-8"},  # 国学大师成语
            {"url": "https://www.lz13.cn/chengyu/", "encoding": "utf-8"},  # 励志网成语频道
            {"url": "https://www.zhengjicn.com/chengyu/", "encoding": "utf-8"},  # 正集成语大全
            {"url": "http://www.idcot.com/cy/", "encoding": "utf-8"},  # 成语词典
            
            # 新闻媒体（增加更多语料）
            {"url": "http://www.people.com.cn/", "encoding": "gb2312"},  # 人民网
            {"url": "http://www.xinhuanet.com/", "encoding": "utf-8"},  # 新华网
            {"url": "https://www.zaobao.com/", "encoding": "utf-8"},  # 联合早报
            
            # 百科类网站（更多成语解释）
            {"url": "https://baike.baidu.com/item/成语/86319", "encoding": "utf-8"},  # 百度百科成语词条
            {"url": "https://baike.baidu.com/item/中国成语大全", "encoding": "utf-8"},
            {"url": "https://wiki.mbalib.com/wiki/成语", "encoding": "utf-8"},  # MBA智库百科
            
            # 教育类网站
            {"url": "https://www.eol.cn/", "encoding": "utf-8"},  # 中国教育在线
            {"url": "http://www.pep.com.cn/", "encoding": "utf-8"},  # 人民教育出版社
            
            # 成语故事专题
            {"url": "https://www.61w.cn/news/chengyu/", "encoding": "utf-8"},  # 61阅读网成语故事
            {"url": "http://www.tom61.com/chengyu/chengyugushi/index.html", "encoding": "gb2312"},  # 成语故事大全
        ]
        
        # 使用线程池并行获取内容，增加最大工作线程数
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for source in sources:
                # 为future对象添加source_url属性以便于日志记录
                future = executor.submit(self._fetch_content, source["url"], source["encoding"])
                future.source_url = source["url"]
                futures.append(future)
            
            # 收集结果
            for future in futures:
                try:
                    result = future.result(timeout=15)  # 增加超时时间
                    if result:
                        print(f"从 {future.source_url} 获取了 {len(result)} 字符")
                        corpus_text += result + "\n"
                except Exception as e:
                    print(f"获取内容时出错 ({future.source_url}): {e}")
        
        # 如果获取的语料太少，抛出异常以便回退到示例语料
        if len(corpus_text) < 1000:
            raise Exception("获取的语料内容不足")
        
        # 保存语料库到本地文件以便重用
        try:
            with open("corpus_cache.txt", "w", encoding="utf-8") as f:
                f.write(corpus_text)
            print("语料库已缓存到本地文件")
        except Exception as e:
            print(f"缓存语料库失败: {e}")
        
        print(f"总共获取了 {len(corpus_text)} 字符的语料")    
        return corpus_text
    
    def _fetch_content(self, url, encoding="utf-8"):
        """从URL获取文本内容并清理"""
        try:
            # 随机化User-Agent以减少被屏蔽的可能性
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
            ]
            
            headers = {
                "User-Agent": user_agents[hash(url) % len(user_agents)],
                "Accept": "text/html,application/xhtml+xml,application/xml",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": "https://www.baidu.com/",  # 添加引用来源
                "Connection": "keep-alive"
            }
            
            # 添加随机延迟，避免请求过于频繁
            time.sleep(0.5 + hash(url) % 10 * 0.1)
            
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = encoding
            
            # 使用更复杂的方法提取正文内容
            # 1. 先去除script和style标签内容
            content = re.sub(r'<script.*?>.*?</script>', '', response.text, flags=re.DOTALL)
            content = re.sub(r'<style.*?>.*?</style>', '', content, flags=re.DOTALL)
            
            # 2. 去除HTML标签
            content = re.sub(r'<.*?>', ' ', content)
            
            # 3. 去除多余空白字符
            content = re.sub(r'\s+', ' ', content)
            
            # 4. 提取可能包含成语的段落（包含至少一个中文字符的段落）
            chinese_paragraphs = re.findall(r'[^。！？.!?]*[\u4e00-\u9fa5]+[^。！？.!?]*[。！？.!?]', content)
            
            # 5. 特别关注包含成语的段落
            idiom_paragraphs = []
            for idiom in self.idioms:
                for para in chinese_paragraphs:
                    if idiom in para and para not in idiom_paragraphs:
                        idiom_paragraphs.append(para)
            
            # 合并结果，优先使用包含成语的段落
            filtered_content = ' '.join(idiom_paragraphs + chinese_paragraphs)
            
            return filtered_content
        except Exception as e:
            print(f"从 {url} 获取内容失败: {e}")
            return ""
    
    def _read_large_corpus(self, file_path, chunk_size=10*1024*1024):
        """分块读取大型语料库文件，避免内存溢出"""
        print(f"正在分块读取大型语料库: {file_path}")
        full_text = ""
        
        try:
            file_size = os.path.getsize(file_path)
            chunks_count = file_size // chunk_size + 1
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for i in range(chunks_count):
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    full_text += chunk
                    print(f"已读取 {i+1}/{chunks_count} 块，当前语料大小: {len(full_text)} 字符")
            
            return full_text
        except UnicodeDecodeError:
            # 尝试其他编码
            for encoding in ['gbk', 'gb2312', 'gb18030']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都失败，抛出异常
            raise Exception(f"无法解码文件 {file_path}，请检查文件编码")
    
    def analyze_search_popularity(self):
        """分析搜索引擎中成语的流行度，优化评分机制"""
        print("正在分析搜索引擎流行度...")
        
        # 注意：实际应用中应使用搜索引擎API，这里使用模拟数据
        # 模拟搜索结果数量（实际应用中替换为API调用）
        search_results = {
            "一举两得": 2500000,
            "守株待兔": 1800000,
            "画蛇添足": 1500000,
            "对牛弹琴": 1200000,
            "入木三分": 900000,
            "望梅止渴": 800000,
            "纸上谈兵": 1100000,
            "四面楚歌": 700000,
            "风和日丽": 3000000,
            "万马奔腾": 600000
        }
        
        # 为列表中所有成语设置随机值，使用对数正态分布
        # 这样可以模拟真实世界中的搜索结果分布
        import random
        import math
        random.seed(42)  # 使用固定种子以确保结果可重现
        
        for idiom in self.idioms:
            if idiom not in search_results:
                # 使用对数正态分布生成随机搜索结果数量
                mu = 12  # 对数均值
                sigma = 1.5  # 对数标准差
                search_results[idiom] = int(math.exp(random.normalvariate(mu, sigma)))
        
        # 对搜索结果取对数，然后标准化到0-100范围
        # 这样可以处理搜索结果数量的长尾分布
        log_results = {idiom: math.log(max(1, result)) for idiom, result in search_results.items()}
        
        min_log = min(log_results.values())
        max_log = max(log_results.values())
        range_log = max_log - min_log if max_log > min_log else 1
        
        # 使用非线性映射拉大分数差距
        search_scores = {}
        for idiom, log_result in log_results.items():
            # 先标准化到0-1范围
            normalized = (log_result - min_log) / range_log
            # 使用幂函数拉大差距
            search_scores[idiom] = 100 * (normalized ** 0.7)
        
        return search_scores
    
    def analyze_education_level(self):
        """分析成语在教育中的分级，优化评分机制"""
        print("正在分析教育分级...")
        
        # 模拟教育分级数据（1-6级，1级为小学低年级，6级为高中及以上）
        # 实际应用中应从教育词汇表或教材中提取
        education_levels = {
            "一举两得": 2,  # 小学中年级
            "守株待兔": 3,  # 小学高年级
            "画蛇添足": 3,
            "对牛弹琴": 3,
            "入木三分": 4,  # 初中
            "望梅止渴": 3,
            "纸上谈兵": 4,
            "四面楚歌": 5,  # 高中
            "风和日丽": 2,
            "万马奔腾": 4
        }
        
        # 为列表中所有成语设置默认值，使用随机分布而非固定值
        # 这样可以避免大量成语获得相同分数
        import random
        random.seed(42)  # 使用固定种子以确保结果可重现
        
        for idiom in self.idioms:
            if idiom not in education_levels:
                # 使用加权随机分布，使分数更符合正态分布
                weights = [0.05, 0.15, 0.25, 0.30, 0.15, 0.10]  # 各级别的权重
                education_levels[idiom] = random.choices([1, 2, 3, 4, 5, 6], weights=weights)[0]
        
        # 转换为分数（低年级学习的成语更常用，得分更高）
        # 使用非线性映射，拉大分数差距
        education_scores = {}
        for idiom, level in education_levels.items():
            # 非线性映射：1级=100分，2级=85分，3级=65分，4级=40分，5级=20分，6级=5分
            score_map = {1: 100, 2: 85, 3: 65, 4: 40, 5: 20, 6: 5}
            education_scores[idiom] = score_map[level]
        
        return education_scores
    
    def calculate_overall_scores(self):
        """计算成语的综合常用度分数，优化分数分布"""
        corpus_scores = self.analyze_corpus_frequency()
        search_scores = self.analyze_search_popularity()
        education_scores = self.analyze_education_level()
        
        # 计算加权综合分数
        raw_scores = {}
        for idiom in self.idioms:
            score = (
                corpus_scores.get(idiom, 0) * self.corpus_weight +
                search_scores.get(idiom, 0) * self.search_weight +
                education_scores.get(idiom, 0) * self.education_weight
            )
            raw_scores[idiom] = score
        
        # 应用正态分布优化
        return self._normalize_scores_with_distribution(raw_scores)
    
    def _normalize_scores_with_distribution(self, raw_scores):
        """将原始分数转换为更符合正态分布的分数"""
        scores = list(raw_scores.values())
        
        if not scores:
            return {}
        
        # 计算均值和标准差
        mean = sum(scores) / len(scores)
        std_dev = (sum((x - mean) ** 2 for x in scores) / len(scores)) ** 0.5
        
        # 如果标准差接近0，说明分数几乎相同，需要人为拉开差距
        if std_dev < 0.1:
            print("分数分布过于集中，应用人为拉伸...")
            # 根据排名拉伸分数
            sorted_idioms = sorted(raw_scores.items(), key=lambda x: x[1], reverse=True)
            normalized_scores = {}
            
            # 使用指数衰减函数拉伸分数
            total_idioms = len(sorted_idioms)
            for i, (idiom, _) in enumerate(sorted_idioms):
                # 排名越高，分数越高，使用指数衰减
                rank_ratio = i / total_idioms  # 0到1之间，0表示最高排名
                score = 100 * math.exp(-5 * rank_ratio)  # 指数衰减函数
                normalized_scores[idiom] = round(score, 1)
            
            return normalized_scores
        
        # 使用Z-score标准化，然后映射到0-100范围
        normalized_scores = {}
        for idiom, score in raw_scores.items():
            # 计算Z-score
            z_score = (score - mean) / std_dev
            
            # 将Z-score映射到0-100范围，使用sigmoid函数
            # sigmoid函数将使分数分布更接近正态分布
            normalized_score = 100 / (1 + math.exp(-z_score * 0.8))
            
            # 进一步拉伸分数范围，使高分和低分的差距更明显
            if normalized_score > 50:
                normalized_score = 50 + (normalized_score - 50) * 1.5
            else:
                normalized_score = normalized_score * 0.8
            
            # 确保分数在1-100范围内
            normalized_score = max(1, min(100, normalized_score))
            normalized_scores[idiom] = round(normalized_score, 1)
        
        # 检查分数分布
        self._check_score_distribution(normalized_scores)
        
        return normalized_scores
    
    def _check_score_distribution(self, scores):
        """检查并打印分数分布情况"""
        score_values = list(scores.values())
        
        # 计算分数分布
        ranges = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        distribution = [0] * (len(ranges) - 1)
        
        for score in score_values:
            for i in range(len(ranges) - 1):
                if ranges[i] <= score < ranges[i+1]:
                    distribution[i] += 1
                    break
        
        # 打印分布情况
        print("\n分数分布情况:")
        for i in range(len(ranges) - 1):
            range_str = f"{ranges[i]}-{ranges[i+1]}"
            count = distribution[i]
            percentage = (count / len(score_values)) * 100
            bar = "#" * int(percentage / 2)
            print(f"{range_str:>7}: {count:>4} ({percentage:>5.1f}%) {bar}")
        
        # 计算统计指标
        mean = sum(score_values) / len(score_values)
        variance = sum((x - mean) ** 2 for x in score_values) / len(score_values)
        std_dev = variance ** 0.5
        
        print(f"\n平均分: {mean:.2f}")
        print(f"标准差: {std_dev:.2f}")
        print(f"最高分: {max(score_values):.1f}")
        print(f"最低分: {min(score_values):.1f}")
        print(f"分数范围: {max(score_values) - min(score_values):.1f}")
    
    def rank_idioms(self):
        """根据常用度对成语进行排序"""
        scores = self.calculate_overall_scores()
        
        # 按分数从高到低排序
        ranked_idioms = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return ranked_idioms
    
    def export_results(self, output_path="ranked_idioms.csv"):
        """导出排序结果到CSV文件"""
        ranked_idioms = self.rank_idioms()
        
        # 创建DataFrame
        df = pd.DataFrame(ranked_idioms, columns=["成语", "常用度分数"])
        
        # 导出到CSV
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"排序结果已导出到 {output_path}")
        
        return df

# 使用示例
if __name__ == "__main__":
    # 使用成语文件路径，如果文件不存在则使用内置示例
    ranker = IdiomRanker("chengyu.txt")
    
    # 排序并显示结果
    ranked_df = ranker.export_results()
    print("\n常用成语排名（前10）:")
    print(ranked_df.head(10))