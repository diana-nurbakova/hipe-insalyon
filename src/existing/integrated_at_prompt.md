# Task A: at

## System Prompt

You are an expert annotator for historical named-entity relation extraction
in the HIPE-2026 shared task.

CONTEXT:
- Documents are historical newspaper articles from 1850–1950.
- Languages: English, French, German (read as-is — do NOT translate).
- OCR may introduce minor noise; ignore obvious OCR errors.
- Entity markers [E1] PERSON [/E1] and [E2] LOCATION [/E2] are added to help
  you locate the entities in the text.

DEFINITIONS:
- "at" relation: The person has a general association with this location
  (born there, lived there, worked there, visited, etc.)
  Values: TRUE, PROBABLE, FALSE
- "isAt" relation: The person is physically present at this location around
  the publication date of the article (within approximately ±2 weeks).
  Values: TRUE, FALSE  (no PROBABLE for isAt)

REASONING GUIDELINES:
1. VERB TENSE AND ASPECT are the primary signal:
   - Present tense / present progressive → TRUE or PROBABLE (at), TRUE (isAt)
   - Simple past / past perfect → suggests historical, not current → likely FALSE
   - "formerly", "used to", "jadis", "ehemals", "autrefois" → FALSE
   - Negation ("no longer", "nicht mehr", "ne … plus") → FALSE
   - Future tense → person not yet there → FALSE for isAt

2. TEMPORAL EXPRESSIONS must be resolved against the publication date:
   - Resolve relative expressions ("last week", "yesterday", "la semaine dernière",
     "vorige Woche") relative to the publication date provided.
   - If a resolved date falls within ±14 days of the publication date → strong
     evidence for isAt=TRUE.
   - If outside that window → not sufficient for isAt=TRUE.

3. BIOGRAPHY AND WIKIDATA context (when provided):
   - If the person died before the publication date → both at=FALSE and isAt=FALSE.
   - If the location matches a known residence or work location in Wikidata
     and the article uses present tense → at=TRUE.
   - Birth place alone does NOT imply at=TRUE unless corroborated by the text.

4. SIMILAR ANNOTATED EXAMPLES (retrieved from training data):
   - Use them as soft evidence, not hard rules.
   - A majority of TRUE examples for the same person/location is a positive signal.
   - Always check whether the current article's tense/context overrides the examples.

5. OCR AND LANGUAGE NOISE:
   - Ignore stray characters, truncated words.
   - Prioritise clear verbal structures and named entities.

OUTPUT FORMAT - respond ONLY with one prediction per sample, nothing else:
Sample 0: FALSE | confidence=0.73
Sample 1: TRUE | confidence=0.91
Sample 2: PROBABLE | confidence=0.58
...
Confidence must be a number between 0.00 and 1.00.
Do NOT add explanations, JSON, or any other text.

## User Message

TASK: "at" — General association
Determine whether the PERSON had the LOCATION as their base, residence,
or regular place of activity at the time the article was written.
  - TRUE     : that location was clearly their base/residence at document time
               (present tense, known biography, Wikidata residence/work)
  - FALSE    : no association — clearly somewhere else, deceased, or unrelated
  - PROBABLE : the text implies a connection but is not definitive
               (Use PROBABLE sparingly — only when genuinely uncertain)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FEW-SHOT EXAMPLES FROM THE TRAIN SPLIT FOR TASK 'at'
These examples are already labeled. Learn the decision pattern from them.

────────────────────────────────────────────────────────────
Sample 0:
  Publication date : 1820-05-05
  Language         : en
  Person  : 'Sir Wiiliam Blackstono'  (QID: Q332449)
  Location: 'Great Britain'  (QID: Q23666)

  [ARTICLE TEXT — entity markers added]
  "[E1] Sir Wiiliam Blackstono [/E1] has collated and commented on it—his fine copy of Magna Charta has been excelled by later specimens of art, and the fac-similes of the seals and signatur e.diave made every reader of taste in [E2] Great Britain [/E2] acquainted, in some de gree, not merely with the state ofknowledge and of art at the period in question, but with the literary attainments, al>©, of King John, King Henry, and fbeir “ Barons bold.”"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: William Blackstone
    Description: English jurist, judge and Tory politician (1723-1780)
    Born: ['+1723-07-10T00:00:00Z', '+1723-01-01T00:00:00Z']
    Died: ['+1780-02-14T00:00:00Z', '+1780-01-01T00:00:00Z']
    Birth place: ['City of London', 'Cheapside']
    Death place: ['Wallingford']
    Residences: ["Lincoln's Inn Fields"]
  Location Wikidata:
    Label: Great Britain
    Description: island in the North Atlantic Ocean off the northwest coast of continental Europe
    Country: ['United Kingdom']
    Aliases: {'en': ['Gt. Brit', 'GB', 'Blighty', 'Albion', 'Britannia', 'GBR', 'mainland Britain', 'Britain'], 'fr': ['G-B', 'Grande Bretagne', 'G.-B.', 'île de Bretagne'], 'de': ['GB-GBN', 'Grossbritannien']}
    Coordinates: [{'lat': 53.833333333333, 'lon': -2.4166666666667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now, late, later
    Verb cluster: "has been excelled" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "Sir Wiiliam Blackstono has collated and commented on it—his fine copy of Magna Charta has been excelled by later specime"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.999

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Sir Wiiliam Blackstono' and 'Great Britain' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Sir Wiiliam Blackstono' near 'Great Britain' around 1820-05-05?
  4. Resolve temporal expressions relative to 1820-05-05. Are they within ±14 days?
Correct label for task 'at': PROBABLE
Key cue summary: temporal signals: now, late, later; verb cue: has been excelled [Pres, Perf, Ind]; person died before the publication date

────────────────────────────────────────────────────────────
Sample 1:
  Publication date : 1988-02-15
  Language         : fr
  Person  : 'voyageur allemand, Christian\nHirschfeld'  (QID: Q321679)
  Location: 'Suisse'  (QID: Q39)

  [ARTICLE TEXT — entity markers added]
  "La [E2] Suisse [/E2] au regard du monde : entre réalité et fiction Dans son Essai sur les Révolutions, Chateaubriand écrit en 1797 que « les Scythes, dans le monde ancien, les Suisses, dans le monde moderne, attirèrent les yeux de leurs contemporains par la célébrité de leur innocence. » Manfred Gsteiger Une telle remarque est pour ainsi dire le résumé d'innombrables discours, littéraires et autres, de l'Europe des Lumières et de la sensibilité préromantique où la Suisse apparaît comme le lieu idyllique d'une nature et d'une humanité non conompues et la patrie de toutes les vertus républicaines. Et pourtant, à la même époque, Goethe note dans ses Lettres écrites de la Suisse que le mythe de la liberté helvétique n'est qu'un « vieux conte pour enfants conservé dans de l'esprit de vin », et un autre voyageur allemand, Christian Hirschfeld, se plaint en 1776 de l'immoralité et de l'ivrognerie des Suisses."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Christian Cay Lorenz Hirschfeld
    Description: German author (1742–1792)
    Born: ['+1742-02-16T00:00:00Z']
    Died: ['+1792-02-20T00:00:00Z']
    Birth place: ['Q641663']
    Death place: ['Q1707']
    Work locations: ['Q1707']
  Location Wikidata:
    Label: Suisse
    Description: pays d'Europe centrale
    Country: ['Suisse']
    Aliases: {'en': ['Swiss Confederation', 'Swiss', 'Confoederatio Helvetica'], 'fr': ['Confédération helvétique', 'Confédération suisse', 'SUI', 'Helvétie', 'la Confédération suisse'], 'de': ['Schweizerische Eidgenossenschaft', 'Eidgenossenschaft', 'SUI', 'Confoederatio Helvetica', 'Confœderatio Helvetica'], 'lb': ['SUI']}
    Coordinates: [{'lat': 46.798562, 'lon': 8.231973}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1797" → 1797
      - "1776" → 1776
    Temporal signal words: ancien
    Verb cluster: "plaint" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Et pourtant, à la même époque, Goethe note dans ses Lettres écrites de la Suisse que le mythe de la liberté helvétique n"
    Verb cluster: "attirèrent" — tense=Pres, aspect=None, mood=Ind
      Sentence: "La Suisse au regard du monde : entre réalité et fiction Dans son Essai sur les Révolutions, Chateaubriand écrit en 1797 "
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 191 days
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.989

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'voyageur allemand, Christian\nHirschfeld' and 'Suisse' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'voyageur allemand, Christian\nHirschfeld' near 'Suisse' around 1988-02-15?
  4. Resolve temporal expressions relative to 1988-02-15. Are they within ±14 days?
Correct label for task 'at': PROBABLE
Key cue summary: temporal signals: ancien; verb cue: plaint [Pres, Ind]; person died before the publication date

────────────────────────────────────────────────────────────
Sample 2:
  Publication date : 1948-04-23
  Language         : de
  Person  : 'Vorsitz\nGladwyn Jebb'  (QID: Q1275)
  Location: 'Lancaster Housc'  (QID: Q1146311)

  [ARTICLE TEXT — entity markers added]
  "Der britische Außenminister Ernest Elevin wird die Konferenz der ständigen Organisation der westeuropäischen Union morgen in [E2] Lancaster Housc [/E2] eröffnen, teilte das Foreign Office gestern mit. Nach der Eröffnungsansprache an die Delegierten der fünf Teilnehmerstaaten wird e« für die erste Sitzung dem Vorsitz Gladwyn Jebb vom Foreign Office überge"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Gladwyn Jebb
    Description: britischer Politiker und Diplomat
    Born: ['+1900-04-25T00:00:00Z']
    Died: ['+1996-10-24T00:00:00Z']
    Birth place: ['Yorkshire']
    Death place: ['Halesworth']
    Work locations: ['Straßburg', 'Brüssel']
  Location Wikidata:
    Label: Lancaster House
    Description: palastartiges Herrenhaus im Londoner Stadtteil St James’s
    Country: ['Vereinigtes Königreich']
    Located in: ['City of Westminster']
    Aliases: {'en': ['York House', 'Stafford House']}
    Coordinates: [{'lat': 51.503888888889, 'lon': -0.13916666666667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: gestern, nach, vor
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Nach der Eröffnungsansprache an die Delegierten der fünf Teilnehmerstaaten wird e« für die erste Sitzung dem Vorsitz Gla"
    Verb cluster: "teilte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Der britische Außenminister Ernest Elevin wird die Konferenz der ständigen Organisation der westeuropäischen Union morge"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 6 (0 = most prominent)
    OCR quality estimate: 0.985

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Vorsitz\nGladwyn Jebb' and 'Lancaster Housc' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Vorsitz\nGladwyn Jebb' near 'Lancaster Housc' around 1948-04-23?
  4. Resolve temporal expressions relative to 1948-04-23. Are they within ±14 days?
Correct label for task 'at': PROBABLE
Key cue summary: temporal signals: gestern, nach, vor; verb cue: wird [Pres, Ind]

────────────────────────────────────────────────────────────
Sample 3:
  Publication date : 1840-04-18
  Language         : en
  Person  : 'Gen.\nJackson'  (QID: Q11817)
  Location: 'the United\nStates'  (QID: Q30)

  [ARTICLE TEXT — entity markers added]
  "Van Buren’s and Gen. Jackson's friends; this heretofore odious name of the friends of popular rights, those candid federal whigs now take up and claim as their own. What will the people think of such miserable trickery; such cool unblushing deceit? Federal Wlilggery ashamed of Its name! "NVe see in an opposition paper, a whig address from Baltimore, to “the young men of the United States,” headed “your DEMOCRATIC Harrison brethren of Baltimore send you this address, greet ing.”"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Andrew Jackson
    Description: president of the United States from 1829 to 1837
    Born: ['+1767-03-15T00:00:00Z']
    Died: ['+1845-06-08T00:00:00Z']
    Birth place: ['Waxhaws']
    Death place: ['The Hermitage']
    Work locations: ['Washington, D.C.']
  Location Wikidata:
    Label: United States
    Description: country located primarily in North America
    Country: ['United States']
    Aliases: {'en': ['the States', 'the United States of America', 'US of America', 'the US', 'the U.S.', 'the US of A', 'U.S. of America', 'the US of America', 'the USA', 'the U.S.A.', 'the U.S. of A', 'US of A', 'the U.S. of America', 'the United States', 'Merica', 'Murica', 'United States of America', 'U.S.', 'U.S.A.', 'U. S.', 'U. S. A.', 'America'], 'fr': ['É.-U.', 'É-U', 'É-U.', 'E.-U.', 'É.U.', 'les États', 'Oncle Sam', 'Amérique', 'Etats-Unis', 'States', 'les États-Unis d’Amérique', 'États-unis', 'ÉU', 'É.-U. A.', "Pays de l'Oncle Sam", 'Etats-unis', 'États-Unis d’Amérique', 'pays de l’Oncle Sam'], 'de': ['Vereinigte Staaten von Amerika', 'US-Amerika', 'U.S.-Amerika', 'Staaten von Amerika', 'VSA', 'V.S.A.', 'V. S. A.', 'Staaten', 'die Staaten', 'VS', 'V.S.', 'V. S.', 'Amerika', 'U.S.A.', 'U. S. A.', 'United States of America', 'United States', 'U.S.', 'U. S.', 'America'], 'lb': ['Vereenegt Staaten']}
    Coordinates: [{'lat': 39.828175, 'lon': -98.5795}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now
    Verb cluster: "take" — tense=Pres, aspect=None, mood=None
      Sentence: "Van Buren’s and Gen. Jackson's friends; this heretofore odious name of the friends of popular rights, those candid feder"
    Verb cluster: "headed" — tense=Past, aspect=None, mood=None
      Sentence: ""NVe see in an opposition paper, a whig address from Baltimore, to “the young men of the United States,” headed “your DE"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Gen.\nJackson' and 'the United\nStates' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Gen.\nJackson' near 'the United\nStates' around 1840-04-18?
  4. Resolve temporal expressions relative to 1840-04-18. Are they within ±14 days?
Correct label for task 'at': PROBABLE
Key cue summary: temporal signals: now; verb cue: take [Pres]

────────────────────────────────────────────────────────────
Sample 4:
  Publication date : 1868-02-17
  Language         : de
  Person  : 'Disraeli'  (QID: Q82006)
  Location: 'England'  (QID: Q21)

  [ARTICLE TEXT — entity markers added]
  "Einmal wird von Nordamerika Entschädigung verlangt für die nordischen Kauffahrer, welche von den in [E2] England [/E2] ge kauften und bewaffneten Korsaren wie Alabama, Georgia, Florida, Sumter u. s. w. während dem Bürgerkrieg ge kapert und verbrannt worden sind. Dann wird aber England auch der Verletzung des Völkerrechts beschul digt, indem es in seinen Häfen die Ausrüstung von sonderbündischen Kaperschiffen zugelassen hat. Diese Erscheinung ist um so tröst licher, als die industrielle Krise von 1866 in England zugleich mit einer schlechten Ernte und einer großen Theuerung der Nahrungsmittel verbunden war. Der Widerspruch gegen das von [E1] Disraeli [/E1] vorgeschla gene Wahlbestechungsgericht — drei Richter mit je einem Gehalt von 200 Pfund — erklärt sich aus der Be schränkung, die dadurch den Rechten des Unterhauses erwachsen wäre."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Benjamin Disraeli
    Description: britischer Premierminister und Romanschriftsteller
    Born: ['+1804-12-21T00:00:00Z', '+1804-01-01T00:00:00Z']
    Died: ['+1881-04-19T00:00:00Z', '+1881-01-01T00:00:00Z']
    Birth place: ['London']
    Death place: ['Mayfair', 'Curzon Street', 'London']
    Work locations: ['London']
  Location Wikidata:
    Label: England
    Description: Land im Nordwesten Europas, Teil des Vereinigten Königreichs
    Country: ['Vereinigtes Königreich', 'Vereinigtes Königreich Großbritannien und Irland', 'Königreich Großbritannien']
    Located in: ['Q145', 'Vereinigtes Königreich Großbritannien und Irland', 'Königreich Großbritannien']
    Aliases: {'en': ['ENG', 'England, United Kingdom', 'England, UK'], 'fr': ['Ang.', 'Mère des parlements']}
    Coordinates: [{'lat': 53, 'lon': -1}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1866" → 1866
    Temporal signal words: vor
    Verb cluster: "erklärt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Der Widerspruch gegen das von Disraeli vorgeschla gene Wahlbestechungsgericht — drei Richter mit je einem Gehalt von 200"
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Einmal wird von Nordamerika Entschädigung verlangt für die nordischen Kauffahrer, welche von den in England ge kauften u"
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 2 days
    Entity sentence position in article: 10 (0 = most prominent)
    OCR quality estimate: 0.975

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Disraeli' and 'England' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Disraeli' near 'England' around 1868-02-17?
  4. Resolve temporal expressions relative to 1868-02-17. Are they within ±14 days?
Correct label for task 'at': PROBABLE
Key cue summary: temporal signals: vor; verb cue: erklärt [Pres, Ind]

────────────────────────────────────────────────────────────
Sample 5:
  Publication date : 1938-05-20
  Language         : de
  Person  : 'Kardinal Rampolla'  (QID: Q508860)
  Location: 'Rom'  (QID: Q220)

  [ARTICLE TEXT — entity markers added]
  "Der Präsident der Republik, der allein auf dem Laufenden war, entsandte ohne Wissen der französischen Botschaft in [E2] Rom [/E2] Victor Homberg in geheimer Mission nach Rom, um durch Vermittlung von [E1] Kardinal Rampolla [/E1] Konzessionen namentlich in der Frage der Vischofsernennungen zu erlangen;"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Mariano Rampolla del Tindaro
    Description: italienischer Geistlicher, Kardinalstaatssekretär während des Pontifikats Leo XIII.
    Born: ['+1843-08-17T00:00:00Z']
    Died: ['+1913-12-16T00:00:00Z', '+1913-12-17T00:00:00Z']
    Birth place: ['Q502657']
    Death place: ['Rom']
  Location Wikidata:
    Label: Rom
    Description: Haupt- und bevölkerungsreichste Stadt Italiens
    Country: ['Italien', 'Kirchenstaat', 'Kingdom of Italy', 'Q583038', 'Q12544', 'Königreich Italien', 'Römische Königszeit', 'Römische Republik', 'Römisches Kaiserreich', 'Weströmisches Reich', 'Vatikanstadt']
    Located in: ['Provinz Rom', 'Kirchenstaat', 'Rome', 'Q1747689', 'Römische Republik', 'Q2277', 'Weströmisches Reich', 'Metropolitanstadt Rom', 'circle of Rome']
    Aliases: {'en': ['The Eternal City', 'Roma', 'Rome, Italy', 'City of Seven Hills'], 'fr': ['La ville éternelle', 'La ville aux sept collines', 'Roma', "l'Urbs"], 'de': ['Die Ewige Stadt', 'Roma'], 'lb': ['Roma', "D'Éiweg Stad"]}
    Coordinates: [{'lat': 41.893055555556, 'lon': 12.482777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach
    Verb cluster: "entsandte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Der Präsident der Republik, der allein auf dem Laufenden war, entsandte ohne Wissen der französischen Botschaft in Rom V"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 4 (0 = most prominent)
    OCR quality estimate: 1.000

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Kardinal Rampolla' and 'Rom' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Kardinal Rampolla' near 'Rom' around 1938-05-20?
  4. Resolve temporal expressions relative to 1938-05-20. Are they within ±14 days?
Correct label for task 'at': PROBABLE
Key cue summary: temporal signals: nach; verb cue: entsandte [Past, Ind]; person died before the publication date

────────────────────────────────────────────────────────────
Sample 6:
  Publication date : 1828-05-10
  Language         : de
  Person  : 'Hr. Oberst Salis-Soglio'  (QID: Q117870)
  Location: 'Schwyz'  (QID: Q12433)

  [ARTICLE TEXT — entity markers added]
  "Die in [E2] Schwyz [/E2] versammelte Kantonsgemeinde am 4. May war zahlreich und gieng in Ruhe und Stille vorüber, ungeachtet ein paar Gegenstände die Gemüther in Spannung setzten. Nachdem Herr Landammann J. Martin Hediger die Landsgemeinde mit einer Anrede eröffnet hatte, erhob sich ein Landmann mit dem Antrag: daß man das in Lachen errichtete Werbdepot für drey Kompagnien, welches seiner Zeit dem [E1] Hr. Oberst Salis-Soglio [/E1] bewilligt ward, aufheben möchte."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Johann Ulrich von Salis-Soglio
    Description: Schweizer General und Kommandierender der Sonderbundstruppen
    Born: ['+1790-03-18T00:00:00Z']
    Died: ['+1874-04-27T00:00:00Z']
    Birth place: ['Chur']
    Death place: ['Chur']
  Location Wikidata:
    Label: Kanton Schwyz
    Description: Kanton der Schweiz
    Country: ['Schweiz']
    Located in: ['Schweiz']
    Aliases: {'en': ['Schwytz', 'Kanton Schwyz', 'Canton of Schwytz', 'SZ'], 'fr': ['Schwytz', 'Schwyz', 'canton de Schwyz', 'SZ'], 'de': ['SZ', 'Schwyz'], 'lb': ['SZ', 'Kanton Schwyz']}
    Coordinates: [{'lat': 47.066666666667, 'lon': 8.75}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Verb cluster: "erhob" — tense=Past, aspect=None, mood=Ind
      Sentence: "Nachdem Herr Landammann J. Martin Hediger die Landsgemeinde mit einer Anrede eröffnet hatte, erhob sich ein Landmann mit"
    Verb cluster: "war" — tense=Past, aspect=None, mood=Ind
      Sentence: "Die in Schwyz versammelte Kantonsgemeinde am 4. May war zahlreich und gieng in Ruhe und Stille vorüber, ungeachtet ein p"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.984

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Hr. Oberst Salis-Soglio' and 'Schwyz' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Hr. Oberst Salis-Soglio' near 'Schwyz' around 1828-05-10?
  4. Resolve temporal expressions relative to 1828-05-10. Are they within ±14 days?
Correct label for task 'at': PROBABLE
Key cue summary: temporal signals: nach, vor; verb cue: erhob [Past, Ind]

────────────────────────────────────────────────────────────
Sample 7:
  Publication date : 1898-11-07
  Language         : de
  Person  : 'Königin Elisabeth'  (QID: Q150782)
  Location: 'Ungarns'  (QID: Q28)

  [ARTICLE TEXT — entity markers added]
  "Gar eigenartige Gedanken, schreibt unser Wiener VKorrespondent, sind es, die der soeben bekannt gewordene, in ganz Ungarn leiden schaftlich bejubelte Entschluß des Kaisers in den deutschen, d. h. in den einzigen noch gut altösterreichischen Kreisen hervorruft. Dem Fernstehenden mag vielleicht Verständnis und Gefühl für diese Auslegung der Sache mangeln. Nunmehr ergreift der „König" Franz Josef selbst den Anlaß der monumentalen Verherrlichung der gemordeten Kaiserin, um Pest von dem verhaßten Denkmal des Generals Hentzi zu befreien. Der schwärmerische Dichter-Politiker Maurus Jokai feiert das Ereignis in seinem Blatte, indem er sagt, die [E1] Königin Elisabeth [/E1] sei noch nach ihrem Tode der Schutzengel [E2] Ungarns [/E2]", der der Nation zur Erfüllung eines lange ge hegten Herzenswunsches verhelfe."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Elisabeth von Österreich-Ungarn
    Description: Kaiserin von Österreich und Königin von Ungarn (1837–1898)
    Born: ['+1837-12-24T00:00:00Z']
    Died: ['+1898-09-10T00:00:00Z']
    Birth place: ['München']
    Death place: ['Genf']
  Location Wikidata:
    Label: Ungarn
    Description: Staat in Mitteleuropa
    Country: ['Ungarn']
    Aliases: {'fr': ['la Hongrie']}
    Coordinates: [{'lat': 47, 'lon': 19}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Verb cluster: "feiert" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Der schwärmerische Dichter-Politiker Maurus Jokai feiert das Ereignis in seinem Blatte, indem er sagt, die Königin Elisa"
    Verb cluster: "schreibt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Gar eigenartige Gedanken, schreibt unser Wiener VKorrespondent, sind es, die der soeben bekannt gewordene, in ganz Ungar"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.992

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Königin Elisabeth' and 'Ungarns' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Königin Elisabeth' near 'Ungarns' around 1898-11-07?
  4. Resolve temporal expressions relative to 1898-11-07. Are they within ±14 days?
Correct label for task 'at': PROBABLE
Key cue summary: temporal signals: nach, vor; verb cue: feiert [Pres, Ind]

────────────────────────────────────────────────────────────
Sample 8:
  Publication date : 1948-12-30
  Language         : de
  Person  : 'Nulns Paschns'  (QID: Q403629)
  Location: 'Aeppptens'  (QID: Q748617)

  [ARTICLE TEXT — entity markers added]
  "Dasselbe Amt bekleidete er noch einmal im dritten Kabinett Nahas vom Mai 1936. Sein mun teres Mesen machte il bei den jungen An hüngern der Partei besonders beliebt und brachte ilm auberdem seinem Parteikreund und Alters genossen Amed Maher Pascha näher, dem Prisi denten der Abgeordnetenkammer, von dem er sich in der Folge nicht mehr trennte. Im Februar 1942 wurde das Enbinett Hussein Sirry vom letzten Wafdlnbinett unter Nalias Paschn abgelöst. Als im Oktober 1944 Lord Killearn und die britische Regierung sehlieslich einschen mußten, das das weitere Verbleiben [E1] Nulns Paschns [/E1] in der Regierung ihre eigene Stel lung gekührdete, entzogen sie ihm ihre Unter stiitzung und drüngten zur Ernennung Ahmed Mahen Paschas als Nnchfolger, der als Gegner Nahus' und als probritisch gesinnter Politiker zn gleich im Pulnis und bei der britischen Botsehnft gut ungesehrieben war."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Mustafa an-Nahhas Pascha
    Description: ägyptischer Politiker
    Born: ['+1879-06-15T00:00:00Z']
    Died: ['+1965-08-23T00:00:00Z', '+1965-01-01T00:00:00Z']
    Birth place: ['Samannud']
    Death place: ['Alexandria']
  Location Wikidata:
    Label: Wafd-Partei
    Description: ägyptische nationalistische Partei
    Country: ['Ägypten', 'Sultanat Ägypten']
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1936" → 1936
      - "1942" → 1942
      - "1944" → 1944
    Temporal signal words: nicht mehr
    Verb cluster: "entzogen" — tense=Past, aspect=None, mood=Ind
      Sentence: "Als im Oktober 1944 Lord Killearn und die britische Regierung sehlieslich einschen mußten, das das weitere Verbleiben Nu"
    Verb cluster: "bekleidete" — tense=Past, aspect=None, mood=Ind
      Sentence: "Dasselbe Amt bekleidete er noch einmal im dritten Kabinett Nahas vom Mai 1936."
    Verb cluster: "wurde" — tense=Past, aspect=None, mood=Ind
      Sentence: "Im Februar 1942 wurde das Enbinett Hussein Sirry vom letzten Wafdlnbinett unter Nalias Paschn abgelöst."
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 4 days
    Entity sentence position in article: 24 (0 = most prominent)
    OCR quality estimate: 0.983

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Nulns Paschns' and 'Aeppptens' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Nulns Paschns' near 'Aeppptens' around 1948-12-30?
  4. Resolve temporal expressions relative to 1948-12-30. Are they within ±14 days?
Correct label for task 'at': PROBABLE
Key cue summary: temporal signals: nicht mehr; verb cue: entzogen [Past, Ind]

────────────────────────────────────────────────────────────
Sample 9:
  Publication date : 1950-11-25
  Language         : en
  Person  : 'Christ Jesus'  (QID: Q302)
  Location: 'Caper\nnaum'  (QID: Q59174)

  [ARTICLE TEXT — entity markers added]
  "AJi can help by means of scientific prayer, the kind of prayer given to the world nearly two thousand year* ago by [E1] Christ Jesus [/E1]. He had no fortune to distribute to the needy, no endowed insti tutions to call upon for assist ance, no worldly prestige. Yet he healed the sick, fed the hungry, met the demands of the tax col lectors, even raised the dead — all through understanding, scien tific prayer. . . . When the centurion at Caper naum asked the Master to heal his servant, he pleaded iMatthew 8:H>, “Speak the word only, and my servant shall be healed.”"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Jesus Christ
    Description: central figure of Christianity (6 or 4 BC – AD 30 or 33)
    Born: ['-0007-00-00T00:00:00Z', '-0002-00-00T00:00:00Z', '-0005-00-00T00:00:00Z']
    Died: ['+0030-04-07T00:00:00Z', '+0033-04-03T00:00:00Z']
    Birth place: ['Bethlehem', 'Nazareth']
    Death place: ['Calvary']
    Residences: ['Nazareth', 'Capernaum', 'Galilee']
    Work locations: ['Galilee', 'Jerusalem']
  Location Wikidata:
    Label: Capernaum
    Description: village at Lake Tiberias in the north of historical Judea, associated with Jesus
    Country: ['Israel']
    Located in: ['Northern District', 'Galilee']
    Aliases: {'en': ['Kfar Nahum', 'Kfar Nachum'], 'fr': ['Capharnaum', 'Kefar Nahoum', 'Kfar Nakhoum'], 'de': ['Kapernaum', 'Kafar Nahum', 'Kapharnaum', 'Tel Hum']}
    Coordinates: [{'lat': 32.881111111111, 'lon': 35.575}]
  Known person–location links: {"residence": "P551"}

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: early
    Verb cluster: "can help" — tense=None, aspect=None, mood=None
      Sentence: "AJi can help by means of scientific prayer, the kind of prayer given to the world nearly two thousand year* ago by Chris"
    Verb cluster: "pleaded" — tense=Past, aspect=None, mood=None
      Sentence: "When the centurion at Caper naum asked the Master to heal his servant, he pleaded iMatthew 8:H>, “Speak the word only, a"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Christ Jesus' and 'Caper\nnaum' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Christ Jesus' near 'Caper\nnaum' around 1950-11-25?
  4. Resolve temporal expressions relative to 1950-11-25. Are they within ±14 days?
Correct label for task 'at': TRUE
Key cue summary: temporal signals: early; verb cue: can help []; person died before the publication date; Wikidata links: residence

────────────────────────────────────────────────────────────
Sample 10:
  Publication date : 1838-05-11
  Language         : fr
  Person  : 'comte Bomfin'  (QID: Q560962)
  Location: 'PORTUGAL'  (QID: Q45)

  [ARTICLE TEXT — entity markers added]
  "[E2] PORTUGAL [/E2]. LisBOKNE 26 aoril. — Un changement partiel vient de s'opérer dans le cabinet. M. d'Oliveira s'est retiré du ministère des finances, en acceptant le titre de baron de Tojal, et il est remplacé par M. de Carvalho, qui avait anciennement été chargé de ce déparlement, et était président de la chambre des députés, quand don Miguel l'avait dissoute en 1828. M. Carvalho a accepté, malgré lui, dit-on, et après de vives sollicitations. Le [E1] comte Bomfin [/E1] est revenu au ministère de la guerre."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: José Travassos Valdez
    Description: Portuguese noble (1787-1862)
    Born: ['+1787-02-23T00:00:00Z']
    Died: ['+1862-07-10T00:00:00Z']
    Birth place: ['Q622819']
    Death place: ['Q597']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1828" → 1828
    Temporal signal words: ancien, ancienne, après
    Verb cluster: "accepté" — tense=Past, aspect=None, mood=None
      Sentence: "M. Carvalho a accepté, malgré lui, dit-on, et après de vives sollicitations."
    Verb cluster: "revenu" — tense=Past, aspect=None, mood=None
      Sentence: "Le comte Bomfin est revenu au ministère de la guerre."
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 10 days
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.985

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'comte Bomfin' and 'PORTUGAL' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'comte Bomfin' near 'PORTUGAL' around 1838-05-11?
  4. Resolve temporal expressions relative to 1838-05-11. Are they within ±14 days?
Correct label for task 'at': TRUE
Key cue summary: temporal signals: ancien, ancienne, après; verb cue: accepté [Past]

────────────────────────────────────────────────────────────
Sample 11:
  Publication date : 1858-02-24
  Language         : de
  Person  : 'Napoleons l'  (QID: Q517)
  Location: 'Frankreich'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "Der Anblick, welchen [E2] Frankreich [/E2] seit einiger Zeit gewährt, ist im höchsten Grade betrübend und Be» sorgniß erregend, Trotz der gewaltigen Hand, welche seit dem 2. Dez. 1852 dort die Zügel der Regie» nlng gefaßt , ist die Revolution doch eine per» man ente geblieben; Auf die Bourboncn folgte die Pöbelherrschaft, auf diese [E1] Napoleons l [/E1]. Gewaltregiment, dieser wurde dann wieder durch die Bourbonen verdrängt, deren Regierungsfähig» keit in der Thai erloschen schien, als Ludwig Phil» livpe sie mit einem Hauche vom Throne blasen konnte, um achtzehn Jahre später noch schmählicher gestürzt zu werden! Nach ihm, der nichts gethan, mn Frankreich moralisch zu heben, — worin doch die einzige Stütze seiner Monarchie bestand, —nach ihm sehen wir wieder die Pöbelherrschaft im wilde» sten Auswüchse, wir sehen die Nepublick gegen ihre eigenen Ultras die blutigsten Straßenkampfe führen, Ins zuletzt Napoleon !11. abermals über Nacht dem ein Ende und sich zum Herrscher Frankreichs machte."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Napoleon Bonaparte
    Description: französischer General, Staatsmann und Kaiser
    Born: ['+1769-08-15T00:00:00Z', '+1769-01-01T00:00:00Z']
    Died: ['+1821-05-05T00:00:00Z', '+1821-01-01T00:00:00Z']
    Birth place: ['Ajaccio']
    Death place: ['Longwood House']
    Residences: ['St. Helena', 'Ajaccio', 'Paris', 'Elba']
  Location Wikidata:
    Label: Frankreich
    Description: Staat in Westeuropa mit Überseegebieten
    Country: ['Frankreich']
    Aliases: {'en': ['French Republic'], 'fr': ['République française', 'RF', 'fr', 'la République française', 'Fr.', 'La France', "L'Hexagone"], 'de': ['Französische Republik', 'fr', 'RF']}
    Coordinates: [{'lat': 47, 'lon': 2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1852" → 1852
    Temporal signal words: nach, spät
    Verb cluster: "folgte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Auf die Bourboncn folgte die Pöbelherrschaft, auf diese Napoleons l. Gewaltregiment, dieser wurde dann wieder durch die "
    Verb cluster: "ist" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Der Anblick, welchen Frankreich seit einiger Zeit gewährt, ist im höchsten Grade betrübend und Be» sorgniß erregend, Tro"
    Verb cluster: "sehen" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Nach ihm, der nichts gethan, mn Frankreich moralisch zu heben, — worin doch die einzige Stütze seiner Monarchie bestand,"
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 6 days
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.990

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Napoleons l' and 'Frankreich' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Napoleons l' near 'Frankreich' around 1858-02-24?
  4. Resolve temporal expressions relative to 1858-02-24. Are they within ±14 days?
Correct label for task 'at': TRUE
Key cue summary: temporal signals: nach, spät; verb cue: folgte [Past, Ind]; person died before the publication date

────────────────────────────────────────────────────────────
Sample 12:
  Publication date : 1810-04-14
  Language         : en
  Person  : 'George Cinton,\nVice President of the United Slates, and\nPresident of the Senate'  (QID: Q201646)
  Location: 'Virginia'  (QID: Q1370)

  [ARTICLE TEXT — entity markers added]
  "AN ACT To extend the time for locating [E2] Virginia [/E2] military land warrants, and for returning the surveys there on to the Secretary of the Department ot War. B E it enacted by the Senate and House §f Representatives o f the United States of America, in Congress assembled, That the officers and soldiers of the Virginia line on continental establishment, their heirs or as signs entitled to bounty lands within the tract reserved by Virginia, between the lit tle Miami and Sciota rivers, for satisfying the legal bounties to her officers and soldi ers upon continental establishment, shall be allowed a further term of five years, from and after the passage of this act, to obtain warrants and complete their locations, and Speaker of the House of Representatives. George Cinton, Vice President of the United Slates, and President of the Senate."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: George Clinton
    Description: vice president of the United States from 1805 to 1812 (1739–1812)
    Born: ['+1739-07-26T00:00:00Z']
    Died: ['+1812-04-20T00:00:00Z']
    Birth place: ['Little Britain']
    Death place: ['Washington, D.C.']
    Work locations: ['United States']
  Location Wikidata:
    Label: Virginia
    Description: state of the United States of America
    Country: ['United States']
    Located in: ['United States']
    Aliases: {'en': ['Commonwealth of Virginia', 'State of Virginia', 'VA', 'Virginia, United States', 'Old Dominion', 'Va.', 'US-VA'], 'de': ['Virginien']}
    Coordinates: [{'lat': 37.5, 'lon': -79}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after, late
    Verb cluster: "assembled" — tense=Past, aspect=None, mood=None
      Sentence: "B E it enacted by the Senate and House §f Representatives o f the United States of America, in Congress assembled, That "
    Verb cluster: "To extend" — tense=None, aspect=None, mood=None
      Sentence: "AN ACT To extend the time for locating Virginia military land warrants, and for returning the surveys there on to the Se"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 4 (0 = most prominent)
    OCR quality estimate: 0.989

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'George Cinton,\nVice President of the United Slates, and\nPresident of the Senate' and 'Virginia' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'George Cinton,\nVice President of the United Slates, and\nPresident of the Senate' near 'Virginia' around 1810-04-14?
  4. Resolve temporal expressions relative to 1810-04-14. Are they within ±14 days?
Correct label for task 'at': FALSE
Key cue summary: temporal signals: after, late; verb cue: assembled [Past]

────────────────────────────────────────────────────────────
Sample 13:
  Publication date : 1928-05-06
  Language         : fr
  Person  : 'Mgr. Stéphane'  (QID: Q2713806)
  Location: 'Philippopoli'  (QID: Q459)

  [ARTICLE TEXT — entity markers added]
  "Pour les enfants sinistrés de Bulgarie et de Grèce [E1] Mgr. Stéphane [/E1], archevêque de Sofia, rient d'adresser à l'Union internationale de secours aux enfants une dépêche, où, après avoir rendu hommage à cette institution, il s'exprime comme suit : La solidarité humaine ae manifeste le plue sensiblement dane les heures critiques. Le peuple bulgare est sincèrement reconnaissant envers tous ceux qui, dans son épreuve actuelle, lui ont témoigné sympathie et aide. Dieu bénisse chaque effort qui soulagera la souffrance, surtout celle des malheureux petits. D'autre part, l'U. I. S. E. reçoit de sa déléguée la nouvelle qu'elle a pu assurer une distribution quotidienne de pain à 3400 enfants dans les environs de [E2] Philippopoli [/E2] et, dans la ville même, de pain et de thé à 2500 enfants."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Stéphane Ier
    Description: Bulgarian priest (1878-1957)
    Born: ['+1878-09-07T00:00:00Z']
    Died: ['+1957-05-14T00:00:00Z', '+1957-01-01T00:00:00Z']
    Birth place: ['Chiroka laka']
    Death place: ['Banya']
    Residences: ['Sofia']
  Location Wikidata:
    Label: Plovdiv
    Description: deuxième plus grande ville de Bulgarie
    Country: ['Bulgarie', 'république populaire de Bulgarie', 'royaume de Bulgarie', 'principauté de Bulgarie', 'Roumélie orientale', 'Empire ottoman']
    Located in: ['Plovdiv']
    Aliases: {'en': ['Philippopolis', 'Filibe'], 'fr': ['Plodviv'], 'de': ['Philippoupolis']}
    Coordinates: [{'lat': 42.142086, 'lon': 24.741454}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "3400" → 3400
      - "2500" → 2500
    Temporal signal words: après
    Verb cluster: "rient" — tense=Imp, aspect=None, mood=Ind
      Sentence: "Stéphane, archevêque de Sofia, rient d'adresser à l'Union internationale de secours aux enfants une dépêche, où, après a"
    Verb cluster: "reçoit" — tense=Pres, aspect=None, mood=Ind
      Sentence: "D'autre part, l'U. I. S. E. reçoit de sa déléguée la nouvelle qu'elle a pu assurer une distribution quotidienne de pain "
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 572 days
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.984

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mgr. Stéphane' and 'Philippopoli' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mgr. Stéphane' near 'Philippopoli' around 1928-05-06?
  4. Resolve temporal expressions relative to 1928-05-06. Are they within ±14 days?
Correct label for task 'at': FALSE
Key cue summary: temporal signals: après; verb cue: rient [Imp, Ind]

────────────────────────────────────────────────────────────
Sample 14:
  Publication date : 1928-02-17
  Language         : de
  Person  : 'Luther'  (QID: Q9554)
  Location: 'Yverdon'  (QID: Q63946)

  [ARTICLE TEXT — entity markers added]
  "Sind die beiden wie Sokrates und Plato, wie [E1] Luther [/E1] und Me lauchthon oder wie Gebender und — Richter? Ueber Münchenbuchsee geht's nach [E2] Yverdon [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Martin Luther
    Description: deutscher Theologe, Autor und Urheber der Reformation
    Born: ['+1483-11-10T00:00:00Z', '+1483-00-00T00:00:00Z']
    Died: ['+1546-02-18T00:00:00Z']
    Birth place: ['Q484870']
    Death place: ['Q484870']
    Residences: ['Eisleben', 'Mansfeld', 'Magdeburg', 'Q7070', 'Erfurt', 'Lutherstadt Wittenberg', 'Wartburg']
    Work locations: ['Augustinereremitenkloster Erfurt', 'Q151545']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach
    Verb cluster: "Sind" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Sind die beiden wie Sokrates und Plato, wie Luther und Me lauchthon oder wie Gebender und — Richter?"
    Verb cluster: "geht's" — tense=Past, aspect=None, mood=Ind
      Sentence: "Ueber Münchenbuchsee geht's nach Yverdon."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 34 (0 = most prominent)
    OCR quality estimate: 0.996

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Luther' and 'Yverdon' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Luther' near 'Yverdon' around 1928-02-17?
  4. Resolve temporal expressions relative to 1928-02-17. Are they within ±14 days?
Correct label for task 'at': FALSE
Key cue summary: temporal signals: nach; verb cue: Sind [Pres, Ind]; person died before the publication date

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
END OF FEW-SHOT EXAMPLES

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOW CLASSIFY THE FOLLOWING TEST SAMPLES.
Use the same decision style as in the few-shot examples.
Think through the cues silently, but do not output the reasoning.
Respond with exactly one line per sample in the format:
  Sample N: LABEL | confidence=0.00-1.00
Valid labels: TRUE / FALSE / PROBABLE
Confidence must be your calibrated confidence for that label.
Do NOT output explanations, JSON, markdown, or extra commentary.

────────────────────────────────────────────────────────────
Sample 0:
  Publication date : 1874-08-25
  Language         : de
  Person  : 'Roſenſtein'  (QID: N/A)
  Location: 'Berlin'  (QID: Q64)

  [ARTICLE TEXT — entity markers added]
  "[E1] Roſenſtein [/E1] und Dr . Fuchs . Jn der kettang des Unternehmens wird demnach keinerlei LNenderung — Für Herſtellung eines zweiten Geleiſes der [E2] Berlin [/E2]⸗ Charlottenburger Pferdeeiſenbahn iſt der Geſellſchaft die deſinitive Concefſton zugeſtelit werden , und die Lustübrung kann erfolgen , Gerſtellnng des zweiten Geleiſes werden walrſcheinlich durch Aus⸗ tabe nener Aktien beſchafft werden ;"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Berlin
    Description: Hauptstadt und bevölkerungsreichste Stadt der Bundesrepublik Deutschland
    Country: ['Mark Brandenburg', 'Brandenburg-Preußen', 'Königreich Preußen', 'Norddeutscher Bund', 'Deutsches Kaiserreich', 'Weimarer Republik', 'NS-Staat', 'Sowjetische Besatzungszone', 'Deutsche Demokratische Republik', 'Deutschland', 'Bundesrepublik Deutschland bis 1990']
    Located in: ['Mark Brandenburg', 'Brandenburg-Preußen', 'Königreich Preußen', 'Provinz Brandenburg', 'Königreich Preußen', 'Freistaat Preußen', 'NS-Staat', 'Deutschland']
    Aliases: {'en': ['Berlin, Germany', 'DE-BE'], 'de': ['Stadt Berlin', 'Berlin, Deutschland', 'Bundeshauptstadt Berlin', 'Land Berlin', 'DE-BE', 'Berlin (Deutschland)', 'BE', 'Bln', 'Bln.']}
    Coordinates: [{'lat': 52.516666666667, 'lon': 13.383333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach
    Verb cluster: "werden" — tense=None, aspect=None, mood=None
      Sentence: "Für Herſtellung eines zweiten Geleiſes der Berlin⸗ Charlottenburger Pferdeeiſenbahn iſt der Geſellſchaft die deſinitive "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 13 (0 = most prominent)
    OCR quality estimate: 0.973

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Roſenſtein' and 'Berlin' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Roſenſtein' near 'Berlin' around 1874-08-25?
  4. Resolve temporal expressions relative to 1874-08-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 1:
  Publication date : 1881-09-24
  Language         : fr
  Person  : 'M. Berthoud'  (QID: N/A)
  Location: "gorges de l'Areuse"  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Les [E2] gorges de l'Areuse [/E2], un bien joli site à recommander même aux habitants de votre incomparable canton de Vaud ; le château de Gorgier, une merveille d'antique architecture, appartenant au plus aimable des châtelains, [E1] M. Berthoud [/E1], de Londres ;"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Verb cluster: "appartenant" — tense=Pres, aspect=None, mood=None
      Sentence: "le château de Gorgier, une merveille d'antique architecture, appartenant au plus aimable des châtelains, M. Berthoud, de"
    Verb cluster: "recommander" — tense=None, aspect=None, mood=None
      Sentence: "Les gorges de l'Areuse, un bien joli site à recommander même aux habitants de votre incomparable canton de Vaud ;"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 60 (0 = most prominent)
    OCR quality estimate: 0.997

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Berthoud' and "gorges de l'Areuse" in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Berthoud' near "gorges de l'Areuse" around 1881-09-24?
  4. Resolve temporal expressions relative to 1881-09-24. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 2:
  Publication date : 1838-05-11
  Language         : fr
  Person  : 'ba da Bandeira'  (QID: Q669820)
  Location: 'PORTUGAL'  (QID: Q45)

  [ARTICLE TEXT — entity markers added]
  "[E2] PORTUGAL [/E2]. LisBOKNE 26 aoril. Le comte Bomfin est revenu au ministère de la guerre. Le cabinet portugais se trouve, en conséquence, actuellement composé de [E1] ba da Bandeira [/E1], pour la marine et les affaires étrangères."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Portugal
    Description: pays du sud-ouest de l'Europe
    Country: ['Portugal']
    Aliases: {'en': ['Portuguese Republic', 'PRT', 'POR'], 'fr': ['République portugaise'], 'de': ['Portugiesische Republik', 'PRT']}
    Coordinates: [{'lat': 38.7, 'lon': -9.183333333333334}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: actuellement
    Verb cluster: "trouve" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Le cabinet portugais se trouve, en conséquence, actuellement composé de ba da Bandeira, pour la marine et les affaires é"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.985

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'ba da Bandeira' and 'PORTUGAL' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'ba da Bandeira' near 'PORTUGAL' around 1838-05-11?
  4. Resolve temporal expressions relative to 1838-05-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 3:
  Publication date : 1981-11-17
  Language         : fr
  Person  : 'G .-W. Pabst'  (QID: N/A)
  Location: 'Bourges'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Le Franciscain de [E2] Bourges [/E2] », de Cl. Autant- Lara ; 20.30, « L'amour de Jeanne Ney », de G .-W."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 31 (0 = most prominent)
    OCR quality estimate: 0.778

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'G .-W. Pabst' and 'Bourges' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'G .-W. Pabst' near 'Bourges' around 1981-11-17?
  4. Resolve temporal expressions relative to 1981-11-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 4:
  Publication date : 1948-07-19
  Language         : de
  Person  : "Senatzanzler Sir Stafford\nC'ripye"  (QID: Q332405)
  Location: 'Frankreich'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "Man rechnet namentlich damit, dals für Grolbritannien Senatzanzler Sir Stafford C'ripye und für [E2] Frankreich [/E2] Einanzminister Fene Hage; erscheinen werden. Bei dieser Gelenenheit wird vohi eine allgemeine Aus prache über die Ddurehführune des Mars!nll Plancs Kattfinden. Der Europäische Wirtschaftsrat hat be schlonsen, den ihm von amenilennischer Seite gemnchten Vorsehing anzunchmen und sic mit der Verteilung der amerihanischen Hise an seine Mitelieder zu befassen. Dur Vorherei tung des Verteilungsprogrammes ist im Nahmen der ständigen Konunission für euro pilische Wirtschaftszusammenurheit ein betzon deres nur aus vier Mityliedern besktchendes Unterkcomitee gebildet vorden, in dem der Ver treter Grollbnitanniens den Vorsit» führt und dem ferner Vertreter Frankreichs, Italiens und Hollands angchören."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Richard Stafford Cripps
    Description: britischer Politiker, Jurist und Diplomat (1889–1952)
    Born: ['+1889-04-24T00:00:00Z']
    Died: ['+1952-04-21T00:00:00Z']
    Birth place: ['London']
    Death place: ['Zürich']
    Work locations: ['London']
  Location Wikidata:
    Label: Frankreich
    Description: Staat in Westeuropa mit Überseegebieten
    Country: ['Frankreich']
    Aliases: {'en': ['French Republic'], 'fr': ['République française', 'RF', 'fr', 'la République française', 'Fr.', 'La France', "L'Hexagone"], 'de': ['Französische Republik', 'fr', 'RF']}
    Coordinates: [{'lat': 47, 'lon': 2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "rechnet" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Man rechnet namentlich damit, dals für Grolbritannien Senatzanzler Sir Stafford C'ripye und für Frankreich Einanzministe"
    Verb cluster: "ist" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Dur Vorherei tung des Verteilungsprogrammes ist im Nahmen der ständigen Konunission für euro pilische Wirtschaftszusamme"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.980

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between "Senatzanzler Sir Stafford\nC'ripye" and 'Frankreich' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing "Senatzanzler Sir Stafford\nC'ripye" near 'Frankreich' around 1948-07-19?
  4. Resolve temporal expressions relative to 1948-07-19. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 5:
  Publication date : 1981-12-11
  Language         : fr
  Person  : 'M. Benjamin'  (QID: N/A)
  Location: 'Fulgur'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "on s'aventure grâce à [E1] M. Benjamin [/E1] sur la froide planète [E2] Fulgur [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "aventure" — tense=Pres, aspect=None, mood=Ind
      Sentence: "on s'aventure grâce à M. Benjamin sur la froide planète Fulgur."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.985

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Benjamin' and 'Fulgur' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Benjamin' near 'Fulgur' around 1981-12-11?
  4. Resolve temporal expressions relative to 1981-12-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 6:
  Publication date : 1938-11-13
  Language         : de
  Person  : 'Siurgenenger'  (QID: N/A)
  Location: 'Fußach'  (QID: Q701030)

  [ARTICLE TEXT — entity markers added]
  "Bevor der bei [E2] Fußach [/E2] mündende Rheinkanal angelegt und damit ein direkter Abfluß des Stroms in das große See becken geschaffen wurde, ergossen sich die Wasser des Oberrheins durch diesen Arm in den Bodensee, und oft war sein Bett viel zu eng, um sie zu fassen. Ob gleich er seit dem Fußacher Durchstich nur noch die überschüssigen Stauwasser des Kanals und die Wasser der anschließenden Bäche dem Bodensee zuführen darf. Leider ist es freilich auch schon das Letzte! Ie: Dand [E1] Siurgenenger [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Fußach
    Description: Gemeinde im Bezirk Bregenz, Vorarlberg
    Country: ['Österreich']
    Located in: ['Bezirk Bregenz']
    Aliases: {'de': ['Fussach']}
    Coordinates: [{'lat': 47.478333333333, 'lon': 9.6638888888889}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "ergossen" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Bevor der bei Fußach mündende Rheinkanal angelegt und damit ein direkter Abfluß des Stroms in das große See becken gesch"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 26 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Siurgenenger' and 'Fußach' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Siurgenenger' near 'Fußach' around 1938-11-13?
  4. Resolve temporal expressions relative to 1938-11-13. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 7:
  Publication date : 1938-05-06
  Language         : de
  Person  : 'General\nKwasniewski, Präsident der Liga für eine\nKolonialmarine'  (QID: Q9342427)
  Location: 'Danzig'  (QID: Q1792)

  [ARTICLE TEXT — entity markers added]
  "General Kwasniewski, Präsident der Liga für eine Kolonialmarine, erklärte in einer Ansprache vor der [E2] Danzig [/E2]er polnischen Kolonie, aus Anlaß des 3. Mai u. a.: „Danzig kann unmöglich von Polen abgetrennt werden."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Stanisław Kwaśniewski
    Description: polnischer Offizier
    Born: ['+1886-11-14T00:00:00Z']
    Died: ['+1956-03-09T00:00:00Z']
    Birth place: ['Krakau']
    Death place: ['Q47164']
  Location Wikidata:
    Label: Danzig
    Description: Hauptstadt der Woiwodschaft Pommern im Norden von Polen
    Country: ['Polen', 'Deutsches Reich', 'Freie Stadt Danzig', 'Königreich Preußen', 'Republik Danzig', 'Q27306', 'Q172107', 'Q1649871', 'Q156020', 'Königreich Polen', 'Q156020', 'Q696640']
    Located in: ['Woiwodschaft Pommern', 'Q1222000', 'Woiwodschaft Danzig', 'Q510368', 'Q216173', 'Q161947', 'Provinz Westpreußen', 'Provinz Preußen', 'Q42887355']
    Aliases: {'en': ['Gdansk', 'Danzig', 'Dantzig', 'Dantzick'], 'fr': ['Dantzig'], 'de': ['Gdańsk']}
    Coordinates: [{'lat': 54.3482907, 'lon': 18.6540233}, {'lat': 54.35, 'lon': 18.666666666666668}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "erklärte" — tense=Past, aspect=None, mood=Ind
      Sentence: "General Kwasniewski, Präsident der Liga für eine Kolonialmarine, erklärte in einer Ansprache vor der Danziger polnischen"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 16 (0 = most prominent)
    OCR quality estimate: 0.971

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'General\nKwasniewski, Präsident der Liga für eine\nKolonialmarine' and 'Danzig' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'General\nKwasniewski, Präsident der Liga für eine\nKolonialmarine' near 'Danzig' around 1938-05-06?
  4. Resolve temporal expressions relative to 1938-05-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 8:
  Publication date : 1790-03-03
  Language         : en
  Person  : 'General D’Alton'  (QID: Q3934904)
  Location: 'LONDON'  (QID: Q84)

  [ARTICLE TEXT — entity markers added]
  "[E2] LONDON [/E2], Dec. 31. The official account of the capture ofBruffels pnbliflied by the Patriots, is as under. The firft attenpt was.tp make prifoners of all the loldiers who guarded the Mint, and thofe who were quartered in the different converts. [E1] General D’Alton [/E1] did his tu rnoff from fix o’clock in the morning to negociate an armifiice."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Richard d'Alton
    Description: Austrian officer
    Born: ['+1732-01-01T00:00:00Z', '+1733-00-00T00:00:00Z']
    Died: ['+1791-02-16T00:00:00Z', '+1790-02-16T00:00:00Z']
    Birth place: ['Rathconrath']
    Death place: ['Speyer', 'Trier']
  Location Wikidata:
    Label: London
    Description: capital and largest city of England and the United Kingdom
    Country: ['Roman Empire', 'Kingdom of Essex', 'Kingdom of Mercia', 'Kingdom of Wessex', 'Kingdom of England', 'Kingdom of Great Britain', 'United Kingdom of Great Britain and Ireland', 'United Kingdom']
    Located in: ['Kingdom of Wessex', 'Kingdom of England', 'England', 'County of London', 'Greater London']
    Aliases: {'en': ['London, UK', 'London, United Kingdom', 'London, England', 'London UK', 'London U.K.', 'Londinium', 'Loñ', 'Lundenwic', 'Londinio', 'Londini', 'Londiniensium', 'Augusta', 'Trinovantum', 'Kaerlud', 'Karelundein', 'Lunden', 'Big Smoke', 'the Big Smoke', 'Lundenburh', 'Lundenburgh', 'Llyn Dain', 'Llan Dian', 'Londinion', 'Loniniensi', 'Lon.', 'Loñ.', 'Lond.', 'LDN'], 'fr': ['London']}
    Coordinates: [{'lat': 51.507222222222, 'lon': -0.1275}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "attenpt" — tense=Pres, aspect=None, mood=None
      Sentence: "The firft attenpt was.tp make prifoners of all the loldiers who guarded the Mint, and thofe who were quartered in the di"
    Verb cluster: "did" — tense=Past, aspect=None, mood=None
      Sentence: "General D’Alton did his tu rnoff from fix o’clock in the morning to negociate an armifiice."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.974

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'General D’Alton' and 'LONDON' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'General D’Alton' near 'LONDON' around 1790-03-03?
  4. Resolve temporal expressions relative to 1790-03-03. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 9:
  Publication date : 1878-10-02
  Language         : de
  Person  : 'Fröbel'  (QID: Q76679)
  Location: 'Ungarn'  (QID: Q28)

  [ARTICLE TEXT — entity markers added]
  "— Mailand stellt Arbeiten der [E1] Fröbel [/E1]schulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die Kinder weit überschreiten: soll das Kinderarbeit sein; Begreiflicher Weise fehlt auch die Türkei. Oesterreich erscheint getrennt als Deutschösterreich und als [E2] Ungarn [/E2], das getreue Bild der feindlichen, sich aber umarmenden Brüder."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Friedrich Fröbel
    Description: deutscher Pädagoge
    Born: ['+1782-04-21T00:00:00Z', '+1782-00-00T00:00:00Z']
    Died: ['+1852-06-21T00:00:00Z', '+1852-00-00T00:00:00Z']
    Birth place: ['Oberweißbach/Thüringer Wald']
    Death place: ['Marienthal']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "stellt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "— Mailand stellt Arbeiten der Fröbelschulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die "
    Verb cluster: "erscheint" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Oesterreich erscheint getrennt als Deutschösterreich und als Ungarn, das getreue Bild der feindlichen, sich aber umarmen"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 27 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Fröbel' and 'Ungarn' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Fröbel' near 'Ungarn' around 1878-10-02?
  4. Resolve temporal expressions relative to 1878-10-02. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 10:
  Publication date : 1960-04-13
  Language         : en
  Person  : 'Alvie Mitchell Godwin'  (QID: N/A)
  Location: '5811\nAlandade Drive'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "County Natives' Son Acclaimed Outstanding Kentucky Student [E1] Alvie Mitchell Godwin [/E1]. 5811 Alandade Drive."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "5811" → 5811
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 3851 days
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.967

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Alvie Mitchell Godwin' and '5811\nAlandade Drive' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Alvie Mitchell Godwin' near '5811\nAlandade Drive' around 1960-04-13?
  4. Resolve temporal expressions relative to 1960-04-13. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 11:
  Publication date : 1898-05-02
  Language         : de
  Person  : 'Jakob Welti'  (QID: N/A)
  Location: 'Zürichhorn'  (QID: Q248693)

  [ARTICLE TEXT — entity markers added]
  "Das Schlußstück bildet das wohlgetroffene Oelbildnis, das [E1] Jakob Welti [/E1] im vorigen Jahre von Rudolf Koller entwerfen durfte. Bei dieser chronologischen Anordnung kann man deutlich beobachten, wie der Künstler sich allmählich zu einem eigenen selbständigen Stil durchrang, wie er immer mehr sich von jeglicher Schulschablone frei machte und einzig auf die getreue Naturbeobachtung abstellte, wie er zugleich in der Farbe kräftiger, in der Komposition souveräner wurde und wie er mehr und mehr seinen Gemälden einen reichen Stimmungsgehalt zu geben, manche sogar mit einer warmen Glut poetischer Empfindung zu erfüllen wußte. Nach einigem Zögern willigte Hr. Koller ein und so wird das Publikum jetzt Gelegenheit finden, auch die Arbeitsstätte des Meisters zu besichtigen, wo er den größten Teil seines Lebens thätig gewesen ist. Kollers Ateliers in dem schöngelegenen Landsitz am [E2] Zürichhorn [/E2] (Fröhlichstraße 1, in der Nähe der Pferde bahnstation) enthält eine Reihe interessanter Studien und Bilder, insbesondere aus der letzten Zeit, und wird ohne Zweifel in den nächsten Wochen der Wallfahrtsort werden, nach welchem die Kunstliebhaber und Verehrer des Künstlers pilgern werden."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: jetzt, nach, vor
    Verb cluster: "bildet" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Das Schlußstück bildet das wohlgetroffene Oelbildnis, das Jakob Welti im vorigen Jahre von Rudolf Koller entwerfen durft"
    Verb cluster: "enthält" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Kollers Ateliers in dem schöngelegenen Landsitz am Zürichhorn (Fröhlichstraße 1, in der Nähe der Pferde bahnstation) ent"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 13 (0 = most prominent)
    OCR quality estimate: 0.998

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Jakob Welti' and 'Zürichhorn' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Jakob Welti' near 'Zürichhorn' around 1898-05-02?
  4. Resolve temporal expressions relative to 1898-05-02. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 12:
  Publication date : 1928-02-17
  Language         : de
  Person  : 'Pfarrer Niederer'  (QID: N/A)
  Location: 'Schloßberg'  (QID: Q2244426)

  [ARTICLE TEXT — entity markers added]
  "Vom Hin tersässenschulmeister am [E2] Schloßberg [/E2] steigt er auf zum Seminardirektor auf dem Schloß Burgdorf. „Sein Streben war, die Wege zu erkennen, auf denen die pädagogische Arbeit — nicht nur seine eigne, sondern eine jede — vorwärtsgehen müsse. Er glaubte an die unabänderliche Gleichheit der menschlichen Natur und an die Ewigkeit der menschlichen Ziele; und darum glaubte er, daß eine Methode der Erziehung die richtige, die not wendige sein müsse." Wenn uns auch heute seine Einzelerkenntnisse wenig mehr zu sagen haben, seine Rückführung der Pädagogik auf Psychologie, sein Arbeitsprinzip, sie leben. [E1] Pfarrer Niederer [/E1] taucht in seinem Lebenskreis auf."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Schlossberg (Uri)
    Description: Berg in den Alpen
    Country: ['Q39']
    Located in: ['Q12404']
    Aliases: {'de': ['Hinter Schloss']}
    Coordinates: [{'lat': 46.8025, 'lon': 8.52694}, {'lat': 46.80277778, 'lon': 8.52722222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: heute, vor
    Verb cluster: "haben" — tense=None, aspect=None, mood=None
      Sentence: "Wenn uns auch heute seine Einzelerkenntnisse wenig mehr zu sagen haben, seine Rückführung der Pädagogik auf Psychologie,"
    Verb cluster: "steigt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Vom Hin tersässenschulmeister am Schloßberg steigt er auf zum Seminardirektor auf dem Schloß Burgdorf."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 33 (0 = most prominent)
    OCR quality estimate: 0.996

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Pfarrer Niederer' and 'Schloßberg' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Pfarrer Niederer' near 'Schloßberg' around 1928-02-17?
  4. Resolve temporal expressions relative to 1928-02-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 13:
  Publication date : 1961-01-20
  Language         : fr
  Person  : 'Roger Rivière'  (QID: N/A)
  Location: 'Lamalou-les-Bains'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Le Dr Stern, directeur de la clinique de rééducation de [E2] Lamalou-les-Bains [/E2], a rendu visite à [E1] Roger Rivière [/E1], qu'il avait soigné le premier après sa chute dans le Tour de France."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: après
    Verb cluster: "soigné" — tense=Past, aspect=None, mood=None
      Sentence: "Le Dr Stern, directeur de la clinique de rééducation de Lamalou-les-Bains, a rendu visite à Roger Rivière, qu'il avait s"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 18 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Roger Rivière' and 'Lamalou-les-Bains' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Roger Rivière' near 'Lamalou-les-Bains' around 1961-01-20?
  4. Resolve temporal expressions relative to 1961-01-20. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 14:
  Publication date : 1881-01-15
  Language         : fr
  Person  : 'M. Patrick Collins'  (QID: N/A)
  Location: 'Boston'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Dans une réunion qui vient d'avoir lieu, une résolution a été adoptée tendant à former une nouvelle ligue qui s'appelle la Ligue agraire nationale des Etats-Unis, sous la présidence de [E1] M. Patrick Collins [/E1], de [E2] Boston [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "adoptée" — tense=Past, aspect=None, mood=None
      Sentence: "Dans une réunion qui vient d'avoir lieu, une résolution a été adoptée tendant à former une nouvelle ligue qui s'appelle "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.967

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Patrick Collins' and 'Boston' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Patrick Collins' near 'Boston' around 1881-01-15?
  4. Resolve temporal expressions relative to 1881-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 15:
  Publication date : 1790-03-03
  Language         : en
  Person  : 'General D’Alton'  (QID: Q3934904)
  Location: 'Bafleville'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "[E1] General D’Alton [/E1] did his tu rnoff from fix o’clock in the morning to negociate an armifiice. About (even o’clock, 8co men of Benden-D’Aloft entered the city with two pieces of cannon, which they planted on the Grand Pa lace. About ten o’clock General D’Alton thought proper to fend a large dctatchment in order to releafe, by forcible means, the ollicers and pri vates made prifoners in lhe [E2] Bafleville [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Richard d'Alton
    Description: Austrian officer
    Born: ['+1732-01-01T00:00:00Z', '+1733-00-00T00:00:00Z']
    Died: ['+1791-02-16T00:00:00Z', '+1790-02-16T00:00:00Z']
    Birth place: ['Rathconrath']
    Death place: ['Speyer', 'Trier']
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "did" — tense=Past, aspect=None, mood=None
      Sentence: "General D’Alton did his tu rnoff from fix o’clock in the morning to negociate an armifiice."
    Verb cluster: "made" — tense=Past, aspect=None, mood=None
      Sentence: "About ten o’clock General D’Alton thought proper to fend a large dctatchment in order to releafe, by forcible means, the"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.974

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'General D’Alton' and 'Bafleville' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'General D’Alton' near 'Bafleville' around 1790-03-03?
  4. Resolve temporal expressions relative to 1790-03-03. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 16:
  Publication date : 1918-11-18
  Language         : fr
  Person  : 'Hubacher'  (QID: Q1603686)
  Location: 'St-Gervais'  (QID: Q55335900)

  [ARTICLE TEXT — entity markers added]
  "[E1] Hubacher [/E1]. Hofmanr et Nicole, arrêtés la veille,. Les dégâts dépassent 100,000 fr. — Le juge d'instruction militaire Rehfous, après avoir entendu vendredi après midi MM. Nicolet député socialiste, Hubacher, secrétaire des métallurgistes, et Hoffmann, président du parti socialiste genevois, qui avaient été arrêtés au cours do la bagarre de Coutance, les a remis en liberté."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Helmut Hubacher
    Description: politicien suisse
    Born: ['+1926-04-15T00:00:00Z']
    Died: ['+2020-08-19T00:00:00Z']
    Birth place: ['Krauchthal']
    Death place: ['Porrentruy']
    Work locations: ['Berne']
  Location Wikidata:
    Label: St-Gervais – Chantepoulet
    Description: quarter in the municipality of Geneva, Switzerland
    Country: ['Q39']
    Located in: ['Q71']
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: après
    Verb cluster: "remis" — tense=Past, aspect=None, mood=None
      Sentence: "— Le juge d'instruction militaire Rehfous, après avoir entendu vendredi après midi MM. Nicolet député socialiste, Hubach"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 85 (0 = most prominent)
    OCR quality estimate: 0.988

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Hubacher' and 'St-Gervais' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Hubacher' near 'St-Gervais' around 1918-11-18?
  4. Resolve temporal expressions relative to 1918-11-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 17:
  Publication date : 1898-05-02
  Language         : de
  Person  : 'Präsident der Kunstgesell\nschaft, Hr. Dr. Carl v. Muralt,'  (QID: N/A)
  Location: 'Zürichhorn'  (QID: Q248693)

  [ARTICLE TEXT — entity markers added]
  "Der Präsident der Kunstgesell schaft, Hr. Dr. Carl v. Muralt, übernahm die Aus stellung im Namen des Vorstandes und sprach den sämtlichen Mitgliedern, die sich um die Fertigstellung der Ausstellung verdient gemacht hatten, den besten Dank für ihre Bemühungen aus. Warme Worte widmete der Präsident dem anwesenden greisen Künstler, zu dessen Ehren die Ausstellung veranstaltet wurde. Nach einigem Zögern willigte Hr. Koller ein und so wird das Publikum jetzt Gelegenheit finden, auch die Arbeitsstätte des Meisters zu besichtigen, wo er den größten Teil seines Lebens thätig gewesen ist. Kollers Ateliers in dem schöngelegenen Landsitz am [E2] Zürichhorn [/E2] (Fröhlichstraße 1, in der Nähe der Pferde bahnstation) enthält eine Reihe interessanter Studien und Bilder, insbesondere aus der letzten Zeit, und wird ohne Zweifel in den nächsten Wochen der Wallfahrtsort werden, nach welchem die Kunstliebhaber und Verehrer des Künstlers pilgern werden."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Zürichhorn
    Description: Schwemmkegel am Ostufer des unteren Seebeckens des Zürichsees
    Country: ['Q39']
    Located in: ['Zürich', 'Kanton Zürich']
    Aliases: {'en': ['Zurichhorn']}
    Coordinates: [{'lat': 47.3536, 'lon': 8.55211}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: jetzt, nach, vor
    Verb cluster: "übernahm" — tense=Past, aspect=None, mood=Ind
      Sentence: "Der Präsident der Kunstgesell schaft, Hr. Dr. Carl v. Muralt, übernahm die Aus stellung im Namen des Vorstandes und spra"
    Verb cluster: "enthält" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Kollers Ateliers in dem schöngelegenen Landsitz am Zürichhorn (Fröhlichstraße 1, in der Nähe der Pferde bahnstation) ent"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.998

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Präsident der Kunstgesell\nschaft, Hr. Dr. Carl v. Muralt,' and 'Zürichhorn' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Präsident der Kunstgesell\nschaft, Hr. Dr. Carl v. Muralt,' near 'Zürichhorn' around 1898-05-02?
  4. Resolve temporal expressions relative to 1898-05-02. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 18:
  Publication date : 1800-10-16
  Language         : en
  Person  : 'D.C * I.DWELL,\nClerl of lie DiJtriEl of Peonsyl v aoisA'  (QID: N/A)
  Location: 'United States of America'  (QID: Q30)

  [ARTICLE TEXT — entity markers added]
  "Tenth day of July in the twenty fif-.h year of the Indepen dence of the [E2] United States of America [/E2], Alexan der Addison of the said District hath deposited in this office the title of a book the right where of he claims as Author in tha words following to wit, “ Reports of cafes in the County courts of the Fifth Circuit and in the High Court of Errors and appeals of the State of Pennsylvania, and charges to Grand Juries of those County Courts. By Alexander Addison, President of the Courts of Common Pleas of me Fifth Cir cuit of the State of Pennlylvann.” In conformity to the act of Congress of the Uni ted States istitlrd “ An act for the encouragement of learning by securimr the copies of maps charts and books to the Authors and Proprietors of such copies during the times therein mentioned." D.C * I.DWELL, Clerl of lie DiJtriEl of Peonsyl v aoisA The above book is now pohlsshcd."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: United States
    Description: country located primarily in North America
    Country: ['United States']
    Aliases: {'en': ['the States', 'the United States of America', 'US of America', 'the US', 'the U.S.', 'the US of A', 'U.S. of America', 'the US of America', 'the USA', 'the U.S.A.', 'the U.S. of A', 'US of A', 'the U.S. of America', 'the United States', 'Merica', 'Murica', 'United States of America', 'U.S.', 'U.S.A.', 'U. S.', 'U. S. A.', 'America'], 'fr': ['É.-U.', 'É-U', 'É-U.', 'E.-U.', 'É.U.', 'les États', 'Oncle Sam', 'Amérique', 'Etats-Unis', 'States', 'les États-Unis d’Amérique', 'États-unis', 'ÉU', 'É.-U. A.', "Pays de l'Oncle Sam", 'Etats-unis', 'États-Unis d’Amérique', 'pays de l’Oncle Sam'], 'de': ['Vereinigte Staaten von Amerika', 'US-Amerika', 'U.S.-Amerika', 'Staaten von Amerika', 'VSA', 'V.S.A.', 'V. S. A.', 'Staaten', 'die Staaten', 'VS', 'V.S.', 'V. S.', 'Amerika', 'U.S.A.', 'U. S. A.', 'United States of America', 'United States', 'U.S.', 'U. S.', 'America'], 'lb': ['Vereenegt Staaten']}
    Coordinates: [{'lat': 39.828175, 'lon': -98.5795}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now
    Verb cluster: "deposited" — tense=Past, aspect=None, mood=None
      Sentence: "Tenth day of July in the twenty fif-.h year of the Indepen dence of the United States of America, Alexan der Addison of "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 1 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'D.C * I.DWELL,\nClerl of lie DiJtriEl of Peonsyl v aoisA' and 'United States of America' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'D.C * I.DWELL,\nClerl of lie DiJtriEl of Peonsyl v aoisA' near 'United States of America' around 1800-10-16?
  4. Resolve temporal expressions relative to 1800-10-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 19:
  Publication date : 1928-01-17
  Language         : fr
  Person  : 'Aicide Matthey'  (QID: N/A)
  Location: 'Etang'  (QID: Q2721193)

  [ARTICLE TEXT — entity markers added]
  "Matthey de l'[E2] Etang [/E2] ( Matthey de la Gouille Horloger de son métier, il était aussi un enragé coureur de forêts, ramassant fruits et champignons, à l'occasion cueillant des plantes rares pour l'herboriste des Geneveys, ou collectionnant toutes les curiosités des règnes animal, minéral et végétal pour enrichir le musée du village, où se trouven t réunis de glorieux vestiges du bon vieux temps, où l'on était Prussiens, voisinant avec un autographe de Victor Hugo et des armes de Zanzibar. Pour tout dire, [E1] Aicide Matthey [/E1] était dans son genre une personnalité intéressante et originale, quelque peu misanthrope qui ne voyait _* u genre humain que malices et méchancetés."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: lac Grenon
    Description: lac suisse
    Country: ['Suisse']
    Located in: ['canton du Valais', 'Montana']
    Aliases: {'en': ['Lac Grenon']}
    Coordinates: [{'lat': 46.31, 'lon': 7.4758333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "était genre" — tense=Imp, aspect=None, mood=Ind
      Sentence: "Pour tout dire, Aicide Matthey était dans son genre une personnalité intéressante et originale, quelque peu misanthrope "
    Verb cluster: "était enragé" — tense=Imp, aspect=None, mood=Ind
      Sentence: "Matthey de l'Etang ( Matthey de la Gouille Horloger de son métier, il était aussi un enragé coureur de forêts, ramassant"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.981

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Aicide Matthey' and 'Etang' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Aicide Matthey' near 'Etang' around 1928-01-17?
  4. Resolve temporal expressions relative to 1928-01-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 20:
  Publication date : 1826-09-29
  Language         : fr
  Person  : 'M. le marquis de Souza'  (QID: N/A)
  Location: 'Zamora'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "On ne sait pas si la ville de [E2] Zamora [/E2] se ressent aussi du même mal, mais on assure qu'on va y envoyer un bataillon d'infanterie de la garde ; ..''.-- -Lé gouvernement parait également embarrassé au'sujet d'une affaire importante. [E1] M. le marquis de Souza [/E1] vient d'être nommé ambassadeur du Portugal près notre'cour, et notre ministère- ^ requ officiellement l'avis de sa nomination."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "sait" — tense=Pres, aspect=None, mood=Ind [NEGATED]
      Sentence: "On ne sait pas si la ville de Zamora se ressent aussi du même mal, mais on assure qu'on va y envoyer un bataillon d'infa"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 19 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. le marquis de Souza' and 'Zamora' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. le marquis de Souza' near 'Zamora' around 1826-09-29?
  4. Resolve temporal expressions relative to 1826-09-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 21:
  Publication date : 1918-07-10
  Language         : fr
  Person  : 'M. de Kûhlmann'  (QID: N/A)
  Location: 'Berlin'  (QID: Q31910791)

  [ARTICLE TEXT — entity markers added]
  "BERLIN, 9. — Groupe d'armées du prince héritier Rupprecht. > BERLIN * 9 (Wolff). — On annonce de source autorisée que l'empereur a accepté la démission présentée par le secrétaire d'Etat de Kûhlmann."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "autorisée" — tense=Past, aspect=None, mood=None
      Sentence: "— On annonce de source autorisée que l'empereur a accepté la démission présentée par le secrétaire d'Etat de Kûhlmann."
    Verb cluster: "BERLIN" — tense=Past, aspect=None, mood=None
      Sentence: "BERLIN, 9."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 58 (0 = most prominent)
    OCR quality estimate: 0.956

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. de Kûhlmann' and 'Berlin' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. de Kûhlmann' near 'Berlin' around 1918-07-10?
  4. Resolve temporal expressions relative to 1918-07-10. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 22:
  Publication date : 1938-05-20
  Language         : de
  Person  : 'Victor Homberg'  (QID: N/A)
  Location: 'Frankreichs'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "und der Bruch [E2] Frankreichs [/E2] mit dem Vatikan. In seinen, in der „Revue de Paris" verössentlichten neues Material zutagefördernden Erinnerungen über Frankreichs größten Außenminister Deleass. stellt Octave Homberg fest, daß Delcass. Er hat alles getan, um Eombes am Bruch des Konkordates zu verhindern. Der Präsident der Republik, der allein auf dem Laufenden war, entsandte ohne Wissen der französischen Botschaft in Rom [E1] Victor Homberg [/E1] in geheimer Mission nach Rom, um durch Vermittlung von Kardinal Rampolla Konzessionen namentlich in der Frage der Vischofsernennungen zu erlangen;"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Frankreich
    Description: Staat in Westeuropa mit Überseegebieten
    Country: ['Frankreich']
    Aliases: {'en': ['French Republic'], 'fr': ['République française', 'RF', 'fr', 'la République française', 'Fr.', 'La France', "L'Hexagone"], 'de': ['Französische Republik', 'fr', 'RF']}
    Coordinates: [{'lat': 47, 'lon': 2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach
    Verb cluster: "entsandte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Der Präsident der Republik, der allein auf dem Laufenden war, entsandte ohne Wissen der französischen Botschaft in Rom V"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 4 (0 = most prominent)
    OCR quality estimate: 1.000

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Victor Homberg' and 'Frankreichs' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Victor Homberg' near 'Frankreichs' around 1938-05-20?
  4. Resolve temporal expressions relative to 1938-05-20. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 23:
  Publication date : 1810-04-07
  Language         : en
  Person  : 'Gen. Fain'  (QID: N/A)
  Location: 'Boneventa'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "He in forms that the French army was fast ap proaching the borders of Portugal, and rea ched [E2] Boneventa [/E2]. Bonaparte at the head of an army of 100,000 men, was marching through Spain and Portugal; and capt. B. says, he was informed by [E1] Gen. Fain [/E1], of the British army, that he expected the French would have Lisbon in April."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "was marching" — tense=Past, aspect=Prog, mood=Ind
      Sentence: "Bonaparte at the head of an army of 100,000 men, was marching through Spain and Portugal; and capt. B. says, he was info"
    Verb cluster: "ap" — tense=None, aspect=None, mood=None
      Sentence: "He in forms that the French army was fast ap proaching the borders of Portugal, and rea ched Boneventa."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.947

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Gen. Fain' and 'Boneventa' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Gen. Fain' near 'Boneventa' around 1810-04-07?
  4. Resolve temporal expressions relative to 1810-04-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 24:
  Publication date : 1800-12-27
  Language         : en
  Person  : 'OTTO'  (QID: N/A)
  Location: 'Fiance'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "The principles contained in these two pieces are, in several respects so little analogous to the proposals which I have been directed to make, and the object of which was to compensate by a Britissi ar mistice, the inconveniences which might re- fultto [E2] Fiance [/E2] from the eventual prolonga tion of the German armistice, that I can not take upon myself to admit them with out previously receiving furthcrinstroctiona. I have therefore complied with your excel lency’s intentions by fanfmittihg to my go vernment those two pieces, with as little delay as possible. I have the honour to be, 8cc. (Signed) “ [E1] OTTO [/E1]-’’"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: France
    Description: country in Western Europe and other continents (through its overseas territories in America, Africa and Oceania)
    Country: ['France']
    Aliases: {'en': ['French Republic'], 'fr': ['République française', 'RF', 'fr', 'la République française', 'Fr.', 'La France', "L'Hexagone"], 'de': ['Französische Republik', 'fr', 'RF']}
    Coordinates: [{'lat': 47, 'lon': 2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "Signed" — tense=Past, aspect=Perf, mood=None
      Sentence: "(Signed) “ OTTO-’’"
    Verb cluster: "are" — tense=Pres, aspect=None, mood=Ind
      Sentence: "The principles contained in these two pieces are, in several respects so little analogous to the proposals which I have "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 4 (0 = most prominent)
    OCR quality estimate: 0.964

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'OTTO' and 'Fiance' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'OTTO' near 'Fiance' around 1800-12-27?
  4. Resolve temporal expressions relative to 1800-12-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 25:
  Publication date : 1790-05-29
  Language         : en
  Person  : 'Hon. Peter Sylvester'  (QID: Q2078354)
  Location: 'Belipatain'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "The Ship Harmony Capt. IVillet is arrived at Philadelphia from Bengal.—Accounts from the Eaft-Indies State—there is a mod plealing pro- fpeft of a plentiful harveft in that pare of the world—that Cotton has fold fo low as 11 Tales in China—that the Englifli/ fettlements enjoy a profound peace—that the greateft part of trea- fure on board the Vanfittart one of the Eaft-In- idea company’s Ships lately loft, had been re covered from the wreck—that the ffiip Durham Capt. Kepling ; and another fhip were loft in a gale of wind, foundering in the road—that Tippoo Sultan to puQjfh the faults of fome of the tributary Princes had depopulated and laid wafte their country from [E2] Belipatain [/E2] to Callicut, an ex tent of 80 or 90 miles, where the latepoffeflors of its fields and habitations arefeen no more. The Hon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: late
    Verb cluster: "is" — tense=Pres, aspect=None, mood=Ind
      Sentence: "IVillet is arrived at Philadelphia from Bengal.—Accounts from the Eaft-Indies State—there is a mod plealing pro- fpeft o"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Hon. Peter Sylvester' and 'Belipatain' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Hon. Peter Sylvester' near 'Belipatain' around 1790-05-29?
  4. Resolve temporal expressions relative to 1790-05-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 26:
  Publication date : 1921-02-22
  Language         : fr
  Person  : 'M. Stadler'  (QID: N/A)
  Location: 'Suisse romande'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "chanteurs de Genève-Ville organisent, avec le concours de M Stalder. de Berne, une soirée de pioiections lumineuses qui sera donnée dans la salle de la Réformation, le 2 mars 'prochain. M. Stalder a déjà fait avec le Plus scrand SUCCÈS de nombreuses conférences de ce eenre en [E2] Suisse romande [/E2], en France et en Belgique. C'est en véritable artiste, amoureux de l'Alpe. que [E1] M. Stadler [/E1] a patiemment recueilli la splendide collection de clichés colorés, an moyen desquels ii nous promènera en zigzag dans les cantons alpins."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Verb cluster: "organisent" — tense=Pres, aspect=None, mood=Ind
      Sentence: "chanteurs de Genève-Ville organisent, avec le concours de M Stalder."
    Verb cluster: "fait" — tense=Past, aspect=None, mood=None
      Sentence: "M. Stalder a déjà fait avec le Plus scrand SUCCÈS de nombreuses conférences de ce eenre en Suisse romande, en France et "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 30 (0 = most prominent)
    OCR quality estimate: 0.932

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Stadler' and 'Suisse romande' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Stadler' near 'Suisse romande' around 1921-02-22?
  4. Resolve temporal expressions relative to 1921-02-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 27:
  Publication date : 1808-09-01
  Language         : fr
  Person  : 'demoiselle Julie-Valérie Bonvêpre'  (QID: N/A)
  Location: 'Verrières'  (QID: Q69807)

  [ARTICLE TEXT — entity markers added]
  "Jaques Henri Boûrquin, veuve de Jacob fils de Jaques Guye, des [E2] Verrières [/E2] _, résidante et paroissienne de la Cote-aux-Fées, de mettre ses biens en décret ; _£. Le public est informé, que le sieur Charles-Henri vêpre, et la [E1] demoiselle Julie-Valérie Bonvêpre [/E1], fils et fille de feu M. Charles-Guillaume Bonvêpre, membre du Grand-Conseil et hôpitalier, et de la damé Susanne Petitpierre, sa veuve, bourgeoise de Neuchatel, ont ¦ été admis par arrêt du Conseil d'Etat en date du 5 Juil-."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "informé" — tense=Past, aspect=None, mood=None
      Sentence: "Le public est informé, que le sieur Charles-Henri vêpre, et la demoiselle Julie-Valérie Bonvêpre, fils et fille de feu M"
    Verb cluster: "mettre" — tense=None, aspect=None, mood=None
      Sentence: "Jaques Henri Boûrquin, veuve de Jacob fils de Jaques Guye, des Verrières _, résidante et paroissienne de la Cote-aux-Fée"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 17 (0 = most prominent)
    OCR quality estimate: 0.952

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'demoiselle Julie-Valérie Bonvêpre' and 'Verrières' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'demoiselle Julie-Valérie Bonvêpre' near 'Verrières' around 1808-09-01?
  4. Resolve temporal expressions relative to 1808-09-01. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 28:
  Publication date : 1930-03-21
  Language         : en
  Person  : 'G. D. Miller'  (QID: N/A)
  Location: 'Dare\ncounty'  (QID: Q295787)

  [ARTICLE TEXT — entity markers added]
  "The students are being taught in the neighboring homes of E. P. White, [E1] G. D. Miller [/E1] and U. B. Williams.— D. V. M. Buxton Loses Its School Building Buxton, at Cane Hattcras, Dare county, finds itself in a bad situ-"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Dare County
    Description: county in North Carolina, United States
    Country: ['United States']
    Located in: ['North Carolina']
    Aliases: {'en': ['Dare County, North Carolina', 'Dare County, NC'], 'fr': ['Dare County']}
    Coordinates: [{'lat': 35.69, 'lon': -75.73}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "are being taught" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "The students are being taught in the neighboring homes of E. P. White, G. D. Miller and U. B. Williams.—"
    Verb cluster: "Loses" — tense=Pres, aspect=None, mood=None
      Sentence: "D. V. M. Buxton Loses Its School Building Buxton, at Cane Hattcras, Dare county, finds itself in a bad situ-"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.969

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'G. D. Miller' and 'Dare\ncounty' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'G. D. Miller' near 'Dare\ncounty' around 1930-03-21?
  4. Resolve temporal expressions relative to 1930-03-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 29:
  Publication date : 1950-09-23
  Language         : en
  Person  : 'Mrs. H. F. Thomas'  (QID: N/A)
  Location: 'Birming\nham, Ala.'  (QID: Q79867)

  [ARTICLE TEXT — entity markers added]
  "Among the guests were: [E1] Mrs. H. F. Thomas [/E1]. Birming ham, Ala., a rug and mattress manufacturer; and Mrs. Freddvo S Henderson."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Birmingham
    Description: city in and county seat of Jefferson County, Alabama, United States
    Country: ['United States']
    Located in: ['Jefferson County', 'Shelby County']
    Aliases: {'en': ['Birmingham, Alabama', 'The Magic City', 'Birmingham, AL'], 'de': ['Birmingham, Alabama']}
    Coordinates: [{'lat': 33.5175, 'lon': -86.80944444444444}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "were" — tense=Past, aspect=None, mood=Ind
      Sentence: "Among the guests were: Mrs. H. F. Thomas."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 18 (0 = most prominent)
    OCR quality estimate: 0.998

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mrs. H. F. Thomas' and 'Birming\nham, Ala.' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mrs. H. F. Thomas' near 'Birming\nham, Ala.' around 1950-09-23?
  4. Resolve temporal expressions relative to 1950-09-23. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 30:
  Publication date : 1948-04-23
  Language         : de
  Person  : 'Vorsitz\nGladwyn Jebb'  (QID: Q1275)
  Location: 'Brüssel'  (QID: Q239)

  [ARTICLE TEXT — entity markers added]
  "Finanzsachverständige der am [E2] Brüssel [/E2]er Fünf-Mächte-Pakt beteiligten Staaten beendeten gestern im Haag ihre vorbereitenden Besprechungen über eine Zusammenarbeit auf finanziellem Gebiet. In einem kurzen Kommuniquee heißt es, die Finanzminister der 5 Staaten werden in der kommenden Woche in Brüssel zusammentreffen, um die Fragen der finanziellen und wirtschaftlichen Zusammenarbeit nicht allein im Hinblick auf den Fünf-Mächte- Pakt sondern ebenso in Verbindung mit dem europäischen Wiederaufbau zu beraten. Der britische Außenminister Ernest Elevin wird die Konferenz der ständigen Organisation der westeuropäischen Union morgen in Lancaster Housc eröffnen, teilte das Foreign Office gestern mit. Nach der Eröffnungsansprache an die Delegierten der fünf Teilnehmerstaaten wird e« für die erste Sitzung dem Vorsitz Gladwyn Jebb vom Foreign Office überge"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Gladwyn Jebb
    Description: britischer Politiker und Diplomat
    Born: ['+1900-04-25T00:00:00Z']
    Died: ['+1996-10-24T00:00:00Z']
    Birth place: ['Q163']
    Death place: ['Q1570884']
    Work locations: ['Straßburg', 'Brüssel']
  Location Wikidata:
    Label: Brüssel
    Description: Hauptstadt Belgiens
    Country: ['Q31']
    Located in: ['Bezirk Brüssel-Hauptstadt']
    Aliases: {'en': ['02', 'Bru', 'BXL', 'Brussels City', 'Brussels, Belgium', 'Brussel', 'Ville de Bruxelles', 'Brussels (municipality)', 'Bruxelles', 'Stad Brussel', 'Brussels', 'City of Brussels'], 'fr': ['BXL', '02', 'Bruxelles-Ville', 'Ville de Bruxelles'], 'de': ['Bruxelles', 'Brussel', 'BXL'], 'lb': ['Bruxelles']}
    Coordinates: [{'lat': 50.846666666666664, 'lon': 4.351666666666667}]
  Known person–location links: {"work_location": "P937"}

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: gestern, nach, vor
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Nach der Eröffnungsansprache an die Delegierten der fünf Teilnehmerstaaten wird e« für die erste Sitzung dem Vorsitz Gla"
    Verb cluster: "beendeten" — tense=Past, aspect=None, mood=Ind
      Sentence: "Finanzsachverständige der am Brüsseler Fünf-Mächte-Pakt beteiligten Staaten beendeten gestern im Haag ihre vorbereitende"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 6 (0 = most prominent)
    OCR quality estimate: 0.985

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Vorsitz\nGladwyn Jebb' and 'Brüssel' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Vorsitz\nGladwyn Jebb' near 'Brüssel' around 1948-04-23?
  4. Resolve temporal expressions relative to 1948-04-23. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 31:
  Publication date : 1868-02-19
  Language         : de
  Person  : 'Bismarck'  (QID: Q8442)
  Location: 'Preußens'  (QID: Q38872)

  [ARTICLE TEXT — entity markers added]
  "digt : überall in Deutſchland und über deſſen Grenzen hinaus richtet ſich die Beachtung und Anerkennung der Regierung und der Völker auf das Verfahren [E2] Preußens [/E2] in den eroberten Provinzen . Die bedeutſamſten Stimmen aus Süddeutſchland ver⸗ zu dieſer Berathung herbeigekommen und von 141 Anweſenden baben 127 ihre Zuſtimmung zu der Vorlage ertheilt ; geſtimmt hat , iſt eine Politik des Wohlwollens und der Ge — hat , zur feſten Stütze zu dienen . Rechte und die provinzielle Selbſtſtändigkeit der gewonnenen Landestheile mit ſolcher Fürſorge wahrt , nicht eine engberzige Eroberungspolitik , ſondern eine wahrhaft nationale Politik be⸗ mit wie gutem Rechte Graf [E1] Bismarck [/E1] darauf hindeutete , daß dieſe hannoverſche Frage nur im Zuſammenhange der geſammten Politik Preußens richtig beurtheilt werden könne ."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Otto von Bismarck
    Description: deutscher Politiker und Staatsmann
    Born: ['+1815-04-01T00:00:00Z', '+1815-01-01T00:00:00Z']
    Died: ['+1898-07-30T00:00:00Z', '+1898-01-01T00:00:00Z']
    Birth place: ['Schönhausen (Elbe)']
    Death place: ['Friedrichsruh']
    Work locations: ['Berlin', 'Friedrichsruh', 'Warcino']
  Location Wikidata:
    Label: Preußen
    Description: Staatswesen (Herzogtum, Königreich, Freistaat), 1525–1947
    Country: ['Preußen']
    Aliases: {'en': ['Prussia (Germany)'], 'fr': ['État prussien', 'Prussienne'], 'de': ['Preussen']}
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "wahrt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Rechte und die provinzielle Selbſtſtändigkeit der gewonnenen Landestheile mit ſolcher Fürſorge wahrt , nicht eine engber"
    Verb cluster: "richtet" — tense=Pres, aspect=None, mood=Ind
      Sentence: "digt : überall in Deutſchland und über deſſen Grenzen hinaus richtet ſich die Beachtung und Anerkennung der Regierung un"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 26 (0 = most prominent)
    OCR quality estimate: 0.994

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Bismarck' and 'Preußens' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Bismarck' near 'Preußens' around 1868-02-19?
  4. Resolve temporal expressions relative to 1868-02-19. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 32:
  Publication date : 1892-07-05
  Language         : de
  Person  : 'G . A . Hendrichs'  (QID: N/A)
  Location: 'Berliner'  (QID: Q64)

  [ARTICLE TEXT — entity markers added]
  "Handels⸗ Zeitung des [E2] Berliner [/E2] Tageblatts . Nummer 335 . J . Beck zu Euven und G ."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Berlin
    Description: Hauptstadt und bevölkerungsreichste Stadt der Bundesrepublik Deutschland
    Country: ['Mark Brandenburg', 'Brandenburg-Preußen', 'Königreich Preußen', 'Q150981', 'Q43287', 'Q41304', 'NS-Staat', 'Q55300', 'Deutsche Demokratische Republik', 'Q183', 'Bundesrepublik Deutschland bis 1990']
    Located in: ['Mark Brandenburg', 'Q157367', 'Königreich Preußen', 'Q700264', 'Königreich Preußen', 'Q161036', 'NS-Staat', 'Q183']
    Aliases: {'en': ['Berlin, Germany', 'DE-BE'], 'de': ['Stadt Berlin', 'Berlin, Deutschland', 'Bundeshauptstadt Berlin', 'Land Berlin', 'DE-BE', 'Berlin (Deutschland)', 'BE', 'Bln', 'Bln.']}
    Coordinates: [{'lat': 52.516666666667, 'lon': 13.383333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 124 (0 = most prominent)
    OCR quality estimate: 0.975

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'G . A . Hendrichs' and 'Berliner' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'G . A . Hendrichs' near 'Berliner' around 1892-07-05?
  4. Resolve temporal expressions relative to 1892-07-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 33:
  Publication date : 1848-10-21
  Language         : de
  Person  : 'Radetzky'  (QID: Q153500)
  Location: 'Frankfurt'  (QID: Q1794)

  [ARTICLE TEXT — entity markers added]
  "Der gestern erwähnte Tagsbefehl [E1] Radetzky [/E1]'s lautet: „Soldaten! Ihr habt mich oft Euern Deutschland. [E2] Frankfurt [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Josef Wenzel Radetzky von Radetz
    Description: österreichischer Feldmarschall böhmischer Herkunft (1766–1858)
    Born: ['+1766-11-02T00:00:00Z']
    Died: ['+1858-01-05T00:00:00Z']
    Birth place: ['Q12060275']
    Death place: ['Q490']
    Work locations: ['Kaiserreich Österreich', 'Q81137', 'Österreich-Ungarn']
  Location Wikidata:
    Label: Frankfurt am Main
    Description: bevölkerungsreichste Stadt in Hessen, Deutschland
    Country: ['Fränkisches Reich', 'Q153080', 'Heiliges Römisches Reich', 'Großherzogtum Frankfurt', 'Freie Stadt Frankfurt', 'Q151624', 'Königreich Preußen', 'Q1206012', 'Q41304', 'Q7318', 'Deutschland 1945 bis 1949', 'Bundesrepublik Deutschland bis 1990', 'Deutschland']
    Located in: ['Regierungsbezirk Darmstadt', 'Regierungsbezirk Wiesbaden', 'Freie Stadt Frankfurt']
    Aliases: {'en': ['Frankfurt/Main', 'Frankfurt (Main)', 'Kreisfreie Stadt Frankfurt am Main', 'Frankfort-on-the-Main', 'Frankfurt, Germany', 'Frankfurt am Main, Germany', 'Frankfurt am Main', 'Francfort'], 'fr': ['Francfort', 'Frankfurt am Main', 'Francfort-sur-le-Mein', 'Francfort-sur-le-main', 'Frankfurt'], 'de': ['Frankfurt', 'Frankfurt/Main', 'FFM', 'Frankfurt (Main)', 'Frankfurt a. M.', 'Ffm', 'Ffm.', 'Fft.', 'Frankfurt a.M.', 'Franckfurt am Mayn', 'Frankfurt a. Main', 'Internationale Messestadt'], 'lb': ['Frankfurt', 'Frankfurt/Main']}
    Coordinates: [{'lat': 50.11055555555556, 'lon': 8.682222222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: gestern
    Verb cluster: "lautet" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Der gestern erwähnte Tagsbefehl Radetzky's lautet: „Soldaten!"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Radetzky' and 'Frankfurt' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Radetzky' near 'Frankfurt' around 1848-10-21?
  4. Resolve temporal expressions relative to 1848-10-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 34:
  Publication date : 1938-05-20
  Language         : de
  Person  : 'Eombes'  (QID: Q275020)
  Location: 'Vatikan'  (QID: Q237)

  [ARTICLE TEXT — entity markers added]
  "und der Bruch Frankreichs mit dem [E2] Vatikan [/E2]. In seinen, in der „Revue de Paris" verössentlichten neues Material zutagefördernden Erinnerungen über Frankreichs größten Außenminister Deleass. stellt Octave Homberg fest, daß Delcass. gegen den seinerzeitigen Bruch Frankreichs mit dem Vatikan gewesen war. Obwohl Radikalsozialist war er nicht antiklerikal; als Außenminister hatte er überdies die moralische Macht des Papsttums kennen gelernt. Er hat alles getan, um [E1] Eombes [/E1] am Bruch des Konkordates zu verhindern."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Émile Combes
    Description: französischer Politiker
    Born: ['+1835-09-06T00:00:00Z']
    Died: ['+1921-05-25T00:00:00Z', '+1921-05-24T00:00:00Z']
    Birth place: ['Roquecourbe']
    Death place: ['Q741626']
    Work locations: ['Q90']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "hat" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Er hat alles getan, um Eombes am Bruch des Konkordates zu verhindern."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 1.000

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Eombes' and 'Vatikan' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Eombes' near 'Vatikan' around 1938-05-20?
  4. Resolve temporal expressions relative to 1938-05-20. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 35:
  Publication date : 1981-11-17
  Language         : fr
  Person  : 'Melaine Favenncc'  (QID: N/A)
  Location: 'Montreux'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Club 24 Heures »-21.00, [E1] Melaine Favenncc [/E1]. Le Guet-21.00, Gilbert Savioz présente le peintre Dominko. [E2] Montreux [/E2]"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "présente" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Le Guet-21.00, Gilbert Savioz présente le peintre Dominko."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 10 (0 = most prominent)
    OCR quality estimate: 0.778

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Melaine Favenncc' and 'Montreux' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Melaine Favenncc' near 'Montreux' around 1981-11-17?
  4. Resolve temporal expressions relative to 1981-11-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 36:
  Publication date : 1981-05-13
  Language         : fr
  Person  : 'Ronald Reagan'  (QID: N/A)
  Location: 'Syrie'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Pourquoi [E2] Syrie [/E2]ns et Israéliens menacent-ils soudain de s'affronter dans une guerre risquant d'embraser tout le Proche-Orient ? La réponse est évidente : les deux capitales tentent désespéramment d'éveiller l'intérêt des Etats-Unis, et d'attirer ces derniers dans leur jeu respectif. Sur le mode : « Faites quelque chose, arrêteznous, ou nous ne répondons plus de rien ».Depuis l'élection de [E1] Ronald Reagan [/E1], les Américains ont montré les dispositions suivantes à l'égard du Proche-Orient : 1)"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Verb cluster: "montré" — tense=Past, aspect=None, mood=None
      Sentence: "Sur le mode : « Faites quelque chose, arrêteznous, ou nous ne répondons plus de rien ».Depuis l'élection de Ronald Reaga"
    Verb cluster: "menacent" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Pourquoi Syriens et Israéliens menacent-ils soudain de s'affronter dans une guerre risquant d'embraser tout le Proche-Or"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 11 (0 = most prominent)
    OCR quality estimate: 0.988

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Ronald Reagan' and 'Syrie' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Ronald Reagan' near 'Syrie' around 1981-05-13?
  4. Resolve temporal expressions relative to 1981-05-13. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 37:
  Publication date : 1868-02-19
  Language         : de
  Person  : 'Georg'  (QID: Q57428)
  Location: 'Holland'  (QID: Q102911)

  [ARTICLE TEXT — entity markers added]
  "Aufenthalt in Hietzing , die Regierung dann verpflichtet ſein wird , das Während die preußiſche Regierung dem früheren König von Hannover die größte und edelſte Rückſicht zu Theil werden läßt , während andererſeits ihre Fürſorge für die neue Provinz unter der be — des Königs [E1] Georg [/E1] und ſeiner Umgebung in Hietzing die verwerflichen Verſuche fortgeſetzt , einen Theil ſeiner früheren Unterthanen , meiſt aus den unterſten Ständen , für das völlige boffnungsloſe und thörichte Unternehmen einer Wiederherſtellung ſeines Thrones zu gewinnen . zwiſchen Deutſchland und Frankreich herbeizuführen drohete , ließ König Georg ſchluſſe an die Franzoſen gegen ihr Vaterland marſchiren ſollte . Als ſodann die luxemburgiſche Angelegenheit eine friedliche Löſung fand , begab ſich die in [E2] Holland [/E2] geſammelte Schaar von Hannoveranern nach der Schweiz , wo ſie in feſter militairiſcher Eintheilung verblieb und aus Mitteln des Königs Georg fort und fort ihren Unterhalt erhielt ."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Georg V. von Hannover
    Description: König von Hannover, Deutschland
    Born: ['+1819-05-27T00:00:00Z']
    Died: ['+1878-06-12T00:00:00Z']
    Birth place: ['Berlin']
    Death place: ['Paris']
    Work locations: ['Berlin', 'London', 'Hannover']
  Location Wikidata:
    Label: Holland
    Description: Region in den Niederlanden
    Country: ['Niederlande']
    Located in: ['Niederlande']
    Aliases: {'en': ['County of Holland', 'Holland, Netherlands', 'Province of Holland'], 'fr': ['Hollandaise', 'Hollande (région)']}
    Coordinates: [{'lat': 52.25, 'lon': 4.667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: früher, nach, früh
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Aufenthalt in Hietzing , die Regierung dann verpflichtet ſein wird , das Während die preußiſche Regierung dem früheren K"
    Verb cluster: "begab" — tense=Past, aspect=None, mood=Ind
      Sentence: "Als ſodann die luxemburgiſche Angelegenheit eine friedliche Löſung fand , begab ſich die in Holland geſammelte Schaar vo"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 29 (0 = most prominent)
    OCR quality estimate: 0.994

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Georg' and 'Holland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Georg' near 'Holland' around 1868-02-19?
  4. Resolve temporal expressions relative to 1868-02-19. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 38:
  Publication date : 1848-10-21
  Language         : de
  Person  : 'Radetzky'  (QID: Q153500)
  Location: 'Deutschland'  (QID: Q183)

  [ARTICLE TEXT — entity markers added]
  "Der gestern erwähnte Tagsbefehl [E1] Radetzky [/E1]'s lautet: „Soldaten! Ihr habt mich oft Euern Generalquartier Mailand, 12. Okt. Radetzky. [E2] Deutschland [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Josef Wenzel Radetzky von Radetz
    Description: österreichischer Feldmarschall böhmischer Herkunft (1766–1858)
    Born: ['+1766-11-02T00:00:00Z']
    Died: ['+1858-01-05T00:00:00Z']
    Birth place: ['Třebnice']
    Death place: ['Mailand']
    Work locations: ['Kaiserreich Österreich', 'Q81137', 'Österreich-Ungarn']
  Location Wikidata:
    Label: Deutschland
    Description: Staat in Mitteleuropa
    Country: ['Deutschland']
    Aliases: {'en': ['Federal Republic of Germany'], 'fr': ['RFA', "République fédérale d'Allemagne", 'République fédérale allemande', 'la République fédérale d’Allemagne', 'All.', 'R. F. A.'], 'de': ['Bundesrepublik Deutschland', 'BR Deutschland']}
    Coordinates: [{'lat': 51, 'lon': 10}, {'lat': 51.5, 'lon': 10.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: gestern
    Verb cluster: "lautet" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Der gestern erwähnte Tagsbefehl Radetzky's lautet: „Soldaten!"
    Verb cluster: "habt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Ihr habt mich oft Euern Generalquartier Mailand, 12. Okt. Radetzky."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Radetzky' and 'Deutschland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Radetzky' near 'Deutschland' around 1848-10-21?
  4. Resolve temporal expressions relative to 1848-10-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 39:
  Publication date : 1892-07-05
  Language         : de
  Person  : 'August Jabu'  (QID: N/A)
  Location: 'Fran öſiſcheſtraße'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "[E1] August Jabu [/E1] Jnbaber iſt der Kaufmann Max Franke zu Berlin . — rirma Friedländer . Freymark u . Co . , [E2] Fran öſiſcheſtraße [/E2] 60 / 61 ."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "öſiſcheſtraße" — tense=Pres, aspect=None, mood=Sub
      Sentence: ", Fran öſiſcheſtraße 60 / 61 ."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 104 (0 = most prominent)
    OCR quality estimate: 0.975

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'August Jabu' and 'Fran öſiſcheſtraße' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'August Jabu' near 'Fran öſiſcheſtraße' around 1892-07-05?
  4. Resolve temporal expressions relative to 1892-07-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 40:
  Publication date : 1930-07-11
  Language         : en
  Person  : 'the King'  (QID: N/A)
  Location: 'Rome'  (QID: Q220)

  [ARTICLE TEXT — entity markers added]
  "‘W. O.” MEETS OLD FRIEND IN ROME (Continued from Page One) bloodshed, he turned his army to the running of rail roads and fac tories that had been paralyzed by striking communists. And [E1] the King [/E1], beholding one mightier than him self in Italy, called Mussolini to his side."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Rome
    Description: capital and largest city of Italy
    Country: ['Italy', 'Papal States', 'Kingdom of Italy', 'Ostrogothic Kingdom', 'Byzantine Empire', 'Kingdom of Italy', 'Roman Kingdom', 'Roman Republic', 'Roman Empire', 'Western Roman Empire', 'Vatican City']
    Located in: ['Province of Rome', 'Papal States', 'Rome', 'Ancient Rome', 'Roman Republic', 'Roman Empire', 'Western Roman Empire', 'Metropolitan City of Rome', 'circle of Rome']
    Aliases: {'en': ['The Eternal City', 'Roma', 'Rome, Italy', 'City of Seven Hills'], 'fr': ['La ville éternelle', 'La ville aux sept collines', 'Roma', "l'Urbs"], 'de': ['Die Ewige Stadt', 'Roma'], 'lb': ['Roma', "D'Éiweg Stad"]}
    Coordinates: [{'lat': 41.893055555556, 'lon': 12.482777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "beholding" — tense=Pres, aspect=Prog, mood=None
      Sentence: "And the King, beholding one mightier than him self in Italy, called Mussolini to his side."
    Verb cluster: "turned" — tense=Past, aspect=None, mood=None
      Sentence: "‘W. O.” MEETS OLD FRIEND IN ROME (Continued from Page One) bloodshed, he turned his army to the running of rail roads an"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 1.000

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'the King' and 'Rome' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'the King' near 'Rome' around 1930-07-11?
  4. Resolve temporal expressions relative to 1930-07-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 41:
  Publication date : 1930-01-15
  Language         : fr
  Person  : 'Falconetti'  (QID: Q440600)
  Location: 'COM. CH. ELYSÉES'  (QID: Q726531)

  [ARTICLE TEXT — entity markers added]
  ", La rouille [E1] Falconetti [/E1]).BOUFFES-PARISIENS. 8 Relâche. COM."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: théâtre des Champs-Élysées
    Description: salle de spectacle du 8e arrondissement de Paris, inaugurée en 1913
    Country: ['Q142']
    Located in: ['Q3413229']
    Aliases: {'en': ['Theatre des Champs-Elysees'], 'fr': ['Theatre des Champs-Elysees'], 'de': ['Theatre des Champs-Elysees']}
    Coordinates: [{'lat': 48.865833333333335, 'lon': 2.3030555555555554}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 30 (0 = most prominent)
    OCR quality estimate: 0.824

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Falconetti' and 'COM. CH. ELYSÉES' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Falconetti' near 'COM. CH. ELYSÉES' around 1930-01-15?
  4. Resolve temporal expressions relative to 1930-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 42:
  Publication date : 1820-05-05
  Language         : en
  Person  : 'JOHN BINNS'  (QID: N/A)
  Location: 'Great Britain'  (QID: Q23666)

  [ARTICLE TEXT — entity markers added]
  "Sir Wiiliam Blackstono has collated and commented on it—his fine copy of Magna Charta has been excelled by later specimens of art, and the fac-similes of the seals and signatur e.diave made every reader of taste in [E2] Great Britain [/E2] acquainted, in some de gree, not merely with the state ofknowledge and of art at the period in question, but with the literary attainments, al>©, of King John, King Henry, and fbeir “ Barons bold.” Surely the Declaration of American Inde pendence is, at least, as well entitled to the decorations of art as the Magna. As no more of those copies will be printed than 'ball be subscribed for, gentlemen who wish for them, are requested to add the word “ colored ” to their subscription. [E1] JOHN BINNS [/E1], Chesnut-street, Philadelphia."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Great Britain
    Description: island in the North Atlantic Ocean off the northwest coast of continental Europe
    Country: ['United Kingdom']
    Aliases: {'en': ['Gt. Brit', 'GB', 'Blighty', 'Albion', 'Britannia', 'GBR', 'mainland Britain', 'Britain'], 'fr': ['G-B', 'Grande Bretagne', 'G.-B.', 'île de Bretagne'], 'de': ['GB-GBN', 'Grossbritannien']}
    Coordinates: [{'lat': 53.833333333333, 'lon': -2.4166666666667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now, late, later
    Verb cluster: "are requested" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "As no more of those copies will be printed than 'ball be subscribed for, gentlemen who wish for them, are requested to a"
    Verb cluster: "has been excelled" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "Sir Wiiliam Blackstono has collated and commented on it—his fine copy of Magna Charta has been excelled by later specime"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 14 (0 = most prominent)
    OCR quality estimate: 0.999

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'JOHN BINNS' and 'Great Britain' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'JOHN BINNS' near 'Great Britain' around 1820-05-05?
  4. Resolve temporal expressions relative to 1820-05-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 43:
  Publication date : 1840-04-18
  Language         : en
  Person  : 'Mr. Van Buren'  (QID: Q11820)
  Location: 'the United\nStates'  (QID: Q30)

  [ARTICLE TEXT — entity markers added]
  "The term Democrat, which they have always ridiculed, and abused because it i 3 every where claimed by][E1] Mr. Van Buren [/E1]’s and Gen. Jackson's friends; this heretofore odious name of the friends of popular rights, those candid federal whigs now take up and claim as their own. Federal Wlilggery ashamed of Its name! "NVe see in an opposition paper, a whig address from Baltimore, to “the young men of the United States,” headed “your DEMOCRATIC Harrison brethren of Baltimore send you this address, greet ing.”"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Martin Van Buren
    Description: president of the United States from 1837 to 1841
    Born: ['+1782-12-05T00:00:00Z']
    Died: ['+1862-07-24T00:00:00Z']
    Birth place: ['Kinderhook']
    Death place: ['Kinderhook']
    Work locations: ['Washington, D.C.']
  Location Wikidata:
    Label: United States
    Description: country located primarily in North America
    Country: ['United States']
    Aliases: {'en': ['the States', 'the United States of America', 'US of America', 'the US', 'the U.S.', 'the US of A', 'U.S. of America', 'the US of America', 'the USA', 'the U.S.A.', 'the U.S. of A', 'US of A', 'the U.S. of America', 'the United States', 'Merica', 'Murica', 'United States of America', 'U.S.', 'U.S.A.', 'U. S.', 'U. S. A.', 'America'], 'fr': ['É.-U.', 'É-U', 'É-U.', 'E.-U.', 'É.U.', 'les États', 'Oncle Sam', 'Amérique', 'Etats-Unis', 'States', 'les États-Unis d’Amérique', 'États-unis', 'ÉU', 'É.-U. A.', "Pays de l'Oncle Sam", 'Etats-unis', 'États-Unis d’Amérique', 'pays de l’Oncle Sam'], 'de': ['Vereinigte Staaten von Amerika', 'US-Amerika', 'U.S.-Amerika', 'Staaten von Amerika', 'VSA', 'V.S.A.', 'V. S. A.', 'Staaten', 'die Staaten', 'VS', 'V.S.', 'V. S.', 'Amerika', 'U.S.A.', 'U. S. A.', 'United States of America', 'United States', 'U.S.', 'U. S.', 'America'], 'lb': ['Vereenegt Staaten']}
    Coordinates: [{'lat': 39.828175, 'lon': -98.5795}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now
    Verb cluster: "have ridiculed" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "The term Democrat, which they have always ridiculed, and abused because it i 3 every where claimed by]Mr."
    Verb cluster: "headed" — tense=Past, aspect=None, mood=None
      Sentence: ""NVe see in an opposition paper, a whig address from Baltimore, to “the young men of the United States,” headed “your DE"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mr. Van Buren' and 'the United\nStates' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mr. Van Buren' near 'the United\nStates' around 1840-04-18?
  4. Resolve temporal expressions relative to 1840-04-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 44:
  Publication date : 1920-07-08
  Language         : en
  Person  : 'Bood Choat'  (QID: N/A)
  Location: 'Cookeville'  (QID: Q2456192)

  [ARTICLE TEXT — entity markers added]
  "RAWLEY AGAIN Haven’t b en satisfied since I left [E2] Cookeville [/E2] until now. I seemed like I was almost lost, as I stayed in Gainesboro about IS months or 2 years. He treats all alike. Bill Dabbs and [E1] Bood Choat [/E1] are the night police."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Cookeville
    Description: city in Tennessee, United States
    Country: ['United States']
    Located in: ['Putnam County']
    Aliases: {'en': ['Cookeville, Tennessee', 'Cookeville, TN']}
    Coordinates: [{'lat': 36.164202, 'lon': -85.504295}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now
    Verb cluster: "are" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Bill Dabbs and Bood Choat are the night police."
    Verb cluster: "Have" — tense=Pres, aspect=None, mood=Ind
      Sentence: "RAWLEY AGAIN Haven’t b en satisfied since I left Cookeville until now."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 42 (0 = most prominent)
    OCR quality estimate: 0.993

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Bood Choat' and 'Cookeville' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Bood Choat' near 'Cookeville' around 1920-07-08?
  4. Resolve temporal expressions relative to 1920-07-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 45:
  Publication date : 1790-05-29
  Language         : en
  Person  : 'Hon. Peter Sylvester'  (QID: Q2078354)
  Location: 'Callicut,'  (QID: Q28729)

  [ARTICLE TEXT — entity markers added]
  "The Ship Harmony Capt. IVillet is arrived at Philadelphia from Bengal.—Accounts from the Eaft-Indies State—there is a mod plealing pro- fpeft of a plentiful harveft in that pare of the world—that Cotton has fold fo low as 11 Tales in China—that the Englifli/ fettlements enjoy a profound peace—that the greateft part of trea- fure on board the Vanfittart one of the Eaft-In- idea company’s Ships lately loft, had been re covered from the wreck—that the ffiip Durham Capt. Kepling ; and another fhip were loft in a gale of wind, foundering in the road—that Tippoo Sultan to puQjfh the faults of fome of the tributary Princes had depopulated and laid wafte their country from Belipatain to [E2] Callicut, [/E2] an ex tent of 80 or 90 miles, where the latepoffeflors of its fields and habitations arefeen no more. The Hon."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Peter Silvester
    Description: American politician
    Born: ['+1734-01-01T00:00:00Z']
    Died: ['+1808-10-21T00:00:00Z', '+1808-10-15T00:00:00Z']
    Birth place: ['Shelter Island']
    Death place: ['Columbia County']
    Work locations: ['Washington, D.C.']
  Location Wikidata:
    Label: Kozhikode
    Description: city in Kerala, India
    Country: ['India', 'Portuguese Empire']
    Located in: ['Kozhikode district', 'Malabar District']
    Aliases: {'en': ['Calicut'], 'fr': ['Kozhikode'], 'de': ['Kalikut', 'Calicut']}
    Coordinates: [{'lat': 11.247777777777777, 'lon': 75.78027777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: late
    Verb cluster: "is" — tense=Pres, aspect=None, mood=Ind
      Sentence: "IVillet is arrived at Philadelphia from Bengal.—Accounts from the Eaft-Indies State—there is a mod plealing pro- fpeft o"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Hon. Peter Sylvester' and 'Callicut,' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Hon. Peter Sylvester' near 'Callicut,' around 1790-05-29?
  4. Resolve temporal expressions relative to 1790-05-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 46:
  Publication date : 1938-05-06
  Language         : de
  Person  : 'neuen deutschen Botschafter, Dr. Herbert von\nDirksen'  (QID: Q213954)
  Location: 'London'  (QID: Q84)

  [ARTICLE TEXT — entity markers added]
  "Außenpolitischer Nachtrag [E2] London [/E2], 5. Mai. König Georg VI. empfing am Donnerstag im Buckinghampalast ben neuen deutschen Botschafter, Dr. Herbert von Dirksen, ber ihm sein Beglaubigungsschreiben unb"

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: London
    Description: Hauptstadt und bevölkerungsreichste Stadt des Vereinigten Königreichs
    Country: ['Römisches Kaiserreich', 'Königreich Essex', 'Mercia', 'Königreich Wessex', 'Königreich England', 'Königreich Großbritannien', 'Q174193', 'Vereinigtes Königreich']
    Located in: ['Königreich Wessex', 'Königreich England', 'England', 'County of London', 'Groß-London']
    Aliases: {'en': ['London, UK', 'London, United Kingdom', 'London, England', 'London UK', 'London U.K.', 'Londinium', 'Loñ', 'Lundenwic', 'Londinio', 'Londini', 'Londiniensium', 'Augusta', 'Trinovantum', 'Kaerlud', 'Karelundein', 'Lunden', 'Big Smoke', 'the Big Smoke', 'Lundenburh', 'Lundenburgh', 'Llyn Dain', 'Llan Dian', 'Londinion', 'Loniniensi', 'Lon.', 'Loñ.', 'Lond.', 'LDN'], 'fr': ['London']}
    Coordinates: [{'lat': 51.507222222222, 'lon': -0.1275}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach
    Verb cluster: "empfing" — tense=Past, aspect=None, mood=Ind
      Sentence: "empfing am Donnerstag im Buckinghampalast ben neuen deutschen Botschafter, Dr. Herbert von Dirksen, ber ihm sein Beglaub"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.971

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'neuen deutschen Botschafter, Dr. Herbert von\nDirksen' and 'London' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'neuen deutschen Botschafter, Dr. Herbert von\nDirksen' near 'London' around 1938-05-06?
  4. Resolve temporal expressions relative to 1938-05-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 47:
  Publication date : 1826-08-22
  Language         : fr
  Person  : 'M. le prince de Metternicli'  (QID: N/A)
  Location: 'Sardaigne'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "NOUVELLES DIVERSES.Le toi de [E2] Sardaigne [/E2] à refusé toute espèce de garde d'honneur pendant son séjour en Savoye. S. M. n'a d'ailleurs amené avec elle de Turin que quannte gardes-du-corps. On présume qu'immédiatement après les fêtes religieuses d'Annecy, qui ont dû commencer le 16 août, LL.MM. se rendront à Moutiers en Tarentaise. Des lettres de Mayence, que'nous recevons aujourd'hui', annoncent que [E1] M. le prince de Metternicli [/E1] est arrivé le 12 août à Johannisberg."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: aujourd'hui, après
    Verb cluster: "annoncent" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Des lettres de Mayence, que'nous recevons aujourd'hui', annoncent que M. le prince de Metternicli est arrivé le 12 août "
    Verb cluster: "refusé" — tense=Past, aspect=None, mood=None
      Sentence: "NOUVELLES DIVERSES.Le toi de Sardaigne à refusé toute espèce de garde d'honneur pendant son séjour en Savoye."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 1 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. le prince de Metternicli' and 'Sardaigne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. le prince de Metternicli' near 'Sardaigne' around 1826-08-22?
  4. Resolve temporal expressions relative to 1826-08-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 48:
  Publication date : 1948-05-04
  Language         : de
  Person  : 'Philip Kaiser'  (QID: Q3379042)
  Location: 'Europas'  (QID: Q46)

  [ARTICLE TEXT — entity markers added]
  "Der stellvertretende Arbeitsminister David Morse legte in einer Pressekonferenz gestern einen Bericht vor, den [E1] Philip Kaiser [/E1], Leiter der Abteilung für internationale Angelegenheiten im Arbeitsministerium, über die Arbeitsverhältnisse in Europa verfaßt hat. Kaiser, der mehrere Monate zu Studienzwecken in Europa verbrachte, trifft in seinem Bericht die Feststellung, daß nach allgemeiner Auffassung der zuständigen europäischen Stellen die höchstmögliche Steigerung der Produktion wichtiger als Hilfsmaßnahmen sei, um Europa wieder auf eigene Füße zu stellen. Die Verhandlungen mit anderen Nationen im Rahmen des hierfür erlassenen Gesetzes seien eng mit der Verwirklichung des - europäischen Wiederaufbauprogramms verknüpft. Auf diese Weise würden die Vorteile, die sich aus dem europäischen Wiederaufbauprogramm ergeben, den Farmern, Arbeitern und Geschäftsleuten der Vereinigten Staaten ebenso zugute kommen wie denjenigen [E2] Europas [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Philip Mayer Kaiser
    Description: US-amerikanischer Regierungsbeamter, Hochschullehrer und Diplomat
    Born: ['+1913-07-12T00:00:00Z']
    Died: ['+2007-05-24T00:00:00Z']
    Birth place: ['Q18419']
    Death place: ['Q61']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: gestern, nach, vor
    Verb cluster: "legte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Der stellvertretende Arbeitsminister David Morse legte in einer Pressekonferenz gestern einen Bericht vor, den Philip Ka"
    Verb cluster: "würden" — tense=Past, aspect=None, mood=Sub
      Sentence: "Auf diese Weise würden die Vorteile, die sich aus dem europäischen Wiederaufbauprogramm ergeben, den Farmern, Arbeitern "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Philip Kaiser' and 'Europas' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Philip Kaiser' near 'Europas' around 1948-05-04?
  4. Resolve temporal expressions relative to 1948-05-04. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 49:
  Publication date : 1921-02-22
  Language         : fr
  Person  : 'M. Ernest Ansemiet'  (QID: N/A)
  Location: 'Gourgas'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "fants rralades du chemin [E2] Gourgas [/E2] et ils espèrent que le pub'ic leur peimettra, en occupant toutes les. places de la salle de là Réforrra'lon. d'apporter. un soulagement aux charges très, fortes q'ni in *. combeni, à cette'institution si utile et si 'di £ ne d'yîpuiConcerts annoncés Jeudi 24 février, 20 h.30, salle de la Réformation, treizième concert populaire de l'Orchestre de la Suisse romande, sous la direction de [E1] M. Ernest Ansemiet [/E1] et avec le concours de M. More !, violoncelliste."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "annoncés" — tense=Past, aspect=None, mood=None
      Sentence: "combeni, à cette'institution si utile et si 'di £ ne d'yîpuiConcerts annoncés Jeudi 24 février, 20 h.30, salle de la Réf"
    Verb cluster: "espèrent" — tense=Pres, aspect=None, mood=Ind
      Sentence: "fants rralades du chemin Gourgas et ils espèrent que le pub'ic leur peimettra, en occupant toutes les. places de la sall"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 38 (0 = most prominent)
    OCR quality estimate: 0.932

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Ernest Ansemiet' and 'Gourgas' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Ernest Ansemiet' near 'Gourgas' around 1921-02-22?
  4. Resolve temporal expressions relative to 1921-02-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 50:
  Publication date : 1928-10-25
  Language         : fr
  Person  : 'M. de Rabours'  (QID: N/A)
  Location: 'canton de Vaud'  (QID: Q12771)

  [ARTICLE TEXT — entity markers added]
  "Les choses semblent devoir se passer beau coup plus calmement dans le [E2] canton de Vaud [/E2], où aucun changement notable n'est prévu, et à Genève, où l'on s'attend généralement à un déchet démocrate en faveur du parti de défense économique. C'est [E1] M. de Rabours [/E1] que tous livrent d'avance au fatal couperet de la guillotine sèche."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: canton de Vaud
    Description: canton de la Suisse
    Country: ['Suisse']
    Located in: ['Suisse']
    Aliases: {'en': ['VD', 'Vaud', 'Canton Vaud'], 'fr': ['Vaud', 'VD', 'État de Vaud'], 'de': ['Waadt', 'VD', 'Vaud'], 'lb': ['Kanton Vaud', 'VD', 'Kanton Waadt']}
    Coordinates: [{'lat': 46.6, 'lon': 6.55}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Verb cluster: "est M." — tense=Pres, aspect=None, mood=Ind
      Sentence: "C'est M. de Rabours que tous livrent d'avance au fatal couperet de la guillotine sèche."
    Verb cluster: "semblent" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Les choses semblent devoir se passer beau coup plus calmement dans le canton de Vaud, où aucun changement notable n'est "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 16 (0 = most prominent)
    OCR quality estimate: 0.982

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. de Rabours' and 'canton de Vaud' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. de Rabours' near 'canton de Vaud' around 1928-10-25?
  4. Resolve temporal expressions relative to 1928-10-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 51:
  Publication date : 1920-04-22
  Language         : en
  Person  : 'Tiui Apple'  (QID: N/A)
  Location: 'GAINESBORO'  (QID: Q2057053)

  [ARTICLE TEXT — entity markers added]
  "[E2] GAINESBORO [/E2], ROUTE 3 Reckon [E1] Tiui Apple [/E1] Is still living as I beard him the other night talk ing to some one about a law suit. Old Tim is a good lawyer and a hustler in the courts. I am glad of that. I guess I had better wind up by saying, Ralph Wirt, you will please send me the Putnam County Herald three months, Gainesboro, Tenn., R. 3, as the Herald is a hustling paper and the men who run it are, too."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Gainesboro
    Description: town in Tennessee, United States
    Country: ['United States']
    Located in: ['Jackson County']
    Aliases: {'en': ['Gainesboro, Tennessee', 'Gainesboro, Tenn.', 'Gainesboro, TN']}
    Coordinates: [{'lat': 36.359722222222, 'lon': -85.654722222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "Is living" — tense=Pres, aspect=Prog, mood=Ind
      Sentence: "GAINESBORO, ROUTE 3 Reckon Tiui Apple Is still living as I beard him the other night talk ing to some one about a law su"
    Verb cluster: "guess" — tense=Pres, aspect=None, mood=None
      Sentence: "I guess I had better wind up by saying, Ralph Wirt, you will please send me the Putnam County Herald three months, Gaine"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.992

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Tiui Apple' and 'GAINESBORO' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Tiui Apple' near 'GAINESBORO' around 1920-04-22?
  4. Resolve temporal expressions relative to 1920-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 52:
  Publication date : 1878-02-06
  Language         : de
  Person  : 'Mehemed Ali Pascha'  (QID: Q66452)
  Location: 'Konstantinopel'  (QID: Q16869)

  [ARTICLE TEXT — entity markers added]
  "Von dem Augenblick an, wo die Russen [E2] Konstantinopel [/E2] und die Dardanellenstraße nicht mehr direkt bedrohen, wird das englische Kabinet sich be friedigt erklären. Wer weiß, ob die Nachricht vom Abschluß des Waffenstillstandes nicht die Autorität der Regierung in der Diskussion der Supplementar kredite schwächt? Die türkische Verwaltung von Epirus und Thessalien bereitet sich auf energischen Widerstand vor, und wie aus Konstantinopel ge meldet wird, hat auch der türkische Admiral Ho bart Pascha Befehl erhalten, sich zur Abfahrt be reit zu halten, wie man glaubt, nach dem Piräus. — [E1] Mehemed Ali Pascha [/E1] ist zum Kommandanten, Adaisildes (ein Christ) zum Gouverneur von Kreta ernannt worden."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Mehmed Ali Pascha
    Description: osmanischer Feldmarschall deutscher Herkunft
    Born: ['+1827-11-18T00:00:00Z']
    Died: ['+1878-09-07T00:00:00Z']
    Birth place: ['Q1733']
    Death place: ['Q474651']
  Location Wikidata:
    Label: Konstantinopel
    Description: früherer Name des heutigen Istanbul
    Country: ['Byzantinisches Reich', 'Q178897', 'Q1747689', 'Osmanisches Reich', 'Q43']
    Aliases: {'en': ['Constantinopolis', "The City of the World's Desire", 'Tsarigrad', 'Tsargorod', 'Czargrad', 'Tzargrad'], 'fr': ['Constantinopolis'], 'de': ['Dersaadet', 'Carigrad', 'Zarigrad', 'Constantinopel', 'Konstantinoupolis', 'Kostantiniyye', 'Theodosius']}
    Coordinates: [{'lat': 41.0125, 'lon': 28.98}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nicht mehr, nach, vor
    Verb cluster: "ist" — tense=Pres, aspect=None, mood=Ind
      Sentence: "— Mehemed Ali Pascha ist zum Kommandanten, Adaisildes (ein Christ) zum Gouverneur von Kreta ernannt worden."
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Von dem Augenblick an, wo die Russen Konstantinopel und die Dardanellenstraße nicht mehr direkt bedrohen, wird das engli"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 36 (0 = most prominent)
    OCR quality estimate: 0.999

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mehemed Ali Pascha' and 'Konstantinopel' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mehemed Ali Pascha' near 'Konstantinopel' around 1878-02-06?
  4. Resolve temporal expressions relative to 1878-02-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 53:
  Publication date : 1978-09-27
  Language         : fr
  Person  : 'Heighway'  (QID: Q1370340)
  Location: 'Liverpool'  (QID: Q24826)

  [ARTICLE TEXT — entity markers added]
  "Le règne de [E2] Liverpool [/E2] se terminern-t-il ce soir ? La période de domination de Liverpool en coupe d'Europe des clubs champions pourrait se terminer ce soir, à I'Anfield Road, quand les champions de 1977 et 1978, recevront Nottingham Forest, champion d'Angleterre, en match retour du premier tour de cette compétition. Les défenseurs de l'équipe d'Angleterre, Phil Neal et Emlyn Hughes, et l'ailier Steve Heigh way (Eire) ont perdS la forme. Les deux premiers ont été décevants contre le Danemark, la semaine dernière, à Copenhague, et [E1] Heighway [/E1] a été remplacé aussi bien contre l'Irlande, à Dublin, que contre West Bromwich Albion, samedi dernier."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Steve Heighway
    Description: footballeur irlandais
    Born: ['+1947-11-25T00:00:00Z']
    Birth place: ['Dublin']
  Location Wikidata:
    Label: Liverpool
    Description: ville en Angleterre, Royaume-Uni
    Country: ['Q145']
    Located in: ['Q21665571', 'district métropolitain de Liverpool', 'district métropolitain de Liverpool']
    Aliases: {'en': ['City of Liverpool', 'Liverpool, Merseyside', 'Liverpool, UK', 'Liverpool, England'], 'de': ['Liverpudlian']}
    Coordinates: [{'lat': 53.407222222222224, 'lon': -2.9916666666666667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1977" → 1977
      - "1978" → 1978
    Verb cluster: "décevants" — tense=Past, aspect=None, mood=None
      Sentence: "Les deux premiers ont été décevants contre le Danemark, la semaine dernière, à Copenhague, et Heighway a été remplacé au"
    Verb cluster: "ont" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Les défenseurs de l'équipe d'Angleterre, Phil Neal et Emlyn Hughes, et l'ailier Steve Heigh way (Eire) ont perdS la form"
    Verb cluster: "terminern" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Le règne de Liverpool se terminern-t-il ce soir ?"
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    Entity sentence position in article: 12 (0 = most prominent)
    OCR quality estimate: 0.979

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Heighway' and 'Liverpool' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Heighway' near 'Liverpool' around 1978-09-27?
  4. Resolve temporal expressions relative to 1978-09-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 54:
  Publication date : 1928-10-25
  Language         : fr
  Person  : 'Marx'  (QID: Q9061)
  Location: 'Saint-Gall'  (QID: Q25607)

  [ARTICLE TEXT — entity markers added]
  "On escompte ,, soit une avance radicale à Berne, Zurich, [E2] Saint-Gall [/E2], Grisons, soit une avance conservatrice à Zurich, Schwytz, peut-être Saint-Gall et peutêtre Valais. Quel que soit le succès de la liste socialiste, on s'accorde généralement à prévoir qu'il ne suffira pas à procurer aux disciples dé [E1] Marx [/E1] le gros succès moral de conquérir la majorité relative au Parlement."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Karl Marx
    Description: philosophe, sociologue et économiste allemand
    Born: ['+1818-05-05T00:00:00Z']
    Died: ['+1883-03-14T00:00:00Z']
    Birth place: ['Trèves']
    Death place: ['Londres']
    Residences: ['Londres', 'Trèves', 'Berlin', 'Paris', 'Le Cygne', 'Berlin', 'Berlin']
    Work locations: ['Cologne']
  Location Wikidata:
    Label: Saint-Gall
    Description: ville suisse et chef-lieu du canton de Saint-Gall
    Country: ['Suisse']
    Located in: ['district de Saint-Gall']
    Aliases: {'en': ['St. Gall', 'Saint Gall', 'Saint Gallen', 'Sankt Gallen', 'St. Gallen SG'], 'fr': ['St-Gall', 'St. Gallen', 'Sankt Gallen'], 'de': ['St.Gallen', 'Stadt St. Gallen', 'St-Gall', 'Gallusstadt', 'Sankt Gallen', 'Stadt St.Gallen']}
    Coordinates: [{'lat': 47.423333333333, 'lon': 9.3772222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "accorde" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Quel que soit le succès de la liste socialiste, on s'accorde généralement à prévoir qu'il ne suffira pas à procurer aux "
    Verb cluster: "peutêtre" — tense=Pres, aspect=None, mood=None
      Sentence: "On escompte ,, soit une avance radicale à Berne, Zurich, Saint-Gall, Grisons, soit une avance conservatrice à Zurich, Sc"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 4 (0 = most prominent)
    OCR quality estimate: 0.982

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Marx' and 'Saint-Gall' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Marx' near 'Saint-Gall' around 1928-10-25?
  4. Resolve temporal expressions relative to 1928-10-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 55:
  Publication date : 1890-09-25
  Language         : en
  Person  : 'M. Pliillippe de Ferrari'  (QID: Q44105)
  Location: 'Paris'  (QID: Q90)

  [ARTICLE TEXT — entity markers added]
  "[E1] M. Pliillippe de Ferrari [/E1] perhaps has the largest and most valuable collec tion of stamps in the world, amount ing to something like 2ft0,000, and within tbe present year he solJ one little stamp to a collector in [E2] Paris [/E2] for 150.000."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Philipp von Ferrary
    Description: French philatelist, owner of the world's largest stamp collection (1850–1917)
    Born: ['+1850-01-11T00:00:00Z']
    Died: ['+1917-05-20T00:00:00Z']
    Birth place: ['Paris']
    Death place: ['Lausanne']
    Residences: ['Hôtel Matignon']
  Location Wikidata:
    Label: Paris
    Description: capital and most populous city in France
    Country: ['France', 'Kingdom of France', 'Francia', 'German military administration in occupied France during World War II', 'France', 'First French Empire', 'French First Republic']
    Located in: ['Grand Paris', 'Île-de-France', 'Kingdom of France', 'arrondissement of Paris', 'Seine', 'Paris Department']
    Aliases: {'en': ['City of Light', 'City of Love', 'Lutetia'], 'fr': ['Ville-Lumière', 'Paname', 'Lutèce', "Ville de l'Amour", 'FR-75', 'Pantruche', 'Ville de Paris']}
    Coordinates: [{'lat': 48.85666666666667, 'lon': 2.352222222222222}]
  Known person–location links: {"birth_place": "P19"}

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "has" — tense=Pres, aspect=None, mood=Ind
      Sentence: "M. Pliillippe de Ferrari perhaps has the largest and most valuable collec tion of stamps in the world, amount ing to som"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.945

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Pliillippe de Ferrari' and 'Paris' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Pliillippe de Ferrari' near 'Paris' around 1890-09-25?
  4. Resolve temporal expressions relative to 1890-09-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 56:
  Publication date : 1810-04-07
  Language         : en
  Person  : 'Capt. Burger'  (QID: N/A)
  Location: 'Lisbon'  (QID: Q597)

  [ARTICLE TEXT — entity markers added]
  "[E1] Capt. Burger [/E1], osthe ship John and Ed- ward, left [E2] Lisbon [/E2] on the 5ih."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Lisbon
    Description: municipality and capital city of Portugal
    Country: ['Portugal', 'Roman Republic', 'Kingdom of the Suebi', 'Visigothic Kingdom', 'Umayyad Caliphate', 'emirate of Córdoba', 'Caliphate of Córdoba', 'Taifa of Badajoz', 'Taifa of Lisbon', 'Taifa of Badajoz', 'Almoravid dynasty']
    Located in: ['Lisbon', 'Grande Lisboa Subregion']
    Aliases: {'en': ['Lisboa'], 'fr': ['Lisboa'], 'de': ['Lisboa']}
    Coordinates: [{'lat': 38.708042, 'lon': -9.139016}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "left" — tense=Past, aspect=None, mood=None
      Sentence: "Capt. Burger, osthe ship John and Ed- ward, left Lisbon on the 5ih."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.947

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Capt. Burger' and 'Lisbon' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Capt. Burger' near 'Lisbon' around 1810-04-07?
  4. Resolve temporal expressions relative to 1810-04-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 57:
  Publication date : 1886-06-22
  Language         : de
  Person  : 'Lüderitz'  (QID: Q77340)
  Location: 'Togo⸗'  (QID: Q161062)

  [ARTICLE TEXT — entity markers added]
  "Juni ſind es zwei Jahre , daß der Reichskanzler Fürſt Bismarck bei Gelegenheit der Berathung der damals eingebrachten erſten Poſt⸗ Dampfervorlage der Budgetcommiſſion di Mittheilung machte , daß die [E1] Lüderitz [/E1] 'ſchen Erwerbungen in Südafrika ohne Widerſpruch Englands unter deutſchen Schutz geſtellt ſeien . Sieht man ab von den mühevollen diplomatiſchen Vorverhandlungen , welche den Zweck hatten , England zum Aufgeben ſeines Widerſpruchs gegen die erſten colonialen Unternehmungen Deutſchlands zu veranlaſſen , ſo kann der 28 . Geſtützt durch das Vertrauen der Nation , das ſich in zahlloſen Zuſtimmungserklärungen wie auch in der Stimmung der Wählerſchaft kundgab , verfolgte der Kanzler mit Feſtigkeit und Thatkraft das von ihm ins Auge gefaßte Ziel , einerſeits dem deutſchen Unternehmungsgeiſt nachgehend und den Anträgen auf Uebernahme der Schutzherrlichkeit , wo es angemeſſen erſchien , nachgebend , andererſeits die berechtigten Jntereſſen anderer europäiſcher Staaten mit Sorgfalt berückſichtigend , unberechtigten Anſprüchen aber auf diplomatiſchem Wege mit Entſchiedenheit und Erfolg entgegentretend . Unſere Flagge weht im [E2] Togo⸗ [/E2] und Kamerungebiet , deren Verwaltung von kaiſerlichen Beamten in die Hand genommen werden mußte ;"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Adolf Lüderitz
    Description: deutscher Großkaufmann und Begründer der Kolonie Deutsch-Südwestafrika
    Born: ['+1834-07-16T00:00:00Z']
    Died: ['+1886-10-00T00:00:00Z', '+1886-10-24T00:00:00Z']
    Birth place: ['Bremen']
    Death place: ['Oranje']
    Work locations: ['Deutsch-Südwestafrika']
  Location Wikidata:
    Label: Togo
    Description: ehemalige deutsche Kolonie in Westafrika
    Country: ['Q43287']
    Aliases: {'en': ['Togo'], 'fr': ['Togo'], 'de': ['Deutsch-Togo', 'Togoland', 'Togogebiet']}
    Coordinates: [{'lat': 6.272, 'lon': 1.187}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Verb cluster: "ſind" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Juni ſind es zwei Jahre , daß der Reichskanzler Fürſt Bismarck bei Gelegenheit der Berathung der damals eingebrachten er"
    Verb cluster: "weht" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Unſere Flagge weht im Togo⸗ und Kamerungebiet , deren Verwaltung von kaiſerlichen Beamten in die Hand genommen werden mu"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 27 (0 = most prominent)
    OCR quality estimate: 0.993

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Lüderitz' and 'Togo⸗' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Lüderitz' near 'Togo⸗' around 1886-06-22?
  4. Resolve temporal expressions relative to 1886-06-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 58:
  Publication date : 1868-02-17
  Language         : de
  Person  : 'Deputirten Mellana'  (QID: N/A)
  Location: 'Amerika'  (QID: Q828)

  [ARTICLE TEXT — entity markers added]
  "Einmal wird von Nordamerika Entschädigung verlangt für die nordischen Kauffahrer, welche von den in England ge kauften und bewaffneten Korsaren wie Alabama, Georgia, Florida, Sumter u. s. w. während dem Bürgerkrieg ge kapert und verbrannt worden sind. Dann wird aber England auch der Verletzung des Völkerrechts beschul digt, indem es in seinen Häfen die Ausrüstung von sonderbündischen Kaperschiffen zugelassen hat. Von ganz besonderer Bedeutung ist die letzten Samstag in der N. Z. Ztg. erschienene Bundesstadt-Korrespondenz, durch welche die Angabe des Lieutenant v. Tschirschnitz, als ob die Han noveraner durch preußischen Einfluß aus der Schweiz verdrängt worden seien, als durch und durch unbegrün det nachgewiesen wird. Der Antrag des [E1] Deputirten Mellana [/E1], das Militär büdget von 162 Millionen auf 142 zu reduziren, wurde verworfen."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Amerika
    Description: Doppelkontinent, bestehend aus Nord- und Südamerika
    Aliases: {'en': ['America', 'North, Central, and South America', 'the New World', 'the Americas', 'American continent', 'North and South America'], 'fr': ['Amériques', 'les Amériques', 'continent américain'], 'de': ['Amerikas', 'America', 'Neue Welt', 'amerikanischer Doppelkontinent']}
    Coordinates: [{'lat': 19, 'lon': -96}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach
    Verb cluster: "wurde" — tense=Past, aspect=None, mood=Ind
      Sentence: "Der Antrag des Deputirten Mellana, das Militär büdget von 162 Millionen auf 142 zu reduziren, wurde verworfen."
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Einmal wird von Nordamerika Entschädigung verlangt für die nordischen Kauffahrer, welche von den in England ge kauften u"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 19 (0 = most prominent)
    OCR quality estimate: 0.975

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Deputirten Mellana' and 'Amerika' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Deputirten Mellana' near 'Amerika' around 1868-02-17?
  4. Resolve temporal expressions relative to 1868-02-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 59:
  Publication date : 1908-09-15
  Language         : de
  Person  : 'Fräulein Josephine Zapf'  (QID: N/A)
  Location: 'Schloß Güttingen'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Im [E2] Schloß Güttingen [/E2] lebte ein Sonderling, der Berner Albert Rätzer, der ein arbeitreiches Leben als Privatier beschließen wollte, in Wirklichkeit sich aber den Lebensabend durch allerlei eingebildete Schikanen ver bitterte. Diesen Rätzer fand sein Dienstpersonal am Nach mittag des 11. Septembers 1907 im Treppenhaus in den letzten Zügen liegend; Dabei war der Schloßbesitzer „verunglückt": Dr. Meier und Fräulein Zapf aber waren spurlos ver schwunden. In einer Villa in Thielle, Kanton Neuenburg, lebte ein Dr. Meier mit seiner Mutter Witwe Meier und einer Haushälterin Josephine Zapf."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1907" → 1907
    Temporal signal words: nach
    Verb cluster: "lebte" — tense=Past, aspect=None, mood=Ind
      Sentence: "In einer Villa in Thielle, Kanton Neuenburg, lebte ein Dr. Meier mit seiner Mutter Witwe Meier und einer Haushälterin Jo"
    Verb cluster: "lebte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Im Schloß Güttingen lebte ein Sonderling, der Berner Albert Rätzer, der ein arbeitreiches Leben als Privatier beschließe"
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    Entity sentence position in article: 8 (0 = most prominent)
    OCR quality estimate: 0.981

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Fräulein Josephine Zapf' and 'Schloß Güttingen' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Fräulein Josephine Zapf' near 'Schloß Güttingen' around 1908-09-15?
  4. Resolve temporal expressions relative to 1908-09-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 60:
  Publication date : 1820-09-09
  Language         : en
  Person  : 'Governor Lloyd'  (QID: N/A)
  Location: 'United States'  (QID: Q30)

  [ARTICLE TEXT — entity markers added]
  "and that it is not on ieserving the encou ragementof the Agriculturists of the Unit ;d States, the following testimonials are respect fully submitted—others equally conclusive, might be offered. Extract of a letter from [E1] Governor Lloyd [/E1], »• ho is acknowledged to be one of the most wealthy, well informed and best managing farmers in the [E2] United States [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: United States
    Description: country located primarily in North America
    Country: ['United States']
    Aliases: {'en': ['the States', 'the United States of America', 'US of America', 'the US', 'the U.S.', 'the US of A', 'U.S. of America', 'the US of America', 'the USA', 'the U.S.A.', 'the U.S. of A', 'US of A', 'the U.S. of America', 'the United States', 'Merica', 'Murica', 'United States of America', 'U.S.', 'U.S.A.', 'U. S.', 'U. S. A.', 'America'], 'fr': ['É.-U.', 'É-U', 'É-U.', 'E.-U.', 'É.U.', 'les États', 'Oncle Sam', 'Amérique', 'Etats-Unis', 'States', 'les États-Unis d’Amérique', 'États-unis', 'ÉU', 'É.-U. A.', "Pays de l'Oncle Sam", 'Etats-unis', 'États-Unis d’Amérique', 'pays de l’Oncle Sam'], 'de': ['Vereinigte Staaten von Amerika', 'US-Amerika', 'U.S.-Amerika', 'Staaten von Amerika', 'VSA', 'V.S.A.', 'V. S. A.', 'Staaten', 'die Staaten', 'VS', 'V.S.', 'V. S.', 'Amerika', 'U.S.A.', 'U. S. A.', 'United States of America', 'United States', 'U.S.', 'U. S.', 'America'], 'lb': ['Vereenegt Staaten']}
    Coordinates: [{'lat': 39.828175, 'lon': -98.5795}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now
    Verb cluster: "is acknowledged" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "Extract of a letter from Governor Lloyd, »• ho is acknowledged to be one of the most wealthy, well informed and best man"
    Verb cluster: "is" — tense=Pres, aspect=None, mood=Ind [NEGATED]
      Sentence: "and that it is not on ieserving the encou ragementof the Agriculturists of the Unit ;d States, the following testimonial"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 11 (0 = most prominent)
    OCR quality estimate: 0.989

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Governor Lloyd' and 'United States' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Governor Lloyd' near 'United States' around 1820-09-09?
  4. Resolve temporal expressions relative to 1820-09-09. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 61:
  Publication date : 1900-06-26
  Language         : en
  Person  : 'N. B. Scott'  (QID: Q1966467)
  Location: 'Idaho'  (QID: Q1221)

  [ARTICLE TEXT — entity markers added]
  "Just before the adjournment of the national committee, on motion of Sena tor Scott of West Virginia, George Wls- woll of Milwaukee was unanimously elected sergeant-at arms of tin* nation al committee for four years. In the | place of II. New, Indiana, and George L. Slump. [E2] Idaho [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Nathan B. Scott
    Description: Union Army soldier (1842-1924)
    Born: ['+1842-12-18T00:00:00Z']
    Died: ['+1924-01-02T00:00:00Z']
    Birth place: ['Quaker City']
    Death place: ['Washington, D.C.']
    Work locations: ['Washington, D.C.']
  Location Wikidata:
    Label: Idaho
    Description: state of the United States of America
    Country: ['United States']
    Located in: ['United States']
    Aliases: {'en': ['ID', 'Idaho, United States', 'Gem State', 'Potato State', 'State of Idaho', 'US-ID'], 'de': ['ID']}
    Coordinates: [{'lat': 45, 'lon': -114}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: before
    Verb cluster: "was elected" — tense=Past, aspect=Perf, mood=Ind
      Sentence: "Just before the adjournment of the national committee, on motion of Sena tor Scott of West Virginia, George Wls- woll of"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 12 (0 = most prominent)
    OCR quality estimate: 0.982

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'N. B. Scott' and 'Idaho' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'N. B. Scott' near 'Idaho' around 1900-06-26?
  4. Resolve temporal expressions relative to 1900-06-26. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 62:
  Publication date : 1881-09-24
  Language         : fr
  Person  : 'M. Aimé Humbert'  (QID: N/A)
  Location: 'Glaris'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "[E1] M. Aimé Humbert [/E1], ancien conseiller d'Etat, l'a bien dit dans un toast à la patrie : « Dès que » cette grande image de la patrie nous » apparaît, toutes les divisions sont ou-» bliées ; nous nous trouvons tous unis » dans un commun amour du bien pu-» blic. » C'est à [E2] Glaris [/E2] que la Société tiendra l'an prochain ses assises."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien
    Verb cluster: "dit" — tense=Past, aspect=None, mood=None
      Sentence: "M. Aimé Humbert, ancien conseiller d'Etat, l'a bien dit dans un toast à la patrie : «"
    Verb cluster: "est Glaris" — tense=Pres, aspect=None, mood=Ind
      Sentence: "» C'est à Glaris que la Société tiendra l'an prochain ses assises."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 67 (0 = most prominent)
    OCR quality estimate: 0.997

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Aimé Humbert' and 'Glaris' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Aimé Humbert' near 'Glaris' around 1881-09-24?
  4. Resolve temporal expressions relative to 1881-09-24. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 63:
  Publication date : 1858-10-24
  Language         : de
  Person  : 'Admiral Großfürsten Konstantin'  (QID: Q446724)
  Location: 'Villa Avigdor'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "keit soll jedoch, wie die „Presse" meldet, erst nach dem Eintreffen der russischen Flotte, die den letzten Nach« richten zufolge vor Brest ankerte und so ziemlich gleich» zeitig mit dem [E1] Admiral Großfürsten Konstantin [/E1] in Villafranca anlangen dürfte, stattfinden. T'as diese genügte jedoch bei der beschränk» ten Räumlichkeit nicht die in Nizza weilenden Gläubi» gen alle zu fassen. — Vor zwei Jahren kam Großfürst Konstantin auf dem Admiralschiff Wiborg nach La Spezzia, um die Localität in Augenschein zu nehmen."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Konstantin Nikolajewitsch Romanow
    Description: Sohn des Nikolaus I. Pawlowitsch
    Born: ['+1827-09-21T00:00:00Z', '+1827-09-09T00:00:00Z']
    Died: ['+1892-01-25T00:00:00Z']
    Birth place: ['Sankt Petersburg']
    Death place: ['Pawlowsk']
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Verb cluster: "soll" — tense=Pres, aspect=None, mood=Ind
      Sentence: "keit soll jedoch, wie die „Presse" meldet, erst nach dem Eintreffen der russischen Flotte, die den letzten Nach« richten"
    Verb cluster: "kam" — tense=Past, aspect=None, mood=Ind
      Sentence: "— Vor zwei Jahren kam Großfürst Konstantin auf dem Admiralschiff Wiborg nach La Spezzia, um die Localität in Augenschein"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 12 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Admiral Großfürsten Konstantin' and 'Villa Avigdor' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Admiral Großfürsten Konstantin' near 'Villa Avigdor' around 1858-10-24?
  4. Resolve temporal expressions relative to 1858-10-24. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 64:
  Publication date : 1820-05-05
  Language         : en
  Person  : 'King Henry'  (QID: Q101384)
  Location: 'Philadelphia'  (QID: Q1345)

  [ARTICLE TEXT — entity markers added]
  "Sir Wiiliam Blackstono has collated and commented on it—his fine copy of Magna Charta has been excelled by later specimens of art, and the fac-similes of the seals and signatur e.diave made every reader of taste in Great Britain acquainted, in some de gree, not merely with the state ofknowledge and of art at the period in question, but with the literary attainments, al>©, of King John, [E1] King Henry [/E1], and fbeir “ Barons bold.” Surely the Declaration of American Inde pendence is, at least, as well entitled to the decorations of art as the Magna. As no more of those copies will be printed than 'ball be subscribed for, gentlemen who wish for them, are requested to add the word “ colored ” to their subscription. JOHN BINNS, Chesnut-street, [E2] Philadelphia [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Henry I of England
    Description: King of England from 1100 to 1135 (1068–1135)
    Born: ['+1068-00-00T00:00:00Z', '+1068-09-21T00:00:00Z']
    Died: ['+1135-12-01T00:00:00Z', '+1135-12-02T00:00:00Z']
    Birth place: ['Selby']
    Death place: ['Saint-Denis-le-Ferment', 'Lyons-la-Forêt']
  Location Wikidata:
    Label: Philadelphia
    Description: largest city in Pennsylvania, United States
    Country: ['United States']
    Located in: ['Philadelphia County']
    Aliases: {'en': ['Philly', 'City of Brotherly Love', 'Cradle of Liberty', 'Philadelphia, Pennsylvania', 'City of Philadelphia', 'Philadelphia, PA', 'Philadelphia, Pa']}
    Coordinates: [{'lat': 39.952777777778, 'lon': -75.163611111111}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now, late, later
    Verb cluster: "has been excelled" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "Sir Wiiliam Blackstono has collated and commented on it—his fine copy of Magna Charta has been excelled by later specime"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.999

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'King Henry' and 'Philadelphia' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'King Henry' near 'Philadelphia' around 1820-05-05?
  4. Resolve temporal expressions relative to 1820-05-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 65:
  Publication date : 1820-05-05
  Language         : en
  Person  : 'JOHN BINNS'  (QID: N/A)
  Location: 'Chesnut-street'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "[E1] JOHN BINNS [/E1], [E2] Chesnut-street [/E2], Philadelphia."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 14 (0 = most prominent)
    OCR quality estimate: 0.999

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'JOHN BINNS' and 'Chesnut-street' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'JOHN BINNS' near 'Chesnut-street' around 1820-05-05?
  4. Resolve temporal expressions relative to 1820-05-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 66:
  Publication date : 1790-05-29
  Language         : en
  Person  : 'Capt. Kepling'  (QID: N/A)
  Location: 'China—that'  (QID: Q29520)

  [ARTICLE TEXT — entity markers added]
  "The Ship Harmony Capt. IVillet is arrived at Philadelphia from Bengal.—Accounts from the Eaft-Indies State—there is a mod plealing pro- fpeft of a plentiful harveft in that pare of the world—that Cotton has fold fo low as 11 Tales in [E2] China—that [/E2] the Englifli/ fettlements enjoy a profound peace—that the greateft part of trea- fure on board the Vanfittart one of the Eaft-In- idea company’s Ships lately loft, had been re covered from the wreck—that the ffiip Durham [E1] Capt. Kepling [/E1] ; and another fhip were loft in a gale of wind, foundering in the road—that Tippoo Sultan to puQjfh the faults of fome of the tributary Princes had depopulated and laid wafte their country from Belipatain to Callicut, an ex tent of 80 or 90 miles, where the latepoffeflors of its fields and habitations arefeen no more."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: China
    Description: cultural region, ancient civilization, and nation in East Asia; mostly refers to the People's Republic of China in political situation and rarely refers to the Republic of China
    Aliases: {'en': ['Cathay', 'Chunghwa', 'Zhongguo', 'Chung-kuo', 'Zhonghua', 'Chung-hua', 'Sinae', 'Flowery Kingdom', 'Celestial Kingdom', 'Middle Kingdom', 'Central Kingdom', 'Tianxia', 'All under Heaven', 'Katay', 'Khitai'], 'fr': ['empire du Milieu', 'Chine impériale']}
    Coordinates: [{'lat': 35, 'lon': 105}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: late
    Verb cluster: "is" — tense=Pres, aspect=None, mood=Ind
      Sentence: "IVillet is arrived at Philadelphia from Bengal.—Accounts from the Eaft-Indies State—there is a mod plealing pro- fpeft o"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Capt. Kepling' and 'China—that' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Capt. Kepling' near 'China—that' around 1790-05-29?
  4. Resolve temporal expressions relative to 1790-05-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 67:
  Publication date : 1961-12-21
  Language         : fr
  Person  : 'Rilc'  (QID: N/A)
  Location: 'Belge'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "[E1] Rilc [/E1] van Looy n'est pas content. Le champion du monde sur route a déclaré : « Quatre étapes contre la montre ? s'était exclamé le [E2] Belge [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "est content" — tense=Pres, aspect=None, mood=Ind [NEGATED]
      Sentence: "Rilc van Looy n'est pas content."
    Verb cluster: "exclamé" — tense=Past, aspect=None, mood=None
      Sentence: "s'était exclamé le Belge."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.988

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Rilc' and 'Belge' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Rilc' near 'Belge' around 1961-12-21?
  4. Resolve temporal expressions relative to 1961-12-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 68:
  Publication date : 1981-07-25
  Language         : fr
  Person  : 'Raymond Vincy'  (QID: N/A)
  Location: 'France'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Opérette de [E1] Raymond Vincy [/E1], musique : Francis Lopez 22.30 Madame Columbo (2) Mystère et caviar 23.20 TF 1 actualités FRANCE :"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.663

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Raymond Vincy' and 'France' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Raymond Vincy' near 'France' around 1981-07-25?
  4. Resolve temporal expressions relative to 1981-07-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 69:
  Publication date : 1800-10-16
  Language         : en
  Person  : 'Alexan\nder Addison'  (QID: N/A)
  Location: 'United States of America'  (QID: Q30)

  [ARTICLE TEXT — entity markers added]
  "Tenth day of July in the twenty fif-.h year of the Indepen dence of the [E2] United States of America [/E2], Alexan der Addison of the said District hath deposited in this office the title of a book the right where of he claims as Author in tha words following to wit, “ Reports of cafes in the County courts of the Fifth Circuit and in the High Court of Errors and appeals of the State of Pennsylvania, and charges to Grand Juries of those County Courts."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: United States
    Description: country located primarily in North America
    Country: ['United States']
    Aliases: {'en': ['the States', 'the United States of America', 'US of America', 'the US', 'the U.S.', 'the US of A', 'U.S. of America', 'the US of America', 'the USA', 'the U.S.A.', 'the U.S. of A', 'US of A', 'the U.S. of America', 'the United States', 'Merica', 'Murica', 'United States of America', 'U.S.', 'U.S.A.', 'U. S.', 'U. S. A.', 'America'], 'fr': ['É.-U.', 'É-U', 'É-U.', 'E.-U.', 'É.U.', 'les États', 'Oncle Sam', 'Amérique', 'Etats-Unis', 'States', 'les États-Unis d’Amérique', 'États-unis', 'ÉU', 'É.-U. A.', "Pays de l'Oncle Sam", 'Etats-unis', 'États-Unis d’Amérique', 'pays de l’Oncle Sam'], 'de': ['Vereinigte Staaten von Amerika', 'US-Amerika', 'U.S.-Amerika', 'Staaten von Amerika', 'VSA', 'V.S.A.', 'V. S. A.', 'Staaten', 'die Staaten', 'VS', 'V.S.', 'V. S.', 'Amerika', 'U.S.A.', 'U. S. A.', 'United States of America', 'United States', 'U.S.', 'U. S.', 'America'], 'lb': ['Vereenegt Staaten']}
    Coordinates: [{'lat': 39.828175, 'lon': -98.5795}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "deposited" — tense=Past, aspect=None, mood=None
      Sentence: "Tenth day of July in the twenty fif-.h year of the Indepen dence of the United States of America, Alexan der Addison of "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Alexan\nder Addison' and 'United States of America' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Alexan\nder Addison' near 'United States of America' around 1800-10-16?
  4. Resolve temporal expressions relative to 1800-10-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 70:
  Publication date : 1961-01-20
  Language         : fr
  Person  : 'M. F. Stirnimann'  (QID: N/A)
  Location: 'Olten'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "TIR Décès de [E1] M. F. Stirnimann [/E1] Lienhard y habite aujourd'hui en qualité de conservateur. M. Stirnimann, homme loyal et d'un dévouement inlassable, a largement mérité les honneurs que les tireurs suisses lui rendent aujourd'hui."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: aujourd'hui
    Verb cluster: "habite" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Lienhard y habite aujourd'hui en qualité de conservateur."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 7 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. F. Stirnimann' and 'Olten' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. F. Stirnimann' near 'Olten' around 1961-01-20?
  4. Resolve temporal expressions relative to 1961-01-20. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 71:
  Publication date : 1920-06-17
  Language         : en
  Person  : 'Pharaoh'  (QID: N/A)
  Location: 'Nashville, Tenn.'  (QID: Q23197)

  [ARTICLE TEXT — entity markers added]
  "[E2] Nashville, Tenn. [/E2] (Special)—How a band of Jewish war refugees have just staged a modern exoudus from Egypt ant suffered tribulations strikingly similar to those undergone by the band that Moses led of old ia recount ed in a Zionist report made public here. The Twentieth-cen’ury wanderers traveled by special train instead of a-foot, and they did not crosB tike Red sea. Instead of [E1] Pharaoh [/E1] and his hosts perverse fate pursued them."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Nashville
    Description: capital and largest city of Tennessee, United States
    Country: ['United States']
    Located in: ['Davidson County']
    Aliases: {'en': ['Nashville, Tennessee', 'Nashville–Davidson County', 'Metropolitan Government of Nashville and Davidson County', 'Nashville, TN', 'Nashville, Tenn.'], 'de': ['Nashville, Tennessee']}
    Coordinates: [{'lat': 36.16222222222222, 'lon': -86.77444444444444}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "perverse" — tense=Pres, aspect=None, mood=None
      Sentence: "Instead of Pharaoh and his hosts perverse fate pursued them."
    Verb cluster: "have staged" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "Nashville, Tenn. (Special)—How a band of Jewish war refugees have just staged a modern exoudus from Egypt ant suffered t"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 1 (0 = most prominent)
    OCR quality estimate: 0.986

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Pharaoh' and 'Nashville, Tenn.' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Pharaoh' near 'Nashville, Tenn.' around 1920-06-17?
  4. Resolve temporal expressions relative to 1920-06-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 72:
  Publication date : 1890-09-25
  Language         : en
  Person  : 'M. Pliillippe de Ferrari'  (QID: Q44105)
  Location: 'European'  (QID: Q46)

  [ARTICLE TEXT — entity markers added]
  "The museum of the Berlin post-cfllce alone contains a collection of between 4,000 and 5,000 specimens, half of which are [E2] European [/E2] and the remain der divided between tbe Americans, Asia, Africa and Australia. The emblems upon the stamps of nations are legion; the earth, the sea and the vaulted canopy above have been ransacked for curious and mraning less devices and legends. The en tire animal kingdom, the stars and the moon iu all its phases, besides legendary emblems by the thousand, are known to the oollLctors of stamps, who pride themselves upon being “philatelists.” Upon the printed faces of these little squares of paper may be fonri*} the fogies of five em perors, eighteen kings,three q icens, one grand duke, several inferior tilled rulcr9 and many presidents. [E1] M. Pliillippe de Ferrari [/E1] perhaps has the largest and most valuable collec tion of stamps in the world, amount ing to something like 2ft0,000, and within tbe present year he solJ one little stamp to a collector in Paris for 150.000."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Philipp von Ferrary
    Description: French philatelist, owner of the world's largest stamp collection (1850–1917)
    Born: ['+1850-01-11T00:00:00Z']
    Died: ['+1917-05-20T00:00:00Z']
    Birth place: ['Paris']
    Death place: ['Lausanne']
    Residences: ['Hôtel Matignon']
  Location Wikidata:
    Label: Europe
    Description: terrestrial continent located in north-western Eurasia
    Aliases: {'en': ['European continent', 'The Old Continent', 'European Continent', 'European Peninsula', 'Old Continent'], 'fr': ['continent européen', 'Vieux Continent'], 'de': ['Alter Kontinent', 'Die alte Welt', 'Europäischer Kontinent']}
    Coordinates: [{'lat': 48.690959, 'lon': 9.14062}, {'lat': 53.5, 'lon': 15.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now, late
    Verb cluster: "may be" — tense=None, aspect=None, mood=None
      Sentence: "Upon the printed faces of these little squares of paper may be fonri*} the fogies of five em perors, eighteen kings,thre"
    Verb cluster: "contains" — tense=Pres, aspect=None, mood=None
      Sentence: "The museum of the Berlin post-cfllce alone contains a collection of between 4,000 and 5,000 specimens, half of which are"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.945

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Pliillippe de Ferrari' and 'European' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Pliillippe de Ferrari' near 'European' around 1890-09-25?
  4. Resolve temporal expressions relative to 1890-09-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 73:
  Publication date : 1960-04-13
  Language         : en
  Person  : 'Clinton Shipley'  (QID: N/A)
  Location: 'Georgia'  (QID: Q1428)

  [ARTICLE TEXT — entity markers added]
  "5811 Idaho Drive Taler Patch, [E2] Georgia [/E2] July 7. 1959 Tabor City Yam Market 54 Main Street Tabor City, North Carolina Gentleman: [E1] Clinton Shipley [/E1] has asked me to recommend him for the International Yam Digging Contest that will take place in Tabor City on the eighteenth * day of September. !"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Georgia
    Description: state of the United States of America
    Country: ['United States']
    Located in: ['United States']
    Aliases: {'en': ['State of Georgia', 'GA', 'Georgia, United States', 'The Peach State', 'The Goober State', 'The Empire State of the South', 'US-GA'], 'fr': ['État de Géorgie'], 'de': ['Georgien', 'Georgien, Vereinigte Staaten']}
    Coordinates: [{'lat': 33, 'lon': -83.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "5811" → 5811
      - "1959" → 1959
    Verb cluster: "has asked" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "Tabor City Yam Market 54 Main Street Tabor City, North Carolina Gentleman: Clinton Shipley has asked me to recommend him"
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.967

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Clinton Shipley' and 'Georgia' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Clinton Shipley' near 'Georgia' around 1960-04-13?
  4. Resolve temporal expressions relative to 1960-04-13. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 74:
  Publication date : 1920-07-08
  Language         : en
  Person  : 'Jim Koffmeister'  (QID: N/A)
  Location: 'Cookeville'  (QID: Q2456192)

  [ARTICLE TEXT — entity markers added]
  "RAWLEY AGAIN Haven’t b en satisfied since I left [E2] Cookeville [/E2] until now. I seemed like I was almost lost, as I stayed in Gainesboro about IS months or 2 years. Good roads and drivers who know the roads. W. W. Brown is al ways ready, and [E1] Jim Koffmeister [/E1] 1s too."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Cookeville
    Description: city in Tennessee, United States
    Country: ['United States']
    Located in: ['Putnam County']
    Aliases: {'en': ['Cookeville, Tennessee', 'Cookeville, TN']}
    Coordinates: [{'lat': 36.164202, 'lon': -85.504295}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now
    Verb cluster: "is" — tense=Pres, aspect=None, mood=Ind
      Sentence: "W. W. Brown is al ways ready, and Jim Koffmeister 1s too."
    Verb cluster: "Have" — tense=Pres, aspect=None, mood=Ind
      Sentence: "RAWLEY AGAIN Haven’t b en satisfied since I left Cookeville until now."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 15 (0 = most prominent)
    OCR quality estimate: 0.993

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Jim Koffmeister' and 'Cookeville' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Jim Koffmeister' near 'Cookeville' around 1920-07-08?
  4. Resolve temporal expressions relative to 1920-07-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 75:
  Publication date : 1826-09-29
  Language         : fr
  Person  : "M'.'Càrnéro"  (QID: N/A)
  Location: 'MADRID'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "ESPAGNE.[E2] MADRID [/E2] \ 6 septembre."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "\" — tense=Pres, aspect=None, mood=Sub
      Sentence: "ESPAGNE.MADRID \ 6 septembre."
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between "M'.'Càrnéro" and 'MADRID' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing "M'.'Càrnéro" near 'MADRID' around 1826-09-29?
  4. Resolve temporal expressions relative to 1826-09-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 76:
  Publication date : 1828-04-09
  Language         : de
  Person  : 'Raths\nherrn Jakob Tobler'  (QID: N/A)
  Location: 'Gemeinde Speicher'  (QID: Q67148)

  [ARTICLE TEXT — entity markers added]
  "Ansehnliche Vermächtnisse erhielt die [E2] Gemeinde Speicher [/E2] vom Raths herrn Jakob Tobler, der am 7. Dez. 1827, 67 Jahre alt und kinderlos starb."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Speicher
    Description: Gemeinde im Kanton Appenzell Ausserrhoden, Schweiz
    Country: ['Schweiz']
    Located in: ['Kanton Appenzell Ausserrhoden', 'Bezirk Mittelland']
    Aliases: {'en': ['Speicher AR'], 'fr': ['Speicher AR'], 'de': ['Speicherschwendi', 'Speicher AR']}
    Coordinates: [{'lat': 47.410555555556, 'lon': 9.4433333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1827" → 1827
    Verb cluster: "erhielt" — tense=Past, aspect=None, mood=Ind
      Sentence: "Ansehnliche Vermächtnisse erhielt die Gemeinde Speicher vom Raths herrn Jakob Tobler, der am 7. Dez. 1827, 67 Jahre alt "
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    Entity sentence position in article: 11 (0 = most prominent)
    OCR quality estimate: 0.973

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Raths\nherrn Jakob Tobler' and 'Gemeinde Speicher' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Raths\nherrn Jakob Tobler' near 'Gemeinde Speicher' around 1828-04-09?
  4. Resolve temporal expressions relative to 1828-04-09. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 77:
  Publication date : 1868-02-19
  Language         : de
  Person  : 'von der Heydt'  (QID: Q765327)
  Location: 'Holland'  (QID: Q102911)

  [ARTICLE TEXT — entity markers added]
  "Als ſodann die luxemburgiſche Angelegenheit eine friedliche Löſung fand , begab ſich die in [E2] Holland [/E2] geſammelte Schaar von Hannoveranern nach der Schweiz , wo ſie in feſter militairiſcher Eintheilung verblieb und aus Mitteln des Königs Georg fort und fort ihren Unterhalt erhielt . Durch ihr müßiges Umhertreiben und ihren Uebermuth erreate dieſelbe dort vielfach Aergerniß und wurde von der Schweizer Bevölkerung , ſo wie von den Kantonsregierungen nicht grade freundlich angeſehen . riſchen Unternehmen gegen Preußen anwerben und cuS⸗ Fürſten , welcher preußiſche Unterthanen zu einem kriege — rüſten läßt , nicht gerade als ein Zeichen einer freund . Miniſter [E1] von der Heydt [/E1] ſoeben im Herrenhauſe ausgeſprochen , Jn Bezug auf das Gebahren des Königs Georg hat der Staats⸗ Minister ."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Holland
    Description: Region in den Niederlanden
    Country: ['Q55']
    Located in: ['Q55']
    Aliases: {'en': ['County of Holland', 'Holland, Netherlands', 'Province of Holland'], 'fr': ['Hollandaise', 'Hollande (région)']}
    Coordinates: [{'lat': 52.25, 'lon': 4.667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach
    Verb cluster: "ſoeben" — tense=Past, aspect=None, mood=Ind
      Sentence: "Miniſter von der Heydt ſoeben im Herrenhauſe ausgeſprochen , Jn Bezug auf das Gebahren des Königs Georg hat der Staats⸗ "
    Verb cluster: "begab" — tense=Past, aspect=None, mood=Ind
      Sentence: "Als ſodann die luxemburgiſche Angelegenheit eine friedliche Löſung fand , begab ſich die in Holland geſammelte Schaar vo"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 44 (0 = most prominent)
    OCR quality estimate: 0.994

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'von der Heydt' and 'Holland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'von der Heydt' near 'Holland' around 1868-02-19?
  4. Resolve temporal expressions relative to 1868-02-19. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 78:
  Publication date : 1920-04-22
  Language         : en
  Person  : 'Lon Morelock'  (QID: N/A)
  Location: 'Cookeville'  (QID: Q2456192)

  [ARTICLE TEXT — entity markers added]
  "[E2] Cookeville [/E2] has the best lawyers at all. Everything else is up to date. Say, you Silver Point guys, Casto Jditchell. [E1] Lon Morelock [/E1], every Jones of the name and others down around there, how is every one of my old customers?"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Cookeville
    Description: city in Tennessee, United States
    Country: ['United States']
    Located in: ['Putnam County']
    Aliases: {'en': ['Cookeville, Tennessee', 'Cookeville, TN']}
    Coordinates: [{'lat': 36.164202, 'lon': -85.504295}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "Say" — tense=None, aspect=None, mood=None
      Sentence: "Say, you Silver Point guys, Casto Jditchell."
    Verb cluster: "has" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Cookeville has the best lawyers at all."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 10 (0 = most prominent)
    OCR quality estimate: 0.992

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Lon Morelock' and 'Cookeville' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Lon Morelock' near 'Cookeville' around 1920-04-22?
  4. Resolve temporal expressions relative to 1920-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 79:
  Publication date : 1960-04-06
  Language         : en
  Person  : 'George Rent'  (QID: N/A)
  Location: 'Myrtle\nBeach Air Force Base'  (QID: Q6948590)

  [ARTICLE TEXT — entity markers added]
  "competing joined in a camp fire meeting and heard an ad dress by Col. Gruenwald, com manding officer of the Myrtle Beach Air Force Base. The Loris troop, sponsored by the First Baptist church, was the only troop to have all its Scout leaders present: Francis Ragan, [E1] George Rent [/E1]/ and George Lav."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Myrtle Beach Air Force Base
    Description: United States Air Force base located near Myrtle Beach, South Carolina
    Country: ['United States']
    Located in: ['South Carolina']
    Coordinates: [{'lat': 33.6706, 'lon': -78.9339}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "was" — tense=Past, aspect=None, mood=Ind
      Sentence: "The Loris troop, sponsored by the First Baptist church, was the only troop to have all its Scout leaders present: Franci"
    Verb cluster: "competing" — tense=Pres, aspect=Prog, mood=None
      Sentence: "competing joined in a camp fire meeting and heard an ad dress by Col. Gruenwald, com manding officer of the Myrtle Beach"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 5 (0 = most prominent)
    OCR quality estimate: 0.966

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'George Rent' and 'Myrtle\nBeach Air Force Base' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'George Rent' near 'Myrtle\nBeach Air Force Base' around 1960-04-06?
  4. Resolve temporal expressions relative to 1960-04-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 80:
  Publication date : 1810-04-07
  Language         : en
  Person  : 'capt. B.'  (QID: N/A)
  Location: 'Portugal'  (QID: Q45)

  [ARTICLE TEXT — entity markers added]
  "Capt. Burger, osthe ship John and Ed- ward, left Lisbon on the 5ih. ult. He in forms that the French army was fast ap proaching the borders of [E2] Portugal [/E2], and rea ched Boneventa."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Portugal
    Description: country in Southwestern Europe
    Country: ['Portugal']
    Aliases: {'en': ['Portuguese Republic', 'PRT', 'POR'], 'fr': ['République portugaise'], 'de': ['Portugiesische Republik', 'PRT']}
    Coordinates: [{'lat': 38.7, 'lon': -9.183333333333334}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "left" — tense=Past, aspect=None, mood=None
      Sentence: "Capt. Burger, osthe ship John and Ed- ward, left Lisbon on the 5ih."
    Verb cluster: "ap" — tense=None, aspect=None, mood=None
      Sentence: "He in forms that the French army was fast ap proaching the borders of Portugal, and rea ched Boneventa."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.947

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'capt. B.' and 'Portugal' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'capt. B.' near 'Portugal' around 1810-04-07?
  4. Resolve temporal expressions relative to 1810-04-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 81:
  Publication date : 1881-01-15
  Language         : fr
  Person  : 'M. Patrick Collins'  (QID: N/A)
  Location: 'Salford'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Dans une réunion qui vient d'avoir lieu, une résolution a été adoptée tendant à former une nouvelle ligue qui s'appelle la Ligue agraire nationale des Etats-Unis, sous la présidence de [E1] M. Patrick Collins [/E1], de Boston. Une réunion des membres de la Landleague américaine aura lieu prochainement à Washington. , 15 janvier.— On mande de [E2] Salford [/E2] qu'une explosion de dynamite a eu lieu hier dans un hangar contigu au dépôt des armes."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier
    Verb cluster: "adoptée" — tense=Past, aspect=None, mood=None
      Sentence: "Dans une réunion qui vient d'avoir lieu, une résolution a été adoptée tendant à former une nouvelle ligue qui s'appelle "
    Verb cluster: "mande" — tense=Pres, aspect=None, mood=Ind
      Sentence: "On mande de Salford qu'une explosion de dynamite a eu lieu hier dans un hangar contigu au dépôt des armes."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.967

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Patrick Collins' and 'Salford' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Patrick Collins' near 'Salford' around 1881-01-15?
  4. Resolve temporal expressions relative to 1881-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 82:
  Publication date : 1930-07-11
  Language         : en
  Person  : 'W. O.'  (QID: N/A)
  Location: 'Italy'  (QID: Q38)

  [ARTICLE TEXT — entity markers added]
  "‘[E1] W. O. [/E1]” MEETS OLD FRIEND IN ROME (Continued from Page One) bloodshed, he turned his army to the running of rail roads and fac tories that had been paralyzed by striking communists. And the King, beholding one mightier than him self in [E2] Italy [/E2], called Mussolini to his side."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Italy
    Description: country in southern Europe
    Country: ['Italy']
    Aliases: {'en': ['Italian Republic', 'Republic of Italy', 'Italia'], 'fr': ['République italienne', 'Italia', 'la République italienne', 'It.', 'Ital.', 'Ita.'], 'de': ['Italienische Republik'], 'lb': ['Italieenesch Republik']}
    Coordinates: [{'lat': 42.5, 'lon': 12.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "turned" — tense=Past, aspect=None, mood=None
      Sentence: "‘W. O.” MEETS OLD FRIEND IN ROME (Continued from Page One) bloodshed, he turned his army to the running of rail roads an"
    Verb cluster: "beholding" — tense=Pres, aspect=Prog, mood=None
      Sentence: "And the King, beholding one mightier than him self in Italy, called Mussolini to his side."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 1.000

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'W. O.' and 'Italy' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'W. O.' near 'Italy' around 1930-07-11?
  4. Resolve temporal expressions relative to 1930-07-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 83:
  Publication date : 1892-07-05
  Language         : de
  Person  : 'Simon Beſas'  (QID: N/A)
  Location: 'Berliner'  (QID: Q64)

  [ARTICLE TEXT — entity markers added]
  "Handels⸗ Zeitung des [E2] Berliner [/E2] Tageblatts . Nummer 335 . — Firma Gebrüder Beſas . Juhaber iſt der Kauſunann [E1] Simon Beſas [/E1] zu Berlin ."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Berlin
    Description: Hauptstadt und bevölkerungsreichste Stadt der Bundesrepublik Deutschland
    Country: ['Mark Brandenburg', 'Brandenburg-Preußen', 'Königreich Preußen', 'Norddeutscher Bund', 'Q43287', 'Q41304', 'NS-Staat', 'Sowjetische Besatzungszone', 'Q16957', 'Deutschland', 'Bundesrepublik Deutschland bis 1990']
    Located in: ['Mark Brandenburg', 'Brandenburg-Preußen', 'Königreich Preußen', 'Q700264', 'Q27306', 'Q161036', 'NS-Staat', 'Q183']
    Aliases: {'en': ['Berlin, Germany', 'DE-BE'], 'de': ['Stadt Berlin', 'Berlin, Deutschland', 'Bundeshauptstadt Berlin', 'Land Berlin', 'DE-BE', 'Berlin (Deutschland)', 'BE', 'Bln', 'Bln.']}
    Coordinates: [{'lat': 52.516666666667, 'lon': 13.383333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 93 (0 = most prominent)
    OCR quality estimate: 0.975

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Simon Beſas' and 'Berliner' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Simon Beſas' near 'Berliner' around 1892-07-05?
  4. Resolve temporal expressions relative to 1892-07-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 84:
  Publication date : 1978-09-27
  Language         : fr
  Person  : "défenseurs de l'équipe\nd'Angleterre, Phil Neal"  (QID: Q465956)
  Location: 'Liverpool'  (QID: Q24826)

  [ARTICLE TEXT — entity markers added]
  "Le règne de [E2] Liverpool [/E2] se terminern-t-il ce soir ? La période de domination de Liverpool en coupe d'Europe des clubs champions pourrait se terminer ce soir, à I'Anfield Road, quand les champions de 1977 et 1978, recevront Nottingham Forest, champion d'Angleterre, en match retour du premier tour de cette compétition. De plus, Liverpool a d'autres problèmes. Les défenseurs de l'équipe d'Angleterre, Phil Neal et Emlyn Hughes, et l'ailier Steve Heigh way (Eire) ont perdS la forme."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Liverpool
    Description: ville en Angleterre, Royaume-Uni
    Country: ['Q145']
    Located in: ['district métropolitain de Liverpool', 'Q21665571', 'Q21665571']
    Aliases: {'en': ['City of Liverpool', 'Liverpool, Merseyside', 'Liverpool, UK', 'Liverpool, England'], 'de': ['Liverpudlian']}
    Coordinates: [{'lat': 53.407222222222224, 'lon': -2.9916666666666667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1977" → 1977
      - "1978" → 1978
    Temporal signal words: plus
    Verb cluster: "ont" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Les défenseurs de l'équipe d'Angleterre, Phil Neal et Emlyn Hughes, et l'ailier Steve Heigh way (Eire) ont perdS la form"
    Verb cluster: "terminern" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Le règne de Liverpool se terminern-t-il ce soir ?"
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    Entity sentence position in article: 11 (0 = most prominent)
    OCR quality estimate: 0.979

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between "défenseurs de l'équipe\nd'Angleterre, Phil Neal" and 'Liverpool' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing "défenseurs de l'équipe\nd'Angleterre, Phil Neal" near 'Liverpool' around 1978-09-27?
  4. Resolve temporal expressions relative to 1978-09-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 85:
  Publication date : 1948-07-19
  Language         : de
  Person  : 'Mars!nll'  (QID: Q151414)
  Location: 'Grollbnitanniens'  (QID: Q145)

  [ARTICLE TEXT — entity markers added]
  "Man rechnet namentlich damit, dals für Grolbritannien Senatzanzler Sir Stafford C'ripye und für Frankreich Einanzminister Fene Hage; erscheinen werden. Bei dieser Gelenenheit wird vohi eine allgemeine Aus prache über die Ddurehführune des [E1] Mars!nll [/E1] Plancs Kattfinden. Der Europäische Wirtschaftsrat hat be schlonsen, den ihm von amenilennischer Seite gemnchten Vorsehing anzunchmen und sic mit der Verteilung der amerihanischen Hise an seine Mitelieder zu befassen. Dur Vorherei tung des Verteilungsprogrammes ist im Nahmen der ständigen Konunission für euro pilische Wirtschaftszusammenurheit ein betzon deres nur aus vier Mityliedern besktchendes Unterkcomitee gebildet vorden, in dem der Ver treter [E2] Grollbnitanniens [/E2] den Vorsit» führt und dem ferner Vertreter Frankreichs, Italiens und Hollands angchören."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: George C. Marshall
    Description: amerikanischer General of the Army und Staatsmann (1880–1959)
    Born: ['+1880-12-31T00:00:00Z']
    Died: ['+1959-10-16T00:00:00Z']
    Birth place: ['Uniontown']
    Death place: ['Washington, D.C.']
    Residences: ['Dodona Manor']
  Location Wikidata:
    Label: Vereinigtes Königreich
    Description: Inselstaat in Nordwesteuropa
    Country: ['Vereinigtes Königreich']
    Aliases: {'en': ['United Kingdom of Great Britain and Northern Ireland', 'U K', 'G B', 'Great Britain', 'Great Britain and Northern Ireland', 'the United Kingdom of Great Britain and Northern Ireland', 'the UK', 'the United Kingdom'], 'fr': ["Royaume-Uni de Grande-Bretagne et d'Irlande du Nord", 'Royaume Uni', 'Royaume-Uni de Grande-Bretagne et Irlande du Nord', 'Royaume-uni', 'R.-U.', 'R.U.', 'Grande-Bretagne'], 'de': ['Vereinigtes Königreich Großbritannien und Nordirland', 'Großbritannien', 'U K', 'G B', 'G B R', 'Vereinigte Königreich']}
    Coordinates: [{'lat': 54.6, 'lon': -2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Bei dieser Gelenenheit wird vohi eine allgemeine Aus prache über die Ddurehführune des Mars!nll Plancs Kattfinden."
    Verb cluster: "ist" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Dur Vorherei tung des Verteilungsprogrammes ist im Nahmen der ständigen Konunission für euro pilische Wirtschaftszusamme"
    Verb cluster: "rechnet" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Man rechnet namentlich damit, dals für Grolbritannien Senatzanzler Sir Stafford C'ripye und für Frankreich Einanzministe"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.980

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mars!nll' and 'Grollbnitanniens' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mars!nll' near 'Grollbnitanniens' around 1948-07-19?
  4. Resolve temporal expressions relative to 1948-07-19. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 86:
  Publication date : 1878-10-02
  Language         : de
  Person  : 'Fröbel'  (QID: Q76679)
  Location: 'Mailand'  (QID: Q490)

  [ARTICLE TEXT — entity markers added]
  "— [E2] Mailand [/E2] stellt Arbeiten der [E1] Fröbel [/E1]schulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die Kinder weit überschreiten:"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Friedrich Fröbel
    Description: deutscher Pädagoge
    Born: ['+1782-04-21T00:00:00Z', '+1782-00-00T00:00:00Z']
    Died: ['+1852-06-21T00:00:00Z', '+1852-00-00T00:00:00Z']
    Birth place: ['Q310955']
    Death place: ['Marienthal']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "stellt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "— Mailand stellt Arbeiten der Fröbelschulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 27 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Fröbel' and 'Mailand' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Fröbel' near 'Mailand' around 1878-10-02?
  4. Resolve temporal expressions relative to 1878-10-02. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 87:
  Publication date : 1948-05-04
  Language         : de
  Person  : 'Philip Kaiser'  (QID: Q3379042)
  Location: 'Washington'  (QID: Q61)

  [ARTICLE TEXT — entity markers added]
  "Europäische Wiederaufbau- Bedingungen [E2] Washington [/E2], 4. Mai. Der stellvertretende Arbeitsminister David Morse legte in einer Pressekonferenz gestern einen Bericht vor, den [E1] Philip Kaiser [/E1], Leiter der Abteilung für internationale Angelegenheiten im Arbeitsministerium, über die Arbeitsverhältnisse in Europa verfaßt hat. Kaiser, der mehrere Monate zu Studienzwecken in Europa verbrachte, trifft in seinem Bericht die Feststellung, daß nach allgemeiner Auffassung der zuständigen europäischen Stellen die höchstmögliche Steigerung der Produktion wichtiger als Hilfsmaßnahmen sei, um Europa wieder auf eigene Füße zu stellen. Vollproduktion sei der einzige Weg, der Aussichten auf eine wirkliche europäische Wiedergesundung eröffne.. In dem Bericht Kaisers wird weiter ausgeführt, daß die aufbauwillige europäische Arbeiterschaft noch „unter dem Druck aktiver Gegenkräfte" stehe, die den Marshall-Plan bekämpften, und daß die europäischen Arbeiter selbst „eine wichtige Rolle bei dem Gelingen oder dem Scheitern des Wiederaufbaus von Europa spielen werden.""

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Philip Mayer Kaiser
    Description: US-amerikanischer Regierungsbeamter, Hochschullehrer und Diplomat
    Born: ['+1913-07-12T00:00:00Z']
    Died: ['+2007-05-24T00:00:00Z']
    Birth place: ['Brooklyn']
    Death place: ['Washington, D.C.']
  Location Wikidata:
    Label: Washington, D.C.
    Description: Hauptstadt der Vereinigten Staaten
    Country: ['Vereinigte Staaten']
    Located in: ['District of Columbia']
    Aliases: {'en': ['Washington, District of Columbia', 'D.C. Washington', 'The District', 'District of Columbia', 'City of Washington, D.C.', 'Washington City, D.C.', "Nation's Capital (D.C.)", 'Federal City (D.C.)', 'Columbia District'], 'fr': ['Washington D.C.', 'Washington DC', 'Washington, D.C.', 'Washington, district de Columbia', 'Washington, District de Columbia', 'D.C.', 'DC'], 'de': ['Washington, District of Columbia', 'Washington', 'Washington D.C.']}
    Coordinates: [{'lat': 38.895, 'lon': -77.036666666667}]
  Known person–location links: {"death_place": "P20"}

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: gestern, nach, vor
    Verb cluster: "legte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Der stellvertretende Arbeitsminister David Morse legte in einer Pressekonferenz gestern einen Bericht vor, den Philip Ka"
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "In dem Bericht Kaisers wird weiter ausgeführt, daß die aufbauwillige europäische Arbeiterschaft noch „unter dem Druck ak"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Philip Kaiser' and 'Washington' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Philip Kaiser' near 'Washington' around 1948-05-04?
  4. Resolve temporal expressions relative to 1948-05-04. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 88:
  Publication date : 1881-01-15
  Language         : fr
  Person  : 'M. Patrick Collins'  (QID: N/A)
  Location: 'Lancashire'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Dans une réunion qui vient d'avoir lieu, une résolution a été adoptée tendant à former une nouvelle ligue qui s'appelle la Ligue agraire nationale des Etats-Unis, sous la présidence de [E1] M. Patrick Collins [/E1], de Boston. Une réunion des membres de la Landleague américaine aura lieu prochainement à Washington. Le hangar a sauté et d'autres dégâts insignifiants ont été causés par l'explosion, qu'on attribue aux fenians. La grève des mineurs du [E2] Lancashire [/E2] augmente ;"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "adoptée" — tense=Past, aspect=None, mood=None
      Sentence: "Dans une réunion qui vient d'avoir lieu, une résolution a été adoptée tendant à former une nouvelle ligue qui s'appelle "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.967

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Patrick Collins' and 'Lancashire' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Patrick Collins' near 'Lancashire' around 1881-01-15?
  4. Resolve temporal expressions relative to 1881-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 89:
  Publication date : 1874-08-25
  Language         : de
  Person  : 'Raſche .'  (QID: Q1612411)
  Location: 'Schleſten'  (QID: Q81720)

  [ARTICLE TEXT — entity markers added]
  "[E1] Raſche . [/E1] Dr . Dieier Zeitvunkt dürfte min nicht mehr ferne ſein , da die Geſchaͤfte der Geſellſchaft in letzter Zeit einen ſehr erfreulichen Auiſchwung genommen baben . So wnd und gemeldet , datz die Kefſelſchmiede der Gefenſ Gaft in [E2] Schleſten [/E2] dieler Tage Auftraͤge im Betrage von 250 00 Eutr ."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Hermann Rasche
    Description: deutscher Jurist und Politiker, MdR
    Born: ['+1809-08-01T00:00:00Z']
    Died: ['+1882-12-24T00:00:00Z']
    Birth place: ['Berlin']
    Death place: ['Wittstock/Dosse']
    Work locations: ['Berlin']
  Location Wikidata:
    Label: Schlesien
    Description: Region in Mitteleuropa
    Country: ['Polen', 'Tschechien', 'Deutschland']
    Aliases: {'fr': ['Silésiens', 'Silesia', 'Silesie', 'Schlesien'], 'de': ['Schläsing']}
    Coordinates: [{'lat': 51.1035, 'lon': 17.0396}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nicht mehr
    Verb cluster: "gemeldet" — tense=None, aspect=None, mood=None
      Sentence: "So wnd und gemeldet , datz die Kefſelſchmiede der Gefenſ Gaft in Schleſten dieler Tage Auftraͤge im Betrage von 250 00 E"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 11 (0 = most prominent)
    OCR quality estimate: 0.973

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Raſche .' and 'Schleſten' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Raſche .' near 'Schleſten' around 1874-08-25?
  4. Resolve temporal expressions relative to 1874-08-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 90:
  Publication date : 1948-05-04
  Language         : de
  Person  : 'Marshall'  (QID: Q151414)
  Location: 'Vereinigten Staaten'  (QID: Q30)

  [ARTICLE TEXT — entity markers added]
  "In dem Bericht Kaisers wird weiter ausgeführt, daß die aufbauwillige europäische Arbeiterschaft noch „unter dem Druck aktiver Gegenkräfte" stehe, die den [E1] Marshall [/E1]-Plan bekämpften, und daß die europäischen Arbeiter selbst „eine wichtige Rolle bei dem Gelingen oder dem Scheitern des Wiederaufbaus von Europa spielen werden." Morse erklärte, da s Arbeitsministerium sei an einem Ausbau der wechselseitigen Handelabkommen durch den Kongreß interessiert. Die Verhandlungen mit anderen Nationen im Rahmen des hierfür erlassenen Gesetzes seien eng mit der Verwirklichung des - europäischen Wiederaufbauprogramms verknüpft. Auf diese Weise würden die Vorteile, die sich aus dem europäischen Wiederaufbauprogramm ergeben, den Farmern, Arbeitern und Geschäftsleuten der [E2] Vereinigten Staaten [/E2] ebenso zugute kommen wie denjenigen Europas."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: George C. Marshall
    Description: amerikanischer General of the Army und Staatsmann (1880–1959)
    Born: ['+1880-12-31T00:00:00Z']
    Died: ['+1959-10-16T00:00:00Z']
    Birth place: ['Q1187047']
    Death place: ['Q61']
    Residences: ['Dodona Manor']
  Location Wikidata:
    Label: Vereinigte Staaten
    Description: Staat in Nordamerika
    Country: ['Vereinigte Staaten']
    Aliases: {'en': ['the States', 'the United States of America', 'US of America', 'the US', 'the U.S.', 'the US of A', 'U.S. of America', 'the US of America', 'the USA', 'the U.S.A.', 'the U.S. of A', 'US of A', 'the U.S. of America', 'the United States', 'Merica', 'Murica', 'United States of America', 'U.S.', 'U.S.A.', 'U. S.', 'U. S. A.', 'America'], 'fr': ['É.-U.', 'É-U', 'É-U.', 'E.-U.', 'É.U.', 'les États', 'Oncle Sam', 'Amérique', 'Etats-Unis', 'States', 'les États-Unis d’Amérique', 'États-unis', 'ÉU', 'É.-U. A.', "Pays de l'Oncle Sam", 'Etats-unis', 'États-Unis d’Amérique', 'pays de l’Oncle Sam'], 'de': ['Vereinigte Staaten von Amerika', 'US-Amerika', 'U.S.-Amerika', 'Staaten von Amerika', 'VSA', 'V.S.A.', 'V. S. A.', 'Staaten', 'die Staaten', 'VS', 'V.S.', 'V. S.', 'Amerika', 'U.S.A.', 'U. S. A.', 'United States of America', 'United States', 'U.S.', 'U. S.', 'America'], 'lb': ['Vereenegt Staaten']}
    Coordinates: [{'lat': 39.828175, 'lon': -98.5795}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "In dem Bericht Kaisers wird weiter ausgeführt, daß die aufbauwillige europäische Arbeiterschaft noch „unter dem Druck ak"
    Verb cluster: "würden" — tense=Past, aspect=None, mood=Sub
      Sentence: "Auf diese Weise würden die Vorteile, die sich aus dem europäischen Wiederaufbauprogramm ergeben, den Farmern, Arbeitern "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 1 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Marshall' and 'Vereinigten Staaten' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Marshall' near 'Vereinigten Staaten' around 1948-05-04?
  4. Resolve temporal expressions relative to 1948-05-04. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 91:
  Publication date : 1928-06-05
  Language         : de
  Person  : 'Venezianers Gabrieli'  (QID: Q34624)
  Location: 'Lau\nsanne'  (QID: Q807)

  [ARTICLE TEXT — entity markers added]
  "Sängerfest in Lau sanne auszuweisen. U. Wehrlis kraftvolles Sem pacherlied leitete als Gesamtchor ein. „Die Schmiede im Wald" glänzte durch vornehme Melodik, die durch die modern gehaltene, charakteristische Orchester begleitung aber nicht beeinträchtigt wird. Im acht stimmigen a cappella-Chor „Jubilate Deo“ des [E1] Venezianers Gabrieli [/E1] ließen die Präzision der Einsätze und die Geschlossenheit des Ensembles nichts zu wünschen übrig."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Lausanne
    Description: Schweizer Stadt und Hauptstadt des Kantons Waadt
    Country: ['Schweiz']
    Located in: ['Kanton Bern', 'Bezirk Lausanne']
    Aliases: {'en': ['Lausanne VD', 'Olympic Capital', 'City of Lausanne'], 'fr': ['Capitale olympique', 'Lausanne VD', 'Ville de Lausanne', 'Lausanngrad', 'Lausanngeles'], 'de': ['olympische Hauptstadt']}
    Coordinates: [{'lat': 46.533333333333, 'lon': 6.6333333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "ließen" — tense=Past, aspect=None, mood=Ind
      Sentence: "Im acht stimmigen a cappella-Chor „Jubilate Deo“ des Venezianers Gabrieli ließen die Präzision der Einsätze und die Gesc"
    Verb cluster: "sanne" — tense=Pres, aspect=None, mood=Sub
      Sentence: "Sängerfest in Lau sanne auszuweisen."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 16 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Venezianers Gabrieli' and 'Lau\nsanne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Venezianers Gabrieli' near 'Lau\nsanne' around 1928-06-05?
  4. Resolve temporal expressions relative to 1928-06-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 92:
  Publication date : 1948-11-06
  Language         : de
  Person  : 'Mittelläufer Gewirk'  (QID: Q697373)
  Location: 'Bratislava'  (QID: Q1780)

  [ARTICLE TEXT — entity markers added]
  "Es ist beschämend, zwölf österreichische Stürmer, die im A und B-Team gegen die Tschechoslowakei in Wien und [E2] Bratislava [/E2] antraten, schössen nur einen Treffer, und der Mann, der dieses Kunststück zuwege brachte, ist der Nestor dieses Dutzend, der 35jährige Pepi Stroh von der Wiener Austria. Es waren nicht zehn sondern zwölf Stürmer, da je ein Mann in beiden Mannschaften in der Pause ausgetauscht wurde. War bisher die Stürmerreihe das Sorgenkind des Verbandskapitäns, ist es nun die Halfreihe geworden, denn außer dem [E1] Mittelläufer Gewirk [/E1] von der Austria zeigten seine beiden Helfer nicht viel erfreuliches."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Ernst Ocwirk
    Description: österreichischer Fußballspieler und -trainer
    Born: ['+1926-03-07T00:00:00Z']
    Died: ['+1980-01-23T00:00:00Z']
    Birth place: ['Q1741']
    Death place: ['Q675036']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "ist" — tense=Pres, aspect=None, mood=Ind
      Sentence: "War bisher die Stürmerreihe das Sorgenkind des Verbandskapitäns, ist es nun die Halfreihe geworden, denn außer dem Mitte"
    Verb cluster: "ist" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Es ist beschämend, zwölf österreichische Stürmer, die im A und B-Team gegen die Tschechoslowakei in Wien und Bratislava "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.944

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mittelläufer Gewirk' and 'Bratislava' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mittelläufer Gewirk' near 'Bratislava' around 1948-11-06?
  4. Resolve temporal expressions relative to 1948-11-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 93:
  Publication date : 1858-02-24
  Language         : de
  Person  : 'Ludwig Phil»\nlivpe'  (QID: Q7771)
  Location: 'Frankreich'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "Der Anblick, welchen [E2] Frankreich [/E2] seit einiger Zeit gewährt, ist im höchsten Grade betrübend und Be» sorgniß erregend, Trotz der gewaltigen Hand, welche seit dem 2. Dez. 1852 dort die Zügel der Regie» nlng gefaßt , ist die Revolution doch eine per» man ente geblieben; Auf die Bourboncn folgte die Pöbelherrschaft, auf diese Napoleons l. Gewaltregiment, dieser wurde dann wieder durch die Bourbonen verdrängt, deren Regierungsfähig» keit in der Thai erloschen schien, als Ludwig Phil» livpe sie mit einem Hauche vom Throne blasen konnte, um achtzehn Jahre später noch schmählicher gestürzt zu werden! Nach ihm, der nichts gethan, mn Frankreich moralisch zu heben, — worin doch die einzige Stütze seiner Monarchie bestand, —nach ihm sehen wir wieder die Pöbelherrschaft im wilde» sten Auswüchse, wir sehen die Nepublick gegen ihre eigenen Ultras die blutigsten Straßenkampfe führen, Ins zuletzt Napoleon !11. abermals über Nacht dem ein Ende und sich zum Herrscher Frankreichs machte."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Louis-Philippe I.
    Description: König der Franzosen von 1830 bis 1848
    Born: ['+1773-10-06T00:00:00Z']
    Died: ['+1850-08-26T00:00:00Z']
    Birth place: ['Paris']
    Death place: ['Claremont House']
    Work locations: ['Paris']
  Location Wikidata:
    Label: Frankreich
    Description: Staat in Westeuropa mit Überseegebieten
    Country: ['Frankreich']
    Aliases: {'en': ['French Republic'], 'fr': ['République française', 'RF', 'fr', 'la République française', 'Fr.', 'La France', "L'Hexagone"], 'de': ['Französische Republik', 'fr', 'RF']}
    Coordinates: [{'lat': 47, 'lon': 2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1852" → 1852
    Temporal signal words: nach, spät
    Verb cluster: "folgte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Auf die Bourboncn folgte die Pöbelherrschaft, auf diese Napoleons l. Gewaltregiment, dieser wurde dann wieder durch die "
    Verb cluster: "ist" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Der Anblick, welchen Frankreich seit einiger Zeit gewährt, ist im höchsten Grade betrübend und Be» sorgniß erregend, Tro"
    Verb cluster: "sehen" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Nach ihm, der nichts gethan, mn Frankreich moralisch zu heben, — worin doch die einzige Stütze seiner Monarchie bestand,"
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 6 days
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.990

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Ludwig Phil»\nlivpe' and 'Frankreich' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Ludwig Phil»\nlivpe' near 'Frankreich' around 1858-02-24?
  4. Resolve temporal expressions relative to 1858-02-24. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 94:
  Publication date : 1804-07-20
  Language         : fr
  Person  : 'Napoléon Bonaparte'  (QID: N/A)
  Location: 'CoNSTANTiNOPLE'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "R. [E2] CoNSTANTiNOPLE [/E2], io Juin. L'efcadre ruffe fur laquelle le général de Sprengporten eft venu ici, n'a pu enepre remettre à la voile, à caufe des vents contraires.— La nouvelle de l'élévation de [E1] Napoléon Bonaparte [/E1] à la dignité impériale, a fait une grande fenfation fur notre miniftère, & a donné lieu à plufieurs confeils d'état .."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "fait" — tense=Past, aspect=None, mood=None
      Sentence: "L'efcadre ruffe fur laquelle le général de Sprengporten eft venu ici, n'a pu enepre remettre à la voile, à caufe des ven"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 5 (0 = most prominent)
    OCR quality estimate: 0.948

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Napoléon Bonaparte' and 'CoNSTANTiNOPLE' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Napoléon Bonaparte' near 'CoNSTANTiNOPLE' around 1804-07-20?
  4. Resolve temporal expressions relative to 1804-07-20. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 95:
  Publication date : 1948-11-06
  Language         : de
  Person  : 'Mittelläufer Gewirk'  (QID: Q697373)
  Location: 'Tschechoslowakei'  (QID: Q33946)

  [ARTICLE TEXT — entity markers added]
  "Es ist beschämend, zwölf österreichische Stürmer, die im A und B-Team gegen die [E2] Tschechoslowakei [/E2] in Wien und Bratislava antraten, schössen nur einen Treffer, und der Mann, der dieses Kunststück zuwege brachte, ist der Nestor dieses Dutzend, der 35jährige Pepi Stroh von der Wiener Austria. Es waren nicht zehn sondern zwölf Stürmer, da je ein Mann in beiden Mannschaften in der Pause ausgetauscht wurde. Die Ungarn waren in Wien zu Gast und setzten ihre Siegesserie — seit zehn Jahren hat Oesterreich noch keinen Länderkampf gegen Ungarn gewonnen — fort. 5—1 wurde Oesterreich geschlagen u. auch bei den anschließenden internationalen Meisterschaften kamen die Gäste aus der CSR und Ungarn zu Siegen."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Ernst Ocwirk
    Description: österreichischer Fußballspieler und -trainer
    Born: ['+1926-03-07T00:00:00Z']
    Died: ['+1980-01-23T00:00:00Z']
    Birth place: ['Q1741']
    Death place: ['Q675036']
  Location Wikidata:
    Label: Tschechoslowakei
    Description: historischer Staat in Mitteleuropa (1918–1992)
    Country: ['Tschechoslowakei']
    Aliases: {'en': ['Czecho-Slovakia', 'cs', 'TCH', 'Československo', 'Federation of Czechoslovakia', "People's Republic of Czechoslovakia"], 'fr': ['Tchecoslovaquie', 'République tchécoslovaque', 'Tchéco-Slovaquie', 'République socialiste tchécoslovaque', 'République fédérale tchèque et slovaque', 'Tchéc.'], 'de': ['Tschechoslowakisch', 'ČSR', 'Tschecho-Slowakei', 'Tschechoslowakische Sozialistische Republik', 'Republik Tschecho-Slowakei', 'Tschecho-Slowakische Republik', 'Tschechoslowakische Republik', 'Republik Tschechoslowakei', 'Tschechische und Slowakische Föderative Republik']}
    Coordinates: [{'lat': 50.083333333333, 'lon': 14.416666666667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "ist" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Es ist beschämend, zwölf österreichische Stürmer, die im A und B-Team gegen die Tschechoslowakei in Wien und Bratislava "
    Verb cluster: "wurde" — tense=Past, aspect=None, mood=Ind
      Sentence: "5—1 wurde Oesterreich geschlagen u. auch bei den anschließenden internationalen Meisterschaften kamen die Gäste aus der "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.944

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mittelläufer Gewirk' and 'Tschechoslowakei' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mittelläufer Gewirk' near 'Tschechoslowakei' around 1948-11-06?
  4. Resolve temporal expressions relative to 1948-11-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 96:
  Publication date : 1810-04-14
  Language         : en
  Person  : 'JAMES MADISON'  (QID: Q11813)
  Location: 'lit\ntle Miami'  (QID: Q450324)

  [ARTICLE TEXT — entity markers added]
  "B E it enacted by the Senate and House §f Representatives o f the United States of America, in Congress assembled, That the officers and soldiers of the Virginia line on continental establishment, their heirs or as signs entitled to bounty lands within the tract reserved by Virginia, between the lit tle Miami and Sciota rivers, for satisfying the legal bounties to her officers and soldi ers upon continental establishment, shall be allowed a further term of five years, from and after the passage of this act, to obtain warrants and complete their locations, and a further term of seven years, from and as ter the passage of this act as aforesaid, to return their surveys and warrants to the of sice of the Secretary of the War Depart ment, any thing in any former act to the contrary notwithstanding- Provided , That no locations as aforesaid within the above mentioned tract shall after the passing of this act he made on tracts of land for which patents had previously been issued or which had been previously surveyed, and any pa tent which may nevertheless be obtained for land located contrary to the provisions of this section, shall be considered as null and void. Approved. [E1] JAMES MADISON [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: James Madison
    Description: President of the United States from 1809 to 1817 (1751–1836)
    Born: ['+1751-03-16T00:00:00Z']
    Died: ['+1836-06-28T00:00:00Z']
    Birth place: ['Port Conway']
    Death place: ['Montpelier']
    Work locations: ['Washington, D.C.']
  Location Wikidata:
    Label: Little Miami River
    Description: tributary of the Ohio River in Ohio, United States
    Country: ['United States']
    Located in: ['Ohio']
    Aliases: {'fr': ['Little Miami River']}
    Coordinates: [{'lat': 39.82756, 'lon': -83.5765885}, {'lat': 39.078116305556, 'lon': -84.432996388889}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after
    Verb cluster: "Approved" — tense=Past, aspect=Perf, mood=None
      Sentence: "Approved."
    Verb cluster: "assembled" — tense=Past, aspect=None, mood=None
      Sentence: "B E it enacted by the Senate and House §f Representatives o f the United States of America, in Congress assembled, That "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 7 (0 = most prominent)
    OCR quality estimate: 0.989

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'JAMES MADISON' and 'lit\ntle Miami' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'JAMES MADISON' near 'lit\ntle Miami' around 1810-04-14?
  4. Resolve temporal expressions relative to 1810-04-14. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 97:
  Publication date : 1830-03-03
  Language         : en
  Person  : 'Ferdinand'  (QID: N/A)
  Location: 'South Carolina'  (QID: Q1456)

  [ARTICLE TEXT — entity markers added]
  "Intelligencer, printed at Georgetown, in [E2] South Carolina [/E2], will show the extraordinary degre of ex citement which still prevails in that; State, on the subject oftlie Tariff.— It is not pleasant to recur to tl esc things, hut it is in vain to shut the eye eye upon them.— They well know that a sep aration of the Union would be a der.th blow to the Northern Atlantic .sea board, and of course a great injury to tbe interior. But to those who, when— not tri fling, not speculative, but'important, practical lights are taken from us, even the most important of all,- s*“lf-' government—to those who in sucit times shrink Iroin acting, and entrench themselves behind arguments and sen timents which have been in all ages the apology for submission and servi tude; we would recommend to them as a master the beloved [E1] Ferdinand [/E1], or, better' yet, the amiable Don Mi- gucl."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: South Carolina
    Description: state of the United States of America
    Country: ['United States', 'United States']
    Located in: ['United States']
    Aliases: {'en': ['SC', 'State of South Carolina', 'South Carolina, United States', 'S. C.', 'S.C.', 'Palmetto State', 'US-SC'], 'fr': ['État de la Caroline du Sud', 'État de Caroline du Sud', 'South Carolina'], 'de': ['Südkarolina', 'Süd-Karolina', 'Staat Südkarolina', 'Staat Süd-Karolina']}
    Coordinates: [{'lat': 34, 'lon': -81}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now
    Verb cluster: "would recommend" — tense=None, aspect=None, mood=None
      Sentence: "But to those who, when— not tri fling, not speculative, but'important, practical lights are taken from us, even the most"
    Verb cluster: "will show" — tense=None, aspect=None, mood=None
      Sentence: "Intelligencer, printed at Georgetown, in South Carolina, will show the extraordinary degre of ex citement which still pr"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 8 (0 = most prominent)
    OCR quality estimate: 1.000

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Ferdinand' and 'South Carolina' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Ferdinand' near 'South Carolina' around 1830-03-03?
  4. Resolve temporal expressions relative to 1830-03-03. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 98:
  Publication date : 1868-02-19
  Language         : de
  Person  : 'Georg'  (QID: Q57428)
  Location: 'Hannover'  (QID: Q164079)

  [ARTICLE TEXT — entity markers added]
  "Das Herrenhaus hat die Zuverſicht , welche jüngſt an dieſer Stelle ausgeſprochen wurde , gerechtfertigt : daſſelbe hat in der Angelegenheit des [E2] Hannover [/E2]ſchen Provinzialfonds die Geſichtspunkte einer großen patriotiſchen Politik über alle anderen Rückſichten und Neigungen geſtellt und der Staatsregierung ſeine bereitwillige und volle Unterſtützung zur Durchführung ihrer Abſichten für die neue Provinz gewährt . Zahlreicher als gewöhnlich waren die Mitglieder des Hauſes baben ſich dagegen erklärt und auch dieſe nicht gegen die be⸗ Es bewährt ſich hierin , Jndem das Herrenhaus durch ſeinen jüngſten Beſchluß von Neuem mit vollſter Entſchiedenheit für dieſe Politik eingetreten iſt , hat daſſelbe zugleich die Zuverſicht erhöht , daß die konſervative Partei Die ſogenaunte Hannoverſche Legion . Aufenthalt in Hietzing , die Regierung dann verpflichtet ſein wird , das Während die preußiſche Regierung dem früheren König von Hannover die größte und edelſte Rückſicht zu Theil werden läßt , während andererſeits ihre Fürſorge für die neue Provinz unter der be — des Königs [E1] Georg [/E1] und ſeiner Umgebung in Hietzing die verwerflichen Verſuche fortgeſetzt , einen Theil ſeiner früheren Unterthanen , meiſt aus den unterſten Ständen , für das völlige boffnungsloſe und thörichte Unternehmen einer Wiederherſtellung ſeines Thrones zu gewinnen ."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Georg V. von Hannover
    Description: König von Hannover, Deutschland
    Born: ['+1819-05-27T00:00:00Z']
    Died: ['+1878-06-12T00:00:00Z']
    Birth place: ['Berlin']
    Death place: ['Paris']
    Work locations: ['Berlin', 'London', 'Hannover']
  Location Wikidata:
    Label: Königreich Hannover
    Description: deutsches Königreich (1814-1866)
    Aliases: {'en': ['Königreich Hannover', 'Hanover', 'Hannover'], 'fr': ['Hanovre'], 'de': ['Hannover', 'Kgr. Hannover']}
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: früher, früh
    Verb cluster: "verpflichtet" — tense=None, aspect=None, mood=None
      Sentence: "Aufenthalt in Hietzing , die Regierung dann verpflichtet ſein wird , das Während die preußiſche Regierung dem früheren K"
    Verb cluster: "hat" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Das Herrenhaus hat die Zuverſicht , welche jüngſt an dieſer Stelle ausgeſprochen wurde , gerechtfertigt : daſſelbe hat i"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 29 (0 = most prominent)
    OCR quality estimate: 0.994

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Georg' and 'Hannover' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Georg' near 'Hannover' around 1868-02-19?
  4. Resolve temporal expressions relative to 1868-02-19. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 99:
  Publication date : 1928-06-05
  Language         : de
  Person  : 'Hegars'  (QID: Q670852)
  Location: 'Lau\nsanne'  (QID: Q807)

  [ARTICLE TEXT — entity markers added]
  "Sängerfest in Lau sanne auszuweisen. U. Wehrlis kraftvolles Sem pacherlied leitete als Gesamtchor ein. „Das ist das Meer", bei dessen Wiedergabe die schwierigen Modulationen zu gutem Gelingen kamen. Man darf wohl annehmen, daß in Lausanne die Orchesterbegleitung dem Soldaten- und Studenten chor aus „Fausts Verdammung" von H. Berlioz zum nötigen, rhythmisch beschwingten Vortrag ver helfen werde."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Friedrich Hegar
    Description: Schweizer Komponist und Dirigent
    Born: ['+1841-10-11T00:00:00Z']
    Died: ['+1927-06-02T00:00:00Z']
    Birth place: ['Basel']
    Death place: ['Q72']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "sanne" — tense=Pres, aspect=None, mood=Sub
      Sentence: "Sängerfest in Lau sanne auszuweisen."
    Verb cluster: "darf" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Man darf wohl annehmen, daß in Lausanne die Orchesterbegleitung dem Soldaten- und Studenten chor aus „Fausts Verdammung""
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 6 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Hegars' and 'Lau\nsanne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Hegars' near 'Lau\nsanne' around 1928-06-05?
  4. Resolve temporal expressions relative to 1928-06-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 100:
  Publication date : 1920-04-22
  Language         : en
  Person  : 'Old\nTim'  (QID: N/A)
  Location: 'Cookeville'  (QID: Q2456192)

  [ARTICLE TEXT — entity markers added]
  "Old Tim is a good lawyer and a hustler in the courts. [E2] Cookeville [/E2] has the best lawyers at all. I have tried Morgan up one side and down the other and find them o. k. As I stated above 1 was in Cooke ville a few days ago, but did not stay long enough t ofind out any news."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Cookeville
    Description: city in Tennessee, United States
    Country: ['United States']
    Located in: ['Putnam County']
    Aliases: {'en': ['Cookeville, Tennessee', 'Cookeville, TN']}
    Coordinates: [{'lat': 36.164202, 'lon': -85.504295}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "is" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Old Tim is a good lawyer and a hustler in the courts."
    Verb cluster: "was" — tense=Past, aspect=None, mood=Ind
      Sentence: "As I stated above 1 was in Cooke ville a few days ago, but did not stay long enough t ofind out any news."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.992

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Old\nTim' and 'Cookeville' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Old\nTim' near 'Cookeville' around 1920-04-22?
  4. Resolve temporal expressions relative to 1920-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 101:
  Publication date : 1818-01-06
  Language         : de
  Person  : 'Herzogs von\nWellington'  (QID: Q131691)
  Location: 'Sy\nbillen-Tempel'  (QID: Q784000)

  [ARTICLE TEXT — entity markers added]
  "um dessen Basis sich eine runde Kolonnade zieht, ähnlich einem der bewundertsten Reste des Alterthums, dem Sy billen-Tempel zu Tivoli. Die Trafalgar-Säule wird 100,000. Pfund kosten, und zu Greenwich errichtet wer den. Sie besteht aus einem einfachen Oktogon, von einer angemessenen Basis, mit einer Schiffskrone bedeckt, zu wel cher kolossale Stufen führen. An beyden Monumenten wird gearbeitet. Außerdem wird zu Ehren des Herzogs von Wellington ein Denkmal auf Blakdownhill errichtet, wel ches die Gestalt eines Dreyecks und die Höhe von 150."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Arthur Wellesley, 1. Duke of Wellington
    Description: britischer Feldmarschall und Staatsmann
    Born: ['+1769-05-01T00:00:00Z']
    Died: ['+1852-09-14T00:00:00Z']
    Birth place: ['Dublin']
    Death place: ['Walmer Castle']
    Residences: ['Dangan Castle']
    Work locations: ['Q84']
  Location Wikidata:
    Label: Tempel der Sibylle
    Description: römischer Tempel in Tivoli
    Country: ['Italien']
    Located in: ['Tivoli']
    Aliases: {'en': ['Temple of Sibyl']}
    Coordinates: [{'lat': 41.9669, 'lon': 12.8009}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Außerdem wird zu Ehren des Herzogs von Wellington ein Denkmal auf Blakdownhill errichtet, wel ches die Gestalt eines Dre"
    Verb cluster: "zieht" — tense=Pres, aspect=None, mood=Ind
      Sentence: "um dessen Basis sich eine runde Kolonnade zieht, ähnlich einem der bewundertsten Reste des Alterthums, dem Sy billen-Tem"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 10 (0 = most prominent)
    OCR quality estimate: 0.970

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Herzogs von\nWellington' and 'Sy\nbillen-Tempel' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Herzogs von\nWellington' near 'Sy\nbillen-Tempel' around 1818-01-06?
  4. Resolve temporal expressions relative to 1818-01-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 102:
  Publication date : 1898-06-10
  Language         : de
  Person  : 'Aunnen'  (QID: N/A)
  Location: 'Buenos Aires'  (QID: Q1486)

  [ARTICLE TEXT — entity markers added]
  "Dasselbe gilt von [E1] Aunnen [/E1], der sein Seeheldentum der armseligen Thatsache verdankt, daß er einmal als Komman dant eines Kriegsschiffes, das im Rio de la Plata lag, der Madrider Regierung, die das Schiff zurückrief, den Gehorsam verweigerte, Staatsangehörigen, die durch die Revolution von [E2] Buenos Aires [/E2] bedroht waren, zu schützen hatte."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Buenos Aires
    Description: Hauptstadt und bevölkerungsreichste Stadt Argentiniens
    Country: ['Argentinien']
    Located in: ['Argentinien']
    Aliases: {'en': ['Ciudad Autonoma de Buenos Aires', 'Buenos Ayres', 'Ciudad de Buenos Aires'], 'de': ['Buenos Ayres', 'Ciudad Autónoma de Buenos Aires']}
    Coordinates: [{'lat': -34.599722222222, 'lon': -58.381944444444}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "gilt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Dasselbe gilt von Aunnen, der sein Seeheldentum der armseligen Thatsache verdankt, daß er einmal als Komman dant eines K"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 41 (0 = most prominent)
    OCR quality estimate: 0.998

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Aunnen' and 'Buenos Aires' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Aunnen' near 'Buenos Aires' around 1898-06-10?
  4. Resolve temporal expressions relative to 1898-06-10. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 103:
  Publication date : 1988-02-15
  Language         : fr
  Person  : 'Manfred Gsteiger'  (QID: N/A)
  Location: 'Europe'  (QID: Q46)

  [ARTICLE TEXT — entity markers added]
  "[E1] Manfred Gsteiger [/E1] Une telle remarque est pour ainsi dire le résumé d'innombrables discours, littéraires et autres, de l'[E2] Europe [/E2] des Lumières et de la sensibilité préromantique où la Suisse apparaît comme le lieu idyllique d'une nature et d'une humanité non conompues et la patrie de toutes les vertus républicaines."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Europe
    Description: continent terrestre situé au nord-ouest de l'Eurasie
    Aliases: {'en': ['European continent', 'The Old Continent', 'European Continent', 'European Peninsula', 'Old Continent'], 'fr': ['continent européen', 'Vieux Continent'], 'de': ['Alter Kontinent', 'Die alte Welt', 'Europäischer Kontinent']}
    Coordinates: [{'lat': 48.690959, 'lon': 9.14062}, {'lat': 53.5, 'lon': 15.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "est dire" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Une telle remarque est pour ainsi dire le résumé d'innombrables discours, littéraires et autres, de l'Europe des Lumière"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.989

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Manfred Gsteiger' and 'Europe' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Manfred Gsteiger' near 'Europe' around 1988-02-15?
  4. Resolve temporal expressions relative to 1988-02-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 104:
  Publication date : 2018-01-03
  Language         : fr
  Person  : 'Scipion'  (QID: N/A)
  Location: 'Bahreïn'  (QID: Q398)

  [ARTICLE TEXT — entity markers added]
  "Sur un bateau au large de [E2] Bahreïn [/E2] : « Les porteurs chargés comme des mu-lets prennent la passerelle étroite d’assaut, un vrai film de pirates à l’abordage, et en même temps d’autres porteurs redescendent par la même échelle prendre livraison d’un nouveau chargement, ce qui provoque des embouteillages des familles (...). » Chez le médecin en Inde : « Il y a un dispensaire, avec un toubib indigène, genre charlatan, nous y amenons « [E1] Scipion [/E1] »;"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Bahreïn
    Description: pays du Moyen-Orient
    Country: ['Bahreïn']
    Aliases: {'en': ['bh', 'Kingdom of Bahrain', 'BAH', 'Bahrein Islands', 'ISO 3166-1:BH', 'Mamlakat al-Baḥrayn', 'Dawlat al-Bahrain'], 'fr': ['Royaume de Bahreïn', 'BH', 'le Royaume de Bahreïn'], 'de': ['Königreich Bahrain', 'Bahrein']}
    Coordinates: [{'lat': 26.0675, 'lon': 50.551111}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "a" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Il y a un dispensaire, avec un toubib indigène, genre charlatan, nous y amenons « Scipion »;"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 12 (0 = most prominent)
    OCR quality estimate: 1.000

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Scipion' and 'Bahreïn' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Scipion' near 'Bahreïn' around 2018-01-03?
  4. Resolve temporal expressions relative to 2018-01-03. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 105:
  Publication date : 1961-12-21
  Language         : fr
  Person  : 'Coppi'  (QID: N/A)
  Location: 'Herentals'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Quant à l'étape contre la montre par équipes, organisée par hasard à [E2] Herentals [/E2], le village de Rilc van Looy, c'est une mauvaise plaisanterie que l'on aurait souhaité ne plus revoir dans une épreuve de l'importance du Tour. Mais entre notre opinion et le « veto » de van Looy, il y a une marge. Les organisateurs sont seuls juges.Van Looy, non content de gagner 800 000 francs suisses par saison, voudrait que l'on fasse le Tour à sa mesure...Jamais le grand [E1] Coppi [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Verb cluster: "voudrait" — tense=Imp, aspect=None, mood=Ind
      Sentence: "Les organisateurs sont seuls juges.Van Looy, non content de gagner 800 000 francs suisses par saison, voudrait que l'on "
    Verb cluster: "est plaisanterie" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Quant à l'étape contre la montre par équipes, organisée par hasard à Herentals, le village de Rilc van Looy, c'est une m"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 20 (0 = most prominent)
    OCR quality estimate: 0.988

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Coppi' and 'Herentals' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Coppi' near 'Herentals' around 1961-12-21?
  4. Resolve temporal expressions relative to 1961-12-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 106:
  Publication date : 1981-12-11
  Language         : fr
  Person  : 'Maria Estève'  (QID: N/A)
  Location: 'Fulgur'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "on s'aventure grâce à M. Benjamin sur la froide planète [E2] Fulgur [/E2]. Bandes dessinées, télévision, cinéma ont depuis longtemps compris et commercialisé l'engouement de la jeunesse pour la science-fiction. Les costumes signés Mouky respectent admirablement la mode spatiale et les accessoires d'Henri Barbier et [E1] Maria Estève [/E1] intriguent suffisamment pour qu'à la fin du spectacle jeunes et moins jeunes s'élancent sur scène pour comprendre, toucher, explorer ces nouveaux gadgets."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "respectent" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Mouky respectent admirablement la mode spatiale et les accessoires d'Henri Barbier et Maria Estève intriguent suffisamme"
    Verb cluster: "aventure" — tense=Pres, aspect=None, mood=Ind
      Sentence: "on s'aventure grâce à M. Benjamin sur la froide planète Fulgur."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 13 (0 = most prominent)
    OCR quality estimate: 0.985

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Maria Estève' and 'Fulgur' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Maria Estève' near 'Fulgur' around 1981-12-11?
  4. Resolve temporal expressions relative to 1981-12-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 107:
  Publication date : 1868-04-22
  Language         : fr
  Person  : 'sir Robert Napier'  (QID: Q336474)
  Location: 'Grande-Bretagne'  (QID: Q145)

  [ARTICLE TEXT — entity markers added]
  "[E2] Grande-Bretagne [/E2]. —Sir Strafford Norlhcole, secrétaire d'Elat des colonies, a reçu de [E1] sir Robert Napier [/E1] la dépêche suivante, en dale de Lait, le 23 mars :"

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Royaume-Uni
    Description: pays d'Europe occidentale
    Country: ['Royaume-Uni']
    Aliases: {'en': ['United Kingdom of Great Britain and Northern Ireland', 'U K', 'G B', 'Great Britain', 'Great Britain and Northern Ireland', 'the United Kingdom of Great Britain and Northern Ireland', 'the UK', 'the United Kingdom'], 'fr': ["Royaume-Uni de Grande-Bretagne et d'Irlande du Nord", 'Royaume Uni', 'Royaume-Uni de Grande-Bretagne et Irlande du Nord', 'Royaume-uni', 'R.-U.', 'R.U.', 'Grande-Bretagne'], 'de': ['Vereinigtes Königreich Großbritannien und Nordirland', 'Großbritannien', 'U K', 'G B', 'G B R', 'Vereinigte Königreich']}
    Coordinates: [{'lat': 54.6, 'lon': -2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "reçu" — tense=Past, aspect=None, mood=None
      Sentence: "—Sir Strafford Norlhcole, secrétaire d'Elat des colonies, a reçu de sir Robert Napier la dépêche suivante, en dale de La"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.983

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'sir Robert Napier' and 'Grande-Bretagne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'sir Robert Napier' near 'Grande-Bretagne' around 1868-04-22?
  4. Resolve temporal expressions relative to 1868-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 108:
  Publication date : 1892-07-05
  Language         : de
  Person  : 'August Jabu'  (QID: N/A)
  Location: 'Berliner'  (QID: Q64)

  [ARTICLE TEXT — entity markers added]
  "Handels⸗ Zeitung des [E2] Berliner [/E2] Tageblatts . Nummer 335 . Juhaber iſt der Buchhändler Richard Heinrich zu Berlin . [E1] August Jabu [/E1] Jnbaber iſt der Kaufmann Max Franke zu Berlin ."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Berlin
    Description: Hauptstadt und bevölkerungsreichste Stadt der Bundesrepublik Deutschland
    Country: ['Mark Brandenburg', 'Brandenburg-Preußen', 'Königreich Preußen', 'Norddeutscher Bund', 'Q43287', 'Q41304', 'NS-Staat', 'Sowjetische Besatzungszone', 'Q16957', 'Q183', 'Bundesrepublik Deutschland bis 1990']
    Located in: ['Q148499', 'Brandenburg-Preußen', 'Q27306', 'Q700264', 'Q27306', 'Freistaat Preußen', 'Q7318', 'Q183']
    Aliases: {'en': ['Berlin, Germany', 'DE-BE'], 'de': ['Stadt Berlin', 'Berlin, Deutschland', 'Bundeshauptstadt Berlin', 'Land Berlin', 'DE-BE', 'Berlin (Deutschland)', 'BE', 'Bln', 'Bln.']}
    Coordinates: [{'lat': 52.516666666667, 'lon': 13.383333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 104 (0 = most prominent)
    OCR quality estimate: 0.975

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'August Jabu' and 'Berliner' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'August Jabu' near 'Berliner' around 1892-07-05?
  4. Resolve temporal expressions relative to 1892-07-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 109:
  Publication date : 1900-06-26
  Language         : en
  Person  : 'Henry C.\nPayne'  (QID: Q212679)
  Location: 'West Virginia'  (QID: Q1371)

  [ARTICLE TEXT — entity markers added]
  "Just before the adjournment of the national committee, on motion of Sena tor Scott of [E2] West Virginia [/E2], George Wls- woll of Milwaukee was unanimously elected sergeant-at arms of tin* nation al committee for four years. In the | place of II. L. Swords of New York, re- > signed. Ckaii-innu Ilanna to-night announced the names of the five members of the new executive committee of tin* nation al committee, as follows: Henry C. Payne."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Henry Clay Payne
    Description: American politician (1843-1904)
    Born: ['+1843-11-23T00:00:00Z']
    Died: ['+1904-10-04T00:00:00Z']
    Birth place: ['Ashfield']
    Death place: ['Washington, D.C.']
  Location Wikidata:
    Label: West Virginia
    Description: state of the United States of America
    Country: ['United States']
    Located in: ['United States']
    Aliases: {'en': ['The Mountain State', 'Almost Heaven', 'WV', 'West Virginia, United States', 'State of West Virginia', 'W. Va.', 'W.Va.', 'US-WV'], 'fr': ["Virginie de l'Ouest", 'WV'], 'de': ['West-Virginia', 'Staat West-Virginia', 'WV', 'Westvirginien']}
    Coordinates: [{'lat': 39, 'lon': -80.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: before
    Verb cluster: "announced" — tense=Past, aspect=None, mood=None
      Sentence: "Ckaii-innu Ilanna to-night announced the names of the five members of the new executive committee of tin* nation al comm"
    Verb cluster: "was elected" — tense=Past, aspect=Perf, mood=Ind
      Sentence: "Just before the adjournment of the national committee, on motion of Sena tor Scott of West Virginia, George Wls- woll of"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 10 (0 = most prominent)
    OCR quality estimate: 0.982

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Henry C.\nPayne' and 'West Virginia' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Henry C.\nPayne' near 'West Virginia' around 1900-06-26?
  4. Resolve temporal expressions relative to 1900-06-26. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 110:
  Publication date : 1938-05-06
  Language         : de
  Person  : 'früher«\nbeutschen Botschafters von Ribbentrop'  (QID: Q101886)
  Location: 'Buckinghampalast'  (QID: Q42182)

  [ARTICLE TEXT — entity markers added]
  "empfing am Donnerstag im [E2] Buckinghampalast [/E2] ben neuen deutschen Botschafter, Dr. Herbert von Dirksen, ber ihm sein Beglaubigungsschreiben unb bas Abberufungsschreiben bes früher« beutschen Botschafters von Ribbentrop überreichte."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Joachim von Ribbentrop
    Description: deutscher Politiker (NSDAP), MdR, Reichsaußenminister, Kriegsverbrecher
    Born: ['+1893-04-30T00:00:00Z']
    Died: ['+1946-10-16T00:00:00Z']
    Birth place: ['Wesel']
    Death place: ['Nürnberg', 'Zellengefängnis Nürnberg']
    Residences: ['Schweiz', 'England', 'Kanada', 'Deutschland', 'Dahlem']
  Location Wikidata:
    Label: Buckingham Palace
    Description: offizielle Londoner Residenz und Hauptarbeitsplatz des britischen Monarchen
    Country: ['Vereinigtes Königreich']
    Located in: ['City of Westminster']
    Aliases: {'en': ['Buckingham House', 'Buck House'], 'fr': ['Buckingham Palace'], 'de': ['Buckinghampalast', 'Buckingham Palast', 'Buckingham-Palast']}
    Coordinates: [{'lat': 51.501, 'lon': -0.142}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: früher, früh
    Verb cluster: "überreichte" — tense=Past, aspect=None, mood=Ind
      Sentence: "bas Abberufungsschreiben bes früher« beutschen Botschafters von Ribbentrop überreichte."
    Verb cluster: "empfing" — tense=Past, aspect=None, mood=Ind
      Sentence: "empfing am Donnerstag im Buckinghampalast ben neuen deutschen Botschafter, Dr. Herbert von Dirksen, ber ihm sein Beglaub"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.971

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'früher«\nbeutschen Botschafters von Ribbentrop' and 'Buckinghampalast' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'früher«\nbeutschen Botschafters von Ribbentrop' near 'Buckinghampalast' around 1938-05-06?
  4. Resolve temporal expressions relative to 1938-05-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 111:
  Publication date : 1960-04-06
  Language         : en
  Person  : 'Col. Gruenwald'  (QID: N/A)
  Location: 'Horry\nDistrict Scout Camporee'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Boy Scout Troop 843 of Loris won top honors at the Horry District Scout Camporee March 25-27 at Clear Pond between ( Conway and Myrtle Beach. Competing against some ot the finest units in the county, the boys won top honors after participating in Compassing, : rope throwing, Morse Code, hiking with compass and indi- ) vidual cooking. Friday night the troops! competing joined in a camp fire meeting and heard an ad dress by [E1] Col. Gruenwald [/E1], com manding officer of the Myrtle Beach Air Force Base."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after
    Verb cluster: "competing" — tense=Pres, aspect=Prog, mood=None
      Sentence: "competing joined in a camp fire meeting and heard an ad dress by Col. Gruenwald, com manding officer of the Myrtle Beach"
    Verb cluster: "won" — tense=Past, aspect=None, mood=None
      Sentence: "Boy Scout Troop 843 of Loris won top honors at the Horry District Scout Camporee March 25-27 at Clear Pond between ( Con"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 4 (0 = most prominent)
    OCR quality estimate: 0.966

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Col. Gruenwald' and 'Horry\nDistrict Scout Camporee' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Col. Gruenwald' near 'Horry\nDistrict Scout Camporee' around 1960-04-06?
  4. Resolve temporal expressions relative to 1960-04-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 112:
  Publication date : 1858-10-24
  Language         : de
  Person  : 'Graf Pcs di Villamarina,\nGeschäftsträger am französischen Hofe'  (QID: Q2215748)
  Location: 'T u r i n'  (QID: Q495)

  [ARTICLE TEXT — entity markers added]
  "Graf Pcs di Villamarina, Geschäftsträger am französischen Hofe, sowie Marchcsc d'Azeglio, Geschäftsträger am Hofe von St. James, weilen seit einigen Tagen in Turin und haben mit dem Minister» Präsidenten Grafen Cavour öftere und lange dauernde Conferenzcn. In mehreren picmontcsischcn Blätter wurde seit einiger Zeit Klage über die Art und Weise erhoben, in der die Behörden hinsichtlich der in den aufgehobenen Klöstern vorgefundenen Bibliotheken verfahren. das vertragsmäßige Recht achten zu wollen scheint, laßt den Prinzen von Carigoan eine mysteriöse Ncisc nach dem Norden von Teutschland machen, um, wenn nickt ein Schutz- und Trutzbündniß, so doch einen Neutra« litäts'Vertraz mit Preußen für den Krieg zu schließen, „zu welchem sich Piémont gegen Oesterreich vorberei tet." T"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Salvatore Pes di Villamarina
    Description: piemontesischer Offizier, Botschafter, Präfekt und Senator
    Born: ['+1808-08-31T00:00:00Z']
    Died: ['+1877-05-14T00:00:00Z']
    Birth place: ['Cagliari']
    Death place: ['Q495']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Verb cluster: "weilen" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Graf Pcs di Villamarina, Geschäftsträger am französischen Hofe, sowie Marchcsc d'Azeglio, Geschäftsträger am Hofe von St"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Graf Pcs di Villamarina,\nGeschäftsträger am französischen Hofe' and 'T u r i n' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Graf Pcs di Villamarina,\nGeschäftsträger am französischen Hofe' near 'T u r i n' around 1858-10-24?
  4. Resolve temporal expressions relative to 1858-10-24. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 113:
  Publication date : 1938-11-13
  Language         : de
  Person  : 'Siurgenenger'  (QID: N/A)
  Location: 'St. Mar\ngrethen'  (QID: Q66243)

  [ARTICLE TEXT — entity markers added]
  "Es handelt sich bei dem in Frage stehenden Pro jekt um die Umgestaltung des als „Alter Rhein" bezeichneten, reichgewundenen Wasserarms, der als Jahrzeichen der zwischen St. Margrethen und Boden see liegenden Niederungen das ganze sogenannte Alte Kheintal beherrscht (siehe Situationsbild). Bevor der bei Fußach mündende Rheinkanal angelegt und damit ein direkter Abfluß des Stroms in das große See becken geschaffen wurde, ergossen sich die Wasser des Oberrheins durch diesen Arm in den Bodensee, und oft war sein Bett viel zu eng, um sie zu fassen. Leider ist es freilich auch schon das Letzte! Ie: Dand [E1] Siurgenenger [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "handelt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Es handelt sich bei dem in Frage stehenden Pro jekt um die Umgestaltung des als „Alter Rhein" bezeichneten, reichgewunde"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 26 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Siurgenenger' and 'St. Mar\ngrethen' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Siurgenenger' near 'St. Mar\ngrethen' around 1938-11-13?
  4. Resolve temporal expressions relative to 1938-11-13. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 114:
  Publication date : 1898-11-07
  Language         : de
  Person  : 'Führer Görgey'  (QID: Q716001)
  Location: 'Ofner Festung'  (QID: Q46313)

  [ARTICLE TEXT — entity markers added]
  "Er eröffnete dem Ausschusse, der „König" habe den Wunsch ausgesprochen, das Denkmal seiner hohen Gemahlin möge genau an der Stelle angebracht werden, auf welcher bisher das Denkmal des Generals Hentzi steht, der Mitte des schönsten Platzes der Festung Ofen. Das Hentzi-Denkmal wolle der Kaiser auf seine Kosten entfernen und auf dem Fried hofe oder im Innern eines militärischen Gebäudes wieder aufrichten lassen. Sie dankt dem „König", für einen Entschluß, der einer Stimmung Rechnung trug, die von der „Unab hängigkeitspartei" vertreten wurde, während sie jetzt durch die Regierung verwirklicht wird. Wer waren die Truppen Görgeys, unter deren Schüssen General Hentzi und seine Tapferen ver bluteten?"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Artúr Görgei
    Description: ungarischer General
    Born: ['+1818-01-30T00:00:00Z', '+1818-02-05T00:00:00Z']
    Died: ['+1916-05-21T00:00:00Z']
    Birth place: ['Toporec']
    Death place: ['Budapest']
    Work locations: ['Budapest']
  Location Wikidata:
    Label: Budaer Burg
    Description: größtes Gebäude in Ungarn, Sehenswürdigkeit der Hauptstadt Budapest
    Country: ['Ungarn']
    Located in: ['I. Budapester Bezirk']
    Aliases: {'fr': ['château royal de Buda'], 'de': ['Budavári palota', 'Budavari palota', 'Burgpalast']}
    Coordinates: [{'lat': 47.496111111111, 'lon': 19.039722222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: jetzt
    Verb cluster: "waren" — tense=Past, aspect=None, mood=Ind
      Sentence: "Wer waren die Truppen Görgeys, unter deren Schüssen General Hentzi und seine Tapferen ver bluteten?"
    Verb cluster: "eröffnete" — tense=Past, aspect=None, mood=Ind
      Sentence: "Er eröffnete dem Ausschusse, der „König" habe den Wunsch ausgesprochen, das Denkmal seiner hohen Gemahlin möge genau an "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 10 (0 = most prominent)
    OCR quality estimate: 0.992

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Führer Görgey' and 'Ofner Festung' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Führer Görgey' near 'Ofner Festung' around 1898-11-07?
  4. Resolve temporal expressions relative to 1898-11-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 115:
  Publication date : 1848-10-21
  Language         : de
  Person  : 'HH. Reichskommissare Teichert'  (QID: N/A)
  Location: 'Mailand'  (QID: Q490)

  [ARTICLE TEXT — entity markers added]
  "[E2] Mailand [/E2]. Der gestern erwähnte Tagsbefehl Radetzky's lautet: „Soldaten! Frankfurt. Am 14. Oktober haben die HH."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Mailand
    Description: zweitgrößte Stadt Italiens, Hauptstadt der Lombardei
    Country: ['Italien', 'Königreich Italien', 'Kaisertum Österreich', 'Q165154', 'Q223936', 'Italienische Republik', 'Q213353', 'Q729481', 'Q153529', 'Signoria of Milan', 'Q80702']
    Located in: ['Q15121', 'Provinz Mailand', 'Q3924625', 'Q18288155', 'Q199728']
    Aliases: {'en': ['Milano', 'Milano, Italy', 'Milan, Italy', 'Mailand', 'Milan, Lombardy'], 'fr': ['Milano']}
    Coordinates: [{'lat': 45.466944444444, 'lon': 9.19}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: gestern
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 27 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'HH. Reichskommissare Teichert' and 'Mailand' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'HH. Reichskommissare Teichert' near 'Mailand' around 1848-10-21?
  4. Resolve temporal expressions relative to 1848-10-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 116:
  Publication date : 1928-01-17
  Language         : fr
  Person  : 'grande Uranie Montandon'  (QID: N/A)
  Location: 'Cœudres'  (QID: Q68532)

  [ARTICLE TEXT — entity markers added]
  ", comme l' appelaient ses amis) avait passé la majeure partie de g. vie dans cette vallée jurassienne où dans lés temps anciens vécurent (?) le Solitaire dès Sagnes et Gédéon le Contreleyu. Cet endroit avait été par lui choisi en une occasion mémorable, quand un beau jour, ou plutôt un malheureux soir, il s'était aventuré à demander Êour femme la [E1] grande Uranie Montandon [/E1] du ronillet. A sa complète stupéfaction, il lui fut répondu négativement. Quand il demanda les raisons de ce refus, elle lui déclara tout uniment « qu'il sentait trop l'horloger >. Pendant une heure ou deux, l'Alcide scngea à se noyer de dépit dans le lac des Tailleres, mais son bon sens lui revenant ei l'instinct de conservation aidant, il se borna à secouer sur ce Sol ingrat la poussière de ses souliers et, quelque temps plus tard, alla planter sa tente aux [E2] Cœudres [/E2], pensant que son noir chagrin se fondrait dans les brouillards de la Sagne."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: La Sagne
    Description: commune suisse
    Country: ['Suisse']
    Located in: ['canton de Neuchâtel']
    Aliases: {'en': ['Sagne', 'La Sagne NE'], 'de': ['La Sagne-Eglise', 'Les Coeudres', 'La Corbatière', 'Marmoud']}
    Coordinates: [{'lat': 47.0388, 'lon': 6.7988}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien, plus, tôt, tard
    Verb cluster: "choisi" — tense=Past, aspect=None, mood=None
      Sentence: "Cet endroit avait été par lui choisi en une occasion mémorable, quand un beau jour, ou plutôt un malheureux soir, il s'é"
    Verb cluster: "scngea" — tense=Past, aspect=None, mood=None
      Sentence: "Pendant une heure ou deux, l'Alcide scngea à se noyer de dépit dans le lac des Tailleres, mais son bon sens lui revenant"
    Verb cluster: "passé" — tense=Past, aspect=None, mood=None
      Sentence: ", comme l' appelaient ses amis) avait passé la majeure partie de g. vie dans cette vallée jurassienne où dans lés temps "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.981

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'grande Uranie Montandon' and 'Cœudres' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'grande Uranie Montandon' near 'Cœudres' around 1928-01-17?
  4. Resolve temporal expressions relative to 1928-01-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 117:
  Publication date : 1908-01-07
  Language         : fr
  Person  : 'M. Pichon'  (QID: Q1069292)
  Location: 'Madrid'  (QID: Q2807)

  [ARTICLE TEXT — entity markers added]
  "M. PIclaon à ffltadrid. [E1] M. Pichon [/E1], ministre des affaires étrangères, esl arrive' à [E2] Madrid [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Stephen Pichon
    Description: personnalité politique française
    Born: ['+1857-08-10T00:00:00Z']
    Died: ['+1933-09-18T00:00:00Z']
    Birth place: ['Arnay-le-Duc']
    Death place: ['Vers-en-Montagne']
    Work locations: ['Paris']
  Location Wikidata:
    Label: Madrid
    Description: capitale de l'Espagne
    Country: ['Espagne']
    Located in: ['communauté de Madrid', 'province de Madrid', 'Madrid']
    Aliases: {'fr': ['Madrid (Espagne)'], 'de': ['Madrid, Spanien']}
    Coordinates: [{'lat': 40.41694444444445, 'lon': -3.703333333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "arrive" — tense=Pres, aspect=None, mood=Ind
      Sentence: "M. Pichon, ministre des affaires étrangères, esl arrive' à Madrid."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.990

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Pichon' and 'Madrid' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Pichon' near 'Madrid' around 1908-01-07?
  4. Resolve temporal expressions relative to 1908-01-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 118:
  Publication date : 1848-10-21
  Language         : de
  Person  : 'Windischgrätz'  (QID: Q455008)
  Location: 'Brünn'  (QID: Q14960)

  [ARTICLE TEXT — entity markers added]
  "— Von [E2] Brünn [/E2] kamen uns in der Nacht vom 10. auf den 11. National garden zu Hülfe, von Grätz Studenten. Die Czechen dagegen schmieden allerlei Ränke gegen Wien. [E1] Windischgrätz [/E1], der mit 12,000 Mann von Prag abzog, um sich der Wiener Garnison anzuschließen, bekam vor seiner Abreise von Prag einen Fackelzug."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Alfred I. zu Windisch-Graetz
    Description: österreichischer Feldmarschall
    Born: ['+1787-05-11T00:00:00Z']
    Died: ['+1862-03-21T00:00:00Z']
    Birth place: ['Q9005']
    Death place: ['Wien']
  Location Wikidata:
    Label: Brünn
    Description: Stadt in Tschechien
    Country: ['Tschechien', 'Tschechoslowakei', 'Protektorat Böhmen und Mähren', 'Q33946', 'Q28513', 'Q131964', 'Q153136', 'Länder der Böhmischen Krone']
    Located in: ['Okres Brno-město', 'Markgrafschaft Mähren', 'Land of Moravia', 'Q10860593', 'Q11343779', 'Q850531']
    Aliases: {'en': ['Statutory City of Brno'], 'lb': ['Brünn']}
    Coordinates: [{'lat': 49.195277777778, 'lon': 16.608333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Verb cluster: "schmieden" — tense=Past, aspect=None, mood=Ind
      Sentence: "Die Czechen dagegen schmieden allerlei Ränke gegen Wien."
    Verb cluster: "kamen" — tense=Past, aspect=None, mood=Ind
      Sentence: "— Von Brünn kamen uns in der Nacht vom 10. auf den 11. National garden zu Hülfe, von Grätz Studenten."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 54 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Windischgrätz' and 'Brünn' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Windischgrätz' near 'Brünn' around 1848-10-21?
  4. Resolve temporal expressions relative to 1848-10-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 119:
  Publication date : 1981-11-17
  Language         : fr
  Person  : 'Jeanne Ney'  (QID: N/A)
  Location: 'Halles'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "L'amour de [E1] Jeanne Ney [/E1] », de G .-W. Pabst . PALAIS DE BEAULIEU [E2] Halles [/E2] I et 2 j"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 30 (0 = most prominent)
    OCR quality estimate: 0.778

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Jeanne Ney' and 'Halles' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Jeanne Ney' near 'Halles' around 1981-11-17?
  4. Resolve temporal expressions relative to 1981-11-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 120:
  Publication date : 1920-06-17
  Language         : en
  Person  : 'Moses'  (QID: Q9077)
  Location: 'Nashville, Tenn.'  (QID: Q23197)

  [ARTICLE TEXT — entity markers added]
  "[E2] Nashville, Tenn. [/E2] (Special)—How a band of Jewish war refugees have just staged a modern exoudus from Egypt ant suffered tribulations strikingly similar to those undergone by the band that [E1] Moses [/E1] led of old ia recount ed in a Zionist report made public here."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Moses
    Description: Abrahamic prophet said to have led the Israelites out of Egypt
    Born: ['-1393-00-00T00:00:00Z', '-1526-00-00T00:00:00Z', '-2000-00-00T00:00:00Z']
    Died: ['-1273-00-00T00:00:00Z', '-1406-00-00T00:00:00Z', '-1500-00-00T00:00:00Z']
    Birth place: ['Helwan']
    Death place: ['Mount Nebo']
    Residences: ['Egypt', 'Sinai Peninsula', 'Midian']
  Location Wikidata:
    Label: Nashville
    Description: capital and largest city of Tennessee, United States
    Country: ['United States']
    Located in: ['Davidson County']
    Aliases: {'en': ['Nashville, Tennessee', 'Nashville–Davidson County', 'Metropolitan Government of Nashville and Davidson County', 'Nashville, TN', 'Nashville, Tenn.'], 'de': ['Nashville, Tennessee']}
    Coordinates: [{'lat': 36.16222222222222, 'lon': -86.77444444444444}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "have staged" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "Nashville, Tenn. (Special)—How a band of Jewish war refugees have just staged a modern exoudus from Egypt ant suffered t"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.986

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Moses' and 'Nashville, Tenn.' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Moses' near 'Nashville, Tenn.' around 1920-06-17?
  4. Resolve temporal expressions relative to 1920-06-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 121:
  Publication date : 1810-04-14
  Language         : en
  Person  : 'J. li. Varniim.\nSpeaker of the House of Representatives'  (QID: Q1706673)
  Location: 'Virginia'  (QID: Q1370)

  [ARTICLE TEXT — entity markers added]
  "AN ACT To extend the time for locating [E2] Virginia [/E2] military land warrants, and for returning the surveys there on to the Secretary of the Department ot War. B E it enacted by the Senate and House §f Representatives o f the United States of America, in Congress assembled, That the officers and soldiers of the Virginia line on continental establishment, their heirs or as signs entitled to bounty lands within the tract reserved by Virginia, between the lit tle Miami and Sciota rivers, for satisfying the legal bounties to her officers and soldi ers upon continental establishment, shall be allowed a further term of five years, from and after the passage of this act, to obtain warrants and complete their locations, and a further term of seven years, from and as ter the passage of this act as aforesaid, to return their surveys and warrants to the of sice of the Secretary of the War Depart ment, any thing in any former act to the contrary notwithstanding- Provided , That no locations as aforesaid within the above mentioned tract shall after the passing of this act he made on tracts of land for which patents had previously been issued or which had been previously surveyed, and any pa tent which may nevertheless be obtained for land located contrary to the provisions of this section, shall be considered as null and void. J. li."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Joseph Bradley Varnum
    Description: American politician (1751-1821)
    Born: ['+1751-01-29T00:00:00Z']
    Died: ['+1821-09-21T00:00:00Z', '+1821-09-11T00:00:00Z']
    Birth place: ['Dracut']
    Death place: ['Dracut']
    Residences: ['Massachusetts']
    Work locations: ['Washington, D.C.', 'Boston']
  Location Wikidata:
    Label: Virginia
    Description: state of the United States of America
    Country: ['United States']
    Located in: ['United States']
    Aliases: {'en': ['Commonwealth of Virginia', 'State of Virginia', 'VA', 'Virginia, United States', 'Old Dominion', 'Va.', 'US-VA'], 'de': ['Virginien']}
    Coordinates: [{'lat': 37.5, 'lon': -79}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after
    Verb cluster: "To extend" — tense=None, aspect=None, mood=None
      Sentence: "AN ACT To extend the time for locating Virginia military land warrants, and for returning the surveys there on to the Se"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.989

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'J. li. Varniim.\nSpeaker of the House of Representatives' and 'Virginia' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'J. li. Varniim.\nSpeaker of the House of Representatives' near 'Virginia' around 1810-04-14?
  4. Resolve temporal expressions relative to 1810-04-14. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 122:
  Publication date : 1878-10-02
  Language         : de
  Person  : 'Fröbel'  (QID: Q76679)
  Location: 'Italien'  (QID: Q172579)

  [ARTICLE TEXT — entity markers added]
  "[E2] Italien [/E2] zeigt in seiner Ausstellung deutlich, daß es den guten Willen hat, für die Schulen etwas zu thun, daß es aber bis anhin nicht weiter gekommen ist, als einige gute Vorbilder zu schaffen. Die ausgestellten Schul apparate und Instrumente sind außerordentlich schön, sie zeugen von der Hochachtung der Behörden für die Schule — aber wo sind solche Veranschaulichungsmittel wirklich im Gebrauch; wo die Volksschulen, welche sie besitzen? — Mailand stellt Arbeiten der [E1] Fröbel [/E1]schulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die Kinder weit überschreiten:"

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Königreich Italien
    Description: historischer Staat von 1861 bis 1946
    Aliases: {'en': ['Regno d’Italia', 'Italy'], 'fr': ["L'Italie après l'unification", "Histoire de l'Italie de l'unification à la Première Guerre mondiale", 'Royaume d’Italie', "Histoire de l'Italie de l'unification a la Premiere Guerre mondiale"]}
    Coordinates: [{'lat': 41.9, 'lon': 12.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "stellt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "— Mailand stellt Arbeiten der Fröbelschulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die "
    Verb cluster: "zeigt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Italien zeigt in seiner Ausstellung deutlich, daß es den guten Willen hat, für die Schulen etwas zu thun, daß es aber bi"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 27 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Fröbel' and 'Italien' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Fröbel' near 'Italien' around 1878-10-02?
  4. Resolve temporal expressions relative to 1878-10-02. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 123:
  Publication date : 1948-07-19
  Language         : de
  Person  : 'Einanzminister\nFene Hage'  (QID: Q382070)
  Location: 'Frankreich'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "Man rechnet namentlich damit, dals für Grolbritannien Senatzanzler Sir Stafford C'ripye und für [E2] Frankreich [/E2] Einanzminister Fene Hage; erscheinen werden. Bei dieser Gelenenheit wird vohi eine allgemeine Aus prache über die Ddurehführune des Mars!nll Plancs Kattfinden. Der Europäische Wirtschaftsrat hat be schlonsen, den ihm von amenilennischer Seite gemnchten Vorsehing anzunchmen und sic mit der Verteilung der amerihanischen Hise an seine Mitelieder zu befassen. Dur Vorherei tung des Verteilungsprogrammes ist im Nahmen der ständigen Konunission für euro pilische Wirtschaftszusammenurheit ein betzon deres nur aus vier Mityliedern besktchendes Unterkcomitee gebildet vorden, in dem der Ver treter Grollbnitanniens den Vorsit» führt und dem ferner Vertreter Frankreichs, Italiens und Hollands angchören."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: René Mayer
    Description: französischer Politiker
    Born: ['+1895-05-04T00:00:00Z']
    Died: ['+1972-12-13T00:00:00Z']
    Birth place: ['8. Arrondissement von Paris']
    Death place: ['7. Arrondissement von Paris']
    Work locations: ['Paris']
  Location Wikidata:
    Label: Frankreich
    Description: Staat in Westeuropa mit Überseegebieten
    Country: ['Frankreich']
    Aliases: {'en': ['French Republic'], 'fr': ['République française', 'RF', 'fr', 'la République française', 'Fr.', 'La France', "L'Hexagone"], 'de': ['Französische Republik', 'fr', 'RF']}
    Coordinates: [{'lat': 47, 'lon': 2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "rechnet" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Man rechnet namentlich damit, dals für Grolbritannien Senatzanzler Sir Stafford C'ripye und für Frankreich Einanzministe"
    Verb cluster: "ist" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Dur Vorherei tung des Verteilungsprogrammes ist im Nahmen der ständigen Konunission für euro pilische Wirtschaftszusamme"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.980

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Einanzminister\nFene Hage' and 'Frankreich' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Einanzminister\nFene Hage' near 'Frankreich' around 1948-07-19?
  4. Resolve temporal expressions relative to 1948-07-19. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 124:
  Publication date : 1810-04-14
  Language         : en
  Person  : 'JAMES MADISON'  (QID: Q11813)
  Location: 'United States of\nAmerica'  (QID: Q30)

  [ARTICLE TEXT — entity markers added]
  "B E it enacted by the Senate and House §f Representatives o f the United States of America, in Congress assembled, That the officers and soldiers of the Virginia line on continental establishment, their heirs or as signs entitled to bounty lands within the tract reserved by Virginia, between the lit tle Miami and Sciota rivers, for satisfying the legal bounties to her officers and soldi ers upon continental establishment, shall be allowed a further term of five years, from and after the passage of this act, to obtain warrants and complete their locations, and a further term of seven years, from and as ter the passage of this act as aforesaid, to return their surveys and warrants to the of sice of the Secretary of the War Depart ment, any thing in any former act to the contrary notwithstanding- Provided , That no locations as aforesaid within the above mentioned tract shall after the passing of this act he made on tracts of land for which patents had previously been issued or which had been previously surveyed, and any pa tent which may nevertheless be obtained for land located contrary to the provisions of this section, shall be considered as null and void. Approved. [E1] JAMES MADISON [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: James Madison
    Description: President of the United States from 1809 to 1817 (1751–1836)
    Born: ['+1751-03-16T00:00:00Z']
    Died: ['+1836-06-28T00:00:00Z']
    Birth place: ['Port Conway']
    Death place: ['Montpelier']
    Work locations: ['Washington, D.C.']
  Location Wikidata:
    Label: United States
    Description: country located primarily in North America
    Country: ['United States']
    Aliases: {'en': ['the States', 'the United States of America', 'US of America', 'the US', 'the U.S.', 'the US of A', 'U.S. of America', 'the US of America', 'the USA', 'the U.S.A.', 'the U.S. of A', 'US of A', 'the U.S. of America', 'the United States', 'Merica', 'Murica', 'United States of America', 'U.S.', 'U.S.A.', 'U. S.', 'U. S. A.', 'America'], 'fr': ['É.-U.', 'É-U', 'É-U.', 'E.-U.', 'É.U.', 'les États', 'Oncle Sam', 'Amérique', 'Etats-Unis', 'States', 'les États-Unis d’Amérique', 'États-unis', 'ÉU', 'É.-U. A.', "Pays de l'Oncle Sam", 'Etats-unis', 'États-Unis d’Amérique', 'pays de l’Oncle Sam'], 'de': ['Vereinigte Staaten von Amerika', 'US-Amerika', 'U.S.-Amerika', 'Staaten von Amerika', 'VSA', 'V.S.A.', 'V. S. A.', 'Staaten', 'die Staaten', 'VS', 'V.S.', 'V. S.', 'Amerika', 'U.S.A.', 'U. S. A.', 'United States of America', 'United States', 'U.S.', 'U. S.', 'America'], 'lb': ['Vereenegt Staaten']}
    Coordinates: [{'lat': 39.828175, 'lon': -98.5795}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after
    Verb cluster: "Approved" — tense=Past, aspect=Perf, mood=None
      Sentence: "Approved."
    Verb cluster: "assembled" — tense=Past, aspect=None, mood=None
      Sentence: "B E it enacted by the Senate and House §f Representatives o f the United States of America, in Congress assembled, That "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 7 (0 = most prominent)
    OCR quality estimate: 0.989

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'JAMES MADISON' and 'United States of\nAmerica' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'JAMES MADISON' near 'United States of\nAmerica' around 1810-04-14?
  4. Resolve temporal expressions relative to 1810-04-14. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 125:
  Publication date : 1961-12-21
  Language         : fr
  Person  : 'Van Looy'  (QID: N/A)
  Location: 'Herentals'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Rilc van Looy n'est pas content. Le champion du monde sur route a déclaré : « Personnellement, j'estime que quatre étapes contre le chronomètre nuisent à l'intérêt général d'un Tour. Quant à l'étape contre la montre par équipes, organisée par hasard à [E2] Herentals [/E2], le village de Rilc van Looy, c'est une mauvaise plaisanterie que l'on aurait souhaité ne plus revoir dans une épreuve de l'importance du Tour."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Verb cluster: "est content" — tense=Pres, aspect=None, mood=Ind [NEGATED]
      Sentence: "Rilc van Looy n'est pas content."
    Verb cluster: "est plaisanterie" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Quant à l'étape contre la montre par équipes, organisée par hasard à Herentals, le village de Rilc van Looy, c'est une m"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.988

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Van Looy' and 'Herentals' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Van Looy' near 'Herentals' around 1961-12-21?
  4. Resolve temporal expressions relative to 1961-12-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 126:
  Publication date : 1890-11-06
  Language         : en
  Person  : 'S. H. Clifford'  (QID: N/A)
  Location: 'Harrisburg,\nIII.'  (QID: Q576252)

  [ARTICLE TEXT — entity markers added]
  "[E1] S. H. Clifford [/E1], New Cassel, Wis., was troubled with neuralgia and rheumatism, his stomach was disor dered, bis liver was affected to an alarming degree, appetite fell away and he was terribly reduced in flesb and strength. Three bottles of Elec trie Bitters cured him. Edward Shepherd, Harrisburg, III., bad a running sore on his leg of eight years’ standing."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Harrisburg
    Description: county seat of Saline County, Illinois, United States
    Country: ['United States']
    Located in: ['Saline County']
    Aliases: {'en': ['Harrisburg, Illinois', 'Harrisburg, IL']}
    Coordinates: [{'lat': 37.733888888889, 'lon': -88.545833333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "fell" — tense=Past, aspect=None, mood=None
      Sentence: "S. H. Clifford, New Cassel, Wis., was troubled with neuralgia and rheumatism, his stomach was disor dered, bis liver was"
    Verb cluster: "running" — tense=Pres, aspect=Prog, mood=None
      Sentence: "Edward Shepherd, Harrisburg, III., bad a running sore on his leg of eight years’ standing."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.992

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'S. H. Clifford' and 'Harrisburg,\nIII.' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'S. H. Clifford' near 'Harrisburg,\nIII.' around 1890-11-06?
  4. Resolve temporal expressions relative to 1890-11-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 127:
  Publication date : 1868-02-19
  Language         : de
  Person  : 'Georg'  (QID: Q57428)
  Location: 'Elſaß'  (QID: Q1142)

  [ARTICLE TEXT — entity markers added]
  "Aufenthalt in Hietzing , die Regierung dann verpflichtet ſein wird , das Während die preußiſche Regierung dem früheren König von Hannover die größte und edelſte Rückſicht zu Theil werden läßt , während andererſeits ihre Fürſorge für die neue Provinz unter der be — des Königs [E1] Georg [/E1] und ſeiner Umgebung in Hietzing die verwerflichen Verſuche fortgeſetzt , einen Theil ſeiner früheren Unterthanen , meiſt aus den unterſten Ständen , für das völlige boffnungsloſe und thörichte Unternehmen einer Wiederherſtellung ſeines Thrones zu gewinnen . zwiſchen Vor Kurzem begab ſich nun dieſe ſogenannte » Hannoverſche Legion unmittelbar an der deutſchen Grenze Aufenthalt nahm . Hannoversche Legion « aus der Schweiz nach Frankreich , wo ſie zunaͤchſt im [E2] Elſaß [/E2] So ungefährlich dies thörichte Unternehmen iſt , ſo mußte es doch Befremden erregen , daß eine offenbar gegen Preußen gerüſtete Schaar hannoverſcher Flüchtlinge ihre Ueberſiedelung von der Schweiz nach Frankreich mit Hülfe öſterreichiſcher Päſſe bewerkſtelligt hatte und daß dieſelbe in Frankreich , wie es zuerſt hieß , entgegenkommende Aufnahme von Seiten der Behörden fand ."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Georg V. von Hannover
    Description: König von Hannover, Deutschland
    Born: ['+1819-05-27T00:00:00Z']
    Died: ['+1878-06-12T00:00:00Z']
    Birth place: ['Berlin']
    Death place: ['Paris']
    Work locations: ['Berlin', 'Q84', 'Hannover']
  Location Wikidata:
    Label: Elsass
    Description: historische und kulturelle Region und Gebietskörperschaft im Osten Frankreichs
    Country: ['Frankreich']
    Located in: ['Grand Est', 'Königreich Frankreich', 'Königreich Frankreich', 'Königreich Frankreich']
    Aliases: {'en': ['Elsass'], 'de': ['Elsaß']}
    Coordinates: [{'lat': 48.5, 'lon': 7.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: früher, nach, vor, früh
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Aufenthalt in Hietzing , die Regierung dann verpflichtet ſein wird , das Während die preußiſche Regierung dem früheren K"
    Verb cluster: "mußte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Hannoversche Legion « aus der Schweiz nach Frankreich , wo ſie zunaͤchſt im Elſaß So ungefährlich dies thörichte Unterne"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 29 (0 = most prominent)
    OCR quality estimate: 0.994

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Georg' and 'Elſaß' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Georg' near 'Elſaß' around 1868-02-19?
  4. Resolve temporal expressions relative to 1868-02-19. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 128:
  Publication date : 1928-01-17
  Language         : fr
  Person  : 'Gédéon le Contreleyu'  (QID: N/A)
  Location: 'lac des Tailleres'  (QID: Q671611)

  [ARTICLE TEXT — entity markers added]
  ", comme l' appelaient ses amis) avait passé la majeure partie de g. vie dans cette vallée jurassienne où dans lés temps anciens vécurent (?) le Solitaire dès Sagnes et [E1] Gédéon le Contreleyu [/E1]. Cet endroit avait été par lui choisi en une occasion mémorable, quand un beau jour, ou plutôt un malheureux soir, il s'était aventuré à demander Êour femme la grande Uranie Montandon du ronillet. A sa complète stupéfaction, il lui fut répondu négativement. Quand il demanda les raisons de ce refus, elle lui déclara tout uniment « qu'il sentait trop l'horloger >. Pendant une heure ou deux, l'Alcide scngea à se noyer de dépit dans le [E2] lac des Tailleres [/E2], mais son bon sens lui revenant ei l'instinct de conservation aidant, il se borna à secouer sur ce Sol ingrat la poussière de ses souliers et, quelque temps plus tard, alla planter sa tente aux Cœudres, pensant que son noir chagrin se fondrait dans les brouillards de la Sagne."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: lac des Taillères
    Description: lac suisse
    Country: ['Suisse']
    Located in: ['canton de Neuchâtel']
    Aliases: {'en': ['Lac des Tailleres'], 'fr': ['Lac des Tailleres']}
    Coordinates: [{'lat': 46.966944444444, 'lon': 6.5747222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien, plus, tôt, tard
    Verb cluster: "passé" — tense=Past, aspect=None, mood=None
      Sentence: ", comme l' appelaient ses amis) avait passé la majeure partie de g. vie dans cette vallée jurassienne où dans lés temps "
    Verb cluster: "scngea" — tense=Past, aspect=None, mood=None
      Sentence: "Pendant une heure ou deux, l'Alcide scngea à se noyer de dépit dans le lac des Tailleres, mais son bon sens lui revenant"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 1 (0 = most prominent)
    OCR quality estimate: 0.981

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Gédéon le Contreleyu' and 'lac des Tailleres' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Gédéon le Contreleyu' near 'lac des Tailleres' around 1928-01-17?
  4. Resolve temporal expressions relative to 1928-01-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 129:
  Publication date : 1961-01-20
  Language         : fr
  Person  : 'Stern'  (QID: N/A)
  Location: 'Lamalou-les-Bains'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Le Dr [E1] Stern [/E1], directeur de la clinique de rééducation de [E2] Lamalou-les-Bains [/E2], a rendu visite à Roger Rivière, qu'il avait soigné le premier après sa chute dans le Tour de France."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: après
    Verb cluster: "soigné" — tense=Past, aspect=None, mood=None
      Sentence: "Le Dr Stern, directeur de la clinique de rééducation de Lamalou-les-Bains, a rendu visite à Roger Rivière, qu'il avait s"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 18 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Stern' and 'Lamalou-les-Bains' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Stern' near 'Lamalou-les-Bains' around 1961-01-20?
  4. Resolve temporal expressions relative to 1961-01-20. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 130:
  Publication date : 1938-12-12
  Language         : de
  Person  : 'Führer\nder „Undo", Mudry,'  (QID: Q7917056)
  Location: 'Ostgaliziens'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Die Entstehung des autonomen Karpatho rußland das von deutscher Seite bewußt als „Karpathoukraine" bezeichnet wird, im Rahmen des tschechoslowakischen Staates hat einen starken Einfluß auf die Verhältnisse in Ostgalizien ausgeübt, dessen Bevölkerung mehrheitlich ukrai nischer Nationalität ist. Das Verhältnis zwischen den Polen und Ukrainern in Ostgalizien war nie herzlich oder auch nur zufriedenstellend. Ihre Anhänger murren immer vernehmlicher, und es bleibt der Partei daher nichts anderes übrig, als daraus die Konsequenzen zu ziehen und der Regierung gegenüber entschiedener aufzutreten. Der Führer der „Undo", Mudry, hielt am 3. Dezember im Seim eine ziemlich scharfe Rede, in der er den inzwischen eingebrachten Antrag über die Ge währung einer territorialen Autono mie für Ostgalizien ankündigte."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Wassyl Mudryj
    Description: ukrainischer Journalist, Politiker und politischer Aktivist
    Born: ['+1893-03-19T00:00:00Z']
    Died: ['+1966-03-19T00:00:00Z']
    Birth place: ['Wikno']
    Death place: ['Yonkers']
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "hielt" — tense=Past, aspect=None, mood=Ind
      Sentence: "Der Führer der „Undo", Mudry, hielt am 3. Dezember im Seim eine ziemlich scharfe Rede, in der er den inzwischen eingebra"
    Verb cluster: "hat" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Die Entstehung des autonomen Karpatho rußland das von deutscher Seite bewußt als „Karpathoukraine" bezeichnet wird, im R"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 25 (0 = most prominent)
    OCR quality estimate: 0.983

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Führer\nder „Undo", Mudry,' and 'Ostgaliziens' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Führer\nder „Undo", Mudry,' near 'Ostgaliziens' around 1938-12-12?
  4. Resolve temporal expressions relative to 1938-12-12. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 131:
  Publication date : 1928-05-06
  Language         : fr
  Person  : 'Dr Doxiadès'  (QID: Q16524004)
  Location: 'Grèce'  (QID: Q41)

  [ARTICLE TEXT — entity markers added]
  "Pour les enfants sinistrés de Bulgarie et de [E2] Grèce [/E2] Mgr. Stéphane, archevêque de Sofia, rient d'adresser à l'Union internationale de secours aux enfants une dépêche, où, après avoir rendu hommage à cette institution, il s'exprime comme suit : La solidarité humaine ae manifeste le plue sensiblement dane les heures critiques. En outre, elle a fourni des couvertures à l'hôpital de dix baraques ouvert près de Philippopoli par le chef de la garnison de cette ville, le général Koutzeroff. D'Athènes, le [E1] Dr Doxiadès [/E1], ancien ministre, président de la Ligue patriotique d'assistance aux enfants, télégraphie à l'U."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Apostolos Doxiadis
    Description: homme politique grec
    Born: ['+1873-00-00T00:00:00Z']
    Died: ['+1942-00-00T00:00:00Z']
    Birth place: ['Assénovgrad']
    Death place: ['Athènes']
  Location Wikidata:
    Label: Grèce
    Description: pays d'Europe du Sud-Est indépendant depuis 1822
    Country: ['Grèce']
    Aliases: {'en': ['Hellenic Republic', 'Hellas', 'gr', 'el', 'Greek Republic', 'Ellada', 'Hellas, Greece'], 'fr': ['République hellénique', 'Grece', 'Hellas, Grèce'], 'de': ['Hellas', 'Hellenische Republik', 'Hellas, Griechenland'], 'lb': ['Griichenland']}
    Coordinates: [{'lat': 38.5, 'lon': 23}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien, après
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.984

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Dr Doxiadès' and 'Grèce' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Dr Doxiadès' near 'Grèce' around 1928-05-06?
  4. Resolve temporal expressions relative to 1928-05-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 132:
  Publication date : 1818-01-06
  Language         : de
  Person  : 'Prinz Leopold von Koburg'  (QID: Q12971)
  Location: 'Claremont'  (QID: Q1095337)

  [ARTICLE TEXT — entity markers added]
  "Der [E1] Prinz Leopold von Koburg [/E1] wurde fortwährend durch seinen übeln Gesundheitszustand in [E2] Claremont [/E2] zu rückgehalten."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Leopold I.
    Description: König der Belgier (1831–1865)
    Born: ['+1790-12-16T00:00:00Z']
    Died: ['+1865-12-10T00:00:00Z']
    Birth place: ['Coburg']
    Death place: ['Q730506']
  Location Wikidata:
    Label: Claremont House
    Description: Landsitz in der englischen Grafschaft Surrey
    Country: ['Vereinigtes Königreich']
    Located in: ['Elmbridge']
    Aliases: {'en': ['Claremont House'], 'fr': ['Claremont house']}
    Coordinates: [{'lat': 51.359444444444, 'lon': -0.36833333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "wurde" — tense=Past, aspect=None, mood=Ind
      Sentence: "Der Prinz Leopold von Koburg wurde fortwährend durch seinen übeln Gesundheitszustand in Claremont zu rückgehalten."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.970

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Prinz Leopold von Koburg' and 'Claremont' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Prinz Leopold von Koburg' near 'Claremont' around 1818-01-06?
  4. Resolve temporal expressions relative to 1818-01-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 133:
  Publication date : 1920-04-22
  Language         : en
  Person  : 'Bob Maggart'  (QID: N/A)
  Location: 'France'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "If I do I still want your custom and trade [E1] Bob Maggart [/E1]. I understand you did not get killed in [E2] France [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: France
    Description: country in Western Europe and other continents (through its overseas territories in America, Africa and Oceania)
    Country: ['France']
    Aliases: {'en': ['French Republic'], 'fr': ['République française', 'RF', 'fr', 'la République française', 'Fr.', 'La France', "L'Hexagone"], 'de': ['Französische Republik', 'fr', 'RF']}
    Coordinates: [{'lat': 47, 'lon': 2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "want" — tense=Pres, aspect=None, mood=None
      Sentence: "If I do I still want your custom and trade Bob Maggart."
    Verb cluster: "understand" — tense=Pres, aspect=None, mood=None
      Sentence: "I understand you did not get killed in France."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 15 (0 = most prominent)
    OCR quality estimate: 0.992

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Bob Maggart' and 'France' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Bob Maggart' near 'France' around 1920-04-22?
  4. Resolve temporal expressions relative to 1920-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 134:
  Publication date : 1828-05-10
  Language         : de
  Person  : 'Hr. Alt-Kan\ntonsseckelmeister Nazar Richlin'  (QID: N/A)
  Location: 'Schwyz'  (QID: Q12433)

  [ARTICLE TEXT — entity markers added]
  "Die in [E2] Schwyz [/E2] versammelte Kantonsgemeinde am 4. May war zahlreich und gieng in Ruhe und Stille vorüber, ungeachtet ein paar Gegenstände die Gemüther in Spannung setzten. Nachdem Herr Landammann J. Martin Hediger die Landsgemeinde mit einer Anrede eröffnet hatte, erhob sich ein Landmann mit dem Antrag: daß man das in Lachen errichtete Werbdepot für drey Kompagnien, welches seiner Zeit dem Hr. Oberst Salis-Soglio bewilligt ward, aufheben möchte. Hr. Kan tonsstatthalter Dominik Jütz ward als Landammann, und Hr. Alt-Kan tonsseckelmeister Nazar Richlin als Statthalter für die nächsten zwey Jahre gewählt, und auf die Tagsatzung Hr. Landammann Jütz und Hr. Landammann Hediger bestimmt."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Kanton Schwyz
    Description: Kanton der Schweiz
    Country: ['Schweiz']
    Located in: ['Schweiz']
    Aliases: {'en': ['Schwytz', 'Kanton Schwyz', 'Canton of Schwytz', 'SZ'], 'fr': ['Schwytz', 'Schwyz', 'canton de Schwyz', 'SZ'], 'de': ['SZ', 'Schwyz'], 'lb': ['SZ', 'Kanton Schwyz']}
    Coordinates: [{'lat': 47.066666666667, 'lon': 8.75}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Verb cluster: "ward" — tense=Past, aspect=None, mood=Ind
      Sentence: "Kan tonsstatthalter Dominik Jütz ward als Landammann, und Hr. Alt-Kan tonsseckelmeister Nazar Richlin als Statthalter fü"
    Verb cluster: "war" — tense=Past, aspect=None, mood=Ind
      Sentence: "Die in Schwyz versammelte Kantonsgemeinde am 4. May war zahlreich und gieng in Ruhe und Stille vorüber, ungeachtet ein p"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 11 (0 = most prominent)
    OCR quality estimate: 0.984

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Hr. Alt-Kan\ntonsseckelmeister Nazar Richlin' and 'Schwyz' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Hr. Alt-Kan\ntonsseckelmeister Nazar Richlin' near 'Schwyz' around 1828-05-10?
  4. Resolve temporal expressions relative to 1828-05-10. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 135:
  Publication date : 1920-07-08
  Language         : en
  Person  : 'Mansfield Judd'  (QID: N/A)
  Location: 'Cookeville'  (QID: Q2456192)

  [ARTICLE TEXT — entity markers added]
  "RAWLEY AGAIN Haven’t b en satisfied since I left [E2] Cookeville [/E2] until now. I seemed like I was almost lost, as I stayed in Gainesboro about IS months or 2 years. So, If you want to learn any fresh news just call around at D. A. Rawley’s place and you can find It out. If I don’t know, some one will be here to tell you, as they are always posted, and I am, too If you want to make a flying trip anywhere on the dirt road, Cooke ville is the place to come to hire a car."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Cookeville
    Description: city in Tennessee, United States
    Country: ['United States']
    Located in: ['Putnam County']
    Aliases: {'en': ['Cookeville, Tennessee', 'Cookeville, TN']}
    Coordinates: [{'lat': 36.164202, 'lon': -85.504295}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now
    Verb cluster: "Have" — tense=Pres, aspect=None, mood=Ind
      Sentence: "RAWLEY AGAIN Haven’t b en satisfied since I left Cookeville until now."
    Verb cluster: "will be" — tense=None, aspect=None, mood=None
      Sentence: "If I don’t know, some one will be here to tell you, as they are always posted, and I am, too If you want to make a flyin"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 11 (0 = most prominent)
    OCR quality estimate: 0.993

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mansfield Judd' and 'Cookeville' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mansfield Judd' near 'Cookeville' around 1920-07-08?
  4. Resolve temporal expressions relative to 1920-07-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 136:
  Publication date : 1898-11-07
  Language         : de
  Person  : 'Kaiser Franz Josef'  (QID: Q51056)
  Location: 'Ungarns'  (QID: Q28)

  [ARTICLE TEXT — entity markers added]
  "Gar eigenartige Gedanken, schreibt unser Wiener VKorrespondent, sind es, die der soeben bekannt gewordene, in ganz Ungarn leiden schaftlich bejubelte Entschluß des Kaisers in den deutschen, d. h. in den einzigen noch gut altösterreichischen Kreisen hervorruft. Dem Fernstehenden mag vielleicht Verständnis und Gefühl für diese Auslegung der Sache mangeln. Wer waren die Truppen Görgeys, unter deren Schüssen General Hentzi und seine Tapferen ver bluteten? Es waren die Truppen des „Gouver neurs" Kossuth und des Debrecziner Landtags, der den Kaiser Franz Joseph und die Dynastie Habsburg des ungarischen Thrones für verlustig erklärt hatte."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Franz Joseph I.
    Description: Kaiser von Österreich, Apostolischer König von Ungarn, König von Böhmen (1848–1916)
    Born: ['+1830-08-18T00:00:00Z']
    Died: ['+1916-11-21T00:00:00Z']
    Birth place: ['Q131330']
    Death place: ['Schloss Schönbrunn']
    Residences: ['Hofburg', 'Q46313']
    Work locations: ['Wien', 'Q250984', 'Q81137']
  Location Wikidata:
    Label: Ungarn
    Description: Staat in Mitteleuropa
    Country: ['Ungarn']
    Aliases: {'fr': ['la Hongrie']}
    Coordinates: [{'lat': 47, 'lon': 19}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "waren" — tense=Past, aspect=None, mood=Ind
      Sentence: "Es waren die Truppen des „Gouver neurs" Kossuth und des Debrecziner Landtags, der den Kaiser Franz Joseph und die Dynast"
    Verb cluster: "schreibt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Gar eigenartige Gedanken, schreibt unser Wiener VKorrespondent, sind es, die der soeben bekannt gewordene, in ganz Ungar"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 12 (0 = most prominent)
    OCR quality estimate: 0.992

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Kaiser Franz Josef' and 'Ungarns' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Kaiser Franz Josef' near 'Ungarns' around 1898-11-07?
  4. Resolve temporal expressions relative to 1898-11-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 137:
  Publication date : 1874-08-25
  Language         : de
  Person  : 'Zwicker'  (QID: N/A)
  Location: 'Schleſten'  (QID: Q81720)

  [ARTICLE TEXT — entity markers added]
  "Oieſf wird ſich in Kürze konſtttuiren , und werden den Aufſichtzratt derſelben bilden : der Gebeime Commerzienratb [E1] Zwicker [/E1] für die Firma Gebrüder Schickler der Geheime Cemmerzienratt v . Bleichroeder für die ſitrma S . Dieier Zeitvunkt dürfte min nicht mehr ferne ſein , da die Geſchaͤfte der Geſellſchaft in letzter Zeit einen ſehr erfreulichen Auiſchwung genommen baben . So wnd und gemeldet , datz die Kefſelſchmiede der Gefenſ Gaft in [E2] Schleſten [/E2] dieler Tage Auftraͤge im Betrage von 250 00 Eutr ."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Schlesien
    Description: Region in Mitteleuropa
    Country: ['Polen', 'Tschechien', 'Deutschland']
    Aliases: {'fr': ['Silésiens', 'Silesia', 'Silesie', 'Schlesien'], 'de': ['Schläsing']}
    Coordinates: [{'lat': 51.1035, 'lon': 17.0396}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nicht mehr
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Oieſf wird ſich in Kürze konſtttuiren , und werden den Aufſichtzratt derſelben bilden : der Gebeime Commerzienratb Zwick"
    Verb cluster: "gemeldet" — tense=None, aspect=None, mood=None
      Sentence: "So wnd und gemeldet , datz die Kefſelſchmiede der Gefenſ Gaft in Schleſten dieler Tage Auftraͤge im Betrage von 250 00 E"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.973

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Zwicker' and 'Schleſten' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Zwicker' near 'Schleſten' around 1874-08-25?
  4. Resolve temporal expressions relative to 1874-08-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 138:
  Publication date : 1930-03-21
  Language         : en
  Person  : 'G. D. Miller'  (QID: N/A)
  Location: 'Buxton'  (QID: Q745614)

  [ARTICLE TEXT — entity markers added]
  "C. P. Gray, is principal of the [E2] Buxton [/E2] school. The students are being taught in the neighboring homes of E. P. White, [E1] G. D. Miller [/E1] and U. B. Williams.—"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Buxton
    Description: unincorporated community of North Carolina, United States
    Country: ['United States']
    Located in: ['Dare County']
    Aliases: {'en': ['Buxton, NC']}
    Coordinates: [{'lat': 35.267777777778, 'lon': -75.5425}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "are being taught" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "The students are being taught in the neighboring homes of E. P. White, G. D. Miller and U. B. Williams.—"
    Verb cluster: "is" — tense=Pres, aspect=None, mood=Ind
      Sentence: "C. P. Gray, is principal of the Buxton school."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.969

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'G. D. Miller' and 'Buxton' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'G. D. Miller' near 'Buxton' around 1930-03-21?
  4. Resolve temporal expressions relative to 1930-03-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 139:
  Publication date : 1981-12-11
  Language         : fr
  Person  : 'Mouky'  (QID: N/A)
  Location: 'Fulgur'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "on s'aventure grâce à M. Benjamin sur la froide planète [E2] Fulgur [/E2]. Bandes dessinées, télévision, cinéma ont depuis longtemps compris et commercialisé l'engouement de la jeunesse pour la science-fiction. Les costumes signés [E1] Mouky [/E1] respectent admirablement la mode spatiale et les accessoires d'Henri Barbier et Maria Estève intriguent suffisamment pour qu'à la fin du spectacle jeunes et moins jeunes s'élancent sur scène pour comprendre, toucher, explorer ces nouveaux gadgets."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "aventure" — tense=Pres, aspect=None, mood=Ind
      Sentence: "on s'aventure grâce à M. Benjamin sur la froide planète Fulgur."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 13 (0 = most prominent)
    OCR quality estimate: 0.985

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mouky' and 'Fulgur' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mouky' near 'Fulgur' around 1981-12-11?
  4. Resolve temporal expressions relative to 1981-12-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 140:
  Publication date : 1928-01-17
  Language         : fr
  Person  : 'Gédéon le Contreleyu'  (QID: N/A)
  Location: 'Cœudres'  (QID: Q68532)

  [ARTICLE TEXT — entity markers added]
  ", comme l' appelaient ses amis) avait passé la majeure partie de g. vie dans cette vallée jurassienne où dans lés temps anciens vécurent (?) le Solitaire dès Sagnes et [E1] Gédéon le Contreleyu [/E1]. Cet endroit avait été par lui choisi en une occasion mémorable, quand un beau jour, ou plutôt un malheureux soir, il s'était aventuré à demander Êour femme la grande Uranie Montandon du ronillet. A sa complète stupéfaction, il lui fut répondu négativement. Quand il demanda les raisons de ce refus, elle lui déclara tout uniment « qu'il sentait trop l'horloger >. Pendant une heure ou deux, l'Alcide scngea à se noyer de dépit dans le lac des Tailleres, mais son bon sens lui revenant ei l'instinct de conservation aidant, il se borna à secouer sur ce Sol ingrat la poussière de ses souliers et, quelque temps plus tard, alla planter sa tente aux [E2] Cœudres [/E2], pensant que son noir chagrin se fondrait dans les brouillards de la Sagne."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: La Sagne
    Description: commune suisse
    Country: ['Suisse']
    Located in: ['canton de Neuchâtel']
    Aliases: {'en': ['Sagne', 'La Sagne NE'], 'de': ['La Sagne-Eglise', 'Les Coeudres', 'La Corbatière', 'Marmoud']}
    Coordinates: [{'lat': 47.0388, 'lon': 6.7988}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien, plus, tôt, tard
    Verb cluster: "passé" — tense=Past, aspect=None, mood=None
      Sentence: ", comme l' appelaient ses amis) avait passé la majeure partie de g. vie dans cette vallée jurassienne où dans lés temps "
    Verb cluster: "scngea" — tense=Past, aspect=None, mood=None
      Sentence: "Pendant une heure ou deux, l'Alcide scngea à se noyer de dépit dans le lac des Tailleres, mais son bon sens lui revenant"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 1 (0 = most prominent)
    OCR quality estimate: 0.981

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Gédéon le Contreleyu' and 'Cœudres' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Gédéon le Contreleyu' near 'Cœudres' around 1928-01-17?
  4. Resolve temporal expressions relative to 1928-01-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 141:
  Publication date : 1868-04-22
  Language         : fr
  Person  : 'jeune R'  (QID: N/A)
  Location: 'Môliers'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "— Dans la matinée du mercredi 15 avril, on a retiré de l'Areuse, près de [E2] Môliers [/E2], le corps de la [E1] jeune R [/E1] ."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "retiré" — tense=Past, aspect=None, mood=None
      Sentence: "— Dans la matinée du mercredi 15 avril, on a retiré de l'Areuse, près de Môliers, le corps de la jeune R ."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 49 (0 = most prominent)
    OCR quality estimate: 0.983

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'jeune R' and 'Môliers' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'jeune R' near 'Môliers' around 1868-04-22?
  4. Resolve temporal expressions relative to 1868-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 142:
  Publication date : 1930-03-21
  Language         : en
  Person  : 'E. P. White'  (QID: N/A)
  Location: 'Dare\ncounty'  (QID: Q295787)

  [ARTICLE TEXT — entity markers added]
  "The students are being taught in the neighboring homes of [E1] E. P. White [/E1], G. D. Miller and U. B. Williams.— D. V. M. Buxton Loses Its School Building Buxton, at Cane Hattcras, Dare county, finds itself in a bad situ-"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Dare County
    Description: county in North Carolina, United States
    Country: ['United States']
    Located in: ['North Carolina']
    Aliases: {'en': ['Dare County, North Carolina', 'Dare County, NC'], 'fr': ['Dare County']}
    Coordinates: [{'lat': 35.69, 'lon': -75.73}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "are being taught" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "The students are being taught in the neighboring homes of E. P. White, G. D. Miller and U. B. Williams.—"
    Verb cluster: "Loses" — tense=Pres, aspect=None, mood=None
      Sentence: "D. V. M. Buxton Loses Its School Building Buxton, at Cane Hattcras, Dare county, finds itself in a bad situ-"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.969

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'E. P. White' and 'Dare\ncounty' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'E. P. White' near 'Dare\ncounty' around 1930-03-21?
  4. Resolve temporal expressions relative to 1930-03-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 143:
  Publication date : 1826-08-22
  Language         : fr
  Person  : 'M. le prince de Metternicli'  (QID: N/A)
  Location: 'Annecy'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "On présume qu'immédiatement après les fêtes religieuses d'[E2] Annecy [/E2], qui ont dû commencer le 16 août, LL.MM. se rendront à Moutiers en Tarentaise. Des lettres de Mayence, que'nous recevons aujourd'hui', annoncent que [E1] M. le prince de Metternicli [/E1] est arrivé le 12 août à Johannisberg."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: aujourd'hui, après
    Verb cluster: "annoncent" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Des lettres de Mayence, que'nous recevons aujourd'hui', annoncent que M. le prince de Metternicli est arrivé le 12 août "
    Verb cluster: "présume" — tense=Pres, aspect=None, mood=Ind
      Sentence: "On présume qu'immédiatement après les fêtes religieuses d'Annecy, qui ont dû commencer le 16 août, LL.MM."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 1 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. le prince de Metternicli' and 'Annecy' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. le prince de Metternicli' near 'Annecy' around 1826-08-22?
  4. Resolve temporal expressions relative to 1826-08-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 144:
  Publication date : 1930-03-21
  Language         : en
  Person  : 'D. V. M.'  (QID: N/A)
  Location: 'Buxton'  (QID: Q745614)

  [ARTICLE TEXT — entity markers added]
  "C. P. Gray, is principal of the [E2] Buxton [/E2] school. The students are being taught in the neighboring homes of E. P. White, G. D. Miller and U. B. Williams.— [E1] D. V. M. [/E1] Buxton Loses Its School Building Buxton, at Cane Hattcras, Dare county, finds itself in a bad situ-"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Buxton
    Description: unincorporated community of North Carolina, United States
    Country: ['United States']
    Located in: ['Dare County']
    Aliases: {'en': ['Buxton, NC']}
    Coordinates: [{'lat': 35.267777777778, 'lon': -75.5425}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "are being taught" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "The students are being taught in the neighboring homes of E. P. White, G. D. Miller and U. B. Williams.—"
    Verb cluster: "is" — tense=Pres, aspect=None, mood=Ind
      Sentence: "C. P. Gray, is principal of the Buxton school."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 4 (0 = most prominent)
    OCR quality estimate: 0.969

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'D. V. M.' and 'Buxton' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'D. V. M.' near 'Buxton' around 1930-03-21?
  4. Resolve temporal expressions relative to 1930-03-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 145:
  Publication date : 1938-11-13
  Language         : de
  Person  : 'Siurgenenger'  (QID: N/A)
  Location: 'Ostschweiz'  (QID: Q31003)

  [ARTICLE TEXT — entity markers added]
  "Zum Entsetzen aller, die davon hören, soll eine der schönsten Flußlandschaften der [E2] Ostschweiz [/E2] (und der Schweiz überhaupt) dem Moloch der Zivilisation zum Opfer gebracht und mit einem (vorläufigen!) Kosten aufwand von rund 1,6 Millionen Franken von Grund aus und für alle Zeiten vernichtet werden. Wäre der massive Plan eine rein st.-gallische Kan tonsangelegenheit, so bliebe uns andern nichts übrig, als tatenlos zur Seite zu treten und trauernden Herzens zuzusehen, daß man in einem Winkel unseres Vaterlandes wieder einmal nicht begreifen will, wie sehr auch die aus sich selbst gewordene Natur eines wird, dazu schweigend seine Duldung zu geben und sich nicht aufzulehnen gegen ein Vorhaben, das einzig artige Landschaftsreize unrettbar vernichtet. Leider ist es freilich auch schon das Letzte! Ie: Dand [E1] Siurgenenger [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Ostschweiz
    Description: Grossregion der Schweiz
    Country: ['Q39']
    Located in: ['Q39']
    Coordinates: [{'lat': 47.3, 'lon': 9.3}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "soll" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Zum Entsetzen aller, die davon hören, soll eine der schönsten Flußlandschaften der Ostschweiz (und der Schweiz überhaupt"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 26 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Siurgenenger' and 'Ostschweiz' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Siurgenenger' near 'Ostschweiz' around 1938-11-13?
  4. Resolve temporal expressions relative to 1938-11-13. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 146:
  Publication date : 1804-08-28
  Language         : fr
  Person  : 'Ne'  (QID: N/A)
  Location: 'Alger'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "U E. — [E2] Alger [/E2], le 10 juiUùH & t Jf * NOUVELLES ETRANGE Une frégate anglaise vient de mouiller dans ce port."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "vient" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Une frégate anglaise vient de mouiller dans ce port."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.982

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Ne' and 'Alger' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Ne' near 'Alger' around 1804-08-28?
  4. Resolve temporal expressions relative to 1804-08-28. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 147:
  Publication date : 1881-01-15
  Language         : fr
  Person  : 'M. Patrick Collins'  (QID: N/A)
  Location: 'Washington'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Dans une réunion qui vient d'avoir lieu, une résolution a été adoptée tendant à former une nouvelle ligue qui s'appelle la Ligue agraire nationale des Etats-Unis, sous la présidence de [E1] M. Patrick Collins [/E1], de Boston. Une réunion des membres de la Landleague américaine aura lieu prochainement à [E2] Washington [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "adoptée" — tense=Past, aspect=None, mood=None
      Sentence: "Dans une réunion qui vient d'avoir lieu, une résolution a été adoptée tendant à former une nouvelle ligue qui s'appelle "
    Verb cluster: "aura" — tense=Fut, aspect=None, mood=Ind
      Sentence: "Une réunion des membres de la Landleague américaine aura lieu prochainement à Washington."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.967

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Patrick Collins' and 'Washington' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Patrick Collins' near 'Washington' around 1881-01-15?
  4. Resolve temporal expressions relative to 1881-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 148:
  Publication date : 1918-04-22
  Language         : fr
  Person  : 'J. B. RUSCH'  (QID: Q2734959)
  Location: 'Su. _sss allemands'  (QID: Q689055)

  [ARTICLE TEXT — entity markers added]
  "Lettre de la [E2] Su. _sss allemands [/E2] ( Une seule et même justice pour tous. [E1] J. B. RUSCH [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Johann Baptist Rusch
    Description: Swiss journalist and author (1886-1954)
    Born: ['+1886-02-07T00:00:00Z']
    Died: ['+1954-11-24T00:00:00Z']
    Birth place: ['Appenzell']
    Death place: ['Bad Ragaz']
  Location Wikidata:
    Label: Suisse alémanique
    Description: région de Suisse dont la population a majoritairement le suisse-allemand comme langue maternelle
    Country: ['Suisse']
    Aliases: {'en': ['German-speaking part of Switzerland', 'German Switzerland'], 'fr': ['Suisse allemande', 'Suisse alemanique'], 'de': ['Deutschsprachige Schweiz', 'Deutsche Schweiz'], 'lb': ['däitschen Deel vun der Schwäiz']}
    Coordinates: [{'lat': 46.952406, 'lon': 7.439583}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 30 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'J. B. RUSCH' and 'Su. _sss allemands' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'J. B. RUSCH' near 'Su. _sss allemands' around 1918-04-22?
  4. Resolve temporal expressions relative to 1918-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 149:
  Publication date : 1848-10-21
  Language         : de
  Person  : 'Kriegsminister, Artille\nriegeneral Graf Latour,'  (QID: Q78807)
  Location: 'Wien'  (QID: Q1741)

  [ARTICLE TEXT — entity markers added]
  "Blutige Auftritte haben in [E2] Wien [/E2] stattgefunden, unglücklicherweise veranlaßt durch die Zwietracht, welche gegenwärtig unser theures, gemein sames Vaterland in Parteien theilt. Der Kriegsminister, Artille riegeneral Graf Latour, unser alter, tapferer Gefährte, ist von einer rasenden Horde ermordet worden;"

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Wien
    Description: Bundeshauptstadt und bevölkerungsreichste Stadt der Republik Österreich
    Country: ['Österreich', 'Erste Republik', 'Q28513', 'Q268970', 'Q131964', 'Bundesstaat Österreich', 'Q7318', 'Q153136', 'Q699964', 'Herzogtum Österreich', 'Q283627', 'Q47261', 'besetztes Nachkriegsösterreich']
    Located in: ['Q40', 'Q596239', 'Q7318', 'Bundesstaat Österreich', 'Q518101', 'Q268970', 'Q28513', 'Kaisertum Österreich']
    Aliases: {'en': ['Vienna, Austria'], 'fr': ['Wien']}
    Coordinates: [{'lat': 48.208333333333336, 'lon': 16.3725}]
  Known person–location links: {"death_place": "P20"}

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "ist" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Der Kriegsminister, Artille riegeneral Graf Latour, unser alter, tapferer Gefährte, ist von einer rasenden Horde ermorde"
    Verb cluster: "haben" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Blutige Auftritte haben in Wien stattgefunden, unglücklicherweise veranlaßt durch die Zwietracht, welche gegenwärtig uns"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 5 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Kriegsminister, Artille\nriegeneral Graf Latour,' and 'Wien' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Kriegsminister, Artille\nriegeneral Graf Latour,' near 'Wien' around 1848-10-21?
  4. Resolve temporal expressions relative to 1848-10-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 150:
  Publication date : 1820-03-06
  Language         : en
  Person  : 'William\nMurphy'  (QID: N/A)
  Location: 'BaltimorCy'  (QID: Q5092)

  [ARTICLE TEXT — entity markers added]
  "[E2] BaltimorCy [/E2] March 2. This morning, John F. Ferguson. William Murphy, Thomas O’Brien, Charles Weaver, Isaac \llister, J. Jackson, and Isaac Denuie, convicted of Piracy, committed on board of La Irresistable privateer, which they ran a- way with from Margaritta, were brought be fore bis honor Judge Bland, wh, after a ‘short but impressive address,."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Baltimore
    Description: city in Maryland, United States
    Country: ['United States']
    Located in: ['Maryland', 'Province of Maryland']
    Aliases: {'en': ['Baltimore, Maryland', 'City of Baltimore', 'Baltimore City', 'Charm City', 'B more', 'Bmore', 'Baltimore, MD', 'Balt.', 'BAL', "B'more"], 'fr': ['municipalité de Baltimore City']}
    Coordinates: [{'lat': 39.286388888889, 'lon': -76.615}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.993

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'William\nMurphy' and 'BaltimorCy' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'William\nMurphy' near 'BaltimorCy' around 1820-03-06?
  4. Resolve temporal expressions relative to 1820-03-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 151:
  Publication date : 1878-10-02
  Language         : de
  Person  : 'Fröbel'  (QID: Q76679)
  Location: 'Türkei'  (QID: Q43)

  [ARTICLE TEXT — entity markers added]
  "— Mailand stellt Arbeiten der [E1] Fröbel [/E1]schulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die Kinder weit überschreiten: soll das Kinderarbeit sein; Man empfindet dies als einen recht fühlbaren Mangel; hat doch in Wien Deutschland mit seinen Schulausstellungen unbedingt Großes geleistet und nach allen Beziehungen werthvolle Anregungen gegeben. Begreiflicher Weise fehlt auch die [E2] Türkei [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Friedrich Fröbel
    Description: deutscher Pädagoge
    Born: ['+1782-04-21T00:00:00Z', '+1782-00-00T00:00:00Z']
    Died: ['+1852-06-21T00:00:00Z', '+1852-00-00T00:00:00Z']
    Birth place: ['Oberweißbach/Thüringer Wald']
    Death place: ['Marienthal']
  Location Wikidata:
    Label: Türkei
    Description: Staat in Südosteuropa und Vorderasien
    Country: ['Türkei']
    Aliases: {'en': ['Republic of Türkiye', 'Republic of Turkey'], 'fr': ['la République de Turquie', 'Turq', 'République de Turquie', 'République turque'], 'de': ['Republik Türkei'], 'lb': ['Republik Tierkei']}
    Coordinates: [{'lat': 39, 'lon': 36}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach
    Verb cluster: "stellt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "— Mailand stellt Arbeiten der Fröbelschulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die "
    Verb cluster: "fehlt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Begreiflicher Weise fehlt auch die Türkei."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 27 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Fröbel' and 'Türkei' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Fröbel' near 'Türkei' around 1878-10-02?
  4. Resolve temporal expressions relative to 1878-10-02. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 152:
  Publication date : 1886-06-22
  Language         : de
  Person  : 'Bismarck'  (QID: Q8442)
  Location: 'England'  (QID: Q21)

  [ARTICLE TEXT — entity markers added]
  "Juni ſind es zwei Jahre , daß der Reichskanzler Fürſt [E1] Bismarck [/E1] bei Gelegenheit der Berathung der damals eingebrachten erſten Poſt⸗ Dampfervorlage der Budgetcommiſſion di Mittheilung machte , daß die Lüderitz 'ſchen Erwerbungen in Südafrika ohne Widerſpruch [E2] England [/E2]s unter deutſchen Schutz geſtellt ſeien ."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: England
    Description: Land im Nordwesten Europas, Teil des Vereinigten Königreichs
    Country: ['Vereinigtes Königreich', 'Vereinigtes Königreich Großbritannien und Irland', 'Königreich Großbritannien']
    Located in: ['Vereinigtes Königreich', 'Vereinigtes Königreich Großbritannien und Irland', 'Königreich Großbritannien']
    Aliases: {'en': ['ENG', 'England, United Kingdom', 'England, UK'], 'fr': ['Ang.', 'Mère des parlements']}
    Coordinates: [{'lat': 53, 'lon': -1}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "ſind" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Juni ſind es zwei Jahre , daß der Reichskanzler Fürſt Bismarck bei Gelegenheit der Berathung der damals eingebrachten er"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 27 (0 = most prominent)
    OCR quality estimate: 0.993

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Bismarck' and 'England' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Bismarck' near 'England' around 1886-06-22?
  4. Resolve temporal expressions relative to 1886-06-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 153:
  Publication date : 1928-10-25
  Language         : fr
  Person  : 'Marx'  (QID: Q9061)
  Location: 'Schwytz'  (QID: Q12433)

  [ARTICLE TEXT — entity markers added]
  "On escompte ,, soit une avance radicale à Berne, Zurich, Saint-Gall, Grisons, soit une avance conservatrice à Zurich, [E2] Schwytz [/E2], peut-être Saint-Gall et peutêtre Valais. Quel que soit le succès de la liste socialiste, on s'accorde généralement à prévoir qu'il ne suffira pas à procurer aux disciples dé [E1] Marx [/E1] le gros succès moral de conquérir la majorité relative au Parlement."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "accorde" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Quel que soit le succès de la liste socialiste, on s'accorde généralement à prévoir qu'il ne suffira pas à procurer aux "
    Verb cluster: "peutêtre" — tense=Pres, aspect=None, mood=None
      Sentence: "On escompte ,, soit une avance radicale à Berne, Zurich, Saint-Gall, Grisons, soit une avance conservatrice à Zurich, Sc"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 4 (0 = most prominent)
    OCR quality estimate: 0.982

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Marx' and 'Schwytz' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Marx' near 'Schwytz' around 1928-10-25?
  4. Resolve temporal expressions relative to 1928-10-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 154:
  Publication date : 1981-11-17
  Language         : fr
  Person  : 'Frescobaldi'  (QID: N/A)
  Location: 'Eglise Saint-Jacques'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "[E2] Eglise Saint-Jacques [/E2]-20.30, récital d'orgue par Pierre Perdigon. Œuvres de Buxtehude, Tunder, [E1] Frescobaldi [/E1], Martini, Bach."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.778

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Frescobaldi' and 'Eglise Saint-Jacques' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Frescobaldi' near 'Eglise Saint-Jacques' around 1981-11-17?
  4. Resolve temporal expressions relative to 1981-11-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 155:
  Publication date : 1960-04-06
  Language         : en
  Person  : 'Col. Gruenwald'  (QID: N/A)
  Location: 'Myrtle\nBeach Air Force Base'  (QID: Q6948590)

  [ARTICLE TEXT — entity markers added]
  "competing joined in a camp fire meeting and heard an ad dress by [E1] Col. Gruenwald [/E1], com manding officer of the Myrtle Beach Air Force Base."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Myrtle Beach Air Force Base
    Description: United States Air Force base located near Myrtle Beach, South Carolina
    Country: ['United States']
    Located in: ['South Carolina']
    Coordinates: [{'lat': 33.6706, 'lon': -78.9339}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "competing" — tense=Pres, aspect=Prog, mood=None
      Sentence: "competing joined in a camp fire meeting and heard an ad dress by Col. Gruenwald, com manding officer of the Myrtle Beach"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 4 (0 = most prominent)
    OCR quality estimate: 0.966

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Col. Gruenwald' and 'Myrtle\nBeach Air Force Base' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Col. Gruenwald' near 'Myrtle\nBeach Air Force Base' around 1960-04-06?
  4. Resolve temporal expressions relative to 1960-04-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 156:
  Publication date : 1790-03-31
  Language         : en
  Person  : 'Vian, J. Cadiot Lombard-Rebian'  (QID: N/A)
  Location: 'Point\na Petre'  (QID: Q335322)

  [ARTICLE TEXT — entity markers added]
  "O N the 12th of February, at fcven in the even ing, a tremendous fire broke out at Point Petre, in Guadaloupe, and was not extinguished till midnight. There were twenty five capital buildings confumed, befides a number of fnrjler ones—the whole lofs ellimared at fix millions of livres. Done and concluded by the committee at Point a Petre, this 18th of February, 1 790. (Signed) [E1] Vian, J. Cadiot Lombard-Rebian [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Pointe-à-Pitre
    Description: French commune in Guadeloupe
    Country: ['France']
    Located in: ['Guadeloupe', 'canton of Pointe-à-Pitre-1', 'canton of Pointe-à-Pitre-2', 'canton of Pointe-à-Pitre-3', 'arrondissement of Pointe-à-Pitre']
    Aliases: {'en': ['Pwentapit', 'Pointe à Pitre', 'Lapwent', 'La Pointe'], 'fr': ['Pointe à Pitre', 'La Pointe'], 'de': ['Pointe à Pitre', 'Pwentapit', 'Lapwent']}
    Coordinates: [{'lat': 16.241111111111, 'lon': -61.533055555556}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "Signed" — tense=Past, aspect=Perf, mood=None
      Sentence: "(Signed) Vian, J. Cadiot Lombard-Rebian."
    Verb cluster: "Done" — tense=Past, aspect=Perf, mood=None
      Sentence: "Done and concluded by the committee at Point a Petre, this 18th of February, 1 790."
    Verb cluster: "broke" — tense=Past, aspect=None, mood=None
      Sentence: "O N the 12th of February, at fcven in the even ing, a tremendous fire broke out at Point Petre, in Guadaloupe, and was n"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 5 (0 = most prominent)
    OCR quality estimate: 0.979

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Vian, J. Cadiot Lombard-Rebian' and 'Point\na Petre' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Vian, J. Cadiot Lombard-Rebian' near 'Point\na Petre' around 1790-03-31?
  4. Resolve temporal expressions relative to 1790-03-31. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 157:
  Publication date : 1921-10-05
  Language         : fr
  Person  : 'M. Bosgbartft'  (QID: N/A)
  Location: 'Autriche'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "[E1] M. Bosgbartft [/E1] a visité toutes les installations de la Bourse de Copenhague. L'aide à l'[E2] Autriche [/E2] Benne, 3 octobre."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "a" — tense=Pres, aspect=None, mood=Ind
      Sentence: "M. Bosgbartft a visité toutes les installations de la Bourse de Copenhague."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 30 (0 = most prominent)
    OCR quality estimate: 0.951

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Bosgbartft' and 'Autriche' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Bosgbartft' near 'Autriche' around 1921-10-05?
  4. Resolve temporal expressions relative to 1921-10-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 158:
  Publication date : 1928-10-25
  Language         : fr
  Person  : 'Démosthène'  (QID: Q117253)
  Location: 'Berne'  (QID: Q70)

  [ARTICLE TEXT — entity markers added]
  "La géographie électorale et ses aspects A LA VEILLE DU SCRUTIN (Correspondance particulière) [E2] Berne [/E2], le 24 octobre. Nous avons longuement exposé, lundi. C'est M. de Rabours que tous livrent d'avance au fatal couperet de la guillotine sèche. Si pareille prédiction devait se vérifier exacte, le Parlement perdrait une de ses figures les plus sympathiques et l'un de ses meilleurs orateurs, à un moment où les disciples de [E1] Démosthène [/E1], à Berne, se comptent presque sur les doigts 1..."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Démosthène
    Description: homme d'état et orateur athénien
    Born: ['-0384-01-01T00:00:00Z']
    Died: ['-0322-10-12T00:00:00Z']
    Birth place: ['Péanie']
    Death place: ['Póros']
  Location Wikidata:
    Label: Berne
    Description: ville de Suisse, capitale du canton de Berne et capitale de facto de la Suisse
    Country: ['Suisse']
    Located in: ['arrondissement administratif de Berne-Mittelland', 'district de Berne']
    Aliases: {'en': ['Berne', 'city of Bern', 'Berna'], 'fr': ['Bern'], 'de': ['Stadt Bern']}
    Coordinates: [{'lat': 46.94798, 'lon': 7.44743}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Verb cluster: "perdrait" — tense=Imp, aspect=None, mood=Ind
      Sentence: "Si pareille prédiction devait se vérifier exacte, le Parlement perdrait une de ses figures les plus sympathiques et l'un"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 17 (0 = most prominent)
    OCR quality estimate: 0.982

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Démosthène' and 'Berne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Démosthène' near 'Berne' around 1928-10-25?
  4. Resolve temporal expressions relative to 1928-10-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 159:
  Publication date : 1868-02-19
  Language         : de
  Person  : 'Georg'  (QID: Q57428)
  Location: 'Preußens'  (QID: Q38872)

  [ARTICLE TEXT — entity markers added]
  "digt : überall in Deutſchland und über deſſen Grenzen hinaus richtet ſich die Beachtung und Anerkennung der Regierung und der Völker auf das Verfahren [E2] Preußens [/E2] in den eroberten Provinzen . Die bedeutſamſten Stimmen aus Süddeutſchland ver⸗ zu dieſer Berathung herbeigekommen und von 141 Anweſenden baben 127 ihre Zuſtimmung zu der Vorlage ertheilt ; Es bewährt ſich hierin , Jndem das Herrenhaus durch ſeinen jüngſten Beſchluß von Neuem mit vollſter Entſchiedenheit für dieſe Politik eingetreten iſt , hat daſſelbe zugleich die Zuverſicht erhöht , daß die konſervative Partei Die ſogenaunte Hannoverſche Legion . Aufenthalt in Hietzing , die Regierung dann verpflichtet ſein wird , das Während die preußiſche Regierung dem früheren König von Hannover die größte und edelſte Rückſicht zu Theil werden läßt , während andererſeits ihre Fürſorge für die neue Provinz unter der be — des Königs [E1] Georg [/E1] und ſeiner Umgebung in Hietzing die verwerflichen Verſuche fortgeſetzt , einen Theil ſeiner früheren Unterthanen , meiſt aus den unterſten Ständen , für das völlige boffnungsloſe und thörichte Unternehmen einer Wiederherſtellung ſeines Thrones zu gewinnen ."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Georg V. von Hannover
    Description: König von Hannover, Deutschland
    Born: ['+1819-05-27T00:00:00Z']
    Died: ['+1878-06-12T00:00:00Z']
    Birth place: ['Berlin']
    Death place: ['Paris']
    Work locations: ['Berlin', 'London', 'Hannover']
  Location Wikidata:
    Label: Preußen
    Description: Staatswesen (Herzogtum, Königreich, Freistaat), 1525–1947
    Country: ['Preußen']
    Aliases: {'en': ['Prussia (Germany)'], 'fr': ['État prussien', 'Prussienne'], 'de': ['Preussen']}
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: früher, vor, früh
    Verb cluster: "verpflichtet" — tense=None, aspect=None, mood=None
      Sentence: "Aufenthalt in Hietzing , die Regierung dann verpflichtet ſein wird , das Während die preußiſche Regierung dem früheren K"
    Verb cluster: "richtet" — tense=Pres, aspect=None, mood=Ind
      Sentence: "digt : überall in Deutſchland und über deſſen Grenzen hinaus richtet ſich die Beachtung und Anerkennung der Regierung un"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 29 (0 = most prominent)
    OCR quality estimate: 0.994

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Georg' and 'Preußens' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Georg' near 'Preußens' around 1868-02-19?
  4. Resolve temporal expressions relative to 1868-02-19. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 160:
  Publication date : 1908-01-21
  Language         : fr
  Person  : 'sir H.\nCampbeil-Bannerman'  (QID: Q106618)
  Location: 'Irlande'  (QID: Q27)

  [ARTICLE TEXT — entity markers added]
  "L'élection de lord Curzon Lord Curzon a été élu lundi lord représentatif pour l'[E2] Irlande [/E2]. Cette nomination lui permet d'entrer dans la Chambre des lords. On se souvient que sir H. Campbeil-Bannerman avait refusé à Pcx-vice-roi des Indes la pairie -anglaise, qui lui eût donné droit d'entrer dans la Chambre-Haute."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Henry Campbell-Bannerman
    Description: homme d’État britannique, Premier ministre du Royaume-Uni de 1905 à 1908
    Born: ['+1836-09-07T00:00:00Z']
    Died: ['+1908-04-22T00:00:00Z']
    Birth place: ['Glasgow']
    Death place: ['Downing Street']
    Residences: ['Glasgow']
    Work locations: ['Londres']
  Location Wikidata:
    Label: Irlande
    Description: pays du nord-ouest de l'Europe
    Country: ['Irlande']
    Aliases: {'en': ['Éire', 'Hibernia', 'Southern Ireland', 'Irish Republic', 'Republic of Ireland'], 'fr': ["République d'Irlande", 'Éire', 'Ireland', "l'Irlande", 'Irl.', 'République irlandaise'], 'de': ['Republik Irland'], 'lb': ['Éire', 'Republik Irland']}
    Coordinates: [{'lat': 53, 'lon': -8}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "refusé" — tense=Past, aspect=None, mood=None
      Sentence: "On se souvient que sir H. Campbeil-Bannerman avait refusé à Pcx-vice-roi des Indes la pairie -anglaise, qui lui eût donn"
    Verb cluster: "élu" — tense=Past, aspect=None, mood=None
      Sentence: "L'élection de lord Curzon Lord Curzon a été élu lundi lord représentatif pour l'Irlande."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 25 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'sir H.\nCampbeil-Bannerman' and 'Irlande' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'sir H.\nCampbeil-Bannerman' near 'Irlande' around 1908-01-21?
  4. Resolve temporal expressions relative to 1908-01-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 161:
  Publication date : 1878-10-02
  Language         : de
  Person  : 'Fröbel'  (QID: Q76679)
  Location: 'Deutschösterreich'  (QID: Q40)

  [ARTICLE TEXT — entity markers added]
  "— Mailand stellt Arbeiten der [E1] Fröbel [/E1]schulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die Kinder weit überschreiten: soll das Kinderarbeit sein; Begreiflicher Weise fehlt auch die Türkei. Oesterreich erscheint getrennt als [E2] Deutschösterreich [/E2] und als Ungarn, das getreue Bild der feindlichen, sich aber umarmenden Brüder."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Friedrich Fröbel
    Description: deutscher Pädagoge
    Born: ['+1782-04-21T00:00:00Z', '+1782-00-00T00:00:00Z']
    Died: ['+1852-06-21T00:00:00Z', '+1852-00-00T00:00:00Z']
    Birth place: ['Q310955']
    Death place: ['Q1897986']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "stellt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "— Mailand stellt Arbeiten der Fröbelschulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die "
    Verb cluster: "erscheint" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Oesterreich erscheint getrennt als Deutschösterreich und als Ungarn, das getreue Bild der feindlichen, sich aber umarmen"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 27 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Fröbel' and 'Deutschösterreich' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Fröbel' near 'Deutschösterreich' around 1878-10-02?
  4. Resolve temporal expressions relative to 1878-10-02. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 162:
  Publication date : 1790-05-29
  Language         : en
  Person  : 'H011. James Gordon'  (QID: N/A)
  Location: 'Callicut,'  (QID: Q28729)

  [ARTICLE TEXT — entity markers added]
  "The Ship Harmony Capt. IVillet is arrived at Philadelphia from Bengal.—Accounts from the Eaft-Indies State—there is a mod plealing pro- fpeft of a plentiful harveft in that pare of the world—that Cotton has fold fo low as 11 Tales in China—that the Englifli/ fettlements enjoy a profound peace—that the greateft part of trea- fure on board the Vanfittart one of the Eaft-In- idea company’s Ships lately loft, had been re covered from the wreck—that the ffiip Durham Capt. Kepling ; and another fhip were loft in a gale of wind, foundering in the road—that Tippoo Sultan to puQjfh the faults of fome of the tributary Princes had depopulated and laid wafte their country from Belipatain to [E2] Callicut, [/E2] an ex tent of 80 or 90 miles, where the latepoffeflors of its fields and habitations arefeen no more. The Hon. Peter Sylvester is re-elefted a member of the Houfe of Reprefentatives of the United States—and the H011."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Kozhikode
    Description: city in Kerala, India
    Country: ['India', 'Portuguese Empire']
    Located in: ['Kozhikode district', 'Malabar District']
    Aliases: {'en': ['Calicut'], 'fr': ['Kozhikode'], 'de': ['Kalikut', 'Calicut']}
    Coordinates: [{'lat': 11.247777777777777, 'lon': 75.78027777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: late
    Verb cluster: "is" — tense=Pres, aspect=None, mood=Ind
      Sentence: "IVillet is arrived at Philadelphia from Bengal.—Accounts from the Eaft-Indies State—there is a mod plealing pro- fpeft o"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 1 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'H011. James Gordon' and 'Callicut,' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'H011. James Gordon' near 'Callicut,' around 1790-05-29?
  4. Resolve temporal expressions relative to 1790-05-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 163:
  Publication date : 1928-05-06
  Language         : fr
  Person  : 'Mgr. Stéphane'  (QID: Q2713806)
  Location: 'Corinthe'  (QID: Q103011)

  [ARTICLE TEXT — entity markers added]
  "Pour les enfants sinistrés de Bulgarie et de Grèce [E1] Mgr. Stéphane [/E1], archevêque de Sofia, rient d'adresser à l'Union internationale de secours aux enfants une dépêche, où, après avoir rendu hommage à cette institution, il s'exprime comme suit : La solidarité humaine ae manifeste le plue sensiblement dane les heures critiques. I. S. E. : Envisageant le danger auquel sont exposés les enfants de la population de [E2] Corinthe [/E2], la Ligue patriotique fait appel aux généreux sentiments de l'Union pour aider et faciliter la bonne marche de l'œuvre de eecours eutrperise."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Stéphane Ier
    Description: Bulgarian priest (1878-1957)
    Born: ['+1878-09-07T00:00:00Z']
    Died: ['+1957-05-14T00:00:00Z', '+1957-01-01T00:00:00Z']
    Birth place: ['Chiroka laka']
    Death place: ['Banya']
    Residences: ['Sofia']
  Location Wikidata:
    Label: Corinthe
    Description: ville grecque
    Country: ['Grèce']
    Located in: ['dème des Corinthiens', 'Commune of Korinthos']
    Aliases: {'en': ['Korinthos', 'Gördüs']}
    Coordinates: [{'lat': 37.93861111111111, 'lon': 22.927222222222223}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: après
    Verb cluster: "rient" — tense=Imp, aspect=None, mood=Ind
      Sentence: "Stéphane, archevêque de Sofia, rient d'adresser à l'Union internationale de secours aux enfants une dépêche, où, après a"
    Verb cluster: "fait" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Envisageant le danger auquel sont exposés les enfants de la population de Corinthe, la Ligue patriotique fait appel aux "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.984

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mgr. Stéphane' and 'Corinthe' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mgr. Stéphane' near 'Corinthe' around 1928-05-06?
  4. Resolve temporal expressions relative to 1928-05-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 164:
  Publication date : 1808-09-01
  Language         : fr
  Person  : 'Jacob'  (QID: N/A)
  Location: 'Verrières'  (QID: Q69807)

  [ARTICLE TEXT — entity markers added]
  "Jaques Henri Boûrquin, veuve de [E1] Jacob [/E1] fils de Jaques Guye, des [E2] Verrières [/E2] _, résidante et paroissienne de la Cote-aux-Fées, de mettre ses biens en décret ; joran, la. vigne de M. le capitaine Jacobel de' vent."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Les Verrières
    Description: commune suisse
    Country: ['Suisse']
    Located in: ['canton de Neuchâtel']
    Aliases: {'en': ['Les Verrières NE', 'Verrières', 'Les Verrieres', 'Les Verrieres NE', 'Verrieres'], 'fr': ['Les Verrieres'], 'de': ['Les Verrieres', 'Mont des Verrières', 'Petits Cernets', 'Grands Cernets']}
    Coordinates: [{'lat': 46.9, 'lon': 6.4833333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "mettre" — tense=None, aspect=None, mood=None
      Sentence: "Jaques Henri Boûrquin, veuve de Jacob fils de Jaques Guye, des Verrières _, résidante et paroissienne de la Cote-aux-Fée"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 9 (0 = most prominent)
    OCR quality estimate: 0.952

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Jacob' and 'Verrières' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Jacob' near 'Verrières' around 1808-09-01?
  4. Resolve temporal expressions relative to 1808-09-01. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 165:
  Publication date : 1948-12-30
  Language         : de
  Person  : 'Nokeraschi Pasehn'  (QID: Q1391679)
  Location: 'Eniro'  (QID: Q85)

  [ARTICLE TEXT — entity markers added]
  "Nokcraschi Pascha Ed. 7. Seine Studien an der Veterinär-Hedi zinischen Faleultiit wurden ihm dureh ein Ssipen dium, dus ilim von Nokraschi Pascha persönlich gewührt worden war, ermöglicht. In einer Sehublade des Sebreibtisches des er mordeten Ministerprüsidenten fand man einen Stolz Drokbriefe, die [E1] Nokeraschi Pasehn [/E1] erhalten hatte und über die er nieht einmal eine Untersuchung angeordnet lntte."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: {"death_place": "P20"}

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "fand" — tense=Past, aspect=None, mood=Ind
      Sentence: "In einer Sehublade des Sebreibtisches des er mordeten Ministerprüsidenten fand man einen Stolz Drokbriefe, die Nokerasch"
    Verb cluster: "wurden" — tense=Past, aspect=None, mood=Ind
      Sentence: "Seine Studien an der Veterinär-Hedi zinischen Faleultiit wurden ihm dureh ein Ssipen dium, dus ilim von Nokraschi Pascha"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 63 (0 = most prominent)
    OCR quality estimate: 0.983

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Nokeraschi Pasehn' and 'Eniro' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Nokeraschi Pasehn' near 'Eniro' around 1948-12-30?
  4. Resolve temporal expressions relative to 1948-12-30. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 166:
  Publication date : 1841-07-30
  Language         : fr
  Person  : 'Fanny Elliott'  (QID: N/A)
  Location: 'Angleterre'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "ANGLETERRE LONDRES 22 juillet.— Les journaux anglais continuent à spéculer sur les actes de l'ancien et du futur ministère, sans nous apprendre à cet égard rien de définitif. En attendant, les principaux chefs du parti publient leurs manifestes. Dans le nombre se fait remarquer celui de lord John Russell, adressé par ce ministre aux électeurs de la Cité, la veille de son mariage avec lady [E1] Fanny Elliott [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien
    Verb cluster: "fait" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Dans le nombre se fait remarquer celui de lord John Russell, adressé par ce ministre aux électeurs de la Cité, la veille"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.998

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Fanny Elliott' and 'Angleterre' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Fanny Elliott' near 'Angleterre' around 1841-07-30?
  4. Resolve temporal expressions relative to 1841-07-30. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 167:
  Publication date : 1892-07-05
  Language         : de
  Person  : 'H . Kray'  (QID: N/A)
  Location: 'Berliner'  (QID: Q64)

  [ARTICLE TEXT — entity markers added]
  "Handels⸗ Zeitung des [E2] Berliner [/E2] Tageblatts . Nummer 335 . Co . H ."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 97 (0 = most prominent)
    OCR quality estimate: 0.975

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'H . Kray' and 'Berliner' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'H . Kray' near 'Berliner' around 1892-07-05?
  4. Resolve temporal expressions relative to 1892-07-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 168:
  Publication date : 1961-12-21
  Language         : fr
  Person  : 'Serge Lang'  (QID: N/A)
  Location: 'Belge'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "LES 24 HEURES de [E1] Serge Lang [/E1] La mauvaise querelle Quatre étapes contre la montre ? s'était exclamé le [E2] Belge [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "exclamé" — tense=Past, aspect=None, mood=None
      Sentence: "s'était exclamé le Belge."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.988

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Serge Lang' and 'Belge' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Serge Lang' near 'Belge' around 1961-12-21?
  4. Resolve temporal expressions relative to 1961-12-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 169:
  Publication date : 1920-04-22
  Language         : en
  Person  : 'Lon Morelock'  (QID: N/A)
  Location: 'France'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "[E1] Lon Morelock [/E1], every Jones of the name and others down around there, how is every one of my old customers? O. K. I hope. If I do I still want your custom and trade Bob Maggart. I understand you did not get killed in [E2] France [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: France
    Description: country in Western Europe and other continents (through its overseas territories in America, Africa and Oceania)
    Country: ['France']
    Aliases: {'en': ['French Republic'], 'fr': ['République française', 'RF', 'fr', 'la République française', 'Fr.', 'La France', "L'Hexagone"], 'de': ['Französische Republik', 'fr', 'RF']}
    Coordinates: [{'lat': 47, 'lon': 2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "is" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Lon Morelock, every Jones of the name and others down around there, how is every one of my old customers?"
    Verb cluster: "understand" — tense=Pres, aspect=None, mood=None
      Sentence: "I understand you did not get killed in France."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 10 (0 = most prominent)
    OCR quality estimate: 0.992

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Lon Morelock' and 'France' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Lon Morelock' near 'France' around 1920-04-22?
  4. Resolve temporal expressions relative to 1920-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 170:
  Publication date : 1858-10-24
  Language         : de
  Person  : 'Admiral Großfürsten Konstantin'  (QID: Q446724)
  Location: 'mittelländischen\nMeere'  (QID: Q4918)

  [ARTICLE TEXT — entity markers added]
  "keit soll jedoch, wie die „Presse" meldet, erst nach dem Eintreffen der russischen Flotte, die den letzten Nach« richten zufolge vor Brest ankerte und so ziemlich gleich» zeitig mit dem [E1] Admiral Großfürsten Konstantin [/E1] in Villafranca anlangen dürfte, stattfinden. T'as — Vor zwei Jahren kam Großfürst Konstantin auf dem Admiralschiff Wiborg nach La Spezzia, um die Localität in Augenschein zu nehmen. Nun ist es leicht möglich, daß Villafranca für große Schiffe nicht Sicherheit genug darbietet, und daß man sich vornimmt, während des Winters jene nach La Spezzia zu senden, welche Rußland im mittelländischen Meere unterhalten wird."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Konstantin Nikolajewitsch Romanow
    Description: Sohn des Nikolaus I. Pawlowitsch
    Born: ['+1827-09-21T00:00:00Z', '+1827-09-09T00:00:00Z']
    Died: ['+1892-01-25T00:00:00Z']
    Birth place: ['Sankt Petersburg']
    Death place: ['Pawlowsk']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Verb cluster: "soll" — tense=Pres, aspect=None, mood=Ind
      Sentence: "keit soll jedoch, wie die „Presse" meldet, erst nach dem Eintreffen der russischen Flotte, die den letzten Nach« richten"
    Verb cluster: "ist" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Nun ist es leicht möglich, daß Villafranca für große Schiffe nicht Sicherheit genug darbietet, und daß man sich vornimmt"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 12 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Admiral Großfürsten Konstantin' and 'mittelländischen\nMeere' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Admiral Großfürsten Konstantin' near 'mittelländischen\nMeere' around 1858-10-24?
  4. Resolve temporal expressions relative to 1858-10-24. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 171:
  Publication date : 1960-04-06
  Language         : en
  Person  : 'George Rent'  (QID: N/A)
  Location: 'Horry\nDistrict Scout Camporee'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Boy Scout Troop 843 of Loris won top honors at the Horry District Scout Camporee March 25-27 at Clear Pond between ( Conway and Myrtle Beach. Competing against some ot the finest units in the county, the boys won top honors after participating in Compassing, : rope throwing, Morse Code, hiking with compass and indi- ) vidual cooking. Friday night the troops! competing joined in a camp fire meeting and heard an ad dress by Col. Gruenwald, com manding officer of the Myrtle Beach Air Force Base. The Loris troop, sponsored by the First Baptist church, was the only troop to have all its Scout leaders present: Francis Ragan, [E1] George Rent [/E1]/ and George Lav."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after
    Verb cluster: "was" — tense=Past, aspect=None, mood=Ind
      Sentence: "The Loris troop, sponsored by the First Baptist church, was the only troop to have all its Scout leaders present: Franci"
    Verb cluster: "won" — tense=Past, aspect=None, mood=None
      Sentence: "Boy Scout Troop 843 of Loris won top honors at the Horry District Scout Camporee March 25-27 at Clear Pond between ( Con"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 5 (0 = most prominent)
    OCR quality estimate: 0.966

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'George Rent' and 'Horry\nDistrict Scout Camporee' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'George Rent' near 'Horry\nDistrict Scout Camporee' around 1960-04-06?
  4. Resolve temporal expressions relative to 1960-04-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 172:
  Publication date : 1868-02-19
  Language         : de
  Person  : 'von der Heydt'  (QID: Q765327)
  Location: 'Oeſterreich'  (QID: Q40)

  [ARTICLE TEXT — entity markers added]
  "Was [E2] Oeſterreich [/E2] betrifft , ſo iſt Seitens der dortigen Regierung die Verſicherung gegeben worden , daß die Päſſe für die Hannoveraner von der öſterreichiſchen Polizeibehörde ohne Wiſſen der üſterreichiſchen Staatsregierung ertheilt worden ſeien , was mit Bezug auf die große Zahl der Päſſe 00 ) und die unverkennbare politiſche Bedeutung der Sache jedenfalls höchſt auffällig erſcheinen muß . Die Erörterungen zwiſchen der preußiſchen und der öſterreichiſchen Regierung deshalb auch noch nicht beſtimmt angeben , ob und inwieweit in öſterreichiſchen Regierung über dieſen Punkt ſind noch im Gange ; es läßt ſich der Angelegenheit eine Verletzung des Voͤlkerrechts ſtattgefunden hat . Das aber kann wohl keinem Zweifel unterliegen , daß die Fort . riſchen Unternehmen gegen Preußen anwerben und cuS⸗ Fürſten , welcher preußiſche Unterthanen zu einem kriege — rüſten läßt , nicht gerade als ein Zeichen einer freund . Miniſter [E1] von der Heydt [/E1] ſoeben im Herrenhauſe ausgeſprochen , Jn Bezug auf das Gebahren des Königs Georg hat der Staats⸗ Minister ."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: August von der Heydt
    Description: deutscher Bankier und preußischer Handels- und Finanzminister (1801-1874)
    Born: ['+1801-02-15T00:00:00Z']
    Died: ['+1874-06-13T00:00:00Z']
    Birth place: ['Q702259']
    Death place: ['Berlin']
  Location Wikidata:
    Label: Österreich
    Description: Staat in Mitteleuropa
    Country: ['Österreich']
    Aliases: {'en': ['Republic of Austria'], 'fr': ["République d'Autriche"], 'de': ['Republik Österreich', 'Zweite Republik'], 'lb': ['Republik Éisträich']}
    Coordinates: [{'lat': 48, 'lon': 14}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "ſoeben" — tense=Past, aspect=None, mood=Ind
      Sentence: "Miniſter von der Heydt ſoeben im Herrenhauſe ausgeſprochen , Jn Bezug auf das Gebahren des Königs Georg hat der Staats⸗ "
    Verb cluster: "betrifft" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Was Oeſterreich betrifft , ſo iſt Seitens der dortigen Regierung die Verſicherung gegeben worden , daß die Päſſe für die"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 44 (0 = most prominent)
    OCR quality estimate: 0.994

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'von der Heydt' and 'Oeſterreich' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'von der Heydt' near 'Oeſterreich' around 1868-02-19?
  4. Resolve temporal expressions relative to 1868-02-19. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 173:
  Publication date : 1981-07-25
  Language         : fr
  Person  : 'George'  (QID: N/A)
  Location: 'Monte-CarloCyclisme'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Le Sénégal Les jeux du stade-Tennis : Coupe de Galéa, demi-finales dames à [E2] Monte-CarloCyclisme [/E2] : Championnat de France sur pisteHippisme : King [E1] George [/E1] Horse Show"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 13 (0 = most prominent)
    OCR quality estimate: 0.663

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'George' and 'Monte-CarloCyclisme' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'George' near 'Monte-CarloCyclisme' around 1981-07-25?
  4. Resolve temporal expressions relative to 1981-07-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 174:
  Publication date : 1918-07-10
  Language         : fr
  Person  : 'prince Oscar dé _Crusse'  (QID: Q61242)
  Location: 'Helsingfors'  (QID: Q1757)

  [ARTICLE TEXT — entity markers added]
  "_BELSTNGFORS, 8. — La Diète a adopté en seconde lecture la loi de punition des insurgés et voté par 65 voix _contre 36 l'envoi des insurgés aux travaux forcés à l'étranger. [E2] Helsingfors [/E2]. Il proposera probablement au Sénat de choisir le [E1] prince Oscar dé _Crusse [/E1] comme roi de Finlande."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Oscar de Prusse
    Description: Prussian prince (1888-1958)
    Born: ['+1888-07-27T00:00:00Z']
    Died: ['+1958-01-27T00:00:00Z']
    Birth place: ['Q573662']
    Death place: ['Q1726']
    Residences: ['Villa Quandt']
  Location Wikidata:
    Label: Helsinki
    Description: capitale de la Finlande
    Country: ['Finlande', 'Empire russe', 'Suède', 'République socialiste des travailleurs de Finlande']
    Located in: ['Uusimaa', 'Helsinki', 'Gouvernement de Nyland']
    Aliases: {'en': ['Helsingfors', 'Helsingia', 'Helsingin kaupunki', 'Stadi', 'Hesa'], 'fr': ['Helsingfors'], 'de': ['Helsingfors']}
    Coordinates: [{'lat': 60.170833333333334, 'lon': 24.9375}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "proposera" — tense=Fut, aspect=None, mood=Ind
      Sentence: "Il proposera probablement au Sénat de choisir le prince Oscar dé _Crusse comme roi de Finlande."
    Verb cluster: "adopté" — tense=Past, aspect=None, mood=None
      Sentence: "— La Diète a adopté en seconde lecture la loi de punition des insurgés et voté par 65 voix _contre 36 l'envoi des insurg"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 80 (0 = most prominent)
    OCR quality estimate: 0.956

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'prince Oscar dé _Crusse' and 'Helsingfors' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'prince Oscar dé _Crusse' near 'Helsingfors' around 1918-07-10?
  4. Resolve temporal expressions relative to 1918-07-10. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 175:
  Publication date : 1826-08-22
  Language         : fr
  Person  : 'M. le prince de Metternicli'  (QID: N/A)
  Location: 'lac de Côme'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Des lettres de Mayence, que'nous recevons aujourd'hui', annoncent que [E1] M. le prince de Metternicli [/E1] est arrivé le 12 août à Johannisberg. Il règne actuellement en Frise et à Groningue des fièvres qui font périr beaucoup de monde. Il a même enjoint aux pasteurs dencourager les fidèles, $ ix des exhortations publiques, à ces actes de charité. On a lancé le 30 juillet, en grande pompe, un bateau à vapeur sur le [E2] lac de Côme [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: actuellement, aujourd'hui
    Verb cluster: "annoncent" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Des lettres de Mayence, que'nous recevons aujourd'hui', annoncent que M. le prince de Metternicli est arrivé le 12 août "
    Verb cluster: "lancé" — tense=Past, aspect=None, mood=None
      Sentence: "On a lancé le 30 juillet, en grande pompe, un bateau à vapeur sur le lac de Côme."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 1 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. le prince de Metternicli' and 'lac de Côme' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. le prince de Metternicli' near 'lac de Côme' around 1826-08-22?
  4. Resolve temporal expressions relative to 1826-08-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 176:
  Publication date : 1848-10-01
  Language         : de
  Person  : 'Neumann'  (QID: N/A)
  Location: 'Wiltz'  (QID: Q741589)

  [ARTICLE TEXT — entity markers added]
  "Und gingen auch bei der zweiten Abstimmung manche Candidaten wieder verloren, wie in Echternach Gigrang und Dieschburg, in [E2] Wiltz [/E2] [E1] Neumann [/E1], in Grevenmachern Kuborn, so ist dennoch das Gesammtrcsultat der Wahlen ein erfreuliches zu nennen."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Wiltz
    Description: Gemeinde in Luxemburg
    Country: ['Q32']
    Located in: ['Q550021']
    Aliases: {'en': ['Wolz', 'Wiltz, Luxembourg'], 'fr': ['Wolz'], 'de': ['Wolz'], 'lb': ['Gemeng Wolz', 'Gemeng Wiltz']}
    Coordinates: [{'lat': 49.96611111111111, 'lon': 5.9325}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach
    Verb cluster: "ist" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Und gingen auch bei der zweiten Abstimmung manche Candidaten wieder verloren, wie in Echternach Gigrang und Dieschburg, "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 9 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Neumann' and 'Wiltz' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Neumann' near 'Wiltz' around 1848-10-01?
  4. Resolve temporal expressions relative to 1848-10-01. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 177:
  Publication date : 1868-04-22
  Language         : fr
  Person  : 'jeune R'  (QID: N/A)
  Location: 'Fontainemelon'  (QID: Q68544)

  [ARTICLE TEXT — entity markers added]
  "— La question de la création d'un hôpital, dans le district du Val-de-Ruz, a été étudiée par une commission nommée le 5 avril à [E2] Fontainemelon [/E2], dans une assemblée de délégués de quatorze communes. Elle a décidé de faire une souscription particulière à domicile, dans tout le district, et de prier les communes de faire connaître pour le 15 mai quelles sommes elles seraient disposées à verser pour l'hôpital projeté ; cet établissement serait combiné de manière à recevoir aussi des incurables. On pense que Fontainemclon est la localité qui offrirait le plus d'avantages pour la situation de cet hôpital. — Dans la matinée du mercredi 15 avril, on a retiré de l'Areuse, près de Môliers, le corps de la [E1] jeune R [/E1] ."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, avant
    Verb cluster: "retiré" — tense=Past, aspect=None, mood=None
      Sentence: "— Dans la matinée du mercredi 15 avril, on a retiré de l'Areuse, près de Môliers, le corps de la jeune R ."
    Verb cluster: "étudiée" — tense=Past, aspect=None, mood=None
      Sentence: "— La question de la création d'un hôpital, dans le district du Val-de-Ruz, a été étudiée par une commission nommée le 5 "
    Verb cluster: "pense" — tense=Pres, aspect=None, mood=Ind
      Sentence: "On pense que Fontainemclon est la localité qui offrirait le plus d'avantages pour la situation de cet hôpital."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 49 (0 = most prominent)
    OCR quality estimate: 0.983

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'jeune R' and 'Fontainemelon' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'jeune R' near 'Fontainemelon' around 1868-04-22?
  4. Resolve temporal expressions relative to 1868-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 178:
  Publication date : 1880-03-09
  Language         : en
  Person  : 'Ve\nnard'  (QID: N/A)
  Location: 'Nevada, Col.'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "A Western paper tells the story of Steve Venard’s fight with three rob bers in 1866. The stage coming to [E2] Nevada, Col. [/E2], had been robbed by three men, and the treasure-box taken. He found him running up the mount ain, sixty yards or more ahead. Ve nard fired and the robber fell."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1866" → 1866
    Verb cluster: "found" — tense=Past, aspect=None, mood=None
      Sentence: "He found him running up the mount ain, sixty yards or more ahead."
    Verb cluster: "tells" — tense=Pres, aspect=None, mood=None
      Sentence: "A Western paper tells the story of Steve Venard’s fight with three rob bers in 1866."
    Verb cluster: "had been robbed" — tense=Past, aspect=Perf, mood=None
      Sentence: "The stage coming to Nevada, Col., had been robbed by three men, and the treasure-box taken."
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 14 days
    Entity sentence position in article: 21 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Ve\nnard' and 'Nevada, Col.' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Ve\nnard' near 'Nevada, Col.' around 1880-03-09?
  4. Resolve temporal expressions relative to 1880-03-09. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 179:
  Publication date : 1810-04-07
  Language         : en
  Person  : 'capt. B.'  (QID: N/A)
  Location: 'Lisbon'  (QID: Q597)

  [ARTICLE TEXT — entity markers added]
  "Capt. Burger, osthe ship John and Ed- ward, left [E2] Lisbon [/E2] on the 5ih."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Lisbon
    Description: municipality and capital city of Portugal
    Country: ['Portugal', 'Roman Republic', 'Kingdom of the Suebi', 'Visigothic Kingdom', 'Umayyad Caliphate', 'emirate of Córdoba', 'Caliphate of Córdoba', 'Taifa of Badajoz', 'Taifa of Lisbon', 'Taifa of Badajoz', 'Almoravid dynasty']
    Located in: ['Lisbon', 'Grande Lisboa Subregion']
    Aliases: {'en': ['Lisboa'], 'fr': ['Lisboa'], 'de': ['Lisboa']}
    Coordinates: [{'lat': 38.708042, 'lon': -9.139016}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "left" — tense=Past, aspect=None, mood=None
      Sentence: "Capt. Burger, osthe ship John and Ed- ward, left Lisbon on the 5ih."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.947

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'capt. B.' and 'Lisbon' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'capt. B.' near 'Lisbon' around 1810-04-07?
  4. Resolve temporal expressions relative to 1810-04-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 180:
  Publication date : 1878-10-02
  Language         : de
  Person  : 'Fröbel'  (QID: Q76679)
  Location: 'Philadelphia'  (QID: Q1345)

  [ARTICLE TEXT — entity markers added]
  "Sie wurde unseres Wissens zum ersten Mal in Paris 1867 versucht, kam dann in Wien 1873 und in [E2] Philadelphia [/E2] 1876 zur Ausführung und jetzt wiederum und zwar in großem Maßstab in Paris. Gegenüber andern Kultur zweigen treten zwar die Schulen immer noch zurück, nicht in ihren Leistungen, wohl aber in der Schätzung, die sie erfahren. wo die Volksschulen, welche sie besitzen? — Mailand stellt Arbeiten der [E1] Fröbel [/E1]schulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die Kinder weit überschreiten:"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Friedrich Fröbel
    Description: deutscher Pädagoge
    Born: ['+1782-04-21T00:00:00Z', '+1782-00-00T00:00:00Z']
    Died: ['+1852-06-21T00:00:00Z', '+1852-00-00T00:00:00Z']
    Birth place: ['Oberweißbach/Thüringer Wald']
    Death place: ['Q1897986']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1867" → 1867
      - "1873" → 1873
      - "1876" → 1876
    Temporal signal words: jetzt
    Verb cluster: "stellt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "— Mailand stellt Arbeiten der Fröbelschulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die "
    Verb cluster: "wurde" — tense=Past, aspect=None, mood=Ind
      Sentence: "Sie wurde unseres Wissens zum ersten Mal in Paris 1867 versucht, kam dann in Wien 1873 und in Philadelphia 1876 zur Ausf"
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 2 days
    Entity sentence position in article: 27 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Fröbel' and 'Philadelphia' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Fröbel' near 'Philadelphia' around 1878-10-02?
  4. Resolve temporal expressions relative to 1878-10-02. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 181:
  Publication date : 1921-02-22
  Language         : fr
  Person  : 'M. Stadler'  (QID: N/A)
  Location: 'Berne'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "chanteurs de Genève-Ville organisent, avec le concours de M Stalder. de [E2] Berne [/E2], une soirée de pioiections lumineuses qui sera donnée dans la salle de la Réformation, le 2 mars 'prochain. M. Stalder a déjà fait avec le Plus scrand SUCCÈS de nombreuses conférences de ce eenre en Suisse romande, en France et en Belgique. C'est en véritable artiste, amoureux de l'Alpe. que [E1] M. Stadler [/E1] a patiemment recueilli la splendide collection de clichés colorés, an moyen desquels ii nous promènera en zigzag dans les cantons alpins."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Verb cluster: "organisent" — tense=Pres, aspect=None, mood=Ind
      Sentence: "chanteurs de Genève-Ville organisent, avec le concours de M Stalder."
    Verb cluster: "sera" — tense=Fut, aspect=None, mood=Ind
      Sentence: "de Berne, une soirée de pioiections lumineuses qui sera donnée dans la salle de la Réformation, le 2 mars 'prochain."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 30 (0 = most prominent)
    OCR quality estimate: 0.932

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Stadler' and 'Berne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Stadler' near 'Berne' around 1921-02-22?
  4. Resolve temporal expressions relative to 1921-02-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 182:
  Publication date : 1868-02-19
  Language         : de
  Person  : 'Bismarck'  (QID: Q8442)
  Location: 'Hietzing'  (QID: Q1228247)

  [ARTICLE TEXT — entity markers added]
  "Rechte und die provinzielle Selbſtſtändigkeit der gewonnenen Landestheile mit ſolcher Fürſorge wahrt , nicht eine engberzige Eroberungspolitik , ſondern eine wahrhaft nationale Politik be⸗ mit wie gutem Rechte Graf [E1] Bismarck [/E1] darauf hindeutete , daß dieſe hannoverſche Frage nur im Zuſammenhange der geſammten Politik Preußens richtig beurtheilt werden könne . konservative Partei , welche der Regierung bisher mit vollem Vertrauen und mit Hingebung gefolgt iſt , fort und fort ihre Aufgabe und ihre Ehre darin finden werde , einer Regierung , welche ſo Großes für Preußen und Deutſchland errungen und geſchaffen folgt und eben deshalb das Vertrauen des deutſchen Volkes in vollem Maße in Anſpruch nehmen darf . Es bewährt ſich hierin , Jndem das Herrenhaus durch ſeinen jüngſten Beſchluß von Neuem mit vollſter Entſchiedenheit für dieſe Politik eingetreten iſt , hat daſſelbe zugleich die Zuverſicht erhöht , daß die konſervative Partei Die ſogenaunte Hannoverſche Legion . Aufenthalt in [E2] Hietzing [/E2] , die Regierung dann verpflichtet ſein wird , das Während die preußiſche Regierung dem früheren König von Hannover die größte und edelſte Rückſicht zu Theil werden läßt , während andererſeits ihre Fürſorge für die neue Provinz unter der be — des Königs Georg und ſeiner Umgebung in Hietzing die verwerflichen Verſuche fortgeſetzt , einen Theil ſeiner früheren Unterthanen , meiſt aus den unterſten Ständen , für das völlige boffnungsloſe und thörichte Unternehmen einer Wiederherſtellung ſeines Thrones zu gewinnen ."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Otto von Bismarck
    Description: deutscher Politiker und Staatsmann
    Born: ['+1815-04-01T00:00:00Z', '+1815-01-01T00:00:00Z']
    Died: ['+1898-07-30T00:00:00Z', '+1898-01-01T00:00:00Z']
    Birth place: ['Q59974']
    Death place: ['Q695011']
    Work locations: ['Berlin', 'Friedrichsruh', 'Q1015028']
  Location Wikidata:
    Label: Hietzing
    Description: Bezirksteil (Zentrum) des 13. Wiener Gemeindebezirks (Hietzing)
    Country: ['Österreich']
    Located in: ['Wien', 'Hietzing']
    Aliases: {'de': ['Alt-Hietzing']}
    Coordinates: [{'lat': 48.1856, 'lon': 16.2986}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: früher, früh
    Verb cluster: "wahrt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Rechte und die provinzielle Selbſtſtändigkeit der gewonnenen Landestheile mit ſolcher Fürſorge wahrt , nicht eine engber"
    Verb cluster: "verpflichtet" — tense=None, aspect=None, mood=None
      Sentence: "Aufenthalt in Hietzing , die Regierung dann verpflichtet ſein wird , das Während die preußiſche Regierung dem früheren K"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 26 (0 = most prominent)
    OCR quality estimate: 0.994

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Bismarck' and 'Hietzing' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Bismarck' near 'Hietzing' around 1868-02-19?
  4. Resolve temporal expressions relative to 1868-02-19. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 183:
  Publication date : 1830-03-03
  Language         : en
  Person  : 'Ferdinand'  (QID: N/A)
  Location: 'Vir\nginia'  (QID: Q1370)

  [ARTICLE TEXT — entity markers added]
  "The Richmond Whig says, “Vir ginia is brought to the alternative which i^e long ago predicted—-either to secede fiom the Union, or to ac quiesce in the Tariff.” So far we agree with the above, that we have long believed no real change of the tarifl' would take place; that those who tax us for their own benefit are and will continue to be a majority, & that we must act decided ly, be the consequence what it may, or “acquiesce” in infractions of our liberties and interests,. They well know that a sep aration of the Union would be a der.th blow to the Northern Atlantic .sea board, and of course a great injury to tbe interior. But to those who, when— not tri fling, not speculative, but'important, practical lights are taken from us, even the most important of all,- s*“lf-' government—to those who in sucit times shrink Iroin acting, and entrench themselves behind arguments and sen timents which have been in all ages the apology for submission and servi tude; we would recommend to them as a master the beloved [E1] Ferdinand [/E1], or, better' yet, the amiable Don Mi- gucl."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Virginia
    Description: state of the United States of America
    Country: ['United States']
    Located in: ['United States']
    Aliases: {'en': ['Commonwealth of Virginia', 'State of Virginia', 'VA', 'Virginia, United States', 'Old Dominion', 'Va.', 'US-VA'], 'de': ['Virginien']}
    Coordinates: [{'lat': 37.5, 'lon': -79}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now
    Verb cluster: "would recommend" — tense=None, aspect=None, mood=None
      Sentence: "But to those who, when— not tri fling, not speculative, but'important, practical lights are taken from us, even the most"
    Verb cluster: "says" — tense=Pres, aspect=None, mood=None
      Sentence: "The Richmond Whig says, “Vir ginia is brought to the alternative which i^e long ago predicted—-either to secede fiom the"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 8 (0 = most prominent)
    OCR quality estimate: 1.000

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Ferdinand' and 'Vir\nginia' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Ferdinand' near 'Vir\nginia' around 1830-03-03?
  4. Resolve temporal expressions relative to 1830-03-03. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 184:
  Publication date : 1826-06-30
  Language         : fr
  Person  : 'Ibrahim'  (QID: N/A)
  Location: 'Patras'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Ni [E1] Ibrahim [/E1] qui, après s'être dirigé sur Calavrita, a été obligé de se replier sur [E2] Patras [/E2], ni Chiutaehi, qui se trouvait dans la Grèce occidentale, n'ont entrepris auGune opération, tant ils ont été affaiblis par les pertes que leurs troupes ont éprouvées devant Missolonghi."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: après
    Verb cluster: "obligé" — tense=Past, aspect=None, mood=None
      Sentence: "Ni Ibrahim qui, après s'être dirigé sur Calavrita, a été obligé de se replier sur Patras, ni Chiutaehi, qui se trouvait "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 13 (0 = most prominent)
    OCR quality estimate: 0.989

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Ibrahim' and 'Patras' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Ibrahim' near 'Patras' around 1826-06-30?
  4. Resolve temporal expressions relative to 1826-06-30. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 185:
  Publication date : 1918-04-22
  Language         : fr
  Person  : 'Schoeller'  (QID: N/A)
  Location: 'N-ûenhoî'  (QID: Q64461)

  [ARTICLE TEXT — entity markers added]
  "[E2] N-ûenhoî [/E2], près Wettingen, 19 avril 1918. Lorsque, un jour, un de mes copains de lège avait à donner la définition du mot « Ce geste, le Conseil fédéral n' avait pas le droit de le faire. M. Schœller n'étant pas fonctionnaire fédéral, mais un simple particulier."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Neuenhof
    Description: commune suisse
    Country: ['Suisse']
    Located in: ["canton d'Argovie", 'district de Baden']
    Aliases: {'en': ['Neuenhof AG'], 'de': ['Neuenhof AG']}
    Coordinates: [{'lat': 47.446944444444, 'lon': 8.3291666666667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1918" → 1918
    Verb cluster: "avait" — tense=Imp, aspect=None, mood=Ind [NEGATED]
      Sentence: "Ce geste, le Conseil fédéral n' avait pas le droit de le faire."
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    Entity sentence position in article: 10 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Schoeller' and 'N-ûenhoî' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Schoeller' near 'N-ûenhoî' around 1918-04-22?
  4. Resolve temporal expressions relative to 1918-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 186:
  Publication date : 1898-05-02
  Language         : de
  Person  : 'Hr.\nKoller'  (QID: Q123734)
  Location: 'Zürichhorn'  (QID: Q248693)

  [ARTICLE TEXT — entity markers added]
  "Andolf Koler-Inbiläums-Ansstellung in Zürich. A. F. Für die Besichtigung der Ateliers am [E2] Zürichhorn [/E2] erhält der Ausstellungsbesucher an der Kasse im Künstlerhaus bezw. in der Börse unentgeltlich eine besondere Einlaßkarte, die zum Besuche der Kollerschen Ateliers berechtigt."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Zürichhorn
    Description: Schwemmkegel am Ostufer des unteren Seebeckens des Zürichsees
    Country: ['Q39']
    Located in: ['Zürich', 'Kanton Zürich']
    Aliases: {'en': ['Zurichhorn']}
    Coordinates: [{'lat': 47.3536, 'lon': 8.55211}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "berechtigt" — tense=None, aspect=None, mood=None
      Sentence: "in der Börse unentgeltlich eine besondere Einlaßkarte, die zum Besuche der Kollerschen Ateliers berechtigt."
    Verb cluster: "erhält" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Für die Besichtigung der Ateliers am Zürichhorn erhält der Ausstellungsbesucher an der Kasse im Künstlerhaus bezw."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 34 (0 = most prominent)
    OCR quality estimate: 0.998

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Hr.\nKoller' and 'Zürichhorn' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Hr.\nKoller' near 'Zürichhorn' around 1898-05-02?
  4. Resolve temporal expressions relative to 1898-05-02. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 187:
  Publication date : 1938-11-13
  Language         : de
  Person  : 'Siurgenenger'  (QID: N/A)
  Location: 'Voralpenlandschaft'  (QID: Q670576)

  [ARTICLE TEXT — entity markers added]
  "Da jedoch der Bund 80 Prozent an die Kosten wird zahlen müssen, geht das Vorhaben nicht nur die St. Galler an, sondern alle, die wissen, daß wir schon längst nicht mehr so dick im Reichtum sitzen, daß man die immer seltener werdenden land schaftlichen Kleinodien unserer [E2] Voralpenlandschaft [/E2] einfach verschleudern darf. Es handelt sich bei dem in Frage stehenden Pro jekt um die Umgestaltung des als „Alter Rhein" bezeichneten, reichgewundenen Wasserarms, der als Jahrzeichen der zwischen St. Margrethen und Boden see liegenden Niederungen das ganze sogenannte Alte Kheintal beherrscht (siehe Situationsbild). Leider ist es freilich auch schon das Letzte! Ie: Dand [E1] Siurgenenger [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Voralpen
    Description: mountain range
    Country: ['Schweiz']
    Located in: ['Kanton Appenzell Ausserrhoden', 'Kanton Appenzell Innerrhoden', 'Kanton Zürich', 'Kanton Freiburg', 'Kanton Waadt', 'Kanton St. Gallen', 'Kanton Luzern', 'Kanton Obwalden', 'Kanton Nidwalden', 'Q11911', 'Kanton Zug', 'Kanton Schwyz']
    Aliases: {'de': ['Schweizer Voralpen'], 'lb': ['Viralpen']}
    Coordinates: [{'lat': 46.5572, 'lon': 7.83528}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nicht mehr, vor
    Verb cluster: "geht" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Da jedoch der Bund 80 Prozent an die Kosten wird zahlen müssen, geht das Vorhaben nicht nur die St. Galler an, sondern a"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 26 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Siurgenenger' and 'Voralpenlandschaft' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Siurgenenger' near 'Voralpenlandschaft' around 1938-11-13?
  4. Resolve temporal expressions relative to 1938-11-13. Are they within ±14 days?
