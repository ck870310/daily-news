import feedparser
from zhipuai import ZhipuAI
import json
import time
import os

# 🌟 1. 从云端“保险箱”读取 API Key
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY") 
client = ZhipuAI(api_key=ZHIPU_API_KEY)

# 🌟 2. 读取关键词备忘录
watch_keywords = ""
keyword_file = "keywords.txt"
if os.path.exists(keyword_file):
    with open(keyword_file, "r", encoding="utf-8") as f:
        watch_keywords = f.read().strip()

# 🌟 3. 更换为国内可直连的优质新闻源
rss_urls = [
    {"source": "36氪", "url": "https://36kr.com/feed"},
    {"source": "新浪财经", "url": "https://feed.sina.com.cn/api/roll/finance/rss"},
    {"source": "钛媒体", "url": "https://www.tmtpost.com/rss.xml"},
    {"source": "人民网", "url": "http://www.people.com.cn/rss/world.xml"}
]

final_news_data = []
news_id = 1

print("\n🚀 国内源升级版 AI 机器人开始运行...")

for feed_info in rss_urls:
    print(f"正在前往 {feed_info['source']} 抓取 Top 10 新闻...")
    try:
        feed = feedparser.parse(feed_info['url'])
    except Exception as e:
        print(f"  [失败] 无法连接到 {feed_info['source']}")
        continue
    
    # 抓取每个平台的前 10 条
    for entry in feed.entries[:10]:
        title = entry.title
        link = entry.link
        raw_summary = entry.description if hasattr(entry, 'description') else "无"
        
        keyword_instruction = ""
        if watch_keywords:
            keyword_instruction = f"用户的追踪关键词是【{watch_keywords}】。如高度相关，isImportant设为true并在keyword字段填入该词。"
            
        prompt_text = f"""
        你是一个专业的新闻主编。请阅读以下新闻：
        标题: {title}
        摘要: {raw_summary}
        
        请完成：
        1. 翻译/润色为专业中文。
        2. 用 100 到 150 字详细总结核心事件、背景及可能的影响（要求逻辑清晰，字数必须达标）。
        3. 判断地区 (中国、美国、欧洲、其他)。
        4. 判断种类 (政治、宏观、财经、科技、政策)。
        {keyword_instruction}
        
        请严格以下面 JSON 格式返回：
        {{"summary": "详细总结...", "region": "地区", "type": "种类", "isImportant": false, "keyword": ""}}
        """
        
        try:
            response = client.chat.completions.create(
                model="glm-4-flash",  
                messages=[{"role": "user", "content": prompt_text}],
            )
            ai_result_text = response.choices[0].message.content.strip()
            # 清理 Markdown 块
            if ai_result_text.startswith("
