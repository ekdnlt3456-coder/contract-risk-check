from flask import Flask, request, jsonify, render_template
import anthropic
import os
import json
import re

app = Flask(__name__)

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")

PROMPT = """You are a Korean contract analysis expert. Analyze the contract below and respond ONLY with valid JSON. No other text.

Contract:
---
{text}
---

Respond with exactly this JSON structure:
{{
  "summary": "2-3 sentence summary in Korean",
  "risks": [
    {{"level": "high", "title": "risk title in Korean", "detail": "detail in Korean"}}
  ],
  "keyPoints": ["point 1 in Korean", "point 2 in Korean"],
  "suggestions": ["suggestion 1 in Korean", "suggestion 2 in Korean"],
  "negotiation": ["negotiation point 1 in Korean", "negotiation point 2 in Korean"]
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
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = message.content[0].text.strip()
        print(f"Claude raw response: {raw[:500]}", flush=True)

        raw = re.sub(r'```json\s*', '', raw)
        raw = re.sub(r'```\s*', '', raw)
        raw = raw.strip()

        start = raw.find('{')
        end = raw.rfind('}') + 1
        if start != -1 and end > start:
            raw = raw[start:end]

        result = json.loads(raw)
        print(f"Parsed result keys: {list(result.keys())}", flush=True)
        return jsonify(result)

    except json.JSONDecodeError as e:
        print(f"JSON error: {e}, raw: {raw[:300]}", flush=True)
        return jsonify({"error": "다시 시도해주세요."}), 500
    except Exception as e:
        print(f"Exception: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
