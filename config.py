"""
見た目と動作の設定

文字の大きさや色を変えたいときは、このファイルだけを直せばよい。
"""

# 1件のタスクに入力できる最大文字数
MAX_LENGTH = 50

# ------------------------------------------------------------
# 見た目の設定（ここの数字や色を変えると、デザインが変わる）
# ------------------------------------------------------------
FONT_NAME = "Meiryo UI"     # 文字の種類（例："Yu Gothic UI", "BIZ UDPGothic"）
FONT_SIZE = 13              # 一覧・入力欄の文字の大きさ
SMALL_FONT_SIZE = 11        # ボタン・件数表示の文字の大きさ
WINDOW_SIZE = "460x520"     # 窓の大きさ（横x縦）

BG_COLOR = "#FAF7F2"        # 窓の背景色
LIST_BG = "#FFFFFF"         # 一覧の背景色
TEXT_COLOR = "#333333"      # 文字の色
SELECT_COLOR = "#CFE3D4"    # 選んだタスクの色
BUTTON_COLOR = "#7FA88A"    # 追加ボタンの色
BUTTON_TEXT = "#FFFFFF"     # 追加ボタンの文字の色
OVERDUE_COLOR = "#C0392B"   # 期限切れの文字の色
TODAY_COLOR = "#D35400"     # 今日が期限の文字の色

WEEKDAYS = "月火水木金土日"
