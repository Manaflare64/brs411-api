import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Base URL for BRS411 arbitration search
BASE_URL = "http://brs411.org/cgi-bin/search.cgi"

# ✅ Fixed: Properly formatted query templates
QUERY_TEMPLATES = [
    '"{}" -contractor',
    '*{}*',
    '"{0}" OR "{0}*"',  # Fix: Uses {0} correctly in both placeholders
    '{} -porters',
    '{} "public law board"',
]

def format_query(user_query):
    """Formats user input into structured search queries for BRS411."""
    return [template.format(user_query) for template in QUERY_TEMPLATES]

def search_brs411(query, results_per_page=5):
    """Searches BRS411.org using structured queries for better results."""
    results = []
    search_variations = format_query(query)  # ✅ Uses properly formatted queries

    for formatted_query in search_variations:
        params = {
            "zoom_query": formatted_query,
            "zoom_per_page": results_per_page
        }

        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            response.raise_for_status()  # ✅ Prevents crashes if BRS411 returns an error

        except requests.exceptions.RequestException as e:
            return [{"error": f"Failed to reach BRS411.org: {str(e)}"}]

        soup = BeautifulSoup(response.text, 'html.parser')

        for result in soup.find_all('a', href=True):
            title = result.text.strip()
            link = "http://brs411.org" + result['href']
            snippet = result.find_next('div').text.strip() if result.find_next('div') else "No summary available."
            snippet = snippet[:250] + "..." if len(snippet) > 250 else snippet  # ✅ Trims long snippets

            results.append({"title": title, "link": link, "snippet": snippet})

        if results:
            break  # ✅ Stops searching once good results are found

    return results[:5]  # ✅ Limits to top 5 results to prevent API overload

@app.route("/search", methods=["GET"])
def search():
    """API endpoint for searching BRS411.org."""
    query = request.args.get("query", "").strip()

    if not query:
        return jsonify({"error": "Missing search query"}), 400  # ✅ Prevents empty query crashes

    results = search_brs411(query)
    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # ✅ Uses Render's assigned port
    app.run(host="0.0.0.0", port=port, debug=True)
