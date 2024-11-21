import requests

def search_wikidata_nlp(query, limit=5):
    """
    Wikidata'da bir sorgu araması yapar ve sonuçları döndürür.
    """
    url = "https://www.wikidata.org/w/api.php"
    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'language': 'en',
        'search': query,
        'limit': limit
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json().get('search', [])
        return [
            {
                'id': result['id'],
                'label': result.get('label'),
                'description': result.get('description'),
                'url': f"https://www.wikidata.org/wiki/{result['id']}"
            }
            for result in results
        ]
    return []