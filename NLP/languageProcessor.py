import spacy
from NLP.entityMatchers import EntityMatchers
from NLP.sectionizer import Sectionizer
from NLP.sentencizer import Sentencizer
from NLP.tokenizer import CustomTokenizer
from NLP.icdKeywordMatcher import IcdKeywordMatcher

import spacy


class LanguageProcessor:
    def __init__(self):
        print("Initializing LanguageProcessor...")
        self.nlp = spacy.load('en_core_web_lg')
        self.doc = self.nlp("")
        self.icdKwMatcher = IcdKeywordMatcher("NLP/secrets/icd_10_cm_index_clean.csv")
        self.sectionizer = Sectionizer("NLP/secrets/sections.csv")
        self.entityMatcher = EntityMatchers(self.nlp, self.icdKwMatcher.keywordPhrases)
        self.sentencizer = Sentencizer(self.nlp)
        self.tokenizer = CustomTokenizer(self.nlp)

    def analyzeText(self, text):
        self.doc = self.nlp(text)
        self.sections = self.sectionizer.getSectionsForAnnotation(self.doc)
        self.entities = self.entityMatcher.getMatchesForAnnotation(self.doc)
        self.sentences = self.sentencizer.getMatchesForAnnotation(self.doc)
        self.tokens = self.tokenizer.getMatchesForAnnotation(self.doc)
        self.icdCodes = self.icdKwMatcher.getIcdCodes(text, self.entities)

        return {'entities': self.entities,
                'sections': self.sections,
                'sentences': self.sentences,
                'tokens': self.tokens,
                'icdCodes': self.icdCodes
                }
