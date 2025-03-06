import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

app = Flask(__name__)

BASE_URL = "http://brs411.org/cgi-bin/search.cgi"

# ✅ Smart search refinements based on BRS411 rules
QUERY_TEMPLATES = [
    '"{}" -contractor',             # Prioritizes phrase searching
    '*{}*',                         # Uses wildcard matching
    '"{}" OR "{}*"',                # Combines phrase + wildcard
    '{} -porters',                  # Excludes unwanted results
    '{} "public law board"',        # Focuses on arbitration awards
]

def format_query(user_query):
    """Converts user input into multiple structured search queries."""
    formatted_queries = [template.format(user_query) for template in QUERY_TEMPLATES]
    return formatted_queries

def search_brs411(query, results_per_page=5):
    """Search brs411.org using structured queries for better results."""
    results = []
    search_variations = format_query(query)

    for formatted_query in search_variations:
        params = {
            "zoom_query": formatted_query,
            "zoom_per_page": results_per_page
        }

        response = requests.get(BASE_URL, params=params)
        if response.status_code != 200:
            continue  # Skip to the next search variation if one fails

        soup = BeautifulSoup(response.text, 'html.parser')

        for result in soup.find_all('a', href=True):
            title = result.text.strip()
            link = "http://brs411.org" + result['href']
            snippet = result.find_next('div').text.strip() if result.find_next('div') else "No summary available."
            snippet = snippet[:250] + "..." if len(snippet) > 250 else snippet  # Trim long snippets

            results.append({"title": title, "link": link, "snippet": snippet})

        if results:
            break  # Stop searching once good results are found

    return results[:5]  # Limit results to the top 5 for faster response

@app.route("/search", methods=["GET"])
def search():
    """API endpoint for searching brs411.org"""
    query = request.args.get("query", "")

    if not query:
        return jsonify({"error": "Missing search query"}), 400

    results = search_brs411(query)
    return jsonify(results)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))  
    app.run(host="0.0.0.0", port=port, debug=True)
