"""
タスクの保存と読み込み（画面とは切り離してあるので、画面を開かずにテストできる）

- load_tasks：tasks.json を読み込む。壊れたデータや古い形式のデータにも対応する
- save_tasks：tasks.json に安全に保存する
"""
import json
import os
from datetime import date

# 保存先：このファイルと同じフォルダの tasks.json
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")


def load_tasks(path):
    """
    ファイルからタスクを読み込む。
    戻り値：(タスクのリスト, 警告メッセージ または None)
    第2段階までの古いデータ（期限の項目が無い）は「期限なし」として読み込む。
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

    tasks = []
    skipped = 0        # 読み飛ばしたタスクの数
    bad_deadline = 0   # 期限が読めず「期限なし」にしたタスクの数
    for item in data:
        if not (isinstance(item, dict) and isinstance(item.get("text"), str) and item["text"].strip()):
            skipped += 1
            continue

        deadline = item.get("deadline")
        if deadline is not None:
            try:
                date.fromisoformat(deadline)
            except (TypeError, ValueError):
                item["deadline"] = None
                bad_deadline += 1
        else:
            item["deadline"] = None  # 古いデータ・期限なし
        tasks.append(item)

    messages = []
    if skipped:
        messages.append(f"形式が正しくないデータが {skipped} 件あったため、読み飛ばしました。")
    if bad_deadline:
        messages.append(f"期限が読み取れないタスクが {bad_deadline} 件あったため、「期限なし」にしました。")
    return tasks, "\n".join(messages) or None


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
