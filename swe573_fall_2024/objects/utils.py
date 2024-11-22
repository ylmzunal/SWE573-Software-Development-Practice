import re
import requests
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')  # Semantik analiz modeli

def build_query_from_post(post):
    """
    Post içeriğinden anahtar kelimeler çıkararak sorgu oluşturur.
    """
    # Etiketlerden ve içerikten önemli kelimeleri seç
    tags = " ".join([tag.name for tag in post.tags.all()])
    content = post.content

    # İçerikten sadece 4 harften uzun kelimeleri al
    keywords = re.findall(r'\b[A-Za-z]{4,}\b', content)
    selected_keywords = " ".join(keywords[:10])  # İlk 10 kelimeyi al

    query = f"{selected_keywords} {tags}"
    print("Optimized Query for NLP:", query)  # Optimizasyon kontrolü için
    return query.strip()



def rank_wikidata_results(query, wikidata_results):
    """
    Post içeriğini Wikidata sonuçlarıyla semantik olarak karşılaştırır.
    """
    if not wikidata_results:
        print("No results from Wikidata.")
        return []

    # Sadece açıklaması olan sonuçları al
    descriptions = [result['description'] for result in wikidata_results if result['description']]
    if not descriptions:
        print("No descriptions available in Wikidata results.")
        return []

    # Sorguyu ve açıklamaları vektörleştir
    query_embedding = model.encode(query, convert_to_tensor=True)
    description_embeddings = model.encode(descriptions, convert_to_tensor=True)

    # Semantik benzerlik hesapla
    similarities = util.cos_sim(query_embedding, description_embeddings).flatten()

    # Sonuçları benzerlik skoruna göre sırala
    ranked_results = sorted(
        zip(wikidata_results, similarities),
        key=lambda x: x[1],  # Benzerlik skoruna göre sırala
        reverse=True
    )

    return [
        {
            'label': result[0]['label'],
            'description': result[0]['description'],
            'similarity': result[1].item()
        }
        for result in ranked_results
    ]


# objects/utils.py

def fetch_wikidata_options(property_id=None, item_type=None):
    """
    Belirli bir Wikidata özelliği (property_id) ve/veya sınıf (item_type) için olası değerleri alır.
    """
    if property_id and item_type:
        sparql_query = f"""
        SELECT DISTINCT ?value ?valueLabel WHERE {{
          ?item wdt:P31 wd:{item_type};
                wdt:{property_id} ?value.
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 50
        """
    elif item_type:
        sparql_query = f"""
        SELECT DISTINCT ?value ?valueLabel WHERE {{
          ?value wdt:P31 wd:{item_type}.
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 50
        """
    elif property_id:
        sparql_query = f"""
        SELECT DISTINCT ?value ?valueLabel WHERE {{
          ?value wdt:{property_id} ?item.
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 50
        """
    else:
        raise ValueError("Either property_id or item_type must be provided.")

    # SPARQL endpoint'i çağır
    url = "https://query.wikidata.org/sparql"
    headers = {"Accept": "application/json"}
    response = requests.get(url, params={"query": sparql_query}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return [
            {"id": result["value"]["value"], "label": result["valueLabel"]["value"]}
            for result in data["results"]["bindings"]
        ]
    else:
        print(f"Failed to fetch data for {property_id or item_type}")
        return []
    
# Old version

# import spacy
# from sklearn.metrics.pairwise import cosine_similarity
# from sklearn.feature_extraction.text import TfidfVectorizer

# # spaCy modelini yükleyin
# nlp = spacy.load("en_core_web_sm")

# def extract_keywords_nlp(content):
#     """
#     Post içeriğinden anahtar kelimeler çıkarır.
#     """
#     doc = nlp(content)
#     return [ent.text for ent in doc.ents]  # Adlandırılmış varlıkları döndür


# def semantic_similarity(input_text, descriptions):
#     """
#     Post içeriği ve diğer açıklamalar arasında semantic benzerliği hesaplar.
#     """
#     vectorizer = TfidfVectorizer()
#     vectors = vectorizer.fit_transform([input_text] + descriptions)
#     return cosine_similarity(vectors[0:1], vectors[1:]).flatten()


# def find_best_match(input_text, objects):
#     """
#     Metni veritabanındaki nesnelerle eşleştirir.
#     """
#     descriptions = [obj.description for obj in objects]
#     similarities = semantic_similarity(input_text, descriptions)
#     best_match_index = similarities.argmax()
#     return objects[best_match_index], similarities[best_match_index]