import spacy
from NLP.entityMatchers import EntityMatchers
from NLP.sectionizer import Sectionizer
from NLP.sentencizer import Sentencizer
from NLP.tokenizer import CustomTokenizer
from NLP.icdKeywordMatcher import IcdKeywordMatcher
from NLP.entityPostProcessor import EntityPostProcessor
from NLP.matcherPatterns import Labels
from NLP.phraseNormalizer import PhraseNormalizer
import spacy


class LanguageProcessor:
    def __init__(self):
        print("Initializing LanguageProcessor...")
        self.nlp = spacy.load('en_core_web_lg')
        self.phraseNormalizer = PhraseNormalizer(
            self.nlp, "NLP/Normalization_terms.csv", "NLP/UMLS_terms_normalized.csv")
        self.icdKwMatcher = IcdKeywordMatcher("NLP/icd_10_cm_index_clean.csv")
        self.sectionizer = Sectionizer("NLP/sections.csv")
        self.entityMatcher = EntityMatchers(self.nlp, self.icdKwMatcher.keywordPhrases)
        self.sentencizer = Sentencizer(self.nlp)
        self.tokenizer = CustomTokenizer(self.nlp)
        print("LanguageProcessor ready.")

    def analyzeText(self, text, scope='document', removeNested=True, maxSentDist=3, sectionsIgnored=[], phraseNorm=True):
        '''
        - scope can have three values:
            - 'document': Default, keyword matching searches in the scope of the whole document
            - 'section': keyword matching searches within the scopes of single sections
            - 'sentence': keyword matching searches within the scopes of single sentences
        - removeNested: default to True, remove nested multi-part linked entities and only keep the largest one.
        - maxSentDist: default to 3, remove multi-part linked entities if the parts are more than 3 sentences apart.
        - sectionsIgnored: default to [], list of standardized sections tags to be ignored for icd entity recognition.
        - phraseNorm: phrase normalization flag default to True.
        '''
        doc = self.nlp(text)
        sections = self.sectionizer.getSections(doc)
        logicEntities = self.entityMatcher.getLogics(doc)
        sentences = self.sentencizer.getSentences(doc)
        tokens = self.tokenizer.getTokens(doc)

        icdEntities = self._icdKeywordMatchStrategy(
            doc, sections, sentences, scope, removeNested, maxSentDist, sectionsIgnored, phraseNorm)

        return {'entities': [*logicEntities, *icdEntities],
                'sections': sections,
                'sentences': sentences,
                'tokens': tokens
                }

    def _icdKeywordMatchStrategy(self, doc, sections, sentences, scope, removeNested, maxSentDist, sectionsIgnored, phraseNorm):
        '''
        @Params:
        - doc: of type spacy.nlp.load(str)
        - sections: output of Sectionizer.getSections()
        - sentences: output of Sentencizer.getSentences()
        - scope: scope of ICD keyword searching, str values: 'section', 'sentence', defaults to 'document'
        - removeNested: whether to remove nested ICD keyword results, boolean.
        - maxSentDist: maximum sentence distance for ICD keyword searching when scope is set to 'section' or 'document'.
        - sectionsIgnored: a list of section header tags to ignore ICD keyword searching.
        - phraseNorm: whether to normalize keyword phrases before searching for ICD keyword, boolean.
        '''

        if scope == 'document':
            if phraseNorm:
                normalizedPhrases = self.phraseNormalizer.getNormPhrases(doc)
            else:
                normalizedPhrases = None
            icdKeywords = self.entityMatcher.getIcdKeywordMatches(doc, normalizedPhrases)
            icdEntities = self.icdKwMatcher.getIcdAnnotations(icdKeywords, phraseNorm)

        elif scope == 'section':
            icdEntities, _ = self._getIcdKeywordByParts(doc, sections, phraseNorm)

        elif scope == 'sentence':
            icdEntities, _ = self._getIcdKeywordByParts(doc, sentences, phraseNorm)

        cleanIcdEntities = EntityPostProcessor(sections, sentences, icdEntities, Labels.ICD_KEYWORD_LABEL).processICD(
            removeNested, maxSentDist, sectionsIgnored)

        return cleanIcdEntities

    def _getIcdKeywordByParts(self, doc, parts, phraseNorm):
        '''Search document part by part for ICD keywords, constraining the search scope to each part.'''
        icdEntities = []
        icdKeywords = []
        for part in parts:
            partStart = part['start']
            partEnd = part['end']
            partTag = part['tag']
            textInPart = doc.text[partStart:partEnd]

            if phraseNorm:
                normalizedPhrases = self.phraseNormalizer.getNormPhrases(doc, offset=partStart)
            else:
                normalizedPhrases = None

            icdKeywordsInPart = self.entityMatcher.getIcdKeywordMatches(
                self.nlp(textInPart), normalizedPhrases, offset=partStart)

            icdEntitiesInPart = self.icdKwMatcher.getIcdAnnotations(icdKeywordsInPart, phraseNorm)

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
