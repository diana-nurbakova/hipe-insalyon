# Task B: isAt

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

TASK: "isAt" — Physical presence
Determine whether the PERSON was physically present at / living in the LOCATION
at the time the newspaper article was written (i.e. around the publication date).
  - TRUE  : the person WAS at or living in that location at document time
            (present tense, 'currently', 'residing', timex within ±2 weeks)
  - FALSE : the person was NOT there at document time
            (past tense only, 'formerly', 'used to', negation, person deceased)
Note: isAt has NO PROBABLE label — it is a binary TRUE / FALSE decision.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FEW-SHOT EXAMPLES FROM THE TRAIN SPLIT FOR TASK 'isAt'
These examples are already labeled. Learn the decision pattern from them.

────────────────────────────────────────────────────────────
Sample 0:
  Publication date : 1810-05-30
  Language         : en
  Person  : 'JAMES MADISON'  (QID: Q11813)
  Location: 'United States'  (QID: Q30)

  [ARTICLE TEXT — entity markers added]
  "A a act providing for fWr| census or enumeration of tire inhabitants of I he [E2] United States [/E2] . ** May 1, 1810. Approved, [E1] JAMES MADISON [/E1]."

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
    Temporal expressions found (2):
      - "1810" → 1810
      - "May 1, 1810" → May 1, 1810
    Verb cluster: "Approved" — tense=Past, aspect=Perf, mood=None
      Sentence: "Approved, JAMES MADISON."
    Verb cluster: "providing" — tense=Pres, aspect=Prog, mood=None
      Sentence: "A a act providing for fWr| census or enumeration of tire inhabitants of I he United States ."
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    Entity sentence position in article: 12 (0 = most prominent)
    OCR quality estimate: 0.989

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'JAMES MADISON' and 'United States' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'JAMES MADISON' near 'United States' around 1810-05-30?
  4. Resolve temporal expressions relative to 1810-05-30. Are they within ±14 days?
Correct label for task 'isAt': TRUE
Key cue summary: verb cue: Approved [Past, Perf]; resolved timex falls inside the isAt window

