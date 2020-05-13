from spacy.matcher import Matcher, PhraseMatcher
from NLP.matcherPatterns import Labels, negation_forward_patterns, negation_backward_patterns, negation_bidirection_patterns, closure_patterns
import csv
from Utility.progress import printProgressBar


class EntityMatchers:

    def __init__(self, nlp, icdKeywordPhrases, **kwargs):
        print("Initializing EntityMatchers...")
        self.negationMatcher = Matcher(nlp.vocab)
        self.closureMatcher = Matcher(nlp.vocab)
        self.icdKwMatcher = PhraseMatcher(nlp.vocab)

        # self._addNegationPatternFromFile()
        self._buildMatchers()
        #  self._loadIcdKeywordFromFile(nlp, filePath)
        self._loadIcdKeywordPhrases(nlp, icdKeywordPhrases)

    def _loadIcdKeywordPhrases(self, nlp, icdKeywordPhrases):
        '''Given a list of phrases, create PhraseMatcher patterns'''
        patterns = []
        total = len(icdKeywordPhrases)
        for i, phrase in enumerate(icdKeywordPhrases):
            patterns.append(nlp(phrase))
            printProgressBar(i+1, total, prefix='Loading keyword phrases:', suffix='Complete', length=5)

        self.icdKwMatcher.add(Labels.ICD_KEYWORD_LABEL, None, *patterns)

    def _loadIcdKeywordFromFile(self, nlp, IcdKeywordFile):
        '''Function for loading Icd keyword phrases from file, and create PhraseMatcher patterns'''
        with open(IcdKeywordFile, mode='r') as file:
            csvReader = csv.reader(file)
            phrases = list(map(lambda item: item[0], list(csvReader)))
            patterns = []
            for phrase in phrases:
                patterns.append(nlp(phrase))

            self.icdKwMatchericdKwMatcher.add(Labels.ICD_KEYWORD_LABEL, None, *patterns)

    def _addNegationPatternFromFile(self):
        '''Function for loading negation matcher terms from file to negationMatcher.'''

        matcher_terms = self._loadNegationTermsFromFile("NLP/neg_list_complete.txt")

        for matcher_item in matcher_terms:
            phrase_string = matcher_item['phrases']   # ie: "[{'LOWER': 'negative'},{'LOWER': 'for'}]"
            matcher_category = matcher_item['category']
            neg_dir = matcher_item['direction']
            matcher_label = self._mapMatcherLabels(matcher_category, neg_dir)
            code_string = eval(self._createMatchPattern(phrase_string))
            self.negationMatcher.add(matcher_label, None, code_string)

    def _loadNegationTermsFromFile(self, path):
        '''Helper function to load negation terms from file, 
        returns list of dictionaries containing following keys: 
        phrases, category, direction.'''

        patterns = list()

        with open(path) as f:

            for i, line in enumerate(f):

                if i == 0:
                    continue

                line = line.strip().split("\t")
                phrases = line[0]
                category = line[1]
                direction = line[2]
                patterns.append({"phrases": phrases, "category": category, "direction": direction})

        return patterns

    def _createMatchPattern(self, string):
        '''Helper function for loading negation terms from file that creates a Spacy matcher pattern given a string containing 1 or more phrases.'''

        word_pre_wrap = "{'LOWER': '"
        word_post_wrap = "'}"
        word_separator = ","

        pattern_string = "["  # begining of code string
        list_of_phrases = string.split()

        for i, phrase in enumerate(list_of_phrases):

            if i > 0:
                pattern_string += word_separator

            pattern_string += word_pre_wrap + phrase.lower() + word_post_wrap

        pattern_string += "]"  # end of code string

        return pattern_string

    def _mapMatcherLabels(self, neg_category, neg_dir):
        '''Helper function for loading negation terms from file that maps negation labels from file to desired labels.'''

        cat_label = ""
        dir_label = ""

        if neg_category == "definiteNegatedExistence":
            cat_label = Labels.NEGATION_LABEL
        elif neg_category == "probableNegatedExistence":
            cat_label = Labels.NEGATION_LABEL
        elif neg_category == "pseudoNegation":
            cat_label = Labels.PSEUDO_NEGATION_LABEL
        else:
            cat_label = Labels.UNKNOWN_LABEL

        if neg_dir == "forward":
            dir_label = Labels.FORWARD_LABEL
        elif neg_dir == "backward":
            dir_label = Labels.BACKWARD_LABEL
        elif neg_dir == "bidirectional":
            dir_label = Labels.BIDIRECTION_LABEL
        else:
            dir_label = Labels.UNKNOWN_LABEL

        return cat_label + '_' + dir_label

    def _buildMatchers(self):
        self.negationMatcher.add(Labels.NEGATION_FORWARD_LABEL, None, *negation_forward_patterns)
        self.negationMatcher.add(Labels.NEGATION_BACKWARD_LABEL, None, *negation_backward_patterns)
        self.negationMatcher.add(Labels.NEGATION_BIDIRECTION_LABEL, None, *negation_bidirection_patterns)
        self.closureMatcher.add(Labels.CLOSURE_BUT_LABEL, None, *closure_patterns)

    def _parseMatches(self, matchList, doc, tagType, **kwargs):
        '''Helper function that parse the list of matches as output from Spacy, and returns a list of matches using our annotation notations.'''

        outputDetail = kwargs.get('outputDetail')

        outputMatches = []
        for match_id, start, end in matchList:

            start_token = doc[start]
            end_token = doc[end-1]

            matchObj = {
                "start": start_token.idx,  # start char position
                "end": end_token.idx + len(end_token),  # end char position
                "tag": doc.vocab.strings[match_id],  # label
                "type": tagType
            }

            if outputDetail:
                tokens = [doc[i] for i in range(start, end)]
                tokenText = ""
                for token in tokens:
                    tokenText += token.text_with_ws
                matchObj['text'] = tokenText

            outputMatches.append(matchObj)

        return outputMatches

    def getNegationMatches(self, doc, **kwargs):
        '''Returns list of dictionary containing: start char #, end char #, label, type'''
        spacyMatches = self.negationMatcher(
            doc)  # list of tuples describing matches in format of (match_id, start_token_#, end_token_#)
        annotMatches = self._parseMatches(spacyMatches, doc, 'Logic', **kwargs)
        return annotMatches

    def getClosureMatches(self, doc, **kwargs):
        '''Returns list of dictionary containing: start char #, end char #, label, type'''
        spacyMatches = self.closureMatcher(
            doc)  # list of tuples describing matches in format of (match_id, start_token_#, end_token_#)
        annotMatches = self._parseMatches(spacyMatches, doc, 'Logic', **kwargs)
        return annotMatches

    def getIcdKeywordMatches(self, doc, normalizedPhrases, offset=0, **kwargs):
        '''Get list of ICD keyword matches from document. Parameter offset is used to produce correct overall characrer positions when this method is used to process exerpts of the document in parts.'''
        spacyMatches = self.icdKwMatcher(doc)

        outputMatches = []

        for match_id, start, end in spacyMatches:
            start_token = doc[start]
            end_token = doc[end-1]
            annotate_start_char = start_token.idx
            annotate_end_char = end_token.idx + len(end_token)
            text = doc.text[annotate_start_char:annotate_end_char]

            outputMatches.append({"start": annotate_start_char + offset, "end": annotate_end_char +
                                  offset, "text": text, "type": Labels.ICD_KEYWORD_LABEL})

        if normalizedPhrases:  # normalizedPhrases is not None, combine outputMatches with normalizedPhrases

            return self.combineReplaceNormalizedPhrases(normalizedPhrases, outputMatches)

        return outputMatches

    def combineReplaceNormalizedPhrases(self, normPhrases, phrases):
        '''
        Given list of normalized phrases and keyword matched phrases, combine into one list.
        This method makes sure the combined output list has unique spans from both normPhrases and phrases. 
        Any span from normPhrases will have both the 'normalizedTo' and 'text' keys.
        '''

        combinedOutput = []

        for phrase in phrases:

             # look for text span from the list of normPhrases, with identical start and end character positions
            sameSpan = next((x for x in normPhrases if x['start'] ==
                             phrase['start'] and x['end'] == phrase['end']), None)

            if sameSpan:  # add key to the phrase, copy value from normPhrase with same span
                phrase['normalizedTo'] = sameSpan['normalizedTo']

            combinedOutput.append(phrase)

        for normPhrase in normPhrases:
             # look for text span from the list of phrases, with identical start and end character positions
            sameSpan = next((x for x in phrases if x['start'] ==
                             normPhrase['start'] and x['end'] == normPhrase['end']), None)

            if sameSpan is None:
                normPhrase['type'] = Labels.ICD_KEYWORD_LABEL
                combinedOutput.append(normPhrase)

        return combinedOutput

    def getLogics(self, doc, **kwargs):

        return [*self.getNegationMatches(doc, **kwargs), *self.getClosureMatches(doc, **kwargs)]
