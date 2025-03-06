import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

app = Flask(__name__)

# Base URL for searching arbitration decisions
BASE_URL = "http://brs411.org/cgi-bin/search.cgi"

def search_brs411(query, results_per_page=100):
    """Search brs411.org and return results in JSON format."""
    
    params = {
        "zoom_query": query,
        "zoom_per_page": results_per_page
    }

    response = requests.get(BASE_URL, params=params)
    
    if response.status_code != 200:
        return {"error": f"Received status code {response.status_code}"}

    soup = BeautifulSoup(response.text, 'html.parser')
    
    results = []
    for result in soup.find_all('a', href=True):
        if result['href'].endswith('.pdf'):  # Only extract PDF links
            title = result.text.strip()
            link = "http://brs411.org" + result['href']
            snippet = result.find_next('div').text.strip() if result.find_next('div') else ""
            snippet = snippet[:300] + "..." if len(snippet) > 300 else snippet  # Trim long snippets
            results.append({"title": title, "link": link, "snippet": snippet})

    return results[:5]  # Limit to 5 results

# 🔒 Block external access (only allow requests from local machine)
@app.before_request
def limit_remote_addr():
    if request.remote_addr != "127.0.0.1":
        return jsonify({"error": "Access denied"}), 403

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
    port = int(os.environ.get("PORT", 10000))  # Default to 10000
    app.run(host="0.0.0.0", port=port, debug=True)

