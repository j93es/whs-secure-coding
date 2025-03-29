import html
import re
from flask import abort

def safe_str(target):
    return f'{target}' if target else ''

# === XSS 방지를 위한 입력값 이스케이프 ===

def sanitize_input(text):
    """
    XSS 방지를 위해 HTML 태그 및 스크립트 코드를 이스케이프합니다.
    """
    text = safe_str(text)   # 입력값을 문자열로 변환
    
    if not text:
        return ""

    # 1. 모든 태그 제거 (기본 필터링이 필요할 경우)
    tag_stripped = re.sub(r'<.*?>', '', text)

    # 2. HTML 엔티티 이스케이프 (가장 안전한 처리)
    escaped = html.escape(tag_stripped)

    return escaped


def safe_int(target, use_abort=False):
    try:
        return int(sanitize_input(target))
    except (ValueError, TypeError):
        if use_abort:
            abort(400)
        return 0