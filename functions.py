from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.request
import os
from urllib.parse import urlparse
from urllib.parse import unquote
from bs4 import BeautifulSoup
import difflib
import json


options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

remote_server_url = "http://standalone-chrome:4444/wd/hub"

# webドライバの初期化
driver = webdriver.Remote(
    command_executor=remote_server_url,
    options=options
)

os.makedirs("/mnt/download/", exist_ok=True)

def clicker(target, xpath=None):
    next_url = None
    # ひとつめの引数で指定されたURLにアクセス
    driver.get(target)
    
    # ふたつめの引数でXpathが指定されている場合はその要素を取得する
    if xpath:
        # Xpathで指定された要素が見つかるまで待機する
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        href = element.get_attribute("href")
        
        if href:
            # Xpathで指定された要素にhrefがあればそのURLを戻り値とする
            next_url = href
        else:
            # Xpathで指定された要素にhrefがなければその要素をクリックする
            driver.execute_script("arguments[0].click();", element)
            
            # クリック後に遷移したページのURLを戻り値とする
            next_url = driver.current_url

            # ひとつめの引数で指定されたURLがedgeのものであれば，動的に生成されるページなので下記の特別な手順を行う
            if target == "https://www.microsoft.com/ja-jp/edge/business/download":
                # 同意してダウンロード のボタン要素を取得する
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="eula-dialog"]/div[5]/a'))
                )
                # 同意してダウンロード のボタンにあるhrefのURLを取得して戻り値とする
                href = element.get_attribute("href")
                next_url = href

            if target == "https://www.microsoft.com/en-us/download/details.aspx?id=49030":
                # "Choose the download you want" を選択する
                element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="dlc-details-multi-download-modal"]/div/div/div[2]/div/table/tbody/tr[1]/td[1]/div/label'))
                )
                element.click()
                
                element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="dlc-details-multi-download-modal"]/div/div/div[2]/div/div/div[1]/button'))
                )
                element.click()

                # ログを取得してダウンロードURLを探す
                logs = driver.get_log("performance")
                for log in logs:
                    try:
                        message = json.loads(log["message"])["message"]
                        if "Network.responseReceived" in message["method"]:
                            url = message["params"]["response"]["url"]
                            if ".exe" in url:  # ダウンロードリンクの可能性があるURLを取得
                                next_url = url
                    except:
                        pass

    # 引数にXpathが指定されていない場合は，URLのファイルをダウンロードする
    else:
        parsed_url = urlparse(target)
        file_name = unquote(os.path.basename(parsed_url.path))
        save_path = os.path.join('/mnt/download/', file_name)

        with urllib.request.urlopen(target) as web_file, open(save_path, 'wb') as local_file:
            local_file.write(web_file.read())
        print(f"ファイルを保存しました: {save_path}")

    return next_url


def compare_text_files(file_a_path, file_b_path, encoding, file_name, output_folder):
    try:
        with open(file_a_path, 'r', encoding=encoding) as file_a, open(file_b_path, 'r', encoding=encoding) as file_b:
            diff = list(difflib.unified_diff(
                file_a.readlines(),
                file_b.readlines(),
                fromfile = file_a_path,
                tofile = file_b_path
            ))

            if diff:
                diff_output_path = os.path.join(output_folder, f"{file_name}_{encoding}_diff.txt")
                os.makedirs(os.path.dirname(diff_output_path), exist_ok=True)
                with open(diff_output_path, 'w', encoding='utf-8') as diff_file:
                    diff_file.write(''.join(diff))
                print(f"差分をファイルに出力しました: {diff_output_path}")
            return True
    except UnicodeDecodeError:
        return False


def search_in_diff_output_folder(search_term, diff_output_folder, source_html_file, output_file):
    # DiffOutput フォルダ内のすべてのファイルを検索
    with open(output_file, 'a', encoding='utf-8') as out_file:  # ファイルを追記モードで開く
        for root, _, files in os.walk(diff_output_folder):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as diff_file:
                    lines = diff_file.readlines()
                    for line_number, line in enumerate(lines, start=1):
                        if search_term in line:
                            output_line = (
                                "-----------------------------------------------------------\n"
                                "このレポートに含まれるポリシーは，新しいテンプレートで内容が変更されています\n"
                                f"ポリシーレポート: {source_html_file}\n"
                                f"ポリシー名: {search_term}\n"
                                f"ポリシーテンプレート: {file}\n"
                                f"行番号: {line_number}\n"
                                #f"内容: {line.strip()}\n"
                                "-----------------------------------------------------------\n"
                            )
                            out_file.write(output_line)  # ファイルに出力

