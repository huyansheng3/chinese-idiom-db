import os
import re
import json
import jieba
import numpy as np
from collections import Counter

# 定义具体名词类别
CONCRETE_CATEGORIES = {
    '动物': ['鸟', '鱼', '龙', '虎', '狗', '猫', '牛', '马', '羊', '鸡', '鹰', '蛇', '龟', '兔', '鼠', '猴', '象', '狼', '熊', '豹', '鹿', '蝶', '蚁', '蜂', '鹅', '鸭', '猪'],
    '植物': ['花', '草', '树', '木', '叶', '果', '松', '竹', '梅', '兰', '菊', '荷', '莲', '柳', '桃', '杏', '李', '梨', '枣', '麦', '稻', '谷'],
    '自然物': ['山', '水', '石', '云', '雨', '雪', '风', '雷', '电', '日', '月', '星', '天', '地', '海', '河', '湖', '江', '泉', '沙', '土', '火'],
    '身体部位': ['头', '眼', '耳', '鼻', '口', '手', '足', '心', '肝', '肺', '肠', '胃', '骨', '血', '肉', '发', '须', '牙', '舌', '唇', '臂', '腿'],
    '颜色': ['红', '黄', '蓝', '绿', '紫', '黑', '白', '灰', '金', '银', '彩', '色'],
    '方位': ['东', '西', '南', '北', '上', '下', '左', '右', '前', '后', '内', '外', '中', '间'],
    '数字': ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '百', '千', '万', '亿'],
    '物品': ['刀', '剑', '笔', '墨', '纸', '砚', '琴', '棋', '书', '画', '杯', '盘', '碗', '筷', '桌', '椅', '床', '门', '窗', '车', '船', '伞', '镜', '钟', '鼓', '钱', '布', '衣', '帽', '鞋', '袜']
}

# 合并所有具体名词
CONCRETE_NOUNS = []
for category, words in CONCRETE_CATEGORIES.items():
    CONCRETE_NOUNS.extend(words)

# 定义动词列表
ACTION_VERBS = ['走', '跑', '跳', '飞', '游', '爬', '看', '听', '说', '吃', '喝', '打', '拿', '给', '做', '来', '去', '进', '出', '上', '下', '开', '关', '推', '拉', '抓', '放', '举', '投', '抱', '背', '扛', '提', '拖', '踢', '摇', '晃', '转', '弯', '倒', '立', '坐', '躺', '跪', '蹲', '跌', '倒']

# 定义难以图像化的抽象词
ABSTRACT_WORDS = ['思', '想', '念', '情', '爱', '恨', '怒', '喜', '忧', '愁', '志', '意', '智', '德', '仁', '义', '礼', '信', '忠', '孝', '廉', '耻', '勇', '谦', '诚', '敬', '善', '美', '真', '道', '理', '法', '则', '权', '利', '责', '任', '命', '运', '缘', '分', '福', '祸', '吉', '凶', '祥', '瑞']

# 定义常见成语结构模式
CHENGYU_PATTERNS = [
    r'(.)\1(.)\2',  # AABB模式，如"高高兴兴"
    r'(.)(.)\1\2',  # ABAB模式，如"来来往往"
    r'(.)(.)(.)\3',  # ABCC模式，如"无边无际"
    r'(.)(.)\2\1',  # ABBA模式，如"天翻地覆"
    r'(.)\1(.)(.)',  # AABC模式，如"步步为营"
    r'(.)(.)(.)\1',  # ABCA模式，如"有口难言"
]

def load_chengyu_list(file_path):
    """从文件中加载成语列表"""
    chengyu_list = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            chengyu = line.strip()
            if chengyu and not chengyu.startswith('...'):  # 跳过省略行
                chengyu_list.append(chengyu)
    return chengyu_list

