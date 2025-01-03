import sqlite3
from datetime import datetime
import json
import nltk
import spacy
from collections import Counter
from string import punctuation
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

class ArticleTracker:
    def __init__(self):
        self.db_path = 'newsletter_data.db'
        self.setup_nltk()  # Add NLTK setup
        self.nlp = spacy.load('en_core_web_sm')
        self.lemmatizer = WordNetLemmatizer()
        self.setup_database()
        
        # Enhanced stopwords
        self.stopwords = set(stopwords.words('english'))
        self.stopwords.update(['said', 'says', 'would', 'could', 'may', 'might', 
                             'today', 'yesterday', 'tomorrow', 'year', 'week',
                             'according', 'report'])

    def setup_nltk(self):
        """Download required NLTK resources."""
        resources = {
            'tokenizers/punkt': 'punkt',
            'taggers/averaged_perceptron_tagger': 'averaged_perceptron_tagger',
            'corpora/wordnet': 'wordnet',
            'corpora/stopwords': 'stopwords'
        }
        
        for path, resource in resources.items():
            try:
                nltk.data.find(path)
            except LookupError:
                print(f"Downloading {resource}...")
                nltk.download(resource, quiet=True)

    def setup_database(self):
        """Create the necessary database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for storing articles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                url TEXT UNIQUE,
                category TEXT,
                keywords TEXT,
                source TEXT,
                published_date TEXT,
                sent_date TEXT
            )
        ''')
        
        # Table for tracking clicks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS article_clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_url TEXT,
                click_date TEXT,
                FOREIGN KEY (article_url) REFERENCES articles (url)
            )
        ''')
        
        # Table for keyword weights
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keyword_weights (
                keyword TEXT PRIMARY KEY,
                weight FLOAT,
                last_updated TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_db_connection(self):
        """Get a database connection with proper timeout and isolation level"""
        conn = sqlite3.connect(self.db_path, timeout=20)
        conn.isolation_level = None  # Enable autocommit mode
        return conn

    def track_article(self, article):
        """Store article in database with enhanced keyword extraction."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Extract keywords with weights
            text = f"{article.get('title', '')} {article.get('description', '')}"
            keywords_with_weights = self._extract_keywords(text)
            
            # Handle source whether it's a string or dict
            source = article.get('source')
            if isinstance(source, dict):
                source_name = source.get('name', '')
            else:
                source_name = str(source)
            
            cursor.execute('BEGIN')
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO articles 
                    (title, url, category, keywords, source, published_date, sent_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article.get('title'),
                    article.get('url'),
                    article.get('category', 'general'),
                    json.dumps(keywords_with_weights),
                    source_name,
                    article.get('publishedAt', datetime.now().isoformat()),
                    datetime.now().isoformat()
                ))
                cursor.execute('COMMIT')
            except Exception as e:
                cursor.execute('ROLLBACK')
                raise e

    def record_click(self, url):
        """Record when an article is clicked."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('BEGIN')
            try:
                # Record the click
                cursor.execute('''
                    INSERT INTO article_clicks (article_url, click_date)
                    VALUES (?, ?)
                ''', (url, datetime.now().isoformat()))
                
                # Update weights in the same transaction
                cursor.execute('SELECT keywords FROM articles WHERE url = ?', (url,))
                result = cursor.fetchone()
                
                if result:
                    keywords = json.loads(result[0])
                    current_time = datetime.now()
                    
                    for keyword, importance in keywords.items():
                        cursor.execute('''
                            SELECT weight, last_updated 
                            FROM keyword_weights 
                            WHERE keyword = ?
                        ''', (keyword,))
                        
                        result = cursor.fetchone()
                        if result:
                            old_weight, last_updated = result
                            time_diff = (current_time - datetime.fromisoformat(last_updated)).days
                            decay_factor = 0.95 ** min(time_diff, 30)
                            new_weight = (old_weight * decay_factor) + (importance * 0.5)
                        else:
                            new_weight = importance
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO keyword_weights (keyword, weight, last_updated)
                            VALUES (?, ?, ?)
                        ''', (keyword, new_weight, current_time.isoformat()))
                
                cursor.execute('COMMIT')
            except Exception as e:
                cursor.execute('ROLLBACK')
                raise e

    def get_article_score(self, article):
        """Calculate a more nuanced relevance score for an article."""
        text = f"{article.get('title', '')} {article.get('description', '')}"
        article_keywords = self._extract_keywords(text)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        total_score = 0
        # Get all keyword weights from database
        cursor.execute('SELECT keyword, weight FROM keyword_weights')
        db_weights = dict(cursor.fetchall())
        
        for keyword, importance in article_keywords.items():
            # Combine keyword importance with historical weight
            if keyword in db_weights:
                total_score += importance * db_weights[keyword]
            else:
                total_score += importance * 0.5  # Default weight for new keywords
        
        conn.close()
        return total_score

    def _extract_keywords(self, text):
        """Extract relevant keywords using NLP techniques."""
        # Process text with spaCy
        doc = self.nlp(text.lower())
        
        # Extract named entities
        entities = [ent.text for ent in doc.ents if ent.label_ in 
                   ['ORG', 'PRODUCT', 'GPE', 'PERSON', 'WORK_OF_ART', 'EVENT']]
        
        # Tokenize and lemmatize
        tokens = word_tokenize(text.lower())
        
        # Part of speech tagging
        pos_tags = nltk.pos_tag(tokens)
        
        # Extract nouns, verbs, and adjectives
        important_words = []
        for word, tag in pos_tags:
            # Skip if it's a stopword or punctuation
            if word in self.stopwords or word in punctuation:
                continue
                
            # Lemmatize based on POS
            if tag.startswith('NN'):  # Nouns
                lemma = self.lemmatizer.lemmatize(word, pos='n')
                important_words.append(lemma)
            elif tag.startswith('VB'):  # Verbs
                lemma = self.lemmatizer.lemmatize(word, pos='v')
                important_words.append(lemma)
            elif tag.startswith('JJ'):  # Adjectives
                lemma = self.lemmatizer.lemmatize(word, pos='a')
                important_words.append(lemma)

        # Combine entities and important words
        all_keywords = entities + important_words
        
        # Count frequencies
        keyword_freq = Counter(all_keywords)
        
        # Get phrases using spaCy
        phrases = [chunk.text.lower() for chunk in doc.noun_chunks 
                  if len(chunk.text.split()) > 1]
        
        # Add frequent phrases
        for phrase in phrases:
            if not any(word in self.stopwords for word in phrase.split()):
                keyword_freq[phrase] = keyword_freq.get(phrase, 0) + 1

        # Return top keywords with their weights
        return {word: freq/len(all_keywords) 
                for word, freq in keyword_freq.most_common(10)}

    def _update_keyword_weights(self, url, conn=None):
        """Update keyword weights with decay factor for older weights."""
        should_close = conn is None
        conn = conn or self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('BEGIN')
        try:
            cursor.execute('SELECT keywords FROM articles WHERE url = ?', (url,))
            result = cursor.fetchone()
            
            if result:
                keywords = json.loads(result[0])
                current_time = datetime.now()
                
                for keyword, importance in keywords.items():
                    cursor.execute('''
                        SELECT weight, last_updated 
                        FROM keyword_weights 
                        WHERE keyword = ?
                    ''', (keyword,))
                    
                    result = cursor.fetchone()
                    if result:
                        old_weight, last_updated = result
                        time_diff = (current_time - datetime.fromisoformat(last_updated)).days
                        decay_factor = 0.95 ** min(time_diff, 30)
                        new_weight = (old_weight * decay_factor) + (importance * 0.5)
                    else:
                        new_weight = importance
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO keyword_weights (keyword, weight, last_updated)
                        VALUES (?, ?, ?)
                    ''', (keyword, new_weight, current_time.isoformat()))
            
            cursor.execute('COMMIT')
        except Exception as e:
            cursor.execute('ROLLBACK')
            raise e
        finally:
            if should_close:
                conn.close() 