────────────────────────────────────────────────────────────
Sample 1:
  Publication date : 1948-10-09
  Language         : fr
  Person  : 'VAAST'  (QID: Q729132)
  Location: 'Suisse'  (QID: Q39)

  [ARTICLE TEXT — entity markers added]
  "Mais les dirigeants du SBB voudraient bien que les organisateurs çais avancent leur épreuve d'une semaine afin que l'on trouve le moyen d'insérer le Tour de [E2] Suisse [/E2] entre le Tour de France et les championnats du monde. Après un échange de vue sur les enseignements de la course de 1948, les organisateurs ont décidé qu'elle serait courue dans le même sens, c'est-à dire d'ouest à est. De * nombreuses candidatures de villes sont parvenues aux organisateurs, mais l'itinéraire définitif ne sera établi que plus tard. Le Tour de 1949 sera disputé selon la formule équipes nationales et régionales. Football [E1] VAAST [/E1], DU RACING PARIS, SIGNE AU SERVETTE Le joueur du Racing Vaast, fixé à Genève, a envoyé sa lettre de démission au Racing et a signé au Servette."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Ernest Vaast
    Description: footballeur français
    Born: ['+1922-10-28T00:00:00Z']
    Died: ['+2011-04-10T00:00:00Z']
    Birth place: ['5e arrondissement de Paris']
    Death place: ['Clermont-Ferrand']
  Location Wikidata:
    Label: Suisse
    Description: pays d'Europe centrale
    Country: ['Suisse']
    Aliases: {'en': ['Swiss Confederation', 'Swiss', 'Confoederatio Helvetica'], 'fr': ['Confédération helvétique', 'Confédération suisse', 'SUI', 'Helvétie', 'la Confédération suisse'], 'de': ['Schweizerische Eidgenossenschaft', 'Eidgenossenschaft', 'SUI', 'Confoederatio Helvetica', 'Confœderatio Helvetica'], 'lb': ['SUI']}
    Coordinates: [{'lat': 46.798562, 'lon': 8.231973}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1948" → 1948
      - "1949" → 1949
    Temporal signal words: plus, après, tard
    Verb cluster: "voudraient" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Mais les dirigeants du SBB voudraient bien que les organisateurs çais avancent leur épreuve d'une semaine afin que l'on "
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    Entity sentence position in article: 4 (0 = most prominent)
    OCR quality estimate: 0.954

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'VAAST' and 'Suisse' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'VAAST' near 'Suisse' around 1948-10-09?
  4. Resolve temporal expressions relative to 1948-10-09. Are they within ±14 days?
Correct label for task 'isAt': TRUE
Key cue summary: temporal signals: plus, après, tard; verb cue: voudraient [Pres, Ind]; resolved timex falls inside the isAt window

────────────────────────────────────────────────────────────
Sample 2:
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
Correct label for task 'isAt': TRUE
Key cue summary: temporal signals: vor; verb cue: erklärt [Pres, Ind]; resolved timex falls inside the isAt window

────────────────────────────────────────────────────────────
Sample 3:
  Publication date : 1978-09-27
  Language         : fr
  Person  : 'Thompson'  (QID: Q430706)
  Location: 'Liverpool'  (QID: Q24826)

  [ARTICLE TEXT — entity markers added]
  "Le règne de [E2] Liverpool [/E2] se terminern-t-il ce soir ? La période de domination de Liverpool en coupe d'Europe des clubs champions pourrait se terminer ce soir, à I'Anfield Road, quand les champions de 1977 et 1978, recevront Nottingham Forest, champion d'Angleterre, en match retour du premier tour de cette compétition. Elle compte également, pour réussir, sur l'appui que ne manqueront pas de lui apporter ses fanatiques « supporters ». La composition probable des équipes : Liverpool (4-4-2) : Clémence — Neal, [E1] Thompson [/E1], Hugues (Cap), Alan Kennedy.-Cas, McDermott, Souness, Ray Kennedy.-Dalglish, Johnson ( Fairclough)."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: {"birth_place": "P19"}

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1977" → 1977
      - "1978" → 1978
    Verb cluster: "terminern" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Le règne de Liverpool se terminern-t-il ce soir ?"
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    Entity sentence position in article: 26 (0 = most prominent)
    OCR quality estimate: 0.979

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Thompson' and 'Liverpool' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Thompson' near 'Liverpool' around 1978-09-27?
  4. Resolve temporal expressions relative to 1978-09-27. Are they within ±14 days?
Correct label for task 'isAt': TRUE
Key cue summary: verb cue: terminern [Pres, Ind]; resolved timex falls inside the isAt window; Wikidata links: birth_place

────────────────────────────────────────────────────────────
Sample 4:
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
Correct label for task 'isAt': TRUE
Key cue summary: temporal signals: gestern, nach, vor; verb cue: legte [Past, Ind]; Wikidata links: death_place

────────────────────────────────────────────────────────────
Sample 5:
  Publication date : 1820-05-05
  Language         : en
  Person  : 'King John'  (QID: Q129308)
  Location: 'Great Britain'  (QID: Q23666)

  [ARTICLE TEXT — entity markers added]
  "Sir Wiiliam Blackstono has collated and commented on it—his fine copy of Magna Charta has been excelled by later specimens of art, and the fac-similes of the seals and signatur e.diave made every reader of taste in [E2] Great Britain [/E2] acquainted, in some de gree, not merely with the state ofknowledge and of art at the period in question, but with the literary attainments, al>©, of [E1] King John [/E1], King Henry, and fbeir “ Barons bold.”"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: John, King of England
    Description: King of England from 1199 to 1216
    Born: ['+1166-12-24T00:00:00Z']
    Died: ['+1216-10-19T00:00:00Z']
    Birth place: ['Beaumont Palace']
    Death place: ['Newark Castle']
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
  1. What is the relationship between 'King John' and 'Great Britain' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'King John' near 'Great Britain' around 1820-05-05?
  4. Resolve temporal expressions relative to 1820-05-05. Are they within ±14 days?
Correct label for task 'isAt': FALSE
Key cue summary: temporal signals: now, late, later; verb cue: has been excelled [Pres, Perf, Ind]; person died before the publication date

────────────────────────────────────────────────────────────
Sample 6:
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
Correct label for task 'isAt': FALSE
Key cue summary: temporal signals: ancien; verb cue: plaint [Pres, Ind]; person died before the publication date

────────────────────────────────────────────────────────────
Sample 7:
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
Correct label for task 'isAt': FALSE
Key cue summary: temporal signals: gestern, nach, vor; verb cue: wird [Pres, Ind]; Wikidata links: work_location

────────────────────────────────────────────────────────────
Sample 8:
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
Correct label for task 'isAt': FALSE
Key cue summary: temporal signals: nach, spät; verb cue: folgte [Past, Ind]; person died before the publication date

────────────────────────────────────────────────────────────
Sample 9:
  Publication date : 1838-05-11
  Language         : fr
  Person  : 'don Miguel'  (QID: Q310790)
  Location: 'PORTUGAL'  (QID: Q45)

  [ARTICLE TEXT — entity markers added]
  "[E2] PORTUGAL [/E2]. LisBOKNE 26 aoril. — Un changement partiel vient de s'opérer dans le cabinet. M. d'Oliveira s'est retiré du ministère des finances, en acceptant le titre de baron de Tojal, et il est remplacé par M. de Carvalho, qui avait anciennement été chargé de ce déparlement, et était président de la chambre des députés, quand [E1] don Miguel [/E1] l'avait dissoute en 1828."

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
    Temporal expressions found (1):
      - "1828" → 1828
    Temporal signal words: ancien, ancienne
    Verb cluster: "retiré" — tense=Past, aspect=None, mood=None
      Sentence: "M. d'Oliveira s'est retiré du ministère des finances, en acceptant le titre de baron de Tojal, et il est remplacé par M."
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 10 days
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.985

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'don Miguel' and 'PORTUGAL' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'don Miguel' near 'PORTUGAL' around 1838-05-11?
  4. Resolve temporal expressions relative to 1838-05-11. Are they within ±14 days?
Correct label for task 'isAt': FALSE
Key cue summary: temporal signals: ancien, ancienne; verb cue: retiré [Past]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
END OF FEW-SHOT EXAMPLES

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOW CLASSIFY THE FOLLOWING TEST SAMPLES.
Use the same decision style as in the few-shot examples.
Think through the cues silently, but do not output the reasoning.
Respond with exactly one line per sample in the format:
  Sample N: LABEL | confidence=0.00-1.00
Valid labels: TRUE / FALSE
Confidence must be your calibrated confidence for that label.
Do NOT output explanations, JSON, markdown, or extra commentary.

────────────────────────────────────────────────────────────
Sample 0:
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
Sample 1:
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
Sample 2:
  Publication date : 1918-07-10
  Language         : fr
  Person  : 'ambassadeur actuel à\nChristiania, Hintze'  (QID: N/A)
  Location: 'Finlande'  (QID: Q33)

  [ARTICLE TEXT — entity markers added]
  "On parlé, pour lui succéder, dé M. fîintze, qui, depuis une année, est ministre plénipotentiaire d'Allemagne à Christiania. Le Reichstag a immédiatement envoyé à la commission centrale le projet de crédit afin de se concerter sur lés conséquences politiques de la retraite de M. de Kûhlmann. La décision' définitive n'a néanmoins pas encore été prise. ' __ a [E2] Finlande [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "parlé" — tense=Past, aspect=None, mood=None
      Sentence: "On parlé, pour lui succéder, dé M. fîintze, qui, depuis une année, est ministre plénipotentiaire d'Allemagne à Christian"
    Verb cluster: "a" — tense=Pres, aspect=None, mood=Ind
      Sentence: "' __ a Finlande."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 67 (0 = most prominent)
    OCR quality estimate: 0.956

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'ambassadeur actuel à\nChristiania, Hintze' and 'Finlande' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'ambassadeur actuel à\nChristiania, Hintze' near 'Finlande' around 1918-07-10?
  4. Resolve temporal expressions relative to 1918-07-10. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 3:
  Publication date : 1820-03-06
  Language         : en
  Person  : 'John F. Ferguson'  (QID: N/A)
  Location: 'BaltimorCy'  (QID: Q5092)

  [ARTICLE TEXT — entity markers added]
  "[E2] BaltimorCy [/E2] March 2. This morning, [E1] John F. Ferguson [/E1]."

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
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.993

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'John F. Ferguson' and 'BaltimorCy' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'John F. Ferguson' near 'BaltimorCy' around 1820-03-06?
  4. Resolve temporal expressions relative to 1820-03-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 4:
  Publication date : 1820-05-05
  Language         : en
  Person  : 'Sir Wiiliam Blackstono'  (QID: Q332449)
  Location: 'Philadelphia'  (QID: Q1345)

  [ARTICLE TEXT — entity markers added]
  "[E1] Sir Wiiliam Blackstono [/E1] has collated and commented on it—his fine copy of Magna Charta has been excelled by later specimens of art, and the fac-similes of the seals and signatur e.diave made every reader of taste in Great Britain acquainted, in some de gree, not merely with the state ofknowledge and of art at the period in question, but with the literary attainments, al>©, of King John, King Henry, and fbeir “ Barons bold.” Surely the Declaration of American Inde pendence is, at least, as well entitled to the decorations of art as the Magna. As no more of those copies will be printed than 'ball be subscribed for, gentlemen who wish for them, are requested to add the word “ colored ” to their subscription. JOHN BINNS, Chesnut-street, [E2] Philadelphia [/E2]."

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
  1. What is the relationship between 'Sir Wiiliam Blackstono' and 'Philadelphia' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Sir Wiiliam Blackstono' near 'Philadelphia' around 1820-05-05?
  4. Resolve temporal expressions relative to 1820-05-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 5:
  Publication date : 1868-02-17
  Language         : de
  Person  : "Abbe Migne's"  (QID: Q326431)
  Location: 'London'  (QID: Q84)

  [ARTICLE TEXT — entity markers added]
  "Nach glaubwürdigen [E2] London [/E2]er Privatberichten treten die erfreulichsten Vorzeichen eines kräftigern Geschäfts verkehrs zu Tage. Diese Erscheinung ist um so tröst licher, als die industrielle Krise von 1866 in England zugleich mit einer schlechten Ernte und einer großen Theuerung der Nahrungsmittel verbunden war. Von ihm kursirte die Bitte an den Kaiser in Bordeaux: Sire, ich hoffe, daß Sie mich noch einmal zum Präfekten von London wählen. [E1] Abbe Migne's [/E1] Druckerei der Kirchenväter in Paris ist abgebrannt."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Jacques Paul Migne
    Description: französischer Priester, Schöpfer der Patrologia Latina
    Born: ['+1800-09-05T00:00:00Z', '+1800-10-25T00:00:00Z']
    Died: ['+1875-10-24T00:00:00Z']
    Birth place: ['Saint-Flour']
    Death place: ['Paris']
    Work locations: ['Paris']
  Location Wikidata:
    Label: London
    Description: Hauptstadt und bevölkerungsreichste Stadt des Vereinigten Königreichs
    Country: ['Römisches Kaiserreich', 'Königreich Essex', 'Mercia', 'Q105313', 'Königreich England', 'Königreich Großbritannien', 'Vereinigtes Königreich Großbritannien und Irland', 'Vereinigtes Königreich']
    Located in: ['Königreich Wessex', 'Königreich England', 'England', 'County of London', 'Q23306']
    Aliases: {'en': ['London, UK', 'London, United Kingdom', 'London, England', 'London UK', 'London U.K.', 'Londinium', 'Loñ', 'Lundenwic', 'Londinio', 'Londini', 'Londiniensium', 'Augusta', 'Trinovantum', 'Kaerlud', 'Karelundein', 'Lunden', 'Big Smoke', 'the Big Smoke', 'Lundenburh', 'Lundenburgh', 'Llyn Dain', 'Llan Dian', 'Londinion', 'Loniniensi', 'Lon.', 'Loñ.', 'Lond.', 'LDN'], 'fr': ['London']}
    Coordinates: [{'lat': 51.507222222222, 'lon': -0.1275}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1866" → 1866
    Temporal signal words: nach, vor
    Verb cluster: "kursirte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Von ihm kursirte die Bitte an den Kaiser in Bordeaux: Sire, ich hoffe, daß Sie mich noch einmal zum Präfekten von London"
    Verb cluster: "treten" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Nach glaubwürdigen Londoner Privatberichten treten die erfreulichsten Vorzeichen eines kräftigern Geschäfts verkehrs zu "
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 2 days
    Entity sentence position in article: 30 (0 = most prominent)
    OCR quality estimate: 0.975

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between "Abbe Migne's" and 'London' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing "Abbe Migne's" near 'London' around 1868-02-17?
  4. Resolve temporal expressions relative to 1868-02-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 6:
  Publication date : 1960-04-13
  Language         : en
  Person  : 'Clinton Shipley'  (QID: N/A)
  Location: 'Tabor City'  (QID: Q586130)

  [ARTICLE TEXT — entity markers added]
  "Since the letter is concern ing the [E2] Tabor City [/E2] Yam Mark et it will be of interest to you and it is written below as it appeared in the school paper, “The Valley Hi-Lites." 5811 Idaho Drive Taler Patch, Georgia July 7. 1959 Tabor City Yam Market 54 Main Street Tabor City, North Carolina Gentleman: [E1] Clinton Shipley [/E1] has asked me to recommend him for the International Yam Digging Contest that will take place in Tabor City on the eighteenth * day of September. !"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Tabor City
    Description: town in Columbus County, North Carolina, United States
    Country: ['United States']
    Located in: ['Columbus County']
    Aliases: {'en': ['Tabor City, North Carolina', 'Tabor City, NC']}
    Coordinates: [{'lat': 34.148611111111, 'lon': -78.871944444444}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "5811" → 5811
      - "1959" → 1959
    Verb cluster: "has asked" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "Tabor City Yam Market 54 Main Street Tabor City, North Carolina Gentleman: Clinton Shipley has asked me to recommend him"
    Verb cluster: "is" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Since the letter is concern ing the Tabor City Yam Mark et"
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.967

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Clinton Shipley' and 'Tabor City' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Clinton Shipley' near 'Tabor City' around 1960-04-13?
  4. Resolve temporal expressions relative to 1960-04-13. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 7:
  Publication date : 1868-04-22
  Language         : fr
  Person  : 'colonel Payre'  (QID: N/A)
  Location: 'Magdala'  (QID: Q2279371)

  [ARTICLE TEXT — entity markers added]
  "La distance entre le camp le plus avancé et [E2] Magdala [/E2] est de 60 milles. Le [E1] colonel Payre [/E1] a fait une reconnaissance à 20 milles plus loin."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Amba Mariam
    Description: établissement humain en Éthiopie
    Country: ['Q115']
    Located in: ['Q2919962']
    Aliases: {'en': ['Magdala'], 'fr': ['Meqdela', 'Magdala'], 'de': ['Magdala']}
    Coordinates: [{'lat': 11.2, 'lon': 39.283333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Verb cluster: "fait" — tense=Past, aspect=None, mood=None
      Sentence: "Le colonel Payre a fait une reconnaissance à 20 milles plus loin."
    Verb cluster: "est milles" — tense=Pres, aspect=None, mood=Ind
      Sentence: "La distance entre le camp le plus avancé et Magdala est de 60 milles."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 10 (0 = most prominent)
    OCR quality estimate: 0.983

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'colonel Payre' and 'Magdala' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'colonel Payre' near 'Magdala' around 1868-04-22?
  4. Resolve temporal expressions relative to 1868-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 8:
  Publication date : 1918-04-22
  Language         : fr
  Person  : 'Cléopâtre\nhelvétique'  (QID: N/A)
  Location: 'Su. _sss allemands'  (QID: Q689055)

  [ARTICLE TEXT — entity markers added]
  "Lettre de la [E2] Su. _sss allemands [/E2] ( Mais à présent que j'appartiens dans le pays des Helvètes à cette catégorie privilégiée des gens de la presse, aujourd'hui que je connais depuis de longues années ce que c'est que la politique, je ne ris plus de cette définition. Du moins quand, en parlant de l'histoire suisse, on pense à l'histoire contemporaine sous le régime des pleins pouvoirs, de cette Cléopâtre helvétique."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Suisse alémanique
    Description: région de Suisse dont la population a majoritairement le suisse-allemand comme langue maternelle
    Country: ['Suisse']
    Aliases: {'en': ['German-speaking part of Switzerland', 'German Switzerland'], 'fr': ['Suisse allemande', 'Suisse alemanique'], 'de': ['Deutschsprachige Schweiz', 'Deutsche Schweiz'], 'lb': ['däitschen Deel vun der Schwäiz']}
    Coordinates: [{'lat': 46.952406, 'lon': 7.439583}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: aujourd'hui, plus
    Verb cluster: "pense" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Du moins quand, en parlant de l'histoire suisse, on pense à l'histoire contemporaine sous le régime des pleins pouvoirs,"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 6 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Cléopâtre\nhelvétique' and 'Su. _sss allemands' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Cléopâtre\nhelvétique' near 'Su. _sss allemands' around 1918-04-22?
  4. Resolve temporal expressions relative to 1918-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 9:
  Publication date : 1930-01-15
  Language         : fr
  Person  : 'Falconetti'  (QID: Q440600)
  Location: 'CHATELET'  (QID: Q1469315)

  [ARTICLE TEXT — entity markers added]
  ", La rouille [E1] Falconetti [/E1]).BOUFFES-PARISIENS. 8 h. 45, Flossie[E2] CHATELET [/E2], 8 h. 30 Robert-le-Pirate."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Renée Falconetti
    Description: actrice française
    Born: ['+1892-07-21T00:00:00Z']
    Died: ['+1946-12-12T00:00:00Z']
    Birth place: ['Q209086']
    Death place: ['Buenos Aires']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "FlossieCHATELET" — tense=Past, aspect=None, mood=None
      Sentence: "45, FlossieCHATELET, 8 h. 30 Robert-le-Pirate."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 30 (0 = most prominent)
    OCR quality estimate: 0.824

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Falconetti' and 'CHATELET' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Falconetti' near 'CHATELET' around 1930-01-15?
  4. Resolve temporal expressions relative to 1930-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 10:
  Publication date : 1981-05-13
  Language         : fr
  Person  : 'Philip Habib'  (QID: N/A)
  Location: 'Etats-Unis'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "La réponse est évidente : les deux capitales tentent désespéramment d'éveiller l'intérêt des [E2] Etats-Unis [/E2], et d'attirer ces derniers dans leur jeu respectif. Sur le mode : « Faites quelque chose, arrêteznous, ou nous ne répondons plus de rien ».Depuis l'élection de Ronald Reagan, les Américains ont montré les dispositions suivantes à l'égard du Proche-Orient : 1) Le raisonnement est particulièrement vrai pour Israël qui a vu, il y a quelques semaines, les Etats-Unis disposés à vendre des radars volants à l'Arabie Saoudite, dans un souci prioritaire de renforcer un front antisoviétique dans la région, et en négligeant de considérer les craintes que cette transaction ne pouvait manquer d'éveiller à Jérusalem. La Syrie, quant à elle, a fait savoir à [E1] Philip Habib [/E1], le médiateur dépêché par Ronald Reagan, que les Etats-Unis étaient seuls à pouvoir influencer efficacement la politique israélienne."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Verb cluster: "a" — tense=Pres, aspect=None, mood=Ind
      Sentence: "La Syrie, quant à elle, a fait savoir à Philip Habib, le médiateur dépêché par Ronald Reagan, que les Etats-Unis étaient"
    Verb cluster: "est évidente" — tense=Pres, aspect=None, mood=Ind
      Sentence: "La réponse est évidente : les deux capitales tentent désespéramment d'éveiller l'intérêt des Etats-Unis, et d'attirer ce"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 22 (0 = most prominent)
    OCR quality estimate: 0.988

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Philip Habib' and 'Etats-Unis' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Philip Habib' near 'Etats-Unis' around 1981-05-13?
  4. Resolve temporal expressions relative to 1981-05-13. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 11:
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
Sample 12:
  Publication date : 1868-06-16
  Language         : de
  Person  : 'HH. Hüni'  (QID: N/A)
  Location: 'Thalweil'  (QID: Q68959)

  [ARTICLE TEXT — entity markers added]
  "Zum Hauptmann bei den Scharfschützen wird Hr. Oberlieutenant Syfrig von [E2] Thalweil [/E2], wohnhaft in Mettmenstetten, ernannt. Die HH."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Thalwil
    Description: Gemeinde in der Schweiz
    Country: ['Q39']
    Located in: ['Bezirk Horgen']
    Aliases: {'en': ['Thalwil ZH']}
    Coordinates: [{'lat': 47.295277777778, 'lon': 8.5647222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Zum Hauptmann bei den Scharfschützen wird Hr. Oberlieutenant Syfrig von Thalweil, wohnhaft in Mettmenstetten, ernannt."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.990

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'HH. Hüni' and 'Thalweil' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'HH. Hüni' near 'Thalweil' around 1868-06-16?
  4. Resolve temporal expressions relative to 1868-06-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 13:
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
Sample 14:
  Publication date : 1868-04-22
  Language         : fr
  Person  : 'Thédoros'  (QID: N/A)
  Location: 'Magdala'  (QID: Q2279371)

  [ARTICLE TEXT — entity markers added]
  "La distance entre le camp le plus avancé et [E2] Magdala [/E2] est de 60 milles. Le colonel Payre a fait une reconnaissance à 20 milles plus loin. [E1] Thédoros [/E1] est toujours à Magdala."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Amba Mariam
    Description: établissement humain en Éthiopie
    Country: ['Éthiopie']
    Located in: ['Debub Wollo']
    Aliases: {'en': ['Magdala'], 'fr': ['Meqdela', 'Magdala'], 'de': ['Magdala']}
    Coordinates: [{'lat': 11.2, 'lon': 39.283333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Verb cluster: "fait" — tense=Past, aspect=None, mood=None
      Sentence: "Le colonel Payre a fait une reconnaissance à 20 milles plus loin."
    Verb cluster: "est milles" — tense=Pres, aspect=None, mood=Ind
      Sentence: "La distance entre le camp le plus avancé et Magdala est de 60 milles."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 11 (0 = most prominent)
    OCR quality estimate: 0.983

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Thédoros' and 'Magdala' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Thédoros' near 'Magdala' around 1868-04-22?
  4. Resolve temporal expressions relative to 1868-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 15:
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
Sample 16:
  Publication date : 1888-03-08
  Language         : de
  Person  : 'Dynamithelden Cyvoct'  (QID: Q17350092)
  Location: 'Numea'  (QID: Q9733)

  [ARTICLE TEXT — entity markers added]
  "Den Vorwand zu dem Meeting gab das Todesurtheil ab, welches das Kriegsgericht in [E2] Numea [/E2] über zwei Sträflinge, die [E1] Dynamithelden Cyvoct [/E1] und Gallo, gefällt hat."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Antoine Cyvoct
    Description: in Frankreich zum Tode verurteilt
    Born: ['+1861-02-28T00:00:00Z']
    Died: ['+1930-04-05T00:00:00Z', '+1930-05-04T00:00:00Z']
  Location Wikidata:
    Label: Nouméa
    Description: Hauptstadt und Gemeinde Neukaledoniens
    Country: ['Frankreich']
    Located in: ['Südprovinz', 'Aire coutumière Djubéa-Kaponé']
    Aliases: {'en': ['Noumea'], 'fr': ['COMMUNE DE NOUMEA'], 'de': ['Numea'], 'lb': ['Nouméa']}
    Coordinates: [{'lat': -22.266666666667, 'lon': 166.45}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "gab" — tense=Past, aspect=None, mood=Ind
      Sentence: "Den Vorwand zu dem Meeting gab das Todesurtheil ab, welches das Kriegsgericht in Numea über zwei Sträflinge, die Dynamit"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 17 (0 = most prominent)
    OCR quality estimate: 0.990

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Dynamithelden Cyvoct' and 'Numea' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Dynamithelden Cyvoct' near 'Numea' around 1888-03-08?
  4. Resolve temporal expressions relative to 1888-03-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 17:
  Publication date : 1928-10-25
  Language         : fr
  Person  : 'Démosthène'  (QID: Q117253)
  Location: 'Genève'  (QID: Q71)

  [ARTICLE TEXT — entity markers added]
  "Les choses semblent devoir se passer beau coup plus calmement dans le canton de Vaud, où aucun changement notable n'est prévu, et à [E2] Genève [/E2], où l'on s'attend généralement à un déchet démocrate en faveur du parti de défense économique. C'est M. de Rabours que tous livrent d'avance au fatal couperet de la guillotine sèche. Si pareille prédiction devait se vérifier exacte, le Parlement perdrait une de ses figures les plus sympathiques et l'un de ses meilleurs orateurs, à un moment où les disciples de [E1] Démosthène [/E1], à Berne, se comptent presque sur les doigts 1..."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Démosthène
    Description: homme d'état et orateur athénien
    Born: ['-0384-01-01T00:00:00Z']
    Died: ['-0322-10-12T00:00:00Z']
    Birth place: ['Q3411612']
    Death place: ['Póros']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Verb cluster: "perdrait" — tense=Imp, aspect=None, mood=Ind
      Sentence: "Si pareille prédiction devait se vérifier exacte, le Parlement perdrait une de ses figures les plus sympathiques et l'un"
    Verb cluster: "semblent" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Les choses semblent devoir se passer beau coup plus calmement dans le canton de Vaud, où aucun changement notable n'est "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 17 (0 = most prominent)
    OCR quality estimate: 0.982

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Démosthène' and 'Genève' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Démosthène' near 'Genève' around 1928-10-25?
  4. Resolve temporal expressions relative to 1928-10-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 18:
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
Sample 19:
  Publication date : 1826-09-29
  Language         : fr
  Person  : "M'.'Càrnéro"  (QID: N/A)
  Location: 'ehPortugal'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Le ministère est positivement informa par les rapports officiels des gouverneurs d'Estramadure et de Galice, que la désertion a jusqu'à ce jour enlevé à l'armée espagnole 3400 hommes, " dont 2000 sont entrés'[E2] ehPortugal [/E2] par l'Estramadure portugaise, qu'on nomme l'Alentejo, et 1400 par la province de Tras-los-Montès."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "3400" → 3400
      - "2000" → 2000
      - "1400" → 1400
    Verb cluster: "est positivement" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Le ministère est positivement informa par les rapports officiels des gouverneurs d'Estramadure et de Galice, que la dése"
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 174 days
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between "M'.'Càrnéro" and 'ehPortugal' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing "M'.'Càrnéro" near 'ehPortugal' around 1826-09-29?
  4. Resolve temporal expressions relative to 1826-09-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 20:
  Publication date : 1826-09-29
  Language         : fr
  Person  : 'don Nazàrio-Eguia'  (QID: N/A)
  Location: 'Afrique'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  ", D'un autre côté, on apprend que le plus grand nombre d'Espagnols qui se trouvaient réfugiés en Angleterre, à Gibraltar", et sur divers points de l'[E2] Afrique [/E2], se sont déjà rendus à Lisbonne ^ Nul doute que, si le gouvernement portugais y consent, il né'se formé, bientôt une armée espagnole au service du Portugal ,-'X '''.'-',. '. Heureusement que ce capitaine-général est un homme ferme et habile, et dont le dévouement est garanti par des preuves de fidélité. C'est [E1] don Nazàrio-Eguia [/E1]..."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, tôt
    Verb cluster: "est don" — tense=Pres, aspect=None, mood=Ind
      Sentence: "C'est don Nazàrio-Eguia..."
    Verb cluster: "apprend" — tense=Pres, aspect=None, mood=Ind
      Sentence: ", D'un autre côté, on apprend que le plus grand nombre d'Espagnols qui se trouvaient réfugiés en Angleterre, à Gibraltar"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 14 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'don Nazàrio-Eguia' and 'Afrique' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'don Nazàrio-Eguia' near 'Afrique' around 1826-09-29?
  4. Resolve temporal expressions relative to 1826-09-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 21:
  Publication date : 1961-01-20
  Language         : fr
  Person  : 'M. F. Stirnimann'  (QID: N/A)
  Location: 'Lamalou-les-Bains'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "TIR Décès de [E1] M. F. Stirnimann [/E1] CYCLISME.— Le Dr Stern, directeur de la clinique de rééducation de [E2] Lamalou-les-Bains [/E2], a rendu visite à Roger Rivière, qu'il avait soigné le premier après sa chute dans le Tour de France."

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
    Entity sentence position in article: 7 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. F. Stirnimann' and 'Lamalou-les-Bains' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. F. Stirnimann' near 'Lamalou-les-Bains' around 1961-01-20?
  4. Resolve temporal expressions relative to 1961-01-20. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 22:
  Publication date : 1858-02-24
  Language         : de
  Person  : 'Graf Morny'  (QID: Q965335)
  Location: 'Frankreich'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "Der Anblick, welchen [E2] Frankreich [/E2] seit einiger Zeit gewährt, ist im höchsten Grade betrübend und Be» sorgniß erregend, Trotz der gewaltigen Hand, welche seit dem 2. Dez. 1852 dort die Zügel der Regie» nlng gefaßt , ist die Revolution doch eine per» man ente geblieben; als sich selbst. Diese Permanenz der Revolution in Frankreich wird aber jetzt allerdings äußerlich weniger ficht» bar, desto mehr aber fühlt man sie, und wenn Männer wie [E1] Graf Morny [/E1],in officielle» Ac» tcnstücken diese Permanenz der Revolution an er» kennen, in Actenstücken, welche der amtliche Moniteur veröffentlicht, dann muß die Sache weit gedi'chen sein."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
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
    Temporal signal words: jetzt
    Verb cluster: "muß" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Diese Permanenz der Revolution in Frankreich wird aber jetzt allerdings äußerlich weniger ficht» bar, desto mehr aber fü"
    Verb cluster: "ist" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Der Anblick, welchen Frankreich seit einiger Zeit gewährt, ist im höchsten Grade betrübend und Be» sorgniß erregend, Tro"
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 6 days
    Entity sentence position in article: 17 (0 = most prominent)
    OCR quality estimate: 0.990

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Graf Morny' and 'Frankreich' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Graf Morny' near 'Frankreich' around 1858-02-24?
  4. Resolve temporal expressions relative to 1858-02-24. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 23:
  Publication date : 1858-02-24
  Language         : de
  Person  : 'Napoleons l'  (QID: Q517)
  Location: 'L rnnburg'  (QID: Q32)

  [ARTICLE TEXT — entity markers added]
  "Auf die Bourboncn folgte die Pöbelherrschaft, auf diese [E1] Napoleons l [/E1]. Gewaltregiment, dieser wurde dann wieder durch die Bourbonen verdrängt, deren Regierungsfähig» keit in der Thai erloschen schien, als Ludwig Phil» livpe sie mit einem Hauche vom Throne blasen konnte, um achtzehn Jahre später noch schmählicher gestürzt zu werden! Nach ihm, der nichts gethan, mn Frankreich moralisch zu heben, — worin doch die einzige Stütze seiner Monarchie bestand, —nach ihm sehen wir wieder die Pöbelherrschaft im wilde» sten Auswüchse, wir sehen die Nepublick gegen ihre eigenen Ultras die blutigsten Straßenkampfe führen, Ins zuletzt Napoleon !11. abermals über Nacht dem ein Ende und sich zum Herrscher Frankreichs machte. Zeitung" geriren wollte; wir entnehmen das daraus, daß er die Assisen« und (Zerichtver» Handlungen in [E2] L rnnburg [/E2] berichtet, wie denn auch^ daß er die unten stehende Erklärung über die Eisenbahnfrage abgegeben hat."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Napoleon Bonaparte
    Description: französischer General, Staatsmann und Kaiser
    Born: ['+1769-08-15T00:00:00Z', '+1769-01-01T00:00:00Z']
    Died: ['+1821-05-05T00:00:00Z', '+1821-01-01T00:00:00Z']
    Birth place: ['Q40104']
    Death place: ['Longwood House']
    Residences: ['St. Helena', 'Ajaccio', 'Paris', 'Elba']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, spät
    Verb cluster: "folgte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Auf die Bourboncn folgte die Pöbelherrschaft, auf diese Napoleons l. Gewaltregiment, dieser wurde dann wieder durch die "
    Verb cluster: "entnehmen" — tense=Pres, aspect=None, mood=Ind
      Sentence: "wir entnehmen das daraus, daß er die Assisen« und (Zerichtver» Handlungen in L rnnburg berichtet, wie denn auch^ daß er "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.990

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Napoleons l' and 'L rnnburg' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Napoleons l' near 'L rnnburg' around 1858-02-24?
  4. Resolve temporal expressions relative to 1858-02-24. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 24:
  Publication date : 1886-06-22
  Language         : de
  Person  : 'Bismarck'  (QID: Q8442)
  Location: 'Südafrika'  (QID: Q258)

  [ARTICLE TEXT — entity markers added]
  "Juni ſind es zwei Jahre , daß der Reichskanzler Fürſt [E1] Bismarck [/E1] bei Gelegenheit der Berathung der damals eingebrachten erſten Poſt⸗ Dampfervorlage der Budgetcommiſſion di Mittheilung machte , daß die Lüderitz 'ſchen Erwerbungen in [E2] Südafrika [/E2] ohne Widerſpruch Englands unter deutſchen Schutz geſtellt ſeien ."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Südafrika
    Description: Staat im Süden Afrikas
    Country: ['Südafrika']
    Aliases: {'en': ['Republic of South Africa', 'RSA', 'SA', 'zaf', 'R.S.A.'], 'fr': ['République sud-africaine', 'République d’Afrique du Sud', 'république sud-africaine', 'république d’Afrique du Sud'], 'de': ['Suedafrika', 'Republik Südafrika']}
    Coordinates: [{'lat': -29, 'lon': 24}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "ſind" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Juni ſind es zwei Jahre , daß der Reichskanzler Fürſt Bismarck bei Gelegenheit der Berathung der damals eingebrachten er"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 27 (0 = most prominent)
    OCR quality estimate: 0.993

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Bismarck' and 'Südafrika' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Bismarck' near 'Südafrika' around 1886-06-22?
  4. Resolve temporal expressions relative to 1886-06-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 25:
  Publication date : 1868-02-19
  Language         : de
  Person  : 'Georg'  (QID: Q57428)
  Location: 'Schweiz'  (QID: Q39)

  [ARTICLE TEXT — entity markers added]
  "Aufenthalt in Hietzing , die Regierung dann verpflichtet ſein wird , das Während die preußiſche Regierung dem früheren König von Hannover die größte und edelſte Rückſicht zu Theil werden läßt , während andererſeits ihre Fürſorge für die neue Provinz unter der be — des Königs [E1] Georg [/E1] und ſeiner Umgebung in Hietzing die verwerflichen Verſuche fortgeſetzt , einen Theil ſeiner früheren Unterthanen , meiſt aus den unterſten Ständen , für das völlige boffnungsloſe und thörichte Unternehmen einer Wiederherſtellung ſeines Thrones zu gewinnen . zwiſchen Deutſchland und Frankreich herbeizuführen drohete , ließ König Georg ſchluſſe an die Franzoſen gegen ihr Vaterland marſchiren ſollte . Als ſodann die luxemburgiſche Angelegenheit eine friedliche Löſung fand , begab ſich die in Holland geſammelte Schaar von Hannoveranern nach der [E2] Schweiz [/E2] , wo ſie in feſter militairiſcher Eintheilung verblieb und aus Mitteln des Königs Georg fort und fort ihren Unterhalt erhielt ."

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
    Label: Schweiz
    Description: Staat in Mitteleuropa
    Country: ['Schweiz']
    Aliases: {'en': ['Swiss Confederation', 'Swiss', 'Confoederatio Helvetica'], 'fr': ['Confédération helvétique', 'Confédération suisse', 'SUI', 'Helvétie', 'la Confédération suisse'], 'de': ['Schweizerische Eidgenossenschaft', 'Eidgenossenschaft', 'SUI', 'Confoederatio Helvetica', 'Confœderatio Helvetica'], 'lb': ['SUI']}
    Coordinates: [{'lat': 46.798562, 'lon': 8.231973}]
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
  1. What is the relationship between 'Georg' and 'Schweiz' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Georg' near 'Schweiz' around 1868-02-19?
  4. Resolve temporal expressions relative to 1868-02-19. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 26:
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
Sample 27:
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
Sample 28:
  Publication date : 1928-10-25
  Language         : fr
  Person  : 'Démosthène'  (QID: Q117253)
  Location: 'canton de Vaud'  (QID: Q12771)

  [ARTICLE TEXT — entity markers added]
  "Les choses semblent devoir se passer beau coup plus calmement dans le [E2] canton de Vaud [/E2], où aucun changement notable n'est prévu, et à Genève, où l'on s'attend généralement à un déchet démocrate en faveur du parti de défense économique. C'est M. de Rabours que tous livrent d'avance au fatal couperet de la guillotine sèche. Si pareille prédiction devait se vérifier exacte, le Parlement perdrait une de ses figures les plus sympathiques et l'un de ses meilleurs orateurs, à un moment où les disciples de [E1] Démosthène [/E1], à Berne, se comptent presque sur les doigts 1..."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Démosthène
    Description: homme d'état et orateur athénien
    Born: ['-0384-01-01T00:00:00Z']
    Died: ['-0322-10-12T00:00:00Z']
    Birth place: ['Péanie']
    Death place: ['Q724394']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Verb cluster: "perdrait" — tense=Imp, aspect=None, mood=Ind
      Sentence: "Si pareille prédiction devait se vérifier exacte, le Parlement perdrait une de ses figures les plus sympathiques et l'un"
    Verb cluster: "semblent" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Les choses semblent devoir se passer beau coup plus calmement dans le canton de Vaud, où aucun changement notable n'est "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 17 (0 = most prominent)
    OCR quality estimate: 0.982

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Démosthène' and 'canton de Vaud' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Démosthène' near 'canton de Vaud' around 1928-10-25?
  4. Resolve temporal expressions relative to 1928-10-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 29:
  Publication date : 1921-10-05
  Language         : fr
  Person  : 'Staehli'  (QID: N/A)
  Location: 'Copenhague'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "MM.Schneider, conseiller d'Etat de Bâle, et [E1] Staehli [/E1], secrétaire ouvrier, de Berne, ont prononcé des discours. Suisse -Danemark [E2] Copenhague [/E2], 3 octobre."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "prononcé" — tense=Past, aspect=None, mood=None
      Sentence: "MM.Schneider, conseiller d'Etat de Bâle, et Staehli, secrétaire ouvrier, de Berne, ont prononcé des discours."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 24 (0 = most prominent)
    OCR quality estimate: 0.951

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Staehli' and 'Copenhague' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Staehli' near 'Copenhague' around 1921-10-05?
  4. Resolve temporal expressions relative to 1921-10-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 30:
  Publication date : 1928-06-05
  Language         : de
  Person  : 'Hegars'  (QID: Q670852)
  Location: 'St. Jakobskirche'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Konzort in der [E2] St. Jakobskirche [/E2]. C. Sch. Trieb der Chor auch um einen halben Ton in die Höhe, so blieb doch die erwünschte Phrasierung richt aus. Mit der Wahl von [E1] Hegars [/E1] Ballade „Rudolf von Werdenberg" zum Wettlied hat sich der „Liederkranz" eine wirkungssichere, aber klip penreiche Aufgabe gestellt, die er sinngemäß erfaßt und kontrastreich interpretiert hat."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "hat" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Mit der Wahl von Hegars Ballade „Rudolf von Werdenberg" zum Wettlied hat sich der „Liederkranz" eine wirkungssichere, ab"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 6 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Hegars' and 'St. Jakobskirche' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Hegars' near 'St. Jakobskirche' around 1928-06-05?
  4. Resolve temporal expressions relative to 1928-06-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 31:
  Publication date : 1908-01-07
  Language         : fr
  Person  : "général d'Amade"  (QID: Q2478026)
  Location: 'Mediouna'  (QID: Q2254188)

  [ARTICLE TEXT — entity markers added]
  ""' ..' Le [E1] général d'Amade [/E1] est arrivé lundi matin, à dix heures, à Casablanca, et il a pris immédiatement le commandement des troupes du corps d'occupation. Auto tir de Casablanca. On mande de Casablanca : Nos troupes sont rentrées à Casablanca, laissant à lakasbades [E2] Mediouna [/E2] un bataillon d'infanterie, un escadron d'artillerie, deux sections de mitrailleuses et un peloton de « avalerie."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Albert d'Amade
    Description: militaire français
    Born: ['+1856-12-24T00:00:00Z']
    Died: ['+1941-11-11T00:00:00Z']
    Birth place: ['Q7880']
    Death place: ['Q327290']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "arrivé" — tense=Past, aspect=None, mood=None
      Sentence: ""' ..' Le général d'Amade est arrivé lundi matin, à dix heures, à Casablanca, et il a pris immédiatement le commandement"
    Verb cluster: "rentrées" — tense=Past, aspect=None, mood=None
      Sentence: "Nos troupes sont rentrées à Casablanca, laissant à lakasbades Mediouna un bataillon d'infanterie, un escadron d'artiller"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 6 (0 = most prominent)
    OCR quality estimate: 0.990

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between "général d'Amade" and 'Mediouna' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing "général d'Amade" near 'Mediouna' around 1908-01-07?
  4. Resolve temporal expressions relative to 1908-01-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 32:
  Publication date : 1920-04-22
  Language         : en
  Person  : 'Ralph Wirt'  (QID: N/A)
  Location: 'France'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "I understand you did not get killed in [E2] France [/E2]. I am glad of that. I guess I had better wind up by saying, [E1] Ralph Wirt [/E1], you will please send me the Putnam County Herald three months, Gainesboro, Tenn., R. 3, as the Herald is a hustling paper and the men who run it are, too."

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
    Verb cluster: "guess" — tense=Pres, aspect=None, mood=None
      Sentence: "I guess I had better wind up by saying, Ralph Wirt, you will please send me the Putnam County Herald three months, Gaine"
    Verb cluster: "understand" — tense=Pres, aspect=None, mood=None
      Sentence: "I understand you did not get killed in France."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 18 (0 = most prominent)
    OCR quality estimate: 0.992

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Ralph Wirt' and 'France' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Ralph Wirt' near 'France' around 1920-04-22?
  4. Resolve temporal expressions relative to 1920-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 33:
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

────────────────────────────────────────────────────────────
Sample 34:
  Publication date : 1920-07-08
  Language         : en
  Person  : 'Mr. Farley'  (QID: N/A)
  Location: 'NashvUle'  (QID: Q23197)

  [ARTICLE TEXT — entity markers added]
  "It is too slow for D. A. Main street Cookeville looks like Broad street In [E2] NashvUle [/E2], tbere is so much business going on here, and if you want a good school for your children here is the place for them as they bave good schools, and plen ty of churches and Sunday schools, and the best teachers that can be found. They are up on the Job in any branch you wish to study. If you want a house pattern just come here and you con get -very thing ou want In the building line— cement, lime, brick or any stuff you may need In the way of building ma terial. The Cookeville Roller Mills furnish this place with theb est flour, as Mr. Pleas Farley has the best miller that can be found; [E1] Mr. Farley [/E1] Is mighty nice, clever man and hanlles all kinds of feed stuff."

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
    Verb cluster: "Is" — tense=Pres, aspect=None, mood=Ind
      Sentence: "The Cookeville Roller Mills furnish this place with theb est flour, as Mr. Pleas Farley has the best miller that can be "
    Verb cluster: "is" — tense=Pres, aspect=None, mood=Ind
      Sentence: "It is too slow for D. A. Main street Cookeville looks like Broad street In NashvUle, tbere is so much business going on "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 9 (0 = most prominent)
    OCR quality estimate: 0.993

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mr. Farley' and 'NashvUle' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mr. Farley' near 'NashvUle' around 1920-07-08?
  4. Resolve temporal expressions relative to 1920-07-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 35:
  Publication date : 1820-09-09
  Language         : en
  Person  : 'ROB. MOORE'  (QID: N/A)
  Location: 'Baltimore'  (QID: Q5092)

  [ARTICLE TEXT — entity markers added]
  "Each volume will consist of fifty-two numbers, a title page and an index ; and numerous Engravings to re present new implements, and approved sys tems of husbandry Each number gives a true and accurate statement of the th*m selling prices of coun try produce, live stock and all tbe principal articles brought for sale in the [E2] Baltimore [/E2] market. . Terms of subscription 4 dollars per an num, to be paid in advance. It is by the diffusion of knowle dge only, that we can expect our country to improve in Agricul ture, which thy paper is admirably calcula ted to impart, to all who will take pains to be improved by reading.” Respectfully th friend, ROB."

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
    Temporal signal words: now
    Verb cluster: "will consist" — tense=None, aspect=None, mood=None
      Sentence: "Each volume will consist of fifty-two numbers, a title page and an index ; and numerous Engravings to re present new imp"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 18 (0 = most prominent)
    OCR quality estimate: 0.989

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'ROB. MOORE' and 'Baltimore' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'ROB. MOORE' near 'Baltimore' around 1820-09-09?
  4. Resolve temporal expressions relative to 1820-09-09. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 36:
  Publication date : 1981-12-11
  Language         : fr
  Person  : 'Henri Barbier'  (QID: N/A)
  Location: 'Fulgur'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "on s'aventure grâce à M. Benjamin sur la froide planète [E2] Fulgur [/E2]. Bandes dessinées, télévision, cinéma ont depuis longtemps compris et commercialisé l'engouement de la jeunesse pour la science-fiction. Les costumes signés Mouky respectent admirablement la mode spatiale et les accessoires d'[E1] Henri Barbier [/E1] et Maria Estève intriguent suffisamment pour qu'à la fin du spectacle jeunes et moins jeunes s'élancent sur scène pour comprendre, toucher, explorer ces nouveaux gadgets."

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
  1. What is the relationship between 'Henri Barbier' and 'Fulgur' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Henri Barbier' near 'Fulgur' around 1981-12-11?
  4. Resolve temporal expressions relative to 1981-12-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 37:
  Publication date : 1790-05-29
  Language         : en
  Person  : 'H011. James Gordon'  (QID: N/A)
  Location: 'Long-Ifland'  (QID: Q18438)

  [ARTICLE TEXT — entity markers added]
  "Peter Sylvester is re-elefted a member of the Houfe of Reprefentatives of the United States—and the [E1] H011. James Gordon [/E1] is chofen to ferve in the fame hon. branch of the next Congrefs.— On Tuefdaylaft.died at Jericho on [E2] Long-Ifland [/E2], the hon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "is" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Peter Sylvester is re-elefted a member of the Houfe of Reprefentatives of the United States—and the H011."
    Verb cluster: "Tuefdaylaft.died" — tense=Past, aspect=Perf, mood=None
      Sentence: "On Tuefdaylaft.died at Jericho on Long-Ifland, the hon."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 1 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'H011. James Gordon' and 'Long-Ifland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'H011. James Gordon' near 'Long-Ifland' around 1790-05-29?
  4. Resolve temporal expressions relative to 1790-05-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 38:
  Publication date : 1868-02-17
  Language         : de
  Person  : "Abbe Migne's"  (QID: Q326431)
  Location: 'Paris'  (QID: Q90)

  [ARTICLE TEXT — entity markers added]
  "Mehrere Söhne der ersten Familien des Königreichs Siam sind in [E2] Paris [/E2] erwartet. Nach glaubwürdigen Londoner Privatberichten treten die erfreulichsten Vorzeichen eines kräftigern Geschäfts verkehrs zu Tage. Von ihm kursirte die Bitte an den Kaiser in Bordeaux: Sire, ich hoffe, daß Sie mich noch einmal zum Präfekten von London wählen. [E1] Abbe Migne's [/E1] Druckerei der Kirchenväter in Paris ist abgebrannt."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Paris
    Description: Hauptstadt und bevölkerungsreichste Stadt Frankreichs
    Country: ['Frankreich', 'Königreich Frankreich', 'Fränkisches Reich', 'Deutsche Besetzung Frankreichs 1940–1945', 'Frankreich', 'Erstes Kaiserreich', 'Erste Französische Republik']
    Located in: ['Q16665915', 'Île-de-France', 'Königreich Frankreich', 'Q2863958', 'Département Seine', 'Departement Paris']
    Aliases: {'en': ['City of Light', 'City of Love', 'Lutetia'], 'fr': ['Ville-Lumière', 'Paname', 'Lutèce', "Ville de l'Amour", 'FR-75', 'Pantruche', 'Ville de Paris']}
    Coordinates: [{'lat': 48.85666666666667, 'lon': 2.352222222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Verb cluster: "kursirte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Von ihm kursirte die Bitte an den Kaiser in Bordeaux: Sire, ich hoffe, daß Sie mich noch einmal zum Präfekten von London"
    Verb cluster: "sind" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Mehrere Söhne der ersten Familien des Königreichs Siam sind in Paris erwartet."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 30 (0 = most prominent)
    OCR quality estimate: 0.975

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between "Abbe Migne's" and 'Paris' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing "Abbe Migne's" near 'Paris' around 1868-02-17?
  4. Resolve temporal expressions relative to 1868-02-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 39:
  Publication date : 1948-10-09
  Language         : fr
  Person  : 'A. S.'  (QID: N/A)
  Location: 'Genève'  (QID: Q71)

  [ARTICLE TEXT — entity markers added]
  "LES SPORTS Cyclisme LE TOUR DE FRANCE 1949 ([E1] A. S. [/E1]) — Les organisateurs du Tour de France viennent de r— "dre leurs travaux en vue de l'épreuve de 1949. Football VAAST, DU RACING PARIS, SIGNE AU SERVETTE Le joueur du Racing Vaast, fixé à [E2] Genève [/E2], a envoyé sa lettre de démission au Racing et a signé au Servette."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Genève
    Description: ville de Suisse et chef-lieu du canton de Genève
    Country: ['Suisse', 'république de Genève', 'France', 'république de Genève']
    Located in: ['canton de Genève']
    Aliases: {'en': ['Genève', 'Geneva GE', 'Geneve', 'Genf'], 'fr': ['Geneve', 'GE', 'Cité de Calvin', 'Ville de Genève'], 'de': ['Genève', 'Stadt Genf', 'Ville de Genève']}
    Coordinates: [{'lat': 46.2, 'lon': 6.15}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1949" → 1949
      - "1949" → 1949
    Verb cluster: "envoyé" — tense=Past, aspect=None, mood=None
      Sentence: "Le joueur du Racing Vaast, fixé à Genève, a envoyé sa lettre de démission au Racing et a signé au Servette."
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.954

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'A. S.' and 'Genève' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'A. S.' near 'Genève' around 1948-10-09?
  4. Resolve temporal expressions relative to 1948-10-09. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 40:
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

────────────────────────────────────────────────────────────
Sample 41:
  Publication date : 1938-11-13
  Language         : de
  Person  : 'Siurgenenger'  (QID: N/A)
  Location: 'Oberrheins'  (QID: Q663546)

  [ARTICLE TEXT — entity markers added]
  "Bevor der bei Fußach mündende Rheinkanal angelegt und damit ein direkter Abfluß des Stroms in das große See becken geschaffen wurde, ergossen sich die Wasser des [E2] Oberrheins [/E2] durch diesen Arm in den Bodensee, und oft war sein Bett viel zu eng, um sie zu fassen. Ob gleich er seit dem Fußacher Durchstich nur noch die überschüssigen Stauwasser des Kanals und die Wasser der anschließenden Bäche dem Bodensee zuführen darf. Leider ist es freilich auch schon das Letzte! Ie: Dand [E1] Siurgenenger [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Oberrhein
    Description: Abschnitt des Rheins zwischen Basel und Bingen
    Country: ['Frankreich', 'Schweiz', 'Deutschland']
    Located in: ['Kanton Basel-Stadt', 'Baden-Württemberg', 'Grand Est', 'Rheinland-Pfalz', 'Hessen']
    Coordinates: [{'lat': 48.95, 'lon': 8.2666666666667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "ergossen" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Bevor der bei Fußach mündende Rheinkanal angelegt und damit ein direkter Abfluß des Stroms in das große See becken gesch"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 26 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Siurgenenger' and 'Oberrheins' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Siurgenenger' near 'Oberrheins' around 1938-11-13?
  4. Resolve temporal expressions relative to 1938-11-13. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 42:
  Publication date : 1800-10-16
  Language         : en
  Person  : 'D.C * I.DWELL,\nClerl of lie DiJtriEl of Peonsyl v aoisA'  (QID: N/A)
  Location: 'District of Pennsylvania'  (QID: Q7163624)

  [ARTICLE TEXT — entity markers added]
  "[E2] District of Pennsylvania [/E2] to wit : B E it remembered that on tshe Tenth day of July in the twenty fif-.h year of the Indepen dence of the United States of America, Alexan der Addison of the said District hath deposited in this office the title of a book the right where of he claims as Author in tha words following to wit, “ Reports of cafes in the County courts of the Fifth Circuit and in the High Court of Errors and appeals of the State of Pennsylvania, and charges to Grand Juries of those County Courts. By Alexander Addison, President of the Courts of Common Pleas of me Fifth Cir cuit of the State of Pennlylvann.” In conformity to the act of Congress of the Uni ted States istitlrd “ An act for the encouragement of learning by securimr the copies of maps charts and books to the Authors and Proprietors of such copies during the times therein mentioned." D.C * I.DWELL, Clerl of lie DiJtriEl of Peonsyl v aoisA The above book is now pohlsshcd."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Pennsylvania's congressional districts
    Description: congressional districting since 2003
    Country: ['United States']
    Located in: ['Pennsylvania']
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now
    Verb cluster: "remembered" — tense=Past, aspect=None, mood=None
      Sentence: "District of Pennsylvania to wit : B E it remembered that on tshe"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 1 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'D.C * I.DWELL,\nClerl of lie DiJtriEl of Peonsyl v aoisA' and 'District of Pennsylvania' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'D.C * I.DWELL,\nClerl of lie DiJtriEl of Peonsyl v aoisA' near 'District of Pennsylvania' around 1800-10-16?
  4. Resolve temporal expressions relative to 1800-10-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 43:
  Publication date : 1908-01-07
  Language         : fr
  Person  : "général d'Amade"  (QID: Q2478026)
  Location: 'Casablanca'  (QID: Q7903)

  [ARTICLE TEXT — entity markers added]
  ""' ..' Le [E1] général d'Amade [/E1] est arrivé lundi matin, à dix heures, à [E2] Casablanca [/E2], et il a pris immédiatement le commandement des troupes du corps d'occupation."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Albert d'Amade
    Description: militaire français
    Born: ['+1856-12-24T00:00:00Z']
    Died: ['+1941-11-11T00:00:00Z']
    Birth place: ['Toulouse']
    Death place: ['Fronsac']
  Location Wikidata:
    Label: Casablanca
    Description: ville du Maroc
    Country: ['Maroc', 'protectorat français au Maroc']
    Located in: ['Casablanca']
    Aliases: {'en': ['Anfa', 'Dar el-Beida', 'ad-Dār al-Bayḍāʾ', 'White House', 'Bedawa', 'الدار البيضاء'], 'fr': ['Anfa', 'Ad-dar Al Bayda', 'ad-Dār al-Bayḍāʾ', 'Maison Blanche', 'Commune de Casablanca', 'Ville de Casablanca'], 'de': ['Al-Dār al-bayḍāʾ', 'Anfa', 'Ed Dar el Beida', 'Ad-Dar-el-Beida']}
    Coordinates: [{'lat': 33.599166666667, 'lon': -7.62}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "arrivé" — tense=Past, aspect=None, mood=None
      Sentence: ""' ..' Le général d'Amade est arrivé lundi matin, à dix heures, à Casablanca, et il a pris immédiatement le commandement"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 6 (0 = most prominent)
    OCR quality estimate: 0.990

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between "général d'Amade" and 'Casablanca' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing "général d'Amade" near 'Casablanca' around 1908-01-07?
  4. Resolve temporal expressions relative to 1908-01-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 44:
  Publication date : 1888-03-08
  Language         : de
  Person  : 'Blankenburg'  (QID: Q111102)
  Location: 'Deutschland'  (QID: Q1206012)

  [ARTICLE TEXT — entity markers added]
  "[E2] Deutschland [/E2]. Einer der Führer der preußi schen Hochkonservativen, Moritz von Blanken burg, ist gestorben. Er bekämpfte die Gleichberechtigung der Juden, ohne ein Judenfeind zu sein — einfach weil er den Grundsatz des christlichen Staats nicht wollte durchbrechen lassen. Im Abgeordnetenhaus sagte [E1] Blankenburg [/E1] einmal: „Ich bin kein Juden hasser, sondern eher ein Freund der Juden;"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Moritz von Blanckenburg
    Description: deutscher Politiker, MdR
    Born: ['+1815-05-25T00:00:00Z']
    Died: ['+1888-03-03T00:00:00Z']
    Birth place: ['Mechowo (Płoty)']
    Death place: ['Mechowo (Płoty)']
    Work locations: ['Berlin']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "sagte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Im Abgeordnetenhaus sagte Blankenburg einmal: „Ich bin kein Juden hasser, sondern eher ein Freund der Juden;"
    Verb cluster: "ist" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Einer der Führer der preußi schen Hochkonservativen, Moritz von Blanken burg, ist gestorben."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 10 (0 = most prominent)
    OCR quality estimate: 0.990

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Blankenburg' and 'Deutschland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Blankenburg' near 'Deutschland' around 1888-03-08?
  4. Resolve temporal expressions relative to 1888-03-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 45:
  Publication date : 1820-03-06
  Language         : en
  Person  : 'William\nMurphy'  (QID: N/A)
  Location: 'Margaritta'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "William Murphy, Thomas O’Brien, Charles Weaver, Isaac \llister, J. Jackson, and Isaac Denuie, convicted of Piracy, committed on board of La Irresistable privateer, which they ran a- way with from [E2] Margaritta [/E2], were brought be fore bis honor Judge Bland, wh, after a ‘short but impressive address,."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after
    Verb cluster: "were brought" — tense=Past, aspect=Perf, mood=Ind
      Sentence: "William Murphy, Thomas O’Brien, Charles Weaver, Isaac \llister, J. Jackson, and Isaac Denuie, convicted of Piracy, commi"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.993

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'William\nMurphy' and 'Margaritta' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'William\nMurphy' near 'Margaritta' around 1820-03-06?
  4. Resolve temporal expressions relative to 1820-03-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 46:
  Publication date : 1874-08-25
  Language         : de
  Person  : 'Schüler'  (QID: N/A)
  Location: 'Schleſten'  (QID: Q81720)

  [ARTICLE TEXT — entity markers added]
  "Gerr [E1] Schüler [/E1] fur die — — ꝓ — — — ⏑ n ⏑ — ⏑ : : — 1 — enteten . Firma F . Dieier Zeitvunkt dürfte min nicht mehr ferne ſein , da die Geſchaͤfte der Geſellſchaft in letzter Zeit einen ſehr erfreulichen Auiſchwung genommen baben . So wnd und gemeldet , datz die Kefſelſchmiede der Gefenſ Gaft in [E2] Schleſten [/E2] dieler Tage Auftraͤge im Betrage von 250 00 Eutr ."

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
    Verb cluster: "enteten" — tense=Past, aspect=None, mood=Sub
      Sentence: "Gerr Schüler fur die — — ꝓ — — — ⏑ n ⏑ — ⏑ : : — 1 — enteten ."
    Verb cluster: "gemeldet" — tense=None, aspect=None, mood=None
      Sentence: "So wnd und gemeldet , datz die Kefſelſchmiede der Gefenſ Gaft in Schleſten dieler Tage Auftraͤge im Betrage von 250 00 E"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.973

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Schüler' and 'Schleſten' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Schüler' near 'Schleſten' around 1874-08-25?
  4. Resolve temporal expressions relative to 1874-08-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 47:
  Publication date : 1808-09-01
  Language         : fr
  Person  : 'Marianne Perrenoud'  (QID: N/A)
  Location: 'la _Sagoe'  (QID: Q68532)

  [ARTICLE TEXT — entity markers added]
  "[E1] Marianne Perrenoud [/E1], de la Sagne, fille de feu Jacob Perrenoud, et de Judith née Jaquet, morte le 27 Juillet Et les dits parens pouvant n'être pas tous connus, on les avise par la présente, que le Vendredi 9 Septembre courant, est le jour fatal sur lequel la mise en possession et investiture des biens de la " défunte, doivent être réclamées devant \ i noble Cour de Justice, assemblée dans l'hôtel-dê ville, par ceux des dits païens qui sont au pays, et qui estimeront avoir des droits à faire valoir. La présente information ainsi donnée sans conséquence, vu la clause extraordinaire ci-dessus, _exiraite du testament de la défunte, qui est déposé en original au _' grefle de Neuchatel, sera inséré trois fois dans la présente, et publié au prône de l'é glise de [E2] la _Sagoe [/E2], juridiction de la défunte."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "inséré" — tense=Past, aspect=None, mood=None
      Sentence: "La présente information ainsi donnée sans conséquence, vu la clause extraordinaire ci-dessus, _exiraite du testament de "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 32 (0 = most prominent)
    OCR quality estimate: 0.952

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Marianne Perrenoud' and 'la _Sagoe' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Marianne Perrenoud' near 'la _Sagoe' around 1808-09-01?
  4. Resolve temporal expressions relative to 1808-09-01. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 48:
  Publication date : 1878-02-06
  Language         : de
  Person  : 'General\nZimmermann'  (QID: N/A)
  Location: 'Ruschtschuk'  (QID: Q160173)

  [ARTICLE TEXT — entity markers added]
  "Man weiß zwar, daß die Türken die Donaufestungen räumen müssen, und es heißt, daß die Russen Widdin, [E2] Ruschtschuk [/E2] und Silistria besetzen werden, und daß General Zimmermann bereits vor den Mauern von Varna stehe, wahrscheinlich um auch von dieser Festung Besitz zu nehmen."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Russe
    Description: Stadt an der Donau in Bulgarien
    Country: ['Bulgarien', 'Volksrepublik Bulgarien', 'Zarentum Bulgarien', 'Fürstentum Bulgarien', 'Q12560']
    Located in: ['Q2652929']
    Aliases: {'en': ['Rousse', 'Rusçuk', 'Rustchuk'], 'fr': ['Roustchouk', 'Rusciuc', 'Rouchtchouk'], 'de': ['Sexaginta Prista', 'Rustschuk', 'Liuben Dimitrov', 'Gemeinde Russe', 'Rousse'], 'lb': ['Rousse']}
    Coordinates: [{'lat': 43.844532, 'lon': 25.953907}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "weiß" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Man weiß zwar, daß die Türken die Donaufestungen räumen müssen, und es heißt, daß die Russen Widdin, Ruschtschuk und Sil"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 8 (0 = most prominent)
    OCR quality estimate: 0.999

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'General\nZimmermann' and 'Ruschtschuk' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'General\nZimmermann' near 'Ruschtschuk' around 1878-02-06?
  4. Resolve temporal expressions relative to 1878-02-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 49:
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
Sample 50:
  Publication date : 1981-07-25
  Language         : fr
  Person  : 'Van der Valk'  (QID: N/A)
  Location: 'SUISSE ITALIENNE'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Panorama sportif-22.40 [E1] Van der Valk [/E1], série-23.30 Sammy Price en concert-0.15 Téléjournal. [E2] SUISSE ITALIENNE [/E2] 18.10"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 37 (0 = most prominent)
    OCR quality estimate: 0.663

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Van der Valk' and 'SUISSE ITALIENNE' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Van der Valk' near 'SUISSE ITALIENNE' around 1981-07-25?
  4. Resolve temporal expressions relative to 1981-07-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 51:
  Publication date : 1874-08-25
  Language         : de
  Person  : 'Ruß'  (QID: N/A)
  Location: 'Schleſten'  (QID: Q81720)

  [ARTICLE TEXT — entity markers added]
  "So wnd und gemeldet , datz die Kefſelſchmiede der Gefenſ Gaft in [E2] Schleſten [/E2] dieler Tage Auftraͤge im Betrage von 250 00 Eutr . erbalten bat ; ben Summe war biber zu Abſchrelbungen verwendet worden . Bei der Neuwabl des Aufsichtsraths wurde Herr Banquier [E1] Ruß [/E1] Flema A ."

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
    Verb cluster: "wurde" — tense=Past, aspect=None, mood=Ind
      Sentence: "Bei der Neuwabl des Aufsichtsraths wurde Herr Banquier Ruß Flema A ."
    Verb cluster: "gemeldet" — tense=None, aspect=None, mood=None
      Sentence: "So wnd und gemeldet , datz die Kefſelſchmiede der Gefenſ Gaft in Schleſten dieler Tage Auftraͤge im Betrage von 250 00 E"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 51 (0 = most prominent)
    OCR quality estimate: 0.973

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Ruß' and 'Schleſten' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Ruß' near 'Schleſten' around 1874-08-25?
  4. Resolve temporal expressions relative to 1874-08-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 52:
  Publication date : 1818-01-06
  Language         : de
  Person  : 'Wilkins'  (QID: Q676998)
  Location: 'Sy\nbillen-Tempel'  (QID: Q784000)

  [ARTICLE TEXT — entity markers added]
  "Die Plane, welche die Baukünstler, Smirke für die Seemacht, und [E1] Wilkins [/E1] für die Landmacht, eingereicht haben, sind genehmigt. Das Waterloo-Monument wird 200,000. Pf. Sterl. kosten, und am Ende des Portlands-Platzes, nahe bey dem Park des Prinzen Regenten, errichtet werden. Es wird in ei nem antiken Thurm von drey Säulenordnungen besteh. um dessen Basis sich eine runde Kolonnade zieht, ähnlich einem der bewundertsten Reste des Alterthums, dem Sy billen-Tempel zu Tivoli."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: William Wilkins
    Description: English architect, classical scholar and archaeologist (1778–1839)
    Born: ['+1778-08-31T00:00:00Z']
    Died: ['+1839-08-31T00:00:00Z']
    Birth place: ['Norwich']
    Death place: ['Cambridge']
    Residences: ['England']
  Location Wikidata:
    Label: Tempel der Sibylle
    Description: römischer Tempel in Tivoli
    Country: ['Italien']
    Located in: ['Tivoli']
    Aliases: {'en': ['Temple of Sibyl']}
    Coordinates: [{'lat': 41.9669, 'lon': 12.8009}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "sind" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Die Plane, welche die Baukünstler, Smirke für die Seemacht, und Wilkins für die Landmacht, eingereicht haben, sind geneh"
    Verb cluster: "zieht" — tense=Pres, aspect=None, mood=Ind
      Sentence: "um dessen Basis sich eine runde Kolonnade zieht, ähnlich einem der bewundertsten Reste des Alterthums, dem Sy billen-Tem"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 1 (0 = most prominent)
    OCR quality estimate: 0.970

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Wilkins' and 'Sy\nbillen-Tempel' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Wilkins' near 'Sy\nbillen-Tempel' around 1818-01-06?
  4. Resolve temporal expressions relative to 1818-01-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 53:
  Publication date : 1898-05-02
  Language         : de
  Person  : 'Hr.\nKoller'  (QID: Q123734)
  Location: 'Fröhlichstraße 1'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Andolf Koler-Inbiläums-Ansstellung in Zürich. A. F. Für die Besichtigung der Ateliers am Zürichhorn erhält der Ausstellungsbesucher an der Kasse im Künstlerhaus bezw. in der Börse unentgeltlich eine besondere Einlaßkarte, die zum Besuche der Kollerschen Ateliers berechtigt."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "berechtigt" — tense=None, aspect=None, mood=None
      Sentence: "in der Börse unentgeltlich eine besondere Einlaßkarte, die zum Besuche der Kollerschen Ateliers berechtigt."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 34 (0 = most prominent)
    OCR quality estimate: 0.998

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Hr.\nKoller' and 'Fröhlichstraße 1' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Hr.\nKoller' near 'Fröhlichstraße 1' around 1898-05-02?
  4. Resolve temporal expressions relative to 1898-05-02. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 54:
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
Sample 55:
  Publication date : 2018-01-03
  Language         : fr
  Person  : 'Diable'  (QID: N/A)
  Location: 'Bahreïn'  (QID: Q398)

  [ARTICLE TEXT — entity markers added]
  "Sur un bateau au large de [E2] Bahreïn [/E2] : « Les porteurs chargés comme des mu-lets prennent la passerelle étroite d’assaut, un vrai film de pirates à l’abordage, et en même temps d’autres porteurs redescendent par la même échelle prendre livraison d’un nouveau chargement, ce qui provoque des embouteillages des familles (...). Invités par une famille en Inde : « En attendant le dîner, un des sikhs nous apporte un gramophone à manivelle et des disques hindous, et insiste au moins une heure pour que « le [E1] Diable [/E1] » et «"

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
    Verb cluster: "apporte" — tense=Pres, aspect=None, mood=Ind
      Sentence: "En attendant le dîner, un des sikhs nous apporte un gramophone à manivelle et des disques hindous, et insiste au moins u"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 8 (0 = most prominent)
    OCR quality estimate: 1.000

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Diable' and 'Bahreïn' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Diable' near 'Bahreïn' around 2018-01-03?
  4. Resolve temporal expressions relative to 2018-01-03. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 56:
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
Sample 57:
  Publication date : 1878-10-02
  Language         : de
  Person  : 'Fröbel'  (QID: Q76679)
  Location: 'Spanien'  (QID: Q29)

  [ARTICLE TEXT — entity markers added]
  "— Mailand stellt Arbeiten der [E1] Fröbel [/E1]schulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die Kinder weit überschreiten: soll das Kinderarbeit sein; soll das zarteste Jugendalter mit solch difficilen und feinen Aufgaben beglückt werden? Wahrlich, Fröbel, Deine An hänger sind größer als Du, so groß, daß selbst Du ihnen nicht mehr folgen könntest und ihnen mit Macht zurufen würdest: Bleibt bei der Natur, lernet erst die Jugend kennen! [E2] Spanien [/E2] macht keinen Versuch, eine Ausstellung zu arrangiren, dagegen hat Portugal Schülerarbeiten und das Modell einer Volksschule nach Paris gesandt."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Spanien
    Description: Staat in Südeuropa, mit Territorium in Afrika
    Country: ['Spanien']
    Aliases: {'en': ['Kingdom of Spain'], 'fr': ["Royaume d'Espagne", 'Esp.'], 'de': ['Königreich Spanien'], 'lb': ['Kinnekräich Spuenien']}
    Coordinates: [{'lat': 40.2, 'lon': -3.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nicht mehr, nach
    Verb cluster: "stellt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "— Mailand stellt Arbeiten der Fröbelschulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die "
    Verb cluster: "macht" — tense=Pres, aspect=None, mood=Ind [NEGATED]
      Sentence: "Spanien macht keinen Versuch, eine Ausstellung zu arrangiren, dagegen hat Portugal Schülerarbeiten und das Modell einer "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 27 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Fröbel' and 'Spanien' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Fröbel' near 'Spanien' around 1878-10-02?
  4. Resolve temporal expressions relative to 1878-10-02. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 58:
  Publication date : 1981-05-13
  Language         : fr
  Person  : 'Philip Habib'  (QID: N/A)
  Location: 'Syrie'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Pourquoi [E2] Syrie [/E2]ns et Israéliens menacent-ils soudain de s'affronter dans une guerre risquant d'embraser tout le Proche-Orient ? Le raisonnement est particulièrement vrai pour Israël qui a vu, il y a quelques semaines, les Etats-Unis disposés à vendre des radars volants à l'Arabie Saoudite, dans un souci prioritaire de renforcer un front antisoviétique dans la région, et en négligeant de considérer les craintes que cette transaction ne pouvait manquer d'éveiller à Jérusalem. La Syrie, quant à elle, a fait savoir à [E1] Philip Habib [/E1], le médiateur dépêché par Ronald Reagan, que les Etats-Unis étaient seuls à pouvoir influencer efficacement la politique israélienne."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "a" — tense=Pres, aspect=None, mood=Ind
      Sentence: "La Syrie, quant à elle, a fait savoir à Philip Habib, le médiateur dépêché par Ronald Reagan, que les Etats-Unis étaient"
    Verb cluster: "menacent" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Pourquoi Syriens et Israéliens menacent-ils soudain de s'affronter dans une guerre risquant d'embraser tout le Proche-Or"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 22 (0 = most prominent)
    OCR quality estimate: 0.988

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Philip Habib' and 'Syrie' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Philip Habib' near 'Syrie' around 1981-05-13?
  4. Resolve temporal expressions relative to 1981-05-13. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 59:
  Publication date : 2018-01-03
  Language         : fr
  Person  : 'Diable'  (QID: N/A)
  Location: 'Inde'  (QID: Q668)

  [ARTICLE TEXT — entity markers added]
  "Invités par une famille en [E2] Inde [/E2] : « En attendant le dîner, un des sikhs nous apporte un gramophone à manivelle et des disques hindous, et insiste au moins une heure pour que « le [E1] Diable [/E1] » et «"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Inde
    Description: pays d'Asie du Sud
    Country: ['Inde']
    Aliases: {'en': ['Republic of India', 'Bharat', 'Bharatvarsh', 'Hindustan', 'Bharata', 'Hindoostan', 'Indostan', 'Bharat Ganarajya', 'Al Hind', 'Tianzhu', 'Tenjiku'], 'fr': ["République d'Inde", 'Bharat', "République de l'Inde", 'Hindustan', 'Bharatvarsh', 'Indostan'], 'de': ['in']}
    Coordinates: [{'lat': 22.8, 'lon': 83}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "apporte" — tense=Pres, aspect=None, mood=Ind
      Sentence: "En attendant le dîner, un des sikhs nous apporte un gramophone à manivelle et des disques hindous, et insiste au moins u"
    Verb cluster: "Invités" — tense=Past, aspect=None, mood=None
      Sentence: "Invités par une famille en Inde : «"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 8 (0 = most prominent)
    OCR quality estimate: 1.000

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Diable' and 'Inde' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Diable' near 'Inde' around 2018-01-03?
  4. Resolve temporal expressions relative to 2018-01-03. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 60:
  Publication date : 1820-02-01
  Language         : en
  Person  : 'Loid Coke'  (QID: N/A)
  Location: 'Falls bridge'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "The stay law was to-day on the carpet, and (as my [E1] Loid Coke [/E1] says) will most probably “ be bandied to and fro” for several days to come. Its fate is less certain than formerly ; but I still think it will be rejected. question has excited more interest in either house, than that relating to the remo val ol Piince YV illiam Court House. In the House of Delegates it was decided, after a very warm contest, by an almost unanimous vote in favor of removal ; and in the Senate, the same result was obtained in a vote of 16 to 5, alter a discussion occupying the great er part of two days. A bill has passed, authorising the Board of Public Works to subscribe (l think,) 25,00U dollars to the road leading from the [E2] Falls bridge [/E2] to the Leesburg road."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: formerly, after
    Verb cluster: "was" — tense=Past, aspect=None, mood=Ind
      Sentence: "The stay law was to-day on the carpet, and (as my Loid Coke says) will most probably “ be bandied to and fro” for severa"
    Verb cluster: "has passed" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "A bill has passed, authorising the Board of Public Works to subscribe (l think,) 25,00U dollars to the road leading from"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 5 (0 = most prominent)
    OCR quality estimate: 0.976

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Loid Coke' and 'Falls bridge' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Loid Coke' near 'Falls bridge' around 1820-02-01?
  4. Resolve temporal expressions relative to 1820-02-01. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 61:
  Publication date : 1930-01-15
  Language         : fr
  Person  : 'Clérouc'  (QID: N/A)
  Location: 'PALACE'  (QID: Q3225157)

  [ARTICLE TEXT — entity markers added]
  "NOCTAMBULES, Hyspa, [E1] Clérouc [/E1]. Faut. 15 fr.[E2] PALACE [/E2], 9 h., Good News (Bonnes nouvelles).CIRQUE D'HIVER, 8.30, Fratellini;"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Le Palace
    Description: salle de spectacle dans le 9e arrondissement de Paris, qui fut tour à tour cinéma, cabaret, théâtre et boîte de nuit
    Country: ['France']
    Located in: ['9e arrondissement de Paris']
    Aliases: {'fr': ['Le Palace ( de Paris )', 'Le Palace (de Paris)', 'Alcazar de Paris']}
    Coordinates: [{'lat': 48.871944444444, 'lon': 2.3433333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "HIVER" — tense=None, aspect=None, mood=None
      Sentence: "15 fr.PALACE, 9 h., Good News (Bonnes nouvelles).CIRQUE D'HIVER, 8.30, Fratellini;"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 140 (0 = most prominent)
    OCR quality estimate: 0.824

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Clérouc' and 'PALACE' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Clérouc' near 'PALACE' around 1930-01-15?
  4. Resolve temporal expressions relative to 1930-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 62:
  Publication date : 1800-10-16
  Language         : en
  Person  : 'Alexander Addison, President of\nthe Courts of Common Pleas of me Fifth Cir\ncuit of the State of Pennlylvann'  (QID: Q25184130)
  Location: 'United States of America'  (QID: Q30)

  [ARTICLE TEXT — entity markers added]
  "Tenth day of July in the twenty fif-.h year of the Indepen dence of the [E2] United States of America [/E2], Alexan der Addison of the said District hath deposited in this office the title of a book the right where of he claims as Author in tha words following to wit, “ Reports of cafes in the County courts of the Fifth Circuit and in the High Court of Errors and appeals of the State of Pennsylvania, and charges to Grand Juries of those County Courts. By Alexander Addison, President of the Courts of Common Pleas of me Fifth Cir cuit of the State of Pennlylvann.”"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Alexander Addison
    Description: American lawyer
    Born: ['+1758-00-00T00:00:00Z']
    Died: ['+1807-00-00T00:00:00Z']
    Birth place: ['Scotland']
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
  1. What is the relationship between 'Alexander Addison, President of\nthe Courts of Common Pleas of me Fifth Cir\ncuit of the State of Pennlylvann' and 'United States of America' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Alexander Addison, President of\nthe Courts of Common Pleas of me Fifth Cir\ncuit of the State of Pennlylvann' near 'United States of America' around 1800-10-16?
  4. Resolve temporal expressions relative to 1800-10-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 63:
  Publication date : 1930-03-21
  Language         : en
  Person  : 'U. B. Williams'  (QID: N/A)
  Location: 'Dare\ncounty'  (QID: Q295787)

  [ARTICLE TEXT — entity markers added]
  "The students are being taught in the neighboring homes of E. P. White, G. D. Miller and [E1] U. B. Williams [/E1].— D. V. M. Buxton Loses Its School Building Buxton, at Cane Hattcras, Dare county, finds itself in a bad situ-"

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
  1. What is the relationship between 'U. B. Williams' and 'Dare\ncounty' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'U. B. Williams' near 'Dare\ncounty' around 1930-03-21?
  4. Resolve temporal expressions relative to 1930-03-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 64:
  Publication date : 1981-12-11
  Language         : fr
  Person  : 'André Fiaux'  (QID: N/A)
  Location: 'Lyon'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "La tête dans les étoiles », une pièce conçue et créée en 1977 par Maurice Yendt directeur du Théâtre des Jeunes Années de [E2] Lyon [/E2]. Du mystère, des aventures palpitantes, du rêve, une part de poésie, beaucoup d'imagination et une cascade d'actions sensationnelles ; Et surtout « La tête dans les étoiles » se prête à la plus mobile des mises en scène. Passerelles métalliques, plateforme d'envol, salle secrète du Tout-Puissant, monde souterrain interdit, prison, appareil sophistiqué détecteur de la Vérité, pistolets à rayons alphabétiques XAZE, etc ..Le Théâtre du Levant, dirigé par [E1] André Fiaux [/E1], a réalisé pour ce spectacle futuriste un décor mystérieux, merveilleux, aussi fascinant et compliqué qu'un alambic d'alchimiste."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1977" → 1977
    Temporal signal words: plus
    Verb cluster: "interdit" — tense=Past, aspect=None, mood=Ind
      Sentence: "Passerelles métalliques, plateforme d'envol, salle secrète du Tout-Puissant, monde souterrain interdit, prison, appareil"
    Verb cluster: "créée" — tense=Past, aspect=None, mood=None
      Sentence: "La tête dans les étoiles », une pièce conçue et créée en 1977 par Maurice Yendt directeur du Théâtre des Jeunes Années d"
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 4 days
    Entity sentence position in article: 11 (0 = most prominent)
    OCR quality estimate: 0.985

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'André Fiaux' and 'Lyon' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'André Fiaux' near 'Lyon' around 1981-12-11?
  4. Resolve temporal expressions relative to 1981-12-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 65:
  Publication date : 1928-05-06
  Language         : fr
  Person  : 'chef de la garnison de cette ville'  (QID: N/A)
  Location: 'Bulgarie'  (QID: Q219)

  [ARTICLE TEXT — entity markers added]
  "Pour les enfants sinistrés de [E2] Bulgarie [/E2] et de Grèce Mgr. Stéphane, archevêque de Sofia, rient d'adresser à l'Union internationale de secours aux enfants une dépêche, où, après avoir rendu hommage à cette institution, il s'exprime comme suit : La solidarité humaine ae manifeste le plue sensiblement dane les heures critiques. Le peuple bulgare est sincèrement reconnaissant envers tous ceux qui, dans son épreuve actuelle, lui ont témoigné sympathie et aide. Dieu bénisse chaque effort qui soulagera la souffrance, surtout celle des malheureux petits. D'autre part, l'U. I. S. E. reçoit de sa déléguée la nouvelle qu'elle a pu assurer une distribution quotidienne de pain à 3400 enfants dans les environs de Philippopoli et, dans la ville même, de pain et de thé à 2500 enfants. En outre, elle a fourni des couvertures à l'hôpital de dix baraques ouvert près de Philippopoli par le [E1] chef de la garnison de cette ville [/E1], le général Koutzeroff."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Bulgarie
    Description: pays d’Europe du Sud-Est situé dans les Balkans
    Country: ['Bulgarie']
    Aliases: {'en': ['Republic of Bulgaria'], 'fr': ['Bulg.', 'République de Bulgarie']}
    Coordinates: [{'lat': 42.75, 'lon': 25.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "3400" → 3400
      - "2500" → 2500
    Temporal signal words: après
    Verb cluster: "fourni" — tense=Past, aspect=None, mood=None
      Sentence: "En outre, elle a fourni des couvertures à l'hôpital de dix baraques ouvert près de Philippopoli par le chef de la garnis"
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 572 days
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.984

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'chef de la garnison de cette ville' and 'Bulgarie' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'chef de la garnison de cette ville' near 'Bulgarie' around 1928-05-06?
  4. Resolve temporal expressions relative to 1928-05-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 66:
  Publication date : 2018-01-03
  Language         : fr
  Person  : 'Simon'  (QID: N/A)
  Location: 'Europe'  (QID: Q46)

  [ARTICLE TEXT — entity markers added]
  "[E1] Simon [/E1] » fassent une démonstration de danse de chez nous. Impossible de leur faire comprendre qu’en [E2] Europe [/E2] on danse avec une femme."

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
    Verb cluster: "faire" — tense=None, aspect=None, mood=None
      Sentence: "Impossible de leur faire comprendre qu’en Europe on danse avec une femme."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 9 (0 = most prominent)
    OCR quality estimate: 1.000

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Simon' and 'Europe' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Simon' near 'Europe' around 2018-01-03?
  4. Resolve temporal expressions relative to 2018-01-03. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 67:
  Publication date : 1948-12-30
  Language         : de
  Person  : 'Amed Maher Pascha näher, dem Prisi\ndenten der Abgeordnetenkammer'  (QID: Q1572537)
  Location: 'Eniro'  (QID: Q85)

  [ARTICLE TEXT — entity markers added]
  "Der am Montag in Kairo ermordete ögxp tische Ministerprüsident Mahmud Fahmi Al-Nostra schi Pascha gehörte, obsohl ex bereits 60 Jnhire alt war, zu den verhültnismülig jungen Politikern, die erst in den swei leteten Juhrzelnken in die politische Arena hinabgestiegen sind. Fxüherer Anbünger des Waldl, wie überhaupt alle ügpptisehen Politikker, trat er zum ersten Mal als Verkehrsminister im zweiten Kahinett Nahns Pascha in den Vorder grund, das nur vom Jannar bis Juni 1930 im Amte blieb. Die Einweilung des Mausoleims hätte demnichst stattkinden sollen. Die Leiche von Almed Anher Paselm wurde in der Aneht dorthin gebrucht, dumit die beiden Freunde und Kampkkamernden Seite an Seite ruhen können."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Kairo
    Description: Hauptstadt von Ägypten
    Country: ['Ägypten', 'Ayyubiden', 'Sultanat der Mameluken', 'Q12560', 'Q127861', 'Sultanat Ägypten', 'Q160307']
    Located in: ['Q30805', 'Khedivat Ägypten', 'Q370173', 'Q491507']
    Aliases: {'en': ['al-Qāhira', 'Qahira', 'Cairo, Egypt', 'ghahere'], 'fr': ['Caire', 'Cairo', 'al-Qāhira'], 'de': ['al-Qāhira']}
    Coordinates: [{'lat': 30.044444444444444, 'lon': 31.235833333333332}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1930" → 1930
    Temporal signal words: vor
    Verb cluster: "wurde" — tense=Past, aspect=None, mood=Ind
      Sentence: "Die Leiche von Almed Anher Paselm wurde in der Aneht dorthin gebrucht, dumit die beiden Freunde und Kampkkamernden Seite"
    Verb cluster: "gehörte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Der am Montag in Kairo ermordete ögxp tische Ministerprüsident Mahmud Fahmi Al-Nostra schi Pascha gehörte, obsohl ex ber"
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 18 days
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.983

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Amed Maher Pascha näher, dem Prisi\ndenten der Abgeordnetenkammer' and 'Eniro' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Amed Maher Pascha näher, dem Prisi\ndenten der Abgeordnetenkammer' near 'Eniro' around 1948-12-30?
  4. Resolve temporal expressions relative to 1948-12-30. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 68:
  Publication date : 1948-10-09
  Language         : fr
  Person  : 'A. S.'  (QID: N/A)
  Location: 'Suisse'  (QID: Q39)

  [ARTICLE TEXT — entity markers added]
  "LES SPORTS Cyclisme LE TOUR DE FRANCE 1949 ([E1] A. S. [/E1]) — Les organisateurs du Tour de France viennent de r— "dre leurs travaux en vue de l'épreuve de 1949. Ils proposeront au congrès du calendrier de l'UCI la période allant du 7 au 31'juillet. Mais les dirigeants du SBB voudraient bien que les organisateurs çais avancent leur épreuve d'une semaine afin que l'on trouve le moyen d'insérer le Tour de [E2] Suisse [/E2] entre le Tour de France et les championnats du monde."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1949" → 1949
      - "1949" → 1949
    Verb cluster: "voudraient" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Mais les dirigeants du SBB voudraient bien que les organisateurs çais avancent leur épreuve d'une semaine afin que l'on "
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.954

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'A. S.' and 'Suisse' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'A. S.' near 'Suisse' around 1948-10-09?
  4. Resolve temporal expressions relative to 1948-10-09. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 69:
  Publication date : 1848-10-21
  Language         : de
  Person  : 'HH. Reichskommissare Teichert'  (QID: N/A)
  Location: 'Frankfurt'  (QID: Q1794)

  [ARTICLE TEXT — entity markers added]
  "[E2] Frankfurt [/E2]. Am 14. Oktober haben die HH."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Frankfurt am Main
    Description: bevölkerungsreichste Stadt in Hessen, Deutschland
    Country: ['Fränkisches Reich', 'Q153080', 'Heiliges Römisches Reich', 'Q704312', 'Freie Stadt Frankfurt', 'Q151624', 'Q27306', 'Q1206012', 'Weimarer Republik', 'NS-Staat', 'Deutschland 1945 bis 1949', 'Bundesrepublik Deutschland bis 1990', 'Deutschland']
    Located in: ['Regierungsbezirk Darmstadt', 'Regierungsbezirk Wiesbaden', 'Freie Stadt Frankfurt']
    Aliases: {'en': ['Frankfurt/Main', 'Frankfurt (Main)', 'Kreisfreie Stadt Frankfurt am Main', 'Frankfort-on-the-Main', 'Frankfurt, Germany', 'Frankfurt am Main, Germany', 'Frankfurt am Main', 'Francfort'], 'fr': ['Francfort', 'Frankfurt am Main', 'Francfort-sur-le-Mein', 'Francfort-sur-le-main', 'Frankfurt'], 'de': ['Frankfurt', 'Frankfurt/Main', 'FFM', 'Frankfurt (Main)', 'Frankfurt a. M.', 'Ffm', 'Ffm.', 'Fft.', 'Frankfurt a.M.', 'Franckfurt am Mayn', 'Frankfurt a. Main', 'Internationale Messestadt'], 'lb': ['Frankfurt', 'Frankfurt/Main']}
    Coordinates: [{'lat': 50.11055555555556, 'lon': 8.682222222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 27 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'HH. Reichskommissare Teichert' and 'Frankfurt' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'HH. Reichskommissare Teichert' near 'Frankfurt' around 1848-10-21?
  4. Resolve temporal expressions relative to 1848-10-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 70:
  Publication date : 1828-04-09
  Language         : de
  Person  : 'Raths\nherrn Jakob Tobler'  (QID: N/A)
  Location: 'Appenzell-Außerrhoden'  (QID: Q12079)

  [ARTICLE TEXT — entity markers added]
  "Der Rückblick auf das Jahr 1827, welchen das Appenzellische Mo natsblatt, für [E2] Appenzell-Außerrhoden [/E2] entworfen hat, schließt sich mit folgender Stelle: „Zwey wichtige Gegenstände und die vollgültigsten Zeugen für die fortschreitende Aufklärung fallen in der Geschichte des verflossenen Jahres besonders auf: der Eifer für den Jugendunterricht und die Oeffentlichkeit in allgemeinen Angelegenheiten. Außer demjenigen, was in den gewöhnlichen Schulen gelehrt wird, wird hier besonders der Gesangunterricht nach der Nägelischen Methode betrieben, an welchem auch erwachsene Personen Antheil nehmen. Ansehnliche Vermächtnisse erhielt die Gemeinde Speicher vom Raths herrn Jakob Tobler, der am 7. Dez. 1827, 67 Jahre alt und kinderlos starb."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Kanton Appenzell Ausserrhoden
    Description: (Halb-)Kanton der Schweiz
    Country: ['Schweiz']
    Located in: ['Schweiz']
    Aliases: {'en': ['AR', 'Kanton Appenzell Ausserrhoden', 'Appenzell Outer Rhodes', 'Canton of Appenzell Ausserrhoden', 'Kanton Appenzell A.Rh.', 'Appenzell A.Rh.'], 'fr': ['AR', 'Appenzell extérieur', 'Rhodes-Extérieures', 'Appenzell Ausserrhoden', 'Appenzell Rhodes-Extérieures'], 'de': ['AR', 'Ausserrhoden', 'Kanton Ausserrhoden', 'Kanton Appenzell A.Rh.', 'Appenzell A.Rh.', 'Appenzell Ausserrhoden'], 'lb': ['AR', 'Kanton Appenzell Rhodes-Extérieures', 'Kanton Appenzell Ausserrhoden']}
    Coordinates: [{'lat': 47.3784, 'lon': 9.3128}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1827" → 1827
      - "1827" → 1827
    Temporal signal words: nach
    Verb cluster: "erhielt" — tense=Past, aspect=None, mood=Ind
      Sentence: "Ansehnliche Vermächtnisse erhielt die Gemeinde Speicher vom Raths herrn Jakob Tobler, der am 7. Dez. 1827, 67 Jahre alt "
    Verb cluster: "schließt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Der Rückblick auf das Jahr 1827, welchen das Appenzellische Mo natsblatt, für Appenzell-Außerrhoden entworfen hat, schli"
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    Entity sentence position in article: 11 (0 = most prominent)
    OCR quality estimate: 0.973

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Raths\nherrn Jakob Tobler' and 'Appenzell-Außerrhoden' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Raths\nherrn Jakob Tobler' near 'Appenzell-Außerrhoden' around 1828-04-09?
  4. Resolve temporal expressions relative to 1828-04-09. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 71:
  Publication date : 1960-04-06
  Language         : en
  Person  : 'George Lav'  (QID: N/A)
  Location: 'Myrtle\nBeach Air Force Base'  (QID: Q6948590)

  [ARTICLE TEXT — entity markers added]
  "competing joined in a camp fire meeting and heard an ad dress by Col. Gruenwald, com manding officer of the Myrtle Beach Air Force Base. The Loris troop, sponsored by the First Baptist church, was the only troop to have all its Scout leaders present: Francis Ragan, George Rent/ and [E1] George Lav [/E1]."

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
  1. What is the relationship between 'George Lav' and 'Myrtle\nBeach Air Force Base' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'George Lav' near 'Myrtle\nBeach Air Force Base' around 1960-04-06?
  4. Resolve temporal expressions relative to 1960-04-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 72:
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
Sample 73:
  Publication date : 1790-03-03
  Language         : en
  Person  : 'Benden-D’Aloft'  (QID: N/A)
  Location: 'Pal\nace Royale'  (QID: Q635307)

  [ARTICLE TEXT — entity markers added]
  "About (even o’clock, 8co men of [E1] Benden-D’Aloft [/E1] entered the city with two pieces of cannon, which they planted on the Grand Pa lace. About ten o’clock General D’Alton thought proper to fend a large dctatchment in order to releafe, by forcible means, the ollicers and pri vates made prifoners in lhe Bafleville. About the fame time the engagement re-commenced in all quartersof the city ; and, in lefs than two hours, the Patriots made themfelves matter of the barracks of the military andofthe magazines, in which they found near 2,000 muf- kets, befides cartridges, ammunition, &c. To wards noon, they attacked the Park and the Pal ace Royale, where the greateft body of troops were concentered, with 12 pieces or cannon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Royal Palace of Brussels
    Description: palace in Brussels, Belgium
    Country: ['Belgium']
    Located in: ['Brussels']
    Aliases: {'en': ['Royal Palace, Brussels'], 'fr': ['palais royal, Bruxelles']}
    Coordinates: [{'lat': 50.841667, 'lon': 4.362222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "entered" — tense=Past, aspect=None, mood=None
      Sentence: "About (even o’clock, 8co men of Benden-D’Aloft entered the city with two pieces of cannon, which they planted on the Gra"
    Verb cluster: "attacked" — tense=Past, aspect=None, mood=None
      Sentence: "To wards noon, they attacked the Park and the Pal ace Royale, where the greateft body of troops were concentered, with 1"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 4 (0 = most prominent)
    OCR quality estimate: 0.974

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Benden-D’Aloft' and 'Pal\nace Royale' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Benden-D’Aloft' near 'Pal\nace Royale' around 1790-03-03?
  4. Resolve temporal expressions relative to 1790-03-03. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 74:
  Publication date : 1790-03-03
  Language         : en
  Person  : 'General D’Alton'  (QID: Q3934904)
  Location: 'great market'  (QID: Q215429)

  [ARTICLE TEXT — entity markers added]
  "[E1] General D’Alton [/E1] did his tu rnoff from fix o’clock in the morning to negociate an armifiice. About (even o’clock, 8co men of Benden-D’Aloft entered the city with two pieces of cannon, which they planted on the Grand Pa lace. About ten o’clock General D’Alton thought proper to fend a large dctatchment in order to releafe, by forcible means, the ollicers and pri vates made prifoners in lhe Bafleville. This was the fignal for a new engagement, which will be ever memorable for its victory. The Patriots no longer able to contain themfelves, routed the whole detatchment. To the number of joo, at the utmoft, they invelled the [E2] great market [/E2], and after a mod obllinatc conflict, they made them felves mafters of the Coros de Garde, and two pieces of cannon, and took obotlt 400 Auftrians prifoners."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Richard d'Alton
    Description: Austrian officer
    Born: ['+1732-01-01T00:00:00Z', '+1733-00-00T00:00:00Z']
    Died: ['+1791-02-16T00:00:00Z', '+1790-02-16T00:00:00Z']
    Birth place: ['Rathconrath']
    Death place: ['Speyer', 'Trier']
  Location Wikidata:
    Label: Grand-Place
    Description: main square in Brussels, Belgium
    Country: ['Belgium']
    Located in: ['Brussels']
    Aliases: {'en': ['Grote Markt', 'Nedermerckt', 'Grand Place Brussels'], 'fr': ["Grand'place de bruxelles", 'Grand Place de Bruxelles', 'Grand Place', 'Grote Markt', 'Nedermerckt'], 'de': ['Großer Markt Brüssel', 'Grand-Place / Grote Markt', 'Grote Markt']}
    Coordinates: [{'lat': 50.84670775, 'lon': 4.35253815}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: no longer, after
    Verb cluster: "did" — tense=Past, aspect=None, mood=None
      Sentence: "General D’Alton did his tu rnoff from fix o’clock in the morning to negociate an armifiice."
    Verb cluster: "invelled" — tense=Past, aspect=None, mood=None
      Sentence: "To the number of joo, at the utmoft, they invelled the great market, and after a mod obllinatc conflict, they made them "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.974

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'General D’Alton' and 'great market' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'General D’Alton' near 'great market' around 1790-03-03?
  4. Resolve temporal expressions relative to 1790-03-03. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 75:
  Publication date : 1920-07-08
  Language         : en
  Person  : 'Bob Lee Maddux'  (QID: N/A)
  Location: 'Cookeville'  (QID: Q2456192)

  [ARTICLE TEXT — entity markers added]
  "RAWLEY AGAIN Haven’t b en satisfied since I left [E2] Cookeville [/E2] until now. I seemed like I was almost lost, as I stayed in Gainesboro about IS months or 2 years. .Well, I was on (the square the other day and stopped in Maddux ft Mas- sa’s store and found a nice stock of goods. [E1] Bob Lee Maddux [/E1] Is a hus tler."

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
    Verb cluster: "was" — tense=Past, aspect=None, mood=Ind
      Sentence: ".Well, I was on (the square the other day and stopped in Maddux ft Mas- sa’s store and found a nice stock of goods."
    Verb cluster: "Have" — tense=Pres, aspect=None, mood=Ind
      Sentence: "RAWLEY AGAIN Haven’t b en satisfied since I left Cookeville until now."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 22 (0 = most prominent)
    OCR quality estimate: 0.993

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Bob Lee Maddux' and 'Cookeville' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Bob Lee Maddux' near 'Cookeville' around 1920-07-08?
  4. Resolve temporal expressions relative to 1920-07-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 76:
  Publication date : 1840-04-18
  Language         : en
  Person  : 'Gen.\nJackson'  (QID: Q11817)
  Location: 'Baltimore'  (QID: Q5092)

  [ARTICLE TEXT — entity markers added]
  "The party in [E2] Baltimore [/E2] drop the darling name of “ whig ” and send out a general address to their friends in the whole Union as “ Democrats .” The term Democrat, which they have always ridiculed, and abused because it i 3 every where claimed by]Mr. Van Buren’s and Gen. Jackson's friends; this heretofore odious name of the friends of popular rights, those candid federal whigs now take up and claim as their own."

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
    Label: Baltimore
    Description: city in Maryland, United States
    Country: ['United States']
    Located in: ['Maryland', 'Province of Maryland']
    Aliases: {'en': ['Baltimore, Maryland', 'City of Baltimore', 'Baltimore City', 'Charm City', 'B more', 'Bmore', 'Baltimore, MD', 'Balt.', 'BAL', "B'more"], 'fr': ['municipalité de Baltimore City']}
    Coordinates: [{'lat': 39.286388888889, 'lon': -76.615}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now
    Verb cluster: "take" — tense=Pres, aspect=None, mood=None
      Sentence: "Van Buren’s and Gen. Jackson's friends; this heretofore odious name of the friends of popular rights, those candid feder"
    Verb cluster: "drop" — tense=Pres, aspect=None, mood=None
      Sentence: "The party in Baltimore drop the darling name of “ whig ” and send out a general address to their friends in the whole Un"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Gen.\nJackson' and 'Baltimore' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Gen.\nJackson' near 'Baltimore' around 1840-04-18?
  4. Resolve temporal expressions relative to 1840-04-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 77:
  Publication date : 1918-04-22
  Language         : fr
  Person  : 'J. B. RUSCH'  (QID: Q2734959)
  Location: '_Suiraa'  (QID: Q39)

  [ARTICLE TEXT — entity markers added]
  "Nous serons heureux de publier de temps à autre, sous cette rubrique, des articles du bon Suisse qu'est M. J .-B. Rusch, qui a bien voulu nous donner sa collaboration. ) Une seule et même justice pour tous. [E1] J. B. RUSCH [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Johann Baptist Rusch
    Description: Swiss journalist and author (1886-1954)
    Born: ['+1886-02-07T00:00:00Z']
    Died: ['+1954-11-24T00:00:00Z']
    Birth place: ['Appenzell']
    Death place: ['Bad Ragaz']
  Location Wikidata:
    Label: Suisse
    Description: pays d'Europe centrale
    Country: ['Suisse']
    Aliases: {'en': ['Swiss Confederation', 'Swiss', 'Confoederatio Helvetica'], 'fr': ['Confédération helvétique', 'Confédération suisse', 'SUI', 'Helvétie', 'la Confédération suisse'], 'de': ['Schweizerische Eidgenossenschaft', 'Eidgenossenschaft', 'SUI', 'Confoederatio Helvetica', 'Confœderatio Helvetica'], 'lb': ['SUI']}
    Coordinates: [{'lat': 46.798562, 'lon': 8.231973}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "serons" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Nous serons heureux de publier de temps à autre, sous cette rubrique, des articles du bon Suisse qu'est M. J .-B. Rusch,"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 30 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'J. B. RUSCH' and '_Suiraa' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'J. B. RUSCH' near '_Suiraa' around 1918-04-22?
  4. Resolve temporal expressions relative to 1918-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 78:
  Publication date : 1808-09-01
  Language         : fr
  Person  : 'Judith née Jaquet'  (QID: N/A)
  Location: 'la _Sagoe'  (QID: Q68532)

  [ARTICLE TEXT — entity markers added]
  "Marianne Perrenoud, de la Sagne, fille de feu Jacob Perrenoud, et de [E1] Judith née Jaquet [/E1], morte le 27 Juillet Et les dits parens pouvant n'être pas tous connus, on les avise par la présente, que le Vendredi 9 Septembre courant, est le jour fatal sur lequel la mise en possession et investiture des biens de la " défunte, doivent être réclamées devant \ i noble Cour de Justice, assemblée dans l'hôtel-dê ville, par ceux des dits païens qui sont au pays, et qui estimeront avoir des droits à faire valoir. La présente information ainsi donnée sans conséquence, vu la clause extraordinaire ci-dessus, _exiraite du testament de la défunte, qui est déposé en original au _' grefle de Neuchatel, sera inséré trois fois dans la présente, et publié au prône de l'é glise de [E2] la _Sagoe [/E2], juridiction de la défunte."

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
    Verb cluster: "morte" — tense=Past, aspect=None, mood=None
      Sentence: "Jacob Perrenoud, et de Judith née Jaquet, morte le 27 Juillet"
    Verb cluster: "inséré" — tense=Past, aspect=None, mood=None
      Sentence: "La présente information ainsi donnée sans conséquence, vu la clause extraordinaire ci-dessus, _exiraite du testament de "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 33 (0 = most prominent)
    OCR quality estimate: 0.952

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Judith née Jaquet' and 'la _Sagoe' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Judith née Jaquet' near 'la _Sagoe' around 1808-09-01?
  4. Resolve temporal expressions relative to 1808-09-01. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 79:
  Publication date : 1930-07-11
  Language         : en
  Person  : 'W. O.'  (QID: N/A)
  Location: 'an\ncient Rome'  (QID: Q1747689)

  [ARTICLE TEXT — entity markers added]
  "‘[E1] W. O. [/E1]” MEETS OLD FRIEND IN ROME (Continued from Page One) bloodshed, he turned his army to the running of rail roads and fac tories that had been paralyzed by striking communists. And the King, beholding one mightier than him self in Italy, called Mussolini to his side. He has made Italians conscious of their illustrious an cestry. Much cf the glory of an cient Rome was buried under its hills and sidewalks."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Ancient Rome
    Description: country that began growing on the Italian Peninsula from the 8th century BC
    Aliases: {'en': ['Roman antiquity', 'Roman civilization', 'Roman culture', 'ancient Roman civilization', 'ancient Roman culture'], 'fr': ['antiquité romaine'], 'de': ['Altes Rom', 'Rom']}
    Coordinates: [{'lat': 41.89, 'lon': 12.48}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "turned" — tense=Past, aspect=None, mood=None
      Sentence: "‘W. O.” MEETS OLD FRIEND IN ROME (Continued from Page One) bloodshed, he turned his army to the running of rail roads an"
    Verb cluster: "cf" — tense=Pres, aspect=None, mood=None
      Sentence: "Much cf the glory of an cient Rome was buried under its hills and sidewalks."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 1.000

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'W. O.' and 'an\ncient Rome' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'W. O.' near 'an\ncient Rome' around 1930-07-11?
  4. Resolve temporal expressions relative to 1930-07-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 80:
  Publication date : 1808-09-01
  Language         : fr
  Person  : 'Jacob'  (QID: N/A)
  Location: 'Cote-aux-Fées'  (QID: Q68526)

  [ARTICLE TEXT — entity markers added]
  "Jaques Henri Boûrquin, veuve de [E1] Jacob [/E1] fils de Jaques Guye, des Verrières _, résidante et paroissienne de la [E2] Cote-aux-Fées [/E2], de mettre ses biens en décret ; joran, la. vigne de M. le capitaine Jacobel de' vent."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: La Côte-aux-Fées
    Description: localité et commune du canton de Neuchâtel
    Country: ['Suisse']
    Located in: ['région Val-de-Travers', 'district du Val-de-Travers']
    Aliases: {'en': ['La Côte-aux-Fées NE', 'Côte-aux-Fées', 'La Cote-aux-Fees', 'La Côte-aux-Fees', 'La Cote-aux-Fees NE', 'Cote-aux-Fees', 'La Côte'], 'fr': ['La Cote-aux-Fees', 'La Côte']}
    Coordinates: [{'lat': 46.866666666667, 'lon': 6.4833333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "mettre" — tense=None, aspect=None, mood=None
      Sentence: "Jaques Henri Boûrquin, veuve de Jacob fils de Jaques Guye, des Verrières _, résidante et paroissienne de la Cote-aux-Fée"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 9 (0 = most prominent)
    OCR quality estimate: 0.952

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Jacob' and 'Cote-aux-Fées' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Jacob' near 'Cote-aux-Fées' around 1808-09-01?
  4. Resolve temporal expressions relative to 1808-09-01. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 81:
  Publication date : 1921-10-05
  Language         : fr
  Person  : 'Donini'  (QID: N/A)
  Location: 'Lugano'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "[E1] Donini [/E1], de [E2] Lugano [/E2] ;"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 49 (0 = most prominent)
    OCR quality estimate: 0.951

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Donini' and 'Lugano' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Donini' near 'Lugano' around 1921-10-05?
  4. Resolve temporal expressions relative to 1921-10-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 82:
  Publication date : 1938-05-11
  Language         : fr
  Person  : 'M. Henlein'  (QID: Q57462)
  Location: 'Reich'  (QID: Q518617)

  [ARTICLE TEXT — entity markers added]
  "le discours de [E1] M. Henlein [/E1]. au congrès du parti des Allemands des Sudètes à Karlsbad et écrit ce qui suit : Les intentions de M. Henlein, telles qu'elles apparaissent dans son discours de Karlsbad, ont pour but de mettre en pratique l'enseignement de Nietzsche sm la revalorisation de toutes les valeurs et cela avec l'aide du gouvernement de Prague. Mais, M. Henlein veut un Etat qui serait fédératif comme la Suisse et raciste comme l'Allemagne. H demande que le nouvel Etat fasse une politique qui soit favorable au « Drang nach Osten » du [E2] Reich [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Konrad Henlein
    Description: homme politique pro-nazi dans la Tchécoslovaquie de l'entre-deux-guerres
    Born: ['+1898-05-06T00:00:00Z']
    Died: ['+1945-05-10T00:00:00Z']
    Birth place: ['Vratislavice nad Nisou']
    Death place: ['Q43453', 'Q12045676']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "demande" — tense=Pres, aspect=None, mood=Ind
      Sentence: "H demande que le nouvel Etat fasse une politique qui soit favorable au « Drang nach Osten » du Reich."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 44 (0 = most prominent)
    OCR quality estimate: 0.981

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Henlein' and 'Reich' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Henlein' near 'Reich' around 1938-05-11?
  4. Resolve temporal expressions relative to 1938-05-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 83:
  Publication date : 1898-05-02
  Language         : de
  Person  : 'Jakob Welti'  (QID: N/A)
  Location: 'Bahnhof\nstraße'  (QID: Q675026)

  [ARTICLE TEXT — entity markers added]
  "Die Bilder sind annähernd in chronologischer Reihen folge aufgehängt, und zwar hat man sich bei der Be trachtung immer links, zunächst also an die Wände zu halten, welche auf der Fensterseite nach der Bahnhof straße zu liegen, bis man in die Abteilung am Ende des Saales gelangt, von wo man, immer sich links haltend, wieder zum Ausgang zurückkehrt, wo die Ge mälde aus des Künstlers letzter Periode angebracht sind. Das Schlußstück bildet das wohlgetroffene Oelbildnis, das [E1] Jakob Welti [/E1] im vorigen Jahre von Rudolf Koller entwerfen durfte."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Bahnhofstrasse
    Description: Straße in der Stadt Zürich, Schweiz
    Country: ['Q39']
    Located in: ['Q72', 'Kanton Zürich']
    Aliases: {'en': ['Bahnhofstrasse, Zürich', 'Bahnhof Strasse'], 'de': ['Bahnhofstraße']}
    Coordinates: [{'lat': 47.373681, 'lon': 8.538523}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Verb cluster: "bildet" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Das Schlußstück bildet das wohlgetroffene Oelbildnis, das Jakob Welti im vorigen Jahre von Rudolf Koller entwerfen durft"
    Verb cluster: "sind" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Die Bilder sind annähernd in chronologischer Reihen folge aufgehängt, und zwar hat man sich bei der Be trachtung immer l"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 13 (0 = most prominent)
    OCR quality estimate: 0.998

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Jakob Welti' and 'Bahnhof\nstraße' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Jakob Welti' near 'Bahnhof\nstraße' around 1898-05-02?
  4. Resolve temporal expressions relative to 1898-05-02. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 84:
  Publication date : 1930-03-21
  Language         : en
  Person  : 'C. P. Gray'  (QID: N/A)
  Location: 'Dare\ncounty'  (QID: Q295787)

  [ARTICLE TEXT — entity markers added]
  "[E1] C. P. Gray [/E1], is principal of the Buxton school. The students are being taught in the neighboring homes of E. P. White, G. D. Miller and U. B. Williams.— D. V. M. Buxton Loses Its School Building Buxton, at Cane Hattcras, Dare county, finds itself in a bad situ-"

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
    Verb cluster: "is" — tense=Pres, aspect=None, mood=Ind
      Sentence: "C. P. Gray, is principal of the Buxton school."
    Verb cluster: "Loses" — tense=Pres, aspect=None, mood=None
      Sentence: "D. V. M. Buxton Loses Its School Building Buxton, at Cane Hattcras, Dare county, finds itself in a bad situ-"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.969

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'C. P. Gray' and 'Dare\ncounty' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'C. P. Gray' near 'Dare\ncounty' around 1930-03-21?
  4. Resolve temporal expressions relative to 1930-03-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 85:
  Publication date : 1790-05-29
  Language         : en
  Person  : 'hon. James Townfena'  (QID: N/A)
  Location: 'Jericho'  (QID: Q3476975)

  [ARTICLE TEXT — entity markers added]
  "On Tuefdaylaft.died at [E2] Jericho [/E2] on Long-Ifland, the hon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Jericho
    Description: hamlet and census-designated place in Nassau County, New York, United States
    Country: ['United States']
    Located in: ['Nassau County']
    Aliases: {'en': ['Jericho, New York', 'Jericho, NY']}
    Coordinates: [{'lat': 40.7867, 'lon': -73.5367}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "Tuefdaylaft.died" — tense=Past, aspect=Perf, mood=None
      Sentence: "On Tuefdaylaft.died at Jericho on Long-Ifland, the hon."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 4 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'hon. James Townfena' and 'Jericho' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'hon. James Townfena' near 'Jericho' around 1790-05-29?
  4. Resolve temporal expressions relative to 1790-05-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 86:
  Publication date : 1858-10-24
  Language         : de
  Person  : 'Minister»\nPräsidenten Grafen Cavour'  (QID: Q166092)
  Location: 'T u r i n'  (QID: Q495)

  [ARTICLE TEXT — entity markers added]
  "Graf Pcs di Villamarina, Geschäftsträger am französischen Hofe, sowie Marchcsc d'Azeglio, Geschäftsträger am Hofe von St. James, weilen seit einigen Tagen in Turin und haben mit dem Minister» Präsidenten Grafen Cavour öftere und lange dauernde Conferenzcn. In mehreren picmontcsischcn Blätter wurde seit einiger Zeit Klage über die Art und Weise erhoben, in der die Behörden hinsichtlich der in den aufgehobenen Klöstern vorgefundenen Bibliotheken verfahren. das vertragsmäßige Recht achten zu wollen scheint, laßt den Prinzen von Carigoan eine mysteriöse Ncisc nach dem Norden von Teutschland machen, um, wenn nickt ein Schutz- und Trutzbündniß, so doch einen Neutra« litäts'Vertraz mit Preußen für den Krieg zu schließen, „zu welchem sich Piémont gegen Oesterreich vorberei tet." T"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Camillo Benso von Cavour
    Description: italienischer Staatsmann und erster Premierminister
    Born: ['+1810-08-10T00:00:00Z', '+1810-01-01T00:00:00Z']
    Died: ['+1861-06-06T00:00:00Z', '+1861-01-01T00:00:00Z']
    Birth place: ['Turin']
    Death place: ['Turin']
  Location Wikidata:
    Label: Turin
    Description: Großstadt im Piemont, Norditalien
    Country: ['Italien', 'Königreich Sardinien', 'Herzogtum Savoyen', 'County of Savoy', 'Markgrafschaft Turin', 'Markgrafschaft Ivrea', 'Karolingerreich', 'Langobardenreich']
    Located in: ['Provinz Turin', 'Metropolitanstadt Turin', 'Herzogtum Savoyen', 'Province of Turin', 'Pô', 'Römisches Kaiserreich']
    Aliases: {'en': ['Torino', 'Turin, Italy']}
    Coordinates: [{'lat': 45.079166666666666, 'lon': 7.676111111111111}]
  Known person–location links: {"birth_place": "P19", "death_place": "P20"}

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Verb cluster: "weilen" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Graf Pcs di Villamarina, Geschäftsträger am französischen Hofe, sowie Marchcsc d'Azeglio, Geschäftsträger am Hofe von St"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Minister»\nPräsidenten Grafen Cavour' and 'T u r i n' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Minister»\nPräsidenten Grafen Cavour' near 'T u r i n' around 1858-10-24?
  4. Resolve temporal expressions relative to 1858-10-24. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 87:
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
Sample 88:
  Publication date : 1868-02-19
  Language         : de
  Person  : 'Bismarck'  (QID: Q8442)
  Location: 'Deutſchland'  (QID: Q183)

  [ARTICLE TEXT — entity markers added]
  "digt : überall in [E2] Deutſchland [/E2] und über deſſen Grenzen hinaus richtet ſich die Beachtung und Anerkennung der Regierung und der Völker auf das Verfahren Preußens in den eroberten Provinzen . Die bedeutſamſten Stimmen aus Süddeutſchland ver⸗ zu dieſer Berathung herbeigekommen und von 141 Anweſenden baben 127 ihre Zuſtimmung zu der Vorlage ertheilt ; geſtimmt hat , iſt eine Politik des Wohlwollens und der Ge — hat , zur feſten Stütze zu dienen . Rechte und die provinzielle Selbſtſtändigkeit der gewonnenen Landestheile mit ſolcher Fürſorge wahrt , nicht eine engberzige Eroberungspolitik , ſondern eine wahrhaft nationale Politik be⸗ mit wie gutem Rechte Graf [E1] Bismarck [/E1] darauf hindeutete , daß dieſe hannoverſche Frage nur im Zuſammenhange der geſammten Politik Preußens richtig beurtheilt werden könne ."

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
    No relevant Wikidata properties found.
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
  1. What is the relationship between 'Bismarck' and 'Deutſchland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Bismarck' near 'Deutſchland' around 1868-02-19?
  4. Resolve temporal expressions relative to 1868-02-19. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 89:
  Publication date : 1938-05-11
  Language         : fr
  Person  : 'M. E.\nJuillerat'  (QID: N/A)
  Location: 'Porrentruy'  (QID: Q68256)

  [ARTICLE TEXT — entity markers added]
  "Il suggère à M. E. Juillerat, au « Jura » de [E2] Porrentruy [/E2] ces utiles réflexions tendant à proposer un remède :"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Porrentruy
    Description: commune suisse dans le canton du Jura
    Country: ['Suisse']
    Located in: ['district de Porrentruy']
    Aliases: {'en': ['Porrentruy JU', 'Purrentru', 'pons Ragentrudis', 'Poérreintru', 'Pruntrut', 'Bruntrutain', 'ville bruntrutaine'], 'fr': ['Pruntrut', 'ville bruntrutaine', 'bruntrutain'], 'de': ['Puntrut', 'Porrentruy', 'Bruntrut', 'Porentrui']}
    Coordinates: [{'lat': 47.416666666667, 'lon': 7.0833333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "tendant" — tense=Pres, aspect=None, mood=None
      Sentence: "Il suggère à M. E. Juillerat, au « Jura » de Porrentruy ces utiles réflexions tendant à proposer un remède :"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.981

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. E.\nJuillerat' and 'Porrentruy' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. E.\nJuillerat' near 'Porrentruy' around 1938-05-11?
  4. Resolve temporal expressions relative to 1938-05-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 90:
  Publication date : 1841-07-30
  Language         : fr
  Person  : 'John Russell'  (QID: N/A)
  Location: 'Angleterre'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "ANGLETERRE LONDRES 22 juillet.— Les journaux anglais continuent à spéculer sur les actes de l'ancien et du futur ministère, sans nous apprendre à cet égard rien de définitif. En attendant, les principaux chefs du parti publient leurs manifestes. Dans le nombre se fait remarquer celui de lord [E1] John Russell [/E1], adressé par ce ministre aux électeurs de la Cité, la veille de son mariage avec lady Fanny Elliott."

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
  1. What is the relationship between 'John Russell' and 'Angleterre' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'John Russell' near 'Angleterre' around 1841-07-30?
  4. Resolve temporal expressions relative to 1841-07-30. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 91:
  Publication date : 1890-11-06
  Language         : en
  Person  : 'Edward Shepherd'  (QID: N/A)
  Location: 'Harrisburg,\nIII.'  (QID: Q576252)

  [ARTICLE TEXT — entity markers added]
  "[E1] Edward Shepherd [/E1], Harrisburg, III., bad a running sore on his leg of eight years’ standing."

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
    Verb cluster: "running" — tense=Pres, aspect=Prog, mood=None
      Sentence: "Edward Shepherd, Harrisburg, III., bad a running sore on his leg of eight years’ standing."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.992

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Edward Shepherd' and 'Harrisburg,\nIII.' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Edward Shepherd' near 'Harrisburg,\nIII.' around 1890-11-06?
  4. Resolve temporal expressions relative to 1890-11-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 92:
  Publication date : 1981-07-25
  Language         : fr
  Person  : 'Sammy Price'  (QID: N/A)
  Location: 'SUISSE ITALIENNE'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Valk, série-23.30 [E1] Sammy Price [/E1] en concert-0.15 Téléjournal. [E2] SUISSE ITALIENNE [/E2] 18.10"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 37 (0 = most prominent)
    OCR quality estimate: 0.663

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Sammy Price' and 'SUISSE ITALIENNE' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Sammy Price' near 'SUISSE ITALIENNE' around 1981-07-25?
  4. Resolve temporal expressions relative to 1981-07-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 93:
  Publication date : 1981-12-11
  Language         : fr
  Person  : 'M. Benjamin'  (QID: N/A)
  Location: 'Lyon'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "La tête dans les étoiles », une pièce conçue et créée en 1977 par Maurice Yendt directeur du Théâtre des Jeunes Années de [E2] Lyon [/E2]. Du mystère, des aventures palpitantes, du rêve, une part de poésie, beaucoup d'imagination et une cascade d'actions sensationnelles ; cette pièce rassemble toutes les qualités du théâtre épique. Mais il ne s'agit plus là de mousquetaires ou de cow-boys ; on s'aventure grâce à [E1] M. Benjamin [/E1] sur la froide planète Fulgur."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1977" → 1977
    Temporal signal words: plus
    Verb cluster: "aventure" — tense=Pres, aspect=None, mood=Ind
      Sentence: "on s'aventure grâce à M. Benjamin sur la froide planète Fulgur."
    Verb cluster: "créée" — tense=Past, aspect=None, mood=None
      Sentence: "La tête dans les étoiles », une pièce conçue et créée en 1977 par Maurice Yendt directeur du Théâtre des Jeunes Années d"
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 4 days
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.985

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Benjamin' and 'Lyon' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Benjamin' near 'Lyon' around 1981-12-11?
  4. Resolve temporal expressions relative to 1981-12-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 94:
  Publication date : 1978-09-27
  Language         : fr
  Person  : 'Heighway'  (QID: Q1370340)
  Location: 'Danemark'  (QID: Q35)

  [ARTICLE TEXT — entity markers added]
  "Les défenseurs de l'équipe d'Angleterre, Phil Neal et Emlyn Hughes, et l'ailier Steve Heigh way (Eire) ont perdS la forme. Les deux premiers ont été décevants contre le [E2] Danemark [/E2], la semaine dernière, à Copenhague, et [E1] Heighway [/E1] a été remplacé aussi bien contre l'Irlande, à Dublin, que contre West Bromwich Albion, samedi dernier."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Steve Heighway
    Description: footballeur irlandais
    Born: ['+1947-11-25T00:00:00Z']
    Birth place: ['Q1761']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "décevants" — tense=Past, aspect=None, mood=None
      Sentence: "Les deux premiers ont été décevants contre le Danemark, la semaine dernière, à Copenhague, et Heighway a été remplacé au"
    Verb cluster: "ont" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Les défenseurs de l'équipe d'Angleterre, Phil Neal et Emlyn Hughes, et l'ailier Steve Heigh way (Eire) ont perdS la form"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 12 (0 = most prominent)
    OCR quality estimate: 0.979

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Heighway' and 'Danemark' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Heighway' near 'Danemark' around 1978-09-27?
  4. Resolve temporal expressions relative to 1978-09-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 95:
  Publication date : 1981-11-17
  Language         : fr
  Person  : 'Pierre Perdigon'  (QID: N/A)
  Location: 'Eglise Saint-Jacques'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "[E2] Eglise Saint-Jacques [/E2]-20.30, récital d'orgue par [E1] Pierre Perdigon [/E1]."

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
  1. What is the relationship between 'Pierre Perdigon' and 'Eglise Saint-Jacques' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Pierre Perdigon' near 'Eglise Saint-Jacques' around 1981-11-17?
  4. Resolve temporal expressions relative to 1981-11-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 96:
  Publication date : 1900-11-06
  Language         : en
  Person  : 'Blank!'  (QID: N/A)
  Location: 'Kiowa'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "But a ghost dance now being held in the Wichita and [E2] Kiowa [/E2] reservations of Indian territory is not believed to presage any such terrible scenes. The reservations named are to be opened to white settlers when the allotment of lands to Indians shall have been completed, and the red men fear that once the paleface gets in among them the days of tribal power will have been numbered. With the view of ■preventing the Impending Incursion thepe older chiefs have organized the ghost dance, which will, they hope, serve to keep the white men away. [E1] Blank! [/E1], the leader of the ghost dance, is & high priest in his tribe and a dreamer as well."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now
    Verb cluster: "have organized" — tense=Pres, aspect=Perf, mood=Ind
      Sentence: "With the view of ■preventing the Impending Incursion thepe older chiefs have organized the ghost dance, which will, they"
    Verb cluster: "is believed" — tense=Pres, aspect=Perf, mood=Ind [NEGATED]
      Sentence: "But a ghost dance now being held in the Wichita and Kiowa reservations of Indian territory is not believed to presage an"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.990

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Blank!' and 'Kiowa' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Blank!' near 'Kiowa' around 1900-11-06?
  4. Resolve temporal expressions relative to 1900-11-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 97:
  Publication date : 1928-02-17
  Language         : de
  Person  : 'Luther'  (QID: Q9554)
  Location: 'Münchenbuchsee'  (QID: Q69071)

  [ARTICLE TEXT — entity markers added]
  "Sind die beiden wie Sokrates und Plato, wie [E1] Luther [/E1] und Me lauchthon oder wie Gebender und — Richter? Ueber [E2] Münchenbuchsee [/E2] geht's nach Yverdon."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Martin Luther
    Description: deutscher Theologe, Autor und Urheber der Reformation
    Born: ['+1483-11-10T00:00:00Z', '+1483-00-00T00:00:00Z']
    Died: ['+1546-02-18T00:00:00Z']
    Birth place: ['Q484870']
    Death place: ['Q484870']
    Residences: ['Eisleben', 'Q502926', 'Q1733', 'Q7070', 'Erfurt', 'Lutherstadt Wittenberg', 'Q151545']
    Work locations: ['Q420158', 'Wartburg']
  Location Wikidata:
    Label: Münchenbuchsee
    Description: Gemeinde im Kanton Bern in der Schweiz
    Country: ['Schweiz']
    Located in: ['Verwaltungskreis Bern-Mittelland', 'Q263941']
    Aliases: {'en': ['Münchenbuchsee BE', 'Munchenbuchsee', 'Muenchenbuchsee'], 'fr': ['Munchenbuchsee']}
    Coordinates: [{'lat': 47.016388888889, 'lon': 7.45}]
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
  1. What is the relationship between 'Luther' and 'Münchenbuchsee' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Luther' near 'Münchenbuchsee' around 1928-02-17?
  4. Resolve temporal expressions relative to 1928-02-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 98:
  Publication date : 1830-05-15
  Language         : en
  Person  : 'James Daniel'  (QID: N/A)
  Location: 'Satvanah Old Town'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "[E1] James Daniel [/E1], late on® of tho Judg es of the Cherokee Courts, in the Cherokee nation, aged forty years, has been raised in the southeastern part of the Cherokee nation—is ac quainted on the Appalachy anti Chat- lahoochy rivers,—he thinks the High Shoals of the Appalachy is nearly a- bout dne east from the Buzzard roost on Chattahoochy—he knows of the placo called [E2] Satvanah Old Town [/E2] on Chattahoochy and the place called Buzzard Roost on the same river, and he never knew of any other plac es knotvrt by these harries. He fur ther states that he was educated in Green County Georgia, and when there he haS frequently heard the subject of the boundary between the Creeks and Cherokees mentioned a- roongst tho people of that county, as running from the High Shoals of Ap palachy a direct course to the mouth of Will’s creek on Coosa river, and he alwavs received the same impression from the Cherokees. Given under m'y hand in the Cherokee nation. JAVIES DANIEL."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now, early, late
    Verb cluster: "thinks" — tense=Pres, aspect=None, mood=None
      Sentence: "James Daniel, late on® of tho Judg es of the Cherokee Courts, in the Cherokee nation, aged forty years, has been raised "
    Verb cluster: "Given" — tense=Past, aspect=Perf, mood=None
      Sentence: "Given under m'y hand in the Cherokee nation."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.989

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'James Daniel' and 'Satvanah Old Town' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'James Daniel' near 'Satvanah Old Town' around 1830-05-15?
  4. Resolve temporal expressions relative to 1830-05-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 99:
  Publication date : 1818-01-06
  Language         : de
  Person  : 'Wilkins'  (QID: Q676998)
  Location: 'Waterloo'  (QID: Q179034)

  [ARTICLE TEXT — entity markers added]
  "Die Plane, welche die Baukünstler, Smirke für die Seemacht, und [E1] Wilkins [/E1] für die Landmacht, eingereicht haben, sind genehmigt. Das [E2] Waterloo [/E2]-Monument wird 200,000. Pf."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: William Wilkins
    Description: English architect, classical scholar and archaeologist (1778–1839)
    Born: ['+1778-08-31T00:00:00Z']
    Died: ['+1839-08-31T00:00:00Z']
    Birth place: ['Norwich']
    Death place: ['Cambridge']
    Residences: ['England']
  Location Wikidata:
    Label: Waterloo
    Description: Gemeinde in Wallonisch Brabant, Belgien
    Country: ['Q31']
    Located in: ['Q93707']
    Aliases: {'en': ['Waterlô'], 'fr': ['Waterloo, Belgique'], 'de': ['Waterlô']}
    Coordinates: [{'lat': 50.716666666667, 'lon': 4.3833333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "sind" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Die Plane, welche die Baukünstler, Smirke für die Seemacht, und Wilkins für die Landmacht, eingereicht haben, sind geneh"
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Das Waterloo-Monument wird 200,000. Pf."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 1 (0 = most prominent)
    OCR quality estimate: 0.970

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Wilkins' and 'Waterloo' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Wilkins' near 'Waterloo' around 1818-01-06?
  4. Resolve temporal expressions relative to 1818-01-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 100:
  Publication date : 1868-02-17
  Language         : de
  Person  : 'Marquis Boissy'  (QID: Q3135539)
  Location: 'Paris'  (QID: Q90)

  [ARTICLE TEXT — entity markers added]
  "Mehrere Söhne der ersten Familien des Königreichs Siam sind in [E2] Paris [/E2] erwartet. Nach glaubwürdigen Londoner Privatberichten treten die erfreulichsten Vorzeichen eines kräftigern Geschäfts verkehrs zu Tage. Was von einem parlamentarischen Ministerium in Frankreich verlautet hat, ist durch den gestrigen Pariser Telegraphen total in Abrede gestellt worden. Der vor Kurzem verstorbene Senator Montlaville war ein geschworner Feind der Engländer ganz à la [E1] Marquis Boissy [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Hilaire Étienne Octave Rouillé de Boissy
    Description: French politician
    Born: ['+1798-05-05T00:00:00Z']
    Died: ['+1866-09-26T00:00:00Z']
    Birth place: ['Paris']
    Death place: ['Louveciennes']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: {"birth_place": "P19"}

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Verb cluster: "war" — tense=Past, aspect=None, mood=Ind
      Sentence: "Der vor Kurzem verstorbene Senator Montlaville war ein geschworner Feind der Engländer ganz à la Marquis Boissy."
    Verb cluster: "sind" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Mehrere Söhne der ersten Familien des Königreichs Siam sind in Paris erwartet."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 28 (0 = most prominent)
    OCR quality estimate: 0.975

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Marquis Boissy' and 'Paris' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Marquis Boissy' near 'Paris' around 1868-02-17?
  4. Resolve temporal expressions relative to 1868-02-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 101:
  Publication date : 1950-09-23
  Language         : en
  Person  : 'Mrs. H. F. Thomas'  (QID: N/A)
  Location: 'Tuskegee'  (QID: Q79718)

  [ARTICLE TEXT — entity markers added]
  "Housewives League Hold: Convention at [E2] Tuskegee [/E2] The National Housewives Lea gue of America recently convened at T iskegee Institute. Ala . Mrs. Fuqua urged all members and visitors of the fifteen states represented at the Convention who were engaged in new enter prises of manufacturing, to join the league or keep in touch with it in order that they may be pro moted. Among the guests were: [E1] Mrs. H. F. Thomas [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Tuskegee
    Description: city in Macon County, Alabama, United States
    Country: ['United States']
    Located in: ['Macon County']
    Aliases: {'en': ['Tuskegee, Alabama', 'Tuskegee, AL']}
    Coordinates: [{'lat': 32.431506, 'lon': -85.706781}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: recently
    Verb cluster: "were" — tense=Past, aspect=None, mood=Ind
      Sentence: "Among the guests were: Mrs. H. F. Thomas."
    Verb cluster: "convened" — tense=Past, aspect=None, mood=None
      Sentence: "Housewives League Hold: Convention at Tuskegee The National Housewives Lea gue of America recently convened at T iskegee"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 18 (0 = most prominent)
    OCR quality estimate: 0.998

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mrs. H. F. Thomas' and 'Tuskegee' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mrs. H. F. Thomas' near 'Tuskegee' around 1950-09-23?
  4. Resolve temporal expressions relative to 1950-09-23. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 102:
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
Sample 103:
  Publication date : 1790-03-03
  Language         : en
  Person  : 'Benden-D’Aloft'  (QID: N/A)
  Location: 'Porte de Namur'  (QID: Q3399071)

  [ARTICLE TEXT — entity markers added]
  "About (even o’clock, 8co men of [E1] Benden-D’Aloft [/E1] entered the city with two pieces of cannon, which they planted on the Grand Pa lace. About ten o’clock General D’Alton thought proper to fend a large dctatchment in order to releafe, by forcible means, the ollicers and pri vates made prifoners in lhe Bafleville. To wards noon, they attacked the Park and the Pal ace Royale, where the greateft body of troops were concentered, with 12 pieces or cannon. After a very heavy firing on both fides, D’Alton perceiving that the place was no longer tenable againtt fo much bravery, capitulated for the im mediate retreat of his whole gerrifon ; and the requell having been acceded to, about one o’clock they departed, with great precipitation, through the [E2] Porte de Namur [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Namur Gate
    Description: former city gate of Brussels, Belgium
    Country: ['Belgium']
    Located in: ['Brussels']
    Coordinates: [{'lat': 50.83861, 'lon': 4.36194}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: no longer, after, late
    Verb cluster: "entered" — tense=Past, aspect=None, mood=None
      Sentence: "About (even o’clock, 8co men of Benden-D’Aloft entered the city with two pieces of cannon, which they planted on the Gra"
    Verb cluster: "perceiving" — tense=Pres, aspect=Prog, mood=None
      Sentence: "After a very heavy firing on both fides, D’Alton perceiving that the place was no longer tenable againtt fo much bravery"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 4 (0 = most prominent)
    OCR quality estimate: 0.974

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Benden-D’Aloft' and 'Porte de Namur' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Benden-D’Aloft' near 'Porte de Namur' around 1790-03-03?
  4. Resolve temporal expressions relative to 1790-03-03. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 104:
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
Sample 105:
  Publication date : 1928-10-25
  Language         : fr
  Person  : 'Marx'  (QID: Q9061)
  Location: 'Bâle-Campagne'  (QID: Q78)

  [ARTICLE TEXT — entity markers added]
  "Quel que soit le succès de la liste socialiste, on s'accorde généralement à prévoir qu'il ne suffira pas à procurer aux disciples dé [E1] Marx [/E1] le gros succès moral de conquérir la majorité relative au Parlement. La masse élec torale, dans son ensemble, a fini par comprendre qu'en coupant les racines et en entamant le trône de l'arbre économique nationàL on dessécherait fatalement, finalement, branches, feuilles « t'fruits... Bâle-Ville députait à Berne quatre bourgeois et trois extrémistes, Un parti « évangéliste » intervient, cette fois, dans la mêlée et a. refusé l'apparentement avec les autres partis nationaux. Cette attitude étrange n'est pas sans causer des inquiétudes sur l'issue du scrutin dans la grande ville du Rhin et l'on craint que l'évangélisme n'y serve de tremplin aux moscoutaires, ce qui serait à déplorer vivement. [E2] Bâle-Campagne [/E2] est fertile en dissidents et en brouillons."

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
    Label: Bâle
    Description: ville de Suisse et chef-lieu du canton de Bâle-Ville
    Country: ['Suisse']
    Located in: ['canton de Bâle-Ville']
    Aliases: {'en': ['Basle', 'Basel BS', 'Bâle'], 'fr': ['Basel'], 'de': ['Bâle'], 'lb': ['Bâle']}
    Coordinates: [{'lat': 47.560555555556, 'lon': 7.5905555555556}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "accorde" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Quel que soit le succès de la liste socialiste, on s'accorde généralement à prévoir qu'il ne suffira pas à procurer aux "
    Verb cluster: "est causer" — tense=Pres, aspect=None, mood=Ind [NEGATED]
      Sentence: "Cette attitude étrange n'est pas sans causer des inquiétudes sur l'issue du scrutin dans la grande ville du Rhin et l'on"
    Verb cluster: "députait" — tense=Imp, aspect=None, mood=Ind
      Sentence: "La masse élec torale, dans son ensemble, a fini par comprendre qu'en coupant les racines et en entamant le trône de l'ar"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 4 (0 = most prominent)
    OCR quality estimate: 0.982

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Marx' and 'Bâle-Campagne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Marx' near 'Bâle-Campagne' around 1928-10-25?
  4. Resolve temporal expressions relative to 1928-10-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 106:
  Publication date : 1828-04-09
  Language         : de
  Person  : 'Rathsherrn Rechsteiner'  (QID: N/A)
  Location: 'Appenzell-Innerrhoden'  (QID: Q12094)

  [ARTICLE TEXT — entity markers added]
  "Aus [E2] Appenzell-Innerrhoden [/E2] meldet das Merzstück des „Ap penzellischen Monatsblattes" was folgt: „Wie schon regelmäßig seit 5 Jahren, so erschienen auch diesesmal bey dem am 20. Merz abgehal tenen großen zweyfachen Landrath mehrere Männer, welche ein Memorial eingaben, das im Wesentlichen Folgendes besagt: „Tit. Schon seit 1823 wurden Ihnen alljährlich am heutigen Verfassungsrathe schriftliche und mündliche Wünsche zur Berücksichtigung mitgetheilt, die Sie jedes mal. — Zugleich soll an künftiger Landsgemeinde zur Entscheidung kommen, ob in Fällen, wo die positiven Gesetze nicht bestimmt absprechen, könne und möge ap pellirt werden? Hierzu gab wahrscheinlich der im vorigen Jahre vorge fallene Prozeß des [E1] Rathsherrn Rechsteiner [/E1] die Veranlassung."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Kanton Appenzell Innerrhoden
    Description: (Halb-)Kanton der Schweiz
    Country: ['Schweiz']
    Located in: ['Schweiz']
    Aliases: {'en': ['AI', 'Appenzell Inner-Rhodes', 'Innerrhoden', 'Appenzell Inner Rhodes', 'Appenzell Inner-Rhoden', 'Kanton Appenzell Innerrhoden'], 'fr': ['Appenzell intérieur', 'AI', 'Rhodes-Intérieures', 'Appenzell Rhodes-Intérieures'], 'de': ['AI', 'Innerrhoden', 'Kanton Innerrhoden', 'Appenzell Innerrhoden', 'Appenzell I. Rh.', 'Eidgenössischer Stand Appenzell Innerrhoden', 'Eidgenössischer Stand Appenzell I. Rh.', 'Kanton Appenzell I. Rh.'], 'lb': ['Kanton Appenzell Rhodes-Intérieures', 'Kanton Appenzell Innerrhoden']}
    Coordinates: [{'lat': 47.3, 'lon': 9.4}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1823" → 1823
    Temporal signal words: vor
    Verb cluster: "gab" — tense=Past, aspect=None, mood=Ind
      Sentence: "Hierzu gab wahrscheinlich der im vorigen Jahre vorge fallene Prozeß des Rathsherrn Rechsteiner die Veranlassung."
    Verb cluster: "meldet" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Aus Appenzell-Innerrhoden meldet das Merzstück des „Ap penzellischen Monatsblattes" was folgt: „Wie schon regelmäßig sei"
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 5 days
    Entity sentence position in article: 39 (0 = most prominent)
    OCR quality estimate: 0.973

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Rathsherrn Rechsteiner' and 'Appenzell-Innerrhoden' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Rathsherrn Rechsteiner' near 'Appenzell-Innerrhoden' around 1828-04-09?
  4. Resolve temporal expressions relative to 1828-04-09. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 107:
  Publication date : 1818-01-06
  Language         : de
  Person  : 'Herzogs von\nWellington'  (QID: Q131691)
  Location: 'Greenwich'  (QID: Q179385)

  [ARTICLE TEXT — entity markers added]
  "Die Trafalgar-Säule wird 100,000. Pfund kosten, und zu [E2] Greenwich [/E2] errichtet wer den. Sie besteht aus einem einfachen Oktogon, von einer angemessenen Basis, mit einer Schiffskrone bedeckt, zu wel cher kolossale Stufen führen. An beyden Monumenten wird gearbeitet. Außerdem wird zu Ehren des Herzogs von Wellington ein Denkmal auf Blakdownhill errichtet, wel ches die Gestalt eines Dreyecks und die Höhe von 150."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Außerdem wird zu Ehren des Herzogs von Wellington ein Denkmal auf Blakdownhill errichtet, wel ches die Gestalt eines Dre"
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Die Trafalgar-Säule wird 100,000. Pfund kosten, und zu Greenwich errichtet wer den."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 10 (0 = most prominent)
    OCR quality estimate: 0.970

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Herzogs von\nWellington' and 'Greenwich' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Herzogs von\nWellington' near 'Greenwich' around 1818-01-06?
  4. Resolve temporal expressions relative to 1818-01-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 108:
  Publication date : 1830-05-15
  Language         : en
  Person  : 'James Daniel'  (QID: N/A)
  Location: 'Appalachy'  (QID: Q93332)

  [ARTICLE TEXT — entity markers added]
  "[E1] James Daniel [/E1], late on® of tho Judg es of the Cherokee Courts, in the Cherokee nation, aged forty years, has been raised in the southeastern part of the Cherokee nation—is ac quainted on the [E2] Appalachy [/E2] anti Chat- lahoochy rivers,—he thinks the High Shoals of the Appalachy is nearly a- bout dne east from the Buzzard roost on Chattahoochy—he knows of the placo called Satvanah Old Town on Chattahoochy and the place called Buzzard Roost on the same river, and he never knew of any other plac es knotvrt by these harries. He fur ther states that he was educated in Green County Georgia, and when there he haS frequently heard the subject of the boundary between the Creeks and Cherokees mentioned a- roongst tho people of that county, as running from the High Shoals of Ap palachy a direct course to the mouth of Will’s creek on Coosa river, and he alwavs received the same impression from the Cherokees. Given under m'y hand in the Cherokee nation. JAVIES DANIEL."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Appalachian Mountains
    Description: mountain range in the eastern United States and Canada
    Country: ['United States', 'Canada', 'France']
    Located in: ['Newfoundland and Labrador', 'Quebec', 'Nova Scotia', 'New Brunswick', 'Maine', 'New Hampshire', 'Vermont', 'Massachusetts', 'Connecticut', 'New York', 'Pennsylvania', 'Maryland', 'Virginia', 'West Virginia', 'Ohio', 'Kentucky', 'Tennessee', 'New Jersey', 'North Carolina', 'South Carolina', 'Georgia', 'Alabama', 'Saint Pierre and Miquelon']
    Aliases: {'en': ['Apalaches', 'The Appalachians', 'Appalachians'], 'fr': ['Alleghanys', 'Appalache', 'Les Appalaches']}
    Coordinates: [{'lat': 35.764722222222, 'lon': -82.265277777778}, {'lat': 38, 'lon': -79}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now, early, late
    Verb cluster: "thinks" — tense=Pres, aspect=None, mood=None
      Sentence: "James Daniel, late on® of tho Judg es of the Cherokee Courts, in the Cherokee nation, aged forty years, has been raised "
    Verb cluster: "Given" — tense=Past, aspect=Perf, mood=None
      Sentence: "Given under m'y hand in the Cherokee nation."
    Verb cluster: "states" — tense=Pres, aspect=None, mood=None
      Sentence: "He fur ther states that he was educated in Green County Georgia, and when there he haS frequently heard the subject of t"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.989

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'James Daniel' and 'Appalachy' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'James Daniel' near 'Appalachy' around 1830-05-15?
  4. Resolve temporal expressions relative to 1830-05-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 109:
  Publication date : 1820-09-09
  Language         : en
  Person  : 'ROB. MOORE'  (QID: N/A)
  Location: 'Maryland'  (QID: Q1391)

  [ARTICLE TEXT — entity markers added]
  "Eastern Shore of [E2] Maryland [/E2]. 1 am anxious to preserve the whole of the work, and wish it was in the hands of every lamer in the United States. It is by the diffusion of knowle dge only, that we can expect our country to improve in Agricul ture, which thy paper is admirably calcula ted to impart, to all who will take pains to be improved by reading.” Respectfully th friend, ROB."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Maryland
    Description: state of the United States of America
    Country: ['United States']
    Located in: ['United States']
    Aliases: {'en': ['State of Maryland', 'Maryland, United States', 'MD', 'Md.', 'Old Line State', 'US-MD']}
    Coordinates: [{'lat': 39, 'lon': -76.7}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 18 (0 = most prominent)
    OCR quality estimate: 0.989

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'ROB. MOORE' and 'Maryland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'ROB. MOORE' near 'Maryland' around 1820-09-09?
  4. Resolve temporal expressions relative to 1820-09-09. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 110:
  Publication date : 1950-09-23
  Language         : en
  Person  : 'Horace Sudduth'  (QID: N/A)
  Location: 'Birming\nham, Ala.'  (QID: Q79867)

  [ARTICLE TEXT — entity markers added]
  "[E1] Horace Sudduth [/E1]. president of the National Negro Business League stated in his address to the Business and Housewives League; ‘ There is nothing that will build our neighborhood business es on a competitive basis faster than the program that has been carried on by the Housewives League for the past 17 years. Among the guests were: Mrs. H. F. Thomas. Birming ham, Ala., a rug and mattress manufacturer; and Mrs. Freddvo S Henderson."

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
    Entity sentence position in article: 11 (0 = most prominent)
    OCR quality estimate: 0.998

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Horace Sudduth' and 'Birming\nham, Ala.' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Horace Sudduth' near 'Birming\nham, Ala.' around 1950-09-23?
  4. Resolve temporal expressions relative to 1950-09-23. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 111:
  Publication date : 1858-02-24
  Language         : de
  Person  : 'Louis Napoleon'  (QID: Q7721)
  Location: 'L rnnburg'  (QID: Q32)

  [ARTICLE TEXT — entity markers added]
  "Auf die Bourboncn folgte die Pöbelherrschaft, auf diese Napoleons l. Gewaltregiment, dieser wurde dann wieder durch die Bourbonen verdrängt, deren Regierungsfähig» keit in der Thai erloschen schien, als Ludwig Phil» livpe sie mit einem Hauche vom Throne blasen konnte, um achtzehn Jahre später noch schmählicher gestürzt zu werden! Nach ihm, der nichts gethan, mn Frankreich moralisch zu heben, — worin doch die einzige Stütze seiner Monarchie bestand, —nach ihm sehen wir wieder die Pöbelherrschaft im wilde» sten Auswüchse, wir sehen die Nepublick gegen ihre eigenen Ultras die blutigsten Straßenkampfe führen, Ins zuletzt Napoleon !11. abermals über Nacht dem ein Ende und sich zum Herrscher Frankreichs machte. Zeitung" geriren wollte; wir entnehmen das daraus, daß er die Assisen« und (Zerichtver» Handlungen in [E2] L rnnburg [/E2] berichtet, wie denn auch^ daß er die unten stehende Erklärung über die Eisenbahnfrage abgegeben hat."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Napoleon III.
    Description: französischer Staatspräsident, Kaiser der Franzosen (1808–1873)
    Born: ['+1808-04-20T00:00:00Z']
    Died: ['+1873-01-09T00:00:00Z']
    Birth place: ['Paris']
    Death place: ['Chislehurst']
    Work locations: ['Paris']
  Location Wikidata:
    Label: Luxemburg
    Description: Staat in Westeuropa
    Country: ['Luxemburg']
    Aliases: {'en': ['Luxemburg', 'Grand Duchy of Luxembourg'], 'fr': ['Grand-Duché de Luxembourg', 'Grand-duché de Luxembourg', 'grand-duché de Luxembourg', 'le Grand-Duché de Luxembourg', 'Lux.'], 'de': ['Groussherzogtum Lëtzebuerg', 'Grand-Duché de Luxembourg', 'Luxembourg'], 'lb': ['Groussherzogtum Lëtzebuerg', 'Lëtzebuerger Land', 'Grand-Duché de Luxembourg', 'Grand-Duché']}
    Coordinates: [{'lat': 49.77, 'lon': 6.13}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, spät
    Verb cluster: "folgte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Auf die Bourboncn folgte die Pöbelherrschaft, auf diese Napoleons l. Gewaltregiment, dieser wurde dann wieder durch die "
    Verb cluster: "sehen" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Nach ihm, der nichts gethan, mn Frankreich moralisch zu heben, — worin doch die einzige Stütze seiner Monarchie bestand,"
    Verb cluster: "entnehmen" — tense=Pres, aspect=None, mood=Ind
      Sentence: "wir entnehmen das daraus, daß er die Assisen« und (Zerichtver» Handlungen in L rnnburg berichtet, wie denn auch^ daß er "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 5 (0 = most prominent)
    OCR quality estimate: 0.990

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Louis Napoleon' and 'L rnnburg' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Louis Napoleon' near 'L rnnburg' around 1858-02-24?
  4. Resolve temporal expressions relative to 1858-02-24. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 112:
  Publication date : 1808-09-01
  Language         : fr
  Person  : 'F. COREVOïT, greffier'  (QID: N/A)
  Location: 'Yverdon'  (QID: Q63946)

  [ARTICLE TEXT — entity markers added]
  "La Commission du bénéfice d'inventaire de la succès »' _sion dû voitnrier Louis Floquet, donne avis par les présentes, que le Mardi 6 Septembre prochain, à neuf heures du matin, sur la place d'[E2] Yverdon [/E2], on _exposera en vente par voie d'enchère publique et aux conditions qui seront lues, quaire voitures _, deux chars-à- bancs, dont l'un est couvert, un grand et fort char de routier, harnois et autres objets de l'attirail de voilurier. Donné à _Yveidon, le _ï 3 Août 3 * 08.. AUBERJOSOIS, président. 25. F."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Yverdon-les-Bains
    Description: ville et commune du canton de Vaud en Suisse
    Country: ['Q39']
    Located in: ['Q683542', 'Q660762']
    Aliases: {'en': ['Yverdon', 'Yverdon-les-Bains VD'], 'fr': ['Yverdun', 'Eburodunum', 'Yverdon'], 'de': ['Iferten', 'Ifferten', 'Bad Ifferten', 'Bad Iferten', 'Yverdon', 'Yverdon-les-Bains VD']}
    Coordinates: [{'lat': 46.7785, 'lon': 6.6408333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: né à
    Verb cluster: "dû" — tense=Past, aspect=None, mood=None
      Sentence: "La Commission du bénéfice d'inventaire de la succès »' _sion dû voitnrier Louis Floquet, donne avis par les présentes, q"
    Verb cluster: "Donné" — tense=Past, aspect=None, mood=None
      Sentence: "Donné à _Yveidon, le _ï 3 Août 3 * 08.."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 48 (0 = most prominent)
    OCR quality estimate: 0.952

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'F. COREVOïT, greffier' and 'Yverdon' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'F. COREVOïT, greffier' near 'Yverdon' around 1808-09-01?
  4. Resolve temporal expressions relative to 1808-09-01. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 113:
  Publication date : 1892-07-05
  Language         : de
  Person  : 'L . Sonnenfeld'  (QID: N/A)
  Location: 'Berliner'  (QID: Q64)

  [ARTICLE TEXT — entity markers added]
  "Handels⸗ Zeitung des [E2] Berliner [/E2] Tageblatts . Nummer 335 . F . Flach und der Kaufmann ſind L ."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 117 (0 = most prominent)
    OCR quality estimate: 0.975

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'L . Sonnenfeld' and 'Berliner' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'L . Sonnenfeld' near 'Berliner' around 1892-07-05?
  4. Resolve temporal expressions relative to 1892-07-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 114:
  Publication date : 1840-04-18
  Language         : en
  Person  : 'Harri\nson'  (QID: Q11869)
  Location: 'Baltimore'  (QID: Q5092)

  [ARTICLE TEXT — entity markers added]
  "The party in [E2] Baltimore [/E2] drop the darling name of “ whig ” and send out a general address to their friends in the whole Union as “ Democrats .” The term Democrat, which they have always ridiculed, and abused because it i 3 every where claimed by]Mr. "NVe see in an opposition paper, a whig address from Baltimore, to “the young men of the United States,” headed “your DEMOCRATIC Harrison brethren of Baltimore send you this address, greet ing.” In one part of the “address,” these Harri son Democrats of Baltimore, (brother ichigs of the Obseiver) say “from your ranks are to come the future rulers of thejland, makinglyou the guardians, in the western world of tru e Democracy!"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: William Henry Harrison
    Description: president of the United States in 1841
    Born: ['+1773-02-09T00:00:00Z']
    Died: ['+1841-04-04T00:00:00Z']
    Birth place: ['Charles City County']
    Death place: ['Washington, D.C.', 'White House']
    Residences: ['North Bend', 'Grouseland']
    Work locations: ['Washington, D.C.', 'Fort Washington', 'Vincennes', 'Bogotá', 'Cincinnati']
  Location Wikidata:
    Label: Baltimore
    Description: city in Maryland, United States
    Country: ['United States']
    Located in: ['Maryland', 'Province of Maryland']
    Aliases: {'en': ['Baltimore, Maryland', 'City of Baltimore', 'Baltimore City', 'Charm City', 'B more', 'Bmore', 'Baltimore, MD', 'Balt.', 'BAL', "B'more"], 'fr': ['municipalité de Baltimore City']}
    Coordinates: [{'lat': 39.286388888889, 'lon': -76.615}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "say" — tense=Pres, aspect=None, mood=None
      Sentence: "In one part of the “address,” these Harri son Democrats of Baltimore, (brother ichigs of the Obseiver) say “from your ra"
    Verb cluster: "headed" — tense=Past, aspect=None, mood=None
      Sentence: ""NVe see in an opposition paper, a whig address from Baltimore, to “the young men of the United States,” headed “your DE"
    Verb cluster: "drop" — tense=Pres, aspect=None, mood=None
      Sentence: "The party in Baltimore drop the darling name of “ whig ” and send out a general address to their friends in the whole Un"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 9 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Harri\nson' and 'Baltimore' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Harri\nson' near 'Baltimore' around 1840-04-18?
  4. Resolve temporal expressions relative to 1840-04-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 115:
  Publication date : 1961-12-21
  Language         : fr
  Person  : 'Anquetil'  (QID: N/A)
  Location: 'Herentals'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Mais on veut donc faire gagner à tout prix [E1] Anquetil [/E1] ? Si c'est comme cela, je déclare forfait...* La prise de position du champion belge ne nanqua pas de surprendre désagréablement les organisateurs. Personnellement, j'estime que quatre étapes contre le chronomètre nuisent à l'intérêt général d'un Tour. Quant à l'étape contre la montre par équipes, organisée par hasard à [E2] Herentals [/E2], le village de Rilc van Looy, c'est une mauvaise plaisanterie que l'on aurait souhaité ne plus revoir dans une épreuve de l'importance du Tour."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Verb cluster: "veut" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Mais on veut donc faire gagner à tout prix Anquetil ?"
    Verb cluster: "est plaisanterie" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Quant à l'étape contre la montre par équipes, organisée par hasard à Herentals, le village de Rilc van Looy, c'est une m"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 6 (0 = most prominent)
    OCR quality estimate: 0.988

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Anquetil' and 'Herentals' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Anquetil' near 'Herentals' around 1961-12-21?
  4. Resolve temporal expressions relative to 1961-12-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 116:
  Publication date : 1908-01-07
  Language         : fr
  Person  : 'colonel\nBoutégoûrd'  (QID: Q3425922)
  Location: 'Mediouna'  (QID: Q2254188)

  [ARTICLE TEXT — entity markers added]
  "Nos troupes sont rentrées à Casablanca, laissant à lakasbades [E2] Mediouna [/E2] un bataillon d'infanterie, un escadron d'artillerie, deux sections de mitrailleuses et un peloton de « avalerie. : ^-" W' A là date du 5 janvier, le colonel Boutégoûrd"

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "rentrées" — tense=Past, aspect=None, mood=None
      Sentence: "Nos troupes sont rentrées à Casablanca, laissant à lakasbades Mediouna un bataillon d'infanterie, un escadron d'artiller"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 11 (0 = most prominent)
    OCR quality estimate: 0.990

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'colonel\nBoutégoûrd' and 'Mediouna' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'colonel\nBoutégoûrd' near 'Mediouna' around 1908-01-07?
  4. Resolve temporal expressions relative to 1908-01-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 117:
  Publication date : 1981-07-25
  Language         : fr
  Person  : 'George'  (QID: N/A)
  Location: 'France'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "FRANCE : ANTENNE 2 10.10 12.30 12.45 13.35 14.00 18.00 18.50 19.20 19.45 20.00 20.35 22.10 23.30 A 2 Antiope Le Sénégal Les jeux du stade-Tennis : Coupe de Galéa, demi-finales dames à Monte-CarloCyclisme : Championnat de [E2] France [/E2] sur pisteHippisme : King [E1] George [/E1] Horse Show"

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
  1. What is the relationship between 'George' and 'France' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'George' near 'France' around 1981-07-25?
  4. Resolve temporal expressions relative to 1981-07-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 118:
  Publication date : 1890-09-25
  Language         : en
  Person  : 'M. Pliillippe de Ferrari'  (QID: Q44105)
  Location: 'Africa'  (QID: Q15)

  [ARTICLE TEXT — entity markers added]
  "The museum of the Berlin post-cfllce alone contains a collection of between 4,000 and 5,000 specimens, half of which are European and the remain der divided between tbe Americans, Asia, [E2] Africa [/E2] and Australia. The emblems upon the stamps of nations are legion; the earth, the sea and the vaulted canopy above have been ransacked for curious and mraning less devices and legends. The en tire animal kingdom, the stars and the moon iu all its phases, besides legendary emblems by the thousand, are known to the oollLctors of stamps, who pride themselves upon being “philatelists.” Upon the printed faces of these little squares of paper may be fonri*} the fogies of five em perors, eighteen kings,three q icens, one grand duke, several inferior tilled rulcr9 and many presidents. [E1] M. Pliillippe de Ferrari [/E1] perhaps has the largest and most valuable collec tion of stamps in the world, amount ing to something like 2ft0,000, and within tbe present year he solJ one little stamp to a collector in Paris for 150.000."

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
    Label: Africa
    Description: continent
    Aliases: {'en': ['African continent'], 'fr': ['continent africain'], 'de': ['afrikanischer Kontinent']}
    Coordinates: [{'lat': 21.09375, 'lon': 7.1881}, {'lat': 0, 'lon': 15}]
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
  1. What is the relationship between 'M. Pliillippe de Ferrari' and 'Africa' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Pliillippe de Ferrari' near 'Africa' around 1890-09-25?
  4. Resolve temporal expressions relative to 1890-09-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 119:
  Publication date : 1928-01-17
  Language         : fr
  Person  : 'Gédéon le Contreleyu'  (QID: N/A)
  Location: 'Etang'  (QID: Q2721193)

  [ARTICLE TEXT — entity markers added]
  "Matthey de l'[E2] Etang [/E2] ( Matthey de la Gouille , comme l' appelaient ses amis) avait passé la majeure partie de g. vie dans cette vallée jurassienne où dans lés temps anciens vécurent (?) le Solitaire dès Sagnes et [E1] Gédéon le Contreleyu [/E1]."

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
    Temporal signal words: ancien
    Verb cluster: "appelaient" — tense=Pres, aspect=None, mood=Sub
      Sentence: "Matthey de l'Etang ( Matthey de la Gouille , comme l' appelaient ses amis) avait passé la majeure partie de g. vie dans "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 1 (0 = most prominent)
    OCR quality estimate: 0.981

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Gédéon le Contreleyu' and 'Etang' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Gédéon le Contreleyu' near 'Etang' around 1928-01-17?
  4. Resolve temporal expressions relative to 1928-01-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 120:
  Publication date : 1868-02-19
  Language         : de
  Person  : 'Georg'  (QID: Q57428)
  Location: 'Deutſchland'  (QID: Q183)

  [ARTICLE TEXT — entity markers added]
  "digt : überall in [E2] Deutſchland [/E2] und über deſſen Grenzen hinaus richtet ſich die Beachtung und Anerkennung der Regierung und der Völker auf das Verfahren Preußens in den eroberten Provinzen . Die bedeutſamſten Stimmen aus Süddeutſchland ver⸗ zu dieſer Berathung herbeigekommen und von 141 Anweſenden baben 127 ihre Zuſtimmung zu der Vorlage ertheilt ; Es bewährt ſich hierin , Jndem das Herrenhaus durch ſeinen jüngſten Beſchluß von Neuem mit vollſter Entſchiedenheit für dieſe Politik eingetreten iſt , hat daſſelbe zugleich die Zuverſicht erhöht , daß die konſervative Partei Die ſogenaunte Hannoverſche Legion . Aufenthalt in Hietzing , die Regierung dann verpflichtet ſein wird , das Während die preußiſche Regierung dem früheren König von Hannover die größte und edelſte Rückſicht zu Theil werden läßt , während andererſeits ihre Fürſorge für die neue Provinz unter der be — des Königs [E1] Georg [/E1] und ſeiner Umgebung in Hietzing die verwerflichen Verſuche fortgeſetzt , einen Theil ſeiner früheren Unterthanen , meiſt aus den unterſten Ständen , für das völlige boffnungsloſe und thörichte Unternehmen einer Wiederherſtellung ſeines Thrones zu gewinnen ."

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
    Label: Deutschland
    Description: Staat in Mitteleuropa
    Country: ['Deutschland']
    Aliases: {'en': ['Federal Republic of Germany'], 'fr': ['RFA', "République fédérale d'Allemagne", 'République fédérale allemande', 'la République fédérale d’Allemagne', 'All.', 'R. F. A.'], 'de': ['Bundesrepublik Deutschland', 'BR Deutschland']}
    Coordinates: [{'lat': 51, 'lon': 10}, {'lat': 51.5, 'lon': 10.5}]
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
  1. What is the relationship between 'Georg' and 'Deutſchland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Georg' near 'Deutſchland' around 1868-02-19?
  4. Resolve temporal expressions relative to 1868-02-19. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 121:
  Publication date : 1920-04-22
  Language         : en
  Person  : 'Mansfield Judd'  (QID: N/A)
  Location: 'GAINESBORO'  (QID: Q2057053)

  [ARTICLE TEXT — entity markers added]
  "[E2] GAINESBORO [/E2], ROUTE 3 Reckon Tiui Apple Is still living as I beard him the other night talk ing to some one about a law suit. Old Tim is a good lawyer and a hustler in the courts. I guess I had better wind up by saying, Ralph Wirt, you will please send me the Putnam County Herald three months, Gainesboro, Tenn., R. 3, as the Herald is a hustling paper and the men who run it are, too. Say, [E1] Mansfield Judd [/E1], do you still read and play checkers as much as you used to?"

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
    Verb cluster: "do read" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Say, Mansfield Judd, do you still read and play checkers as much as you used to?"
    Verb cluster: "Is living" — tense=Pres, aspect=Prog, mood=Ind
      Sentence: "GAINESBORO, ROUTE 3 Reckon Tiui Apple Is still living as I beard him the other night talk ing to some one about a law su"
    Verb cluster: "guess" — tense=Pres, aspect=None, mood=None
      Sentence: "I guess I had better wind up by saying, Ralph Wirt, you will please send me the Putnam County Herald three months, Gaine"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 19 (0 = most prominent)
    OCR quality estimate: 0.992

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mansfield Judd' and 'GAINESBORO' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mansfield Judd' near 'GAINESBORO' around 1920-04-22?
  4. Resolve temporal expressions relative to 1920-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 122:
  Publication date : 1810-04-14
  Language         : en
  Person  : 'J. li. Varniim.\nSpeaker of the House of Representatives'  (QID: Q1706673)
  Location: 'Sciota'  (QID: Q209540)

  [ARTICLE TEXT — entity markers added]
  "B E it enacted by the Senate and House §f Representatives o f the United States of America, in Congress assembled, That the officers and soldiers of the Virginia line on continental establishment, their heirs or as signs entitled to bounty lands within the tract reserved by Virginia, between the lit tle Miami and [E2] Sciota [/E2] rivers, for satisfying the legal bounties to her officers and soldi ers upon continental establishment, shall be allowed a further term of five years, from and after the passage of this act, to obtain warrants and complete their locations, and a further term of seven years, from and as ter the passage of this act as aforesaid, to return their surveys and warrants to the of sice of the Secretary of the War Depart ment, any thing in any former act to the contrary notwithstanding- Provided , That no locations as aforesaid within the above mentioned tract shall after the passing of this act he made on tracts of land for which patents had previously been issued or which had been previously surveyed, and any pa tent which may nevertheless be obtained for land located contrary to the provisions of this section, shall be considered as null and void. J. li."

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
    Label: Scioto River
    Description: river in Ohio
    Country: ['United States']
    Located in: ['Ohio']
    Aliases: {'fr': ['Scioto River']}
    Coordinates: [{'lat': 40.556944444444, 'lon': -83.930277777778}, {'lat': 38.730277777778, 'lon': -83.013055555556}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after
    Verb cluster: "assembled" — tense=Past, aspect=None, mood=None
      Sentence: "B E it enacted by the Senate and House §f Representatives o f the United States of America, in Congress assembled, That "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.989

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'J. li. Varniim.\nSpeaker of the House of Representatives' and 'Sciota' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'J. li. Varniim.\nSpeaker of the House of Representatives' near 'Sciota' around 1810-04-14?
  4. Resolve temporal expressions relative to 1810-04-14. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 123:
  Publication date : 1928-10-25
  Language         : fr
  Person  : 'B.'  (QID: N/A)
  Location: 'canton de Vaud'  (QID: Q12771)

  [ARTICLE TEXT — entity markers added]
  "La géographie électorale et ses aspects A LA VEILLE DU SCRUTIN (Correspondance particulière) Berne, le 24 octobre. Nous avons longuement exposé, lundi. Cette nouvelle constellation électorale pourrait bien enregistrer d'emblée un premier succès, nutis nul ne peut prédire si le siège conquis sera enlevé au parti majoritaire ou aux radicaux. Les choses semblent devoir se passer beau coup plus calmement dans le [E2] canton de Vaud [/E2], où aucun changement notable n'est prévu, et à Genève, où l'on s'attend généralement à un déchet démocrate en faveur du parti de défense économique."

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
    Verb cluster: "semblent" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Les choses semblent devoir se passer beau coup plus calmement dans le canton de Vaud, où aucun changement notable n'est "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.982

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'B.' and 'canton de Vaud' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'B.' near 'canton de Vaud' around 1928-10-25?
  4. Resolve temporal expressions relative to 1928-10-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 124:
  Publication date : 1878-10-02
  Language         : de
  Person  : 'Fröbel'  (QID: Q76679)
  Location: 'Portugal'  (QID: Q45)

  [ARTICLE TEXT — entity markers added]
  "— Mailand stellt Arbeiten der [E1] Fröbel [/E1]schulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die Kinder weit überschreiten: soll das Kinderarbeit sein; soll das zarteste Jugendalter mit solch difficilen und feinen Aufgaben beglückt werden? Wahrlich, Fröbel, Deine An hänger sind größer als Du, so groß, daß selbst Du ihnen nicht mehr folgen könntest und ihnen mit Macht zurufen würdest: Bleibt bei der Natur, lernet erst die Jugend kennen! Spanien macht keinen Versuch, eine Ausstellung zu arrangiren, dagegen hat [E2] Portugal [/E2] Schülerarbeiten und das Modell einer Volksschule nach Paris gesandt."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Portugal
    Description: Staat in Südwesteuropa
    Country: ['Portugal']
    Aliases: {'en': ['Portuguese Republic', 'PRT', 'POR'], 'fr': ['République portugaise'], 'de': ['Portugiesische Republik', 'PRT']}
    Coordinates: [{'lat': 38.7, 'lon': -9.183333333333334}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nicht mehr, nach
    Verb cluster: "stellt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "— Mailand stellt Arbeiten der Fröbelschulen aus, die aber die Grenze des Zulässigen betreffend Ausführbarkeit durch die "
    Verb cluster: "macht" — tense=Pres, aspect=None, mood=Ind [NEGATED]
      Sentence: "Spanien macht keinen Versuch, eine Ausstellung zu arrangiren, dagegen hat Portugal Schülerarbeiten und das Modell einer "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 27 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Fröbel' and 'Portugal' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Fröbel' near 'Portugal' around 1878-10-02?
  4. Resolve temporal expressions relative to 1878-10-02. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 125:
  Publication date : 1868-04-22
  Language         : fr
  Person  : "Sir Strafford\nNorlhcole, secrétaire d'Elat des colonies"  (QID: Q332650)
  Location: 'Grande-Bretagne'  (QID: Q145)

  [ARTICLE TEXT — entity markers added]
  "[E2] Grande-Bretagne [/E2]. —Sir Strafford Norlhcole, secrétaire d'Elat des colonies, a reçu de sir Robert Napier la dépêche suivante, en dale de Lait, le 23 mars :"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Stafford Northcote
    Description: politicien britannique
    Born: ['+1818-10-27T00:00:00Z']
    Died: ['+1887-01-12T00:00:00Z']
    Birth place: ['Londres']
    Death place: ['Londres']
    Work locations: ['Londres']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "reçu" — tense=Past, aspect=None, mood=None
      Sentence: "—Sir Strafford Norlhcole, secrétaire d'Elat des colonies, a reçu de sir Robert Napier la dépêche suivante, en dale de La"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 3 (0 = most prominent)
    OCR quality estimate: 0.983

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between "Sir Strafford\nNorlhcole, secrétaire d'Elat des colonies" and 'Grande-Bretagne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing "Sir Strafford\nNorlhcole, secrétaire d'Elat des colonies" near 'Grande-Bretagne' around 1868-04-22?
  4. Resolve temporal expressions relative to 1868-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 126:
  Publication date : 1928-02-17
  Language         : de
  Person  : 'Gertrud'  (QID: N/A)
  Location: 'Schloßberg'  (QID: Q2244426)

  [ARTICLE TEXT — entity markers added]
  "Ein Lichtblick: Lienhard und [E1] Gertrud [/E1] gerät. Lange interessierte darin Arner am meisten. Stans grüßt ihn, brennend nach Betä tigung und Erweisung seines Wertes. Vom Hin tersässenschulmeister am [E2] Schloßberg [/E2] steigt er auf zum Seminardirektor auf dem Schloß Burgdorf."

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
    Temporal signal words: nach
    Verb cluster: "gerät" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Ein Lichtblick: Lienhard und Gertrud gerät."
    Verb cluster: "steigt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Vom Hin tersässenschulmeister am Schloßberg steigt er auf zum Seminardirektor auf dem Schloß Burgdorf."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 19 (0 = most prominent)
    OCR quality estimate: 0.996

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Gertrud' and 'Schloßberg' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Gertrud' near 'Schloßberg' around 1928-02-17?
  4. Resolve temporal expressions relative to 1928-02-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 127:
  Publication date : 1868-06-16
  Language         : de
  Person  : 'Goldschmied'  (QID: N/A)
  Location: 'Winterthur'  (QID: Q9125)

  [ARTICLE TEXT — entity markers added]
  "Hüni in Riesbach und [E1] Goldschmied [/E1] in [E2] Winterthur [/E2] werden für eine neue Amtsdauer als Kreis ingenieure bestätigt. Zum Pfarrverweser in Fischenthal wird Hr. E. Wink ler, V. D. M., ernannt. Der Große Rath wird in seiner nächsten Sitzung sich ausschließlich mit Wahlen zu beschäftigen haben. Die Hälfte des Regierungsrathes unterliegt einer Neuwahl. — (Mitgetheilt.) Der „Landbote" macht von der Er klärung Mittheilung, welche „die Nordostbahn betreffend „den von der Gemeinde Winterthur beschlossenen unter „irdischen Durchgang durch den dortigen Bahnhof zur „Verbindung mit dem Neuwiesenquartiere" abgegeben habe."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Winterthur
    Description: Stadt im Kanton Zürich, Schweiz
    Country: ['Schweiz']
    Located in: ['Bezirk Winterthur']
    Aliases: {'en': ['Winterthur ZH'], 'fr': ['Winterthur']}
    Coordinates: [{'lat': 47.4992, 'lon': 8.72671}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "werden" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Hüni in Riesbach und Goldschmied in Winterthur werden für eine neue Amtsdauer als Kreis ingenieure bestätigt."
    Verb cluster: "macht" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Der „Landbote" macht von der Er klärung Mittheilung, welche „die Nordostbahn betreffend „den von der Gemeinde Winterthur"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.990

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Goldschmied' and 'Winterthur' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Goldschmied' near 'Winterthur' around 1868-06-16?
  4. Resolve temporal expressions relative to 1868-06-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 128:
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
Sample 129:
  Publication date : 1920-04-22
  Language         : en
  Person  : 'Lon Morelock'  (QID: N/A)
  Location: 'Silver Point'  (QID: Q7516246)

  [ARTICLE TEXT — entity markers added]
  "Say, you [E2] Silver Point [/E2] guys, Casto Jditchell. [E1] Lon Morelock [/E1], every Jones of the name and others down around there, how is every one of my old customers?"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Silver Point
    Description: human settlement in Putnam County, Tennessee, United States of America
    Country: ['United States']
    Located in: ['Putnam County']
    Aliases: {'en': ['Silver Point, Tennessee', 'Silver Point, TN']}
    Coordinates: [{'lat': 36.0906, 'lon': -85.7297}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "Say" — tense=None, aspect=None, mood=None
      Sentence: "Say, you Silver Point guys, Casto Jditchell."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 10 (0 = most prominent)
    OCR quality estimate: 0.992

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Lon Morelock' and 'Silver Point' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Lon Morelock' near 'Silver Point' around 1920-04-22?
  4. Resolve temporal expressions relative to 1920-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 130:
  Publication date : 1874-08-25
  Language         : de
  Person  : 'R . Wentzel'  (QID: N/A)
  Location: 'Schleſten'  (QID: Q81720)

  [ARTICLE TEXT — entity markers added]
  "die Firma M . Oppenheim ' s Söhne und der Gebeime Gommiſflonsratb [E1] R . Wentzel [/E1] . Dieier Zeitvunkt dürfte min nicht mehr ferne ſein , da die Geſchaͤfte der Geſellſchaft in letzter Zeit einen ſehr erfreulichen Auiſchwung genommen baben . So wnd und gemeldet , datz die Kefſelſchmiede der Gefenſ Gaft in [E2] Schleſten [/E2] dieler Tage Auftraͤge im Betrage von 250 00 Eutr ."

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
    Verb cluster: "gemeldet" — tense=None, aspect=None, mood=None
      Sentence: "So wnd und gemeldet , datz die Kefſelſchmiede der Gefenſ Gaft in Schleſten dieler Tage Auftraͤge im Betrage von 250 00 E"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 8 (0 = most prominent)
    OCR quality estimate: 0.973

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'R . Wentzel' and 'Schleſten' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'R . Wentzel' near 'Schleſten' around 1874-08-25?
  4. Resolve temporal expressions relative to 1874-08-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 131:
  Publication date : 1878-02-06
  Language         : de
  Person  : 'General Diebitsch'  (QID: Q703307)
  Location: 'Konstantinopel'  (QID: Q16869)

  [ARTICLE TEXT — entity markers added]
  "Von dem Augenblick an, wo die Russen [E2] Konstantinopel [/E2] und die Dardanellenstraße nicht mehr direkt bedrohen, wird das englische Kabinet sich be friedigt erklären. Wer weiß, ob die Nachricht vom Abschluß des Waffenstillstandes nicht die Autorität der Regierung in der Diskussion der Supplementar kredite schwächt? Deutschland ist ja der treueste Alliirte Rußlands und wir sind überzeugt, daß Rußland selbst die Beendigung der Feindselig keiten wünscht. Mit großer Anstrengung führten sie diesen kühnen, abenteuerlichen Marsch über den Balkan und gegen Konstantinopel aus, der lebhaft an die berühmte Operation des [E1] General Diebitsch [/E1] im Jahr 1829 erinnert."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Hans Karl von Diebitsch-Sabalkanski
    Description: kaiserlich-russischer Feldmarschall (1785–1831)
    Born: ['+1785-05-13T00:00:00Z']
    Died: ['+1831-05-29T00:00:00Z', '+1831-06-10T00:00:00Z']
    Birth place: ['Q669807', 'Groß Leipe']
    Death place: ['Q548922', 'Q6420698']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1829" → 1829
    Temporal signal words: nicht mehr, nach
    Verb cluster: "führten" — tense=Past, aspect=None, mood=Ind
      Sentence: "Mit großer Anstrengung führten sie diesen kühnen, abenteuerlichen Marsch über den Balkan und gegen Konstantinopel aus, d"
    Verb cluster: "wird" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Von dem Augenblick an, wo die Russen Konstantinopel und die Dardanellenstraße nicht mehr direkt bedrohen, wird das engli"
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 49 days
    Entity sentence position in article: 26 (0 = most prominent)
    OCR quality estimate: 0.999

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'General Diebitsch' and 'Konstantinopel' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'General Diebitsch' near 'Konstantinopel' around 1878-02-06?
  4. Resolve temporal expressions relative to 1878-02-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 132:
  Publication date : 1826-09-29
  Language         : fr
  Person  : 'don Nazàrio-Eguia'  (QID: N/A)
  Location: 'Galice'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Le ministère est positivement informa par les rapports officiels des gouverneurs d'Estramadure et de [E2] Galice [/E2], que la désertion a jusqu'à ce jour enlevé à l'armée espagnole 3400 hommes, " dont 2000 sont entrés'ehPortugal par l'Estramadure portugaise, qu'on nomme l'Alentejo, et 1400 par la province de Tras-los-Montès. La première de ces deux colonnes s'est présentée au'gouverneur -de Jelvès, et'la deuxième à celui de Chaves, qui'ont aussitôt demandé des ordres à leur gouvernement. Heureusement que ce capitaine-général est un homme ferme et habile, et dont le dévouement est garanti par des preuves de fidélité. C'est [E1] don Nazàrio-Eguia [/E1]..."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "3400" → 3400
      - "2000" → 2000
      - "1400" → 1400
    Temporal signal words: tôt
    Verb cluster: "est don" — tense=Pres, aspect=None, mood=Ind
      Sentence: "C'est don Nazàrio-Eguia..."
    Verb cluster: "est positivement" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Le ministère est positivement informa par les rapports officiels des gouverneurs d'Estramadure et de Galice, que la dése"
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 174 days
    Entity sentence position in article: 14 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'don Nazàrio-Eguia' and 'Galice' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'don Nazàrio-Eguia' near 'Galice' around 1826-09-29?
  4. Resolve temporal expressions relative to 1826-09-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 133:
  Publication date : 1920-11-11
  Language         : en
  Person  : 'Current His\ntory'  (QID: Q5195051)
  Location: 'State of New York'  (QID: Q1384)

  [ARTICLE TEXT — entity markers added]
  "The official announcement in August that the [E2] State of New York [/E2] had purchased two grams and a quarter of radium for the free treatment of cancer, begin ning Oct. 15, also to treat other allied malignant diseases, and that this tiny amount of the rare and super precious metal is enough to treat two billion patients, is wonderful statement to be found in an article entitled “Science and Discovery” in the October number of Current His tory."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Current History
    Description: academic journal
  Location Wikidata:
    Label: New York
    Description: state of the United States of America
    Country: ['United States']
    Located in: ['United States']
    Aliases: {'en': ['NY', 'New York, United States', 'State of New York', 'NYS', 'New York (state)', 'NY state', 'New York state', 'The Empire State', 'US-NY', 'Empire State'], 'fr': ['NY', 'NYS', 'État de New York', "État de l'Empire"], 'de': ['Empire State', 'New York Staat', 'Staat New York', 'New York State', 'State of New York', 'NY', 'US-NY']}
    Coordinates: [{'lat': 43, 'lon': -75}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "begin" — tense=Pres, aspect=None, mood=None [NEGATED]
      Sentence: "The official announcement in August that the State of New York had purchased two grams and a quarter of radium for the f"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.998

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Current His\ntory' and 'State of New York' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Current His\ntory' near 'State of New York' around 1920-11-11?
  4. Resolve temporal expressions relative to 1920-11-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 134:
  Publication date : 1900-06-26
  Language         : en
  Person  : 'N. B. Scott'  (QID: Q1966467)
  Location: 'Indiana'  (QID: Q1415)

  [ARTICLE TEXT — entity markers added]
  "Just before the adjournment of the national committee, on motion of Sena tor Scott of West Virginia, George Wls- woll of Milwaukee was unanimously elected sergeant-at arms of tin* nation al committee for four years. In the | place of II. Maine: [E1] N. B. Scott [/E1], West Virginia; Harry I >. New, [E2] Indiana [/E2], and George L. Slump."

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
    Label: Indiana
    Description: state of the United States of America
    Country: ['United States']
    Located in: ['United States']
    Aliases: {'en': ['IN', 'Indiana, United States', 'State of Indiana', 'US-IN', 'Hoosier State', 'Ind.'], 'fr': ["État d'Indiana"], 'de': ['Hoosier State', 'US-IN', 'US-Bundesstaat Indiana']}
    Coordinates: [{'lat': 39.933333333333, 'lon': -86.216666666667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: before
    Verb cluster: "was elected" — tense=Past, aspect=Perf, mood=Ind
      Sentence: "Just before the adjournment of the national committee, on motion of Sena tor Scott of West Virginia, George Wls- woll of"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 12 (0 = most prominent)
    OCR quality estimate: 0.982

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'N. B. Scott' and 'Indiana' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'N. B. Scott' near 'Indiana' around 1900-06-26?
  4. Resolve temporal expressions relative to 1900-06-26. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 135:
  Publication date : 2018-01-03
  Language         : fr
  Person  : 'Simon'  (QID: N/A)
  Location: 'Bulgarie'  (QID: Q219)

  [ARTICLE TEXT — entity markers added]
  "A l’entrée en [E2] Bulgarie [/E2] : « La douane se passe fort bien, les douaniers nous demandèrent juste si l’on avait des montres : à notre réponse négative, ils nous dirent que nous étions de mauvais commerçants ». En attendant le dîner, un des sikhs nous apporte un gramophone à manivelle et des disques hindous, et insiste au moins une heure pour que « le Diable » et « [E1] Simon [/E1] » fassent une démonstration de danse de chez nous."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Bulgarie
    Description: pays d’Europe du Sud-Est situé dans les Balkans
    Country: ['Bulgarie']
    Aliases: {'en': ['Republic of Bulgaria'], 'fr': ['Bulg.', 'République de Bulgarie']}
    Coordinates: [{'lat': 42.75, 'lon': 25.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "entrée" — tense=Past, aspect=None, mood=None
      Sentence: "A l’entrée en Bulgarie : «"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 9 (0 = most prominent)
    OCR quality estimate: 1.000

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Simon' and 'Bulgarie' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Simon' near 'Bulgarie' around 2018-01-03?
  4. Resolve temporal expressions relative to 2018-01-03. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 136:
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
Sample 137:
  Publication date : 1938-05-06
  Language         : de
  Person  : 'neuen deutschen Botschafter, Dr. Herbert von\nDirksen'  (QID: Q213954)
  Location: 'Buckinghampalast'  (QID: Q42182)

  [ARTICLE TEXT — entity markers added]
  "empfing am Donnerstag im [E2] Buckinghampalast [/E2] ben neuen deutschen Botschafter, Dr. Herbert von Dirksen, ber ihm sein Beglaubigungsschreiben unb"

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Buckingham Palace
    Description: offizielle Londoner Residenz und Hauptarbeitsplatz des britischen Monarchen
    Country: ['Vereinigtes Königreich']
    Located in: ['City of Westminster']
    Aliases: {'en': ['Buckingham House', 'Buck House'], 'fr': ['Buckingham Palace'], 'de': ['Buckinghampalast', 'Buckingham Palast', 'Buckingham-Palast']}
    Coordinates: [{'lat': 51.501, 'lon': -0.142}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "empfing" — tense=Past, aspect=None, mood=Ind
      Sentence: "empfing am Donnerstag im Buckinghampalast ben neuen deutschen Botschafter, Dr. Herbert von Dirksen, ber ihm sein Beglaub"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.971

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'neuen deutschen Botschafter, Dr. Herbert von\nDirksen' and 'Buckinghampalast' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'neuen deutschen Botschafter, Dr. Herbert von\nDirksen' near 'Buckinghampalast' around 1938-05-06?
  4. Resolve temporal expressions relative to 1938-05-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 138:
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
Sample 139:
  Publication date : 1830-03-03
  Language         : en
  Person  : 'Don Mi-\ngucl'  (QID: N/A)
  Location: 'South Carolina'  (QID: Q1456)

  [ARTICLE TEXT — entity markers added]
  "Intelligencer, printed at Georgetown, in [E2] South Carolina [/E2], will show the extraordinary degre of ex citement which still prevails in that; State, on the subject oftlie Tariff.— It is not pleasant to recur to tl esc things, hut it is in vain to shut the eye eye upon them.— They well know that a sep aration of the Union would be a der.th blow to the Northern Atlantic .sea board, and of course a great injury to tbe interior. But to those who, when— not tri fling, not speculative, but'important, practical lights are taken from us, even the most important of all,- s*“lf-' government—to those who in sucit times shrink Iroin acting, and entrench themselves behind arguments and sen timents which have been in all ages the apology for submission and servi tude; we would recommend to them as a master the beloved Ferdinand, or, better' yet, the amiable Don Mi- gucl."

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
  1. What is the relationship between 'Don Mi-\ngucl' and 'South Carolina' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Don Mi-\ngucl' near 'South Carolina' around 1830-03-03?
  4. Resolve temporal expressions relative to 1830-03-03. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 140:
  Publication date : 1868-02-19
  Language         : de
  Person  : 'von der Heydt'  (QID: Q765327)
  Location: 'Preußens'  (QID: Q38872)

  [ARTICLE TEXT — entity markers added]
  "digt : überall in Deutſchland und über deſſen Grenzen hinaus richtet ſich die Beachtung und Anerkennung der Regierung und der Völker auf das Verfahren [E2] Preußens [/E2] in den eroberten Provinzen . Die bedeutſamſten Stimmen aus Süddeutſchland ver⸗ zu dieſer Berathung herbeigekommen und von 141 Anweſenden baben 127 ihre Zuſtimmung zu der Vorlage ertheilt ; riſchen Unternehmen gegen Preußen anwerben und cuS⸗ Fürſten , welcher preußiſche Unterthanen zu einem kriege — rüſten läßt , nicht gerade als ein Zeichen einer freund . Miniſter [E1] von der Heydt [/E1] ſoeben im Herrenhauſe ausgeſprochen , Jn Bezug auf das Gebahren des Königs Georg hat der Staats⸗ Minister ."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: August von der Heydt
    Description: deutscher Bankier und preußischer Handels- und Finanzminister (1801-1874)
    Born: ['+1801-02-15T00:00:00Z']
    Died: ['+1874-06-13T00:00:00Z']
    Birth place: ['Elberfeld']
    Death place: ['Berlin']
  Location Wikidata:
    Label: Preußen
    Description: Staatswesen (Herzogtum, Königreich, Freistaat), 1525–1947
    Country: ['Preußen']
    Aliases: {'en': ['Prussia (Germany)'], 'fr': ['État prussien', 'Prussienne'], 'de': ['Preussen']}
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "ſoeben" — tense=Past, aspect=None, mood=Ind
      Sentence: "Miniſter von der Heydt ſoeben im Herrenhauſe ausgeſprochen , Jn Bezug auf das Gebahren des Königs Georg hat der Staats⸗ "
    Verb cluster: "richtet" — tense=Pres, aspect=None, mood=Ind
      Sentence: "digt : überall in Deutſchland und über deſſen Grenzen hinaus richtet ſich die Beachtung und Anerkennung der Regierung un"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 44 (0 = most prominent)
    OCR quality estimate: 0.994

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'von der Heydt' and 'Preußens' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'von der Heydt' near 'Preußens' around 1868-02-19?
  4. Resolve temporal expressions relative to 1868-02-19. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 141:
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
Sample 142:
  Publication date : 1938-11-13
  Language         : de
  Person  : 'Siurgenenger'  (QID: N/A)
  Location: 'Rheineck'  (QID: Q69595)

  [ARTICLE TEXT — entity markers added]
  "Der unfaßliche Plan geht nun dahin, aus diesem, das Antlitz der ganzen Gegend prägenden Wasserarm den der Rhein schon vor endlos vielen Jahrhunderten sich selber gegraben hat, eine Wasserrinne mit ein gebundenen Ufern zu machen, die zwischen St. Mar grethen und [E2] Rheineck [/E2] eine Sohlenbreite von nur 16,5 m und zwischen Rheineck und der Mündung eine fast ohne Gefälle durch die Niederung gleitet, zur Linken von schöngeschwungenen Höhenrücken bewacht. Es kommen die Maler, es kommen die Dichter, es kommen die Schulen, denen man ein anspruchslos liebliches und doch unvergeßliches Stück ihrer Heimat vorführen will, und sie alle lernen die Landschaft lieben, die sie empfängt. Leider ist es freilich auch schon das Letzte! Ie: Dand [E1] Siurgenenger [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Rheineck
    Description: Gemeinde im Kanton St. Gallen, Schweiz
    Country: ['Q39']
    Located in: ['Wahlkreis Rheintal']
    Aliases: {'en': ['Rheineck SG'], 'fr': ['Rheineck SG'], 'de': ['Rheineck SG']}
    Coordinates: [{'lat': 47.47005, 'lon': 9.5834}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "geht" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Der unfaßliche Plan geht nun dahin, aus diesem, das Antlitz der ganzen Gegend prägenden Wasserarm den der Rhein schon vo"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 26 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Siurgenenger' and 'Rheineck' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Siurgenenger' near 'Rheineck' around 1938-11-13?
  4. Resolve temporal expressions relative to 1938-11-13. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 143:
  Publication date : 1928-10-25
  Language         : fr
  Person  : 'M. de Rabours'  (QID: N/A)
  Location: 'Berne'  (QID: Q70)

  [ARTICLE TEXT — entity markers added]
  "La géographie électorale et ses aspects A LA VEILLE DU SCRUTIN (Correspondance particulière) [E2] Berne [/E2], le 24 octobre. Nous avons longuement exposé, lundi. Les choses semblent devoir se passer beau coup plus calmement dans le canton de Vaud, où aucun changement notable n'est prévu, et à Genève, où l'on s'attend généralement à un déchet démocrate en faveur du parti de défense économique. C'est [E1] M. de Rabours [/E1] que tous livrent d'avance au fatal couperet de la guillotine sèche."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
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
    Verb cluster: "est M." — tense=Pres, aspect=None, mood=Ind
      Sentence: "C'est M. de Rabours que tous livrent d'avance au fatal couperet de la guillotine sèche."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 16 (0 = most prominent)
    OCR quality estimate: 0.982

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. de Rabours' and 'Berne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. de Rabours' near 'Berne' around 1928-10-25?
  4. Resolve temporal expressions relative to 1928-10-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 144:
  Publication date : 1918-04-22
  Language         : fr
  Person  : 'Cléopâtre\nhelvétique'  (QID: N/A)
  Location: 'N-ûenhoî'  (QID: Q64461)

  [ARTICLE TEXT — entity markers added]
  "[E2] N-ûenhoî [/E2], près Wettingen, 19 avril 1918. Lorsque, un jour, un de mes copains de lège avait à donner la définition du mot « histoire >, il répondit, sans réfléchir longtemps < l'histoire, c'est une chronique d'affaires >. La classe se moqua alors bien de lui et à mon pauvre ami est resté dès lors le sobriquet de < chronique d'affaires >. Mais à présent que j'appartiens dans le pays des Helvètes à cette catégorie privilégiée des gens de la presse, aujourd'hui que je connais depuis de longues années ce que c'est que la politique, je ne ris plus de cette définition. Du moins quand, en parlant de l'histoire suisse, on pense à l'histoire contemporaine sous le régime des pleins pouvoirs, de cette Cléopâtre helvétique."

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
    Temporal signal words: aujourd'hui, plus
    Verb cluster: "pense" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Du moins quand, en parlant de l'histoire suisse, on pense à l'histoire contemporaine sous le régime des pleins pouvoirs,"
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    Entity sentence position in article: 6 (0 = most prominent)
    OCR quality estimate: 0.995

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Cléopâtre\nhelvétique' and 'N-ûenhoî' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Cléopâtre\nhelvétique' near 'N-ûenhoî' around 1918-04-22?
  4. Resolve temporal expressions relative to 1918-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 145:
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

────────────────────────────────────────────────────────────
Sample 146:
  Publication date : 1900-06-26
  Language         : en
  Person  : 'Harry I >. New'  (QID: Q1586757)
  Location: 'Maine'  (QID: Q724)

  [ARTICLE TEXT — entity markers added]
  "[E2] Maine [/E2]: N. B. Scott, West Virginia; Harry I >."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Harry Stewart New
    Description: American politician (1858–1937)
    Born: ['+1858-12-31T00:00:00Z', '+1858-00-00T00:00:00Z']
    Died: ['+1937-05-09T00:00:00Z', '+1937-00-00T00:00:00Z']
    Birth place: ['Indianapolis']
    Death place: ['Baltimore']
    Work locations: ['Washington, D.C.']
  Location Wikidata:
    Label: Maine
    Description: state of the United States of America
    Country: ['United States']
    Located in: ['United States']
    Aliases: {'en': ['ME', 'State of Maine', 'Maine, United States', 'The Pine Tree State', 'US-ME'], 'de': ['ME']}
    Coordinates: [{'lat': 45.5, 'lon': -69}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 13 (0 = most prominent)
    OCR quality estimate: 0.982

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Harry I >. New' and 'Maine' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Harry I >. New' near 'Maine' around 1900-06-26?
  4. Resolve temporal expressions relative to 1900-06-26. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 147:
  Publication date : 1948-12-30
  Language         : de
  Person  : 'Nokeraschi Pasehn'  (QID: Q1391679)
  Location: 'Abbas-Brücke'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Nokcraschi Pascha Ed. 7. Seine Studien an der Veterinär-Hedi zinischen Faleultiit wurden ihm dureh ein Ssipen dium, dus ilim von Nokraschi Pascha persönlich gewührt worden war, ermöglicht. In einer Sehublade des Sebreibtisches des er mordeten Ministerprüsidenten fand man einen Stolz Drokbriefe, die [E1] Nokeraschi Pasehn [/E1] erhalten hatte und über die er nieht einmal eine Untersuchung angeordnet lntte."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Mahmoud an-Nukrashi Pascha
    Description: ägyptischer Premierminister
    Born: ['+1888-04-26T00:00:00Z', '+1888-01-01T00:00:00Z']
    Died: ['+1948-12-28T00:00:00Z', '+1948-01-01T00:00:00Z']
    Birth place: ['Q87']
    Death place: ['Q85']
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "fand" — tense=Past, aspect=None, mood=Ind
      Sentence: "In einer Sehublade des Sebreibtisches des er mordeten Ministerprüsidenten fand man einen Stolz Drokbriefe, die Nokerasch"
    Verb cluster: "wurden" — tense=Past, aspect=None, mood=Ind
      Sentence: "Seine Studien an der Veterinär-Hedi zinischen Faleultiit wurden ihm dureh ein Ssipen dium, dus ilim von Nokraschi Pascha"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 63 (0 = most prominent)
    OCR quality estimate: 0.983

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Nokeraschi Pasehn' and 'Abbas-Brücke' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Nokeraschi Pasehn' near 'Abbas-Brücke' around 1948-12-30?
  4. Resolve temporal expressions relative to 1948-12-30. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 148:
  Publication date : 1826-09-29
  Language         : fr
  Person  : 'don Nazàrio-Eguia'  (QID: N/A)
  Location: 'ehPortugal'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Le ministère est positivement informa par les rapports officiels des gouverneurs d'Estramadure et de Galice, que la désertion a jusqu'à ce jour enlevé à l'armée espagnole 3400 hommes, " dont 2000 sont entrés'[E2] ehPortugal [/E2] par l'Estramadure portugaise, qu'on nomme l'Alentejo, et 1400 par la province de Tras-los-Montès. La première de ces deux colonnes s'est présentée au'gouverneur -de Jelvès, et'la deuxième à celui de Chaves, qui'ont aussitôt demandé des ordres à leur gouvernement. Heureusement que ce capitaine-général est un homme ferme et habile, et dont le dévouement est garanti par des preuves de fidélité. C'est [E1] don Nazàrio-Eguia [/E1]..."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "3400" → 3400
      - "2000" → 2000
      - "1400" → 1400
    Temporal signal words: tôt
    Verb cluster: "est don" — tense=Pres, aspect=None, mood=Ind
      Sentence: "C'est don Nazàrio-Eguia..."
    Verb cluster: "est positivement" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Le ministère est positivement informa par les rapports officiels des gouverneurs d'Estramadure et de Galice, que la dése"
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 174 days
    Entity sentence position in article: 14 (0 = most prominent)
    OCR quality estimate: 0.991

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'don Nazàrio-Eguia' and 'ehPortugal' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'don Nazàrio-Eguia' near 'ehPortugal' around 1826-09-29?
  4. Resolve temporal expressions relative to 1826-09-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 149:
  Publication date : 1920-11-11
  Language         : en
  Person  : 'Miss Williams'  (QID: N/A)
  Location: 'Shelby coun\nty'  (QID: Q501602)

  [ARTICLE TEXT — entity markers added]
  "A very charming woman politician in our midst recently, Miss Chari Williams, proved that a woman can have the entire political situation at her tongue’s end, and can give out his informatiofi to an audience with dignity, womanly modesty, yet w r ith splendid force and with the con vincing method of instruction that proves her to have been a successful teacher as well as having successful ly filled the place of superintendent of public Instruction for Shelby coun ty for eight years. [E1] Miss Williams [/E1] spoke with ease and handled the po litical questions, t,b.e League of Na tions and other subjects pertinent to the present election with ease, dignity and power."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Shelby County
    Description: county in Tennessee, United States
    Country: ['United States']
    Located in: ['Tennessee']
    Aliases: {'en': ['Shelby County, Tennessee', 'Shelby County, TN']}
    Coordinates: [{'lat': 35.18, 'lon': -89.89}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: recently
    Verb cluster: "proved" — tense=Past, aspect=None, mood=None
      Sentence: "A very charming woman politician in our midst recently, Miss Chari Williams, proved that a woman can have the entire pol"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 5 (0 = most prominent)
    OCR quality estimate: 0.998

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Miss Williams' and 'Shelby coun\nty' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Miss Williams' near 'Shelby coun\nty' around 1920-11-11?
  4. Resolve temporal expressions relative to 1920-11-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 150:
  Publication date : 1848-10-01
  Language         : de
  Person  : 'Metz'  (QID: Q5080926)
  Location: 'Bartringen'  (QID: Q809603)

  [ARTICLE TEXT — entity markers added]
  "©te hatte sich im entscheidenden Augenblicke der Partei [E1] Metz [/E1] in die Arme geworfen, und dieser jegliche Unterstützung geboten, um den sonst ohne Zweifel schon sicheren Sieg des katholischen Wahlcomitcs zu vereiteln. Dadurch ist es ihr allerdings gelungen, die achtbarsten Bürger ter Statt, Der Wahltag zu Luxemburg. Herr Pescatore erhielt seitens des kath. Wahlcomites über 500 Stimmen, unb ging mit absoluter Stimmenmehrheit (939 St.) aus dem Wahlkampfe hervor. Außerdem erhielten eine absolute Stimmenmehrheit: Fischer (805 St.), Ch."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Charles Metz
    Description: luxemburgischer Politiker
    Born: ['+1799-01-06T00:00:00Z']
    Died: ['+1853-04-24T00:00:00Z']
    Birth place: ['Luxemburg']
    Death place: ['Diekirch']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: vor
    Verb cluster: "hatte" — tense=Past, aspect=None, mood=Ind
      Sentence: "©te hatte sich im entscheidenden Augenblicke der Partei Metz in die Arme geworfen, und dieser jegliche Unterstützung geb"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 16 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Metz' and 'Bartringen' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Metz' near 'Bartringen' around 1848-10-01?
  4. Resolve temporal expressions relative to 1848-10-01. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 151:
  Publication date : 1938-05-20
  Language         : de
  Person  : 'Octave Homberg'  (QID: Q15969995)
  Location: 'Rom'  (QID: Q220)

  [ARTICLE TEXT — entity markers added]
  "In seinen, in der „Revue de Paris" verössentlichten neues Material zutagefördernden Erinnerungen über Frankreichs größten Außenminister Deleass. stellt [E1] Octave Homberg [/E1] fest, daß Delcass. gegen den seinerzeitigen Bruch Frankreichs mit dem Vatikan gewesen war. Obwohl Radikalsozialist war er nicht antiklerikal; als Außenminister hatte er überdies die moralische Macht des Papsttums kennen gelernt. Er hat alles getan, um Eombes am Bruch des Konkordates zu verhindern. Der Präsident der Republik, der allein auf dem Laufenden war, entsandte ohne Wissen der französischen Botschaft in [E2] Rom [/E2] Victor Homberg in geheimer Mission nach Rom, um durch Vermittlung von Kardinal Rampolla Konzessionen namentlich in der Frage der Vischofsernennungen zu erlangen;"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Octave Homberg
    Description: French financier
    Born: ['+1876-01-19T00:00:00Z']
    Died: ['+1941-07-09T00:00:00Z']
    Birth place: ['Paris']
    Death place: ['Cannes']
  Location Wikidata:
    Label: Rom
    Description: Haupt- und bevölkerungsreichste Stadt Italiens
    Country: ['Italien', 'Kirchenstaat', 'Kingdom of Italy', 'Ostgotenreich', 'Byzantinisches Reich', 'Q172579', 'Q201038', 'Römische Republik', 'Q2277', 'Weströmisches Reich', 'Q237']
    Located in: ['Q15119', 'Kirchenstaat', 'Rome', 'Q1747689', 'Q17167', 'Q2277', 'Weströmisches Reich', 'Q18288160', 'circle of Rome']
    Aliases: {'en': ['The Eternal City', 'Roma', 'Rome, Italy', 'City of Seven Hills'], 'fr': ['La ville éternelle', 'La ville aux sept collines', 'Roma', "l'Urbs"], 'de': ['Die Ewige Stadt', 'Roma'], 'lb': ['Roma', "D'Éiweg Stad"]}
    Coordinates: [{'lat': 41.893055555556, 'lon': 12.482777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach
    Verb cluster: "stellt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "stellt Octave Homberg fest, daß Delcass."
    Verb cluster: "entsandte" — tense=Past, aspect=None, mood=Ind
      Sentence: "Der Präsident der Republik, der allein auf dem Laufenden war, entsandte ohne Wissen der französischen Botschaft in Rom V"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 1.000

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Octave Homberg' and 'Rom' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Octave Homberg' near 'Rom' around 1938-05-20?
  4. Resolve temporal expressions relative to 1938-05-20. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 152:
  Publication date : 1820-03-06
  Language         : en
  Person  : 'Thomas O’Brien'  (QID: N/A)
  Location: 'BaltimorCy'  (QID: Q5092)

  [ARTICLE TEXT — entity markers added]
  "[E2] BaltimorCy [/E2] March 2. This morning, John F. Ferguson. William Murphy, [E1] Thomas O’Brien [/E1], Charles Weaver, Isaac \llister, J. Jackson, and Isaac Denuie, convicted of Piracy, committed on board of La Irresistable privateer, which they ran a- way with from Margaritta, were brought be fore bis honor Judge Bland, wh, after a ‘short but impressive address,."

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
    Verb cluster: "were brought" — tense=Past, aspect=Perf, mood=Ind
      Sentence: "William Murphy, Thomas O’Brien, Charles Weaver, Isaac \llister, J. Jackson, and Isaac Denuie, convicted of Piracy, commi"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.993

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Thomas O’Brien' and 'BaltimorCy' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Thomas O’Brien' near 'BaltimorCy' around 1820-03-06?
  4. Resolve temporal expressions relative to 1820-03-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 153:
  Publication date : 1961-01-20
  Language         : fr
  Person  : 'Roger Rivière'  (QID: N/A)
  Location: 'France'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Le Dr Stern, directeur de la clinique de rééducation de Lamalou-les-Bains, a rendu visite à [E1] Roger Rivière [/E1], qu'il avait soigné le premier après sa chute dans le Tour de [E2] France [/E2]."

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
  1. What is the relationship between 'Roger Rivière' and 'France' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Roger Rivière' near 'France' around 1961-01-20?
  4. Resolve temporal expressions relative to 1961-01-20. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 154:
  Publication date : 1868-04-22
  Language         : fr
  Person  : 'jeune R'  (QID: N/A)
  Location: 'Areuse'  (QID: Q111680)

  [ARTICLE TEXT — entity markers added]
  "— Dans la matinée du mercredi 15 avril, on a retiré de l'[E2] Areuse [/E2], près de Môliers, le corps de la [E1] jeune R [/E1] ."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Areuse
    Description: rivière de Suisse
    Country: ['Q39']
    Located in: ['Q12738']
    Coordinates: [{'lat': 46.9455, 'lon': 6.871}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "retiré" — tense=Past, aspect=None, mood=None
      Sentence: "— Dans la matinée du mercredi 15 avril, on a retiré de l'Areuse, près de Môliers, le corps de la jeune R ."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 49 (0 = most prominent)
    OCR quality estimate: 0.983

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'jeune R' and 'Areuse' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'jeune R' near 'Areuse' around 1868-04-22?
  4. Resolve temporal expressions relative to 1868-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 155:
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
Sample 156:
  Publication date : 1930-01-15
  Language         : fr
  Person  : 'E. Dieudonné'  (QID: N/A)
  Location: 'CHATELET'  (QID: Q1469315)

  [ARTICLE TEXT — entity markers added]
  "45, Flossie[E2] CHATELET [/E2], 8 h. 30 Robert-le-Pirate. CLUNY, 9 h., Au bagne ! ([E1] E. Dieudonné [/E1]).CO.-CAUMARTIN."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: théâtre du Châtelet
    Description: théâtre dans le 1er arrondissement de Paris
    Country: ['Q142']
    Located in: ['Q161741']
    Aliases: {'en': ['Theatre du Chatelet', 'Théâtre Musical de Paris'], 'fr': ['théâtre musical de Paris', 'théâtre du Chatelet', 'théâtre impérial du Châtelet'], 'de': ['Theatre du Chatelet', 'Chatelet Theater']}
    Coordinates: [{'lat': 48.857777777778, 'lon': 2.3463888888889}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "FlossieCHATELET" — tense=Past, aspect=None, mood=None
      Sentence: "45, FlossieCHATELET, 8 h. 30 Robert-le-Pirate."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 35 (0 = most prominent)
    OCR quality estimate: 0.824

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'E. Dieudonné' and 'CHATELET' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'E. Dieudonné' near 'CHATELET' around 1930-01-15?
  4. Resolve temporal expressions relative to 1930-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 157:
  Publication date : 1918-11-18
  Language         : fr
  Person  : 'M. Willemin'  (QID: Q15694941)
  Location: 'Genève'  (QID: Q71)

  [ARTICLE TEXT — entity markers added]
  "GENÈVE. — Vendredi, à midi, comme il descendait du tram au Molard, à [E2] Genève [/E2], pour se rendre à son étude, [E1] M. Willemin [/E1], avocat, maire de Plainpalais, ex-conseiller national, a été l' objet d'une violente manifestation de la part de quelques centaines de citoyens."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Albert Dupont-Willemin
    Description: homme politique suisse
    Born: ['+1903-05-00T00:00:00Z']
    Died: ['+1977-05-03T00:00:00Z']
    Birth place: ['Q71']
    Death place: ['Q84']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: {"birth_place": "P19"}

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "descendait" — tense=Imp, aspect=None, mood=Ind
      Sentence: "— Vendredi, à midi, comme il descendait du tram au Molard, à Genève, pour se rendre à son étude, M. Willemin, avocat, ma"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 77 (0 = most prominent)
    OCR quality estimate: 0.988

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Willemin' and 'Genève' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Willemin' near 'Genève' around 1918-11-18?
  4. Resolve temporal expressions relative to 1918-11-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 158:
  Publication date : 1820-05-05
  Language         : en
  Person  : 'King Henry'  (QID: Q101384)
  Location: 'Great Britain'  (QID: Q23666)

  [ARTICLE TEXT — entity markers added]
  "Sir Wiiliam Blackstono has collated and commented on it—his fine copy of Magna Charta has been excelled by later specimens of art, and the fac-similes of the seals and signatur e.diave made every reader of taste in [E2] Great Britain [/E2] acquainted, in some de gree, not merely with the state ofknowledge and of art at the period in question, but with the literary attainments, al>©, of King John, [E1] King Henry [/E1], and fbeir “ Barons bold.”"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Henry I of England
    Description: King of England from 1100 to 1135 (1068–1135)
    Born: ['+1068-00-00T00:00:00Z', '+1068-09-21T00:00:00Z']
    Died: ['+1135-12-01T00:00:00Z', '+1135-12-02T00:00:00Z']
    Birth place: ['Selby']
    Death place: ['Saint-Denis-le-Ferment', 'Lyons-la-Forêt']
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
  1. What is the relationship between 'King Henry' and 'Great Britain' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'King Henry' near 'Great Britain' around 1820-05-05?
  4. Resolve temporal expressions relative to 1820-05-05. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 159:
  Publication date : 1920-11-11
  Language         : en
  Person  : 'Miss Williams'  (QID: N/A)
  Location: 'State of New York'  (QID: Q1384)

  [ARTICLE TEXT — entity markers added]
  "The official announcement in August that the [E2] State of New York [/E2] had purchased two grams and a quarter of radium for the free treatment of cancer, begin ning Oct. 15, also to treat other allied malignant diseases, and that this tiny amount of the rare and super precious metal is enough to treat two billion patients, is wonderful statement to be found in an article entitled “Science and Discovery” in the October number of Current His tory. This also gives the use of ra dium in wireless messages, in air planes, and states tAa Madam Curie has recently discovered a new meth od of using it. A very charming woman politician in our midst recently, Miss Chari Williams, proved that a woman can have the entire political situation at her tongue’s end, and can give out his informatiofi to an audience with dignity, womanly modesty, yet w r ith splendid force and with the con vincing method of instruction that proves her to have been a successful teacher as well as having successful ly filled the place of superintendent of public Instruction for Shelby coun ty for eight years. [E1] Miss Williams [/E1] spoke with ease and handled the po litical questions, t,b.e League of Na tions and other subjects pertinent to the present election with ease, dignity and power."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: New York
    Description: state of the United States of America
    Country: ['United States']
    Located in: ['United States']
    Aliases: {'en': ['NY', 'New York, United States', 'State of New York', 'NYS', 'New York (state)', 'NY state', 'New York state', 'The Empire State', 'US-NY', 'Empire State'], 'fr': ['NY', 'NYS', 'État de New York', "État de l'Empire"], 'de': ['Empire State', 'New York Staat', 'Staat New York', 'New York State', 'State of New York', 'NY', 'US-NY']}
    Coordinates: [{'lat': 43, 'lon': -75}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: recently
    Verb cluster: "proved" — tense=Past, aspect=None, mood=None
      Sentence: "A very charming woman politician in our midst recently, Miss Chari Williams, proved that a woman can have the entire pol"
    Verb cluster: "begin" — tense=Pres, aspect=None, mood=None [NEGATED]
      Sentence: "The official announcement in August that the State of New York had purchased two grams and a quarter of radium for the f"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 5 (0 = most prominent)
    OCR quality estimate: 0.998

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Miss Williams' and 'State of New York' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Miss Williams' near 'State of New York' around 1920-11-11?
  4. Resolve temporal expressions relative to 1920-11-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 160:
  Publication date : 1930-01-15
  Language         : fr
  Person  : 'Capella'  (QID: N/A)
  Location: 'FOLIES-BERGÈRE'  (QID: Q330375)

  [ARTICLE TEXT — entity markers added]
  "Roseray et [E1] Capella [/E1]. [E2] FOLIES-BERGÈRE [/E2], 8.30."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 134 (0 = most prominent)
    OCR quality estimate: 0.824

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Capella' and 'FOLIES-BERGÈRE' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Capella' near 'FOLIES-BERGÈRE' around 1930-01-15?
  4. Resolve temporal expressions relative to 1930-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 161:
  Publication date : 1808-09-01
  Language         : fr
  Person  : 'Henriette'  (QID: N/A)
  Location: 'Chaux-de-Fonds'  (QID: Q68124)

  [ARTICLE TEXT — entity markers added]
  "Le public est informé, qu'au bénéfice d'un gracieux arrêt de la Seigneurie, " et d'une sentence de direction de l'honorable Justice de la [E2] Chaux-de-Fonds [/E2], le tuteur et les parens des enfans'de Henri Jean-Maire, se présenteront en cour de Justice de la dite Chaùx-de-Fonds, le Mardi _s _? o. Septembre courant, au plaid ordinaire, aux lieu et heure accoutumés, ponr postuler au nom des enfans nés et à naître du dit Henri Jean-Maire et de Reine née Robert-Nicoud, mari et femme, une renonciation formelle et juridique aux biens et dettes présens et futurs, de leurs dits père et mère. jft. Le Gouvernement ayant concède à [E1] Henriette [/E1], fille de feu le sieur cap itaine-lieutenant"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: La Chaux-de-Fonds
    Description: commune suisse du canton de Neuchâtel
    Country: ['Suisse']
    Located in: ['district de La Chaux-de-Fonds', 'canton de Neuchâtel']
    Aliases: {'en': ['La Chaux-de-Fonds NE', 'Chaux-de-Fonds', 'La Chaux de Fonds'], 'fr': ['Chaux-de-Fonds', 'La Tchaux', "La T'chaux"], 'de': ['Chaux-de-Fonds', 'La Tchaux', "La T'chaux"]}
    Coordinates: [{'lat': 47.099627777778, 'lon': 6.8295583333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "concède" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Le Gouvernement ayant concède à Henriette, fille de feu le sieur cap itaine-lieutenant"
    Verb cluster: "présenteront" — tense=Fut, aspect=None, mood=Ind
      Sentence: "Le public est informé, qu'au bénéfice d'un gracieux arrêt de la Seigneurie, " et d'une sentence de direction de l'honora"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 8 (0 = most prominent)
    OCR quality estimate: 0.952

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Henriette' and 'Chaux-de-Fonds' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Henriette' near 'Chaux-de-Fonds' around 1808-09-01?
  4. Resolve temporal expressions relative to 1808-09-01. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 162:
  Publication date : 1930-01-15
  Language         : fr
  Person  : 'Roseray'  (QID: N/A)
  Location: 'DIX-HEURES'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "[E1] Roseray [/E1] et Capella."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 134 (0 = most prominent)
    OCR quality estimate: 0.824

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Roseray' and 'DIX-HEURES' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Roseray' near 'DIX-HEURES' around 1930-01-15?
  4. Resolve temporal expressions relative to 1930-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 163:
  Publication date : 1826-06-30
  Language         : fr
  Person  : 'Ibrahim'  (QID: N/A)
  Location: 'Péloponèse'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Celles-ci se sont reudues dans le [E2] Péloponèse [/E2], pour chercher un asile auprès du gouvernement ; les autres se trouvent à Cravari (Locride) réunis à d'autres chefs grecs qui gardent les défilés de cette province. Ni [E1] Ibrahim [/E1] qui, après s'être dirigé sur Calavrita, a été obligé de se replier sur Patras, ni Chiutaehi, qui se trouvait dans la Grèce occidentale, n'ont entrepris auGune opération, tant ils ont été affaiblis par les pertes que leurs troupes ont éprouvées devant Missolonghi."

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
    Verb cluster: "sont" — tense=Pres, aspect=None, mood=Ind
      Sentence: "-ci se sont reudues dans le Péloponèse, pour chercher un asile auprès du gouvernement ;"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 13 (0 = most prominent)
    OCR quality estimate: 0.989

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Ibrahim' and 'Péloponèse' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Ibrahim' near 'Péloponèse' around 1826-06-30?
  4. Resolve temporal expressions relative to 1826-06-30. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 164:
  Publication date : 1838-05-11
  Language         : fr
  Person  : 'F. Coelho'  (QID: N/A)
  Location: 'Lisbonne'  (QID: Q597)

  [ARTICLE TEXT — entity markers added]
  "LisBOKNE 26 aoril. — Un changement partiel vient de s'opérer dans le cabinet. _ — Tout est tranquilles [E2] Lisbonne [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Lisbonne
    Description: capitale du Portugal
    Country: ['Portugal', 'République romaine', 'Royaume suève', 'royaume des Wisigoths', 'Califat omeyyade', 'émirat de Cordoue', 'califat de Cordoue', 'Q276841', 'taïfa de Lisbonne', 'Q276841', 'Q75613']
    Located in: ['Q207199', 'Q241731']
    Aliases: {'en': ['Lisboa'], 'fr': ['Lisboa'], 'de': ['Lisboa']}
    Coordinates: [{'lat': 38.708042, 'lon': -9.139016}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "est tranquilles" — tense=Pres, aspect=None, mood=Ind
      Sentence: "— Tout est tranquilles Lisbonne."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 5 (0 = most prominent)
    OCR quality estimate: 0.985

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'F. Coelho' and 'Lisbonne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'F. Coelho' near 'Lisbonne' around 1838-05-11?
  4. Resolve temporal expressions relative to 1838-05-11. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 165:
  Publication date : 1898-06-10
  Language         : de
  Person  : 'Schriftsteller Ganivet'  (QID: Q706889)
  Location: 'Helsingford'  (QID: Q1757)

  [ARTICLE TEXT — entity markers added]
  "Trotzdem sitzt oben in Finnland, in [E2] Helsingford [/E2], ein spanischer Berufskonsul, der mir befreundete [E1] Schriftsteller Ganivet [/E1]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Ángel Ganivet
    Description: spanischer Schriftsteller
    Born: ['+1865-12-13T00:00:00Z']
    Died: ['+1898-11-29T00:00:00Z']
    Birth place: ['Granada']
    Death place: ['Riga']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "sitzt" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Trotzdem sitzt oben in Finnland, in Helsingford, ein spanischer Berufskonsul, der mir befreundete Schriftsteller Ganivet"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 30 (0 = most prominent)
    OCR quality estimate: 0.998

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Schriftsteller Ganivet' and 'Helsingford' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Schriftsteller Ganivet' near 'Helsingford' around 1898-06-10?
  4. Resolve temporal expressions relative to 1898-06-10. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 166:
  Publication date : 1930-03-21
  Language         : en
  Person  : 'E. P. White'  (QID: N/A)
  Location: 'Buxton'  (QID: Q745614)

  [ARTICLE TEXT — entity markers added]
  "C. P. Gray, is principal of the [E2] Buxton [/E2] school. The students are being taught in the neighboring homes of [E1] E. P. White [/E1], G. D. Miller and U. B. Williams.—"

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
  1. What is the relationship between 'E. P. White' and 'Buxton' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'E. P. White' near 'Buxton' around 1930-03-21?
  4. Resolve temporal expressions relative to 1930-03-21. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 167:
  Publication date : 1808-09-01
  Language         : fr
  Person  : 'Jeanne-Marie née Morel'  (QID: N/A)
  Location: 'Villard'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Et Henri Favre, de [E2] Villard [/E2] _, et sa femme [E1] Jeanne-Marie née Morel [/E1], veuve de Jean-Daniel Favre, ayant'obtenu la discussion de leurs biens, pour satisfaire à leurs dettes, qui a aussi été _firfe au Mercredi 7 du dit mois : Tous créanciers quelcçtiqnes de ces deux masses, compris ceux de celle à la _stfsdite veuve du chef de son premier mari, sont requis % è se présenter _"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "obtenu" — tense=Past, aspect=None, mood=None
      Sentence: "Et Henri Favre, de Villard _, et sa femme Jeanne-Marie née Morel, veuve de Jean-Daniel Favre, ayant'obtenu la discussion"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 27 (0 = most prominent)
    OCR quality estimate: 0.952

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Jeanne-Marie née Morel' and 'Villard' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Jeanne-Marie née Morel' near 'Villard' around 1808-09-01?
  4. Resolve temporal expressions relative to 1808-09-01. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 168:
  Publication date : 1874-08-25
  Language         : de
  Person  : 'v . Oppenfeld'  (QID: N/A)
  Location: 'Schleſten'  (QID: Q81720)

  [ARTICLE TEXT — entity markers added]
  "Magnus , Conful [E1] v . Oppenfeld [/E1] f Dieier Zeitvunkt dürfte min nicht mehr ferne ſein , da die Geſchaͤfte der Geſellſchaft in letzter Zeit einen ſehr erfreulichen Auiſchwung genommen baben . So wnd und gemeldet , datz die Kefſelſchmiede der Gefenſ Gaft in [E2] Schleſten [/E2] dieler Tage Auftraͤge im Betrage von 250 00 Eutr ."

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
    Verb cluster: "gemeldet" — tense=None, aspect=None, mood=None
      Sentence: "So wnd und gemeldet , datz die Kefſelſchmiede der Gefenſ Gaft in Schleſten dieler Tage Auftraͤge im Betrage von 250 00 E"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 6 (0 = most prominent)
    OCR quality estimate: 0.973

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'v . Oppenfeld' and 'Schleſten' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'v . Oppenfeld' near 'Schleſten' around 1874-08-25?
  4. Resolve temporal expressions relative to 1874-08-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 169:
  Publication date : 1908-01-07
  Language         : fr
  Person  : 'colonel Félineau'  (QID: N/A)
  Location: 'Titinies'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Un télégramme du général Lyautey, daté du 4 janvier, annonce qu'une colonne forte de six compagnies d'infanterie, d'une section d'artillerie de montagne et du goum, commandée par le [E1] colonel Félineau [/E1], est partie d'Aïn-Sfa et a battu le massif montagneux, en passant par Kattecha et le col de [E2] Titinies [/E2] et a poussé son avant-garde jusqu'à bou-Zabel."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: avant
    Verb cluster: "daté" — tense=Past, aspect=None, mood=None
      Sentence: "Un télégramme du général Lyautey, daté du 4 janvier, annonce qu'une colonne forte de six compagnies d'infanterie, d'une "
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 18 (0 = most prominent)
    OCR quality estimate: 0.990

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'colonel Félineau' and 'Titinies' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'colonel Félineau' near 'Titinies' around 1908-01-07?
  4. Resolve temporal expressions relative to 1908-01-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 170:
  Publication date : 1921-02-22
  Language         : fr
  Person  : 'M. Stadler'  (QID: N/A)
  Location: 'Suisse'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "La [E2] Suisse [/E2] en ziaza-ï.— Les gyms. C'est en véritable artiste, amoureux de l'Alpe. que [E1] M. Stadler [/E1] a patiemment recueilli la splendide collection de clichés colorés, an moyen desquels ii nous promènera en zigzag dans les cantons alpins."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "recueilli" — tense=Past, aspect=None, mood=None
      Sentence: "que M. Stadler a patiemment recueilli la splendide collection de clichés colorés, an moyen desquels ii nous promènera en"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 30 (0 = most prominent)
    OCR quality estimate: 0.932

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Stadler' and 'Suisse' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Stadler' near 'Suisse' around 1921-02-22?
  4. Resolve temporal expressions relative to 1921-02-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 171:
  Publication date : 1978-09-27
  Language         : fr
  Person  : 'Brian\nClough'  (QID: Q207658)
  Location: 'Liverpool'  (QID: Q24826)

  [ARTICLE TEXT — entity markers added]
  "Le règne de [E2] Liverpool [/E2] se terminern-t-il ce soir ? La période de domination de Liverpool en coupe d'Europe des clubs champions pourrait se terminer ce soir, à I'Anfield Road, quand les champions de 1977 et 1978, recevront Nottingham Forest, champion d'Angleterre, en match retour du premier tour de cette compétition. De son côté, le « Forest » devra jouer sans son arrière gauche, Colin Barrett, blessé samedi dernier. Son remplaçant sera probablement Frank Clark, un « vétéran » de trente-trois ans, mais McLough pourrait créer une nouvelle surprise, comme par exemple l'éviction de son « stratège »"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Brian Clough
    Description: footballeur et entraîneur anglais
    Born: ['+1935-03-21T00:00:00Z']
    Died: ['+2004-09-20T00:00:00Z']
    Birth place: ['Middlesbrough']
    Death place: ['Derby']
  Location Wikidata:
    Label: Liverpool
    Description: ville en Angleterre, Royaume-Uni
    Country: ['Royaume-Uni']
    Located in: ['district métropolitain de Liverpool', 'district métropolitain de Liverpool', 'district métropolitain de Liverpool']
    Aliases: {'en': ['City of Liverpool', 'Liverpool, Merseyside', 'Liverpool, UK', 'Liverpool, England'], 'de': ['Liverpudlian']}
    Coordinates: [{'lat': 53.407222222222224, 'lon': -2.9916666666666667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1977" → 1977
      - "1978" → 1978
    Verb cluster: "sera" — tense=Fut, aspect=None, mood=Ind
      Sentence: "Son remplaçant sera probablement Frank Clark, un « vétéran » de trente-trois ans, mais McLough pourrait créer une nouvel"
    Verb cluster: "terminern" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Le règne de Liverpool se terminern-t-il ce soir ?"
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    Entity sentence position in article: 2 (0 = most prominent)
    OCR quality estimate: 0.979

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Brian\nClough' and 'Liverpool' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Brian\nClough' near 'Liverpool' around 1978-09-27?
  4. Resolve temporal expressions relative to 1978-09-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 172:
  Publication date : 1878-02-06
  Language         : de
  Person  : 'türkische Admiral Ho\nbart Pascha'  (QID: Q608043)
  Location: 'Piräus'  (QID: Q58976)

  [ARTICLE TEXT — entity markers added]
  "Die türkische Verwaltung von Epirus und Thessalien bereitet sich auf energischen Widerstand vor, und wie aus Konstantinopel ge meldet wird, hat auch der türkische Admiral Ho bart Pascha Befehl erhalten, sich zur Abfahrt be reit zu halten, wie man glaubt, nach dem [E2] Piräus [/E2]."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Augustus Charles Hobart
    Description: britisch-türkischer Admiral
    Born: ['+1822-04-01T00:00:00Z']
    Died: ['+1886-06-19T00:00:00Z']
    Birth place: ['Q2547610']
    Death place: ['Q490']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Verb cluster: "bereitet" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Die türkische Verwaltung von Epirus und Thessalien bereitet sich auf energischen Widerstand vor, und wie aus Konstantino"
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 35 (0 = most prominent)
    OCR quality estimate: 0.999

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'türkische Admiral Ho\nbart Pascha' and 'Piräus' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'türkische Admiral Ho\nbart Pascha' near 'Piräus' around 1878-02-06?
  4. Resolve temporal expressions relative to 1878-02-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 173:
  Publication date : 1948-10-09
  Language         : fr
  Person  : 'Ben Barek'  (QID: Q609626)
  Location: 'Espagne'  (QID: Q29)

  [ARTICLE TEXT — entity markers added]
  "[E1] Ben Barek [/E1] qui est fixé actuellement en [E2] Espagne [/E2], serait déjà naturalisé espagnol."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Larbi Benbarek
    Description: footballeur marocain
    Born: ['+1917-06-16T00:00:00Z', '+1914-06-16T00:00:00Z']
    Died: ['+1992-09-16T00:00:00Z']
    Birth place: ['Casablanca']
    Death place: ['Q7903']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: actuellement
    Verb cluster: "fixé" — tense=Past, aspect=None, mood=None
      Sentence: "qui est fixé actuellement en Espagne, serait déjà naturalisé espagnol."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 7 (0 = most prominent)
    OCR quality estimate: 0.954

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Ben Barek' and 'Espagne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Ben Barek' near 'Espagne' around 1948-10-09?
  4. Resolve temporal expressions relative to 1948-10-09. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 174:
  Publication date : 1981-11-17
  Language         : fr
  Person  : 'Buxtehude'  (QID: N/A)
  Location: 'Eglise Saint-Jacques'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "[E2] Eglise Saint-Jacques [/E2]-20.30, récital d'orgue par Pierre Perdigon. Œuvres de [E1] Buxtehude [/E1], Tunder, Frescobaldi, Martini, Bach."

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
  1. What is the relationship between 'Buxtehude' and 'Eglise Saint-Jacques' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Buxtehude' near 'Eglise Saint-Jacques' around 1981-11-17?
  4. Resolve temporal expressions relative to 1981-11-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 175:
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
Sample 176:
  Publication date : 1826-06-30
  Language         : fr
  Person  : 'Chiutaehi'  (QID: N/A)
  Location: 'Patras'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Ni Ibrahim qui, après s'être dirigé sur Calavrita, a été obligé de se replier sur [E2] Patras [/E2], ni [E1] Chiutaehi [/E1], qui se trouvait dans la Grèce occidentale, n'ont entrepris auGune opération, tant ils ont été affaiblis par les pertes que leurs troupes ont éprouvées devant Missolonghi."

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
  1. What is the relationship between 'Chiutaehi' and 'Patras' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Chiutaehi' near 'Patras' around 1826-06-30?
  4. Resolve temporal expressions relative to 1826-06-30. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 177:
  Publication date : 1981-11-17
  Language         : fr
  Person  : 'G .-W. Pabst'  (QID: N/A)
  Location: 'PALAIS DE BEAULIEU'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "L'amour de Jeanne Ney », de [E1] G .-W. Pabst [/E1] . [E2] PALAIS DE BEAULIEU [/E2]"

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
  1. What is the relationship between 'G .-W. Pabst' and 'PALAIS DE BEAULIEU' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'G .-W. Pabst' near 'PALAIS DE BEAULIEU' around 1981-11-17?
  4. Resolve temporal expressions relative to 1981-11-17. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 178:
  Publication date : 1898-05-02
  Language         : de
  Person  : 'Präsident der Kunstgesell\nschaft, Hr. Dr. Carl v. Muralt,'  (QID: N/A)
  Location: 'Fröhlichstraße 1'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Der Präsident der Kunstgesell schaft, Hr. Dr. Carl v. Muralt, übernahm die Aus stellung im Namen des Vorstandes und sprach den sämtlichen Mitgliedern, die sich um die Fertigstellung der Ausstellung verdient gemacht hatten, den besten Dank für ihre Bemühungen aus. Warme Worte widmete der Präsident dem anwesenden greisen Künstler, zu dessen Ehren die Ausstellung veranstaltet wurde. Nach einigem Zögern willigte Hr. Koller ein und so wird das Publikum jetzt Gelegenheit finden, auch die Arbeitsstätte des Meisters zu besichtigen, wo er den größten Teil seines Lebens thätig gewesen ist. Kollers Ateliers in dem schöngelegenen Landsitz am Zürichhorn ([E2] Fröhlichstraße 1 [/E2], in der Nähe der Pferde bahnstation) enthält eine Reihe interessanter Studien und Bilder, insbesondere aus der letzten Zeit, und wird ohne Zweifel in den nächsten Wochen der Wallfahrtsort werden, nach welchem die Kunstliebhaber und Verehrer des Künstlers pilgern werden."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
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
  1. What is the relationship between 'Präsident der Kunstgesell\nschaft, Hr. Dr. Carl v. Muralt,' and 'Fröhlichstraße 1' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Präsident der Kunstgesell\nschaft, Hr. Dr. Carl v. Muralt,' near 'Fröhlichstraße 1' around 1898-05-02?
  4. Resolve temporal expressions relative to 1898-05-02. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 179:
  Publication date : 1868-04-22
  Language         : fr
  Person  : 'M Pocbin'  (QID: N/A)
  Location: 'Montagne-Noire'  (QID: Q1509963)

  [ARTICLE TEXT — entity markers added]
  "[E1] M Pocbin [/E1], femme du maire de Salford, a obtenu un grand succès. France. — On reçoit de fâcheuses nouvelles des récoltes, surtout dans le midi. 11 est tombé de la neige dans le département de l'Hérault, à la [E2] Montagne-Noire [/E2] et jusque dans les environs d'Avignon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Montagne Noire
    Description: massif montagneux situé à l'extrémité sud-ouest du Massif central, France
    Country: ['France']
    Located in: ['Pradelles-Cabardès']
    Aliases: {'de': ['Montagne-Noire-Zone']}
    Coordinates: [{'lat': 43.424444444444, 'lon': 2.4627777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "obtenu" — tense=Past, aspect=None, mood=None
      Sentence: "M Pocbin, femme du maire de Salford, a obtenu un grand succès."
    Verb cluster: "est tombé" — tense=Pres, aspect=None, mood=Ind
      Sentence: "11 est tombé de la neige dans le département de l'Hérault, à la Montagne-Noire et jusque dans les environs d'Avignon."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 18 (0 = most prominent)
    OCR quality estimate: 0.983

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M Pocbin' and 'Montagne-Noire' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M Pocbin' near 'Montagne-Noire' around 1868-04-22?
  4. Resolve temporal expressions relative to 1868-04-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 180:
  Publication date : 1898-06-10
  Language         : de
  Person  : 'Kolumbuskaravelen'  (QID: Q7322)
  Location: 'Amerika'  (QID: Q828)

  [ARTICLE TEXT — entity markers added]
  "Da ist Concas, der 1892 die Nachahmungen der [E1] Kolumbuskaravelen [/E1] nach [E2] Amerika [/E2] hinüber schaffte, oder sie vielmehr von modernen Kriegs schiffen dorthin bugsieren ließ;"

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1892" → 1892
    Temporal signal words: nach
    Verb cluster: "ist" — tense=Pres, aspect=None, mood=Ind
      Sentence: "Da ist Concas, der 1892 die Nachahmungen der Kolumbuskaravelen nach Amerika hinüber schaffte, oder sie vielmehr von mode"
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 6 days
    Entity sentence position in article: 38 (0 = most prominent)
    OCR quality estimate: 0.998

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Kolumbuskaravelen' and 'Amerika' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Kolumbuskaravelen' near 'Amerika' around 1898-06-10?
  4. Resolve temporal expressions relative to 1898-06-10. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 181:
  Publication date : 1890-11-06
  Language         : en
  Person  : 'S. H. Clifford'  (QID: N/A)
  Location: 'Catawba, O.'  (QID: Q1844924)

  [ARTICLE TEXT — entity markers added]
  "[E1] S. H. Clifford [/E1], New Cassel, Wis., was troubled with neuralgia and rheumatism, his stomach was disor dered, bis liver was affected to an alarming degree, appetite fell away and he was terribly reduced in flesb and strength. Three bottles of Elec trie Bitters cured him. Edward Shepherd, Harrisburg, III., bad a running sore on his leg of eight years’ standing. Used three bottles of Electric Bitters and seven boxes of Bucklen’s Arnica Salve, and bis leg is sound and well. John Speaker, [E2] Catawba, O. [/E2], bad five large fever sores on bis leg, doctors said he wa3 incurable."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Catawba
    Description: human settlement in Clark County, Ohio, United States of America
    Country: ['United States']
    Located in: ['Clark County']
    Aliases: {'en': ['Catawba, Ohio', 'Catawba, OH']}
    Coordinates: [{'lat': 40, 'lon': -83.6222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Verb cluster: "fell" — tense=Past, aspect=None, mood=None
      Sentence: "S. H. Clifford, New Cassel, Wis., was troubled with neuralgia and rheumatism, his stomach was disor dered, bis liver was"
    Verb cluster: "said" — tense=Past, aspect=None, mood=None
      Sentence: "John Speaker, Catawba, O., bad five large fever sores on bis leg, doctors said he wa3 incurable."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 0 (0 = most prominent)
    OCR quality estimate: 0.992

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'S. H. Clifford' and 'Catawba, O.' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'S. H. Clifford' near 'Catawba, O.' around 1890-11-06?
  4. Resolve temporal expressions relative to 1890-11-06. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 182:
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
Sample 183:
  Publication date : 1920-07-08
  Language         : en
  Person  : 'Dabbs'  (QID: N/A)
  Location: 'Cookeville'  (QID: Q2456192)

  [ARTICLE TEXT — entity markers added]
  "RAWLEY AGAIN Haven’t b en satisfied since I left [E2] Cookeville [/E2] until now. I seemed like I was almost lost, as I stayed in Gainesboro about IS months or 2 years. He treats all alike. Bill [E1] Dabbs [/E1] and Bood Choat are the night police."

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
  1. What is the relationship between 'Dabbs' and 'Cookeville' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Dabbs' near 'Cookeville' around 1920-07-08?
  4. Resolve temporal expressions relative to 1920-07-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 184:
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
Sample 185:
  Publication date : 1890-09-25
  Language         : en
  Person  : 'M. Pliillippe de Ferrari'  (QID: Q44105)
  Location: 'Asia'  (QID: Q48)

  [ARTICLE TEXT — entity markers added]
  "The museum of the Berlin post-cfllce alone contains a collection of between 4,000 and 5,000 specimens, half of which are European and the remain der divided between tbe Americans, [E2] Asia [/E2], Africa and Australia. The emblems upon the stamps of nations are legion; the earth, the sea and the vaulted canopy above have been ransacked for curious and mraning less devices and legends. The en tire animal kingdom, the stars and the moon iu all its phases, besides legendary emblems by the thousand, are known to the oollLctors of stamps, who pride themselves upon being “philatelists.” Upon the printed faces of these little squares of paper may be fonri*} the fogies of five em perors, eighteen kings,three q icens, one grand duke, several inferior tilled rulcr9 and many presidents. [E1] M. Pliillippe de Ferrari [/E1] perhaps has the largest and most valuable collec tion of stamps in the world, amount ing to something like 2ft0,000, and within tbe present year he solJ one little stamp to a collector in Paris for 150.000."

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
    Label: Asia
    Description: terrestrial continent, mainly in the northeastern quadrant
    Aliases: {'en': ['Asian continent', 'Continental Asia'], 'fr': ['continent asiatique', 'Asie continentale'], 'de': ['asiatischer Kontinent']}
    Coordinates: [{'lat': 43.681111111111115, 'lon': 87.33111111111111}, {'lat': 35, 'lon': 108}]
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
  1. What is the relationship between 'M. Pliillippe de Ferrari' and 'Asia' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Pliillippe de Ferrari' near 'Asia' around 1890-09-25?
  4. Resolve temporal expressions relative to 1890-09-25. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 186:
  Publication date : 1826-08-22
  Language         : fr
  Person  : 'M. le prince de Metternicli'  (QID: N/A)
  Location: 'Turin'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "S. M. n'a d'ailleurs amené avec elle de [E2] Turin [/E2] que quannte gardes-du-corps. On présume qu'immédiatement après les fêtes religieuses d'Annecy, qui ont dû commencer le 16 août, LL.MM. se rendront à Moutiers en Tarentaise. Des lettres de Mayence, que'nous recevons aujourd'hui', annoncent que [E1] M. le prince de Metternicli [/E1] est arrivé le 12 août à Johannisberg."

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
    Verb cluster: "a" — tense=Pres, aspect=None, mood=Ind [NEGATED]
      Sentence: "S. M. n'a d'ailleurs amené avec elle de Turin que quannte gardes-du-corps."
    Timex within ±14-day isAt window: False
    Entity sentence position in article: 1 (0 = most prominent)
    OCR quality estimate: 0.977

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. le prince de Metternicli' and 'Turin' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. le prince de Metternicli' near 'Turin' around 1826-08-22?
  4. Resolve temporal expressions relative to 1826-08-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 187:
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
