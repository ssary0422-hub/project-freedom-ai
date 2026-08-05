import os
from flask import Flask, render_template, request
from openai import OpenAI

app = Flask(__name__)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
@app.route("/", methods=["GET", "POST"])
def home():

    result = ""

    business = ""
    company = ""
    style = ""

    if request.method == "POST":

        business = request.form["business"]
        company = request.form["company"]
        style = request.form["style"]

        prompt = f"""
업종 : {business}
회사명 : {company}
분위기 : {style}

SNS 광고 문구를 5개 만들어줘.
"""

        response = client.responses.create(
            model="gpt-5.5",
            input=prompt
        )

        result = response.output_text

    return render_template(
        "index.html",
        result=result,
        business=business,
        company=company,
        style=style
    )

if __name__ == "__main__":
        app.run(debug=True)