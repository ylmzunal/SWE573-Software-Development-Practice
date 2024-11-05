import requests
from django.shortcuts import render

def homepage(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')  # Get selected category from the form
    wikidata_results = []

    if query:
        url = "https://www.wikidata.org/w/api.php"
        # Define search parameters
        params = {
            "action": "wbsearchentities",
            "format": "json",
            "language": "en",
            "search": query
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()
            for result in data.get("search", []):
                # Filter results by category if selected
                if category and category not in result.get("description", "").lower():
                    continue  # Skip result if it doesn't match the selected category

                wikidata_results.append({
                    "label": result.get("label", ""),
                    "description": result.get("description", "No description available"),
                })
        except Exception as e:
            print("Error querying Wikidata:", e)

    context = {
        'query': query,
        'wikidata_results': wikidata_results,
    }
    return render(request, 'objects/homepage.html', context)