from flask import Flask, render_template, request, redirect
from openai import OpenAI
from dotenv import load_dotenv
import os
import csv
import re
from datetime import datetime

# .env から APIキーを読み込み
load_dotenv()
app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 履歴ファイルがなければ作成
if not os.path.exists("history.csv"):
    with open("history.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["日時", "企業名", "自己紹介", "質問1", "質問2", "質問3"])

@app.route("/")
def index():
    return redirect("/interview")

@app.route("/interview")
def interview():
    return render_template("interview.html")

@app.route("/interview/result", methods=["POST"])
def interview_result():
    company = request.form["company"]
    self_intro = request.form["user_intro"]

    prompt = f"""以下は就活の面接練習アプリです。企業名と自己紹介に応じて、想定質問を3つ生成してください。
企業名：{company}
自己紹介：{self_intro}"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは就活支援のプロです。"},
                {"role": "user", "content": prompt}
            ]
        )
        questions = response.choices[0].message.content.strip()

        # 前処理：行ごとに分割し、「想定質問：」などを除去
        lines = [line.strip() for line in questions.splitlines() if line.strip()]
        lines = [line for line in lines if not re.match(r'^想定質問[:：]?', line)]

        # 質問番号で分割（1. 2. 3. ...）
        question_lines = re.split(r'\n?\s*\d\.\s*', '\n'.join(lines))
        question_lines = [q.strip() for q in question_lines if q.strip()]

        # 分割がうまくいかなかった場合は改行で分割
        if len(question_lines) < 3:
            question_lines = [q.strip() for q in '\n'.join(lines).split('\n') if q.strip()]

        # 空欄補完（3個になるように）
        while len(question_lines) < 3:
            question_lines.append("")

        # 履歴に保存（最新を上に表示）
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("history.csv", "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, company, self_intro] + question_lines[:3])

    except Exception as e:
        questions = f"エラーが発生しました: {str(e)}"
        question_lines = ["", "", ""]

    # 履歴を読み込み（新しい順に）
    records = []
    try:
        with open("history.csv", "r", encoding="utf-8", newline="") as f:
            reader = list(csv.reader(f))
            header = reader[0]
            data = reader[1:]
            for row in reversed(data):
                row = [item.replace('\n', '<br>') for item in row]
                records.append(row)
    except FileNotFoundError:
        records = []

    return render_template(
        "interview_result.html",
        company=company,
        self_intro=self_intro,
        questions=questions,
        question_lines=question_lines,
        records=records
    )

@app.route("/history")
def history():
    records = []
    try:
        with open("history.csv", "r", encoding="utf-8", newline="") as f:
            reader = list(csv.reader(f))
            header = reader[0]
            data = reader[1:]
            for row in reversed(data):
                row = [item.replace('\n', '<br>') for item in row]
                records.append(row)
    except FileNotFoundError:
        records = []

    return render_template("history.html", records=records)

if __name__ == "__main__":
    app.run(debug=True)
