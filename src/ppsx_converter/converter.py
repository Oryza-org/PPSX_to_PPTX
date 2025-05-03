import uno
import unohelper
import sys
import os
import time
# --- UNO例外クラスのインポート ---
# 変換処理に必要な基本的なUNO例外をインポート
from com.sun.star.uno import Exception as UnoException
from com.sun.star.connection import NoConnectException
from com.sun.star.io import IOException
from com.sun.star.lang import DisposedException, IllegalArgumentException
from com.sun.star.script import CannotConvertException
from com.sun.star.uno import RuntimeException
from com.sun.star.task import ErrorCodeIOException
# --- UNO列挙型（Enum）のインポート ---
from com.sun.star.document.UpdateDocMode import NO_UPDATE

# --- ANSII CODE
ESC = '\x1b'
GREEN = f'{ESC}[32m'
YELLOW = f'{ESC}[33m'
RED = f'{ESC}[31m'
RESET = f'{ESC}[0m'

def printMsg(message):
    print(f"{message}", end='')

def printStatus(status, color):
    print(f"{color}[{status}]{RESET}")

# --- 設定 ---
# OfficeインスタンスのUNO URL
UNO_HOST = "localhost"
UNO_PORT = "2002"
UNO_URL = f"uno:socket,host={UNO_HOST},port={UNO_PORT};urp;StarOffice.ComponentContext"

# 接続リトライ設定
MAX_RETRY_ATTEMPTS = 10
RETRY_DELAY_SECONDS = 1

# --- UNO連携ヘルパー関数 ---

def UnoProps(**args):
    """UNOプロパティのタプルを作成"""
    props = []
    for key in args:
        prop = uno.createUnoStruct("com.sun.star.beans.PropertyValue")
        prop.Name = key
        prop.Value = args[key]
        props.append(prop)
    return tuple(props)

# --- UNO連携クラス ---

