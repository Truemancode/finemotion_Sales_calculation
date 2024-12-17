import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from helium import set_driver, go_to
import requests
import os
import sys
import importlib
from webdriver_manager.chrome import ChromeDriverManager
import re
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from requests.structures import CaseInsensitiveDict

cluster_develop = "DKdCyzHD66MkVLAykESKl6oKRaiGkjapLqJsiNV4fw8"

def send_line_notify_with_image(message, image_path, token):
    print(f"send_line_notify_with_image called with message={message}, image_path={image_path}")
    url = 'https://notify-api.line.me/api/notify'
    headers = CaseInsensitiveDict({
        'Authorization': f'Bearer {token}'
    })

    with open(image_path, 'rb') as image_file:
        files = {
            'imageFile': image_file,
            'message': (None, message)
        }
        response = requests.post(url, headers=headers, files=files)
    print("LINE通知レスポンス:", response.status_code, response.text)
    return response.status_code

def generate_webdriver():
    print("=== generate_webdriver START ===")
    driver = None
    try:
        if os.environ.get("HEROKU"):
            print("HEROKU環境検出。CHROMEDRIVER_PATHとGOOGLE_CHROME_BINを使用します。")
            print("GOOGLE_CHROME_BIN:", os.environ.get("GOOGLE_CHROME_BIN"))
            print("CHROMEDRIVER_PATH:", os.environ.get("CHROMEDRIVER_PATH"))
            
            options = Options()
            options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
            options.add_argument("--headless")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
            options.add_argument('window-size=1920x1080')

            chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
            print("CHROMEDRIVER_PATHへのchmod実行")
            os.chmod(chromedriver_path, 0o755)

            driver = webdriver.Chrome(options=options, executable_path=chromedriver_path)
            print("Heroku環境でのwebdriver起動成功")
        else:
            print("ローカル環境検出。webdriver_managerでchromedriverを取得します。")
            driver_path = ChromeDriverManager().install()
            print("ChromeDriverManagerが返したパス:", driver_path)

            driver_dir = os.path.dirname(driver_path)
            print("driver_dir:", driver_dir)
            dir_contents = os.listdir(driver_dir)
            print("driver_dir 内のファイル:", dir_contents)

            chrome_binary = None
            for f in dir_contents:
                if f == "chromedriver":
                    chrome_binary = os.path.join(driver_dir, f)
                    break

            if chrome_binary is None:
                print("chromedriver実行ファイルが見つかりません。")
                print("取得したディレクトリ:", driver_dir)
                print("ファイル一覧:", dir_contents)
                raise FileNotFoundError("chromedriver実行ファイルが見つかりません。")

            print("使用するchromedriverバイナリ:", chrome_binary)
            os.chmod(chrome_binary, 0o755)

            options = Options()
            #options.add_argument('--headless')  # 必要であればコメント解除
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
            options.add_argument('window-size=1920x1080')

            driver = webdriver.Chrome(options=options, executable_path=chrome_binary)
            print("ローカル環境でのwebdriver起動成功")

    except Exception as e:
        print(f"Error occurred in generate_webdriver: {e}")
        print("webdriver_managerで再度chromedriver取得を試みます...")
        driver_path = ChromeDriverManager().install()
        print("再取得したdriver_path:", driver_path)

        driver_dir = os.path.dirname(driver_path)
        print("再取得後のdriver_dir:", driver_dir)
        dir_contents = os.listdir(driver_dir)
        print("driver_dir 内のファイル:", dir_contents)

        chrome_binary = None
        for f in dir_contents:
            if f == "chromedriver":
                chrome_binary = os.path.join(driver_dir, f)
                break

        if chrome_binary is None:
            print("再取得後もchromedriver実行ファイルが見つかりません。")
            raise FileNotFoundError("chromedriver実行ファイルが見つかりません。")

        print("再取得したchromedriverにもchmodを付与します。")
        os.chmod(chrome_binary, 0o755)

        options = Options()
        options.add_argument("--headless")
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
        options.add_argument('window-size=1920x1080')

        driver = webdriver.Chrome(executable_path=chrome_binary, options=options)
        print("例外処理後のwebdriver起動成功")

    set_driver(driver)
    print("=== generate_webdriver END ===")

    # 起動直後のスクショ送信
    driver.save_screenshot('screenshot_driver_started.png')
    send_line_notify_with_image("WebDriver起動直後の状態です。", "screenshot_driver_started.png", cluster_develop)
    return driver

