# mecab_windows_setup_revised.py
import os
import sys
import shutil
import subprocess
from pathlib import Path

def setup_mecab_for_windows():
    # MeCabのインストールパス
    mecab_install_dir = Path("C:/Program Files/MeCab")
    
    # 環境変数を設定
    os.environ["PATH"] = f"{mecab_install_dir};{os.environ['PATH']}"
    
    # Pythonの環境設定
    site_packages = Path(sys.prefix) / "Lib/site-packages"
    unidic_dir = site_packages / "unidic"
    unidic_dicdir = unidic_dir / "dicdir"
    
    # 必要なディレクトリを作成
    unidic_dicdir.mkdir(exist_ok=True, parents=True)
    
    # MeCabの辞書ファイルをコピー
    mecab_dic_dir = mecab_install_dir / "dic/ipadic"
    if mecab_dic_dir.exists():
        print(f"MeCab辞書ディレクトリが見つかりました: {mecab_dic_dir}")
        for file in mecab_dic_dir.glob("*"):
            target = unidic_dicdir / file.name
            shutil.copy(file, target)
            print(f"ファイルをコピー: {file} -> {target}")
    else:
        print(f"MeCab辞書ディレクトリが見つかりません: {mecab_dic_dir}")
    
    # パスを正規化
    unidic_dicdir_str = str(unidic_dicdir).replace('\\', '/')
    dicrc_path_str = str(unidic_dicdir / 'dicrc').replace('\\', '/')
    
    # mecabrcファイルを作成/更新
    mecabrc_content = """
dicdir = {0}
userdic =
debug = 0
maxopt = 2
dicinfo = {1}
output-format-type = wakati
""".format(unidic_dicdir_str, dicrc_path_str)
    
    # 適切な場所にmecabrcを作成
    mecab_dir = Path("c:/mecab")
    app_data_dir = Path(os.environ.get("APPDATA", "")) / "MeCab"
    
    paths_to_create = [
        mecab_dir / "mecabrc",
        unidic_dicdir / "mecabrc",
        app_data_dir / "mecabrc"  # AppDataディレクトリに作成
    ]
    
    for path in paths_to_create:
        path.parent.mkdir(exist_ok=True, parents=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(mecabrc_content)
        print(f"mecabrcファイルを作成しました: {path}")
    
    # 環境変数の設定
    mecabrc_path = str(mecab_dir / "mecabrc")
    os.environ["MECABRC"] = mecabrc_path
    print(f"環境変数MECABRCを設定しました: {mecabrc_path}")
    
    # windowsレジストリに環境変数を登録（再起動後も有効にするため）
    try:
        subprocess.run([
            "powershell", 
            '[Environment]::SetEnvironmentVariable("MECABRC", "{0}", "User")'.format(mecabrc_path)
        ], check=True)
        print("環境変数MECABRCをユーザー環境変数に設定しました")
    except Exception as e:
        print(f"環境変数の設定に失敗しました: {e}")
    
    print("MeCabの設定が完了しました。")

if __name__ == "__main__":
    setup_mecab_for_windows()