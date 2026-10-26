"""
いつも最前面に表示される、シンプルなToDoリスト

第1段階：タスクの追加・一覧表示・完了（削除）
第2段階：JSONファイルへの保存と、起動時の読み込み

実行方法：python todo.py
（Windowsでは拡張子を .pyw にすると、黒いコンソール画面が出ません）
"""
import json
import os
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

# 保存先：このスクリプトと同じフォルダの tasks.json
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")

# 1件のタスクに入力できる最大文字数
MAX_LENGTH = 50

# ------------------------------------------------------------
# 見た目の設定（ここの数字や色を変えると、デザインが変わる）
# ------------------------------------------------------------
FONT_NAME = "Meiryo UI"     # 文字の種類（例："Yu Gothic UI", "BIZ UDPGothic"）
FONT_SIZE = 13              # 一覧・入力欄の文字の大きさ
SMALL_FONT_SIZE = 11        # ボタン・件数表示の文字の大きさ
WINDOW_SIZE = "380x500"     # 窓の大きさ（横x縦）

BG_COLOR = "#FAF7F2"        # 窓の背景色
LIST_BG = "#FFFFFF"         # 一覧の背景色
TEXT_COLOR = "#333333"      # 文字の色
SELECT_COLOR = "#CFE3D4"    # 選んだタスクの色
BUTTON_COLOR = "#7FA88A"    # 追加ボタンの色
BUTTON_TEXT = "#FFFFFF"     # 追加ボタンの文字の色


# ------------------------------------------------------------
# データの読み書き（画面とは切り離しておく）
# ------------------------------------------------------------
def load_tasks(path):
    """
    ファイルからタスクを読み込む。
    戻り値：(タスクのリスト, 警告メッセージ または None)
    """
    if not os.path.exists(path):
        return [], None  # 初回起動時はファイルが無いので空で始める

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        # 壊れたファイルは消さずに退避し、空の状態で始める
        backup = path + ".broken"
        os.replace(path, backup)
        return [], f"保存ファイルが読み込めませんでした。\n元のファイルは {os.path.basename(backup)} として残してあります。"

    if not isinstance(data, list):
        return [], "保存ファイルの形式が正しくないため、空の状態で始めます。"

    # 形式が正しい行だけを採用し、おかしな行は数を数えておく
    tasks = []
    skipped = 0
    for item in data:
        if isinstance(item, dict) and isinstance(item.get("text"), str) and item["text"].strip():
            tasks.append(item)
        else:
            skipped += 1

    message = f"形式が正しくないデータが {skipped} 件あったため、読み飛ばしました。" if skipped else None
    return tasks, message


def save_tasks(path, tasks):
    """
    タスクをファイルに保存する。
    いったん一時ファイルに書いてから置き換えるので、
    保存の途中で止まっても元のファイルが壊れない。
    """
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


