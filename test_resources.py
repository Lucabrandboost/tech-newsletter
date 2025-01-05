import nltk
import spacy
import sys

def verify_resources():
    print("Verifying NLTK resources...")
    
    # Test NLTK resources
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('taggers/averaged_perceptron_tagger')
        nltk.data.find('corpora/wordnet')
        nltk.data.find('corpora/stopwords')
        print("✓ NLTK resources verified")
    except LookupError as e:
        print(f"✗ NLTK Error: {e}")
        print("Running nltk.download('all')...")
        nltk.download('all')
    
    # Test spaCy model
    try:
        nlp = spacy.load('en_core_web_sm')
        print("✓ spaCy model verified")
    except Exception as e:
        print(f"✗ spaCy Error: {e}")
        print("Please run: python -m spacy download en_core_web_sm")

if __name__ == "__main__":
    verify_resources() 