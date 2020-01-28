import spacy
from spacy.tokenizer import Tokenizer
from spacy.util import compile_infix_regex, compile_prefix_regex, compile_suffix_regex
import re


class CustomTokenizer:

    def __init__(self, nlp):
        print("Initializing Tokenizer...")
        self.nlp = nlp
        self.nlp.tokenizer = self.custom_tokenizer()

    def _make_prefix_cases(self, prefix_list):
        '''Given a list of prefixes, create alternative version of varying upper & lower cases, 
        return a list with regex for each prefix'''

        prefix_with_cases = []
        for prefix in prefix_list:
            for i in range(2**len(prefix)):
                bits = bin(i)[2:]
                while len(bits) < len(prefix):
                    bits = '0' + bits
                output = ''

                for letter in range(len(prefix)):
                    if bits[letter] == '0':
                        output += prefix[letter].lower()
                    else:
                        output += prefix[letter].upper()

                prefix_with_cases.append(output)

        return [prefix + '\.\s?' for prefix in prefix_with_cases]  # add "\.\s?" to each prefix

    def custom_tokenizer(self):
        '''Set up custom tokenizer'''

        default_infix = self.nlp.Defaults.infixes
        default_prefix = self.nlp.Defaults.prefixes
        default_suffix = self.nlp.Defaults.suffixes

        prefix_list = ['mr', 'dr', 'mrs', 'prof', 'ms', 'mx']
        prefix_re_list = self._make_prefix_cases(prefix_list)

        all_infix_re = compile_infix_regex(default_infix)
        all_prefix_re = spacy.util.compile_prefix_regex(tuple(list(default_prefix) + prefix_re_list))

        all_suffix_re = compile_suffix_regex(default_suffix)

        return Tokenizer(self.nlp.vocab, prefix_search=all_prefix_re.search, suffix_search=all_suffix_re.search, infix_finditer=all_infix_re.finditer, token_match=None)

    def getMatchesForAnnotation(self, doc, **kwargs):
        '''Used for visualizing tokens in a document. Returns a list of tokens to be annotated.'''
        tokens = []
        for i, token in enumerate(doc):
            start = token.idx
            end = start + len(token)

            if 'number' in kwargs and kwargs['number']:   # Optional argument for displaying numbering in annotations
                label = str(i)
            else:
                label = ''

            tokens.append({"start": start, "end": end, "tag": label})

        return tokens
