import json
import re
import os
from collections import defaultdict
import NLP.debugSettings as debugFlags


class Sectionizer:

    def __init__(self, patternFile):
        print("Initializing Sectionizer...")
        self._loadPatternsFromFile(patternFile)

    def _loadPatternsFromFile(self, patternFile):
        if patternFile.lower().endswith('.csv'):
            self._makeJSONfromCSV(patternFile)
            self.sectionsRegex, self.sections = self._loadSectionPatternsFromCSV(patternFile)
        elif patternFile.lower().endswith('json'):
            self.sectionsRegex, self.sections = self._loadSectionPatternsFromJSON(patternFile)

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
        return {
            '\\n\**' + sectionAlias + '\**.?\\n',
            '\\n' + sectionAlias + ':+\s*'
        }

    def _loadSectionPatternsFromCSV(self, patternFile):
        expressions = set()   # regex for section headers in document
        sections = defaultdict(list)

        with open(patternFile, mode='r') as f:   # file containing dictionary for mapping section headers
            for line in f:
                section = line.strip().split(',')[0]
                alias = line.strip().split(',')[1].lower()
                sections[section].append(alias)
                expressions.update(self._makeRegularExpression(alias))

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

    def _findSectionEndings(self, doc):
        endingStrings = ['electronically signed by', 'authenticated signature applied', 'dictated by:']
        sectionEndings = []  # characters where sections end
        for ending in endingStrings:
            for match in re.finditer(ending, doc.text.lower()):
                sectionEndings.append(match.span()[0])
        return sectionEndings

    def _getSectionsFromDoc(self, doc):
        '''Given a Spacy document, outputs a list of tuples containing character index (start, end) and text of the section headers.'''

        doc_sections = []  # list of sections in format of (start_char, end_char, section_header_in_doc)

        for expression in self.sectionsRegex:
            for match in re.finditer(expression, doc.text.lower()):
                start, end = match.span()
                section = doc.text.lower()[start+1:end-1]
                doc_sections.append((start, end, section))

        # Sorting sections in order
        doc_sections.sort()

        # Adding section at the beginning if there is not a section there
        # if len(doc_sections) > 0 and doc_sections[0][0] != 0:
        #     temp = doc_sections
        #     doc_sections = [(0, 0, '')]
        #     doc_sections.extend(temp)
        # else:
        #     doc_sections = [(0, 0, '')]

        return self._cleanSectionHeadings(doc_sections)

    def _cleanSectionHeadings(self, doc_sections):
        '''Given a list of sorted doc section headings, check of overlap, returns cleaned list.'''
        lastStart = None
        lastEnd = None
        lastHeading = None

        output = []

        def _getLongestSectionHeading(sectionHeadings):
            return max(sectionHeadings, key=lambda x: x[1] - x[0])[2]

        for start, end, heading in doc_sections:
            if lastStart is None:  # loop initial condition
                lastStart = start
                lastEnd = end
                lastHeading = heading
                output.append((start, end, heading))

            elif start >= lastEnd:  # no overlap
                output.append((start, end, heading))

            elif start < lastEnd and end > lastEnd:  # partial overlap, keep longer heading
                output.pop()
                combinedHeading = (start, lastEnd, _getLongestSectionHeading(
                    [(start, end, heading), (lastStart, lastEnd, lastHeading)]))
                output.append(combinedHeading)

            lastStart = start
            lastEnd = end
            lastHeading = heading

        return output

    def _sectionizeDoc(self, doc, **kwargs):
        '''Creates a list of sections from a given Spacy doc.
        Returns a list of dictionaries. Each dictionary contains standard_header, header_in_doc, and text_indicies.'''

        debug = kwargs.get('debug')

        endings = self._findSectionEndings(doc)
        doc_sections = self._getSectionsFromDoc(doc)  # list of section headings as tuples: (start, end, heading)
        document = []

        if debug and debugFlags.sectionizer in debug:
            print("/////// doc_sections///////")
            print(doc_sections)
            print("///////////////////////////")

        for i, section in enumerate(doc_sections):
            general_section = ''
            section_heading = section[2].strip().replace('*', '')[:-1]

            for key, value in self.sections.items():
                if section_heading in value:
                    general_section = key
            sec_dict = dict()
            sec_dict['standard_header'] = general_section
            sec_dict['header_in_doc'] = section[2]

            # For all sections except the last one, go to section ending or a defined ending of a section
            if i != len(doc_sections) - 1:
                end = None
                for ending in endings:
                    if ending > section[0]:
                        end = ending
                        break
                sec_dict['text_indicies'] = (section[0], min(doc_sections[i+1][0], end)
                                             if end else doc_sections[i+1][0])
            # for the last section
            else:
                end = None
                for ending in endings:
                    if ending > section[0]:
                        end = ending
                        break
                sec_dict['text_indicies'] = (section[0], end if end else len(doc.text))

            document.append(sec_dict)
        return document

    def getSections(self, doc, **kwargs):
        '''Returns a list of sections to be annotated.'''
        outputDetail = kwargs.get('outputDetail')

        sections = self._sectionizeDoc(doc, **kwargs)
        sections_annotate = []

        for sec in sections:

            sec_annotation = {
                "start": sec['text_indicies'][0],
                "end": sec['text_indicies'][1],
                "tag": sec['standard_header'],
                "type": "Sections",  # TODO: currently being used by frontend to generate tag template, its an unnecesary key and inefficient source for information, should be removed after frontend is updated
            }

            if outputDetail:
                sec_annotation['header_text'] = sec['header_in_doc']

            sections_annotate.append(sec_annotation)

        return sections_annotate
