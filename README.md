# ppsx-converter

## 概要

このプロジェクトは、Microsoft PowerPoint ショー ファイル (.ppsx) を Microsoft PowerPoint プレゼンテーション ファイル (.pptx) に変換する Python スクリプトを提供します。変換処理には LibreOffice または OpenOffice の UNO (Universal Network Objects) インターフェースを利用します。

## ファイル構成

```
ppsx-converter/
├── src/                   # ソースコード
│   └── ppsx_converter/    # Pythonパッケージ
│       ├── __init__.py    # パッケージ初期化ファイル
│       └── converter.py   # ★主要な変換スクリプト
├── scripts/               # 補助スクリプト
│   └── show_filters.py    # 利用可能なフィルター情報表示スクリプト
├── data/                  # 参考データ
│   └── FilterType.txt     # LibreOffice/OpenOffice フィルター情報リスト
├── examples/              # サンプルファイル置き場 (手動で配置)
│   └── (ここに test.pptx などを配置)
├── .gitignore             # Git バージョン管理用 除外リスト
├── requirements.txt       # 依存関係についての注意書き
└── README.md              # このファイル
```

## 必要なもの

* **Python 3.x**
* **LibreOffice または OpenOffice:** システムにインストールされている必要があります。
* **Python UNO ライブラリ (`uno`, `unohelper`):**
    * **重要:** このスクリプトは、**LibreOffice/OpenOffice に同梱されている Python 環境** から実行する必要があります。お使いのOSに別途インストールされた Python (コマンドプロンプトで `python` と打って起動する等) から実行すると、通常 `uno` モジュールが見つからず `ModuleNotFoundError` が発生します。
    * UNO ライブラリは通常、LibreOffice/OpenOffice のインストールに含まれており、`pip install` 等で別途インストールするものではありません。
* **実行中の Office インスタンス:** スクリプトを実行する*前*に、LibreOffice/OpenOffice が UNO リスニングモードで実行されている必要があります。通常、コマンドラインから次のように起動できます：
    ```bash
    # Linux/macOS の例 (sofficeのパスは環境による場合があります)
    # 例: /usr/bin/soffice や /opt/libreofficeX.X/program/soffice など
    soffice --accept="socket,host=localhost,port=2002;urp;" --headless --invisible &

    # Windows の例 (パスはご自身の環境に合わせてください)
    # start "" はコマンドプロンプトでバックグラウンド実行するためのものです
    start "" "C:\Program Files\LibreOffice\program\soffice.exe" --accept="socket,host=localhost,port=2002;urp;" --headless --invisible
    ```
    *(注意: `--headless` や `--invisible`、バックグラウンド実行(`&`, `start`)の方法は環境によって調整が必要な場合があります。リスニングモードで起動していることが重要です。)*

## 設定

接続先の Office インスタンスのホストとポートは `src/ppsx_converter/converter.py` スクリプト内で設定されています。デフォルトは以下の通りです。

* ホスト: `localhost`
* ポート: `2002`

必要に応じて、これらの設定はスクリプト内で直接変更できます。接続確立のためのリトライロジックも含まれています。

## 使い方

### PPSX から PPTX への変換

1.  上記の「必要なもの」に記載されている通り、LibreOffice/OpenOffice を UNO リスニングモードで**起動しておきます**。
2.  **LibreOffice/OpenOffice に同梱されている Python を使って**、コマンドラインから以下のコマンドを実行します。
    **Windows の例:**
    ```bash
    # "C:\Program Files\LibreOffice" の部分は実際のインストールパスに置き換えてください
    "C:\Program Files\LibreOffice\program\python.exe" src\ppsx_converter\converter.py <入力ファイルの絶対パス.ppsx> <出力ファイルの絶対パス.pptx> [パスワード]
    ```
    実行例:
    ```bash
    "C:\Program Files\LibreOffice\program\python.exe" src\ppsx_converter\converter.py C:\Users\YourUser\Documents\presentation.ppsx C:\Users\YourUser\Documents\converted_presentation.pptx
    ```

    **Linux/macOS の例:**
    ```bash
    # LibreOffice 同梱の python へのパスは環境により異なります。
    # 例: /usr/lib/libreoffice/program/python, /opt/libreoffice7.6/program/python など
    /path/to/libreoffice/program/python src/ppsx_converter/converter.py <入力ファイルの絶対パス.ppsx> <出力ファイルの絶対パス.pptx> [パスワード]
    ```
    実行例:
    ```bash
    /usr/lib/libreoffice/program/python src/ppsx_converter/converter.py /home/user/docs/presentation.ppsx /home/user/docs/converted_presentation.pptx
    ```

    **引数の説明:**
    * `<入力ファイルの絶対パス.ppsx>`: 変換したい PPSX ファイルの**絶対パス**を指定します。
    * `<出力ファイルの絶対パス.pptx>`: 保存する PPTX ファイルの**絶対パス**を指定します。**相対パス (`output.pptx` 等) ではなく、ディレクトリを含めた絶対パス (`C:\output\dir\output.pptx` や `/home/user/output/output.pptx` 等) で指定することを強く推奨します。** これにより予期せぬ保存エラーを防ぐことができます。また、入力ファイルとは**異なる**ファイル名を指定してください。
    * `[パスワード]`: (オプション) 入力ファイルがパスワードで保護されている場合に指定します。**パスワードが設定されていない場合は、この引数は指定しないでください。**

### 利用可能なフィルターの表示 (補助スクリプト)

`scripts/show_filters.py` は、LibreOffice/OpenOffice のレジストリ設定ファイル (XML) から、利用可能なインポート/エクスポートフィルターの一覧を CSV 形式で出力する補助スクリプトです。`converter.py` で使用する `FilterName` を調べる際などに役立ちます。

使い方例:

```bash
# Windows例 (レジストリファイルのパスは環境により異なります)
"C:\Program Files\LibreOffice\program\python.exe" scripts/show_filters.py "C:\Program Files\LibreOffice\share\registry\registrymodifications.xcu"

# Linux/macOS例
/path/to/libreoffice/program/python scripts/show_filters.py /usr/lib/libreoffice/share/registry/registrymodifications.xcu

# ファイルに出力する場合
"C:\Program Files\LibreOffice\program\python.exe" scripts/show_filters.py "path/to/registrymodifications.xcu" -o filters_list.csv
```
*(注意: レジストリファイルのパスは環境によって異なります)*

## 注意点

* `requirements.txt` に記載されている通り、`uno` および `unohelper` は `pip` でインストールするものではありません。LibreOffice/OpenOffice のインストールが必要です。
* 変換スクリプトを実行するには、事前に LibreOffice/OpenOffice を UNO リスニングモードで起動しておく必要があります。
* スクリプト実行後、起動した Office インスタンスは自動的に終了しません。手動で終了させるか、プロセス管理を行ってください。
* `examples/` ディレクトリには、サンプルの `.ppsx` ファイルや変換後の `.pptx` ファイル (`test.pptx`など) を手動で配置してご利用ください。このスクリプトでは `examples` ディレクトリを作成するのみです。

## ライセンス

(ここにライセンス情報を記述してください)