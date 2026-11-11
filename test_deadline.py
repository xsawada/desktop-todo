"""
期限の処理のテスト（画面を開かずに実行できる）

実行方法：python test_deadline.py
すべて通れば「すべてのテストに合格しました」と表示される。
"""
from datetime import date

from deadline import parse_deadline, format_deadline, sort_key

TODAY = date(2026, 11, 11)  # テストの基準日を固定して、いつ実行しても同じ結果にする


def test_parse_deadline():
    # いろいろな書き方を受け付ける
    assert parse_deadline("11/20", TODAY) == (date(2026, 11, 20), None)
    assert parse_deadline("11-20", TODAY) == (date(2026, 11, 20), None)
    assert parse_deadline("11月20日", TODAY) == (date(2026, 11, 20), None)
    assert parse_deadline("１１／２０", TODAY) == (date(2026, 11, 20), None)   # 全角
    assert parse_deadline("2027/1/5", TODAY) == (date(2027, 1, 5), None)

    # 空欄は「期限なし」
    assert parse_deadline("", TODAY) == (None, None)

    # 年を省略して、ずっと前の日付になるときは来年とみなす
    assert parse_deadline("1/10", TODAY) == (date(2027, 1, 10), None)

    # おかしな入力はエラーメッセージを返す
    assert parse_deadline("2/30", TODAY)[1] is not None   # 存在しない日付
    assert parse_deadline("13/1", TODAY)[1] is not None   # 13月
    assert parse_deadline("あした", TODAY)[1] is not None  # 書き方が違う


def test_format_deadline():
    assert format_deadline("2026-11-20") == "11/20(金)"
    assert format_deadline(None) == "―"


def test_sort_key():
    tasks = [
        {"text": "期限なし", "deadline": None, "created": "1"},
        {"text": "来週", "deadline": "2026-11-18", "created": "2"},
        {"text": "期限切れ", "deadline": "2026-11-01", "created": "3"},
    ]
    names = [t["text"] for t in sorted(tasks, key=sort_key)]
    assert names == ["期限切れ", "来週", "期限なし"]


if __name__ == "__main__":
    test_parse_deadline()
    test_format_deadline()
    test_sort_key()
    print("すべてのテストに合格しました")
