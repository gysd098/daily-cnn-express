import requests
from bs4 import BeautifulSoup
from google import genai
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os 

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

client = genai.Client(api_key=GEMINI_API_KEY)

url = "https://edition.cnn.com/business/investing?utm_source=hp"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    print("CNN 실시간 경제 기사 수집 중...")
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    news_elements = soup.find_all("a", class_="container__link")

    news_context = ""
    parsed_count = 0

    for element in news_elements:
        href = element.get("href")
        if href and href.startswith("/202"):
            full_url = f"https://edition.cnn.com{href}"
            headline_span = element.find("span", class_="container__headline-text")

            if headline_span:
                headline = headline_span.text.strip()
                parsed_count += 1

                news_context += f"기사 {parsed_count}\n"
                news_context += f"제목: {headline}\n"
                news_context += f"링크: {full_url}\n\n"

                if parsed_count >= 5: 
                    break

    if news_context:
        print(f"🤖 Gemini AI에게 고등학생 맞춤형 경제 요약 요청 중 ({parsed_count}개 기사)...")

        prompt = f"""
        너는 고등학생을 위한 친절한 경제 선생님이야.
        아래 제공된 최신 CNN 경제 뉴스 기사 목록을 보고, 학생들이 전반적인 글로벌 경제 흐름을 파악할 수 있도록 통합 요약 브리핑을 작성해줘.

        [요약 규칙]
        1. 전체 기사들을 아우르는 오늘 하루 경제 핵심 요약을 한국어로 작성해줘.
        2. 기사 제목에 나온 주요 경제 용어(예: Big Tech, Wall Street, Inflation 등)가 있다면 고등학생이 이해하기 쉽게 한 줄로 풀어서 설명해줘.
        3. 각 기사의 원문 링크는 요약본 바로 옆이나 아래에 그대로 유지해줘.
        4. 친근하고 격려하는 말투(~요, ~습니다)를 사용해줘.
        5. 요약 내용을 5문장으로 요약해줘
        6. 답변할 때 볼드체()나 글머리 기호 같은 마크다운 형식을 절대 사용하지 말고, 평문(Plain text)으로만 작성해 줘.


        [CNN 뉴스 목록]
        {news_context}
        """

        response_ai = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        print("\n" + "="*20 + " 경제 브리핑 완료 " + "="*20)
        mail_txt = response_ai.text
        print(response_ai.text)
        print("="*60)

        print("Gmail 발송 준비 중...")

        SMTP_SERVER = "smtp.gmail.com"
        SMTP_PORT = 587  
        SENDER_EMAIL = "sopbunny714@gmail.com"
        RECEIVER_EMAIL = "sopbunny714@gmail.com"  

        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = "[CNN summary]"

        msg.attach(MIMEText(mail_txt, 'plain', 'utf-8'))

        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.ehlo()
            server.starttls()  
            server.ehlo()

            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            server.quit()

            print("이메일이 성공적으로 발송되었습니다! 수신 메일함을 확인하세요.")
        except Exception as e:
            print(f"❌ Gmail 발송 실패 에러 로그: {e}")
    else:
        print("❌ 분석할 수 있는 기사를 찾지 못했습니다.")

except requests.exceptions.HTTPError as e:
    print(f"❌ 웹사이트 접근 제한 (Header 또는 차단 문제): {e}")
except Exception as e:
    print(f"❌ 오류 발생: {e}")
