class Sentencizer:

    def __init__(self, nlp):
        print("Initializing Sentencizer...")
        self.nlp = nlp
        self.nlp.add_pipe(self._sentence_boundary, before='parser')

    def _set_start(self, token, action):
        if token.is_sent_start == None:
            token.is_sent_start = action
        return token

    def _sentence_boundary(self, doc):
        '''Add custom sentence boundary definitions'''

        delimiters = ['\n\n', '\n\n\n', '.', '?', '!']

        # Explicit rules
        for token in doc:
            if token.i + 1 < len(doc):
                if token.text.isnumeric() and doc[token.i-1].text.endswith('\n') and doc[token.i+1].text == '.':
                    doc[token.i].is_sent_start = True
                    doc[token.i+1].is_sent_start = False
                    doc[token.i+2].is_sent_start = False
                    doc[token.i-1].is_sent_start = False

        # Delimiter based for tokens not affected by explicit rules
        for token in doc:
            if token.i + 1 < len(doc):
                # Delimiters
                if token.text in delimiters:
                    self._set_start(doc[token.i+1], True)
                else:
                    self._set_start(doc[token.i+1], False)
        return doc

    def getSentences(self, doc, **kwargs):
        '''Helper function used for visualizing the whole sentences in a document. Returns a list of sentences to be annotated.'''
        sentences = []

        outputDetail = kwargs.get('outputDetail')

        for i, sent in enumerate(doc.sents):
            start_char = doc[sent.start].idx
            end_char = doc[sent.end-1].idx + len(doc[sent.end-1])

            sentenceAnnot = {"start": start_char, "end": end_char, "tag": ""}

            if outputDetail:   # displaying numbering in annotations
                sentenceAnnot['number'] = i

            sentences.append(sentenceAnnot)
        return sentences
