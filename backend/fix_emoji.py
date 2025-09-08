#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

# 이모지 제거 함수
def remove_emojis(text):
    emoji_pattern = re.compile("["
        "\U0001F600-\U0001F64F"  # 감정
        "\U0001F300-\U0001F5FF"  # 기호 및 픽토그램
        "\U0001F680-\U0001F6FF"  # 운송 및 지도
        "\U0001F1E0-\U0001F1FF"  # 국기
        "\U00002600-\U000026FF"  # 기타 기호
        "\U00002700-\U000027BF"  # 딩벳
        "\U0001F900-\U0001F9FF"  # 보조 기호
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text)

# auth_routes.py 파일 수정
with open('routes/auth_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 이모지 제거
fixed_content = remove_emojis(content)

# 파일에 저장
with open('routes/auth_routes.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("이모지 제거 완료!")