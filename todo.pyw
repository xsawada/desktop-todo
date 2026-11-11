"""
いつも最前面に表示される、シンプルなToDoリスト（起動用のファイル）

第1段階：タスクの追加・一覧表示・完了（削除）
第2段階：JSONファイルへの保存と、起動時の読み込み
第3段階：期限の入力、期限が近い順の並べ替え、期限切れ・当日の色分け
第4段階：登録したタスクの修正（ダブルクリックまたは「編集」ボタン）
第5段階：役割ごとにモジュールを分割

  todo.py     … 起動するだけ（このファイル）
  gui.py      … 画面（窓・ボタン・修正画面）
  deadline.py … 期限の読み取り・表示形式・並び順
  storage.py  … tasks.json の読み込みと保存
  config.py   … 見た目と動作の設定

実行方法：python todo.py
（Windowsでは拡張子を .pyw にすると、黒いコンソール画面が出ません。
  5つのファイルは同じフォルダに置いてください）
"""
import tkinter as tk

from gui import TodoApp


def main():
    root = tk.Tk()
    TodoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
