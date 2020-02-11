from django.core.management.base import BaseCommand, CommandError
from annotations.models import TreeCode
from collections import defaultdict
from django.db import transaction


class Command(BaseCommand):
    help = 'Generates Table of ICD-10 Codes (Includes chapters and blocks for the tree viewer)'

    def readDataFile(self, filename):
        with open("secrets/"+filename, 'r') as f:
            contents = f.readlines()
        if contents[-1] == '':
            del contents[-1]
        return contents

    def findParent(self, code):
        # returns parent code of actual codes
        parent = ''
        if len(code) > 3:
            parent = code[:-1]
        return parent

    def setCategoryHiearchy(self, startNum, endNum, block, startLetter, parentDict, childrenDict):
        # Sets hierarchy of block categories
        for j in range(startNum, endNum+1):
            child = startLetter + '{:02d}'.format(j)
            parentDict[child] = block
            childrenDict[block].append(child)

    def findChapter(self, block):
        # Determine which chapter the block belongs to by some character math
        for chapterRange in self.chapterRanges:
            blockVal = ord(block[0])*100 + int(block[1:3])
            chapVal = ord(chapterRange[0])*100 + int(chapterRange[1:3])
            if blockVal >= chapVal:
                chapter = self.chapters[chapterRange]
                return chapter
        chapter = self.chapters[chapterRange]
        return chapter

    def handle(self, *args, **options):
        # Read codes and descriptions from text file
        TreeCode.objects.all().delete()

        # Read in disabled codes
        disabledCodes = set()
        for line in self.readDataFile("DorO2018.csv"):
            line = line.strip()
            disabledCodes.add(line)

        allCodes = set()
        descriptions = dict()
        for line in self.readDataFile("codedescriptions.txt"):
            line = line.split('\t')
            code = line[0].strip()
            desc = line[1].strip().replace('"', '')
            allCodes.add(code)
            descriptions[code] = desc

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

        # Add ICD-10 chapters
        self.chapterRanges = []
        self.chapters = dict()

        baseCode = 'ICD-10-CA'
        allCodes.add(baseCode)
        descriptions[baseCode] = ''
        parentDict[baseCode] = ''
        for line in self.readDataFile("ICDChapters.txt"):
            line = line.strip().split('\t')
            chap = 'Chapter ' + line[0]
            chapChildren = line[1]
            chapDesc = line[2]
            allCodes.add(chap)
            descriptions[chap] = chapDesc
            parentDict[chap] = baseCode
            childrenDict[baseCode].append(chap)
            self.chapterRanges.append(chapChildren)
            self.chapters[chapChildren] = chap

            self.chapterRanges.sort()
            self.chapterRanges.reverse()

        # Add ICD-10 blocks
        for line in self.readDataFile("ICDBlocks.txt"):
            line = line.strip().split('\t')
            block = line[0].strip()
            blockDesc = line[1].strip().replace('"', '')
            allCodes.add(block)
            descriptions[block] = blockDesc
            chapter = self.findChapter(block)
            parentDict[block] = chapter
            childrenDict[chapter].append(block)

            # Add 3 letter codes to blocks
            if len(block) > 3:
                startNum = int(block[1:3])
                endNum = int(block[5:7])
                startLetter = block[0]
                endLetter = block[4]
                if startLetter != endLetter:
                    self.setCategoryHiearchy(startNum, 99, block, startLetter, parentDict, childrenDict)
                    numLettersBetween = ord(endLetter) - ord(startLetter) - 1
                    for i in range(numLettersBetween):
                        print(chr(ord(startLetter)+i+1))
                        self.setCategoryHiearchy(0, 99, block, chr(ord(startLetter)+i+1), parentDict, childrenDict)
                    self.setCategoryHiearchy(0, endNum, block, endLetter, parentDict, childrenDict)
                else:
                    self.setCategoryHiearchy(startNum, endNum, block, startLetter, parentDict, childrenDict)

        # Creating and saving objects
        with transaction.atomic():
            count = 0
            codes = list(allCodes)
            codes.sort()
            for code in codes:
                # Check if ICD-10-CA has a description first and use that
                description = descriptions.get(code, '')
                if description == '':
                    description = categoryDescriptions.get(code, '')
                    # Use descfiption from ICD-10-CM if it doesn't exist
                parent = parentDict[code]
                children = ''
                if len(childrenDict[code]) > 0:
                    childrenDict[code].sort()
                    for child in childrenDict[code]:
                        children += child + ','
                    children = children[:-1]

                row = TreeCode.objects.create(code=code, children=children, parent=parent, description=description)
                row.save()
                count += 1
                if count % 1000 == 0:
                    print("Added", count, "codes")
        print("SAVED")
