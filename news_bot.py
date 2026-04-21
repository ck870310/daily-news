import feedparser
from zhipuai import ZhipuAI
import json
import time
import os

# 🌟 1. 从云端“保险箱”读取 API Key
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY") 

# 如果没有读到密钥，直接发出致命警告
if not ZHIPU_API_KEY:
    print("🚨 致命错误：未获取到 ZHIPU_API_KEY！请检查 GitHub Secrets 是否配置正确。")

# 加入 timeout=60，防止云端网络波动导致连接超时
client = ZhipuAI(api_key=ZHIPU_API_KEY, timeout=60)

# 🌟 2. 读取桌面上的关键词备忘录
watch_keywords = ""
keyword_file = "keywords.txt"
if os.path.exists(keyword_file):
    with open(keyword_file, "r", encoding="utf-8") as f:
        watch_keywords = f.read().strip()
    print(f"📖 已读取今日关注关键词: {watch_keywords}")
else:
    print("📖 未发现 keywords.txt，当前无特别关注关键词。")

# 🌟 3. 更换为国内可直连的优质新闻源
rss_urls = [
    {"source": "36氪", "url": "https://36kr.com/feed"},
    {"source": "新浪财经", "url": "https://feed.sina.com.cn/api/roll/finance/rss"},
    {"source": "钛媒体", "url": "https://www.tmtpost.com/rss.xml"},
    {"source": "人民网", "url": "http://www.people.com.cn/rss/world.xml"}
]

final_news_data = []
news_id = 1

print("\n🚀 国内源抗压升级版 AI 机器人开始运行...")
print("-----------------------------------")

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
            keyword_instruction = f"""
            5. 特别任务：用户的近期关注关键词是【{watch_keywords}】。
            如果这篇新闻的内容与上述任何一个关键词高度相关，请务必将 isImportant 设为 true，并在 keyword 字段填入命中的关键词（如果没有命中，isImportant 设为 false，keyword 留空）。
            """
            
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
        
        请严格以下面 JSON 格式返回，不要有 Markdown 符号：
        {{"summary": "详细总结...", "region": "地区", "type": "种类", "isImportant": false, "keyword": ""}}
        """
        
        # ⚠️ 【终极抗压修改】：遇到连接错误不再直接跳过，最多重试 3 次！
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model="glm-4-flash",  
                    messages=[{"role": "user", "content": prompt_text}],
                )
                
                ai_result_text = response.choices[0].message.content.strip()
                # 智能清理可能产生的多余符号
                if ai_result_text.startswith('```json'):
                    ai_result_text = ai_result_text[7:]
                if ai_result_text.startswith('```'):
                    ai_result_text = ai_result_text[3:]
                if ai_result_text.endswith('```'):
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
                
                print(f"  [完成] {title[:15]}...")
                
                # 成功后，强制休息 3 秒，避免请求过于密集
                time.sleep(3)
                break  # 成功完成，跳出重试循环
                
            except Exception as e:
                # 如果遇到错误，打印具体原因并休息 5 秒后重试
                print(f"  [警告] 第 {attempt + 1} 次尝试失败: {type(e).__name__}")
                time.sleep(5)
                
        else:
            # 如果循环了 3 次都失败了，才会真的跳过
            print(f"  [放弃] 连续 3 次连接失败，跳过此条新闻。")

print("================================================================")
print("🎉 所有新闻处理完毕！正在生成数据文件...")
js_content = "const newsData = " + json.dumps(final_news_data, ensure_ascii=False, indent=4) + ";"

# 写入文件
with open("news_data.js", "w", encoding="utf-8") as f:
    f.write(js_content)
    
print("✅ 大功告成！数据已成功保存到同目录下的 news_data.js 文件中！")
