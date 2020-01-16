import spacy
from NLP.entityMatchers import EntityMatchers
from NLP.sectionizer import Sectionizer
from NLP.sentencizer import Sentencizer
from NLP.tokenizer import CustomTokenizer


class LanguageProcessor:
    def __init__(self, text):
        nlp = spacy.load('en_core_web_lg')
        self.doc = nlp(text)

        self.sectionizer = Sectionizer(self.doc, "NLP/secrets/sections.csv")
        self.entityMatcher = EntityMatchers(self.doc, nlp)
        self.sentencizer = Sentencizer(self.doc, nlp)
        self.tokenizer = CustomTokenizer(self.doc, nlp)

    def getDocumentSections(self):
        return self.sectionizer.getSectionsForAnnotation()

    def getDocumentEntities(self):
        return self.entityMatcher.getMatchesForAnnotation()

    def getDocumentSentences(self):
        return self.sentencizer.getMatchesForAnnotation()

    def getDocumentTokens(self):
        return self.tokenizer.getMatchesForAnnotation()