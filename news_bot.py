import feedparser
from zhipuai import ZhipuAI
import json
import time
import os

# 🌟 1. 从 GitHub 环境变量安全读取智谱 API 密钥
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY") 
client = ZhipuAI(api_key=ZHIPU_API_KEY)

# 🌟 2. 读取追踪词备忘录
watch_keywords = ""
keyword_file = "keywords.txt"
if os.path.exists(keyword_file):
    with open(keyword_file, "r", encoding="utf-8") as f:
        watch_keywords = f.read().strip()
    print(f"📖 已读取追踪关键词: {watch_keywords}")
else:
    print("📖 未发现 keywords.txt，当前无特别追踪关键词。")

# 🌟 3. 新闻源列表 (扩充为 8 大国内外权威平台)
rss_urls = [
    {"source": "FT中文网", "url": "http://www.ftchinese.com/rss/news"},
    {"source": "BBC国际", "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"source": "华尔街日报", "url": "https://cn.wsj.com/zh-hans/rss"},
    {"source": "联合早报", "url": "https://www.zaobao.com/realtime/world/rss"},
    {"source": "36氪", "url": "https://36kr.com/feed"},
    {"source": "新浪财经", "url": "https://feed.sina.com.cn/api/roll/finance/rss"},
    {"source": "钛媒体", "url": "https://www.tmtpost.com/rss.xml"},
    {"source": "人民网", "url": "http://www.people.com.cn/rss/world.xml"}
]

final_news_data = []
news_id = 1

print("\n🚀 媒体专栏版 AI 读报机器人开始运行...")
print("-----------------------------------")

for feed_info in rss_urls:
    print(f"\n📡 正在前往 {feed_info['source']} 抓取 Top 10 新闻...")
    try:
        feed = feedparser.parse(feed_info['url'])
    except Exception as e:
        print(f"  [失败] 无法连接到 {feed_info['source']}")
        continue
    
    # 强制目标：每个平台必须成功抓取 10 条
    success_count = 0
    
    # 扩大候选池到前 25 条，确保遇到坏新闻被跳过后，依然能凑够 10 条
    for entry in feed.entries[:25]:
        if success_count >= 10:
            print(f"  🎯 {feed_info['source']} 已成功抓满 10 条，切换下一平台。")
            break
            
        title = entry.title
        link = entry.link
        raw_summary = entry.description if hasattr(entry, 'description') else "无"
        
        print(f"  -> 发现: {title}")
        
        keyword_instruction = ""
        if watch_keywords:
            keyword_instruction = f"""
            5. 特别任务：用户的近期追踪关键词是【{watch_keywords}】。
            如果这篇新闻的内容与上述任何一个关键词高度相关，请务必将 isImportant 设为 true，并在 keyword 字段填入命中的关键词（否则 false/留空）。
            """
            
        prompt_text = f"""
        你是一个专业的新闻主编。请阅读以下新闻：
        标题: {title}
        摘要: {raw_summary}
        
        请完成：
        1. 翻译成中文。
        2. 用 100 到 150 字详细总结这篇新闻的核心事件和影响。
        3. 判断所属地区 (仅限：中国、美国、欧洲、其他)。
        4. 判断所属种类 (仅限：政治、宏观、财经、科技、政策)。
        {keyword_instruction}
        
        请严格以下面的 JSON 格式返回，不要有 Markdown 符号：
        {{"summary": "详细总结...", "region": "地区", "type": "种类", "isImportant": false, "keyword": ""}}
        """
        
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model="glm-4-flash",  
                    messages=[{"role": "user", "content": prompt_text}],
                )
                
                # 清洗 JSON 格式防止报错
                ai_result_text = response.choices[0].message.content.strip()
                if ai_result_text.startswith("```json"):
                    ai_result_text = ai_result_text[7:]
                if ai_result_text.startswith("```"):
                    ai_result_text = ai_result_text[3:]
                if ai_result_text.endswith("```"):
                    ai_result_text = ai_result_text[:-3]
                ai_result_text = ai_result_text.strip()
                
                ai_data = json.loads(ai_result_text)
                
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
                
                print(f"     [搞定] 总结完成 ({success_count}/10)")
                time.sleep(3) # 休息3秒防封
                break 
                
            except Exception as e:
                print(f"     [警告] 第 {attempt + 1} 次尝试失败，休息重试...")
                time.sleep(4)
        else:
            print(f"     [放弃] 连续 3 次失败，跳过此条。")

print("\n================================================================")
print("🎉 所有新闻处理完毕！正在生成数据文件...")
js_content = "const newsData = " + json.dumps(final_news_data, ensure_ascii=False, indent=4) + ";"

with open("news_data.js", "w", encoding="utf-8") as f:
    f.write(js_content)
    
print("✅ 大功告成！数据已成功写入 news_data.js。")
