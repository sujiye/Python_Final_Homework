import sys
import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

Browser = None
cookies_path = "./cookies.json"

def init_browser():
    global Browser
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    try:
        print("init browser...") 
        service = Service(ChromeDriverManager().install())
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

def publish_note(title, content, image_paths=None, hashtags=None):
    """
    自动化发布小红书笔记。
    参数:
        title (str): 笔记标题。
        content (str): 笔记正文内容。
        image_paths (list): 图片文件路径列表。
        hashtags (list): 话题标签列表。
    """
    print("\n--- start publish note ---")
    try:
        # 1. 导航到发布页面
        Browser.get("https://creator.xiaohongshu.com/publish/publish?source=official&from=tab_switch&target=image")
        print("navigated to publish page.")
        time.sleep(5) # 等待页面加载

        # # 等待遮挡元素消失
        # try:
        #     WebDriverWait(Browser, 10).until(
        #         EC.invisibility_of_element_located((By.CSS_SELECTOR, "span.short-note-tooltip-text-title"))
        #     )
        #     print("intercepting element disappeared.")
        # except:
        #     print("no intercepting element found or it did not disappear within timeout.")

        # # 尝试点击图片元素，如果它确实是触发上传的按钮
        # image_click_element = wait_and_find(By.CSS_SELECTOR, "img[data-v-3d0a30be]")
        # if image_click_element:
        #     image_click_element.click()
        #     print("image click element clicked.")
        #     time.sleep(2) # 等待点击后的响应，例如文件选择框弹出

        # 2. 上传图片 (如果存在)
        if image_paths:
            print(f"uploading {len(image_paths)} images...")
            # 小红书上传图片通常是通过文件输入框，需要找到对应的 input 元素
            # 这里的选择器可能需要根据实际页面调整
            upload_input = wait_and_find(By.CSS_SELECTOR, "input[type='file']")
            if upload_input:
                # Selenium 的 send_keys 方法可以直接上传文件
            # 如果有多个图片，需要将路径用换行符连接
                absolute_image_paths = [os.path.abspath(p) for p in image_paths]
                upload_input.send_keys("\n".join(absolute_image_paths))
                print("images sent to upload input.")
                time.sleep(10) # 等待图片上传和处理
            else:
                print("could not find image upload input.")
                return False

        # 3. 输入标题
        try:
            title_input = WebDriverWait(Browser, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input.d-text[placeholder='填写标题会有更多赞哦～']"))
            )
            title_input.send_keys(title)
            print(f"title entered: {title}")
        except Exception as e:
            print(f"could not find or interact with title input: {e}")
            return False

        # 4. 输入正文内容
        try:
            content_textarea = WebDriverWait(Browser, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.tiptap.ProseMirror[contenteditable='true']"))
            )
            content_textarea.send_keys(content)
            print(f"content entered: {content}")

            # 根据用户反馈，话题标签直接在正文后输入并回车
            if hashtags:
                print("adding hashtags...")
                for tag in hashtags:
                    content_textarea.send_keys(f" #{tag}") # 注意这里添加一个空格，避免和正文粘连
                    time.sleep(1) # 短暂等待，确保标签被识别
                    content_textarea.send_keys(Keys.ENTER) # 输入标签后按回车确认
                print(f"hashtags added: {', '.join(hashtags)}")

        except Exception as e:
            print(f"could not find or interact with content textarea: {e}")
            return False

        # 5. 点击发布按钮
        publish_button = wait_and_find(By.CSS_SELECTOR, "button.publishBtn")
        if publish_button:
            publish_button.click()
            print("publish button clicked.")
            time.sleep(5) # 等待发布完成
            print("note published successfully!")
            return True
        else:
            print("could not find publish button.")
            return False

    except Exception as e:
        print(f"failed to publish note error: {e}")
        return False

def start_publisher(title, content, image_paths=None, hashtags=None):
    """
    启动发布程序。
    参数:
        title (str): 笔记标题。
        content (str): 笔记正文内容。
        image_paths (list): 图片文件路径列表。
        hashtags (list): 话题标签列表。
    """
    print("-----start publisher-----")
    init_browser()
    try:
        login()
        publish_note(title, content, image_paths, hashtags)
        print("\n-------------------")
        print(" finish publisher ")
        print("-------------------")

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
    # 示例用法
    example_title = "zzz日历"
    example_content = "绝区零2026年1月月历"
    example_image_paths = [
        os.path.join(os.getcwd(), "publish", "IMG_8981.PNG")
    ] # 替换为你的图片路径列表，例如 ["/path/to/image1.jpg", "/path/to/image2.png"]
    example_hashtags = ["绝区零", "叶瞬光", "日历"]

    start_publisher(example_title, example_content, example_image_paths, example_hashtags)