class OfficeConverter:
    """Officeインスタンスへの接続と変換を管理"""
    def __init__(self, uno_url):
        printMsg("--- Connecting to Office instance...")
        self.context = self._get_uno_context_with_retry(uno_url)
        if self.context is None:
            # 接続に失敗した場合はエラーを発生させる
            printStatus("ERROR", RED)
            raise ConnectionError("Failed to obtain UNO context after retries.")

        printMsg("--- Creating desktop component...")
        try:
            self.svcmgr = self.context.getServiceManager()
            self.desktop = self.svcmgr.createInstanceWithContext("com.sun.star.frame.Desktop", self.context)
        except Exception as e:
            # ServiceManager/Desktop取得エラー
            printStatus("ERROR", RED)
            raise RuntimeError(f"Error obtaining ServiceManager or Desktop: {e}") from e
        printStatus("OK", GREEN)

    def _get_uno_context_with_retry(self, uno_url):
        """UNOコンテキストをリトライして取得"""
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                # 接続試行メッセージを簡潔に
                if attempt > 0:
                    printStatus("RETRY", YELLOW)
                    printMsg(f"--- Attempt {attempt + 1}/{MAX_RETRY_ATTEMPTS}: Retrying connection...")

                localContext = uno.getComponentContext()
                resolver = localContext.getServiceManager().createInstanceWithContext(
                    "com.sun.star.bridge.UnoUrlResolver", localContext)
                ctx = resolver.resolve(uno_url)
                printStatus("OK", GREEN)
                return ctx
            except Exception as e:
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    # 最終的な接続失敗メッセージ
                    printStatus("ERROR", RED)
                    print(f"--- Failed to connect to UNO context at {uno_url} after {MAX_RETRY_ATTEMPTS} attempts.")
                    return None
        return None

    def convert(self, input_path, output_path, password=None):
        """ファイルを読み込みPPTXで保存"""
        document = None
        try:
            input_url = unohelper.systemPathToFileUrl(input_path)
            output_url = unohelper.systemPathToFileUrl(output_path)

            # ロードプロパティ
            load_properties = UnoProps(
                Hidden=True,
                ReadOnly=True,
                UpdateDocMode=NO_UPDATE
            )
            if password:
                 load_properties += UnoProps(Password=password)

            printMsg(f"--- Loading document: {input_path}...")
            document = self.desktop.loadComponentFromURL(input_url, "_blank", 0, load_properties)
            if document is None:
                 # ロード失敗時はUNO例外を発生
                 printStatus("ERROR", RED)
                 raise UnoException(f"Failed to load document from URL: {input_url}. loadComponentFromURL returned None.", self.context)
            printStatus("OK", GREEN)

            # PresentationDocumentか確認
            if not document.supportsService("com.sun.star.presentation.PresentationDocument"):
                raise TypeError("Opened document is not a presentation document.")

            # 保存プロパティ (PPTX固定)
            save_properties = UnoProps(
                FilterName="Impress MS PowerPoint 2007 XML",
                Overwrite=True
            )

            printMsg(f"--- Saving document to: {output_path}...")
            document.storeAsURL(output_url, save_properties)
            printStatus("OK", GREEN)
        # --- 例外処理を簡潔化 ---
        # UNO関連の既知の例外をまとめて捕捉
        except (UnoException, ErrorCodeIOException, IOException, NoConnectException, DisposedException, IllegalArgumentException, CannotConvertException, RuntimeException) as e:
             print(f"--- Error during conversion...")
             print(f"Error Type: {type(e).__name__}") # 例外のクラス名を表示
             if hasattr(e, 'Message'):
                  print(f"Message: {e.Message}")
             if hasattr(e, 'ErrCode'):
                  print(f"ErrCode: {e.ErrCode}")
             raise # エラーを呼び出し元に伝える
        except Exception as e:
            # その他の予期しない例外
            print(f"--- An unexpected error occurred...")
            print(f"Error Type: {type(e).__name__}") # 例外のクラス名を表示
            print(f"Message: {e}")
            raise # エラーを呼び出し元に伝える
        # --- 例外処理ここまで ---

        finally:
            # ドキュメントのクリーンアップ
            if document:
                try:
                    if hasattr(document, 'dispose'):
                        document.dispose()
                    elif hasattr(document, 'close'):
                        document.close(True)
                except Exception as e:
                    # クリーンアップ中のエラーは警告として表示
                    print(f"--- {RED}[ERROR]{RESET} Warning: Error during document cleanup: {e}")


def main():
    """コマンドライン引数を処理し、変換を実行する"""
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python src/ppsx_converter/converter.py <input_file_path> <output_file_path> [password]")
        print("Ensure Office is running in UNO listening mode (e.g., soffice --accept=socket,host=localhost,port=2002;urp; --headless)")
        sys.exit(1) # 引数エラー時はここで終了

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    file_password = sys.argv[3] if len(sys.argv) == 4 else None

    # 入力ファイルの存在チェック
    if not os.path.exists(input_file):
        print(f"--- {RED}[ERROR]{RESET} Input file not found at {input_file}")
        sys.exit(1) # ファイルが見つからない場合はここで終了

    # 変換処理の実行 (エラーは呼び出し元に raise される)
    converter = OfficeConverter(UNO_URL)
    converter.convert(input_file, output_file, file_password)
    print(f"--- {GREEN}[OK]{RESET} Conversion Successful")


# --- スクリプトとして実行された場合のみ main() を呼び出す ---
if __name__ == "__main__":
    try:
        main()
        sys.exit(0) # 成功時はここで終了
    except ConnectionError as e:
        # OfficeConverter __init__ または convert 内で発生し捕捉された ConnectionError
        print(f"--- {RED}[ERROR]{RESET} Connection Error: {e}")
        print("--- Please ensure Office is running in UNO listening mode.")
        sys.exit(1)
    except Exception as e:
        # main() 内の引数エラーやファイルチェック以外の、予期せぬエラー
        print(f"--- {RED}[ERROR]{RESET} An unexpected error occurred during execution: {e}")
        sys.exit(1)

# 実行中のOfficeインスタンスは自動終了しないため、run.cmdなどの外部スクリプトで終了させる必要があります。