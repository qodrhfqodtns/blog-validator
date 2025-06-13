from flask import Flask, request, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re

app = Flask(__name__)

HTML_FORM = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>블로그 검수기</title>
</head>
<body>
    <h2>🔍 블로그 검수기</h2>
    <form method="GET" action="/check">
        블로그 주소: <input type="text" name="url" size="50"><br><br>
        키워드 1: <input type="text" name="kw1"><br><br>
        키워드 2: <input type="text" name="kw2"><br><br>
        <input type="submit" value="검수하기">
    </form>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_FORM

@app.route('/check', methods=['GET'])
def check():
    url = request.args.get('url')
    kw1 = request.args.get('kw1')
    kw2 = request.args.get('kw2')

    if not url or not kw1 or not kw2:
        return '모든 항목을 입력해주세요.'

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        time.sleep(2)

        try:
            iframe = driver.find_element(By.ID, "mainFrame")
            driver.switch_to.frame(iframe)
            time.sleep(1)
        except:
            print("⚠ iframe 없음 또는 전환 실패")

        # ✅ 스마트플레이스 링크 유무 먼저 감지 (제거 전에!)
        try:
            place_map_divs = driver.find_elements(By.CLASS_NAME, "se-placesMap")
            place_link_found = len(place_map_divs) > 0
        except:
            place_link_found = False

        # ✅ 본문 텍스트 추출 (스마트플레이스 제거 후)
        try:
            content_elem = driver.find_element(By.CLASS_NAME, "se-main-container")
            for el in content_elem.find_elements(By.CLASS_NAME, "se-placesMap"):
                driver.execute_script("arguments[0].remove();", el)
            content = content_elem.get_attribute("innerText").strip()
            print("📄 진짜 본문 내용:\n", content)
        except Exception as e:
            content = ""
            print("❌ 본문 추출 오류:", str(e))

        title = driver.title or ""
        keyword1_in_title = kw1 in title
        keyword2_in_title = kw2 in title

        keyword1_count = content.count(kw1)
        keyword2_count = content.count(kw2)

        try:
            images = content_elem.find_elements(By.CLASS_NAME, "se-image-resource")
            all_image_urls = [img.get_attribute("src") for img in images if img.get_attribute("src")]

            print("\n📸 전체 이미지 목록:")
            for url in all_image_urls:
                print(url)

            real_images = [url for url in all_image_urls if "postfiles.pstatic.net" in url]
            ad_images = [url for url in all_image_urls if "blogfiles.pstatic.net" in url]

            image_count = len(real_images)
            ad_image_found = len(ad_images) > 0

            print(f"🖼 실제 이미지: {image_count}장 / 공정위 이미지 포함: {ad_image_found}")
        except Exception as e:
            image_count = 0
            ad_image_found = False
            print("❌ 이미지 분석 오류:", str(e))

        # ✅ 동영상 감지: iframe + video 태그 모두 확인
        try:
            video_count = 0
            iframes = content_elem.find_elements(By.TAG_NAME, "iframe")
            video_count += sum(1 for f in iframes if 'youtube.com' in (f.get_attribute("src") or ''))
            videos = content_elem.find_elements(By.TAG_NAME, "video")
            video_count += len(videos)
        except:
            video_count = 0

        result = f"""
        <h2>검수 결과</h2>
        <ul>
            <li><strong>제목:</strong> {title}</li>
            <li><strong>{kw1} 제목 포함:</strong> {'✅' if keyword1_in_title else '❌'}</li>
            <li><strong>{kw2} 제목 포함:</strong> {'✅' if keyword2_in_title else '❌'}</li>
            <li><strong>{kw1} 본문 포함 횟수:</strong> {keyword1_count}회 (기준: 3회 이상)</li>
            <li><strong>{kw2} 본문 포함 횟수:</strong> {keyword2_count}회 (기준: 1회 이상)</li>
            <li><strong>이미지 수:</strong> {image_count}개 (기준: 15장 이상)</li>
            <li><strong>공정위 이미지 포함:</strong> {'✅ 포함' if ad_image_found else '❌ 없음'}</li>
            <li><strong>동영상 포함:</strong> {'✅ 포함' if video_count >= 1 else '❌ 없음'}</li>
            <li><strong>스마트플레이스 링크:</strong> {'✅ 포함' if place_link_found else '❌ 없음'}</li>
        </ul>
        <pre>📄 진짜 본문 내용:\n{content}</pre>
        <pre>📸 전체 이미지 목록:\n{'\n'.join(all_image_urls)}</pre>
        <a href="/">← 다시 검사하기</a>
        """
        return render_template_string(result)

    except Exception as e:
        return f"오류 발생: {str(e)}"
    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(port=5000)
