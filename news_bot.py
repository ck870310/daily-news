# ... existing code ...
import feedparser
from zhipuai import ZhipuAI
import json
import time
import os
import httpx  # 新增：用来伪装成真实电脑浏览器，突破防爬虫拦截

# 🌟 1. 安全读取智谱 API 密钥
# ... existing code ...
# 🌟 3. 换上了全新的对云端服务器绝对友好的8大权威新闻源
rss_urls = [
    {"source": "FT中文网", "url": "http://www.ftchinese.com/rss/news"},
    {"source": "BBC国际", "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"source": "纽约时报", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"}, # 使用官方英文源，AI自动翻译
    {"source": "华尔街日报", "url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml"}, # 替换日经，使用官方英文源
    {"source": "36氪", "url": "https://36kr.com/feed"},
    {"source": "新浪财经", "url": "https://feed.sina.com.cn/api/roll/finance/rss"},
    {"source": "第一财经", "url": "https://www.yicai.com/rss/"}, # 虎嗅关闭了接口，替换为顶尖的第一财经
    {"source": "人民网", "url": "http://www.people.com.cn/rss/world.xml"}
]

final_news_data = []
news_id = 1

print("\n🚀 防火墙突破版 AI 机器人开始运行...")
print("-----------------------------------")

for feed_info in rss_urls:
    print(f"\n📡 正在前往 {feed_info['source']} 抓取 Top 10 新闻...")
    try:
        # 伪装成真实的电脑浏览器，绕过防火墙拦截
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = httpx.get(feed_info['url'], headers=headers, timeout=20.0, follow_redirects=True)
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"  [失败] 无法连接到 {feed_info['source']}")
        continue
    
    success_count = 0
    
    # 扩大候选池到前 25 条，确保凑够 10 条
# ... existing code ...
```

### 2. 修改前端页面：`index.html`

去 GitHub 编辑 `index.html`，把顶部的导航栏按钮名字更新一下，对应我们新的权威新闻源。

```html:前端界面:index.html
<!-- ... existing code ... -->
        <div class="tracker-box">
            <div class="tracker-title">🎯 页面雷达追踪 (输入关键词并回车，自动置顶命中新闻)</div>
            <div class="tracker-input-group">
                <input type="text" id="kwInput" class="tracker-input" placeholder="例如：降息, 人工智能, 苹果...">
                <button id="addBtn" class="tracker-btn">添加追踪</button>
            </div>
            <div id="kwContainer"></div>
        </div>

        <!-- 替换了全新的8大强力新闻源按钮 -->
        <div class="tabs" id="tabContainer">
            <button class="tab active" data-source="全部">全部</button>
            <button class="tab" data-source="FT中文网">FT中文网</button>
            <button class="tab" data-source="BBC国际">BBC国际</button>
            <button class="tab" data-source="纽约时报">纽约时报</button>
            <button class="tab" data-source="华尔街日报">华尔街日报</button>
            <button class="tab" data-source="36氪">36氪</button>
            <button class="tab" data-source="新浪财经">新浪财经</button>
            <button class="tab" data-source="第一财经">第一财经</button>
            <button class="tab" data-source="人民网">人民网</button>
        </div>
        
        <div class="news-list" id="newsContainer"></div>
    </div>
<!-- ... existing code ... -->
