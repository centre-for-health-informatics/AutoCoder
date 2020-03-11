import spacy
from NLP.entityMatchers import EntityMatchers
from NLP.sectionizer import Sectionizer
from NLP.sentencizer import Sentencizer
from NLP.tokenizer import CustomTokenizer
from NLP.icdKeywordMatcher import IcdKeywordMatcher
from NLP.entityPostProcessor import EntityPostProcessor
from NLP.matcherPatterns import Labels
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
        print("LanguageProcessor ready.")

    def analyzeText(self, text, scope='document', removeNested=True, maxSentDist=3, sectionsIgnored=[]):
        '''
        - scope can have three values:
            - 'document': Default, keyword matching searches in the scope of the whole document
            - 'section': keyword matching searches within the scopes of single sections
            - 'sentence': keyword matching searches within the scopes of single sentences
        - removeNested: default to True, remove nested multi-part linked entities and only keep the largest one.
        - maxSentDist: default to 3, remove multi-part linked entities if the parts are more than 3 sentences apart.
        '''
        doc = self.nlp(text)
        sections = self.sectionizer.getSectionsForAnnotation(doc)
        logicEntities = self.entityMatcher.getLogicMatchesForAnnotation(doc)
        sentences = self.sentencizer.getMatchesForAnnotation(doc)
        tokens = self.tokenizer.getMatchesForAnnotation(doc)

        icdEntities = self._icdKeywordMatchStrategy(
            doc, sections, sentences, scope, removeNested, maxSentDist, sectionsIgnored)

        return {'entities': [*logicEntities, *icdEntities],
                'sections': sections,
                'sentences': sentences,
                'tokens': tokens
                }

    def _icdKeywordMatchStrategy(self, doc, sections, sentences, scope, removeNested, maxSentDist, sectionsIgnored):

        if scope == 'document':
            icdKeywords = self.entityMatcher.getIcdKeywordMatches(doc)
            icdEntities = self.icdKwMatcher.getIcdAnnotations(icdKeywords)

        elif scope == 'section':
            icdEntities, _ = self._getIcdKeywordByParts(doc, sections)

        elif scope == 'sentence':
            icdEntities, _ = self._getIcdKeywordByParts(doc, sentences)

        cleanIcdEntities = EntityPostProcessor(sections, sentences, icdEntities, Labels.ICD_KEYWORD_LABEL).processICD(
            removeNested, maxSentDist, sectionsIgnored)

        return cleanIcdEntities

    def _getIcdKeywordByParts(self, doc, parts):
        '''Search document part by part for ICD keywords, constraining the search scope to each part.'''
        icdEntities = []
        icdKeywords = []
        for part in parts:
            partStart = part['start']
            partEnd = part['end']
            partTag = part['tag']
            textInPart = doc.text[partStart:partEnd]
            icdKeywordsInPart = self.entityMatcher.getIcdKeywordMatches(self.nlp(textInPart), offset=partStart)
            icdEntitiesInPart = self.icdKwMatcher.getIcdAnnotations(icdKeywordsInPart)

            if len(icdKeywordsInPart) > 0:
                icdKeywords += icdKeywordsInPart
            if len(icdEntitiesInPart) > 0:
                icdEntities += icdEntitiesInPart

        self._formatIcdEntities(icdEntities)

        return (icdEntities, icdKeywords)

    def _formatIcdEntities(self, icdEntities):
        '''Remove dots from ICD codes, add additional tags.'''
        for icdEntity in icdEntities:
            icdEntity["tag"] = icdEntity["tag"].replace(".", "")
            icdEntity["confirmed"] = False
            currentTag = icdEntity
            while True:
                try:
                    currentTag = currentTag["next"]
                    currentTag["tag"] = currentTag["tag"].replace(".", "")
                except:
                    break