# ------------------------------------------------------------
# 画面
# ------------------------------------------------------------
class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ToDo")
        self.root.geometry(WINDOW_SIZE)
        self.root.configure(bg=BG_COLOR)
        self.root.attributes("-topmost", True)  # いつも最前面に表示

        # よく使う文字の設定をまとめておく
        self.font = (FONT_NAME, FONT_SIZE)
        self.small_font = (FONT_NAME, SMALL_FONT_SIZE)

        self.build_widgets()

        # 起動時にファイルから読み込む
        self.tasks, warning = load_tasks(DATA_FILE)
        if warning:
            messagebox.showwarning("読み込みについて", warning, parent=self.root)
        self.refresh_list()

    def build_widgets(self):
        # --- 入力欄と追加ボタン ---
        input_frame = tk.Frame(self.root, bg=BG_COLOR)
        input_frame.pack(fill="x", padx=12, pady=12)

        self.entry = tk.Entry(
            input_frame, font=self.font, fg=TEXT_COLOR,
            relief="solid", bd=1,
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.entry.bind("<Return>", lambda event: self.add_task())  # Enterキーでも追加
        self.entry.focus_set()

        tk.Button(
            input_frame, text="追加", command=self.add_task,
            font=self.small_font, bg=BUTTON_COLOR, fg=BUTTON_TEXT,
            activebackground=BUTTON_COLOR, activeforeground=BUTTON_TEXT,
            relief="flat", padx=12, cursor="hand2",
        ).pack(side="left", padx=(8, 0), fill="y")

        # --- タスク一覧（スクロールバー付き） ---
        list_frame = tk.Frame(self.root, bg=BG_COLOR)
        list_frame.pack(fill="both", expand=True, padx=12)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            list_frame, yscrollcommand=scrollbar.set,
            font=self.font, fg=TEXT_COLOR, bg=LIST_BG,
            selectbackground=SELECT_COLOR, selectforeground=TEXT_COLOR,
            relief="solid", bd=1, highlightthickness=0,
            activestyle="none",
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<Delete>", lambda event: self.complete_task())  # Deleteキーでも完了
        scrollbar.config(command=self.listbox.yview)

        # --- 下部：完了ボタンと最前面の切り替え ---
        bottom_frame = tk.Frame(self.root, bg=BG_COLOR)
        bottom_frame.pack(fill="x", padx=12, pady=10)

        tk.Button(
            bottom_frame, text="完了（削除）", command=self.complete_task,
            font=self.small_font, fg=TEXT_COLOR, relief="groove",
            padx=8, cursor="hand2",
        ).pack(side="left")

        self.topmost_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            bottom_frame, text="最前面に表示",
            variable=self.topmost_var, command=self.toggle_topmost,
            font=self.small_font, fg=TEXT_COLOR,
            bg=BG_COLOR, activebackground=BG_COLOR,
        ).pack(side="right")

        # --- 件数表示 ---
        self.status = tk.Label(
            self.root, anchor="w", fg="gray",
            font=self.small_font, bg=BG_COLOR,
        )
        self.status.pack(fill="x", padx=12, pady=(0, 10))

    # ---- 操作 ----
    def add_task(self):
        text = self.entry.get().strip()

        # 入力チェック
        if not text:
            messagebox.showwarning("入力エラー", "タスクを入力してください。", parent=self.root)
            return
        if len(text) > MAX_LENGTH:
            messagebox.showwarning(
                "入力エラー",
                f"{MAX_LENGTH}文字以内で入力してください。（いま {len(text)} 文字）",
                parent=self.root,
            )
            return
        if any(task["text"] == text for task in self.tasks):
            if not messagebox.askyesno("確認", f"「{text}」はすでにあります。\nそれでも追加しますか？", parent=self.root):
                return

        self.tasks.append({
            "text": text,
            "created": datetime.now().isoformat(timespec="seconds"),
        })
        if self.save():
            self.entry.delete(0, tk.END)
        self.refresh_list()

    def complete_task(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo("お知らせ", "完了したタスクを一覧から選んでください。", parent=self.root)
            return

        index = selected[0]
        removed = self.tasks.pop(index)
        if not self.save():
            self.tasks.insert(index, removed)  # 保存に失敗したら元に戻す
        self.refresh_list()

    def toggle_topmost(self):
        self.root.attributes("-topmost", self.topmost_var.get())

    # ---- 補助 ----
    def save(self):
        """保存して、成功したら True を返す"""
        try:
            save_tasks(DATA_FILE, self.tasks)
            return True
        except OSError as e:
            messagebox.showerror("保存エラー", f"保存できませんでした。\n{e}", parent=self.root)
            return False

    def refresh_list(self):
        """一覧を tasks の内容で描き直す"""
        self.listbox.delete(0, tk.END)
        for task in self.tasks:
            self.listbox.insert(tk.END, "・" + task["text"])
        self.status.config(text=f"残り {len(self.tasks)} 件")


if __name__ == "__main__":
    root = tk.Tk()
    TodoApp(root)
    root.mainloop()
