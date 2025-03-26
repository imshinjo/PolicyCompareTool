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


options = Options()
#options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

remote_server_url = "http://standalone-chrome:4444/wd/hub"

# webドライバの初期化
driver = webdriver.Remote(
    command_executor=remote_server_url,
    options=options
)

os.makedirs("/workspace/download/", exist_ok=True)

def clicker(target, xpath=None):
    next_url = None
    # ひとつめの引数で指定されたURLにアクセス
    driver.get(target)
    
    # ふたつめの引数でXpathが指定されている場合はその要素を取得する
    if xpath:
        # Xpathで指定された要素が見つかるまで待機する
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        href = element.get_attribute("href")
        
        if href:
            # Xpathで指定された要素にhrefがあればそのURLを戻り値とする
            next_url = href
        else:
            # Xpathで指定された要素にhrefがなければその要素をクリックする
            element.click()
            # クリック後に遷移したページのURLを戻り値とする
            next_url = driver.current_url

            # ひとつめの引数で指定されたURLがedgeのものであれば，動的に生成されるページなので下記の特別な手順を行う
            if target == "https://www.microsoft.com/ja-jp/edge/business/download":
                # ふたつめの引数で指定されたXpathをクリックした後に，同意してダウンロード のボタンが表示されるまで待つ
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="eula-dialog"]/div[5]/a'))
                )
                # 同意してダウンロード のボタンにあるhrefのURLを取得して戻り値とする
                href = element.get_attribute("href")
                next_url = href

    else:
        parsed_url = urlparse(target)
        file_name = unquote(os.path.basename(parsed_url.path))
        save_path = os.path.join('/workspace/download/', file_name)

        with urllib.request.urlopen(target) as web_file, open(save_path, 'wb') as local_file:
            local_file.write(web_file.read())
        print(f"ファイルを保存しました: {save_path}")

    return next_url



def find_policy_report_folder(base_path):
    # "PolicyReport" を含むフォルダを検索
    for root, dirs, files in os.walk(base_path):
        for dir_name in dirs:
            if "PolicyReport" in dir_name:
                return os.path.join(root, dir_name)
    return None

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
                                f"一致しました: ファイル: {file_path}, 行番号: {line_number}, "
                                f"内容: {line.strip()}, 元のHTMLファイル: {source_html_file}\n"
                            )
                            print(output_line.strip())  # コンソールに出力
                            out_file.write(output_line)  # ファイルに出力

def process_html_files(folder_path, diff_output_folder, output_file):
    # フォルダ内のすべてのファイルを処理
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            
            # HTMLファイルを読み込む
            with open(file_path, 'r', encoding='utf-16') as html_file:
                html_content = html_file.read()

            # BeautifulSoupオブジェクトの作成
            soup = BeautifulSoup(html_content, 'html.parser')

            # spanタグを取得し、gpmc_settingname属性の値を抽出
            span = soup.find('span', attrs={'gpmc_settingname': True})
            if span:
                gpmc_settingname_value = span['gpmc_settingname']
                
                # DiffOutputフォルダ内で検索 (元のHTMLファイル名を渡す)
                search_in_diff_output_folder(gpmc_settingname_value, diff_output_folder, file_path, output_file)

