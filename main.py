from flask import Flask, render_template, request
from openai import OpenAI
import os

app = Flask(__name__)

api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPEN_AI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    if request.method == "POST":
        user_input = request.form.get("user_input", "").strip()

        if not client:
            error = "OpenAI API key is not configured. Please set the OPENAI_API_KEY environment variable."
        elif not user_input:
            error = "Please enter some text before submitting."
        else:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an AI governance ideation assistant."},
                        {"role": "user", "content": user_input}
                    ]
                )
                result = response.choices[0].message.content
            except Exception as e:
                error = f"An error occurred: {str(e)}"

    return render_template("index.html", result=result, error=error)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

