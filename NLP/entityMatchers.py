from spacy.matcher import Matcher
from NLP.matcherPatterns import Labels, negation_forward_patterns, negation_backward_patterns, negation_bidirection_patterns, closure_patterns


class EntityMatchers:

    def __init__(self, nlp):
        self.negation_matcher = Matcher(nlp.vocab)
        self.closure_matcher = Matcher(nlp.vocab)

        # self._addMatcherPatternFromFile()
        self._buildMatchers()

    def _addMatcherPatternFromFile(self):
        '''Function for loading matcher terms from file to negation_matcher.'''

        matcher_terms = self._loadNegationTermsFromFile("NLP/secrets/neg_list_complete.txt")

        for matcher_item in matcher_terms:
            phrase_string = matcher_item['phrases']   # ie: "[{'LOWER': 'negative'},{'LOWER': 'for'}]"
            matcher_category = matcher_item['category']
            neg_dir = matcher_item['direction']
            matcher_label = self._mapMatcherLabels(matcher_category, neg_dir)
            code_string = eval(self._createMatchPattern(phrase_string))
            self.negation_matcher.add(matcher_label, None, code_string)

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
        self.negation_matcher.add(Labels.NEGATION_FORWARD_LABEL, None, *negation_forward_patterns)
        self.negation_matcher.add(Labels.NEGATION_BACKWARD_LABEL, None, *negation_backward_patterns)
        self.negation_matcher.add(Labels.NEGATION_BIDIRECTION_LABEL, None, *negation_bidirection_patterns)
        self.closure_matcher.add(Labels.CLOSURE_BUT_LABEL, None, *closure_patterns)

    def _getNegationMatches(self, doc):
        '''Returns list of tuples describing matches in format of (match_id, start_token_#, end_token_#)'''
        return self.negation_matcher(doc)

    def _getClosureMatches(self, doc):
        '''Returns list of tuples describing matches in format of (match_id, start_token_#, end_token_#)'''
        return self.closure_matcher(doc)

    def getMatchesForAnnotation(self, doc, **kwargs):
        '''Helper function used for manually visualizing a set of matched entities. 
        Given 1 or more sets of matches, returns a list of entities to be annotated manually.
        Returns list of dictionary containing: start_char_#, end_char_#, label.'''

        entities = []
        listOfMatches = [self._getNegationMatches(doc), self._getClosureMatches(doc)]

        for matches in listOfMatches:
            for match_id, start, end in matches:
                start_token = doc[start]
                end_token = doc[end-1]
                annotate_start_char = start_token.idx
                annotate_end_char = end_token.idx + len(end_token)
                label = doc.vocab.strings[match_id]
                entities.append({"start": annotate_start_char, "end": annotate_end_char, "tag": label, "type": "Logic"})

        return entities
