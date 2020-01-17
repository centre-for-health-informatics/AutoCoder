import json
import re
import os
from collections import defaultdict


class Sectionizer:

    def __init__(self, patternFile):

        self._loadPatternsFromFile(patternFile)

    def _loadPatternsFromFile(self, patternFile):
        if patternFile.lower().endswith('.csv'):
            self._makeJSONfromCSV(patternFile)
            self.sections_regex, self.sections = self._loadSectionPatternsFromCSV(patternFile)
        elif patternFile.lower().endswith('json'):
            self.sections_regex, self.sections = self._loadSectionPatternsFromJSON(patternFile)

    def _loadSectionPatternsFromJSON(self, patternFile):
        expressions = set()
        sections = defaultdict(list)

        with open(patternFile, mode='r') as file:
            root = json.load(file)

            for sectionName, sectionAlias in self._jsonSectionNameAliasGenerator(root):
                expressions.add(self._makeRegularExpression(sectionAlias))
                sections[sectionName].append(sectionAlias)

        return expressions, sections

    def _jsonSectionNameAliasGenerator(self, jsonObj):
        '''Recursively look through a section pattern json, returns section name and alias pairs as a tupple.'''

        for k, v in jsonObj.items():
            if k == 'aliases':
                for alias in v:
                    yield (jsonObj['name'], alias)

            elif k == 'children':
                for child in v:
                    yield from self._jsonSectionNameAliasGenerator(child)

    def _makeRegularExpression(self, sectionAlias):
        return ('\\n\**' + sectionAlias + '\**.?\\n')

    def _loadSectionPatternsFromCSV(self, patternFile):
        expressions = set()   # regex for section headers in document
        sections = defaultdict(list)

        with open(patternFile, mode='r') as f:   # file containing dictionary for mapping section headers
            for line in f:
                section = line.strip().split(',')[0]
                alias = line.strip().split(',')[1].lower()
                sections[section].append(alias)
                expressions.add(self._makeRegularExpression(alias))

        return expressions, sections

    def _makeJSONfromCSV(self, csvFile):
        '''Given a csv file containing section patterns, create a json pattern file.'''
        with open(csvFile, mode='r') as file:

            root = {"name": "root", "children": []}

            for line in file:
                section = line.strip().split(',')[0]
                section_alias = line.strip().split(',')[1].lower()

                for child in root['children']:
                    if section == child['name']:
                        child['aliases'].append(section_alias)
                        break
                else:
                    root['children'].append({'name': section, 'aliases': [section_alias]})

        jsonFile = os.path.splitext(csvFile)[0]+'.json'

        with open(jsonFile, mode="w") as file:
            json.dump(root, file)

        return root

    def _getSectionsFromDoc(self, doc):
        '''Given a Spacy document, outputs a list of tuples containing character index (start, end) and text of the section headers.'''

        doc_sections = []  # list of sections in format of (start_char, end_char, section_header_in_doc)

        for expression in self.sections_regex:
            for match in re.finditer(expression, doc.text.lower()):
                start, end = match.span()
                section = doc.text.lower()[start+1:end-1]
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

    def _sectionizeDoc(self, doc):
        '''Creates a list of sections from a given Spacy doc.
        Returns a list of dictionaries. Each dictionary contains standard_header, header_in_doc, text_indicies, and text.'''

        doc_sections = self._getSectionsFromDoc(doc)
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
                sec_dict['text'] = doc.text[section[0]:doc_sections[i+1][0]]
            else:
                sec_dict['text_indicies'] = (section[0], len(doc.text))
                sec_dict['text'] = doc.text[section[0]:]

            document.append(sec_dict)
        return document

    def getSectionsForAnnotation(self, doc):
        '''Returns a list of sections to be annotated.'''
        sections = self._sectionizeDoc(doc)
        sections_annotate = []

        for sec in sections:
            start = sec['text_indicies'][0]
            end = sec['text_indicies'][1]
            label = sec['standard_header']
            sections_annotate.append({"start": start, "end": end, "tag": label})

        return sections_annotate
