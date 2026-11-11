"""
期限の扱い（画面とは切り離してあるので、画面を開かずにテストできる）

- parse_deadline   ：入力された文字を日付に変換し、おかしければエラーを返す
- format_deadline  ：一覧に表示する形（10/31(土)）に変える
- deadline_to_input：修正画面の入力欄に入れる形（10/31）に変える
- sort_key         ：期限が近い順に並べるための基準
"""
import re
import unicodedata
from datetime import date, timedelta

from config import WEEKDAYS


def parse_deadline(text, today=None):
    """
    入力された期限の文字を日付に変換する。
    受け付ける書き方：10/31, 10-31, 10月31日, 2026/10/31, 2026-10-31, 2026年10月31日
    （全角数字もOK）
    戻り値：(date または None, エラーメッセージ または None)
      空欄なら (None, None) ＝「期限なし」
    """
    today = today or date.today()
    text = unicodedata.normalize("NFKC", text).strip()  # 全角→半角
    if not text:
        return None, None

    m = re.fullmatch(r"(?:(\d{4})[/\-年])?(\d{1,2})[/\-月](\d{1,2})日?", text)
    if not m:
        return None, "期限は「10/31」や「2026/10/31」の形で入力してください。"

    year_text, month, day = m.group(1), int(m.group(2)), int(m.group(3))
    year = int(year_text) if year_text else today.year

    try:
        result = date(year, month, day)
    except ValueError:
        return None, f"{month}月{day}日 は存在しない日付です。"

    # 年を省略して、ずっと前の日付になった場合は来年とみなす
    # （例：12月に「1/10」と入力したら翌年の1月10日）
    if not year_text and result < today - timedelta(days=90):
        try:
            result = date(year + 1, month, day)
        except ValueError:  # 来年に2/29が無い場合など
            return None, f"{year + 1}年{month}月{day}日 は存在しない日付です。"

    return result, None


def format_deadline(iso_text):
    """保存形式（2026-10-31）を表示用（10/31(土)）に変える"""
    if not iso_text:
        return "―"
    d = date.fromisoformat(iso_text)
    label = f"{d.month}/{d.day}({WEEKDAYS[d.weekday()]})"
    if d.year != date.today().year:
        label = f"{d.year}/" + label
    return label


def deadline_to_input(iso_text):
    """保存形式（2026-10-31）を、修正画面の入力欄に入れる形（10/31）に変える"""
    if not iso_text:
        return ""
    d = date.fromisoformat(iso_text)
    if d.year != date.today().year:
        return f"{d.year}/{d.month}/{d.day}"
    return f"{d.month}/{d.day}"


def sort_key(task):
    """
    並び順：期限のあるものを日付の早い順（期限切れが自然に一番上）
            → 期限なしは一番下 → 同じ期限なら先に登録した順
    """
    deadline = task.get("deadline")
    return (deadline is None, deadline or "", task.get("created", ""))
