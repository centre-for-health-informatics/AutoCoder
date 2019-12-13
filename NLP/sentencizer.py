class Sentencizer:

    def __init__(self,doc,nlp):
        self.doc = doc
        self.nlp = nlp
        self.nlp.add_pipe(self._sentence_boundary, before='parser')

    def _set_start(self, token, action):
        if token.is_sent_start == None:
            token.is_sent_start = action
        return token

    def _sentence_boundary(self, doc):
            '''Add custom sentence boundary definitions'''
            
            delimiters = ['\n\n','\n\n\n','.','?','!']
            
            # Explicit rules
            for token in self.doc:
                if token.i + 1 < len(self.doc):
                    if token.text.isnumeric() and self.doc[token.i-1].text.endswith('\n') and self.doc[token.i+1].text == '.':
                        self.doc[token.i].is_sent_start = True
                        self.doc[token.i+1].is_sent_start = False
                        self.doc[token.i+2].is_sent_start = False
                        self.doc[token.i-1].is_sent_start = False
                    
            # Delimiter based for tokens not affected by explicit rules
            for token in self.doc:
                if token.i + 1 < len(self.doc):
                # Delimiters
                    if token.text in delimiters:
                        self._set_start(self.doc[token.i+1], True)
                    else:
                        self._set_start(self.doc[token.i+1], False)


    def getMatchesForAnnotation(self, **kwargs):
        '''Helper function used for visualizing the whole sentences in a document. Returns a list of sentences to be annotated.'''
        sentences = []
        for i, sent in enumerate(self.doc.sents):
            start_char = self.doc[sent.start].idx
            end_char = self.doc[sent.end-1].idx + len(self.doc[sent.end-1])
            
            if 'number' in kwargs and kwargs['number']:   # Optional argument for displaying numbering in annotations
                label=str(i)
            else:
                label=''

            sentences.append({"start":start_char, "end": end_char, "label": ''})
        return sentences