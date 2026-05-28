from flask import Flask, request, jsonify, render_template
import anthropic
import os
import json
import re

app = Flask(__name__)

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")

PROMPT = """계약서를 분석해서 아래 JSON 형식으로만 답하세요. JSON 외 다른 말은 하지 마세요. 문자열 안에 큰따옴표(")를 쓰지 마세요.

계약서:
---
{text}
---

반드시 이 형식으로만:
{{"summary":"요약","risks":[{{"level":"high","title":"제목","detail":"설명"}}],"keyPoints":["포인트1","포인트2"],"suggestions":["제안1","제안2"],"negotiation":["협상1","협상2"]}}"""

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
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = message.content[0].text.strip()
        raw = re.sub(r'```json\s*', '', raw)
        raw = re.sub(r'```\s*', '', raw)
        raw = raw.strip()

        # JSON 시작/끝 추출
        start = raw.find('{')
        end = raw.rfind('}') + 1
        if start != -1 and end > start:
            raw = raw[start:end]

        result = json.loads(raw)
        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({"error": "다시 시도해주세요."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
