import feedparser
from zhipuai import ZhipuAI
import json
import time
import os
import httpx  # 用来伪装成真实电脑浏览器，突破防爬虫拦截

# 1. 安全读取智谱 API 密钥
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY")
if not ZHIPU_API_KEY:
    print("🚨 致命错误: 未获取到 ZHIPU_API_KEY！请检查 GitHub Secrets 是否配置正确。")
    exit(1)

client = ZhipuAI(api_key=ZHIPU_API_KEY)

# 2. 读取桌面上的关键词备忘录
watch_keywords = ""
keyword_file = "keywords.txt"
if os.path.exists(keyword_file):
    with open(keyword_file, "r", encoding="utf-8") as f:
        watch_keywords = f.read().strip()
    print(f"📖 已读取今日关注关键词: {watch_keywords}")
else:
    print("📖 未发现 keywords.txt，当前无特别关注关键词。")

# 3. 8大权威新闻源 (中外兼顾，使用英文源让 AI 自动翻译以抗封锁)
rss_urls = [
    {"source": "FT中文网", "url": "http://www.ftchinese.com/rss/news"},
    {"source": "BBC国际", "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"source": "纽约时报", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"}, 
    {"source": "华尔街日报", "url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml"}, 
    {"source": "36氪", "url": "https://36kr.com/feed"},
    {"source": "新浪财经", "url": "https://feed.sina.com.cn/api/roll/finance/rss"},
    {"source": "第一财经", "url": "https://www.yicai.com/rss/"}, 
    {"source": "人民网", "url": "http://www.people.com.cn/rss/world.xml"}
]

final_news_data = []
news_id = 1

print("\n🚀 终极加强版 AI 自动读报机器人开始运行...")
print("-----------------------------------")

# 设置请求头伪装成真实浏览器，防拦截
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

for feed_info in rss_urls:
    print(f"\n📡 正在前往 {feed_info['source']} 抓取新闻...")
    try:
        # 使用 httpx 突破防火墙拦截
        response = httpx.get(feed_info['url'], headers=headers, timeout=20.0, follow_redirects=True)
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"  [失败] 无法连接到 {feed_info['source']}, 错误: {e}")
        continue
    
    success_count = 0
    
    # 扩大候选池到前 25 条，确保能凑够 10 条
    for entry in feed.entries[:25]:
        if success_count >= 10:
            print(f"  🎯 {feed_info['source']} 已成功抓取 10 条，前往下一个平台。")
            break
            
        title = entry.title
        link = entry.link
        raw_summary = entry.description if hasattr(entry, 'description') else "无"
        
        print(f"  -> 发现: {title}")
        
        keyword_instruction = ""
        if watch_keywords:
            keyword_instruction = f"""
            5. 特别任务：用户的近期关注关键词是【{watch_keywords}】。
            如果这篇新闻的内容与上述任何一个关键词高度相关，请务必将 isImportant 设为 true，并在 keyword 字段填入命中的关键词（如果没有命中，isImportant 设为 false，keyword 留空）。
            """
            
        prompt_text = f"""
        你是一个专业的新闻主编。请阅读以下新闻：
        标题: {title}
        摘要: {raw_summary}
        
        请完成：
        1. 如果是外文，请翻译成流畅的中文。
        2. 用100-150字详细总结这篇新闻的核心事件和影响（客观冷静）。
        3. 判断所属地区 (仅限：中国、美国、欧洲、其他)。
        4. 判断所属种类 (仅限：政治、宏观、财经、科技、政策)。
        {keyword_instruction}
        
        请严格以下面的 JSON 格式返回，不要有 Markdown 符号：
        {{"summary": "总结", "region": "地区", "type": "种类", "isImportant": false, "keyword": ""}}
        """
        
        retry_count = 0
        while retry_count < 3:
            try:
                response = client.chat.completions.create(
                    model="glm-4-flash",  
                    messages=[{"role": "user", "content": prompt_text}],
                    timeout=15 
                )
                
                ai_result_text = response.choices[0].message.content.strip()
                if ai_result_text.startswith('```json'): ai_result_text = ai_result_text[7:]
                if ai_result_text.startswith('```'): ai_result_text = ai_result_text[3:]
                if ai_result_text.endswith('```'): ai_result_text = ai_result_text[:-3]
                
                ai_data = json.loads(ai_result_text.strip())
                
                news_item = {
                    "id": news_id,
                    "title": title,
                    "summary": "AI总结：" + ai_data.get("summary", "总结失败"),
                    "source": feed_info['source'],
                    "region": ai_data.get("region", "其他"),
                    "type": ai_data.get("type", "宏观"),
                    "url": link,
                    "isImportant": ai_data.get("isImportant", False), 
                    "keyword": ai_data.get("keyword", "")
                }
                final_news_data.append(news_item)
                news_id += 1
                success_count += 1
                print(f"  [完成] 成功提炼 (当前进度: {success_count}/10)")
                time.sleep(3) 
                break 
                
            except Exception as e:
                retry_count += 1
                print(f"  [警告] 第 {retry_count} 次尝试失败，正在重试...")
                time.sleep(2)
        
        if retry_count == 3:
            print("  [放弃] 连续 3 次连接失败，跳过此条新闻。")

print("\n================================================================")
print("🎉 所有新闻处理完毕！正在生成数据文件...")

js_content = "const newsData = " + json.dumps(final_news_data, ensure_ascii=False, indent=4) + ";"
with open("news_data.js", "w", encoding="utf-8") as f:
    f.write(js_content)
    
print("✅ 大功告成！数据已成功保存到同目录下的 news_data.js 文件中！")
print("================================================================")
