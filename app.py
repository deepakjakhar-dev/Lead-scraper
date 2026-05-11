import io
import json
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from scraper import scrape_google_maps

app = Flask(__name__, template_folder='templates', static_folder='static')

# In-memory store for the last scrape result (simple single-user app)
_last_results: list[dict] = []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/scrape", methods=["POST"])
def scrape():
    global _last_results
    data = request.get_json()
    keyword = (data.get("keyword") or "").strip()
    city = (data.get("city") or "").strip()
    max_results = int(data.get("max_results", 20))

    if not keyword or not city:
        return jsonify({"error": "Keyword and city are required."}), 400

    try:
        results = scrape_google_maps(keyword, city, max_results=max_results)
        _last_results = results
        return jsonify({"results": results, "count": len(results)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download/csv")
def download_csv():
    global _last_results
    if not _last_results:
        return "No data to download.", 400

    df = pd.DataFrame(_last_results)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="leads.csv",
        mimetype="text/csv",
    )


@app.route("/download/excel")
def download_excel():
    global _last_results
    if not _last_results:
        return "No data to download.", 400

    df = pd.DataFrame(_last_results)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="leads.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
