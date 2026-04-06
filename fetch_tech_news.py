import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ====================== 配置（已填好你的API Key） ======================
DOUBAO_API_KEY = "7572b867-d9c2-4c75-aaf2-bbcc5754ed7b"
DOUBAO_API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
OUTLOOK_EMAIL = os.getenv("OUTLOOK_EMAIL")
OUTLOOK_PASSWORD = os.getenv("OUTLOOK_PASSWORD")
RECIPIENT_EMAIL = "ZCAyyds666@outlook.com"

# ====================== 1. 抓取科技新闻 ======================
def fetch_tech_news():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}
    news_list = []

    # 抓取TechCrunch中文网
    try:
        url = "https://techcrunch.cn/"
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select(".post-block__title")[:15]:
            a = item.find("a")
            if a:
                title = a.get_text(strip=True)
                link = a["href"]
                news_list.append({"title": title, "link": link, "source": "TechCrunch中文"})
    except Exception as e:
        print(f"TechCrunch抓取失败: {e}")

    return news_list

# ====================== 2. 调用豆包API整理新闻 ======================
def summarize_with_doubao(news_list):
    if not news_list:
        return "❌ 今日未抓取到任何科技新闻。"

    prompt = f"""
你是专业科技编辑，请把以下科技新闻整理成清晰、易读的每日早报：
- 分点列出，每条含标题 + 链接
- 控制在10条内，优先重要内容
- 语言简洁，适合邮件阅读
- 开头加一句今日科技概览

新闻列表：
{[f'{n["source"]}：{n["title"]} {n["link"]}' for n in news_list]}
"""

    payload = {
        "model": "doubao-seed-2.0-pro",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    headers = {
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(DOUBAO_API_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ 豆包API调用失败: {str(e)}\n\n原始新闻：\n" + "\n".join([f"- {n['source']}：{n['title']}\n{n['link']}" for n in news_list[:10]])

# ====================== 3. 发送到Outlook邮箱 ======================
def send_email(content):
    msg = MIMEMultipart()
    msg["From"] = OUTLOOK_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = f"📰 每日科技早报 {datetime.now().strftime('%Y-%m-%d')}"

    html_content = f"""
    <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2563eb; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">📰 每日科技早报</h2>
            <div style="font-size: 15px; color: #374151; white-space: pre-line;">
                {content}
            </div>
            <p style="margin-top: 30px; color: #9ca3af; font-size: 12px;">
                自动发送 · GitHub Actions · Doubao-Seed-2.0-pro
            </p>
        </body>
    </html>
    """
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
            server.starttls()
            server.login(OUTLOOK_EMAIL, OUTLOOK_PASSWORD)
            server.sendmail(OUTLOOK_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        print("✅ 邮件发送成功")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# ====================== 主流程 ======================
if __name__ == "__main__":
    print("🔍 开始抓取科技新闻...")
    news = fetch_tech_news()
    print(f"✅ 抓取到 {len(news)} 条新闻")

    print("🤖 调用豆包API整理...")
    summary = summarize_with_doubao(news)

    print("📤 发送邮件...")
    send_email(summary)
