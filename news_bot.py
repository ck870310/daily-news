import feedparser
from zhipuai import ZhipuAI
import json
import time
import os

# 🌟 1. 从云端“保险箱”（环境变量）安全读取 API Key
# 绝对不要把真实的密钥明文写在这里，上传到公开的 GitHub 库会被黑客抓取！
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY") 
client = ZhipuAI(api_key=ZHIPU_API_KEY)

# 🌟 2. 读取关键词备忘录 (云端如果没有这个文件，也不会报错)
watch_keywords = ""
keyword_file = "keywords.txt"
if os.path.exists(keyword_file):
    with open(keyword_file, "r", encoding="utf-8") as f:
        watch_keywords = f.read().strip()
    print(f"📖 已读取关注关键词: {watch_keywords}")
else:
    print("📖 未发现 keywords.txt，当前无特别关注关键词。")

# 🌟 3. 新闻源库
rss_urls = [
    {"source": "FT中文网", "url": "http://www.ftchinese.com/rss/news"},
    {"source": "BBC国际", "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"source": "华尔街日报", "url": "https://cn.wsj.com/zh-hans/rss"},
    {"source": "联合早报", "url": "https://www.zaobao.com/realtime/world/rss"}
]

final_news_data = []
news_id = 1

print("\n🚀 终极云端版 AI 读报机器人开始运行...")
print("-----------------------------------")

for feed_info in rss_urls:
    print(f"正在前往 {feed_info['source']} 抓取新闻...")
    try:
        feed = feedparser.parse(feed_info['url'])
    except Exception as e:
        print(f"  [失败] 无法连接到 {feed_info['source']}")
        continue
    
    for entry in feed.entries[:10]:
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
        1. 翻译成中文。
        2. 用50字内提炼核心结论（客观冷静）。
        3. 判断所属地区 (仅限：中国、美国、欧洲、其他)。
        4. 判断所属种类 (仅限：政治、宏观、财经、科技、政策)。
        {keyword_instruction}
        
        请严格以下面的 JSON 格式返回，不要有 Markdown 符号：
        {{"summary": "总结", "region": "地区", "type": "种类", "isImportant": false, "keyword": ""}}
        """
        
        try:
            response = client.chat.completions.create(
                model="glm-4-flash",  
                messages=[{"role": "user", "content": prompt_text}],
            )
            
            ai_result_text = response.choices[0].message.content.strip()
            
            # 清理 AI 返回的多余符号
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
            print("  [完成] 总结完毕\n")
            time.sleep(1)
            
        except Exception as e:
            print(f"  [跳过] 处理失败: {e}\n")

print("================================================================")
print("🎉 所有新闻处理完毕！正在自动生成数据文件...")

# 🌟 核心自动化步骤：生成 js 文件
js_content = "const newsData = " + json.dumps(final_news_data, ensure_ascii=False, indent=4) + ";"

# 自动在当前运行目录下，新建或覆盖 news_data.js 文件
with open("news_data.js", "w", encoding="utf-8") as f:
    f.write(js_content)

print("✅ 大功告成！数据已成功保存到同目录下的 news_data.js 文件中！")
print("================================================================")