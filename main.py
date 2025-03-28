import functions
import os
import zipfile
import shutil
import glob
import subprocess


if __name__ == "__main__":

    # Webからファイルを取得
    try:
        # # windows
        # win_latest_policy_link = functions.clicker(
        #     "https://learn.microsoft.com/en-us/troubleshoot/windows-client/group-policy/create-and-manage-central-store#links-to-download-the-administrative-templates-files-based-on-the-operating-system-version",
        #     '/html/body/div[2]/div/section/div/div[1]/main/div[3]/ul[1]/li[1]/a'
        # )
        # win_download_link = functions.clicker(win_latest_policy_link,'//*[@id="rootContainer_DLCDetails"]/section[3]/div/div/div/div/div/a')
        # win_download = functions.clicker(win_download_link)
        
        # edge
        edge_download_link = functions.clicker(
            "https://www.microsoft.com/ja-jp/edge/business/download",
            '//*[@id="main"]/div/div[1]/div[1]/section[1]/div/div/div/div[3]/div[1]/div[2]/button[2]'
            )
        edge_download = functions.clicker(edge_download_link)

        # chrome
        chrome_template_download = functions.clicker("https://dl.google.com/dl/edgedl/chrome/policy/policy_templates.zip")
        chrome_update_download = functions.clicker("http://dl.google.com/update2/enterprise/googleupdateadmx.zip")

        # # office
        # office_download_link = functions.clicker(
        #     "https://www.microsoft.com/en-us/download/details.aspx?id=49030",
        #     "//*[@id="dlc-details-multi-download-modal"]/div/div/div[2]/div/table/tbody/tr[2]/td[1]/div"
        #     )
        # office_download = functions.clicker(office_download_link)

    finally:
        functions.driver.quit()


    # ファイルを比較可能な状態に整える
    # 必要なディレクトリを作成
    os.makedirs("/workspace/download/new_policy/", exist_ok=True)

    # .cab ファイルを .zip に変換する
    subprocess.run(["cabextract", "-d", "/workspace/download/", "/workspace/download/MicrosoftEdgePolicyTemplates.cab"])

    # .zip を解凍
    with zipfile.ZipFile("/workspace/download/MicrosoftEdgePolicyTemplates.zip", 'r') as zip_ref:
        zip_ref.extractall("/workspace/download/new_policy/MicrosoftEdgePolicyTemplates")

    with zipfile.ZipFile("/workspace/download/policy_templates.zip", 'r') as zip_ref:
        zip_ref.extractall("/workspace/download/new_policy/policy_templates")

    with zipfile.ZipFile("/workspace/download/googleupdateadmx.zip", 'r') as zip_ref:
        zip_ref.extractall("/workspace/download/new_policy/googleupdateadmx")

    # .zip と .cab 拡張子のファイルを削除
    for file_extension in ["*.zip", "*.cab"]:
        for file in glob.glob(f"/workspace/download/{file_extension}"):
            os.remove(file)

    # OneDrive.admlを移動
    shutil.copy("/workspace/download/OneDrive.adml", "/workspace/download/new_policy/")

    # 既存ポリシーテンプレートを複製
    shutil.copytree(
        "/workspace/download/PolicyDefinitions/",
        "/workspace/download/new_PolicyDefinitions/",
        dirs_exist_ok=True
    )

    # 既存のポリシーファイルの中で、更新があったファイルのみ、新しいファイルで上書きする
    source_folder = "/workspace/download/new_policy"
    destination_folder = "/workspace/download/new_PolicyDefinitions"

    # フォルダA内のすべてのファイルを再帰的に取得
    for root, dirs, files in os.walk(source_folder):
        # "ja-JP"以外の"xx-XX"または"xx-XXX"形式のサブフォルダをスキップ
        if any(part for part in root.split(os.sep) if part != "ja-JP" and len(part) >= 5 and '-' in part):
            continue  # 条件を満たした場合スキップ

        for file in files:
            source_file = os.path.join(root, file)

            # フォルダB内で同名ファイルを検索
            for dest_root, dest_dirs, dest_files in os.walk(destination_folder):
                if file in dest_files:
                    destination_file = os.path.join(dest_root, file)

                    # 上書きコピーを実行
                    shutil.copy2(source_file, destination_file)
                    print(f"上書きしました: {source_file} -> {destination_file}")


    # ファイルを比較する
    # フォルダAとフォルダBのパスを指定
    folder_a = "/workspace/download/PolicyDefinitions"
    folder_b = "/workspace/download/new_PolicyDefinitions"
    output_folder = "/workspace/DiffOutput"  # 差分出力用のフォルダ

    # 差分出力フォルダを作成（存在しない場合）
    os.makedirs(output_folder, exist_ok=True)

    # フォルダA内のすべての`.adml`ファイルを再帰的に処理
    for root_a, dirs_a, files_a in os.walk(folder_a):
        for file_name in files_a:
            # `.adml`拡張子のファイルのみを対象
            if not file_name.endswith('.adml'):
                continue

            file_a_path = os.path.join(root_a, file_name)

            # フォルダB内で同じ相対パスを持つファイルを探す
            relative_path = os.path.relpath(file_a_path, folder_a)
            file_b_path = os.path.join(folder_b, relative_path)

            # フォルダBに対応するファイルが存在する場合のみ比較
            if os.path.exists(file_b_path):
                try:
                    # UTF-8で比較
                    functions.compare_text_files(file_a_path, file_b_path, 'utf-8', relative_path, folder_a, folder_b, output_folder)

                except UnicodeDecodeError:
                    # UTF-16で再試行
                    functions.compare_text_files(file_a_path, file_b_path, 'utf-16', relative_path, folder_a, folder_b, output_folder)



    # 差分ファイルに使用中のポリシーが含まれているか確認する
    # 基準となるディレクトリを指定
    base_path = "/workspace/download/"
    diff_output_folder = "/workspace/DiffOutput/"
    output_file = "/workspace/output_results.txt"  # 出力ファイルのパス

    # 出力ファイルを初期化
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("検索結果:\n\n")

    # "PolicyReport" を含むフォルダを検索
    policy_report_folder = functions.find_policy_report_folder(base_path)
    
    if policy_report_folder:
        print(f"対象のフォルダが見つかりました: {policy_report_folder}")
        functions.process_html_files(policy_report_folder, diff_output_folder, output_file)
        print(f"検索結果を {output_file} に保存しました。")
    else:
        print("指定されたディレクトリ内に 'PolicyReport' を含むフォルダが見つかりませんでした。")

