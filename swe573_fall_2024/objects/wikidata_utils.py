from SPARQLWrapper import SPARQLWrapper, JSON

def format_to_wikidata_id(value):
    """
    Wikidata'dan dönen URL veya ID'yi düzgün bir ID formatına dönüştürür.
    """
    if value.startswith("http://www.wikidata.org/entity/"):
        return value.split("/")[-1]
    return value

def search_wikidata_nlp(material=None, size=None, color=None, shape=None, weight=None, limit=10):
    """
    SPARQL endpoint kullanarak özelliklere göre Wikidata sorgusu yapar.
    """
    endpoint_url = "https://query.wikidata.org/sparql"

    # Sorgunun temel kısmı
    sparql_query = """
    SELECT ?item ?itemLabel ?description WHERE {
        ?item wdt:P31 wd:Q11460.  # Q11460 = "tool"
    """

    # Özellikleri sorguya ekle
    if material and material != "None":
        sparql_query += f"        ?item wdt:P186 wd:{material}.\n"  # P186 = "material"
    if size:
        sparql_query += f"        ?item wdt:P2048 ?height.\n        FILTER((?height >= {size - 2} && ?height <= {size + 2})).\n"
    if color and color != "None":
        sparql_query += f"        ?item wdt:P462 wd:{color}.\n"  # P462 = "color"
    if shape and shape != "None":
        sparql_query += f"        ?item wdt:P1419 wd:{shape}.\n"  # P1419 = "shape"
    if weight:
        sparql_query += f"        ?item wdt:P2067 ?weight.\n        FILTER((?weight >= {weight - 50} && ?weight <= {weight + 50})).\n"

    # Sonuçları ekle
    sparql_query += """
        ?item schema:description ?description.
        FILTER(lang(?description) = "en").
    }
    LIMIT """ + str(limit)

    # SPARQLWrapper ile sorguyu çalıştır
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)

    try:
        results = sparql.query().convert()
        items = results["results"]["bindings"]

        # Sonuçları düzenle ve döndür
        return [
            {
                'label': item["itemLabel"]["value"],
                'description': item.get("description", {}).get("value", ""),
            }
            for item in items
        ]
    except Exception as e:
        print(f"SPARQL query failed: {e}")
        return []
    


def build_attributes_for_sparql(post):
    """
    Post nesnesinden SPARQL özelliklerini çıkarır.
    """
    attributes = {
        "material": post.material if post.material else None,
        "size": post.size if post.size else None,
        "color": post.color if post.color else None,
        "shape": post.shape if post.shape else None,
        "weight": post.weight if post.weight else None
    }
    return attributes