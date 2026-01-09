import re
from typing import Dict, List, Optional

class LanguageDetector:
    """
    Detects language from user text using keyword matching
    """
    
    def __init__(self):
        # Language detection keywords
        self.keywords = {
            "ar": {
                "words": ["السلام", "مرحبا", "شكرا", "لو سمحت", "ممكن", "وين", "كيف"],
                "chars": r'[\u0600-\u06FF]'  # Arabic Unicode range
            },
            "fr": {
                "words": ["bonjour", "salut", "merci", "s'il vous plaît", "rdv", "rendez-vous"],
                "chars": r'[éèêëàâäçîïôöùûüÿœæ]'
            },
            "en": {
                "words": ["hello", "hi", "thanks", "please", "appointment", "booking"],
                "chars": r'[^a-zA-Z0-9\s]'  # Non-ASCII indicator
            },
            "ma": {
                "words": ["salam", "labas", "bghit", "kifach", "wach", "b7al", "3la"],
                "chars": r'[3-7]'  # Common Darija numbers for letters
            }
        }
        
    def detect(self, text: str) -> str:
        """
        Detect language from text
        
        Args:
            text: Input text
            
        Returns:
            Language code (en, fr, ar, ma)
        """
        if not text or not isinstance(text, str):
            return "en"  # Default to English
        
        text_lower = text.lower().strip()
        
        # Score each language
        scores = {lang: 0 for lang in self.keywords}
        
        for lang, data in self.keywords.items():
            # Check for keywords
            for word in data["words"]:
                if word in text_lower:
                    scores[lang] += 2
            
            # Check for special characters
            if re.search(data["chars"], text):
                scores[lang] += 1
        
        # Check for Arabic script
        if re.search(r'[\u0600-\u06FF]', text):
            scores["ar"] += 5  # Strong indicator
        
        # Check for Darija patterns
        if any(char in text_lower for char in ['3', '5', '7', '9']):
            scores["ma"] += 2
        
        # Get language with highest score
        detected_lang = max(scores.items(), key=lambda x: x[1])[0]
        
        # If score is too low, default to English
        if scores[detected_lang] < 2:
            return "en"
        
        return detected_lang
    
    def get_language_name(self, lang_code: str) -> str:
        """
        Get full language name from code
        
        Args:
            lang_code: Language code
            
        Returns:
            Language name
        """
        names = {
            "en": "English",
            "fr": "French", 
            "ar": "Arabic",
            "ma": "Moroccan Darija"
        }
        return names.get(lang_code, "English")
    
    def is_arabic_script(self, text: str) -> bool:
        """
        Check if text contains Arabic script
        
        Args:
            text: Input text
            
        Returns:
            True if contains Arabic characters
        """
        return bool(re.search(r'[\u0600-\u06FF]', text))