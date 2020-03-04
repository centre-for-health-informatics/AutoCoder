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
        self.icdKwMatcher = IcdKeywordMatcher("NLP/secrets/icd_10_cm_index_clean.csv")
        self.sectionizer = Sectionizer("NLP/secrets/sections.csv")
        self.entityMatcher = EntityMatchers(self.nlp, self.icdKwMatcher.keywordPhrases)
        self.sentencizer = Sentencizer(self.nlp)
        self.tokenizer = CustomTokenizer(self.nlp)

    def analyzeText(self, text, scope='document'):
        '''
        - scope can have three values:
            - 'document': keyword matching searches in the scope of the whole document
            - 'section': keyword matching searches within the scopes of single sections
            - 'sentence': keyword matching searches within the scopes of single sentences
        '''
        doc = self.nlp(text)
        sections = self.sectionizer.getSectionsForAnnotation(doc)
        logicEntities = self.entityMatcher.getLogicMatchesForAnnotation(doc)
        sentences = self.sentencizer.getMatchesForAnnotation(doc)
        tokens = self.tokenizer.getMatchesForAnnotation(doc)

        icdEntities, icdKeywords = self._icdKeywordMatchStrategy(doc, sections, sentences, scope)

        return {'entities': [*logicEntities, *icdEntities],
                'sections': sections,
                'sentences': sentences,
                'tokens': tokens,
                'icd': icdKeywords
                }

    def _icdKeywordMatchStrategy(self, doc, sections, sentences, scope):

        icdEntities = []
        icdKeywords = []

        if scope == 'document':
            icdKeywords = self.entityMatcher.getIcdKeywordMatches(doc)
            icdEntities = self.icdKwMatcher.getIcdAnnotations(icdKeywords)

        elif scope == 'section':

            for section in sections:
                sectionStart = section['start']
                sectionEnd = section['end']
                sectionTag = section['tag']
                textInSection = doc.text[sectionStart:sectionEnd]
                icdKeywordsInSection = self.entityMatcher.getIcdKeywordMatches(
                    self.nlp(textInSection), offset=sectionStart)
                icdEntitiesInSection = self.icdKwMatcher.getIcdAnnotations(icdKeywordsInSection, section=sectionTag)

                if len(icdKeywordsInSection) > 0:
                    icdKeywords += icdKeywordsInSection
                if len(icdEntitiesInSection) > 0:
                    icdEntities += icdEntitiesInSection

        elif scope == 'sentence':

            for sentence in sentences:
                sentenceStart = sentence['start']
                sentenceEnd = sentence['end']
                textInSentence = doc.text[sentenceStart:sentenceEnd]
                icdKeywordsInSentence = self.entityMatcher.getIcdKeywordMatches(
                    self.nlp(textInSentence), offset=sentenceStart)
                icdEntitiesInSentence = self.icdKwMatcher.getIcdAnnotations(icdKeywordsInSentence)

                if len(icdKeywordsInSentence) > 0:
                    icdKeywords += icdKeywordsInSentence
                if len(icdEntitiesInSentence) > 0:
                    icdEntities += icdEntitiesInSentence

        for icdEntity in icdEntities:
            icdEntity["tag"] = icdEntity["tag"].replace(".","")
            currentTag = icdEntity
            while True:
                try:
                    currentTag = currentTag["next"]
                    currentTag["tag"] = currentTag["tag"].replace(".","")
                except:
                    break
        return (icdEntities, icdKeywords)
