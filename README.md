# PPSX to PPTX 変換ツール

## 概要

このスクリプトは、Microsoft PowerPoint ショー ファイル (.ppsx) を Microsoft PowerPoint プレゼンテーション ファイル (.pptx) に変換します [cite: 4]。変換処理には、LibreOffice/OpenOffice の UNO (Universal Network Objects) インターフェースを利用します。

## 必要なもの

* **Python 3.x**
* **LibreOffice または OpenOffice:** システムにインストールされている必要があります。
* **Python UNO ライブラリ:** (`uno`, `unohelper`) - 通常、LibreOffice/OpenOffice に同梱されていますが、OS やインストール方法によっては別途インストールが必要な場合があります。
* **実行中の Office インスタンス:** スクリプトを実行する*前*に、LibreOffice/OpenOffice が UNO リスニングモードで実行されている必要があります。通常、コマンドラインから次のように起動できます：

    ```bash
    soffice --accept="socket,host=localhost,port=2002;urp;" --headless
    ```
    *(注意: ご利用のシステムに合わせて `soffice` コマンドやパスを調整してください。)*

## 設定 (`convert.py`)

スクリプトは、ソケット接続を介して実行中の Office インスタンスに接続します。デフォルト設定は以下の通りです：
* **ホスト:** `localhost`
* **ポート:** `2002`

必要に応じて、これらの設定は `convert.py` スクリプト内で直接変更できます。スクリプトには接続確立のためのリトライロジックが含まれています。

## 使い方 (`convert.py`)

コマンドラインからスクリプトを実行します：

```bash
python convert.py <入力ファイル.ppsx> <出力ファイル.pptx> [パスワード]
