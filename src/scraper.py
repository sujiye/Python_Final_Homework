"""
一个用于小红书笔记数据爬取的脚本,将自动利用chrome浏览器登陆爬取小红书对应关键词的笔记
调用:scraper.start_scraper(<keyword>)
参数:keyword: 要搜索的关键词
输出:
    1. 所有符合关键词的小红书笔记数据将保存到./data/notes_data.json 文件中
    2. 将每个笔记根据其标题创建一个文件夹,将笔记的文本内容、图片保存到这个文件夹中
"""
import sys
import time
import json
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

Browser = None
# cookies 文件路径：相对根目录
cookies_path = "./cookies.json"

def init_browser():
    """
    初始化 Chrome 浏览器,配置选项包括最大化窗口、禁用自动化检测等
    在这里使用的是arm架构macOS中的Chrome test浏览器,更换测试平台可能需要重新进行配置
    """
    global Browser # 声明使用全局变量 Browser
    # 浏览器配置信息
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    try:
        print("init browser...") 
        service = Service(ChromeDriverManager().install()) # 使用 Service 对象
        Browser = webdriver.Chrome(service=service, options=options)
        print("init browser success.")  
    except Exception as e:
        print(f"faild to init browser error: {e}")
        input("press enter to exit...")
        sys.exit(1)

    Browser.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"}
    )



