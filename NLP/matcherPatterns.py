class Labels:
    SENTENCE_START_LABEL = "SENT_S"
    NEGATION_LABEL = 'NEG'
    PSEUDO_NEGATION_LABEL = 'PSEU_NEG'
    FORWARD_LABEL = 'F'
    BACKWARD_LABEL = 'B'
    BIDIRECTION_LABEL = 'BI'
    CLOSURE_BUT_LABEL = 'CLOS'
    NEGATION_FORWARD_LABEL = NEGATION_LABEL + '_' + FORWARD_LABEL
    NEGATION_BACKWARD_LABEL = NEGATION_LABEL + '_' + BACKWARD_LABEL
    NEGATION_BIDIRECTION_LABEL = NEGATION_LABEL + '_' + BIDIRECTION_LABEL
    UNKNOWN_LABEL = '??'
    ICD_KEYWORD_LABEL = 'ICD Codes'
    NORMALIZE_LABEL = 'Normazlized Phrase'


negation_forward_patterns = (
    # rule * out
    [{"LEMMA": "rule"}, {'IS_ALPHA': True, "OP": "*"}, {"LOWER": "out"}],
    # Decline, deny, reject
    [{"LEMMA": {"IN": ["deny", "decline", "reject", "doubt", "exclude", "resolve", "question", "suspect", "counsel"]}}],
    # Free of, clear of, absent of, etc.
    [{"LEMMA": {"IN": ["free", "clear", "absence", "absent", "disappearance", "resolution",
                       "removal", "resolution", "drainage", "question", "suggestion"]}}, {"LOWER": "of"}],
    # Nagative
    [{"LEMMA": {"IN": ["negative", "unremarkable", "test"]}}, {
        'IS_ALPHA': True, "OP": "*"}, {"LOWER": {"IN": ["for", "of"]}}],
    #
    [{"LEMMA": {"IN": ["nothing", "neither", "never", "not", "without", "no", "unable", "versus", "vs", "either", "uncertain"]}}],
    # Uncertainty
    [{"LOWER": {"IN": ["possible", "possibly", "presumably", "probable", "questionable", "suspicious", "r/o", "r\o"]}}],
    # Uncertainty
    [{"LEMMA": {"IN": ["may", "would", "could"]}}],
    # Without evidence of
    [{"LEMMA": {"IN": ["without", "no"]}}, {'IS_ALPHA': True, "OP": "*"},
        {"LOWER": {"IN": ["evidence", "finding", "focus", "moderate"]}}, {"LEMMA": {"IN": ["of", "for", "to"]}}],
    # Not think/feel/see, etc.
    [{"LOWER": "not"}, {"LOWER": {"IN": ["exclude", "see", "think", "know", "feel", "reveal", "appreciate", "demonstrate", "visualize"]}}],
    # Low probablity
    [{"LOWER": 'low'}, {"LOWER": {"IN": ["feasibility", "plausibility", "possibility",
                                         "probability", "likelihood", "likeliness", "chance", "chances"]}}],
    # Fail to
    [{"LEMMA": 'fail'}, {"LOWER": "to"}],
    # rather than
    [{"LOWER": 'rather'}, {"LOWER": "than"}],
    #
    [{"LOWER": 'differential'}, {"LOWER": "diagnosis"}],
)


negation_backward_patterns = (
    # be ruled out
    [{"LEMMA": "be"}, {"LEMMA": "rule"}, {'IS_ALPHA': True, "OP": "*"}, {"TEXT": "out"}],
    # be absent or negative
    [{"LEMMA": "be"}, {'IS_ALPHA': True, "OP": "*"}, {"LEMMA": {"IN": ["absent", "negative"]}}],
    # resolved
    [{"TEXT": {"IN": ["suspected", "resolved"]}}],
    # not seen, not excluded, not indicated
    [{"TEXT": "not"}, {"TEXT": {"IN": ["seen", "excluded", "indicated", "appear", "domonstrated", "visualized"]}}],
    # doubtfull, unremarkable-MP
    [{"TEXT": {"IN": ["doubtful", "unremarkable"]}}],
    # not rule out
    [{"LEMMA": "not"}, {"TEXT": "ruled"}, {'IS_ALPHA': True, "OP": "*"}, {"TEXT": "out"}],
)


negation_bidirection_patterns = (
    # excluded
    [{"LOWER": {"IN": ["doubtful", "excluded", "unlikely", "improbable", "impossible",
                       "implausible", "questionable", "unrealistic", "inconceivable", "uncertain"]}}],
    [{"LOWER": "not"}, {"LOWER": "LIKELY"}],
    # free,
    [{"TEXT": "free"}],
)

closure_patterns = (
    [{"LOWER": {"IN": ["although", "but", "except", "however", "nevertheless", "still", "though", "yet"]}}],
    [{"TEXT": {"IN": ["apart", "aside"]}}, {"TEXT": "from"}],
)
