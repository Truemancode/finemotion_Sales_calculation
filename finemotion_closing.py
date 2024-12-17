import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from helium import *
import requests
import os
import sys
import importlib
from helium import start_chrome, go_to, kill_browser, set_driver
from webdriver_manager.chrome import ChromeDriverManager
import re
import time

def generate_webdriver():
    driver = None
    try:
        # "HEROKU"環境変数が設定されている場合、Heroku環境とみなす
        if os.environ.get("HEROKU"):
            # Heroku環境の場合
            options = Options()
            options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
            options.add_argument("--headless")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
            options.add_argument('window-size=1920x1080')
            driver = webdriver.Chrome(options=options, executable_path=os.environ.get("CHROMEDRIVER_PATH"))
        else:
            # Heroku環境でない場合（ローカル環境）
            driver_path = ChromeDriverManager().install()
            options = Options()
            #options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
            options.add_argument('window-size=1920x1080')
            driver = webdriver.Chrome(options=options, executable_path=driver_path)

    except Exception as e:
        # エラーが出た場合、webdriver_managerで再度ダウンロードを試みる
        print(f"Error occurred: {e}. Trying to download chromedriver using webdriver_manager...")
        driver_path = ChromeDriverManager().install()
        options = Options()
        options.add_argument("--headless")
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
        options.add_argument('window-size=1920x1080')
        driver = webdriver.Chrome(executable_path=driver_path, options=options)

    set_driver(driver)
    return driver

# ここから元の処理
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
    driver = generate_webdriver()  # ここでgenerate_webdriver()を呼ぶ

    driver.set_window_size(1800,2000)
    go_to("https://mp-system.info/shadymotionAdmin/PcAdmin/auth/login/")

    driver.find_element_by_xpath("/html/body/div[2]/form/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/input").send_keys("mutou")
    driver.find_element_by_xpath("/html/body/div[2]/form/table/tbody/tr[2]/td/table/tbody/tr[2]/td[2]/input").send_keys("mutou")
    driver.find_element_by_xpath("/html/body/div[2]/form/table/tbody/tr[4]/td/input").click()

    frame = driver.find_element_by_xpath("/html/frameset/frame")
    driver.switch_to.frame(frame)

    #タスク表をクリック
    driver.find_element_by_xpath("/html/body/div/div[4]/a[1]").click()

    driver.switch_to.default_content()
    frame = driver.find_element_by_xpath("/html/frameset/frameset/frame[2]")
    driver.switch_to.frame(frame)

    #池袋ファインをクリック
    driver.find_element_by_xpath("/html/body/div[2]/table/tbody/tr/td[11]/form/input[7]").click()

    driver.find_element_by_xpath("/html/body/div[2]/table/tbody/tr/td[3]/form/input[6]").click()

    time.sleep(3)
    namber = driver.find_element_by_xpath("/html/body/div[3]/table[1]/tbody/tr[1]/td/table/tbody/tr/td[1]")
    namber = namber.text

    match = re.search(r'(\d+)\s*件目', namber)
    if match:
        result = match.group(1)
    else:
        st.write("No match found.")

    result = int(result) * 2
    result += 2

    cord = 0
    sales = 0
    subject_0 = 0
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

    st.write(f"会計済み:{subject_0}件")
    st.write(f"カード売り上げ:{cord}円")
    st.write(f"現金売り上げ:{sales}円")
    total_sales =  cord + sales
    st.write(f"総売り上げ:{total_sales}円")

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

    match = re.search(r'\((\d+)\件\)', value)

    if match:
        number = match.group(1)
        number = int(number)
        number += 1
    else:
        st.write("No match found.")

    salary = 0
    subject_1 = 0
    for y in range(1,number):
        elem_3 = driver.find_element_by_xpath(f"/html/body/div[3]/table/tbody/tr[4]/td/div/table/tbody/tr[{y}]/td[7]")
        elem_3 = elem_3.text
        elem_3 = elem_3.replace(",","").replace("円","")
        
        try:
            salary += int(elem_3)
            subject_1 += 1
        except ValueError:
            salary += 0

    st.write(f"給与件数{subject_1}")
    st.write(f"女子給{salary}")

    st.write("現金売上からカード、女子給料、経費を引いた額")
    Final_total_1 = total_sales - cord
    Final_total_1 = Final_total_1 - salary
    Final_total_1 = Final_total_1 - int(total_expense)
    st.write(f"{Final_total_1}円\n")

    st.write("現金売上にスタート金を足してからカード、女子給料、経費を引いた額")
    Final_total_2 = int(starting_money) + total_sales
    Final_total_2 = Final_total_2 - cord
    Final_total_2 = Final_total_2 - salary
    Final_total_2 = Final_total_2 - int(total_expense)
    st.write(f"{Final_total_2}円\n")

    driver.quit()
