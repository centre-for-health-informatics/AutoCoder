from django.core.management.base import BaseCommand, CommandError
from ICD.models import Code
from collections import defaultdict
from django.db import transaction


class Command(BaseCommand):
    help = 'Generates Table of ICD-10 Codes'

    def readDataFile(self, filename):
        print("Reading", filename, "from local")
        with open("secrets/"+filename, 'r') as f:
            contents = f.readlines()
        if contents[-1] == '':
            del contents[-1]
        return contents


    def handle(self, *args, **options):
        Code.objects.all().delete()

        # Read in disabled codes
        disabledCodes = set()
        for line in self.readDataFile("DorO2018.csv"):
            line = line.strip()
            disabledCodes.add(line)

        # Read codes and descriptions from text file
        allCodes = set()
        codeDescriptions = dict()
        for line in self.readDataFile("codedescriptions.txt"):
            line = line.split('\t')
            code = line[0].strip()
            desc = line[1].strip().replace('"', '')
            allCodes.add(code)
            codeDescriptions[code] = desc

        categoryDescriptions = dict()
        for line in self.readDataFile("category_descriptions.csv"):
            line = line.split(',')
            code = line[0].strip()
            desc = line[1].strip().replace('"', '')
            categoryDescriptions[code] = desc

        # Generate all intermediate nodes and add to code set
        # Repeat until no more intermediate nodes are created
        parentsAdded = -1
        while parentsAdded != 0:
            parents = []
            for code in allCodes:
                parent = self.findParent(code)
                if parent != '':
                    parents.append(parent)
            oldLen = len(allCodes)
            allCodes.update(parents)
            parentsAdded = len(allCodes) - oldLen
        print("Number of nodes: ", len(allCodes))

        parentDict = dict()
        childrenDict = defaultdict(list)
        for code in allCodes:
            parent = self.findParent(code)
            # set parent of code
            parentDict[code] = parent
            if parent != '':
                # set code as child of parent
                childrenDict[parent].append(code)

        keywordDict = dict()
        for line in self.readDataFile("keywordTerms.txt"):
            splitline = line.split('\t')
            keywordDict[splitline[0]] = splitline[1]
        with transaction.atomic():
            count = 0
            codes = list(allCodes)
            codes.sort()
            for code in codes:
                # Check if ICD-10-CA has a description first and use that
                description = codeDescriptions.get(code, '')
                if description == '':
                    # Use descfiption from ICD-10-CM if it doesn't exist
                    description = categoryDescriptions.get(code, '')
                parent = parentDict[code]
                children = ''
                if len(childrenDict[code]) > 0:
                    childrenDict[code].sort()
                    for child in childrenDict[code]:
                        children += child + ','
                    children = children[:-1]

                if code in disabledCodes:
                    selectable = False
                else:
                    selectable = True

                # check if code has keyword associated with it
                keyword_terms = keywordDict.get(code, '').lower()
                if keyword_terms == '' and len(code) > 3:
                    # add keywords from children if empty (due to using CM keywords)
                    for i in range(10):
                        keyword_terms += keywordDict.get(code + str(i), '').lower()
                row = Code.objects.create(code=code, children=children, parent=parent,
                                        description=description, keyword_terms=keyword_terms, selectable=selectable)
                row.save()
                count += 1
                if count % 1000 == 0:
                    print("Added", count, "codes")
        print("SAVED")

    # Returns parent code of any code
    def findParent(self, code):
        parent = ''
        if len(code) > 3:
            parent = code[:-1]
        elif len(code) == 3:
            parent = code[0]
        return parent
