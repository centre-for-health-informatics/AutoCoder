from intervaltree import Interval, IntervalTree


class EntityPostProcessor:
    '''
    Pipeline for post-processing of matched entities. Must instantiate when a client thread connects to ensure data independence between clients.
    '''

    def __init__(self, sections, sentences, entities, entityType):
        self.sentences = sentences
        self.sections = sections
        self.sentenceIntervalTree = IntervalTree()
        self.sectionIntervalTree = IntervalTree()
        self.entities = [i for i in entities if i['type'] == entityType]

        for sent in sentences:
            self.sentenceIntervalTree[sent['start']:sent['end']] = sent

        for section in sections:
            self.sectionIntervalTree[section['start']:section['end']] = section

    def processICD(self, removeNested, maxSentDist, sectionsIgnored):
        '''Pre-defined post process specific for ICD entity types, returns list of entities for annotations.'''

        filteredEntities = self.filterAnnotationsFromSections(self.entities, sectionsIgnored)
        headEntities = self.buildHeadItemsList(filteredEntities)
        headEntities = self.filterBySentenceDistance(headEntities, maxSentDist)

        if removeNested:
            headEntities = self.filterNestedItems(headEntities)

        return self._getFlatList(headEntities)

    def filterAnnotationsFromSections(self, inputEntities, sectionsIgnored):
        '''Build filtered list of entities, ignore ones in sectionsToIgnore'''

        output = []

        for entity in inputEntities:
            intervals = self.sectionIntervalTree[entity['start']:entity['end']]
            for interval in intervals:  # get first item from set
                section = interval.data
                if not section['tag'] in sectionsIgnored:
                    output.append(entity)
                break

        return output

    def buildHeadItemsList(self, inputEntities,):
        '''
        Build a list of linked-list style of annotations, where each item is a dictionary with an attribute 'next' which points to the next linked item.
        This method is required due to LanguageProcessor currently produces flat lists of annotations.
        '''
        output = []

        for i, entity in enumerate(inputEntities):
            isHead = True

            # loop through the list to see if another entity has 'next' attribute pointing at the cursor
            for j, cursor in enumerate(inputEntities):
                if i == j:
                    continue
                if 'next' in cursor and cursor['next'] == entity:
                    isHead = False

            if isHead:
                output.append(entity)

        return output

    def filterBySentenceDistance(self, headEntities, maxSentDist):
        '''Add sentence index number to each of the entity tokens and remove ones beyond the maxSentDist threshold.'''

        filteredHeadEntities = []

        for entity in headEntities:
            sentenceIndices = []

            cursor = entity
            sentenceIndices.append(self._addSentenceIndex(cursor))

            while 'next' in cursor:
                cursor = cursor['next']
                sentenceIndices.append(self._addSentenceIndex(cursor))

            if max(sentenceIndices) - min(sentenceIndices) <= maxSentDist:
                filteredHeadEntities.append(entity)

        return filteredHeadEntities

    def filterNestedItems(self, headEntities):
        '''
        Filter the head entities list to produce list with nested items removed.
        '''

        sortedHeadEntities = sorted(headEntities, key=lambda item: self._getLinkDepth(item), reverse=True)
        removalIndices = set()
        for i, item in enumerate(sortedHeadEntities):
            compareIndex = i + 1

            while compareIndex < len(sortedHeadEntities):

                nestStatus = self._checkNested(item, sortedHeadEntities[compareIndex])

                if nestStatus > 0:
                    removalIndices.add(compareIndex)

                compareIndex += 1

        return [item for i, item in enumerate(sortedHeadEntities) if i not in removalIndices]

    def _addSentenceIndex(self, entity):
        '''Given an entity, appends sentence index as an attribute. Returns the sentence index.'''
        interval = list(self.sentenceIntervalTree[entity['start']:entity['end']])[0]  # get first item from set
        sentenceIndex = self.sentences.index(interval.data)
        entity['sent-idx'] = sentenceIndex
        return sentenceIndex

    def _getLinkDepth(self, head):
        cursor = head
        i = 1
        while 'next' in cursor:
            i += 1
            cursor = cursor['next']
        return i

    def _getSpanTuple(self, annot):
        return (annot['start'], annot['end'])

    def _checkNested(self, headA, headB):
        '''
            Given the heads of two linked set of annotations. Compare the spans of the two sets,
            return 1 if the first set is larger and overlaps all of the second set;
            return -1 if the second set is larger and overlaps all of the first set;
            return 0 otherwise (including when the two sets have equal spans).
        '''

        spansA = [self._getSpanTuple(headA)]
        spansB = [self._getSpanTuple(headB)]

        cursor = headA
        while 'next' in cursor:
            spansA.append(self._getSpanTuple(cursor['next']))
            cursor = cursor['next']

        cursor = headB
        while 'next' in cursor:
            spansB.append(self._getSpanTuple(cursor['next']))
            cursor = cursor['next']

        if set(spansA) > set(spansB):
            return 1
        elif set(spansA) < set(spansB):
            return -1
        else:
            return 0

    def _getFlatList(self, listOfLinkedLists):
        '''Iterate through the list of linked-lists, and create a list that contains every single item from every linked-list.'''

        flatList = []
        for head in listOfLinkedLists:
            flatList.append(head)
            cursor = head
            while 'next' in cursor:
                cursor = cursor['next']
                flatList.append(cursor)

        return flatList