def wait_and_find(by, selector, timeout=10):
    try:
        element = WebDriverWait(Browser, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
        return element
    except:
        print(f"faild to wait and find element: {by} {selector}") 
        return None

def login():
    """
    自动登录小红书，使用 cookies.json 文件中的 Cookie。
    如果文件不存在或读取失败，会提示用户手动登录。
    """

    print("\n--- auto login ---")
    Browser.get("https://www.xiaohongshu.com")
    time.sleep(1)

    cookie_list = []
    if os.path.exists(cookies_path):
        try:
            with open(cookies_path, "r", encoding="utf-8") as f:
                cookie_list = json.load(f)
            print(f"successfully load {len(cookie_list)} cookies.")
        except Exception as e:
            print(f" faild to load cookies.json error: {e}")
            print("please check cookies.json file format.")
    else:
        print(f" faild to find cookies.json file, please ensure it is located in {os.getcwd()} directory.")

    if not cookie_list:
        print("no usable cookie, please login manually.")
        input("press enter to continue...")
        sys.exit(1) # 如果没有 cookie 且无法手动登录，则退出

    for ck in cookie_list:
        try:
            ck.pop("sameSite", None)
            ck.pop("storeId", None)
            if ck.get("domain", "").startswith("."):
                ck["domain"] = ck["domain"][1:]
            Browser.add_cookie(ck)
        except Exception as e:
            # 某些 cookie 可能是 httpOnly，无法通过 Selenium 添加，这是正常现象
            # print(f" cookie 写入失败：{ck.get('name')}（正常现象，可能是 httpOnly）")
            pass

    print("successfully write cookies to browser.")
    time.sleep(1)
    Browser.get("https://www.xiaohongshu.com") # 刷新主页以应用cookie
    time.sleep(3) # 等待页面加载

    if "login" in Browser.current_url or "passport" in Browser.current_url: # 增加对 passport 的判断
        print("faild to login, redirect to login page or register page.")
        print("may be cookie expired or invalid. please login manually once to update cookies.json.")
        input("press enter to continue...")
        sys.exit(1) # 如果登录失败，则退出
    else:   
        print("successfully login.")

def sanitize_filename(filename):
    # 移除文件名中不允许的特殊字符
    invalid_chars = '<>:"/\\|?*\n'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    # 替换空格为下划线，或者直接移除，这里选择替换为下划线
    filename = filename.replace(' ', '_')
    # 限制文件名长度，例如200个字符
    return filename[:200]

def scrape_notes(keywords, output_dir="data"):
    print(f"start scrape_notes function, output directory: {output_dir}")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"create output directory: {output_dir}")

    all_notes_data = []
    note_id_counter = [0]
    used_titles = {} # 用于处理重复标题

    for keyword in keywords:
        print(f"\n=== start scrape notes with keyword: {keyword} ===")
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
        print(f"visit search page: {search_url}")
        Browser.get(search_url)
        time.sleep(5)

        print("start scroll page to load more notes...")
        for i in range(3):
            Browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            print(f"scroll page {i+1} times.")

        note_links = set()
        try:
            print("try to extract note urls...")
            note_elements = Browser.find_elements(By.CSS_SELECTOR, "section.note-item a")
            for element in note_elements:
                href = element.get_attribute("href")
                if href and ("/search_result/" in href or "/explore/" in href):
                    note_links.add(href)
            print(f"successfully extract {len(note_links)} note urls.") 
        except Exception as e:
            print(f" faild to extract note urls error: {e}")

        print(f" find {len(note_links)} note urls")

        for link in list(note_links)[:40]:
            print(f" start scrape note: {link}")
            Browser.get(link)
            time.sleep(5)

            note_title = "无标题笔记"
            try:
                title_element = wait_and_find(By.CSS_SELECTOR, "div#detail-title")
                if title_element:
                    note_title = title_element.text
                    print(f" successfully extract title: {note_title}")
            except Exception as e:
                print(f" faild to extract title error: {e}")
                time.sleep(3)

            sanitized_title = sanitize_filename(note_title)
            final_folder_name = sanitized_title
            if final_folder_name in used_titles:
                used_titles[final_folder_name] += 1
                final_folder_name = f"{sanitized_title}_{used_titles[final_folder_name]}"
            else:
                used_titles[final_folder_name] = 0

            note_folder_path = os.path.join(output_dir, final_folder_name)
            if not os.path.exists(note_folder_path):
                os.makedirs(note_folder_path)
                print(f"create note folder: {note_folder_path}")

            note_id_counter[0] += 1
            note_data = {
                "id": note_id_counter[0],
                "title": note_title,
                "url": link,
                "images": [],
                "text_file": ""
            }

            try:
                print("try to extract images...")
                img_elements = Browser.find_elements(By.CSS_SELECTOR, "div.swiper-slide img")
                for i, img_element in enumerate(img_elements):
                    img_url = img_element.get_attribute("src")
                    if img_url:
                        img_name = f"{keyword}_{os.path.basename(img_url).split('?')[0]}_{i}.jpg"
                        img_path = os.path.join(note_folder_path, img_name)
                        try:
                            print(f" try to download image: {img_url}")
                            response = requests.get(img_url, stream=True)
                            response.raise_for_status()
                            with open(img_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            note_data["images"].append({"path": img_path, "url": img_url})
                            print(f" successfully download image: {img_name}")
                            time.sleep(0.5)
                        except Exception as img_e:
                            print(f" faild to download image {img_url} error: {img_e}")

                print("try to extract note text...")
                text_element = wait_and_find(By.CSS_SELECTOR, "span.note-text") # 更新为新的选择器
                if text_element:
                    note_text_content = text_element.text
                    text_file_path = os.path.join(note_folder_path, "text.txt")
                    with open(text_file_path, "w", encoding="utf-8") as f:
                        f.write(note_text_content)
                    note_data["text_file"] = text_file_path
                    print(f" successfully extract text and save to: {text_file_path}")
                else:
                    print(" faild to extract note text.")



            except Exception as note_e:
                print(f" get {link} failed:{note_e}")

            if note_data["images"] or note_data["text_file"]:
                all_notes_data.append(note_data)

    # 保存总的 JSON 数据
    json_output_path = os.path.join(output_dir, "notes_data.json")
    print(f"save notes data to {json_output_path}")
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(all_notes_data, f, ensure_ascii=False, indent=4)
    print(f"\nnotes data saved to {json_output_path}")
    return all_notes_data

def start_scraper(keyword: str):
    """
    启动爬虫,根据给定的关键词进行笔记的爬取
    参数:keyword:用于搜索的关键词,多个关键词之间用空格分隔
    """
    print("-----start-----") 
    init_browser()
    try:
        login()
        keywords = [keyword]
        scraped_data = scrape_notes(keywords)
        print("\n-------------------")
        print(" finish ")
        print("-------------------")
        # print(json.dumps(scraped_data, ensure_ascii=False, indent=4))

    except Exception as e:
        print("Error:", e)
        import traceback
        traceback.print_exc()

    finally:
        try:
            Browser.quit()
            print("browser closed.")
        except:
            pass

if __name__ == "__main__":
    start_scraper("带娃 育儿 亲子 熊孩子 漫画")
