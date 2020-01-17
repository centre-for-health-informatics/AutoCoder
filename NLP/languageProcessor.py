import spacy
from NLP.entityMatchers import EntityMatchers
from NLP.sectionizer import Sectionizer
from NLP.sentencizer import Sentencizer
from NLP.tokenizer import CustomTokenizer


class LanguageProcessor:
    def __init__(self):

        print("Initiating LanguageProcessor...")
        self.nlp = spacy.load('en_core_web_lg')
        self.doc = self.nlp("")
        self.sectionizer = Sectionizer("NLP/secrets/sections.csv")
        self.entityMatcher = EntityMatchers(self.nlp)
        self.sentencizer = Sentencizer(self.nlp)
        self.tokenizer = CustomTokenizer(self.nlp)

    def setText(self, text):
        self.doc = self.nlp(text)

    def getDocumentSections(self):
        return self.sectionizer.getSectionsForAnnotation(self.doc)

    def getDocumentEntities(self):
        return self.entityMatcher.getMatchesForAnnotation(self.doc)

    def getDocumentSentences(self):
        return self.sentencizer.getMatchesForAnnotation(self.doc)

    def getDocumentTokens(self):
        return self.tokenizer.getMatchesForAnnotation(self.doc)
