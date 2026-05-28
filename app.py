from flask import Flask, request, jsonify, render_template
import anthropic
import os
import json
import re

app = Flask(__name__)

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")

PROMPT = """당신은 계약서 분석 전문가입니다. 아래 계약서를 분석하여 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요. 큰따옴표 안에 큰따옴표를 사용하지 마세요.

계약서:
---
{text}
---

다음 JSON 구조로만 응답하세요:
{{
  "summary": "계약서 전체 요약 2-3문장",
  "risks": [
    {{"level": "high", "title": "위험조항 제목", "detail": "상세 설명"}},
    {{"level": "medium", "title": "위험조항 제목", "detail": "상세 설명"}}
  ],
  "keyPoints": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
  "suggestions": ["수정 제안 1", "수정 제안 2", "수정 제안 3"],
  "negotiation": ["협상 포인트 1", "협상 포인트 2", "협상 포인트 3"]
}}"""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "계약서 내용을 입력해주세요."}), 400

    if not CLAUDE_API_KEY:
        return jsonify({"error": "서버 API 키가 설정되지 않았습니다."}), 500

    try:
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        prompt = PROMPT.format(text=text[:4000])

        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = message.content[0].text.strip()
        # 마크다운 코드블록 제거
        raw = re.sub(r'```json\s*', '', raw)
        raw = re.sub(r'```\s*', '', raw)
        raw = raw.strip()

        # JSON 파싱
        result = json.loads(raw)
        return jsonify(result)

    except json.JSONDecodeError as e:
        return jsonify({"error": f"분석 결과 파싱 오류. 다시 시도해주세요."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