def analyze_chengyu(chengyu):
    """分析单个成语的特征"""
    # 初始化特征字典
    features = {
        'chengyu': chengyu,
        'length': len(chengyu),
        'concrete_noun_count': 0,
        'concrete_categories': set(),
        'action_verb_count': 0,
        'abstract_word_count': 0,
        'has_pattern': False,
        'pattern_type': None,
        'visualizable_score': 0
    }
    
    # 检查成语长度
    if features['length'] != 4:
        features['visualizable_score'] -= 10  # 非四字成语降低分数
    
    # 检查每个字是否为具体名词
    for char in chengyu:
        if char in CONCRETE_NOUNS:
            features['concrete_noun_count'] += 1
            # 找出字属于哪个类别
            for category, words in CONCRETE_CATEGORIES.items():
                if char in words:
                    features['concrete_categories'].add(category)
        
        if char in ACTION_VERBS:
            features['action_verb_count'] += 1
            
        if char in ABSTRACT_WORDS:
            features['abstract_word_count'] += 1
    
    # 检查成语是否符合特定模式
    for pattern in CHENGYU_PATTERNS:
        match = re.match(pattern, chengyu)
        if match:
            features['has_pattern'] = True
            features['pattern_type'] = pattern
            break
    
    # 计算可视化得分
    # 具体名词越多，得分越高
    features['visualizable_score'] += features['concrete_noun_count'] * 2.5
    
    # 动作动词也有助于可视化
    features['visualizable_score'] += features['action_verb_count'] * 1.5
    
    # 抽象词越多，得分越低
    features['visualizable_score'] -= features['abstract_word_count'] * 2
    
    # 如果有特定模式，增加得分
    if features['has_pattern']:
        features['visualizable_score'] += 1
    
    # 如果包含多个类别的具体名词，增加得分
    features['visualizable_score'] += len(features['concrete_categories']) * 1.5
    
    # 将集合转换为列表以便JSON序列化
    features['concrete_categories'] = list(features['concrete_categories'])
    
    return features

def check_image_exists(chengyu, image_dir='chengyu_images'):
    """检查是否已经有该成语的图片"""
    chengyu_dir = os.path.join(image_dir, chengyu)
    if os.path.exists(chengyu_dir):
        image_files = [f for f in os.listdir(chengyu_dir) if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        return len(image_files) > 0
    return False

def main():
    # 加载成语列表
    chengyu_list = load_chengyu_list('chengyu.txt')
    print(f"共加载 {len(chengyu_list)} 个成语")
    
    # 分析每个成语
    analyzed_results = []
    for chengyu in chengyu_list:
        features = analyze_chengyu(chengyu)
        
        # 检查是否已有图片
        features['has_images'] = check_image_exists(chengyu)
        
        # 如果已有图片，增加得分
        if features['has_images']:
            features['visualizable_score'] += 3
        
        analyzed_results.append(features)
    
    # 按可视化得分排序
    sorted_results = sorted(analyzed_results, key=lambda x: x['visualizable_score'], reverse=True)
    
    # 保存分析结果
    with open('chengyu_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(sorted_results, f, ensure_ascii=False, indent=2)
    
    # 输出前100个最适合的成语
    print("\n最适合看图猜成语的前100个成语:")
    for i, result in enumerate(sorted_results[:100], 1):
        print(f"{i}. {result['chengyu']} (得分: {result['visualizable_score']:.1f}, 具体名词: {result['concrete_noun_count']}, 动作动词: {result['action_verb_count']}, 已有图片: {'是' if result['has_images'] else '否'})")
    
    # 统计分析
    score_distribution = [r['visualizable_score'] for r in analyzed_results]
    print(f"\n得分统计: 最高 {max(score_distribution):.1f}, 最低 {min(score_distribution):.1f}, 平均 {np.mean(score_distribution):.1f}")
    
    # 统计各类别的成语数量
    category_counts = Counter()
    for result in analyzed_results:
        for category in result['concrete_categories']:
            category_counts[category] += 1
    
    print("\n各类别成语数量:")
    for category, count in category_counts.most_common():
        print(f"{category}: {count}个")
    
    # 生成推荐列表
    recommended = [r for r in sorted_results if r['visualizable_score'] > 5 and r['length'] == 4]
    with open('recommended_chengyu.txt', 'w', encoding='utf-8') as f:
        for r in recommended:
            f.write(f"{r['chengyu']}\n")
    
    print(f"\n已生成推荐成语列表，共 {len(recommended)} 个成语")

if __name__ == "__main__":
    main()
