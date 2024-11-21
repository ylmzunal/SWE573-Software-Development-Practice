import spacy
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# spaCy modelini yükleyin
nlp = spacy.load("en_core_web_sm")

def extract_features(text):
    """
    Metinden öznitelikleri çıkarır.
    """
    doc = nlp(text)
    features = {}
    for ent in doc.ents:
        features[ent.label_] = ent.text
    return features

def semantic_similarity(input_text, object_descriptions):
    """
    Gelen metin ile veritabanındaki nesnelerin açıklamaları arasındaki benzerliği hesaplar.
    """
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([input_text] + object_descriptions)
    similarity = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
    return similarity

def find_best_match(input_text, objects):
    """
    Metni veritabanındaki nesnelerle eşleştirir.
    """
    descriptions = [obj.description for obj in objects]
    similarities = semantic_similarity(input_text, descriptions)
    best_match_index = similarities.argmax()
    return objects[best_match_index], similarities[best_match_index]