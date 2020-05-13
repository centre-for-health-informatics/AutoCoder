from NLP.matcherPatterns import Labels
from Utility.progress import printProgressBar
import csv
from spacy.matcher import PhraseMatcher
import NLP.debugSettings as debugFlags


class PhraseNormalizer:
    def __init__(self, nlp, lexicalFile, umlsFile):
        print("Initializing PhraseNormalizer...")
        umlsLookup = self._createUmlsDictionary(umlsFile)
        lexicalLookup = self._createLexicalDictionary(lexicalFile)
        self.normalizationDict = self._combineNormalizationDictionary(umlsLookup, lexicalLookup)

        self.normalizePhraseMatcher = PhraseMatcher(nlp.vocab)
        self._loadNormalizePhrases(nlp)

    def _createUmlsDictionary(self, path):
        '''Create a dictionary of UMLS normalization from csv file.'''
        lookup = dict()
        with open(path) as file:
            csvReader = csv.reader(file)
            next(csvReader)  # skipe first row

            for row in csvReader:
                if row[4] != row[0]:
                    lookup[row[4]] = row[0]
                if row[6] != row[0]:
                    lookup[row[6]] = row[0]
        return lookup

    def _createLexicalDictionary(self, path):
        '''Create a dictionary of lexical normalization from csv file.'''
        lookup = dict()
        with open(path) as file:
            csvReader = csv.reader(file)
            next(csvReader)  # skipe first row

            for row in csvReader:
                if row[1] != row[5]:
                    lookup[row[1]] = row[5]
                if row[3] != row[1] and row[3] != row[5]:
                    lookup[row[3]] = row[5]
        return lookup

    def _combineNormalizationDictionary(self, *dictionaries):
        '''
        Give a number of normalization dictionaries, combine/chain them to create one normalization dictionary.
        The dictionaries must be passed in reverse order: i.e. final normalization step must be the first argument, 
        any additional normalization steps prior to the final step must be past as secondary, third arguments, etc.
        '''
        outputDict = dict()

        for dictionary in dictionaries:

            for key, value in dictionary.items():

                if not key in outputDict.keys():  # key is not found in outputDict, add key-value pair
                    outputDict[key] = value

                if value in outputDict.keys():  # value is found as a key of outputDict, make new entry as result of chaining
                    outputDict[key] = outputDict[value]

        return outputDict

    def _loadNormalizePhrases(self, nlp):
        '''
        Populate Spacy PhraseMatcher with normalization search phrases.
        '''
        patterns = []
        total = len(self.normalizationDict)
        for i, phrase in enumerate(self.normalizationDict.keys()):
            patterns.append(nlp(phrase))
            printProgressBar(i+1, total, prefix='Loading normalization phrases:', suffix='Complete', length=5)
        self.normalizePhraseMatcher.add(Labels.NORMALIZE_LABEL, None, *patterns)

    def getNormPhrases(self, doc, offset=0, **kwargs):
        '''
        Given a doc (of type Spacy.nlp(Str)), find and return a list normalization phrases.
        '''
        # outputDetail = kwargs.get('outputDetail')
        debug = kwargs.get('debug')

        spacyMatches = self.normalizePhraseMatcher(doc)
        outputMatches = []

        for match_id, start, end in spacyMatches:

            start_token = doc[start]
            end_token = doc[end-1]
            annotate_start_char = start_token.idx
            annotate_end_char = end_token.idx + len(end_token)

            text = doc.text[annotate_start_char:annotate_end_char]
            normalizedTo = self.normalizationDict[text]

            matchObj = {
                "start": annotate_start_char + offset,
                "end": annotate_end_char + offset,
                "text": text,
                "normalizedTo": normalizedTo,
                "type": Labels.NORMALIZE_LABEL
            }

            outputMatches.append(matchObj)

        if debug and debugFlags.phraseNormalizer in debug:
            print("////////////////// phraseNormalizer returns //////////////////")
            print(outputMatches)
            print("//////////////////////////////////////////////////////////////")

        return outputMatches
