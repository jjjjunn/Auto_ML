#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import os

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

# 수정할 파일 목록
files_to_fix = [
    'oauth/social_auth.py'
]

for file_path in files_to_fix:
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 이모지 제거
            fixed_content = remove_emojis(content)
            
            # 파일에 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"OK {file_path} 이모지 제거 완료!")
        except Exception as e:
            print(f"ERROR {file_path} 처리 중 오류: {e}")
    else:
        print(f"! {file_path} 파일을 찾을 수 없습니다")

print("모든 이모지 제거 완료!")