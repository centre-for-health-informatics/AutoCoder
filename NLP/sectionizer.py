
import re
from collections import defaultdict


class Sectionizer:

    def __init__(self, doc):
        self.doc = doc
        self.sections_regex, self.sections = self._loadSectionPatternsFromFile()

    def _loadSectionPatternsFromFile(self):
        expressions = set()   # regex for section headers in document
        sections = defaultdict(list)

        with open("NLP/secrets/sections.csv") as f:   # file containing dictionary for mapping section headers
            for line in f:
                section = line.strip().split(',')[0]
                description = line.strip().split(',')[1].lower()
                sections[section].append(description)
                expressions.add('\\n\**' + description + '\**.?\\n')

        return expressions, sections

    def _getSectionsFromDoc(self):
        '''Given a Spacy document, outputs a list of tuples containing character index (start, end) and text of the section headers.'''

        doc_sections = []  # list of sections in format of (start_char, end_char, section_header_in_doc)

        for expression in self.sections_regex:
            for match in re.finditer(expression, self.doc.text.lower()):
                start, end = match.span()
                section = self.doc.text.lower()[start+1:end-1]
                doc_sections.append((start, end, section))

        # Sorting sections in order and adding section at the beginning if there is not a section there
        doc_sections.sort()

        if len(doc_sections) > 0 and doc_sections[0][0] != 0:
            temp = doc_sections
            doc_sections = [(0, 0, '')]
            doc_sections.extend(temp)
        else:
            doc_sections = [(0, 0, '')]

        return doc_sections

    def _sectionizeDoc(self):
        '''Creates a list of sections from a given Spacy doc.
        Returns a list of dictionaries. Each dictionary contains standard_header, header_in_doc, text_indicies, and text.'''

        doc_sections = self._getSectionsFromDoc()
        document = []

        for i, section in enumerate(doc_sections):
            general_section = ''
            for key, value in self.sections.items():
                if section[2].replace('*', '') in value or section[2].replace('*', '')[:-1] in value:
                    general_section = key
            sec_dict = dict()
            sec_dict['standard_header'] = general_section
            sec_dict['header_in_doc'] = section
            if i != len(doc_sections) - 1:
                sec_dict['text_indicies'] = (section[0], doc_sections[i+1][0])
                sec_dict['text'] = self.doc.text[section[0]:doc_sections[i+1][0]]
            else:
                sec_dict['text_indicies'] = (section[0], len(self.doc.text))
                sec_dict['text'] = self.doc.text[section[0]:]

            document.append(sec_dict)
        return document

    def getSectionsForAnnotation(self):
        '''Returns a list of sections to be annotated.'''
        sections = self._sectionizeDoc()
        sections_annotate = []

        for sec in sections:
            start = sec['text_indicies'][0]
            end = sec['text_indicies'][1]
            tag = sec['standard_header']
            sections_annotate.append({"start": start, "end": end, "tag": tag, "type": "Sections"})

        return sections_annotate
