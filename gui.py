"""
画面（ToDoの窓・ボタン・修正画面）

画面の組み立てと操作だけを担当し、
期限の処理は deadline.py、保存は storage.py、見た目の設定は config.py に任せている。
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

from config import (
    MAX_LENGTH, FONT_NAME, FONT_SIZE, SMALL_FONT_SIZE, WINDOW_SIZE,
    BG_COLOR, LIST_BG, TEXT_COLOR, SELECT_COLOR, BUTTON_COLOR, BUTTON_TEXT,
    OVERDUE_COLOR, TODAY_COLOR,
)
from deadline import parse_deadline, format_deadline, deadline_to_input, sort_key
from storage import DATA_FILE, load_tasks, save_tasks


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
        self.schedule_refresh()

    def build_widgets(self):
        # --- 表の見た目（ttk の部品はスタイルで設定する） ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview", font=self.font, rowheight=int(FONT_SIZE * 2.4),
            background=LIST_BG, fieldbackground=LIST_BG, foreground=TEXT_COLOR,
        )
        style.configure("Treeview.Heading", font=self.small_font)
        style.map("Treeview", background=[("selected", SELECT_COLOR)],
                  foreground=[("selected", TEXT_COLOR)])

        # --- 入力欄：タスク・期限・追加ボタン ---
        input_frame = tk.Frame(self.root, bg=BG_COLOR)
        input_frame.pack(fill="x", padx=12, pady=(12, 2))

        self.entry = tk.Entry(input_frame, font=self.font, fg=TEXT_COLOR, relief="solid", bd=1)
        self.entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.entry.bind("<Return>", lambda event: self.add_task())  # Enterキーでも追加
        self.entry.focus_set()

        self.deadline_entry = tk.Entry(input_frame, font=self.font, fg=TEXT_COLOR,
                                       relief="solid", bd=1, width=8)
        self.deadline_entry.pack(side="left", padx=(6, 0), ipady=4)
        self.deadline_entry.bind("<Return>", lambda event: self.add_task())

        tk.Button(
            input_frame, text="追加", command=self.add_task,
            font=self.small_font, bg=BUTTON_COLOR, fg=BUTTON_TEXT,
            activebackground=BUTTON_COLOR, activeforeground=BUTTON_TEXT,
            relief="flat", padx=12, cursor="hand2",
        ).pack(side="left", padx=(8, 0), fill="y")

        # 入力欄の説明
        tk.Label(
            self.root, text="右の欄に期限（例：10/31）。空欄なら期限なし",
            font=(FONT_NAME, SMALL_FONT_SIZE - 1), fg="gray", bg=BG_COLOR, anchor="e",
        ).pack(fill="x", padx=12, pady=(0, 8))

        # --- タスク一覧：「タスク｜期限」の表（スクロールバー付き） ---
        list_frame = tk.Frame(self.root, bg=BG_COLOR)
        list_frame.pack(fill="both", expand=True, padx=12)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            list_frame, columns=("task", "deadline"), show="headings",
            selectmode="browse", yscrollcommand=scrollbar.set,
        )
        self.tree.heading("task", text="タスク", anchor="w")
        self.tree.heading("deadline", text="期限")
        self.tree.column("task", anchor="w", stretch=True, width=260)
        self.tree.column("deadline", anchor="center", stretch=False, width=110)
        self.tree.tag_configure("overdue", foreground=OVERDUE_COLOR)
        self.tree.tag_configure("today", foreground=TODAY_COLOR)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Delete>", lambda event: self.complete_task())  # Deleteキーでも完了
        self.tree.bind("<Double-1>", self.on_double_click)               # ダブルクリックで修正
        scrollbar.config(command=self.tree.yview)

        # --- 下部：完了・編集ボタンと最前面の切り替え ---
        bottom_frame = tk.Frame(self.root, bg=BG_COLOR)
        bottom_frame.pack(fill="x", padx=12, pady=10)

        tk.Button(
            bottom_frame, text="完了（削除）", command=self.complete_task,
            font=self.small_font, fg=TEXT_COLOR, relief="groove",
            padx=8, cursor="hand2",
        ).pack(side="left")

        tk.Button(
            bottom_frame, text="編集", command=self.edit_task,
            font=self.small_font, fg=TEXT_COLOR, relief="groove",
            padx=8, cursor="hand2",
        ).pack(side="left", padx=(6, 0))

        self.topmost_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            bottom_frame, text="最前面に表示",
            variable=self.topmost_var, command=self.toggle_topmost,
            font=self.small_font, fg=TEXT_COLOR,
            bg=BG_COLOR, activebackground=BG_COLOR,
        ).pack(side="right")

        # --- 件数表示 ---
        self.status = tk.Label(self.root, anchor="w", fg="gray", font=self.small_font, bg=BG_COLOR)
        self.status.pack(fill="x", padx=12, pady=(0, 10))

    # ---- 入力チェック（追加と修正で共通） ----
    def check_input(self, text, deadline_text, parent, current=None, deadline_widget=None):
        """
        タスク名と期限をチェックする。
        current：修正中のタスク（追加のときは None）
        戻り値：問題なければ (タスク名, 期限の保存形式 または None)、だめなら None
        """
        text = text.strip()

        # タスク名のチェック
        if not text:
            messagebox.showwarning("入力エラー", "タスクを入力してください。", parent=parent)
            return None
        if len(text) > MAX_LENGTH:
            messagebox.showwarning(
                "入力エラー",
                f"{MAX_LENGTH}文字以内で入力してください。（いま {len(text)} 文字）",
                parent=parent,
            )
            return None

        # 期限のチェック
        deadline, error = parse_deadline(deadline_text)
        if error:
            messagebox.showwarning("期限の入力エラー", error, parent=parent)
            if deadline_widget:
                deadline_widget.focus_set()
            return None
        deadline_iso = deadline.isoformat() if deadline else None

        # 過ぎた日付の確認（修正で期限を変えていないときは聞かない）
        unchanged = current is not None and current.get("deadline") == deadline_iso
        if deadline and deadline < date.today() and not unchanged:
            if not messagebox.askyesno(
                "確認", f"期限（{deadline.month}/{deadline.day}）はもう過ぎています。\nこのまま登録しますか？",
                parent=parent,
            ):
                return None

        # 同じタスク名の確認（修正中のタスク自身は除く）
        if any(task["text"] == text for task in self.tasks if task is not current):
            if not messagebox.askyesno("確認", f"「{text}」はすでにあります。\nこのまま登録しますか？", parent=parent):
                return None

        return text, deadline_iso

    # ---- 操作 ----
    def add_task(self):
        result = self.check_input(
            self.entry.get(), self.deadline_entry.get(), self.root,
            deadline_widget=self.deadline_entry,
        )
        if result is None:
            return
        text, deadline_iso = result

        self.tasks.append({
            "text": text,
            "deadline": deadline_iso,
            "created": datetime.now().isoformat(timespec="seconds"),
        })
        if self.save():
            self.entry.delete(0, tk.END)
            self.deadline_entry.delete(0, tk.END)
            self.entry.focus_set()
        self.refresh_list()

    def complete_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("お知らせ", "完了したタスクを一覧から選んでください。", parent=self.root)
            return

        index = int(selected[0])  # 行のIDに、並べ替え後の番号を入れてある
        removed = self.tasks.pop(index)
        if not self.save():
            self.tasks.insert(index, removed)  # 保存に失敗したら元に戻す
        self.refresh_list()

    def edit_task(self):
        """選んだタスクの修正画面を開く"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("お知らせ", "修正したいタスクを一覧から選んでください。", parent=self.root)
            return
        task = self.tasks[int(selected[0])]

        # --- 修正用の小さな窓 ---
        dialog = tk.Toplevel(self.root)
        dialog.title("タスクの修正")
        dialog.configure(bg=BG_COLOR)
        dialog.resizable(False, False)
        dialog.transient(self.root)               # 本体の窓の上に出す
        dialog.attributes("-topmost", True)

        form = tk.Frame(dialog, bg=BG_COLOR)
        form.pack(padx=16, pady=(16, 4))

        tk.Label(form, text="タスク", font=self.small_font, bg=BG_COLOR, fg=TEXT_COLOR)\
            .grid(row=0, column=0, sticky="w", pady=4)
        text_entry = tk.Entry(form, font=self.font, fg=TEXT_COLOR, relief="solid", bd=1, width=24)
        text_entry.grid(row=0, column=1, pady=4, ipady=3)
        text_entry.insert(0, task["text"])

        tk.Label(form, text="期限", font=self.small_font, bg=BG_COLOR, fg=TEXT_COLOR)\
            .grid(row=1, column=0, sticky="w", pady=4)
        deadline_entry = tk.Entry(form, font=self.font, fg=TEXT_COLOR, relief="solid", bd=1, width=24)
        deadline_entry.grid(row=1, column=1, pady=4, ipady=3)
        deadline_entry.insert(0, deadline_to_input(task.get("deadline")))

        tk.Label(
            dialog, text="期限を空欄にすると「期限なし」になります",
            font=(FONT_NAME, SMALL_FONT_SIZE - 1), fg="gray", bg=BG_COLOR,
        ).pack(padx=16, anchor="w")

        def save_edit():
            result = self.check_input(
                text_entry.get(), deadline_entry.get(), dialog,
                current=task, deadline_widget=deadline_entry,
            )
            if result is None:
                return
            old = (task["text"], task.get("deadline"))
            task["text"], task["deadline"] = result
            if not self.save():
                task["text"], task["deadline"] = old  # 保存に失敗したら元に戻す
                return
            dialog.destroy()
            self.refresh_list(select=task)

        buttons = tk.Frame(dialog, bg=BG_COLOR)
        buttons.pack(fill="x", padx=16, pady=12)
        tk.Button(
            buttons, text="保存", command=save_edit,
            font=self.small_font, bg=BUTTON_COLOR, fg=BUTTON_TEXT,
            activebackground=BUTTON_COLOR, activeforeground=BUTTON_TEXT,
            relief="flat", padx=16, cursor="hand2",
        ).pack(side="right")
        tk.Button(
            buttons, text="キャンセル", command=dialog.destroy,
            font=self.small_font, fg=TEXT_COLOR, relief="groove", padx=8, cursor="hand2",
        ).pack(side="right", padx=(0, 8))

        dialog.bind("<Return>", lambda event: save_edit())
        dialog.bind("<Escape>", lambda event: dialog.destroy())

        # 本体の窓の近くに表示し、閉じるまで本体は操作できないようにする
        dialog.geometry(f"+{self.root.winfo_rootx() + 30}+{self.root.winfo_rooty() + 60}")
        deadline_entry.focus_set()
        deadline_entry.select_range(0, tk.END)
        dialog.grab_set()

    def on_double_click(self, event):
        """見出しではなく、タスクの行をダブルクリックしたときだけ修正画面を開く"""
        if self.tree.identify_row(event.y):
            self.edit_task()

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

    def refresh_list(self, select=None):
        """
        期限が近い順に並べ替えて、表を描き直す。
        select：描き直したあとに選んだ状態にするタスク（修正後、並び順が変わっても見失わないように）
        """
        self.tasks.sort(key=sort_key)
        today = date.today().isoformat()

        self.tree.delete(*self.tree.get_children())
        overdue_count = 0
        for i, task in enumerate(self.tasks):
            deadline = task.get("deadline")
            tags = ()
            if deadline and deadline < today:
                tags = ("overdue",)
                overdue_count += 1
            elif deadline == today:
                tags = ("today",)
            self.tree.insert("", "end", iid=str(i), tags=tags,
                             values=(task["text"], format_deadline(deadline)))
            if task is select:
                self.tree.selection_set(str(i))
                self.tree.see(str(i))

        status = f"残り {len(self.tasks)} 件"
        if overdue_count:
            status += f"（うち期限切れ {overdue_count} 件）"
        self.status.config(text=status)

    def schedule_refresh(self):
        """
        日付が変わったときに色分けが更新されるよう、1分ごとに描き直す。
        （選んでいる行があるときは、操作の邪魔をしないよう描き直さない）
        """
        if not self.tree.selection():
            self.refresh_list()
        self.root.after(60_000, self.schedule_refresh)