total_expense = 0
st.title("Sales calculation")
st.write("MIND+の情報を元に計算します。\nお客様の会計が済んでいるものを「済」に変更してあるか、\nまた給与を渡した女性のキャスト報酬が締められているか確認をしてください。")

starting_money = st.text_input("レジ金入力")
st.write(f"レジ金{starting_money}円\n")

expenses = st.text_area("経費入力", "経費を改行区切りで入力してください")

expenses_list = expenses.split("\n")  # Split the text into lines
total_expense = sum(int(expense) for expense in expenses_list if expense.isdigit())  # Sum up the expenses

st.write(f"経費合計{total_expense}円")

if st.button('Start'):
    print("=== Startボタン押下: 処理開始 ===")
    driver = generate_webdriver()  # ドライバ生成（デバッグ多数）

    print("画面遷移開始: ログインページへ")
    driver.set_window_size(1800,2000)
    go_to("https://mp-system.info/shadymotionAdmin/PcAdmin/auth/login/")
    driver.save_screenshot('screenshot_after_goto_login.png')
    send_line_notify_with_image("ログインページ表示確認", "screenshot_after_goto_login.png", cluster_develop)
    print("go_to完了")

    print("ログイン処理開始")
    try:
        driver.find_element_by_xpath("/html/body/div[2]/form/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/input").send_keys("mutou")
        driver.find_element_by_xpath("/html/body/div[2]/form/table/tbody/tr[2]/td/table/tbody/tr[2]/td[2]/input").send_keys("mutou")
        driver.find_element_by_xpath("/html/body/div[2]/form/table/tbody/tr[4]/td/input").click()
        print("ログイン処理完了")
    except Exception as e:
        print("ログイン処理でエラー:", e)
        driver.save_screenshot('screenshot_login_error.png')
        send_line_notify_with_image("ログイン処理中にエラー発生", "screenshot_login_error.png", cluster_develop)
        driver.quit()
        sys.exit(1)

    print("フレーム切り替え中")
    try:
        frame = driver.find_element_by_xpath("/html/frameset/frame")
        driver.switch_to.frame(frame)
        print("フレーム切り替え成功")
    except Exception as e:
        print("フレーム切り替えでエラー:", e)
        driver.save_screenshot('screenshot_frame_error.png')
        send_line_notify_with_image("フレーム切り替えエラー発生", "screenshot_frame_error.png", cluster_develop)
        driver.quit()
        sys.exit(1)

    #タスク表をクリック
    print("タスク表クリック")
    try:
        driver.find_element_by_xpath("/html/body/div/div[4]/a[1]").click()
        print("タスク表クリック成功")
    except Exception as e:
        print("タスク表クリックでエラー:", e)
        driver.save_screenshot('screenshot_task_error.png')
        send_line_notify_with_image("タスク表クリックエラー", "screenshot_task_error.png", cluster_develop)
        driver.quit()
        sys.exit(1)

    driver.switch_to.default_content()
    frame = driver.find_element_by_xpath("/html/frameset/frameset/frame[2]")
    driver.switch_to.frame(frame)

    print("池袋ファインクリック")
    try:
        driver.find_element_by_xpath("/html/body/div[2]/table/tbody/tr/td[11]/form/input[7]").click()
        driver.find_element_by_xpath("/html/body/div[2]/table/tbody/tr/td[3]/form/input[6]").click()
        print("池袋ファインクリック成功")
    except Exception as e:
        print("池袋ファインクリックでエラー:", e)
        driver.save_screenshot('screenshot_fine_click_error.png')
        send_line_notify_with_image("池袋ファインクリックエラー", "screenshot_fine_click_error.png", cluster_develop)
        driver.quit()
        sys.exit(1)

    time.sleep(3)
    print("件数取得（最大20秒待機）")
    driver.save_screenshot('screenshot_before_wait_namber.png')
    send_line_notify_with_image("件数取得前のページ状況", "screenshot_before_wait_namber.png", cluster_develop)

    try:
        namber_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/table[1]/tbody/tr[1]/td/table/tbody/tr/td[1]"))
        )
        namber = namber_element.text
        print("取得したテキスト:", namber)
    except Exception as e:
        print("件数取得でタイムアウト/エラー:", e)
        driver.save_screenshot('screenshot_namber_timeout.png')
        send_line_notify_with_image("件数取得タイムアウト/エラー発生", "screenshot_namber_timeout.png", cluster_develop)
        driver.quit()
        sys.exit(1)

    match = re.search(r'(\d+)\s*件目', namber)
    if match:
        result = match.group(1)
        print("ヒットした件数:", result)
    else:
        print("No match found for 件数")
        driver.save_screenshot('screenshot_namber_nomatch.png')
        send_line_notify_with_image("件数が取得できませんでした", "screenshot_namber_nomatch.png", cluster_develop)
        driver.quit()
        sys.exit(1)

    result = int(result) * 2
    result += 2

    cord = 0
    sales = 0
    subject_0 = 0
    print("売上集計開始")
    driver.save_screenshot('screenshot_before_sales_check.png')
    send_line_notify_with_image("売上集計前状態", "screenshot_before_sales_check.png", cluster_develop)

    for x in range(3, int(result), 2):
        elem_0 = driver.find_element_by_xpath(f"/html/body/div[3]/table[1]/tbody/tr[2]/td/table/tbody/tr[{x}]/td[12]/div/a").text
        if elem_0 == "済":
            elem_1 = driver.find_element_by_xpath(f"/html/body/div[3]/table[1]/tbody/tr[2]/td/table/tbody/tr[{x}]/td[10]").text
            elem_1 = elem_1.replace(",", "").replace("円", "")
            subject_0 += 1
            
            if "※カード" in elem_1:
                elem_1 = elem_1.replace("※カード", "")
                cord += int(elem_1)
                subject_0 += 1
                continue
            sales += int(elem_1)

    print("売上集計完了。会計済み:", subject_0, "件, カード売:", cord, "現金売:", sales)
    total_sales =  cord + sales

    print("給与情報取得開始")
    driver.switch_to.default_content()
    frame = driver.find_element_by_xpath("/html/frameset/frameset/frame[1]")
    driver.switch_to.frame(frame)

    driver.find_element_by_xpath("/html/body/div[1]/div/map[1]/area").click()
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/form/ul/li[1]/span/select").send_keys("池袋ファインモーション")
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/form/ul/li[4]/input[2]").click()

    driver.switch_to.default_content()
    frame = driver.find_element_by_xpath("/html/frameset/frameset/frame[2]")
    driver.switch_to.frame(frame)

    value = driver.find_element_by_xpath("/html/body/div[3]/table/tbody/tr[3]/td/table/tbody/tr/td")
    value = value.text
    print("取得した給与テキスト:", value)
    match = re.search(r'\((\d+)\件\)', value)

    if match:
        number = match.group(1)
        number = int(number)
        number += 1
    else:
        print("No match found for 給与件数")
        driver.save_screenshot('screenshot_salary_nomatch.png')
        send_line_notify_with_image("給与件数が取得できませんでした", "screenshot_salary_nomatch.png", cluster_develop)
        driver.quit()
        sys.exit(1)

    salary = 0
    subject_1 = 0
    print("給与集計開始")
    driver.save_screenshot('screenshot_before_salary_calc.png')
    send_line_notify_with_image("給与集計前状態", "screenshot_before_salary_calc.png", cluster_develop)

    for y in range(1,number):
        elem_3 = driver.find_element_by_xpath(f"/html/body/div[3]/table/tbody/tr[4]/td/div/table/tbody/tr[{y}]/td[7]")
        elem_3 = elem_3.text
        elem_3 = elem_3.replace(",","").replace("円","")

        try:
            salary += int(elem_3)
            subject_1 += 1
        except ValueError:
            salary += 0

    print("給与集計完了。給与件数:", subject_1, "女子給:", salary)

    # 結果表示
    st.write(f"会計済み:{subject_0}件")
    st.write(f"カード売り上げ:{cord}円")
    st.write(f"現金売り上げ:{sales}円")
    st.write(f"総売り上げ:{total_sales}円")

    st.write(f"給与件数{subject_1}")
    st.write(f"女子給{salary}")

    st.write("現金売上からカード、女子給料、経費を引いた額")
    Final_total_1 = total_sales - cord - salary - int(total_expense)
    st.write(f"{Final_total_1}円\n")

    st.write("現金売上にスタート金を足してからカード、女子給料、経費を引いた額")
    Final_total_2 = int(starting_money) + total_sales - cord - salary - int(total_expense)
    st.write(f"{Final_total_2}円\n")

    print("処理終了。ブラウザを終了します。最終結果をスクショします。")
    driver.save_screenshot('screenshot_final.png')
    send_line_notify_with_image("処理完了。最終結果です。", "screenshot_final.png", cluster_develop)

    driver.quit()
    print("=== 全処理完了 ===")
