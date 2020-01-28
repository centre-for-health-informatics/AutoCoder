from collections import defaultdict
import csv
from NLP.matcherPatterns import Labels


class IcdKeywordMatcher:

    def __init__(self, icdIndexFilePath):
        print("Initializing IcdKeywordMatcher...")
        self.keywordPhrases = None
        self.searchAsset = self.createSearchAssetFromCSV(icdIndexFilePath)

    def createSearchAssetFromCSV(self, path):
        '''
        Returns list of dictionaries used for searching and referencing. The list has the following items:
        index 0: dictionary for looking up icd_code by seq_id. eg: {seq_id: icd_code}
        index 1: dictionary for looking up seq_id by phrases (level 1 only). eg {phrase: [seq_id]}
        index 2: dictionary for looking up phrases (level 2 only) by seq_id. eg {seg_id: [phrase]}
        index 3: dictionary for looking up phrases (level 3 only) by seq_id. eg {seg_id: [phrase]}
        ...
        '''

        segToIcd = defaultdict(str)
        levelOnePhraseToSeq = defaultdict(list)
        levelTwoSegToPhrases = defaultdict(list)
        knowledgeDictionaries = [segToIcd, levelOnePhraseToSeq, levelTwoSegToPhrases]
        keywordPhraseSet = set()

        print("Creating search asset for IcdKeywordMatcher...")

        with open(path, mode='r') as file:

            csvReader = csv.reader(file, delimiter=',')

            for i, row in enumerate(csvReader):
                if i == 0:
                    continue

                _, icd_code, seq_id, _, phrase, _, level_final = row

                level = int(level_final)
                keywordPhraseSet.add(phrase)

                if level == 1:
                    segToIcd[seq_id] = icd_code
                    levelOnePhraseToSeq[phrase].append(seq_id)

                else:
                    while len(knowledgeDictionaries) <= level:
                        knowledgeDictionaries.append(defaultdict(list))
                    knowledgeDictionaries[level][seq_id].append(phrase)

        self.keywordPhrases = list(keywordPhraseSet)
        self.keywordPhrases.sort()

        return knowledgeDictionaries

    def getIcdAnnotations(self, keywordMatches):
        '''
        Given a list of icd keyword matches found in a document that denotes positions of keywords within the string,
        Returns a list of annotations.
        Params:
        - keywordMatches: a list of dictionaries describing position of tokens, dictionaries must have the key 'text' as required by self.getICDforTokens().
        '''

        icdCodeTuples = self.getICDforTokens(keywordMatches)
        ''' 
        list of tuples in the form such as the following
        ('I46.8',
          [{'start': 279, 'end': 285, 'text': 'arrest', 'type': 'ICD_KW'},
           {'start': 2850, 'end': 2857, 'text': 'cardiac', 'type': 'ICD_KW'}])
        '''
        annotations = []

        for icdLabel, meta in icdCodeTuples:

            for i, annotation in enumerate(meta):

                annot = {"start": annotation['start'],
                         "end": annotation['end'],
                         "tag": icdLabel,
                         "type": Labels.ICD_KEYWORD_LABEL
                         }

                if i > 0:

                    prevAnnot['next'] = annot

                prevAnnot = annot
                annotations.append(annot)

        return annotations

    def getICDforTokens(self, searchTokens):
        '''
        Params:
        - a list of search tokens, such as words from a single sentence. This could be a string, or a dictionary containing the key 'text' that maps to a string.
        - a reference to search Asset (as from createSearchAsset()). searchAsset is a list [{seq_id: icd_code}, {level_one_phrase: [seq_id]}, {seg_id: [level_two_phrases]}, {seg_id: [level_three_phrase]}, ...]
        Returns:
        - a list of tuples, where the first element of the tuple is an icd code and the second element is a list of tokens that triggered the icd code.
        '''

        if len(searchTokens) < 1:
            return

        valid_seq_tuples = []

        for searchToken in searchTokens:

            # If searchToken is a string, it is the search term,
            # otherwise if a dictionary is passed, it should have a key 'text' that contains the search string
            if type(searchToken) == str:
                searchTerm = searchToken

            elif type(searchToken) == dict and 'text' in searchToken:
                searchTerm = searchToken['text']

            else:
                print("Unknown search token data format.")
                return

            # search level 1 keywords
            if searchTerm in self.searchAsset[1]:

                seq_ids = self.searchAsset[1][searchTerm]

                # for each level 1 match of seq_id
                for seq_id in seq_ids:

                    level = 2
                    matched_terms = self._recursiveLevelSearch(searchTokens, seq_id, level)

                    if 'FINAL_LEVEL_REACHED' in matched_terms:
                        matched_terms.insert(0, searchToken)
                        matched_terms.remove('FINAL_LEVEL_REACHED')
                        valid_seq_tuples.append((seq_id, matched_terms))

    #     print(valid_seq_tuples)

        icd_codes = []

        for seq_id_tuple in valid_seq_tuples:

            seq_id, token = seq_id_tuple

            icd_codes.append((self.searchAsset[0][seq_id], token))

    #     print(icd_codes)

        return icd_codes

    def _recursiveLevelSearch(self, searchTokens, seq_id, level):
        '''
        Helper functions that recursively checks deeper levels* of a sequence_id for matching keywords.
        Params:
        - searchTokens: a list of search tokens as input.
        - seq_id: seq_id to be checked against.
        - level: the level to start checking on.
        Returns:
        - 
        * This method is for level 2 and beyond, as searchAsset level 0 & 1 dictionaries have different data structures.
        '''

        # there is no deeper level for the sequence id, return True
        if not(seq_id in self.searchAsset[level]):
            #         print("No furthur level for seq_id, returning True.")
            return ["FINAL_LEVEL_REACHED"]
        else:
            current_level_phrases = self.searchAsset[level][seq_id]

            trigger_token = self._findTriggerTokenFromLevelPhrases(searchTokens, current_level_phrases)

            if trigger_token:
                #             print(f"Going to next level, level {level + 1}")
                return [trigger_token, *self._recursiveLevelSearch(searchTokens, seq_id, level + 1)]
            else:
                #             print(f"Did not find matching keyword for level {level}, returning False.")
                return ["FINAL_LEVEL_NOT_REACHED"]

    def _findTriggerTokenFromLevelPhrases(self, searchTokens, levelPhrases):
        '''
        Helper function that looks for a trigger token from a list of searchTokens, by comparing with a list of levelPhrases.
        Returns the trigger token if found, otherwise None.
        The searchTokens can be a list of strings, or dictionary with a key 'text' that contains a string.
        '''

        for token in searchTokens:

            if type(token) == str:
                searchTerm = token
            else:
                searchTerm = token['text']

            if searchTerm in levelPhrases:
                return token

        return None
