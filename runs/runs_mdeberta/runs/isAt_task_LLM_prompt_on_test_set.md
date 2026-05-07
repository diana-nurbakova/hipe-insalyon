You are an expert annotator for historical named-entity relation extraction
in the HIPE-2026 shared task.

CONTEXT:
- The samples you are asked to classify were pre-selected because the mDeBERTa
  baseline found them difficult or ambiguous.
- Treat them as hard cases requiring careful second-pass reasoning.
- Do NOT assume the encoder model was correct.
- Documents are historical newspaper articles from 1850-1950.
- Languages: English, French, German (read as-is; do NOT translate).
- OCR may introduce minor noise; ignore obvious OCR errors.
- Entity markers <PERSON>...</PERSON> and <LOCATION>...</LOCATION> are added to help
  you locate the entities in the text.


DEFINITIONS:
- "at" relation: The person has a general association with this location
  (born there, lived there, worked there, visited there, held office there, etc.).
  Values: TRUE, PROBABLE, FALSE
- "isAt" relation: The person is physically present at this location around
  the publication date of the article (within approximately +/- 2 weeks).
  Values: TRUE, FALSE

REASONING GUIDELINES:
1. First separate the two tasks clearly:
   - `at` asks for any real association with the location, including historical ones.
   - `isAt` asks only whether the person is there around document time.
   - If isAt=TRUE, then at should not be FALSE.

2. Use verb tense and aspect mainly for `isAt`, not as a hard rule for `at`:
   - Present tense / present progressive / ongoing situation -> positive signal for isAt.
   - Simple past / past perfect often means historical association only -> may still support at,
     but usually not isAt.
   - "formerly", "used to", "jadis", "ehemals", "autrefois" -> negative for isAt and often
     weaker for at unless another association is explicit.
   - Negation ("no longer", "nicht mehr", "ne ... plus") -> negative for isAt.
   - Future tense / planned travel -> not yet there -> FALSE for isAt.

3. Temporal expressions must be resolved against the publication date:
   - Resolve relative expressions ("last week", "yesterday", "la semaine derniere",
     "vorige Woche") relative to the publication date provided.
   - If a resolved date falls within +/- 14 days of the publication date and places the person
     at the location -> strong evidence for isAt=TRUE.
   - If outside that window -> it may still support at, but not necessarily isAt.

4. Biography and Wikidata context (when provided):
   - If the person died before the publication date -> isAt=FALSE.
   - Birth place, residence, work location, office, or death place can support at when they
     match the location.
   - Biography alone is usually not enough for isAt unless it is clearly time-aligned with
     the article or explicitly confirmed by the text.

5. Similar annotated examples:
   - Use them as soft evidence, not hard rules.
   - Always check whether the current article's wording and timing override the examples.

6. OCR and language noise:
   - Ignore stray characters and truncated words.
   - Prioritize clear verbal structures and named entities.

OUTPUT FORMAT - respond ONLY with one prediction per sample, nothing else:
Sample 0: FALSE
Sample 1: TRUE
...
Do NOT add explanations, JSON, or any other text.
```

## User Prompt

```text
TASK: "isAt" - Physical presence
Determine whether the PERSON was physically present at / living in the LOCATION
at the time the newspaper article was written (i.e. around the publication date).
  - TRUE  : explicit or strongly implied presence at document time
            (current residence, ongoing stay, event participation, or a resolved timex
             within about +/- 14 days that places the person there)
  - FALSE : no evidence of presence at document time
            (only historical association, past-only mention, future plan, negation,
             or the person is already deceased)
Important: if the evidence supports only a historical/general link but not presence
at document time, choose FALSE for isAt.
Note: isAt has NO PROBABLE label - it is a binary TRUE / FALSE decision.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FEW-SHOT EXAMPLES for task 'isAt' (DO NOT PREDICT THESE)

Example 0:
  Person           : General D’Alton
  Location         : Porte de Namur
  Publication date : 1790-03-03
  Language         : en
  Text             : <PERSON>General D’Alton</PERSON> did his tu rnoff from fix o’clock in the morning to negociate an armifiice. About (even o’clock, 8co men of Benden-D’Aloft entered the city with two pieces of cannon, which they planted on the Grand Pa lace. To wards noon, they attacked the Park and the Pal ace Royale, where the greateft body of troops were concentered, with 12 pieces or cannon. After a very heavy firing on both fides, D’Alton perceiving that the place was no longer tenable againtt fo much bravery, capitulated for the im mediate retreat of his whole gerrifon ; and the requell having been acceded to, about one o’clock they departed, with great precipitation, through the <LOCATION>Porte de Namur</LOCATION>.
  Person context   : Label: Richard d'Alton | Description: Austrian officer | Born: ['+1732-01-01T00:00:00Z', '+1733-00-00T00:00:00Z'] | Died: ['+1791-02-16T00:00:00Z', '+1790-02-16T00:00:00Z'] | Birth place: ['Rathconrath'] | Death place: ['Speyer', 'Trier']
  Temporal signals : no longer, after, late
  Verb cluster     : did(Past); perceiving(Pres+Prog)
  Timex resolved   : none
  ±14-day window   : False
  → Correct label  : TRUE
  Reasoning        : Annotated training example from the train set.

Example 1:
  Person           : George Cinton,
Vice President of the United Slates, and
President of the Senate
  Location         : United States of
America
  Publication date : 1810-04-14
  Language         : en
  Text             : B E it enacted by the Senate and House §f Representatives o f the United States of America, in Congress assembled, That the officers and soldiers of the Virginia line on continental establishment, their heirs or as signs entitled to bounty lands within the tract reserved by Virginia, between the lit tle Miami and Sciota rivers, for satisfying the legal bounties to her officers and soldi ers upon continental establishment, shall be allowed a further term of five years, from and after the passage of this act, to obtain warrants and complete their locations, and a further term of seven years, from and as ter the passage of this act as aforesaid, to return their surveys and warrants to the of sice of the Secretary of the War Depart ment, any thing in any former act to the contrary notwithstanding- Provided , That no locations as aforesaid within the above mentioned tract shall after the passing of this act he made on tracts of land for which patents had previously been issued or which had been previously surveyed, and any pa tent which may nevertheless be obtained for land located contrary to the provisions of this section, shall be considered as null and void. J. li. Varniim. Speaker of the House of Representatives. George Cinton, Vice President of the United Slates, and President of the Senate.
  Person context   : Label: George Clinton | Description: vice president of the United States from 1805 to 1812 (1739–1812) | Born: ['+1739-07-26T00:00:00Z'] | Died: ['+1812-04-20T00:00:00Z'] | Birth place: ['Little Britain'] | Death place: ['Washington, D.C.'] | Work locations: ['United States']
  Temporal signals : after, late
  Verb cluster     : assembled(Past)
  Timex resolved   : none
  ±14-day window   : False
  → Correct label  : TRUE
  Reasoning        : Annotated training example from the train set.

Example 2:
  Person           : VAAST
  Location         : Suisse
  Publication date : 1948-10-09
  Language         : fr
  Text             : Mais les dirigeants du SBB voudraient bien que les organisateurs çais avancent leur épreuve d'une semaine afin que l'on trouve le moyen d'insérer le Tour de <LOCATION>Suisse</LOCATION> entre le Tour de France et les championnats du monde. Après un échange de vue sur les enseignements de la course de 1948, les organisateurs ont décidé qu'elle serait courue dans le même sens, c'est-à dire d'ouest à est. De * nombreuses candidatures de villes sont parvenues aux organisateurs, mais l'itinéraire définitif ne sera établi que plus tard. Le Tour de 1949 sera disputé selon la formule équipes nationales et régionales. Football <PERSON>VAAST</PERSON>, DU RACING PARIS, SIGNE AU SERVETTE Le joueur du Racing Vaast, fixé à Genève, a envoyé sa lettre de démission au Racing et a signé au Servette.
  Person context   : Label: Ernest Vaast | Description: footballeur français | Born: ['+1922-10-28T00:00:00Z'] | Died: ['+2011-04-10T00:00:00Z'] | Birth place: ['5e arrondissement de Paris'] | Death place: ['Clermont-Ferrand']
  Temporal signals : plus, après, tard
  Verb cluster     : voudraient(Pres)
  Timex resolved   : 1948 -> 1948 | 1949 -> 1949
  ±14-day window   : True
  → Correct label  : TRUE
  Reasoning        : Annotated training example from the train set.

Example 3:
  Person           : comte Bomfin
  Location         : PORTUGAL
  Publication date : 1838-05-11
  Language         : fr
  Text             : <LOCATION>PORTUGAL</LOCATION>. LisBOKNE 26 aoril. — Un changement partiel vient de s'opérer dans le cabinet. M. d'Oliveira s'est retiré du ministère des finances, en acceptant le titre de baron de Tojal, et il est remplacé par M. de Carvalho, qui avait anciennement été chargé de ce déparlement, et était président de la chambre des députés, quand don Miguel l'avait dissoute en 1828. M. Carvalho a accepté, malgré lui, dit-on, et après de vives sollicitations. Le <PERSON>comte Bomfin</PERSON> est revenu au ministère de la guerre.
  Person context   : Label: José Travassos Valdez | Description: Portuguese noble (1787-1862) | Born: ['+1787-02-23T00:00:00Z'] | Died: ['+1862-07-10T00:00:00Z'] | Birth place: ['Q622819'] | Death place: ['Q597']
  Temporal signals : ancien, ancienne, après
  Verb cluster     : accepté(Past); revenu(Past)
  Timex resolved   : 1828 -> 1828
  ±14-day window   : False
  → Correct label  : TRUE
  Reasoning        : Annotated training example from the train set.

Example 4:
  Person           : König Milan
  Location         : Serbien
  Publication date : 1888-03-08
  Language         : de
  Text             : Bei dem großen Interesse, welches Oesterreich an den Vor gängen im Orient und insbesondere in <LOCATION>Serbien</LOCATION> nimmt, ist es begreiflich, daß unsere politischen Kreise mit Spannung den Wahlkampf in Serbien verfolgten, und daß sie Genugthuung empfinden über die eklatante Niederlage des Herrn Ristitsch, zumal letzterer jetzt offen als Parteigänger des rus sischen Panslavismus auftrat. Aber die Freude über seine Niederlage wird gemildert durch die Er wägung, daß es die Radikalen sind, welche als Sieger hervorgingen. Es ist noch nicht lange her, daß die radikale Partei in Serbien zu den ge schworensten Feinden Oesterreichs gehörte. Das Programm ihrer auswärtigen Politik lau tete kurz und bündig: Bosnien. Weil <PERSON>König Milan</PERSON> sich zu dieser Politik nicht bekennen wollte, vielmehr ein freundschaftliches Verhältniß zu der benachbarten mächtigen Monarchie unterhielt, wurden die Radi kalen von tödtlichem Hasse gegen die Person des Königs erfüllt, und vor fünf Jahren versuchten sie sogar auf gewaltsame Weise den König zu stürzen und eine panslavistisch gesinnte Regierung einzu setzen.
  Person context   : Label: Milan I. | Description: serbischer Fürst, König von Serbien | Born: ['+1854-08-10T00:00:00Z', '+1854-08-22T00:00:00Z'] | Died: ['+1901-01-29T00:00:00Z', '+1901-01-01T00:00:00Z', '+1901-01-11T00:00:00Z'] | Birth place: ['Q576804'] | Death place: ['Wien']
  Temporal signals : jetzt, nach, vor
  Verb cluster     : wurden(Past); ist(Pres)
  Timex resolved   : none
  ±14-day window   : False
  → Correct label  : TRUE
  Reasoning        : Annotated training example from the train set.

Example 5:
  Person           : Madam Sklodowsky
Curie
  Location         : Shelby coun
ty
  Publication date : 1920-11-11
  Language         : en
  Text             : WOMEN IN THE WORLD’S PROG RESS A woman who has achieved much, in the world’s recent most valued discoveries, is Madam Sklodowsky Curie, who with her late husband discovered radium and Its wonderful uses. Much has been written of the use of radium in the curing of the dread disease, cancer. It can no longer be said, they must not vote unless they would fight, for the famous Woman's Battalion of Death in Russia proved that women can fight for a cause to h'xe last ditch, meeting death and worse than death with a courage un conquered. A very charming woman politician in our midst recently, Miss Chari Williams, proved that a woman can have the entire political situation at her tongue’s end, and can give out his informatiofi to an audience with dignity, womanly modesty, yet w r ith splendid force and with the con vincing method of instruction that proves her to have been a successful teacher as well as having successful ly filled the place of superintendent of public Instruction for Shelby coun ty for eight years.
  Person context   : Label: Marie Curie | Description: Polish-French physicist and chemist (1867–1934) | Born: ['+1867-11-07T00:00:00Z'] | Died: ['+1934-07-04T00:00:00Z'] | Birth place: ['Warsaw'] | Death place: ['Sancellemoz'] | Residences: ['Warsaw', 'Paris']
  Temporal signals : recently, no longer, late
  Verb cluster     : is(Pres); proved(Past)
  Timex resolved   : none
  ±14-day window   : False
  → Correct label  : FALSE
  Reasoning        : Annotated training example from the train set.

Example 6:
  Person           : Sir Wiiliam Blackstono
  Location         : Philadelphia
  Publication date : 1820-05-05
  Language         : en
  Text             : <PERSON>Sir Wiiliam Blackstono</PERSON> has collated and commented on it—his fine copy of Magna Charta has been excelled by later specimens of art, and the fac-similes of the seals and signatur e.diave made every reader of taste in Great Britain acquainted, in some de gree, not merely with the state ofknowledge and of art at the period in question, but with the literary attainments, al>©, of King John, King Henry, and fbeir “ Barons bold.” Surely the Declaration of American Inde pendence is, at least, as well entitled to the decorations of art as the Magna. As no more of those copies will be printed than 'ball be subscribed for, gentlemen who wish for them, are requested to add the word “ colored ” to their subscription. JOHN BINNS, Chesnut-street, <LOCATION>Philadelphia</LOCATION>.
  Person context   : Label: William Blackstone | Description: English jurist, judge and Tory politician (1723-1780) | Born: ['+1723-07-10T00:00:00Z', '+1723-01-01T00:00:00Z'] | Died: ['+1780-02-14T00:00:00Z', '+1780-01-01T00:00:00Z'] | Birth place: ['City of London', 'Cheapside'] | Death place: ['Wallingford'] | Residences: ["Lincoln's Inn Fields"]
  Temporal signals : now, late, later
  Verb cluster     : has been excelled(Pres+Perf)
  Timex resolved   : none
  ±14-day window   : False
  → Correct label  : FALSE
  Reasoning        : Annotated training example from the train set.

Example 7:
  Person           : grande Uranie Montandon
  Location         : Cœudres
  Publication date : 1928-01-17
  Language         : fr
  Text             : , comme l' appelaient ses amis) avait passé la majeure partie de g. vie dans cette vallée jurassienne où dans lés temps anciens vécurent (?) le Solitaire dès Sagnes et Gédéon le Contreleyu. Cet endroit avait été par lui choisi en une occasion mémorable, quand un beau jour, ou plutôt un malheureux soir, il s'était aventuré à demander Êour femme la <PERSON>grande Uranie Montandon</PERSON> du ronillet. A sa complète stupéfaction, il lui fut répondu négativement. Quand il demanda les raisons de ce refus, elle lui déclara tout uniment « qu'il sentait trop l'horloger >. Pendant une heure ou deux, l'Alcide scngea à se noyer de dépit dans le lac des Tailleres, mais son bon sens lui revenant ei l'instinct de conservation aidant, il se borna à secouer sur ce Sol ingrat la poussière de ses souliers et, quelque temps plus tard, alla planter sa tente aux <LOCATION>Cœudres</LOCATION>, pensant que son noir chagrin se fondrait dans les brouillards de la Sagne.
  Person context   : No Wikidata data available for this person.
  Temporal signals : ancien, plus, tôt, tard
  Verb cluster     : choisi(Past); scngea(Past); passé(Past)
  Timex resolved   : none
  ±14-day window   : False
  → Correct label  : FALSE
  Reasoning        : Annotated training example from the train set.

Example 8:
  Person           : Gédéon le Contreleyu
  Location         : lac des Tailleres
  Publication date : 1928-01-17
  Language         : fr
  Text             : , comme l' appelaient ses amis) avait passé la majeure partie de g. vie dans cette vallée jurassienne où dans lés temps anciens vécurent (?) le Solitaire dès Sagnes et <PERSON>Gédéon le Contreleyu</PERSON>. Cet endroit avait été par lui choisi en une occasion mémorable, quand un beau jour, ou plutôt un malheureux soir, il s'était aventuré à demander Êour femme la grande Uranie Montandon du ronillet. A sa complète stupéfaction, il lui fut répondu négativement. Quand il demanda les raisons de ce refus, elle lui déclara tout uniment « qu'il sentait trop l'horloger >. Pendant une heure ou deux, l'Alcide scngea à se noyer de dépit dans le <LOCATION>lac des Tailleres</LOCATION>, mais son bon sens lui revenant ei l'instinct de conservation aidant, il se borna à secouer sur ce Sol ingrat la poussière de ses souliers et, quelque temps plus tard, alla planter sa tente aux Cœudres, pensant que son noir chagrin se fondrait dans les brouillards de la Sagne.
  Person context   : No Wikidata data available for this person.
  Temporal signals : ancien, plus, tôt, tard
  Verb cluster     : passé(Past); scngea(Past)
  Timex resolved   : none
  ±14-day window   : False
  → Correct label  : FALSE
  Reasoning        : Annotated training example from the train set.

Example 9:
  Person           : Louise Michel
  Location         : Havre
  Publication date : 1888-03-08
  Language         : de
  Text             : Gestern haben <PERSON>Louise Michel</PERSON> und ihre Freunde im Faubourg du Temple eine Ver sammlung abgehalten, in der nichts Bestehendes geschont und eine blutige Revolution herbeigewünscht wurde, um die mit Füßen getretene Ordnung und Gerechtigkeit wieder herzustellen. Den Vorwand zu dem Meeting gab das Todesurtheil ab, welches das Kriegsgericht in Numea über zwei Sträflinge, die Dynamithelden Cyvoct und Gallo, gefällt hat. Die beiden Deportirten hatten einen Unteroffizier überfallen, um ausreißen zu können, und nun nahm man in Paris eine Tagesordnung an, in der sie weiß wie Schnee neben ihren schwarzen Ty rannen, den Vollstreckern des Gesetzes, stehen. Aber nicht nur diese mußten herhalten, sondern auch der arme Joffrin, den seine Mitbürger von Belleville nicht in den Gemeinderath wählten, damit er den Bourgeois spiele und im Tuchrocke einhergehe, son dern um einen Vertreter der revolutionären In teressen im Stadthause zu haben, welcher Joffrin jetzt — o Schande! — allen anarchistischen Lehren zum Trotz als Vizepräsident im Vorstande sitzt! Es war das erste Mal, daß Louise Michel seit dem Attentate in <LOCATION>Havre</LOCATION> öffentlich auftrat, noch etwas magerer, aszetischer aussehend, als früher, aber mit ungebrochener Energie.
  Person context   : Label: Louise Michel | Description: französische Autorin und Anarchistin | Born: ['+1830-05-29T00:00:00Z'] | Died: ['+1905-01-09T00:00:00Z'] | Birth place: ['Q1331799'] | Death place: ['Q23482'] | Work locations: ['Q90']
  Temporal signals : jetzt, gestern, früher, vor, früh
  Verb cluster     : haben(Pres); war(Past)
  Timex resolved   : none
  ±14-day window   : False
  → Correct label  : FALSE
  Reasoning        : Annotated training example from the train set.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
END OF FEW-SHOT EXAMPLES

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOW CLASSIFY THE FOLLOWING SAMPLES.
Respond with exactly one line per sample in the format:
  Sample N | ID=<source_name__sample_idx>: LABEL
Valid labels: FALSE / TRUE
Use the ID exactly as shown in the sample header.
Do NOT add explanations, JSON, or blank lines between predictions.

────────────────────────────────────────────────────────────
Sample 0 [ID: test_de__124]:
  Publication date : 1948-08-27
  Language         : de
  Person  : 'Brigadier M. R. L. Robinson, ein\nMitarbeiter von Logan'  (QID: N/A)
  Location: 'Frankfurt a. M.'  (QID: Q1794)

  [ARTICLE TEXT — entity markers added]
  "Steigende Produktionsquote in Westdeutschland » <LOCATION>Frankfurt a. M.</LOCATION>, 27. August (AP). Die "wirtschaftliche Lage der Bi-Zone mache rasche Fortschritte, erklärte gestern der Direktor der J.E.I.A., W. John Logan. Die ProdMktàomsquote sei in den letzten beiden Monaten stark angestiegen und betrage jetzt 60 Prozent de s Standes von 1937. Zwei Faktoren, denen der beginnende Aufschwung mit zu verdanken sei, seien die im Juni durchgeführte Währungsreform und die Bemühungen der J.E.IA. um Belebung der Aus- und Einfuhr. Die Einfuhren in die Bi-Zone hätten in den ersten sieben Monaten dieses Jahres 282 400 000 Dollar und damit mehr betragen als im gesamten vorigen Jahr. Brigadier M. R. L. Robinson, ein Mitarbeiter von Logan, sagte vor Presse- 1 Vertretern, die Pläne zur Zusammenfassung der Wirtschaft der französischen Zone mit derjenigen .der britisch und amerikanisch besetzten Doppelzone würden vorangetrieben. Auf Befragen erklärte er, es seien keine unerwarteten Schwierigkeiten hierbei aufgetaucht. Er erinnerte daran, daß die Vereinigung der Wirtschaftsverwaltungen der britischen und der amerikanischen Zone sogar nach dem diesbezüglichen Beschluß einige Monate gedauert habe. Als mutmaßlichen Zeitpunkt für den Anschluß der Wirtschaft der französischen Zone nannte er den Beginn des nächsten Jahres. Logan nahm dann zu falschen Darstellungen im Zusammenhang mit der J.E.I.A. Stellung, die in verschiedenen Blättern von der sowjetisch lizenzierten „Berliner Zeitung" bis zu dem amerikanischen „Wall Street Journal" erschienen seien. Zu der Behauptung der „Berliner Zeitung", die J.E I.A. habe die Bi-Zone in eine „Zwangsjacke" gesteckt, um den Vereinigten - Staaten Profite zu verschaffen, sagte Logan: „Alle Erlöse aus den Bi-Zonen-Exporten wurden für Importe verwandt. Darüber hinaus werden die Vereinigten Staaten etwa ein« Milliarde Dollar für Lebensimiiitteleinfuhren nach Deutschland ausgeben. Wie kann man da von Profiten für Amerika sprechen?" Klarstellung der französischen Militärregierung zur Borsig-Demontage Berlin, 27. August. (AP). Wegen ungenauer und absichtlich irreführender Pressemeldungen über „Ausplünderung" der Rheinmetall-Borsigwerke in Berlin seitens der französischen Besetzungstruppen — die Meldungen waren in der sowjetisch lizenzierten Presse erschienen — veröffentlicht die französische Militärregierung folgende Klarstellung: 1. Bevor die französischen Behörden ihren Sektor in Berlin übernahmen, war von den sowjetischen Besatzungstruppen der größere Teil des Maschinenparks, das heißt rund 2000 Maschinen, eigenmächtig bereits demontiert und abtransportiert worden. 2. Vor dem Ausschul? für die Liquidierung von Rüstungsmaterial wurden die Rheinmetall-Borsigwerke am 15. Juni 1947 von den Vertretern der Sowjetunion, Englands und Frankreichs als Rüstungsbetrieb bezeichnet. Diese Entscheidung wurde am 29. Juli 1947 vom Koordinierungs-Ausschuß bestätigt. 3. In Erfüllung dieses Beschlusses wurde von den verantwortlichen sowjetischen, amerikanischen, britischen und französischen Behörden die Borsigwerke als reparationspfliahtig erklärt. 4. Nach den Bestimmungen dUese s Beschlusses verteilte die interalliierte Repairatdonsbehörde in Brüssel (IARA) Geräte dieses Betriebes an eine Anzahl von Mitgliedstaalten der Vereinten Nationen. Ausgenommen wurde dabei das elektrische Kraftwerk, das auf Ersuchen Frankreichs von der Reparationsliste gestrichen wurde. Die Mehrzahl der Maschinen wurde den Staaten Mittel- und Ost-Europas auf deren Bitten hin zugesprochein, vor allem der Tschechoslowakei und Jugoslawien. Frankreich erhielt von den 1800 Maschinen nur 100."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Frankfurt am Main
    Description: bevölkerungsreichste Stadt in Hessen, Deutschland
    Country: ['Fränkisches Reich', 'Ostfrankenreich', 'Heiliges Römisches Reich', 'Großherzogtum Frankfurt', 'Freie Stadt Frankfurt', 'Q151624', 'Q27306', 'Q1206012', 'Q41304', 'NS-Staat', 'Q2415901', 'Q713750', 'Q183']
    Located in: ['Regierungsbezirk Darmstadt', 'Q314243', 'Q704300']
    Aliases: {'en': ['Frankfurt/Main', 'Frankfurt (Main)', 'Kreisfreie Stadt Frankfurt am Main', 'Frankfort-on-the-Main', 'Frankfurt, Germany', 'Frankfurt am Main, Germany', 'Frankfurt am Main', 'Francfort'], 'fr': ['Francfort', 'Frankfurt am Main', 'Francfort-sur-le-Mein', 'Francfort-sur-le-main', 'Frankfurt'], 'de': ['Frankfurt', 'Frankfurt/Main', 'FFM', 'Frankfurt (Main)', 'Frankfurt a. M.', 'Ffm', 'Ffm.', 'Fft.', 'Frankfurt a.M.', 'Franckfurt am Mayn', 'Frankfurt a. Main', 'Internationale Messestadt'], 'lb': ['Frankfurt', 'Frankfurt/Main']}
    Coordinates: [{'lat': 50.11055555555556, 'lon': 8.682222222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (5):
      - "1937" → 1937
      - "2000" → 2000
      - "1947" → 1947
      - "1947" → 1947
      - "1800" → 1800
    Temporal signal words: jetzt, gestern, nach, vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    OCR quality estimate: 0.961

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Brigadier M. R. L. Robinson, ein\nMitarbeiter von Logan' and 'Frankfurt a. M.' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Brigadier M. R. L. Robinson, ein\nMitarbeiter von Logan' near 'Frankfurt a. M.' around 1948-08-27?
  4. Resolve temporal expressions relative to 1948-08-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 1 [ID: test_de__168]:
  Publication date : 1848-08-26
  Language         : de
  Person  : 'Republikaner\nEdgar Bauer'  (QID: Q67299)
  Location: 'Charlottenburg'  (QID: Q162049)

  [ARTICLE TEXT — entity markers added]
  "Deutschland. Preußen. Berlin. In <LOCATION>Charlottenburg</LOCATION> kam es am 20. d. zwischen dem Preußenverein und dem demo kratischen Verein zu Schlägereien. Laut einer Korrespondenz der Fr. O. P. Z. bediente sich der Preußenverein eines Lokals, das der Demokratenverein zu seinen Zusammenkünften benutzte und dieser verlangte Räumung desselben. Aus Wortwechsel entsteht Handgemenge, und so kam es zu einer ernsthaften Prügelei. Die Demokraten ergriffen zum Theil die Flucht, um den Schlägen der „Preußen" zu entgehen; einige verkrochen sich in Ställen, andere sogar in Schornsteinen. Bei der Flucht war einer so un klug, auf der Straße „Republik" zu brüllen. Er wurde von nachsetzenden Verfolgern niedergeschlagen. Die vorgekommenen Verwundungen sind so bedeutend, daß man selbst an dem Auf kommen einzelner Personen zweifelt. Auch der Republikaner Edgar Bauer ist arg zugerichtet. So berichtet u. a. dieser Kor respondent, der ferner hinzufügt, wie in Folge dieser Auftritte Berlin selbst in Aufregung gerieth. Eine Menge Arbeiter setzte sich in Bewegung. Dieselbe endigte jedoch mit der Verhaftung von 10 Führern der Arbeiter. Unter den Linden blieben jedoch namhafte Gruppen versammelt, die mit dem Plane umgingen, sich Charlottenburg zu nahen. Weiter geht der Bericht nicht."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Edgar Bauer
    Description: philosophischer Schriftsteller
    Born: ['+1820-10-07T00:00:00Z']
    Died: ['+1886-08-18T00:00:00Z']
    Birth place: ['Q162049']
    Death place: ['Q1715', 'Berlin']
  Location Wikidata:
    Label: Charlottenburg
    Description: Ortsteil von Berlin
    Country: ['Q183', 'Q43287']
    Located in: ['Charlottenburg-Wilmersdorf', 'Q853708', 'Q827186', 'Q1803494', 'Q932182']
    Aliases: {'en': ['Berlin-Charlottenburg'], 'fr': ['Berlin-Charlottenbourg'], 'de': ['Berlin-Charlottenburg']}
    Coordinates: [{'lat': 52.516666666667, 'lon': 13.3}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.989

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Republikaner\nEdgar Bauer' and 'Charlottenburg' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Republikaner\nEdgar Bauer' near 'Charlottenburg' around 1848-08-26?
  4. Resolve temporal expressions relative to 1848-08-26. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 2 [ID: test_de__20]:
  Publication date : 1848-12-15
  Language         : de
  Person  : 'General-Administrator des Innern,\nUlrich'  (QID: N/A)
  Location: 'Cantons Diekirch'  (QID: Q691842)

  [ARTICLE TEXT — entity markers added]
  "Die Wahlcollegien der <LOCATION>Cantons Diekirch</LOCATION> und Sa« pellen werden auf Donnerstag, den 21. Dezember d. 1., zehn Uhr Vormittags, zusammenberufen, um jedes einen Abgeordneten zu respectiver Ersetzung der Herrn Ulrich und N. Metz zu wählen. Der General-Administrator des Innern, Ulrich. Die neve, durch Beschlüsse bei» Königs GroßherzogS vom 2. d. M. angeordnete Regierung, welche Unterm heutigen Tage in Thätigkeit getreten ist, hat sofort über cine vorläufig anzunehmende Und der Könlgllch'Großhelzoglichen Genehmigung vorbehaltene Vertheilung der öffentlichen Dienstzweige unter ihre vier Mitglieder Folgende beschlossen: 1. Die General'Admmistration der auswärtigen Angelegenheiten, der Justiz und der Culte ist Herrn Willmai übertragen; die des Inneren Hrn. Ulrich; die der Gemeinde-Angelegenheiten Hrn. Ulveling, und die der Finanzen Hrn. Norbert Metz. 2. Die Genetal-Administration der öffentlichen Staats- und Gemeindebauten und der Militär-Ange» legenheiten ist vorläufig in der Art geseilt, daß vor» läusig die General-Administration der öffentlichen Bauten mit der bei} Inneren, «nd die der Militär« Angelegenheiten mit der der Finanzen vereinigt ist. 3. Auch ist vorläufig der öffentliche Unterricht von der General-Administration des Inneren getrennt und mit der der auswärtigen Angelegenheiten, der Justiz und der Culte verbunden. Der einstweilige Gcneral»Administrator, Präsident des Conseils, Willmar. Bekanntmachung , betreffend den Dienstantritt der neuen General'Admimstratoren und die neve Verthei- Ittrtg der verschiedenen Dienstzweige unter dieselben» Luxemburg, de« 6. Dezembet 1848."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Kanton Diekirch
    Description: Kanton in Luxemburg
    Country: ['Luxemburg']
    Located in: ['Distrikt Diekirch', 'Q32']
    Aliases: {'fr': ['Diekirch']}
    Coordinates: [{'lat': 49.8, 'lon': 6.2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1848" → 1848
    Temporal signal words: vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.963

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'General-Administrator des Innern,\nUlrich' and 'Cantons Diekirch' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'General-Administrator des Innern,\nUlrich' near 'Cantons Diekirch' around 1848-12-15?
  4. Resolve temporal expressions relative to 1848-12-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 3 [ID: test_de__33]:
  Publication date : 1858-02-07
  Language         : de
  Person  : 'jetzige nominelle Herausgeber, Brismee'  (QID: N/A)
  Location: 'Brüssel'  (QID: Q239)

  [ARTICLE TEXT — entity markers added]
  "Belgien. <LOCATION>Brüssel</LOCATION> 31. Jan. Als Verfasser deS im „Dra» pcau" erschienenen und angeklagten Artikels wird jetzt der frühere Rédacteur des Blattes, Louis Labarre, genannt. Der <PERSON>jetzige nominelle Herausgeber, Brismee</PERSON>, soll diesmal seine verantwortliche Haut nicht zu Markte tragen wollen, da ihm noch das Jahr Gefängnis), was cc vor Kurzem abgesessen, in den Gliedern liege. Gro» Bes Aufsehen macht ein neuer Artikel in Bezug auf das Attentat, der vor einigen Tagen in einem kleinen Blatte, der „Proletarier" betitelt, erschienen ist. Dieses giftige Blatt steht mit dem socialen Handwerkervereine in London in Verbindung und wird von einem rabiaten Schneider, Namens Coulon, redigirt. Das Attentat wird in diesem Artikel mit perfider Frechheit verherr licht, und zugleich werden Orsini und Pierri als Helden ausgerufen und für ihre That mit dem Beifalle des Wahnwitzes überschüttet. Mr. Coulon, der kühne Schneider, wird mit den Rédacteur?« des „Drapeau" und „Crocodile" zusammen demnächst vor Gericht zu erscheinen haben. sM. I.)"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: jetzt, früher, vor, früh
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.993

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'jetzige nominelle Herausgeber, Brismee' and 'Brüssel' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'jetzige nominelle Herausgeber, Brismee' near 'Brüssel' around 1858-02-07?
  4. Resolve temporal expressions relative to 1858-02-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 4 [ID: test_de__204]:
  Publication date : 1808-04-29
  Language         : de
  Person  : 'General Hutchinson'  (QID: Q321765)
  Location: 'Bartenstein'  (QID: Q809585)

  [ARTICLE TEXT — entity markers added]
  "henden und glücklichen Zustande gelebt habe, und daß kein Beweggrund ihn jemals dahin bringen könne, von diesem Vorsatze abzustehen. Se. Kaiserl. Majestät fügten hinzu, daß ich den festen Karakter des Kronprinzen hinlänglich ken nen müße, um zu wissen, daß nichts schwerer sey, als seine Entschlüsse zu erschüttern, oder ihn zu bewegen, ein ein mal angenommenes System zu verlassen, und daß er, der Kaiser, überzeugt sey, es habe vor unserm Angriff auf Ro (Aus dem danischen Blatte Dagen.) Da das engli sche Ministerium die englische Nation versichert hat, daß den Kaiser von Rußland Anfangs nicht das geringste Miß vergnügen über den Raubzug nach Seeland geäussert habe, so wird man nicht ohne Interesse nachstehende Erläuterun gen über eine, zwischen dem Kaiser von Rußland und dem <PERSON>General Hutchinson</PERSON> vorgefallene, Unterredung lesen. Se. Kaiserl. Majestät — so berichtet der General Hutchinson — flengen die Unterredung mit der Frage an, was ich von unserm Angriff auf Kopenhagen denke? Ich erwiederte, daß mir die Umstände, welche solchen veranlaßt hätten, zwar ganz unbekannt wären, daß ich aber hoffe, die englische Administration werde sich rechtfertigen, und der ganzen Welt beweisen können, daß die Dänen im Begriff waren, ihre ganze Macht mit der französischen gegen England zu vereinigen. Se. Kaiserl. Majestät bemerkten, daß ich un möglich dieser Meynung seyn könne, wenn ich noch der Un terredungen gedächte, die wir in <LOCATION>Bartenstein</LOCATION> gehabt hät ten. In diesen sagte der Kaiser mir, er habe alle mögliche Mühe angewandt, um den Kronprinzen von Dänemark zu! vermögen, der Koalition gegen Frankreich beyzutreten; daß aber die Antwort des Prinzen immer deutlich und un verändert dieselbe gewesen sey, daß er viele Jahre lang ein Neutralitätssystem behauptet habe, bey dem er zu beharren fest entschlossen sey; da sein Volk dadurch in einem blü und dänischen Regierung statt gefunden. Ich sagte dar auf, ich glaubte, daß der Lord Gower dem Kaiserl Mi nisterium über diesen Gegenstand eine Note übergeben habe, worauf Se. Majestät erwiederten, daß dies sich so verhalte, daß aber der Inhalt der Note lächerlich sey, da solche we der hinlängliche Auskunft enthalte, noch irgend eine Genug thuung anbiete. Se. Kaiserl. Majestät sprachen darnächst von der großen Betrübniß, die Ihnen durch unsern unver antwortlichen Angriff verursacht worden, und daß nie et was Aehnliches geschehen sey; daß, wenn ein solches Ver fahren gelten sollte, alle Verhältnisse, die das Verfahren der Nationen gegen einander bisher bestimmt hätten, zu Grunde gehen würden, und daß in dem Falle ein jeder thun könnte, was ihm beliebe. Se. Kaiserl. Majestät sagten mir in den bestimmtesten Ausdrücken, mit dem festesten Tone, daß er Genugthuung für diesen, ohne alle Veranlassung un ternommenen, Angriff fordere; daß dies seine Pflicht, als Kaiser von Rußland, sey, und daß er Genugthuung wolle. Er fragte mich, ob ich wagen dürfe, über diesen Gegenstand anderer Meynung, als er, zu seyn? Er sagte ferner; daß die feyerlichsten Traktate und Verpflichtungen ihn mit Dä nemark verbänden, und daß er entschlossen sey, solche zu erfüllen. Se Kaiserl. Majestät fügten hinzu, er vermuthe, wir dächten auf einen Angriff auf Kronstadt; daß er zwar den Ausgang eines solchen Angriffs nicht vorhersehen könne, daß er aber bis zum letzten Mann Widerstand leisten, und sich des hohen Postens, worauf ihn die Vorsehung gestellt habe, nicht unwürdig bezeigen wolle. — Ich antwortete, ich hätte alle Ursache zu heffen und zu glauben, daß wir auf Kronstadt keinen Angriff thun würden. Er entgegnete, daß er darauf gefaßt, und sein Entschluß unerschütterlich sey. Darauf endigte er das Gespräch, und wiederholte mit vielem Nachdruck: „Daß er Genugthuung für Dänemark wolle Der Freymüthige vom 7. April enthält Folgendes: Hamburger-Korrespondenten wird, von Petersburg aus, angedeutet, und in der neuesten Berlinischen Zeitung aus gesprochen, daß H. von Rotzebue in Ehstland gestorben sey. Man hat viele Gründe, die Authentizität dieser Nach richt zu bezweifeln; merkwürdig ist übrigens die Eilfertig keit, mit der man dem Publikum unverbürgte Notizen mit theilt, die für dasselbe tief erschütternd seyn müßen!" Das *Am 22. Merz sah man auf der großen Parade zu Peters burg 4. eroberte schwedische Fahnen und eine Flagge die General Burhöyden eingeschickt hatte."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Bartoszyce
    Description: Stadt in Polen
    Country: ['Q36']
    Located in: ['Q1130338', 'Landkreis Bartenstein (Ostpr.)', 'Q9269801']
    Aliases: {'en': ['Bartenstein', 'Barštynas'], 'fr': ['Bartenstein', 'Barštynas'], 'de': ['Bartenstein', 'Barštynas']}
    Coordinates: [{'lat': 54.25354, 'lon': 20.80819}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.995

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'General Hutchinson' and 'Bartenstein' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'General Hutchinson' near 'Bartenstein' around 1808-04-29?
  4. Resolve temporal expressions relative to 1808-04-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 5 [ID: test_de__31]:
  Publication date : 1858-02-07
  Language         : de
  Person  : 'jetzige nominelle Herausgeber, Brismee'  (QID: N/A)
  Location: 'Belgien'  (QID: Q31)

  [ARTICLE TEXT — entity markers added]
  "<LOCATION>Belgien</LOCATION>. Brüssel 31. Jan. Als Verfasser deS im „Dra» pcau" erschienenen und angeklagten Artikels wird jetzt der frühere Rédacteur des Blattes, Louis Labarre, genannt. Der <PERSON>jetzige nominelle Herausgeber, Brismee</PERSON>, soll diesmal seine verantwortliche Haut nicht zu Markte tragen wollen, da ihm noch das Jahr Gefängnis), was cc vor Kurzem abgesessen, in den Gliedern liege. Gro» Bes Aufsehen macht ein neuer Artikel in Bezug auf das Attentat, der vor einigen Tagen in einem kleinen Blatte, der „Proletarier" betitelt, erschienen ist. Dieses giftige Blatt steht mit dem socialen Handwerkervereine in London in Verbindung und wird von einem rabiaten Schneider, Namens Coulon, redigirt. Das Attentat wird in diesem Artikel mit perfider Frechheit verherr licht, und zugleich werden Orsini und Pierri als Helden ausgerufen und für ihre That mit dem Beifalle des Wahnwitzes überschüttet. Mr. Coulon, der kühne Schneider, wird mit den Rédacteur?« des „Drapeau" und „Crocodile" zusammen demnächst vor Gericht zu erscheinen haben. sM. I.)"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Belgien
    Description: föderaler Staat in Westeuropa
    Country: ['Belgien']
    Aliases: {'en': ['Kingdom of Belgium'], 'fr': ['Royaume de Belgique', 'Belg.'], 'de': ['Königreich Belgien'], 'lb': ['Kinnekräich Belsch']}
    Coordinates: [{'lat': 50.641111111111, 'lon': 4.6680555555556}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: jetzt, früher, vor, früh
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.993

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'jetzige nominelle Herausgeber, Brismee' and 'Belgien' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'jetzige nominelle Herausgeber, Brismee' near 'Belgien' around 1858-02-07?
  4. Resolve temporal expressions relative to 1858-02-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 6 [ID: test_de__29]:
  Publication date : 1858-02-07
  Language         : de
  Person  : 'frühere Rédacteur des Blattes, Louis Labarre'  (QID: Q4251818)
  Location: 'Brüssel'  (QID: Q239)

  [ARTICLE TEXT — entity markers added]
  "Belgien. <LOCATION>Brüssel</LOCATION> 31. Jan. Als Verfasser deS im „Dra» pcau" erschienenen und angeklagten Artikels wird jetzt der <PERSON>frühere Rédacteur des Blattes, Louis Labarre</PERSON>, genannt. Der jetzige nominelle Herausgeber, Brismee, soll diesmal seine verantwortliche Haut nicht zu Markte tragen wollen, da ihm noch das Jahr Gefängnis), was cc vor Kurzem abgesessen, in den Gliedern liege. Gro» Bes Aufsehen macht ein neuer Artikel in Bezug auf das Attentat, der vor einigen Tagen in einem kleinen Blatte, der „Proletarier" betitelt, erschienen ist. Dieses giftige Blatt steht mit dem socialen Handwerkervereine in London in Verbindung und wird von einem rabiaten Schneider, Namens Coulon, redigirt. Das Attentat wird in diesem Artikel mit perfider Frechheit verherr licht, und zugleich werden Orsini und Pierri als Helden ausgerufen und für ihre That mit dem Beifalle des Wahnwitzes überschüttet. Mr. Coulon, der kühne Schneider, wird mit den Rédacteur?« des „Drapeau" und „Crocodile" zusammen demnächst vor Gericht zu erscheinen haben. sM. I.)"

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: jetzt, früher, vor, früh
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.993

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'frühere Rédacteur des Blattes, Louis Labarre' and 'Brüssel' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'frühere Rédacteur des Blattes, Louis Labarre' near 'Brüssel' around 1858-02-07?
  4. Resolve temporal expressions relative to 1858-02-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 7 [ID: test_de__167]:
  Publication date : 1848-08-26
  Language         : de
  Person  : 'Republikaner\nEdgar Bauer'  (QID: Q67299)
  Location: 'Unter den Linden'  (QID: Q160899)

  [ARTICLE TEXT — entity markers added]
  "Deutschland. Preußen. Berlin. In Charlottenburg kam es am 20. d. zwischen dem Preußenverein und dem demo kratischen Verein zu Schlägereien. Laut einer Korrespondenz der Fr. O. P. Z. bediente sich der Preußenverein eines Lokals, das der Demokratenverein zu seinen Zusammenkünften benutzte und dieser verlangte Räumung desselben. Aus Wortwechsel entsteht Handgemenge, und so kam es zu einer ernsthaften Prügelei. Die Demokraten ergriffen zum Theil die Flucht, um den Schlägen der „Preußen" zu entgehen; einige verkrochen sich in Ställen, andere sogar in Schornsteinen. Bei der Flucht war einer so un klug, auf der Straße „Republik" zu brüllen. Er wurde von nachsetzenden Verfolgern niedergeschlagen. Die vorgekommenen Verwundungen sind so bedeutend, daß man selbst an dem Auf kommen einzelner Personen zweifelt. Auch der Republikaner Edgar Bauer ist arg zugerichtet. So berichtet u. a. dieser Kor respondent, der ferner hinzufügt, wie in Folge dieser Auftritte Berlin selbst in Aufregung gerieth. Eine Menge Arbeiter setzte sich in Bewegung. Dieselbe endigte jedoch mit der Verhaftung von 10 Führern der Arbeiter. <LOCATION>Unter den Linden</LOCATION> blieben jedoch namhafte Gruppen versammelt, die mit dem Plane umgingen, sich Charlottenburg zu nahen. Weiter geht der Bericht nicht."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Unter den Linden
    Description: Prachtstraße in Berlin
    Country: ['Q183']
    Located in: ['Q163966']
    Aliases: {'de': ['Straße Unter den Linden', 'UdL']}
    Coordinates: [{'lat': 52.51658, 'lon': 13.381}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.989

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Republikaner\nEdgar Bauer' and 'Unter den Linden' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Republikaner\nEdgar Bauer' near 'Unter den Linden' around 1848-08-26?
  4. Resolve temporal expressions relative to 1848-08-26. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 8 [ID: test_de__23]:
  Publication date : 1848-12-15
  Language         : de
  Person  : 'Herrn\nWillmai'  (QID: Q738855)
  Location: 'Cantons Diekirch'  (QID: Q691842)

  [ARTICLE TEXT — entity markers added]
  "Die Wahlcollegien der <LOCATION>Cantons Diekirch</LOCATION> und Sa« pellen werden auf Donnerstag, den 21. Dezember d. 1., zehn Uhr Vormittags, zusammenberufen, um jedes einen Abgeordneten zu respectiver Ersetzung der Herrn Ulrich und N. Metz zu wählen. Der General-Administrator des Innern, Ulrich. Die neve, durch Beschlüsse bei» Königs GroßherzogS vom 2. d. M. angeordnete Regierung, welche Unterm heutigen Tage in Thätigkeit getreten ist, hat sofort über cine vorläufig anzunehmende Und der Könlgllch'Großhelzoglichen Genehmigung vorbehaltene Vertheilung der öffentlichen Dienstzweige unter ihre vier Mitglieder Folgende beschlossen: 1. Die General'Admmistration der auswärtigen Angelegenheiten, der Justiz und der Culte ist Herrn Willmai übertragen; die des Inneren Hrn. Ulrich; die der Gemeinde-Angelegenheiten Hrn. Ulveling, und die der Finanzen Hrn. Norbert Metz. 2. Die Genetal-Administration der öffentlichen Staats- und Gemeindebauten und der Militär-Ange» legenheiten ist vorläufig in der Art geseilt, daß vor» läusig die General-Administration der öffentlichen Bauten mit der bei} Inneren, «nd die der Militär« Angelegenheiten mit der der Finanzen vereinigt ist. 3. Auch ist vorläufig der öffentliche Unterricht von der General-Administration des Inneren getrennt und mit der der auswärtigen Angelegenheiten, der Justiz und der Culte verbunden. Der einstweilige Gcneral»Administrator, Präsident des Conseils, Willmar. Bekanntmachung , betreffend den Dienstantritt der neuen General'Admimstratoren und die neve Verthei- Ittrtg der verschiedenen Dienstzweige unter dieselben» Luxemburg, de« 6. Dezembet 1848."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1848" → 1848
    Temporal signal words: vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.963

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Herrn\nWillmai' and 'Cantons Diekirch' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Herrn\nWillmai' near 'Cantons Diekirch' around 1848-12-15?
  4. Resolve temporal expressions relative to 1848-12-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 9 [ID: test_de__205]:
  Publication date : 1808-04-29
  Language         : de
  Person  : 'General Hutchinson'  (QID: Q321765)
  Location: 'Dä\nnemark'  (QID: Q35)

  [ARTICLE TEXT — entity markers added]
  "henden und glücklichen Zustande gelebt habe, und daß kein Beweggrund ihn jemals dahin bringen könne, von diesem Vorsatze abzustehen. Se. Kaiserl. Majestät fügten hinzu, daß ich den festen Karakter des Kronprinzen hinlänglich ken nen müße, um zu wissen, daß nichts schwerer sey, als seine Entschlüsse zu erschüttern, oder ihn zu bewegen, ein ein mal angenommenes System zu verlassen, und daß er, der Kaiser, überzeugt sey, es habe vor unserm Angriff auf Ro (Aus dem danischen Blatte Dagen.) Da das engli sche Ministerium die englische Nation versichert hat, daß den Kaiser von Rußland Anfangs nicht das geringste Miß vergnügen über den Raubzug nach Seeland geäussert habe, so wird man nicht ohne Interesse nachstehende Erläuterun gen über eine, zwischen dem Kaiser von Rußland und dem <PERSON>General Hutchinson</PERSON> vorgefallene, Unterredung lesen. Se. Kaiserl. Majestät — so berichtet der General Hutchinson — flengen die Unterredung mit der Frage an, was ich von unserm Angriff auf Kopenhagen denke? Ich erwiederte, daß mir die Umstände, welche solchen veranlaßt hätten, zwar ganz unbekannt wären, daß ich aber hoffe, die englische Administration werde sich rechtfertigen, und der ganzen Welt beweisen können, daß die Dänen im Begriff waren, ihre ganze Macht mit der französischen gegen England zu vereinigen. Se. Kaiserl. Majestät bemerkten, daß ich un möglich dieser Meynung seyn könne, wenn ich noch der Un terredungen gedächte, die wir in Bartenstein gehabt hät ten. In diesen sagte der Kaiser mir, er habe alle mögliche Mühe angewandt, um den Kronprinzen von Dänemark zu! vermögen, der Koalition gegen Frankreich beyzutreten; daß aber die Antwort des Prinzen immer deutlich und un verändert dieselbe gewesen sey, daß er viele Jahre lang ein Neutralitätssystem behauptet habe, bey dem er zu beharren fest entschlossen sey; da sein Volk dadurch in einem blü und dänischen Regierung statt gefunden. Ich sagte dar auf, ich glaubte, daß der Lord Gower dem Kaiserl Mi nisterium über diesen Gegenstand eine Note übergeben habe, worauf Se. Majestät erwiederten, daß dies sich so verhalte, daß aber der Inhalt der Note lächerlich sey, da solche we der hinlängliche Auskunft enthalte, noch irgend eine Genug thuung anbiete. Se. Kaiserl. Majestät sprachen darnächst von der großen Betrübniß, die Ihnen durch unsern unver antwortlichen Angriff verursacht worden, und daß nie et was Aehnliches geschehen sey; daß, wenn ein solches Ver fahren gelten sollte, alle Verhältnisse, die das Verfahren der Nationen gegen einander bisher bestimmt hätten, zu Grunde gehen würden, und daß in dem Falle ein jeder thun könnte, was ihm beliebe. Se. Kaiserl. Majestät sagten mir in den bestimmtesten Ausdrücken, mit dem festesten Tone, daß er Genugthuung für diesen, ohne alle Veranlassung un ternommenen, Angriff fordere; daß dies seine Pflicht, als Kaiser von Rußland, sey, und daß er Genugthuung wolle. Er fragte mich, ob ich wagen dürfe, über diesen Gegenstand anderer Meynung, als er, zu seyn? Er sagte ferner; daß die feyerlichsten Traktate und Verpflichtungen ihn mit Dä nemark verbänden, und daß er entschlossen sey, solche zu erfüllen. Se Kaiserl. Majestät fügten hinzu, er vermuthe, wir dächten auf einen Angriff auf Kronstadt; daß er zwar den Ausgang eines solchen Angriffs nicht vorhersehen könne, daß er aber bis zum letzten Mann Widerstand leisten, und sich des hohen Postens, worauf ihn die Vorsehung gestellt habe, nicht unwürdig bezeigen wolle. — Ich antwortete, ich hätte alle Ursache zu heffen und zu glauben, daß wir auf Kronstadt keinen Angriff thun würden. Er entgegnete, daß er darauf gefaßt, und sein Entschluß unerschütterlich sey. Darauf endigte er das Gespräch, und wiederholte mit vielem Nachdruck: „Daß er Genugthuung für Dänemark wolle Der Freymüthige vom 7. April enthält Folgendes: Hamburger-Korrespondenten wird, von Petersburg aus, angedeutet, und in der neuesten Berlinischen Zeitung aus gesprochen, daß H. von Rotzebue in Ehstland gestorben sey. Man hat viele Gründe, die Authentizität dieser Nach richt zu bezweifeln; merkwürdig ist übrigens die Eilfertig keit, mit der man dem Publikum unverbürgte Notizen mit theilt, die für dasselbe tief erschütternd seyn müßen!" Das *Am 22. Merz sah man auf der großen Parade zu Peters burg 4. eroberte schwedische Fahnen und eine Flagge die General Burhöyden eingeschickt hatte."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Dänemark
    Description: Staat in Nordeuropa und Nordamerika
    Country: ['Königreich Dänemark']
    Located in: ['Königreich Dänemark', 'Q62623']
    Aliases: {'en': ['dk', 'TAN', 'Denmark proper', 'metropolitan Denmark', 'Dania'], 'fr': ['DK', 'Dan.', 'Danemark propre', 'Danemark métropolitain']}
    Coordinates: [{'lat': 56, 'lon': 10}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.995

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'General Hutchinson' and 'Dä\nnemark' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'General Hutchinson' near 'Dä\nnemark' around 1808-04-29?
  4. Resolve temporal expressions relative to 1808-04-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 10 [ID: test_de__166]:
  Publication date : 1848-08-26
  Language         : de
  Person  : 'Republikaner\nEdgar Bauer'  (QID: Q67299)
  Location: 'Berlin'  (QID: Q64)

  [ARTICLE TEXT — entity markers added]
  "Deutschland. Preußen. <LOCATION>Berlin</LOCATION>. In Charlottenburg kam es am 20. d. zwischen dem Preußenverein und dem demo kratischen Verein zu Schlägereien. Laut einer Korrespondenz der Fr. O. P. Z. bediente sich der Preußenverein eines Lokals, das der Demokratenverein zu seinen Zusammenkünften benutzte und dieser verlangte Räumung desselben. Aus Wortwechsel entsteht Handgemenge, und so kam es zu einer ernsthaften Prügelei. Die Demokraten ergriffen zum Theil die Flucht, um den Schlägen der „Preußen" zu entgehen; einige verkrochen sich in Ställen, andere sogar in Schornsteinen. Bei der Flucht war einer so un klug, auf der Straße „Republik" zu brüllen. Er wurde von nachsetzenden Verfolgern niedergeschlagen. Die vorgekommenen Verwundungen sind so bedeutend, daß man selbst an dem Auf kommen einzelner Personen zweifelt. Auch der Republikaner Edgar Bauer ist arg zugerichtet. So berichtet u. a. dieser Kor respondent, der ferner hinzufügt, wie in Folge dieser Auftritte Berlin selbst in Aufregung gerieth. Eine Menge Arbeiter setzte sich in Bewegung. Dieselbe endigte jedoch mit der Verhaftung von 10 Führern der Arbeiter. Unter den Linden blieben jedoch namhafte Gruppen versammelt, die mit dem Plane umgingen, sich Charlottenburg zu nahen. Weiter geht der Bericht nicht."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Edgar Bauer
    Description: philosophischer Schriftsteller
    Born: ['+1820-10-07T00:00:00Z']
    Died: ['+1886-08-18T00:00:00Z']
    Birth place: ['Q162049']
    Death place: ['Q1715', 'Q64']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: {"death_place": "P20"}

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.989

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Republikaner\nEdgar Bauer' and 'Berlin' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Republikaner\nEdgar Bauer' near 'Berlin' around 1848-08-26?
  4. Resolve temporal expressions relative to 1848-08-26. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 11 [ID: test_de__170]:
  Publication date : 1848-08-26
  Language         : de
  Person  : 'Republikaner\nEdgar Bauer'  (QID: Q67299)
  Location: 'Deutschland'  (QID: Q183)

  [ARTICLE TEXT — entity markers added]
  "<LOCATION>Deutschland</LOCATION>. Preußen. Berlin. In Charlottenburg kam es am 20. d. zwischen dem Preußenverein und dem demo kratischen Verein zu Schlägereien. Laut einer Korrespondenz der Fr. O. P. Z. bediente sich der Preußenverein eines Lokals, das der Demokratenverein zu seinen Zusammenkünften benutzte und dieser verlangte Räumung desselben. Aus Wortwechsel entsteht Handgemenge, und so kam es zu einer ernsthaften Prügelei. Die Demokraten ergriffen zum Theil die Flucht, um den Schlägen der „Preußen" zu entgehen; einige verkrochen sich in Ställen, andere sogar in Schornsteinen. Bei der Flucht war einer so un klug, auf der Straße „Republik" zu brüllen. Er wurde von nachsetzenden Verfolgern niedergeschlagen. Die vorgekommenen Verwundungen sind so bedeutend, daß man selbst an dem Auf kommen einzelner Personen zweifelt. Auch der Republikaner Edgar Bauer ist arg zugerichtet. So berichtet u. a. dieser Kor respondent, der ferner hinzufügt, wie in Folge dieser Auftritte Berlin selbst in Aufregung gerieth. Eine Menge Arbeiter setzte sich in Bewegung. Dieselbe endigte jedoch mit der Verhaftung von 10 Führern der Arbeiter. Unter den Linden blieben jedoch namhafte Gruppen versammelt, die mit dem Plane umgingen, sich Charlottenburg zu nahen. Weiter geht der Bericht nicht."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Deutschland
    Description: Staat in Mitteleuropa
    Country: ['Deutschland']
    Aliases: {'en': ['Federal Republic of Germany'], 'fr': ['RFA', "République fédérale d'Allemagne", 'République fédérale allemande', 'la République fédérale d’Allemagne', 'All.', 'R. F. A.'], 'de': ['Bundesrepublik Deutschland', 'BR Deutschland']}
    Coordinates: [{'lat': 51, 'lon': 10}, {'lat': 51.5, 'lon': 10.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.989

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Republikaner\nEdgar Bauer' and 'Deutschland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Republikaner\nEdgar Bauer' near 'Deutschland' around 1848-08-26?
  4. Resolve temporal expressions relative to 1848-08-26. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 12 [ID: test_de__115]:
  Publication date : 1948-08-27
  Language         : de
  Person  : 'Direktor der J.E.I.A., W. John Logan'  (QID: N/A)
  Location: 'Frankfurt a. M.'  (QID: Q1794)

  [ARTICLE TEXT — entity markers added]
  "Steigende Produktionsquote in Westdeutschland » <LOCATION>Frankfurt a. M.</LOCATION>, 27. August (AP). Die "wirtschaftliche Lage der Bi-Zone mache rasche Fortschritte, erklärte gestern der <PERSON>Direktor der J.E.I.A., W. John Logan</PERSON>. Die ProdMktàomsquote sei in den letzten beiden Monaten stark angestiegen und betrage jetzt 60 Prozent de s Standes von 1937. Zwei Faktoren, denen der beginnende Aufschwung mit zu verdanken sei, seien die im Juni durchgeführte Währungsreform und die Bemühungen der J.E.IA. um Belebung der Aus- und Einfuhr. Die Einfuhren in die Bi-Zone hätten in den ersten sieben Monaten dieses Jahres 282 400 000 Dollar und damit mehr betragen als im gesamten vorigen Jahr. Brigadier M. R. L. Robinson, ein Mitarbeiter von Logan, sagte vor Presse- 1 Vertretern, die Pläne zur Zusammenfassung der Wirtschaft der französischen Zone mit derjenigen .der britisch und amerikanisch besetzten Doppelzone würden vorangetrieben. Auf Befragen erklärte er, es seien keine unerwarteten Schwierigkeiten hierbei aufgetaucht. Er erinnerte daran, daß die Vereinigung der Wirtschaftsverwaltungen der britischen und der amerikanischen Zone sogar nach dem diesbezüglichen Beschluß einige Monate gedauert habe. Als mutmaßlichen Zeitpunkt für den Anschluß der Wirtschaft der französischen Zone nannte er den Beginn des nächsten Jahres. Logan nahm dann zu falschen Darstellungen im Zusammenhang mit der J.E.I.A. Stellung, die in verschiedenen Blättern von der sowjetisch lizenzierten „Berliner Zeitung" bis zu dem amerikanischen „Wall Street Journal" erschienen seien. Zu der Behauptung der „Berliner Zeitung", die J.E I.A. habe die Bi-Zone in eine „Zwangsjacke" gesteckt, um den Vereinigten - Staaten Profite zu verschaffen, sagte Logan: „Alle Erlöse aus den Bi-Zonen-Exporten wurden für Importe verwandt. Darüber hinaus werden die Vereinigten Staaten etwa ein« Milliarde Dollar für Lebensimiiitteleinfuhren nach Deutschland ausgeben. Wie kann man da von Profiten für Amerika sprechen?" Klarstellung der französischen Militärregierung zur Borsig-Demontage Berlin, 27. August. (AP). Wegen ungenauer und absichtlich irreführender Pressemeldungen über „Ausplünderung" der Rheinmetall-Borsigwerke in Berlin seitens der französischen Besetzungstruppen — die Meldungen waren in der sowjetisch lizenzierten Presse erschienen — veröffentlicht die französische Militärregierung folgende Klarstellung: 1. Bevor die französischen Behörden ihren Sektor in Berlin übernahmen, war von den sowjetischen Besatzungstruppen der größere Teil des Maschinenparks, das heißt rund 2000 Maschinen, eigenmächtig bereits demontiert und abtransportiert worden. 2. Vor dem Ausschul? für die Liquidierung von Rüstungsmaterial wurden die Rheinmetall-Borsigwerke am 15. Juni 1947 von den Vertretern der Sowjetunion, Englands und Frankreichs als Rüstungsbetrieb bezeichnet. Diese Entscheidung wurde am 29. Juli 1947 vom Koordinierungs-Ausschuß bestätigt. 3. In Erfüllung dieses Beschlusses wurde von den verantwortlichen sowjetischen, amerikanischen, britischen und französischen Behörden die Borsigwerke als reparationspfliahtig erklärt. 4. Nach den Bestimmungen dUese s Beschlusses verteilte die interalliierte Repairatdonsbehörde in Brüssel (IARA) Geräte dieses Betriebes an eine Anzahl von Mitgliedstaalten der Vereinten Nationen. Ausgenommen wurde dabei das elektrische Kraftwerk, das auf Ersuchen Frankreichs von der Reparationsliste gestrichen wurde. Die Mehrzahl der Maschinen wurde den Staaten Mittel- und Ost-Europas auf deren Bitten hin zugesprochein, vor allem der Tschechoslowakei und Jugoslawien. Frankreich erhielt von den 1800 Maschinen nur 100."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Frankfurt am Main
    Description: bevölkerungsreichste Stadt in Hessen, Deutschland
    Country: ['Fränkisches Reich', 'Ostfrankenreich', 'Heiliges Römisches Reich', 'Großherzogtum Frankfurt', 'Q704300', 'Deutscher Bund', 'Q27306', 'Q1206012', 'Q41304', 'NS-Staat', 'Deutschland 1945 bis 1949', 'Q713750', 'Deutschland']
    Located in: ['Regierungsbezirk Darmstadt', 'Regierungsbezirk Wiesbaden', 'Freie Stadt Frankfurt']
    Aliases: {'en': ['Frankfurt/Main', 'Frankfurt (Main)', 'Kreisfreie Stadt Frankfurt am Main', 'Frankfort-on-the-Main', 'Frankfurt, Germany', 'Frankfurt am Main, Germany', 'Frankfurt am Main', 'Francfort'], 'fr': ['Francfort', 'Frankfurt am Main', 'Francfort-sur-le-Mein', 'Francfort-sur-le-main', 'Frankfurt'], 'de': ['Frankfurt', 'Frankfurt/Main', 'FFM', 'Frankfurt (Main)', 'Frankfurt a. M.', 'Ffm', 'Ffm.', 'Fft.', 'Frankfurt a.M.', 'Franckfurt am Mayn', 'Frankfurt a. Main', 'Internationale Messestadt'], 'lb': ['Frankfurt', 'Frankfurt/Main']}
    Coordinates: [{'lat': 50.11055555555556, 'lon': 8.682222222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (5):
      - "1937" → 1937
      - "2000" → 2000
      - "1947" → 1947
      - "1947" → 1947
      - "1800" → 1800
    Temporal signal words: jetzt, gestern, nach, vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    OCR quality estimate: 0.961

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Direktor der J.E.I.A., W. John Logan' and 'Frankfurt a. M.' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Direktor der J.E.I.A., W. John Logan' near 'Frankfurt a. M.' around 1948-08-27?
  4. Resolve temporal expressions relative to 1948-08-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 13 [ID: test_de__122]:
  Publication date : 1948-08-27
  Language         : de
  Person  : 'Brigadier M. R. L. Robinson, ein\nMitarbeiter von Logan'  (QID: N/A)
  Location: 'Westdeutschland'  (QID: Q713750)

  [ARTICLE TEXT — entity markers added]
  "Steigende Produktionsquote in <LOCATION>Westdeutschland</LOCATION> » Frankfurt a. M., 27. August (AP). Die "wirtschaftliche Lage der Bi-Zone mache rasche Fortschritte, erklärte gestern der Direktor der J.E.I.A., W. John Logan. Die ProdMktàomsquote sei in den letzten beiden Monaten stark angestiegen und betrage jetzt 60 Prozent de s Standes von 1937. Zwei Faktoren, denen der beginnende Aufschwung mit zu verdanken sei, seien die im Juni durchgeführte Währungsreform und die Bemühungen der J.E.IA. um Belebung der Aus- und Einfuhr. Die Einfuhren in die Bi-Zone hätten in den ersten sieben Monaten dieses Jahres 282 400 000 Dollar und damit mehr betragen als im gesamten vorigen Jahr. Brigadier M. R. L. Robinson, ein Mitarbeiter von Logan, sagte vor Presse- 1 Vertretern, die Pläne zur Zusammenfassung der Wirtschaft der französischen Zone mit derjenigen .der britisch und amerikanisch besetzten Doppelzone würden vorangetrieben. Auf Befragen erklärte er, es seien keine unerwarteten Schwierigkeiten hierbei aufgetaucht. Er erinnerte daran, daß die Vereinigung der Wirtschaftsverwaltungen der britischen und der amerikanischen Zone sogar nach dem diesbezüglichen Beschluß einige Monate gedauert habe. Als mutmaßlichen Zeitpunkt für den Anschluß der Wirtschaft der französischen Zone nannte er den Beginn des nächsten Jahres. Logan nahm dann zu falschen Darstellungen im Zusammenhang mit der J.E.I.A. Stellung, die in verschiedenen Blättern von der sowjetisch lizenzierten „Berliner Zeitung" bis zu dem amerikanischen „Wall Street Journal" erschienen seien. Zu der Behauptung der „Berliner Zeitung", die J.E I.A. habe die Bi-Zone in eine „Zwangsjacke" gesteckt, um den Vereinigten - Staaten Profite zu verschaffen, sagte Logan: „Alle Erlöse aus den Bi-Zonen-Exporten wurden für Importe verwandt. Darüber hinaus werden die Vereinigten Staaten etwa ein« Milliarde Dollar für Lebensimiiitteleinfuhren nach Deutschland ausgeben. Wie kann man da von Profiten für Amerika sprechen?" Klarstellung der französischen Militärregierung zur Borsig-Demontage Berlin, 27. August. (AP). Wegen ungenauer und absichtlich irreführender Pressemeldungen über „Ausplünderung" der Rheinmetall-Borsigwerke in Berlin seitens der französischen Besetzungstruppen — die Meldungen waren in der sowjetisch lizenzierten Presse erschienen — veröffentlicht die französische Militärregierung folgende Klarstellung: 1. Bevor die französischen Behörden ihren Sektor in Berlin übernahmen, war von den sowjetischen Besatzungstruppen der größere Teil des Maschinenparks, das heißt rund 2000 Maschinen, eigenmächtig bereits demontiert und abtransportiert worden. 2. Vor dem Ausschul? für die Liquidierung von Rüstungsmaterial wurden die Rheinmetall-Borsigwerke am 15. Juni 1947 von den Vertretern der Sowjetunion, Englands und Frankreichs als Rüstungsbetrieb bezeichnet. Diese Entscheidung wurde am 29. Juli 1947 vom Koordinierungs-Ausschuß bestätigt. 3. In Erfüllung dieses Beschlusses wurde von den verantwortlichen sowjetischen, amerikanischen, britischen und französischen Behörden die Borsigwerke als reparationspfliahtig erklärt. 4. Nach den Bestimmungen dUese s Beschlusses verteilte die interalliierte Repairatdonsbehörde in Brüssel (IARA) Geräte dieses Betriebes an eine Anzahl von Mitgliedstaalten der Vereinten Nationen. Ausgenommen wurde dabei das elektrische Kraftwerk, das auf Ersuchen Frankreichs von der Reparationsliste gestrichen wurde. Die Mehrzahl der Maschinen wurde den Staaten Mittel- und Ost-Europas auf deren Bitten hin zugesprochein, vor allem der Tschechoslowakei und Jugoslawien. Frankreich erhielt von den 1800 Maschinen nur 100."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Bundesrepublik Deutschland bis 1990
    Description: Westdeutschland einschließlich West-Berlin 1949–1990
    Country: ['Deutschland']
    Aliases: {'en': ['West-Deutschland', 'BR Dtld.', 'history of West Germany from 1949 to 1990', 'Federal Republic of Germany (1949–1990)'], 'fr': ['RFA', 'République fédérale allemande', 'République fédérale d’Allemagne', 'Ouest-Allemand', 'Allemagne fédérale', 'Allemagne de l’Ouest'], 'de': ['Westdeutschland', 'BR Deutschland', 'BRD', 'Bundesrepublik Deutschland (1949-1990)', 'FRG', 'RFA', 'West-Deutschland', 'alte Bundesrepublik', 'alte Bundesrepublik Deutschland', 'BR Dtld.', 'Bundesrepublik Deutschland von 1949 bis 1990']}
    Coordinates: [{'lat': 50.733888888889, 'lon': 7.0997222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (5):
      - "1937" → 1937
      - "2000" → 2000
      - "1947" → 1947
      - "1947" → 1947
      - "1800" → 1800
    Temporal signal words: jetzt, gestern, nach, vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    OCR quality estimate: 0.961

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Brigadier M. R. L. Robinson, ein\nMitarbeiter von Logan' and 'Westdeutschland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Brigadier M. R. L. Robinson, ein\nMitarbeiter von Logan' near 'Westdeutschland' around 1948-08-27?
  4. Resolve temporal expressions relative to 1948-08-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 14 [ID: test_de__118]:
  Publication date : 1948-08-27
  Language         : de
  Person  : 'Brigadier M. R. L. Robinson, ein\nMitarbeiter von Logan'  (QID: N/A)
  Location: 'französischen Zone'  (QID: Q55309)

  [ARTICLE TEXT — entity markers added]
  "Steigende Produktionsquote in Westdeutschland » Frankfurt a. M., 27. August (AP). Die "wirtschaftliche Lage der Bi-Zone mache rasche Fortschritte, erklärte gestern der Direktor der J.E.I.A., W. John Logan. Die ProdMktàomsquote sei in den letzten beiden Monaten stark angestiegen und betrage jetzt 60 Prozent de s Standes von 1937. Zwei Faktoren, denen der beginnende Aufschwung mit zu verdanken sei, seien die im Juni durchgeführte Währungsreform und die Bemühungen der J.E.IA. um Belebung der Aus- und Einfuhr. Die Einfuhren in die Bi-Zone hätten in den ersten sieben Monaten dieses Jahres 282 400 000 Dollar und damit mehr betragen als im gesamten vorigen Jahr. Brigadier M. R. L. Robinson, ein Mitarbeiter von Logan, sagte vor Presse- 1 Vertretern, die Pläne zur Zusammenfassung der Wirtschaft der <LOCATION>französischen Zone</LOCATION> mit derjenigen .der britisch und amerikanisch besetzten Doppelzone würden vorangetrieben. Auf Befragen erklärte er, es seien keine unerwarteten Schwierigkeiten hierbei aufgetaucht. Er erinnerte daran, daß die Vereinigung der Wirtschaftsverwaltungen der britischen und der amerikanischen Zone sogar nach dem diesbezüglichen Beschluß einige Monate gedauert habe. Als mutmaßlichen Zeitpunkt für den Anschluß der Wirtschaft der französischen Zone nannte er den Beginn des nächsten Jahres. Logan nahm dann zu falschen Darstellungen im Zusammenhang mit der J.E.I.A. Stellung, die in verschiedenen Blättern von der sowjetisch lizenzierten „Berliner Zeitung" bis zu dem amerikanischen „Wall Street Journal" erschienen seien. Zu der Behauptung der „Berliner Zeitung", die J.E I.A. habe die Bi-Zone in eine „Zwangsjacke" gesteckt, um den Vereinigten - Staaten Profite zu verschaffen, sagte Logan: „Alle Erlöse aus den Bi-Zonen-Exporten wurden für Importe verwandt. Darüber hinaus werden die Vereinigten Staaten etwa ein« Milliarde Dollar für Lebensimiiitteleinfuhren nach Deutschland ausgeben. Wie kann man da von Profiten für Amerika sprechen?" Klarstellung der französischen Militärregierung zur Borsig-Demontage Berlin, 27. August. (AP). Wegen ungenauer und absichtlich irreführender Pressemeldungen über „Ausplünderung" der Rheinmetall-Borsigwerke in Berlin seitens der französischen Besetzungstruppen — die Meldungen waren in der sowjetisch lizenzierten Presse erschienen — veröffentlicht die französische Militärregierung folgende Klarstellung: 1. Bevor die französischen Behörden ihren Sektor in Berlin übernahmen, war von den sowjetischen Besatzungstruppen der größere Teil des Maschinenparks, das heißt rund 2000 Maschinen, eigenmächtig bereits demontiert und abtransportiert worden. 2. Vor dem Ausschul? für die Liquidierung von Rüstungsmaterial wurden die Rheinmetall-Borsigwerke am 15. Juni 1947 von den Vertretern der Sowjetunion, Englands und Frankreichs als Rüstungsbetrieb bezeichnet. Diese Entscheidung wurde am 29. Juli 1947 vom Koordinierungs-Ausschuß bestätigt. 3. In Erfüllung dieses Beschlusses wurde von den verantwortlichen sowjetischen, amerikanischen, britischen und französischen Behörden die Borsigwerke als reparationspfliahtig erklärt. 4. Nach den Bestimmungen dUese s Beschlusses verteilte die interalliierte Repairatdonsbehörde in Brüssel (IARA) Geräte dieses Betriebes an eine Anzahl von Mitgliedstaalten der Vereinten Nationen. Ausgenommen wurde dabei das elektrische Kraftwerk, das auf Ersuchen Frankreichs von der Reparationsliste gestrichen wurde. Die Mehrzahl der Maschinen wurde den Staaten Mittel- und Ost-Europas auf deren Bitten hin zugesprochein, vor allem der Tschechoslowakei und Jugoslawien. Frankreich erhielt von den 1800 Maschinen nur 100."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Französische Besatzungszone
    Description: eine von vier Zonen, in die Deutschland von den Alliierten nach dem Zweiten Weltkrieg aufgeteilt wurde
    Country: ['Deutschland']
    Aliases: {'de': ['Westzone']}
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (5):
      - "1937" → 1937
      - "2000" → 2000
      - "1947" → 1947
      - "1947" → 1947
      - "1800" → 1800
    Temporal signal words: jetzt, gestern, nach, vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    OCR quality estimate: 0.961

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Brigadier M. R. L. Robinson, ein\nMitarbeiter von Logan' and 'französischen Zone' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Brigadier M. R. L. Robinson, ein\nMitarbeiter von Logan' near 'französischen Zone' around 1948-08-27?
  4. Resolve temporal expressions relative to 1948-08-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 15 [ID: test_de__117]:
  Publication date : 1948-08-27
  Language         : de
  Person  : 'Direktor der J.E.I.A., W. John Logan'  (QID: N/A)
  Location: 'Westdeutschland'  (QID: Q713750)

  [ARTICLE TEXT — entity markers added]
  "Steigende Produktionsquote in <LOCATION>Westdeutschland</LOCATION> » Frankfurt a. M., 27. August (AP). Die "wirtschaftliche Lage der Bi-Zone mache rasche Fortschritte, erklärte gestern der <PERSON>Direktor der J.E.I.A., W. John Logan</PERSON>. Die ProdMktàomsquote sei in den letzten beiden Monaten stark angestiegen und betrage jetzt 60 Prozent de s Standes von 1937. Zwei Faktoren, denen der beginnende Aufschwung mit zu verdanken sei, seien die im Juni durchgeführte Währungsreform und die Bemühungen der J.E.IA. um Belebung der Aus- und Einfuhr. Die Einfuhren in die Bi-Zone hätten in den ersten sieben Monaten dieses Jahres 282 400 000 Dollar und damit mehr betragen als im gesamten vorigen Jahr. Brigadier M. R. L. Robinson, ein Mitarbeiter von Logan, sagte vor Presse- 1 Vertretern, die Pläne zur Zusammenfassung der Wirtschaft der französischen Zone mit derjenigen .der britisch und amerikanisch besetzten Doppelzone würden vorangetrieben. Auf Befragen erklärte er, es seien keine unerwarteten Schwierigkeiten hierbei aufgetaucht. Er erinnerte daran, daß die Vereinigung der Wirtschaftsverwaltungen der britischen und der amerikanischen Zone sogar nach dem diesbezüglichen Beschluß einige Monate gedauert habe. Als mutmaßlichen Zeitpunkt für den Anschluß der Wirtschaft der französischen Zone nannte er den Beginn des nächsten Jahres. Logan nahm dann zu falschen Darstellungen im Zusammenhang mit der J.E.I.A. Stellung, die in verschiedenen Blättern von der sowjetisch lizenzierten „Berliner Zeitung" bis zu dem amerikanischen „Wall Street Journal" erschienen seien. Zu der Behauptung der „Berliner Zeitung", die J.E I.A. habe die Bi-Zone in eine „Zwangsjacke" gesteckt, um den Vereinigten - Staaten Profite zu verschaffen, sagte Logan: „Alle Erlöse aus den Bi-Zonen-Exporten wurden für Importe verwandt. Darüber hinaus werden die Vereinigten Staaten etwa ein« Milliarde Dollar für Lebensimiiitteleinfuhren nach Deutschland ausgeben. Wie kann man da von Profiten für Amerika sprechen?" Klarstellung der französischen Militärregierung zur Borsig-Demontage Berlin, 27. August. (AP). Wegen ungenauer und absichtlich irreführender Pressemeldungen über „Ausplünderung" der Rheinmetall-Borsigwerke in Berlin seitens der französischen Besetzungstruppen — die Meldungen waren in der sowjetisch lizenzierten Presse erschienen — veröffentlicht die französische Militärregierung folgende Klarstellung: 1. Bevor die französischen Behörden ihren Sektor in Berlin übernahmen, war von den sowjetischen Besatzungstruppen der größere Teil des Maschinenparks, das heißt rund 2000 Maschinen, eigenmächtig bereits demontiert und abtransportiert worden. 2. Vor dem Ausschul? für die Liquidierung von Rüstungsmaterial wurden die Rheinmetall-Borsigwerke am 15. Juni 1947 von den Vertretern der Sowjetunion, Englands und Frankreichs als Rüstungsbetrieb bezeichnet. Diese Entscheidung wurde am 29. Juli 1947 vom Koordinierungs-Ausschuß bestätigt. 3. In Erfüllung dieses Beschlusses wurde von den verantwortlichen sowjetischen, amerikanischen, britischen und französischen Behörden die Borsigwerke als reparationspfliahtig erklärt. 4. Nach den Bestimmungen dUese s Beschlusses verteilte die interalliierte Repairatdonsbehörde in Brüssel (IARA) Geräte dieses Betriebes an eine Anzahl von Mitgliedstaalten der Vereinten Nationen. Ausgenommen wurde dabei das elektrische Kraftwerk, das auf Ersuchen Frankreichs von der Reparationsliste gestrichen wurde. Die Mehrzahl der Maschinen wurde den Staaten Mittel- und Ost-Europas auf deren Bitten hin zugesprochein, vor allem der Tschechoslowakei und Jugoslawien. Frankreich erhielt von den 1800 Maschinen nur 100."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Bundesrepublik Deutschland bis 1990
    Description: Westdeutschland einschließlich West-Berlin 1949–1990
    Country: ['Deutschland']
    Aliases: {'en': ['West-Deutschland', 'BR Dtld.', 'history of West Germany from 1949 to 1990', 'Federal Republic of Germany (1949–1990)'], 'fr': ['RFA', 'République fédérale allemande', 'République fédérale d’Allemagne', 'Ouest-Allemand', 'Allemagne fédérale', 'Allemagne de l’Ouest'], 'de': ['Westdeutschland', 'BR Deutschland', 'BRD', 'Bundesrepublik Deutschland (1949-1990)', 'FRG', 'RFA', 'West-Deutschland', 'alte Bundesrepublik', 'alte Bundesrepublik Deutschland', 'BR Dtld.', 'Bundesrepublik Deutschland von 1949 bis 1990']}
    Coordinates: [{'lat': 50.733888888889, 'lon': 7.0997222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (5):
      - "1937" → 1937
      - "2000" → 2000
      - "1947" → 1947
      - "1947" → 1947
      - "1800" → 1800
    Temporal signal words: jetzt, gestern, nach, vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    OCR quality estimate: 0.961

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Direktor der J.E.I.A., W. John Logan' and 'Westdeutschland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Direktor der J.E.I.A., W. John Logan' near 'Westdeutschland' around 1948-08-27?
  4. Resolve temporal expressions relative to 1948-08-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 16 [ID: test_de__110]:
  Publication date : 1948-08-27
  Language         : de
  Person  : 'Direktor der J.E.I.A., W. John Logan'  (QID: N/A)
  Location: 'Bi-Zone'  (QID: Q693911)

  [ARTICLE TEXT — entity markers added]
  "Steigende Produktionsquote in Westdeutschland » Frankfurt a. M., 27. August (AP). Die "wirtschaftliche Lage der <LOCATION>Bi-Zone</LOCATION> mache rasche Fortschritte, erklärte gestern der <PERSON>Direktor der J.E.I.A., W. John Logan</PERSON>. Die ProdMktàomsquote sei in den letzten beiden Monaten stark angestiegen und betrage jetzt 60 Prozent de s Standes von 1937. Zwei Faktoren, denen der beginnende Aufschwung mit zu verdanken sei, seien die im Juni durchgeführte Währungsreform und die Bemühungen der J.E.IA. um Belebung der Aus- und Einfuhr. Die Einfuhren in die Bi-Zone hätten in den ersten sieben Monaten dieses Jahres 282 400 000 Dollar und damit mehr betragen als im gesamten vorigen Jahr. Brigadier M. R. L. Robinson, ein Mitarbeiter von Logan, sagte vor Presse- 1 Vertretern, die Pläne zur Zusammenfassung der Wirtschaft der französischen Zone mit derjenigen .der britisch und amerikanisch besetzten Doppelzone würden vorangetrieben. Auf Befragen erklärte er, es seien keine unerwarteten Schwierigkeiten hierbei aufgetaucht. Er erinnerte daran, daß die Vereinigung der Wirtschaftsverwaltungen der britischen und der amerikanischen Zone sogar nach dem diesbezüglichen Beschluß einige Monate gedauert habe. Als mutmaßlichen Zeitpunkt für den Anschluß der Wirtschaft der französischen Zone nannte er den Beginn des nächsten Jahres. Logan nahm dann zu falschen Darstellungen im Zusammenhang mit der J.E.I.A. Stellung, die in verschiedenen Blättern von der sowjetisch lizenzierten „Berliner Zeitung" bis zu dem amerikanischen „Wall Street Journal" erschienen seien. Zu der Behauptung der „Berliner Zeitung", die J.E I.A. habe die Bi-Zone in eine „Zwangsjacke" gesteckt, um den Vereinigten - Staaten Profite zu verschaffen, sagte Logan: „Alle Erlöse aus den Bi-Zonen-Exporten wurden für Importe verwandt. Darüber hinaus werden die Vereinigten Staaten etwa ein« Milliarde Dollar für Lebensimiiitteleinfuhren nach Deutschland ausgeben. Wie kann man da von Profiten für Amerika sprechen?" Klarstellung der französischen Militärregierung zur Borsig-Demontage Berlin, 27. August. (AP). Wegen ungenauer und absichtlich irreführender Pressemeldungen über „Ausplünderung" der Rheinmetall-Borsigwerke in Berlin seitens der französischen Besetzungstruppen — die Meldungen waren in der sowjetisch lizenzierten Presse erschienen — veröffentlicht die französische Militärregierung folgende Klarstellung: 1. Bevor die französischen Behörden ihren Sektor in Berlin übernahmen, war von den sowjetischen Besatzungstruppen der größere Teil des Maschinenparks, das heißt rund 2000 Maschinen, eigenmächtig bereits demontiert und abtransportiert worden. 2. Vor dem Ausschul? für die Liquidierung von Rüstungsmaterial wurden die Rheinmetall-Borsigwerke am 15. Juni 1947 von den Vertretern der Sowjetunion, Englands und Frankreichs als Rüstungsbetrieb bezeichnet. Diese Entscheidung wurde am 29. Juli 1947 vom Koordinierungs-Ausschuß bestätigt. 3. In Erfüllung dieses Beschlusses wurde von den verantwortlichen sowjetischen, amerikanischen, britischen und französischen Behörden die Borsigwerke als reparationspfliahtig erklärt. 4. Nach den Bestimmungen dUese s Beschlusses verteilte die interalliierte Repairatdonsbehörde in Brüssel (IARA) Geräte dieses Betriebes an eine Anzahl von Mitgliedstaalten der Vereinten Nationen. Ausgenommen wurde dabei das elektrische Kraftwerk, das auf Ersuchen Frankreichs von der Reparationsliste gestrichen wurde. Die Mehrzahl der Maschinen wurde den Staaten Mittel- und Ost-Europas auf deren Bitten hin zugesprochein, vor allem der Tschechoslowakei und Jugoslawien. Frankreich erhielt von den 1800 Maschinen nur 100."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (5):
      - "1937" → 1937
      - "2000" → 2000
      - "1947" → 1947
      - "1947" → 1947
      - "1800" → 1800
    Temporal signal words: jetzt, gestern, nach, vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    OCR quality estimate: 0.961

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Direktor der J.E.I.A., W. John Logan' and 'Bi-Zone' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Direktor der J.E.I.A., W. John Logan' near 'Bi-Zone' around 1948-08-27?
  4. Resolve temporal expressions relative to 1948-08-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 17 [ID: test_de__114]:
  Publication date : 1948-08-27
  Language         : de
  Person  : 'Logan'  (QID: N/A)
  Location: 'Vereinigten Staaten'  (QID: Q30)

  [ARTICLE TEXT — entity markers added]
  "Steigende Produktionsquote in Westdeutschland » Frankfurt a. M., 27. August (AP). Die "wirtschaftliche Lage der Bi-Zone mache rasche Fortschritte, erklärte gestern der Direktor der J.E.I.A., W. John <PERSON>Logan</PERSON>. Die ProdMktàomsquote sei in den letzten beiden Monaten stark angestiegen und betrage jetzt 60 Prozent de s Standes von 1937. Zwei Faktoren, denen der beginnende Aufschwung mit zu verdanken sei, seien die im Juni durchgeführte Währungsreform und die Bemühungen der J.E.IA. um Belebung der Aus- und Einfuhr. Die Einfuhren in die Bi-Zone hätten in den ersten sieben Monaten dieses Jahres 282 400 000 Dollar und damit mehr betragen als im gesamten vorigen Jahr. Brigadier M. R. L. Robinson, ein Mitarbeiter von Logan, sagte vor Presse- 1 Vertretern, die Pläne zur Zusammenfassung der Wirtschaft der französischen Zone mit derjenigen .der britisch und amerikanisch besetzten Doppelzone würden vorangetrieben. Auf Befragen erklärte er, es seien keine unerwarteten Schwierigkeiten hierbei aufgetaucht. Er erinnerte daran, daß die Vereinigung der Wirtschaftsverwaltungen der britischen und der amerikanischen Zone sogar nach dem diesbezüglichen Beschluß einige Monate gedauert habe. Als mutmaßlichen Zeitpunkt für den Anschluß der Wirtschaft der französischen Zone nannte er den Beginn des nächsten Jahres. Logan nahm dann zu falschen Darstellungen im Zusammenhang mit der J.E.I.A. Stellung, die in verschiedenen Blättern von der sowjetisch lizenzierten „Berliner Zeitung" bis zu dem amerikanischen „Wall Street Journal" erschienen seien. Zu der Behauptung der „Berliner Zeitung", die J.E I.A. habe die Bi-Zone in eine „Zwangsjacke" gesteckt, um den Vereinigten - Staaten Profite zu verschaffen, sagte Logan: „Alle Erlöse aus den Bi-Zonen-Exporten wurden für Importe verwandt. Darüber hinaus werden die <LOCATION>Vereinigten Staaten</LOCATION> etwa ein« Milliarde Dollar für Lebensimiiitteleinfuhren nach Deutschland ausgeben. Wie kann man da von Profiten für Amerika sprechen?" Klarstellung der französischen Militärregierung zur Borsig-Demontage Berlin, 27. August. (AP). Wegen ungenauer und absichtlich irreführender Pressemeldungen über „Ausplünderung" der Rheinmetall-Borsigwerke in Berlin seitens der französischen Besetzungstruppen — die Meldungen waren in der sowjetisch lizenzierten Presse erschienen — veröffentlicht die französische Militärregierung folgende Klarstellung: 1. Bevor die französischen Behörden ihren Sektor in Berlin übernahmen, war von den sowjetischen Besatzungstruppen der größere Teil des Maschinenparks, das heißt rund 2000 Maschinen, eigenmächtig bereits demontiert und abtransportiert worden. 2. Vor dem Ausschul? für die Liquidierung von Rüstungsmaterial wurden die Rheinmetall-Borsigwerke am 15. Juni 1947 von den Vertretern der Sowjetunion, Englands und Frankreichs als Rüstungsbetrieb bezeichnet. Diese Entscheidung wurde am 29. Juli 1947 vom Koordinierungs-Ausschuß bestätigt. 3. In Erfüllung dieses Beschlusses wurde von den verantwortlichen sowjetischen, amerikanischen, britischen und französischen Behörden die Borsigwerke als reparationspfliahtig erklärt. 4. Nach den Bestimmungen dUese s Beschlusses verteilte die interalliierte Repairatdonsbehörde in Brüssel (IARA) Geräte dieses Betriebes an eine Anzahl von Mitgliedstaalten der Vereinten Nationen. Ausgenommen wurde dabei das elektrische Kraftwerk, das auf Ersuchen Frankreichs von der Reparationsliste gestrichen wurde. Die Mehrzahl der Maschinen wurde den Staaten Mittel- und Ost-Europas auf deren Bitten hin zugesprochein, vor allem der Tschechoslowakei und Jugoslawien. Frankreich erhielt von den 1800 Maschinen nur 100."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Vereinigte Staaten
    Description: Staat in Nordamerika
    Country: ['Vereinigte Staaten']
    Aliases: {'en': ['the States', 'the United States of America', 'US of America', 'the US', 'the U.S.', 'the US of A', 'U.S. of America', 'the US of America', 'the USA', 'the U.S.A.', 'the U.S. of A', 'US of A', 'the U.S. of America', 'the United States', 'Merica', 'Murica', 'United States of America', 'U.S.', 'U.S.A.', 'U. S.', 'U. S. A.', 'America'], 'fr': ['É.-U.', 'É-U', 'É-U.', 'E.-U.', 'É.U.', 'les États', 'Oncle Sam', 'Amérique', 'Etats-Unis', 'States', 'les États-Unis d’Amérique', 'États-unis', 'ÉU', 'É.-U. A.', "Pays de l'Oncle Sam", 'Etats-unis', 'États-Unis d’Amérique', 'pays de l’Oncle Sam'], 'de': ['Vereinigte Staaten von Amerika', 'US-Amerika', 'U.S.-Amerika', 'Staaten von Amerika', 'VSA', 'V.S.A.', 'V. S. A.', 'Staaten', 'die Staaten', 'VS', 'V.S.', 'V. S.', 'Amerika', 'U.S.A.', 'U. S. A.', 'United States of America', 'United States', 'U.S.', 'U. S.', 'America'], 'lb': ['Vereenegt Staaten']}
    Coordinates: [{'lat': 39.828175, 'lon': -98.5795}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (5):
      - "1937" → 1937
      - "2000" → 2000
      - "1947" → 1947
      - "1947" → 1947
      - "1800" → 1800
    Temporal signal words: jetzt, gestern, nach, vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    OCR quality estimate: 0.961

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Logan' and 'Vereinigten Staaten' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Logan' near 'Vereinigten Staaten' around 1948-08-27?
  4. Resolve temporal expressions relative to 1948-08-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 18 [ID: test_de__169]:
  Publication date : 1848-08-26
  Language         : de
  Person  : 'Republikaner\nEdgar Bauer'  (QID: Q67299)
  Location: 'Preußen'  (QID: Q38872)

  [ARTICLE TEXT — entity markers added]
  "Deutschland. <LOCATION>Preußen</LOCATION>. Berlin. In Charlottenburg kam es am 20. d. zwischen dem Preußenverein und dem demo kratischen Verein zu Schlägereien. Laut einer Korrespondenz der Fr. O. P. Z. bediente sich der Preußenverein eines Lokals, das der Demokratenverein zu seinen Zusammenkünften benutzte und dieser verlangte Räumung desselben. Aus Wortwechsel entsteht Handgemenge, und so kam es zu einer ernsthaften Prügelei. Die Demokraten ergriffen zum Theil die Flucht, um den Schlägen der „Preußen" zu entgehen; einige verkrochen sich in Ställen, andere sogar in Schornsteinen. Bei der Flucht war einer so un klug, auf der Straße „Republik" zu brüllen. Er wurde von nachsetzenden Verfolgern niedergeschlagen. Die vorgekommenen Verwundungen sind so bedeutend, daß man selbst an dem Auf kommen einzelner Personen zweifelt. Auch der Republikaner Edgar Bauer ist arg zugerichtet. So berichtet u. a. dieser Kor respondent, der ferner hinzufügt, wie in Folge dieser Auftritte Berlin selbst in Aufregung gerieth. Eine Menge Arbeiter setzte sich in Bewegung. Dieselbe endigte jedoch mit der Verhaftung von 10 Führern der Arbeiter. Unter den Linden blieben jedoch namhafte Gruppen versammelt, die mit dem Plane umgingen, sich Charlottenburg zu nahen. Weiter geht der Bericht nicht."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Preußen
    Description: Staatswesen (Herzogtum, Königreich, Freistaat), 1525–1947
    Country: ['Preußen']
    Aliases: {'en': ['Prussia (Germany)'], 'fr': ['État prussien', 'Prussienne'], 'de': ['Preussen']}
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.989

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Republikaner\nEdgar Bauer' and 'Preußen' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Republikaner\nEdgar Bauer' near 'Preußen' around 1848-08-26?
  4. Resolve temporal expressions relative to 1848-08-26. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 19 [ID: test_de__18]:
  Publication date : 1848-12-15
  Language         : de
  Person  : 'General-Administrator des Innern,\nUlrich'  (QID: N/A)
  Location: 'Sa«\npellen'  (QID: Q397678)

  [ARTICLE TEXT — entity markers added]
  "Die Wahlcollegien der Cantons Diekirch und Sa« pellen werden auf Donnerstag, den 21. Dezember d. 1., zehn Uhr Vormittags, zusammenberufen, um jedes einen Abgeordneten zu respectiver Ersetzung der Herrn Ulrich und N. Metz zu wählen. Der General-Administrator des Innern, Ulrich. Die neve, durch Beschlüsse bei» Königs GroßherzogS vom 2. d. M. angeordnete Regierung, welche Unterm heutigen Tage in Thätigkeit getreten ist, hat sofort über cine vorläufig anzunehmende Und der Könlgllch'Großhelzoglichen Genehmigung vorbehaltene Vertheilung der öffentlichen Dienstzweige unter ihre vier Mitglieder Folgende beschlossen: 1. Die General'Admmistration der auswärtigen Angelegenheiten, der Justiz und der Culte ist Herrn Willmai übertragen; die des Inneren Hrn. Ulrich; die der Gemeinde-Angelegenheiten Hrn. Ulveling, und die der Finanzen Hrn. Norbert Metz. 2. Die Genetal-Administration der öffentlichen Staats- und Gemeindebauten und der Militär-Ange» legenheiten ist vorläufig in der Art geseilt, daß vor» läusig die General-Administration der öffentlichen Bauten mit der bei} Inneren, «nd die der Militär« Angelegenheiten mit der der Finanzen vereinigt ist. 3. Auch ist vorläufig der öffentliche Unterricht von der General-Administration des Inneren getrennt und mit der der auswärtigen Angelegenheiten, der Justiz und der Culte verbunden. Der einstweilige Gcneral»Administrator, Präsident des Conseils, Willmar. Bekanntmachung , betreffend den Dienstantritt der neuen General'Admimstratoren und die neve Verthei- Ittrtg der verschiedenen Dienstzweige unter dieselben» Luxemburg, de« 6. Dezembet 1848."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1848" → 1848
    Temporal signal words: vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.963

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'General-Administrator des Innern,\nUlrich' and 'Sa«\npellen' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'General-Administrator des Innern,\nUlrich' near 'Sa«\npellen' around 1848-12-15?
  4. Resolve temporal expressions relative to 1848-12-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 20 [ID: test_de__36]:
  Publication date : 1858-02-07
  Language         : de
  Person  : 'sM. I.'  (QID: N/A)
  Location: 'London'  (QID: Q84)

  [ARTICLE TEXT — entity markers added]
  "Belgien. Brüssel 31. Jan. Als Verfasser deS im „Dra» pcau" erschienenen und angeklagten Artikels wird jetzt der frühere Rédacteur des Blattes, Louis Labarre, genannt. Der jetzige nominelle Herausgeber, Brismee, soll diesmal seine verantwortliche Haut nicht zu Markte tragen wollen, da ihm noch das Jahr Gefängnis), was cc vor Kurzem abgesessen, in den Gliedern liege. Gro» Bes Aufsehen macht ein neuer Artikel in Bezug auf das Attentat, der vor einigen Tagen in einem kleinen Blatte, der „Proletarier" betitelt, erschienen ist. Dieses giftige Blatt steht mit dem socialen Handwerkervereine in <LOCATION>London</LOCATION> in Verbindung und wird von einem rabiaten Schneider, Namens Coulon, redigirt. Das Attentat wird in diesem Artikel mit perfider Frechheit verherr licht, und zugleich werden Orsini und Pierri als Helden ausgerufen und für ihre That mit dem Beifalle des Wahnwitzes überschüttet. Mr. Coulon, der kühne Schneider, wird mit den Rédacteur?« des „Drapeau" und „Crocodile" zusammen demnächst vor Gericht zu erscheinen haben. <PERSON>sM. I.</PERSON>)"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: London
    Description: Hauptstadt und bevölkerungsreichste Stadt des Vereinigten Königreichs
    Country: ['Q2277', 'Q110888', 'Mercia', 'Q105313', 'Q179876', 'Königreich Großbritannien', 'Vereinigtes Königreich Großbritannien und Irland', 'Vereinigtes Königreich']
    Located in: ['Königreich Wessex', 'Q179876', 'Q21', 'County of London', 'Q23306']
    Aliases: {'en': ['London, UK', 'London, United Kingdom', 'London, England', 'London UK', 'London U.K.', 'Londinium', 'Loñ', 'Lundenwic', 'Londinio', 'Londini', 'Londiniensium', 'Augusta', 'Trinovantum', 'Kaerlud', 'Karelundein', 'Lunden', 'Big Smoke', 'the Big Smoke', 'Lundenburh', 'Lundenburgh', 'Llyn Dain', 'Llan Dian', 'Londinion', 'Loniniensi', 'Lon.', 'Loñ.', 'Lond.', 'LDN'], 'fr': ['London']}
    Coordinates: [{'lat': 51.507222222222, 'lon': -0.1275}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: jetzt, früher, vor, früh
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.993

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'sM. I.' and 'London' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'sM. I.' near 'London' around 1858-02-07?
  4. Resolve temporal expressions relative to 1858-02-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 21 [ID: test_de__111]:
  Publication date : 1948-08-27
  Language         : de
  Person  : 'Brigadier M. R. L. Robinson, ein\nMitarbeiter von Logan'  (QID: N/A)
  Location: 'Bi-Zone'  (QID: Q693911)

  [ARTICLE TEXT — entity markers added]
  "Steigende Produktionsquote in Westdeutschland » Frankfurt a. M., 27. August (AP). Die "wirtschaftliche Lage der <LOCATION>Bi-Zone</LOCATION> mache rasche Fortschritte, erklärte gestern der Direktor der J.E.I.A., W. John Logan. Die ProdMktàomsquote sei in den letzten beiden Monaten stark angestiegen und betrage jetzt 60 Prozent de s Standes von 1937. Zwei Faktoren, denen der beginnende Aufschwung mit zu verdanken sei, seien die im Juni durchgeführte Währungsreform und die Bemühungen der J.E.IA. um Belebung der Aus- und Einfuhr. Die Einfuhren in die Bi-Zone hätten in den ersten sieben Monaten dieses Jahres 282 400 000 Dollar und damit mehr betragen als im gesamten vorigen Jahr. Brigadier M. R. L. Robinson, ein Mitarbeiter von Logan, sagte vor Presse- 1 Vertretern, die Pläne zur Zusammenfassung der Wirtschaft der französischen Zone mit derjenigen .der britisch und amerikanisch besetzten Doppelzone würden vorangetrieben. Auf Befragen erklärte er, es seien keine unerwarteten Schwierigkeiten hierbei aufgetaucht. Er erinnerte daran, daß die Vereinigung der Wirtschaftsverwaltungen der britischen und der amerikanischen Zone sogar nach dem diesbezüglichen Beschluß einige Monate gedauert habe. Als mutmaßlichen Zeitpunkt für den Anschluß der Wirtschaft der französischen Zone nannte er den Beginn des nächsten Jahres. Logan nahm dann zu falschen Darstellungen im Zusammenhang mit der J.E.I.A. Stellung, die in verschiedenen Blättern von der sowjetisch lizenzierten „Berliner Zeitung" bis zu dem amerikanischen „Wall Street Journal" erschienen seien. Zu der Behauptung der „Berliner Zeitung", die J.E I.A. habe die Bi-Zone in eine „Zwangsjacke" gesteckt, um den Vereinigten - Staaten Profite zu verschaffen, sagte Logan: „Alle Erlöse aus den Bi-Zonen-Exporten wurden für Importe verwandt. Darüber hinaus werden die Vereinigten Staaten etwa ein« Milliarde Dollar für Lebensimiiitteleinfuhren nach Deutschland ausgeben. Wie kann man da von Profiten für Amerika sprechen?" Klarstellung der französischen Militärregierung zur Borsig-Demontage Berlin, 27. August. (AP). Wegen ungenauer und absichtlich irreführender Pressemeldungen über „Ausplünderung" der Rheinmetall-Borsigwerke in Berlin seitens der französischen Besetzungstruppen — die Meldungen waren in der sowjetisch lizenzierten Presse erschienen — veröffentlicht die französische Militärregierung folgende Klarstellung: 1. Bevor die französischen Behörden ihren Sektor in Berlin übernahmen, war von den sowjetischen Besatzungstruppen der größere Teil des Maschinenparks, das heißt rund 2000 Maschinen, eigenmächtig bereits demontiert und abtransportiert worden. 2. Vor dem Ausschul? für die Liquidierung von Rüstungsmaterial wurden die Rheinmetall-Borsigwerke am 15. Juni 1947 von den Vertretern der Sowjetunion, Englands und Frankreichs als Rüstungsbetrieb bezeichnet. Diese Entscheidung wurde am 29. Juli 1947 vom Koordinierungs-Ausschuß bestätigt. 3. In Erfüllung dieses Beschlusses wurde von den verantwortlichen sowjetischen, amerikanischen, britischen und französischen Behörden die Borsigwerke als reparationspfliahtig erklärt. 4. Nach den Bestimmungen dUese s Beschlusses verteilte die interalliierte Repairatdonsbehörde in Brüssel (IARA) Geräte dieses Betriebes an eine Anzahl von Mitgliedstaalten der Vereinten Nationen. Ausgenommen wurde dabei das elektrische Kraftwerk, das auf Ersuchen Frankreichs von der Reparationsliste gestrichen wurde. Die Mehrzahl der Maschinen wurde den Staaten Mittel- und Ost-Europas auf deren Bitten hin zugesprochein, vor allem der Tschechoslowakei und Jugoslawien. Frankreich erhielt von den 1800 Maschinen nur 100."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Bizone
    Description: gemeinsame Verwaltung der Britischen und Amerikanischen Besatzungszonen in Nachkriegsdeutschland
    Country: ['Q2415901']
    Aliases: {'de': ['Vereinigtes Wirtschaftsgebiet', 'Bi-Zone']}
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (5):
      - "1937" → 1937
      - "2000" → 2000
      - "1947" → 1947
      - "1947" → 1947
      - "1800" → 1800
    Temporal signal words: jetzt, gestern, nach, vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    OCR quality estimate: 0.961

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Brigadier M. R. L. Robinson, ein\nMitarbeiter von Logan' and 'Bi-Zone' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Brigadier M. R. L. Robinson, ein\nMitarbeiter von Logan' near 'Bi-Zone' around 1948-08-27?
  4. Resolve temporal expressions relative to 1948-08-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 22 [ID: test_de__112]:
  Publication date : 1948-08-27
  Language         : de
  Person  : 'Logan'  (QID: N/A)
  Location: 'Bi-Zone'  (QID: Q693911)

  [ARTICLE TEXT — entity markers added]
  "Steigende Produktionsquote in Westdeutschland » Frankfurt a. M., 27. August (AP). Die "wirtschaftliche Lage der <LOCATION>Bi-Zone</LOCATION> mache rasche Fortschritte, erklärte gestern der Direktor der J.E.I.A., W. John <PERSON>Logan</PERSON>. Die ProdMktàomsquote sei in den letzten beiden Monaten stark angestiegen und betrage jetzt 60 Prozent de s Standes von 1937. Zwei Faktoren, denen der beginnende Aufschwung mit zu verdanken sei, seien die im Juni durchgeführte Währungsreform und die Bemühungen der J.E.IA. um Belebung der Aus- und Einfuhr. Die Einfuhren in die Bi-Zone hätten in den ersten sieben Monaten dieses Jahres 282 400 000 Dollar und damit mehr betragen als im gesamten vorigen Jahr. Brigadier M. R. L. Robinson, ein Mitarbeiter von Logan, sagte vor Presse- 1 Vertretern, die Pläne zur Zusammenfassung der Wirtschaft der französischen Zone mit derjenigen .der britisch und amerikanisch besetzten Doppelzone würden vorangetrieben. Auf Befragen erklärte er, es seien keine unerwarteten Schwierigkeiten hierbei aufgetaucht. Er erinnerte daran, daß die Vereinigung der Wirtschaftsverwaltungen der britischen und der amerikanischen Zone sogar nach dem diesbezüglichen Beschluß einige Monate gedauert habe. Als mutmaßlichen Zeitpunkt für den Anschluß der Wirtschaft der französischen Zone nannte er den Beginn des nächsten Jahres. Logan nahm dann zu falschen Darstellungen im Zusammenhang mit der J.E.I.A. Stellung, die in verschiedenen Blättern von der sowjetisch lizenzierten „Berliner Zeitung" bis zu dem amerikanischen „Wall Street Journal" erschienen seien. Zu der Behauptung der „Berliner Zeitung", die J.E I.A. habe die Bi-Zone in eine „Zwangsjacke" gesteckt, um den Vereinigten - Staaten Profite zu verschaffen, sagte Logan: „Alle Erlöse aus den Bi-Zonen-Exporten wurden für Importe verwandt. Darüber hinaus werden die Vereinigten Staaten etwa ein« Milliarde Dollar für Lebensimiiitteleinfuhren nach Deutschland ausgeben. Wie kann man da von Profiten für Amerika sprechen?" Klarstellung der französischen Militärregierung zur Borsig-Demontage Berlin, 27. August. (AP). Wegen ungenauer und absichtlich irreführender Pressemeldungen über „Ausplünderung" der Rheinmetall-Borsigwerke in Berlin seitens der französischen Besetzungstruppen — die Meldungen waren in der sowjetisch lizenzierten Presse erschienen — veröffentlicht die französische Militärregierung folgende Klarstellung: 1. Bevor die französischen Behörden ihren Sektor in Berlin übernahmen, war von den sowjetischen Besatzungstruppen der größere Teil des Maschinenparks, das heißt rund 2000 Maschinen, eigenmächtig bereits demontiert und abtransportiert worden. 2. Vor dem Ausschul? für die Liquidierung von Rüstungsmaterial wurden die Rheinmetall-Borsigwerke am 15. Juni 1947 von den Vertretern der Sowjetunion, Englands und Frankreichs als Rüstungsbetrieb bezeichnet. Diese Entscheidung wurde am 29. Juli 1947 vom Koordinierungs-Ausschuß bestätigt. 3. In Erfüllung dieses Beschlusses wurde von den verantwortlichen sowjetischen, amerikanischen, britischen und französischen Behörden die Borsigwerke als reparationspfliahtig erklärt. 4. Nach den Bestimmungen dUese s Beschlusses verteilte die interalliierte Repairatdonsbehörde in Brüssel (IARA) Geräte dieses Betriebes an eine Anzahl von Mitgliedstaalten der Vereinten Nationen. Ausgenommen wurde dabei das elektrische Kraftwerk, das auf Ersuchen Frankreichs von der Reparationsliste gestrichen wurde. Die Mehrzahl der Maschinen wurde den Staaten Mittel- und Ost-Europas auf deren Bitten hin zugesprochein, vor allem der Tschechoslowakei und Jugoslawien. Frankreich erhielt von den 1800 Maschinen nur 100."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (5):
      - "1937" → 1937
      - "2000" → 2000
      - "1947" → 1947
      - "1947" → 1947
      - "1800" → 1800
    Temporal signal words: jetzt, gestern, nach, vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    OCR quality estimate: 0.961

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Logan' and 'Bi-Zone' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Logan' near 'Bi-Zone' around 1948-08-27?
  4. Resolve temporal expressions relative to 1948-08-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 23 [ID: test_de__121]:
  Publication date : 1948-08-27
  Language         : de
  Person  : 'Brigadier M. R. L. Robinson, ein\nMitarbeiter von Logan'  (QID: N/A)
  Location: 'amerikanischen Zone'  (QID: Q55304)

  [ARTICLE TEXT — entity markers added]
  "Steigende Produktionsquote in Westdeutschland » Frankfurt a. M., 27. August (AP). Die "wirtschaftliche Lage der Bi-Zone mache rasche Fortschritte, erklärte gestern der Direktor der J.E.I.A., W. John Logan. Die ProdMktàomsquote sei in den letzten beiden Monaten stark angestiegen und betrage jetzt 60 Prozent de s Standes von 1937. Zwei Faktoren, denen der beginnende Aufschwung mit zu verdanken sei, seien die im Juni durchgeführte Währungsreform und die Bemühungen der J.E.IA. um Belebung der Aus- und Einfuhr. Die Einfuhren in die Bi-Zone hätten in den ersten sieben Monaten dieses Jahres 282 400 000 Dollar und damit mehr betragen als im gesamten vorigen Jahr. Brigadier M. R. L. Robinson, ein Mitarbeiter von Logan, sagte vor Presse- 1 Vertretern, die Pläne zur Zusammenfassung der Wirtschaft der französischen Zone mit derjenigen .der britisch und amerikanisch besetzten Doppelzone würden vorangetrieben. Auf Befragen erklärte er, es seien keine unerwarteten Schwierigkeiten hierbei aufgetaucht. Er erinnerte daran, daß die Vereinigung der Wirtschaftsverwaltungen der britischen und der <LOCATION>amerikanischen Zone</LOCATION> sogar nach dem diesbezüglichen Beschluß einige Monate gedauert habe. Als mutmaßlichen Zeitpunkt für den Anschluß der Wirtschaft der französischen Zone nannte er den Beginn des nächsten Jahres. Logan nahm dann zu falschen Darstellungen im Zusammenhang mit der J.E.I.A. Stellung, die in verschiedenen Blättern von der sowjetisch lizenzierten „Berliner Zeitung" bis zu dem amerikanischen „Wall Street Journal" erschienen seien. Zu der Behauptung der „Berliner Zeitung", die J.E I.A. habe die Bi-Zone in eine „Zwangsjacke" gesteckt, um den Vereinigten - Staaten Profite zu verschaffen, sagte Logan: „Alle Erlöse aus den Bi-Zonen-Exporten wurden für Importe verwandt. Darüber hinaus werden die Vereinigten Staaten etwa ein« Milliarde Dollar für Lebensimiiitteleinfuhren nach Deutschland ausgeben. Wie kann man da von Profiten für Amerika sprechen?" Klarstellung der französischen Militärregierung zur Borsig-Demontage Berlin, 27. August. (AP). Wegen ungenauer und absichtlich irreführender Pressemeldungen über „Ausplünderung" der Rheinmetall-Borsigwerke in Berlin seitens der französischen Besetzungstruppen — die Meldungen waren in der sowjetisch lizenzierten Presse erschienen — veröffentlicht die französische Militärregierung folgende Klarstellung: 1. Bevor die französischen Behörden ihren Sektor in Berlin übernahmen, war von den sowjetischen Besatzungstruppen der größere Teil des Maschinenparks, das heißt rund 2000 Maschinen, eigenmächtig bereits demontiert und abtransportiert worden. 2. Vor dem Ausschul? für die Liquidierung von Rüstungsmaterial wurden die Rheinmetall-Borsigwerke am 15. Juni 1947 von den Vertretern der Sowjetunion, Englands und Frankreichs als Rüstungsbetrieb bezeichnet. Diese Entscheidung wurde am 29. Juli 1947 vom Koordinierungs-Ausschuß bestätigt. 3. In Erfüllung dieses Beschlusses wurde von den verantwortlichen sowjetischen, amerikanischen, britischen und französischen Behörden die Borsigwerke als reparationspfliahtig erklärt. 4. Nach den Bestimmungen dUese s Beschlusses verteilte die interalliierte Repairatdonsbehörde in Brüssel (IARA) Geräte dieses Betriebes an eine Anzahl von Mitgliedstaalten der Vereinten Nationen. Ausgenommen wurde dabei das elektrische Kraftwerk, das auf Ersuchen Frankreichs von der Reparationsliste gestrichen wurde. Die Mehrzahl der Maschinen wurde den Staaten Mittel- und Ost-Europas auf deren Bitten hin zugesprochein, vor allem der Tschechoslowakei und Jugoslawien. Frankreich erhielt von den 1800 Maschinen nur 100."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Amerikanische Besatzungszone
    Description: eine von vier Zonen, in die Deutschland nach dem Zweiten Weltkrieg von den Alliierten aufgeteilt wurde
    Country: ['Deutschland']
    Aliases: {'en': ['American Zone of Occupation in Germany', 'AMZON', 'U.S. occupation zone, Germany', 'US Zone of Occupation, Germany'], 'de': ['Südwestzone']}
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (5):
      - "1937" → 1937
      - "2000" → 2000
      - "1947" → 1947
      - "1947" → 1947
      - "1800" → 1800
    Temporal signal words: jetzt, gestern, nach, vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    OCR quality estimate: 0.961

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Brigadier M. R. L. Robinson, ein\nMitarbeiter von Logan' and 'amerikanischen Zone' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Brigadier M. R. L. Robinson, ein\nMitarbeiter von Logan' near 'amerikanischen Zone' around 1948-08-27?
  4. Resolve temporal expressions relative to 1948-08-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 24 [ID: test_de__190]:
  Publication date : 1808-04-29
  Language         : de
  Person  : 'General Hutchinson'  (QID: Q321765)
  Location: 'Kopenhagen'  (QID: Q1748)

  [ARTICLE TEXT — entity markers added]
  "henden und glücklichen Zustande gelebt habe, und daß kein Beweggrund ihn jemals dahin bringen könne, von diesem Vorsatze abzustehen. Se. Kaiserl. Majestät fügten hinzu, daß ich den festen Karakter des Kronprinzen hinlänglich ken nen müße, um zu wissen, daß nichts schwerer sey, als seine Entschlüsse zu erschüttern, oder ihn zu bewegen, ein ein mal angenommenes System zu verlassen, und daß er, der Kaiser, überzeugt sey, es habe vor unserm Angriff auf Ro (Aus dem danischen Blatte Dagen.) Da das engli sche Ministerium die englische Nation versichert hat, daß den Kaiser von Rußland Anfangs nicht das geringste Miß vergnügen über den Raubzug nach Seeland geäussert habe, so wird man nicht ohne Interesse nachstehende Erläuterun gen über eine, zwischen dem Kaiser von Rußland und dem <PERSON>General Hutchinson</PERSON> vorgefallene, Unterredung lesen. Se. Kaiserl. Majestät — so berichtet der General Hutchinson — flengen die Unterredung mit der Frage an, was ich von unserm Angriff auf <LOCATION>Kopenhagen</LOCATION> denke? Ich erwiederte, daß mir die Umstände, welche solchen veranlaßt hätten, zwar ganz unbekannt wären, daß ich aber hoffe, die englische Administration werde sich rechtfertigen, und der ganzen Welt beweisen können, daß die Dänen im Begriff waren, ihre ganze Macht mit der französischen gegen England zu vereinigen. Se. Kaiserl. Majestät bemerkten, daß ich un möglich dieser Meynung seyn könne, wenn ich noch der Un terredungen gedächte, die wir in Bartenstein gehabt hät ten. In diesen sagte der Kaiser mir, er habe alle mögliche Mühe angewandt, um den Kronprinzen von Dänemark zu! vermögen, der Koalition gegen Frankreich beyzutreten; daß aber die Antwort des Prinzen immer deutlich und un verändert dieselbe gewesen sey, daß er viele Jahre lang ein Neutralitätssystem behauptet habe, bey dem er zu beharren fest entschlossen sey; da sein Volk dadurch in einem blü und dänischen Regierung statt gefunden. Ich sagte dar auf, ich glaubte, daß der Lord Gower dem Kaiserl Mi nisterium über diesen Gegenstand eine Note übergeben habe, worauf Se. Majestät erwiederten, daß dies sich so verhalte, daß aber der Inhalt der Note lächerlich sey, da solche we der hinlängliche Auskunft enthalte, noch irgend eine Genug thuung anbiete. Se. Kaiserl. Majestät sprachen darnächst von der großen Betrübniß, die Ihnen durch unsern unver antwortlichen Angriff verursacht worden, und daß nie et was Aehnliches geschehen sey; daß, wenn ein solches Ver fahren gelten sollte, alle Verhältnisse, die das Verfahren der Nationen gegen einander bisher bestimmt hätten, zu Grunde gehen würden, und daß in dem Falle ein jeder thun könnte, was ihm beliebe. Se. Kaiserl. Majestät sagten mir in den bestimmtesten Ausdrücken, mit dem festesten Tone, daß er Genugthuung für diesen, ohne alle Veranlassung un ternommenen, Angriff fordere; daß dies seine Pflicht, als Kaiser von Rußland, sey, und daß er Genugthuung wolle. Er fragte mich, ob ich wagen dürfe, über diesen Gegenstand anderer Meynung, als er, zu seyn? Er sagte ferner; daß die feyerlichsten Traktate und Verpflichtungen ihn mit Dä nemark verbänden, und daß er entschlossen sey, solche zu erfüllen. Se Kaiserl. Majestät fügten hinzu, er vermuthe, wir dächten auf einen Angriff auf Kronstadt; daß er zwar den Ausgang eines solchen Angriffs nicht vorhersehen könne, daß er aber bis zum letzten Mann Widerstand leisten, und sich des hohen Postens, worauf ihn die Vorsehung gestellt habe, nicht unwürdig bezeigen wolle. — Ich antwortete, ich hätte alle Ursache zu heffen und zu glauben, daß wir auf Kronstadt keinen Angriff thun würden. Er entgegnete, daß er darauf gefaßt, und sein Entschluß unerschütterlich sey. Darauf endigte er das Gespräch, und wiederholte mit vielem Nachdruck: „Daß er Genugthuung für Dänemark wolle Der Freymüthige vom 7. April enthält Folgendes: Hamburger-Korrespondenten wird, von Petersburg aus, angedeutet, und in der neuesten Berlinischen Zeitung aus gesprochen, daß H. von Rotzebue in Ehstland gestorben sey. Man hat viele Gründe, die Authentizität dieser Nach richt zu bezweifeln; merkwürdig ist übrigens die Eilfertig keit, mit der man dem Publikum unverbürgte Notizen mit theilt, die für dasselbe tief erschütternd seyn müßen!" Das *Am 22. Merz sah man auf der großen Parade zu Peters burg 4. eroberte schwedische Fahnen und eine Flagge die General Burhöyden eingeschickt hatte."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: John Hely-Hutchinson, 2. Earl of Donoughmore
    Description: britischer General
    Born: ['+1757-05-15T00:00:00Z']
    Died: ['+1832-06-29T00:00:00Z']
    Birth place: ['Q1761']
    Work locations: ['Q84']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.995

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'General Hutchinson' and 'Kopenhagen' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'General Hutchinson' near 'Kopenhagen' around 1808-04-29?
  4. Resolve temporal expressions relative to 1808-04-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 25 [ID: test_de__27]:
  Publication date : 1848-12-15
  Language         : de
  Person  : 'General-Administrator des Innern,\nUlrich'  (QID: N/A)
  Location: 'Luxemburg'  (QID: Q32)

  [ARTICLE TEXT — entity markers added]
  "Die Wahlcollegien der Cantons Diekirch und Sa« pellen werden auf Donnerstag, den 21. Dezember d. 1., zehn Uhr Vormittags, zusammenberufen, um jedes einen Abgeordneten zu respectiver Ersetzung der Herrn Ulrich und N. Metz zu wählen. Der General-Administrator des Innern, Ulrich. Die neve, durch Beschlüsse bei» Königs GroßherzogS vom 2. d. M. angeordnete Regierung, welche Unterm heutigen Tage in Thätigkeit getreten ist, hat sofort über cine vorläufig anzunehmende Und der Könlgllch'Großhelzoglichen Genehmigung vorbehaltene Vertheilung der öffentlichen Dienstzweige unter ihre vier Mitglieder Folgende beschlossen: 1. Die General'Admmistration der auswärtigen Angelegenheiten, der Justiz und der Culte ist Herrn Willmai übertragen; die des Inneren Hrn. Ulrich; die der Gemeinde-Angelegenheiten Hrn. Ulveling, und die der Finanzen Hrn. Norbert Metz. 2. Die Genetal-Administration der öffentlichen Staats- und Gemeindebauten und der Militär-Ange» legenheiten ist vorläufig in der Art geseilt, daß vor» läusig die General-Administration der öffentlichen Bauten mit der bei} Inneren, «nd die der Militär« Angelegenheiten mit der der Finanzen vereinigt ist. 3. Auch ist vorläufig der öffentliche Unterricht von der General-Administration des Inneren getrennt und mit der der auswärtigen Angelegenheiten, der Justiz und der Culte verbunden. Der einstweilige Gcneral»Administrator, Präsident des Conseils, Willmar. Bekanntmachung , betreffend den Dienstantritt der neuen General'Admimstratoren und die neve Verthei- Ittrtg der verschiedenen Dienstzweige unter dieselben» <LOCATION>Luxemburg</LOCATION>, de« 6. Dezembet 1848."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Luxemburg
    Description: Staat in Westeuropa
    Country: ['Luxemburg']
    Aliases: {'en': ['Luxemburg', 'Grand Duchy of Luxembourg'], 'fr': ['Grand-Duché de Luxembourg', 'Grand-duché de Luxembourg', 'grand-duché de Luxembourg', 'le Grand-Duché de Luxembourg', 'Lux.'], 'de': ['Groussherzogtum Lëtzebuerg', 'Grand-Duché de Luxembourg', 'Luxembourg'], 'lb': ['Groussherzogtum Lëtzebuerg', 'Lëtzebuerger Land', 'Grand-Duché de Luxembourg', 'Grand-Duché']}
    Coordinates: [{'lat': 49.77, 'lon': 6.13}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1848" → 1848
    Temporal signal words: vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.963

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'General-Administrator des Innern,\nUlrich' and 'Luxemburg' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'General-Administrator des Innern,\nUlrich' near 'Luxemburg' around 1848-12-15?
  4. Resolve temporal expressions relative to 1848-12-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 26 [ID: test_de__84]:
  Publication date : 1918-11-22
  Language         : de
  Person  : 'Nationalrat Jäger'  (QID: Q17305208)
  Location: 'Bezirken\nReuenburg'  (QID: Q511990)

  [ARTICLE TEXT — entity markers added]
  "Generalstreik-Nachklänge. Postdienst der Zürcher Studenten. (Korr.) Die Postaustragung durch Studenten während des Generalstreiles in der Stadt Zürich, das war wohl eines der erfreulichsten Bilder in den trüben, ernsten Tagen, die wir durchgemacht haben. Wie freundlicher, wärmender Sonnenschein war's, diese fröhliche, diensteifrige Jungmannschaft in mitten der Atmosphäre von Erbitterung und Haß, Aufhetzung und Terrorismus. Als Ordnung und Diszipuin versagten, als die Postangestellten, statt ihren Obliegenheiten nachzukommen, im Volks hause von politischen Strebern und turbulenten Schwätzern sich ihr Tun und Lassen vorschreiben ließen, da hat die akademische Jugend spontan aus dem Bestreben heraus, sich nutzlich zu machen und der Allgemeinheit zu dienen, sich der Post und Telegraphenverwallung zur Verfügung ge stellt. Vorerst galt es, die Aufforderungen zur Wiederaufnahme der Arbeit an das streikende Personal an Mann zu bringen. Dann ging's an die Austragung der Briefe, Pakete und Tele gramme. Die strengen Bestimmungen betr. Wah rung des Postgeheimnisses ließen es aber nicht zu, die arbeitsfreudigen Studenten, die sich mehrere hundert Mann stark auf der Hauptpost eingefun den hatten, ohne weiteres zu beschäftigen. Ein jeder mußte zuerst unter Bekanntgabe der Vor schriften des Bundesstrafrechtes formell in Pflicht genommen und als Postaushelser angestellt wer den. Und was noch viel erschwerender war, es mußte für jeden dieser Bestellboten eine mili tärische Bedeckung von 1—2 Mann, nebst ebenso vielen Kommilitonen mitgegeben werden, damit gegen Bedrohungen und Ueberfälle von seiten Streikender ein ausreichender Schutz vorhanden sei. Diese Vorsichtsmaßregel erwies sich leider nicht als unnötig. Einzelne Studenten wurden tatsächlich auf der Bestelltour von bolschewistischen Gslementen auf der Straße oder in Hausgängen überfallen und geschlagen, und wenn keine bösen Folgen daraus erwachsen sind, so muß dies als ein Glück bezeichnet werden. In Außersihl wurde eine solche von 4 Wehrmännern begleitete Briefträgergruppe durch einen Volkshausen an gegriffen und tatlich bedroht. Aber trotz diesen Gefahren ließen sich unsere Studenten nicht abhalten. Mit Feuereifer und mit Geschick ordneten sie ihre Briefschaften und dann ging's in raschem Arbeitstempo von einer Haus türe, von einer Wohnung zur andern, von der bürgerlichen Bevölkerung überall freudig begrüßt. Um die Schimpfworte, die ihnen von Streikern zugerufen wurden, kümmerten sie sich nicht. Sie wußten, was auf dem Spiele war: dee Wohlfahrt und Unabhängigkeit unseres Landes, die Unter drückung der ruhigen arbeitswilligen Bevölke rung durch eine terroristische Minderheit. Dieses frische Zugreifen, dieser Wagemut, dieses Erfassen des Ernstes der Sachlage von seiten der akademi schen Jugend, das gibt uns auch Hoffnung, getrost in die Zukunft zu schauen. Unser Volk wird nicht vom rechten Pfade abkommen, wenn seine besten Söhne sich vom wahren Patriotisnus leiten las sen. Und Zürichs akademische Jugend krönte ihre Tätigkeit durch Verzicht auf die Entschädigungen, die ihr für den Hilfsdienst angeboten wurden. Sie überwies den ganzen Betrag, annähernd 2000 Fr., der Sammlung zugunsten des im Dienst von Demonstranten erschossenen Luzerner Soldaten Vogel! Basel. Bei der Wiederherstellung von Ord nung und Ruhe wuden in Basel das Militär und die Polizei durch die Bürgerwehr wacker unterstützt. Dieser Organisation sind bereits etwa 6000 Bürger aller Stände beigetreten. Weniger vorbildlich war die Haltung des Regie rungsrates zum Streik. Erst als der eigent liche Landesstreik verkündet wurde und größere Unruhen in Aussicht standen, entschloß er sich end lich, um militärische Hilse nachzusuchen. Am Diens tag ging die Regierung dann sogar soweit, mit dem Streikkomitee zu paktieren. Sie sicherte diesem zu, daß sie beim Bundesrat die Zurückziehung der Truppen verlangen werde, wenn das Streikkomitee für Aufrechterhaltung der Ruhe schriftliche Garan tie leiste. Glücklicherweise kam es nicht dazu. Als am Donnerstag morgen die Meldung einlief, daß das Oltener Aktionskomitee bedingungslos kapitu liert habe, unterließ sie es, das erwähnte Ver langen an den Bundesrat zu richten. Wenn auch der Regierungsrat mit seinem Verhalten die an sich gewiß lobenswerte Absicht verfolgte, einen friedlichen Ausgang des Streiks zu sichern, so mußte es doch als Schwäche ausgelegt werden. In der Sitzung des Großen Rates vom 14. November wurde denn auch an der Haltung des Regierungsrates scharfe Kritik geübt und ihm vor geworfen, daß er seine Pflicht, für Aufrechterhal tung von Ruhe und Ordnung zu sorgen, nicht, wie es sich gehört hätte, erfüllt habe und sogar im Be griff gewesen sei, seine Gewalt an die Streik leitung abzugeben. Während Regierungspräsident Dr. A. Im Hof (lib.) und die Regierungsräte Dr. Aemmer (freis.) und Dr. Miescher (lib.) für energisches Auftreten waren, nahmen die Regie rungsräte A. Stöcklin (freis.), Dr. Mangold (wild), E. Wullschleger (soz.) und Dr. Hauser (soz.) einen gegenteiligen Standpunkt ein. Die rückhaltlose Mißbilligung, welche die Haltung der Mehrheit der Regierung bei der Bevölkerung sand, hat nun bereits zu einem Rücktritt geführt, indem Re gierungsrat A. Stöcklin dem Großen Rat sein Entlassungsgesuch eingereicht hat. Mit aller Strenge ging man im Großen Rate mit den Anstiftern und Führern des Streiks ins Gericht. Die Redner aller bürgerlichen Fraktionen traten da geschlossen auf. Schonungslos legte man die wirklichen Ziele der Streikanstifter bloß. Der Anschlag mißlang dank der festen Haltung von Bundesrat und Bundes versammlung. Alle Redner sprachen diesen Be hörden Zustimmung und Dank aus. So scharf das verwersliche Gewaltmittel des Landesstreiks ver urteilt wurde, ebenso einmütig sprachen sich die bürgerlichen Redner für die Durchführung billiger Reformen aus. Baden, 20. Nov. pt Der Gemeinderat von Baden, an dessen Spitze <PERSON>Nationalrat Jäger</PERSON> steht, veröffentlicht über seine letzte Sitzung folgende Bekanntmachung: Da während des jüngsten revo lutionären Landesstreikes leider auch städtische Ar beiter durch Treubruch gegenüber der Gemeinde öffentliche Interessen gefährdet haben, wird unter Berufung auf Artikel 352 O.-R. sämtlichen Ar beitern der Stadt und der städtischen Werke er öffnet, daß künftig jede Dienstverweigerung sofor tige Entlassung zur Folge hat. Der Gemeinde wird beantragt, dem „Freien Aargauer", der in schamloser Weise revolutionäre Propaganda be treibt, seien die amtlichen Veröffentlichungen der Gemeinde bis auf weiteres zu entziehen. Bei zu ständiger Seite wird das Begehren gestellt, die Be zeichnung „Publikationsorgan der Gemeinde Ba den" im Untertitel des „Freien Aargauer" (Sozial demokratisches Tagblatt des Kantons Aargau) zu verbieten. Neuenburg. Die Bilanz der eben durchleb ten Generalstreiktage ist nicht schwer zu ziehen; sie schließt mit einer tatsachlichen Niederlage der Or ganisatoren dieser Bewegung ab. In den Bezirken Reuenburg, Boudry, Val-de-Travers und Val-de Ruz, wo Tausende von Arbeitern in den verschie densten Industriezweigen beschäftigt sind, wurde nicht gestreikt. Für Locle und La Chaux-de-Fonds wäre dasselbe eingetreten, wenn nicht die elektrische Stromleitung unterbrochon worden wäre, welche die sozialistischen Verwaltungen dieser beiden Orte, absichtlich oder nicht, nicht wiederherzustellen vermochten. Was diejenigen, die dem Oltener Komitee ge horchen, am meisten überraschte, war der hart näckige Widerstand der Streilgegner. Ueberall wurden sofort Bürgerwehren gebildet, und die Großzahl der Neuenburger Jugend hat sich gleich auf die Seite der Ordnungs- und Freiheitsfreunde gestellt. Der Staatsrat erließ eine Proklamation, worin er die Bevölkerung einlud, mit allen gesetz lichen Mitteln gegen die soziale Desorganisation, die der Generalstreik bedeutet, aufzutreten. Dieser Appell tat seine Wirkung. Die Regierung genoß die dauernde und wirksame Unterstützung des Neuenburger Volkes, das seine Nuhe und Kalt blütigkeit bewahrte. Schon vom Dienstagabend, dem 12. November an, war bei den Streikenden eine Müdigkeit zu beobachten, als Vorläuferin der Kapitulation, die am Donnerstag im ganzen Kan ton geseiert wurde. Unsere Sozialdemokraten haben die bittere Er fahrung machen müssen, daß bei uns brutale Mit tel keinen Erfolg haben. Bei der drohenden Ge fahr haben sich die Streikgegner zusammengeschlos sen. Etwas von diesen sozialen Verteidigungs organisationen, die eben gebildet wurden, wird bleiben, und es ist nicht zu zweifeln, daß ein neuer Streik- oder Umsturzversuch noch weniger Erfolg haben würde als der, der soeben jämmerlich ge scheitert ist. Die Festbefoldeten, von denen man behauptete, daß sie zur extremen Linken überge gangen seien, haben, außer wenigen Ausnahmen, die Arbeitsniederlegung verweigert. Mit ihren Verbandsfahnen haben sie an der vaterländischen Kundgebung vom Donnerstagabend in der Haupt stadt teilgenommen. Gegen die sozialistischen Behörden von Locle und La Chaux-de-Fonds, die für die Lichtunter brechung, sogar in den Spitälern, verantwortlich sind, richtet sich ein allgemeiner Sturm der Ent rüstung. Sie würden entfernt, wenn gegenwärtig Wahlen stattfänden. Hingegen werden die kanto nalen Behörden wegen ihrer ruhigen Energie, die die Ruhe und Ordnung ohne militärisches Ein schreiten aufrechtzuerhalten vermochten, einstimmig gelobt. Das Erwachen des Patriotismus bei der stu dierenden Jugend wurde besonders bemerkt. Ohne Zweifel werden von jetzt an die Theorien der außersten Linken in diesen Kreisen, in welchen in den letzten Jahren ein Schwenken nach links zu beobachten war, zum Mißerfolg verurteilt sein. Den streikenden Eisenbahnern verzeiht man ihre Pflichtverletzung nicht, um so weniger, als sie schöne Löhne und große Teuerungszulagen bezie hen. Man verlangt, daß sie exemplarisch gestraft werden, damit sie die Größe ihres Fehlers ein sehen, der die ohnehin schon schwierige Lebens mittelversorgung des Landes außerst gefährdete. Mit einem Wort, der Erfolg der Bürger und der Behörden, die den Ceneralstreik bekämpft ha ben, ist ein vollständiger. Wie zur Zeit der Fünf zigjahrfeier der Republik im Jahre 1898 tat das Neuenburger Volk seine Pflicht, und mit berech tigtem Stolz sieht es heute, daß seine schweizerische Vaterlandsliebe noch in voller Kraft besteht. Der Benjamin der Eidgenossenschaft ist besser als sein Ruf. Er hat es in diesen schweren Tagen der Prü fung bewiesen. Unsere Eidgenossen mögen daran denken, wenn wir in Bern auf mehr Demokratie und mehr Achtung vor den Rechten des Volkes dringen werden. Liebesgaben für das Militär. pt Für die in Rapperswil stationierte Landsturmkompagnie I771 wurde von bürgerlicher Seite eine Sammlung veranstaltet, welche 4324 Fr. ergab. Von diesem Betrag erhielt jeder der 180 Landsturmsoldaten einen Chrensold von 20 Fr. Der verbleibende Rest wird dem gegenwärtig noch 26 Grippekranke, wovon 9 Soldaten, beherbergenden Notspital Rap perswil zugewendet. Die Bündner Gebirasbatailone 92 und 93 er freuen sich im Thurgau herzlicher Aufnahme aich die Bevölkerung, welche die Mannschaften durch Schenkungen von Obst (über 15,000 Kg.), Tee, Zigarren usw. in reichlichem Maße erfreut. Leider haust unter diesen Truppen arg die Grippe, glücklicherweise sind die Fälle aber fast ausschließ lich leichterer Natur. Die bündnerische Regierung hat be schlossen, aus Dank und Anerkennung für die treue Pflierteriüllung jedem aufgebotenen Bündner für die Streitwoche eine besondere Soldzulage von 2 Fr. pro Tag aus der Kantonsbasse zu verab folgen."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (4):
      - "2000" → 2000
      - "6000" → 6000
      - "1898" → 1898
      - "4324" → 4324
    Temporal signal words: jetzt, heute, nach, vor
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 20 days
    OCR quality estimate: 0.987

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Nationalrat Jäger' and 'Bezirken\nReuenburg' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Nationalrat Jäger' near 'Bezirken\nReuenburg' around 1918-11-22?
  4. Resolve temporal expressions relative to 1918-11-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 27 [ID: test_de__123]:
  Publication date : 1948-08-27
  Language         : de
  Person  : 'Direktor der J.E.I.A., W. John Logan'  (QID: N/A)
  Location: 'französischen Zone'  (QID: Q55309)

  [ARTICLE TEXT — entity markers added]
  "Steigende Produktionsquote in Westdeutschland » Frankfurt a. M., 27. August (AP). Die "wirtschaftliche Lage der Bi-Zone mache rasche Fortschritte, erklärte gestern der <PERSON>Direktor der J.E.I.A., W. John Logan</PERSON>. Die ProdMktàomsquote sei in den letzten beiden Monaten stark angestiegen und betrage jetzt 60 Prozent de s Standes von 1937. Zwei Faktoren, denen der beginnende Aufschwung mit zu verdanken sei, seien die im Juni durchgeführte Währungsreform und die Bemühungen der J.E.IA. um Belebung der Aus- und Einfuhr. Die Einfuhren in die Bi-Zone hätten in den ersten sieben Monaten dieses Jahres 282 400 000 Dollar und damit mehr betragen als im gesamten vorigen Jahr. Brigadier M. R. L. Robinson, ein Mitarbeiter von Logan, sagte vor Presse- 1 Vertretern, die Pläne zur Zusammenfassung der Wirtschaft der <LOCATION>französischen Zone</LOCATION> mit derjenigen .der britisch und amerikanisch besetzten Doppelzone würden vorangetrieben. Auf Befragen erklärte er, es seien keine unerwarteten Schwierigkeiten hierbei aufgetaucht. Er erinnerte daran, daß die Vereinigung der Wirtschaftsverwaltungen der britischen und der amerikanischen Zone sogar nach dem diesbezüglichen Beschluß einige Monate gedauert habe. Als mutmaßlichen Zeitpunkt für den Anschluß der Wirtschaft der französischen Zone nannte er den Beginn des nächsten Jahres. Logan nahm dann zu falschen Darstellungen im Zusammenhang mit der J.E.I.A. Stellung, die in verschiedenen Blättern von der sowjetisch lizenzierten „Berliner Zeitung" bis zu dem amerikanischen „Wall Street Journal" erschienen seien. Zu der Behauptung der „Berliner Zeitung", die J.E I.A. habe die Bi-Zone in eine „Zwangsjacke" gesteckt, um den Vereinigten - Staaten Profite zu verschaffen, sagte Logan: „Alle Erlöse aus den Bi-Zonen-Exporten wurden für Importe verwandt. Darüber hinaus werden die Vereinigten Staaten etwa ein« Milliarde Dollar für Lebensimiiitteleinfuhren nach Deutschland ausgeben. Wie kann man da von Profiten für Amerika sprechen?" Klarstellung der französischen Militärregierung zur Borsig-Demontage Berlin, 27. August. (AP). Wegen ungenauer und absichtlich irreführender Pressemeldungen über „Ausplünderung" der Rheinmetall-Borsigwerke in Berlin seitens der französischen Besetzungstruppen — die Meldungen waren in der sowjetisch lizenzierten Presse erschienen — veröffentlicht die französische Militärregierung folgende Klarstellung: 1. Bevor die französischen Behörden ihren Sektor in Berlin übernahmen, war von den sowjetischen Besatzungstruppen der größere Teil des Maschinenparks, das heißt rund 2000 Maschinen, eigenmächtig bereits demontiert und abtransportiert worden. 2. Vor dem Ausschul? für die Liquidierung von Rüstungsmaterial wurden die Rheinmetall-Borsigwerke am 15. Juni 1947 von den Vertretern der Sowjetunion, Englands und Frankreichs als Rüstungsbetrieb bezeichnet. Diese Entscheidung wurde am 29. Juli 1947 vom Koordinierungs-Ausschuß bestätigt. 3. In Erfüllung dieses Beschlusses wurde von den verantwortlichen sowjetischen, amerikanischen, britischen und französischen Behörden die Borsigwerke als reparationspfliahtig erklärt. 4. Nach den Bestimmungen dUese s Beschlusses verteilte die interalliierte Repairatdonsbehörde in Brüssel (IARA) Geräte dieses Betriebes an eine Anzahl von Mitgliedstaalten der Vereinten Nationen. Ausgenommen wurde dabei das elektrische Kraftwerk, das auf Ersuchen Frankreichs von der Reparationsliste gestrichen wurde. Die Mehrzahl der Maschinen wurde den Staaten Mittel- und Ost-Europas auf deren Bitten hin zugesprochein, vor allem der Tschechoslowakei und Jugoslawien. Frankreich erhielt von den 1800 Maschinen nur 100."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Französische Besatzungszone
    Description: eine von vier Zonen, in die Deutschland von den Alliierten nach dem Zweiten Weltkrieg aufgeteilt wurde
    Country: ['Deutschland']
    Aliases: {'de': ['Westzone']}
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (5):
      - "1937" → 1937
      - "2000" → 2000
      - "1947" → 1947
      - "1947" → 1947
      - "1800" → 1800
    Temporal signal words: jetzt, gestern, nach, vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    OCR quality estimate: 0.961

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Direktor der J.E.I.A., W. John Logan' and 'französischen Zone' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Direktor der J.E.I.A., W. John Logan' near 'französischen Zone' around 1948-08-27?
  4. Resolve temporal expressions relative to 1948-08-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 28 [ID: test_de__125]:
  Publication date : 1948-08-27
  Language         : de
  Person  : 'Direktor der J.E.I.A., W. John Logan'  (QID: N/A)
  Location: 'amerikanischen Zone'  (QID: Q55304)

  [ARTICLE TEXT — entity markers added]
  "Steigende Produktionsquote in Westdeutschland » Frankfurt a. M., 27. August (AP). Die "wirtschaftliche Lage der Bi-Zone mache rasche Fortschritte, erklärte gestern der <PERSON>Direktor der J.E.I.A., W. John Logan</PERSON>. Die ProdMktàomsquote sei in den letzten beiden Monaten stark angestiegen und betrage jetzt 60 Prozent de s Standes von 1937. Zwei Faktoren, denen der beginnende Aufschwung mit zu verdanken sei, seien die im Juni durchgeführte Währungsreform und die Bemühungen der J.E.IA. um Belebung der Aus- und Einfuhr. Die Einfuhren in die Bi-Zone hätten in den ersten sieben Monaten dieses Jahres 282 400 000 Dollar und damit mehr betragen als im gesamten vorigen Jahr. Brigadier M. R. L. Robinson, ein Mitarbeiter von Logan, sagte vor Presse- 1 Vertretern, die Pläne zur Zusammenfassung der Wirtschaft der französischen Zone mit derjenigen .der britisch und amerikanisch besetzten Doppelzone würden vorangetrieben. Auf Befragen erklärte er, es seien keine unerwarteten Schwierigkeiten hierbei aufgetaucht. Er erinnerte daran, daß die Vereinigung der Wirtschaftsverwaltungen der britischen und der <LOCATION>amerikanischen Zone</LOCATION> sogar nach dem diesbezüglichen Beschluß einige Monate gedauert habe. Als mutmaßlichen Zeitpunkt für den Anschluß der Wirtschaft der französischen Zone nannte er den Beginn des nächsten Jahres. Logan nahm dann zu falschen Darstellungen im Zusammenhang mit der J.E.I.A. Stellung, die in verschiedenen Blättern von der sowjetisch lizenzierten „Berliner Zeitung" bis zu dem amerikanischen „Wall Street Journal" erschienen seien. Zu der Behauptung der „Berliner Zeitung", die J.E I.A. habe die Bi-Zone in eine „Zwangsjacke" gesteckt, um den Vereinigten - Staaten Profite zu verschaffen, sagte Logan: „Alle Erlöse aus den Bi-Zonen-Exporten wurden für Importe verwandt. Darüber hinaus werden die Vereinigten Staaten etwa ein« Milliarde Dollar für Lebensimiiitteleinfuhren nach Deutschland ausgeben. Wie kann man da von Profiten für Amerika sprechen?" Klarstellung der französischen Militärregierung zur Borsig-Demontage Berlin, 27. August. (AP). Wegen ungenauer und absichtlich irreführender Pressemeldungen über „Ausplünderung" der Rheinmetall-Borsigwerke in Berlin seitens der französischen Besetzungstruppen — die Meldungen waren in der sowjetisch lizenzierten Presse erschienen — veröffentlicht die französische Militärregierung folgende Klarstellung: 1. Bevor die französischen Behörden ihren Sektor in Berlin übernahmen, war von den sowjetischen Besatzungstruppen der größere Teil des Maschinenparks, das heißt rund 2000 Maschinen, eigenmächtig bereits demontiert und abtransportiert worden. 2. Vor dem Ausschul? für die Liquidierung von Rüstungsmaterial wurden die Rheinmetall-Borsigwerke am 15. Juni 1947 von den Vertretern der Sowjetunion, Englands und Frankreichs als Rüstungsbetrieb bezeichnet. Diese Entscheidung wurde am 29. Juli 1947 vom Koordinierungs-Ausschuß bestätigt. 3. In Erfüllung dieses Beschlusses wurde von den verantwortlichen sowjetischen, amerikanischen, britischen und französischen Behörden die Borsigwerke als reparationspfliahtig erklärt. 4. Nach den Bestimmungen dUese s Beschlusses verteilte die interalliierte Repairatdonsbehörde in Brüssel (IARA) Geräte dieses Betriebes an eine Anzahl von Mitgliedstaalten der Vereinten Nationen. Ausgenommen wurde dabei das elektrische Kraftwerk, das auf Ersuchen Frankreichs von der Reparationsliste gestrichen wurde. Die Mehrzahl der Maschinen wurde den Staaten Mittel- und Ost-Europas auf deren Bitten hin zugesprochein, vor allem der Tschechoslowakei und Jugoslawien. Frankreich erhielt von den 1800 Maschinen nur 100."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Amerikanische Besatzungszone
    Description: eine von vier Zonen, in die Deutschland nach dem Zweiten Weltkrieg von den Alliierten aufgeteilt wurde
    Country: ['Q183']
    Aliases: {'en': ['American Zone of Occupation in Germany', 'AMZON', 'U.S. occupation zone, Germany', 'US Zone of Occupation, Germany'], 'de': ['Südwestzone']}
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (5):
      - "1937" → 1937
      - "2000" → 2000
      - "1947" → 1947
      - "1947" → 1947
      - "1800" → 1800
    Temporal signal words: jetzt, gestern, nach, vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    OCR quality estimate: 0.961

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Direktor der J.E.I.A., W. John Logan' and 'amerikanischen Zone' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Direktor der J.E.I.A., W. John Logan' near 'amerikanischen Zone' around 1948-08-27?
  4. Resolve temporal expressions relative to 1948-08-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 29 [ID: test_de__0]:
  Publication date : 1937-12-28
  Language         : de
  Person  : 'Franco'  (QID: Q29179)
  Location: 'Stockholm'  (QID: Q1754)

  [ARTICLE TEXT — entity markers added]
  "Morgen⸗ Ausgabe . Deutſches Nachrichtenbüro G . m . b . H . — — — — — — — — — — — — — — — — — ( Als Manuſkript gedruckt , Nachdruck und jede Art Verbreitung ohne Vereinbarung unterſagt . Ohne alle Gewähr . ) 4 . Jahrg . Berlin , Dienstag , 28 . Dezember Nr . 1937 Von Haſſell beſucht Panzerſchiff „ Deutſchland “ . Rom , 27 . Dezember . Botſchafter von Haſſell hat ſich in Begleitung des Marineattachés , Kapitän zur See Lange , am Montag zum Beſuch des Befehlshabers der deutſchen Spanienſtreitkräfte , Konteradmirals Marſchall , an Bord des über Weihnachten und Neujahr in Neapel liegenden Panzerſchiffes „ Deutſchland “ begeben . Admiral Marſchall gab an Bord ein Frühſtück , an dem außer dem Botſchafter , dem Generalkonſul und dem Marineattaché mit ihren Frauen u . a . auch der Kommandierende Admiral des unteren Tyrrheniſchen Meeres , Geſchwader⸗ Admiral Valli , mit Frau teilnahm . Ein Enkel Muſſolinis geboren . Rom , 27 . Dezember . Die Gemahlin von Vittorio Muſſolini , dem älteſten Sohn des italieniſchen Regierungschefs , iſt am Montag von einem Knaben entbunden worden . der den Namen Guido erhalten ſoll . Jtalieniſche Studienkommiſſion geht nach Tokio . Rom , 27 . Dezember . Die Nachricht der bevorſtehenden Entſendung einer italieniſchen Studienkommiſſion nach Japan findet in der italieniſchen Preſſe lebhafte Zuſtimmung . Der Direktor des Giornale d ' Jtalia erklärt , eine politiſche , wirtſchaftliche und kulturelle Zuſammenarbeit , die durch beiderſeitige Beſuche gefördert und vertieft werde , ſei eine Notwendigkeit , wenn man bedenke , daß die beiden Länder gleichartige Poſitionen und Probleme hätten . Jtalien und Japan ſtänden heute zuſammen mit Deutſchland im Abwehrkampf gegen den Kommunismus , der größten Gefahr , die die Kulturwelt bedrohe . Die verantwortungsbewußte Politik Roms , Berlins und Tokios beruhe auf dem entſchloſſenen Willen ihrer Regierungen und Völker , ſtütze ſich auf eine ſtarke Wehrmacht und verfolge ein klares Ziel , durch das niemand bedroht werde . Trotzdem könne man noch kein Nachlaſſen der gegen die drei Mächte gerichteten feindlichen Stimmung beobachten . So wende ſich beiſpielsweiſe gerade jetzt wieder die amerikaniſche Preſſe gegen die japaniſchen Rüſtungen zur See , obwohl dieſe nicht im entfernteſten an die amerikaniſchen Bauprogramme heranreichten . Die Gleichberechtigung , die angeblich einer der Grundſätze der Demokratie ſei , werde ebenſo auf dem Gebiet der Rüſtungen wie auf anderen lebenswichtigen Gebieten von den drei großen imperialiſtiſchen und kriegeriſchen Demokratien hartnäckig beſtritten . Gegen das Fortbeſtehen der großen Selbſtſucht und der Privilegien ſei jedoch eine entſchiedene Abwehr geboten . Eine Wehrformation der öſterreichiſchen Legitimiſten . Wien , 27 . Dezember . Die Legitimiſten haben in letzter Zeit nicht nur ihre Agitation zuſehends verſtärkt , ſondern ſind auch bemüht , ihre Organiſation auszubauen . Das Neueſte iſt die Gründung einer „ Eiſernen Legion “ , die ſich hauptſächlich aus jungen Leuten zuſammenſetzen und dazu beſtimmt ſein ſoll , den Ordnungs⸗ und Schutzdienſt bei Verſammlungen durchzuführen . Mit einbezogen werden legitimiſtiſche ehemalige Soldaten . Bekanntlich ſind die früheren freiwilligen Wehrformationen im September 1936 aufgelöſt worden , wobei der Vaterländiſchen Front das alleinige Recht übertragen wurde , im Einvernehmen mit dem Bundesheer bewaffnete Formationen aufzuſtellen und zu unterhalten . 5 Memelländer vom litauiſchen Staatspräſidenten begnadigt . Kowno , 27 . Dezember . Der litauiſche Staatspräſident hat aus Anlaß des Weihnachtsfeſtes die vom Kriegsgericht im Neumann⸗ Saß⸗ Prozeß zu zehn Jahren Zuchthaus verurteilten Gefangenen Kwanka , Grau , Kuhn , Riegel und Lapins begnadigt . Neuer Schlag gegen die Kirchen in Sowjetrußland . Warſchau , 27 . Dezember . Nach Meldungen aus Moskau hat die GPU . ein neues Mittel gefunden , um den wenigen noch nicht geſchloſſenen Kirchen in der Sowjetunion den Todesſtoß zu verſetzen . Danach iſt eine Verordnung erſchienen , wonach vom 1 . Januar 1938 ab die Steuern , mit denen die Kirchen und Bethäuſer belegt werden , um 120 v . H . erhöht werden . Es kann kein Zweifel beſtehen , daß die Kirchen nicht in der Lage ſein werden , dieſe Steuer aufzubringen ; denn nach der Verfügung hätte die kleinſte noch erhaltene Kirche in Moskau im Jahre 25000 Rubel zu bezahlen . Es iſt offenbar auch die Abſicht der GPU . auf dem Umweg über dieſe enorme Beſteuerung die chriſtlichen Gemeinden zur Schließung der Kirchen zu zwingen . Schwedens Wirtſchaft fordert Handelsabkommen mit <PERSON>Franco</PERSON> . <LOCATION>Stockholm</LOCATION> , 27 . Dezember . Die maßgebenden Organiſationen der ſchwediſchen Wirtſchaft haben ſich mit einem Schreiben an das Außenminiſterium gewandt , in dem die Wiederanknüpfung von Handelsbeziehungen zum nationalen Spanien verlangt wird . Jn dem Schreiben heißt es , es müßten ſofort Maßnahmen ergriffen werden , um mit den nationalſpaniſchen Behörden Verhandlungen zum Abſchluß eines Handels⸗ und Schiffahrtsabkommens aufzunehmen . Nur durch ein ſolches Abkommen ſei es möglich , die Belange Schwedens auf dem ſpaniſchen Markt wahrzunehmen . Schwere Verluſte der Bolſchewiſten bei Teruel . San Sebaſtian , 27 . Dezember . Wie der Heeresbericht vom Sonntag meldet , dauert der heldenhafte Widerſtand der nationalſpaniſchen Truppen in der Stadt Teruel weiter an . Den bolſchewiſtiſchen Horden wurden ſchwere Verluſte zugefügt . Die nationalen Truppen verbeſſern fortgeſetzt ihre Stellungen . Zwei rote Flugzeuge wurden abgeſchoſſen . Kraftloſere bolſchewiſtiſche Angriffe bei Teruel . Bilbao , 27 . Dezember . Auch am Montag , dem 12 . Tag des bolſchewiſtiſchen Verſuchs , Teruel zu erobern , dauerten die Kämpfe an . Die nationalen Flieger bombardierten heftig die feindlichen Stellungen am Stadtrand und die Nachſchubſtraßen . Sie brachten den Bolſchewiſten große Verluſte bei , was zur Folge hat , daß die bolſchewiſtiſchen Angriffe auf die Feſtung Teruel , die hauptſächlich von Ausländern durchgeführt werden , merklich nachlaſſen . Obwohl die Bolſchewiſten den zur Befreiung anrückenden nationalen Truppen ihre beſten Kräfte entgegenwerfen , müſſen ſie langſam zurückweichen . Den nationalen Truppen unter General Aranda iſt es bereits gelungen , einige wichtige Höhen zu beſetzen . Auf beiden Seiten treffen immer neue Verſtärkungen ein . Die Generalinſpektorin der nationalſpaniſchen Lazarette dankte in einem Aufruf den Krankenpflegerinnen in Teruel und forderte ſie zu weiterem Ausharren auf . Der Kommandeur des I . Armeekorps brachte in einem Funkſpruch die Hoffnung zum Ausdruck , daß die hohen ſoldatiſchen Tugenden und der heldenhafte Kampf der Beſatzung Teruels bald zum entſcheidenden Erfolg führen werden . Deutſche Teilnehmer am Sternflug nach Hoggar unterweas . Paris , 27 . Dezember . Die deutſchen Flieger Miniſterialdirigent Mühlig⸗ Hofmann und ſein Begleiter Oberregierungsrat Dr . Mülberger , ſowie Oberleutnant Goetze und ſein Begleiter Leutnant von Harnier , die jeder an Bord eines Meſſerſchmitt⸗ Flugzeuges von 240 PS an dem Sternflug nach Hoggar teilnehmen , der vom Aero⸗ Klub von Frankreich und vom Aero⸗ Klub von Algerien organiſiert wird , ſind am Montag gegen 16 Uhr 30 auf dem Pariſer Flughafen Le Bourget eingetroffen . Die deutſchen Flieger werden von Le Bourget am 29 . Dezember über Bordeaux — Biarritz — Nimes — Piſa — Rom — Neapel — Palermo — Catania — Tunis nach Algier ſtarten . Sie haben am Sonntag die Strecke Rangsdorf — Breslau — Stolp — Berlin und am Montag die Strecke Berlin — Köln — Paris zurückgelegt . Das dritte deutſche Flugzeug konnte bis Montag noch nicht nach Berlin übergeführt werden und wird demnächſt mit der Beſatzung des NSFK . , Gruppe Lufthanſa , Flugkapitän Klitzſch und Funkermaſchiniſt Schnurr , ſtarten , um nach Möglichkeit die beiden anderen Flugzeuge in Algier zu erreichen ."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Francisco Franco
    Description: spanischer General und Diktator (1892–1975)
    Born: ['+1892-12-04T00:00:00Z']
    Died: ['+1975-11-20T00:00:00Z']
    Birth place: ['Ferrol']
    Death place: ['Madrid']
    Residences: ['Palacio Real El Pardo', 'Pazo de Meirás']
    Work locations: ['Madrid']
  Location Wikidata:
    Label: Stockholm
    Description: Hauptstadt von Schweden
    Country: ['Schweden', 'Kalmarer Union', 'Union zwischen Schweden und Norwegen']
    Located in: ['Oberstatthalterschaft von Schweden', 'Stockholm ehemalige Stadtgemeinde', 'Gemeinde Stockholm']
    Aliases: {'en': ['Sthlm', 'STHLM'], 'fr': ['STHLM']}
    Coordinates: [{'lat': 59.329444444444, 'lon': 18.068611111111}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1937" → 1937
      - "1936" → 1936
      - "1938" → 1938
    Temporal signal words: jetzt, heute, früher, ehemalig, nach, vor, früh
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.977

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Franco' and 'Stockholm' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Franco' near 'Stockholm' around 1937-12-28?
  4. Resolve temporal expressions relative to 1937-12-28. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 30 [ID: test_de__38]:
  Publication date : 1858-02-07
  Language         : de
  Person  : 'frühere Rédacteur des Blattes, Louis Labarre'  (QID: Q4251818)
  Location: 'London'  (QID: Q84)

  [ARTICLE TEXT — entity markers added]
  "Belgien. Brüssel 31. Jan. Als Verfasser deS im „Dra» pcau" erschienenen und angeklagten Artikels wird jetzt der <PERSON>frühere Rédacteur des Blattes, Louis Labarre</PERSON>, genannt. Der jetzige nominelle Herausgeber, Brismee, soll diesmal seine verantwortliche Haut nicht zu Markte tragen wollen, da ihm noch das Jahr Gefängnis), was cc vor Kurzem abgesessen, in den Gliedern liege. Gro» Bes Aufsehen macht ein neuer Artikel in Bezug auf das Attentat, der vor einigen Tagen in einem kleinen Blatte, der „Proletarier" betitelt, erschienen ist. Dieses giftige Blatt steht mit dem socialen Handwerkervereine in <LOCATION>London</LOCATION> in Verbindung und wird von einem rabiaten Schneider, Namens Coulon, redigirt. Das Attentat wird in diesem Artikel mit perfider Frechheit verherr licht, und zugleich werden Orsini und Pierri als Helden ausgerufen und für ihre That mit dem Beifalle des Wahnwitzes überschüttet. Mr. Coulon, der kühne Schneider, wird mit den Rédacteur?« des „Drapeau" und „Crocodile" zusammen demnächst vor Gericht zu erscheinen haben. sM. I.)"

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: London
    Description: Hauptstadt und bevölkerungsreichste Stadt des Vereinigten Königreichs
    Country: ['Römisches Kaiserreich', 'Q110888', 'Mercia', 'Königreich Wessex', 'Königreich England', 'Q161885', 'Q174193', 'Vereinigtes Königreich']
    Located in: ['Königreich Wessex', 'Königreich England', 'Q21', 'Q1137312', 'Q23306']
    Aliases: {'en': ['London, UK', 'London, United Kingdom', 'London, England', 'London UK', 'London U.K.', 'Londinium', 'Loñ', 'Lundenwic', 'Londinio', 'Londini', 'Londiniensium', 'Augusta', 'Trinovantum', 'Kaerlud', 'Karelundein', 'Lunden', 'Big Smoke', 'the Big Smoke', 'Lundenburh', 'Lundenburgh', 'Llyn Dain', 'Llan Dian', 'Londinion', 'Loniniensi', 'Lon.', 'Loñ.', 'Lond.', 'LDN'], 'fr': ['London']}
    Coordinates: [{'lat': 51.507222222222, 'lon': -0.1275}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: jetzt, früher, vor, früh
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.993

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'frühere Rédacteur des Blattes, Louis Labarre' and 'London' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'frühere Rédacteur des Blattes, Louis Labarre' near 'London' around 1858-02-07?
  4. Resolve temporal expressions relative to 1858-02-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 31 [ID: test_de__119]:
  Publication date : 1948-08-27
  Language         : de
  Person  : 'Logan'  (QID: N/A)
  Location: 'Deutschland'  (QID: Q183)

  [ARTICLE TEXT — entity markers added]
  "Steigende Produktionsquote in Westdeutschland » Frankfurt a. M., 27. August (AP). Die "wirtschaftliche Lage der Bi-Zone mache rasche Fortschritte, erklärte gestern der Direktor der J.E.I.A., W. John <PERSON>Logan</PERSON>. Die ProdMktàomsquote sei in den letzten beiden Monaten stark angestiegen und betrage jetzt 60 Prozent de s Standes von 1937. Zwei Faktoren, denen der beginnende Aufschwung mit zu verdanken sei, seien die im Juni durchgeführte Währungsreform und die Bemühungen der J.E.IA. um Belebung der Aus- und Einfuhr. Die Einfuhren in die Bi-Zone hätten in den ersten sieben Monaten dieses Jahres 282 400 000 Dollar und damit mehr betragen als im gesamten vorigen Jahr. Brigadier M. R. L. Robinson, ein Mitarbeiter von Logan, sagte vor Presse- 1 Vertretern, die Pläne zur Zusammenfassung der Wirtschaft der französischen Zone mit derjenigen .der britisch und amerikanisch besetzten Doppelzone würden vorangetrieben. Auf Befragen erklärte er, es seien keine unerwarteten Schwierigkeiten hierbei aufgetaucht. Er erinnerte daran, daß die Vereinigung der Wirtschaftsverwaltungen der britischen und der amerikanischen Zone sogar nach dem diesbezüglichen Beschluß einige Monate gedauert habe. Als mutmaßlichen Zeitpunkt für den Anschluß der Wirtschaft der französischen Zone nannte er den Beginn des nächsten Jahres. Logan nahm dann zu falschen Darstellungen im Zusammenhang mit der J.E.I.A. Stellung, die in verschiedenen Blättern von der sowjetisch lizenzierten „Berliner Zeitung" bis zu dem amerikanischen „Wall Street Journal" erschienen seien. Zu der Behauptung der „Berliner Zeitung", die J.E I.A. habe die Bi-Zone in eine „Zwangsjacke" gesteckt, um den Vereinigten - Staaten Profite zu verschaffen, sagte Logan: „Alle Erlöse aus den Bi-Zonen-Exporten wurden für Importe verwandt. Darüber hinaus werden die Vereinigten Staaten etwa ein« Milliarde Dollar für Lebensimiiitteleinfuhren nach <LOCATION>Deutschland</LOCATION> ausgeben. Wie kann man da von Profiten für Amerika sprechen?" Klarstellung der französischen Militärregierung zur Borsig-Demontage Berlin, 27. August. (AP). Wegen ungenauer und absichtlich irreführender Pressemeldungen über „Ausplünderung" der Rheinmetall-Borsigwerke in Berlin seitens der französischen Besetzungstruppen — die Meldungen waren in der sowjetisch lizenzierten Presse erschienen — veröffentlicht die französische Militärregierung folgende Klarstellung: 1. Bevor die französischen Behörden ihren Sektor in Berlin übernahmen, war von den sowjetischen Besatzungstruppen der größere Teil des Maschinenparks, das heißt rund 2000 Maschinen, eigenmächtig bereits demontiert und abtransportiert worden. 2. Vor dem Ausschul? für die Liquidierung von Rüstungsmaterial wurden die Rheinmetall-Borsigwerke am 15. Juni 1947 von den Vertretern der Sowjetunion, Englands und Frankreichs als Rüstungsbetrieb bezeichnet. Diese Entscheidung wurde am 29. Juli 1947 vom Koordinierungs-Ausschuß bestätigt. 3. In Erfüllung dieses Beschlusses wurde von den verantwortlichen sowjetischen, amerikanischen, britischen und französischen Behörden die Borsigwerke als reparationspfliahtig erklärt. 4. Nach den Bestimmungen dUese s Beschlusses verteilte die interalliierte Repairatdonsbehörde in Brüssel (IARA) Geräte dieses Betriebes an eine Anzahl von Mitgliedstaalten der Vereinten Nationen. Ausgenommen wurde dabei das elektrische Kraftwerk, das auf Ersuchen Frankreichs von der Reparationsliste gestrichen wurde. Die Mehrzahl der Maschinen wurde den Staaten Mittel- und Ost-Europas auf deren Bitten hin zugesprochein, vor allem der Tschechoslowakei und Jugoslawien. Frankreich erhielt von den 1800 Maschinen nur 100."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Deutschland
    Description: Staat in Mitteleuropa
    Country: ['Deutschland']
    Aliases: {'en': ['Federal Republic of Germany'], 'fr': ['RFA', "République fédérale d'Allemagne", 'République fédérale allemande', 'la République fédérale d’Allemagne', 'All.', 'R. F. A.'], 'de': ['Bundesrepublik Deutschland', 'BR Deutschland']}
    Coordinates: [{'lat': 51, 'lon': 10}, {'lat': 51.5, 'lon': 10.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (5):
      - "1937" → 1937
      - "2000" → 2000
      - "1947" → 1947
      - "1947" → 1947
      - "1800" → 1800
    Temporal signal words: jetzt, gestern, nach, vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 1 days
    OCR quality estimate: 0.961

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Logan' and 'Deutschland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Logan' near 'Deutschland' around 1948-08-27?
  4. Resolve temporal expressions relative to 1948-08-27. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 32 [ID: test_de__142]:
  Publication date : 1858-06-20
  Language         : de
  Person  : 'Graf Orloff'  (QID: Q3776769)
  Location: 'Rußland'  (QID: Q34266)

  [ARTICLE TEXT — entity markers added]
  "Frankreich. Paris, >3. Juni. Wohl zu keiner Zeit war man i,it Gerüchten erfinderischer als gerade jstzt, wo fast jede Woche Journale wegen Mitteilung falscher Nach» richten vor Gericht gestellt werden, weil dieselben die öffentliche Meinung aufregten. Wollte man alle Gerüchte beleuchten und widerlegen , die Tag wie Pilze aus dem Boden schießen läßt, ohne daß man sich Rechenschaft über ihren Ursprung zu geben vermöchte, so wäre dies eine eben so mühvolle wie un» dankbare Aufgabe. Wir halten es nur unseres Amtes, das deutsche Publikum vor den lllbertrtibungtn zu warnen, die unsere Zustände doch zu schwarz hinftel« len und schon Unwetter im Anzug sehen, deren Los» bruch nahe bevorstände. Was fabelt man nicht aus dem Umft,nde, daß <PERSON>Graf Orloff</PERSON> sich länger hier aufgehalten, als man Anfangs vermeinte, und schon wußten unsere politischen Lauscher, daß die verlängerte Anwesenheit des Grafen, der in die geheimsten Intentionen seines Souveräns eingeweiht ist, linem Schutz und Trutzbündnisse zwischen Frankreich und <LOCATION>Rußland</LOCATION> gelte, dessen Grundlagen schon festgestellt seien. Wir legen diesem Oerede keine größere Bedeutung bei, als es verdient. Es ist einfach aus der Thatsache entsprungen, daß unser Cabiuct in so manchen politi» schen Fragen mit dem Petersburger Cabinet sympathi« sirt.daß man daraus auf ein einfaffendereS Einver« ständniß schließt, das sich nicht blos auf die restirenben Fragen des Orientfriedens bezieht. Auch über unsere innere Zustände und Fragen gebiert jeder Tag neue Gerüchte, die mit Blitzesschnelle von Mund zu Mund fliegen, obgleich die Presse leine Notiz davon neb» men darf. Alles Verbotene reizt einmal die öffentliche Wißbegier an; was hier nicht gesagt werden darf, fluchtet sich in die Londoner und Brüsseler Presse , wo es alsdann immer in vergrößertem Maßstäbe auftaucht, und gerade das Bestreben unserer Regierenden, die fremde Presse sich dienstbar zu machen, trägt dazu bei, die öffentliche Meinung in dem Glauben zu bestar« ken, daß man Dinge zu verheimlichen suche, die das Licht der Oeffentlichkeit zu scheuen haben. Wäre unsere Presse nur halbfrei, so würde man den Absur» ditaten nicht Glauben schenken, die gläubige Gemüther genug finden. Wähnen nicht Manche, daß ein zweiter 18 Fructidor im Anzüge sei, weil die Orleanisten ihre Sympathien nicht verleugnen, weil die Nepubli kaner, trotz der jüngsten Auönahmsgesehe wieder sich regen und bei den bevorstehenden Tevartementa» wählen ihre Candidate« vorzubringen wagen? Selbst die jüngsten Atk'utatsgcschichtcn finden noch ein gläu« bigeö Publicum, weil die Regierung nicht entschieden dieselben demcntirt und so darf man sich nicht ver wundern, daß unsere politische Atmosphäre so schwül und drückend auf uns lastet, als die senegambische Hitze , unter der wir die ganze Woche seufzen. (Dl.)"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Grigori Iwanowitsch Orlow
    Description: Russian politician (1685-1746)
    Born: ['+1685-01-01T00:00:00Z']
    Died: ['+1746-04-01T00:00:00Z']
    Birth place: ['Q2327841']
    Death place: ['Q649']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.995

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Graf Orloff' and 'Rußland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Graf Orloff' near 'Rußland' around 1858-06-20?
  4. Resolve temporal expressions relative to 1858-06-20. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 33 [ID: test_de__207]:
  Publication date : 1818-08-18
  Language         : de
  Person  : 'H. Decazes'  (QID: Q202289)
  Location: 'Paris'  (QID: Q90)

  [ARTICLE TEXT — entity markers added]
  "In Briefen aus <LOCATION>Paris</LOCATION> vom 3. Aug. heißt es: „Eine Ordonnanz hat also die Absetzung des H. von Vitrolles, als Staatsministers, ausgesprochen. So hat nun dieser Mann, der, aus niedern Volksklassen stammend (er ist der Enkel eines Gastwirths in den Alpen), Sekretair des Ra thes der Minister, Staatsminister und Mitglied des ge heimen Rathes des Königs ward, und 80,000. Fr. Besol dungen zusammenhäufte, nach und nach alle seine Aemter und Einkünfte verloren; und alle diese Opfer hat er dem Vergnügen zu intriguiren gebracht! Man gibt ihn als den Verfasser der Adresse an, welche Franzosen an die frem den Souveraine gerichtet, um sie zu bewegen, sich in unsre häuslichen Angelegenheiten zu mischen. In dieser Adresse ward ganz ernsthaft die Frage erörtert, ob das gegenwär tige Ministerium Frankreich retten könne? Sie entschied, daß es dessen nicht fähig sey, und ersuchte die Mächte, sich ins Mittel zu legen, um dem Könige von Frankreich an dere Minister zu geben, die mehr nach dem Geschmacke des H. v. Vitrolles wären. — Sein Sekretair, H. Lasitte, ist in Verhaft; man hofft, daß seine Erklärungen, und das Verhör, welches H. v. Vitrolles unstreitig selbst zu be stehn haben wird, endlich die Urheber jener Adresse aus Tagslicht ziehn, und uns belehren werden, auf welche Klasse von Franzosen sich der öffentliche Unwille werfen muß. Die Dienstentsetzung des H. v. Vitrolles hat auf die Gemüther der Freunde des Königs und ihres Landes die beßte Wir kung hervorgebracht. Mit Vergnügen gewahrt man, wie die Regierung eine Kraft entwickelt, welche zur Erhaltung chen Ruhe nothwendig ist. Eine neue Handlung der Streuge bezeichnet neuerdings die Linie, die sie sich vorgezeichnet hat. Sie entsetzte H. Agier, Substituten des Königlichen Anwalds beym Pariser-Gerichtshofe, seiner Stelle; seit langer Zeit hat er sich unter die Feinde des Throns gereiht, und man hatte ihn im Verdacht, einer der Rathgeber der elenden Urheber der letzten Verschwörung zu seyn. Dieser junge Mann, von einer ausschweifenden Eigenliebe geblen det, glaubte sich zu großen Dingen bestimmt; da es ihn verdroß, vom Ministerium in einer untergeordneten Stelle gelassen zu werden, so bildete er sich ein, ein Mittel sich emporzuschwingen wäre, wenn er gegen seinen Fürsten Par tey ergriffe. Man kann aus diesem Schritte auf seinen Takt und seine Urtheilskraft schließen. — Die Frau Herzo gin Braunschweig-Bevern ist zu Paris angekommen, um der Vermählung ihrer Nichte, der Fräulein von St. Aulaire, mit dem Polizeyminister beyzuwohnen. Der Aer ger der Ultraroyalisten scheint in gleichem Grade mit dem Glücke des <PERSON>H. Decazes</PERSON> zuzunehmen. Sie sind wüthend über den Glanz, den diese Verbindung über ihn verbreitet; sie sind wüthend über die neuen Beweise von Vertrauen und Achtung, womit der König ihn beehrt; und sie werden rasend über die Entdeckung der Verschwörung, welche das Ansehn und den Ruhm eines Ministers vermehrt, der sich über das Unglück, sie zu Feinden zu haben, damit tröstet, daß er jeden Tag neue Dienste seinem Könige leistet.""

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Élie Decazes
    Description: französischer Staatsmann
    Born: ['+1780-09-28T00:00:00Z']
    Died: ['+1860-10-24T00:00:00Z']
    Birth place: ['Q1007208']
    Death place: ['Q90']
    Work locations: ['Q90']
  Location Wikidata:
    Label: Paris
    Description: Hauptstadt und bevölkerungsreichste Stadt Frankreichs
    Country: ['Q142', 'Königreich Frankreich', 'Q146246', 'Deutsche Besetzung Frankreichs 1940–1945', 'Q142', 'Q71084', 'Q58296']
    Located in: ['Métropole du Grand Paris', 'Q13917', 'Q70972', 'Arrondissement Paris', 'Q1142326', 'Q124881945']
    Aliases: {'en': ['City of Light', 'City of Love', 'Lutetia'], 'fr': ['Ville-Lumière', 'Paname', 'Lutèce', "Ville de l'Amour", 'FR-75', 'Pantruche', 'Ville de Paris']}
    Coordinates: [{'lat': 48.85666666666667, 'lon': 2.352222222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.994

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'H. Decazes' and 'Paris' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'H. Decazes' near 'Paris' around 1818-08-18?
  4. Resolve temporal expressions relative to 1818-08-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 34 [ID: test_de__24]:
  Publication date : 1848-12-15
  Language         : de
  Person  : 'N. Metz'  (QID: Q3343509)
  Location: 'Luxemburg'  (QID: Q32)

  [ARTICLE TEXT — entity markers added]
  "Die Wahlcollegien der Cantons Diekirch und Sa« pellen werden auf Donnerstag, den 21. Dezember d. 1., zehn Uhr Vormittags, zusammenberufen, um jedes einen Abgeordneten zu respectiver Ersetzung der Herrn Ulrich und <PERSON>N. Metz</PERSON> zu wählen. Der General-Administrator des Innern, Ulrich. Die neve, durch Beschlüsse bei» Königs GroßherzogS vom 2. d. M. angeordnete Regierung, welche Unterm heutigen Tage in Thätigkeit getreten ist, hat sofort über cine vorläufig anzunehmende Und der Könlgllch'Großhelzoglichen Genehmigung vorbehaltene Vertheilung der öffentlichen Dienstzweige unter ihre vier Mitglieder Folgende beschlossen: 1. Die General'Admmistration der auswärtigen Angelegenheiten, der Justiz und der Culte ist Herrn Willmai übertragen; die des Inneren Hrn. Ulrich; die der Gemeinde-Angelegenheiten Hrn. Ulveling, und die der Finanzen Hrn. Norbert Metz. 2. Die Genetal-Administration der öffentlichen Staats- und Gemeindebauten und der Militär-Ange» legenheiten ist vorläufig in der Art geseilt, daß vor» läusig die General-Administration der öffentlichen Bauten mit der bei} Inneren, «nd die der Militär« Angelegenheiten mit der der Finanzen vereinigt ist. 3. Auch ist vorläufig der öffentliche Unterricht von der General-Administration des Inneren getrennt und mit der der auswärtigen Angelegenheiten, der Justiz und der Culte verbunden. Der einstweilige Gcneral»Administrator, Präsident des Conseils, Willmar. Bekanntmachung , betreffend den Dienstantritt der neuen General'Admimstratoren und die neve Verthei- Ittrtg der verschiedenen Dienstzweige unter dieselben» <LOCATION>Luxemburg</LOCATION>, de« 6. Dezembet 1848."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Luxemburg
    Description: Staat in Westeuropa
    Country: ['Luxemburg']
    Aliases: {'en': ['Luxemburg', 'Grand Duchy of Luxembourg'], 'fr': ['Grand-Duché de Luxembourg', 'Grand-duché de Luxembourg', 'grand-duché de Luxembourg', 'le Grand-Duché de Luxembourg', 'Lux.'], 'de': ['Groussherzogtum Lëtzebuerg', 'Grand-Duché de Luxembourg', 'Luxembourg'], 'lb': ['Groussherzogtum Lëtzebuerg', 'Lëtzebuerger Land', 'Grand-Duché de Luxembourg', 'Grand-Duché']}
    Coordinates: [{'lat': 49.77, 'lon': 6.13}]
  Known person–location links: {"birth_place": "P19"}

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1848" → 1848
    Temporal signal words: vor
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.963

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'N. Metz' and 'Luxemburg' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'N. Metz' near 'Luxemburg' around 1848-12-15?
  4. Resolve temporal expressions relative to 1848-12-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 35 [ID: test_de__37]:
  Publication date : 1858-02-07
  Language         : de
  Person  : 'jetzige nominelle Herausgeber, Brismee'  (QID: N/A)
  Location: 'London'  (QID: Q84)

  [ARTICLE TEXT — entity markers added]
  "Belgien. Brüssel 31. Jan. Als Verfasser deS im „Dra» pcau" erschienenen und angeklagten Artikels wird jetzt der frühere Rédacteur des Blattes, Louis Labarre, genannt. Der <PERSON>jetzige nominelle Herausgeber, Brismee</PERSON>, soll diesmal seine verantwortliche Haut nicht zu Markte tragen wollen, da ihm noch das Jahr Gefängnis), was cc vor Kurzem abgesessen, in den Gliedern liege. Gro» Bes Aufsehen macht ein neuer Artikel in Bezug auf das Attentat, der vor einigen Tagen in einem kleinen Blatte, der „Proletarier" betitelt, erschienen ist. Dieses giftige Blatt steht mit dem socialen Handwerkervereine in <LOCATION>London</LOCATION> in Verbindung und wird von einem rabiaten Schneider, Namens Coulon, redigirt. Das Attentat wird in diesem Artikel mit perfider Frechheit verherr licht, und zugleich werden Orsini und Pierri als Helden ausgerufen und für ihre That mit dem Beifalle des Wahnwitzes überschüttet. Mr. Coulon, der kühne Schneider, wird mit den Rédacteur?« des „Drapeau" und „Crocodile" zusammen demnächst vor Gericht zu erscheinen haben. sM. I.)"

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: jetzt, früher, vor, früh
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.993

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'jetzige nominelle Herausgeber, Brismee' and 'London' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'jetzige nominelle Herausgeber, Brismee' near 'London' around 1858-02-07?
  4. Resolve temporal expressions relative to 1858-02-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 36 [ID: test_de__60]:
  Publication date : 1928-02-15
  Language         : de
  Person  : 'Simon Tovbini'  (QID: N/A)
  Location: 'Berlin'  (QID: Q64)

  [ARTICLE TEXT — entity markers added]
  "Paris. 15. Febr. Gs scheinen französischerseits Bemühungen im Gange zu sein, die französischen Kammerwahlen nach den deutschen Reichstagswahlen stattfinden zu lassen. Von Regierungsseite war wiederholt versichert worden, daß die Wahlen am 22. April erfolgen sollen. Gestern abend tauchten in den Wandelgängen der Kammer plötzlich Gerüchte auf,die von einer Verschiebung des Wahltages berichteten. Paris, 15. Febr. Wie aus CasManca gemeldet wird, haben sich die Unruhen im noch nicht unterwor- fenen Grenzgebiet so gesteigert, daß sich die französi- sche Militärverwaltung zur Entsendung einer Straf- expedition entschloßEs soll eine Beschießung des Gebietes der Beue Mellal erfolgen, wo seinerzeit die Angehörigen des Generalgouverneurs Steeg hinge, führt worden waren. Zum wirksameren Erfolge der Beschießung ist ein- Hlluptanfiedlungsort der zahlreichen Gebirgsbewohner gewählt worden. » » « Paris, 15. Febr. Die Anklagekammer hat gestern die Anwäge von Blumenstein, Laeasze und <PERSON>Simon Tovbini</PERSON> auf proviforifche Freilassung verworfen., « » » <LOCATION>Berlin</LOCATION>, 15. Febr. Das ..Berliner Tageblatt" meldet aus Wiesbaden: Gegen den Eingemeindungsplan von Frankfurt am Main ist von der Rheinlandlommission Einspruch erhoben worden. Saarbrücken, 14. Febr. Die französischen Bergwerlsdireltionen haben mit den angetündigien Massenentlafsungen von Bergarbeitern bereits begonnen. Auf der Grube “Velsen" wurde eine Anzahl Arbeiter mit einer Schichtvergütung fristlos entlassen. Auf der Grube «Hoftenbach" wurde den Bergleuten, die im Alter von 54 bis 62 Jahren stehen, gekündigt. Man spricht sogar von einer Stillegung dieser Grube. « » » Butarest, 14. Febr. Die 'Nationale Bauernpartei hat mit der Sozialistischen Partei eine Vereinbarung für einen gemeinsamen Kampf gegen die Regierung getroffen. London, 14. Febr. Nach Meldungen aus NewYork hielt der amerikanische Admiral Plunkeii, der ßestern von seinem Posten der Flottenstation in VroUyn zurückgetreten ist. bei einem Essen eine Rede, in der er seine frühere Erklärung wiederholte, daß der Krieg nach seiner Ansicht unvermeidlich sei. Plunlett fügte aber abschwächend hinzu, daß für die nahe Znz knnft noch leine Gefahr bestände."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Berlin
    Description: Hauptstadt und bevölkerungsreichste Stadt der Bundesrepublik Deutschland
    Country: ['Mark Brandenburg', 'Brandenburg-Preußen', 'Q27306', 'Q150981', 'Q43287', 'Weimarer Republik', 'Q7318', 'Q55300', 'Deutsche Demokratische Republik', 'Q183', 'Q713750']
    Located in: ['Q148499', 'Brandenburg-Preußen', 'Q27306', 'Q700264', 'Q27306', 'Freistaat Preußen', 'Q7318', 'Deutschland']
    Aliases: {'en': ['Berlin, Germany', 'DE-BE'], 'de': ['Stadt Berlin', 'Berlin, Deutschland', 'Bundeshauptstadt Berlin', 'Land Berlin', 'DE-BE', 'Berlin (Deutschland)', 'BE', 'Bln', 'Bln.']}
    Coordinates: [{'lat': 52.516666666667, 'lon': 13.383333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: gestern, früher, nach, früh
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.966

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Simon Tovbini' and 'Berlin' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Simon Tovbini' near 'Berlin' around 1928-02-15?
  4. Resolve temporal expressions relative to 1928-02-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 37 [ID: test_de__143]:
  Publication date : 1858-06-20
  Language         : de
  Person  : 'Graf Orloff'  (QID: Q3776769)
  Location: 'Frankreich'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "<LOCATION>Frankreich</LOCATION>. Paris, >3. Juni. Wohl zu keiner Zeit war man i,it Gerüchten erfinderischer als gerade jstzt, wo fast jede Woche Journale wegen Mitteilung falscher Nach» richten vor Gericht gestellt werden, weil dieselben die öffentliche Meinung aufregten. Wollte man alle Gerüchte beleuchten und widerlegen , die Tag wie Pilze aus dem Boden schießen läßt, ohne daß man sich Rechenschaft über ihren Ursprung zu geben vermöchte, so wäre dies eine eben so mühvolle wie un» dankbare Aufgabe. Wir halten es nur unseres Amtes, das deutsche Publikum vor den lllbertrtibungtn zu warnen, die unsere Zustände doch zu schwarz hinftel« len und schon Unwetter im Anzug sehen, deren Los» bruch nahe bevorstände. Was fabelt man nicht aus dem Umft,nde, daß <PERSON>Graf Orloff</PERSON> sich länger hier aufgehalten, als man Anfangs vermeinte, und schon wußten unsere politischen Lauscher, daß die verlängerte Anwesenheit des Grafen, der in die geheimsten Intentionen seines Souveräns eingeweiht ist, linem Schutz und Trutzbündnisse zwischen Frankreich und Rußland gelte, dessen Grundlagen schon festgestellt seien. Wir legen diesem Oerede keine größere Bedeutung bei, als es verdient. Es ist einfach aus der Thatsache entsprungen, daß unser Cabiuct in so manchen politi» schen Fragen mit dem Petersburger Cabinet sympathi« sirt.daß man daraus auf ein einfaffendereS Einver« ständniß schließt, das sich nicht blos auf die restirenben Fragen des Orientfriedens bezieht. Auch über unsere innere Zustände und Fragen gebiert jeder Tag neue Gerüchte, die mit Blitzesschnelle von Mund zu Mund fliegen, obgleich die Presse leine Notiz davon neb» men darf. Alles Verbotene reizt einmal die öffentliche Wißbegier an; was hier nicht gesagt werden darf, fluchtet sich in die Londoner und Brüsseler Presse , wo es alsdann immer in vergrößertem Maßstäbe auftaucht, und gerade das Bestreben unserer Regierenden, die fremde Presse sich dienstbar zu machen, trägt dazu bei, die öffentliche Meinung in dem Glauben zu bestar« ken, daß man Dinge zu verheimlichen suche, die das Licht der Oeffentlichkeit zu scheuen haben. Wäre unsere Presse nur halbfrei, so würde man den Absur» ditaten nicht Glauben schenken, die gläubige Gemüther genug finden. Wähnen nicht Manche, daß ein zweiter 18 Fructidor im Anzüge sei, weil die Orleanisten ihre Sympathien nicht verleugnen, weil die Nepubli kaner, trotz der jüngsten Auönahmsgesehe wieder sich regen und bei den bevorstehenden Tevartementa» wählen ihre Candidate« vorzubringen wagen? Selbst die jüngsten Atk'utatsgcschichtcn finden noch ein gläu« bigeö Publicum, weil die Regierung nicht entschieden dieselben demcntirt und so darf man sich nicht ver wundern, daß unsere politische Atmosphäre so schwül und drückend auf uns lastet, als die senegambische Hitze , unter der wir die ganze Woche seufzen. (Dl.)"

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.995

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Graf Orloff' and 'Frankreich' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Graf Orloff' near 'Frankreich' around 1858-06-20?
  4. Resolve temporal expressions relative to 1858-06-20. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 38 [ID: test_de__186]:
  Publication date : 1858-11-28
  Language         : de
  Person  : 'Gott'  (QID: Q190)
  Location: 'Preußen'  (QID: Q27306)

  [ARTICLE TEXT — entity markers added]
  "Gewisse sehnsüchtige Blicke richten sich jetzt in eini» gen Ländern Deutschlands nach einem gewissen Ziele, das sie nie aus den Augen gelassen haben, mit ge» schärfter Aufmerksamkeit, und die betreffenden Leute reiben sich im Geheimen die Hände und glauben in den Zeichen der Zeit für ihr Werk eine günstige Constella» tion zu finden, Sie begrüßten mit Jubel den .System» Wechsel" (wie sie es nennen) in <LOCATION>Preußen</LOCATION>, sie gratu» liren aller Welt zu dem nun hereinbrechen sollenden liberaleren Regime. Die Negenwürmcr, welche bisher hübsch ruhig und sittsam unter der Bodendecke ver» blieben waren, wühlen sich nun, seit ein so erquickender Liberalitätsregen auf das verdorrte Preußenland nie» dergerauscht sein soll, emsig empor und zeigen die Köpfe. Man agitirt und „arbeitet" mit Macht; man bearbeitet und entstammt die Wahlgemüther und all» bereits ist, wie wir lesen, ein Treiben in Berlin, wie es seit 1848 nicht mehr vorhanden gewesen. Es wer» den Reden und Ervectorationen laut, die an die schönsten ersten Vlütben von damals nur zu frappant erinnern, und — wo hinaus? Vergeblich versichern berechtigte öffentliche Organe und vernünftige Leute, baß in Preußen kein System» Wechsel eingetreten sei, sondern bloß ein Personen» Wechsel; das hinoert gewisse Leute nicht, in ihrer Arbeit fortzufahren, und gesetzt auch, es wäre nun kein System-, sondern bloß ein Personenwechsel gewesen? Tas macht gewisse Leute nicht irre; sie geben sich dann höchstens die Parole: „Einstweilen zum Rückzug ge» blasen!" wir haben doch schon ein gut Stück Arbeit dem Ziele näher gerückt; denn die Gemüther sind ent» flammt, die hoffnungsschwangeren erhitzten Gemüther Zur „neuen Aera" in Preußen. werden mit der neuen Negierung, wenn sie ihren Wünschen nicht gerecht werden will, unzufrieden; man hat ferner bei dieser Liberalitätsgelegenheit seine Leute lenüen gelernt", man hat herausfühlen können, daß man zurrechten Zeit auf diesen und jenen bauen könne;" man hat wieder ein artiges Portiönchcn Unkraut unter den Waizcn gesäet, —Herz was willst du mehr? — Unverkennbar läuft ein rother Faden durch diese Er» scheinungcn und sehen kann ihn Jedermann, ausgenommen wer sich darin behaglich fühlt, in Sicher» heitoträumen eingelullt zu werden. Doch das Er» wachen wird wohl nicht gar zu lange auf sich warten lassen und ist bei <PERSON>Gott</PERSON> nachgerade eben nicht an der Unzeit, zu den Rossen zu schauen. Niemand aber verhehle sich, daß es überall in Deutschland unter der Oberfläche erklecklich gahrt, und Niemand gebe sich dem unsinnigen Wahne hin, es gebe keinen Feind, weil man keinen sieht. Radicale Leiber können sterben, aber der radicale Geist stirbt nicht; er ist nur seit 1849 vorsichtiger geworden und nimmt seine Zeit wahr, wo er handeln zu können glaubt, Die Schweiz hat seiner Zeit diesen Wahn theuer bezahlt ; man war nach den Siegen des Sonderbundes über die Radicale« von 1844 und 1845 ganz entzückt und beruhigt, man träumte von einem für lange Zeiten vernichteten Feinde ; allein dieser Feind nahm seine Zeit wahr; im Jahre 1847, unter dem Zuwinken und Veklückwünschen gewisser liberalisirender Länder — die es dann hart genug büßen mußten — richtete er sich in voller Brutalität empor; die edlen U» kantone verbluteten in dieser Principienschlacht und kamen in radicale Knechtschaft; die liberalen Nachbarn jubelten; es zeigten sich im deutschen Westen die ersten Schwalben der Revolution ; in Baden tagte ein Vorparlament, man hielt schon gedruckt „die Wünsche des Volkes" bereit, die dann zu „Förde« rungen wurden , und es hat bloß noch des Pariser Februar bedurft und die entfesselte Fluth brach he« rein Bayern, Oesterreich , Preußen erlebten ihre Maiztage und bald hatte sich der rothe Faden nach allen Seiten hin verbreitet. Es kommt eben Alles darauf an, diesen rothen Faden nicht aus den Augen zu lassen , ihn sorgsam zu verfolgen und sich nicht täuschen zu lassen, wenn er sich plötzlich hie und da unter einen weißschwarzen, schwarzgelbcn, oder weiß» blauen Oberfläche verbergen sollte. (M. I.)"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Gott
    Description: zentrales Objekt des Glaubens in monotheistischen Religionen
  Location Wikidata:
    Label: Königreich Preußen
    Description: ehemaliger europäischer Staat (1701–1918), ab 1871 Teil des Deutschen Reichs
    Country: ['Deutsches Kaiserreich']
    Aliases: {'fr': ['Prusse'], 'de': ['Preußen', 'Kgr. Preußen', 'preussische Monarchie'], 'lb': ['Preisen']}
    Coordinates: [{'lat': 53, 'lon': 14}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (5):
      - "1848" → 1848
      - "1849" → 1849
      - "1844" → 1844
      - "1845" → 1845
      - "1847" → 1847
    Temporal signal words: jetzt, nicht mehr, nach, vor
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 9 days
    OCR quality estimate: 0.992

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Gott' and 'Preußen' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Gott' near 'Preußen' around 1858-11-28?
  4. Resolve temporal expressions relative to 1858-11-28. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 39 [ID: test_de__14]:
  Publication date : 1937-12-28
  Language         : de
  Person  : 'Guido'  (QID: N/A)
  Location: 'Roms'  (QID: Q220)

  [ARTICLE TEXT — entity markers added]
  "Morgen⸗ Ausgabe . Deutſches Nachrichtenbüro G . m . b . H . — — — — — — — — — — — — — — — — — ( Als Manuſkript gedruckt , Nachdruck und jede Art Verbreitung ohne Vereinbarung unterſagt . Ohne alle Gewähr . ) 4 . Jahrg . Berlin , Dienstag , 28 . Dezember Nr . 1937 Von Haſſell beſucht Panzerſchiff „ Deutſchland “ . Rom , 27 . Dezember . Botſchafter von Haſſell hat ſich in Begleitung des Marineattachés , Kapitän zur See Lange , am Montag zum Beſuch des Befehlshabers der deutſchen Spanienſtreitkräfte , Konteradmirals Marſchall , an Bord des über Weihnachten und Neujahr in Neapel liegenden Panzerſchiffes „ Deutſchland “ begeben . Admiral Marſchall gab an Bord ein Frühſtück , an dem außer dem Botſchafter , dem Generalkonſul und dem Marineattaché mit ihren Frauen u . a . auch der Kommandierende Admiral des unteren Tyrrheniſchen Meeres , Geſchwader⸗ Admiral Valli , mit Frau teilnahm . Ein Enkel Muſſolinis geboren . Rom , 27 . Dezember . Die Gemahlin von Vittorio Muſſolini , dem älteſten Sohn des italieniſchen Regierungschefs , iſt am Montag von einem Knaben entbunden worden . der den Namen <PERSON>Guido</PERSON> erhalten ſoll . Jtalieniſche Studienkommiſſion geht nach Tokio . Rom , 27 . Dezember . Die Nachricht der bevorſtehenden Entſendung einer italieniſchen Studienkommiſſion nach Japan findet in der italieniſchen Preſſe lebhafte Zuſtimmung . Der Direktor des Giornale d ' Jtalia erklärt , eine politiſche , wirtſchaftliche und kulturelle Zuſammenarbeit , die durch beiderſeitige Beſuche gefördert und vertieft werde , ſei eine Notwendigkeit , wenn man bedenke , daß die beiden Länder gleichartige Poſitionen und Probleme hätten . Jtalien und Japan ſtänden heute zuſammen mit Deutſchland im Abwehrkampf gegen den Kommunismus , der größten Gefahr , die die Kulturwelt bedrohe . Die verantwortungsbewußte Politik <LOCATION>Roms</LOCATION> , Berlins und Tokios beruhe auf dem entſchloſſenen Willen ihrer Regierungen und Völker , ſtütze ſich auf eine ſtarke Wehrmacht und verfolge ein klares Ziel , durch das niemand bedroht werde . Trotzdem könne man noch kein Nachlaſſen der gegen die drei Mächte gerichteten feindlichen Stimmung beobachten . So wende ſich beiſpielsweiſe gerade jetzt wieder die amerikaniſche Preſſe gegen die japaniſchen Rüſtungen zur See , obwohl dieſe nicht im entfernteſten an die amerikaniſchen Bauprogramme heranreichten . Die Gleichberechtigung , die angeblich einer der Grundſätze der Demokratie ſei , werde ebenſo auf dem Gebiet der Rüſtungen wie auf anderen lebenswichtigen Gebieten von den drei großen imperialiſtiſchen und kriegeriſchen Demokratien hartnäckig beſtritten . Gegen das Fortbeſtehen der großen Selbſtſucht und der Privilegien ſei jedoch eine entſchiedene Abwehr geboten . Eine Wehrformation der öſterreichiſchen Legitimiſten . Wien , 27 . Dezember . Die Legitimiſten haben in letzter Zeit nicht nur ihre Agitation zuſehends verſtärkt , ſondern ſind auch bemüht , ihre Organiſation auszubauen . Das Neueſte iſt die Gründung einer „ Eiſernen Legion “ , die ſich hauptſächlich aus jungen Leuten zuſammenſetzen und dazu beſtimmt ſein ſoll , den Ordnungs⸗ und Schutzdienſt bei Verſammlungen durchzuführen . Mit einbezogen werden legitimiſtiſche ehemalige Soldaten . Bekanntlich ſind die früheren freiwilligen Wehrformationen im September 1936 aufgelöſt worden , wobei der Vaterländiſchen Front das alleinige Recht übertragen wurde , im Einvernehmen mit dem Bundesheer bewaffnete Formationen aufzuſtellen und zu unterhalten . 5 Memelländer vom litauiſchen Staatspräſidenten begnadigt . Kowno , 27 . Dezember . Der litauiſche Staatspräſident hat aus Anlaß des Weihnachtsfeſtes die vom Kriegsgericht im Neumann⸗ Saß⸗ Prozeß zu zehn Jahren Zuchthaus verurteilten Gefangenen Kwanka , Grau , Kuhn , Riegel und Lapins begnadigt . Neuer Schlag gegen die Kirchen in Sowjetrußland . Warſchau , 27 . Dezember . Nach Meldungen aus Moskau hat die GPU . ein neues Mittel gefunden , um den wenigen noch nicht geſchloſſenen Kirchen in der Sowjetunion den Todesſtoß zu verſetzen . Danach iſt eine Verordnung erſchienen , wonach vom 1 . Januar 1938 ab die Steuern , mit denen die Kirchen und Bethäuſer belegt werden , um 120 v . H . erhöht werden . Es kann kein Zweifel beſtehen , daß die Kirchen nicht in der Lage ſein werden , dieſe Steuer aufzubringen ; denn nach der Verfügung hätte die kleinſte noch erhaltene Kirche in Moskau im Jahre 25000 Rubel zu bezahlen . Es iſt offenbar auch die Abſicht der GPU . auf dem Umweg über dieſe enorme Beſteuerung die chriſtlichen Gemeinden zur Schließung der Kirchen zu zwingen . Schwedens Wirtſchaft fordert Handelsabkommen mit Franco . Stockholm , 27 . Dezember . Die maßgebenden Organiſationen der ſchwediſchen Wirtſchaft haben ſich mit einem Schreiben an das Außenminiſterium gewandt , in dem die Wiederanknüpfung von Handelsbeziehungen zum nationalen Spanien verlangt wird . Jn dem Schreiben heißt es , es müßten ſofort Maßnahmen ergriffen werden , um mit den nationalſpaniſchen Behörden Verhandlungen zum Abſchluß eines Handels⸗ und Schiffahrtsabkommens aufzunehmen . Nur durch ein ſolches Abkommen ſei es möglich , die Belange Schwedens auf dem ſpaniſchen Markt wahrzunehmen . Schwere Verluſte der Bolſchewiſten bei Teruel . San Sebaſtian , 27 . Dezember . Wie der Heeresbericht vom Sonntag meldet , dauert der heldenhafte Widerſtand der nationalſpaniſchen Truppen in der Stadt Teruel weiter an . Den bolſchewiſtiſchen Horden wurden ſchwere Verluſte zugefügt . Die nationalen Truppen verbeſſern fortgeſetzt ihre Stellungen . Zwei rote Flugzeuge wurden abgeſchoſſen . Kraftloſere bolſchewiſtiſche Angriffe bei Teruel . Bilbao , 27 . Dezember . Auch am Montag , dem 12 . Tag des bolſchewiſtiſchen Verſuchs , Teruel zu erobern , dauerten die Kämpfe an . Die nationalen Flieger bombardierten heftig die feindlichen Stellungen am Stadtrand und die Nachſchubſtraßen . Sie brachten den Bolſchewiſten große Verluſte bei , was zur Folge hat , daß die bolſchewiſtiſchen Angriffe auf die Feſtung Teruel , die hauptſächlich von Ausländern durchgeführt werden , merklich nachlaſſen . Obwohl die Bolſchewiſten den zur Befreiung anrückenden nationalen Truppen ihre beſten Kräfte entgegenwerfen , müſſen ſie langſam zurückweichen . Den nationalen Truppen unter General Aranda iſt es bereits gelungen , einige wichtige Höhen zu beſetzen . Auf beiden Seiten treffen immer neue Verſtärkungen ein . Die Generalinſpektorin der nationalſpaniſchen Lazarette dankte in einem Aufruf den Krankenpflegerinnen in Teruel und forderte ſie zu weiterem Ausharren auf . Der Kommandeur des I . Armeekorps brachte in einem Funkſpruch die Hoffnung zum Ausdruck , daß die hohen ſoldatiſchen Tugenden und der heldenhafte Kampf der Beſatzung Teruels bald zum entſcheidenden Erfolg führen werden . Deutſche Teilnehmer am Sternflug nach Hoggar unterweas . Paris , 27 . Dezember . Die deutſchen Flieger Miniſterialdirigent Mühlig⸗ Hofmann und ſein Begleiter Oberregierungsrat Dr . Mülberger , ſowie Oberleutnant Goetze und ſein Begleiter Leutnant von Harnier , die jeder an Bord eines Meſſerſchmitt⸗ Flugzeuges von 240 PS an dem Sternflug nach Hoggar teilnehmen , der vom Aero⸗ Klub von Frankreich und vom Aero⸗ Klub von Algerien organiſiert wird , ſind am Montag gegen 16 Uhr 30 auf dem Pariſer Flughafen Le Bourget eingetroffen . Die deutſchen Flieger werden von Le Bourget am 29 . Dezember über Bordeaux — Biarritz — Nimes — Piſa — Rom — Neapel — Palermo — Catania — Tunis nach Algier ſtarten . Sie haben am Sonntag die Strecke Rangsdorf — Breslau — Stolp — Berlin und am Montag die Strecke Berlin — Köln — Paris zurückgelegt . Das dritte deutſche Flugzeug konnte bis Montag noch nicht nach Berlin übergeführt werden und wird demnächſt mit der Beſatzung des NSFK . , Gruppe Lufthanſa , Flugkapitän Klitzſch und Funkermaſchiniſt Schnurr , ſtarten , um nach Möglichkeit die beiden anderen Flugzeuge in Algier zu erreichen ."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Rom
    Description: Haupt- und bevölkerungsreichste Stadt Italiens
    Country: ['Italien', 'Kirchenstaat', 'Kingdom of Italy', 'Q583038', 'Q12544', 'Q172579', 'Römische Königszeit', 'Q17167', 'Q2277', 'Q42834', 'Vatikanstadt']
    Located in: ['Provinz Rom', 'Kirchenstaat', 'Rome', 'Q1747689', 'Q17167', 'Römisches Kaiserreich', 'Weströmisches Reich', 'Metropolitanstadt Rom', 'circle of Rome']
    Aliases: {'en': ['The Eternal City', 'Roma', 'Rome, Italy', 'City of Seven Hills'], 'fr': ['La ville éternelle', 'La ville aux sept collines', 'Roma', "l'Urbs"], 'de': ['Die Ewige Stadt', 'Roma'], 'lb': ['Roma', "D'Éiweg Stad"]}
    Coordinates: [{'lat': 41.893055555556, 'lon': 12.482777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1937" → 1937
      - "1936" → 1936
      - "1938" → 1938
    Temporal signal words: jetzt, heute, früher, ehemalig, nach, vor, früh
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.977

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Guido' and 'Roms' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Guido' near 'Roms' around 1937-12-28?
  4. Resolve temporal expressions relative to 1937-12-28. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 40 [ID: test_de__72]:
  Publication date : 1928-02-15
  Language         : de
  Person  : 'Blumenstein'  (QID: N/A)
  Location: 'Frankfurt am Main'  (QID: Q1794)

  [ARTICLE TEXT — entity markers added]
  "Paris. 15. Febr. Gs scheinen französischerseits Bemühungen im Gange zu sein, die französischen Kammerwahlen nach den deutschen Reichstagswahlen stattfinden zu lassen. Von Regierungsseite war wiederholt versichert worden, daß die Wahlen am 22. April erfolgen sollen. Gestern abend tauchten in den Wandelgängen der Kammer plötzlich Gerüchte auf,die von einer Verschiebung des Wahltages berichteten. Paris, 15. Febr. Wie aus CasManca gemeldet wird, haben sich die Unruhen im noch nicht unterwor- fenen Grenzgebiet so gesteigert, daß sich die französi- sche Militärverwaltung zur Entsendung einer Straf- expedition entschloßEs soll eine Beschießung des Gebietes der Beue Mellal erfolgen, wo seinerzeit die Angehörigen des Generalgouverneurs Steeg hinge, führt worden waren. Zum wirksameren Erfolge der Beschießung ist ein- Hlluptanfiedlungsort der zahlreichen Gebirgsbewohner gewählt worden. » » « Paris, 15. Febr. Die Anklagekammer hat gestern die Anwäge von <PERSON>Blumenstein</PERSON>, Laeasze und Simon Tovbini auf proviforifche Freilassung verworfen., « » » Berlin, 15. Febr. Das ..Berliner Tageblatt" meldet aus Wiesbaden: Gegen den Eingemeindungsplan von <LOCATION>Frankfurt am Main</LOCATION> ist von der Rheinlandlommission Einspruch erhoben worden. Saarbrücken, 14. Febr. Die französischen Bergwerlsdireltionen haben mit den angetündigien Massenentlafsungen von Bergarbeitern bereits begonnen. Auf der Grube “Velsen" wurde eine Anzahl Arbeiter mit einer Schichtvergütung fristlos entlassen. Auf der Grube «Hoftenbach" wurde den Bergleuten, die im Alter von 54 bis 62 Jahren stehen, gekündigt. Man spricht sogar von einer Stillegung dieser Grube. « » » Butarest, 14. Febr. Die 'Nationale Bauernpartei hat mit der Sozialistischen Partei eine Vereinbarung für einen gemeinsamen Kampf gegen die Regierung getroffen. London, 14. Febr. Nach Meldungen aus NewYork hielt der amerikanische Admiral Plunkeii, der ßestern von seinem Posten der Flottenstation in VroUyn zurückgetreten ist. bei einem Essen eine Rede, in der er seine frühere Erklärung wiederholte, daß der Krieg nach seiner Ansicht unvermeidlich sei. Plunlett fügte aber abschwächend hinzu, daß für die nahe Znz knnft noch leine Gefahr bestände."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: gestern, früher, nach, früh
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.966

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Blumenstein' and 'Frankfurt am Main' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Blumenstein' near 'Frankfurt am Main' around 1928-02-15?
  4. Resolve temporal expressions relative to 1928-02-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 41 [ID: test_de__87]:
  Publication date : 1918-11-22
  Language         : de
  Person  : 'Nationalrat Jäger'  (QID: Q17305208)
  Location: 'Val-de-Travers'  (QID: Q648339)

  [ARTICLE TEXT — entity markers added]
  "Generalstreik-Nachklänge. Postdienst der Zürcher Studenten. (Korr.) Die Postaustragung durch Studenten während des Generalstreiles in der Stadt Zürich, das war wohl eines der erfreulichsten Bilder in den trüben, ernsten Tagen, die wir durchgemacht haben. Wie freundlicher, wärmender Sonnenschein war's, diese fröhliche, diensteifrige Jungmannschaft in mitten der Atmosphäre von Erbitterung und Haß, Aufhetzung und Terrorismus. Als Ordnung und Diszipuin versagten, als die Postangestellten, statt ihren Obliegenheiten nachzukommen, im Volks hause von politischen Strebern und turbulenten Schwätzern sich ihr Tun und Lassen vorschreiben ließen, da hat die akademische Jugend spontan aus dem Bestreben heraus, sich nutzlich zu machen und der Allgemeinheit zu dienen, sich der Post und Telegraphenverwallung zur Verfügung ge stellt. Vorerst galt es, die Aufforderungen zur Wiederaufnahme der Arbeit an das streikende Personal an Mann zu bringen. Dann ging's an die Austragung der Briefe, Pakete und Tele gramme. Die strengen Bestimmungen betr. Wah rung des Postgeheimnisses ließen es aber nicht zu, die arbeitsfreudigen Studenten, die sich mehrere hundert Mann stark auf der Hauptpost eingefun den hatten, ohne weiteres zu beschäftigen. Ein jeder mußte zuerst unter Bekanntgabe der Vor schriften des Bundesstrafrechtes formell in Pflicht genommen und als Postaushelser angestellt wer den. Und was noch viel erschwerender war, es mußte für jeden dieser Bestellboten eine mili tärische Bedeckung von 1—2 Mann, nebst ebenso vielen Kommilitonen mitgegeben werden, damit gegen Bedrohungen und Ueberfälle von seiten Streikender ein ausreichender Schutz vorhanden sei. Diese Vorsichtsmaßregel erwies sich leider nicht als unnötig. Einzelne Studenten wurden tatsächlich auf der Bestelltour von bolschewistischen Gslementen auf der Straße oder in Hausgängen überfallen und geschlagen, und wenn keine bösen Folgen daraus erwachsen sind, so muß dies als ein Glück bezeichnet werden. In Außersihl wurde eine solche von 4 Wehrmännern begleitete Briefträgergruppe durch einen Volkshausen an gegriffen und tatlich bedroht. Aber trotz diesen Gefahren ließen sich unsere Studenten nicht abhalten. Mit Feuereifer und mit Geschick ordneten sie ihre Briefschaften und dann ging's in raschem Arbeitstempo von einer Haus türe, von einer Wohnung zur andern, von der bürgerlichen Bevölkerung überall freudig begrüßt. Um die Schimpfworte, die ihnen von Streikern zugerufen wurden, kümmerten sie sich nicht. Sie wußten, was auf dem Spiele war: dee Wohlfahrt und Unabhängigkeit unseres Landes, die Unter drückung der ruhigen arbeitswilligen Bevölke rung durch eine terroristische Minderheit. Dieses frische Zugreifen, dieser Wagemut, dieses Erfassen des Ernstes der Sachlage von seiten der akademi schen Jugend, das gibt uns auch Hoffnung, getrost in die Zukunft zu schauen. Unser Volk wird nicht vom rechten Pfade abkommen, wenn seine besten Söhne sich vom wahren Patriotisnus leiten las sen. Und Zürichs akademische Jugend krönte ihre Tätigkeit durch Verzicht auf die Entschädigungen, die ihr für den Hilfsdienst angeboten wurden. Sie überwies den ganzen Betrag, annähernd 2000 Fr., der Sammlung zugunsten des im Dienst von Demonstranten erschossenen Luzerner Soldaten Vogel! Basel. Bei der Wiederherstellung von Ord nung und Ruhe wuden in Basel das Militär und die Polizei durch die Bürgerwehr wacker unterstützt. Dieser Organisation sind bereits etwa 6000 Bürger aller Stände beigetreten. Weniger vorbildlich war die Haltung des Regie rungsrates zum Streik. Erst als der eigent liche Landesstreik verkündet wurde und größere Unruhen in Aussicht standen, entschloß er sich end lich, um militärische Hilse nachzusuchen. Am Diens tag ging die Regierung dann sogar soweit, mit dem Streikkomitee zu paktieren. Sie sicherte diesem zu, daß sie beim Bundesrat die Zurückziehung der Truppen verlangen werde, wenn das Streikkomitee für Aufrechterhaltung der Ruhe schriftliche Garan tie leiste. Glücklicherweise kam es nicht dazu. Als am Donnerstag morgen die Meldung einlief, daß das Oltener Aktionskomitee bedingungslos kapitu liert habe, unterließ sie es, das erwähnte Ver langen an den Bundesrat zu richten. Wenn auch der Regierungsrat mit seinem Verhalten die an sich gewiß lobenswerte Absicht verfolgte, einen friedlichen Ausgang des Streiks zu sichern, so mußte es doch als Schwäche ausgelegt werden. In der Sitzung des Großen Rates vom 14. November wurde denn auch an der Haltung des Regierungsrates scharfe Kritik geübt und ihm vor geworfen, daß er seine Pflicht, für Aufrechterhal tung von Ruhe und Ordnung zu sorgen, nicht, wie es sich gehört hätte, erfüllt habe und sogar im Be griff gewesen sei, seine Gewalt an die Streik leitung abzugeben. Während Regierungspräsident Dr. A. Im Hof (lib.) und die Regierungsräte Dr. Aemmer (freis.) und Dr. Miescher (lib.) für energisches Auftreten waren, nahmen die Regie rungsräte A. Stöcklin (freis.), Dr. Mangold (wild), E. Wullschleger (soz.) und Dr. Hauser (soz.) einen gegenteiligen Standpunkt ein. Die rückhaltlose Mißbilligung, welche die Haltung der Mehrheit der Regierung bei der Bevölkerung sand, hat nun bereits zu einem Rücktritt geführt, indem Re gierungsrat A. Stöcklin dem Großen Rat sein Entlassungsgesuch eingereicht hat. Mit aller Strenge ging man im Großen Rate mit den Anstiftern und Führern des Streiks ins Gericht. Die Redner aller bürgerlichen Fraktionen traten da geschlossen auf. Schonungslos legte man die wirklichen Ziele der Streikanstifter bloß. Der Anschlag mißlang dank der festen Haltung von Bundesrat und Bundes versammlung. Alle Redner sprachen diesen Be hörden Zustimmung und Dank aus. So scharf das verwersliche Gewaltmittel des Landesstreiks ver urteilt wurde, ebenso einmütig sprachen sich die bürgerlichen Redner für die Durchführung billiger Reformen aus. Baden, 20. Nov. pt Der Gemeinderat von Baden, an dessen Spitze <PERSON>Nationalrat Jäger</PERSON> steht, veröffentlicht über seine letzte Sitzung folgende Bekanntmachung: Da während des jüngsten revo lutionären Landesstreikes leider auch städtische Ar beiter durch Treubruch gegenüber der Gemeinde öffentliche Interessen gefährdet haben, wird unter Berufung auf Artikel 352 O.-R. sämtlichen Ar beitern der Stadt und der städtischen Werke er öffnet, daß künftig jede Dienstverweigerung sofor tige Entlassung zur Folge hat. Der Gemeinde wird beantragt, dem „Freien Aargauer", der in schamloser Weise revolutionäre Propaganda be treibt, seien die amtlichen Veröffentlichungen der Gemeinde bis auf weiteres zu entziehen. Bei zu ständiger Seite wird das Begehren gestellt, die Be zeichnung „Publikationsorgan der Gemeinde Ba den" im Untertitel des „Freien Aargauer" (Sozial demokratisches Tagblatt des Kantons Aargau) zu verbieten. Neuenburg. Die Bilanz der eben durchleb ten Generalstreiktage ist nicht schwer zu ziehen; sie schließt mit einer tatsachlichen Niederlage der Or ganisatoren dieser Bewegung ab. In den Bezirken Reuenburg, Boudry, <LOCATION>Val-de-Travers</LOCATION> und Val-de Ruz, wo Tausende von Arbeitern in den verschie densten Industriezweigen beschäftigt sind, wurde nicht gestreikt. Für Locle und La Chaux-de-Fonds wäre dasselbe eingetreten, wenn nicht die elektrische Stromleitung unterbrochon worden wäre, welche die sozialistischen Verwaltungen dieser beiden Orte, absichtlich oder nicht, nicht wiederherzustellen vermochten. Was diejenigen, die dem Oltener Komitee ge horchen, am meisten überraschte, war der hart näckige Widerstand der Streilgegner. Ueberall wurden sofort Bürgerwehren gebildet, und die Großzahl der Neuenburger Jugend hat sich gleich auf die Seite der Ordnungs- und Freiheitsfreunde gestellt. Der Staatsrat erließ eine Proklamation, worin er die Bevölkerung einlud, mit allen gesetz lichen Mitteln gegen die soziale Desorganisation, die der Generalstreik bedeutet, aufzutreten. Dieser Appell tat seine Wirkung. Die Regierung genoß die dauernde und wirksame Unterstützung des Neuenburger Volkes, das seine Nuhe und Kalt blütigkeit bewahrte. Schon vom Dienstagabend, dem 12. November an, war bei den Streikenden eine Müdigkeit zu beobachten, als Vorläuferin der Kapitulation, die am Donnerstag im ganzen Kan ton geseiert wurde. Unsere Sozialdemokraten haben die bittere Er fahrung machen müssen, daß bei uns brutale Mit tel keinen Erfolg haben. Bei der drohenden Ge fahr haben sich die Streikgegner zusammengeschlos sen. Etwas von diesen sozialen Verteidigungs organisationen, die eben gebildet wurden, wird bleiben, und es ist nicht zu zweifeln, daß ein neuer Streik- oder Umsturzversuch noch weniger Erfolg haben würde als der, der soeben jämmerlich ge scheitert ist. Die Festbefoldeten, von denen man behauptete, daß sie zur extremen Linken überge gangen seien, haben, außer wenigen Ausnahmen, die Arbeitsniederlegung verweigert. Mit ihren Verbandsfahnen haben sie an der vaterländischen Kundgebung vom Donnerstagabend in der Haupt stadt teilgenommen. Gegen die sozialistischen Behörden von Locle und La Chaux-de-Fonds, die für die Lichtunter brechung, sogar in den Spitälern, verantwortlich sind, richtet sich ein allgemeiner Sturm der Ent rüstung. Sie würden entfernt, wenn gegenwärtig Wahlen stattfänden. Hingegen werden die kanto nalen Behörden wegen ihrer ruhigen Energie, die die Ruhe und Ordnung ohne militärisches Ein schreiten aufrechtzuerhalten vermochten, einstimmig gelobt. Das Erwachen des Patriotismus bei der stu dierenden Jugend wurde besonders bemerkt. Ohne Zweifel werden von jetzt an die Theorien der außersten Linken in diesen Kreisen, in welchen in den letzten Jahren ein Schwenken nach links zu beobachten war, zum Mißerfolg verurteilt sein. Den streikenden Eisenbahnern verzeiht man ihre Pflichtverletzung nicht, um so weniger, als sie schöne Löhne und große Teuerungszulagen bezie hen. Man verlangt, daß sie exemplarisch gestraft werden, damit sie die Größe ihres Fehlers ein sehen, der die ohnehin schon schwierige Lebens mittelversorgung des Landes außerst gefährdete. Mit einem Wort, der Erfolg der Bürger und der Behörden, die den Ceneralstreik bekämpft ha ben, ist ein vollständiger. Wie zur Zeit der Fünf zigjahrfeier der Republik im Jahre 1898 tat das Neuenburger Volk seine Pflicht, und mit berech tigtem Stolz sieht es heute, daß seine schweizerische Vaterlandsliebe noch in voller Kraft besteht. Der Benjamin der Eidgenossenschaft ist besser als sein Ruf. Er hat es in diesen schweren Tagen der Prü fung bewiesen. Unsere Eidgenossen mögen daran denken, wenn wir in Bern auf mehr Demokratie und mehr Achtung vor den Rechten des Volkes dringen werden. Liebesgaben für das Militär. pt Für die in Rapperswil stationierte Landsturmkompagnie I771 wurde von bürgerlicher Seite eine Sammlung veranstaltet, welche 4324 Fr. ergab. Von diesem Betrag erhielt jeder der 180 Landsturmsoldaten einen Chrensold von 20 Fr. Der verbleibende Rest wird dem gegenwärtig noch 26 Grippekranke, wovon 9 Soldaten, beherbergenden Notspital Rap perswil zugewendet. Die Bündner Gebirasbatailone 92 und 93 er freuen sich im Thurgau herzlicher Aufnahme aich die Bevölkerung, welche die Mannschaften durch Schenkungen von Obst (über 15,000 Kg.), Tee, Zigarren usw. in reichlichem Maße erfreut. Leider haust unter diesen Truppen arg die Grippe, glücklicherweise sind die Fälle aber fast ausschließ lich leichterer Natur. Die bündnerische Regierung hat be schlossen, aus Dank und Anerkennung für die treue Pflierteriüllung jedem aufgebotenen Bündner für die Streitwoche eine besondere Soldzulage von 2 Fr. pro Tag aus der Kantonsbasse zu verab folgen."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Josef Jäger
    Description: Schweizer Politiker, Lehrer und Journalist
    Born: ['+1852-12-01T00:00:00Z']
    Died: ['+1927-07-19T00:00:00Z']
    Birth place: ['Bad Säckingen']
    Death place: ['Q63939']
    Work locations: ['Bern']
  Location Wikidata:
    Label: Bezirk Val-de-Travers
    Description: Ehemaliger Bezirk im Kanton Neuenburg, Schweiz
    Country: ['Q39']
    Located in: ['Q12738']
    Aliases: {'en': ['District du Val-de-Travers'], 'lb': ['Bezierk Val-de-Travers']}
    Coordinates: [{'lat': 46.9125, 'lon': 6.6125}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (4):
      - "2000" → 2000
      - "6000" → 6000
      - "1898" → 1898
      - "4324" → 4324
    Temporal signal words: jetzt, heute, nach, vor
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 20 days
    OCR quality estimate: 0.987

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Nationalrat Jäger' and 'Val-de-Travers' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Nationalrat Jäger' near 'Val-de-Travers' around 1918-11-22?
  4. Resolve temporal expressions relative to 1918-11-22. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 42 [ID: test_de__133]:
  Publication date : 1911-07-01
  Language         : de
  Person  : 'Jos. Schwarz'  (QID: N/A)
  Location: 'Graz'  (QID: Q13298)

  [ARTICLE TEXT — entity markers added]
  "Redaktion, Administration u. Druckerei:Kolowratring, Fichtegasse Nr. 11.Unfrankierte Briefe werden nicht angenommen undManuskripte in keinem Falle zurückgesendet.Ankündigungs-Bureau:Stadt, Wollzeile 20. Insertionspreis nach Tarif. Inserateübernehmen: Witzek, Ann.-Exp, in Prag undBrünn; Jos. A. Kienreich, Inseraten-Exp. in <LOCATION>Graz</LOCATION>;J. Blockner, J. Leopold, <PERSON>Jos. Schwarz</PERSON>, Ann.-Exp,in Budapest; im Auslande: John F. Jones & Co.in Paris, 31 bis, Rue du Faubourg Montmartre;Rudolf Mosse in Berlin, München, Leipzig;Haasenstein & Vogler in Hamburg, Berlin,Frankfurt a. M. u. Basel; Heinrich Eisler,Ann.-Exp. in Hamburg; Orell Füssli & Co. inZürich u. Basel; Neyroud & Sons in London;Vertreter für Deutschland, Frankreich, England,Köln a. Rh.Italien etc.: Saarbachs News Exchange, Mainz u.Abonnement für Wien:Mit tägl. zweimal, Zustell, ins Haus: Ganzj. K. 50.40,monatl. K. 4.20.Zum Abholen im Hauptverlage Wollzeile 20 oderFichtegasse 11: Ganzj. K. 43.20, monatl. K. 3.60.Einzeln: Morgenblatt 12 H., Abendblatt 6 H., Nach¬ mittagblatt am Montag und nach zwei Feiertagen 12 H.Morgen u. Abendblatt 40 Pf.Für DeutschlandMorgen- und Nachmittagblatteinzeln:allein je 30 Pf.Abendblatt allein je 15 Pf.NeueFreie Presse.Morgenblatt.Abonnement für das Inland:Mit tägl. einmal Postversendung: Ganzj. K. 56, haltelK. 28, viertelj. K. 14. Mit tägl. zweimal. Postversend.:Ganzj. K. 01, halbj. K. 32, viertelj. K. 16.Abonnement für das Ausland:Vierteljährig:Bei uns (Krenzband-Versend.): Deutschland,Serbien K. 20, f. Staaten d. WeltpostvereinesK 22. Bei den Postämtern in DeutschlandM. 11.18, Schweiz Fr. 14.05, Belgien Fr. 15.96,Italien L. 14.47, Rumänien Fr. 15.95, SerbienGriechenland (b.d. Buchh. Beck & Harth u.C. Elef¬ Fr. 13.80, Bulgarien Fr. 15.65, Russland R. 5.30,theroudakis, Athen od. k. k. Zeitgs.-Exp. in Triest) u.Europ. Türkei K. 15.05, Asiat. Türkei K. 17.45,Aegypten Fr. 18.32, Dänemark skand. K. 11.26,Norwegen skand. K. 10.83, Holland F. 9.—.Bei den Agenturen in Italien: Saarbachs NewsExch., Mailand, 2. Gust. Modena, Loescher & Co., RomFr. 23.50; Frankreich: Saarbachs News Exch.,Paris. 148, Faubourg St. Denis, Agence Havas, ParisFr. 28.50; England: Saarbachs News Exch., London,16, John Street, Adelphi Strand W. C., A. Siegle,20, Lime-Street E.C., London, sh. 19; Nordamerika:F. Steiger, 25 Park-PIace, G. E. Stechert, 151—155 West25th St., L. A. Rosswaag, 57. Second-Avenue inNewyork, Doll. 6.40. Vertreter für das gesamte Aus¬ land: Saarbachs News Exchange, G. m. b. H., Mainz.Für die an Agenten, Austräger oder Verschleissenbezahlten Beträge leisten wir keine Garantie.Nr. 16830.Wien, Samstag, den 1. Juli1911.Wien, 30. Juni.Die glorreiche Erinnerung an die Wiener Stich¬ wahlen wird in den heutigen Beschlüssen des DeutschenNationalverbandes mit keinem Worte berührt. Nureisiges Schweigen für die großartige Kundgebung einerdeutschen Stadt mit zwei Millionen Einwohnern; keinZeichen der Herzlichkeit und kein freundlicher Gruß füreine Bewegung, aus der auch für die nationale Politikganz neue Werte gekommen sind. Kann dieses Neben¬ einandergehen der Deutschen in Wien und in den Kron¬ ländern nützlich sein; muß der Deutsche Nationalverbandes nicht als wichtiges Ziel erkennen, die starken, werbendenKräfte der uralten Kaiserstadt, wo jeder Stein von derdeutschen Geschichte erzählt, für seine Politik zu ge¬ winnen; würde nicht der Augenblick, da die politischeZukunft wieder unsicher geworden ist, besonders dazudrängen, die Beziehungen zwischen Wien und demNationalverbande natürlicher und wärmer zu gestalten?Die älteren Parlamentarier, die der Sturmwind des all¬ gemeinen Stimmrechts nicht weggeschleudert hat, mögensich noch erinnern, daß in den Anfängen des GrafenTaaffe eine Versammlung in den Sophiensaal einberufenwurde. Dort hat Franz Schmeykal, der Führer derDeutschen in Böhmen, der deutschen Stadt Wien beideHände entgegengestreckt. Wer die Wirkung erlebt und ge¬ sehen hat, wird sie niemals vergessen. Auf der Tribünestand Franz Schmeykal, damals in Wien persönlich nochwenig bekannt. Er begann zu sprechen, und schon nachwenigen Minuten waren alle Blicke voll Spannung aufden feinen Kopf mit den leuchtenden Augen geheftet, undjeder Satz, jede Geste wurde von den Hörern unter¬ strichen. Wien, das sich die Politik so gerne in einerPerson versinnlicht, schloß ein Bündnis mit Böhmen undmit allen Deutschen in Oesterreich. Wäre dieses Beispiel,das Franz Schmeykal gegeben hat, nicht auch jetzt nach¬ ahmenswert, und sollten nicht die verantwortlichen Trägerder deutschen Politik in Oesterreich eine Brücke schlagenzwischen Wien und der parlamentarischen Vertretung desdeutschen Volkes? Die heimlichen Ursachen des letztenMinisterwechsels werden bald zu spüren sein. Das halb¬ amtliche Communiqué über die neue Orientierung derPolitik sagt dem Erfahrenen genug und vermehrt dasBedürfnis, die Bürgschaften und die Wälle, die dasSchicksal der Deutschen in Oesterreich sichern können, zuverstärken. Deshalb darf Wien weder vernachlässigt nochzur Seite geschoben werden. Hier lebt ein Fünftel allerDeutschen in Oesterreich und ein noch viel größerer Teilaller freisinnigen Deutschen. Eine Politik, die sich umsolche Fundstellen des nationalen Gedankens nicht kümmernwollte oder dagegen gleichgiltig bliebe, wäre geradezuunzulässig.Wien hat zehn freisinnige Abgeordnete gewählt.Davon mögen zwei und vielleicht drei wegen ihrer scharfausgeprägten besonderen Richtung und wegen älterer Ver¬ stimmungen für den Deutschen Nationalverband nicht inDie heutige Nummer enthält:„Landwirtschaftliche Zeitung“:„Neues auf dem Gebiete der Zucker¬ fabrikation.“ Vom k. k. RegierungsratA. Stift. Seite 25 bis 27.„Militärisches Nachrichtenblatt“der „Neuen Freien Presse“: Aus demLandwehr=Verordnungsblatt. Miszellen.Seite 28.Ferner:Die 64. Fortsetzung des Romans „Frühlings¬ taumel“ von Gabriele Reuter. Seite 24.Feuilleton.Alfred v. Berger und seine „hamburgischeDramaturgie“.Von Otto Ernst.Louis Schneider, der Vorleser Kaiser Wilhelms I.,soll einmal nachgewiesen haben, daß die BerlinerZeitungen seit dem Jahre 1768 alljährlich mit großerEinmütigkeit versichert hütten, so weit wie gegenwärtigsei das Theater noch nie herunter gewesen. Es mag jawohl Dienstboten geben, die ihre Schuldigkeit nur danntun, wenn sie unaufhörlich gescholten werden (obschonich an die Zweckmäßigkeit dieser Pädagogik nicht rechtglaube), und in Deutschland scheint man das Theater fürsolch einen Dienstboten zu halten. Siebenmal in jederWoche hat das Theater, sowohl in Hinsicht des Reper¬ Betracht kommen. Dann bleiben immer noch sieben, vondenen jedoch nur zwei zu der für nächsten Freitag einbe¬ rusenen konstituierenden Versammlung des DeutschenNationalverbandes eingeladen wurden. Diese Beschrän¬ kung mag in der Form durchaus zu rechtfertigen sein,weil bisher nur zwei Abgeordnete erklärt haben, daß siedem Deutschen Nationalverbande sich anschließen wollen.Es braucht auch nichts in diesem Beschlusse gewittert zuwerden, was den Verdacht begründen könnte, als solltengerade solche Mitglieder des Parlaments vom National¬ verbande ferngehalten werden, von denen die Christlich¬ sozialen in den Wahlen niedergerungen wurden. Aberselbst die strengste Korrektheit wird die Frage nicht er¬ sticken, ob dem Deutschen Nationalverbande selbst nachseinem glänzenden Siege sieben Stimmen nicht von Wertsein können. Es hat im früheren Abgeordnetenhausemanche Kämpfe und Krisen gegeben, in denen der DeutscheNationalverband um jede einzelne Stimme zitterte unddie Grenzscheide zwischen Mehrheit und Minderheit auchvon sieben Abgeordneten gezogen werden konnte. DerDeutsche Nationalverband kann überhaupt kein Mandatentbehren, das von deutschen und freisinnigen Wählernherrührt. Gewiß werden diese sieben Abgeordneten vonWien niemals dem deutschen Volke in den Rückenfallen und auf den heißesten Schlachtfeldern als Frei¬ willige sich zur Verfügung stellen. Die Führer desDeutschen Nationalverbandes wissen, daß sie innerlichdarauf rechnen dürfen. Wäre es nicht kleinlich, diesensieben Abgeordneten alle Pflichten des Nationalgefühlsaufzuerlegen und ihnen die Rechte zu verweigern odermindestens nicht anzubieten ? Ein freisinniger Abgeordnetervon Wien kann nur deutsch sein, und der Nationalverbandsollte ihn daher durch einen Beschluß, der ihn zu einerBitte um Aufnahme zwingt und vielleicht sogar einerDemütigung aussetzt, nicht gewaltsam zum Freischärlermachen. Das hieße, auf die Hilfsquellen verzichten, dieWien für das deutsche Volk hat; das hieße, die Deutschenin Wiener und Nichtwiener spalten; das hieße, einenFehler begehen, durch den eine große Zukunft preisgegehenwerden könnte. Die politische Verschmelzung von Wienmit den Kronländern muß das Ziel des DeutschenNationalverbandes sein. Er kann diese zwei Millionenvom deutschen Besitzstande, den er sonst mit aller Wach¬ samkeit verteidigt, nicht wegstreichen. Er sollte Wien ge¬ mütlich erobern und nicht von sich stoßen.Der Beschluß des Deutschen Nationalverbandes, nurzwei Wiener Abgeordnete zur konstituierenden Versamm¬ lung für nächsten Freitag einzuladen, mag in der Formdurchaus zulässig gewesen sein. Es handelt sich jedochnicht um das strenge Recht, sondern um jenes politischeGefühl, das mehr ist als Klugheit, weil darin die Gabesteckt, die Wähler anzuziehen; auch weil sich darin tiefereEinsicht und schärfere Voraussicht zeigt. Eine milde Aus¬ legung hätte leicht finden können, daß diese sieben Abge¬ ordneten sich meistens als deutsch und fortschrittlich be¬ zeichnet haben und somit im politischen Zusammenhangetoires wie der Darstellung, einen Tiefstand erreicht, dernicht mehr zu unterbieten ist. Es kann übrigens sein,daß diese Erscheinung nicht nur in der Beurteilung desTheaters auftritt. Ich habe die Beobachtung gemacht,daß die Leute über einem Regentage sieben TageSonnenschein vergessen und daß sie, wenn es gar dreiTage nacheinander regnet, auch nach einem guten Sommerversichern, ein so elender Sommer wie dieser sei nochnicht dagewesen. Es gehört viel Courage dazu, solchenSchimpfmoden zu widersprechen; aber in diesem Punktebin ich dreist. Wir haben eine Operettenpest und habenLaboratorien für ihre Verbreitung, das ist mir bewußt;wir haben auch sonst eine dramatische Schundliteraturund Theater genug, die ihr dienen; aber alles in allemhaben wir auch eine große Anzahl ernsthafterTheater, die ein vortreffliches Repertoire vortrefflichspielen, und im Durchschnitt steht das Theater heutemindestens so hoch, wahrscheinlich aber erheblich höher,als es oft gestanden hat. Ich hege den Verdacht, daß ichzu dieser günstigen Meinung gekommen bin, weil icheiniges vom Theater verstehe, und will gleich erklären,was mich in diesem Verdachte bestärkt hat.Vor kurzem sagte mir ein namhafter, auch von mirsonst aufrichtig hochgeschätzter Schriftsteller: „Seitdem ichdas Theater aus eigener Beobachtung kenne, kann ichnicht mehr darüber schreiben; ich habe meine bestenSachen über Theater geschrieben, als ich nicht die Spurdavon verstand.“ (Ich weiß, lieber Leser: Oskar Wildepflegte dergleichen Sätze als sehr begreiflich und wohl be¬ gründet zu vertreten, ich weiß, ich weiß."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Graz
    Description: Landeshauptstadt der Steiermark, Österreich
    Country: ['Österreich', 'besetztes Nachkriegsösterreich', 'Q7318', 'Q176495', 'Erste Republik', 'Deutschösterreich', 'Q28513', 'Q131964', 'Habsburgermonarchie']
    Located in: ['Steiermark', 'Q580447']
    Aliases: {'en': ['Gratz', 'Grätz', 'Bayrisch-Grätz', 'Bairisch-Grätz', 'Gradec', 'Graecia', 'Grez'], 'fr': ['Gratz', 'Gradec']}
    Coordinates: [{'lat': 47.07083333333333, 'lon': 15.438611111111111}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1768" → 1768
    Temporal signal words: jetzt, heute, früher, nicht mehr, nach, vor, früh
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 143 days
    OCR quality estimate: 0.948

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Jos. Schwarz' and 'Graz' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Jos. Schwarz' near 'Graz' around 1911-07-01?
  4. Resolve temporal expressions relative to 1911-07-01. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 43 [ID: test_de__198]:
  Publication date : 1808-04-29
  Language         : de
  Person  : 'Lord Gower'  (QID: Q334145)
  Location: 'Frankreich'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "henden und glücklichen Zustande gelebt habe, und daß kein Beweggrund ihn jemals dahin bringen könne, von diesem Vorsatze abzustehen. Se. Kaiserl. Majestät fügten hinzu, daß ich den festen Karakter des Kronprinzen hinlänglich ken nen müße, um zu wissen, daß nichts schwerer sey, als seine Entschlüsse zu erschüttern, oder ihn zu bewegen, ein ein mal angenommenes System zu verlassen, und daß er, der Kaiser, überzeugt sey, es habe vor unserm Angriff auf Ro (Aus dem danischen Blatte Dagen.) Da das engli sche Ministerium die englische Nation versichert hat, daß den Kaiser von Rußland Anfangs nicht das geringste Miß vergnügen über den Raubzug nach Seeland geäussert habe, so wird man nicht ohne Interesse nachstehende Erläuterun gen über eine, zwischen dem Kaiser von Rußland und dem General Hutchinson vorgefallene, Unterredung lesen. Se. Kaiserl. Majestät — so berichtet der General Hutchinson — flengen die Unterredung mit der Frage an, was ich von unserm Angriff auf Kopenhagen denke? Ich erwiederte, daß mir die Umstände, welche solchen veranlaßt hätten, zwar ganz unbekannt wären, daß ich aber hoffe, die englische Administration werde sich rechtfertigen, und der ganzen Welt beweisen können, daß die Dänen im Begriff waren, ihre ganze Macht mit der französischen gegen England zu vereinigen. Se. Kaiserl. Majestät bemerkten, daß ich un möglich dieser Meynung seyn könne, wenn ich noch der Un terredungen gedächte, die wir in Bartenstein gehabt hät ten. In diesen sagte der Kaiser mir, er habe alle mögliche Mühe angewandt, um den Kronprinzen von Dänemark zu! vermögen, der Koalition gegen <LOCATION>Frankreich</LOCATION> beyzutreten; daß aber die Antwort des Prinzen immer deutlich und un verändert dieselbe gewesen sey, daß er viele Jahre lang ein Neutralitätssystem behauptet habe, bey dem er zu beharren fest entschlossen sey; da sein Volk dadurch in einem blü und dänischen Regierung statt gefunden. Ich sagte dar auf, ich glaubte, daß der <PERSON>Lord Gower</PERSON> dem Kaiserl Mi nisterium über diesen Gegenstand eine Note übergeben habe, worauf Se. Majestät erwiederten, daß dies sich so verhalte, daß aber der Inhalt der Note lächerlich sey, da solche we der hinlängliche Auskunft enthalte, noch irgend eine Genug thuung anbiete. Se. Kaiserl. Majestät sprachen darnächst von der großen Betrübniß, die Ihnen durch unsern unver antwortlichen Angriff verursacht worden, und daß nie et was Aehnliches geschehen sey; daß, wenn ein solches Ver fahren gelten sollte, alle Verhältnisse, die das Verfahren der Nationen gegen einander bisher bestimmt hätten, zu Grunde gehen würden, und daß in dem Falle ein jeder thun könnte, was ihm beliebe. Se. Kaiserl. Majestät sagten mir in den bestimmtesten Ausdrücken, mit dem festesten Tone, daß er Genugthuung für diesen, ohne alle Veranlassung un ternommenen, Angriff fordere; daß dies seine Pflicht, als Kaiser von Rußland, sey, und daß er Genugthuung wolle. Er fragte mich, ob ich wagen dürfe, über diesen Gegenstand anderer Meynung, als er, zu seyn? Er sagte ferner; daß die feyerlichsten Traktate und Verpflichtungen ihn mit Dä nemark verbänden, und daß er entschlossen sey, solche zu erfüllen. Se Kaiserl. Majestät fügten hinzu, er vermuthe, wir dächten auf einen Angriff auf Kronstadt; daß er zwar den Ausgang eines solchen Angriffs nicht vorhersehen könne, daß er aber bis zum letzten Mann Widerstand leisten, und sich des hohen Postens, worauf ihn die Vorsehung gestellt habe, nicht unwürdig bezeigen wolle. — Ich antwortete, ich hätte alle Ursache zu heffen und zu glauben, daß wir auf Kronstadt keinen Angriff thun würden. Er entgegnete, daß er darauf gefaßt, und sein Entschluß unerschütterlich sey. Darauf endigte er das Gespräch, und wiederholte mit vielem Nachdruck: „Daß er Genugthuung für Dänemark wolle Der Freymüthige vom 7. April enthält Folgendes: Hamburger-Korrespondenten wird, von Petersburg aus, angedeutet, und in der neuesten Berlinischen Zeitung aus gesprochen, daß H. von Rotzebue in Ehstland gestorben sey. Man hat viele Gründe, die Authentizität dieser Nach richt zu bezweifeln; merkwürdig ist übrigens die Eilfertig keit, mit der man dem Publikum unverbürgte Notizen mit theilt, die für dasselbe tief erschütternd seyn müßen!" Das *Am 22. Merz sah man auf der großen Parade zu Peters burg 4. eroberte schwedische Fahnen und eine Flagge die General Burhöyden eingeschickt hatte."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.995

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Lord Gower' and 'Frankreich' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Lord Gower' near 'Frankreich' around 1808-04-29?
  4. Resolve temporal expressions relative to 1808-04-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 44 [ID: test_de__220]:
  Publication date : 1818-08-18
  Language         : de
  Person  : 'Sekretair, H. Lasitte'  (QID: N/A)
  Location: 'Paris'  (QID: Q90)

  [ARTICLE TEXT — entity markers added]
  "In Briefen aus <LOCATION>Paris</LOCATION> vom 3. Aug. heißt es: „Eine Ordonnanz hat also die Absetzung des H. von Vitrolles, als Staatsministers, ausgesprochen. So hat nun dieser Mann, der, aus niedern Volksklassen stammend (er ist der Enkel eines Gastwirths in den Alpen), Sekretair des Ra thes der Minister, Staatsminister und Mitglied des ge heimen Rathes des Königs ward, und 80,000. Fr. Besol dungen zusammenhäufte, nach und nach alle seine Aemter und Einkünfte verloren; und alle diese Opfer hat er dem Vergnügen zu intriguiren gebracht! Man gibt ihn als den Verfasser der Adresse an, welche Franzosen an die frem den Souveraine gerichtet, um sie zu bewegen, sich in unsre häuslichen Angelegenheiten zu mischen. In dieser Adresse ward ganz ernsthaft die Frage erörtert, ob das gegenwär tige Ministerium Frankreich retten könne? Sie entschied, daß es dessen nicht fähig sey, und ersuchte die Mächte, sich ins Mittel zu legen, um dem Könige von Frankreich an dere Minister zu geben, die mehr nach dem Geschmacke des H. v. Vitrolles wären. — Sein <PERSON>Sekretair, H. Lasitte</PERSON>, ist in Verhaft; man hofft, daß seine Erklärungen, und das Verhör, welches H. v. Vitrolles unstreitig selbst zu be stehn haben wird, endlich die Urheber jener Adresse aus Tagslicht ziehn, und uns belehren werden, auf welche Klasse von Franzosen sich der öffentliche Unwille werfen muß. Die Dienstentsetzung des H. v. Vitrolles hat auf die Gemüther der Freunde des Königs und ihres Landes die beßte Wir kung hervorgebracht. Mit Vergnügen gewahrt man, wie die Regierung eine Kraft entwickelt, welche zur Erhaltung chen Ruhe nothwendig ist. Eine neue Handlung der Streuge bezeichnet neuerdings die Linie, die sie sich vorgezeichnet hat. Sie entsetzte H. Agier, Substituten des Königlichen Anwalds beym Pariser-Gerichtshofe, seiner Stelle; seit langer Zeit hat er sich unter die Feinde des Throns gereiht, und man hatte ihn im Verdacht, einer der Rathgeber der elenden Urheber der letzten Verschwörung zu seyn. Dieser junge Mann, von einer ausschweifenden Eigenliebe geblen det, glaubte sich zu großen Dingen bestimmt; da es ihn verdroß, vom Ministerium in einer untergeordneten Stelle gelassen zu werden, so bildete er sich ein, ein Mittel sich emporzuschwingen wäre, wenn er gegen seinen Fürsten Par tey ergriffe. Man kann aus diesem Schritte auf seinen Takt und seine Urtheilskraft schließen. — Die Frau Herzo gin Braunschweig-Bevern ist zu Paris angekommen, um der Vermählung ihrer Nichte, der Fräulein von St. Aulaire, mit dem Polizeyminister beyzuwohnen. Der Aer ger der Ultraroyalisten scheint in gleichem Grade mit dem Glücke des H. Decazes zuzunehmen. Sie sind wüthend über den Glanz, den diese Verbindung über ihn verbreitet; sie sind wüthend über die neuen Beweise von Vertrauen und Achtung, womit der König ihn beehrt; und sie werden rasend über die Entdeckung der Verschwörung, welche das Ansehn und den Ruhm eines Ministers vermehrt, der sich über das Unglück, sie zu Feinden zu haben, damit tröstet, daß er jeden Tag neue Dienste seinem Könige leistet.""

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Paris
    Description: Hauptstadt und bevölkerungsreichste Stadt Frankreichs
    Country: ['Frankreich', 'Königreich Frankreich', 'Fränkisches Reich', 'Deutsche Besetzung Frankreichs 1940–1945', 'Frankreich', 'Erstes Kaiserreich', 'Erste Französische Republik']
    Located in: ['Métropole du Grand Paris', 'Q13917', 'Q70972', 'Q2863958', 'Département Seine', 'Q124881945']
    Aliases: {'en': ['City of Light', 'City of Love', 'Lutetia'], 'fr': ['Ville-Lumière', 'Paname', 'Lutèce', "Ville de l'Amour", 'FR-75', 'Pantruche', 'Ville de Paris']}
    Coordinates: [{'lat': 48.85666666666667, 'lon': 2.352222222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: nach, vor
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.994

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Sekretair, H. Lasitte' and 'Paris' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Sekretair, H. Lasitte' near 'Paris' around 1818-08-18?
  4. Resolve temporal expressions relative to 1818-08-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 45 [ID: test_de__226]:
  Publication date : 1838-06-04
  Language         : de
  Person  : 'Gott'  (QID: Q190)
  Location: 'Darmstadt'  (QID: Q2973)

  [ARTICLE TEXT — entity markers added]
  "Auneaae. Frankreich. Die beiden vorgeschlagenen Eisenbahnen, nach Orleans und nach dem Havre, sollen in den Bureaux der Kammer wenig Ein wendungen erfahren. Nur über das Privilegium gegen Konkurrenz sei man ungleicher Ansicht. Man liest im Journal du Hayre: „Wir erfahren, daß ein Schwei zerhaus seinen Korrespondenten im Havre den Auftrag gegeben hat, mehrere Waarenballen aus unserm Hafen nach England zu senden, damit sie dort, sei es in Bristol oder in London, mit dem ersten Dampfschiff abgehen könnten, das die Reise nach New-York antreten wird. Da die Aufmerksamkeit des Auslandes jetzt auf die neue Verbindung gerichtet ist, die sich England mit Amerika eröffnet hat, ist da nicht zu fürchten, die Schweiz und das nördliche Deutschland werden die Waaren, die sie bisher durch den Havre nach New-York sandten, nun den Weg über London oder Liverpool nehmen lassen? " — Unter dem etwas bizarren Namen einer Gesundheitsassekuranzkom pagnie hat sich in Bordeäux eine Gesellschaft gebildet, welche Beifall und Nachahmung verdient, und überall finden wird, wo man die Ver besserung der Lage der ärmern Volksklassen für eine Aufgabe hält. Der der Gesellschaft ist: gegen einen wöchentlichen Beitrag von 40 Cen times von jedem ihrer Mitglieder alle Kosten zu bestreiten, welche durch die Krankheiten derselben veranlaßt werden könnten, ihnen während der Dauer der Krankheit eine tägliche Geldhülfe von einem Franc zu ver abreichen, im Falle ihres Ablebens für eine anständige Beerdigung zu sorgen, und endlich diejenigen, welche durch Altersschwäche oder Unglücks fälle unfähig gemacht werden zu arbeiten, durch eine jährliche Pension von 100, 200 oder 300 Fr., je nachdem sie der Gesellschafft 10, 20 oder 30 Jahre angehört haben, gegen Elend zu sichern. Der zu einer Pension von 300 Fr. Berechtigte kann statt derselben eine Stelle in dem Hospize wählen, welche die Gesellschaft zu diesem Zwecke errichten w (2. A. 3.) (Temps). Man versichert, der Herzog von Angouleme sei sehr krank; die Getreuen der Partei sind sehr betrübt darüber; wir sprechen hier von den Vernünftigern, denn nach ihrer Ansicht übt der Herzog die Rolle der Mäßigung, und weiß Thorheiten Einhalt zu thun, oder sie zu verzögern; und sie besorgen, daß wenn dieser Zaum einmal verschwun den wäre, der junge Herzog von Bordeaux sich schädlichen Rathschlägen und der Hitze seines Charakters überlassen möchte. Hannover. Eine heftige Debatte in der zweiten Kammer soll eine Protestation des Bauernstandes des Fürstenthums Osnabrück verursacht haben, die nun in häufigen Abschriften circulirt. Die Wahlmänner aus dem Bauernstand erklären darin, daß nur das Beispiel der andern Kor porationen sie bewege, eine Wahl vorzunehmen, wodurch sie aber die Gültigkeit der Aufhebung des Staatsgrundgesetzes keineswegs anerkennen. — Die zweite Kammer ist in diesem Augenblicke mehr als 20 Mit glieder stärker als vor den Ferien, und in der Woche zwischen Himmel fahrt und Pfingsten, werden noch viele neue Abgeordnete erwartet. Die hannoversche Zeitung widerspricht der Nachricht, daß die Kom mission des deutschen Bundestages, welcher die Osnabrücker-Petition zu gewiesen ist, der Versammlung vorgeschlagen hälte, sich für kompetent zu erklären. Die Kommission habe noch gar keinen Bericht erstattet, versichert die hannoversche Zeitung. Hätte jene Nachricht nur die Ge sinnung der Kommission ausdrücken sollen, so könnte sie immerhin wahr sein. Rom, 24. Mai. Professor Gervinus ist aus Göttingen hier einge troffen. Er wird, wie man hört, sich einige Zeit hier aufhalten, um die Bibliotheken Roms zu seinen Studien zu benutzen. (A. Z.) Von der italienischen Grenze, 20. Mai. Die Kölner Angele genheit wird hoffentlich ruhig beendigt werden. So sehr der päpstliche Stuhl sich durch die Abführung des Erzbischofs gekränkt fühlte, und so bestimmt er auch dessen Wiedereinsetzung in das Kölner Bisthum ver langte, ehe er in Unterhandlungen mit der Regierung Preußens treten könne, so scheint er doch veranlaßt worden zu sein, nicht ferner dieses Verlangen geltend zu machen, sondern, so viel von ihm abhängt, auch ohne jene Bedingung die streitige Frage beseitigen zu helfen. Zu diesem Ende hat der h. Vater dem Generalvikar der Kölner Diöcese, Dr. Hüs gen, erlaubt, die Leitung des Erzbisthums in Abwesenheit des Erzbi schofs als dessen Vertreter beizubehalten und zu handhaben. A. Z.) Belgien. Der Bürgermeister von Tilff, Hr. Neef, ist von den Li beralen in Lüttich zum Deputirten gewählt worden; sein Gegner, Herr de Longrée, welcher von der Priesterpartei unterstützt wurde, und ein naher Verwandter des Ministers, Hrn. de Theux, ist, fiel durch. Die Wahl ward hartnäckig bestritten, denn Hr. Neef hatte 445 und Hr. de Longrée 413 Stimmen. Türkei. Die Einrichtung von Quarantänen mußte den rechtgläubi gen Türken befremden, der nie an Ansteckung glauben wollte, weil man nur erkranke, wenn <PERSON>Gott</PERSON> es wolle. Die türkische Staatszeitung über nimmt es darum, die neue Einrichtung auch aus dem Geiste des Propheten zu rechtfertigen, und man darf wol annehmen, daß ihr Artikel nicht ohne einen Ueberrest von Gewissensangst geschrieben ist. Hier einige der merkwürdigsten Stellen. „Es ist Jedermann be kannt, und die theologischen und Gesetzbücher lehren es, daß Gott die Macht hat, alle Dinge in der Welt ohne alle Ursache zu schaffen und zu vernichten. Allein wir finden im Koran und in den mündlichen Ueberlieferungen des Propheten, daß das allerhöchste Wesen in seiner Weisheit und Milde, gewisse Dinge andern zur Ursache gegeben, und daß es durch die Ursachen schafft und zerstört. Demzufolge ist es nöthig, daß man, um den Hunger zu stillen, esse, um den Durst zu löschen, trinke, um die Krankheit zu vertreiben, Arznei nehme, und überhaupt in Allem auf die Ursachen und Mittel zurückgehe. Manche Theologen dringen auf unumschränktes Vertrauen auf Gott; allein man kann die nöthigen Maßregeln ergreifen und dann, nach wie vor, auf Gott ver trauen. Zudem ist die Fähigkeit, diese Maßregeln zu ergreifen, wie auch die Wirksamkeit dieser letztern, nur durch die Gnade und die Er laubniß des Allerhöchsten vorhanden, und sonach ist die Ergreifung solcher Maßregeln keineswegs mit dem Vertrauen auf Gott im Widerspruche. Mit Einem Worte, da die Heilmittel zur Erhaltung der Gesundheit und Vertreibung der Krankheit die Erhaltung des Lebens zur Folge haben, da diese die Zunahme der Bevölkerung, diese hinwieder den Wohlstand des Landes und letztere die Vermehrung der Hülfsquellen des Staates nach sich zieht, so ist es aus diesen und aus Gründen der Menschlichkeit nöthig, Maßregeln gegen die Pest zu ergreifen, zugleich aber an dem Glauben festzuhalten, daß diese Maßregeln nur durch Gottes Zulassen und Gnade wirksam sein können." Dresden, 26. Mai. Die Bevollmächtigten der Zollvereinsstaaten zu der hier Statt findenden Münzkonferenz sind eingetroffen. In <LOCATION>Darmstadt</LOCATION> starb der Schriftsteller Dr. Fr. Heldmann, einst als Lehrer in Aarau und Bern angestellt, und auch in der schweizerischen Journalistik als Redaktor der in Bern erschienenen Europäischen Zeitung bekannt. Ein Werk über die Freimaurerei ist 1819 von ihm in Aarau erschienen."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1819" → 1819
    Temporal signal words: jetzt, nach, vor
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 19 days
    OCR quality estimate: 0.984

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Gott' and 'Darmstadt' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Gott' near 'Darmstadt' around 1838-06-04?
  4. Resolve temporal expressions relative to 1838-06-04. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 46 [ID: test_de__28]:
  Publication date : 1858-02-07
  Language         : de
  Person  : 'frühere Rédacteur des Blattes, Louis Labarre'  (QID: Q4251818)
  Location: 'Belgien'  (QID: Q31)

  [ARTICLE TEXT — entity markers added]
  "<LOCATION>Belgien</LOCATION>. Brüssel 31. Jan. Als Verfasser deS im „Dra» pcau" erschienenen und angeklagten Artikels wird jetzt der <PERSON>frühere Rédacteur des Blattes, Louis Labarre</PERSON>, genannt. Der jetzige nominelle Herausgeber, Brismee, soll diesmal seine verantwortliche Haut nicht zu Markte tragen wollen, da ihm noch das Jahr Gefängnis), was cc vor Kurzem abgesessen, in den Gliedern liege. Gro» Bes Aufsehen macht ein neuer Artikel in Bezug auf das Attentat, der vor einigen Tagen in einem kleinen Blatte, der „Proletarier" betitelt, erschienen ist. Dieses giftige Blatt steht mit dem socialen Handwerkervereine in London in Verbindung und wird von einem rabiaten Schneider, Namens Coulon, redigirt. Das Attentat wird in diesem Artikel mit perfider Frechheit verherr licht, und zugleich werden Orsini und Pierri als Helden ausgerufen und für ihre That mit dem Beifalle des Wahnwitzes überschüttet. Mr. Coulon, der kühne Schneider, wird mit den Rédacteur?« des „Drapeau" und „Crocodile" zusammen demnächst vor Gericht zu erscheinen haben. sM. I.)"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Louis Labarre
    Description: Belgian journalist (1810–1892)
    Born: ['+1810-05-01T00:00:00Z']
    Died: ['+1892-01-17T00:00:00Z']
    Birth place: ['Q108247']
    Death place: ['Q208713']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: jetzt, früher, vor, früh
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.993

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'frühere Rédacteur des Blattes, Louis Labarre' and 'Belgien' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'frühere Rédacteur des Blattes, Louis Labarre' near 'Belgien' around 1858-02-07?
  4. Resolve temporal expressions relative to 1858-02-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 47 [ID: test_de__43]:
  Publication date : 1858-02-07
  Language         : de
  Person  : 'Orsini'  (QID: Q708837)
  Location: 'Brüssel'  (QID: Q239)

  [ARTICLE TEXT — entity markers added]
  "Belgien. <LOCATION>Brüssel</LOCATION> 31. Jan. Als Verfasser deS im „Dra» pcau" erschienenen und angeklagten Artikels wird jetzt der frühere Rédacteur des Blattes, Louis Labarre, genannt. Der jetzige nominelle Herausgeber, Brismee, soll diesmal seine verantwortliche Haut nicht zu Markte tragen wollen, da ihm noch das Jahr Gefängnis), was cc vor Kurzem abgesessen, in den Gliedern liege. Gro» Bes Aufsehen macht ein neuer Artikel in Bezug auf das Attentat, der vor einigen Tagen in einem kleinen Blatte, der „Proletarier" betitelt, erschienen ist. Dieses giftige Blatt steht mit dem socialen Handwerkervereine in London in Verbindung und wird von einem rabiaten Schneider, Namens Coulon, redigirt. Das Attentat wird in diesem Artikel mit perfider Frechheit verherr licht, und zugleich werden <PERSON>Orsini</PERSON> und Pierri als Helden ausgerufen und für ihre That mit dem Beifalle des Wahnwitzes überschüttet. Mr. Coulon, der kühne Schneider, wird mit den Rédacteur?« des „Drapeau" und „Crocodile" zusammen demnächst vor Gericht zu erscheinen haben. sM. I.)"

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Felice Orsini
    Description: italienischer Attentäter auf Napoleon III., Rechtsanwalt
    Born: ['+1819-12-10T00:00:00Z']
    Died: ['+1858-03-13T00:00:00Z']
    Birth place: ['Q99945']
    Death place: ['Q2845761']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: jetzt, früher, vor, früh
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.993

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Orsini' and 'Brüssel' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Orsini' near 'Brüssel' around 1858-02-07?
  4. Resolve temporal expressions relative to 1858-02-07. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 48 [ID: test_en__43]:
  Publication date : 1900-01-16
  Language         : en
  Person  : 'Mar\nshal Foraker'  (QID: N/A)
  Location: 'Santa Fe, N. M'  (QID: Q38555)

  [ARTICLE TEXT — entity markers added]
  "A DARING OUTLAW. LEADER OF BLACK JACK’S GANG OF BANDITS. Ucld-FT p a Train Single-Handed and Afterward Fought a Dcspe>rate llattle with Officers — Killed Two Hundred Men. The notorious leader of the infamous “Black Jack's” gang of train robbeis and murderers, Tom Ketchum, now lies ia the hospital of the penitentiary at <LOCATION>Santa Fe, N. M</LOCATION>., seriously wounded, as the result of an encounter with offi cers of the law. Tom held up a train single-handed and in the sequel to this was wounded and captured. It was the Colorado Southern express that Tom held up. The place selected was near Fulsom, on the northeast corner of New Mexico. One night ns the ex press was puffing laboriously up grade the engineer saw a light ahead giving the signal to stop. When the train slowed down Tom Ketchum jumped into the cab and, carelessly swinging a 45 Colt near the engineer's nose,told him to obey all orders given during the next few minutes. This, Tom said, would save heartaches in the engineer's home and the intrusion of an under taker in the family circle. Then he Jumped off and tried to uncouple the engine, which was made impossible by the steep grade. Failing in this, Tom walked back to the Wells-Fargo ex press car and, thumping the door with the butt of his Colt, demanded admit tance. The messenger opened the door and poked the muzzle of a Winchester out into the dark and pulled the trig ger. That put an end to the hold-up that night. Just how badly Tom was shot Is not known, but he was wound ed in a subsequent battle with United States Marshal Foraker’s posse and he will not say how much damage the messenger did. As he declared the hold-up off it is probable he was se verely injured. The express pulled on and Tom Jumped his broncho and sought safety in the mountains. The attempted robbery was soon known to the officials and three days later Mar shal Foraker’s men were hunting for Tom in the uplands. They finally lilt the trail and followed it hack into the very heart of the mountains. Here they lost it and while discussing the best move a report of a rifle split the air and one of the deputies fell out of his saddle. This was sufficient evi dence of Tom's presence in the vicin ity, but not his exact whereabouts, as Tom used smokeless cartridges. An other shot was heart and another depu ty went to the ground. At this rate every man In the posse would be cut down without a ghost of a chance of getting a shot. The deputies, there fore, separated, and began to scout the brush. A glint of sunshine playing on the blue steel barrels of a Winchester discussed Tom Ketchum’s position be hind a big bowlder surrounded by brushwood. Then the day’s proceed ings began. The deputies shot at that glint of sunshine playing along blue steel; Tom shot at the deputies. The deputies dodged behind trees and rocks and shot wildly. Tom stayed where he was and made bull-eyes. If Tom hadn’t shelved his right arm a little too high in taking aim he would have brought down a full mess of deputies. As it was a slug of lead as big as your finger tore through Tom’s shooting member, and it took a few minutes to change his Winchester over to his left arm. In these short minutes the deputies closed In on Tom and cap tured him. He was In a bad shape. His right arm was terribly broken and torn and he was already suffering from loss of blood. But he was game. Ho offered to take his left arm and begin the performance all over again, which" proposition was respectfully declined. The next day when he was able to be moved Tom was strapped to his bron cho and taken to a train, ultimately landing in the penitentiary hospital at Santa Fe. Of “Black Jack’s" gang of thieves and cutthroats Tom Ketchum was the leader. He was 35 years old, and in Texas, his native state, he is known as the new Jesse James. He stands 5 feet 10 inches In his stocking feet and is built on the graceful lines of a tiger. He is as void of conscience as the Winchester he carried. He would rather shoot a man than eat; if the man be an officer of the law it was more fun to kill him than to go to a dance. One of his boyhood pas times was to hire in some convenient place on the ranch in Texas and shoot Mexican herdsmen. When a lad he was summoned as a witness in a law suit, and not knowing what the sum mons meant, and not caring to take any chances, shot and killed the officer. After this he found it convenient to change his residence, so he rode up into New Mexico and Arizona. Here he soon became a terror to everybody in general and railroad and express sompanies In particular. Ho admits in a roundabout way that since 1S88 he and his gang have stolen from post- offices, trains, stages and wayfarers $200,000 and killed 200 men."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now, after, late, later
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.991

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mar\nshal Foraker' and 'Santa Fe, N. M' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mar\nshal Foraker' near 'Santa Fe, N. M' around 1900-01-16?
  4. Resolve temporal expressions relative to 1900-01-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 49 [ID: test_en__65]:
  Publication date : 1910-12-16
  Language         : en
  Person  : 'C. H. Har\nrison'  (QID: N/A)
  Location: 'I. O. O. F.\nhall'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "MAY BUILD CLUB BOUSE CHAMBER OF COMMERCE CON SIDERS ADVISABILITY OF ERECTING BUILDING FOR MEETINGS AND PERMANENT EXHIBIT. Another large and enthusiastic meeting of the Pullman Chamber of Commerce was held in the I. O. O. F. hall Tuesday evening. The board of trustees announced that C. H. Har rison had been made secretary and treasurer. The several committees reported and then a general discus sion ensued regarding the adoption of an emblem and the securing of a permanent home. Several artistic designs for the emblem were sub mitted but it was decided to post pone action for another week. A number of enthusiastic speech es were made advocating the raising of a sufficient fund to build a home for the club and before adjournment it was decided to appoint a commit tee to look into the possibility of raising the necessary funds. , S. B. Nelson of Spokane made a stirring address in which he insisted that the all important factor in ac complishing results was to make a start and dwelt upon the indirect benefits resulting from every effort to improve a city. He was follewed by F. P. Greene, of Spokane, who explained the work of the Chamber of Commerce of that city and expressed the earnest desire of the Spokane business men to co operate with all tho other cities and towns of the Inland Empire in up building and developing Eastern Washington. Ho said that the pros perity of Spokane depended not so much upon the mines as upon the wheat fields and orchards of the Pa- louse country. The club adjourned to meet next Tuesday evening by which time it is hoped the membership will have passed the 125 mark."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: before
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.996

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'C. H. Har\nrison' and 'I. O. O. F.\nhall' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'C. H. Har\nrison' near 'I. O. O. F.\nhall' around 1910-12-16?
  4. Resolve temporal expressions relative to 1910-12-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 50 [ID: test_en__100]:
  Publication date : 1910-09-16
  Language         : en
  Person  : 'Laura Ellis'  (QID: N/A)
  Location: 'Portland'  (QID: Q6106)

  [ARTICLE TEXT — entity markers added]
  "THE NORTHWEST Captain T. D. Bloni, prominent in shipping circles and head of a codfish company, was found in Wright park, in the heart of the city of Tacotna, last, week, with his throat cut. He will probably die. It Is believed he was at tacked by a robber while on the way to the home of a friend. The attack is supposed to have been made some time before midnight and Blom is be lieved to have lain in the park all night. When found his condition was desperate. Several square feet of sod were covered with blood and there were indications of a struggle. In a fire which desrroyed the home of Jos. C. Wendell located in the sub urbs of <LOCATION>Portland</LOCATION>, Myrtle Wendell, aged 2 years, was burned to death, and <PERSON>Laura Ellis</PERSON>, a domestic, aged IS years, was so badly burned that she died a few minutes after she reached the hospital. It is believed the fire started from the explosion of a gas oline stove. None of the members of the family were home when the fire broke out and it was some time be fore the nearest neighbors could reach the scene, it was then too late to save either of the victims. Two journeyman plumbers out of a job held up and shot Charles Jeakel, a horseshoer of Lewiston, Idaho, through the neck at. Marshal Junction atabout 8 o'clock Saturday night, securing $35 and inflicting a serious wound. The thugs fired three hots at close range at Jeakel, but one taking effect, the other two passing through the victim’s coat at the shoulder. Offering resistance to com mands to stand and deliver caused the use of firearms. Jeakel’s flesh and clothes were powder burnt. Valuable Indian lands on the Yak ima Indian reservation, which were allotted to non-oompetents or held for heirs of dead indians, will be sold by the government on September 26 and October 31. The sale will he made under supervision of S. A. Al. A’oung, the agent in charge. Judge and Mrs. II. E. Canfield were tendered a farewell reception by the members of the Masonic fra ternities of Colfax on the eve of their departure for Spokane last week. Judge Canfield was presented with a gold-headed cane. The property of the Deschutes Irrigation and Power Co., in Oregon, is to be sold at foreclosure sale, the bondholders having just secured an order for the sale from the circuit court in Portland. The claims against the company aggregate $000,0 00. ..J. H. Hildebrant was killed and two Finlanders were seriously injur ed by a premature explosion in the •Mattie Ferguson mine at Basin, Mon tana, Thursday. Hilderbrant had just lighted the fus*l but did not have time to get away before the explosion oc curred."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after, before, late
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.983

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Laura Ellis' and 'Portland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Laura Ellis' near 'Portland' around 1910-09-16?
  4. Resolve temporal expressions relative to 1910-09-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 51 [ID: test_en__63]:
  Publication date : 1920-01-29
  Language         : en
  Person  : 'P. L. Ramsey'  (QID: N/A)
  Location: 'Putnam County'  (QID: Q495045)

  [ARTICLE TEXT — entity markers added]
  "NOTICE. By virtue of a bil of sale issued by Tom Scarlett, Circuit Court Clerk for <LOCATION>Putnam County</LOCATION>, .ennessee, dated on the 6tU. day of January, 1920, I will expore to sale to tne highest bidder for cash on the 31st day of January, 1920, at 1:0; o’clock, P. M. at the Courthouse door in the Town of Cookeville, the following property, to-wit: A house and lot located in the 19th Civil District of Putnam County, Tennessee, containing one acre, more or less, bounded on the east by the lands of J. R. Watson; on the north by the T. C. R. K. Co.; on the west by the lands of Phy; on the south by the lands of J. R. Watson; levied on as the lands of D. Ritten berry, to satisfy a Judgment in favor of <PERSON>P. L. Ramsey</PERSON> ag-ih st him, with interest and all the cost.i of the case. This Jan. 6th, 1920. L. F. MILLER, Sheriff."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1920" → 1920
      - "1920" → 1920
      - "1920" → 1920
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.946

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'P. L. Ramsey' and 'Putnam County' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'P. L. Ramsey' near 'Putnam County' around 1920-01-29?
  4. Resolve temporal expressions relative to 1920-01-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 52 [ID: test_en__99]:
  Publication date : 1910-09-16
  Language         : en
  Person  : 'Judge Canfield'  (QID: N/A)
  Location: 'Spokane'  (QID: Q187805)

  [ARTICLE TEXT — entity markers added]
  "THE NORTHWEST Captain T. D. Bloni, prominent in shipping circles and head of a codfish company, was found in Wright park, in the heart of the city of Tacotna, last, week, with his throat cut. He will probably die. It Is believed he was at tacked by a robber while on the way to the home of a friend. The attack is supposed to have been made some time before midnight and Blom is be lieved to have lain in the park all night. When found his condition was desperate. Several square feet of sod were covered with blood and there were indications of a struggle. In a fire which desrroyed the home of Jos. C. Wendell located in the sub urbs of Portland, Myrtle Wendell, aged 2 years, was burned to death, and Laura Ellis, a domestic, aged IS years, was so badly burned that she died a few minutes after she reached the hospital. It is believed the fire started from the explosion of a gas oline stove. None of the members of the family were home when the fire broke out and it was some time be fore the nearest neighbors could reach the scene, it was then too late to save either of the victims. Two journeyman plumbers out of a job held up and shot Charles Jeakel, a horseshoer of Lewiston, Idaho, through the neck at. Marshal Junction atabout 8 o'clock Saturday night, securing $35 and inflicting a serious wound. The thugs fired three hots at close range at Jeakel, but one taking effect, the other two passing through the victim’s coat at the shoulder. Offering resistance to com mands to stand and deliver caused the use of firearms. Jeakel’s flesh and clothes were powder burnt. Valuable Indian lands on the Yak ima Indian reservation, which were allotted to non-oompetents or held for heirs of dead indians, will be sold by the government on September 26 and October 31. The sale will he made under supervision of S. A. Al. A’oung, the agent in charge. Judge and Mrs. II. E. Canfield were tendered a farewell reception by the members of the Masonic fra ternities of Colfax on the eve of their departure for <LOCATION>Spokane</LOCATION> last week. <PERSON>Judge Canfield</PERSON> was presented with a gold-headed cane. The property of the Deschutes Irrigation and Power Co., in Oregon, is to be sold at foreclosure sale, the bondholders having just secured an order for the sale from the circuit court in Portland. The claims against the company aggregate $000,0 00. ..J. H. Hildebrant was killed and two Finlanders were seriously injur ed by a premature explosion in the •Mattie Ferguson mine at Basin, Mon tana, Thursday. Hilderbrant had just lighted the fus*l but did not have time to get away before the explosion oc curred."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Spokane
    Description: city in and county seat of Spokane County, Washington, United States
    Country: ['Q30']
    Located in: ['Q485276']
    Aliases: {'en': ['The Lilac City', 'Spokane, Washington', 'Spokane, WA'], 'de': ['Spokane Falls', 'Spokane, WA']}
    Coordinates: [{'lat': 47.65719444444444, 'lon': -117.4235}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after, before, late
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.983

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Judge Canfield' and 'Spokane' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Judge Canfield' near 'Spokane' around 1910-09-16?
  4. Resolve temporal expressions relative to 1910-09-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 53 [ID: test_en__87]:
  Publication date : 1960-05-18
  Language         : en
  Person  : 'Neal L. Fowler. Aviation\nElectrician Second Clas USN'  (QID: N/A)
  Location: 'Mediterranean'  (QID: Q4918)

  [ARTICLE TEXT — entity markers added]
  "<LOCATION>Mediterranean</LOCATION> Trip Planned For Fowler Neal L. Fowler. Aviation Electrician Second Clas USN, son of Mr. Worth Fowler of Route I, Tabor City is present ly at home on thirty days leave. Fowler has been in the Navy about three years and will re port to Helicopter Anti-Sub marine Squadron Three at Nor folk Virginia. He will leave in June for a two months cruise of the Mediterranean on a Mid-Shipman cruise."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Mediterranean Sea
    Description: sea between Europe, Africa and Asia
    Country: ['Q29', 'Q142', 'Q38', 'Q235', 'Slovenia', 'Croatia', 'Q236', 'Albania', 'Q41', 'Q233', 'Cyprus', 'Turkey', 'Lebanon', 'Syria', 'Israel', 'Palestine', 'Q79', 'Libya', 'Tunisia', 'Algeria', 'Morocco', 'Bosnia and Herzegovina']
    Aliases: {'en': ['The Mediterranean', 'the Mediterranean Sea'], 'fr': ['Méditerranée'], 'de': ['Mittelländisches Meer']}
    Coordinates: [{'lat': 38, 'lon': 17}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Neal L. Fowler. Aviation\nElectrician Second Clas USN' and 'Mediterranean' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Neal L. Fowler. Aviation\nElectrician Second Clas USN' near 'Mediterranean' around 1960-05-18?
  4. Resolve temporal expressions relative to 1960-05-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 54 [ID: test_en__79]:
  Publication date : 1960-05-18
  Language         : en
  Person  : 'Neal L. Fowler. Aviation\nElectrician Second Clas USN'  (QID: N/A)
  Location: 'Tabor City'  (QID: Q586130)

  [ARTICLE TEXT — entity markers added]
  "Mediterranean Trip Planned For Fowler Neal L. Fowler. Aviation Electrician Second Clas USN, son of Mr. Worth Fowler of Route I, <LOCATION>Tabor City</LOCATION> is present ly at home on thirty days leave. Fowler has been in the Navy about three years and will re port to Helicopter Anti-Sub marine Squadron Three at Nor folk Virginia. He will leave in June for a two months cruise of the Mediterranean on a Mid-Shipman cruise."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Neal L. Fowler. Aviation\nElectrician Second Clas USN' and 'Tabor City' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Neal L. Fowler. Aviation\nElectrician Second Clas USN' near 'Tabor City' around 1960-05-18?
  4. Resolve temporal expressions relative to 1960-05-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 55 [ID: test_en__24]:
  Publication date : 1950-09-30
  Language         : en
  Person  : 'Charlotte Ingram'  (QID: N/A)
  Location: 'Ellendale, Del.'  (QID: Q521614)

  [ARTICLE TEXT — entity markers added]
  "l-HClul) Girl at White House <PERSON>Charlotte Ingram</PERSON>, outstanding 4-H club girl of <LOCATION>Ellendale, Del.</LOCATION> joined with 4-H’er Mary Ann Long of hSelby. Va., and Mrs, Franklin D Roosevelt in present ing the first homemade United Nations Flag to President Harry S. Truman at the White House recently. This ceremony was first of a series of UN flag presentations which wil be made to local of ficials by sewing groups in thous ands of communities throughout the country for flying on October 24th, United Nations Day. White and colored home dem onstration agents will take the lead in ' developing plans for making and presenting the flags, according to M. L. Wilson, direc tor of Extension Work for the U. S. Department of Agriculture."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Ellendale
    Description: town in Sussex County, Delaware, US
    Country: ['United States']
    Located in: ['Sussex County']
    Aliases: {'en': ['Ellendale, Delaware', 'Ellendale, DE']}
    Coordinates: [{'lat': 38.8067, 'lon': -75.4239}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: recently
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.976

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Charlotte Ingram' and 'Ellendale, Del.' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Charlotte Ingram' near 'Ellendale, Del.' around 1950-09-30?
  4. Resolve temporal expressions relative to 1950-09-30. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 56 [ID: test_en__40]:
  Publication date : 1900-01-16
  Language         : en
  Person  : 'United\nStates Marshal Foraker'  (QID: N/A)
  Location: 'Santa Fe, N. M'  (QID: Q38555)

  [ARTICLE TEXT — entity markers added]
  "A DARING OUTLAW. LEADER OF BLACK JACK’S GANG OF BANDITS. Ucld-FT p a Train Single-Handed and Afterward Fought a Dcspe>rate llattle with Officers — Killed Two Hundred Men. The notorious leader of the infamous “Black Jack's” gang of train robbeis and murderers, Tom Ketchum, now lies ia the hospital of the penitentiary at <LOCATION>Santa Fe, N. M</LOCATION>., seriously wounded, as the result of an encounter with offi cers of the law. Tom held up a train single-handed and in the sequel to this was wounded and captured. It was the Colorado Southern express that Tom held up. The place selected was near Fulsom, on the northeast corner of New Mexico. One night ns the ex press was puffing laboriously up grade the engineer saw a light ahead giving the signal to stop. When the train slowed down Tom Ketchum jumped into the cab and, carelessly swinging a 45 Colt near the engineer's nose,told him to obey all orders given during the next few minutes. This, Tom said, would save heartaches in the engineer's home and the intrusion of an under taker in the family circle. Then he Jumped off and tried to uncouple the engine, which was made impossible by the steep grade. Failing in this, Tom walked back to the Wells-Fargo ex press car and, thumping the door with the butt of his Colt, demanded admit tance. The messenger opened the door and poked the muzzle of a Winchester out into the dark and pulled the trig ger. That put an end to the hold-up that night. Just how badly Tom was shot Is not known, but he was wound ed in a subsequent battle with United States Marshal Foraker’s posse and he will not say how much damage the messenger did. As he declared the hold-up off it is probable he was se verely injured. The express pulled on and Tom Jumped his broncho and sought safety in the mountains. The attempted robbery was soon known to the officials and three days later Mar shal Foraker’s men were hunting for Tom in the uplands. They finally lilt the trail and followed it hack into the very heart of the mountains. Here they lost it and while discussing the best move a report of a rifle split the air and one of the deputies fell out of his saddle. This was sufficient evi dence of Tom's presence in the vicin ity, but not his exact whereabouts, as Tom used smokeless cartridges. An other shot was heart and another depu ty went to the ground. At this rate every man In the posse would be cut down without a ghost of a chance of getting a shot. The deputies, there fore, separated, and began to scout the brush. A glint of sunshine playing on the blue steel barrels of a Winchester discussed Tom Ketchum’s position be hind a big bowlder surrounded by brushwood. Then the day’s proceed ings began. The deputies shot at that glint of sunshine playing along blue steel; Tom shot at the deputies. The deputies dodged behind trees and rocks and shot wildly. Tom stayed where he was and made bull-eyes. If Tom hadn’t shelved his right arm a little too high in taking aim he would have brought down a full mess of deputies. As it was a slug of lead as big as your finger tore through Tom’s shooting member, and it took a few minutes to change his Winchester over to his left arm. In these short minutes the deputies closed In on Tom and cap tured him. He was In a bad shape. His right arm was terribly broken and torn and he was already suffering from loss of blood. But he was game. Ho offered to take his left arm and begin the performance all over again, which" proposition was respectfully declined. The next day when he was able to be moved Tom was strapped to his bron cho and taken to a train, ultimately landing in the penitentiary hospital at Santa Fe. Of “Black Jack’s" gang of thieves and cutthroats Tom Ketchum was the leader. He was 35 years old, and in Texas, his native state, he is known as the new Jesse James. He stands 5 feet 10 inches In his stocking feet and is built on the graceful lines of a tiger. He is as void of conscience as the Winchester he carried. He would rather shoot a man than eat; if the man be an officer of the law it was more fun to kill him than to go to a dance. One of his boyhood pas times was to hire in some convenient place on the ranch in Texas and shoot Mexican herdsmen. When a lad he was summoned as a witness in a law suit, and not knowing what the sum mons meant, and not caring to take any chances, shot and killed the officer. After this he found it convenient to change his residence, so he rode up into New Mexico and Arizona. Here he soon became a terror to everybody in general and railroad and express sompanies In particular. Ho admits in a roundabout way that since 1S88 he and his gang have stolen from post- offices, trains, stages and wayfarers $200,000 and killed 200 men."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Santa Fe
    Description: capital city of New Mexico, United States
    Country: ['Q30']
    Located in: ['Santa Fe County']
    Aliases: {'en': ['White Shell Water Place', 'Santa Fe, New Mexico', 'Royal City of the Holy Faith of St. Francis of Assisi', "O gah Po'geh", 'SFNM', 'Santa Fé', 'Santa Fe, NM', "Oghá P'o'oge", 'Po-o-ge', 'Kuapooge', 'Apoga', 'Apoge', "Cua P'Hoge", "Cua-P'ho-o-ge", 'Cua-po-oge', 'Cua-Po-o-que', "Kua-p'o-o-ge", "Oga P'Hoge", "Og-a-p'o-ge", 'Poga', 'Poge', 'Yootó'], 'de': ['Santa Fe, New Mexico']}
    Coordinates: [{'lat': 35.666666666667, 'lon': -105.96666666667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now, after, late, later
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.991

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'United\nStates Marshal Foraker' and 'Santa Fe, N. M' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'United\nStates Marshal Foraker' near 'Santa Fe, N. M' around 1900-01-16?
  4. Resolve temporal expressions relative to 1900-01-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 57 [ID: test_en__88]:
  Publication date : 1960-05-18
  Language         : en
  Person  : 'Neal L. Fowler. Aviation\nElectrician Second Clas USN'  (QID: N/A)
  Location: 'Nor\nfolk Virginia'  (QID: Q49231)

  [ARTICLE TEXT — entity markers added]
  "Mediterranean Trip Planned For Fowler Neal L. Fowler. Aviation Electrician Second Clas USN, son of Mr. Worth Fowler of Route I, Tabor City is present ly at home on thirty days leave. Fowler has been in the Navy about three years and will re port to Helicopter Anti-Sub marine Squadron Three at Nor folk Virginia. He will leave in June for a two months cruise of the Mediterranean on a Mid-Shipman cruise."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Description: independent city in Virginia, United States
    Country: ['Q30']
    Located in: ['Q1370']
    Aliases: {'fr': ['Municipalité de Norfolk', 'Ville de Norfolk']}
    Coordinates: [{'lat': 36.846944444444446, 'lon': -76.28527777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Neal L. Fowler. Aviation\nElectrician Second Clas USN' and 'Nor\nfolk Virginia' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Neal L. Fowler. Aviation\nElectrician Second Clas USN' near 'Nor\nfolk Virginia' around 1960-05-18?
  4. Resolve temporal expressions relative to 1960-05-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 58 [ID: test_en__90]:
  Publication date : 1840-11-14
  Language         : en
  Person  : 'SIMEON COLTON'  (QID: N/A)
  Location: 'Fayetteville'  (QID: Q331104)

  [ARTICLE TEXT — entity markers added]
  "A NEW SCHOOL. O N Monday the 5th of October, the subscriber wnl open in this town, a school for boys where the various branches of English and Classical studies will be taught. The charge tor Tuition will be af 10 25, per term, for all engaged in Classi cal studies and the higher branches of English "or S41 per annum. For fhe ordinary branches of En glish studies the charge will be $8 25 per term, tuition in all cases to be paid in advance, and no student received for less than a term. The year will commence on tho 5th of October, and close early in August, with no intervening vacation ex cept an occasional recess of a few days. No deduc tion will be made for absence unless by special agreement. - Having taken a commodious house, the subscriber will accommodate a number of board ers at SI40 per annum, including lodging, room fuel and lights. <PERSON>SIMEON COLTON</PERSON>. ’ <LOCATION>Fayetteville</LOCATION>, August 13, 1840. 76-tf *** Fayetteville Observer and Wilmington Ad- xertiscr will please copy four weeks."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Fayetteville
    Description: city in Cumberland County, North Carolina, United States
    Country: ['United States']
    Located in: ['Cumberland County']
    Aliases: {'en': ['Fayetteville, North Carolina', 'Fayetteville, NC']}
    Coordinates: [{'lat': 35.066666666667, 'lon': -78.9175}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1840" → 1840
      - "August 13, 1840" → August 13, 1840
    Temporal signal words: early
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.938

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'SIMEON COLTON' and 'Fayetteville' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'SIMEON COLTON' near 'Fayetteville' around 1840-11-14?
  4. Resolve temporal expressions relative to 1840-11-14. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 59 [ID: test_en__53]:
  Publication date : 1920-01-29
  Language         : en
  Person  : 'D. Ritten\nberry'  (QID: N/A)
  Location: 'Cookeville'  (QID: Q2456192)

  [ARTICLE TEXT — entity markers added]
  "NOTICE. By virtue of a bil of sale issued by Tom Scarlett, Circuit Court Clerk for Putnam County, .ennessee, dated on the 6tU. day of January, 1920, I will expore to sale to tne highest bidder for cash on the 31st day of January, 1920, at 1:0; o’clock, P. M. at the Courthouse door in the Town of <LOCATION>Cookeville</LOCATION>, the following property, to-wit: A house and lot located in the 19th Civil District of Putnam County, Tennessee, containing one acre, more or less, bounded on the east by the lands of J. R. Watson; on the north by the T. C. R. K. Co.; on the west by the lands of Phy; on the south by the lands of J. R. Watson; levied on as the lands of D. Ritten berry, to satisfy a Judgment in favor of P. L. Ramsey ag-ih st him, with interest and all the cost.i of the case. This Jan. 6th, 1920. L. F. MILLER, Sheriff."

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
    Temporal expressions found (3):
      - "1920" → 1920
      - "1920" → 1920
      - "1920" → 1920
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.946

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'D. Ritten\nberry' and 'Cookeville' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'D. Ritten\nberry' near 'Cookeville' around 1920-01-29?
  4. Resolve temporal expressions relative to 1920-01-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 60 [ID: test_en__54]:
  Publication date : 1920-01-29
  Language         : en
  Person  : 'Tom Scarlett, Circuit Court Clerk\nfor Putnam County'  (QID: N/A)
  Location: 'Cookeville'  (QID: Q2456192)

  [ARTICLE TEXT — entity markers added]
  "NOTICE. By virtue of a bil of sale issued by Tom Scarlett, Circuit Court Clerk for Putnam County, .ennessee, dated on the 6tU. day of January, 1920, I will expore to sale to tne highest bidder for cash on the 31st day of January, 1920, at 1:0; o’clock, P. M. at the Courthouse door in the Town of <LOCATION>Cookeville</LOCATION>, the following property, to-wit: A house and lot located in the 19th Civil District of Putnam County, Tennessee, containing one acre, more or less, bounded on the east by the lands of J. R. Watson; on the north by the T. C. R. K. Co.; on the west by the lands of Phy; on the south by the lands of J. R. Watson; levied on as the lands of D. Ritten berry, to satisfy a Judgment in favor of P. L. Ramsey ag-ih st him, with interest and all the cost.i of the case. This Jan. 6th, 1920. L. F. MILLER, Sheriff."

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
    Temporal expressions found (3):
      - "1920" → 1920
      - "1920" → 1920
      - "1920" → 1920
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.946

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Tom Scarlett, Circuit Court Clerk\nfor Putnam County' and 'Cookeville' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Tom Scarlett, Circuit Court Clerk\nfor Putnam County' near 'Cookeville' around 1920-01-29?
  4. Resolve temporal expressions relative to 1920-01-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 61 [ID: test_en__60]:
  Publication date : 1920-01-29
  Language         : en
  Person  : 'Tom Scarlett, Circuit Court Clerk\nfor Putnam County'  (QID: N/A)
  Location: 'Putnam County'  (QID: Q495045)

  [ARTICLE TEXT — entity markers added]
  "NOTICE. By virtue of a bil of sale issued by Tom Scarlett, Circuit Court Clerk for <LOCATION>Putnam County</LOCATION>, .ennessee, dated on the 6tU. day of January, 1920, I will expore to sale to tne highest bidder for cash on the 31st day of January, 1920, at 1:0; o’clock, P. M. at the Courthouse door in the Town of Cookeville, the following property, to-wit: A house and lot located in the 19th Civil District of Putnam County, Tennessee, containing one acre, more or less, bounded on the east by the lands of J. R. Watson; on the north by the T. C. R. K. Co.; on the west by the lands of Phy; on the south by the lands of J. R. Watson; levied on as the lands of D. Ritten berry, to satisfy a Judgment in favor of P. L. Ramsey ag-ih st him, with interest and all the cost.i of the case. This Jan. 6th, 1920. L. F. MILLER, Sheriff."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Putnam County
    Description: county in Tennessee, United States
    Country: ['United States']
    Located in: ['Tennessee']
    Aliases: {'en': ['Putnam County, Tennessee', 'Putnam County, TN'], 'fr': ['Putnam County']}
    Coordinates: [{'lat': 36.14, 'lon': -85.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1920" → 1920
      - "1920" → 1920
      - "1920" → 1920
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.946

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Tom Scarlett, Circuit Court Clerk\nfor Putnam County' and 'Putnam County' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Tom Scarlett, Circuit Court Clerk\nfor Putnam County' near 'Putnam County' around 1920-01-29?
  4. Resolve temporal expressions relative to 1920-01-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 62 [ID: test_en__59]:
  Publication date : 1920-01-29
  Language         : en
  Person  : 'D. Ritten\nberry'  (QID: N/A)
  Location: 'Putnam County'  (QID: Q495045)

  [ARTICLE TEXT — entity markers added]
  "NOTICE. By virtue of a bil of sale issued by Tom Scarlett, Circuit Court Clerk for <LOCATION>Putnam County</LOCATION>, .ennessee, dated on the 6tU. day of January, 1920, I will expore to sale to tne highest bidder for cash on the 31st day of January, 1920, at 1:0; o’clock, P. M. at the Courthouse door in the Town of Cookeville, the following property, to-wit: A house and lot located in the 19th Civil District of Putnam County, Tennessee, containing one acre, more or less, bounded on the east by the lands of J. R. Watson; on the north by the T. C. R. K. Co.; on the west by the lands of Phy; on the south by the lands of J. R. Watson; levied on as the lands of D. Ritten berry, to satisfy a Judgment in favor of P. L. Ramsey ag-ih st him, with interest and all the cost.i of the case. This Jan. 6th, 1920. L. F. MILLER, Sheriff."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Putnam County
    Description: county in Tennessee, United States
    Country: ['United States']
    Located in: ['Tennessee']
    Aliases: {'en': ['Putnam County, Tennessee', 'Putnam County, TN'], 'fr': ['Putnam County']}
    Coordinates: [{'lat': 36.14, 'lon': -85.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1920" → 1920
      - "1920" → 1920
      - "1920" → 1920
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.946

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'D. Ritten\nberry' and 'Putnam County' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'D. Ritten\nberry' near 'Putnam County' around 1920-01-29?
  4. Resolve temporal expressions relative to 1920-01-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 63 [ID: test_en__34]:
  Publication date : 1900-01-16
  Language         : en
  Person  : 'Tom'  (QID: Q1813288)
  Location: 'Santa Fe, N. M'  (QID: Q38555)

  [ARTICLE TEXT — entity markers added]
  "A DARING OUTLAW. LEADER OF BLACK JACK’S GANG OF BANDITS. Ucld-FT p a Train Single-Handed and Afterward Fought a Dcspe>rate llattle with Officers — Killed Two Hundred Men. The notorious leader of the infamous “Black Jack's” gang of train robbeis and murderers, <PERSON>Tom</PERSON> Ketchum, now lies ia the hospital of the penitentiary at <LOCATION>Santa Fe, N. M</LOCATION>., seriously wounded, as the result of an encounter with offi cers of the law. Tom held up a train single-handed and in the sequel to this was wounded and captured. It was the Colorado Southern express that Tom held up. The place selected was near Fulsom, on the northeast corner of New Mexico. One night ns the ex press was puffing laboriously up grade the engineer saw a light ahead giving the signal to stop. When the train slowed down Tom Ketchum jumped into the cab and, carelessly swinging a 45 Colt near the engineer's nose,told him to obey all orders given during the next few minutes. This, Tom said, would save heartaches in the engineer's home and the intrusion of an under taker in the family circle. Then he Jumped off and tried to uncouple the engine, which was made impossible by the steep grade. Failing in this, Tom walked back to the Wells-Fargo ex press car and, thumping the door with the butt of his Colt, demanded admit tance. The messenger opened the door and poked the muzzle of a Winchester out into the dark and pulled the trig ger. That put an end to the hold-up that night. Just how badly Tom was shot Is not known, but he was wound ed in a subsequent battle with United States Marshal Foraker’s posse and he will not say how much damage the messenger did. As he declared the hold-up off it is probable he was se verely injured. The express pulled on and Tom Jumped his broncho and sought safety in the mountains. The attempted robbery was soon known to the officials and three days later Mar shal Foraker’s men were hunting for Tom in the uplands. They finally lilt the trail and followed it hack into the very heart of the mountains. Here they lost it and while discussing the best move a report of a rifle split the air and one of the deputies fell out of his saddle. This was sufficient evi dence of Tom's presence in the vicin ity, but not his exact whereabouts, as Tom used smokeless cartridges. An other shot was heart and another depu ty went to the ground. At this rate every man In the posse would be cut down without a ghost of a chance of getting a shot. The deputies, there fore, separated, and began to scout the brush. A glint of sunshine playing on the blue steel barrels of a Winchester discussed Tom Ketchum’s position be hind a big bowlder surrounded by brushwood. Then the day’s proceed ings began. The deputies shot at that glint of sunshine playing along blue steel; Tom shot at the deputies. The deputies dodged behind trees and rocks and shot wildly. Tom stayed where he was and made bull-eyes. If Tom hadn’t shelved his right arm a little too high in taking aim he would have brought down a full mess of deputies. As it was a slug of lead as big as your finger tore through Tom’s shooting member, and it took a few minutes to change his Winchester over to his left arm. In these short minutes the deputies closed In on Tom and cap tured him. He was In a bad shape. His right arm was terribly broken and torn and he was already suffering from loss of blood. But he was game. Ho offered to take his left arm and begin the performance all over again, which" proposition was respectfully declined. The next day when he was able to be moved Tom was strapped to his bron cho and taken to a train, ultimately landing in the penitentiary hospital at Santa Fe. Of “Black Jack’s" gang of thieves and cutthroats Tom Ketchum was the leader. He was 35 years old, and in Texas, his native state, he is known as the new Jesse James. He stands 5 feet 10 inches In his stocking feet and is built on the graceful lines of a tiger. He is as void of conscience as the Winchester he carried. He would rather shoot a man than eat; if the man be an officer of the law it was more fun to kill him than to go to a dance. One of his boyhood pas times was to hire in some convenient place on the ranch in Texas and shoot Mexican herdsmen. When a lad he was summoned as a witness in a law suit, and not knowing what the sum mons meant, and not caring to take any chances, shot and killed the officer. After this he found it convenient to change his residence, so he rode up into New Mexico and Arizona. Here he soon became a terror to everybody in general and railroad and express sompanies In particular. Ho admits in a roundabout way that since 1S88 he and his gang have stolen from post- offices, trains, stages and wayfarers $200,000 and killed 200 men."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Tom Ketchum
    Description: American gunman (1863–1901)
    Born: ['+1863-10-31T00:00:00Z']
    Died: ['+1901-04-26T00:00:00Z']
    Birth place: ['Q484586']
    Death place: ['Q485020']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: now, after, late, later
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.991

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Tom' and 'Santa Fe, N. M' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Tom' near 'Santa Fe, N. M' around 1900-01-16?
  4. Resolve temporal expressions relative to 1900-01-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 64 [ID: test_en__155]:
  Publication date : 1910-02-18
  Language         : en
  Person  : 'C. K. Van Auker'  (QID: N/A)
  Location: 'Boise'  (QID: Q35775)

  [ARTICLE TEXT — entity markers added]
  "Della Pringle Coining The famous Della Pringle company will commence a five nights engage ment in The Auditorium Monday, \ Feb. 21. .Miss Pringle is supported by <PERSON>C. K. Van Auker</PERSON>, and absolutely the strongest company of players in the \ west. Seventy straight weeks in t <LOCATION>Boise</LOCATION> is the record breaking “run” j of this splendid organization, and' not one single failure. Miss Pringle j has selected “The Man on the Box” for the opening play, to be followed by “Peaceful Valley,” "Flora May's Dutchman,” "Married Life,” and the Lewis Morrison version of the won derful play “Faust.” Miss Pringle carries complete sce nic and electrical effects for “Faust" and a correct and perfect perform ance is promised. Many pleasing spe cialties are introduced each night, and a handsome diamond ring will be given away Friday night. Popular prices 2 5, 3 5 and 50 cents will prevail. Tickets at Watt’s Phar macy."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Boise
    Description: city in and state capital of Idaho, United States
    Country: ['United States']
    Located in: ['Ada County']
    Aliases: {'en': ['Boise, Idaho', 'Boise, ID', 'City of Trees'], 'de': ['Boisé City', 'Boise, Idaho']}
    Coordinates: [{'lat': 43.613611111111, 'lon': -116.23777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.961

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'C. K. Van Auker' and 'Boise' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'C. K. Van Auker' near 'Boise' around 1910-02-18?
  4. Resolve temporal expressions relative to 1910-02-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 65 [ID: test_en__18]:
  Publication date : 1950-09-30
  Language         : en
  Person  : 'Charlotte Ingram'  (QID: N/A)
  Location: 'White House'  (QID: Q35525)

  [ARTICLE TEXT — entity markers added]
  "l-HClul) Girl at <LOCATION>White House</LOCATION> <PERSON>Charlotte Ingram</PERSON>, outstanding 4-H club girl of Ellendale, Del. joined with 4-H’er Mary Ann Long of hSelby. Va., and Mrs, Franklin D Roosevelt in present ing the first homemade United Nations Flag to President Harry S. Truman at the White House recently. This ceremony was first of a series of UN flag presentations which wil be made to local of ficials by sewing groups in thous ands of communities throughout the country for flying on October 24th, United Nations Day. White and colored home dem onstration agents will take the lead in ' developing plans for making and presenting the flags, according to M. L. Wilson, direc tor of Extension Work for the U. S. Department of Agriculture."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: White House
    Description: official residence and office of the President of the United States
    Country: ['United States']
    Located in: ['Washington, D.C.']
    Aliases: {'en': ['Executive Mansion', "President's Palace", 'Presidential Mansion', "President's House", 'the White House', '1600 Pennsylvania Avenue'], 'fr': ['Maison Blanche', 'State Floor', 'White House', 'The White House'], 'de': ['1600 Pennsylvania Avenue', 'Weisses Haus', 'White House']}
    Coordinates: [{'lat': 38.897777777777776, 'lon': -77.03666666666666}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: recently
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.976

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Charlotte Ingram' and 'White House' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Charlotte Ingram' near 'White House' around 1950-09-30?
  4. Resolve temporal expressions relative to 1950-09-30. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 66 [ID: test_en__106]:
  Publication date : 1910-09-16
  Language         : en
  Person  : 'Judge and Mrs. II. E. Canfield'  (QID: N/A)
  Location: 'the Yak\nima Indian reservation'  (QID: Q3457242)

  [ARTICLE TEXT — entity markers added]
  "THE NORTHWEST Captain T. D. Bloni, prominent in shipping circles and head of a codfish company, was found in Wright park, in the heart of the city of Tacotna, last, week, with his throat cut. He will probably die. It Is believed he was at tacked by a robber while on the way to the home of a friend. The attack is supposed to have been made some time before midnight and Blom is be lieved to have lain in the park all night. When found his condition was desperate. Several square feet of sod were covered with blood and there were indications of a struggle. In a fire which desrroyed the home of Jos. C. Wendell located in the sub urbs of Portland, Myrtle Wendell, aged 2 years, was burned to death, and Laura Ellis, a domestic, aged IS years, was so badly burned that she died a few minutes after she reached the hospital. It is believed the fire started from the explosion of a gas oline stove. None of the members of the family were home when the fire broke out and it was some time be fore the nearest neighbors could reach the scene, it was then too late to save either of the victims. Two journeyman plumbers out of a job held up and shot Charles Jeakel, a horseshoer of Lewiston, Idaho, through the neck at. Marshal Junction atabout 8 o'clock Saturday night, securing $35 and inflicting a serious wound. The thugs fired three hots at close range at Jeakel, but one taking effect, the other two passing through the victim’s coat at the shoulder. Offering resistance to com mands to stand and deliver caused the use of firearms. Jeakel’s flesh and clothes were powder burnt. Valuable Indian lands on the Yak ima Indian reservation, which were allotted to non-oompetents or held for heirs of dead indians, will be sold by the government on September 26 and October 31. The sale will he made under supervision of S. A. Al. A’oung, the agent in charge. <PERSON>Judge and Mrs. II. E. Canfield</PERSON> were tendered a farewell reception by the members of the Masonic fra ternities of Colfax on the eve of their departure for Spokane last week. Judge Canfield was presented with a gold-headed cane. The property of the Deschutes Irrigation and Power Co., in Oregon, is to be sold at foreclosure sale, the bondholders having just secured an order for the sale from the circuit court in Portland. The claims against the company aggregate $000,0 00. ..J. H. Hildebrant was killed and two Finlanders were seriously injur ed by a premature explosion in the •Mattie Ferguson mine at Basin, Mon tana, Thursday. Hilderbrant had just lighted the fus*l but did not have time to get away before the explosion oc curred."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Yakama Indian Reservation
    Description: Indian Reservation in Eastern Washington State
    Country: ['Q30']
    Located in: ['Q820502', 'Q156629']
    Aliases: {'en': ['Yakima Indian Reservation', 'Yakama Nation']}
    Coordinates: [{'lat': 46.233333333333, 'lon': -120.82194444444}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after, before, late
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.983

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Judge and Mrs. II. E. Canfield' and 'the Yak\nima Indian reservation' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Judge and Mrs. II. E. Canfield' near 'the Yak\nima Indian reservation' around 1910-09-16?
  4. Resolve temporal expressions relative to 1910-09-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 67 [ID: test_en__20]:
  Publication date : 1950-09-30
  Language         : en
  Person  : 'President Harry\nS. Truman'  (QID: Q11613)
  Location: 'White House'  (QID: Q35525)

  [ARTICLE TEXT — entity markers added]
  "l-HClul) Girl at <LOCATION>White House</LOCATION> Charlotte Ingram, outstanding 4-H club girl of Ellendale, Del. joined with 4-H’er Mary Ann Long of hSelby. Va., and Mrs, Franklin D Roosevelt in present ing the first homemade United Nations Flag to President Harry S. Truman at the White House recently. This ceremony was first of a series of UN flag presentations which wil be made to local of ficials by sewing groups in thous ands of communities throughout the country for flying on October 24th, United Nations Day. White and colored home dem onstration agents will take the lead in ' developing plans for making and presenting the flags, according to M. L. Wilson, direc tor of Extension Work for the U. S. Department of Agriculture."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Harry S. Truman
    Description: president of the United States from 1945 to 1953; politician (1884–1972)
    Born: ['+1884-05-08T00:00:00Z', '+1884-01-01T00:00:00Z']
    Died: ['+1972-12-26T00:00:00Z']
    Birth place: ['Lamar']
    Death place: ['Kansas City']
    Work locations: ['Washington, D.C.']
  Location Wikidata:
    Label: White House
    Description: official residence and office of the President of the United States
    Country: ['United States']
    Located in: ['Washington, D.C.']
    Aliases: {'en': ['Executive Mansion', "President's Palace", 'Presidential Mansion', "President's House", 'the White House', '1600 Pennsylvania Avenue'], 'fr': ['Maison Blanche', 'State Floor', 'White House', 'The White House'], 'de': ['1600 Pennsylvania Avenue', 'Weisses Haus', 'White House']}
    Coordinates: [{'lat': 38.897777777777776, 'lon': -77.03666666666666}]
  Known person–location links: {"work_location": "P937"}

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: recently
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.976

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'President Harry\nS. Truman' and 'White House' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'President Harry\nS. Truman' near 'White House' around 1950-09-30?
  4. Resolve temporal expressions relative to 1950-09-30. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 68 [ID: test_en__93]:
  Publication date : 1910-09-16
  Language         : en
  Person  : 'J. H. Hildebrant'  (QID: N/A)
  Location: 'Portland'  (QID: Q6106)

  [ARTICLE TEXT — entity markers added]
  "THE NORTHWEST Captain T. D. Bloni, prominent in shipping circles and head of a codfish company, was found in Wright park, in the heart of the city of Tacotna, last, week, with his throat cut. He will probably die. It Is believed he was at tacked by a robber while on the way to the home of a friend. The attack is supposed to have been made some time before midnight and Blom is be lieved to have lain in the park all night. When found his condition was desperate. Several square feet of sod were covered with blood and there were indications of a struggle. In a fire which desrroyed the home of Jos. C. Wendell located in the sub urbs of <LOCATION>Portland</LOCATION>, Myrtle Wendell, aged 2 years, was burned to death, and Laura Ellis, a domestic, aged IS years, was so badly burned that she died a few minutes after she reached the hospital. It is believed the fire started from the explosion of a gas oline stove. None of the members of the family were home when the fire broke out and it was some time be fore the nearest neighbors could reach the scene, it was then too late to save either of the victims. Two journeyman plumbers out of a job held up and shot Charles Jeakel, a horseshoer of Lewiston, Idaho, through the neck at. Marshal Junction atabout 8 o'clock Saturday night, securing $35 and inflicting a serious wound. The thugs fired three hots at close range at Jeakel, but one taking effect, the other two passing through the victim’s coat at the shoulder. Offering resistance to com mands to stand and deliver caused the use of firearms. Jeakel’s flesh and clothes were powder burnt. Valuable Indian lands on the Yak ima Indian reservation, which were allotted to non-oompetents or held for heirs of dead indians, will be sold by the government on September 26 and October 31. The sale will he made under supervision of S. A. Al. A’oung, the agent in charge. Judge and Mrs. II. E. Canfield were tendered a farewell reception by the members of the Masonic fra ternities of Colfax on the eve of their departure for Spokane last week. Judge Canfield was presented with a gold-headed cane. The property of the Deschutes Irrigation and Power Co., in Oregon, is to be sold at foreclosure sale, the bondholders having just secured an order for the sale from the circuit court in Portland. The claims against the company aggregate $000,0 00. ..<PERSON>J. H. Hildebrant</PERSON> was killed and two Finlanders were seriously injur ed by a premature explosion in the •Mattie Ferguson mine at Basin, Mon tana, Thursday. Hilderbrant had just lighted the fus*l but did not have time to get away before the explosion oc curred."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Portland
    Description: seat of Multnomah County, and largest city in state of Oregon, United States
    Country: ['United States']
    Located in: ['Multnomah County', 'Clackamas County', 'Q484538']
    Aliases: {'en': ['Portland, Oregon', 'City of Portland', 'Rose City', 'City of Roses', 'Rip City', 'Stumptown', 'Portland, OR', 'PDX', 'Beervana', 'Bridgetown'], 'de': ['Portland (Oregon)', 'Portland, Oregon']}
    Coordinates: [{'lat': 45.515, 'lon': -122.67916666666666}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after, before, late
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.983

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'J. H. Hildebrant' and 'Portland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'J. H. Hildebrant' near 'Portland' around 1910-09-16?
  4. Resolve temporal expressions relative to 1910-09-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 69 [ID: test_en__91]:
  Publication date : 1910-09-16
  Language         : en
  Person  : 'J. H. Hildebrant'  (QID: N/A)
  Location: 'Basin, Mon\ntana'  (QID: Q967057)

  [ARTICLE TEXT — entity markers added]
  "THE NORTHWEST Captain T. D. Bloni, prominent in shipping circles and head of a codfish company, was found in Wright park, in the heart of the city of Tacotna, last, week, with his throat cut. He will probably die. It Is believed he was at tacked by a robber while on the way to the home of a friend. The attack is supposed to have been made some time before midnight and Blom is be lieved to have lain in the park all night. When found his condition was desperate. Several square feet of sod were covered with blood and there were indications of a struggle. In a fire which desrroyed the home of Jos. C. Wendell located in the sub urbs of Portland, Myrtle Wendell, aged 2 years, was burned to death, and Laura Ellis, a domestic, aged IS years, was so badly burned that she died a few minutes after she reached the hospital. It is believed the fire started from the explosion of a gas oline stove. None of the members of the family were home when the fire broke out and it was some time be fore the nearest neighbors could reach the scene, it was then too late to save either of the victims. Two journeyman plumbers out of a job held up and shot Charles Jeakel, a horseshoer of Lewiston, Idaho, through the neck at. Marshal Junction atabout 8 o'clock Saturday night, securing $35 and inflicting a serious wound. The thugs fired three hots at close range at Jeakel, but one taking effect, the other two passing through the victim’s coat at the shoulder. Offering resistance to com mands to stand and deliver caused the use of firearms. Jeakel’s flesh and clothes were powder burnt. Valuable Indian lands on the Yak ima Indian reservation, which were allotted to non-oompetents or held for heirs of dead indians, will be sold by the government on September 26 and October 31. The sale will he made under supervision of S. A. Al. A’oung, the agent in charge. Judge and Mrs. II. E. Canfield were tendered a farewell reception by the members of the Masonic fra ternities of Colfax on the eve of their departure for Spokane last week. Judge Canfield was presented with a gold-headed cane. The property of the Deschutes Irrigation and Power Co., in Oregon, is to be sold at foreclosure sale, the bondholders having just secured an order for the sale from the circuit court in Portland. The claims against the company aggregate $000,0 00. ..<PERSON>J. H. Hildebrant</PERSON> was killed and two Finlanders were seriously injur ed by a premature explosion in the •Mattie Ferguson mine at Basin, Mon tana, Thursday. Hilderbrant had just lighted the fus*l but did not have time to get away before the explosion oc curred."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Basin
    Description: census-designated place in Jefferson County, Montana, USA
    Country: ['United States']
    Located in: ['Jefferson County']
    Aliases: {'en': ['Basin, MT', 'Basin, Montana']}
    Coordinates: [{'lat': 46.276666666667, 'lon': -112.26777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after, before, late
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.983

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'J. H. Hildebrant' and 'Basin, Mon\ntana' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'J. H. Hildebrant' near 'Basin, Mon\ntana' around 1910-09-16?
  4. Resolve temporal expressions relative to 1910-09-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 70 [ID: test_en__56]:
  Publication date : 1920-01-29
  Language         : en
  Person  : 'Phy'  (QID: N/A)
  Location: 'Cookeville'  (QID: Q2456192)

  [ARTICLE TEXT — entity markers added]
  "NOTICE. By virtue of a bil of sale issued by Tom Scarlett, Circuit Court Clerk for Putnam County, .ennessee, dated on the 6tU. day of January, 1920, I will expore to sale to tne highest bidder for cash on the 31st day of January, 1920, at 1:0; o’clock, P. M. at the Courthouse door in the Town of <LOCATION>Cookeville</LOCATION>, the following property, to-wit: A house and lot located in the 19th Civil District of Putnam County, Tennessee, containing one acre, more or less, bounded on the east by the lands of J. R. Watson; on the north by the T. C. R. K. Co.; on the west by the lands of <PERSON>Phy</PERSON>; on the south by the lands of J. R. Watson; levied on as the lands of D. Ritten berry, to satisfy a Judgment in favor of P. L. Ramsey ag-ih st him, with interest and all the cost.i of the case. This Jan. 6th, 1920. L. F. MILLER, Sheriff."

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
    Temporal expressions found (3):
      - "1920" → 1920
      - "1920" → 1920
      - "1920" → 1920
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.946

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Phy' and 'Cookeville' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Phy' near 'Cookeville' around 1920-01-29?
  4. Resolve temporal expressions relative to 1920-01-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 71 [ID: test_en__105]:
  Publication date : 1910-09-16
  Language         : en
  Person  : 'Jeakel'  (QID: N/A)
  Location: 'Marshal\nJunction'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "THE NORTHWEST Captain T. D. Bloni, prominent in shipping circles and head of a codfish company, was found in Wright park, in the heart of the city of Tacotna, last, week, with his throat cut. He will probably die. It Is believed he was at tacked by a robber while on the way to the home of a friend. The attack is supposed to have been made some time before midnight and Blom is be lieved to have lain in the park all night. When found his condition was desperate. Several square feet of sod were covered with blood and there were indications of a struggle. In a fire which desrroyed the home of Jos. C. Wendell located in the sub urbs of Portland, Myrtle Wendell, aged 2 years, was burned to death, and Laura Ellis, a domestic, aged IS years, was so badly burned that she died a few minutes after she reached the hospital. It is believed the fire started from the explosion of a gas oline stove. None of the members of the family were home when the fire broke out and it was some time be fore the nearest neighbors could reach the scene, it was then too late to save either of the victims. Two journeyman plumbers out of a job held up and shot Charles <PERSON>Jeakel</PERSON>, a horseshoer of Lewiston, Idaho, through the neck at. Marshal Junction atabout 8 o'clock Saturday night, securing $35 and inflicting a serious wound. The thugs fired three hots at close range at Jeakel, but one taking effect, the other two passing through the victim’s coat at the shoulder. Offering resistance to com mands to stand and deliver caused the use of firearms. Jeakel’s flesh and clothes were powder burnt. Valuable Indian lands on the Yak ima Indian reservation, which were allotted to non-oompetents or held for heirs of dead indians, will be sold by the government on September 26 and October 31. The sale will he made under supervision of S. A. Al. A’oung, the agent in charge. Judge and Mrs. II. E. Canfield were tendered a farewell reception by the members of the Masonic fra ternities of Colfax on the eve of their departure for Spokane last week. Judge Canfield was presented with a gold-headed cane. The property of the Deschutes Irrigation and Power Co., in Oregon, is to be sold at foreclosure sale, the bondholders having just secured an order for the sale from the circuit court in Portland. The claims against the company aggregate $000,0 00. ..J. H. Hildebrant was killed and two Finlanders were seriously injur ed by a premature explosion in the •Mattie Ferguson mine at Basin, Mon tana, Thursday. Hilderbrant had just lighted the fus*l but did not have time to get away before the explosion oc curred."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after, before, late
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.983

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Jeakel' and 'Marshal\nJunction' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Jeakel' near 'Marshal\nJunction' around 1910-09-16?
  4. Resolve temporal expressions relative to 1910-09-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 72 [ID: test_en__110]:
  Publication date : 1930-05-16
  Language         : en
  Person  : "EHz-\naheth City's strong-headed Trial\nJudge Phil Sawyer"  (QID: N/A)
  Location: 'Elizabeth'  (QID: Q1018467)

  [ARTICLE TEXT — entity markers added]
  "A JAIL THREAT FOR ATTORNEY C. E. THOMPSON "If I thought you meant what you said, I’d throw you in jail for contempt of court.” it was EHz- aheth City's strong-headed Trial Judge Phil Sawyer, speaking, and he was speaking to C. E. Thomp son. speeial counsel for the City of <LOCATION>Elizabeth</LOCATION> City and partner in • he law firm of Thompson & Wil son. Tlii'- happened in Itceordcr’s Court Saturday morning and Elizabeth Citizens have not yet beeontc aecu^tomed to the thought of Everett Thompson occupying a cell in the county Jail."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between "EHz-\naheth City's strong-headed Trial\nJudge Phil Sawyer" and 'Elizabeth' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing "EHz-\naheth City's strong-headed Trial\nJudge Phil Sawyer" near 'Elizabeth' around 1930-05-16?
  4. Resolve temporal expressions relative to 1930-05-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 73 [ID: test_en__94]:
  Publication date : 1910-09-16
  Language         : en
  Person  : 'Jeakel'  (QID: N/A)
  Location: 'the Yak\nima Indian reservation'  (QID: Q3457242)

  [ARTICLE TEXT — entity markers added]
  "THE NORTHWEST Captain T. D. Bloni, prominent in shipping circles and head of a codfish company, was found in Wright park, in the heart of the city of Tacotna, last, week, with his throat cut. He will probably die. It Is believed he was at tacked by a robber while on the way to the home of a friend. The attack is supposed to have been made some time before midnight and Blom is be lieved to have lain in the park all night. When found his condition was desperate. Several square feet of sod were covered with blood and there were indications of a struggle. In a fire which desrroyed the home of Jos. C. Wendell located in the sub urbs of Portland, Myrtle Wendell, aged 2 years, was burned to death, and Laura Ellis, a domestic, aged IS years, was so badly burned that she died a few minutes after she reached the hospital. It is believed the fire started from the explosion of a gas oline stove. None of the members of the family were home when the fire broke out and it was some time be fore the nearest neighbors could reach the scene, it was then too late to save either of the victims. Two journeyman plumbers out of a job held up and shot Charles <PERSON>Jeakel</PERSON>, a horseshoer of Lewiston, Idaho, through the neck at. Marshal Junction atabout 8 o'clock Saturday night, securing $35 and inflicting a serious wound. The thugs fired three hots at close range at Jeakel, but one taking effect, the other two passing through the victim’s coat at the shoulder. Offering resistance to com mands to stand and deliver caused the use of firearms. Jeakel’s flesh and clothes were powder burnt. Valuable Indian lands on the Yak ima Indian reservation, which were allotted to non-oompetents or held for heirs of dead indians, will be sold by the government on September 26 and October 31. The sale will he made under supervision of S. A. Al. A’oung, the agent in charge. Judge and Mrs. II. E. Canfield were tendered a farewell reception by the members of the Masonic fra ternities of Colfax on the eve of their departure for Spokane last week. Judge Canfield was presented with a gold-headed cane. The property of the Deschutes Irrigation and Power Co., in Oregon, is to be sold at foreclosure sale, the bondholders having just secured an order for the sale from the circuit court in Portland. The claims against the company aggregate $000,0 00. ..J. H. Hildebrant was killed and two Finlanders were seriously injur ed by a premature explosion in the •Mattie Ferguson mine at Basin, Mon tana, Thursday. Hilderbrant had just lighted the fus*l but did not have time to get away before the explosion oc curred."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after, before, late
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.983

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Jeakel' and 'the Yak\nima Indian reservation' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Jeakel' near 'the Yak\nima Indian reservation' around 1910-09-16?
  4. Resolve temporal expressions relative to 1910-09-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 74 [ID: test_en__32]:
  Publication date : 1950-09-30
  Language         : en
  Person  : 'M. L. Wilson, direc\ntor of Extension Work for the\nU. S. Department of Agriculture'  (QID: Q30088046)
  Location: 'Ellendale, Del.'  (QID: Q521614)

  [ARTICLE TEXT — entity markers added]
  "l-HClul) Girl at White House Charlotte Ingram, outstanding 4-H club girl of <LOCATION>Ellendale, Del.</LOCATION> joined with 4-H’er Mary Ann Long of hSelby. Va., and Mrs, Franklin D Roosevelt in present ing the first homemade United Nations Flag to President Harry S. Truman at the White House recently. This ceremony was first of a series of UN flag presentations which wil be made to local of ficials by sewing groups in thous ands of communities throughout the country for flying on October 24th, United Nations Day. White and colored home dem onstration agents will take the lead in ' developing plans for making and presenting the flags, according to M. L. Wilson, direc tor of Extension Work for the U. S. Department of Agriculture."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: M. L. Wilson
    Description: (1885-1969)
    Born: ['+1885-10-23T00:00:00Z']
    Died: ['+1969-10-00T00:00:00Z']
    Birth place: ['Atlantic']
    Death place: ['Washington, D.C.']
  Location Wikidata:
    Label: Ellendale
    Description: town in Sussex County, Delaware, US
    Country: ['United States']
    Located in: ['Sussex County']
    Aliases: {'en': ['Ellendale, Delaware', 'Ellendale, DE']}
    Coordinates: [{'lat': 38.8067, 'lon': -75.4239}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: recently
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.976

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. L. Wilson, direc\ntor of Extension Work for the\nU. S. Department of Agriculture' and 'Ellendale, Del.' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. L. Wilson, direc\ntor of Extension Work for the\nU. S. Department of Agriculture' near 'Ellendale, Del.' around 1950-09-30?
  4. Resolve temporal expressions relative to 1950-09-30. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 75 [ID: test_en__112]:
  Publication date : 1890-10-02
  Language         : en
  Person  : 'Pallas'  (QID: Q37122)
  Location: 'Kansas City'  (QID: Q41819)

  [ARTICLE TEXT — entity markers added]
  "Some Facts About the Approach of the Priests of <PERSON>Pallas</PERSON>. It 19 with pleasure that we are en abled to announce to-day that Pallas Athene and her pries’ly attendants will surely come to <LOCATION>Kansas City</LOCATION>, again, thU year, with even more splendor than has marked three former visits of the goddess. There is little doubt that tbe attendance from tbis city will be large, as the railroads have all granted a very low rate for the occasion. The spectacle of the goddess, and aud the splendor that alwa}*s accompanies her, should be seen by everyone. It is a pleas ure that no one should deny himself. The goddess and her priests have prepared the entertainment, and a city in our midst has been selected for its production. It is frep to everybody. The goddess has maintained ber usual secrecy, this year, on the question of her theme. The subject is said to be of great simplicity and grandeur, however, and it will as suredly be illustrated in a splendid manner. It is expected that Pallas will arrive in New York with her train, about September 29, taking six special coaches on tbe New York Central road, direct to Kansas City. Visitors should reach the scene of the grand entertainment not later than 8 o’clock, on the evening of October 2."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Kansas City
    Description: city in Missouri, United States, that is one of two county seats of Jackson County and the largest city in Missouri
    Country: ['United States']
    Located in: ['Jackson County', 'Cass County', 'Clay County', 'Platte County']
    Aliases: {'en': ['Kansas City, MO', 'KCMO', 'KC', 'Kansas City, Missouri', 'K.C.'], 'de': ['Kansas City, Missouri']}
    Coordinates: [{'lat': 39.05, 'lon': -94.583333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: late, later
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.982

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Pallas' and 'Kansas City' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Pallas' near 'Kansas City' around 1890-10-02?
  4. Resolve temporal expressions relative to 1890-10-02. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 76 [ID: test_en__25]:
  Publication date : 1950-09-30
  Language         : en
  Person  : 'Mrs,\nFranklin D Roosevelt'  (QID: Q83396)
  Location: 'White House'  (QID: Q35525)

  [ARTICLE TEXT — entity markers added]
  "l-HClul) Girl at <LOCATION>White House</LOCATION> Charlotte Ingram, outstanding 4-H club girl of Ellendale, Del. joined with 4-H’er Mary Ann Long of hSelby. Va., and Mrs, Franklin D Roosevelt in present ing the first homemade United Nations Flag to President Harry S. Truman at the White House recently. This ceremony was first of a series of UN flag presentations which wil be made to local of ficials by sewing groups in thous ands of communities throughout the country for flying on October 24th, United Nations Day. White and colored home dem onstration agents will take the lead in ' developing plans for making and presenting the flags, according to M. L. Wilson, direc tor of Extension Work for the U. S. Department of Agriculture."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Eleanor Roosevelt
    Description: American diplomat and activist, First Lady of the United States from 1933 to 1945 (1884–1962)
    Born: ['+1884-10-11T00:00:00Z']
    Died: ['+1962-11-07T00:00:00Z']
    Birth place: ['Manhattan', 'New York City']
    Death place: ['Upper East Side', 'New York City']
    Residences: ['New York City', 'Washington, D.C.', 'Hyde Park', 'Garden City']
    Work locations: ['Washington, D.C.', 'New York City']
  Location Wikidata:
    Label: White House
    Description: official residence and office of the President of the United States
    Country: ['United States']
    Located in: ['Washington, D.C.']
    Aliases: {'en': ['Executive Mansion', "President's Palace", 'Presidential Mansion', "President's House", 'the White House', '1600 Pennsylvania Avenue'], 'fr': ['Maison Blanche', 'State Floor', 'White House', 'The White House'], 'de': ['1600 Pennsylvania Avenue', 'Weisses Haus', 'White House']}
    Coordinates: [{'lat': 38.897777777777776, 'lon': -77.03666666666666}]
  Known person–location links: {"residence": "P551", "work_location": "P937"}

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: recently
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.976

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mrs,\nFranklin D Roosevelt' and 'White House' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mrs,\nFranklin D Roosevelt' near 'White House' around 1950-09-30?
  4. Resolve temporal expressions relative to 1950-09-30. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 77 [ID: test_en__62]:
  Publication date : 1920-01-29
  Language         : en
  Person  : 'L. F. MILLER, Sheriff'  (QID: N/A)
  Location: 'Tennessee'  (QID: Q1509)

  [ARTICLE TEXT — entity markers added]
  "NOTICE. By virtue of a bil of sale issued by Tom Scarlett, Circuit Court Clerk for Putnam County, .ennessee, dated on the 6tU. day of January, 1920, I will expore to sale to tne highest bidder for cash on the 31st day of January, 1920, at 1:0; o’clock, P. M. at the Courthouse door in the Town of Cookeville, the following property, to-wit: A house and lot located in the 19th Civil District of Putnam County, <LOCATION>Tennessee</LOCATION>, containing one acre, more or less, bounded on the east by the lands of J. R. Watson; on the north by the T. C. R. K. Co.; on the west by the lands of Phy; on the south by the lands of J. R. Watson; levied on as the lands of D. Ritten berry, to satisfy a Judgment in favor of P. L. Ramsey ag-ih st him, with interest and all the cost.i of the case. This Jan. 6th, 1920. <PERSON>L. F. MILLER, Sheriff</PERSON>."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Tennessee
    Description: state of the United States of America
    Country: ['Q30']
    Located in: ['Q30']
    Aliases: {'en': ['State of Tennessee', 'TN', 'Tennessee, United States', 'Volunteer State', 'Tenn.', 'US-TN', 'The Volunteer State'], 'fr': ['TN', 'État du Tennessee'], 'de': ['TN']}
    Coordinates: [{'lat': 36, 'lon': -86}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1920" → 1920
      - "1920" → 1920
      - "1920" → 1920
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.946

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'L. F. MILLER, Sheriff' and 'Tennessee' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'L. F. MILLER, Sheriff' near 'Tennessee' around 1920-01-29?
  4. Resolve temporal expressions relative to 1920-01-29. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 78 [ID: test_en__104]:
  Publication date : 1910-09-16
  Language         : en
  Person  : 'J. H. Hildebrant'  (QID: N/A)
  Location: 'Oregon'  (QID: Q824)

  [ARTICLE TEXT — entity markers added]
  "THE NORTHWEST Captain T. D. Bloni, prominent in shipping circles and head of a codfish company, was found in Wright park, in the heart of the city of Tacotna, last, week, with his throat cut. He will probably die. It Is believed he was at tacked by a robber while on the way to the home of a friend. The attack is supposed to have been made some time before midnight and Blom is be lieved to have lain in the park all night. When found his condition was desperate. Several square feet of sod were covered with blood and there were indications of a struggle. In a fire which desrroyed the home of Jos. C. Wendell located in the sub urbs of Portland, Myrtle Wendell, aged 2 years, was burned to death, and Laura Ellis, a domestic, aged IS years, was so badly burned that she died a few minutes after she reached the hospital. It is believed the fire started from the explosion of a gas oline stove. None of the members of the family were home when the fire broke out and it was some time be fore the nearest neighbors could reach the scene, it was then too late to save either of the victims. Two journeyman plumbers out of a job held up and shot Charles Jeakel, a horseshoer of Lewiston, Idaho, through the neck at. Marshal Junction atabout 8 o'clock Saturday night, securing $35 and inflicting a serious wound. The thugs fired three hots at close range at Jeakel, but one taking effect, the other two passing through the victim’s coat at the shoulder. Offering resistance to com mands to stand and deliver caused the use of firearms. Jeakel’s flesh and clothes were powder burnt. Valuable Indian lands on the Yak ima Indian reservation, which were allotted to non-oompetents or held for heirs of dead indians, will be sold by the government on September 26 and October 31. The sale will he made under supervision of S. A. Al. A’oung, the agent in charge. Judge and Mrs. II. E. Canfield were tendered a farewell reception by the members of the Masonic fra ternities of Colfax on the eve of their departure for Spokane last week. Judge Canfield was presented with a gold-headed cane. The property of the Deschutes Irrigation and Power Co., in <LOCATION>Oregon</LOCATION>, is to be sold at foreclosure sale, the bondholders having just secured an order for the sale from the circuit court in Portland. The claims against the company aggregate $000,0 00. ..<PERSON>J. H. Hildebrant</PERSON> was killed and two Finlanders were seriously injur ed by a premature explosion in the •Mattie Ferguson mine at Basin, Mon tana, Thursday. Hilderbrant had just lighted the fus*l but did not have time to get away before the explosion oc curred."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after, before, late
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.983

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'J. H. Hildebrant' and 'Oregon' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'J. H. Hildebrant' near 'Oregon' around 1910-09-16?
  4. Resolve temporal expressions relative to 1910-09-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 79 [ID: test_en__96]:
  Publication date : 1910-09-16
  Language         : en
  Person  : 'Judge Canfield'  (QID: N/A)
  Location: 'Oregon'  (QID: Q824)

  [ARTICLE TEXT — entity markers added]
  "THE NORTHWEST Captain T. D. Bloni, prominent in shipping circles and head of a codfish company, was found in Wright park, in the heart of the city of Tacotna, last, week, with his throat cut. He will probably die. It Is believed he was at tacked by a robber while on the way to the home of a friend. The attack is supposed to have been made some time before midnight and Blom is be lieved to have lain in the park all night. When found his condition was desperate. Several square feet of sod were covered with blood and there were indications of a struggle. In a fire which desrroyed the home of Jos. C. Wendell located in the sub urbs of Portland, Myrtle Wendell, aged 2 years, was burned to death, and Laura Ellis, a domestic, aged IS years, was so badly burned that she died a few minutes after she reached the hospital. It is believed the fire started from the explosion of a gas oline stove. None of the members of the family were home when the fire broke out and it was some time be fore the nearest neighbors could reach the scene, it was then too late to save either of the victims. Two journeyman plumbers out of a job held up and shot Charles Jeakel, a horseshoer of Lewiston, Idaho, through the neck at. Marshal Junction atabout 8 o'clock Saturday night, securing $35 and inflicting a serious wound. The thugs fired three hots at close range at Jeakel, but one taking effect, the other two passing through the victim’s coat at the shoulder. Offering resistance to com mands to stand and deliver caused the use of firearms. Jeakel’s flesh and clothes were powder burnt. Valuable Indian lands on the Yak ima Indian reservation, which were allotted to non-oompetents or held for heirs of dead indians, will be sold by the government on September 26 and October 31. The sale will he made under supervision of S. A. Al. A’oung, the agent in charge. Judge and Mrs. II. E. Canfield were tendered a farewell reception by the members of the Masonic fra ternities of Colfax on the eve of their departure for Spokane last week. <PERSON>Judge Canfield</PERSON> was presented with a gold-headed cane. The property of the Deschutes Irrigation and Power Co., in <LOCATION>Oregon</LOCATION>, is to be sold at foreclosure sale, the bondholders having just secured an order for the sale from the circuit court in Portland. The claims against the company aggregate $000,0 00. ..J. H. Hildebrant was killed and two Finlanders were seriously injur ed by a premature explosion in the •Mattie Ferguson mine at Basin, Mon tana, Thursday. Hilderbrant had just lighted the fus*l but did not have time to get away before the explosion oc curred."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after, before, late
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.983

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Judge Canfield' and 'Oregon' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Judge Canfield' near 'Oregon' around 1910-09-16?
  4. Resolve temporal expressions relative to 1910-09-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 80 [ID: test_en__101]:
  Publication date : 1910-09-16
  Language         : en
  Person  : 'Jos. C. Wendell'  (QID: N/A)
  Location: 'Portland'  (QID: Q6106)

  [ARTICLE TEXT — entity markers added]
  "THE NORTHWEST Captain T. D. Bloni, prominent in shipping circles and head of a codfish company, was found in Wright park, in the heart of the city of Tacotna, last, week, with his throat cut. He will probably die. It Is believed he was at tacked by a robber while on the way to the home of a friend. The attack is supposed to have been made some time before midnight and Blom is be lieved to have lain in the park all night. When found his condition was desperate. Several square feet of sod were covered with blood and there were indications of a struggle. In a fire which desrroyed the home of <PERSON>Jos. C. Wendell</PERSON> located in the sub urbs of <LOCATION>Portland</LOCATION>, Myrtle Wendell, aged 2 years, was burned to death, and Laura Ellis, a domestic, aged IS years, was so badly burned that she died a few minutes after she reached the hospital. It is believed the fire started from the explosion of a gas oline stove. None of the members of the family were home when the fire broke out and it was some time be fore the nearest neighbors could reach the scene, it was then too late to save either of the victims. Two journeyman plumbers out of a job held up and shot Charles Jeakel, a horseshoer of Lewiston, Idaho, through the neck at. Marshal Junction atabout 8 o'clock Saturday night, securing $35 and inflicting a serious wound. The thugs fired three hots at close range at Jeakel, but one taking effect, the other two passing through the victim’s coat at the shoulder. Offering resistance to com mands to stand and deliver caused the use of firearms. Jeakel’s flesh and clothes were powder burnt. Valuable Indian lands on the Yak ima Indian reservation, which were allotted to non-oompetents or held for heirs of dead indians, will be sold by the government on September 26 and October 31. The sale will he made under supervision of S. A. Al. A’oung, the agent in charge. Judge and Mrs. II. E. Canfield were tendered a farewell reception by the members of the Masonic fra ternities of Colfax on the eve of their departure for Spokane last week. Judge Canfield was presented with a gold-headed cane. The property of the Deschutes Irrigation and Power Co., in Oregon, is to be sold at foreclosure sale, the bondholders having just secured an order for the sale from the circuit court in Portland. The claims against the company aggregate $000,0 00. ..J. H. Hildebrant was killed and two Finlanders were seriously injur ed by a premature explosion in the •Mattie Ferguson mine at Basin, Mon tana, Thursday. Hilderbrant had just lighted the fus*l but did not have time to get away before the explosion oc curred."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: after, before, late
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.983

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Jos. C. Wendell' and 'Portland' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Jos. C. Wendell' near 'Portland' around 1910-09-16?
  4. Resolve temporal expressions relative to 1910-09-16. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 81 [ID: test_fr__13]:
  Publication date : 1948-02-23
  Language         : fr
  Person  : 'Lohrer'  (QID: Q543364)
  Location: 'Montchoisi'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Le C. P. Zurich gagne Z le tournoi de hockey sur glace du Centenaire Samedi et dimanche, la patinoire de Monruz était une nouvelle fois entourée d'un nombreux public qui, bravant un froid très vif, suivit avec beaucoup d'intérêt le tournoi de hockey sur glace du Centenaire. Cette manifestation sportive fut pleinement réussie ; nous exprimons tefois un léger regret : pourquoi les trois rencontres ont-elles débuté avec dix à quinze minutes de retard ? Zurich bat <LOCATION>Montchoisi</LOCATION> par 12 à 8 (3-0, 6-3, 3-5) Les joueurs de Lausanne commencèrent par pratiquer un jeu passablement décousu : la défense était très lente et les avants trop individuels. Aussi tait-il une nette différence de classe entre les deux équipes en présence et Zurich, jouant avec beaucoup de décision, put dès l'abord s'octroyer un avantage de trois buts par Urson, Bieler et Ernst. Au cours du second tiers, les Zuricois relâchèrent un peu leur étreinte, alors que peu à peu l'on voyait Montchoisi s'organiser et attaquer avec mordant. Ce tiers fut ainsi assez équilibré, sans toutefois que les Zuricois perdent l'initiative du jeu. Ils marqueront cinq buts par Bieler (2), Urson, Sylvio Rossi, Boiler et Gugenbuhl, tandis que Banninger devait laisser passer trois tirs des Vaudois, deux de Minder et un de Caseel. Renversement de situation au dernier tiers où Montchoisi part résolument a l'attaque en montrant des qualités insoupçonnées. Le Lausannois Hennsler est particulièrement en verve et il marquera trois buts. D'autres attaques très bien menées permettront encore à Beltrami et à Caseel de diminuer l'écart du score. Mais la défense ne parvient pas à contenir les contre-attaques zuricoises et des shots bien placés de Rossi, Ernst et Boiler consolideront ment la victoire des joueurs de la Limmat. Zurich bat Young Sprinters par 10 à 2 (5-0. 1-2. 4-0) Cette partie, disons-le franchement, nous causa une certaine déception. L'on souhaitait une lutte plus équilibrée ; Young Sprinters est certainement capable de mieux résister à Zurich qu'il ne l'a fait hier matin. Nos joueurs, il est vrai, peuvent invoquer une circonstance atténuante. Hugo Delnon était malade et, de ce fait, la première ligne neuchâteloise était désorganisée. En outre. Reto n'apparut sur la glace qu'au début du second tiers. La première partie du jeu vit ainsi une très facile domination de Zurich. Des Bieler. Schubiger, <PERSON>Lohrer</PERSON>, semaient avec joie la panique dans notre camp et marquèrent cinq buts à intervalle régulier. Le second tiers nous fit espérer un redressement de la situation. Reto est là et il semble décider à bien faire. Il s'échappe par deux fois pour marquer deux superbes buts sans que le gardien Banninger puisse esquisser le moindre mouvement de défense. Mais l'équipe neuchâteloise continue à jouer avec une certaine incohérence. Les deux frères Delnon évoluent aveo le talentueux Ulrich, mais cette ligne manque de cohésion et plus rien ne réussira. Sylvio Rossi marquera au contraire un nouveau but. Dernier tiers assez monotone, les Zuricois sont supérieurs et ils parviendront sans trop d'efforts à accentuer leur avance par trois nouveaux buts réussis par Boiler, Gugenbuhl et Urson. Relevons dans le camp neuchâtelois la bonne partie du gardien Perrottet et la rapidité, la décision et le maniement de crosse d'Ulrich. Chez les Zuricois, il faut surtout louer la sûreté d'une défense très solide et un peu rude ; la première ligne formée de Bieler, Lohrer et Schubiger fut de loin la meilleure ligne du tournoi. Young Sprinters bat Montchoisi par 5 à 3 (2-0. 1-2. 2-1) Cette rencontre nous fait oublier la décevante partie disputée le matin. Les deux grands rivaux romands se livrent une lutte très ouverte et variée. Signalons quelques duels épiques entre Hans Cattini, Stucki, les deux frères Delnon et Ulrich. Remise de sa défaillance, notre équipe joua d'une manière digne d'elle-même et elle ne cessa de jouir d'une légère supériorité sur son adversaire. Reto et Othmar Delnon ouvrirent la marque au premier tiers. Les Lausannois placèrent leur effort principal sur le second tiers, mais notre défense formée de Tinembart et du Dr Grether, ainsi que du gardien Perrottet, dans une forme exceptionnelle dimanche, parvinrent à endiguer leurs assauts à l'exception de deux qui permirent à Jansky et à Beltrami de loger le puck au fond de la cage neuchâteloise. Le dernier tiers, au cours duquel le jeu devient assez dur, permit à Young Sprinters de s'assurer une victoire méritée. Jansky profita tout d'abord judicieusement d'une erreur de notre défense, mais Othmar Delnon trompera deux fois encore le gardien Ayer. Relevons l'excellent travail d'Ulrich. Rapide, poussant jusqu'au bout chaque descente, ne considérant jamais perdue une passe, il mena avec brio les attaques de notre notro seconde ligne et certains de ses shots auraient mérité le but. Le palmarès A la suite de ces rencontre, Zurich gagne le tournoi aveo quatre points, suivi de Young Sprinters (2 p.) et Mont _, choisi (0 p.). Lo C. P. Zurich gagne le premier prix du tournoi, la grande distinction du Centenaire et le challenge du tournoi. Young Sprinters obtient la deuxième distinction du Centenaire et le challenge Vuillomenet, récompensant l'équipe jouant avec le plus de fair-play. Quant à Montchoisi, il reçoit la coupe offerte par le cinéma Palace. B. Ad. Une tournée de Young Sprinters en Tchécoslovaquie Notre équipe de hockey sur glace a été invitée à disputer un certain nombre de matches en Tchécoslovaquie, notamment contre Prague et Brno. Elle partira pour ce pays au début du mois de mars et sera renforcée par quelques autres joueurs de ligue nationale A."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Werner Lohrer
    Description: joueur de hockey sur glace suisse
    Born: ['+1917-03-04T00:00:00Z']
    Died: ['+1991-01-01T00:00:00Z']
    Birth place: ['Arosa']
    Death place: ['canton des Grisons']
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.971

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Lohrer' and 'Montchoisi' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Lohrer' near 'Montchoisi' around 1948-02-23?
  4. Resolve temporal expressions relative to 1948-02-23. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 82 [ID: test_fr__130]:
  Publication date : 1928-08-28
  Language         : fr
  Person  : 'M. Scheller'  (QID: N/A)
  Location: 'Mont-Blanc'  (QID: Q583)

  [ARTICLE TEXT — entity markers added]
  "Les accidents Un alpiniste genevois atteint par nn bloc de rocher a lé crâne fracturé et menrt Genève, 27 août. Dimanche, quatre alpinistes genevois membres du Club des grimpeurs s'étaient rendus au <LOCATION>Mont-Blanc</LOCATION> lorsque, vers 17 heures, au chemin qui conduit du glacier du Grand-Mulet à la station de l'Aiguille du Midi, l'un d'eux, Aimé Scheller, 36 ans, sertisseur, fut soudain atteint par un bloc qui s'était détaché et Sii lui fit une grave blessure à la tête, eux de ses compagnons demeurèrent auprès du blessé tandis que l'autre allait quérir du secours. Une colonne, organisée aussitôt, ramena le blessé à la station. <PERSON>M. Scheller</PERSON> reçut les soins d'un médecin français et fut descendu qu'aux Bossons en automobile. De là, il fut dirigé sur l'hôpital cantonal de Genève où il est mort lundi matin des suites d'une fracture du crâne. Il laisse une femme et une fillette. Un char à chien contre une motocyclette * Un petit char attelé d'un chien et appairtenant à M. François Savoy, demeurant à Bossonens (Èribourg), s'est jeté devant une motocyclette montée par M. Max Veraaud, pasteur à Mézières (Vaud), ayant en croupe son frère. La moto fut renversée avec ses deux occupants ; Je Téservoir à benzine s'étant débouché, l'eesence prit feu au contact du phare à acétylène et se communiqua aux vêtements de M. Vernaud. Une application de sacs mouillés l'éteignit. M. Vernaud a les sourcils et les cheveux légèrement brûlés et des contusions. La motocyclette, fort endommagée, a dû être conduite au garage. Grave accident d'automobile Sarnen, 28 août. Une automobile zurichoise occupée par 4 personnes, a fait une chute près de Lungern. Ses occupante ont été projetés hors de la voiture, Mme Jenny-tHirlimann, 35 ans, femme d un entrepreneur de Zurich, a eu la cage thoracique enfoncée. Un médecin qui circulait, par hasard à cet endroit, a fait transporter la malheureuse à Lungern où elle a succombé lundi matin. L'un des occupants a été également contusionné. Une automobile bousculée * Un oamion-automobite de la brasserie Muliler descendant, dimanche, au début de l'après-imidd, de Sainte-Croix SUT Vuitobœuf, a accroché, au premier grand tournant de la route, au-dessous du Château (Saimte-tCroix) une petite torpédo à trois places occupée par deux personnes et qui montait à Sainte-Croix. H l'a lancée avec violence contre le mur bordant la route. Les occupants de l'auto s'en tirent avec des blessures superficielles ; ils sont rentrés à Sainte-Croix, mais leur voiture gravement endommagée a dû être remorquée au grand garage des Remparts à Yverdon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Scheller' and 'Mont-Blanc' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Scheller' near 'Mont-Blanc' around 1928-08-28?
  4. Resolve temporal expressions relative to 1928-08-28. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 83 [ID: test_fr__131]:
  Publication date : 1928-08-28
  Language         : fr
  Person  : 'M. François Savoy'  (QID: N/A)
  Location: 'Genève'  (QID: Q71)

  [ARTICLE TEXT — entity markers added]
  "Les accidents Un alpiniste genevois atteint par nn bloc de rocher a lé crâne fracturé et menrt <LOCATION>Genève</LOCATION>, 27 août. Dimanche, quatre alpinistes genevois membres du Club des grimpeurs s'étaient rendus au Mont-Blanc lorsque, vers 17 heures, au chemin qui conduit du glacier du Grand-Mulet à la station de l'Aiguille du Midi, l'un d'eux, Aimé Scheller, 36 ans, sertisseur, fut soudain atteint par un bloc qui s'était détaché et Sii lui fit une grave blessure à la tête, eux de ses compagnons demeurèrent auprès du blessé tandis que l'autre allait quérir du secours. Une colonne, organisée aussitôt, ramena le blessé à la station. M. Scheller reçut les soins d'un médecin français et fut descendu qu'aux Bossons en automobile. De là, il fut dirigé sur l'hôpital cantonal de Genève où il est mort lundi matin des suites d'une fracture du crâne. Il laisse une femme et une fillette. Un char à chien contre une motocyclette * Un petit char attelé d'un chien et appairtenant à <PERSON>M. François Savoy</PERSON>, demeurant à Bossonens (Èribourg), s'est jeté devant une motocyclette montée par M. Max Veraaud, pasteur à Mézières (Vaud), ayant en croupe son frère. La moto fut renversée avec ses deux occupants ; Je Téservoir à benzine s'étant débouché, l'eesence prit feu au contact du phare à acétylène et se communiqua aux vêtements de M. Vernaud. Une application de sacs mouillés l'éteignit. M. Vernaud a les sourcils et les cheveux légèrement brûlés et des contusions. La motocyclette, fort endommagée, a dû être conduite au garage. Grave accident d'automobile Sarnen, 28 août. Une automobile zurichoise occupée par 4 personnes, a fait une chute près de Lungern. Ses occupante ont été projetés hors de la voiture, Mme Jenny-tHirlimann, 35 ans, femme d un entrepreneur de Zurich, a eu la cage thoracique enfoncée. Un médecin qui circulait, par hasard à cet endroit, a fait transporter la malheureuse à Lungern où elle a succombé lundi matin. L'un des occupants a été également contusionné. Une automobile bousculée * Un oamion-automobite de la brasserie Muliler descendant, dimanche, au début de l'après-imidd, de Sainte-Croix SUT Vuitobœuf, a accroché, au premier grand tournant de la route, au-dessous du Château (Saimte-tCroix) une petite torpédo à trois places occupée par deux personnes et qui montait à Sainte-Croix. H l'a lancée avec violence contre le mur bordant la route. Les occupants de l'auto s'en tirent avec des blessures superficielles ; ils sont rentrés à Sainte-Croix, mais leur voiture gravement endommagée a dû être remorquée au grand garage des Remparts à Yverdon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. François Savoy' and 'Genève' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. François Savoy' near 'Genève' around 1928-08-28?
  4. Resolve temporal expressions relative to 1928-08-28. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 84 [ID: test_fr__11]:
  Publication date : 1948-02-23
  Language         : fr
  Person  : 'Caseel'  (QID: N/A)
  Location: 'Montchoisi'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Le C. P. Zurich gagne Z le tournoi de hockey sur glace du Centenaire Samedi et dimanche, la patinoire de Monruz était une nouvelle fois entourée d'un nombreux public qui, bravant un froid très vif, suivit avec beaucoup d'intérêt le tournoi de hockey sur glace du Centenaire. Cette manifestation sportive fut pleinement réussie ; nous exprimons tefois un léger regret : pourquoi les trois rencontres ont-elles débuté avec dix à quinze minutes de retard ? Zurich bat <LOCATION>Montchoisi</LOCATION> par 12 à 8 (3-0, 6-3, 3-5) Les joueurs de Lausanne commencèrent par pratiquer un jeu passablement décousu : la défense était très lente et les avants trop individuels. Aussi tait-il une nette différence de classe entre les deux équipes en présence et Zurich, jouant avec beaucoup de décision, put dès l'abord s'octroyer un avantage de trois buts par Urson, Bieler et Ernst. Au cours du second tiers, les Zuricois relâchèrent un peu leur étreinte, alors que peu à peu l'on voyait Montchoisi s'organiser et attaquer avec mordant. Ce tiers fut ainsi assez équilibré, sans toutefois que les Zuricois perdent l'initiative du jeu. Ils marqueront cinq buts par Bieler (2), Urson, Sylvio Rossi, Boiler et Gugenbuhl, tandis que Banninger devait laisser passer trois tirs des Vaudois, deux de Minder et un de <PERSON>Caseel</PERSON>. Renversement de situation au dernier tiers où Montchoisi part résolument a l'attaque en montrant des qualités insoupçonnées. Le Lausannois Hennsler est particulièrement en verve et il marquera trois buts. D'autres attaques très bien menées permettront encore à Beltrami et à Caseel de diminuer l'écart du score. Mais la défense ne parvient pas à contenir les contre-attaques zuricoises et des shots bien placés de Rossi, Ernst et Boiler consolideront ment la victoire des joueurs de la Limmat. Zurich bat Young Sprinters par 10 à 2 (5-0. 1-2. 4-0) Cette partie, disons-le franchement, nous causa une certaine déception. L'on souhaitait une lutte plus équilibrée ; Young Sprinters est certainement capable de mieux résister à Zurich qu'il ne l'a fait hier matin. Nos joueurs, il est vrai, peuvent invoquer une circonstance atténuante. Hugo Delnon était malade et, de ce fait, la première ligne neuchâteloise était désorganisée. En outre. Reto n'apparut sur la glace qu'au début du second tiers. La première partie du jeu vit ainsi une très facile domination de Zurich. Des Bieler. Schubiger, Lohrer, semaient avec joie la panique dans notre camp et marquèrent cinq buts à intervalle régulier. Le second tiers nous fit espérer un redressement de la situation. Reto est là et il semble décider à bien faire. Il s'échappe par deux fois pour marquer deux superbes buts sans que le gardien Banninger puisse esquisser le moindre mouvement de défense. Mais l'équipe neuchâteloise continue à jouer avec une certaine incohérence. Les deux frères Delnon évoluent aveo le talentueux Ulrich, mais cette ligne manque de cohésion et plus rien ne réussira. Sylvio Rossi marquera au contraire un nouveau but. Dernier tiers assez monotone, les Zuricois sont supérieurs et ils parviendront sans trop d'efforts à accentuer leur avance par trois nouveaux buts réussis par Boiler, Gugenbuhl et Urson. Relevons dans le camp neuchâtelois la bonne partie du gardien Perrottet et la rapidité, la décision et le maniement de crosse d'Ulrich. Chez les Zuricois, il faut surtout louer la sûreté d'une défense très solide et un peu rude ; la première ligne formée de Bieler, Lohrer et Schubiger fut de loin la meilleure ligne du tournoi. Young Sprinters bat Montchoisi par 5 à 3 (2-0. 1-2. 2-1) Cette rencontre nous fait oublier la décevante partie disputée le matin. Les deux grands rivaux romands se livrent une lutte très ouverte et variée. Signalons quelques duels épiques entre Hans Cattini, Stucki, les deux frères Delnon et Ulrich. Remise de sa défaillance, notre équipe joua d'une manière digne d'elle-même et elle ne cessa de jouir d'une légère supériorité sur son adversaire. Reto et Othmar Delnon ouvrirent la marque au premier tiers. Les Lausannois placèrent leur effort principal sur le second tiers, mais notre défense formée de Tinembart et du Dr Grether, ainsi que du gardien Perrottet, dans une forme exceptionnelle dimanche, parvinrent à endiguer leurs assauts à l'exception de deux qui permirent à Jansky et à Beltrami de loger le puck au fond de la cage neuchâteloise. Le dernier tiers, au cours duquel le jeu devient assez dur, permit à Young Sprinters de s'assurer une victoire méritée. Jansky profita tout d'abord judicieusement d'une erreur de notre défense, mais Othmar Delnon trompera deux fois encore le gardien Ayer. Relevons l'excellent travail d'Ulrich. Rapide, poussant jusqu'au bout chaque descente, ne considérant jamais perdue une passe, il mena avec brio les attaques de notre notro seconde ligne et certains de ses shots auraient mérité le but. Le palmarès A la suite de ces rencontre, Zurich gagne le tournoi aveo quatre points, suivi de Young Sprinters (2 p.) et Mont _, choisi (0 p.). Lo C. P. Zurich gagne le premier prix du tournoi, la grande distinction du Centenaire et le challenge du tournoi. Young Sprinters obtient la deuxième distinction du Centenaire et le challenge Vuillomenet, récompensant l'équipe jouant avec le plus de fair-play. Quant à Montchoisi, il reçoit la coupe offerte par le cinéma Palace. B. Ad. Une tournée de Young Sprinters en Tchécoslovaquie Notre équipe de hockey sur glace a été invitée à disputer un certain nombre de matches en Tchécoslovaquie, notamment contre Prague et Brno. Elle partira pour ce pays au début du mois de mars et sera renforcée par quelques autres joueurs de ligue nationale A."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.971

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Caseel' and 'Montchoisi' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Caseel' near 'Montchoisi' around 1948-02-23?
  4. Resolve temporal expressions relative to 1948-02-23. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 85 [ID: test_fr__234]:
  Publication date : 1981-02-18
  Language         : fr
  Person  : 'Mme Blanc'  (QID: N/A)
  Location: 'Berne'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "SUISSE dernière COMMISSION DES ETATS La Suissesse mariée garderait son droit de cité <LOCATION>Berne</LOCATION>, 17 (ATS).-La Commission du conseil des Etats chargée d'examiner le nouveau droit matrimonial, qui a terminé ses travaux mardi à Berne, a modifié sur quelques points le projet du Conseil fédéral.Elle a cependant accepté dans ses grandes lignes le projet gouvernemental et notamment le remplacement du régime actuel de l'union des biens par celui de la participation aux acquêts.Cet objet sera traité par le parlement au mois de mars.Au sujet du nom des époux, la Commission rejoint le Conseil fédéral dans son refus d'accorder le droit d'option qui permettrait aux fiancés de choisir le nom de l'épouse comme nom de famille.Mais la femme aura le droit non seulement de faire suivre son nom (Favre-Blanc), mais aussi de le faire précéder (<PERSON>Mme Blanc</PERSON> épouse Favre).La Commission n'a pas retenu la possibilité de l'option en raison de la tradition qui existe dans notre pays.En Allemagne fédérale, où le choix existe, seuls 4 % des époux en font usage.La nouvelle réglementation suisse facilitera- cependant l'adoption éventuelle par les fiancés, avant le mariage, du nom de la femme comme nom de famille.Mais il faudra de bonnes raisons pour l'autoriser (nom à consonnance étrangère, nom connu dans le commerce, la politique, etc).En ce qui concerne le droit de cité, la femme recevra, par le mariage, le droit de cité du mari mais sans perdre le sien.Une majorité s'est formée dans la Commission en faveur de cette solution."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.993

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mme Blanc' and 'Berne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mme Blanc' near 'Berne' around 1981-02-18?
  4. Resolve temporal expressions relative to 1981-02-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 86 [ID: test_fr__92]:
  Publication date : 1968-04-08
  Language         : fr
  Person  : 'Hofer'  (QID: Q60446519)
  Location: 'Zurich'  (QID: Q72)

  [ARTICLE TEXT — entity markers added]
  "Bioiiey remporte le Tour du Léman à Genève Deux importantes épreuves pour nos amateurs d'élite A l'échelon des amateurs-elites, le weekend était d'importance à Genève. Oscar Plattner, grand responsable de cette catégorie d'éventuels futurs champions, avait délégué ses pouvoirs à Gilbert Perrenoud, afin qu'il suive très attentivement ce qui se passait sur les routes. Le Comité national a, en effet, l'intention très arrêtée de mettre sur pied la meilleure équipe possible pour le Tour de l'Avenir, les Jeux olympiques et les championnats du monde. Tout un programme de sélection a ainsi été mis au point. Dimanche à midi, Gilbert Perrenoud se déclarait enchanté de ce qu'il avait vu. Non pas que l'on puisse immédiatement dire que les coureurs suisses sont en forme, mais les sujets de satisfaction ne manquaient pas : « on voit que nous sommes dans une année importante, une année où les voyages et les honneurs seront nombreux. Il y a l'Uruguay, le Mexique, des médailles à revendre. C'est pourquoi nos meilleurs coureurs se sont préparés de belle façon, c'est pourquoi aussi de nombreux jeunes frappent à la porte .. En fait, ces deux courses genevoises ont permis de nombreux enseignements. Animées toutes deux, courues assez rapidement, elles se sont révélées d'une excellente qualité. D'OESCHGER... Samedi après-midi, sur un circuit de seize kiolmètres à parcourir huit fois, quelque soixante-cinq coureurs prirent le départ. Sous le soleil, qui allait bientôt disparaître, et faire place à un violent orage. L'échappée, la bonne, vint très rapidement. Au deuxième tour déjà, après qu'un « faux départ » eut lieu, à savoir une erreur de parcours annulant les efforts des premiers audacieux. Fait assez rare, la course fut stoppée à 9 km 400 de son premier départ puis relancée. C'est alors que l'un des Belges invités, froidement, tenta de partir. Il y parvint en compagnie de Rub, d'Oeschger, de Schnetzler, le champion de Suisse, von Arx, Fischer, et les Romands Behier (Moudon), Regamey (Yverdon) et Vaucher (Lausanne). Cahin-caha, sur de petites routes, étroites et sinueuses, cette échappée prit quelque avance. Sur le peloton tout d'abord, sur un groupe de contre-attaque par la suite, qui allait faire sa jonction. D'ailleurs, il ne resta plus que ces hommes en course... Les autres pensaient au tour du lac du lendemain, et se retiraient II y a encore quelques audacieux : Schnetzler, Spannagel, Birrer et Weber. Mais leurs tentatives solitaires furent réduites à néant. Et sur la fin, le peloton se scinda en deux. . . . A BIOLLEY Ce tour du lac — doyenne des épreuves cyclistes, qui en était hier à sa 76 mc édition — eut un déroulement assez rare. Daniel Biolley, de Fribourg, l'expliqua une fois passée, en vainqueur, la ligne d' arrivée : « C'est mon sixième- tour du lac. Et j'avais jusqu'ici constaté que jamais une échappée partie de loin ne réussissait Aussi je n'ai pas mené depuis Versoix (km 10) où nous sommes partis. Mais comme à Evian, en abordant le col de Vinzier, nous avions plus de cinq minutes sur nos poursuivants, et plus de dix sur le peloton _, je me suis lancé dans la bagarre. » La course partit en effet très tôt : Brunner — qui allait vite disparaître — Lier, <PERSON>Hofer</PERSON> et Grin s'en allèrent vers l'entrée de l'autoroute Genève-Lausanne. Rapidement Biolley, Angelucci, Elliker, Kalt, Rennhard, Rutchmann, Thalmann, Reusser, Adam, Schneider et Melliflio les rejoignirent Et, au gré des kilomètres, de la forme de certains ou de divers ennuis mécaniques, il resta dix hommes ensemble à Evian, dont quatre partirent bien vite dès les premières côtes de la seule difficulté de la journée, quatre qui restèrent ensemble jusqu'à l'arrivée où se produisit un petit drame : Lier sprinta, gagna, mais ne savait pas qu'il y avait un tour et la distance à faire... Biolley passa donc, de même que Rennhardt. Les deux coéquipiers (d'Allegro) avaient des mines patibulaires à l'arrivée. Lier pleurait et Biolley n'était pas plus content que cela : « La victoire lui revenait il avait fait une grosse part de travail. Mais je ne pouvais pas me relever, car Rennhard avait passé. Serge DOURNOW CLASSEMENT DU GRAND PRIX DE MEINIER 1. Oeschger (Oberhofen), les 128 km en 3 h 32'13 " ; 2. Rub (Bmgg) ; 3. Fischer (Brugg) ; 4. Binggeli (Genève ; 5. Regamey (Yverdon). CLASSEMENT DU TOUR DU LÉMAN 1. Biolley (Fribourg), les 187 km en 4 h 30'36 " ; 2. Rennhard (Brugg) ; 3. Lier (Affoltern) ; 4. Thalmann (Meznau), même temps ; 5. Rutschmann (Seuzach), à 3'32 " ; 6. Hofer (Berne) ; 7. Kalt (<LOCATION>Zurich</LOCATION>) ; 8. Elliker (Urdorf) ; 9. Reusser (Brugg), même temps ; 10. Peter (Zurich), à 7'40 "."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Zurich
    Description: ville la plus peuplée de Suisse et chef-lieu du canton de Zurich
    Country: ['Suisse', 'ancienne Confédération suisse', 'République helvétique', 'Q39']
    Located in: ['district de Zurich']
    Aliases: {'en': ['City of Zurich', 'ZH', 'Stadt Zürich', 'Zurich, Switzerland', 'Zürich'], 'fr': ['Zürich', 'Zuerich', 'ville de Zurich'], 'de': ['Stadt Zürich'], 'lb': ['Zürech', 'Stad Zürich']}
    Coordinates: [{'lat': 47.37444444444444, 'lon': 8.54111111111111}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.959

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Hofer' and 'Zurich' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Hofer' near 'Zurich' around 1968-04-08?
  4. Resolve temporal expressions relative to 1968-04-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 87 [ID: test_fr__55]:
  Publication date : 1936-01-15
  Language         : fr
  Person  : 'Compain'  (QID: N/A)
  Location: 'salle de la Justepaix'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Deux nouvelles inculpationsfrappent le surveillantcomplaisant valletM. Hude, juge d'instruction, a in¬ culpé hier le surveillant Vallet de cor¬ ruption de fonctionnaire, faux et usa¬ ge de faux. Tout d'abord, l'expertGebelin avait établi que tous les or¬ dres d'extraction, aussi bien ceux quisont entièrement faux que ceux quin'ont été que maquillés par additiond’un nom, avaient été préparés parla main du gardien de la Souricière.En particulier, l'ordre du 2 octobrequi permit à Pélissier de s’évader lelendemain et qui fut retrouvé le 4 à laSanté, est en entier de lui. Par ail¬ leurs, le petit carnet saisi sur Chris¬ tiane Pélissier établit qu’il avaittouché des sommes d'argent pour lalocation à la journée, de la cellulenuméro 10. Plusieurs autres dames,d'ailleurs, avec leurs maris détenus,ont contribué à alimenter la caissedu geôlier « compatissant ».Le versement des cotisationsd'assurances socialespour les chauffeurs de taxisLe ministère du Travail nous com¬ munique la note suivante :En application de l'article premier,paragraphe 3, du décret-loi du 28 oc¬ tobre 1935, modifiant le régime desAssurances sociales, les conducteursde voitures publiques, dont l'exploi¬ tation est assujettie à des tarifs detransport fixés par l'autorité publi¬ que, sont soumis au régime de l'assu¬ rance obligatoire, dès l'instant queleur rémunération n'excède pas lechiffre-limite prévu pour le bénéficede cette assurance.Les cotisations patronale et ouvriè¬ re sont dues depuis le premier jan¬ vier 1936.Conformément à l'article 3 de l'ar¬ rêté du 27 décembre 1935 paru auJournal Officiel du 29 décembre, lespourboires des intéressés, qui doi¬ vent entrer en compte pour la déter¬ mination de leur rémunération, se¬ ront évalués par des conventions col¬ lectives de travail, et, à défaut detelles conventions, par arrêtés du mi¬ nistre du Travail.L'unité syndicalechez les travailleurs de l'EtatLes sections de la Fédération uni¬ fiée des travailleurs de l'Etat (artil¬ lerie, poudreries, magasins adminis¬ tratifs, génie et aéronautique, em¬ ployés et agents de maîtrise, marinemilitaire, arts et métiers) ont tenuhier leurs assises patriculières dansles différentes salles de la Bourse duTravail.Voici les résultats définitifs du votepar mandats que le congrès de fusiondes deux Fédérations confédérée etunitaire avait été appelé à émettrelundi soir au sujet du cumul desfonctions syndicales et des mandatspolitiques. Contre : 287 voix ; pour :80 voix ; abstentions : 17 voix.PARTIS ET LIGUESGroupe des étudiants radicauxLa réunion du groupe des étu¬ diants radicaux de Paris aura lieuaujourd'hui mercredi, à 21 heures,au café « Chez Emile », 40, rue Ga¬ lande, et 10, rue Fouarre (angle desdeux rues).Fédération nationaledes Libres PenseursFédération de la Seine. — La com¬ mission spéciale d’unité d’action seréunira demain jeudi, à 21 heures,local habituel, rue de Châteaudun.Les responsables voudront bien êtreprésents.Parti radical-socialisteVersailles. — Les Comités radicaux¬ socialistes de la deuxième circons¬ cription de Versailles, réunis à Pois¬ sy, ont procédé à la constitution dila Fédération des Comités de cettecirconscription.Le bureau élu de la Fédération estainsi constitué : Président : RougelotHenri ; Secrétaire : Durand Fernand;Trésorier : Fourlon Pierre.Un ordre du jour a été voté décla¬ rant impossible le maintien de mi¬ nistres radicaux dans le gouverne¬ ment ; et demandant au bureau duComité Exécutif de proposer à laplus prochaine réunion du Comité lerefus de toute collaboration avec legouvernement actuel.Libre PenséeNous sommes heureux d'informer lepublic qu’une permanence de la 14esection de la Libre Pensée est ou¬ verte au numéro 47 de la rue Bé¬ nard (XIVe), à la Librairie des Tra¬ vailleurs.Le but de la Libre Pensée est de dé¬ velopper chez tous l’esprit critique etl'amour du libre examen, sans dis¬ tinction de parti, et de grouper dansson sein ceux qui se réclament de cehaut idéal. L’époque que nous vivonsest corrompue depuis des siècles parles croyances religieuses et leur amiedévouée Sa Majesté l'Argent qui gou¬ vernent le monde à leur seul bénéfice.Il est de notre devoir, pour nos en¬ fants et pour nous-mêmes, d'arracherce voile de l'au-delà et de mettre lemonde en face de ses nécessités réel¬ les. Chacun le peut dans son humblerôle ; la laïcité peut nous aider. Grou¬ pons-nous pour la défendre.Front populaireEpernay. — Dimanche après-midi,M. Eugène Frot, ancien ministre, adonné en la salle des fêtes d'Epernay(Marne) une conférence sous les aus¬ pices de la Ligue des Droits del'Homme et du Comité du Front Po¬ pulaire. Plus de 1.200 personnes yassistaient dont plusieurs élus radi¬ caux et socialistes de la région. M.Guerry, président, assisté de MM.Morange et Guen.MM. Eugène Frot, député, ancienministre, Bossus, conseiller munici¬ pal communiste de Paris, et EmileKahn, secrétaire général de la Liguedes Droits de l'Homme, ont pris suc¬ cessivement la parole très chaleu¬ reusement applaudis.La réunion se termina sans inci¬ dent. Dans la nuit, un membre de laSolidarité Française qui avait tentéde peindre des inscriptions injurieu¬ ses sur les murs de la Salle des Fêtesavait été surpris par la police. Il dé¬ clara avoir été inspiré dans son gestepar un discours du fils de M. Princequ'il avait entendu précédemment..XIVe arr. — Pour la constitutiondes Comités de défense de la Répu¬ blique, trois grands meetings inaugu¬ raux sont organisés par le Front po¬ pulaire du 14e, aujourd'hui mercredi:111, rue du Château ; 115, rue Didot,1, avenue de la Porte-d'Orléans.Trente orateurs inscrits, dontRouffianges, Biquard, Croizat, Mau¬ vais, Paul Marcel, Graziani, MauriceLacroix, Létrange, Mension, etc...Ligue pour le Droit au Travailet le Progrès SocialVe arr — Une grande conférencesera donnée le vendredi 17 janvier,à 21 heures, à la Sorbonne, amphi¬ théâtre Richelieu, par Joseph Dubois,sur « L'Economie soviétique maî¬ tresse de ses destins ». Jacques Du¬ boin entretiendra ensuite les auditeursdu « Problème français ».Les cartes donnant droit aux placesréservées sont à la disposition des au¬ diteurs, au « Droit au Travail », 14,rue FavartViroflay. — Sous les auspices de lasection locaie des Droits de l'Homme,une grande réunion de propagandeaura lieu demain jeudi, à 21 heures,à la salie Robie, 134, route Navoù nos amis Chesneau et Ra,Martin exposeront les vérités dmiques diffusées par le « DroitTous nos amis et sympathisantssont cordialement invitésMaisons-Alfort. — L'Intersection dcanton de Charenton organisedredi 17 janvier, à 21 heures, ugrande réunion à la mairie dusons-Alfort, <LOCATION>salle de la Justepaix</LOCATION>. Nos camarades <PERSON>Compain</PERSON> mond Martin y parleront de « la révo¬ lution économique actuelle »."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1935" → 1935
      - "1936" → 1936
      - "1935" → 1935
    Temporal signal words: aujourd'hui, hier, ancien, plus, après
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.969

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Compain' and 'salle de la Justepaix' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Compain' near 'salle de la Justepaix' around 1936-01-15?
  4. Resolve temporal expressions relative to 1936-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 88 [ID: test_fr__96]:
  Publication date : 1968-04-08
  Language         : fr
  Person  : 'Vaucher'  (QID: Q57662412)
  Location: 'Yverdon'  (QID: Q63946)

  [ARTICLE TEXT — entity markers added]
  "Bioiiey remporte le Tour du Léman à Genève Deux importantes épreuves pour nos amateurs d'élite A l'échelon des amateurs-elites, le weekend était d'importance à Genève. Oscar Plattner, grand responsable de cette catégorie d'éventuels futurs champions, avait délégué ses pouvoirs à Gilbert Perrenoud, afin qu'il suive très attentivement ce qui se passait sur les routes. Le Comité national a, en effet, l'intention très arrêtée de mettre sur pied la meilleure équipe possible pour le Tour de l'Avenir, les Jeux olympiques et les championnats du monde. Tout un programme de sélection a ainsi été mis au point. Dimanche à midi, Gilbert Perrenoud se déclarait enchanté de ce qu'il avait vu. Non pas que l'on puisse immédiatement dire que les coureurs suisses sont en forme, mais les sujets de satisfaction ne manquaient pas : « on voit que nous sommes dans une année importante, une année où les voyages et les honneurs seront nombreux. Il y a l'Uruguay, le Mexique, des médailles à revendre. C'est pourquoi nos meilleurs coureurs se sont préparés de belle façon, c'est pourquoi aussi de nombreux jeunes frappent à la porte .. En fait, ces deux courses genevoises ont permis de nombreux enseignements. Animées toutes deux, courues assez rapidement, elles se sont révélées d'une excellente qualité. D'OESCHGER... Samedi après-midi, sur un circuit de seize kiolmètres à parcourir huit fois, quelque soixante-cinq coureurs prirent le départ. Sous le soleil, qui allait bientôt disparaître, et faire place à un violent orage. L'échappée, la bonne, vint très rapidement. Au deuxième tour déjà, après qu'un « faux départ » eut lieu, à savoir une erreur de parcours annulant les efforts des premiers audacieux. Fait assez rare, la course fut stoppée à 9 km 400 de son premier départ puis relancée. C'est alors que l'un des Belges invités, froidement, tenta de partir. Il y parvint en compagnie de Rub, d'Oeschger, de Schnetzler, le champion de Suisse, von Arx, Fischer, et les Romands Behier (Moudon), Regamey (<LOCATION>Yverdon</LOCATION>) et <PERSON>Vaucher</PERSON> (Lausanne). Cahin-caha, sur de petites routes, étroites et sinueuses, cette échappée prit quelque avance. Sur le peloton tout d'abord, sur un groupe de contre-attaque par la suite, qui allait faire sa jonction. D'ailleurs, il ne resta plus que ces hommes en course... Les autres pensaient au tour du lac du lendemain, et se retiraient II y a encore quelques audacieux : Schnetzler, Spannagel, Birrer et Weber. Mais leurs tentatives solitaires furent réduites à néant. Et sur la fin, le peloton se scinda en deux. . . . A BIOLLEY Ce tour du lac — doyenne des épreuves cyclistes, qui en était hier à sa 76 mc édition — eut un déroulement assez rare. Daniel Biolley, de Fribourg, l'expliqua une fois passée, en vainqueur, la ligne d' arrivée : « C'est mon sixième- tour du lac. Et j'avais jusqu'ici constaté que jamais une échappée partie de loin ne réussissait Aussi je n'ai pas mené depuis Versoix (km 10) où nous sommes partis. Mais comme à Evian, en abordant le col de Vinzier, nous avions plus de cinq minutes sur nos poursuivants, et plus de dix sur le peloton _, je me suis lancé dans la bagarre. » La course partit en effet très tôt : Brunner — qui allait vite disparaître — Lier, Hofer et Grin s'en allèrent vers l'entrée de l'autoroute Genève-Lausanne. Rapidement Biolley, Angelucci, Elliker, Kalt, Rennhard, Rutchmann, Thalmann, Reusser, Adam, Schneider et Melliflio les rejoignirent Et, au gré des kilomètres, de la forme de certains ou de divers ennuis mécaniques, il resta dix hommes ensemble à Evian, dont quatre partirent bien vite dès les premières côtes de la seule difficulté de la journée, quatre qui restèrent ensemble jusqu'à l'arrivée où se produisit un petit drame : Lier sprinta, gagna, mais ne savait pas qu'il y avait un tour et la distance à faire... Biolley passa donc, de même que Rennhardt. Les deux coéquipiers (d'Allegro) avaient des mines patibulaires à l'arrivée. Lier pleurait et Biolley n'était pas plus content que cela : « La victoire lui revenait il avait fait une grosse part de travail. Mais je ne pouvais pas me relever, car Rennhard avait passé. Serge DOURNOW CLASSEMENT DU GRAND PRIX DE MEINIER 1. Oeschger (Oberhofen), les 128 km en 3 h 32'13 " ; 2. Rub (Bmgg) ; 3. Fischer (Brugg) ; 4. Binggeli (Genève ; 5. Regamey (Yverdon). CLASSEMENT DU TOUR DU LÉMAN 1. Biolley (Fribourg), les 187 km en 4 h 30'36 " ; 2. Rennhard (Brugg) ; 3. Lier (Affoltern) ; 4. Thalmann (Meznau), même temps ; 5. Rutschmann (Seuzach), à 3'32 " ; 6. Hofer (Berne) ; 7. Kalt (Zurich) ; 8. Elliker (Urdorf) ; 9. Reusser (Brugg), même temps ; 10. Peter (Zurich), à 7'40 "."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Alcide Vaucher
    Description: coureur cycliste suisse
    Born: ['+1934-04-19T00:00:00Z']
    Died: ['+2022-06-03T00:00:00Z']
    Birth place: ['Q70090']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.959

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Vaucher' and 'Yverdon' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Vaucher' near 'Yverdon' around 1968-04-08?
  4. Resolve temporal expressions relative to 1968-04-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 89 [ID: test_fr__51]:
  Publication date : 1936-01-15
  Language         : fr
  Person  : 'MauriceLacroix'  (QID: Q3300985)
  Location: 'Ve arr'  (QID: Q238723)

  [ARTICLE TEXT — entity markers added]
  "Deux nouvelles inculpationsfrappent le surveillantcomplaisant valletM. Hude, juge d'instruction, a in¬ culpé hier le surveillant Vallet de cor¬ ruption de fonctionnaire, faux et usa¬ ge de faux. Tout d'abord, l'expertGebelin avait établi que tous les or¬ dres d'extraction, aussi bien ceux quisont entièrement faux que ceux quin'ont été que maquillés par additiond’un nom, avaient été préparés parla main du gardien de la Souricière.En particulier, l'ordre du 2 octobrequi permit à Pélissier de s’évader lelendemain et qui fut retrouvé le 4 à laSanté, est en entier de lui. Par ail¬ leurs, le petit carnet saisi sur Chris¬ tiane Pélissier établit qu’il avaittouché des sommes d'argent pour lalocation à la journée, de la cellulenuméro 10. Plusieurs autres dames,d'ailleurs, avec leurs maris détenus,ont contribué à alimenter la caissedu geôlier « compatissant ».Le versement des cotisationsd'assurances socialespour les chauffeurs de taxisLe ministère du Travail nous com¬ munique la note suivante :En application de l'article premier,paragraphe 3, du décret-loi du 28 oc¬ tobre 1935, modifiant le régime desAssurances sociales, les conducteursde voitures publiques, dont l'exploi¬ tation est assujettie à des tarifs detransport fixés par l'autorité publi¬ que, sont soumis au régime de l'assu¬ rance obligatoire, dès l'instant queleur rémunération n'excède pas lechiffre-limite prévu pour le bénéficede cette assurance.Les cotisations patronale et ouvriè¬ re sont dues depuis le premier jan¬ vier 1936.Conformément à l'article 3 de l'ar¬ rêté du 27 décembre 1935 paru auJournal Officiel du 29 décembre, lespourboires des intéressés, qui doi¬ vent entrer en compte pour la déter¬ mination de leur rémunération, se¬ ront évalués par des conventions col¬ lectives de travail, et, à défaut detelles conventions, par arrêtés du mi¬ nistre du Travail.L'unité syndicalechez les travailleurs de l'EtatLes sections de la Fédération uni¬ fiée des travailleurs de l'Etat (artil¬ lerie, poudreries, magasins adminis¬ tratifs, génie et aéronautique, em¬ ployés et agents de maîtrise, marinemilitaire, arts et métiers) ont tenuhier leurs assises patriculières dansles différentes salles de la Bourse duTravail.Voici les résultats définitifs du votepar mandats que le congrès de fusiondes deux Fédérations confédérée etunitaire avait été appelé à émettrelundi soir au sujet du cumul desfonctions syndicales et des mandatspolitiques. Contre : 287 voix ; pour :80 voix ; abstentions : 17 voix.PARTIS ET LIGUESGroupe des étudiants radicauxLa réunion du groupe des étu¬ diants radicaux de Paris aura lieuaujourd'hui mercredi, à 21 heures,au café « Chez Emile », 40, rue Ga¬ lande, et 10, rue Fouarre (angle desdeux rues).Fédération nationaledes Libres PenseursFédération de la Seine. — La com¬ mission spéciale d’unité d’action seréunira demain jeudi, à 21 heures,local habituel, rue de Châteaudun.Les responsables voudront bien êtreprésents.Parti radical-socialisteVersailles. — Les Comités radicaux¬ socialistes de la deuxième circons¬ cription de Versailles, réunis à Pois¬ sy, ont procédé à la constitution dila Fédération des Comités de cettecirconscription.Le bureau élu de la Fédération estainsi constitué : Président : RougelotHenri ; Secrétaire : Durand Fernand;Trésorier : Fourlon Pierre.Un ordre du jour a été voté décla¬ rant impossible le maintien de mi¬ nistres radicaux dans le gouverne¬ ment ; et demandant au bureau duComité Exécutif de proposer à laplus prochaine réunion du Comité lerefus de toute collaboration avec legouvernement actuel.Libre PenséeNous sommes heureux d'informer lepublic qu’une permanence de la 14esection de la Libre Pensée est ou¬ verte au numéro 47 de la rue Bé¬ nard (XIVe), à la Librairie des Tra¬ vailleurs.Le but de la Libre Pensée est de dé¬ velopper chez tous l’esprit critique etl'amour du libre examen, sans dis¬ tinction de parti, et de grouper dansson sein ceux qui se réclament de cehaut idéal. L’époque que nous vivonsest corrompue depuis des siècles parles croyances religieuses et leur amiedévouée Sa Majesté l'Argent qui gou¬ vernent le monde à leur seul bénéfice.Il est de notre devoir, pour nos en¬ fants et pour nous-mêmes, d'arracherce voile de l'au-delà et de mettre lemonde en face de ses nécessités réel¬ les. Chacun le peut dans son humblerôle ; la laïcité peut nous aider. Grou¬ pons-nous pour la défendre.Front populaireEpernay. — Dimanche après-midi,M. Eugène Frot, ancien ministre, adonné en la salle des fêtes d'Epernay(Marne) une conférence sous les aus¬ pices de la Ligue des Droits del'Homme et du Comité du Front Po¬ pulaire. Plus de 1.200 personnes yassistaient dont plusieurs élus radi¬ caux et socialistes de la région. M.Guerry, président, assisté de MM.Morange et Guen.MM. Eugène Frot, député, ancienministre, Bossus, conseiller munici¬ pal communiste de Paris, et EmileKahn, secrétaire général de la Liguedes Droits de l'Homme, ont pris suc¬ cessivement la parole très chaleu¬ reusement applaudis.La réunion se termina sans inci¬ dent. Dans la nuit, un membre de laSolidarité Française qui avait tentéde peindre des inscriptions injurieu¬ ses sur les murs de la Salle des Fêtesavait été surpris par la police. Il dé¬ clara avoir été inspiré dans son gestepar un discours du fils de M. Princequ'il avait entendu précédemment..XI<LOCATION>Ve arr</LOCATION>. — Pour la constitutiondes Comités de défense de la Répu¬ blique, trois grands meetings inaugu¬ raux sont organisés par le Front po¬ pulaire du 14e, aujourd'hui mercredi:111, rue du Château ; 115, rue Didot,1, avenue de la Porte-d'Orléans.Trente orateurs inscrits, dontRouffianges, Biquard, Croizat, Mau¬ vais, Paul Marcel, Graziani, <PERSON>MauriceLacroix</PERSON>, Létrange, Mension, etc...Ligue pour le Droit au Travailet le Progrès SocialVe arr — Une grande conférencesera donnée le vendredi 17 janvier,à 21 heures, à la Sorbonne, amphi¬ théâtre Richelieu, par Joseph Dubois,sur « L'Economie soviétique maî¬ tresse de ses destins ». Jacques Du¬ boin entretiendra ensuite les auditeursdu « Problème français ».Les cartes donnant droit aux placesréservées sont à la disposition des au¬ diteurs, au « Droit au Travail », 14,rue FavartViroflay. — Sous les auspices de lasection locaie des Droits de l'Homme,une grande réunion de propagandeaura lieu demain jeudi, à 21 heures,à la salie Robie, 134, route Navoù nos amis Chesneau et Ra,Martin exposeront les vérités dmiques diffusées par le « DroitTous nos amis et sympathisantssont cordialement invitésMaisons-Alfort. — L'Intersection dcanton de Charenton organisedredi 17 janvier, à 21 heures, ugrande réunion à la mairie dusons-Alfort, salle de la Justepaix. Nos camarades Compain mond Martin y parleront de « la révo¬ lution économique actuelle »."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Maurice Lacroix
    Description: helléniste, enseignant, lexicographe, résistant, syndicaliste et homme politique français
    Born: ['+1893-08-28T00:00:00Z']
    Died: ['+1989-01-13T00:00:00Z']
    Birth place: ['Q966370']
    Death place: ['Q468584']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1935" → 1935
      - "1936" → 1936
      - "1935" → 1935
    Temporal signal words: aujourd'hui, hier, ancien, plus, après
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.969

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'MauriceLacroix' and 'Ve arr' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'MauriceLacroix' near 'Ve arr' around 1936-01-15?
  4. Resolve temporal expressions relative to 1936-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 90 [ID: test_fr__50]:
  Publication date : 1936-01-15
  Language         : fr
  Person  : 'Chesneau'  (QID: N/A)
  Location: 'salie Robie, 134, route Nav'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Deux nouvelles inculpationsfrappent le surveillantcomplaisant valletM. Hude, juge d'instruction, a in¬ culpé hier le surveillant Vallet de cor¬ ruption de fonctionnaire, faux et usa¬ ge de faux. Tout d'abord, l'expertGebelin avait établi que tous les or¬ dres d'extraction, aussi bien ceux quisont entièrement faux que ceux quin'ont été que maquillés par additiond’un nom, avaient été préparés parla main du gardien de la Souricière.En particulier, l'ordre du 2 octobrequi permit à Pélissier de s’évader lelendemain et qui fut retrouvé le 4 à laSanté, est en entier de lui. Par ail¬ leurs, le petit carnet saisi sur Chris¬ tiane Pélissier établit qu’il avaittouché des sommes d'argent pour lalocation à la journée, de la cellulenuméro 10. Plusieurs autres dames,d'ailleurs, avec leurs maris détenus,ont contribué à alimenter la caissedu geôlier « compatissant ».Le versement des cotisationsd'assurances socialespour les chauffeurs de taxisLe ministère du Travail nous com¬ munique la note suivante :En application de l'article premier,paragraphe 3, du décret-loi du 28 oc¬ tobre 1935, modifiant le régime desAssurances sociales, les conducteursde voitures publiques, dont l'exploi¬ tation est assujettie à des tarifs detransport fixés par l'autorité publi¬ que, sont soumis au régime de l'assu¬ rance obligatoire, dès l'instant queleur rémunération n'excède pas lechiffre-limite prévu pour le bénéficede cette assurance.Les cotisations patronale et ouvriè¬ re sont dues depuis le premier jan¬ vier 1936.Conformément à l'article 3 de l'ar¬ rêté du 27 décembre 1935 paru auJournal Officiel du 29 décembre, lespourboires des intéressés, qui doi¬ vent entrer en compte pour la déter¬ mination de leur rémunération, se¬ ront évalués par des conventions col¬ lectives de travail, et, à défaut detelles conventions, par arrêtés du mi¬ nistre du Travail.L'unité syndicalechez les travailleurs de l'EtatLes sections de la Fédération uni¬ fiée des travailleurs de l'Etat (artil¬ lerie, poudreries, magasins adminis¬ tratifs, génie et aéronautique, em¬ ployés et agents de maîtrise, marinemilitaire, arts et métiers) ont tenuhier leurs assises patriculières dansles différentes salles de la Bourse duTravail.Voici les résultats définitifs du votepar mandats que le congrès de fusiondes deux Fédérations confédérée etunitaire avait été appelé à émettrelundi soir au sujet du cumul desfonctions syndicales et des mandatspolitiques. Contre : 287 voix ; pour :80 voix ; abstentions : 17 voix.PARTIS ET LIGUESGroupe des étudiants radicauxLa réunion du groupe des étu¬ diants radicaux de Paris aura lieuaujourd'hui mercredi, à 21 heures,au café « Chez Emile », 40, rue Ga¬ lande, et 10, rue Fouarre (angle desdeux rues).Fédération nationaledes Libres PenseursFédération de la Seine. — La com¬ mission spéciale d’unité d’action seréunira demain jeudi, à 21 heures,local habituel, rue de Châteaudun.Les responsables voudront bien êtreprésents.Parti radical-socialisteVersailles. — Les Comités radicaux¬ socialistes de la deuxième circons¬ cription de Versailles, réunis à Pois¬ sy, ont procédé à la constitution dila Fédération des Comités de cettecirconscription.Le bureau élu de la Fédération estainsi constitué : Président : RougelotHenri ; Secrétaire : Durand Fernand;Trésorier : Fourlon Pierre.Un ordre du jour a été voté décla¬ rant impossible le maintien de mi¬ nistres radicaux dans le gouverne¬ ment ; et demandant au bureau duComité Exécutif de proposer à laplus prochaine réunion du Comité lerefus de toute collaboration avec legouvernement actuel.Libre PenséeNous sommes heureux d'informer lepublic qu’une permanence de la 14esection de la Libre Pensée est ou¬ verte au numéro 47 de la rue Bé¬ nard (XIVe), à la Librairie des Tra¬ vailleurs.Le but de la Libre Pensée est de dé¬ velopper chez tous l’esprit critique etl'amour du libre examen, sans dis¬ tinction de parti, et de grouper dansson sein ceux qui se réclament de cehaut idéal. L’époque que nous vivonsest corrompue depuis des siècles parles croyances religieuses et leur amiedévouée Sa Majesté l'Argent qui gou¬ vernent le monde à leur seul bénéfice.Il est de notre devoir, pour nos en¬ fants et pour nous-mêmes, d'arracherce voile de l'au-delà et de mettre lemonde en face de ses nécessités réel¬ les. Chacun le peut dans son humblerôle ; la laïcité peut nous aider. Grou¬ pons-nous pour la défendre.Front populaireEpernay. — Dimanche après-midi,M. Eugène Frot, ancien ministre, adonné en la salle des fêtes d'Epernay(Marne) une conférence sous les aus¬ pices de la Ligue des Droits del'Homme et du Comité du Front Po¬ pulaire. Plus de 1.200 personnes yassistaient dont plusieurs élus radi¬ caux et socialistes de la région. M.Guerry, président, assisté de MM.Morange et Guen.MM. Eugène Frot, député, ancienministre, Bossus, conseiller munici¬ pal communiste de Paris, et EmileKahn, secrétaire général de la Liguedes Droits de l'Homme, ont pris suc¬ cessivement la parole très chaleu¬ reusement applaudis.La réunion se termina sans inci¬ dent. Dans la nuit, un membre de laSolidarité Française qui avait tentéde peindre des inscriptions injurieu¬ ses sur les murs de la Salle des Fêtesavait été surpris par la police. Il dé¬ clara avoir été inspiré dans son gestepar un discours du fils de M. Princequ'il avait entendu précédemment..XIVe arr. — Pour la constitutiondes Comités de défense de la Répu¬ blique, trois grands meetings inaugu¬ raux sont organisés par le Front po¬ pulaire du 14e, aujourd'hui mercredi:111, rue du Château ; 115, rue Didot,1, avenue de la Porte-d'Orléans.Trente orateurs inscrits, dontRouffianges, Biquard, Croizat, Mau¬ vais, Paul Marcel, Graziani, MauriceLacroix, Létrange, Mension, etc...Ligue pour le Droit au Travailet le Progrès SocialVe arr — Une grande conférencesera donnée le vendredi 17 janvier,à 21 heures, à la Sorbonne, amphi¬ théâtre Richelieu, par Joseph Dubois,sur « L'Economie soviétique maî¬ tresse de ses destins ». Jacques Du¬ boin entretiendra ensuite les auditeursdu « Problème français ».Les cartes donnant droit aux placesréservées sont à la disposition des au¬ diteurs, au « Droit au Travail », 14,rue FavartViroflay. — Sous les auspices de lasection locaie des Droits de l'Homme,une grande réunion de propagandeaura lieu demain jeudi, à 21 heures,à la <LOCATION>salie Robie, 134, route Nav</LOCATION>où nos amis <PERSON>Chesneau</PERSON> et Ra,Martin exposeront les vérités dmiques diffusées par le « DroitTous nos amis et sympathisantssont cordialement invitésMaisons-Alfort. — L'Intersection dcanton de Charenton organisedredi 17 janvier, à 21 heures, ugrande réunion à la mairie dusons-Alfort, salle de la Justepaix. Nos camarades Compain mond Martin y parleront de « la révo¬ lution économique actuelle »."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1935" → 1935
      - "1936" → 1936
      - "1935" → 1935
    Temporal signal words: aujourd'hui, hier, ancien, plus, après
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.969

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Chesneau' and 'salie Robie, 134, route Nav' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Chesneau' near 'salie Robie, 134, route Nav' around 1936-01-15?
  4. Resolve temporal expressions relative to 1936-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 91 [ID: test_fr__3]:
  Publication date : 1948-02-23
  Language         : fr
  Person  : 'Lausannois Hennsler'  (QID: N/A)
  Location: 'Montchoisi'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Le C. P. Zurich gagne Z le tournoi de hockey sur glace du Centenaire Samedi et dimanche, la patinoire de Monruz était une nouvelle fois entourée d'un nombreux public qui, bravant un froid très vif, suivit avec beaucoup d'intérêt le tournoi de hockey sur glace du Centenaire. Cette manifestation sportive fut pleinement réussie ; nous exprimons tefois un léger regret : pourquoi les trois rencontres ont-elles débuté avec dix à quinze minutes de retard ? Zurich bat <LOCATION>Montchoisi</LOCATION> par 12 à 8 (3-0, 6-3, 3-5) Les joueurs de Lausanne commencèrent par pratiquer un jeu passablement décousu : la défense était très lente et les avants trop individuels. Aussi tait-il une nette différence de classe entre les deux équipes en présence et Zurich, jouant avec beaucoup de décision, put dès l'abord s'octroyer un avantage de trois buts par Urson, Bieler et Ernst. Au cours du second tiers, les Zuricois relâchèrent un peu leur étreinte, alors que peu à peu l'on voyait Montchoisi s'organiser et attaquer avec mordant. Ce tiers fut ainsi assez équilibré, sans toutefois que les Zuricois perdent l'initiative du jeu. Ils marqueront cinq buts par Bieler (2), Urson, Sylvio Rossi, Boiler et Gugenbuhl, tandis que Banninger devait laisser passer trois tirs des Vaudois, deux de Minder et un de Caseel. Renversement de situation au dernier tiers où Montchoisi part résolument a l'attaque en montrant des qualités insoupçonnées. Le <PERSON>Lausannois Hennsler</PERSON> est particulièrement en verve et il marquera trois buts. D'autres attaques très bien menées permettront encore à Beltrami et à Caseel de diminuer l'écart du score. Mais la défense ne parvient pas à contenir les contre-attaques zuricoises et des shots bien placés de Rossi, Ernst et Boiler consolideront ment la victoire des joueurs de la Limmat. Zurich bat Young Sprinters par 10 à 2 (5-0. 1-2. 4-0) Cette partie, disons-le franchement, nous causa une certaine déception. L'on souhaitait une lutte plus équilibrée ; Young Sprinters est certainement capable de mieux résister à Zurich qu'il ne l'a fait hier matin. Nos joueurs, il est vrai, peuvent invoquer une circonstance atténuante. Hugo Delnon était malade et, de ce fait, la première ligne neuchâteloise était désorganisée. En outre. Reto n'apparut sur la glace qu'au début du second tiers. La première partie du jeu vit ainsi une très facile domination de Zurich. Des Bieler. Schubiger, Lohrer, semaient avec joie la panique dans notre camp et marquèrent cinq buts à intervalle régulier. Le second tiers nous fit espérer un redressement de la situation. Reto est là et il semble décider à bien faire. Il s'échappe par deux fois pour marquer deux superbes buts sans que le gardien Banninger puisse esquisser le moindre mouvement de défense. Mais l'équipe neuchâteloise continue à jouer avec une certaine incohérence. Les deux frères Delnon évoluent aveo le talentueux Ulrich, mais cette ligne manque de cohésion et plus rien ne réussira. Sylvio Rossi marquera au contraire un nouveau but. Dernier tiers assez monotone, les Zuricois sont supérieurs et ils parviendront sans trop d'efforts à accentuer leur avance par trois nouveaux buts réussis par Boiler, Gugenbuhl et Urson. Relevons dans le camp neuchâtelois la bonne partie du gardien Perrottet et la rapidité, la décision et le maniement de crosse d'Ulrich. Chez les Zuricois, il faut surtout louer la sûreté d'une défense très solide et un peu rude ; la première ligne formée de Bieler, Lohrer et Schubiger fut de loin la meilleure ligne du tournoi. Young Sprinters bat Montchoisi par 5 à 3 (2-0. 1-2. 2-1) Cette rencontre nous fait oublier la décevante partie disputée le matin. Les deux grands rivaux romands se livrent une lutte très ouverte et variée. Signalons quelques duels épiques entre Hans Cattini, Stucki, les deux frères Delnon et Ulrich. Remise de sa défaillance, notre équipe joua d'une manière digne d'elle-même et elle ne cessa de jouir d'une légère supériorité sur son adversaire. Reto et Othmar Delnon ouvrirent la marque au premier tiers. Les Lausannois placèrent leur effort principal sur le second tiers, mais notre défense formée de Tinembart et du Dr Grether, ainsi que du gardien Perrottet, dans une forme exceptionnelle dimanche, parvinrent à endiguer leurs assauts à l'exception de deux qui permirent à Jansky et à Beltrami de loger le puck au fond de la cage neuchâteloise. Le dernier tiers, au cours duquel le jeu devient assez dur, permit à Young Sprinters de s'assurer une victoire méritée. Jansky profita tout d'abord judicieusement d'une erreur de notre défense, mais Othmar Delnon trompera deux fois encore le gardien Ayer. Relevons l'excellent travail d'Ulrich. Rapide, poussant jusqu'au bout chaque descente, ne considérant jamais perdue une passe, il mena avec brio les attaques de notre notro seconde ligne et certains de ses shots auraient mérité le but. Le palmarès A la suite de ces rencontre, Zurich gagne le tournoi aveo quatre points, suivi de Young Sprinters (2 p.) et Mont _, choisi (0 p.). Lo C. P. Zurich gagne le premier prix du tournoi, la grande distinction du Centenaire et le challenge du tournoi. Young Sprinters obtient la deuxième distinction du Centenaire et le challenge Vuillomenet, récompensant l'équipe jouant avec le plus de fair-play. Quant à Montchoisi, il reçoit la coupe offerte par le cinéma Palace. B. Ad. Une tournée de Young Sprinters en Tchécoslovaquie Notre équipe de hockey sur glace a été invitée à disputer un certain nombre de matches en Tchécoslovaquie, notamment contre Prague et Brno. Elle partira pour ce pays au début du mois de mars et sera renforcée par quelques autres joueurs de ligue nationale A."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.971

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Lausannois Hennsler' and 'Montchoisi' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Lausannois Hennsler' near 'Montchoisi' around 1948-02-23?
  4. Resolve temporal expressions relative to 1948-02-23. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 92 [ID: test_fr__233]:
  Publication date : 1981-02-18
  Language         : fr
  Person  : 'Favre-Blanc'  (QID: N/A)
  Location: 'Berne'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "SUISSE dernière COMMISSION DES ETATS La Suissesse mariée garderait son droit de cité <LOCATION>Berne</LOCATION>, 17 (ATS).-La Commission du conseil des Etats chargée d'examiner le nouveau droit matrimonial, qui a terminé ses travaux mardi à Berne, a modifié sur quelques points le projet du Conseil fédéral.Elle a cependant accepté dans ses grandes lignes le projet gouvernemental et notamment le remplacement du régime actuel de l'union des biens par celui de la participation aux acquêts.Cet objet sera traité par le parlement au mois de mars.Au sujet du nom des époux, la Commission rejoint le Conseil fédéral dans son refus d'accorder le droit d'option qui permettrait aux fiancés de choisir le nom de l'épouse comme nom de famille.Mais la femme aura le droit non seulement de faire suivre son nom (<PERSON>Favre-Blanc</PERSON>), mais aussi de le faire précéder (Mme Blanc épouse Favre).La Commission n'a pas retenu la possibilité de l'option en raison de la tradition qui existe dans notre pays.En Allemagne fédérale, où le choix existe, seuls 4 % des époux en font usage.La nouvelle réglementation suisse facilitera- cependant l'adoption éventuelle par les fiancés, avant le mariage, du nom de la femme comme nom de famille.Mais il faudra de bonnes raisons pour l'autoriser (nom à consonnance étrangère, nom connu dans le commerce, la politique, etc).En ce qui concerne le droit de cité, la femme recevra, par le mariage, le droit de cité du mari mais sans perdre le sien.Une majorité s'est formée dans la Commission en faveur de cette solution."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.993

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Favre-Blanc' and 'Berne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Favre-Blanc' near 'Berne' around 1981-02-18?
  4. Resolve temporal expressions relative to 1981-02-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 93 [ID: test_fr__59]:
  Publication date : 1936-01-15
  Language         : fr
  Person  : 'MM. Eugène Frot, député, ancienministre'  (QID: Q3059882)
  Location: 'Epernay'  (QID: Q205537)

  [ARTICLE TEXT — entity markers added]
  "Deux nouvelles inculpationsfrappent le surveillantcomplaisant valletM. Hude, juge d'instruction, a in¬ culpé hier le surveillant Vallet de cor¬ ruption de fonctionnaire, faux et usa¬ ge de faux. Tout d'abord, l'expertGebelin avait établi que tous les or¬ dres d'extraction, aussi bien ceux quisont entièrement faux que ceux quin'ont été que maquillés par additiond’un nom, avaient été préparés parla main du gardien de la Souricière.En particulier, l'ordre du 2 octobrequi permit à Pélissier de s’évader lelendemain et qui fut retrouvé le 4 à laSanté, est en entier de lui. Par ail¬ leurs, le petit carnet saisi sur Chris¬ tiane Pélissier établit qu’il avaittouché des sommes d'argent pour lalocation à la journée, de la cellulenuméro 10. Plusieurs autres dames,d'ailleurs, avec leurs maris détenus,ont contribué à alimenter la caissedu geôlier « compatissant ».Le versement des cotisationsd'assurances socialespour les chauffeurs de taxisLe ministère du Travail nous com¬ munique la note suivante :En application de l'article premier,paragraphe 3, du décret-loi du 28 oc¬ tobre 1935, modifiant le régime desAssurances sociales, les conducteursde voitures publiques, dont l'exploi¬ tation est assujettie à des tarifs detransport fixés par l'autorité publi¬ que, sont soumis au régime de l'assu¬ rance obligatoire, dès l'instant queleur rémunération n'excède pas lechiffre-limite prévu pour le bénéficede cette assurance.Les cotisations patronale et ouvriè¬ re sont dues depuis le premier jan¬ vier 1936.Conformément à l'article 3 de l'ar¬ rêté du 27 décembre 1935 paru auJournal Officiel du 29 décembre, lespourboires des intéressés, qui doi¬ vent entrer en compte pour la déter¬ mination de leur rémunération, se¬ ront évalués par des conventions col¬ lectives de travail, et, à défaut detelles conventions, par arrêtés du mi¬ nistre du Travail.L'unité syndicalechez les travailleurs de l'EtatLes sections de la Fédération uni¬ fiée des travailleurs de l'Etat (artil¬ lerie, poudreries, magasins adminis¬ tratifs, génie et aéronautique, em¬ ployés et agents de maîtrise, marinemilitaire, arts et métiers) ont tenuhier leurs assises patriculières dansles différentes salles de la Bourse duTravail.Voici les résultats définitifs du votepar mandats que le congrès de fusiondes deux Fédérations confédérée etunitaire avait été appelé à émettrelundi soir au sujet du cumul desfonctions syndicales et des mandatspolitiques. Contre : 287 voix ; pour :80 voix ; abstentions : 17 voix.PARTIS ET LIGUESGroupe des étudiants radicauxLa réunion du groupe des étu¬ diants radicaux de Paris aura lieuaujourd'hui mercredi, à 21 heures,au café « Chez Emile », 40, rue Ga¬ lande, et 10, rue Fouarre (angle desdeux rues).Fédération nationaledes Libres PenseursFédération de la Seine. — La com¬ mission spéciale d’unité d’action seréunira demain jeudi, à 21 heures,local habituel, rue de Châteaudun.Les responsables voudront bien êtreprésents.Parti radical-socialisteVersailles. — Les Comités radicaux¬ socialistes de la deuxième circons¬ cription de Versailles, réunis à Pois¬ sy, ont procédé à la constitution dila Fédération des Comités de cettecirconscription.Le bureau élu de la Fédération estainsi constitué : Président : RougelotHenri ; Secrétaire : Durand Fernand;Trésorier : Fourlon Pierre.Un ordre du jour a été voté décla¬ rant impossible le maintien de mi¬ nistres radicaux dans le gouverne¬ ment ; et demandant au bureau duComité Exécutif de proposer à laplus prochaine réunion du Comité lerefus de toute collaboration avec legouvernement actuel.Libre PenséeNous sommes heureux d'informer lepublic qu’une permanence de la 14esection de la Libre Pensée est ou¬ verte au numéro 47 de la rue Bé¬ nard (XIVe), à la Librairie des Tra¬ vailleurs.Le but de la Libre Pensée est de dé¬ velopper chez tous l’esprit critique etl'amour du libre examen, sans dis¬ tinction de parti, et de grouper dansson sein ceux qui se réclament de cehaut idéal. L’époque que nous vivonsest corrompue depuis des siècles parles croyances religieuses et leur amiedévouée Sa Majesté l'Argent qui gou¬ vernent le monde à leur seul bénéfice.Il est de notre devoir, pour nos en¬ fants et pour nous-mêmes, d'arracherce voile de l'au-delà et de mettre lemonde en face de ses nécessités réel¬ les. Chacun le peut dans son humblerôle ; la laïcité peut nous aider. Grou¬ pons-nous pour la défendre.Front populaire<LOCATION>Epernay</LOCATION>. — Dimanche après-midi,M. Eugène Frot, ancien ministre, adonné en la salle des fêtes d'Epernay(Marne) une conférence sous les aus¬ pices de la Ligue des Droits del'Homme et du Comité du Front Po¬ pulaire. Plus de 1.200 personnes yassistaient dont plusieurs élus radi¬ caux et socialistes de la région. M.Guerry, président, assisté de MM.Morange et Guen.<PERSON>MM. Eugène Frot, député, ancienministre</PERSON>, Bossus, conseiller munici¬ pal communiste de Paris, et EmileKahn, secrétaire général de la Liguedes Droits de l'Homme, ont pris suc¬ cessivement la parole très chaleu¬ reusement applaudis.La réunion se termina sans inci¬ dent. Dans la nuit, un membre de laSolidarité Française qui avait tentéde peindre des inscriptions injurieu¬ ses sur les murs de la Salle des Fêtesavait été surpris par la police. Il dé¬ clara avoir été inspiré dans son gestepar un discours du fils de M. Princequ'il avait entendu précédemment..XIVe arr. — Pour la constitutiondes Comités de défense de la Répu¬ blique, trois grands meetings inaugu¬ raux sont organisés par le Front po¬ pulaire du 14e, aujourd'hui mercredi:111, rue du Château ; 115, rue Didot,1, avenue de la Porte-d'Orléans.Trente orateurs inscrits, dontRouffianges, Biquard, Croizat, Mau¬ vais, Paul Marcel, Graziani, MauriceLacroix, Létrange, Mension, etc...Ligue pour le Droit au Travailet le Progrès SocialVe arr — Une grande conférencesera donnée le vendredi 17 janvier,à 21 heures, à la Sorbonne, amphi¬ théâtre Richelieu, par Joseph Dubois,sur « L'Economie soviétique maî¬ tresse de ses destins ». Jacques Du¬ boin entretiendra ensuite les auditeursdu « Problème français ».Les cartes donnant droit aux placesréservées sont à la disposition des au¬ diteurs, au « Droit au Travail », 14,rue FavartViroflay. — Sous les auspices de lasection locaie des Droits de l'Homme,une grande réunion de propagandeaura lieu demain jeudi, à 21 heures,à la salie Robie, 134, route Navoù nos amis Chesneau et Ra,Martin exposeront les vérités dmiques diffusées par le « DroitTous nos amis et sympathisantssont cordialement invitésMaisons-Alfort. — L'Intersection dcanton de Charenton organisedredi 17 janvier, à 21 heures, ugrande réunion à la mairie dusons-Alfort, salle de la Justepaix. Nos camarades Compain mond Martin y parleront de « la révo¬ lution économique actuelle »."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Épernay
    Description: ville et commune française du département de la Marne
    Country: ['France']
    Located in: ["arrondissement d'Épernay", 'Marne']
    Aliases: {'de': ['Epernay']}
    Coordinates: [{'lat': 49.04, 'lon': 3.9591666666667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1935" → 1935
      - "1936" → 1936
      - "1935" → 1935
    Temporal signal words: aujourd'hui, hier, ancien, plus, après
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.969

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'MM. Eugène Frot, député, ancienministre' and 'Epernay' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'MM. Eugène Frot, député, ancienministre' near 'Epernay' around 1936-01-15?
  4. Resolve temporal expressions relative to 1936-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 94 [ID: test_fr__53]:
  Publication date : 1936-01-15
  Language         : fr
  Person  : 'MauriceLacroix'  (QID: Q3300985)
  Location: "1, avenue de la Porte-d'Orléans"  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Deux nouvelles inculpationsfrappent le surveillantcomplaisant valletM. Hude, juge d'instruction, a in¬ culpé hier le surveillant Vallet de cor¬ ruption de fonctionnaire, faux et usa¬ ge de faux. Tout d'abord, l'expertGebelin avait établi que tous les or¬ dres d'extraction, aussi bien ceux quisont entièrement faux que ceux quin'ont été que maquillés par additiond’un nom, avaient été préparés parla main du gardien de la Souricière.En particulier, l'ordre du 2 octobrequi permit à Pélissier de s’évader lelendemain et qui fut retrouvé le 4 à laSanté, est en entier de lui. Par ail¬ leurs, le petit carnet saisi sur Chris¬ tiane Pélissier établit qu’il avaittouché des sommes d'argent pour lalocation à la journée, de la cellulenuméro 10. Plusieurs autres dames,d'ailleurs, avec leurs maris détenus,ont contribué à alimenter la caissedu geôlier « compatissant ».Le versement des cotisationsd'assurances socialespour les chauffeurs de taxisLe ministère du Travail nous com¬ munique la note suivante :En application de l'article premier,paragraphe 3, du décret-loi du 28 oc¬ tobre 1935, modifiant le régime desAssurances sociales, les conducteursde voitures publiques, dont l'exploi¬ tation est assujettie à des tarifs detransport fixés par l'autorité publi¬ que, sont soumis au régime de l'assu¬ rance obligatoire, dès l'instant queleur rémunération n'excède pas lechiffre-limite prévu pour le bénéficede cette assurance.Les cotisations patronale et ouvriè¬ re sont dues depuis le premier jan¬ vier 1936.Conformément à l'article 3 de l'ar¬ rêté du 27 décembre 1935 paru auJournal Officiel du 29 décembre, lespourboires des intéressés, qui doi¬ vent entrer en compte pour la déter¬ mination de leur rémunération, se¬ ront évalués par des conventions col¬ lectives de travail, et, à défaut detelles conventions, par arrêtés du mi¬ nistre du Travail.L'unité syndicalechez les travailleurs de l'EtatLes sections de la Fédération uni¬ fiée des travailleurs de l'Etat (artil¬ lerie, poudreries, magasins adminis¬ tratifs, génie et aéronautique, em¬ ployés et agents de maîtrise, marinemilitaire, arts et métiers) ont tenuhier leurs assises patriculières dansles différentes salles de la Bourse duTravail.Voici les résultats définitifs du votepar mandats que le congrès de fusiondes deux Fédérations confédérée etunitaire avait été appelé à émettrelundi soir au sujet du cumul desfonctions syndicales et des mandatspolitiques. Contre : 287 voix ; pour :80 voix ; abstentions : 17 voix.PARTIS ET LIGUESGroupe des étudiants radicauxLa réunion du groupe des étu¬ diants radicaux de Paris aura lieuaujourd'hui mercredi, à 21 heures,au café « Chez Emile », 40, rue Ga¬ lande, et 10, rue Fouarre (angle desdeux rues).Fédération nationaledes Libres PenseursFédération de la Seine. — La com¬ mission spéciale d’unité d’action seréunira demain jeudi, à 21 heures,local habituel, rue de Châteaudun.Les responsables voudront bien êtreprésents.Parti radical-socialisteVersailles. — Les Comités radicaux¬ socialistes de la deuxième circons¬ cription de Versailles, réunis à Pois¬ sy, ont procédé à la constitution dila Fédération des Comités de cettecirconscription.Le bureau élu de la Fédération estainsi constitué : Président : RougelotHenri ; Secrétaire : Durand Fernand;Trésorier : Fourlon Pierre.Un ordre du jour a été voté décla¬ rant impossible le maintien de mi¬ nistres radicaux dans le gouverne¬ ment ; et demandant au bureau duComité Exécutif de proposer à laplus prochaine réunion du Comité lerefus de toute collaboration avec legouvernement actuel.Libre PenséeNous sommes heureux d'informer lepublic qu’une permanence de la 14esection de la Libre Pensée est ou¬ verte au numéro 47 de la rue Bé¬ nard (XIVe), à la Librairie des Tra¬ vailleurs.Le but de la Libre Pensée est de dé¬ velopper chez tous l’esprit critique etl'amour du libre examen, sans dis¬ tinction de parti, et de grouper dansson sein ceux qui se réclament de cehaut idéal. L’époque que nous vivonsest corrompue depuis des siècles parles croyances religieuses et leur amiedévouée Sa Majesté l'Argent qui gou¬ vernent le monde à leur seul bénéfice.Il est de notre devoir, pour nos en¬ fants et pour nous-mêmes, d'arracherce voile de l'au-delà et de mettre lemonde en face de ses nécessités réel¬ les. Chacun le peut dans son humblerôle ; la laïcité peut nous aider. Grou¬ pons-nous pour la défendre.Front populaireEpernay. — Dimanche après-midi,M. Eugène Frot, ancien ministre, adonné en la salle des fêtes d'Epernay(Marne) une conférence sous les aus¬ pices de la Ligue des Droits del'Homme et du Comité du Front Po¬ pulaire. Plus de 1.200 personnes yassistaient dont plusieurs élus radi¬ caux et socialistes de la région. M.Guerry, président, assisté de MM.Morange et Guen.MM. Eugène Frot, député, ancienministre, Bossus, conseiller munici¬ pal communiste de Paris, et EmileKahn, secrétaire général de la Liguedes Droits de l'Homme, ont pris suc¬ cessivement la parole très chaleu¬ reusement applaudis.La réunion se termina sans inci¬ dent. Dans la nuit, un membre de laSolidarité Française qui avait tentéde peindre des inscriptions injurieu¬ ses sur les murs de la Salle des Fêtesavait été surpris par la police. Il dé¬ clara avoir été inspiré dans son gestepar un discours du fils de M. Princequ'il avait entendu précédemment..XIVe arr. — Pour la constitutiondes Comités de défense de la Répu¬ blique, trois grands meetings inaugu¬ raux sont organisés par le Front po¬ pulaire du 14e, aujourd'hui mercredi:111, rue du Château ; 115, rue Didot,<LOCATION>1, avenue de la Porte-d'Orléans</LOCATION>.Trente orateurs inscrits, dontRouffianges, Biquard, Croizat, Mau¬ vais, Paul Marcel, Graziani, <PERSON>MauriceLacroix</PERSON>, Létrange, Mension, etc...Ligue pour le Droit au Travailet le Progrès SocialVe arr — Une grande conférencesera donnée le vendredi 17 janvier,à 21 heures, à la Sorbonne, amphi¬ théâtre Richelieu, par Joseph Dubois,sur « L'Economie soviétique maî¬ tresse de ses destins ». Jacques Du¬ boin entretiendra ensuite les auditeursdu « Problème français ».Les cartes donnant droit aux placesréservées sont à la disposition des au¬ diteurs, au « Droit au Travail », 14,rue FavartViroflay. — Sous les auspices de lasection locaie des Droits de l'Homme,une grande réunion de propagandeaura lieu demain jeudi, à 21 heures,à la salie Robie, 134, route Navoù nos amis Chesneau et Ra,Martin exposeront les vérités dmiques diffusées par le « DroitTous nos amis et sympathisantssont cordialement invitésMaisons-Alfort. — L'Intersection dcanton de Charenton organisedredi 17 janvier, à 21 heures, ugrande réunion à la mairie dusons-Alfort, salle de la Justepaix. Nos camarades Compain mond Martin y parleront de « la révo¬ lution économique actuelle »."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1935" → 1935
      - "1936" → 1936
      - "1935" → 1935
    Temporal signal words: aujourd'hui, hier, ancien, plus, après
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.969

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'MauriceLacroix' and "1, avenue de la Porte-d'Orléans" in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'MauriceLacroix' near "1, avenue de la Porte-d'Orléans" around 1936-01-15?
  4. Resolve temporal expressions relative to 1936-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 95 [ID: test_fr__90]:
  Publication date : 1968-04-08
  Language         : fr
  Person  : 'Reusser'  (QID: N/A)
  Location: 'Meznau'  (QID: Q14607)

  [ARTICLE TEXT — entity markers added]
  "Bioiiey remporte le Tour du Léman à Genève Deux importantes épreuves pour nos amateurs d'élite A l'échelon des amateurs-elites, le weekend était d'importance à Genève. Oscar Plattner, grand responsable de cette catégorie d'éventuels futurs champions, avait délégué ses pouvoirs à Gilbert Perrenoud, afin qu'il suive très attentivement ce qui se passait sur les routes. Le Comité national a, en effet, l'intention très arrêtée de mettre sur pied la meilleure équipe possible pour le Tour de l'Avenir, les Jeux olympiques et les championnats du monde. Tout un programme de sélection a ainsi été mis au point. Dimanche à midi, Gilbert Perrenoud se déclarait enchanté de ce qu'il avait vu. Non pas que l'on puisse immédiatement dire que les coureurs suisses sont en forme, mais les sujets de satisfaction ne manquaient pas : « on voit que nous sommes dans une année importante, une année où les voyages et les honneurs seront nombreux. Il y a l'Uruguay, le Mexique, des médailles à revendre. C'est pourquoi nos meilleurs coureurs se sont préparés de belle façon, c'est pourquoi aussi de nombreux jeunes frappent à la porte .. En fait, ces deux courses genevoises ont permis de nombreux enseignements. Animées toutes deux, courues assez rapidement, elles se sont révélées d'une excellente qualité. D'OESCHGER... Samedi après-midi, sur un circuit de seize kiolmètres à parcourir huit fois, quelque soixante-cinq coureurs prirent le départ. Sous le soleil, qui allait bientôt disparaître, et faire place à un violent orage. L'échappée, la bonne, vint très rapidement. Au deuxième tour déjà, après qu'un « faux départ » eut lieu, à savoir une erreur de parcours annulant les efforts des premiers audacieux. Fait assez rare, la course fut stoppée à 9 km 400 de son premier départ puis relancée. C'est alors que l'un des Belges invités, froidement, tenta de partir. Il y parvint en compagnie de Rub, d'Oeschger, de Schnetzler, le champion de Suisse, von Arx, Fischer, et les Romands Behier (Moudon), Regamey (Yverdon) et Vaucher (Lausanne). Cahin-caha, sur de petites routes, étroites et sinueuses, cette échappée prit quelque avance. Sur le peloton tout d'abord, sur un groupe de contre-attaque par la suite, qui allait faire sa jonction. D'ailleurs, il ne resta plus que ces hommes en course... Les autres pensaient au tour du lac du lendemain, et se retiraient II y a encore quelques audacieux : Schnetzler, Spannagel, Birrer et Weber. Mais leurs tentatives solitaires furent réduites à néant. Et sur la fin, le peloton se scinda en deux. . . . A BIOLLEY Ce tour du lac — doyenne des épreuves cyclistes, qui en était hier à sa 76 mc édition — eut un déroulement assez rare. Daniel Biolley, de Fribourg, l'expliqua une fois passée, en vainqueur, la ligne d' arrivée : « C'est mon sixième- tour du lac. Et j'avais jusqu'ici constaté que jamais une échappée partie de loin ne réussissait Aussi je n'ai pas mené depuis Versoix (km 10) où nous sommes partis. Mais comme à Evian, en abordant le col de Vinzier, nous avions plus de cinq minutes sur nos poursuivants, et plus de dix sur le peloton _, je me suis lancé dans la bagarre. » La course partit en effet très tôt : Brunner — qui allait vite disparaître — Lier, Hofer et Grin s'en allèrent vers l'entrée de l'autoroute Genève-Lausanne. Rapidement Biolley, Angelucci, Elliker, Kalt, Rennhard, Rutchmann, Thalmann, <PERSON>Reusser</PERSON>, Adam, Schneider et Melliflio les rejoignirent Et, au gré des kilomètres, de la forme de certains ou de divers ennuis mécaniques, il resta dix hommes ensemble à Evian, dont quatre partirent bien vite dès les premières côtes de la seule difficulté de la journée, quatre qui restèrent ensemble jusqu'à l'arrivée où se produisit un petit drame : Lier sprinta, gagna, mais ne savait pas qu'il y avait un tour et la distance à faire... Biolley passa donc, de même que Rennhardt. Les deux coéquipiers (d'Allegro) avaient des mines patibulaires à l'arrivée. Lier pleurait et Biolley n'était pas plus content que cela : « La victoire lui revenait il avait fait une grosse part de travail. Mais je ne pouvais pas me relever, car Rennhard avait passé. Serge DOURNOW CLASSEMENT DU GRAND PRIX DE MEINIER 1. Oeschger (Oberhofen), les 128 km en 3 h 32'13 " ; 2. Rub (Bmgg) ; 3. Fischer (Brugg) ; 4. Binggeli (Genève ; 5. Regamey (Yverdon). CLASSEMENT DU TOUR DU LÉMAN 1. Biolley (Fribourg), les 187 km en 4 h 30'36 " ; 2. Rennhard (Brugg) ; 3. Lier (Affoltern) ; 4. Thalmann (<LOCATION>Meznau</LOCATION>), même temps ; 5. Rutschmann (Seuzach), à 3'32 " ; 6. Hofer (Berne) ; 7. Kalt (Zurich) ; 8. Elliker (Urdorf) ; 9. Reusser (Brugg), même temps ; 10. Peter (Zurich), à 7'40 "."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.959

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Reusser' and 'Meznau' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Reusser' near 'Meznau' around 1968-04-08?
  4. Resolve temporal expressions relative to 1968-04-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 96 [ID: test_fr__128]:
  Publication date : 1928-08-28
  Language         : fr
  Person  : 'M. Scheller'  (QID: N/A)
  Location: 'Grand-Mulet'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Les accidents Un alpiniste genevois atteint par nn bloc de rocher a lé crâne fracturé et menrt Genève, 27 août. Dimanche, quatre alpinistes genevois membres du Club des grimpeurs s'étaient rendus au Mont-Blanc lorsque, vers 17 heures, au chemin qui conduit du glacier du <LOCATION>Grand-Mulet</LOCATION> à la station de l'Aiguille du Midi, l'un d'eux, Aimé Scheller, 36 ans, sertisseur, fut soudain atteint par un bloc qui s'était détaché et Sii lui fit une grave blessure à la tête, eux de ses compagnons demeurèrent auprès du blessé tandis que l'autre allait quérir du secours. Une colonne, organisée aussitôt, ramena le blessé à la station. <PERSON>M. Scheller</PERSON> reçut les soins d'un médecin français et fut descendu qu'aux Bossons en automobile. De là, il fut dirigé sur l'hôpital cantonal de Genève où il est mort lundi matin des suites d'une fracture du crâne. Il laisse une femme et une fillette. Un char à chien contre une motocyclette * Un petit char attelé d'un chien et appairtenant à M. François Savoy, demeurant à Bossonens (Èribourg), s'est jeté devant une motocyclette montée par M. Max Veraaud, pasteur à Mézières (Vaud), ayant en croupe son frère. La moto fut renversée avec ses deux occupants ; Je Téservoir à benzine s'étant débouché, l'eesence prit feu au contact du phare à acétylène et se communiqua aux vêtements de M. Vernaud. Une application de sacs mouillés l'éteignit. M. Vernaud a les sourcils et les cheveux légèrement brûlés et des contusions. La motocyclette, fort endommagée, a dû être conduite au garage. Grave accident d'automobile Sarnen, 28 août. Une automobile zurichoise occupée par 4 personnes, a fait une chute près de Lungern. Ses occupante ont été projetés hors de la voiture, Mme Jenny-tHirlimann, 35 ans, femme d un entrepreneur de Zurich, a eu la cage thoracique enfoncée. Un médecin qui circulait, par hasard à cet endroit, a fait transporter la malheureuse à Lungern où elle a succombé lundi matin. L'un des occupants a été également contusionné. Une automobile bousculée * Un oamion-automobite de la brasserie Muliler descendant, dimanche, au début de l'après-imidd, de Sainte-Croix SUT Vuitobœuf, a accroché, au premier grand tournant de la route, au-dessous du Château (Saimte-tCroix) une petite torpédo à trois places occupée par deux personnes et qui montait à Sainte-Croix. H l'a lancée avec violence contre le mur bordant la route. Les occupants de l'auto s'en tirent avec des blessures superficielles ; ils sont rentrés à Sainte-Croix, mais leur voiture gravement endommagée a dû être remorquée au grand garage des Remparts à Yverdon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Scheller' and 'Grand-Mulet' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Scheller' near 'Grand-Mulet' around 1928-08-28?
  4. Resolve temporal expressions relative to 1928-08-28. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 97 [ID: test_fr__97]:
  Publication date : 1968-04-08
  Language         : fr
  Person  : 'von Arx'  (QID: N/A)
  Location: 'Suisse'  (QID: Q39)

  [ARTICLE TEXT — entity markers added]
  "Bioiiey remporte le Tour du Léman à Genève Deux importantes épreuves pour nos amateurs d'élite A l'échelon des amateurs-elites, le weekend était d'importance à Genève. Oscar Plattner, grand responsable de cette catégorie d'éventuels futurs champions, avait délégué ses pouvoirs à Gilbert Perrenoud, afin qu'il suive très attentivement ce qui se passait sur les routes. Le Comité national a, en effet, l'intention très arrêtée de mettre sur pied la meilleure équipe possible pour le Tour de l'Avenir, les Jeux olympiques et les championnats du monde. Tout un programme de sélection a ainsi été mis au point. Dimanche à midi, Gilbert Perrenoud se déclarait enchanté de ce qu'il avait vu. Non pas que l'on puisse immédiatement dire que les coureurs suisses sont en forme, mais les sujets de satisfaction ne manquaient pas : « on voit que nous sommes dans une année importante, une année où les voyages et les honneurs seront nombreux. Il y a l'Uruguay, le Mexique, des médailles à revendre. C'est pourquoi nos meilleurs coureurs se sont préparés de belle façon, c'est pourquoi aussi de nombreux jeunes frappent à la porte .. En fait, ces deux courses genevoises ont permis de nombreux enseignements. Animées toutes deux, courues assez rapidement, elles se sont révélées d'une excellente qualité. D'OESCHGER... Samedi après-midi, sur un circuit de seize kiolmètres à parcourir huit fois, quelque soixante-cinq coureurs prirent le départ. Sous le soleil, qui allait bientôt disparaître, et faire place à un violent orage. L'échappée, la bonne, vint très rapidement. Au deuxième tour déjà, après qu'un « faux départ » eut lieu, à savoir une erreur de parcours annulant les efforts des premiers audacieux. Fait assez rare, la course fut stoppée à 9 km 400 de son premier départ puis relancée. C'est alors que l'un des Belges invités, froidement, tenta de partir. Il y parvint en compagnie de Rub, d'Oeschger, de Schnetzler, le champion de <LOCATION>Suisse</LOCATION>, <PERSON>von Arx</PERSON>, Fischer, et les Romands Behier (Moudon), Regamey (Yverdon) et Vaucher (Lausanne). Cahin-caha, sur de petites routes, étroites et sinueuses, cette échappée prit quelque avance. Sur le peloton tout d'abord, sur un groupe de contre-attaque par la suite, qui allait faire sa jonction. D'ailleurs, il ne resta plus que ces hommes en course... Les autres pensaient au tour du lac du lendemain, et se retiraient II y a encore quelques audacieux : Schnetzler, Spannagel, Birrer et Weber. Mais leurs tentatives solitaires furent réduites à néant. Et sur la fin, le peloton se scinda en deux. . . . A BIOLLEY Ce tour du lac — doyenne des épreuves cyclistes, qui en était hier à sa 76 mc édition — eut un déroulement assez rare. Daniel Biolley, de Fribourg, l'expliqua une fois passée, en vainqueur, la ligne d' arrivée : « C'est mon sixième- tour du lac. Et j'avais jusqu'ici constaté que jamais une échappée partie de loin ne réussissait Aussi je n'ai pas mené depuis Versoix (km 10) où nous sommes partis. Mais comme à Evian, en abordant le col de Vinzier, nous avions plus de cinq minutes sur nos poursuivants, et plus de dix sur le peloton _, je me suis lancé dans la bagarre. » La course partit en effet très tôt : Brunner — qui allait vite disparaître — Lier, Hofer et Grin s'en allèrent vers l'entrée de l'autoroute Genève-Lausanne. Rapidement Biolley, Angelucci, Elliker, Kalt, Rennhard, Rutchmann, Thalmann, Reusser, Adam, Schneider et Melliflio les rejoignirent Et, au gré des kilomètres, de la forme de certains ou de divers ennuis mécaniques, il resta dix hommes ensemble à Evian, dont quatre partirent bien vite dès les premières côtes de la seule difficulté de la journée, quatre qui restèrent ensemble jusqu'à l'arrivée où se produisit un petit drame : Lier sprinta, gagna, mais ne savait pas qu'il y avait un tour et la distance à faire... Biolley passa donc, de même que Rennhardt. Les deux coéquipiers (d'Allegro) avaient des mines patibulaires à l'arrivée. Lier pleurait et Biolley n'était pas plus content que cela : « La victoire lui revenait il avait fait une grosse part de travail. Mais je ne pouvais pas me relever, car Rennhard avait passé. Serge DOURNOW CLASSEMENT DU GRAND PRIX DE MEINIER 1. Oeschger (Oberhofen), les 128 km en 3 h 32'13 " ; 2. Rub (Bmgg) ; 3. Fischer (Brugg) ; 4. Binggeli (Genève ; 5. Regamey (Yverdon). CLASSEMENT DU TOUR DU LÉMAN 1. Biolley (Fribourg), les 187 km en 4 h 30'36 " ; 2. Rennhard (Brugg) ; 3. Lier (Affoltern) ; 4. Thalmann (Meznau), même temps ; 5. Rutschmann (Seuzach), à 3'32 " ; 6. Hofer (Berne) ; 7. Kalt (Zurich) ; 8. Elliker (Urdorf) ; 9. Reusser (Brugg), même temps ; 10. Peter (Zurich), à 7'40 "."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.959

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'von Arx' and 'Suisse' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'von Arx' near 'Suisse' around 1968-04-08?
  4. Resolve temporal expressions relative to 1968-04-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 98 [ID: test_fr__135]:
  Publication date : 1928-08-28
  Language         : fr
  Person  : 'M. Max Veraaud, pasteur à Mézières\n(Vaud)'  (QID: N/A)
  Location: 'Genève'  (QID: Q71)

  [ARTICLE TEXT — entity markers added]
  "Les accidents Un alpiniste genevois atteint par nn bloc de rocher a lé crâne fracturé et menrt <LOCATION>Genève</LOCATION>, 27 août. Dimanche, quatre alpinistes genevois membres du Club des grimpeurs s'étaient rendus au Mont-Blanc lorsque, vers 17 heures, au chemin qui conduit du glacier du Grand-Mulet à la station de l'Aiguille du Midi, l'un d'eux, Aimé Scheller, 36 ans, sertisseur, fut soudain atteint par un bloc qui s'était détaché et Sii lui fit une grave blessure à la tête, eux de ses compagnons demeurèrent auprès du blessé tandis que l'autre allait quérir du secours. Une colonne, organisée aussitôt, ramena le blessé à la station. M. Scheller reçut les soins d'un médecin français et fut descendu qu'aux Bossons en automobile. De là, il fut dirigé sur l'hôpital cantonal de Genève où il est mort lundi matin des suites d'une fracture du crâne. Il laisse une femme et une fillette. Un char à chien contre une motocyclette * Un petit char attelé d'un chien et appairtenant à M. François Savoy, demeurant à Bossonens (Èribourg), s'est jeté devant une motocyclette montée par M. Max Veraaud, pasteur à Mézières (Vaud), ayant en croupe son frère. La moto fut renversée avec ses deux occupants ; Je Téservoir à benzine s'étant débouché, l'eesence prit feu au contact du phare à acétylène et se communiqua aux vêtements de M. Vernaud. Une application de sacs mouillés l'éteignit. M. Vernaud a les sourcils et les cheveux légèrement brûlés et des contusions. La motocyclette, fort endommagée, a dû être conduite au garage. Grave accident d'automobile Sarnen, 28 août. Une automobile zurichoise occupée par 4 personnes, a fait une chute près de Lungern. Ses occupante ont été projetés hors de la voiture, Mme Jenny-tHirlimann, 35 ans, femme d un entrepreneur de Zurich, a eu la cage thoracique enfoncée. Un médecin qui circulait, par hasard à cet endroit, a fait transporter la malheureuse à Lungern où elle a succombé lundi matin. L'un des occupants a été également contusionné. Une automobile bousculée * Un oamion-automobite de la brasserie Muliler descendant, dimanche, au début de l'après-imidd, de Sainte-Croix SUT Vuitobœuf, a accroché, au premier grand tournant de la route, au-dessous du Château (Saimte-tCroix) une petite torpédo à trois places occupée par deux personnes et qui montait à Sainte-Croix. H l'a lancée avec violence contre le mur bordant la route. Les occupants de l'auto s'en tirent avec des blessures superficielles ; ils sont rentrés à Sainte-Croix, mais leur voiture gravement endommagée a dû être remorquée au grand garage des Remparts à Yverdon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Max Veraaud, pasteur à Mézières\n(Vaud)' and 'Genève' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Max Veraaud, pasteur à Mézières\n(Vaud)' near 'Genève' around 1928-08-28?
  4. Resolve temporal expressions relative to 1928-08-28. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 99 [ID: test_fr__232]:
  Publication date : 1981-02-18
  Language         : fr
  Person  : 'Favre'  (QID: N/A)
  Location: 'Berne'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "SUISSE dernière COMMISSION DES ETATS La Suissesse mariée garderait son droit de cité <LOCATION>Berne</LOCATION>, 17 (ATS).-La Commission du conseil des Etats chargée d'examiner le nouveau droit matrimonial, qui a terminé ses travaux mardi à Berne, a modifié sur quelques points le projet du Conseil fédéral.Elle a cependant accepté dans ses grandes lignes le projet gouvernemental et notamment le remplacement du régime actuel de l'union des biens par celui de la participation aux acquêts.Cet objet sera traité par le parlement au mois de mars.Au sujet du nom des époux, la Commission rejoint le Conseil fédéral dans son refus d'accorder le droit d'option qui permettrait aux fiancés de choisir le nom de l'épouse comme nom de famille.Mais la femme aura le droit non seulement de faire suivre son nom (<PERSON>Favre</PERSON>-Blanc), mais aussi de le faire précéder (Mme Blanc épouse Favre).La Commission n'a pas retenu la possibilité de l'option en raison de la tradition qui existe dans notre pays.En Allemagne fédérale, où le choix existe, seuls 4 % des époux en font usage.La nouvelle réglementation suisse facilitera- cependant l'adoption éventuelle par les fiancés, avant le mariage, du nom de la femme comme nom de famille.Mais il faudra de bonnes raisons pour l'autoriser (nom à consonnance étrangère, nom connu dans le commerce, la politique, etc).En ce qui concerne le droit de cité, la femme recevra, par le mariage, le droit de cité du mari mais sans perdre le sien.Une majorité s'est formée dans la Commission en faveur de cette solution."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.993

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Favre' and 'Berne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Favre' near 'Berne' around 1981-02-18?
  4. Resolve temporal expressions relative to 1981-02-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 100 [ID: test_fr__60]:
  Publication date : 1936-01-15
  Language         : fr
  Person  : 'Létrange'  (QID: N/A)
  Location: 'Ve arr'  (QID: Q238723)

  [ARTICLE TEXT — entity markers added]
  "Deux nouvelles inculpationsfrappent le surveillantcomplaisant valletM. Hude, juge d'instruction, a in¬ culpé hier le surveillant Vallet de cor¬ ruption de fonctionnaire, faux et usa¬ ge de faux. Tout d'abord, l'expertGebelin avait établi que tous les or¬ dres d'extraction, aussi bien ceux quisont entièrement faux que ceux quin'ont été que maquillés par additiond’un nom, avaient été préparés parla main du gardien de la Souricière.En particulier, l'ordre du 2 octobrequi permit à Pélissier de s’évader lelendemain et qui fut retrouvé le 4 à laSanté, est en entier de lui. Par ail¬ leurs, le petit carnet saisi sur Chris¬ tiane Pélissier établit qu’il avaittouché des sommes d'argent pour lalocation à la journée, de la cellulenuméro 10. Plusieurs autres dames,d'ailleurs, avec leurs maris détenus,ont contribué à alimenter la caissedu geôlier « compatissant ».Le versement des cotisationsd'assurances socialespour les chauffeurs de taxisLe ministère du Travail nous com¬ munique la note suivante :En application de l'article premier,paragraphe 3, du décret-loi du 28 oc¬ tobre 1935, modifiant le régime desAssurances sociales, les conducteursde voitures publiques, dont l'exploi¬ tation est assujettie à des tarifs detransport fixés par l'autorité publi¬ que, sont soumis au régime de l'assu¬ rance obligatoire, dès l'instant queleur rémunération n'excède pas lechiffre-limite prévu pour le bénéficede cette assurance.Les cotisations patronale et ouvriè¬ re sont dues depuis le premier jan¬ vier 1936.Conformément à l'article 3 de l'ar¬ rêté du 27 décembre 1935 paru auJournal Officiel du 29 décembre, lespourboires des intéressés, qui doi¬ vent entrer en compte pour la déter¬ mination de leur rémunération, se¬ ront évalués par des conventions col¬ lectives de travail, et, à défaut detelles conventions, par arrêtés du mi¬ nistre du Travail.L'unité syndicalechez les travailleurs de l'EtatLes sections de la Fédération uni¬ fiée des travailleurs de l'Etat (artil¬ lerie, poudreries, magasins adminis¬ tratifs, génie et aéronautique, em¬ ployés et agents de maîtrise, marinemilitaire, arts et métiers) ont tenuhier leurs assises patriculières dansles différentes salles de la Bourse duTravail.Voici les résultats définitifs du votepar mandats que le congrès de fusiondes deux Fédérations confédérée etunitaire avait été appelé à émettrelundi soir au sujet du cumul desfonctions syndicales et des mandatspolitiques. Contre : 287 voix ; pour :80 voix ; abstentions : 17 voix.PARTIS ET LIGUESGroupe des étudiants radicauxLa réunion du groupe des étu¬ diants radicaux de Paris aura lieuaujourd'hui mercredi, à 21 heures,au café « Chez Emile », 40, rue Ga¬ lande, et 10, rue Fouarre (angle desdeux rues).Fédération nationaledes Libres PenseursFédération de la Seine. — La com¬ mission spéciale d’unité d’action seréunira demain jeudi, à 21 heures,local habituel, rue de Châteaudun.Les responsables voudront bien êtreprésents.Parti radical-socialisteVersailles. — Les Comités radicaux¬ socialistes de la deuxième circons¬ cription de Versailles, réunis à Pois¬ sy, ont procédé à la constitution dila Fédération des Comités de cettecirconscription.Le bureau élu de la Fédération estainsi constitué : Président : RougelotHenri ; Secrétaire : Durand Fernand;Trésorier : Fourlon Pierre.Un ordre du jour a été voté décla¬ rant impossible le maintien de mi¬ nistres radicaux dans le gouverne¬ ment ; et demandant au bureau duComité Exécutif de proposer à laplus prochaine réunion du Comité lerefus de toute collaboration avec legouvernement actuel.Libre PenséeNous sommes heureux d'informer lepublic qu’une permanence de la 14esection de la Libre Pensée est ou¬ verte au numéro 47 de la rue Bé¬ nard (XIVe), à la Librairie des Tra¬ vailleurs.Le but de la Libre Pensée est de dé¬ velopper chez tous l’esprit critique etl'amour du libre examen, sans dis¬ tinction de parti, et de grouper dansson sein ceux qui se réclament de cehaut idéal. L’époque que nous vivonsest corrompue depuis des siècles parles croyances religieuses et leur amiedévouée Sa Majesté l'Argent qui gou¬ vernent le monde à leur seul bénéfice.Il est de notre devoir, pour nos en¬ fants et pour nous-mêmes, d'arracherce voile de l'au-delà et de mettre lemonde en face de ses nécessités réel¬ les. Chacun le peut dans son humblerôle ; la laïcité peut nous aider. Grou¬ pons-nous pour la défendre.Front populaireEpernay. — Dimanche après-midi,M. Eugène Frot, ancien ministre, adonné en la salle des fêtes d'Epernay(Marne) une conférence sous les aus¬ pices de la Ligue des Droits del'Homme et du Comité du Front Po¬ pulaire. Plus de 1.200 personnes yassistaient dont plusieurs élus radi¬ caux et socialistes de la région. M.Guerry, président, assisté de MM.Morange et Guen.MM. Eugène Frot, député, ancienministre, Bossus, conseiller munici¬ pal communiste de Paris, et EmileKahn, secrétaire général de la Liguedes Droits de l'Homme, ont pris suc¬ cessivement la parole très chaleu¬ reusement applaudis.La réunion se termina sans inci¬ dent. Dans la nuit, un membre de laSolidarité Française qui avait tentéde peindre des inscriptions injurieu¬ ses sur les murs de la Salle des Fêtesavait été surpris par la police. Il dé¬ clara avoir été inspiré dans son gestepar un discours du fils de M. Princequ'il avait entendu précédemment..XI<LOCATION>Ve arr</LOCATION>. — Pour la constitutiondes Comités de défense de la Répu¬ blique, trois grands meetings inaugu¬ raux sont organisés par le Front po¬ pulaire du 14e, aujourd'hui mercredi:111, rue du Château ; 115, rue Didot,1, avenue de la Porte-d'Orléans.Trente orateurs inscrits, dontRouffianges, Biquard, Croizat, Mau¬ vais, Paul Marcel, Graziani, MauriceLacroix, <PERSON>Létrange</PERSON>, Mension, etc...Ligue pour le Droit au Travailet le Progrès SocialVe arr — Une grande conférencesera donnée le vendredi 17 janvier,à 21 heures, à la Sorbonne, amphi¬ théâtre Richelieu, par Joseph Dubois,sur « L'Economie soviétique maî¬ tresse de ses destins ». Jacques Du¬ boin entretiendra ensuite les auditeursdu « Problème français ».Les cartes donnant droit aux placesréservées sont à la disposition des au¬ diteurs, au « Droit au Travail », 14,rue FavartViroflay. — Sous les auspices de lasection locaie des Droits de l'Homme,une grande réunion de propagandeaura lieu demain jeudi, à 21 heures,à la salie Robie, 134, route Navoù nos amis Chesneau et Ra,Martin exposeront les vérités dmiques diffusées par le « DroitTous nos amis et sympathisantssont cordialement invitésMaisons-Alfort. — L'Intersection dcanton de Charenton organisedredi 17 janvier, à 21 heures, ugrande réunion à la mairie dusons-Alfort, salle de la Justepaix. Nos camarades Compain mond Martin y parleront de « la révo¬ lution économique actuelle »."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: 5e arrondissement de Paris
    Description: arrondissement français
    Country: ['Q142']
    Located in: ['Q90']
    Aliases: {'fr': ['Paris 5e'], 'lb': ['arrondissement du Panthéon']}
    Coordinates: [{'lat': 48.847222222222, 'lon': 2.3444444444444}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1935" → 1935
      - "1936" → 1936
      - "1935" → 1935
    Temporal signal words: aujourd'hui, hier, ancien, plus, après
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.969

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Létrange' and 'Ve arr' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Létrange' near 'Ve arr' around 1936-01-15?
  4. Resolve temporal expressions relative to 1936-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 101 [ID: test_fr__2]:
  Publication date : 1948-02-23
  Language         : fr
  Person  : 'Bieler'  (QID: Q550992)
  Location: 'Montchoisi'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Le C. P. Zurich gagne Z le tournoi de hockey sur glace du Centenaire Samedi et dimanche, la patinoire de Monruz était une nouvelle fois entourée d'un nombreux public qui, bravant un froid très vif, suivit avec beaucoup d'intérêt le tournoi de hockey sur glace du Centenaire. Cette manifestation sportive fut pleinement réussie ; nous exprimons tefois un léger regret : pourquoi les trois rencontres ont-elles débuté avec dix à quinze minutes de retard ? Zurich bat <LOCATION>Montchoisi</LOCATION> par 12 à 8 (3-0, 6-3, 3-5) Les joueurs de Lausanne commencèrent par pratiquer un jeu passablement décousu : la défense était très lente et les avants trop individuels. Aussi tait-il une nette différence de classe entre les deux équipes en présence et Zurich, jouant avec beaucoup de décision, put dès l'abord s'octroyer un avantage de trois buts par Urson, <PERSON>Bieler</PERSON> et Ernst. Au cours du second tiers, les Zuricois relâchèrent un peu leur étreinte, alors que peu à peu l'on voyait Montchoisi s'organiser et attaquer avec mordant. Ce tiers fut ainsi assez équilibré, sans toutefois que les Zuricois perdent l'initiative du jeu. Ils marqueront cinq buts par Bieler (2), Urson, Sylvio Rossi, Boiler et Gugenbuhl, tandis que Banninger devait laisser passer trois tirs des Vaudois, deux de Minder et un de Caseel. Renversement de situation au dernier tiers où Montchoisi part résolument a l'attaque en montrant des qualités insoupçonnées. Le Lausannois Hennsler est particulièrement en verve et il marquera trois buts. D'autres attaques très bien menées permettront encore à Beltrami et à Caseel de diminuer l'écart du score. Mais la défense ne parvient pas à contenir les contre-attaques zuricoises et des shots bien placés de Rossi, Ernst et Boiler consolideront ment la victoire des joueurs de la Limmat. Zurich bat Young Sprinters par 10 à 2 (5-0. 1-2. 4-0) Cette partie, disons-le franchement, nous causa une certaine déception. L'on souhaitait une lutte plus équilibrée ; Young Sprinters est certainement capable de mieux résister à Zurich qu'il ne l'a fait hier matin. Nos joueurs, il est vrai, peuvent invoquer une circonstance atténuante. Hugo Delnon était malade et, de ce fait, la première ligne neuchâteloise était désorganisée. En outre. Reto n'apparut sur la glace qu'au début du second tiers. La première partie du jeu vit ainsi une très facile domination de Zurich. Des Bieler. Schubiger, Lohrer, semaient avec joie la panique dans notre camp et marquèrent cinq buts à intervalle régulier. Le second tiers nous fit espérer un redressement de la situation. Reto est là et il semble décider à bien faire. Il s'échappe par deux fois pour marquer deux superbes buts sans que le gardien Banninger puisse esquisser le moindre mouvement de défense. Mais l'équipe neuchâteloise continue à jouer avec une certaine incohérence. Les deux frères Delnon évoluent aveo le talentueux Ulrich, mais cette ligne manque de cohésion et plus rien ne réussira. Sylvio Rossi marquera au contraire un nouveau but. Dernier tiers assez monotone, les Zuricois sont supérieurs et ils parviendront sans trop d'efforts à accentuer leur avance par trois nouveaux buts réussis par Boiler, Gugenbuhl et Urson. Relevons dans le camp neuchâtelois la bonne partie du gardien Perrottet et la rapidité, la décision et le maniement de crosse d'Ulrich. Chez les Zuricois, il faut surtout louer la sûreté d'une défense très solide et un peu rude ; la première ligne formée de Bieler, Lohrer et Schubiger fut de loin la meilleure ligne du tournoi. Young Sprinters bat Montchoisi par 5 à 3 (2-0. 1-2. 2-1) Cette rencontre nous fait oublier la décevante partie disputée le matin. Les deux grands rivaux romands se livrent une lutte très ouverte et variée. Signalons quelques duels épiques entre Hans Cattini, Stucki, les deux frères Delnon et Ulrich. Remise de sa défaillance, notre équipe joua d'une manière digne d'elle-même et elle ne cessa de jouir d'une légère supériorité sur son adversaire. Reto et Othmar Delnon ouvrirent la marque au premier tiers. Les Lausannois placèrent leur effort principal sur le second tiers, mais notre défense formée de Tinembart et du Dr Grether, ainsi que du gardien Perrottet, dans une forme exceptionnelle dimanche, parvinrent à endiguer leurs assauts à l'exception de deux qui permirent à Jansky et à Beltrami de loger le puck au fond de la cage neuchâteloise. Le dernier tiers, au cours duquel le jeu devient assez dur, permit à Young Sprinters de s'assurer une victoire méritée. Jansky profita tout d'abord judicieusement d'une erreur de notre défense, mais Othmar Delnon trompera deux fois encore le gardien Ayer. Relevons l'excellent travail d'Ulrich. Rapide, poussant jusqu'au bout chaque descente, ne considérant jamais perdue une passe, il mena avec brio les attaques de notre notro seconde ligne et certains de ses shots auraient mérité le but. Le palmarès A la suite de ces rencontre, Zurich gagne le tournoi aveo quatre points, suivi de Young Sprinters (2 p.) et Mont _, choisi (0 p.). Lo C. P. Zurich gagne le premier prix du tournoi, la grande distinction du Centenaire et le challenge du tournoi. Young Sprinters obtient la deuxième distinction du Centenaire et le challenge Vuillomenet, récompensant l'équipe jouant avec le plus de fair-play. Quant à Montchoisi, il reçoit la coupe offerte par le cinéma Palace. B. Ad. Une tournée de Young Sprinters en Tchécoslovaquie Notre équipe de hockey sur glace a été invitée à disputer un certain nombre de matches en Tchécoslovaquie, notamment contre Prague et Brno. Elle partira pour ce pays au début du mois de mars et sera renforcée par quelques autres joueurs de ligue nationale A."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Alfred Bieler
    Description: joueur professionnel de hockey sur glace suisse
    Born: ['+1923-04-18T00:00:00Z']
    Died: ['+2013-04-24T00:00:00Z']
    Birth place: ['Saint-Moritz']
    Death place: ['Zurich']
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.971

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Bieler' and 'Montchoisi' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Bieler' near 'Montchoisi' around 1948-02-23?
  4. Resolve temporal expressions relative to 1948-02-23. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 102 [ID: test_fr__87]:
  Publication date : 1968-04-08
  Language         : fr
  Person  : 'Fischer'  (QID: N/A)
  Location: 'Suisse'  (QID: Q39)

  [ARTICLE TEXT — entity markers added]
  "Bioiiey remporte le Tour du Léman à Genève Deux importantes épreuves pour nos amateurs d'élite A l'échelon des amateurs-elites, le weekend était d'importance à Genève. Oscar Plattner, grand responsable de cette catégorie d'éventuels futurs champions, avait délégué ses pouvoirs à Gilbert Perrenoud, afin qu'il suive très attentivement ce qui se passait sur les routes. Le Comité national a, en effet, l'intention très arrêtée de mettre sur pied la meilleure équipe possible pour le Tour de l'Avenir, les Jeux olympiques et les championnats du monde. Tout un programme de sélection a ainsi été mis au point. Dimanche à midi, Gilbert Perrenoud se déclarait enchanté de ce qu'il avait vu. Non pas que l'on puisse immédiatement dire que les coureurs suisses sont en forme, mais les sujets de satisfaction ne manquaient pas : « on voit que nous sommes dans une année importante, une année où les voyages et les honneurs seront nombreux. Il y a l'Uruguay, le Mexique, des médailles à revendre. C'est pourquoi nos meilleurs coureurs se sont préparés de belle façon, c'est pourquoi aussi de nombreux jeunes frappent à la porte .. En fait, ces deux courses genevoises ont permis de nombreux enseignements. Animées toutes deux, courues assez rapidement, elles se sont révélées d'une excellente qualité. D'OESCHGER... Samedi après-midi, sur un circuit de seize kiolmètres à parcourir huit fois, quelque soixante-cinq coureurs prirent le départ. Sous le soleil, qui allait bientôt disparaître, et faire place à un violent orage. L'échappée, la bonne, vint très rapidement. Au deuxième tour déjà, après qu'un « faux départ » eut lieu, à savoir une erreur de parcours annulant les efforts des premiers audacieux. Fait assez rare, la course fut stoppée à 9 km 400 de son premier départ puis relancée. C'est alors que l'un des Belges invités, froidement, tenta de partir. Il y parvint en compagnie de Rub, d'Oeschger, de Schnetzler, le champion de <LOCATION>Suisse</LOCATION>, von Arx, <PERSON>Fischer</PERSON>, et les Romands Behier (Moudon), Regamey (Yverdon) et Vaucher (Lausanne). Cahin-caha, sur de petites routes, étroites et sinueuses, cette échappée prit quelque avance. Sur le peloton tout d'abord, sur un groupe de contre-attaque par la suite, qui allait faire sa jonction. D'ailleurs, il ne resta plus que ces hommes en course... Les autres pensaient au tour du lac du lendemain, et se retiraient II y a encore quelques audacieux : Schnetzler, Spannagel, Birrer et Weber. Mais leurs tentatives solitaires furent réduites à néant. Et sur la fin, le peloton se scinda en deux. . . . A BIOLLEY Ce tour du lac — doyenne des épreuves cyclistes, qui en était hier à sa 76 mc édition — eut un déroulement assez rare. Daniel Biolley, de Fribourg, l'expliqua une fois passée, en vainqueur, la ligne d' arrivée : « C'est mon sixième- tour du lac. Et j'avais jusqu'ici constaté que jamais une échappée partie de loin ne réussissait Aussi je n'ai pas mené depuis Versoix (km 10) où nous sommes partis. Mais comme à Evian, en abordant le col de Vinzier, nous avions plus de cinq minutes sur nos poursuivants, et plus de dix sur le peloton _, je me suis lancé dans la bagarre. » La course partit en effet très tôt : Brunner — qui allait vite disparaître — Lier, Hofer et Grin s'en allèrent vers l'entrée de l'autoroute Genève-Lausanne. Rapidement Biolley, Angelucci, Elliker, Kalt, Rennhard, Rutchmann, Thalmann, Reusser, Adam, Schneider et Melliflio les rejoignirent Et, au gré des kilomètres, de la forme de certains ou de divers ennuis mécaniques, il resta dix hommes ensemble à Evian, dont quatre partirent bien vite dès les premières côtes de la seule difficulté de la journée, quatre qui restèrent ensemble jusqu'à l'arrivée où se produisit un petit drame : Lier sprinta, gagna, mais ne savait pas qu'il y avait un tour et la distance à faire... Biolley passa donc, de même que Rennhardt. Les deux coéquipiers (d'Allegro) avaient des mines patibulaires à l'arrivée. Lier pleurait et Biolley n'était pas plus content que cela : « La victoire lui revenait il avait fait une grosse part de travail. Mais je ne pouvais pas me relever, car Rennhard avait passé. Serge DOURNOW CLASSEMENT DU GRAND PRIX DE MEINIER 1. Oeschger (Oberhofen), les 128 km en 3 h 32'13 " ; 2. Rub (Bmgg) ; 3. Fischer (Brugg) ; 4. Binggeli (Genève ; 5. Regamey (Yverdon). CLASSEMENT DU TOUR DU LÉMAN 1. Biolley (Fribourg), les 187 km en 4 h 30'36 " ; 2. Rennhard (Brugg) ; 3. Lier (Affoltern) ; 4. Thalmann (Meznau), même temps ; 5. Rutschmann (Seuzach), à 3'32 " ; 6. Hofer (Berne) ; 7. Kalt (Zurich) ; 8. Elliker (Urdorf) ; 9. Reusser (Brugg), même temps ; 10. Peter (Zurich), à 7'40 "."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.959

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Fischer' and 'Suisse' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Fischer' near 'Suisse' around 1968-04-08?
  4. Resolve temporal expressions relative to 1968-04-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 103 [ID: test_fr__95]:
  Publication date : 1968-04-08
  Language         : fr
  Person  : 'Rub'  (QID: Q19581676)
  Location: 'LÉMAN'  (QID: Q28806)

  [ARTICLE TEXT — entity markers added]
  "Bioiiey remporte le Tour du Léman à Genève Deux importantes épreuves pour nos amateurs d'élite A l'échelon des amateurs-elites, le weekend était d'importance à Genève. Oscar Plattner, grand responsable de cette catégorie d'éventuels futurs champions, avait délégué ses pouvoirs à Gilbert Perrenoud, afin qu'il suive très attentivement ce qui se passait sur les routes. Le Comité national a, en effet, l'intention très arrêtée de mettre sur pied la meilleure équipe possible pour le Tour de l'Avenir, les Jeux olympiques et les championnats du monde. Tout un programme de sélection a ainsi été mis au point. Dimanche à midi, Gilbert Perrenoud se déclarait enchanté de ce qu'il avait vu. Non pas que l'on puisse immédiatement dire que les coureurs suisses sont en forme, mais les sujets de satisfaction ne manquaient pas : « on voit que nous sommes dans une année importante, une année où les voyages et les honneurs seront nombreux. Il y a l'Uruguay, le Mexique, des médailles à revendre. C'est pourquoi nos meilleurs coureurs se sont préparés de belle façon, c'est pourquoi aussi de nombreux jeunes frappent à la porte .. En fait, ces deux courses genevoises ont permis de nombreux enseignements. Animées toutes deux, courues assez rapidement, elles se sont révélées d'une excellente qualité. D'OESCHGER... Samedi après-midi, sur un circuit de seize kiolmètres à parcourir huit fois, quelque soixante-cinq coureurs prirent le départ. Sous le soleil, qui allait bientôt disparaître, et faire place à un violent orage. L'échappée, la bonne, vint très rapidement. Au deuxième tour déjà, après qu'un « faux départ » eut lieu, à savoir une erreur de parcours annulant les efforts des premiers audacieux. Fait assez rare, la course fut stoppée à 9 km 400 de son premier départ puis relancée. C'est alors que l'un des Belges invités, froidement, tenta de partir. Il y parvint en compagnie de <PERSON>Rub</PERSON>, d'Oeschger, de Schnetzler, le champion de Suisse, von Arx, Fischer, et les Romands Behier (Moudon), Regamey (Yverdon) et Vaucher (Lausanne). Cahin-caha, sur de petites routes, étroites et sinueuses, cette échappée prit quelque avance. Sur le peloton tout d'abord, sur un groupe de contre-attaque par la suite, qui allait faire sa jonction. D'ailleurs, il ne resta plus que ces hommes en course... Les autres pensaient au tour du lac du lendemain, et se retiraient II y a encore quelques audacieux : Schnetzler, Spannagel, Birrer et Weber. Mais leurs tentatives solitaires furent réduites à néant. Et sur la fin, le peloton se scinda en deux. . . . A BIOLLEY Ce tour du lac — doyenne des épreuves cyclistes, qui en était hier à sa 76 mc édition — eut un déroulement assez rare. Daniel Biolley, de Fribourg, l'expliqua une fois passée, en vainqueur, la ligne d' arrivée : « C'est mon sixième- tour du lac. Et j'avais jusqu'ici constaté que jamais une échappée partie de loin ne réussissait Aussi je n'ai pas mené depuis Versoix (km 10) où nous sommes partis. Mais comme à Evian, en abordant le col de Vinzier, nous avions plus de cinq minutes sur nos poursuivants, et plus de dix sur le peloton _, je me suis lancé dans la bagarre. » La course partit en effet très tôt : Brunner — qui allait vite disparaître — Lier, Hofer et Grin s'en allèrent vers l'entrée de l'autoroute Genève-Lausanne. Rapidement Biolley, Angelucci, Elliker, Kalt, Rennhard, Rutchmann, Thalmann, Reusser, Adam, Schneider et Melliflio les rejoignirent Et, au gré des kilomètres, de la forme de certains ou de divers ennuis mécaniques, il resta dix hommes ensemble à Evian, dont quatre partirent bien vite dès les premières côtes de la seule difficulté de la journée, quatre qui restèrent ensemble jusqu'à l'arrivée où se produisit un petit drame : Lier sprinta, gagna, mais ne savait pas qu'il y avait un tour et la distance à faire... Biolley passa donc, de même que Rennhardt. Les deux coéquipiers (d'Allegro) avaient des mines patibulaires à l'arrivée. Lier pleurait et Biolley n'était pas plus content que cela : « La victoire lui revenait il avait fait une grosse part de travail. Mais je ne pouvais pas me relever, car Rennhard avait passé. Serge DOURNOW CLASSEMENT DU GRAND PRIX DE MEINIER 1. Oeschger (Oberhofen), les 128 km en 3 h 32'13 " ; 2. Rub (Bmgg) ; 3. Fischer (Brugg) ; 4. Binggeli (Genève ; 5. Regamey (Yverdon). CLASSEMENT DU TOUR DU <LOCATION>LÉMAN</LOCATION> 1. Biolley (Fribourg), les 187 km en 4 h 30'36 " ; 2. Rennhard (Brugg) ; 3. Lier (Affoltern) ; 4. Thalmann (Meznau), même temps ; 5. Rutschmann (Seuzach), à 3'32 " ; 6. Hofer (Berne) ; 7. Kalt (Zurich) ; 8. Elliker (Urdorf) ; 9. Reusser (Brugg), même temps ; 10. Peter (Zurich), à 7'40 "."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Kurt Rub
    Description: cycliste suisse
    Born: ['+1946-02-28T00:00:00Z']
    Birth place: ['Q65002']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.959

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Rub' and 'LÉMAN' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Rub' near 'LÉMAN' around 1968-04-08?
  4. Resolve temporal expressions relative to 1968-04-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 104 [ID: test_fr__0]:
  Publication date : 1948-02-23
  Language         : fr
  Person  : 'B. Ad.'  (QID: N/A)
  Location: 'Tchécoslovaquie'  (QID: Q33946)

  [ARTICLE TEXT — entity markers added]
  "Le C. P. Zurich gagne Z le tournoi de hockey sur glace du Centenaire Samedi et dimanche, la patinoire de Monruz était une nouvelle fois entourée d'un nombreux public qui, bravant un froid très vif, suivit avec beaucoup d'intérêt le tournoi de hockey sur glace du Centenaire. Cette manifestation sportive fut pleinement réussie ; nous exprimons tefois un léger regret : pourquoi les trois rencontres ont-elles débuté avec dix à quinze minutes de retard ? Zurich bat Montchoisi par 12 à 8 (3-0, 6-3, 3-5) Les joueurs de Lausanne commencèrent par pratiquer un jeu passablement décousu : la défense était très lente et les avants trop individuels. Aussi tait-il une nette différence de classe entre les deux équipes en présence et Zurich, jouant avec beaucoup de décision, put dès l'abord s'octroyer un avantage de trois buts par Urson, Bieler et Ernst. Au cours du second tiers, les Zuricois relâchèrent un peu leur étreinte, alors que peu à peu l'on voyait Montchoisi s'organiser et attaquer avec mordant. Ce tiers fut ainsi assez équilibré, sans toutefois que les Zuricois perdent l'initiative du jeu. Ils marqueront cinq buts par Bieler (2), Urson, Sylvio Rossi, Boiler et Gugenbuhl, tandis que Banninger devait laisser passer trois tirs des Vaudois, deux de Minder et un de Caseel. Renversement de situation au dernier tiers où Montchoisi part résolument a l'attaque en montrant des qualités insoupçonnées. Le Lausannois Hennsler est particulièrement en verve et il marquera trois buts. D'autres attaques très bien menées permettront encore à Beltrami et à Caseel de diminuer l'écart du score. Mais la défense ne parvient pas à contenir les contre-attaques zuricoises et des shots bien placés de Rossi, Ernst et Boiler consolideront ment la victoire des joueurs de la Limmat. Zurich bat Young Sprinters par 10 à 2 (5-0. 1-2. 4-0) Cette partie, disons-le franchement, nous causa une certaine déception. L'on souhaitait une lutte plus équilibrée ; Young Sprinters est certainement capable de mieux résister à Zurich qu'il ne l'a fait hier matin. Nos joueurs, il est vrai, peuvent invoquer une circonstance atténuante. Hugo Delnon était malade et, de ce fait, la première ligne neuchâteloise était désorganisée. En outre. Reto n'apparut sur la glace qu'au début du second tiers. La première partie du jeu vit ainsi une très facile domination de Zurich. Des Bieler. Schubiger, Lohrer, semaient avec joie la panique dans notre camp et marquèrent cinq buts à intervalle régulier. Le second tiers nous fit espérer un redressement de la situation. Reto est là et il semble décider à bien faire. Il s'échappe par deux fois pour marquer deux superbes buts sans que le gardien Banninger puisse esquisser le moindre mouvement de défense. Mais l'équipe neuchâteloise continue à jouer avec une certaine incohérence. Les deux frères Delnon évoluent aveo le talentueux Ulrich, mais cette ligne manque de cohésion et plus rien ne réussira. Sylvio Rossi marquera au contraire un nouveau but. Dernier tiers assez monotone, les Zuricois sont supérieurs et ils parviendront sans trop d'efforts à accentuer leur avance par trois nouveaux buts réussis par Boiler, Gugenbuhl et Urson. Relevons dans le camp neuchâtelois la bonne partie du gardien Perrottet et la rapidité, la décision et le maniement de crosse d'Ulrich. Chez les Zuricois, il faut surtout louer la sûreté d'une défense très solide et un peu rude ; la première ligne formée de Bieler, Lohrer et Schubiger fut de loin la meilleure ligne du tournoi. Young Sprinters bat Montchoisi par 5 à 3 (2-0. 1-2. 2-1) Cette rencontre nous fait oublier la décevante partie disputée le matin. Les deux grands rivaux romands se livrent une lutte très ouverte et variée. Signalons quelques duels épiques entre Hans Cattini, Stucki, les deux frères Delnon et Ulrich. Remise de sa défaillance, notre équipe joua d'une manière digne d'elle-même et elle ne cessa de jouir d'une légère supériorité sur son adversaire. Reto et Othmar Delnon ouvrirent la marque au premier tiers. Les Lausannois placèrent leur effort principal sur le second tiers, mais notre défense formée de Tinembart et du Dr Grether, ainsi que du gardien Perrottet, dans une forme exceptionnelle dimanche, parvinrent à endiguer leurs assauts à l'exception de deux qui permirent à Jansky et à Beltrami de loger le puck au fond de la cage neuchâteloise. Le dernier tiers, au cours duquel le jeu devient assez dur, permit à Young Sprinters de s'assurer une victoire méritée. Jansky profita tout d'abord judicieusement d'une erreur de notre défense, mais Othmar Delnon trompera deux fois encore le gardien Ayer. Relevons l'excellent travail d'Ulrich. Rapide, poussant jusqu'au bout chaque descente, ne considérant jamais perdue une passe, il mena avec brio les attaques de notre notro seconde ligne et certains de ses shots auraient mérité le but. Le palmarès A la suite de ces rencontre, Zurich gagne le tournoi aveo quatre points, suivi de Young Sprinters (2 p.) et Mont _, choisi (0 p.). Lo C. P. Zurich gagne le premier prix du tournoi, la grande distinction du Centenaire et le challenge du tournoi. Young Sprinters obtient la deuxième distinction du Centenaire et le challenge Vuillomenet, récompensant l'équipe jouant avec le plus de fair-play. Quant à Montchoisi, il reçoit la coupe offerte par le cinéma Palace. <PERSON>B. Ad.</PERSON> Une tournée de Young Sprinters en <LOCATION>Tchécoslovaquie</LOCATION> Notre équipe de hockey sur glace a été invitée à disputer un certain nombre de matches en Tchécoslovaquie, notamment contre Prague et Brno. Elle partira pour ce pays au début du mois de mars et sera renforcée par quelques autres joueurs de ligue nationale A."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Tchécoslovaquie
    Description: ancien pays européen (1918-1992)
    Country: ['Tchécoslovaquie']
    Aliases: {'en': ['Czecho-Slovakia', 'cs', 'TCH', 'Československo', 'Federation of Czechoslovakia', "People's Republic of Czechoslovakia"], 'fr': ['Tchecoslovaquie', 'République tchécoslovaque', 'Tchéco-Slovaquie', 'République socialiste tchécoslovaque', 'République fédérale tchèque et slovaque', 'Tchéc.'], 'de': ['Tschechoslowakisch', 'ČSR', 'Tschecho-Slowakei', 'Tschechoslowakische Sozialistische Republik', 'Republik Tschecho-Slowakei', 'Tschecho-Slowakische Republik', 'Tschechoslowakische Republik', 'Republik Tschechoslowakei', 'Tschechische und Slowakische Föderative Republik']}
    Coordinates: [{'lat': 50.083333333333, 'lon': 14.416666666667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.971

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'B. Ad.' and 'Tchécoslovaquie' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'B. Ad.' near 'Tchécoslovaquie' around 1948-02-23?
  4. Resolve temporal expressions relative to 1948-02-23. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 105 [ID: test_fr__56]:
  Publication date : 1936-01-15
  Language         : fr
  Person  : 'Paul Marcel'  (QID: Q877804)
  Location: 'Ve arr'  (QID: Q238723)

  [ARTICLE TEXT — entity markers added]
  "Deux nouvelles inculpationsfrappent le surveillantcomplaisant valletM. Hude, juge d'instruction, a in¬ culpé hier le surveillant Vallet de cor¬ ruption de fonctionnaire, faux et usa¬ ge de faux. Tout d'abord, l'expertGebelin avait établi que tous les or¬ dres d'extraction, aussi bien ceux quisont entièrement faux que ceux quin'ont été que maquillés par additiond’un nom, avaient été préparés parla main du gardien de la Souricière.En particulier, l'ordre du 2 octobrequi permit à Pélissier de s’évader lelendemain et qui fut retrouvé le 4 à laSanté, est en entier de lui. Par ail¬ leurs, le petit carnet saisi sur Chris¬ tiane Pélissier établit qu’il avaittouché des sommes d'argent pour lalocation à la journée, de la cellulenuméro 10. Plusieurs autres dames,d'ailleurs, avec leurs maris détenus,ont contribué à alimenter la caissedu geôlier « compatissant ».Le versement des cotisationsd'assurances socialespour les chauffeurs de taxisLe ministère du Travail nous com¬ munique la note suivante :En application de l'article premier,paragraphe 3, du décret-loi du 28 oc¬ tobre 1935, modifiant le régime desAssurances sociales, les conducteursde voitures publiques, dont l'exploi¬ tation est assujettie à des tarifs detransport fixés par l'autorité publi¬ que, sont soumis au régime de l'assu¬ rance obligatoire, dès l'instant queleur rémunération n'excède pas lechiffre-limite prévu pour le bénéficede cette assurance.Les cotisations patronale et ouvriè¬ re sont dues depuis le premier jan¬ vier 1936.Conformément à l'article 3 de l'ar¬ rêté du 27 décembre 1935 paru auJournal Officiel du 29 décembre, lespourboires des intéressés, qui doi¬ vent entrer en compte pour la déter¬ mination de leur rémunération, se¬ ront évalués par des conventions col¬ lectives de travail, et, à défaut detelles conventions, par arrêtés du mi¬ nistre du Travail.L'unité syndicalechez les travailleurs de l'EtatLes sections de la Fédération uni¬ fiée des travailleurs de l'Etat (artil¬ lerie, poudreries, magasins adminis¬ tratifs, génie et aéronautique, em¬ ployés et agents de maîtrise, marinemilitaire, arts et métiers) ont tenuhier leurs assises patriculières dansles différentes salles de la Bourse duTravail.Voici les résultats définitifs du votepar mandats que le congrès de fusiondes deux Fédérations confédérée etunitaire avait été appelé à émettrelundi soir au sujet du cumul desfonctions syndicales et des mandatspolitiques. Contre : 287 voix ; pour :80 voix ; abstentions : 17 voix.PARTIS ET LIGUESGroupe des étudiants radicauxLa réunion du groupe des étu¬ diants radicaux de Paris aura lieuaujourd'hui mercredi, à 21 heures,au café « Chez Emile », 40, rue Ga¬ lande, et 10, rue Fouarre (angle desdeux rues).Fédération nationaledes Libres PenseursFédération de la Seine. — La com¬ mission spéciale d’unité d’action seréunira demain jeudi, à 21 heures,local habituel, rue de Châteaudun.Les responsables voudront bien êtreprésents.Parti radical-socialisteVersailles. — Les Comités radicaux¬ socialistes de la deuxième circons¬ cription de Versailles, réunis à Pois¬ sy, ont procédé à la constitution dila Fédération des Comités de cettecirconscription.Le bureau élu de la Fédération estainsi constitué : Président : RougelotHenri ; Secrétaire : Durand Fernand;Trésorier : Fourlon Pierre.Un ordre du jour a été voté décla¬ rant impossible le maintien de mi¬ nistres radicaux dans le gouverne¬ ment ; et demandant au bureau duComité Exécutif de proposer à laplus prochaine réunion du Comité lerefus de toute collaboration avec legouvernement actuel.Libre PenséeNous sommes heureux d'informer lepublic qu’une permanence de la 14esection de la Libre Pensée est ou¬ verte au numéro 47 de la rue Bé¬ nard (XIVe), à la Librairie des Tra¬ vailleurs.Le but de la Libre Pensée est de dé¬ velopper chez tous l’esprit critique etl'amour du libre examen, sans dis¬ tinction de parti, et de grouper dansson sein ceux qui se réclament de cehaut idéal. L’époque que nous vivonsest corrompue depuis des siècles parles croyances religieuses et leur amiedévouée Sa Majesté l'Argent qui gou¬ vernent le monde à leur seul bénéfice.Il est de notre devoir, pour nos en¬ fants et pour nous-mêmes, d'arracherce voile de l'au-delà et de mettre lemonde en face de ses nécessités réel¬ les. Chacun le peut dans son humblerôle ; la laïcité peut nous aider. Grou¬ pons-nous pour la défendre.Front populaireEpernay. — Dimanche après-midi,M. Eugène Frot, ancien ministre, adonné en la salle des fêtes d'Epernay(Marne) une conférence sous les aus¬ pices de la Ligue des Droits del'Homme et du Comité du Front Po¬ pulaire. Plus de 1.200 personnes yassistaient dont plusieurs élus radi¬ caux et socialistes de la région. M.Guerry, président, assisté de MM.Morange et Guen.MM. Eugène Frot, député, ancienministre, Bossus, conseiller munici¬ pal communiste de Paris, et EmileKahn, secrétaire général de la Liguedes Droits de l'Homme, ont pris suc¬ cessivement la parole très chaleu¬ reusement applaudis.La réunion se termina sans inci¬ dent. Dans la nuit, un membre de laSolidarité Française qui avait tentéde peindre des inscriptions injurieu¬ ses sur les murs de la Salle des Fêtesavait été surpris par la police. Il dé¬ clara avoir été inspiré dans son gestepar un discours du fils de M. Princequ'il avait entendu précédemment..XI<LOCATION>Ve arr</LOCATION>. — Pour la constitutiondes Comités de défense de la Répu¬ blique, trois grands meetings inaugu¬ raux sont organisés par le Front po¬ pulaire du 14e, aujourd'hui mercredi:111, rue du Château ; 115, rue Didot,1, avenue de la Porte-d'Orléans.Trente orateurs inscrits, dontRouffianges, Biquard, Croizat, Mau¬ vais, <PERSON>Paul Marcel</PERSON>, Graziani, MauriceLacroix, Létrange, Mension, etc...Ligue pour le Droit au Travailet le Progrès SocialVe arr — Une grande conférencesera donnée le vendredi 17 janvier,à 21 heures, à la Sorbonne, amphi¬ théâtre Richelieu, par Joseph Dubois,sur « L'Economie soviétique maî¬ tresse de ses destins ». Jacques Du¬ boin entretiendra ensuite les auditeursdu « Problème français ».Les cartes donnant droit aux placesréservées sont à la disposition des au¬ diteurs, au « Droit au Travail », 14,rue FavartViroflay. — Sous les auspices de lasection locaie des Droits de l'Homme,une grande réunion de propagandeaura lieu demain jeudi, à 21 heures,à la salie Robie, 134, route Navoù nos amis Chesneau et Ra,Martin exposeront les vérités dmiques diffusées par le « DroitTous nos amis et sympathisantssont cordialement invitésMaisons-Alfort. — L'Intersection dcanton de Charenton organisedredi 17 janvier, à 21 heures, ugrande réunion à la mairie dusons-Alfort, salle de la Justepaix. Nos camarades Compain mond Martin y parleront de « la révo¬ lution économique actuelle »."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1935" → 1935
      - "1936" → 1936
      - "1935" → 1935
    Temporal signal words: aujourd'hui, hier, ancien, plus, après
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.969

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Paul Marcel' and 'Ve arr' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Paul Marcel' near 'Ve arr' around 1936-01-15?
  4. Resolve temporal expressions relative to 1936-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 106 [ID: test_fr__7]:
  Publication date : 1948-02-23
  Language         : fr
  Person  : 'Rossi'  (QID: N/A)
  Location: 'Limmat'  (QID: Q14338)

  [ARTICLE TEXT — entity markers added]
  "Le C. P. Zurich gagne Z le tournoi de hockey sur glace du Centenaire Samedi et dimanche, la patinoire de Monruz était une nouvelle fois entourée d'un nombreux public qui, bravant un froid très vif, suivit avec beaucoup d'intérêt le tournoi de hockey sur glace du Centenaire. Cette manifestation sportive fut pleinement réussie ; nous exprimons tefois un léger regret : pourquoi les trois rencontres ont-elles débuté avec dix à quinze minutes de retard ? Zurich bat Montchoisi par 12 à 8 (3-0, 6-3, 3-5) Les joueurs de Lausanne commencèrent par pratiquer un jeu passablement décousu : la défense était très lente et les avants trop individuels. Aussi tait-il une nette différence de classe entre les deux équipes en présence et Zurich, jouant avec beaucoup de décision, put dès l'abord s'octroyer un avantage de trois buts par Urson, Bieler et Ernst. Au cours du second tiers, les Zuricois relâchèrent un peu leur étreinte, alors que peu à peu l'on voyait Montchoisi s'organiser et attaquer avec mordant. Ce tiers fut ainsi assez équilibré, sans toutefois que les Zuricois perdent l'initiative du jeu. Ils marqueront cinq buts par Bieler (2), Urson, Sylvio <PERSON>Rossi</PERSON>, Boiler et Gugenbuhl, tandis que Banninger devait laisser passer trois tirs des Vaudois, deux de Minder et un de Caseel. Renversement de situation au dernier tiers où Montchoisi part résolument a l'attaque en montrant des qualités insoupçonnées. Le Lausannois Hennsler est particulièrement en verve et il marquera trois buts. D'autres attaques très bien menées permettront encore à Beltrami et à Caseel de diminuer l'écart du score. Mais la défense ne parvient pas à contenir les contre-attaques zuricoises et des shots bien placés de Rossi, Ernst et Boiler consolideront ment la victoire des joueurs de la <LOCATION>Limmat</LOCATION>. Zurich bat Young Sprinters par 10 à 2 (5-0. 1-2. 4-0) Cette partie, disons-le franchement, nous causa une certaine déception. L'on souhaitait une lutte plus équilibrée ; Young Sprinters est certainement capable de mieux résister à Zurich qu'il ne l'a fait hier matin. Nos joueurs, il est vrai, peuvent invoquer une circonstance atténuante. Hugo Delnon était malade et, de ce fait, la première ligne neuchâteloise était désorganisée. En outre. Reto n'apparut sur la glace qu'au début du second tiers. La première partie du jeu vit ainsi une très facile domination de Zurich. Des Bieler. Schubiger, Lohrer, semaient avec joie la panique dans notre camp et marquèrent cinq buts à intervalle régulier. Le second tiers nous fit espérer un redressement de la situation. Reto est là et il semble décider à bien faire. Il s'échappe par deux fois pour marquer deux superbes buts sans que le gardien Banninger puisse esquisser le moindre mouvement de défense. Mais l'équipe neuchâteloise continue à jouer avec une certaine incohérence. Les deux frères Delnon évoluent aveo le talentueux Ulrich, mais cette ligne manque de cohésion et plus rien ne réussira. Sylvio Rossi marquera au contraire un nouveau but. Dernier tiers assez monotone, les Zuricois sont supérieurs et ils parviendront sans trop d'efforts à accentuer leur avance par trois nouveaux buts réussis par Boiler, Gugenbuhl et Urson. Relevons dans le camp neuchâtelois la bonne partie du gardien Perrottet et la rapidité, la décision et le maniement de crosse d'Ulrich. Chez les Zuricois, il faut surtout louer la sûreté d'une défense très solide et un peu rude ; la première ligne formée de Bieler, Lohrer et Schubiger fut de loin la meilleure ligne du tournoi. Young Sprinters bat Montchoisi par 5 à 3 (2-0. 1-2. 2-1) Cette rencontre nous fait oublier la décevante partie disputée le matin. Les deux grands rivaux romands se livrent une lutte très ouverte et variée. Signalons quelques duels épiques entre Hans Cattini, Stucki, les deux frères Delnon et Ulrich. Remise de sa défaillance, notre équipe joua d'une manière digne d'elle-même et elle ne cessa de jouir d'une légère supériorité sur son adversaire. Reto et Othmar Delnon ouvrirent la marque au premier tiers. Les Lausannois placèrent leur effort principal sur le second tiers, mais notre défense formée de Tinembart et du Dr Grether, ainsi que du gardien Perrottet, dans une forme exceptionnelle dimanche, parvinrent à endiguer leurs assauts à l'exception de deux qui permirent à Jansky et à Beltrami de loger le puck au fond de la cage neuchâteloise. Le dernier tiers, au cours duquel le jeu devient assez dur, permit à Young Sprinters de s'assurer une victoire méritée. Jansky profita tout d'abord judicieusement d'une erreur de notre défense, mais Othmar Delnon trompera deux fois encore le gardien Ayer. Relevons l'excellent travail d'Ulrich. Rapide, poussant jusqu'au bout chaque descente, ne considérant jamais perdue une passe, il mena avec brio les attaques de notre notro seconde ligne et certains de ses shots auraient mérité le but. Le palmarès A la suite de ces rencontre, Zurich gagne le tournoi aveo quatre points, suivi de Young Sprinters (2 p.) et Mont _, choisi (0 p.). Lo C. P. Zurich gagne le premier prix du tournoi, la grande distinction du Centenaire et le challenge du tournoi. Young Sprinters obtient la deuxième distinction du Centenaire et le challenge Vuillomenet, récompensant l'équipe jouant avec le plus de fair-play. Quant à Montchoisi, il reçoit la coupe offerte par le cinéma Palace. B. Ad. Une tournée de Young Sprinters en Tchécoslovaquie Notre équipe de hockey sur glace a été invitée à disputer un certain nombre de matches en Tchécoslovaquie, notamment contre Prague et Brno. Elle partira pour ce pays au début du mois de mars et sera renforcée par quelques autres joueurs de ligue nationale A."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Limmat
    Description: rivière suisse
    Country: ['Suisse']
    Located in: ['canton de Zurich', "canton d'Argovie"]
    Aliases: {'de': ['Limmig (aargauischen Unterlauf)']}
    Coordinates: [{'lat': 47.366342, 'lon': 8.543351}, {'lat': 47.501794, 'lon': 8.236313}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.971

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Rossi' and 'Limmat' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Rossi' near 'Limmat' around 1948-02-23?
  4. Resolve temporal expressions relative to 1948-02-23. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 107 [ID: test_fr__179]:
  Publication date : NA
  Language         : fr
  Person  : 'Saugé'  (QID: N/A)
  Location: 'Montlhéry'  (QID: Q250024)

  [ARTICLE TEXT — entity markers added]
  "Le 16 novembre dernier, <PERSON>Saugé</PERSON> rentraitdans la commune avec Renault, et lui annon¬ çait qu'il irait dans l'après-midi chercher desfromages à Brière, et que le soir, vers huitheures, il s'arrêterait à <LOCATION>Montlhéry</LOCATION>. En effet,vers deux heures, Saugé partit dans sa char¬ rette, mais il n'était pas à cent mètres de sademeure qu'il s'aperçut qu'il avait oublié salimousine ; il retourna sur ses pas et trouvadans sa cour sa femme et Renault : celui-ciexpliqua sa présence en disant qu'il venaitvoir si des clous qu'il avait achetés n'étaientpas restés dans la charrette, et il se retira a¬ vec le mari. A peine à trois cents mètres dela maison, celui-ci remarqua qu'il lui man¬ quait ses éclisses à fromage ; il revint. A sonarrivée, sa femme se présenta devant lui, sor¬ tant de la laiterie, où Saugé entrevit l'ombred'un homme ; il y entra et trouva Renault ca¬ ché sous la cage de l'escalier. Le mari mani¬ festa énergiquement ses soupçons, et intima àRenault, avec menaces, l'ordre de ne plusmettre les pieds chez lui."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Montlhéry
    Description: commune française du département de l'Essonne
    Country: ['France']
    Located in: ['Seine-et-Oise', 'Essonne', 'arrondissement de Palaiseau']
    Aliases: {'fr': ['Monthléry'], 'de': ['Montlhery']}
    Coordinates: [{'lat': 48.638611111111, 'lon': 2.2722222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.995

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Saugé' and 'Montlhéry' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Saugé' near 'Montlhéry' around NA?
  4. Resolve temporal expressions relative to NA. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 108 [ID: test_fr__57]:
  Publication date : 1936-01-15
  Language         : fr
  Person  : 'Rouffianges'  (QID: N/A)
  Location: '115, rue Didot'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Deux nouvelles inculpationsfrappent le surveillantcomplaisant valletM. Hude, juge d'instruction, a in¬ culpé hier le surveillant Vallet de cor¬ ruption de fonctionnaire, faux et usa¬ ge de faux. Tout d'abord, l'expertGebelin avait établi que tous les or¬ dres d'extraction, aussi bien ceux quisont entièrement faux que ceux quin'ont été que maquillés par additiond’un nom, avaient été préparés parla main du gardien de la Souricière.En particulier, l'ordre du 2 octobrequi permit à Pélissier de s’évader lelendemain et qui fut retrouvé le 4 à laSanté, est en entier de lui. Par ail¬ leurs, le petit carnet saisi sur Chris¬ tiane Pélissier établit qu’il avaittouché des sommes d'argent pour lalocation à la journée, de la cellulenuméro 10. Plusieurs autres dames,d'ailleurs, avec leurs maris détenus,ont contribué à alimenter la caissedu geôlier « compatissant ».Le versement des cotisationsd'assurances socialespour les chauffeurs de taxisLe ministère du Travail nous com¬ munique la note suivante :En application de l'article premier,paragraphe 3, du décret-loi du 28 oc¬ tobre 1935, modifiant le régime desAssurances sociales, les conducteursde voitures publiques, dont l'exploi¬ tation est assujettie à des tarifs detransport fixés par l'autorité publi¬ que, sont soumis au régime de l'assu¬ rance obligatoire, dès l'instant queleur rémunération n'excède pas lechiffre-limite prévu pour le bénéficede cette assurance.Les cotisations patronale et ouvriè¬ re sont dues depuis le premier jan¬ vier 1936.Conformément à l'article 3 de l'ar¬ rêté du 27 décembre 1935 paru auJournal Officiel du 29 décembre, lespourboires des intéressés, qui doi¬ vent entrer en compte pour la déter¬ mination de leur rémunération, se¬ ront évalués par des conventions col¬ lectives de travail, et, à défaut detelles conventions, par arrêtés du mi¬ nistre du Travail.L'unité syndicalechez les travailleurs de l'EtatLes sections de la Fédération uni¬ fiée des travailleurs de l'Etat (artil¬ lerie, poudreries, magasins adminis¬ tratifs, génie et aéronautique, em¬ ployés et agents de maîtrise, marinemilitaire, arts et métiers) ont tenuhier leurs assises patriculières dansles différentes salles de la Bourse duTravail.Voici les résultats définitifs du votepar mandats que le congrès de fusiondes deux Fédérations confédérée etunitaire avait été appelé à émettrelundi soir au sujet du cumul desfonctions syndicales et des mandatspolitiques. Contre : 287 voix ; pour :80 voix ; abstentions : 17 voix.PARTIS ET LIGUESGroupe des étudiants radicauxLa réunion du groupe des étu¬ diants radicaux de Paris aura lieuaujourd'hui mercredi, à 21 heures,au café « Chez Emile », 40, rue Ga¬ lande, et 10, rue Fouarre (angle desdeux rues).Fédération nationaledes Libres PenseursFédération de la Seine. — La com¬ mission spéciale d’unité d’action seréunira demain jeudi, à 21 heures,local habituel, rue de Châteaudun.Les responsables voudront bien êtreprésents.Parti radical-socialisteVersailles. — Les Comités radicaux¬ socialistes de la deuxième circons¬ cription de Versailles, réunis à Pois¬ sy, ont procédé à la constitution dila Fédération des Comités de cettecirconscription.Le bureau élu de la Fédération estainsi constitué : Président : RougelotHenri ; Secrétaire : Durand Fernand;Trésorier : Fourlon Pierre.Un ordre du jour a été voté décla¬ rant impossible le maintien de mi¬ nistres radicaux dans le gouverne¬ ment ; et demandant au bureau duComité Exécutif de proposer à laplus prochaine réunion du Comité lerefus de toute collaboration avec legouvernement actuel.Libre PenséeNous sommes heureux d'informer lepublic qu’une permanence de la 14esection de la Libre Pensée est ou¬ verte au numéro 47 de la rue Bé¬ nard (XIVe), à la Librairie des Tra¬ vailleurs.Le but de la Libre Pensée est de dé¬ velopper chez tous l’esprit critique etl'amour du libre examen, sans dis¬ tinction de parti, et de grouper dansson sein ceux qui se réclament de cehaut idéal. L’époque que nous vivonsest corrompue depuis des siècles parles croyances religieuses et leur amiedévouée Sa Majesté l'Argent qui gou¬ vernent le monde à leur seul bénéfice.Il est de notre devoir, pour nos en¬ fants et pour nous-mêmes, d'arracherce voile de l'au-delà et de mettre lemonde en face de ses nécessités réel¬ les. Chacun le peut dans son humblerôle ; la laïcité peut nous aider. Grou¬ pons-nous pour la défendre.Front populaireEpernay. — Dimanche après-midi,M. Eugène Frot, ancien ministre, adonné en la salle des fêtes d'Epernay(Marne) une conférence sous les aus¬ pices de la Ligue des Droits del'Homme et du Comité du Front Po¬ pulaire. Plus de 1.200 personnes yassistaient dont plusieurs élus radi¬ caux et socialistes de la région. M.Guerry, président, assisté de MM.Morange et Guen.MM. Eugène Frot, député, ancienministre, Bossus, conseiller munici¬ pal communiste de Paris, et EmileKahn, secrétaire général de la Liguedes Droits de l'Homme, ont pris suc¬ cessivement la parole très chaleu¬ reusement applaudis.La réunion se termina sans inci¬ dent. Dans la nuit, un membre de laSolidarité Française qui avait tentéde peindre des inscriptions injurieu¬ ses sur les murs de la Salle des Fêtesavait été surpris par la police. Il dé¬ clara avoir été inspiré dans son gestepar un discours du fils de M. Princequ'il avait entendu précédemment..XIVe arr. — Pour la constitutiondes Comités de défense de la Répu¬ blique, trois grands meetings inaugu¬ raux sont organisés par le Front po¬ pulaire du 14e, aujourd'hui mercredi:111, rue du Château ; <LOCATION>115, rue Didot</LOCATION>,1, avenue de la Porte-d'Orléans.Trente orateurs inscrits, dont<PERSON>Rouffianges</PERSON>, Biquard, Croizat, Mau¬ vais, Paul Marcel, Graziani, MauriceLacroix, Létrange, Mension, etc...Ligue pour le Droit au Travailet le Progrès SocialVe arr — Une grande conférencesera donnée le vendredi 17 janvier,à 21 heures, à la Sorbonne, amphi¬ théâtre Richelieu, par Joseph Dubois,sur « L'Economie soviétique maî¬ tresse de ses destins ». Jacques Du¬ boin entretiendra ensuite les auditeursdu « Problème français ».Les cartes donnant droit aux placesréservées sont à la disposition des au¬ diteurs, au « Droit au Travail », 14,rue FavartViroflay. — Sous les auspices de lasection locaie des Droits de l'Homme,une grande réunion de propagandeaura lieu demain jeudi, à 21 heures,à la salie Robie, 134, route Navoù nos amis Chesneau et Ra,Martin exposeront les vérités dmiques diffusées par le « DroitTous nos amis et sympathisantssont cordialement invitésMaisons-Alfort. — L'Intersection dcanton de Charenton organisedredi 17 janvier, à 21 heures, ugrande réunion à la mairie dusons-Alfort, salle de la Justepaix. Nos camarades Compain mond Martin y parleront de « la révo¬ lution économique actuelle »."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1935" → 1935
      - "1936" → 1936
      - "1935" → 1935
    Temporal signal words: aujourd'hui, hier, ancien, plus, après
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.969

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Rouffianges' and '115, rue Didot' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Rouffianges' near '115, rue Didot' around 1936-01-15?
  4. Resolve temporal expressions relative to 1936-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 109 [ID: test_fr__58]:
  Publication date : 1936-01-15
  Language         : fr
  Person  : 'M. Prince'  (QID: N/A)
  Location: 'XIVe arr.'  (QID: Q187153)

  [ARTICLE TEXT — entity markers added]
  "Deux nouvelles inculpationsfrappent le surveillantcomplaisant valletM. Hude, juge d'instruction, a in¬ culpé hier le surveillant Vallet de cor¬ ruption de fonctionnaire, faux et usa¬ ge de faux. Tout d'abord, l'expertGebelin avait établi que tous les or¬ dres d'extraction, aussi bien ceux quisont entièrement faux que ceux quin'ont été que maquillés par additiond’un nom, avaient été préparés parla main du gardien de la Souricière.En particulier, l'ordre du 2 octobrequi permit à Pélissier de s’évader lelendemain et qui fut retrouvé le 4 à laSanté, est en entier de lui. Par ail¬ leurs, le petit carnet saisi sur Chris¬ tiane Pélissier établit qu’il avaittouché des sommes d'argent pour lalocation à la journée, de la cellulenuméro 10. Plusieurs autres dames,d'ailleurs, avec leurs maris détenus,ont contribué à alimenter la caissedu geôlier « compatissant ».Le versement des cotisationsd'assurances socialespour les chauffeurs de taxisLe ministère du Travail nous com¬ munique la note suivante :En application de l'article premier,paragraphe 3, du décret-loi du 28 oc¬ tobre 1935, modifiant le régime desAssurances sociales, les conducteursde voitures publiques, dont l'exploi¬ tation est assujettie à des tarifs detransport fixés par l'autorité publi¬ que, sont soumis au régime de l'assu¬ rance obligatoire, dès l'instant queleur rémunération n'excède pas lechiffre-limite prévu pour le bénéficede cette assurance.Les cotisations patronale et ouvriè¬ re sont dues depuis le premier jan¬ vier 1936.Conformément à l'article 3 de l'ar¬ rêté du 27 décembre 1935 paru auJournal Officiel du 29 décembre, lespourboires des intéressés, qui doi¬ vent entrer en compte pour la déter¬ mination de leur rémunération, se¬ ront évalués par des conventions col¬ lectives de travail, et, à défaut detelles conventions, par arrêtés du mi¬ nistre du Travail.L'unité syndicalechez les travailleurs de l'EtatLes sections de la Fédération uni¬ fiée des travailleurs de l'Etat (artil¬ lerie, poudreries, magasins adminis¬ tratifs, génie et aéronautique, em¬ ployés et agents de maîtrise, marinemilitaire, arts et métiers) ont tenuhier leurs assises patriculières dansles différentes salles de la Bourse duTravail.Voici les résultats définitifs du votepar mandats que le congrès de fusiondes deux Fédérations confédérée etunitaire avait été appelé à émettrelundi soir au sujet du cumul desfonctions syndicales et des mandatspolitiques. Contre : 287 voix ; pour :80 voix ; abstentions : 17 voix.PARTIS ET LIGUESGroupe des étudiants radicauxLa réunion du groupe des étu¬ diants radicaux de Paris aura lieuaujourd'hui mercredi, à 21 heures,au café « Chez Emile », 40, rue Ga¬ lande, et 10, rue Fouarre (angle desdeux rues).Fédération nationaledes Libres PenseursFédération de la Seine. — La com¬ mission spéciale d’unité d’action seréunira demain jeudi, à 21 heures,local habituel, rue de Châteaudun.Les responsables voudront bien êtreprésents.Parti radical-socialisteVersailles. — Les Comités radicaux¬ socialistes de la deuxième circons¬ cription de Versailles, réunis à Pois¬ sy, ont procédé à la constitution dila Fédération des Comités de cettecirconscription.Le bureau élu de la Fédération estainsi constitué : Président : RougelotHenri ; Secrétaire : Durand Fernand;Trésorier : Fourlon Pierre.Un ordre du jour a été voté décla¬ rant impossible le maintien de mi¬ nistres radicaux dans le gouverne¬ ment ; et demandant au bureau duComité Exécutif de proposer à laplus prochaine réunion du Comité lerefus de toute collaboration avec legouvernement actuel.Libre PenséeNous sommes heureux d'informer lepublic qu’une permanence de la 14esection de la Libre Pensée est ou¬ verte au numéro 47 de la rue Bé¬ nard (XIVe), à la Librairie des Tra¬ vailleurs.Le but de la Libre Pensée est de dé¬ velopper chez tous l’esprit critique etl'amour du libre examen, sans dis¬ tinction de parti, et de grouper dansson sein ceux qui se réclament de cehaut idéal. L’époque que nous vivonsest corrompue depuis des siècles parles croyances religieuses et leur amiedévouée Sa Majesté l'Argent qui gou¬ vernent le monde à leur seul bénéfice.Il est de notre devoir, pour nos en¬ fants et pour nous-mêmes, d'arracherce voile de l'au-delà et de mettre lemonde en face de ses nécessités réel¬ les. Chacun le peut dans son humblerôle ; la laïcité peut nous aider. Grou¬ pons-nous pour la défendre.Front populaireEpernay. — Dimanche après-midi,M. Eugène Frot, ancien ministre, adonné en la salle des fêtes d'Epernay(Marne) une conférence sous les aus¬ pices de la Ligue des Droits del'Homme et du Comité du Front Po¬ pulaire. Plus de 1.200 personnes yassistaient dont plusieurs élus radi¬ caux et socialistes de la région. M.Guerry, président, assisté de MM.Morange et Guen.MM. Eugène Frot, député, ancienministre, Bossus, conseiller munici¬ pal communiste de Paris, et EmileKahn, secrétaire général de la Liguedes Droits de l'Homme, ont pris suc¬ cessivement la parole très chaleu¬ reusement applaudis.La réunion se termina sans inci¬ dent. Dans la nuit, un membre de laSolidarité Française qui avait tentéde peindre des inscriptions injurieu¬ ses sur les murs de la Salle des Fêtesavait été surpris par la police. Il dé¬ clara avoir été inspiré dans son gestepar un discours du fils de <PERSON>M. Prince</PERSON>qu'il avait entendu précédemment..<LOCATION>XIVe arr.</LOCATION> — Pour la constitutiondes Comités de défense de la Répu¬ blique, trois grands meetings inaugu¬ raux sont organisés par le Front po¬ pulaire du 14e, aujourd'hui mercredi:111, rue du Château ; 115, rue Didot,1, avenue de la Porte-d'Orléans.Trente orateurs inscrits, dontRouffianges, Biquard, Croizat, Mau¬ vais, Paul Marcel, Graziani, MauriceLacroix, Létrange, Mension, etc...Ligue pour le Droit au Travailet le Progrès SocialVe arr — Une grande conférencesera donnée le vendredi 17 janvier,à 21 heures, à la Sorbonne, amphi¬ théâtre Richelieu, par Joseph Dubois,sur « L'Economie soviétique maî¬ tresse de ses destins ». Jacques Du¬ boin entretiendra ensuite les auditeursdu « Problème français ».Les cartes donnant droit aux placesréservées sont à la disposition des au¬ diteurs, au « Droit au Travail », 14,rue FavartViroflay. — Sous les auspices de lasection locaie des Droits de l'Homme,une grande réunion de propagandeaura lieu demain jeudi, à 21 heures,à la salie Robie, 134, route Navoù nos amis Chesneau et Ra,Martin exposeront les vérités dmiques diffusées par le « DroitTous nos amis et sympathisantssont cordialement invitésMaisons-Alfort. — L'Intersection dcanton de Charenton organisedredi 17 janvier, à 21 heures, ugrande réunion à la mairie dusons-Alfort, salle de la Justepaix. Nos camarades Compain mond Martin y parleront de « la révo¬ lution économique actuelle »."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1935" → 1935
      - "1936" → 1936
      - "1935" → 1935
    Temporal signal words: aujourd'hui, hier, ancien, plus, après
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.969

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Prince' and 'XIVe arr.' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Prince' near 'XIVe arr.' around 1936-01-15?
  4. Resolve temporal expressions relative to 1936-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 110 [ID: test_fr__6]:
  Publication date : 1948-02-23
  Language         : fr
  Person  : 'Schubiger'  (QID: Q571055)
  Location: 'Zurich'  (QID: Q72)

  [ARTICLE TEXT — entity markers added]
  "Le C. P. <LOCATION>Zurich</LOCATION> gagne Z le tournoi de hockey sur glace du Centenaire Samedi et dimanche, la patinoire de Monruz était une nouvelle fois entourée d'un nombreux public qui, bravant un froid très vif, suivit avec beaucoup d'intérêt le tournoi de hockey sur glace du Centenaire. Cette manifestation sportive fut pleinement réussie ; nous exprimons tefois un léger regret : pourquoi les trois rencontres ont-elles débuté avec dix à quinze minutes de retard ? Zurich bat Montchoisi par 12 à 8 (3-0, 6-3, 3-5) Les joueurs de Lausanne commencèrent par pratiquer un jeu passablement décousu : la défense était très lente et les avants trop individuels. Aussi tait-il une nette différence de classe entre les deux équipes en présence et Zurich, jouant avec beaucoup de décision, put dès l'abord s'octroyer un avantage de trois buts par Urson, Bieler et Ernst. Au cours du second tiers, les Zuricois relâchèrent un peu leur étreinte, alors que peu à peu l'on voyait Montchoisi s'organiser et attaquer avec mordant. Ce tiers fut ainsi assez équilibré, sans toutefois que les Zuricois perdent l'initiative du jeu. Ils marqueront cinq buts par Bieler (2), Urson, Sylvio Rossi, Boiler et Gugenbuhl, tandis que Banninger devait laisser passer trois tirs des Vaudois, deux de Minder et un de Caseel. Renversement de situation au dernier tiers où Montchoisi part résolument a l'attaque en montrant des qualités insoupçonnées. Le Lausannois Hennsler est particulièrement en verve et il marquera trois buts. D'autres attaques très bien menées permettront encore à Beltrami et à Caseel de diminuer l'écart du score. Mais la défense ne parvient pas à contenir les contre-attaques zuricoises et des shots bien placés de Rossi, Ernst et Boiler consolideront ment la victoire des joueurs de la Limmat. Zurich bat Young Sprinters par 10 à 2 (5-0. 1-2. 4-0) Cette partie, disons-le franchement, nous causa une certaine déception. L'on souhaitait une lutte plus équilibrée ; Young Sprinters est certainement capable de mieux résister à Zurich qu'il ne l'a fait hier matin. Nos joueurs, il est vrai, peuvent invoquer une circonstance atténuante. Hugo Delnon était malade et, de ce fait, la première ligne neuchâteloise était désorganisée. En outre. Reto n'apparut sur la glace qu'au début du second tiers. La première partie du jeu vit ainsi une très facile domination de Zurich. Des Bieler. <PERSON>Schubiger</PERSON>, Lohrer, semaient avec joie la panique dans notre camp et marquèrent cinq buts à intervalle régulier. Le second tiers nous fit espérer un redressement de la situation. Reto est là et il semble décider à bien faire. Il s'échappe par deux fois pour marquer deux superbes buts sans que le gardien Banninger puisse esquisser le moindre mouvement de défense. Mais l'équipe neuchâteloise continue à jouer avec une certaine incohérence. Les deux frères Delnon évoluent aveo le talentueux Ulrich, mais cette ligne manque de cohésion et plus rien ne réussira. Sylvio Rossi marquera au contraire un nouveau but. Dernier tiers assez monotone, les Zuricois sont supérieurs et ils parviendront sans trop d'efforts à accentuer leur avance par trois nouveaux buts réussis par Boiler, Gugenbuhl et Urson. Relevons dans le camp neuchâtelois la bonne partie du gardien Perrottet et la rapidité, la décision et le maniement de crosse d'Ulrich. Chez les Zuricois, il faut surtout louer la sûreté d'une défense très solide et un peu rude ; la première ligne formée de Bieler, Lohrer et Schubiger fut de loin la meilleure ligne du tournoi. Young Sprinters bat Montchoisi par 5 à 3 (2-0. 1-2. 2-1) Cette rencontre nous fait oublier la décevante partie disputée le matin. Les deux grands rivaux romands se livrent une lutte très ouverte et variée. Signalons quelques duels épiques entre Hans Cattini, Stucki, les deux frères Delnon et Ulrich. Remise de sa défaillance, notre équipe joua d'une manière digne d'elle-même et elle ne cessa de jouir d'une légère supériorité sur son adversaire. Reto et Othmar Delnon ouvrirent la marque au premier tiers. Les Lausannois placèrent leur effort principal sur le second tiers, mais notre défense formée de Tinembart et du Dr Grether, ainsi que du gardien Perrottet, dans une forme exceptionnelle dimanche, parvinrent à endiguer leurs assauts à l'exception de deux qui permirent à Jansky et à Beltrami de loger le puck au fond de la cage neuchâteloise. Le dernier tiers, au cours duquel le jeu devient assez dur, permit à Young Sprinters de s'assurer une victoire méritée. Jansky profita tout d'abord judicieusement d'une erreur de notre défense, mais Othmar Delnon trompera deux fois encore le gardien Ayer. Relevons l'excellent travail d'Ulrich. Rapide, poussant jusqu'au bout chaque descente, ne considérant jamais perdue une passe, il mena avec brio les attaques de notre notro seconde ligne et certains de ses shots auraient mérité le but. Le palmarès A la suite de ces rencontre, Zurich gagne le tournoi aveo quatre points, suivi de Young Sprinters (2 p.) et Mont _, choisi (0 p.). Lo C. P. Zurich gagne le premier prix du tournoi, la grande distinction du Centenaire et le challenge du tournoi. Young Sprinters obtient la deuxième distinction du Centenaire et le challenge Vuillomenet, récompensant l'équipe jouant avec le plus de fair-play. Quant à Montchoisi, il reçoit la coupe offerte par le cinéma Palace. B. Ad. Une tournée de Young Sprinters en Tchécoslovaquie Notre équipe de hockey sur glace a été invitée à disputer un certain nombre de matches en Tchécoslovaquie, notamment contre Prague et Brno. Elle partira pour ce pays au début du mois de mars et sera renforcée par quelques autres joueurs de ligue nationale A."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Otto Schubiger
    Description: joueur de hockey sur glace suisse
    Born: ['+1925-01-06T00:00:00Z']
    Died: ['+2019-01-28T00:00:00Z']
    Birth place: ['Zurich']
    Death place: ['Baden']
  Location Wikidata:
    Label: Zurich
    Description: ville la plus peuplée de Suisse et chef-lieu du canton de Zurich
    Country: ['Suisse', 'ancienne Confédération suisse', 'République helvétique', 'Suisse']
    Located in: ['district de Zurich']
    Aliases: {'en': ['City of Zurich', 'ZH', 'Stadt Zürich', 'Zurich, Switzerland', 'Zürich'], 'fr': ['Zürich', 'Zuerich', 'ville de Zurich'], 'de': ['Stadt Zürich'], 'lb': ['Zürech', 'Stad Zürich']}
    Coordinates: [{'lat': 47.37444444444444, 'lon': 8.54111111111111}]
  Known person–location links: {"birth_place": "P19"}

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.971

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Schubiger' and 'Zurich' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Schubiger' near 'Zurich' around 1948-02-23?
  4. Resolve temporal expressions relative to 1948-02-23. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 111 [ID: test_fr__122]:
  Publication date : 1928-08-28
  Language         : fr
  Person  : 'M. Scheller'  (QID: N/A)
  Location: 'Bossons'  (QID: Q68429)

  [ARTICLE TEXT — entity markers added]
  "Les accidents Un alpiniste genevois atteint par nn bloc de rocher a lé crâne fracturé et menrt Genève, 27 août. Dimanche, quatre alpinistes genevois membres du Club des grimpeurs s'étaient rendus au Mont-Blanc lorsque, vers 17 heures, au chemin qui conduit du glacier du Grand-Mulet à la station de l'Aiguille du Midi, l'un d'eux, Aimé Scheller, 36 ans, sertisseur, fut soudain atteint par un bloc qui s'était détaché et Sii lui fit une grave blessure à la tête, eux de ses compagnons demeurèrent auprès du blessé tandis que l'autre allait quérir du secours. Une colonne, organisée aussitôt, ramena le blessé à la station. <PERSON>M. Scheller</PERSON> reçut les soins d'un médecin français et fut descendu qu'aux <LOCATION>Bossons</LOCATION> en automobile. De là, il fut dirigé sur l'hôpital cantonal de Genève où il est mort lundi matin des suites d'une fracture du crâne. Il laisse une femme et une fillette. Un char à chien contre une motocyclette * Un petit char attelé d'un chien et appairtenant à M. François Savoy, demeurant à Bossonens (Èribourg), s'est jeté devant une motocyclette montée par M. Max Veraaud, pasteur à Mézières (Vaud), ayant en croupe son frère. La moto fut renversée avec ses deux occupants ; Je Téservoir à benzine s'étant débouché, l'eesence prit feu au contact du phare à acétylène et se communiqua aux vêtements de M. Vernaud. Une application de sacs mouillés l'éteignit. M. Vernaud a les sourcils et les cheveux légèrement brûlés et des contusions. La motocyclette, fort endommagée, a dû être conduite au garage. Grave accident d'automobile Sarnen, 28 août. Une automobile zurichoise occupée par 4 personnes, a fait une chute près de Lungern. Ses occupante ont été projetés hors de la voiture, Mme Jenny-tHirlimann, 35 ans, femme d un entrepreneur de Zurich, a eu la cage thoracique enfoncée. Un médecin qui circulait, par hasard à cet endroit, a fait transporter la malheureuse à Lungern où elle a succombé lundi matin. L'un des occupants a été également contusionné. Une automobile bousculée * Un oamion-automobite de la brasserie Muliler descendant, dimanche, au début de l'après-imidd, de Sainte-Croix SUT Vuitobœuf, a accroché, au premier grand tournant de la route, au-dessous du Château (Saimte-tCroix) une petite torpédo à trois places occupée par deux personnes et qui montait à Sainte-Croix. H l'a lancée avec violence contre le mur bordant la route. Les occupants de l'auto s'en tirent avec des blessures superficielles ; ils sont rentrés à Sainte-Croix, mais leur voiture gravement endommagée a dû être remorquée au grand garage des Remparts à Yverdon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Scheller' and 'Bossons' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Scheller' near 'Bossons' around 1928-08-28?
  4. Resolve temporal expressions relative to 1928-08-28. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 112 [ID: test_fr__235]:
  Publication date : 1981-02-18
  Language         : fr
  Person  : 'Favre-Blanc'  (QID: N/A)
  Location: 'SUISSE'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "<LOCATION>SUISSE</LOCATION> dernière COMMISSION DES ETATS La Suissesse mariée garderait son droit de cité Berne, 17 (ATS).-La Commission du conseil des Etats chargée d'examiner le nouveau droit matrimonial, qui a terminé ses travaux mardi à Berne, a modifié sur quelques points le projet du Conseil fédéral.Elle a cependant accepté dans ses grandes lignes le projet gouvernemental et notamment le remplacement du régime actuel de l'union des biens par celui de la participation aux acquêts.Cet objet sera traité par le parlement au mois de mars.Au sujet du nom des époux, la Commission rejoint le Conseil fédéral dans son refus d'accorder le droit d'option qui permettrait aux fiancés de choisir le nom de l'épouse comme nom de famille.Mais la femme aura le droit non seulement de faire suivre son nom (<PERSON>Favre-Blanc</PERSON>), mais aussi de le faire précéder (Mme Blanc épouse Favre).La Commission n'a pas retenu la possibilité de l'option en raison de la tradition qui existe dans notre pays.En Allemagne fédérale, où le choix existe, seuls 4 % des époux en font usage.La nouvelle réglementation suisse facilitera- cependant l'adoption éventuelle par les fiancés, avant le mariage, du nom de la femme comme nom de famille.Mais il faudra de bonnes raisons pour l'autoriser (nom à consonnance étrangère, nom connu dans le commerce, la politique, etc).En ce qui concerne le droit de cité, la femme recevra, par le mariage, le droit de cité du mari mais sans perdre le sien.Une majorité s'est formée dans la Commission en faveur de cette solution."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.993

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Favre-Blanc' and 'SUISSE' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Favre-Blanc' near 'SUISSE' around 1981-02-18?
  4. Resolve temporal expressions relative to 1981-02-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 113 [ID: test_fr__63]:
  Publication date : 1936-01-15
  Language         : fr
  Person  : 'Jacques Du¬\nboin'  (QID: Q2118124)
  Location: 'Viroflay'  (QID: Q83432)

  [ARTICLE TEXT — entity markers added]
  "Deux nouvelles inculpationsfrappent le surveillantcomplaisant valletM. Hude, juge d'instruction, a in¬ culpé hier le surveillant Vallet de cor¬ ruption de fonctionnaire, faux et usa¬ ge de faux. Tout d'abord, l'expertGebelin avait établi que tous les or¬ dres d'extraction, aussi bien ceux quisont entièrement faux que ceux quin'ont été que maquillés par additiond’un nom, avaient été préparés parla main du gardien de la Souricière.En particulier, l'ordre du 2 octobrequi permit à Pélissier de s’évader lelendemain et qui fut retrouvé le 4 à laSanté, est en entier de lui. Par ail¬ leurs, le petit carnet saisi sur Chris¬ tiane Pélissier établit qu’il avaittouché des sommes d'argent pour lalocation à la journée, de la cellulenuméro 10. Plusieurs autres dames,d'ailleurs, avec leurs maris détenus,ont contribué à alimenter la caissedu geôlier « compatissant ».Le versement des cotisationsd'assurances socialespour les chauffeurs de taxisLe ministère du Travail nous com¬ munique la note suivante :En application de l'article premier,paragraphe 3, du décret-loi du 28 oc¬ tobre 1935, modifiant le régime desAssurances sociales, les conducteursde voitures publiques, dont l'exploi¬ tation est assujettie à des tarifs detransport fixés par l'autorité publi¬ que, sont soumis au régime de l'assu¬ rance obligatoire, dès l'instant queleur rémunération n'excède pas lechiffre-limite prévu pour le bénéficede cette assurance.Les cotisations patronale et ouvriè¬ re sont dues depuis le premier jan¬ vier 1936.Conformément à l'article 3 de l'ar¬ rêté du 27 décembre 1935 paru auJournal Officiel du 29 décembre, lespourboires des intéressés, qui doi¬ vent entrer en compte pour la déter¬ mination de leur rémunération, se¬ ront évalués par des conventions col¬ lectives de travail, et, à défaut detelles conventions, par arrêtés du mi¬ nistre du Travail.L'unité syndicalechez les travailleurs de l'EtatLes sections de la Fédération uni¬ fiée des travailleurs de l'Etat (artil¬ lerie, poudreries, magasins adminis¬ tratifs, génie et aéronautique, em¬ ployés et agents de maîtrise, marinemilitaire, arts et métiers) ont tenuhier leurs assises patriculières dansles différentes salles de la Bourse duTravail.Voici les résultats définitifs du votepar mandats que le congrès de fusiondes deux Fédérations confédérée etunitaire avait été appelé à émettrelundi soir au sujet du cumul desfonctions syndicales et des mandatspolitiques. Contre : 287 voix ; pour :80 voix ; abstentions : 17 voix.PARTIS ET LIGUESGroupe des étudiants radicauxLa réunion du groupe des étu¬ diants radicaux de Paris aura lieuaujourd'hui mercredi, à 21 heures,au café « Chez Emile », 40, rue Ga¬ lande, et 10, rue Fouarre (angle desdeux rues).Fédération nationaledes Libres PenseursFédération de la Seine. — La com¬ mission spéciale d’unité d’action seréunira demain jeudi, à 21 heures,local habituel, rue de Châteaudun.Les responsables voudront bien êtreprésents.Parti radical-socialisteVersailles. — Les Comités radicaux¬ socialistes de la deuxième circons¬ cription de Versailles, réunis à Pois¬ sy, ont procédé à la constitution dila Fédération des Comités de cettecirconscription.Le bureau élu de la Fédération estainsi constitué : Président : RougelotHenri ; Secrétaire : Durand Fernand;Trésorier : Fourlon Pierre.Un ordre du jour a été voté décla¬ rant impossible le maintien de mi¬ nistres radicaux dans le gouverne¬ ment ; et demandant au bureau duComité Exécutif de proposer à laplus prochaine réunion du Comité lerefus de toute collaboration avec legouvernement actuel.Libre PenséeNous sommes heureux d'informer lepublic qu’une permanence de la 14esection de la Libre Pensée est ou¬ verte au numéro 47 de la rue Bé¬ nard (XIVe), à la Librairie des Tra¬ vailleurs.Le but de la Libre Pensée est de dé¬ velopper chez tous l’esprit critique etl'amour du libre examen, sans dis¬ tinction de parti, et de grouper dansson sein ceux qui se réclament de cehaut idéal. L’époque que nous vivonsest corrompue depuis des siècles parles croyances religieuses et leur amiedévouée Sa Majesté l'Argent qui gou¬ vernent le monde à leur seul bénéfice.Il est de notre devoir, pour nos en¬ fants et pour nous-mêmes, d'arracherce voile de l'au-delà et de mettre lemonde en face de ses nécessités réel¬ les. Chacun le peut dans son humblerôle ; la laïcité peut nous aider. Grou¬ pons-nous pour la défendre.Front populaireEpernay. — Dimanche après-midi,M. Eugène Frot, ancien ministre, adonné en la salle des fêtes d'Epernay(Marne) une conférence sous les aus¬ pices de la Ligue des Droits del'Homme et du Comité du Front Po¬ pulaire. Plus de 1.200 personnes yassistaient dont plusieurs élus radi¬ caux et socialistes de la région. M.Guerry, président, assisté de MM.Morange et Guen.MM. Eugène Frot, député, ancienministre, Bossus, conseiller munici¬ pal communiste de Paris, et EmileKahn, secrétaire général de la Liguedes Droits de l'Homme, ont pris suc¬ cessivement la parole très chaleu¬ reusement applaudis.La réunion se termina sans inci¬ dent. Dans la nuit, un membre de laSolidarité Française qui avait tentéde peindre des inscriptions injurieu¬ ses sur les murs de la Salle des Fêtesavait été surpris par la police. Il dé¬ clara avoir été inspiré dans son gestepar un discours du fils de M. Princequ'il avait entendu précédemment..XIVe arr. — Pour la constitutiondes Comités de défense de la Répu¬ blique, trois grands meetings inaugu¬ raux sont organisés par le Front po¬ pulaire du 14e, aujourd'hui mercredi:111, rue du Château ; 115, rue Didot,1, avenue de la Porte-d'Orléans.Trente orateurs inscrits, dontRouffianges, Biquard, Croizat, Mau¬ vais, Paul Marcel, Graziani, MauriceLacroix, Létrange, Mension, etc...Ligue pour le Droit au Travailet le Progrès SocialVe arr — Une grande conférencesera donnée le vendredi 17 janvier,à 21 heures, à la Sorbonne, amphi¬ théâtre Richelieu, par Joseph Dubois,sur « L'Economie soviétique maî¬ tresse de ses destins ». Jacques Du¬ boin entretiendra ensuite les auditeursdu « Problème français ».Les cartes donnant droit aux placesréservées sont à la disposition des au¬ diteurs, au « Droit au Travail », 14,rue Favart<LOCATION>Viroflay</LOCATION>. — Sous les auspices de lasection locaie des Droits de l'Homme,une grande réunion de propagandeaura lieu demain jeudi, à 21 heures,à la salie Robie, 134, route Navoù nos amis Chesneau et Ra,Martin exposeront les vérités dmiques diffusées par le « DroitTous nos amis et sympathisantssont cordialement invitésMaisons-Alfort. — L'Intersection dcanton de Charenton organisedredi 17 janvier, à 21 heures, ugrande réunion à la mairie dusons-Alfort, salle de la Justepaix. Nos camarades Compain mond Martin y parleront de « la révo¬ lution économique actuelle »."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Viroflay
    Description: commune française du département des Yvelines
    Country: ['Q142']
    Located in: ['Q12820', 'Seine-et-Oise', 'arrondissement de Versailles']
    Coordinates: [{'lat': 48.8, 'lon': 2.1722222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1935" → 1935
      - "1936" → 1936
      - "1935" → 1935
    Temporal signal words: aujourd'hui, hier, ancien, plus, après
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.969

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Jacques Du¬\nboin' and 'Viroflay' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Jacques Du¬\nboin' near 'Viroflay' around 1936-01-15?
  4. Resolve temporal expressions relative to 1936-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 114 [ID: test_fr__120]:
  Publication date : 1928-08-28
  Language         : fr
  Person  : 'M. François Savoy'  (QID: N/A)
  Location: 'Bossons'  (QID: Q68429)

  [ARTICLE TEXT — entity markers added]
  "Les accidents Un alpiniste genevois atteint par nn bloc de rocher a lé crâne fracturé et menrt Genève, 27 août. Dimanche, quatre alpinistes genevois membres du Club des grimpeurs s'étaient rendus au Mont-Blanc lorsque, vers 17 heures, au chemin qui conduit du glacier du Grand-Mulet à la station de l'Aiguille du Midi, l'un d'eux, Aimé Scheller, 36 ans, sertisseur, fut soudain atteint par un bloc qui s'était détaché et Sii lui fit une grave blessure à la tête, eux de ses compagnons demeurèrent auprès du blessé tandis que l'autre allait quérir du secours. Une colonne, organisée aussitôt, ramena le blessé à la station. M. Scheller reçut les soins d'un médecin français et fut descendu qu'aux <LOCATION>Bossons</LOCATION> en automobile. De là, il fut dirigé sur l'hôpital cantonal de Genève où il est mort lundi matin des suites d'une fracture du crâne. Il laisse une femme et une fillette. Un char à chien contre une motocyclette * Un petit char attelé d'un chien et appairtenant à <PERSON>M. François Savoy</PERSON>, demeurant à Bossonens (Èribourg), s'est jeté devant une motocyclette montée par M. Max Veraaud, pasteur à Mézières (Vaud), ayant en croupe son frère. La moto fut renversée avec ses deux occupants ; Je Téservoir à benzine s'étant débouché, l'eesence prit feu au contact du phare à acétylène et se communiqua aux vêtements de M. Vernaud. Une application de sacs mouillés l'éteignit. M. Vernaud a les sourcils et les cheveux légèrement brûlés et des contusions. La motocyclette, fort endommagée, a dû être conduite au garage. Grave accident d'automobile Sarnen, 28 août. Une automobile zurichoise occupée par 4 personnes, a fait une chute près de Lungern. Ses occupante ont été projetés hors de la voiture, Mme Jenny-tHirlimann, 35 ans, femme d un entrepreneur de Zurich, a eu la cage thoracique enfoncée. Un médecin qui circulait, par hasard à cet endroit, a fait transporter la malheureuse à Lungern où elle a succombé lundi matin. L'un des occupants a été également contusionné. Une automobile bousculée * Un oamion-automobite de la brasserie Muliler descendant, dimanche, au début de l'après-imidd, de Sainte-Croix SUT Vuitobœuf, a accroché, au premier grand tournant de la route, au-dessous du Château (Saimte-tCroix) une petite torpédo à trois places occupée par deux personnes et qui montait à Sainte-Croix. H l'a lancée avec violence contre le mur bordant la route. Les occupants de l'auto s'en tirent avec des blessures superficielles ; ils sont rentrés à Sainte-Croix, mais leur voiture gravement endommagée a dû être remorquée au grand garage des Remparts à Yverdon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. François Savoy' and 'Bossons' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. François Savoy' near 'Bossons' around 1928-08-28?
  4. Resolve temporal expressions relative to 1928-08-28. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 115 [ID: test_fr__124]:
  Publication date : 1928-08-28
  Language         : fr
  Person  : 'M. Scheller'  (QID: N/A)
  Location: 'Aiguille du Midi'  (QID: Q404728)

  [ARTICLE TEXT — entity markers added]
  "Les accidents Un alpiniste genevois atteint par nn bloc de rocher a lé crâne fracturé et menrt Genève, 27 août. Dimanche, quatre alpinistes genevois membres du Club des grimpeurs s'étaient rendus au Mont-Blanc lorsque, vers 17 heures, au chemin qui conduit du glacier du Grand-Mulet à la station de l'<LOCATION>Aiguille du Midi</LOCATION>, l'un d'eux, Aimé Scheller, 36 ans, sertisseur, fut soudain atteint par un bloc qui s'était détaché et Sii lui fit une grave blessure à la tête, eux de ses compagnons demeurèrent auprès du blessé tandis que l'autre allait quérir du secours. Une colonne, organisée aussitôt, ramena le blessé à la station. <PERSON>M. Scheller</PERSON> reçut les soins d'un médecin français et fut descendu qu'aux Bossons en automobile. De là, il fut dirigé sur l'hôpital cantonal de Genève où il est mort lundi matin des suites d'une fracture du crâne. Il laisse une femme et une fillette. Un char à chien contre une motocyclette * Un petit char attelé d'un chien et appairtenant à M. François Savoy, demeurant à Bossonens (Èribourg), s'est jeté devant une motocyclette montée par M. Max Veraaud, pasteur à Mézières (Vaud), ayant en croupe son frère. La moto fut renversée avec ses deux occupants ; Je Téservoir à benzine s'étant débouché, l'eesence prit feu au contact du phare à acétylène et se communiqua aux vêtements de M. Vernaud. Une application de sacs mouillés l'éteignit. M. Vernaud a les sourcils et les cheveux légèrement brûlés et des contusions. La motocyclette, fort endommagée, a dû être conduite au garage. Grave accident d'automobile Sarnen, 28 août. Une automobile zurichoise occupée par 4 personnes, a fait une chute près de Lungern. Ses occupante ont été projetés hors de la voiture, Mme Jenny-tHirlimann, 35 ans, femme d un entrepreneur de Zurich, a eu la cage thoracique enfoncée. Un médecin qui circulait, par hasard à cet endroit, a fait transporter la malheureuse à Lungern où elle a succombé lundi matin. L'un des occupants a été également contusionné. Une automobile bousculée * Un oamion-automobite de la brasserie Muliler descendant, dimanche, au début de l'après-imidd, de Sainte-Croix SUT Vuitobœuf, a accroché, au premier grand tournant de la route, au-dessous du Château (Saimte-tCroix) une petite torpédo à trois places occupée par deux personnes et qui montait à Sainte-Croix. H l'a lancée avec violence contre le mur bordant la route. Les occupants de l'auto s'en tirent avec des blessures superficielles ; ils sont rentrés à Sainte-Croix, mais leur voiture gravement endommagée a dû être remorquée au grand garage des Remparts à Yverdon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: aiguille du Midi
    Description: montagne française
    Country: ['Q142']
    Located in: ['Q83236']
    Aliases: {'fr': ['Aiguille du midi', 'Aiguille Du Midi'], 'de': ['Sender Aiguille du Midi']}
    Coordinates: [{'lat': 45.878888888889, 'lon': 6.8875}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M. Scheller' and 'Aiguille du Midi' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M. Scheller' near 'Aiguille du Midi' around 1928-08-28?
  4. Resolve temporal expressions relative to 1928-08-28. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 116 [ID: test_fr__61]:
  Publication date : 1936-01-15
  Language         : fr
  Person  : 'Létrange'  (QID: N/A)
  Location: '111, rue du Château'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Deux nouvelles inculpationsfrappent le surveillantcomplaisant valletM. Hude, juge d'instruction, a in¬ culpé hier le surveillant Vallet de cor¬ ruption de fonctionnaire, faux et usa¬ ge de faux. Tout d'abord, l'expertGebelin avait établi que tous les or¬ dres d'extraction, aussi bien ceux quisont entièrement faux que ceux quin'ont été que maquillés par additiond’un nom, avaient été préparés parla main du gardien de la Souricière.En particulier, l'ordre du 2 octobrequi permit à Pélissier de s’évader lelendemain et qui fut retrouvé le 4 à laSanté, est en entier de lui. Par ail¬ leurs, le petit carnet saisi sur Chris¬ tiane Pélissier établit qu’il avaittouché des sommes d'argent pour lalocation à la journée, de la cellulenuméro 10. Plusieurs autres dames,d'ailleurs, avec leurs maris détenus,ont contribué à alimenter la caissedu geôlier « compatissant ».Le versement des cotisationsd'assurances socialespour les chauffeurs de taxisLe ministère du Travail nous com¬ munique la note suivante :En application de l'article premier,paragraphe 3, du décret-loi du 28 oc¬ tobre 1935, modifiant le régime desAssurances sociales, les conducteursde voitures publiques, dont l'exploi¬ tation est assujettie à des tarifs detransport fixés par l'autorité publi¬ que, sont soumis au régime de l'assu¬ rance obligatoire, dès l'instant queleur rémunération n'excède pas lechiffre-limite prévu pour le bénéficede cette assurance.Les cotisations patronale et ouvriè¬ re sont dues depuis le premier jan¬ vier 1936.Conformément à l'article 3 de l'ar¬ rêté du 27 décembre 1935 paru auJournal Officiel du 29 décembre, lespourboires des intéressés, qui doi¬ vent entrer en compte pour la déter¬ mination de leur rémunération, se¬ ront évalués par des conventions col¬ lectives de travail, et, à défaut detelles conventions, par arrêtés du mi¬ nistre du Travail.L'unité syndicalechez les travailleurs de l'EtatLes sections de la Fédération uni¬ fiée des travailleurs de l'Etat (artil¬ lerie, poudreries, magasins adminis¬ tratifs, génie et aéronautique, em¬ ployés et agents de maîtrise, marinemilitaire, arts et métiers) ont tenuhier leurs assises patriculières dansles différentes salles de la Bourse duTravail.Voici les résultats définitifs du votepar mandats que le congrès de fusiondes deux Fédérations confédérée etunitaire avait été appelé à émettrelundi soir au sujet du cumul desfonctions syndicales et des mandatspolitiques. Contre : 287 voix ; pour :80 voix ; abstentions : 17 voix.PARTIS ET LIGUESGroupe des étudiants radicauxLa réunion du groupe des étu¬ diants radicaux de Paris aura lieuaujourd'hui mercredi, à 21 heures,au café « Chez Emile », 40, rue Ga¬ lande, et 10, rue Fouarre (angle desdeux rues).Fédération nationaledes Libres PenseursFédération de la Seine. — La com¬ mission spéciale d’unité d’action seréunira demain jeudi, à 21 heures,local habituel, rue de Châteaudun.Les responsables voudront bien êtreprésents.Parti radical-socialisteVersailles. — Les Comités radicaux¬ socialistes de la deuxième circons¬ cription de Versailles, réunis à Pois¬ sy, ont procédé à la constitution dila Fédération des Comités de cettecirconscription.Le bureau élu de la Fédération estainsi constitué : Président : RougelotHenri ; Secrétaire : Durand Fernand;Trésorier : Fourlon Pierre.Un ordre du jour a été voté décla¬ rant impossible le maintien de mi¬ nistres radicaux dans le gouverne¬ ment ; et demandant au bureau duComité Exécutif de proposer à laplus prochaine réunion du Comité lerefus de toute collaboration avec legouvernement actuel.Libre PenséeNous sommes heureux d'informer lepublic qu’une permanence de la 14esection de la Libre Pensée est ou¬ verte au numéro 47 de la rue Bé¬ nard (XIVe), à la Librairie des Tra¬ vailleurs.Le but de la Libre Pensée est de dé¬ velopper chez tous l’esprit critique etl'amour du libre examen, sans dis¬ tinction de parti, et de grouper dansson sein ceux qui se réclament de cehaut idéal. L’époque que nous vivonsest corrompue depuis des siècles parles croyances religieuses et leur amiedévouée Sa Majesté l'Argent qui gou¬ vernent le monde à leur seul bénéfice.Il est de notre devoir, pour nos en¬ fants et pour nous-mêmes, d'arracherce voile de l'au-delà et de mettre lemonde en face de ses nécessités réel¬ les. Chacun le peut dans son humblerôle ; la laïcité peut nous aider. Grou¬ pons-nous pour la défendre.Front populaireEpernay. — Dimanche après-midi,M. Eugène Frot, ancien ministre, adonné en la salle des fêtes d'Epernay(Marne) une conférence sous les aus¬ pices de la Ligue des Droits del'Homme et du Comité du Front Po¬ pulaire. Plus de 1.200 personnes yassistaient dont plusieurs élus radi¬ caux et socialistes de la région. M.Guerry, président, assisté de MM.Morange et Guen.MM. Eugène Frot, député, ancienministre, Bossus, conseiller munici¬ pal communiste de Paris, et EmileKahn, secrétaire général de la Liguedes Droits de l'Homme, ont pris suc¬ cessivement la parole très chaleu¬ reusement applaudis.La réunion se termina sans inci¬ dent. Dans la nuit, un membre de laSolidarité Française qui avait tentéde peindre des inscriptions injurieu¬ ses sur les murs de la Salle des Fêtesavait été surpris par la police. Il dé¬ clara avoir été inspiré dans son gestepar un discours du fils de M. Princequ'il avait entendu précédemment..XIVe arr. — Pour la constitutiondes Comités de défense de la Répu¬ blique, trois grands meetings inaugu¬ raux sont organisés par le Front po¬ pulaire du 14e, aujourd'hui mercredi:<LOCATION>111, rue du Château</LOCATION> ; 115, rue Didot,1, avenue de la Porte-d'Orléans.Trente orateurs inscrits, dontRouffianges, Biquard, Croizat, Mau¬ vais, Paul Marcel, Graziani, MauriceLacroix, <PERSON>Létrange</PERSON>, Mension, etc...Ligue pour le Droit au Travailet le Progrès SocialVe arr — Une grande conférencesera donnée le vendredi 17 janvier,à 21 heures, à la Sorbonne, amphi¬ théâtre Richelieu, par Joseph Dubois,sur « L'Economie soviétique maî¬ tresse de ses destins ». Jacques Du¬ boin entretiendra ensuite les auditeursdu « Problème français ».Les cartes donnant droit aux placesréservées sont à la disposition des au¬ diteurs, au « Droit au Travail », 14,rue FavartViroflay. — Sous les auspices de lasection locaie des Droits de l'Homme,une grande réunion de propagandeaura lieu demain jeudi, à 21 heures,à la salie Robie, 134, route Navoù nos amis Chesneau et Ra,Martin exposeront les vérités dmiques diffusées par le « DroitTous nos amis et sympathisantssont cordialement invitésMaisons-Alfort. — L'Intersection dcanton de Charenton organisedredi 17 janvier, à 21 heures, ugrande réunion à la mairie dusons-Alfort, salle de la Justepaix. Nos camarades Compain mond Martin y parleront de « la révo¬ lution économique actuelle »."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1935" → 1935
      - "1936" → 1936
      - "1935" → 1935
    Temporal signal words: aujourd'hui, hier, ancien, plus, après
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.969

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Létrange' and '111, rue du Château' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Létrange' near '111, rue du Château' around 1936-01-15?
  4. Resolve temporal expressions relative to 1936-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 117 [ID: test_fr__5]:
  Publication date : 1948-02-23
  Language         : fr
  Person  : 'Ernst'  (QID: N/A)
  Location: 'Limmat'  (QID: Q14338)

  [ARTICLE TEXT — entity markers added]
  "Le C. P. Zurich gagne Z le tournoi de hockey sur glace du Centenaire Samedi et dimanche, la patinoire de Monruz était une nouvelle fois entourée d'un nombreux public qui, bravant un froid très vif, suivit avec beaucoup d'intérêt le tournoi de hockey sur glace du Centenaire. Cette manifestation sportive fut pleinement réussie ; nous exprimons tefois un léger regret : pourquoi les trois rencontres ont-elles débuté avec dix à quinze minutes de retard ? Zurich bat Montchoisi par 12 à 8 (3-0, 6-3, 3-5) Les joueurs de Lausanne commencèrent par pratiquer un jeu passablement décousu : la défense était très lente et les avants trop individuels. Aussi tait-il une nette différence de classe entre les deux équipes en présence et Zurich, jouant avec beaucoup de décision, put dès l'abord s'octroyer un avantage de trois buts par Urson, Bieler et <PERSON>Ernst</PERSON>. Au cours du second tiers, les Zuricois relâchèrent un peu leur étreinte, alors que peu à peu l'on voyait Montchoisi s'organiser et attaquer avec mordant. Ce tiers fut ainsi assez équilibré, sans toutefois que les Zuricois perdent l'initiative du jeu. Ils marqueront cinq buts par Bieler (2), Urson, Sylvio Rossi, Boiler et Gugenbuhl, tandis que Banninger devait laisser passer trois tirs des Vaudois, deux de Minder et un de Caseel. Renversement de situation au dernier tiers où Montchoisi part résolument a l'attaque en montrant des qualités insoupçonnées. Le Lausannois Hennsler est particulièrement en verve et il marquera trois buts. D'autres attaques très bien menées permettront encore à Beltrami et à Caseel de diminuer l'écart du score. Mais la défense ne parvient pas à contenir les contre-attaques zuricoises et des shots bien placés de Rossi, Ernst et Boiler consolideront ment la victoire des joueurs de la <LOCATION>Limmat</LOCATION>. Zurich bat Young Sprinters par 10 à 2 (5-0. 1-2. 4-0) Cette partie, disons-le franchement, nous causa une certaine déception. L'on souhaitait une lutte plus équilibrée ; Young Sprinters est certainement capable de mieux résister à Zurich qu'il ne l'a fait hier matin. Nos joueurs, il est vrai, peuvent invoquer une circonstance atténuante. Hugo Delnon était malade et, de ce fait, la première ligne neuchâteloise était désorganisée. En outre. Reto n'apparut sur la glace qu'au début du second tiers. La première partie du jeu vit ainsi une très facile domination de Zurich. Des Bieler. Schubiger, Lohrer, semaient avec joie la panique dans notre camp et marquèrent cinq buts à intervalle régulier. Le second tiers nous fit espérer un redressement de la situation. Reto est là et il semble décider à bien faire. Il s'échappe par deux fois pour marquer deux superbes buts sans que le gardien Banninger puisse esquisser le moindre mouvement de défense. Mais l'équipe neuchâteloise continue à jouer avec une certaine incohérence. Les deux frères Delnon évoluent aveo le talentueux Ulrich, mais cette ligne manque de cohésion et plus rien ne réussira. Sylvio Rossi marquera au contraire un nouveau but. Dernier tiers assez monotone, les Zuricois sont supérieurs et ils parviendront sans trop d'efforts à accentuer leur avance par trois nouveaux buts réussis par Boiler, Gugenbuhl et Urson. Relevons dans le camp neuchâtelois la bonne partie du gardien Perrottet et la rapidité, la décision et le maniement de crosse d'Ulrich. Chez les Zuricois, il faut surtout louer la sûreté d'une défense très solide et un peu rude ; la première ligne formée de Bieler, Lohrer et Schubiger fut de loin la meilleure ligne du tournoi. Young Sprinters bat Montchoisi par 5 à 3 (2-0. 1-2. 2-1) Cette rencontre nous fait oublier la décevante partie disputée le matin. Les deux grands rivaux romands se livrent une lutte très ouverte et variée. Signalons quelques duels épiques entre Hans Cattini, Stucki, les deux frères Delnon et Ulrich. Remise de sa défaillance, notre équipe joua d'une manière digne d'elle-même et elle ne cessa de jouir d'une légère supériorité sur son adversaire. Reto et Othmar Delnon ouvrirent la marque au premier tiers. Les Lausannois placèrent leur effort principal sur le second tiers, mais notre défense formée de Tinembart et du Dr Grether, ainsi que du gardien Perrottet, dans une forme exceptionnelle dimanche, parvinrent à endiguer leurs assauts à l'exception de deux qui permirent à Jansky et à Beltrami de loger le puck au fond de la cage neuchâteloise. Le dernier tiers, au cours duquel le jeu devient assez dur, permit à Young Sprinters de s'assurer une victoire méritée. Jansky profita tout d'abord judicieusement d'une erreur de notre défense, mais Othmar Delnon trompera deux fois encore le gardien Ayer. Relevons l'excellent travail d'Ulrich. Rapide, poussant jusqu'au bout chaque descente, ne considérant jamais perdue une passe, il mena avec brio les attaques de notre notro seconde ligne et certains de ses shots auraient mérité le but. Le palmarès A la suite de ces rencontre, Zurich gagne le tournoi aveo quatre points, suivi de Young Sprinters (2 p.) et Mont _, choisi (0 p.). Lo C. P. Zurich gagne le premier prix du tournoi, la grande distinction du Centenaire et le challenge du tournoi. Young Sprinters obtient la deuxième distinction du Centenaire et le challenge Vuillomenet, récompensant l'équipe jouant avec le plus de fair-play. Quant à Montchoisi, il reçoit la coupe offerte par le cinéma Palace. B. Ad. Une tournée de Young Sprinters en Tchécoslovaquie Notre équipe de hockey sur glace a été invitée à disputer un certain nombre de matches en Tchécoslovaquie, notamment contre Prague et Brno. Elle partira pour ce pays au début du mois de mars et sera renforcée par quelques autres joueurs de ligue nationale A."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Limmat
    Description: rivière suisse
    Country: ['Suisse']
    Located in: ['canton de Zurich', "canton d'Argovie"]
    Aliases: {'de': ['Limmig (aargauischen Unterlauf)']}
    Coordinates: [{'lat': 47.366342, 'lon': 8.543351}, {'lat': 47.501794, 'lon': 8.236313}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.971

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Ernst' and 'Limmat' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Ernst' near 'Limmat' around 1948-02-23?
  4. Resolve temporal expressions relative to 1948-02-23. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 118 [ID: test_fr__64]:
  Publication date : 1936-01-15
  Language         : fr
  Person  : 'Rouffianges'  (QID: N/A)
  Location: 'amphi¬\nthéâtre Richelieu'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Deux nouvelles inculpationsfrappent le surveillantcomplaisant valletM. Hude, juge d'instruction, a in¬ culpé hier le surveillant Vallet de cor¬ ruption de fonctionnaire, faux et usa¬ ge de faux. Tout d'abord, l'expertGebelin avait établi que tous les or¬ dres d'extraction, aussi bien ceux quisont entièrement faux que ceux quin'ont été que maquillés par additiond’un nom, avaient été préparés parla main du gardien de la Souricière.En particulier, l'ordre du 2 octobrequi permit à Pélissier de s’évader lelendemain et qui fut retrouvé le 4 à laSanté, est en entier de lui. Par ail¬ leurs, le petit carnet saisi sur Chris¬ tiane Pélissier établit qu’il avaittouché des sommes d'argent pour lalocation à la journée, de la cellulenuméro 10. Plusieurs autres dames,d'ailleurs, avec leurs maris détenus,ont contribué à alimenter la caissedu geôlier « compatissant ».Le versement des cotisationsd'assurances socialespour les chauffeurs de taxisLe ministère du Travail nous com¬ munique la note suivante :En application de l'article premier,paragraphe 3, du décret-loi du 28 oc¬ tobre 1935, modifiant le régime desAssurances sociales, les conducteursde voitures publiques, dont l'exploi¬ tation est assujettie à des tarifs detransport fixés par l'autorité publi¬ que, sont soumis au régime de l'assu¬ rance obligatoire, dès l'instant queleur rémunération n'excède pas lechiffre-limite prévu pour le bénéficede cette assurance.Les cotisations patronale et ouvriè¬ re sont dues depuis le premier jan¬ vier 1936.Conformément à l'article 3 de l'ar¬ rêté du 27 décembre 1935 paru auJournal Officiel du 29 décembre, lespourboires des intéressés, qui doi¬ vent entrer en compte pour la déter¬ mination de leur rémunération, se¬ ront évalués par des conventions col¬ lectives de travail, et, à défaut detelles conventions, par arrêtés du mi¬ nistre du Travail.L'unité syndicalechez les travailleurs de l'EtatLes sections de la Fédération uni¬ fiée des travailleurs de l'Etat (artil¬ lerie, poudreries, magasins adminis¬ tratifs, génie et aéronautique, em¬ ployés et agents de maîtrise, marinemilitaire, arts et métiers) ont tenuhier leurs assises patriculières dansles différentes salles de la Bourse duTravail.Voici les résultats définitifs du votepar mandats que le congrès de fusiondes deux Fédérations confédérée etunitaire avait été appelé à émettrelundi soir au sujet du cumul desfonctions syndicales et des mandatspolitiques. Contre : 287 voix ; pour :80 voix ; abstentions : 17 voix.PARTIS ET LIGUESGroupe des étudiants radicauxLa réunion du groupe des étu¬ diants radicaux de Paris aura lieuaujourd'hui mercredi, à 21 heures,au café « Chez Emile », 40, rue Ga¬ lande, et 10, rue Fouarre (angle desdeux rues).Fédération nationaledes Libres PenseursFédération de la Seine. — La com¬ mission spéciale d’unité d’action seréunira demain jeudi, à 21 heures,local habituel, rue de Châteaudun.Les responsables voudront bien êtreprésents.Parti radical-socialisteVersailles. — Les Comités radicaux¬ socialistes de la deuxième circons¬ cription de Versailles, réunis à Pois¬ sy, ont procédé à la constitution dila Fédération des Comités de cettecirconscription.Le bureau élu de la Fédération estainsi constitué : Président : RougelotHenri ; Secrétaire : Durand Fernand;Trésorier : Fourlon Pierre.Un ordre du jour a été voté décla¬ rant impossible le maintien de mi¬ nistres radicaux dans le gouverne¬ ment ; et demandant au bureau duComité Exécutif de proposer à laplus prochaine réunion du Comité lerefus de toute collaboration avec legouvernement actuel.Libre PenséeNous sommes heureux d'informer lepublic qu’une permanence de la 14esection de la Libre Pensée est ou¬ verte au numéro 47 de la rue Bé¬ nard (XIVe), à la Librairie des Tra¬ vailleurs.Le but de la Libre Pensée est de dé¬ velopper chez tous l’esprit critique etl'amour du libre examen, sans dis¬ tinction de parti, et de grouper dansson sein ceux qui se réclament de cehaut idéal. L’époque que nous vivonsest corrompue depuis des siècles parles croyances religieuses et leur amiedévouée Sa Majesté l'Argent qui gou¬ vernent le monde à leur seul bénéfice.Il est de notre devoir, pour nos en¬ fants et pour nous-mêmes, d'arracherce voile de l'au-delà et de mettre lemonde en face de ses nécessités réel¬ les. Chacun le peut dans son humblerôle ; la laïcité peut nous aider. Grou¬ pons-nous pour la défendre.Front populaireEpernay. — Dimanche après-midi,M. Eugène Frot, ancien ministre, adonné en la salle des fêtes d'Epernay(Marne) une conférence sous les aus¬ pices de la Ligue des Droits del'Homme et du Comité du Front Po¬ pulaire. Plus de 1.200 personnes yassistaient dont plusieurs élus radi¬ caux et socialistes de la région. M.Guerry, président, assisté de MM.Morange et Guen.MM. Eugène Frot, député, ancienministre, Bossus, conseiller munici¬ pal communiste de Paris, et EmileKahn, secrétaire général de la Liguedes Droits de l'Homme, ont pris suc¬ cessivement la parole très chaleu¬ reusement applaudis.La réunion se termina sans inci¬ dent. Dans la nuit, un membre de laSolidarité Française qui avait tentéde peindre des inscriptions injurieu¬ ses sur les murs de la Salle des Fêtesavait été surpris par la police. Il dé¬ clara avoir été inspiré dans son gestepar un discours du fils de M. Princequ'il avait entendu précédemment..XIVe arr. — Pour la constitutiondes Comités de défense de la Répu¬ blique, trois grands meetings inaugu¬ raux sont organisés par le Front po¬ pulaire du 14e, aujourd'hui mercredi:111, rue du Château ; 115, rue Didot,1, avenue de la Porte-d'Orléans.Trente orateurs inscrits, dont<PERSON>Rouffianges</PERSON>, Biquard, Croizat, Mau¬ vais, Paul Marcel, Graziani, MauriceLacroix, Létrange, Mension, etc...Ligue pour le Droit au Travailet le Progrès SocialVe arr — Une grande conférencesera donnée le vendredi 17 janvier,à 21 heures, à la Sorbonne, amphi¬ théâtre Richelieu, par Joseph Dubois,sur « L'Economie soviétique maî¬ tresse de ses destins ». Jacques Du¬ boin entretiendra ensuite les auditeursdu « Problème français ».Les cartes donnant droit aux placesréservées sont à la disposition des au¬ diteurs, au « Droit au Travail », 14,rue FavartViroflay. — Sous les auspices de lasection locaie des Droits de l'Homme,une grande réunion de propagandeaura lieu demain jeudi, à 21 heures,à la salie Robie, 134, route Navoù nos amis Chesneau et Ra,Martin exposeront les vérités dmiques diffusées par le « DroitTous nos amis et sympathisantssont cordialement invitésMaisons-Alfort. — L'Intersection dcanton de Charenton organisedredi 17 janvier, à 21 heures, ugrande réunion à la mairie dusons-Alfort, salle de la Justepaix. Nos camarades Compain mond Martin y parleront de « la révo¬ lution économique actuelle »."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1935" → 1935
      - "1936" → 1936
      - "1935" → 1935
    Temporal signal words: aujourd'hui, hier, ancien, plus, après
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.969

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Rouffianges' and 'amphi¬\nthéâtre Richelieu' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Rouffianges' near 'amphi¬\nthéâtre Richelieu' around 1936-01-15?
  4. Resolve temporal expressions relative to 1936-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 119 [ID: test_fr__237]:
  Publication date : 1981-02-18
  Language         : fr
  Person  : 'Favre'  (QID: N/A)
  Location: 'SUISSE'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "<LOCATION>SUISSE</LOCATION> dernière COMMISSION DES ETATS La Suissesse mariée garderait son droit de cité Berne, 17 (ATS).-La Commission du conseil des Etats chargée d'examiner le nouveau droit matrimonial, qui a terminé ses travaux mardi à Berne, a modifié sur quelques points le projet du Conseil fédéral.Elle a cependant accepté dans ses grandes lignes le projet gouvernemental et notamment le remplacement du régime actuel de l'union des biens par celui de la participation aux acquêts.Cet objet sera traité par le parlement au mois de mars.Au sujet du nom des époux, la Commission rejoint le Conseil fédéral dans son refus d'accorder le droit d'option qui permettrait aux fiancés de choisir le nom de l'épouse comme nom de famille.Mais la femme aura le droit non seulement de faire suivre son nom (<PERSON>Favre</PERSON>-Blanc), mais aussi de le faire précéder (Mme Blanc épouse Favre).La Commission n'a pas retenu la possibilité de l'option en raison de la tradition qui existe dans notre pays.En Allemagne fédérale, où le choix existe, seuls 4 % des époux en font usage.La nouvelle réglementation suisse facilitera- cependant l'adoption éventuelle par les fiancés, avant le mariage, du nom de la femme comme nom de famille.Mais il faudra de bonnes raisons pour l'autoriser (nom à consonnance étrangère, nom connu dans le commerce, la politique, etc).En ce qui concerne le droit de cité, la femme recevra, par le mariage, le droit de cité du mari mais sans perdre le sien.Une majorité s'est formée dans la Commission en faveur de cette solution."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.993

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Favre' and 'SUISSE' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Favre' near 'SUISSE' around 1981-02-18?
  4. Resolve temporal expressions relative to 1981-02-18. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 120 [ID: test_fr__10]:
  Publication date : 1948-02-23
  Language         : fr
  Person  : 'Bieler'  (QID: Q550992)
  Location: 'Zurich'  (QID: Q72)

  [ARTICLE TEXT — entity markers added]
  "Le C. P. <LOCATION>Zurich</LOCATION> gagne Z le tournoi de hockey sur glace du Centenaire Samedi et dimanche, la patinoire de Monruz était une nouvelle fois entourée d'un nombreux public qui, bravant un froid très vif, suivit avec beaucoup d'intérêt le tournoi de hockey sur glace du Centenaire. Cette manifestation sportive fut pleinement réussie ; nous exprimons tefois un léger regret : pourquoi les trois rencontres ont-elles débuté avec dix à quinze minutes de retard ? Zurich bat Montchoisi par 12 à 8 (3-0, 6-3, 3-5) Les joueurs de Lausanne commencèrent par pratiquer un jeu passablement décousu : la défense était très lente et les avants trop individuels. Aussi tait-il une nette différence de classe entre les deux équipes en présence et Zurich, jouant avec beaucoup de décision, put dès l'abord s'octroyer un avantage de trois buts par Urson, <PERSON>Bieler</PERSON> et Ernst. Au cours du second tiers, les Zuricois relâchèrent un peu leur étreinte, alors que peu à peu l'on voyait Montchoisi s'organiser et attaquer avec mordant. Ce tiers fut ainsi assez équilibré, sans toutefois que les Zuricois perdent l'initiative du jeu. Ils marqueront cinq buts par Bieler (2), Urson, Sylvio Rossi, Boiler et Gugenbuhl, tandis que Banninger devait laisser passer trois tirs des Vaudois, deux de Minder et un de Caseel. Renversement de situation au dernier tiers où Montchoisi part résolument a l'attaque en montrant des qualités insoupçonnées. Le Lausannois Hennsler est particulièrement en verve et il marquera trois buts. D'autres attaques très bien menées permettront encore à Beltrami et à Caseel de diminuer l'écart du score. Mais la défense ne parvient pas à contenir les contre-attaques zuricoises et des shots bien placés de Rossi, Ernst et Boiler consolideront ment la victoire des joueurs de la Limmat. Zurich bat Young Sprinters par 10 à 2 (5-0. 1-2. 4-0) Cette partie, disons-le franchement, nous causa une certaine déception. L'on souhaitait une lutte plus équilibrée ; Young Sprinters est certainement capable de mieux résister à Zurich qu'il ne l'a fait hier matin. Nos joueurs, il est vrai, peuvent invoquer une circonstance atténuante. Hugo Delnon était malade et, de ce fait, la première ligne neuchâteloise était désorganisée. En outre. Reto n'apparut sur la glace qu'au début du second tiers. La première partie du jeu vit ainsi une très facile domination de Zurich. Des Bieler. Schubiger, Lohrer, semaient avec joie la panique dans notre camp et marquèrent cinq buts à intervalle régulier. Le second tiers nous fit espérer un redressement de la situation. Reto est là et il semble décider à bien faire. Il s'échappe par deux fois pour marquer deux superbes buts sans que le gardien Banninger puisse esquisser le moindre mouvement de défense. Mais l'équipe neuchâteloise continue à jouer avec une certaine incohérence. Les deux frères Delnon évoluent aveo le talentueux Ulrich, mais cette ligne manque de cohésion et plus rien ne réussira. Sylvio Rossi marquera au contraire un nouveau but. Dernier tiers assez monotone, les Zuricois sont supérieurs et ils parviendront sans trop d'efforts à accentuer leur avance par trois nouveaux buts réussis par Boiler, Gugenbuhl et Urson. Relevons dans le camp neuchâtelois la bonne partie du gardien Perrottet et la rapidité, la décision et le maniement de crosse d'Ulrich. Chez les Zuricois, il faut surtout louer la sûreté d'une défense très solide et un peu rude ; la première ligne formée de Bieler, Lohrer et Schubiger fut de loin la meilleure ligne du tournoi. Young Sprinters bat Montchoisi par 5 à 3 (2-0. 1-2. 2-1) Cette rencontre nous fait oublier la décevante partie disputée le matin. Les deux grands rivaux romands se livrent une lutte très ouverte et variée. Signalons quelques duels épiques entre Hans Cattini, Stucki, les deux frères Delnon et Ulrich. Remise de sa défaillance, notre équipe joua d'une manière digne d'elle-même et elle ne cessa de jouir d'une légère supériorité sur son adversaire. Reto et Othmar Delnon ouvrirent la marque au premier tiers. Les Lausannois placèrent leur effort principal sur le second tiers, mais notre défense formée de Tinembart et du Dr Grether, ainsi que du gardien Perrottet, dans une forme exceptionnelle dimanche, parvinrent à endiguer leurs assauts à l'exception de deux qui permirent à Jansky et à Beltrami de loger le puck au fond de la cage neuchâteloise. Le dernier tiers, au cours duquel le jeu devient assez dur, permit à Young Sprinters de s'assurer une victoire méritée. Jansky profita tout d'abord judicieusement d'une erreur de notre défense, mais Othmar Delnon trompera deux fois encore le gardien Ayer. Relevons l'excellent travail d'Ulrich. Rapide, poussant jusqu'au bout chaque descente, ne considérant jamais perdue une passe, il mena avec brio les attaques de notre notro seconde ligne et certains de ses shots auraient mérité le but. Le palmarès A la suite de ces rencontre, Zurich gagne le tournoi aveo quatre points, suivi de Young Sprinters (2 p.) et Mont _, choisi (0 p.). Lo C. P. Zurich gagne le premier prix du tournoi, la grande distinction du Centenaire et le challenge du tournoi. Young Sprinters obtient la deuxième distinction du Centenaire et le challenge Vuillomenet, récompensant l'équipe jouant avec le plus de fair-play. Quant à Montchoisi, il reçoit la coupe offerte par le cinéma Palace. B. Ad. Une tournée de Young Sprinters en Tchécoslovaquie Notre équipe de hockey sur glace a été invitée à disputer un certain nombre de matches en Tchécoslovaquie, notamment contre Prague et Brno. Elle partira pour ce pays au début du mois de mars et sera renforcée par quelques autres joueurs de ligue nationale A."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Alfred Bieler
    Description: joueur professionnel de hockey sur glace suisse
    Born: ['+1923-04-18T00:00:00Z']
    Died: ['+2013-04-24T00:00:00Z']
    Birth place: ['Saint-Moritz']
    Death place: ['Zurich']
  Location Wikidata:
    Label: Zurich
    Description: ville la plus peuplée de Suisse et chef-lieu du canton de Zurich
    Country: ['Suisse', 'ancienne Confédération suisse', 'République helvétique', 'Suisse']
    Located in: ['district de Zurich']
    Aliases: {'en': ['City of Zurich', 'ZH', 'Stadt Zürich', 'Zurich, Switzerland', 'Zürich'], 'fr': ['Zürich', 'Zuerich', 'ville de Zurich'], 'de': ['Stadt Zürich'], 'lb': ['Zürech', 'Stad Zürich']}
    Coordinates: [{'lat': 47.37444444444444, 'lon': 8.54111111111111}]
  Known person–location links: {"death_place": "P20"}

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.971

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Bieler' and 'Zurich' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Bieler' near 'Zurich' around 1948-02-23?
  4. Resolve temporal expressions relative to 1948-02-23. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 121 [ID: test_fr__85]:
  Publication date : 1968-04-08
  Language         : fr
  Person  : 'Rennhard'  (QID: N/A)
  Location: 'Lausanne'  (QID: Q807)

  [ARTICLE TEXT — entity markers added]
  "Bioiiey remporte le Tour du Léman à Genève Deux importantes épreuves pour nos amateurs d'élite A l'échelon des amateurs-elites, le weekend était d'importance à Genève. Oscar Plattner, grand responsable de cette catégorie d'éventuels futurs champions, avait délégué ses pouvoirs à Gilbert Perrenoud, afin qu'il suive très attentivement ce qui se passait sur les routes. Le Comité national a, en effet, l'intention très arrêtée de mettre sur pied la meilleure équipe possible pour le Tour de l'Avenir, les Jeux olympiques et les championnats du monde. Tout un programme de sélection a ainsi été mis au point. Dimanche à midi, Gilbert Perrenoud se déclarait enchanté de ce qu'il avait vu. Non pas que l'on puisse immédiatement dire que les coureurs suisses sont en forme, mais les sujets de satisfaction ne manquaient pas : « on voit que nous sommes dans une année importante, une année où les voyages et les honneurs seront nombreux. Il y a l'Uruguay, le Mexique, des médailles à revendre. C'est pourquoi nos meilleurs coureurs se sont préparés de belle façon, c'est pourquoi aussi de nombreux jeunes frappent à la porte .. En fait, ces deux courses genevoises ont permis de nombreux enseignements. Animées toutes deux, courues assez rapidement, elles se sont révélées d'une excellente qualité. D'OESCHGER... Samedi après-midi, sur un circuit de seize kiolmètres à parcourir huit fois, quelque soixante-cinq coureurs prirent le départ. Sous le soleil, qui allait bientôt disparaître, et faire place à un violent orage. L'échappée, la bonne, vint très rapidement. Au deuxième tour déjà, après qu'un « faux départ » eut lieu, à savoir une erreur de parcours annulant les efforts des premiers audacieux. Fait assez rare, la course fut stoppée à 9 km 400 de son premier départ puis relancée. C'est alors que l'un des Belges invités, froidement, tenta de partir. Il y parvint en compagnie de Rub, d'Oeschger, de Schnetzler, le champion de Suisse, von Arx, Fischer, et les Romands Behier (Moudon), Regamey (Yverdon) et Vaucher (<LOCATION>Lausanne</LOCATION>). Cahin-caha, sur de petites routes, étroites et sinueuses, cette échappée prit quelque avance. Sur le peloton tout d'abord, sur un groupe de contre-attaque par la suite, qui allait faire sa jonction. D'ailleurs, il ne resta plus que ces hommes en course... Les autres pensaient au tour du lac du lendemain, et se retiraient II y a encore quelques audacieux : Schnetzler, Spannagel, Birrer et Weber. Mais leurs tentatives solitaires furent réduites à néant. Et sur la fin, le peloton se scinda en deux. . . . A BIOLLEY Ce tour du lac — doyenne des épreuves cyclistes, qui en était hier à sa 76 mc édition — eut un déroulement assez rare. Daniel Biolley, de Fribourg, l'expliqua une fois passée, en vainqueur, la ligne d' arrivée : « C'est mon sixième- tour du lac. Et j'avais jusqu'ici constaté que jamais une échappée partie de loin ne réussissait Aussi je n'ai pas mené depuis Versoix (km 10) où nous sommes partis. Mais comme à Evian, en abordant le col de Vinzier, nous avions plus de cinq minutes sur nos poursuivants, et plus de dix sur le peloton _, je me suis lancé dans la bagarre. » La course partit en effet très tôt : Brunner — qui allait vite disparaître — Lier, Hofer et Grin s'en allèrent vers l'entrée de l'autoroute Genève-Lausanne. Rapidement Biolley, Angelucci, Elliker, Kalt, <PERSON>Rennhard</PERSON>, Rutchmann, Thalmann, Reusser, Adam, Schneider et Melliflio les rejoignirent Et, au gré des kilomètres, de la forme de certains ou de divers ennuis mécaniques, il resta dix hommes ensemble à Evian, dont quatre partirent bien vite dès les premières côtes de la seule difficulté de la journée, quatre qui restèrent ensemble jusqu'à l'arrivée où se produisit un petit drame : Lier sprinta, gagna, mais ne savait pas qu'il y avait un tour et la distance à faire... Biolley passa donc, de même que Rennhardt. Les deux coéquipiers (d'Allegro) avaient des mines patibulaires à l'arrivée. Lier pleurait et Biolley n'était pas plus content que cela : « La victoire lui revenait il avait fait une grosse part de travail. Mais je ne pouvais pas me relever, car Rennhard avait passé. Serge DOURNOW CLASSEMENT DU GRAND PRIX DE MEINIER 1. Oeschger (Oberhofen), les 128 km en 3 h 32'13 " ; 2. Rub (Bmgg) ; 3. Fischer (Brugg) ; 4. Binggeli (Genève ; 5. Regamey (Yverdon). CLASSEMENT DU TOUR DU LÉMAN 1. Biolley (Fribourg), les 187 km en 4 h 30'36 " ; 2. Rennhard (Brugg) ; 3. Lier (Affoltern) ; 4. Thalmann (Meznau), même temps ; 5. Rutschmann (Seuzach), à 3'32 " ; 6. Hofer (Berne) ; 7. Kalt (Zurich) ; 8. Elliker (Urdorf) ; 9. Reusser (Brugg), même temps ; 10. Peter (Zurich), à 7'40 "."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Lausanne
    Description: ville de Suisse, chef-lieu du canton de Vaud
    Country: ['Suisse']
    Located in: ['canton de Berne', 'district de Lausanne']
    Aliases: {'en': ['Lausanne VD', 'Olympic Capital', 'City of Lausanne'], 'fr': ['Capitale olympique', 'Lausanne VD', 'Ville de Lausanne', 'Lausanngrad', 'Lausanngeles', "capitale du crime et de l'endettement"], 'de': ['olympische Hauptstadt']}
    Coordinates: [{'lat': 46.533333333333, 'lon': 6.6333333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.959

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Rennhard' and 'Lausanne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Rennhard' near 'Lausanne' around 1968-04-08?
  4. Resolve temporal expressions relative to 1968-04-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 122 [ID: test_fr__82]:
  Publication date : 1968-04-08
  Language         : fr
  Person  : 'Biolley'  (QID: N/A)
  Location: 'Urdorf'  (QID: Q69109)

  [ARTICLE TEXT — entity markers added]
  "Bioiiey remporte le Tour du Léman à Genève Deux importantes épreuves pour nos amateurs d'élite A l'échelon des amateurs-elites, le weekend était d'importance à Genève. Oscar Plattner, grand responsable de cette catégorie d'éventuels futurs champions, avait délégué ses pouvoirs à Gilbert Perrenoud, afin qu'il suive très attentivement ce qui se passait sur les routes. Le Comité national a, en effet, l'intention très arrêtée de mettre sur pied la meilleure équipe possible pour le Tour de l'Avenir, les Jeux olympiques et les championnats du monde. Tout un programme de sélection a ainsi été mis au point. Dimanche à midi, Gilbert Perrenoud se déclarait enchanté de ce qu'il avait vu. Non pas que l'on puisse immédiatement dire que les coureurs suisses sont en forme, mais les sujets de satisfaction ne manquaient pas : « on voit que nous sommes dans une année importante, une année où les voyages et les honneurs seront nombreux. Il y a l'Uruguay, le Mexique, des médailles à revendre. C'est pourquoi nos meilleurs coureurs se sont préparés de belle façon, c'est pourquoi aussi de nombreux jeunes frappent à la porte .. En fait, ces deux courses genevoises ont permis de nombreux enseignements. Animées toutes deux, courues assez rapidement, elles se sont révélées d'une excellente qualité. D'OESCHGER... Samedi après-midi, sur un circuit de seize kiolmètres à parcourir huit fois, quelque soixante-cinq coureurs prirent le départ. Sous le soleil, qui allait bientôt disparaître, et faire place à un violent orage. L'échappée, la bonne, vint très rapidement. Au deuxième tour déjà, après qu'un « faux départ » eut lieu, à savoir une erreur de parcours annulant les efforts des premiers audacieux. Fait assez rare, la course fut stoppée à 9 km 400 de son premier départ puis relancée. C'est alors que l'un des Belges invités, froidement, tenta de partir. Il y parvint en compagnie de Rub, d'Oeschger, de Schnetzler, le champion de Suisse, von Arx, Fischer, et les Romands Behier (Moudon), Regamey (Yverdon) et Vaucher (Lausanne). Cahin-caha, sur de petites routes, étroites et sinueuses, cette échappée prit quelque avance. Sur le peloton tout d'abord, sur un groupe de contre-attaque par la suite, qui allait faire sa jonction. D'ailleurs, il ne resta plus que ces hommes en course... Les autres pensaient au tour du lac du lendemain, et se retiraient II y a encore quelques audacieux : Schnetzler, Spannagel, Birrer et Weber. Mais leurs tentatives solitaires furent réduites à néant. Et sur la fin, le peloton se scinda en deux. . . . A BIOLLEY Ce tour du lac — doyenne des épreuves cyclistes, qui en était hier à sa 76 mc édition — eut un déroulement assez rare. Daniel <PERSON>Biolley</PERSON>, de Fribourg, l'expliqua une fois passée, en vainqueur, la ligne d' arrivée : « C'est mon sixième- tour du lac. Et j'avais jusqu'ici constaté que jamais une échappée partie de loin ne réussissait Aussi je n'ai pas mené depuis Versoix (km 10) où nous sommes partis. Mais comme à Evian, en abordant le col de Vinzier, nous avions plus de cinq minutes sur nos poursuivants, et plus de dix sur le peloton _, je me suis lancé dans la bagarre. » La course partit en effet très tôt : Brunner — qui allait vite disparaître — Lier, Hofer et Grin s'en allèrent vers l'entrée de l'autoroute Genève-Lausanne. Rapidement Biolley, Angelucci, Elliker, Kalt, Rennhard, Rutchmann, Thalmann, Reusser, Adam, Schneider et Melliflio les rejoignirent Et, au gré des kilomètres, de la forme de certains ou de divers ennuis mécaniques, il resta dix hommes ensemble à Evian, dont quatre partirent bien vite dès les premières côtes de la seule difficulté de la journée, quatre qui restèrent ensemble jusqu'à l'arrivée où se produisit un petit drame : Lier sprinta, gagna, mais ne savait pas qu'il y avait un tour et la distance à faire... Biolley passa donc, de même que Rennhardt. Les deux coéquipiers (d'Allegro) avaient des mines patibulaires à l'arrivée. Lier pleurait et Biolley n'était pas plus content que cela : « La victoire lui revenait il avait fait une grosse part de travail. Mais je ne pouvais pas me relever, car Rennhard avait passé. Serge DOURNOW CLASSEMENT DU GRAND PRIX DE MEINIER 1. Oeschger (Oberhofen), les 128 km en 3 h 32'13 " ; 2. Rub (Bmgg) ; 3. Fischer (Brugg) ; 4. Binggeli (Genève ; 5. Regamey (Yverdon). CLASSEMENT DU TOUR DU LÉMAN 1. Biolley (Fribourg), les 187 km en 4 h 30'36 " ; 2. Rennhard (Brugg) ; 3. Lier (Affoltern) ; 4. Thalmann (Meznau), même temps ; 5. Rutschmann (Seuzach), à 3'32 " ; 6. Hofer (Berne) ; 7. Kalt (Zurich) ; 8. Elliker (<LOCATION>Urdorf</LOCATION>) ; 9. Reusser (Brugg), même temps ; 10. Peter (Zurich), à 7'40 "."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.959

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Biolley' and 'Urdorf' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Biolley' near 'Urdorf' around 1968-04-08?
  4. Resolve temporal expressions relative to 1968-04-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 123 [ID: test_fr__180]:
  Publication date : NA
  Language         : fr
  Person  : 'Renault'  (QID: N/A)
  Location: 'Montlhéry'  (QID: Q250024)

  [ARTICLE TEXT — entity markers added]
  "Le 16 novembre dernier, Saugé rentraitdans la commune avec <PERSON>Renault</PERSON>, et lui annon¬ çait qu'il irait dans l'après-midi chercher desfromages à Brière, et que le soir, vers huitheures, il s'arrêterait à <LOCATION>Montlhéry</LOCATION>. En effet,vers deux heures, Saugé partit dans sa char¬ rette, mais il n'était pas à cent mètres de sademeure qu'il s'aperçut qu'il avait oublié salimousine ; il retourna sur ses pas et trouvadans sa cour sa femme et Renault : celui-ciexpliqua sa présence en disant qu'il venaitvoir si des clous qu'il avait achetés n'étaientpas restés dans la charrette, et il se retira a¬ vec le mari. A peine à trois cents mètres dela maison, celui-ci remarqua qu'il lui man¬ quait ses éclisses à fromage ; il revint. A sonarrivée, sa femme se présenta devant lui, sor¬ tant de la laiterie, où Saugé entrevit l'ombred'un homme ; il y entra et trouva Renault ca¬ ché sous la cage de l'escalier. Le mari mani¬ festa énergiquement ses soupçons, et intima àRenault, avec menaces, l'ordre de ne plusmettre les pieds chez lui."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Montlhéry
    Description: commune française du département de l'Essonne
    Country: ['France']
    Located in: ['Seine-et-Oise', 'Essonne', 'arrondissement de Palaiseau']
    Aliases: {'fr': ['Monthléry'], 'de': ['Montlhery']}
    Coordinates: [{'lat': 48.638611111111, 'lon': 2.2722222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.995

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Renault' and 'Montlhéry' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Renault' near 'Montlhéry' around NA?
  4. Resolve temporal expressions relative to NA. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 124 [ID: test_fr__177]:
  Publication date : NA
  Language         : fr
  Person  : 'Saugé'  (QID: N/A)
  Location: 'Brière'  (QID: Q3373423)

  [ARTICLE TEXT — entity markers added]
  "Le 16 novembre dernier, <PERSON>Saugé</PERSON> rentraitdans la commune avec Renault, et lui annon¬ çait qu'il irait dans l'après-midi chercher desfromages à <LOCATION>Brière</LOCATION>, et que le soir, vers huitheures, il s'arrêterait à Montlhéry. En effet,vers deux heures, Saugé partit dans sa char¬ rette, mais il n'était pas à cent mètres de sademeure qu'il s'aperçut qu'il avait oublié salimousine ; il retourna sur ses pas et trouvadans sa cour sa femme et Renault : celui-ciexpliqua sa présence en disant qu'il venaitvoir si des clous qu'il avait achetés n'étaientpas restés dans la charrette, et il se retira a¬ vec le mari. A peine à trois cents mètres dela maison, celui-ci remarqua qu'il lui man¬ quait ses éclisses à fromage ; il revint. A sonarrivée, sa femme se présenta devant lui, sor¬ tant de la laiterie, où Saugé entrevit l'ombred'un homme ; il y entra et trouva Renault ca¬ ché sous la cage de l'escalier. Le mari mani¬ festa énergiquement ses soupçons, et intima àRenault, avec menaces, l'ordre de ne plusmettre les pieds chez lui."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Pays de Bière
    Country: ['Q142']
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.995

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Saugé' and 'Brière' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Saugé' near 'Brière' around NA?
  4. Resolve temporal expressions relative to NA. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 125 [ID: test_fr__89]:
  Publication date : 1968-04-08
  Language         : fr
  Person  : 'Biolley'  (QID: N/A)
  Location: 'Affoltern'  (QID: Q68290)

  [ARTICLE TEXT — entity markers added]
  "Bioiiey remporte le Tour du Léman à Genève Deux importantes épreuves pour nos amateurs d'élite A l'échelon des amateurs-elites, le weekend était d'importance à Genève. Oscar Plattner, grand responsable de cette catégorie d'éventuels futurs champions, avait délégué ses pouvoirs à Gilbert Perrenoud, afin qu'il suive très attentivement ce qui se passait sur les routes. Le Comité national a, en effet, l'intention très arrêtée de mettre sur pied la meilleure équipe possible pour le Tour de l'Avenir, les Jeux olympiques et les championnats du monde. Tout un programme de sélection a ainsi été mis au point. Dimanche à midi, Gilbert Perrenoud se déclarait enchanté de ce qu'il avait vu. Non pas que l'on puisse immédiatement dire que les coureurs suisses sont en forme, mais les sujets de satisfaction ne manquaient pas : « on voit que nous sommes dans une année importante, une année où les voyages et les honneurs seront nombreux. Il y a l'Uruguay, le Mexique, des médailles à revendre. C'est pourquoi nos meilleurs coureurs se sont préparés de belle façon, c'est pourquoi aussi de nombreux jeunes frappent à la porte .. En fait, ces deux courses genevoises ont permis de nombreux enseignements. Animées toutes deux, courues assez rapidement, elles se sont révélées d'une excellente qualité. D'OESCHGER... Samedi après-midi, sur un circuit de seize kiolmètres à parcourir huit fois, quelque soixante-cinq coureurs prirent le départ. Sous le soleil, qui allait bientôt disparaître, et faire place à un violent orage. L'échappée, la bonne, vint très rapidement. Au deuxième tour déjà, après qu'un « faux départ » eut lieu, à savoir une erreur de parcours annulant les efforts des premiers audacieux. Fait assez rare, la course fut stoppée à 9 km 400 de son premier départ puis relancée. C'est alors que l'un des Belges invités, froidement, tenta de partir. Il y parvint en compagnie de Rub, d'Oeschger, de Schnetzler, le champion de Suisse, von Arx, Fischer, et les Romands Behier (Moudon), Regamey (Yverdon) et Vaucher (Lausanne). Cahin-caha, sur de petites routes, étroites et sinueuses, cette échappée prit quelque avance. Sur le peloton tout d'abord, sur un groupe de contre-attaque par la suite, qui allait faire sa jonction. D'ailleurs, il ne resta plus que ces hommes en course... Les autres pensaient au tour du lac du lendemain, et se retiraient II y a encore quelques audacieux : Schnetzler, Spannagel, Birrer et Weber. Mais leurs tentatives solitaires furent réduites à néant. Et sur la fin, le peloton se scinda en deux. . . . A BIOLLEY Ce tour du lac — doyenne des épreuves cyclistes, qui en était hier à sa 76 mc édition — eut un déroulement assez rare. Daniel <PERSON>Biolley</PERSON>, de Fribourg, l'expliqua une fois passée, en vainqueur, la ligne d' arrivée : « C'est mon sixième- tour du lac. Et j'avais jusqu'ici constaté que jamais une échappée partie de loin ne réussissait Aussi je n'ai pas mené depuis Versoix (km 10) où nous sommes partis. Mais comme à Evian, en abordant le col de Vinzier, nous avions plus de cinq minutes sur nos poursuivants, et plus de dix sur le peloton _, je me suis lancé dans la bagarre. » La course partit en effet très tôt : Brunner — qui allait vite disparaître — Lier, Hofer et Grin s'en allèrent vers l'entrée de l'autoroute Genève-Lausanne. Rapidement Biolley, Angelucci, Elliker, Kalt, Rennhard, Rutchmann, Thalmann, Reusser, Adam, Schneider et Melliflio les rejoignirent Et, au gré des kilomètres, de la forme de certains ou de divers ennuis mécaniques, il resta dix hommes ensemble à Evian, dont quatre partirent bien vite dès les premières côtes de la seule difficulté de la journée, quatre qui restèrent ensemble jusqu'à l'arrivée où se produisit un petit drame : Lier sprinta, gagna, mais ne savait pas qu'il y avait un tour et la distance à faire... Biolley passa donc, de même que Rennhardt. Les deux coéquipiers (d'Allegro) avaient des mines patibulaires à l'arrivée. Lier pleurait et Biolley n'était pas plus content que cela : « La victoire lui revenait il avait fait une grosse part de travail. Mais je ne pouvais pas me relever, car Rennhard avait passé. Serge DOURNOW CLASSEMENT DU GRAND PRIX DE MEINIER 1. Oeschger (Oberhofen), les 128 km en 3 h 32'13 " ; 2. Rub (Bmgg) ; 3. Fischer (Brugg) ; 4. Binggeli (Genève ; 5. Regamey (Yverdon). CLASSEMENT DU TOUR DU LÉMAN 1. Biolley (Fribourg), les 187 km en 4 h 30'36 " ; 2. Rennhard (Brugg) ; 3. Lier (<LOCATION>Affoltern</LOCATION>) ; 4. Thalmann (Meznau), même temps ; 5. Rutschmann (Seuzach), à 3'32 " ; 6. Hofer (Berne) ; 7. Kalt (Zurich) ; 8. Elliker (Urdorf) ; 9. Reusser (Brugg), même temps ; 10. Peter (Zurich), à 7'40 "."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Affoltern am Albis
    Description: commune suisse
    Country: ['Q39']
    Located in: ['Q656635']
    Aliases: {'en': ['Affoltern am Albis ZH'], 'de': ['Affoltern a.A.', 'Affoltere', 'Afzgi', 'Affzgi']}
    Coordinates: [{'lat': 47.28167, 'lon': 8.45023}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.959

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Biolley' and 'Affoltern' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Biolley' near 'Affoltern' around 1968-04-08?
  4. Resolve temporal expressions relative to 1968-04-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 126 [ID: test_fr__94]:
  Publication date : 1968-04-08
  Language         : fr
  Person  : 'Elliker'  (QID: N/A)
  Location: 'Zurich'  (QID: Q72)

  [ARTICLE TEXT — entity markers added]
  "Bioiiey remporte le Tour du Léman à Genève Deux importantes épreuves pour nos amateurs d'élite A l'échelon des amateurs-elites, le weekend était d'importance à Genève. Oscar Plattner, grand responsable de cette catégorie d'éventuels futurs champions, avait délégué ses pouvoirs à Gilbert Perrenoud, afin qu'il suive très attentivement ce qui se passait sur les routes. Le Comité national a, en effet, l'intention très arrêtée de mettre sur pied la meilleure équipe possible pour le Tour de l'Avenir, les Jeux olympiques et les championnats du monde. Tout un programme de sélection a ainsi été mis au point. Dimanche à midi, Gilbert Perrenoud se déclarait enchanté de ce qu'il avait vu. Non pas que l'on puisse immédiatement dire que les coureurs suisses sont en forme, mais les sujets de satisfaction ne manquaient pas : « on voit que nous sommes dans une année importante, une année où les voyages et les honneurs seront nombreux. Il y a l'Uruguay, le Mexique, des médailles à revendre. C'est pourquoi nos meilleurs coureurs se sont préparés de belle façon, c'est pourquoi aussi de nombreux jeunes frappent à la porte .. En fait, ces deux courses genevoises ont permis de nombreux enseignements. Animées toutes deux, courues assez rapidement, elles se sont révélées d'une excellente qualité. D'OESCHGER... Samedi après-midi, sur un circuit de seize kiolmètres à parcourir huit fois, quelque soixante-cinq coureurs prirent le départ. Sous le soleil, qui allait bientôt disparaître, et faire place à un violent orage. L'échappée, la bonne, vint très rapidement. Au deuxième tour déjà, après qu'un « faux départ » eut lieu, à savoir une erreur de parcours annulant les efforts des premiers audacieux. Fait assez rare, la course fut stoppée à 9 km 400 de son premier départ puis relancée. C'est alors que l'un des Belges invités, froidement, tenta de partir. Il y parvint en compagnie de Rub, d'Oeschger, de Schnetzler, le champion de Suisse, von Arx, Fischer, et les Romands Behier (Moudon), Regamey (Yverdon) et Vaucher (Lausanne). Cahin-caha, sur de petites routes, étroites et sinueuses, cette échappée prit quelque avance. Sur le peloton tout d'abord, sur un groupe de contre-attaque par la suite, qui allait faire sa jonction. D'ailleurs, il ne resta plus que ces hommes en course... Les autres pensaient au tour du lac du lendemain, et se retiraient II y a encore quelques audacieux : Schnetzler, Spannagel, Birrer et Weber. Mais leurs tentatives solitaires furent réduites à néant. Et sur la fin, le peloton se scinda en deux. . . . A BIOLLEY Ce tour du lac — doyenne des épreuves cyclistes, qui en était hier à sa 76 mc édition — eut un déroulement assez rare. Daniel Biolley, de Fribourg, l'expliqua une fois passée, en vainqueur, la ligne d' arrivée : « C'est mon sixième- tour du lac. Et j'avais jusqu'ici constaté que jamais une échappée partie de loin ne réussissait Aussi je n'ai pas mené depuis Versoix (km 10) où nous sommes partis. Mais comme à Evian, en abordant le col de Vinzier, nous avions plus de cinq minutes sur nos poursuivants, et plus de dix sur le peloton _, je me suis lancé dans la bagarre. » La course partit en effet très tôt : Brunner — qui allait vite disparaître — Lier, Hofer et Grin s'en allèrent vers l'entrée de l'autoroute Genève-Lausanne. Rapidement Biolley, Angelucci, <PERSON>Elliker</PERSON>, Kalt, Rennhard, Rutchmann, Thalmann, Reusser, Adam, Schneider et Melliflio les rejoignirent Et, au gré des kilomètres, de la forme de certains ou de divers ennuis mécaniques, il resta dix hommes ensemble à Evian, dont quatre partirent bien vite dès les premières côtes de la seule difficulté de la journée, quatre qui restèrent ensemble jusqu'à l'arrivée où se produisit un petit drame : Lier sprinta, gagna, mais ne savait pas qu'il y avait un tour et la distance à faire... Biolley passa donc, de même que Rennhardt. Les deux coéquipiers (d'Allegro) avaient des mines patibulaires à l'arrivée. Lier pleurait et Biolley n'était pas plus content que cela : « La victoire lui revenait il avait fait une grosse part de travail. Mais je ne pouvais pas me relever, car Rennhard avait passé. Serge DOURNOW CLASSEMENT DU GRAND PRIX DE MEINIER 1. Oeschger (Oberhofen), les 128 km en 3 h 32'13 " ; 2. Rub (Bmgg) ; 3. Fischer (Brugg) ; 4. Binggeli (Genève ; 5. Regamey (Yverdon). CLASSEMENT DU TOUR DU LÉMAN 1. Biolley (Fribourg), les 187 km en 4 h 30'36 " ; 2. Rennhard (Brugg) ; 3. Lier (Affoltern) ; 4. Thalmann (Meznau), même temps ; 5. Rutschmann (Seuzach), à 3'32 " ; 6. Hofer (Berne) ; 7. Kalt (<LOCATION>Zurich</LOCATION>) ; 8. Elliker (Urdorf) ; 9. Reusser (Brugg), même temps ; 10. Peter (Zurich), à 7'40 "."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Zurich
    Description: ville la plus peuplée de Suisse et chef-lieu du canton de Zurich
    Country: ['Suisse', 'ancienne Confédération suisse', 'République helvétique', 'Suisse']
    Located in: ['district de Zurich']
    Aliases: {'en': ['City of Zurich', 'ZH', 'Stadt Zürich', 'Zurich, Switzerland', 'Zürich'], 'fr': ['Zürich', 'Zuerich', 'ville de Zurich'], 'de': ['Stadt Zürich'], 'lb': ['Zürech', 'Stad Zürich']}
    Coordinates: [{'lat': 47.37444444444444, 'lon': 8.54111111111111}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.959

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Elliker' and 'Zurich' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Elliker' near 'Zurich' around 1968-04-08?
  4. Resolve temporal expressions relative to 1968-04-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 127 [ID: test_fr__83]:
  Publication date : 1968-04-08
  Language         : fr
  Person  : 'Brunner'  (QID: Q18398295)
  Location: 'Lausanne'  (QID: Q807)

  [ARTICLE TEXT — entity markers added]
  "Bioiiey remporte le Tour du Léman à Genève Deux importantes épreuves pour nos amateurs d'élite A l'échelon des amateurs-elites, le weekend était d'importance à Genève. Oscar Plattner, grand responsable de cette catégorie d'éventuels futurs champions, avait délégué ses pouvoirs à Gilbert Perrenoud, afin qu'il suive très attentivement ce qui se passait sur les routes. Le Comité national a, en effet, l'intention très arrêtée de mettre sur pied la meilleure équipe possible pour le Tour de l'Avenir, les Jeux olympiques et les championnats du monde. Tout un programme de sélection a ainsi été mis au point. Dimanche à midi, Gilbert Perrenoud se déclarait enchanté de ce qu'il avait vu. Non pas que l'on puisse immédiatement dire que les coureurs suisses sont en forme, mais les sujets de satisfaction ne manquaient pas : « on voit que nous sommes dans une année importante, une année où les voyages et les honneurs seront nombreux. Il y a l'Uruguay, le Mexique, des médailles à revendre. C'est pourquoi nos meilleurs coureurs se sont préparés de belle façon, c'est pourquoi aussi de nombreux jeunes frappent à la porte .. En fait, ces deux courses genevoises ont permis de nombreux enseignements. Animées toutes deux, courues assez rapidement, elles se sont révélées d'une excellente qualité. D'OESCHGER... Samedi après-midi, sur un circuit de seize kiolmètres à parcourir huit fois, quelque soixante-cinq coureurs prirent le départ. Sous le soleil, qui allait bientôt disparaître, et faire place à un violent orage. L'échappée, la bonne, vint très rapidement. Au deuxième tour déjà, après qu'un « faux départ » eut lieu, à savoir une erreur de parcours annulant les efforts des premiers audacieux. Fait assez rare, la course fut stoppée à 9 km 400 de son premier départ puis relancée. C'est alors que l'un des Belges invités, froidement, tenta de partir. Il y parvint en compagnie de Rub, d'Oeschger, de Schnetzler, le champion de Suisse, von Arx, Fischer, et les Romands Behier (Moudon), Regamey (Yverdon) et Vaucher (<LOCATION>Lausanne</LOCATION>). Cahin-caha, sur de petites routes, étroites et sinueuses, cette échappée prit quelque avance. Sur le peloton tout d'abord, sur un groupe de contre-attaque par la suite, qui allait faire sa jonction. D'ailleurs, il ne resta plus que ces hommes en course... Les autres pensaient au tour du lac du lendemain, et se retiraient II y a encore quelques audacieux : Schnetzler, Spannagel, Birrer et Weber. Mais leurs tentatives solitaires furent réduites à néant. Et sur la fin, le peloton se scinda en deux. . . . A BIOLLEY Ce tour du lac — doyenne des épreuves cyclistes, qui en était hier à sa 76 mc édition — eut un déroulement assez rare. Daniel Biolley, de Fribourg, l'expliqua une fois passée, en vainqueur, la ligne d' arrivée : « C'est mon sixième- tour du lac. Et j'avais jusqu'ici constaté que jamais une échappée partie de loin ne réussissait Aussi je n'ai pas mené depuis Versoix (km 10) où nous sommes partis. Mais comme à Evian, en abordant le col de Vinzier, nous avions plus de cinq minutes sur nos poursuivants, et plus de dix sur le peloton _, je me suis lancé dans la bagarre. » La course partit en effet très tôt : <PERSON>Brunner</PERSON> — qui allait vite disparaître — Lier, Hofer et Grin s'en allèrent vers l'entrée de l'autoroute Genève-Lausanne. Rapidement Biolley, Angelucci, Elliker, Kalt, Rennhard, Rutchmann, Thalmann, Reusser, Adam, Schneider et Melliflio les rejoignirent Et, au gré des kilomètres, de la forme de certains ou de divers ennuis mécaniques, il resta dix hommes ensemble à Evian, dont quatre partirent bien vite dès les premières côtes de la seule difficulté de la journée, quatre qui restèrent ensemble jusqu'à l'arrivée où se produisit un petit drame : Lier sprinta, gagna, mais ne savait pas qu'il y avait un tour et la distance à faire... Biolley passa donc, de même que Rennhardt. Les deux coéquipiers (d'Allegro) avaient des mines patibulaires à l'arrivée. Lier pleurait et Biolley n'était pas plus content que cela : « La victoire lui revenait il avait fait une grosse part de travail. Mais je ne pouvais pas me relever, car Rennhard avait passé. Serge DOURNOW CLASSEMENT DU GRAND PRIX DE MEINIER 1. Oeschger (Oberhofen), les 128 km en 3 h 32'13 " ; 2. Rub (Bmgg) ; 3. Fischer (Brugg) ; 4. Binggeli (Genève ; 5. Regamey (Yverdon). CLASSEMENT DU TOUR DU LÉMAN 1. Biolley (Fribourg), les 187 km en 4 h 30'36 " ; 2. Rennhard (Brugg) ; 3. Lier (Affoltern) ; 4. Thalmann (Meznau), même temps ; 5. Rutschmann (Seuzach), à 3'32 " ; 6. Hofer (Berne) ; 7. Kalt (Zurich) ; 8. Elliker (Urdorf) ; 9. Reusser (Brugg), même temps ; 10. Peter (Zurich), à 7'40 "."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Christian Brunner
    Description: cycliste suisse
    Born: ['+1953-04-02T00:00:00Z']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: hier, plus, après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.959

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Brunner' and 'Lausanne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Brunner' near 'Lausanne' around 1968-04-08?
  4. Resolve temporal expressions relative to 1968-04-08. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 128 [ID: test_fr__62]:
  Publication date : 1936-01-15
  Language         : fr
  Person  : 'Joseph Dubois'  (QID: N/A)
  Location: 'amphi¬\nthéâtre Richelieu'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Deux nouvelles inculpationsfrappent le surveillantcomplaisant valletM. Hude, juge d'instruction, a in¬ culpé hier le surveillant Vallet de cor¬ ruption de fonctionnaire, faux et usa¬ ge de faux. Tout d'abord, l'expertGebelin avait établi que tous les or¬ dres d'extraction, aussi bien ceux quisont entièrement faux que ceux quin'ont été que maquillés par additiond’un nom, avaient été préparés parla main du gardien de la Souricière.En particulier, l'ordre du 2 octobrequi permit à Pélissier de s’évader lelendemain et qui fut retrouvé le 4 à laSanté, est en entier de lui. Par ail¬ leurs, le petit carnet saisi sur Chris¬ tiane Pélissier établit qu’il avaittouché des sommes d'argent pour lalocation à la journée, de la cellulenuméro 10. Plusieurs autres dames,d'ailleurs, avec leurs maris détenus,ont contribué à alimenter la caissedu geôlier « compatissant ».Le versement des cotisationsd'assurances socialespour les chauffeurs de taxisLe ministère du Travail nous com¬ munique la note suivante :En application de l'article premier,paragraphe 3, du décret-loi du 28 oc¬ tobre 1935, modifiant le régime desAssurances sociales, les conducteursde voitures publiques, dont l'exploi¬ tation est assujettie à des tarifs detransport fixés par l'autorité publi¬ que, sont soumis au régime de l'assu¬ rance obligatoire, dès l'instant queleur rémunération n'excède pas lechiffre-limite prévu pour le bénéficede cette assurance.Les cotisations patronale et ouvriè¬ re sont dues depuis le premier jan¬ vier 1936.Conformément à l'article 3 de l'ar¬ rêté du 27 décembre 1935 paru auJournal Officiel du 29 décembre, lespourboires des intéressés, qui doi¬ vent entrer en compte pour la déter¬ mination de leur rémunération, se¬ ront évalués par des conventions col¬ lectives de travail, et, à défaut detelles conventions, par arrêtés du mi¬ nistre du Travail.L'unité syndicalechez les travailleurs de l'EtatLes sections de la Fédération uni¬ fiée des travailleurs de l'Etat (artil¬ lerie, poudreries, magasins adminis¬ tratifs, génie et aéronautique, em¬ ployés et agents de maîtrise, marinemilitaire, arts et métiers) ont tenuhier leurs assises patriculières dansles différentes salles de la Bourse duTravail.Voici les résultats définitifs du votepar mandats que le congrès de fusiondes deux Fédérations confédérée etunitaire avait été appelé à émettrelundi soir au sujet du cumul desfonctions syndicales et des mandatspolitiques. Contre : 287 voix ; pour :80 voix ; abstentions : 17 voix.PARTIS ET LIGUESGroupe des étudiants radicauxLa réunion du groupe des étu¬ diants radicaux de Paris aura lieuaujourd'hui mercredi, à 21 heures,au café « Chez Emile », 40, rue Ga¬ lande, et 10, rue Fouarre (angle desdeux rues).Fédération nationaledes Libres PenseursFédération de la Seine. — La com¬ mission spéciale d’unité d’action seréunira demain jeudi, à 21 heures,local habituel, rue de Châteaudun.Les responsables voudront bien êtreprésents.Parti radical-socialisteVersailles. — Les Comités radicaux¬ socialistes de la deuxième circons¬ cription de Versailles, réunis à Pois¬ sy, ont procédé à la constitution dila Fédération des Comités de cettecirconscription.Le bureau élu de la Fédération estainsi constitué : Président : RougelotHenri ; Secrétaire : Durand Fernand;Trésorier : Fourlon Pierre.Un ordre du jour a été voté décla¬ rant impossible le maintien de mi¬ nistres radicaux dans le gouverne¬ ment ; et demandant au bureau duComité Exécutif de proposer à laplus prochaine réunion du Comité lerefus de toute collaboration avec legouvernement actuel.Libre PenséeNous sommes heureux d'informer lepublic qu’une permanence de la 14esection de la Libre Pensée est ou¬ verte au numéro 47 de la rue Bé¬ nard (XIVe), à la Librairie des Tra¬ vailleurs.Le but de la Libre Pensée est de dé¬ velopper chez tous l’esprit critique etl'amour du libre examen, sans dis¬ tinction de parti, et de grouper dansson sein ceux qui se réclament de cehaut idéal. L’époque que nous vivonsest corrompue depuis des siècles parles croyances religieuses et leur amiedévouée Sa Majesté l'Argent qui gou¬ vernent le monde à leur seul bénéfice.Il est de notre devoir, pour nos en¬ fants et pour nous-mêmes, d'arracherce voile de l'au-delà et de mettre lemonde en face de ses nécessités réel¬ les. Chacun le peut dans son humblerôle ; la laïcité peut nous aider. Grou¬ pons-nous pour la défendre.Front populaireEpernay. — Dimanche après-midi,M. Eugène Frot, ancien ministre, adonné en la salle des fêtes d'Epernay(Marne) une conférence sous les aus¬ pices de la Ligue des Droits del'Homme et du Comité du Front Po¬ pulaire. Plus de 1.200 personnes yassistaient dont plusieurs élus radi¬ caux et socialistes de la région. M.Guerry, président, assisté de MM.Morange et Guen.MM. Eugène Frot, député, ancienministre, Bossus, conseiller munici¬ pal communiste de Paris, et EmileKahn, secrétaire général de la Liguedes Droits de l'Homme, ont pris suc¬ cessivement la parole très chaleu¬ reusement applaudis.La réunion se termina sans inci¬ dent. Dans la nuit, un membre de laSolidarité Française qui avait tentéde peindre des inscriptions injurieu¬ ses sur les murs de la Salle des Fêtesavait été surpris par la police. Il dé¬ clara avoir été inspiré dans son gestepar un discours du fils de M. Princequ'il avait entendu précédemment..XIVe arr. — Pour la constitutiondes Comités de défense de la Répu¬ blique, trois grands meetings inaugu¬ raux sont organisés par le Front po¬ pulaire du 14e, aujourd'hui mercredi:111, rue du Château ; 115, rue Didot,1, avenue de la Porte-d'Orléans.Trente orateurs inscrits, dontRouffianges, Biquard, Croizat, Mau¬ vais, Paul Marcel, Graziani, MauriceLacroix, Létrange, Mension, etc...Ligue pour le Droit au Travailet le Progrès SocialVe arr — Une grande conférencesera donnée le vendredi 17 janvier,à 21 heures, à la Sorbonne, amphi¬ théâtre Richelieu, par <PERSON>Joseph Dubois</PERSON>,sur « L'Economie soviétique maî¬ tresse de ses destins ». Jacques Du¬ boin entretiendra ensuite les auditeursdu « Problème français ».Les cartes donnant droit aux placesréservées sont à la disposition des au¬ diteurs, au « Droit au Travail », 14,rue FavartViroflay. — Sous les auspices de lasection locaie des Droits de l'Homme,une grande réunion de propagandeaura lieu demain jeudi, à 21 heures,à la salie Robie, 134, route Navoù nos amis Chesneau et Ra,Martin exposeront les vérités dmiques diffusées par le « DroitTous nos amis et sympathisantssont cordialement invitésMaisons-Alfort. — L'Intersection dcanton de Charenton organisedredi 17 janvier, à 21 heures, ugrande réunion à la mairie dusons-Alfort, salle de la Justepaix. Nos camarades Compain mond Martin y parleront de « la révo¬ lution économique actuelle »."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1935" → 1935
      - "1936" → 1936
      - "1935" → 1935
    Temporal signal words: aujourd'hui, hier, ancien, plus, après
    Timex within ±14-day isAt window: True
    Nearest timex distance to publication date: 0 days
    OCR quality estimate: 0.969

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Joseph Dubois' and 'amphi¬\nthéâtre Richelieu' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Joseph Dubois' near 'amphi¬\nthéâtre Richelieu' around 1936-01-15?
  4. Resolve temporal expressions relative to 1936-01-15. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 129 [ID: surprise_test_fr__176]:
  Publication date : 1542
  Language         : fr
  Person  : 'Thalmondoys'  (QID: N/A)
  Location: 'port de Olone'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Car elle estoit grande comme six Oriflans, & avoit les pieds fenduz en doigtz, comme le cheval de Jules Cesar, les aureilles ainsi pendentes, comme les chievres de Languegoth, & une petite corne au cul, Au reste avoit poil d' alezan toustade entreillize de grizes pommelettes. Mais sus tout avoit la queue horrible. Car elle estoit poy plus poy moins grosse comme la pile sainct Mars aupres de Langes : & ainsi quarree, avecques les brancars ny plus ny moins ennicrochez, que sont les espicz au bled. Si de ce vous esmerveillez : esmerveillez vous dadvantaige de la queue des beliers de Scythie : que pesoit plus de trente livres, & des moutons de Surie, esquelz fault ( si Tenaud dict vray ) affuster une charrette au cul, pour la porter tant elle est longue & pesante. Vous ne l' avez pas telle vous aultres paillardes de plat pays. Et fut amenee par mer en troys carracques & un brigantin jusques au <LOCATION>port de Olone</LOCATION> en <PERSON>Thalmondoys</PERSON> Lors que Grandgousier la veit, Voicy ( dist il ) bien le cas pour porter mon filz a Paris. Or ca de par dieu, tout yra bien. Il sera grand clerc on temps advenir. Si n' estoient messieurs les bestes, nous vivrions comme clercs. Au lendemain apres boyre ( comme entendez ) prindrent chemin, Gargantua son precepteur Ponocrates & ses gens, ensemble eulx Eudemon le jeune paige. Et par ce que c' estoit en temps serain & bien attrempé, son pere luy feist faire des botes fauves. Babin les nomme brodequins. Ainsi joyeusement passerent leur grand chemin : & tousjours grand chere : jusques au dessus de Orleans. Au quel lieu estoit une ample forest de la longueur de trente & cinq lieues & de largeur dix & sept ou environ. Icelle estoit horriblement fertile & copieuse en mousches bovines & freslons, de sorte que c' estoit une vraye briguanderye pour les pauvres jumens, asnes, & chevaulx. Mais la jument de Gargantua vengea honnestement tous les oultrages en icelle perpetrees sur les bestes de son espece, par un tour, duquel ne se doubtoient mie."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Thalmondoys' and 'port de Olone' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Thalmondoys' near 'port de Olone' around 1542?
  4. Resolve temporal expressions relative to 1542. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 130 [ID: surprise_test_fr__383]:
  Publication date : 1678
  Language         : fr
  Person  : 'François I'  (QID: Q129857)
  Location: 'France'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "Il est vray que ces renoncemens doivent avoir quelque cause legitime, et que les rois feroient tort à leurs successeurs, s' ils retranchoient une province du corps de l' etat sans y être contraints, ou sans y trouver de grands avantages. Mais lors qu' ils ne consentent à ces retranchemens que par necessité, ou pour le bien et l' utilité du royaume, leurs successeurs n' ont aucun sujet de se plaindre d' eux ; et s' ils en ont, la plupart de nos rois auroient eu droit de se plaindre de leurs predecesseurs, particulierement les enfans de Henry Ii qui par le traité de château Cambresy, relâcha et rendit près de deux cens villes ou forteresses. Il faut ajoutter à cela qu' il est difficile de marquer ce point de grandeur dont parle l' auteur qu' on a cité, où les etats étant parvenus, il n' est plus permis aux rois d' en retrancher aucune partie ; parce qu' il ne s' est jamais passé de temps considerable depuis l' établissement de la monarchie, que la <LOCATION>France</LOCATION> ne se soit accruë par les conquêtes de nos rois, ou n' ait diminué par celles de nos voisins. De plus, les rois de la premiere et seconde race luy ont très - souvent ôté sa grandeur, la partageant entre leurs enfans, et divisant le royaume en plusieurs royaumes. Enfin pour ne pas alleguer toutes les provinces qui ont été desunies de la couronne, il suffit de dire que la Bourgogne l' avoit été par le roy Henry, petit fils de Hugues Capet, en faveur de Robert son frere ; qu' elle y revint sous le roy Jean, qui la donna peu de temps après à Philippe Le Hardy son quatriéme fils ; et qu' après la mort de Charles dernier Duc de Bourgogne, Loüis XI s' en rendit le maître ; de sorte qu' il n' y avoit pas cinquante ans qu' elle étoit réünie à la couronne lorsque <PERSON>François I</PERSON> la voulut ceder. Passons maintenant aux autres pretextes qu' on prend pour se dispenser de la fidelité qu' on doit aux souverains."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: France
    Description: pays transcontinental au territoire métropolitain situé en Europe de l'Ouest
    Country: ['France']
    Aliases: {'en': ['French Republic'], 'fr': ['République française', 'RF', 'fr', 'la République française', 'Fr.', 'La France', "L'Hexagone"], 'de': ['Französische Republik', 'fr', 'RF']}
    Coordinates: [{'lat': 47, 'lon': 2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: maintenant, plus, après, avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'François I' and 'France' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'François I' near 'France' around 1678?
  4. Resolve temporal expressions relative to 1678. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 131 [ID: surprise_test_fr__210]:
  Publication date : 1756
  Language         : fr
  Person  : 'Pascal II'  (QID: N/A)
  Location: 'Troye'  (QID: Q211953)

  [ARTICLE TEXT — entity markers added]
  "L' empereur soûtenait, non sans raison, que les états de Matilde lui devaient revenir comme un fief de l' empire ; ainsi les papes combattaient pour le spirituel et pour le temporel. <PERSON>Pascal II</PERSON> n' obtint du roi Philippe que la permission de tenir un concile à <LOCATION>Troye</LOCATION>. Le gouvernement était trop faible, trop divisé pour lui donner des troupes. Henri V ayant terminé par des traités une guerre de peu de durée contre la Pologne, sut tellement intéresser les princes de l' empire à soûtenir ses droits, que ces mêmes princes qui avaient aidé à détroner son pére en vertu des bulles des papes, se réunirent avec lui pour faire annuller dans Rome ces mêmes bulles. Il descend donc des Alpes avec une armée ; et Rome fut encor teinte de sang pour cette querelle de la crosse et de l' anneau. Les traités, les parjures, les excommunications et les meurtres se suivirent avec rapidité. Pascal II ayant solemnellement rendu les investitures avec serment sur l' évangile, fit annuller son serment par es cardinaux ; nouvelle manière de manquer à sa parole. Il se laissa traiter de lâche et de prévaricateur en plein concile, afin d' être forcé à reprendre ce qu' il avait donné. Alors nouvelle irruption de l' empereur à Rome ; car presque jamais ces Césars n' y allèrent que pour des querelles ecclésiastiques, dont la plus grande était le couronnement. Enfin après avoir créé, déposé, chassé, rapellé des papes, Henri V aussi souvent excommunié que son pére, et inquiété comme lui par ses grands vassaux d' Allemagne, fut obligé de terminer la guerre des investitures, en renonçant à cette crosse et à cet anneau. Il fit plus ; il se désista solemnellement du droit que s' étaient attribué les empereurs, ainsi que les rois de France, de nommer aux évêchés, ou d' interposer tellement leur autorité dans les élections, qu' ils en étaient absolument les maîtres. Il fut donc décidé dans un concile tenu à Rome, que les rois ne donneraient plus aux bénéficiers canoniquement élus les investitures par un bâton recourbé, mais par une baguette."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Pascal II' and 'Troye' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Pascal II' near 'Troye' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 132 [ID: surprise_test_fr__277]:
  Publication date : 1756
  Language         : fr
  Person  : 'Sélim'  (QID: N/A)
  Location: 'Constantinople'  (QID: Q16869)

  [ARTICLE TEXT — entity markers added]
  "Mais enfin abandonné et livré au roi, condamné seulement à la prison, et ayant voulu s' évader, il paya sa hardiesse de sa tête. Ce fut alors que l' esprit de faction fut anéanti, et que les anglais, n' étant plus redoutables à leur monarque, commencèrent à le devenir à leurs voisins, surtout lorsque Henri VIII en montant au trône, fut, par l' économie extrême de son pére, possesseur d' un ample trésor, et par la sagesse de ce gouvernement, maître d' un peuple belliqueux, et pourtant soumis autant que les anglais peuvent l' être. CHAPITRE 97 Idée générale du seizième siècle. Le commencement du seiziéme siécle que nous avons déja entamé, nous présente à la fois les plus grands spectacles que le monde ait jamais fournis. Si on jette la vuë sur ceux qui régnaient pour lors en Europe, leur gloire, ou leur conduite, ou les grands changements dont ils ont été cause, rendent leurs noms immortels. C' est à <LOCATION>Constantinople</LOCATION> un <PERSON>Sélim</PERSON> qui met sous la domination ottomane la Syrie et l' égypte, dont les mahométans mammelucs avaient été en possession depuis le treiziéme siécle. C' est après lui son fils, le grand Soliman, qui le premier des empereurs turcs marche jusqu' à Vienne, et se fait couronner roi de Perse dans Bagdat prise par ses armes, faisant trembler à la fois l' Europe et l' Asie. On voit en même tems vers le nord, Gustave Vasa, brisant dans la Suéde le joug étranger, élu roi du pays, dont il est le libérateur. En Moscovie Jean Basilowitz soustrait sa patrie aux tartares dont elle était tributaire ; prince à la vérité barbare, et chef d' une nation plus barbare encore ; mais le vengeur de son pays mérite d' être compté parmi les grands princes."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Sélim' and 'Constantinople' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Sélim' near 'Constantinople' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 133 [ID: surprise_test_fr__212]:
  Publication date : 1756
  Language         : fr
  Person  : 'roi Philippe'  (QID: N/A)
  Location: 'Troye'  (QID: Q211953)

  [ARTICLE TEXT — entity markers added]
  "L' empereur soûtenait, non sans raison, que les états de Matilde lui devaient revenir comme un fief de l' empire ; ainsi les papes combattaient pour le spirituel et pour le temporel. Pascal II n' obtint du <PERSON>roi Philippe</PERSON> que la permission de tenir un concile à <LOCATION>Troye</LOCATION>. Le gouvernement était trop faible, trop divisé pour lui donner des troupes. Henri V ayant terminé par des traités une guerre de peu de durée contre la Pologne, sut tellement intéresser les princes de l' empire à soûtenir ses droits, que ces mêmes princes qui avaient aidé à détroner son pére en vertu des bulles des papes, se réunirent avec lui pour faire annuller dans Rome ces mêmes bulles. Il descend donc des Alpes avec une armée ; et Rome fut encor teinte de sang pour cette querelle de la crosse et de l' anneau. Les traités, les parjures, les excommunications et les meurtres se suivirent avec rapidité. Pascal II ayant solemnellement rendu les investitures avec serment sur l' évangile, fit annuller son serment par es cardinaux ; nouvelle manière de manquer à sa parole. Il se laissa traiter de lâche et de prévaricateur en plein concile, afin d' être forcé à reprendre ce qu' il avait donné. Alors nouvelle irruption de l' empereur à Rome ; car presque jamais ces Césars n' y allèrent que pour des querelles ecclésiastiques, dont la plus grande était le couronnement. Enfin après avoir créé, déposé, chassé, rapellé des papes, Henri V aussi souvent excommunié que son pére, et inquiété comme lui par ses grands vassaux d' Allemagne, fut obligé de terminer la guerre des investitures, en renonçant à cette crosse et à cet anneau. Il fit plus ; il se désista solemnellement du droit que s' étaient attribué les empereurs, ainsi que les rois de France, de nommer aux évêchés, ou d' interposer tellement leur autorité dans les élections, qu' ils en étaient absolument les maîtres. Il fut donc décidé dans un concile tenu à Rome, que les rois ne donneraient plus aux bénéficiers canoniquement élus les investitures par un bâton recourbé, mais par une baguette."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'roi Philippe' and 'Troye' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'roi Philippe' near 'Troye' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 134 [ID: surprise_test_fr__379]:
  Publication date : 1678
  Language         : fr
  Person  : 'Robert'  (QID: N/A)
  Location: 'France'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "Il est vray que ces renoncemens doivent avoir quelque cause legitime, et que les rois feroient tort à leurs successeurs, s' ils retranchoient une province du corps de l' etat sans y être contraints, ou sans y trouver de grands avantages. Mais lors qu' ils ne consentent à ces retranchemens que par necessité, ou pour le bien et l' utilité du royaume, leurs successeurs n' ont aucun sujet de se plaindre d' eux ; et s' ils en ont, la plupart de nos rois auroient eu droit de se plaindre de leurs predecesseurs, particulierement les enfans de Henry Ii qui par le traité de château Cambresy, relâcha et rendit près de deux cens villes ou forteresses. Il faut ajoutter à cela qu' il est difficile de marquer ce point de grandeur dont parle l' auteur qu' on a cité, où les etats étant parvenus, il n' est plus permis aux rois d' en retrancher aucune partie ; parce qu' il ne s' est jamais passé de temps considerable depuis l' établissement de la monarchie, que la <LOCATION>France</LOCATION> ne se soit accruë par les conquêtes de nos rois, ou n' ait diminué par celles de nos voisins. De plus, les rois de la premiere et seconde race luy ont très - souvent ôté sa grandeur, la partageant entre leurs enfans, et divisant le royaume en plusieurs royaumes. Enfin pour ne pas alleguer toutes les provinces qui ont été desunies de la couronne, il suffit de dire que la Bourgogne l' avoit été par le roy Henry, petit fils de Hugues Capet, en faveur de <PERSON>Robert</PERSON> son frere ; qu' elle y revint sous le roy Jean, qui la donna peu de temps après à Philippe Le Hardy son quatriéme fils ; et qu' après la mort de Charles dernier Duc de Bourgogne, Loüis XI s' en rendit le maître ; de sorte qu' il n' y avoit pas cinquante ans qu' elle étoit réünie à la couronne lorsque François I la voulut ceder. Passons maintenant aux autres pretextes qu' on prend pour se dispenser de la fidelité qu' on doit aux souverains."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: France
    Description: pays transcontinental au territoire métropolitain situé en Europe de l'Ouest
    Country: ['France']
    Aliases: {'en': ['French Republic'], 'fr': ['République française', 'RF', 'fr', 'la République française', 'Fr.', 'La France', "L'Hexagone"], 'de': ['Französische Republik', 'fr', 'RF']}
    Coordinates: [{'lat': 47, 'lon': 2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: maintenant, plus, après, avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Robert' and 'France' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Robert' near 'France' around 1678?
  4. Resolve temporal expressions relative to 1678. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 135 [ID: surprise_test_fr__450]:
  Publication date : 1666
  Language         : fr
  Person  : 'Monsieur De Montecuculi'  (QID: N/A)
  Location: 'Châlons'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Réponse du Comte De Bussy à Madame De S. à Chaseu, ce 1 septembre 1675. En me disant que vos lettres ne sont pas dignes de mon approbation, madame, vous m' en écrivez une qui en merite une plus grande, sans compter votre modestie. Mais pour ne la pas offenser davantage, je vais traiter d' autre chose avec vous. Ce qu' a dit monsieur le prince de Monsieur De Turenne en passant à <LOCATION>Châlons</LOCATION>, me paroît d' un fort honnête homme, et d' un homme qui sent bien son merite. <PERSON>Monsieur De Montecuculi</PERSON> se précautionnera encore davantage avec lui qu' il ne faisoit avec Monsieur De Turenne. Il est vrai que le Chevalier De G a été heureux au combat d' Altenhein ; et la trousse à celui de Consarbricq. Je m' en réjouis avec vous, et j' espere vous faire un même compliment pour monsieur vôtre fils à la fin de cette campagne. Vous devriez me conter le procès dont il est question. Je suis tellement affamé de vous entendre, que je vous donnerois une favorable audience quand vous ne me parleriez que d' interlocutoires et d' arrêts. Lettre 61. Réponse du Comte De Bussy à Madame De S. à Chaseu, ce 29 octobre 1675. Je reçus hier vôtre lettre, madame, qui me donna la joie que vos lettres ont accoutumé de me donner. Enfin voilà vôtre niéce sur le point de passer le pas ; elle va trouver ce qu' elle cherchoit. à propos de chercher, ceci me fait souvenir du pauvre Chevalier De Rohan, qui ayant rencontré un soir bien tard à Fontainebleau, Madame D' seule qui passoit dans une galerie, lui demanda ce qu' elle cherchoit : rien, dit -elle. Ma foi, madame, lui répondit -il, je ne voudrois pas avoir perdu ce que vous cherchez. Voilà mon petit conte, madame. Vous m' avez permis d' en faire un aussi, je me sers de la liberté que vous m' avez donnée. J' ai trouvé le vôtre plaisant au dernier point, et je m' en sçai bon gré, car il faut avoir de l' esprit pour trouver cela aussi plaisant qu' il est."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1675" → 1675
      - "1675" → 1675
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 9 days
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Monsieur De Montecuculi' and 'Châlons' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Monsieur De Montecuculi' near 'Châlons' around 1666?
  4. Resolve temporal expressions relative to 1666. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 136 [ID: surprise_test_fr__247]:
  Publication date : 1797
  Language         : fr
  Person  : 'M Poncel De La Haye'  (QID: N/A)
  Location: "île de l' Ascençaon"  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "D' après le rapport de M De Vaujuas et de M Boutin, il était évident que nous ne pouvions trouver à la Trinité l' eau et le bois qui nous manquaient. Je me décidai tout de suite à faire route pour l' île Sainte - Catherine, sur la côte du Brésil : c' était l' ancienne relâche des bâtimens français qui allaient dans la mer du sud. Frézier et l' amiral Anson y trouvèrent abondamment à se pourvoir de tous leurs besoins. Ce fut pour ne pas perdre un seul jour, que je donnai la préférence à l' île Sainte - Catherine sur Rio - Janéïro, où les différentes formalités auraient exigé plus de temps qu' il n' en fallait pour faire l' eau et le bois qui nous manquaient. Mais en dirigeant ma route vers l' île Sainte - Catherine, je voulus m' assurer de l' existence de l' <LOCATION>île de l' Ascençaon</LOCATION>, que M Daprès place à cent lieues dans l' ouest de la Trinité, et à 15 minutes seulement plus sud. Suivant le journal de <PERSON>M Poncel De La Haye</PERSON>, qui commandait la frégate la renommée, j' étais certain que différens navigateurs, entr' autres Frézier, homme très - éclairé, avaient cru aborder à l' Ascençaon, et qu' ils n' avaient été réellement qu' à la Trinité. Malgré l' autorité de M Poncel De La Haye, je crus que ce point de géographie demandait un nouvel éclaircissement. Les deux jours que nous passâmes vers la partie sud de l' île de la Trinité, nous mirent à portée de faire les relèvemens d' après lesquels M Bernizet traça le plan de la partie sud de l' île : il diffère très - peu de celui du docteur Halley, qui m' avait été remis par M De Fleurieu. La vue, peinte par M Duché De Vancy, est d' une vérité si frappante, qu' elle suffira seule pour que les navigateurs qui aborderont dans la partie du sud de la Trinité, ne puissent jamais se tromper."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien, ancienne, plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M Poncel De La Haye' and "île de l' Ascençaon" in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M Poncel De La Haye' near "île de l' Ascençaon" around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 137 [ID: surprise_test_fr__435]:
  Publication date : 1637
  Language         : fr
  Person  : "M. PIERRE D' ANTELMI"  (QID: N/A)
  Location: 'Boisgency'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Excepté le seul dernier volume qui est de quadrupedibus bisulcis, dont la guerre du roy de Suede a interrompu la continuation, et que le prix de tout ce qui est imprimé en Alemagne est de 14 escus, mais que les libraires de Paris n' en ont point d' exemplaires presentement. Sur quoy en attendant vos ordres je finiray, demeurant, monsieur, vostre, etc. à <LOCATION>Boisgency</LOCATION>, ce 13 Aoust 1631. à <PERSON>M. PIERRE D' ANTELMI</PERSON> 1631 Monsieur, c' est trop demeurer en silence et j' ay esté bien aise d' avoir occasion de le rompre pour vous dire, aprez les protestations de la continuation de mes voeux pour vostre service, qu' enfin il est passé un petit balot de quelques livres nouveaux, entre lesquels il y en a d' assez curieux et que je crois bien que vous ne serez pas marry de voir. J' ay envoyé mon libraire à Aix pour me les venir relier et pour avoir moyen de vous en faire participant. Entre autres nous avons eu quelques opuscules du pauvre feu Keplerus qui sont maintenant ès mains de Mr le prieur De La Valette à Aix, concernant les petits ecclypses de soleil qui doivent arriver à ces mois de novembre et decembre, non par l' interposition du corps de la lune, mais à celle des planettes de Venus et de Mercure qui seront aussi belles à observer qu' elles sont rares, n' arrivants qu' une fois en plusieurs centaines d' années, par où l'on pourra tirer d' excellentes consequences de la proportion de leur grandeur et de leur distance ou esloignement de la terre. Il y a aussi un jugement dudict Keplerus sur un livre d' un p. Jesuite de la Chine concernant l' astronomie de ce païs la, qu' on dit estre beaucoup plus exacte que la nostre, où il y a de belles choses à voir. Si vous pouviez faire une debauche jusques icy aprez ces chaleurs, nous tascherons de vous y donner quelque agreable divertissement."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1631" → 1631
      - "1631" → 1631
    Temporal signal words: maintenant, plus
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 6 days
    OCR quality estimate: 0.988

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between "M. PIERRE D' ANTELMI" and 'Boisgency' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing "M. PIERRE D' ANTELMI" near 'Boisgency' around 1637?
  4. Resolve temporal expressions relative to 1637. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 138 [ID: surprise_test_fr__371]:
  Publication date : 1678
  Language         : fr
  Person  : 'Philippe Le Hardy'  (QID: N/A)
  Location: 'Bourgogne'  (QID: Q1173)

  [ARTICLE TEXT — entity markers added]
  "Il est vray que ces renoncemens doivent avoir quelque cause legitime, et que les rois feroient tort à leurs successeurs, s' ils retranchoient une province du corps de l' etat sans y être contraints, ou sans y trouver de grands avantages. Mais lors qu' ils ne consentent à ces retranchemens que par necessité, ou pour le bien et l' utilité du royaume, leurs successeurs n' ont aucun sujet de se plaindre d' eux ; et s' ils en ont, la plupart de nos rois auroient eu droit de se plaindre de leurs predecesseurs, particulierement les enfans de Henry Ii qui par le traité de château Cambresy, relâcha et rendit près de deux cens villes ou forteresses. Il faut ajoutter à cela qu' il est difficile de marquer ce point de grandeur dont parle l' auteur qu' on a cité, où les etats étant parvenus, il n' est plus permis aux rois d' en retrancher aucune partie ; parce qu' il ne s' est jamais passé de temps considerable depuis l' établissement de la monarchie, que la France ne se soit accruë par les conquêtes de nos rois, ou n' ait diminué par celles de nos voisins. De plus, les rois de la premiere et seconde race luy ont très - souvent ôté sa grandeur, la partageant entre leurs enfans, et divisant le royaume en plusieurs royaumes. Enfin pour ne pas alleguer toutes les provinces qui ont été desunies de la couronne, il suffit de dire que la <LOCATION>Bourgogne</LOCATION> l' avoit été par le roy Henry, petit fils de Hugues Capet, en faveur de Robert son frere ; qu' elle y revint sous le roy Jean, qui la donna peu de temps après à <PERSON>Philippe Le Hardy</PERSON> son quatriéme fils ; et qu' après la mort de Charles dernier Duc de Bourgogne, Loüis XI s' en rendit le maître ; de sorte qu' il n' y avoit pas cinquante ans qu' elle étoit réünie à la couronne lorsque François I la voulut ceder. Passons maintenant aux autres pretextes qu' on prend pour se dispenser de la fidelité qu' on doit aux souverains."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: maintenant, plus, après, avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Philippe Le Hardy' and 'Bourgogne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Philippe Le Hardy' near 'Bourgogne' around 1678?
  4. Resolve temporal expressions relative to 1678. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 139 [ID: surprise_test_fr__410]:
  Publication date : 1561
  Language         : fr
  Person  : 'maistre Arnaud'  (QID: N/A)
  Location: 'chemin de Paris'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Misser Iuliano commanda à Torneto de la prendre, & de la mener chez luy en l' estable. Là ou elle se rengea aussi proprement, comme si elle n' en eust jamais bougé. Il la fit ramener le lendemain en la mesme place, pour veoir si quelqu' un la vendiqueroit. Mais il ne venoit personne, dont il fut fort esbahy : & pensoit que ce fust quelque esprit qui l' eust ramenee. De là à quelque temps <PERSON>maistre Arnaud</PERSON> s' addresse à misser Iuliano, lequel il trouva monté sus sa hacquenee, & luy dit : monsieur, je suis fort aise de savoir que ceste hacquenee soit à vous. Car asseurez vous qu' elle est bonne : je l' ay essayee, il y ha environ un an que je la trouvay pres du pont du Rosne, qu' elle s' en alloit toute seule, & qu' un garson la vouloit prendre. Mais congnoissant à sa façon qu' elle n' estoit pas sienne, je la luy ostay : & la garday un jour ou deux sans pouvoir savoir à qui elle estoit. Le troisiesme jour je la menay jusques à Villeneufve, ou j' ouy dire qu' un gentilhomme François la cherchoit, & qu' il luy avoit esté dit qu' on l' avoit veue emmener par un garson sus le <LOCATION>chemin de Paris</LOCATION>. Le gentilhomme alloit apres. Et moy sachant celà, je picque apres luy pour la luy rendre : mais je ne le peu jamais atteindre. Car il alloit grand train pour atteindre son larron. Et allay tant en le cherchant, que je me trouvay jusqu' en Lorraine. Là ou voyant que je n' oyois point de nouvelles de ce gentilhomme, je la garday long temps. Et à la fin m' en suis revenu en ceste ville, ou je l' avoys prise : & ay trouvé par quelques uns de mes amis, qu' il se souvenoit bien l' avoir veue autrefois en ceste ville : mais qu' il ne savoit à qui, sinon que ce fust à quelqu' un de vous autres messieurs de la legation. Sachant celà, je l' ay fait mener en la place du Palais, affin que celuy à qui elle estoit la peust appercevoir. Et ce pendant je m' en estois allé d' icy à Nimes, d' ou je suis retourné depuis deux jours. Mais Dieu soit loué qu' elle ha retrouvé son maistre. Car j' en estois en grand peine."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'maistre Arnaud' and 'chemin de Paris' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'maistre Arnaud' near 'chemin de Paris' around 1561?
  4. Resolve temporal expressions relative to 1561. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 140 [ID: surprise_test_fr__211]:
  Publication date : 1756
  Language         : fr
  Person  : 'Henri V'  (QID: N/A)
  Location: 'Troye'  (QID: Q211953)

  [ARTICLE TEXT — entity markers added]
  "L' empereur soûtenait, non sans raison, que les états de Matilde lui devaient revenir comme un fief de l' empire ; ainsi les papes combattaient pour le spirituel et pour le temporel. Pascal II n' obtint du roi Philippe que la permission de tenir un concile à <LOCATION>Troye</LOCATION>. Le gouvernement était trop faible, trop divisé pour lui donner des troupes. <PERSON>Henri V</PERSON> ayant terminé par des traités une guerre de peu de durée contre la Pologne, sut tellement intéresser les princes de l' empire à soûtenir ses droits, que ces mêmes princes qui avaient aidé à détroner son pére en vertu des bulles des papes, se réunirent avec lui pour faire annuller dans Rome ces mêmes bulles. Il descend donc des Alpes avec une armée ; et Rome fut encor teinte de sang pour cette querelle de la crosse et de l' anneau. Les traités, les parjures, les excommunications et les meurtres se suivirent avec rapidité. Pascal II ayant solemnellement rendu les investitures avec serment sur l' évangile, fit annuller son serment par es cardinaux ; nouvelle manière de manquer à sa parole. Il se laissa traiter de lâche et de prévaricateur en plein concile, afin d' être forcé à reprendre ce qu' il avait donné. Alors nouvelle irruption de l' empereur à Rome ; car presque jamais ces Césars n' y allèrent que pour des querelles ecclésiastiques, dont la plus grande était le couronnement. Enfin après avoir créé, déposé, chassé, rapellé des papes, Henri V aussi souvent excommunié que son pére, et inquiété comme lui par ses grands vassaux d' Allemagne, fut obligé de terminer la guerre des investitures, en renonçant à cette crosse et à cet anneau. Il fit plus ; il se désista solemnellement du droit que s' étaient attribué les empereurs, ainsi que les rois de France, de nommer aux évêchés, ou d' interposer tellement leur autorité dans les élections, qu' ils en étaient absolument les maîtres. Il fut donc décidé dans un concile tenu à Rome, que les rois ne donneraient plus aux bénéficiers canoniquement élus les investitures par un bâton recourbé, mais par une baguette."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Henri V' and 'Troye' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Henri V' near 'Troye' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 141 [ID: surprise_test_fr__370]:
  Publication date : 1678
  Language         : fr
  Person  : 'Henry Ii'  (QID: N/A)
  Location: 'Bourgogne'  (QID: Q1173)

  [ARTICLE TEXT — entity markers added]
  "Il est vray que ces renoncemens doivent avoir quelque cause legitime, et que les rois feroient tort à leurs successeurs, s' ils retranchoient une province du corps de l' etat sans y être contraints, ou sans y trouver de grands avantages. Mais lors qu' ils ne consentent à ces retranchemens que par necessité, ou pour le bien et l' utilité du royaume, leurs successeurs n' ont aucun sujet de se plaindre d' eux ; et s' ils en ont, la plupart de nos rois auroient eu droit de se plaindre de leurs predecesseurs, particulierement les enfans de <PERSON>Henry Ii</PERSON> qui par le traité de château Cambresy, relâcha et rendit près de deux cens villes ou forteresses. Il faut ajoutter à cela qu' il est difficile de marquer ce point de grandeur dont parle l' auteur qu' on a cité, où les etats étant parvenus, il n' est plus permis aux rois d' en retrancher aucune partie ; parce qu' il ne s' est jamais passé de temps considerable depuis l' établissement de la monarchie, que la France ne se soit accruë par les conquêtes de nos rois, ou n' ait diminué par celles de nos voisins. De plus, les rois de la premiere et seconde race luy ont très - souvent ôté sa grandeur, la partageant entre leurs enfans, et divisant le royaume en plusieurs royaumes. Enfin pour ne pas alleguer toutes les provinces qui ont été desunies de la couronne, il suffit de dire que la <LOCATION>Bourgogne</LOCATION> l' avoit été par le roy Henry, petit fils de Hugues Capet, en faveur de Robert son frere ; qu' elle y revint sous le roy Jean, qui la donna peu de temps après à Philippe Le Hardy son quatriéme fils ; et qu' après la mort de Charles dernier Duc de Bourgogne, Loüis XI s' en rendit le maître ; de sorte qu' il n' y avoit pas cinquante ans qu' elle étoit réünie à la couronne lorsque François I la voulut ceder. Passons maintenant aux autres pretextes qu' on prend pour se dispenser de la fidelité qu' on doit aux souverains."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: maintenant, plus, après, avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Henry Ii' and 'Bourgogne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Henry Ii' near 'Bourgogne' around 1678?
  4. Resolve temporal expressions relative to 1678. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 142 [ID: surprise_test_fr__403]:
  Publication date : 1561
  Language         : fr
  Person  : 'misser Iuliano'  (QID: N/A)
  Location: 'pont du Rosne'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Misser Iuliano commanda à Torneto de la prendre, & de la mener chez luy en l' estable. Là ou elle se rengea aussi proprement, comme si elle n' en eust jamais bougé. Il la fit ramener le lendemain en la mesme place, pour veoir si quelqu' un la vendiqueroit. Mais il ne venoit personne, dont il fut fort esbahy : & pensoit que ce fust quelque esprit qui l' eust ramenee. De là à quelque temps maistre Arnaud s' addresse à <PERSON>misser Iuliano</PERSON>, lequel il trouva monté sus sa hacquenee, & luy dit : monsieur, je suis fort aise de savoir que ceste hacquenee soit à vous. Car asseurez vous qu' elle est bonne : je l' ay essayee, il y ha environ un an que je la trouvay pres du <LOCATION>pont du Rosne</LOCATION>, qu' elle s' en alloit toute seule, & qu' un garson la vouloit prendre. Mais congnoissant à sa façon qu' elle n' estoit pas sienne, je la luy ostay : & la garday un jour ou deux sans pouvoir savoir à qui elle estoit. Le troisiesme jour je la menay jusques à Villeneufve, ou j' ouy dire qu' un gentilhomme François la cherchoit, & qu' il luy avoit esté dit qu' on l' avoit veue emmener par un garson sus le chemin de Paris. Le gentilhomme alloit apres. Et moy sachant celà, je picque apres luy pour la luy rendre : mais je ne le peu jamais atteindre. Car il alloit grand train pour atteindre son larron. Et allay tant en le cherchant, que je me trouvay jusqu' en Lorraine. Là ou voyant que je n' oyois point de nouvelles de ce gentilhomme, je la garday long temps. Et à la fin m' en suis revenu en ceste ville, ou je l' avoys prise : & ay trouvé par quelques uns de mes amis, qu' il se souvenoit bien l' avoir veue autrefois en ceste ville : mais qu' il ne savoit à qui, sinon que ce fust à quelqu' un de vous autres messieurs de la legation. Sachant celà, je l' ay fait mener en la place du Palais, affin que celuy à qui elle estoit la peust appercevoir. Et ce pendant je m' en estois allé d' icy à Nimes, d' ou je suis retourné depuis deux jours. Mais Dieu soit loué qu' elle ha retrouvé son maistre. Car j' en estois en grand peine."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'misser Iuliano' and 'pont du Rosne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'misser Iuliano' near 'pont du Rosne' around 1561?
  4. Resolve temporal expressions relative to 1561. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 143 [ID: surprise_test_fr__453]:
  Publication date : 1666
  Language         : fr
  Person  : 'monsieur le prince'  (QID: N/A)
  Location: 'Châlons'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Réponse du Comte De Bussy à Madame De S. à Chaseu, ce 1 septembre 1675. En me disant que vos lettres ne sont pas dignes de mon approbation, madame, vous m' en écrivez une qui en merite une plus grande, sans compter votre modestie. Mais pour ne la pas offenser davantage, je vais traiter d' autre chose avec vous. Ce qu' a dit <PERSON>monsieur le prince</PERSON> de Monsieur De Turenne en passant à <LOCATION>Châlons</LOCATION>, me paroît d' un fort honnête homme, et d' un homme qui sent bien son merite. Monsieur De Montecuculi se précautionnera encore davantage avec lui qu' il ne faisoit avec Monsieur De Turenne. Il est vrai que le Chevalier De G a été heureux au combat d' Altenhein ; et la trousse à celui de Consarbricq. Je m' en réjouis avec vous, et j' espere vous faire un même compliment pour monsieur vôtre fils à la fin de cette campagne. Vous devriez me conter le procès dont il est question. Je suis tellement affamé de vous entendre, que je vous donnerois une favorable audience quand vous ne me parleriez que d' interlocutoires et d' arrêts. Lettre 61. Réponse du Comte De Bussy à Madame De S. à Chaseu, ce 29 octobre 1675. Je reçus hier vôtre lettre, madame, qui me donna la joie que vos lettres ont accoutumé de me donner. Enfin voilà vôtre niéce sur le point de passer le pas ; elle va trouver ce qu' elle cherchoit. à propos de chercher, ceci me fait souvenir du pauvre Chevalier De Rohan, qui ayant rencontré un soir bien tard à Fontainebleau, Madame D' seule qui passoit dans une galerie, lui demanda ce qu' elle cherchoit : rien, dit -elle. Ma foi, madame, lui répondit -il, je ne voudrois pas avoir perdu ce que vous cherchez. Voilà mon petit conte, madame. Vous m' avez permis d' en faire un aussi, je me sers de la liberté que vous m' avez donnée. J' ai trouvé le vôtre plaisant au dernier point, et je m' en sçai bon gré, car il faut avoir de l' esprit pour trouver cela aussi plaisant qu' il est."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1675" → 1675
      - "1675" → 1675
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 9 days
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'monsieur le prince' and 'Châlons' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'monsieur le prince' near 'Châlons' around 1666?
  4. Resolve temporal expressions relative to 1666. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 144 [ID: surprise_test_fr__26]:
  Publication date : 1756
  Language         : fr
  Person  : 'Hussein'  (QID: N/A)
  Location: 'province de Candahar'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "C' est encor ici une de ces révolutions où le caractère des peuples qui la firent, eut plus de part que le caractère de leurs chefs : car Myri - Weis ayant été assassiné et remplacé par un autre barbare nommé Maghmud, son propre neveu, qui n' était âgé que de dix - huit ans, il n' y avait pas d' apparence que ce jeune homme pût faire beaucoup par lui -même, et qu' il conduisit ces troupes indisciplinées de montagnards féroces, comme nos généraux conduisent des armées réglées. Le gouvernement de <PERSON>Hussein</PERSON> était méprisé, et la <LOCATION>province de Candahar</LOCATION> ayant commencé les troubles, les provinces du Caucase du côté de la Georgie se révoltèrent aussi. Enfin Maghmud assiégea Ispahan en 1722. Scha - Hussein lui remit cette capitale, abdiqua le royaume à ses pieds, et le reconnut pour son maître, trop heureux que Maghmud daignât épouser sa fille. Tous les tableaux des cruautés et des malheurs des hommes que nous examinons depuis le tems de Charlemagne, n' ont rien de plus horrible que les suites de la révolution d' Ispahan. Maghmud crut ne pouvoir s' affermir qu' en faisant égorger les familles des principaux citoyens. La Perse entiére a été trente années ce qu' avait été l' Allemagne avant la paix de Westphalie, ce que fut la France du tems de Charles VI, l' Angleterre dans les guerres de la rose rouge et de la rose blanche. Mais la Perse est tombée d' un état plus florissant dans un plus grand abîme de malheurs. La religion eut encor part à ces désolations. Les aguans tenaient pour Omar, comme les persans pour Ali ; et ce Maghmud chef des aguans mêlait les plus lâches superstitions aux plus détestables cruautés. Il mourut en démence en 1725 après avoir désolé la Perse. Un nouvel usurpateur de la nation des aguans lui succéda ; il s' appellait Asraf. La désolation de la Perse redoublait de tous côtés. Les turcs l' inondaient du côté de la Georgie, l' ancienne Colchide."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1722" → 1722
      - "1725" → 1725
    Temporal signal words: ancien, ancienne, plus, après, avant
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 31 days
    OCR quality estimate: 0.994

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Hussein' and 'province de Candahar' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Hussein' near 'province de Candahar' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 145 [ID: surprise_test_fr__251]:
  Publication date : 1797
  Language         : fr
  Person  : 'Ascençaon'  (QID: N/A)
  Location: 'ouest de la Trinité'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "D' après le rapport de M De Vaujuas et de M Boutin, il était évident que nous ne pouvions trouver à la Trinité l' eau et le bois qui nous manquaient. Je me décidai tout de suite à faire route pour l' île Sainte - Catherine, sur la côte du Brésil : c' était l' ancienne relâche des bâtimens français qui allaient dans la mer du sud. Frézier et l' amiral Anson y trouvèrent abondamment à se pourvoir de tous leurs besoins. Ce fut pour ne pas perdre un seul jour, que je donnai la préférence à l' île Sainte - Catherine sur Rio - Janéïro, où les différentes formalités auraient exigé plus de temps qu' il n' en fallait pour faire l' eau et le bois qui nous manquaient. Mais en dirigeant ma route vers l' île Sainte - Catherine, je voulus m' assurer de l' existence de l' île de l' <PERSON>Ascençaon</PERSON>, que M Daprès place à cent lieues dans l' <LOCATION>ouest de la Trinité</LOCATION>, et à 15 minutes seulement plus sud. Suivant le journal de M Poncel De La Haye, qui commandait la frégate la renommée, j' étais certain que différens navigateurs, entr' autres Frézier, homme très - éclairé, avaient cru aborder à l' Ascençaon, et qu' ils n' avaient été réellement qu' à la Trinité. Malgré l' autorité de M Poncel De La Haye, je crus que ce point de géographie demandait un nouvel éclaircissement. Les deux jours que nous passâmes vers la partie sud de l' île de la Trinité, nous mirent à portée de faire les relèvemens d' après lesquels M Bernizet traça le plan de la partie sud de l' île : il diffère très - peu de celui du docteur Halley, qui m' avait été remis par M De Fleurieu. La vue, peinte par M Duché De Vancy, est d' une vérité si frappante, qu' elle suffira seule pour que les navigateurs qui aborderont dans la partie du sud de la Trinité, ne puissent jamais se tromper."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien, ancienne, plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Ascençaon' and 'ouest de la Trinité' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Ascençaon' near 'ouest de la Trinité' around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 146 [ID: surprise_test_fr__253]:
  Publication date : 1797
  Language         : fr
  Person  : 'M Boutin'  (QID: N/A)
  Location: 'ouest de la Trinité'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "D' après le rapport de M De Vaujuas et de <PERSON>M Boutin</PERSON>, il était évident que nous ne pouvions trouver à la Trinité l' eau et le bois qui nous manquaient. Je me décidai tout de suite à faire route pour l' île Sainte - Catherine, sur la côte du Brésil : c' était l' ancienne relâche des bâtimens français qui allaient dans la mer du sud. Frézier et l' amiral Anson y trouvèrent abondamment à se pourvoir de tous leurs besoins. Ce fut pour ne pas perdre un seul jour, que je donnai la préférence à l' île Sainte - Catherine sur Rio - Janéïro, où les différentes formalités auraient exigé plus de temps qu' il n' en fallait pour faire l' eau et le bois qui nous manquaient. Mais en dirigeant ma route vers l' île Sainte - Catherine, je voulus m' assurer de l' existence de l' île de l' Ascençaon, que M Daprès place à cent lieues dans l' <LOCATION>ouest de la Trinité</LOCATION>, et à 15 minutes seulement plus sud. Suivant le journal de M Poncel De La Haye, qui commandait la frégate la renommée, j' étais certain que différens navigateurs, entr' autres Frézier, homme très - éclairé, avaient cru aborder à l' Ascençaon, et qu' ils n' avaient été réellement qu' à la Trinité. Malgré l' autorité de M Poncel De La Haye, je crus que ce point de géographie demandait un nouvel éclaircissement. Les deux jours que nous passâmes vers la partie sud de l' île de la Trinité, nous mirent à portée de faire les relèvemens d' après lesquels M Bernizet traça le plan de la partie sud de l' île : il diffère très - peu de celui du docteur Halley, qui m' avait été remis par M De Fleurieu. La vue, peinte par M Duché De Vancy, est d' une vérité si frappante, qu' elle suffira seule pour que les navigateurs qui aborderont dans la partie du sud de la Trinité, ne puissent jamais se tromper."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien, ancienne, plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M Boutin' and 'ouest de la Trinité' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M Boutin' near 'ouest de la Trinité' around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 147 [ID: surprise_test_fr__448]:
  Publication date : 1666
  Language         : fr
  Person  : 'S.'  (QID: N/A)
  Location: 'Chaseu'  (QID: Q2968914)

  [ARTICLE TEXT — entity markers added]
  "Réponse du Comte De Bussy à Madame De <PERSON>S.</PERSON> à <LOCATION>Chaseu</LOCATION>, ce 1 septembre 1675. En me disant que vos lettres ne sont pas dignes de mon approbation, madame, vous m' en écrivez une qui en merite une plus grande, sans compter votre modestie. Mais pour ne la pas offenser davantage, je vais traiter d' autre chose avec vous. Ce qu' a dit monsieur le prince de Monsieur De Turenne en passant à Châlons, me paroît d' un fort honnête homme, et d' un homme qui sent bien son merite. Monsieur De Montecuculi se précautionnera encore davantage avec lui qu' il ne faisoit avec Monsieur De Turenne. Il est vrai que le Chevalier De G a été heureux au combat d' Altenhein ; et la trousse à celui de Consarbricq. Je m' en réjouis avec vous, et j' espere vous faire un même compliment pour monsieur vôtre fils à la fin de cette campagne. Vous devriez me conter le procès dont il est question. Je suis tellement affamé de vous entendre, que je vous donnerois une favorable audience quand vous ne me parleriez que d' interlocutoires et d' arrêts. Lettre 61. Réponse du Comte De Bussy à Madame De S. à Chaseu, ce 29 octobre 1675. Je reçus hier vôtre lettre, madame, qui me donna la joie que vos lettres ont accoutumé de me donner. Enfin voilà vôtre niéce sur le point de passer le pas ; elle va trouver ce qu' elle cherchoit. à propos de chercher, ceci me fait souvenir du pauvre Chevalier De Rohan, qui ayant rencontré un soir bien tard à Fontainebleau, Madame D' seule qui passoit dans une galerie, lui demanda ce qu' elle cherchoit : rien, dit -elle. Ma foi, madame, lui répondit -il, je ne voudrois pas avoir perdu ce que vous cherchez. Voilà mon petit conte, madame. Vous m' avez permis d' en faire un aussi, je me sers de la liberté que vous m' avez donnée. J' ai trouvé le vôtre plaisant au dernier point, et je m' en sçai bon gré, car il faut avoir de l' esprit pour trouver cela aussi plaisant qu' il est."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1675" → 1675
      - "1675" → 1675
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 9 days
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'S.' and 'Chaseu' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'S.' near 'Chaseu' around 1666?
  4. Resolve temporal expressions relative to 1666. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 148 [ID: surprise_test_fr__64]:
  Publication date : 1756
  Language         : fr
  Person  : 'Mahomet'  (QID: Q9458)
  Location: 'ville de Médine'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Les succès de ce peuple conquérant semblent dûs plutôt à l' entousiasme qui les anime, et à l' esprit de la nation, qu' à ses conducteurs : car Omar est assassiné par un esclave perse en 653. Otman son successeur l' est en 655 dans une émeute. Ali ce fameux gendre de <PERSON>Mahomet</PERSON> n' est élu, et ne gouverne qu' au milieu des troubles. Il meurt assassiné au bout de cinq ans comme ses prédécesseurs, et cependant les armes musulmanes sont toujours heureuses. Cet Ali que les persans révèrent aujourd'hui, et dont ils suivent les principes en oposition à ceux d' Omar, obtint enfin le califat, et transféra le siége des califes de la <LOCATION>ville de Médine</LOCATION>, où Mahomet est enseveli, dans la ville de Couffa, sur les bords de l' Euphrate : à peine en reste - t -il aujourd'hui des ruines. C' est le sort de Babylone, de Séleucie, et de toutes les anciennes villes de la Caldée, qui n' étaient bâties que de briques. Il est évident que le génie du peuple arabe mis en mouvement par Mahomet fit tout de lui -même pendant près de trois siécles, et ressembla en cela au génie des anciens romains. C' est en effet sous Valid le moins guerrier des califes, que se font les plus grandes conquêtes. Un de ses généraux étend son empire jusqu' à Samarkande en 707. Un autre attaque en même tems l' empire des grecs vers la mer Noire. Un autre en 711 passe d' égypte en Espagne soumise aisément tour à tour par les carthaginois, par les romains, par les goths et vandales, et enfin par ces arabes qu' on nomme maures. Ils y établirent d' abord le royaume de Cordoüe. Le sultan d' égypte secoue à la vérité le joug du grand calife de Bagdat, et Abdérame gouverneur de l' Espagne conquise ne reconnait plus le sultan d' égypte : cependant tout plie encor sous les armes musulmanes. Cet Abdérame, petit - fils du calife Hésham, prend les royaumes de Castille, de Navarre, de Portugal, d' Arragon."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Mahomet
    Description: chef politique arabe et fondateur de l’islam
    Born: ['+0571-04-20T00:00:00Z', '+0570-00-00T00:00:00Z']
    Died: ['+0632-06-08T00:00:00Z', '+0634-00-00T00:00:00Z']
    Birth place: ['La Mecque']
    Death place: ['Médine']
    Residences: ['Q5806', 'Q35484']
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: aujourd'hui, ancien, ancienne, plus, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.988

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mahomet' and 'ville de Médine' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mahomet' near 'ville de Médine' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 149 [ID: surprise_test_fr__97]:
  Publication date : 1756
  Language         : fr
  Person  : 'Raoul'  (QID: N/A)
  Location: 'Normandie'  (QID: Q15878)

  [ARTICLE TEXT — entity markers added]
  "Enfin Rolon ou <PERSON>Raoul</PERSON>, le plus illustre de ces brigands du nord, après avoir été chassé du Dannemarck, ayant rassemblé en Scandinavie tous ceux qui voulurent s' attacher à sa fortune, tenta de nouvelles avantures, et fonda l' espérance de sa grandeur sur la faiblesse de l' Europe. Il aborda l' Angleterre, où ses compatriotes étaient déja établis ; mais après deux victoires inutiles, il tourna du côté de la France, que d' autres normands savaient ruiner, mais qu' ils ne savaient pas asservir. Rolon fut le seul de ces barbares qui cessa d' en mériter le nom, en cherchant un établissement fixe. Maître de Rouen sans peine, au lieu de la détruire, il en fit relever les murailles et les tours. Rouen devint sa place d' armes ; de là il volait tantôt en Angleterre, tantôt en France, faisant la guerre avec politique, comme avec fureur. La France était expirante sous le régne de Charles Le Simple, roi de nom, et dont la monarchie était encor plus démembrée par les ducs, par les comtes et par les barons ses sujets, que par les normands. Charles Le Gros n' avait donné que de l' or aux barbares : Charles Le Simple offrit à Rolon sa fille et des provinces. Raoul demanda d' abord la <LOCATION>Normandie</LOCATION> : et on fut trop heureux de la lui céder. Il demanda ensuite la Bretagne ; on disputa ; mais il fallut la céder encor avec des clauses que le plus fort explique toûjours à son avantage. Ainsi la Bretagne, qui était tout - à - l' heure un royaume, devint un fief de la Neustrie ; et la Neustrie, qu' on s' accoutuma bientôt à nommer Normandie du nom de ses usurpateurs, fut un état séparé, dont les ducs rendaient un vain hommage à la couronne de France. L' archevêque de Rouen sut persuader à Rolon de se faire chrêtien. Ce prince embrassa volontiers une religion qui affermissait sa puissance. Les véritables conquérans sont ceux qui savent faire des loix. Leur puissance est stable ; les autres sont des torrens qui passent. Rolon paisible fut le seul législateur de son tems dans le continent chrêtien."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après, avant, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Raoul' and 'Normandie' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Raoul' near 'Normandie' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 150 [ID: surprise_test_fr__123]:
  Publication date : 1637
  Language         : fr
  Person  : 'Tertullien'  (QID: Q174929)
  Location: 'Marseille'  (QID: Q23482)

  [ARTICLE TEXT — entity markers added]
  "Que je n' ay pas, mais de la derniere de Paris dans l' un des derniers volumes de la bibliotheque des peres, où il est inseré avec tous les autres grecs et latins du mesme subject des liturgies. Quant aulx inscriptions du Grutterus, il y a veritablement un recueil d' inscriptions crestiennes parmy lesquelles possible y trouveriez vous quelque chose de vostre faict, mais il fauldroit que vous en fissiez le choix vous mesmes, car tel mot vous fournira de la matiere de discourir qui me pourroit eschapper à moy. Je le vous envoyeray trez volontiers, si vous me l' ordonnez, mais parceque, si je ne me trompe, Monsieur Vias en a un exemplaire qu' il vous baillera volontiers, j' ay creu que possible seriez vous bien ayse de le prendre là, attendu que vous aurez bientost parcouru ce peu de feuilletz qui y sont sur la fin des inscriptions crestiennes. Vous m' avez bien obligé de me faire part de la lettre de Mr Rigault, lequel je congnois de fort longue main, comme aussy Mr De Saulmaise. Je vouldroys bien que les notes de l' un et de l' aultre sur Pline et <PERSON>Tertullien</PERSON> fussent imprimées et serois bien marry que les anglois nous ostassent Mr Saulmaise qui est un grand thresor et seroit beaucoup plus considerable s' il eust peu esviter le coup de son mariage qui luy occasionne tant de troubles et de divertissement en ses estudes et observations singulieres, dont le public se seroit tant prevalu. Mais je me suis infiniment resjouy d' entendre que vous ayez tant advancé vostre traicté des religieux dont je ne puis assez louer l' entreprise et les belles singularitez que vous y aurez remarquées. Nous attendrons avec grande impatience tout ce qu' il vous plaira nous en communiquer et que vous deignez nous honorer de voz commandementz comme celuy qui est et sera à jamais, monsieur, vostre, etc. D' Aix, ce X Febvrier 1627. à monsieur, monsieur l' evesque d' Orleans, conseiller du roy en ses conseils d' estat, à <LOCATION>Marseille</LOCATION>."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Marseille
    Description: ville et commune française (chef-lieu du département des Bouches-du-Rhône et de la région Provence-Alpes-Côte d'Azur) et 2e plus grande ville de France
    Country: ['France']
    Located in: ['Bouches-du-Rhône', 'arrondissement de Marseille', 'Q131466267', 'Q16665884']
    Aliases: {'en': ['Massaliotes', 'Massalia', 'Marsailles', 'Marseilles', 'Marsielles', 'Marsielle', 'City of Marseille', 'Marsaille', 'Marsiglia', 'Marseille, France', 'Marseille City'], 'fr': ['Cité phocéenne', 'Ville-sans-Nom', 'Sans-Nom', 'Massalia', 'Massilia'], 'de': ['Massilia', 'Massaliotisch', 'Marseillais', 'Massillia']}
    Coordinates: [{'lat': 43.296666666667, 'lon': 5.3763888888889}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1627" → 1627
    Temporal signal words: plus
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 10 days
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Tertullien' and 'Marseille' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Tertullien' near 'Marseille' around 1637?
  4. Resolve temporal expressions relative to 1637. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 151 [ID: surprise_test_fr__181]:
  Publication date : 1542
  Language         : fr
  Person  : 'Gargantua'  (QID: Q60836436)
  Location: 'Orleans'  (QID: Q6548)

  [ARTICLE TEXT — entity markers added]
  "Car elle estoit grande comme six Oriflans, & avoit les pieds fenduz en doigtz, comme le cheval de Jules Cesar, les aureilles ainsi pendentes, comme les chievres de Languegoth, & une petite corne au cul, Au reste avoit poil d' alezan toustade entreillize de grizes pommelettes. Mais sus tout avoit la queue horrible. Car elle estoit poy plus poy moins grosse comme la pile sainct Mars aupres de Langes : & ainsi quarree, avecques les brancars ny plus ny moins ennicrochez, que sont les espicz au bled. Si de ce vous esmerveillez : esmerveillez vous dadvantaige de la queue des beliers de Scythie : que pesoit plus de trente livres, & des moutons de Surie, esquelz fault ( si Tenaud dict vray ) affuster une charrette au cul, pour la porter tant elle est longue & pesante. Vous ne l' avez pas telle vous aultres paillardes de plat pays. Et fut amenee par mer en troys carracques & un brigantin jusques au port de Olone en Thalmondoys Lors que Grandgousier la veit, Voicy ( dist il ) bien le cas pour porter mon filz a Paris. Or ca de par dieu, tout yra bien. Il sera grand clerc on temps advenir. Si n' estoient messieurs les bestes, nous vivrions comme clercs. Au lendemain apres boyre ( comme entendez ) prindrent chemin, <PERSON>Gargantua</PERSON> son precepteur Ponocrates & ses gens, ensemble eulx Eudemon le jeune paige. Et par ce que c' estoit en temps serain & bien attrempé, son pere luy feist faire des botes fauves. Babin les nomme brodequins. Ainsi joyeusement passerent leur grand chemin : & tousjours grand chere : jusques au dessus de <LOCATION>Orleans</LOCATION>. Au quel lieu estoit une ample forest de la longueur de trente & cinq lieues & de largeur dix & sept ou environ. Icelle estoit horriblement fertile & copieuse en mousches bovines & freslons, de sorte que c' estoit une vraye briguanderye pour les pauvres jumens, asnes, & chevaulx. Mais la jument de Gargantua vengea honnestement tous les oultrages en icelle perpetrees sur les bestes de son espece, par un tour, duquel ne se doubtoient mie."

  [ENTITY CONTEXT]
  Person Wikidata:
    No relevant Wikidata properties found.
  Location Wikidata:
    Label: Orléans
    Description: ville et commune française (chef-lieu du département du Loiret et de la région Centre-Val de Loire)
    Country: ['France']
    Located in: ['Loiret', 'Q702025']
    Aliases: {'en': ['Orleans', 'Cenabum', 'Genabum', 'Orelianum', 'civitas Aurelianorum', 'Orliens', 'civitas Aurelianensis'], 'fr': ['Cenabum', 'Genabum', 'Orelianum', 'civitas Aurelianorum', 'Orliens', 'civitas Aurelianensis'], 'de': ['Orleans', 'Cenabum', 'Genabum', 'Orelianum', 'civitas Aurelianorum', 'Orliens', 'civitas Aurelianensis']}
    Coordinates: [{'lat': 47.902222222222, 'lon': 1.9041666666667}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Gargantua' and 'Orleans' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Gargantua' near 'Orleans' around 1542?
  4. Resolve temporal expressions relative to 1542. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 152 [ID: surprise_test_fr__242]:
  Publication date : 1797
  Language         : fr
  Person  : "l' amiral Anson"  (QID: N/A)
  Location: 'île Sainte - Catherine'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "D' après le rapport de M De Vaujuas et de M Boutin, il était évident que nous ne pouvions trouver à la Trinité l' eau et le bois qui nous manquaient. Je me décidai tout de suite à faire route pour l' <LOCATION>île Sainte - Catherine</LOCATION>, sur la côte du Brésil : c' était l' ancienne relâche des bâtimens français qui allaient dans la mer du sud. Frézier et <PERSON>l' amiral Anson</PERSON> y trouvèrent abondamment à se pourvoir de tous leurs besoins. Ce fut pour ne pas perdre un seul jour, que je donnai la préférence à l' île Sainte - Catherine sur Rio - Janéïro, où les différentes formalités auraient exigé plus de temps qu' il n' en fallait pour faire l' eau et le bois qui nous manquaient. Mais en dirigeant ma route vers l' île Sainte - Catherine, je voulus m' assurer de l' existence de l' île de l' Ascençaon, que M Daprès place à cent lieues dans l' ouest de la Trinité, et à 15 minutes seulement plus sud. Suivant le journal de M Poncel De La Haye, qui commandait la frégate la renommée, j' étais certain que différens navigateurs, entr' autres Frézier, homme très - éclairé, avaient cru aborder à l' Ascençaon, et qu' ils n' avaient été réellement qu' à la Trinité. Malgré l' autorité de M Poncel De La Haye, je crus que ce point de géographie demandait un nouvel éclaircissement. Les deux jours que nous passâmes vers la partie sud de l' île de la Trinité, nous mirent à portée de faire les relèvemens d' après lesquels M Bernizet traça le plan de la partie sud de l' île : il diffère très - peu de celui du docteur Halley, qui m' avait été remis par M De Fleurieu. La vue, peinte par M Duché De Vancy, est d' une vérité si frappante, qu' elle suffira seule pour que les navigateurs qui aborderont dans la partie du sud de la Trinité, ne puissent jamais se tromper."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien, ancienne, plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between "l' amiral Anson" and 'île Sainte - Catherine' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing "l' amiral Anson" near 'île Sainte - Catherine' around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 153 [ID: surprise_test_fr__246]:
  Publication date : 1797
  Language         : fr
  Person  : 'Frézier'  (QID: N/A)
  Location: 'côte du Brésil'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "D' après le rapport de M De Vaujuas et de M Boutin, il était évident que nous ne pouvions trouver à la Trinité l' eau et le bois qui nous manquaient. Je me décidai tout de suite à faire route pour l' île Sainte - Catherine, sur la <LOCATION>côte du Brésil</LOCATION> : c' était l' ancienne relâche des bâtimens français qui allaient dans la mer du sud. <PERSON>Frézier</PERSON> et l' amiral Anson y trouvèrent abondamment à se pourvoir de tous leurs besoins. Ce fut pour ne pas perdre un seul jour, que je donnai la préférence à l' île Sainte - Catherine sur Rio - Janéïro, où les différentes formalités auraient exigé plus de temps qu' il n' en fallait pour faire l' eau et le bois qui nous manquaient. Mais en dirigeant ma route vers l' île Sainte - Catherine, je voulus m' assurer de l' existence de l' île de l' Ascençaon, que M Daprès place à cent lieues dans l' ouest de la Trinité, et à 15 minutes seulement plus sud. Suivant le journal de M Poncel De La Haye, qui commandait la frégate la renommée, j' étais certain que différens navigateurs, entr' autres Frézier, homme très - éclairé, avaient cru aborder à l' Ascençaon, et qu' ils n' avaient été réellement qu' à la Trinité. Malgré l' autorité de M Poncel De La Haye, je crus que ce point de géographie demandait un nouvel éclaircissement. Les deux jours que nous passâmes vers la partie sud de l' île de la Trinité, nous mirent à portée de faire les relèvemens d' après lesquels M Bernizet traça le plan de la partie sud de l' île : il diffère très - peu de celui du docteur Halley, qui m' avait été remis par M De Fleurieu. La vue, peinte par M Duché De Vancy, est d' une vérité si frappante, qu' elle suffira seule pour que les navigateurs qui aborderont dans la partie du sud de la Trinité, ne puissent jamais se tromper."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien, ancienne, plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Frézier' and 'côte du Brésil' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Frézier' near 'côte du Brésil' around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 154 [ID: surprise_test_fr__250]:
  Publication date : 1797
  Language         : fr
  Person  : 'M Bernizet'  (QID: N/A)
  Location: "sud de l' île de la Trinité"  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "D' après le rapport de M De Vaujuas et de M Boutin, il était évident que nous ne pouvions trouver à la Trinité l' eau et le bois qui nous manquaient. Je me décidai tout de suite à faire route pour l' île Sainte - Catherine, sur la côte du Brésil : c' était l' ancienne relâche des bâtimens français qui allaient dans la mer du sud. Frézier et l' amiral Anson y trouvèrent abondamment à se pourvoir de tous leurs besoins. Ce fut pour ne pas perdre un seul jour, que je donnai la préférence à l' île Sainte - Catherine sur Rio - Janéïro, où les différentes formalités auraient exigé plus de temps qu' il n' en fallait pour faire l' eau et le bois qui nous manquaient. Mais en dirigeant ma route vers l' île Sainte - Catherine, je voulus m' assurer de l' existence de l' île de l' Ascençaon, que M Daprès place à cent lieues dans l' ouest de la Trinité, et à 15 minutes seulement plus sud. Suivant le journal de M Poncel De La Haye, qui commandait la frégate la renommée, j' étais certain que différens navigateurs, entr' autres Frézier, homme très - éclairé, avaient cru aborder à l' Ascençaon, et qu' ils n' avaient été réellement qu' à la Trinité. Malgré l' autorité de M Poncel De La Haye, je crus que ce point de géographie demandait un nouvel éclaircissement. Les deux jours que nous passâmes vers la partie <LOCATION>sud de l' île de la Trinité</LOCATION>, nous mirent à portée de faire les relèvemens d' après lesquels <PERSON>M Bernizet</PERSON> traça le plan de la partie sud de l' île : il diffère très - peu de celui du docteur Halley, qui m' avait été remis par M De Fleurieu. La vue, peinte par M Duché De Vancy, est d' une vérité si frappante, qu' elle suffira seule pour que les navigateurs qui aborderont dans la partie du sud de la Trinité, ne puissent jamais se tromper."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien, ancienne, plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M Bernizet' and "sud de l' île de la Trinité" in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M Bernizet' near "sud de l' île de la Trinité" around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 155 [ID: surprise_test_fr__369]:
  Publication date : 1678
  Language         : fr
  Person  : 'Robert'  (QID: N/A)
  Location: 'Bourgogne'  (QID: Q1173)

  [ARTICLE TEXT — entity markers added]
  "Il est vray que ces renoncemens doivent avoir quelque cause legitime, et que les rois feroient tort à leurs successeurs, s' ils retranchoient une province du corps de l' etat sans y être contraints, ou sans y trouver de grands avantages. Mais lors qu' ils ne consentent à ces retranchemens que par necessité, ou pour le bien et l' utilité du royaume, leurs successeurs n' ont aucun sujet de se plaindre d' eux ; et s' ils en ont, la plupart de nos rois auroient eu droit de se plaindre de leurs predecesseurs, particulierement les enfans de Henry Ii qui par le traité de château Cambresy, relâcha et rendit près de deux cens villes ou forteresses. Il faut ajoutter à cela qu' il est difficile de marquer ce point de grandeur dont parle l' auteur qu' on a cité, où les etats étant parvenus, il n' est plus permis aux rois d' en retrancher aucune partie ; parce qu' il ne s' est jamais passé de temps considerable depuis l' établissement de la monarchie, que la France ne se soit accruë par les conquêtes de nos rois, ou n' ait diminué par celles de nos voisins. De plus, les rois de la premiere et seconde race luy ont très - souvent ôté sa grandeur, la partageant entre leurs enfans, et divisant le royaume en plusieurs royaumes. Enfin pour ne pas alleguer toutes les provinces qui ont été desunies de la couronne, il suffit de dire que la <LOCATION>Bourgogne</LOCATION> l' avoit été par le roy Henry, petit fils de Hugues Capet, en faveur de <PERSON>Robert</PERSON> son frere ; qu' elle y revint sous le roy Jean, qui la donna peu de temps après à Philippe Le Hardy son quatriéme fils ; et qu' après la mort de Charles dernier Duc de Bourgogne, Loüis XI s' en rendit le maître ; de sorte qu' il n' y avoit pas cinquante ans qu' elle étoit réünie à la couronne lorsque François I la voulut ceder. Passons maintenant aux autres pretextes qu' on prend pour se dispenser de la fidelité qu' on doit aux souverains."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Bourgogne
    Description: ancienne région administrative française
    Country: ['Q142']
    Located in: ['Bourgogne-Franche-Comté', 'France métropolitaine']
    Aliases: {'en': ['Bourgogne']}
    Coordinates: [{'lat': 47, 'lon': 4.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: maintenant, plus, après, avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Robert' and 'Bourgogne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Robert' near 'Bourgogne' around 1678?
  4. Resolve temporal expressions relative to 1678. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 156 [ID: surprise_test_fr__376]:
  Publication date : 1678
  Language         : fr
  Person  : 'François I'  (QID: Q129857)
  Location: 'Bourgogne'  (QID: Q1173)

  [ARTICLE TEXT — entity markers added]
  "Il est vray que ces renoncemens doivent avoir quelque cause legitime, et que les rois feroient tort à leurs successeurs, s' ils retranchoient une province du corps de l' etat sans y être contraints, ou sans y trouver de grands avantages. Mais lors qu' ils ne consentent à ces retranchemens que par necessité, ou pour le bien et l' utilité du royaume, leurs successeurs n' ont aucun sujet de se plaindre d' eux ; et s' ils en ont, la plupart de nos rois auroient eu droit de se plaindre de leurs predecesseurs, particulierement les enfans de Henry Ii qui par le traité de château Cambresy, relâcha et rendit près de deux cens villes ou forteresses. Il faut ajoutter à cela qu' il est difficile de marquer ce point de grandeur dont parle l' auteur qu' on a cité, où les etats étant parvenus, il n' est plus permis aux rois d' en retrancher aucune partie ; parce qu' il ne s' est jamais passé de temps considerable depuis l' établissement de la monarchie, que la France ne se soit accruë par les conquêtes de nos rois, ou n' ait diminué par celles de nos voisins. De plus, les rois de la premiere et seconde race luy ont très - souvent ôté sa grandeur, la partageant entre leurs enfans, et divisant le royaume en plusieurs royaumes. Enfin pour ne pas alleguer toutes les provinces qui ont été desunies de la couronne, il suffit de dire que la <LOCATION>Bourgogne</LOCATION> l' avoit été par le roy Henry, petit fils de Hugues Capet, en faveur de Robert son frere ; qu' elle y revint sous le roy Jean, qui la donna peu de temps après à Philippe Le Hardy son quatriéme fils ; et qu' après la mort de Charles dernier Duc de Bourgogne, Loüis XI s' en rendit le maître ; de sorte qu' il n' y avoit pas cinquante ans qu' elle étoit réünie à la couronne lorsque <PERSON>François I</PERSON> la voulut ceder. Passons maintenant aux autres pretextes qu' on prend pour se dispenser de la fidelité qu' on doit aux souverains."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: François Ier de France
    Description: roi de France de 1515 à 1547
    Born: ['+1494-09-12T00:00:00Z']
    Died: ['+1547-03-31T00:00:00Z', '+1547-07-31T00:00:00Z']
    Birth place: ['Cognac']
    Death place: ['Rambouillet']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: maintenant, plus, après, avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'François I' and 'Bourgogne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'François I' near 'Bourgogne' around 1678?
  4. Resolve temporal expressions relative to 1678. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 157 [ID: surprise_test_fr__380]:
  Publication date : 1678
  Language         : fr
  Person  : 'roy Jean'  (QID: N/A)
  Location: 'France'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "Il est vray que ces renoncemens doivent avoir quelque cause legitime, et que les rois feroient tort à leurs successeurs, s' ils retranchoient une province du corps de l' etat sans y être contraints, ou sans y trouver de grands avantages. Mais lors qu' ils ne consentent à ces retranchemens que par necessité, ou pour le bien et l' utilité du royaume, leurs successeurs n' ont aucun sujet de se plaindre d' eux ; et s' ils en ont, la plupart de nos rois auroient eu droit de se plaindre de leurs predecesseurs, particulierement les enfans de Henry Ii qui par le traité de château Cambresy, relâcha et rendit près de deux cens villes ou forteresses. Il faut ajoutter à cela qu' il est difficile de marquer ce point de grandeur dont parle l' auteur qu' on a cité, où les etats étant parvenus, il n' est plus permis aux rois d' en retrancher aucune partie ; parce qu' il ne s' est jamais passé de temps considerable depuis l' établissement de la monarchie, que la <LOCATION>France</LOCATION> ne se soit accruë par les conquêtes de nos rois, ou n' ait diminué par celles de nos voisins. De plus, les rois de la premiere et seconde race luy ont très - souvent ôté sa grandeur, la partageant entre leurs enfans, et divisant le royaume en plusieurs royaumes. Enfin pour ne pas alleguer toutes les provinces qui ont été desunies de la couronne, il suffit de dire que la Bourgogne l' avoit été par le roy Henry, petit fils de Hugues Capet, en faveur de Robert son frere ; qu' elle y revint sous le <PERSON>roy Jean</PERSON>, qui la donna peu de temps après à Philippe Le Hardy son quatriéme fils ; et qu' après la mort de Charles dernier Duc de Bourgogne, Loüis XI s' en rendit le maître ; de sorte qu' il n' y avoit pas cinquante ans qu' elle étoit réünie à la couronne lorsque François I la voulut ceder. Passons maintenant aux autres pretextes qu' on prend pour se dispenser de la fidelité qu' on doit aux souverains."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: France
    Description: pays transcontinental au territoire métropolitain situé en Europe de l'Ouest
    Country: ['France']
    Aliases: {'en': ['French Republic'], 'fr': ['République française', 'RF', 'fr', 'la République française', 'Fr.', 'La France', "L'Hexagone"], 'de': ['Französische Republik', 'fr', 'RF']}
    Coordinates: [{'lat': 47, 'lon': 2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: maintenant, plus, après, avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'roy Jean' and 'France' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'roy Jean' near 'France' around 1678?
  4. Resolve temporal expressions relative to 1678. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 158 [ID: surprise_test_fr__391]:
  Publication date : 1756
  Language         : fr
  Person  : 'Philippe I'  (QID: N/A)
  Location: 'Clermont'  (QID: Q2975160)

  [ARTICLE TEXT — entity markers added]
  "Ce qu' il y a de plus singulier, c' est qu' Urbain II qui prononça cette sentence, la prononça dans les propres états du roi, à <LOCATION>Clermont</LOCATION> en Auvergne, où il venait chercher un azile, et dans ce même concile où nous verrons qu' il prêcha la croisade. Cependant il ne paraît point que Philippe excommunié ait été en horreur à ses sujets ; c' est une raison de plus pour douter de cet abandon général où l'on dit que le roi Robert avait été réduit. Ce qu' il y eut d' assez remarquable, c' est le mariage du roi Henri pére de Philippe avec une princesse moscovite. Les moscovites ou russes commençaient à être chrêtiens ; mais ils n' avaient aucun commerce avec le reste de l' Europe. Ils habitaient au - delà de la Pologne, à peine chrêtienne elle -même, et sans aucune correspondance avec la France. Cependant le roi Henri envoya jusqu' en Russie demander la fille du souverain, à qui les autres européans donnaient le titre de duc, aussi - bien qu' au chef de la Pologne. Les russes le nommaient dans leur langage tzaar, dont on a fait depuis le mot de czar. On prétend que Henri se détermina à ce mariage, dans la crainte d' essuyer des querelles ecclesiastiques. De toutes les superstitions de ces tems -là, ce n' était pas la moins nuisible au bien des états, que celle de ne pouvoir épouser sa parente au septiéme degré. Presque tous les souverains de l' Europe étaient parens de Henri. Quoi qu' il en soit, Anne fille de Jaraslau czar de Moscovie fut reine de France ; et il est à remarquer qu' après la mort de son mari, elle n' eut point la régence, et n' y prétendit point. Les loix changent selon les tems. Ce fut le comte de Flandres, un des vassaux du royaume, qui en fut régent. La reine veuve se remaria à un comte de Crepi. Tout cela serait singulier aujourdhui, et ne le fut point alors. Ni Henri, ni <PERSON>Philippe I</PERSON> ne firent rien de mémorable ; mais de leur tems leurs vassaux et arrière - vassaux conquirent des royaumes."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Philippe I' and 'Clermont' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Philippe I' near 'Clermont' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 159 [ID: surprise_test_fr__6]:
  Publication date : 1756
  Language         : fr
  Person  : 'Eugène IV'  (QID: N/A)
  Location: 'Rome'  (QID: Q220)

  [ARTICLE TEXT — entity markers added]
  "Le pape Jean VIII le reçut à sa communion, le reconnut, lui écrivit ; et malgré ce huitiéme concile oecuménique, qui avait anathématisé ce patriarche, le pape envoya ses légats à un autre concile à Constantinople, dans lequel Photius fut reconnu innocent par quatre - cent évêques, dont trois - cent l' avaient auparavant condamné. Les légats de ce même siége de <LOCATION>Rome</LOCATION>, qui l' avaient anathématisé, servirent eux -mêmes à casser le huitiéme concile oecuménique. Combien tout change chez les hommes ! Combien ce qui était faux, devient vrai selon les tems ! Les légats de Jean VIII s' écrient en plein concile ; si quelqu' un ne reconnait pas Photius, que son partage soit avec Judas. le concile s' écrie, longues années au patriarche Photius, et au patriarche Jean. enfin à la suite des actes du concile on voit une lettre du pape à ce savant patriarche, dans laquelle il lui dit ; nous pensons comme vous... etc. il est donc clair que l' église romaine et la grecque pensaient alors différemment de ce qu' on pense aujourdhui. Il arriva depuis que Rome adopta la procession du pére et du fils ; et il arriva même qu' en 1274 l' empereur des grecs, Michel Paléologue, implorant contre les turcs une nouvelle croisade, envoya au second concile de Lyon, son patriarche et son chancelier, qui chantèrent avec le concile en latin, qui ex patre filioque procedit. mais l' église grecque retourna encor à son opinion, et sembla la quitter encor dans la réunion passagère qui se fit avec <PERSON>Eugène IV</PERSON>. Que les hommes aprennent de là à se tolerer les uns les autres. Voilà des variations et des disputes sur un point fondamental, qui n' ont ni excité de troubles, ni rempli les prisons, ni allumé les buchers. On a blâmé les déférences du pape Jean VIII pour le patriarche Photius ; on n' a pas assez songé que ce pontife avait alors besoin de l' empereur Basile. Un roi de Bulgarie, nommé Bogoris, gagné par l' habileté de sa femme qui était chrêtienne, s' était converti, à l' exemple de Clovis et du roi Egbert."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Rome
    Description: capitale de l'Italie
    Country: ['Italie', 'États pontificaux', "royaume d'Italie", 'royaume des Ostrogoths', 'Empire byzantin', "royaume d'Italie", 'royaume de Rome', 'République romaine', 'Empire romain', "Empire romain d'Occident", 'Vatican']
    Located in: ['province de Rome', 'États pontificaux', 'Rome', 'Rome antique', 'République romaine', 'Empire romain', "Empire romain d'Occident", 'ville métropolitaine de Rome Capitale', 'circle of Rome']
    Aliases: {'en': ['The Eternal City', 'Roma', 'Rome, Italy', 'City of Seven Hills'], 'fr': ['La ville éternelle', 'La ville aux sept collines', 'Roma', "l'Urbs"], 'de': ['Die Ewige Stadt', 'Roma'], 'lb': ['Roma', "D'Éiweg Stad"]}
    Coordinates: [{'lat': 41.893055555556, 'lon': 12.482777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1274" → 1274
    Temporal signal words: avant
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 482 days
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Eugène IV' and 'Rome' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Eugène IV' near 'Rome' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 160 [ID: surprise_test_fr__72]:
  Publication date : 1756
  Language         : fr
  Person  : 'calife Hésham'  (QID: N/A)
  Location: 'Portugal'  (QID: Q45)

  [ARTICLE TEXT — entity markers added]
  "Les succès de ce peuple conquérant semblent dûs plutôt à l' entousiasme qui les anime, et à l' esprit de la nation, qu' à ses conducteurs : car Omar est assassiné par un esclave perse en 653. Otman son successeur l' est en 655 dans une émeute. Ali ce fameux gendre de Mahomet n' est élu, et ne gouverne qu' au milieu des troubles. Il meurt assassiné au bout de cinq ans comme ses prédécesseurs, et cependant les armes musulmanes sont toujours heureuses. Cet Ali que les persans révèrent aujourd'hui, et dont ils suivent les principes en oposition à ceux d' Omar, obtint enfin le califat, et transféra le siége des califes de la ville de Médine, où Mahomet est enseveli, dans la ville de Couffa, sur les bords de l' Euphrate : à peine en reste - t -il aujourd'hui des ruines. C' est le sort de Babylone, de Séleucie, et de toutes les anciennes villes de la Caldée, qui n' étaient bâties que de briques. Il est évident que le génie du peuple arabe mis en mouvement par Mahomet fit tout de lui -même pendant près de trois siécles, et ressembla en cela au génie des anciens romains. C' est en effet sous Valid le moins guerrier des califes, que se font les plus grandes conquêtes. Un de ses généraux étend son empire jusqu' à Samarkande en 707. Un autre attaque en même tems l' empire des grecs vers la mer Noire. Un autre en 711 passe d' égypte en Espagne soumise aisément tour à tour par les carthaginois, par les romains, par les goths et vandales, et enfin par ces arabes qu' on nomme maures. Ils y établirent d' abord le royaume de Cordoüe. Le sultan d' égypte secoue à la vérité le joug du grand calife de Bagdat, et Abdérame gouverneur de l' Espagne conquise ne reconnait plus le sultan d' égypte : cependant tout plie encor sous les armes musulmanes. Cet Abdérame, petit - fils du <PERSON>calife Hésham</PERSON>, prend les royaumes de Castille, de Navarre, de <LOCATION>Portugal</LOCATION>, d' Arragon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Portugal
    Description: pays du sud-ouest de l'Europe
    Country: ['Portugal']
    Aliases: {'en': ['Portuguese Republic', 'PRT', 'POR'], 'fr': ['République portugaise'], 'de': ['Portugiesische Republik', 'PRT']}
    Coordinates: [{'lat': 38.7, 'lon': -9.183333333333334}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: aujourd'hui, ancien, ancienne, plus, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.988

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'calife Hésham' and 'Portugal' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'calife Hésham' near 'Portugal' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 161 [ID: surprise_test_fr__101]:
  Publication date : 1756
  Language         : fr
  Person  : 'Raoul'  (QID: N/A)
  Location: 'Dannemarck'  (QID: Q35)

  [ARTICLE TEXT — entity markers added]
  "Enfin Rolon ou <PERSON>Raoul</PERSON>, le plus illustre de ces brigands du nord, après avoir été chassé du <LOCATION>Dannemarck</LOCATION>, ayant rassemblé en Scandinavie tous ceux qui voulurent s' attacher à sa fortune, tenta de nouvelles avantures, et fonda l' espérance de sa grandeur sur la faiblesse de l' Europe. Il aborda l' Angleterre, où ses compatriotes étaient déja établis ; mais après deux victoires inutiles, il tourna du côté de la France, que d' autres normands savaient ruiner, mais qu' ils ne savaient pas asservir. Rolon fut le seul de ces barbares qui cessa d' en mériter le nom, en cherchant un établissement fixe. Maître de Rouen sans peine, au lieu de la détruire, il en fit relever les murailles et les tours. Rouen devint sa place d' armes ; de là il volait tantôt en Angleterre, tantôt en France, faisant la guerre avec politique, comme avec fureur. La France était expirante sous le régne de Charles Le Simple, roi de nom, et dont la monarchie était encor plus démembrée par les ducs, par les comtes et par les barons ses sujets, que par les normands. Charles Le Gros n' avait donné que de l' or aux barbares : Charles Le Simple offrit à Rolon sa fille et des provinces. Raoul demanda d' abord la Normandie : et on fut trop heureux de la lui céder. Il demanda ensuite la Bretagne ; on disputa ; mais il fallut la céder encor avec des clauses que le plus fort explique toûjours à son avantage. Ainsi la Bretagne, qui était tout - à - l' heure un royaume, devint un fief de la Neustrie ; et la Neustrie, qu' on s' accoutuma bientôt à nommer Normandie du nom de ses usurpateurs, fut un état séparé, dont les ducs rendaient un vain hommage à la couronne de France. L' archevêque de Rouen sut persuader à Rolon de se faire chrêtien. Ce prince embrassa volontiers une religion qui affermissait sa puissance. Les véritables conquérans sont ceux qui savent faire des loix. Leur puissance est stable ; les autres sont des torrens qui passent. Rolon paisible fut le seul législateur de son tems dans le continent chrêtien."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Danemark
    Description: État en Europe du Nord et en Amérique du Nord
    Country: ['Royaume de Danemark']
    Located in: ['Royaume de Danemark', 'Union de Kalmar']
    Aliases: {'en': ['dk', 'TAN', 'Denmark proper', 'metropolitan Denmark', 'Dania'], 'fr': ['DK', 'Dan.', 'Danemark propre', 'Danemark métropolitain']}
    Coordinates: [{'lat': 56, 'lon': 10}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après, avant, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Raoul' and 'Dannemarck' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Raoul' near 'Dannemarck' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 162 [ID: surprise_test_fr__204]:
  Publication date : 1797
  Language         : fr
  Person  : 'Delisle'  (QID: N/A)
  Location: 'France'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "Voulant seconder les intentions de son prince, il publia un recueil de cartes particulieres sous le titre d' atlas de l' empire des Russes, dans le dessein de l' augmenter & de le perfectionner de jour en jour ; mais ce n' étoit qu' un essai encore imparfait. A ce travail succéda celui que l' académie de Pétersbourg avoit résolu de faire de nouveau. M. Joseph <PERSON>Delisle</PERSON> y fut appellé, non - seulement en qualité d' astronome, mais encore comme géographe. Il mit la main à cet ouvrage, dès qu' il fut arrivé à Petersbourg en 1726. Plusieurs membres de l' académie se joignirent à lui en 1740, pour accélérer l' entreprise dont l' exécution fut achevée en 1745. Tel est l' état de la Géographie dans les différens pays de l' Europe. Il ne reste plus qu' à parler des progrès que cette science a faits en <LOCATION>France</LOCATION> depuis François premier, sous le regne duquel les Sciences commencerent à fleurir. L'on y remarque dans le seizieme siecle des amateurs de la Géographie. Quelques provinces dûrent aux travaux de plusieurs savans les cartes qui en furent publiées. François de la Guillotiere natif de Bourdeaux, fut, pour ainsi dire, le premier qui profitant des lumieres des savans antérieurs & contemporains, & des siennes propres, publia en 1584 une carte générale du royaume. Il en avoit dans ses mains toutes les cartes particulieres, prêtes à être mises au jour. Celui qui s' est le plus distingué dans le siecle suivant, fut Nicolas Sanson d' Abbeville, né en 1600 d' une famille distinguée de la Picardie. Ses ouvrages sont trop connus pour vouloir les détailler ici. Ses fils Nicolas, Guillaume & Adrien, coururent la même carriere, & soûtinrent avec honneur la réputation de leur pere. Pierre Moulard Sanson, petit - sils de Nicolas Sanson, entra aussi dans les vûes de son ayeul."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (5):
      - "1726" → 1726
      - "1740" → 1740
      - "1745" → 1745
      - "1584" → 1584
      - "1600" → 1600
    Temporal signal words: plus
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 52 days
    OCR quality estimate: 0.983

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Delisle' and 'France' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Delisle' near 'France' around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 163 [ID: surprise_test_fr__215]:
  Publication date : 1756
  Language         : fr
  Person  : 'roi Philippe'  (QID: N/A)
  Location: 'Pologne'  (QID: Q36)

  [ARTICLE TEXT — entity markers added]
  "L' empereur soûtenait, non sans raison, que les états de Matilde lui devaient revenir comme un fief de l' empire ; ainsi les papes combattaient pour le spirituel et pour le temporel. Pascal II n' obtint du <PERSON>roi Philippe</PERSON> que la permission de tenir un concile à Troye. Le gouvernement était trop faible, trop divisé pour lui donner des troupes. Henri V ayant terminé par des traités une guerre de peu de durée contre la <LOCATION>Pologne</LOCATION>, sut tellement intéresser les princes de l' empire à soûtenir ses droits, que ces mêmes princes qui avaient aidé à détroner son pére en vertu des bulles des papes, se réunirent avec lui pour faire annuller dans Rome ces mêmes bulles. Il descend donc des Alpes avec une armée ; et Rome fut encor teinte de sang pour cette querelle de la crosse et de l' anneau. Les traités, les parjures, les excommunications et les meurtres se suivirent avec rapidité. Pascal II ayant solemnellement rendu les investitures avec serment sur l' évangile, fit annuller son serment par es cardinaux ; nouvelle manière de manquer à sa parole. Il se laissa traiter de lâche et de prévaricateur en plein concile, afin d' être forcé à reprendre ce qu' il avait donné. Alors nouvelle irruption de l' empereur à Rome ; car presque jamais ces Césars n' y allèrent que pour des querelles ecclésiastiques, dont la plus grande était le couronnement. Enfin après avoir créé, déposé, chassé, rapellé des papes, Henri V aussi souvent excommunié que son pére, et inquiété comme lui par ses grands vassaux d' Allemagne, fut obligé de terminer la guerre des investitures, en renonçant à cette crosse et à cet anneau. Il fit plus ; il se désista solemnellement du droit que s' étaient attribué les empereurs, ainsi que les rois de France, de nommer aux évêchés, ou d' interposer tellement leur autorité dans les élections, qu' ils en étaient absolument les maîtres. Il fut donc décidé dans un concile tenu à Rome, que les rois ne donneraient plus aux bénéficiers canoniquement élus les investitures par un bâton recourbé, mais par une baguette."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Pologne
    Description: pays d'Europe centrale
    Country: ['Pologne']
    Aliases: {'en': ['Republic of Poland'], 'fr': ['République de Pologne', 'République polonaise', 'la République de Pologne', 'Pol.'], 'de': ['Republik Polen']}
    Coordinates: [{'lat': 52, 'lon': 19}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'roi Philippe' and 'Pologne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'roi Philippe' near 'Pologne' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 164 [ID: surprise_test_fr__230]:
  Publication date : 1756
  Language         : fr
  Person  : 'Matthieu Visconti seigneur de Milan'  (QID: N/A)
  Location: 'Rome'  (QID: Q220)

  [ARTICLE TEXT — entity markers added]
  "En 1255 le pape Alexandre III établit l' inquisition en France sous le roi S. Louis. Le gardien des cordeliers de Paris, et le provincial des dominicains, étaient les grands inquisiteurs. Ils devaient, par la bulle d' Alexandre, consulter les évêques, mais ils n' en dépendaient pas. Cette étrange jurisdiction donnée à des hommes qui font voeu de renoncer au monde, indigna le clergé et les laïcs. Un cordelier inquisiteur assista au jugement des templiers ; mais bientôt le soulévement de tous les esprits ne laissa à ces moines qu' un titre inutile. En Italie les papes avaient plus de crédit, parce que tout désobéis qu' ils étaient dans <LOCATION>Rome</LOCATION>, tout éloignés qu' ils en furent longtems, ils étaient toujours à la tête de la faction guelphe, contre celle des gibelins. Ils se servirent de cette inquisition contre les partisans de l' empire. Car en 1302 le pape Jean XXII fit procéder par des moines inquisiteurs contre <PERSON>Matthieu Visconti seigneur de Milan</PERSON>, dont le crime était d' être attaché à l' empereur Louis De Baviére. Le dévouement du vassal à son suzerain, fut déclaré hérésie ; la maison d' est, celle de Malatesta, furent traitées de même, pour la même cause ; et si le suplice ne suivit pas la sentence, c' est qu' il était alors plus aisé aux papes d' avoir des inquisiteurs que des armées. Plus ce tribunal s' établit, et plus les évêques qui se voyaient enlever un droit qui semblait leur apartenir, le reclamèrent vivement. Les papes les associèrent aux moines inquisiteurs, qui exerçaient pleinement leur autorité dans presque tous les états d' Italie, et dont les évêques ne furent que les assesseurs. Sur la fin du treiziéme siécle en 1289 Venise avait déja reçu l' inquisition ; mais si ailleurs elle était toute dépendante du pape, elle fut dans l' état vénitien soumise au sénat. La plus sage précaution qu' il prit, fut que les amendes et les confiscations n' apartinssent pas aux inquisiteurs."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Rome
    Description: capitale de l'Italie
    Country: ['Italie', 'États pontificaux', 'Q3755547', 'royaume des Ostrogoths', 'Q12544', 'Q172579', 'Q201038', 'Q17167', 'Empire romain', "Empire romain d'Occident", 'Vatican']
    Located in: ['province de Rome', 'États pontificaux', 'Q1558632', 'Q1747689', 'République romaine', 'Empire romain', "Empire romain d'Occident", 'Q18288160', 'Q3677829']
    Aliases: {'en': ['The Eternal City', 'Roma', 'Rome, Italy', 'City of Seven Hills'], 'fr': ['La ville éternelle', 'La ville aux sept collines', 'Roma', "l'Urbs"], 'de': ['Die Ewige Stadt', 'Roma'], 'lb': ['Roma', "D'Éiweg Stad"]}
    Coordinates: [{'lat': 41.893055555556, 'lon': 12.482777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1255" → 1255
      - "1302" → 1302
      - "1289" → 1289
    Temporal signal words: plus, tôt
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 454 days
    OCR quality estimate: 0.991

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Matthieu Visconti seigneur de Milan' and 'Rome' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Matthieu Visconti seigneur de Milan' near 'Rome' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 165 [ID: surprise_test_fr__243]:
  Publication date : 1797
  Language         : fr
  Person  : 'Halley'  (QID: Q47434)
  Location: "sud de l' île de la Trinité"  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "D' après le rapport de M De Vaujuas et de M Boutin, il était évident que nous ne pouvions trouver à la Trinité l' eau et le bois qui nous manquaient. Je me décidai tout de suite à faire route pour l' île Sainte - Catherine, sur la côte du Brésil : c' était l' ancienne relâche des bâtimens français qui allaient dans la mer du sud. Frézier et l' amiral Anson y trouvèrent abondamment à se pourvoir de tous leurs besoins. Ce fut pour ne pas perdre un seul jour, que je donnai la préférence à l' île Sainte - Catherine sur Rio - Janéïro, où les différentes formalités auraient exigé plus de temps qu' il n' en fallait pour faire l' eau et le bois qui nous manquaient. Mais en dirigeant ma route vers l' île Sainte - Catherine, je voulus m' assurer de l' existence de l' île de l' Ascençaon, que M Daprès place à cent lieues dans l' ouest de la Trinité, et à 15 minutes seulement plus sud. Suivant le journal de M Poncel De La Haye, qui commandait la frégate la renommée, j' étais certain que différens navigateurs, entr' autres Frézier, homme très - éclairé, avaient cru aborder à l' Ascençaon, et qu' ils n' avaient été réellement qu' à la Trinité. Malgré l' autorité de M Poncel De La Haye, je crus que ce point de géographie demandait un nouvel éclaircissement. Les deux jours que nous passâmes vers la partie <LOCATION>sud de l' île de la Trinité</LOCATION>, nous mirent à portée de faire les relèvemens d' après lesquels M Bernizet traça le plan de la partie sud de l' île : il diffère très - peu de celui du docteur <PERSON>Halley</PERSON>, qui m' avait été remis par M De Fleurieu. La vue, peinte par M Duché De Vancy, est d' une vérité si frappante, qu' elle suffira seule pour que les navigateurs qui aborderont dans la partie du sud de la Trinité, ne puissent jamais se tromper."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Edmond Halley
    Description: scientifique anglais (astronome, géophysicien, mathématicien, météorologue, physicien)
    Born: ['+1656-11-08T00:00:00Z', '+1656-11-08T00:00:00Z']
    Died: ['+1742-01-14T00:00:00Z', '+1742-01-25T00:00:00Z']
    Birth place: ['Q2146341']
    Death place: ['Q179385']
    Work locations: ['Sainte-Hélène']
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien, ancienne, plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Halley' and "sud de l' île de la Trinité" in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Halley' near "sud de l' île de la Trinité" around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 166 [ID: surprise_test_fr__347]:
  Publication date : 1756
  Language         : fr
  Person  : 'Issel'  (QID: N/A)
  Location: 'Amsterdam'  (QID: Q727)

  [ARTICLE TEXT — entity markers added]
  "Le siége et la défense de Leyde sont un des plus grands témoignages de ce que peuvent la constance et la liberté. Les hollandais firent précisément la même chose qu' on leur a vû hazarder en 1672 lorsque Louis XIV était aux portes d' <LOCATION>Amsterdam</LOCATION> ; ils percèrent les digues ; les eaux de l' <PERSON>Issel</PERSON>, de la Meuse, et de l' océan inondèrent les campagnes ; et une flotte de deux - cent bateaux aporta du secours dans la ville par - dessus les ouvrages des espagnols. Il y eut un autre prodige ; c' est que les assiégeans osèrent continuer le siége et entreprendre de saigner cette vaste inondation. Il n' y avait point d' exemple dans l' histoire ni d' une telle ressource dans des assiégés, ni d' une telle opiniâtreté dans des assiégeans ; mais cette opiniâtreté fut inutile, et Leyde célèbre encor aujourdhui tous les ans le jour de sa délivrance. Il ne faut pas oublier que les habitans se servirent de pigeons dans ce siége pour donner des nouvelles au prince d' Orange : c' est une pratique commune en Asie. Quel était donc ce gouvernement si sage et si vanté de Philippe II lorsqu' on voit dans ce tems -là même ses troupes se mutiner en Flandre faute de payement, saccager la ville d' Anvers, et que toutes les provinces des Pays - Bas, sans consulter ni lui, ni son gouverneur, font un traité de pacification avec les révoltés, publient une amnistie, rendent les prisonniers, font démolir des forteresses, et ordonnent qu' on abattra la fameuse statue du duc d' Albe, trophée que son orgueil avait élevé à sa cruauté, et qui était encor debout dans la citadelle d' Anvers, dont le roi était le maître ? Après la mort du grand commandeur de Requesens, Philippe qui pouvait encor essayer de remettre le calme dans les Pays - Bas par sa présence, y envoye Don Juan D' Autriche son frére, prince célèbre dans l' Europe par la fameuse victoire de Lépante remportée sur les turcs, et par son ambition qui lui avait fait tenter d' être roi de Tunis. Philippe n' aimait pas Don Juan ; il craignait sa gloire, et se défiait de ses desseins."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Amsterdam
    Description: capitale des Pays-Bas
    Country: ['Pays-Bas', 'Reichskommissariat Niederlande', 'Q55', 'Q15864', 'Q774783', 'Q142', 'Royaume de Hollande', 'Q188553', 'Q170072', 'Pays-Bas des Habsbourg', 'Q157109', 'Q762943']
    Located in: ['Q9899', 'Amstel Department', 'Q762943', 'Q2424414', 'Q1875838', 'Q231168', 'Holland', 'Hollande-Septentrionale']
    Aliases: {'en': ['Mokum', 'Amsterdam, North Holland', 'Amsterdam, NL', 'Amsterdam, Netherlands', "A'dam"], 'fr': ["A'dam"]}
    Coordinates: [{'lat': 52.36666666666667, 'lon': 4.883333333333333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1672" → 1672
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 84 days
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Issel' and 'Amsterdam' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Issel' near 'Amsterdam' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 167 [ID: surprise_test_fr__357]:
  Publication date : 1756
  Language         : fr
  Person  : 'Dunois'  (QID: N/A)
  Location: 'Normandie'  (QID: Q15878)

  [ARTICLE TEXT — entity markers added]
  "Il n' y eut que l' arriére - ban, composé des arrière - petits vassaux, qui resta sujet encor à servir dans les occasions. On s' étonne qu' après tant de désastres la France eût tant de ressources et d' argent. Mais un pays riche par ses denrées, ne cesse jamais de l' être, quand la culture n' est pas abandonnée. Les guerres civiles ébranlent le corps de l' état, et ne le détruisent point. Les meurtres et les saccagements, qui désolent des familles, en enrichissent d' autres. Les négocians deviennent d' autant plus habiles qu' il faut plus d' art pour se sauver parmi tant d' orages. Jacques Coeur en est un grand exemple. Il avait établi le plus grand commerce qu' aucun particulier de l' Europe eût jamais embrassé. Il n' y eut depuis lui que Cosme De Médicis qui l' égalât. Jacques Coeur avait trois - cent facteurs en Italie et dans le levant. Il prêta deux - cent - mille écus d' or au roi, sans quoi on n' aurait jamais repris la <LOCATION>Normandie</LOCATION>. Son industrie était plus utile pendant la paix, que <PERSON>Dunois</PERSON> et la pucelle ne l' avaient été pendant la guerre. C' est une grande tache peut - être à la mémoire de Charles VII qu' on ait persécuté un homme si nécessaire. On n' en sait point le sujet : car qui sait les secrets ressorts des fautes, et des injustices des hommes. Le roi le fit mettre en prison, et le parlement lui fit son procès. On ne put rien prouver, contre lui, sinon qu' il avait fait rendre à un turc un esclave chrêtien, lequel avait quitté et trahi son maître, et qu' il avait fait vendre des armes au soudan d' égypte. Sur ces deux actions, dont l' une était permise, et l' autre vertueuse, il fut condamné à perdre ses biens. Il trouva dans ses commis plus de droiture que dans les courtisans qui l' avaient perdu. Ils se cotisèrent presque tous pour l' aider dans sa disgrace. Jacques Coeur alla continuer son commerce en Chypre, et n' eut jamais le courage de revenir dans son ingrate patrie, quoiqu' il y fût rapellé."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Normandie
    Description: province historique et région culturelle, aujourd'hui répartie entre la France, principalement, et les îles Anglo-Normandes
    Country: ['Q142', 'Q785', 'bailliage de Guernesey']
    Coordinates: [{'lat': 49.12233911111111, 'lon': -0.43664430555555556}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, né à, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Dunois' and 'Normandie' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Dunois' near 'Normandie' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 168 [ID: surprise_test_fr__377]:
  Publication date : 1678
  Language         : fr
  Person  : 'Hugues Capet'  (QID: Q159575)
  Location: 'France'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "Il est vray que ces renoncemens doivent avoir quelque cause legitime, et que les rois feroient tort à leurs successeurs, s' ils retranchoient une province du corps de l' etat sans y être contraints, ou sans y trouver de grands avantages. Mais lors qu' ils ne consentent à ces retranchemens que par necessité, ou pour le bien et l' utilité du royaume, leurs successeurs n' ont aucun sujet de se plaindre d' eux ; et s' ils en ont, la plupart de nos rois auroient eu droit de se plaindre de leurs predecesseurs, particulierement les enfans de Henry Ii qui par le traité de château Cambresy, relâcha et rendit près de deux cens villes ou forteresses. Il faut ajoutter à cela qu' il est difficile de marquer ce point de grandeur dont parle l' auteur qu' on a cité, où les etats étant parvenus, il n' est plus permis aux rois d' en retrancher aucune partie ; parce qu' il ne s' est jamais passé de temps considerable depuis l' établissement de la monarchie, que la <LOCATION>France</LOCATION> ne se soit accruë par les conquêtes de nos rois, ou n' ait diminué par celles de nos voisins. De plus, les rois de la premiere et seconde race luy ont très - souvent ôté sa grandeur, la partageant entre leurs enfans, et divisant le royaume en plusieurs royaumes. Enfin pour ne pas alleguer toutes les provinces qui ont été desunies de la couronne, il suffit de dire que la Bourgogne l' avoit été par le roy Henry, petit fils de <PERSON>Hugues Capet</PERSON>, en faveur de Robert son frere ; qu' elle y revint sous le roy Jean, qui la donna peu de temps après à Philippe Le Hardy son quatriéme fils ; et qu' après la mort de Charles dernier Duc de Bourgogne, Loüis XI s' en rendit le maître ; de sorte qu' il n' y avoit pas cinquante ans qu' elle étoit réünie à la couronne lorsque François I la voulut ceder. Passons maintenant aux autres pretextes qu' on prend pour se dispenser de la fidelité qu' on doit aux souverains."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Hugues Capet
    Description: roi des Francs de 987 à 996, fondateur de la dynastie capétienne
    Born: ['+0940-01-01T00:00:00Z']
    Died: ['+0996-10-24T00:00:00Z']
    Birth place: ['Q646609']
    Death place: ['Q1820536']
  Location Wikidata:
    Label: France
    Description: pays transcontinental au territoire métropolitain situé en Europe de l'Ouest
    Country: ['France']
    Aliases: {'en': ['French Republic'], 'fr': ['République française', 'RF', 'fr', 'la République française', 'Fr.', 'La France', "L'Hexagone"], 'de': ['Französische Republik', 'fr', 'RF']}
    Coordinates: [{'lat': 47, 'lon': 2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: maintenant, plus, après, avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Hugues Capet' and 'France' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Hugues Capet' near 'France' around 1678?
  4. Resolve temporal expressions relative to 1678. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 169 [ID: surprise_test_fr__392]:
  Publication date : 1756
  Language         : fr
  Person  : 'Anne'  (QID: N/A)
  Location: 'Europe'  (QID: Q46)

  [ARTICLE TEXT — entity markers added]
  "Ce qu' il y a de plus singulier, c' est qu' Urbain II qui prononça cette sentence, la prononça dans les propres états du roi, à Clermont en Auvergne, où il venait chercher un azile, et dans ce même concile où nous verrons qu' il prêcha la croisade. Cependant il ne paraît point que Philippe excommunié ait été en horreur à ses sujets ; c' est une raison de plus pour douter de cet abandon général où l'on dit que le roi Robert avait été réduit. Ce qu' il y eut d' assez remarquable, c' est le mariage du roi Henri pére de Philippe avec une princesse moscovite. Les moscovites ou russes commençaient à être chrêtiens ; mais ils n' avaient aucun commerce avec le reste de l' <LOCATION>Europe</LOCATION>. Ils habitaient au - delà de la Pologne, à peine chrêtienne elle -même, et sans aucune correspondance avec la France. Cependant le roi Henri envoya jusqu' en Russie demander la fille du souverain, à qui les autres européans donnaient le titre de duc, aussi - bien qu' au chef de la Pologne. Les russes le nommaient dans leur langage tzaar, dont on a fait depuis le mot de czar. On prétend que Henri se détermina à ce mariage, dans la crainte d' essuyer des querelles ecclesiastiques. De toutes les superstitions de ces tems -là, ce n' était pas la moins nuisible au bien des états, que celle de ne pouvoir épouser sa parente au septiéme degré. Presque tous les souverains de l' Europe étaient parens de Henri. Quoi qu' il en soit, <PERSON>Anne</PERSON> fille de Jaraslau czar de Moscovie fut reine de France ; et il est à remarquer qu' après la mort de son mari, elle n' eut point la régence, et n' y prétendit point. Les loix changent selon les tems. Ce fut le comte de Flandres, un des vassaux du royaume, qui en fut régent. La reine veuve se remaria à un comte de Crepi. Tout cela serait singulier aujourdhui, et ne le fut point alors. Ni Henri, ni Philippe I ne firent rien de mémorable ; mais de leur tems leurs vassaux et arrière - vassaux conquirent des royaumes."

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
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Anne' and 'Europe' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Anne' near 'Europe' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 170 [ID: surprise_test_fr__393]:
  Publication date : 1756
  Language         : fr
  Person  : 'Philippe I'  (QID: N/A)
  Location: 'Europe'  (QID: Q46)

  [ARTICLE TEXT — entity markers added]
  "Ce qu' il y a de plus singulier, c' est qu' Urbain II qui prononça cette sentence, la prononça dans les propres états du roi, à Clermont en Auvergne, où il venait chercher un azile, et dans ce même concile où nous verrons qu' il prêcha la croisade. Cependant il ne paraît point que Philippe excommunié ait été en horreur à ses sujets ; c' est une raison de plus pour douter de cet abandon général où l'on dit que le roi Robert avait été réduit. Ce qu' il y eut d' assez remarquable, c' est le mariage du roi Henri pére de Philippe avec une princesse moscovite. Les moscovites ou russes commençaient à être chrêtiens ; mais ils n' avaient aucun commerce avec le reste de l' <LOCATION>Europe</LOCATION>. Ils habitaient au - delà de la Pologne, à peine chrêtienne elle -même, et sans aucune correspondance avec la France. Cependant le roi Henri envoya jusqu' en Russie demander la fille du souverain, à qui les autres européans donnaient le titre de duc, aussi - bien qu' au chef de la Pologne. Les russes le nommaient dans leur langage tzaar, dont on a fait depuis le mot de czar. On prétend que Henri se détermina à ce mariage, dans la crainte d' essuyer des querelles ecclesiastiques. De toutes les superstitions de ces tems -là, ce n' était pas la moins nuisible au bien des états, que celle de ne pouvoir épouser sa parente au septiéme degré. Presque tous les souverains de l' Europe étaient parens de Henri. Quoi qu' il en soit, Anne fille de Jaraslau czar de Moscovie fut reine de France ; et il est à remarquer qu' après la mort de son mari, elle n' eut point la régence, et n' y prétendit point. Les loix changent selon les tems. Ce fut le comte de Flandres, un des vassaux du royaume, qui en fut régent. La reine veuve se remaria à un comte de Crepi. Tout cela serait singulier aujourdhui, et ne le fut point alors. Ni Henri, ni <PERSON>Philippe I</PERSON> ne firent rien de mémorable ; mais de leur tems leurs vassaux et arrière - vassaux conquirent des royaumes."

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
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Philippe I' and 'Europe' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Philippe I' near 'Europe' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 171 [ID: surprise_test_fr__406]:
  Publication date : 1561
  Language         : fr
  Person  : 'Villeneufve'  (QID: N/A)
  Location: 'Lorraine'  (QID: Q1137)

  [ARTICLE TEXT — entity markers added]
  "Misser Iuliano commanda à Torneto de la prendre, & de la mener chez luy en l' estable. Là ou elle se rengea aussi proprement, comme si elle n' en eust jamais bougé. Il la fit ramener le lendemain en la mesme place, pour veoir si quelqu' un la vendiqueroit. Mais il ne venoit personne, dont il fut fort esbahy : & pensoit que ce fust quelque esprit qui l' eust ramenee. De là à quelque temps maistre Arnaud s' addresse à misser Iuliano, lequel il trouva monté sus sa hacquenee, & luy dit : monsieur, je suis fort aise de savoir que ceste hacquenee soit à vous. Car asseurez vous qu' elle est bonne : je l' ay essayee, il y ha environ un an que je la trouvay pres du pont du Rosne, qu' elle s' en alloit toute seule, & qu' un garson la vouloit prendre. Mais congnoissant à sa façon qu' elle n' estoit pas sienne, je la luy ostay : & la garday un jour ou deux sans pouvoir savoir à qui elle estoit. Le troisiesme jour je la menay jusques à <PERSON>Villeneufve</PERSON>, ou j' ouy dire qu' un gentilhomme François la cherchoit, & qu' il luy avoit esté dit qu' on l' avoit veue emmener par un garson sus le chemin de Paris. Le gentilhomme alloit apres. Et moy sachant celà, je picque apres luy pour la luy rendre : mais je ne le peu jamais atteindre. Car il alloit grand train pour atteindre son larron. Et allay tant en le cherchant, que je me trouvay jusqu' en <LOCATION>Lorraine</LOCATION>. Là ou voyant que je n' oyois point de nouvelles de ce gentilhomme, je la garday long temps. Et à la fin m' en suis revenu en ceste ville, ou je l' avoys prise : & ay trouvé par quelques uns de mes amis, qu' il se souvenoit bien l' avoir veue autrefois en ceste ville : mais qu' il ne savoit à qui, sinon que ce fust à quelqu' un de vous autres messieurs de la legation. Sachant celà, je l' ay fait mener en la place du Palais, affin que celuy à qui elle estoit la peust appercevoir. Et ce pendant je m' en estois allé d' icy à Nimes, d' ou je suis retourné depuis deux jours. Mais Dieu soit loué qu' elle ha retrouvé son maistre. Car j' en estois en grand peine."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Lorraine
    Description: région culturelle et historique française
    Country: ['France']
    Located in: ['France métropolitaine']
    Aliases: {'de': ['Lorraine']}
    Coordinates: [{'lat': 48.6, 'lon': 6.4872222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Villeneufve' and 'Lorraine' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Villeneufve' near 'Lorraine' around 1561?
  4. Resolve temporal expressions relative to 1561. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 172 [ID: surprise_test_fr__411]:
  Publication date : 1561
  Language         : fr
  Person  : 'maistre Arnaud'  (QID: N/A)
  Location: 'Lorraine'  (QID: Q1137)

  [ARTICLE TEXT — entity markers added]
  "Misser Iuliano commanda à Torneto de la prendre, & de la mener chez luy en l' estable. Là ou elle se rengea aussi proprement, comme si elle n' en eust jamais bougé. Il la fit ramener le lendemain en la mesme place, pour veoir si quelqu' un la vendiqueroit. Mais il ne venoit personne, dont il fut fort esbahy : & pensoit que ce fust quelque esprit qui l' eust ramenee. De là à quelque temps <PERSON>maistre Arnaud</PERSON> s' addresse à misser Iuliano, lequel il trouva monté sus sa hacquenee, & luy dit : monsieur, je suis fort aise de savoir que ceste hacquenee soit à vous. Car asseurez vous qu' elle est bonne : je l' ay essayee, il y ha environ un an que je la trouvay pres du pont du Rosne, qu' elle s' en alloit toute seule, & qu' un garson la vouloit prendre. Mais congnoissant à sa façon qu' elle n' estoit pas sienne, je la luy ostay : & la garday un jour ou deux sans pouvoir savoir à qui elle estoit. Le troisiesme jour je la menay jusques à Villeneufve, ou j' ouy dire qu' un gentilhomme François la cherchoit, & qu' il luy avoit esté dit qu' on l' avoit veue emmener par un garson sus le chemin de Paris. Le gentilhomme alloit apres. Et moy sachant celà, je picque apres luy pour la luy rendre : mais je ne le peu jamais atteindre. Car il alloit grand train pour atteindre son larron. Et allay tant en le cherchant, que je me trouvay jusqu' en <LOCATION>Lorraine</LOCATION>. Là ou voyant que je n' oyois point de nouvelles de ce gentilhomme, je la garday long temps. Et à la fin m' en suis revenu en ceste ville, ou je l' avoys prise : & ay trouvé par quelques uns de mes amis, qu' il se souvenoit bien l' avoir veue autrefois en ceste ville : mais qu' il ne savoit à qui, sinon que ce fust à quelqu' un de vous autres messieurs de la legation. Sachant celà, je l' ay fait mener en la place du Palais, affin que celuy à qui elle estoit la peust appercevoir. Et ce pendant je m' en estois allé d' icy à Nimes, d' ou je suis retourné depuis deux jours. Mais Dieu soit loué qu' elle ha retrouvé son maistre. Car j' en estois en grand peine."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Lorraine
    Description: région culturelle et historique française
    Country: ['France']
    Located in: ['France métropolitaine']
    Aliases: {'de': ['Lorraine']}
    Coordinates: [{'lat': 48.6, 'lon': 6.4872222222222}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'maistre Arnaud' and 'Lorraine' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'maistre Arnaud' near 'Lorraine' around 1561?
  4. Resolve temporal expressions relative to 1561. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 173 [ID: surprise_test_fr__70]:
  Publication date : 1756
  Language         : fr
  Person  : 'Abdérame'  (QID: N/A)
  Location: 'Navarre'  (QID: Q200262)

  [ARTICLE TEXT — entity markers added]
  "Les succès de ce peuple conquérant semblent dûs plutôt à l' entousiasme qui les anime, et à l' esprit de la nation, qu' à ses conducteurs : car Omar est assassiné par un esclave perse en 653. Otman son successeur l' est en 655 dans une émeute. Ali ce fameux gendre de Mahomet n' est élu, et ne gouverne qu' au milieu des troubles. Il meurt assassiné au bout de cinq ans comme ses prédécesseurs, et cependant les armes musulmanes sont toujours heureuses. Cet Ali que les persans révèrent aujourd'hui, et dont ils suivent les principes en oposition à ceux d' Omar, obtint enfin le califat, et transféra le siége des califes de la ville de Médine, où Mahomet est enseveli, dans la ville de Couffa, sur les bords de l' Euphrate : à peine en reste - t -il aujourd'hui des ruines. C' est le sort de Babylone, de Séleucie, et de toutes les anciennes villes de la Caldée, qui n' étaient bâties que de briques. Il est évident que le génie du peuple arabe mis en mouvement par Mahomet fit tout de lui -même pendant près de trois siécles, et ressembla en cela au génie des anciens romains. C' est en effet sous Valid le moins guerrier des califes, que se font les plus grandes conquêtes. Un de ses généraux étend son empire jusqu' à Samarkande en 707. Un autre attaque en même tems l' empire des grecs vers la mer Noire. Un autre en 711 passe d' égypte en Espagne soumise aisément tour à tour par les carthaginois, par les romains, par les goths et vandales, et enfin par ces arabes qu' on nomme maures. Ils y établirent d' abord le royaume de Cordoüe. Le sultan d' égypte secoue à la vérité le joug du grand calife de Bagdat, et <PERSON>Abdérame</PERSON> gouverneur de l' Espagne conquise ne reconnait plus le sultan d' égypte : cependant tout plie encor sous les armes musulmanes. Cet Abdérame, petit - fils du calife Hésham, prend les royaumes de Castille, de <LOCATION>Navarre</LOCATION>, de Portugal, d' Arragon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: royaume de Navarre
    Description: (1162-1512) royaume médiéval qui occupait des terres de part et d'autre des Pyrénées occidentales, le long de l'océan Atlantique
    Aliases: {'en': ['Kingdom of Pamplona'], 'de': ['König von Navarra']}
    Coordinates: [{'lat': 42.816944444444, 'lon': -1.6427777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: aujourd'hui, ancien, ancienne, plus, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.988

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Abdérame' and 'Navarre' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Abdérame' near 'Navarre' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 174 [ID: surprise_test_fr__73]:
  Publication date : 1756
  Language         : fr
  Person  : 'Abdérame'  (QID: N/A)
  Location: 'Portugal'  (QID: Q45)

  [ARTICLE TEXT — entity markers added]
  "Les succès de ce peuple conquérant semblent dûs plutôt à l' entousiasme qui les anime, et à l' esprit de la nation, qu' à ses conducteurs : car Omar est assassiné par un esclave perse en 653. Otman son successeur l' est en 655 dans une émeute. Ali ce fameux gendre de Mahomet n' est élu, et ne gouverne qu' au milieu des troubles. Il meurt assassiné au bout de cinq ans comme ses prédécesseurs, et cependant les armes musulmanes sont toujours heureuses. Cet Ali que les persans révèrent aujourd'hui, et dont ils suivent les principes en oposition à ceux d' Omar, obtint enfin le califat, et transféra le siége des califes de la ville de Médine, où Mahomet est enseveli, dans la ville de Couffa, sur les bords de l' Euphrate : à peine en reste - t -il aujourd'hui des ruines. C' est le sort de Babylone, de Séleucie, et de toutes les anciennes villes de la Caldée, qui n' étaient bâties que de briques. Il est évident que le génie du peuple arabe mis en mouvement par Mahomet fit tout de lui -même pendant près de trois siécles, et ressembla en cela au génie des anciens romains. C' est en effet sous Valid le moins guerrier des califes, que se font les plus grandes conquêtes. Un de ses généraux étend son empire jusqu' à Samarkande en 707. Un autre attaque en même tems l' empire des grecs vers la mer Noire. Un autre en 711 passe d' égypte en Espagne soumise aisément tour à tour par les carthaginois, par les romains, par les goths et vandales, et enfin par ces arabes qu' on nomme maures. Ils y établirent d' abord le royaume de Cordoüe. Le sultan d' égypte secoue à la vérité le joug du grand calife de Bagdat, et <PERSON>Abdérame</PERSON> gouverneur de l' Espagne conquise ne reconnait plus le sultan d' égypte : cependant tout plie encor sous les armes musulmanes. Cet Abdérame, petit - fils du calife Hésham, prend les royaumes de Castille, de Navarre, de <LOCATION>Portugal</LOCATION>, d' Arragon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Portugal
    Description: pays du sud-ouest de l'Europe
    Country: ['Portugal']
    Aliases: {'en': ['Portuguese Republic', 'PRT', 'POR'], 'fr': ['République portugaise'], 'de': ['Portugiesische Republik', 'PRT']}
    Coordinates: [{'lat': 38.7, 'lon': -9.183333333333334}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: aujourd'hui, ancien, ancienne, plus, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.988

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Abdérame' and 'Portugal' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Abdérame' near 'Portugal' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 175 [ID: surprise_test_fr__103]:
  Publication date : 1756
  Language         : fr
  Person  : 'Rolon'  (QID: N/A)
  Location: 'Dannemarck'  (QID: Q35)

  [ARTICLE TEXT — entity markers added]
  "Enfin <PERSON>Rolon</PERSON> ou Raoul, le plus illustre de ces brigands du nord, après avoir été chassé du <LOCATION>Dannemarck</LOCATION>, ayant rassemblé en Scandinavie tous ceux qui voulurent s' attacher à sa fortune, tenta de nouvelles avantures, et fonda l' espérance de sa grandeur sur la faiblesse de l' Europe. Il aborda l' Angleterre, où ses compatriotes étaient déja établis ; mais après deux victoires inutiles, il tourna du côté de la France, que d' autres normands savaient ruiner, mais qu' ils ne savaient pas asservir. Rolon fut le seul de ces barbares qui cessa d' en mériter le nom, en cherchant un établissement fixe. Maître de Rouen sans peine, au lieu de la détruire, il en fit relever les murailles et les tours. Rouen devint sa place d' armes ; de là il volait tantôt en Angleterre, tantôt en France, faisant la guerre avec politique, comme avec fureur. La France était expirante sous le régne de Charles Le Simple, roi de nom, et dont la monarchie était encor plus démembrée par les ducs, par les comtes et par les barons ses sujets, que par les normands. Charles Le Gros n' avait donné que de l' or aux barbares : Charles Le Simple offrit à Rolon sa fille et des provinces. Raoul demanda d' abord la Normandie : et on fut trop heureux de la lui céder. Il demanda ensuite la Bretagne ; on disputa ; mais il fallut la céder encor avec des clauses que le plus fort explique toûjours à son avantage. Ainsi la Bretagne, qui était tout - à - l' heure un royaume, devint un fief de la Neustrie ; et la Neustrie, qu' on s' accoutuma bientôt à nommer Normandie du nom de ses usurpateurs, fut un état séparé, dont les ducs rendaient un vain hommage à la couronne de France. L' archevêque de Rouen sut persuader à Rolon de se faire chrêtien. Ce prince embrassa volontiers une religion qui affermissait sa puissance. Les véritables conquérans sont ceux qui savent faire des loix. Leur puissance est stable ; les autres sont des torrens qui passent. Rolon paisible fut le seul législateur de son tems dans le continent chrêtien."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Danemark
    Description: État en Europe du Nord et en Amérique du Nord
    Country: ['Royaume de Danemark']
    Located in: ['Royaume de Danemark', 'Union de Kalmar']
    Aliases: {'en': ['dk', 'TAN', 'Denmark proper', 'metropolitan Denmark', 'Dania'], 'fr': ['DK', 'Dan.', 'Danemark propre', 'Danemark métropolitain']}
    Coordinates: [{'lat': 56, 'lon': 10}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après, avant, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Rolon' and 'Dannemarck' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Rolon' near 'Dannemarck' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 176 [ID: surprise_test_fr__209]:
  Publication date : 1756
  Language         : fr
  Person  : 'Henri V'  (QID: N/A)
  Location: 'Pologne'  (QID: Q36)

  [ARTICLE TEXT — entity markers added]
  "L' empereur soûtenait, non sans raison, que les états de Matilde lui devaient revenir comme un fief de l' empire ; ainsi les papes combattaient pour le spirituel et pour le temporel. Pascal II n' obtint du roi Philippe que la permission de tenir un concile à Troye. Le gouvernement était trop faible, trop divisé pour lui donner des troupes. <PERSON>Henri V</PERSON> ayant terminé par des traités une guerre de peu de durée contre la <LOCATION>Pologne</LOCATION>, sut tellement intéresser les princes de l' empire à soûtenir ses droits, que ces mêmes princes qui avaient aidé à détroner son pére en vertu des bulles des papes, se réunirent avec lui pour faire annuller dans Rome ces mêmes bulles. Il descend donc des Alpes avec une armée ; et Rome fut encor teinte de sang pour cette querelle de la crosse et de l' anneau. Les traités, les parjures, les excommunications et les meurtres se suivirent avec rapidité. Pascal II ayant solemnellement rendu les investitures avec serment sur l' évangile, fit annuller son serment par es cardinaux ; nouvelle manière de manquer à sa parole. Il se laissa traiter de lâche et de prévaricateur en plein concile, afin d' être forcé à reprendre ce qu' il avait donné. Alors nouvelle irruption de l' empereur à Rome ; car presque jamais ces Césars n' y allèrent que pour des querelles ecclésiastiques, dont la plus grande était le couronnement. Enfin après avoir créé, déposé, chassé, rapellé des papes, Henri V aussi souvent excommunié que son pére, et inquiété comme lui par ses grands vassaux d' Allemagne, fut obligé de terminer la guerre des investitures, en renonçant à cette crosse et à cet anneau. Il fit plus ; il se désista solemnellement du droit que s' étaient attribué les empereurs, ainsi que les rois de France, de nommer aux évêchés, ou d' interposer tellement leur autorité dans les élections, qu' ils en étaient absolument les maîtres. Il fut donc décidé dans un concile tenu à Rome, que les rois ne donneraient plus aux bénéficiers canoniquement élus les investitures par un bâton recourbé, mais par une baguette."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Henri V' and 'Pologne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Henri V' near 'Pologne' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 177 [ID: surprise_test_fr__223]:
  Publication date : 1756
  Language         : fr
  Person  : 'Matilde'  (QID: N/A)
  Location: 'Pologne'  (QID: Q36)

  [ARTICLE TEXT — entity markers added]
  "L' empereur soûtenait, non sans raison, que les états de <PERSON>Matilde</PERSON> lui devaient revenir comme un fief de l' empire ; ainsi les papes combattaient pour le spirituel et pour le temporel. Pascal II n' obtint du roi Philippe que la permission de tenir un concile à Troye. Le gouvernement était trop faible, trop divisé pour lui donner des troupes. Henri V ayant terminé par des traités une guerre de peu de durée contre la <LOCATION>Pologne</LOCATION>, sut tellement intéresser les princes de l' empire à soûtenir ses droits, que ces mêmes princes qui avaient aidé à détroner son pére en vertu des bulles des papes, se réunirent avec lui pour faire annuller dans Rome ces mêmes bulles. Il descend donc des Alpes avec une armée ; et Rome fut encor teinte de sang pour cette querelle de la crosse et de l' anneau. Les traités, les parjures, les excommunications et les meurtres se suivirent avec rapidité. Pascal II ayant solemnellement rendu les investitures avec serment sur l' évangile, fit annuller son serment par es cardinaux ; nouvelle manière de manquer à sa parole. Il se laissa traiter de lâche et de prévaricateur en plein concile, afin d' être forcé à reprendre ce qu' il avait donné. Alors nouvelle irruption de l' empereur à Rome ; car presque jamais ces Césars n' y allèrent que pour des querelles ecclésiastiques, dont la plus grande était le couronnement. Enfin après avoir créé, déposé, chassé, rapellé des papes, Henri V aussi souvent excommunié que son pére, et inquiété comme lui par ses grands vassaux d' Allemagne, fut obligé de terminer la guerre des investitures, en renonçant à cette crosse et à cet anneau. Il fit plus ; il se désista solemnellement du droit que s' étaient attribué les empereurs, ainsi que les rois de France, de nommer aux évêchés, ou d' interposer tellement leur autorité dans les élections, qu' ils en étaient absolument les maîtres. Il fut donc décidé dans un concile tenu à Rome, que les rois ne donneraient plus aux bénéficiers canoniquement élus les investitures par un bâton recourbé, mais par une baguette."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Matilde' and 'Pologne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Matilde' near 'Pologne' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 178 [ID: surprise_test_fr__227]:
  Publication date : 1756
  Language         : fr
  Person  : 'S. Louis'  (QID: Q346)
  Location: 'France'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "En 1255 le pape Alexandre III établit l' inquisition en <LOCATION>France</LOCATION> sous le roi <PERSON>S. Louis</PERSON>. Le gardien des cordeliers de Paris, et le provincial des dominicains, étaient les grands inquisiteurs. Ils devaient, par la bulle d' Alexandre, consulter les évêques, mais ils n' en dépendaient pas. Cette étrange jurisdiction donnée à des hommes qui font voeu de renoncer au monde, indigna le clergé et les laïcs. Un cordelier inquisiteur assista au jugement des templiers ; mais bientôt le soulévement de tous les esprits ne laissa à ces moines qu' un titre inutile. En Italie les papes avaient plus de crédit, parce que tout désobéis qu' ils étaient dans Rome, tout éloignés qu' ils en furent longtems, ils étaient toujours à la tête de la faction guelphe, contre celle des gibelins. Ils se servirent de cette inquisition contre les partisans de l' empire. Car en 1302 le pape Jean XXII fit procéder par des moines inquisiteurs contre Matthieu Visconti seigneur de Milan, dont le crime était d' être attaché à l' empereur Louis De Baviére. Le dévouement du vassal à son suzerain, fut déclaré hérésie ; la maison d' est, celle de Malatesta, furent traitées de même, pour la même cause ; et si le suplice ne suivit pas la sentence, c' est qu' il était alors plus aisé aux papes d' avoir des inquisiteurs que des armées. Plus ce tribunal s' établit, et plus les évêques qui se voyaient enlever un droit qui semblait leur apartenir, le reclamèrent vivement. Les papes les associèrent aux moines inquisiteurs, qui exerçaient pleinement leur autorité dans presque tous les états d' Italie, et dont les évêques ne furent que les assesseurs. Sur la fin du treiziéme siécle en 1289 Venise avait déja reçu l' inquisition ; mais si ailleurs elle était toute dépendante du pape, elle fut dans l' état vénitien soumise au sénat. La plus sage précaution qu' il prit, fut que les amendes et les confiscations n' apartinssent pas aux inquisiteurs."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Louis IX de France
    Description: roi de France de 1226 à 1270 canonisé par l'Église catholique
    Born: ['+1214-04-25T00:00:00Z']
    Died: ['+1270-08-25T00:00:00Z']
    Birth place: ['Poissy']
    Death place: ['Q3572']
  Location Wikidata:
    Label: France
    Description: pays transcontinental au territoire métropolitain situé en Europe de l'Ouest
    Country: ['France']
    Aliases: {'en': ['French Republic'], 'fr': ['République française', 'RF', 'fr', 'la République française', 'Fr.', 'La France', "L'Hexagone"], 'de': ['Französische Republik', 'fr', 'RF']}
    Coordinates: [{'lat': 47, 'lon': 2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (3):
      - "1255" → 1255
      - "1302" → 1302
      - "1289" → 1289
    Temporal signal words: plus, tôt
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 454 days
    OCR quality estimate: 0.991

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'S. Louis' and 'France' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'S. Louis' near 'France' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 179 [ID: surprise_test_fr__244]:
  Publication date : 1797
  Language         : fr
  Person  : 'M Poncel De La Haye'  (QID: N/A)
  Location: 'ouest de la Trinité'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "D' après le rapport de M De Vaujuas et de M Boutin, il était évident que nous ne pouvions trouver à la Trinité l' eau et le bois qui nous manquaient. Je me décidai tout de suite à faire route pour l' île Sainte - Catherine, sur la côte du Brésil : c' était l' ancienne relâche des bâtimens français qui allaient dans la mer du sud. Frézier et l' amiral Anson y trouvèrent abondamment à se pourvoir de tous leurs besoins. Ce fut pour ne pas perdre un seul jour, que je donnai la préférence à l' île Sainte - Catherine sur Rio - Janéïro, où les différentes formalités auraient exigé plus de temps qu' il n' en fallait pour faire l' eau et le bois qui nous manquaient. Mais en dirigeant ma route vers l' île Sainte - Catherine, je voulus m' assurer de l' existence de l' île de l' Ascençaon, que M Daprès place à cent lieues dans l' <LOCATION>ouest de la Trinité</LOCATION>, et à 15 minutes seulement plus sud. Suivant le journal de <PERSON>M Poncel De La Haye</PERSON>, qui commandait la frégate la renommée, j' étais certain que différens navigateurs, entr' autres Frézier, homme très - éclairé, avaient cru aborder à l' Ascençaon, et qu' ils n' avaient été réellement qu' à la Trinité. Malgré l' autorité de M Poncel De La Haye, je crus que ce point de géographie demandait un nouvel éclaircissement. Les deux jours que nous passâmes vers la partie sud de l' île de la Trinité, nous mirent à portée de faire les relèvemens d' après lesquels M Bernizet traça le plan de la partie sud de l' île : il diffère très - peu de celui du docteur Halley, qui m' avait été remis par M De Fleurieu. La vue, peinte par M Duché De Vancy, est d' une vérité si frappante, qu' elle suffira seule pour que les navigateurs qui aborderont dans la partie du sud de la Trinité, ne puissent jamais se tromper."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien, ancienne, plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'M Poncel De La Haye' and 'ouest de la Trinité' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'M Poncel De La Haye' near 'ouest de la Trinité' around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 180 [ID: surprise_test_fr__320]:
  Publication date : 1797
  Language         : fr
  Person  : 'Roggewein'  (QID: Q243375)
  Location: 'île des Chiens'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Il découvre : l' île de Pâque, par 27 degrés 4 minutes de latitude sud, et 265 degrés 42 minutes de longitude orientale du méridien de Ténériffe, suivant l' auteur des vies des gouverneurs de Batavia ; ce qui répond à 113 degrés 18 minutes de longitude à l' ouest du méridien de Paris : île habitée, de seize lieues hollandaises de circuit, et remarquable par des statues ou figures colossales élevées en grand nombre sur ses côtes ; ( elle a été reconnue depuis par Cook, qui l' a trouvée par 27 degrés 5 minutes de latitude, et 112 degrés 6 minutes de longitude à l' ouest de Paris, et qui l' a nommée Easter ou Pâque : elle a été vue aussi en 1770, par les espagnols, qui la placent par 27 degrés 6 minutes de latitude, et 268 degrés 19 minutes de longitude, méridien de Ténériffe, ce qui répond à 110 degrés 41 minutes de notre longitude, à l' ouest de Paris ; ces derniers lui ont donné le nom de San - Carlos ). Charls - Hof, ou cour de Charles, par 15 degrés 45 minutes de latitude sud, et après huit cents lieues de course depuis l' île de Pâque ; ( suivant la relation française de ce voyage, c' est une petite île rase, avec une espèce de lac dans l' intérieur. <PERSON>Roggewein</PERSON> crut que c' était l' <LOCATION>île des Chiens</LOCATION> de Le Maire et Schouten, et la relation hollandaise ne lui assigne ni latitude ni longitude : on l' a placée sur la carte relativement à sa distance des îles Pernicieuses, qui en sont à douze lieues à l' ouest, et dont la position est aujourd'hui connue ). Les îles Pernicieuses, par 14 degrés 41 minutes de latitude sud, et à douze lieues hollandaises à l' ouest de Charls - Hof : ce sont quatre îles basses et peuplées, qui ont depuis quatre jusqu' à dix lieues de tour ; ( Roggewein y perdit un vaisseau, ce qui fit donner le nom de Pernicieuse à l' une de ces îles : deux autres furent appelées les deux Frères, et une autre la Soeur ; il y resta cinq hommes de l' équipage, qui désertèrent et qu' on abandonna."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Jacob Roggeveen
    Description: explorateur néerlandais
    Born: ['+1659-02-01T00:00:00Z']
    Died: ['+1729-01-31T00:00:00Z']
    Birth place: ['Middelbourg']
    Death place: ['Middelbourg']
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1770" → 1770
    Temporal signal words: aujourd'hui, après
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 27 days
    OCR quality estimate: 0.941

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Roggewein' and 'île des Chiens' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Roggewein' near 'île des Chiens' around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 181 [ID: surprise_test_fr__335]:
  Publication date : 1797
  Language         : fr
  Person  : 'San - Carlos'  (QID: N/A)
  Location: 'Ténériffe'  (QID: Q40846)

  [ARTICLE TEXT — entity markers added]
  "Il découvre : l' île de Pâque, par 27 degrés 4 minutes de latitude sud, et 265 degrés 42 minutes de longitude orientale du méridien de <LOCATION>Ténériffe</LOCATION>, suivant l' auteur des vies des gouverneurs de Batavia ; ce qui répond à 113 degrés 18 minutes de longitude à l' ouest du méridien de Paris : île habitée, de seize lieues hollandaises de circuit, et remarquable par des statues ou figures colossales élevées en grand nombre sur ses côtes ; ( elle a été reconnue depuis par Cook, qui l' a trouvée par 27 degrés 5 minutes de latitude, et 112 degrés 6 minutes de longitude à l' ouest de Paris, et qui l' a nommée Easter ou Pâque : elle a été vue aussi en 1770, par les espagnols, qui la placent par 27 degrés 6 minutes de latitude, et 268 degrés 19 minutes de longitude, méridien de Ténériffe, ce qui répond à 110 degrés 41 minutes de notre longitude, à l' ouest de Paris ; ces derniers lui ont donné le nom de <PERSON>San - Carlos</PERSON> ). Charls - Hof, ou cour de Charles, par 15 degrés 45 minutes de latitude sud, et après huit cents lieues de course depuis l' île de Pâque ; ( suivant la relation française de ce voyage, c' est une petite île rase, avec une espèce de lac dans l' intérieur. Roggewein crut que c' était l' île des Chiens de Le Maire et Schouten, et la relation hollandaise ne lui assigne ni latitude ni longitude : on l' a placée sur la carte relativement à sa distance des îles Pernicieuses, qui en sont à douze lieues à l' ouest, et dont la position est aujourd'hui connue ). Les îles Pernicieuses, par 14 degrés 41 minutes de latitude sud, et à douze lieues hollandaises à l' ouest de Charls - Hof : ce sont quatre îles basses et peuplées, qui ont depuis quatre jusqu' à dix lieues de tour ; ( Roggewein y perdit un vaisseau, ce qui fit donner le nom de Pernicieuse à l' une de ces îles : deux autres furent appelées les deux Frères, et une autre la Soeur ; il y resta cinq hommes de l' équipage, qui désertèrent et qu' on abandonna."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Ténérife
    Description: île de l'archipel des îles Canaries
    Country: ['Espagne']
    Located in: ['province de Santa Cruz de Ténérife']
    Aliases: {'en': ['Teneriffe', 'Island of Tenerife', 'Island of Teneriffe', 'Nivaria'], 'fr': ['Ténériffe', 'Pluitalia', 'Île de Ténérife', 'Nivaria', 'Tenerife', 'Teneriffe'], 'de': ['Tenerife', 'Insel des ewigen Frühlings']}
    Coordinates: [{'lat': 28.268611111111, 'lon': -16.605555555556}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1770" → 1770
    Temporal signal words: aujourd'hui, après
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 27 days
    OCR quality estimate: 0.941

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'San - Carlos' and 'Ténériffe' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'San - Carlos' near 'Ténériffe' around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 182 [ID: surprise_test_fr__342]:
  Publication date : 1756
  Language         : fr
  Person  : 'Philippe'  (QID: N/A)
  Location: 'Leyde'  (QID: Q43631)

  [ARTICLE TEXT — entity markers added]
  "Le siége et la défense de <LOCATION>Leyde</LOCATION> sont un des plus grands témoignages de ce que peuvent la constance et la liberté. Les hollandais firent précisément la même chose qu' on leur a vû hazarder en 1672 lorsque Louis XIV était aux portes d' Amsterdam ; ils percèrent les digues ; les eaux de l' Issel, de la Meuse, et de l' océan inondèrent les campagnes ; et une flotte de deux - cent bateaux aporta du secours dans la ville par - dessus les ouvrages des espagnols. Il y eut un autre prodige ; c' est que les assiégeans osèrent continuer le siége et entreprendre de saigner cette vaste inondation. Il n' y avait point d' exemple dans l' histoire ni d' une telle ressource dans des assiégés, ni d' une telle opiniâtreté dans des assiégeans ; mais cette opiniâtreté fut inutile, et Leyde célèbre encor aujourdhui tous les ans le jour de sa délivrance. Il ne faut pas oublier que les habitans se servirent de pigeons dans ce siége pour donner des nouvelles au prince d' Orange : c' est une pratique commune en Asie. Quel était donc ce gouvernement si sage et si vanté de <PERSON>Philippe</PERSON> II lorsqu' on voit dans ce tems -là même ses troupes se mutiner en Flandre faute de payement, saccager la ville d' Anvers, et que toutes les provinces des Pays - Bas, sans consulter ni lui, ni son gouverneur, font un traité de pacification avec les révoltés, publient une amnistie, rendent les prisonniers, font démolir des forteresses, et ordonnent qu' on abattra la fameuse statue du duc d' Albe, trophée que son orgueil avait élevé à sa cruauté, et qui était encor debout dans la citadelle d' Anvers, dont le roi était le maître ? Après la mort du grand commandeur de Requesens, Philippe qui pouvait encor essayer de remettre le calme dans les Pays - Bas par sa présence, y envoye Don Juan D' Autriche son frére, prince célèbre dans l' Europe par la fameuse victoire de Lépante remportée sur les turcs, et par son ambition qui lui avait fait tenter d' être roi de Tunis. Philippe n' aimait pas Don Juan ; il craignait sa gloire, et se défiait de ses desseins."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Leyde
    Description: commune néerlandaise en Hollande-Méridionale
    Country: ['Pays-Bas', 'Provinces-Unies']
    Located in: ['comté de Hollande', 'Q694']
    Aliases: {'en': ['Leyden'], 'fr': ['Leiden', 'Leyden', 'Leide'], 'de': ['Leyden']}
    Coordinates: [{'lat': 52.16, 'lon': 4.49}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1672" → 1672
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 84 days
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Philippe' and 'Leyde' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Philippe' near 'Leyde' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 183 [ID: surprise_test_fr__352]:
  Publication date : 1756
  Language         : fr
  Person  : 'Cosme De Médicis'  (QID: N/A)
  Location: 'Europe'  (QID: Q46)

  [ARTICLE TEXT — entity markers added]
  "Il n' y eut que l' arriére - ban, composé des arrière - petits vassaux, qui resta sujet encor à servir dans les occasions. On s' étonne qu' après tant de désastres la France eût tant de ressources et d' argent. Mais un pays riche par ses denrées, ne cesse jamais de l' être, quand la culture n' est pas abandonnée. Les guerres civiles ébranlent le corps de l' état, et ne le détruisent point. Les meurtres et les saccagements, qui désolent des familles, en enrichissent d' autres. Les négocians deviennent d' autant plus habiles qu' il faut plus d' art pour se sauver parmi tant d' orages. Jacques Coeur en est un grand exemple. Il avait établi le plus grand commerce qu' aucun particulier de l' <LOCATION>Europe</LOCATION> eût jamais embrassé. Il n' y eut depuis lui que <PERSON>Cosme De Médicis</PERSON> qui l' égalât. Jacques Coeur avait trois - cent facteurs en Italie et dans le levant. Il prêta deux - cent - mille écus d' or au roi, sans quoi on n' aurait jamais repris la Normandie. Son industrie était plus utile pendant la paix, que Dunois et la pucelle ne l' avaient été pendant la guerre. C' est une grande tache peut - être à la mémoire de Charles VII qu' on ait persécuté un homme si nécessaire. On n' en sait point le sujet : car qui sait les secrets ressorts des fautes, et des injustices des hommes. Le roi le fit mettre en prison, et le parlement lui fit son procès. On ne put rien prouver, contre lui, sinon qu' il avait fait rendre à un turc un esclave chrêtien, lequel avait quitté et trahi son maître, et qu' il avait fait vendre des armes au soudan d' égypte. Sur ces deux actions, dont l' une était permise, et l' autre vertueuse, il fut condamné à perdre ses biens. Il trouva dans ses commis plus de droiture que dans les courtisans qui l' avaient perdu. Ils se cotisèrent presque tous pour l' aider dans sa disgrace. Jacques Coeur alla continuer son commerce en Chypre, et n' eut jamais le courage de revenir dans son ingrate patrie, quoiqu' il y fût rapellé."

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
    Temporal signal words: plus, né à, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Cosme De Médicis' and 'Europe' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Cosme De Médicis' near 'Europe' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 184 [ID: surprise_test_fr__364]:
  Publication date : 1756
  Language         : fr
  Person  : 'Charles VII'  (QID: N/A)
  Location: 'Europe'  (QID: Q46)

  [ARTICLE TEXT — entity markers added]
  "Il n' y eut que l' arriére - ban, composé des arrière - petits vassaux, qui resta sujet encor à servir dans les occasions. On s' étonne qu' après tant de désastres la France eût tant de ressources et d' argent. Mais un pays riche par ses denrées, ne cesse jamais de l' être, quand la culture n' est pas abandonnée. Les guerres civiles ébranlent le corps de l' état, et ne le détruisent point. Les meurtres et les saccagements, qui désolent des familles, en enrichissent d' autres. Les négocians deviennent d' autant plus habiles qu' il faut plus d' art pour se sauver parmi tant d' orages. Jacques Coeur en est un grand exemple. Il avait établi le plus grand commerce qu' aucun particulier de l' <LOCATION>Europe</LOCATION> eût jamais embrassé. Il n' y eut depuis lui que Cosme De Médicis qui l' égalât. Jacques Coeur avait trois - cent facteurs en Italie et dans le levant. Il prêta deux - cent - mille écus d' or au roi, sans quoi on n' aurait jamais repris la Normandie. Son industrie était plus utile pendant la paix, que Dunois et la pucelle ne l' avaient été pendant la guerre. C' est une grande tache peut - être à la mémoire de <PERSON>Charles VII</PERSON> qu' on ait persécuté un homme si nécessaire. On n' en sait point le sujet : car qui sait les secrets ressorts des fautes, et des injustices des hommes. Le roi le fit mettre en prison, et le parlement lui fit son procès. On ne put rien prouver, contre lui, sinon qu' il avait fait rendre à un turc un esclave chrêtien, lequel avait quitté et trahi son maître, et qu' il avait fait vendre des armes au soudan d' égypte. Sur ces deux actions, dont l' une était permise, et l' autre vertueuse, il fut condamné à perdre ses biens. Il trouva dans ses commis plus de droiture que dans les courtisans qui l' avaient perdu. Ils se cotisèrent presque tous pour l' aider dans sa disgrace. Jacques Coeur alla continuer son commerce en Chypre, et n' eut jamais le courage de revenir dans son ingrate patrie, quoiqu' il y fût rapellé."

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
    Temporal signal words: plus, né à, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Charles VII' and 'Europe' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Charles VII' near 'Europe' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 185 [ID: surprise_test_fr__368]:
  Publication date : 1678
  Language         : fr
  Person  : 'Hugues Capet'  (QID: Q159575)
  Location: 'Bourgogne'  (QID: Q1173)

  [ARTICLE TEXT — entity markers added]
  "Il est vray que ces renoncemens doivent avoir quelque cause legitime, et que les rois feroient tort à leurs successeurs, s' ils retranchoient une province du corps de l' etat sans y être contraints, ou sans y trouver de grands avantages. Mais lors qu' ils ne consentent à ces retranchemens que par necessité, ou pour le bien et l' utilité du royaume, leurs successeurs n' ont aucun sujet de se plaindre d' eux ; et s' ils en ont, la plupart de nos rois auroient eu droit de se plaindre de leurs predecesseurs, particulierement les enfans de Henry Ii qui par le traité de château Cambresy, relâcha et rendit près de deux cens villes ou forteresses. Il faut ajoutter à cela qu' il est difficile de marquer ce point de grandeur dont parle l' auteur qu' on a cité, où les etats étant parvenus, il n' est plus permis aux rois d' en retrancher aucune partie ; parce qu' il ne s' est jamais passé de temps considerable depuis l' établissement de la monarchie, que la France ne se soit accruë par les conquêtes de nos rois, ou n' ait diminué par celles de nos voisins. De plus, les rois de la premiere et seconde race luy ont très - souvent ôté sa grandeur, la partageant entre leurs enfans, et divisant le royaume en plusieurs royaumes. Enfin pour ne pas alleguer toutes les provinces qui ont été desunies de la couronne, il suffit de dire que la <LOCATION>Bourgogne</LOCATION> l' avoit été par le roy Henry, petit fils de <PERSON>Hugues Capet</PERSON>, en faveur de Robert son frere ; qu' elle y revint sous le roy Jean, qui la donna peu de temps après à Philippe Le Hardy son quatriéme fils ; et qu' après la mort de Charles dernier Duc de Bourgogne, Loüis XI s' en rendit le maître ; de sorte qu' il n' y avoit pas cinquante ans qu' elle étoit réünie à la couronne lorsque François I la voulut ceder. Passons maintenant aux autres pretextes qu' on prend pour se dispenser de la fidelité qu' on doit aux souverains."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Hugues Capet
    Description: roi des Francs de 987 à 996, fondateur de la dynastie capétienne
    Born: ['+0940-01-01T00:00:00Z']
    Died: ['+0996-10-24T00:00:00Z']
    Birth place: ['Dourdan']
    Death place: ['Q1820536']
  Location Wikidata:
    Label: Bourgogne
    Description: ancienne région administrative française
    Country: ['Q142']
    Located in: ['Bourgogne-Franche-Comté', 'France métropolitaine']
    Aliases: {'en': ['Bourgogne']}
    Coordinates: [{'lat': 47, 'lon': 4.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: maintenant, plus, après, avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Hugues Capet' and 'Bourgogne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Hugues Capet' near 'Bourgogne' around 1678?
  4. Resolve temporal expressions relative to 1678. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 186 [ID: surprise_test_fr__372]:
  Publication date : 1678
  Language         : fr
  Person  : 'roy Jean'  (QID: N/A)
  Location: 'Bourgogne'  (QID: Q1173)

  [ARTICLE TEXT — entity markers added]
  "Il est vray que ces renoncemens doivent avoir quelque cause legitime, et que les rois feroient tort à leurs successeurs, s' ils retranchoient une province du corps de l' etat sans y être contraints, ou sans y trouver de grands avantages. Mais lors qu' ils ne consentent à ces retranchemens que par necessité, ou pour le bien et l' utilité du royaume, leurs successeurs n' ont aucun sujet de se plaindre d' eux ; et s' ils en ont, la plupart de nos rois auroient eu droit de se plaindre de leurs predecesseurs, particulierement les enfans de Henry Ii qui par le traité de château Cambresy, relâcha et rendit près de deux cens villes ou forteresses. Il faut ajoutter à cela qu' il est difficile de marquer ce point de grandeur dont parle l' auteur qu' on a cité, où les etats étant parvenus, il n' est plus permis aux rois d' en retrancher aucune partie ; parce qu' il ne s' est jamais passé de temps considerable depuis l' établissement de la monarchie, que la France ne se soit accruë par les conquêtes de nos rois, ou n' ait diminué par celles de nos voisins. De plus, les rois de la premiere et seconde race luy ont très - souvent ôté sa grandeur, la partageant entre leurs enfans, et divisant le royaume en plusieurs royaumes. Enfin pour ne pas alleguer toutes les provinces qui ont été desunies de la couronne, il suffit de dire que la <LOCATION>Bourgogne</LOCATION> l' avoit été par le roy Henry, petit fils de Hugues Capet, en faveur de Robert son frere ; qu' elle y revint sous le <PERSON>roy Jean</PERSON>, qui la donna peu de temps après à Philippe Le Hardy son quatriéme fils ; et qu' après la mort de Charles dernier Duc de Bourgogne, Loüis XI s' en rendit le maître ; de sorte qu' il n' y avoit pas cinquante ans qu' elle étoit réünie à la couronne lorsque François I la voulut ceder. Passons maintenant aux autres pretextes qu' on prend pour se dispenser de la fidelité qu' on doit aux souverains."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: maintenant, plus, après, avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'roy Jean' and 'Bourgogne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'roy Jean' near 'Bourgogne' around 1678?
  4. Resolve temporal expressions relative to 1678. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 187 [ID: surprise_test_fr__384]:
  Publication date : 1756
  Language         : fr
  Person  : 'Henri'  (QID: N/A)
  Location: 'France'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "Ce qu' il y a de plus singulier, c' est qu' Urbain II qui prononça cette sentence, la prononça dans les propres états du roi, à Clermont en Auvergne, où il venait chercher un azile, et dans ce même concile où nous verrons qu' il prêcha la croisade. Cependant il ne paraît point que Philippe excommunié ait été en horreur à ses sujets ; c' est une raison de plus pour douter de cet abandon général où l'on dit que le roi Robert avait été réduit. Ce qu' il y eut d' assez remarquable, c' est le mariage du roi <PERSON>Henri</PERSON> pére de Philippe avec une princesse moscovite. Les moscovites ou russes commençaient à être chrêtiens ; mais ils n' avaient aucun commerce avec le reste de l' Europe. Ils habitaient au - delà de la Pologne, à peine chrêtienne elle -même, et sans aucune correspondance avec la <LOCATION>France</LOCATION>. Cependant le roi Henri envoya jusqu' en Russie demander la fille du souverain, à qui les autres européans donnaient le titre de duc, aussi - bien qu' au chef de la Pologne. Les russes le nommaient dans leur langage tzaar, dont on a fait depuis le mot de czar. On prétend que Henri se détermina à ce mariage, dans la crainte d' essuyer des querelles ecclesiastiques. De toutes les superstitions de ces tems -là, ce n' était pas la moins nuisible au bien des états, que celle de ne pouvoir épouser sa parente au septiéme degré. Presque tous les souverains de l' Europe étaient parens de Henri. Quoi qu' il en soit, Anne fille de Jaraslau czar de Moscovie fut reine de France ; et il est à remarquer qu' après la mort de son mari, elle n' eut point la régence, et n' y prétendit point. Les loix changent selon les tems. Ce fut le comte de Flandres, un des vassaux du royaume, qui en fut régent. La reine veuve se remaria à un comte de Crepi. Tout cela serait singulier aujourdhui, et ne le fut point alors. Ni Henri, ni Philippe I ne firent rien de mémorable ; mais de leur tems leurs vassaux et arrière - vassaux conquirent des royaumes."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Henri' and 'France' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Henri' near 'France' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 188 [ID: surprise_test_fr__388]:
  Publication date : 1756
  Language         : fr
  Person  : 'Urbain II'  (QID: Q30578)
  Location: 'Auvergne'  (QID: Q1152)

  [ARTICLE TEXT — entity markers added]
  "Ce qu' il y a de plus singulier, c' est qu' <PERSON>Urbain II</PERSON> qui prononça cette sentence, la prononça dans les propres états du roi, à Clermont en <LOCATION>Auvergne</LOCATION>, où il venait chercher un azile, et dans ce même concile où nous verrons qu' il prêcha la croisade. Cependant il ne paraît point que Philippe excommunié ait été en horreur à ses sujets ; c' est une raison de plus pour douter de cet abandon général où l'on dit que le roi Robert avait été réduit. Ce qu' il y eut d' assez remarquable, c' est le mariage du roi Henri pére de Philippe avec une princesse moscovite. Les moscovites ou russes commençaient à être chrêtiens ; mais ils n' avaient aucun commerce avec le reste de l' Europe. Ils habitaient au - delà de la Pologne, à peine chrêtienne elle -même, et sans aucune correspondance avec la France. Cependant le roi Henri envoya jusqu' en Russie demander la fille du souverain, à qui les autres européans donnaient le titre de duc, aussi - bien qu' au chef de la Pologne. Les russes le nommaient dans leur langage tzaar, dont on a fait depuis le mot de czar. On prétend que Henri se détermina à ce mariage, dans la crainte d' essuyer des querelles ecclesiastiques. De toutes les superstitions de ces tems -là, ce n' était pas la moins nuisible au bien des états, que celle de ne pouvoir épouser sa parente au septiéme degré. Presque tous les souverains de l' Europe étaient parens de Henri. Quoi qu' il en soit, Anne fille de Jaraslau czar de Moscovie fut reine de France ; et il est à remarquer qu' après la mort de son mari, elle n' eut point la régence, et n' y prétendit point. Les loix changent selon les tems. Ce fut le comte de Flandres, un des vassaux du royaume, qui en fut régent. La reine veuve se remaria à un comte de Crepi. Tout cela serait singulier aujourdhui, et ne le fut point alors. Ni Henri, ni Philippe I ne firent rien de mémorable ; mais de leur tems leurs vassaux et arrière - vassaux conquirent des royaumes."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Urbain II
    Description: 159e pape de l'Église catholique, de 1088 à 1099
    Born: ['+1035-00-00T00:00:00Z']
    Died: ['+1099-07-29T00:00:00Z']
    Birth place: ['Châtillon-sur-Marne', 'château de Lagery']
    Death place: ['Q220']
    Work locations: ['Rome', 'États pontificaux']
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Urbain II' and 'Auvergne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Urbain II' near 'Auvergne' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 189 [ID: surprise_test_fr__404]:
  Publication date : 1561
  Language         : fr
  Person  : 'Villeneufve'  (QID: N/A)
  Location: 'pont du Rosne'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Misser Iuliano commanda à Torneto de la prendre, & de la mener chez luy en l' estable. Là ou elle se rengea aussi proprement, comme si elle n' en eust jamais bougé. Il la fit ramener le lendemain en la mesme place, pour veoir si quelqu' un la vendiqueroit. Mais il ne venoit personne, dont il fut fort esbahy : & pensoit que ce fust quelque esprit qui l' eust ramenee. De là à quelque temps maistre Arnaud s' addresse à misser Iuliano, lequel il trouva monté sus sa hacquenee, & luy dit : monsieur, je suis fort aise de savoir que ceste hacquenee soit à vous. Car asseurez vous qu' elle est bonne : je l' ay essayee, il y ha environ un an que je la trouvay pres du <LOCATION>pont du Rosne</LOCATION>, qu' elle s' en alloit toute seule, & qu' un garson la vouloit prendre. Mais congnoissant à sa façon qu' elle n' estoit pas sienne, je la luy ostay : & la garday un jour ou deux sans pouvoir savoir à qui elle estoit. Le troisiesme jour je la menay jusques à <PERSON>Villeneufve</PERSON>, ou j' ouy dire qu' un gentilhomme François la cherchoit, & qu' il luy avoit esté dit qu' on l' avoit veue emmener par un garson sus le chemin de Paris. Le gentilhomme alloit apres. Et moy sachant celà, je picque apres luy pour la luy rendre : mais je ne le peu jamais atteindre. Car il alloit grand train pour atteindre son larron. Et allay tant en le cherchant, que je me trouvay jusqu' en Lorraine. Là ou voyant que je n' oyois point de nouvelles de ce gentilhomme, je la garday long temps. Et à la fin m' en suis revenu en ceste ville, ou je l' avoys prise : & ay trouvé par quelques uns de mes amis, qu' il se souvenoit bien l' avoir veue autrefois en ceste ville : mais qu' il ne savoit à qui, sinon que ce fust à quelqu' un de vous autres messieurs de la legation. Sachant celà, je l' ay fait mener en la place du Palais, affin que celuy à qui elle estoit la peust appercevoir. Et ce pendant je m' en estois allé d' icy à Nimes, d' ou je suis retourné depuis deux jours. Mais Dieu soit loué qu' elle ha retrouvé son maistre. Car j' en estois en grand peine."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Villeneufve' and 'pont du Rosne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Villeneufve' near 'pont du Rosne' around 1561?
  4. Resolve temporal expressions relative to 1561. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 190 [ID: surprise_test_fr__449]:
  Publication date : 1666
  Language         : fr
  Person  : 'Monsieur De Turenne'  (QID: N/A)
  Location: 'Châlons'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Réponse du Comte De Bussy à Madame De S. à Chaseu, ce 1 septembre 1675. En me disant que vos lettres ne sont pas dignes de mon approbation, madame, vous m' en écrivez une qui en merite une plus grande, sans compter votre modestie. Mais pour ne la pas offenser davantage, je vais traiter d' autre chose avec vous. Ce qu' a dit monsieur le prince de <PERSON>Monsieur De Turenne</PERSON> en passant à <LOCATION>Châlons</LOCATION>, me paroît d' un fort honnête homme, et d' un homme qui sent bien son merite. Monsieur De Montecuculi se précautionnera encore davantage avec lui qu' il ne faisoit avec Monsieur De Turenne. Il est vrai que le Chevalier De G a été heureux au combat d' Altenhein ; et la trousse à celui de Consarbricq. Je m' en réjouis avec vous, et j' espere vous faire un même compliment pour monsieur vôtre fils à la fin de cette campagne. Vous devriez me conter le procès dont il est question. Je suis tellement affamé de vous entendre, que je vous donnerois une favorable audience quand vous ne me parleriez que d' interlocutoires et d' arrêts. Lettre 61. Réponse du Comte De Bussy à Madame De S. à Chaseu, ce 29 octobre 1675. Je reçus hier vôtre lettre, madame, qui me donna la joie que vos lettres ont accoutumé de me donner. Enfin voilà vôtre niéce sur le point de passer le pas ; elle va trouver ce qu' elle cherchoit. à propos de chercher, ceci me fait souvenir du pauvre Chevalier De Rohan, qui ayant rencontré un soir bien tard à Fontainebleau, Madame D' seule qui passoit dans une galerie, lui demanda ce qu' elle cherchoit : rien, dit -elle. Ma foi, madame, lui répondit -il, je ne voudrois pas avoir perdu ce que vous cherchez. Voilà mon petit conte, madame. Vous m' avez permis d' en faire un aussi, je me sers de la liberté que vous m' avez donnée. J' ai trouvé le vôtre plaisant au dernier point, et je m' en sçai bon gré, car il faut avoir de l' esprit pour trouver cela aussi plaisant qu' il est."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1675" → 1675
      - "1675" → 1675
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 9 days
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Monsieur De Turenne' and 'Châlons' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Monsieur De Turenne' near 'Châlons' around 1666?
  4. Resolve temporal expressions relative to 1666. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 191 [ID: surprise_test_fr__461]:
  Publication date : 1666
  Language         : fr
  Person  : 'monsieur le prince'  (QID: N/A)
  Location: 'Chaseu'  (QID: Q2968914)

  [ARTICLE TEXT — entity markers added]
  "Réponse du Comte De Bussy à Madame De S. à <LOCATION>Chaseu</LOCATION>, ce 1 septembre 1675. En me disant que vos lettres ne sont pas dignes de mon approbation, madame, vous m' en écrivez une qui en merite une plus grande, sans compter votre modestie. Mais pour ne la pas offenser davantage, je vais traiter d' autre chose avec vous. Ce qu' a dit <PERSON>monsieur le prince</PERSON> de Monsieur De Turenne en passant à Châlons, me paroît d' un fort honnête homme, et d' un homme qui sent bien son merite. Monsieur De Montecuculi se précautionnera encore davantage avec lui qu' il ne faisoit avec Monsieur De Turenne. Il est vrai que le Chevalier De G a été heureux au combat d' Altenhein ; et la trousse à celui de Consarbricq. Je m' en réjouis avec vous, et j' espere vous faire un même compliment pour monsieur vôtre fils à la fin de cette campagne. Vous devriez me conter le procès dont il est question. Je suis tellement affamé de vous entendre, que je vous donnerois une favorable audience quand vous ne me parleriez que d' interlocutoires et d' arrêts. Lettre 61. Réponse du Comte De Bussy à Madame De S. à Chaseu, ce 29 octobre 1675. Je reçus hier vôtre lettre, madame, qui me donna la joie que vos lettres ont accoutumé de me donner. Enfin voilà vôtre niéce sur le point de passer le pas ; elle va trouver ce qu' elle cherchoit. à propos de chercher, ceci me fait souvenir du pauvre Chevalier De Rohan, qui ayant rencontré un soir bien tard à Fontainebleau, Madame D' seule qui passoit dans une galerie, lui demanda ce qu' elle cherchoit : rien, dit -elle. Ma foi, madame, lui répondit -il, je ne voudrois pas avoir perdu ce que vous cherchez. Voilà mon petit conte, madame. Vous m' avez permis d' en faire un aussi, je me sers de la liberté que vous m' avez donnée. J' ai trouvé le vôtre plaisant au dernier point, et je m' en sçai bon gré, car il faut avoir de l' esprit pour trouver cela aussi plaisant qu' il est."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No relevant Wikidata properties found.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1675" → 1675
      - "1675" → 1675
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 9 days
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'monsieur le prince' and 'Chaseu' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'monsieur le prince' near 'Chaseu' around 1666?
  4. Resolve temporal expressions relative to 1666. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 192 [ID: surprise_test_fr__3]:
  Publication date : 1756
  Language         : fr
  Person  : 'Photius'  (QID: N/A)
  Location: 'Rome'  (QID: Q220)

  [ARTICLE TEXT — entity markers added]
  "Le pape Jean VIII le reçut à sa communion, le reconnut, lui écrivit ; et malgré ce huitiéme concile oecuménique, qui avait anathématisé ce patriarche, le pape envoya ses légats à un autre concile à Constantinople, dans lequel <PERSON>Photius</PERSON> fut reconnu innocent par quatre - cent évêques, dont trois - cent l' avaient auparavant condamné. Les légats de ce même siége de <LOCATION>Rome</LOCATION>, qui l' avaient anathématisé, servirent eux -mêmes à casser le huitiéme concile oecuménique. Combien tout change chez les hommes ! Combien ce qui était faux, devient vrai selon les tems ! Les légats de Jean VIII s' écrient en plein concile ; si quelqu' un ne reconnait pas Photius, que son partage soit avec Judas. le concile s' écrie, longues années au patriarche Photius, et au patriarche Jean. enfin à la suite des actes du concile on voit une lettre du pape à ce savant patriarche, dans laquelle il lui dit ; nous pensons comme vous... etc. il est donc clair que l' église romaine et la grecque pensaient alors différemment de ce qu' on pense aujourdhui. Il arriva depuis que Rome adopta la procession du pére et du fils ; et il arriva même qu' en 1274 l' empereur des grecs, Michel Paléologue, implorant contre les turcs une nouvelle croisade, envoya au second concile de Lyon, son patriarche et son chancelier, qui chantèrent avec le concile en latin, qui ex patre filioque procedit. mais l' église grecque retourna encor à son opinion, et sembla la quitter encor dans la réunion passagère qui se fit avec Eugène IV. Que les hommes aprennent de là à se tolerer les uns les autres. Voilà des variations et des disputes sur un point fondamental, qui n' ont ni excité de troubles, ni rempli les prisons, ni allumé les buchers. On a blâmé les déférences du pape Jean VIII pour le patriarche Photius ; on n' a pas assez songé que ce pontife avait alors besoin de l' empereur Basile. Un roi de Bulgarie, nommé Bogoris, gagné par l' habileté de sa femme qui était chrêtienne, s' était converti, à l' exemple de Clovis et du roi Egbert."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Rome
    Description: capitale de l'Italie
    Country: ['Italie', 'États pontificaux', "royaume d'Italie", 'royaume des Ostrogoths', 'Empire byzantin', "royaume d'Italie", 'royaume de Rome', 'République romaine', 'Empire romain', "Empire romain d'Occident", 'Vatican']
    Located in: ['province de Rome', 'États pontificaux', 'Rome', 'Rome antique', 'République romaine', 'Empire romain', "Empire romain d'Occident", 'ville métropolitaine de Rome Capitale', 'circle of Rome']
    Aliases: {'en': ['The Eternal City', 'Roma', 'Rome, Italy', 'City of Seven Hills'], 'fr': ['La ville éternelle', 'La ville aux sept collines', 'Roma', "l'Urbs"], 'de': ['Die Ewige Stadt', 'Roma'], 'lb': ['Roma', "D'Éiweg Stad"]}
    Coordinates: [{'lat': 41.893055555556, 'lon': 12.482777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1274" → 1274
    Temporal signal words: avant
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 482 days
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Photius' and 'Rome' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Photius' near 'Rome' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 193 [ID: surprise_test_fr__5]:
  Publication date : 1756
  Language         : fr
  Person  : 'Jean VIII'  (QID: N/A)
  Location: 'Rome'  (QID: Q220)

  [ARTICLE TEXT — entity markers added]
  "Le pape <PERSON>Jean VIII</PERSON> le reçut à sa communion, le reconnut, lui écrivit ; et malgré ce huitiéme concile oecuménique, qui avait anathématisé ce patriarche, le pape envoya ses légats à un autre concile à Constantinople, dans lequel Photius fut reconnu innocent par quatre - cent évêques, dont trois - cent l' avaient auparavant condamné. Les légats de ce même siége de <LOCATION>Rome</LOCATION>, qui l' avaient anathématisé, servirent eux -mêmes à casser le huitiéme concile oecuménique. Combien tout change chez les hommes ! Combien ce qui était faux, devient vrai selon les tems ! Les légats de Jean VIII s' écrient en plein concile ; si quelqu' un ne reconnait pas Photius, que son partage soit avec Judas. le concile s' écrie, longues années au patriarche Photius, et au patriarche Jean. enfin à la suite des actes du concile on voit une lettre du pape à ce savant patriarche, dans laquelle il lui dit ; nous pensons comme vous... etc. il est donc clair que l' église romaine et la grecque pensaient alors différemment de ce qu' on pense aujourdhui. Il arriva depuis que Rome adopta la procession du pére et du fils ; et il arriva même qu' en 1274 l' empereur des grecs, Michel Paléologue, implorant contre les turcs une nouvelle croisade, envoya au second concile de Lyon, son patriarche et son chancelier, qui chantèrent avec le concile en latin, qui ex patre filioque procedit. mais l' église grecque retourna encor à son opinion, et sembla la quitter encor dans la réunion passagère qui se fit avec Eugène IV. Que les hommes aprennent de là à se tolerer les uns les autres. Voilà des variations et des disputes sur un point fondamental, qui n' ont ni excité de troubles, ni rempli les prisons, ni allumé les buchers. On a blâmé les déférences du pape Jean VIII pour le patriarche Photius ; on n' a pas assez songé que ce pontife avait alors besoin de l' empereur Basile. Un roi de Bulgarie, nommé Bogoris, gagné par l' habileté de sa femme qui était chrêtienne, s' était converti, à l' exemple de Clovis et du roi Egbert."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Rome
    Description: capitale de l'Italie
    Country: ['Italie', 'États pontificaux', "royaume d'Italie", 'royaume des Ostrogoths', 'Empire byzantin', "royaume d'Italie", 'royaume de Rome', 'République romaine', 'Empire romain', "Empire romain d'Occident", 'Vatican']
    Located in: ['province de Rome', 'États pontificaux', 'Rome', 'Rome antique', 'République romaine', 'Empire romain', "Empire romain d'Occident", 'ville métropolitaine de Rome Capitale', 'circle of Rome']
    Aliases: {'en': ['The Eternal City', 'Roma', 'Rome, Italy', 'City of Seven Hills'], 'fr': ['La ville éternelle', 'La ville aux sept collines', 'Roma', "l'Urbs"], 'de': ['Die Ewige Stadt', 'Roma'], 'lb': ['Roma', "D'Éiweg Stad"]}
    Coordinates: [{'lat': 41.893055555556, 'lon': 12.482777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1274" → 1274
    Temporal signal words: avant
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 482 days
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Jean VIII' and 'Rome' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Jean VIII' near 'Rome' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 194 [ID: surprise_test_fr__8]:
  Publication date : 1756
  Language         : fr
  Person  : 'empereur Basile'  (QID: N/A)
  Location: 'Rome'  (QID: Q220)

  [ARTICLE TEXT — entity markers added]
  "Le pape Jean VIII le reçut à sa communion, le reconnut, lui écrivit ; et malgré ce huitiéme concile oecuménique, qui avait anathématisé ce patriarche, le pape envoya ses légats à un autre concile à Constantinople, dans lequel Photius fut reconnu innocent par quatre - cent évêques, dont trois - cent l' avaient auparavant condamné. Les légats de ce même siége de <LOCATION>Rome</LOCATION>, qui l' avaient anathématisé, servirent eux -mêmes à casser le huitiéme concile oecuménique. Combien tout change chez les hommes ! Combien ce qui était faux, devient vrai selon les tems ! Les légats de Jean VIII s' écrient en plein concile ; si quelqu' un ne reconnait pas Photius, que son partage soit avec Judas. le concile s' écrie, longues années au patriarche Photius, et au patriarche Jean. enfin à la suite des actes du concile on voit une lettre du pape à ce savant patriarche, dans laquelle il lui dit ; nous pensons comme vous... etc. il est donc clair que l' église romaine et la grecque pensaient alors différemment de ce qu' on pense aujourdhui. Il arriva depuis que Rome adopta la procession du pére et du fils ; et il arriva même qu' en 1274 l' empereur des grecs, Michel Paléologue, implorant contre les turcs une nouvelle croisade, envoya au second concile de Lyon, son patriarche et son chancelier, qui chantèrent avec le concile en latin, qui ex patre filioque procedit. mais l' église grecque retourna encor à son opinion, et sembla la quitter encor dans la réunion passagère qui se fit avec Eugène IV. Que les hommes aprennent de là à se tolerer les uns les autres. Voilà des variations et des disputes sur un point fondamental, qui n' ont ni excité de troubles, ni rempli les prisons, ni allumé les buchers. On a blâmé les déférences du pape Jean VIII pour le patriarche Photius ; on n' a pas assez songé que ce pontife avait alors besoin de l' <PERSON>empereur Basile</PERSON>. Un roi de Bulgarie, nommé Bogoris, gagné par l' habileté de sa femme qui était chrêtienne, s' était converti, à l' exemple de Clovis et du roi Egbert."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Rome
    Description: capitale de l'Italie
    Country: ['Italie', 'États pontificaux', "royaume d'Italie", 'royaume des Ostrogoths', 'Empire byzantin', "royaume d'Italie", 'royaume de Rome', 'République romaine', 'Empire romain', "Empire romain d'Occident", 'Vatican']
    Located in: ['province de Rome', 'États pontificaux', 'Rome', 'Rome antique', 'République romaine', 'Empire romain', "Empire romain d'Occident", 'ville métropolitaine de Rome Capitale', 'circle of Rome']
    Aliases: {'en': ['The Eternal City', 'Roma', 'Rome, Italy', 'City of Seven Hills'], 'fr': ['La ville éternelle', 'La ville aux sept collines', 'Roma', "l'Urbs"], 'de': ['Die Ewige Stadt', 'Roma'], 'lb': ['Roma', "D'Éiweg Stad"]}
    Coordinates: [{'lat': 41.893055555556, 'lon': 12.482777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1274" → 1274
    Temporal signal words: avant
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 482 days
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'empereur Basile' and 'Rome' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'empereur Basile' near 'Rome' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 195 [ID: surprise_test_fr__15]:
  Publication date : 1756
  Language         : fr
  Person  : 'empereur Basile'  (QID: N/A)
  Location: 'Constantinople'  (QID: Q16869)

  [ARTICLE TEXT — entity markers added]
  "Le pape Jean VIII le reçut à sa communion, le reconnut, lui écrivit ; et malgré ce huitiéme concile oecuménique, qui avait anathématisé ce patriarche, le pape envoya ses légats à un autre concile à <LOCATION>Constantinople</LOCATION>, dans lequel Photius fut reconnu innocent par quatre - cent évêques, dont trois - cent l' avaient auparavant condamné. Les légats de ce même siége de Rome, qui l' avaient anathématisé, servirent eux -mêmes à casser le huitiéme concile oecuménique. Combien tout change chez les hommes ! Combien ce qui était faux, devient vrai selon les tems ! Les légats de Jean VIII s' écrient en plein concile ; si quelqu' un ne reconnait pas Photius, que son partage soit avec Judas. le concile s' écrie, longues années au patriarche Photius, et au patriarche Jean. enfin à la suite des actes du concile on voit une lettre du pape à ce savant patriarche, dans laquelle il lui dit ; nous pensons comme vous... etc. il est donc clair que l' église romaine et la grecque pensaient alors différemment de ce qu' on pense aujourdhui. Il arriva depuis que Rome adopta la procession du pére et du fils ; et il arriva même qu' en 1274 l' empereur des grecs, Michel Paléologue, implorant contre les turcs une nouvelle croisade, envoya au second concile de Lyon, son patriarche et son chancelier, qui chantèrent avec le concile en latin, qui ex patre filioque procedit. mais l' église grecque retourna encor à son opinion, et sembla la quitter encor dans la réunion passagère qui se fit avec Eugène IV. Que les hommes aprennent de là à se tolerer les uns les autres. Voilà des variations et des disputes sur un point fondamental, qui n' ont ni excité de troubles, ni rempli les prisons, ni allumé les buchers. On a blâmé les déférences du pape Jean VIII pour le patriarche Photius ; on n' a pas assez songé que ce pontife avait alors besoin de l' <PERSON>empereur Basile</PERSON>. Un roi de Bulgarie, nommé Bogoris, gagné par l' habileté de sa femme qui était chrêtienne, s' était converti, à l' exemple de Clovis et du roi Egbert."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Constantinople
    Description: appellation officielle jusqu'en 1930 de l'actuelle ville d'Istanbul, en Turquie, capitale jusqu'en 1923
    Country: ['Empire byzantin', 'Empire latin de Constantinople', 'Rome antique', 'Empire ottoman', 'Turquie', 'Turquie']
    Aliases: {'en': ['Constantinopolis', "The City of the World's Desire", 'Tsarigrad', 'Tsargorod', 'Czargrad', 'Tzargrad', 'Mint of Constantinople'], 'fr': ['Constantinopolis'], 'de': ['Dersaadet', 'Carigrad', 'Zarigrad', 'Constantinopel', 'Konstantinoupolis', 'Kostantiniyye', 'Theodosius']}
    Coordinates: [{'lat': 41.0125, 'lon': 28.98}, {'lat': 41.01224, 'lon': 28.976018}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1274" → 1274
    Temporal signal words: avant
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 482 days
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'empereur Basile' and 'Constantinople' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'empereur Basile' near 'Constantinople' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 196 [ID: surprise_test_fr__16]:
  Publication date : 1756
  Language         : fr
  Person  : 'Scha - Hussein'  (QID: N/A)
  Location: 'Georgie'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "C' est encor ici une de ces révolutions où le caractère des peuples qui la firent, eut plus de part que le caractère de leurs chefs : car Myri - Weis ayant été assassiné et remplacé par un autre barbare nommé Maghmud, son propre neveu, qui n' était âgé que de dix - huit ans, il n' y avait pas d' apparence que ce jeune homme pût faire beaucoup par lui -même, et qu' il conduisit ces troupes indisciplinées de montagnards féroces, comme nos généraux conduisent des armées réglées. Le gouvernement de Hussein était méprisé, et la province de Candahar ayant commencé les troubles, les provinces du Caucase du côté de la <LOCATION>Georgie</LOCATION> se révoltèrent aussi. Enfin Maghmud assiégea Ispahan en 1722. <PERSON>Scha - Hussein</PERSON> lui remit cette capitale, abdiqua le royaume à ses pieds, et le reconnut pour son maître, trop heureux que Maghmud daignât épouser sa fille. Tous les tableaux des cruautés et des malheurs des hommes que nous examinons depuis le tems de Charlemagne, n' ont rien de plus horrible que les suites de la révolution d' Ispahan. Maghmud crut ne pouvoir s' affermir qu' en faisant égorger les familles des principaux citoyens. La Perse entiére a été trente années ce qu' avait été l' Allemagne avant la paix de Westphalie, ce que fut la France du tems de Charles VI, l' Angleterre dans les guerres de la rose rouge et de la rose blanche. Mais la Perse est tombée d' un état plus florissant dans un plus grand abîme de malheurs. La religion eut encor part à ces désolations. Les aguans tenaient pour Omar, comme les persans pour Ali ; et ce Maghmud chef des aguans mêlait les plus lâches superstitions aux plus détestables cruautés. Il mourut en démence en 1725 après avoir désolé la Perse. Un nouvel usurpateur de la nation des aguans lui succéda ; il s' appellait Asraf. La désolation de la Perse redoublait de tous côtés. Les turcs l' inondaient du côté de la Georgie, l' ancienne Colchide."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1722" → 1722
      - "1725" → 1725
    Temporal signal words: ancien, ancienne, plus, après, avant
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 31 days
    OCR quality estimate: 0.994

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Scha - Hussein' and 'Georgie' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Scha - Hussein' near 'Georgie' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 197 [ID: surprise_test_fr__62]:
  Publication date : 1797
  Language         : fr
  Person  : 'Albert Durer'  (QID: Q5580)
  Location: 'Westphalie'  (QID: Q8614)

  [ARTICLE TEXT — entity markers added]
  "Anselme, la généalogie, la naissance, les noms des rois, des princes, des grands seigneurs ; l' Encyclopédie ne leur doit rien à ce titre, mais elle doit tout aux Arts & aux talens. <PERSON>Albert Durer</PERSON>, né à Nuremberg en 1470, & dont j' ai parlé comme peintre au mot École, ne laisse presque à desirer dans les ouvrages de son tems, dont les Italiens eux -mêmes profiterent, sinon que cet illustre artiste eût connu l' antique, pour donner à ses figures autant d' élégance que de vérité. Aldegraf, ( Albert ) né en <LOCATION>Westphalie</LOCATION>, disciple de Durer, en a saisi la maniere, & s' est fait autrefois une grande réputation. Audran, ( Gérard ) mort en 1703 âgé de soixante trois ans, a exercé son burin à multiplier les grands morceaux du Poussin, de Mignard, & autres. On connoît ses magnifiques estampes des batailles d' Alexandre, qu' il a gravées d' après les desseins de le Brun : l' oeuvre de cet artiste est recommandable par la force & le bon goût de sa maniere. Baldini, ( Baccio ) florentin, fut éleve de Maso Finiguerra, inventeur du secret de la Gravure en cuivre, & fit paroître encore quelque chose de mieux que son maître. Belle, ( Etienne de la ) né à Florence en 1610, mort dans la même ville en 1664, acquit une maniere d' eau - forte très - expéditive, & d' un si grand effet, que quelques curieux le mettent au - dessus de Callot. Si la maniere de ce maître n' est point si finie de gravure ni si précise de dessein que celle de Callot, sa touche est plus libre, plus savante, & plus pittoresque : peu de gens l' ont surpassé pour l' esprit, la finesse, & la legereté de la pointe. Il a généralement négligé les piés & les mains de ses petites figures, mais ses têtes ont une noblesse & une beauté de caractere séduisante ; son oeuvre est très - considérable. Bénédette Castiglione, peintre & graveur, né à Gènes en 1616, mort à Mantoue en 1670, a gravé à l' eau forte plusieurs pieces, où il a mis autant d' esprit que de goût. Le clair - obscur de ses estampes fait le charme des connoisseurs."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Albrecht Dürer
    Description: peintre, graveur et mathématicien allemand (1471–1528)
    Born: ['+1471-05-21T00:00:00Z']
    Died: ['+1528-04-06T00:00:00Z']
    Birth place: ['Q2090']
    Death place: ['Nuremberg']
    Residences: ['Venise', 'Nuremberg']
    Work locations: ['Nuremberg', 'Q641', 'Q78', 'Strasbourg', 'Colmar', 'Q1794', 'Mayence', 'Q365', 'Innsbruck', 'Q1891', 'Q490', 'Florence', 'Bois-le-Duc', 'Arnemuiden', 'Q9811', 'Q192508', 'Q81220', 'Heerewaarden', 'Middelbourg', 'Nimègue', 'Q9857', 'Q73022', 'Q2682889', 'Q9871', 'Veere', 'Zaltbommel', 'Zierikzee', 'Q12892', 'Malines', 'Q220', 'Q6837']
  Location Wikidata:
    Label: Westphalie
    Description: région allemande
    Country: ['Allemagne']
    Located in: ['Rhénanie-du-Nord-Westphalie', 'royaume de Prusse']
    Aliases: {'en': ['Westfalia', 'Westfalen']}
    Coordinates: [{'lat': 52, 'lon': 8}]
  Known person–location links: {"work_location": "P937"}

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (6):
      - "1470" → 1470
      - "1703" → 1703
      - "1610" → 1610
      - "1664" → 1664
      - "1616" → 1616
    Temporal signal words: plus, né à, mort à, après, avant
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 94 days
    OCR quality estimate: 0.983

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Albert Durer' and 'Westphalie' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Albert Durer' near 'Westphalie' around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 198 [ID: surprise_test_fr__65]:
  Publication date : 1756
  Language         : fr
  Person  : "sultan d' égypte"  (QID: N/A)
  Location: 'Espagne'  (QID: Q29)

  [ARTICLE TEXT — entity markers added]
  "Les succès de ce peuple conquérant semblent dûs plutôt à l' entousiasme qui les anime, et à l' esprit de la nation, qu' à ses conducteurs : car Omar est assassiné par un esclave perse en 653. Otman son successeur l' est en 655 dans une émeute. Ali ce fameux gendre de Mahomet n' est élu, et ne gouverne qu' au milieu des troubles. Il meurt assassiné au bout de cinq ans comme ses prédécesseurs, et cependant les armes musulmanes sont toujours heureuses. Cet Ali que les persans révèrent aujourd'hui, et dont ils suivent les principes en oposition à ceux d' Omar, obtint enfin le califat, et transféra le siége des califes de la ville de Médine, où Mahomet est enseveli, dans la ville de Couffa, sur les bords de l' Euphrate : à peine en reste - t -il aujourd'hui des ruines. C' est le sort de Babylone, de Séleucie, et de toutes les anciennes villes de la Caldée, qui n' étaient bâties que de briques. Il est évident que le génie du peuple arabe mis en mouvement par Mahomet fit tout de lui -même pendant près de trois siécles, et ressembla en cela au génie des anciens romains. C' est en effet sous Valid le moins guerrier des califes, que se font les plus grandes conquêtes. Un de ses généraux étend son empire jusqu' à Samarkande en 707. Un autre attaque en même tems l' empire des grecs vers la mer Noire. Un autre en 711 passe d' égypte en <LOCATION>Espagne</LOCATION> soumise aisément tour à tour par les carthaginois, par les romains, par les goths et vandales, et enfin par ces arabes qu' on nomme maures. Ils y établirent d' abord le royaume de Cordoüe. Le <PERSON>sultan d' égypte</PERSON> secoue à la vérité le joug du grand calife de Bagdat, et Abdérame gouverneur de l' Espagne conquise ne reconnait plus le sultan d' égypte : cependant tout plie encor sous les armes musulmanes. Cet Abdérame, petit - fils du calife Hésham, prend les royaumes de Castille, de Navarre, de Portugal, d' Arragon."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Espagne
    Description: pays du sud-ouest de l'Europe
    Country: ['Espagne']
    Aliases: {'en': ['Kingdom of Spain'], 'fr': ["Royaume d'Espagne", 'Esp.'], 'de': ['Königreich Spanien'], 'lb': ['Kinnekräich Spuenien']}
    Coordinates: [{'lat': 40.2, 'lon': -3.5}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: aujourd'hui, ancien, ancienne, plus, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.988

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between "sultan d' égypte" and 'Espagne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing "sultan d' égypte" near 'Espagne' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 199 [ID: surprise_test_fr__74]:
  Publication date : 1756
  Language         : fr
  Person  : 'Abdérame'  (QID: N/A)
  Location: 'Arragon'  (QID: Q4040)

  [ARTICLE TEXT — entity markers added]
  "Les succès de ce peuple conquérant semblent dûs plutôt à l' entousiasme qui les anime, et à l' esprit de la nation, qu' à ses conducteurs : car Omar est assassiné par un esclave perse en 653. Otman son successeur l' est en 655 dans une émeute. Ali ce fameux gendre de Mahomet n' est élu, et ne gouverne qu' au milieu des troubles. Il meurt assassiné au bout de cinq ans comme ses prédécesseurs, et cependant les armes musulmanes sont toujours heureuses. Cet Ali que les persans révèrent aujourd'hui, et dont ils suivent les principes en oposition à ceux d' Omar, obtint enfin le califat, et transféra le siége des califes de la ville de Médine, où Mahomet est enseveli, dans la ville de Couffa, sur les bords de l' Euphrate : à peine en reste - t -il aujourd'hui des ruines. C' est le sort de Babylone, de Séleucie, et de toutes les anciennes villes de la Caldée, qui n' étaient bâties que de briques. Il est évident que le génie du peuple arabe mis en mouvement par Mahomet fit tout de lui -même pendant près de trois siécles, et ressembla en cela au génie des anciens romains. C' est en effet sous Valid le moins guerrier des califes, que se font les plus grandes conquêtes. Un de ses généraux étend son empire jusqu' à Samarkande en 707. Un autre attaque en même tems l' empire des grecs vers la mer Noire. Un autre en 711 passe d' égypte en Espagne soumise aisément tour à tour par les carthaginois, par les romains, par les goths et vandales, et enfin par ces arabes qu' on nomme maures. Ils y établirent d' abord le royaume de Cordoüe. Le sultan d' égypte secoue à la vérité le joug du grand calife de Bagdat, et <PERSON>Abdérame</PERSON> gouverneur de l' Espagne conquise ne reconnait plus le sultan d' égypte : cependant tout plie encor sous les armes musulmanes. Cet Abdérame, petit - fils du calife Hésham, prend les royaumes de Castille, de Navarre, de Portugal, d' <LOCATION>Arragon</LOCATION>."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Aragon
    Description: communauté autonome d'Espagne
    Country: ['Espagne']
    Located in: ['Espagne']
    Coordinates: [{'lat': 41, 'lon': -1}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: aujourd'hui, ancien, ancienne, plus, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.988

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Abdérame' and 'Arragon' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Abdérame' near 'Arragon' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 200 [ID: surprise_test_fr__75]:
  Publication date : 1756
  Language         : fr
  Person  : 'Mahomet'  (QID: Q9458)
  Location: 'Caldée'  (QID: Q200969)

  [ARTICLE TEXT — entity markers added]
  "Les succès de ce peuple conquérant semblent dûs plutôt à l' entousiasme qui les anime, et à l' esprit de la nation, qu' à ses conducteurs : car Omar est assassiné par un esclave perse en 653. Otman son successeur l' est en 655 dans une émeute. Ali ce fameux gendre de <PERSON>Mahomet</PERSON> n' est élu, et ne gouverne qu' au milieu des troubles. Il meurt assassiné au bout de cinq ans comme ses prédécesseurs, et cependant les armes musulmanes sont toujours heureuses. Cet Ali que les persans révèrent aujourd'hui, et dont ils suivent les principes en oposition à ceux d' Omar, obtint enfin le califat, et transféra le siége des califes de la ville de Médine, où Mahomet est enseveli, dans la ville de Couffa, sur les bords de l' Euphrate : à peine en reste - t -il aujourd'hui des ruines. C' est le sort de Babylone, de Séleucie, et de toutes les anciennes villes de la <LOCATION>Caldée</LOCATION>, qui n' étaient bâties que de briques. Il est évident que le génie du peuple arabe mis en mouvement par Mahomet fit tout de lui -même pendant près de trois siécles, et ressembla en cela au génie des anciens romains. C' est en effet sous Valid le moins guerrier des califes, que se font les plus grandes conquêtes. Un de ses généraux étend son empire jusqu' à Samarkande en 707. Un autre attaque en même tems l' empire des grecs vers la mer Noire. Un autre en 711 passe d' égypte en Espagne soumise aisément tour à tour par les carthaginois, par les romains, par les goths et vandales, et enfin par ces arabes qu' on nomme maures. Ils y établirent d' abord le royaume de Cordoüe. Le sultan d' égypte secoue à la vérité le joug du grand calife de Bagdat, et Abdérame gouverneur de l' Espagne conquise ne reconnait plus le sultan d' égypte : cependant tout plie encor sous les armes musulmanes. Cet Abdérame, petit - fils du calife Hésham, prend les royaumes de Castille, de Navarre, de Portugal, d' Arragon."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Mahomet
    Description: chef politique arabe et fondateur de l’islam
    Born: ['+0571-04-20T00:00:00Z', '+0570-00-00T00:00:00Z']
    Died: ['+0632-06-08T00:00:00Z', '+0634-00-00T00:00:00Z']
    Birth place: ['La Mecque']
    Death place: ['Médine']
    Residences: ['La Mecque', 'Médine']
  Location Wikidata:
    Label: Chaldée
    Description: région antique du Proche-Orient
    Aliases: {'en': ['Chaldeans'], 'fr': ['Chaldee', 'Chaldaïque', 'Région Chaldée'], 'de': ['Chaldaia', 'Kaldäea']}
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: aujourd'hui, ancien, ancienne, plus, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.988

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mahomet' and 'Caldée' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mahomet' near 'Caldée' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 201 [ID: surprise_test_fr__83]:
  Publication date : 1756
  Language         : fr
  Person  : 'Henri V'  (QID: N/A)
  Location: 'Rome'  (QID: Q220)

  [ARTICLE TEXT — entity markers added]
  "Deux légats l' y déposent ; deux députés de la diéte, envoyés par son fils, lui arrachent les ornemens impériaux. Bientôt après, échapé de sa prison, pauvre, errant et sans secours, il mourut à Liége plus misérable encor que Grégoire VII et plus obscurément, après avoir si longtems tenu les yeux de l' Europe ouverts sur ses victoires, sur ses grandeurs, sur ses infortunes, sur ses vices et ses vertus. Il s' écriait en mourant : Dieu des vengeances, vous vengerez ce parricide. de tout tems les hommes ont imaginé que Dieu exauçait les malédictions des mourans, et surtout des péres. Erreur utile et respectable, si elle arrêtait le crime. Une autre erreur plus généralement répandue parmi nous faisait croire que les excommuniés étaient damnés. Le fils d' Henri IV mit le comble à son impieté en affectant la piété atroce de déterrer le corps de son pére inhumé dans la cathédrale de Liége, et de le faire porter dans une cave à Spire. Ce fut ainsi qu' il consomma son hypocrisie dénaturée. CHAPITRE 37 De l' empereur <PERSON>Henri V</PERSON> et de <LOCATION>Rome</LOCATION>, jusqu' à Fréderic I. Ce même Henri V qui avait détrôné et exhumé son pére, une bulle du pape à la main, soûtint les mêmes droits de Henri IV contre l' église, dès qu' il fut maître. Déja les papes savaient se faire un apui des rois de France contre les empereurs. Les prétentions de la papauté attaquaient, il est vrai, tous les souverains ; mais on ménageait par des négociations ceux qu' on insultait par des bulles. Les rois de France ne prétendaient rien à Rome. Ils étaient voisins et jaloux de l' Allemagne. Ils étaient donc les alliés naturels des papes. Aussi Pascal II vint en France, et implora le secours du roi Philippe : ses successeurs en usèrent souvent de même. Les domaines que possédait le st siége, le droit qu' il reclamait en vertu des prétendues donations de Pepin et de Charlemagne, la donation réelle de la comtesse Matilde, ne faisaient point encor du pape un souverain puissant. Toutes ces terres étaient ou contestées ou possédées par d' autres."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Rome
    Description: capitale de l'Italie
    Country: ['Italie', 'États pontificaux', "royaume d'Italie", 'royaume des Ostrogoths', 'Empire byzantin', "royaume d'Italie", 'royaume de Rome', 'République romaine', 'Empire romain', "Empire romain d'Occident", 'Vatican']
    Located in: ['province de Rome', 'États pontificaux', 'Q1558632', 'Rome antique', 'République romaine', 'Q2277', 'Q42834', 'ville métropolitaine de Rome Capitale', 'Q3677829']
    Aliases: {'en': ['The Eternal City', 'Roma', 'Rome, Italy', 'City of Seven Hills'], 'fr': ['La ville éternelle', 'La ville aux sept collines', 'Roma', "l'Urbs"], 'de': ['Die Ewige Stadt', 'Roma'], 'lb': ['Roma', "D'Éiweg Stad"]}
    Coordinates: [{'lat': 41.893055555556, 'lon': 12.482777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Henri V' and 'Rome' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Henri V' near 'Rome' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 202 [ID: surprise_test_fr__93]:
  Publication date : 1756
  Language         : fr
  Person  : 'Charlemagne'  (QID: Q3044)
  Location: 'France'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "Deux légats l' y déposent ; deux députés de la diéte, envoyés par son fils, lui arrachent les ornemens impériaux. Bientôt après, échapé de sa prison, pauvre, errant et sans secours, il mourut à Liége plus misérable encor que Grégoire VII et plus obscurément, après avoir si longtems tenu les yeux de l' Europe ouverts sur ses victoires, sur ses grandeurs, sur ses infortunes, sur ses vices et ses vertus. Il s' écriait en mourant : Dieu des vengeances, vous vengerez ce parricide. de tout tems les hommes ont imaginé que Dieu exauçait les malédictions des mourans, et surtout des péres. Erreur utile et respectable, si elle arrêtait le crime. Une autre erreur plus généralement répandue parmi nous faisait croire que les excommuniés étaient damnés. Le fils d' Henri IV mit le comble à son impieté en affectant la piété atroce de déterrer le corps de son pére inhumé dans la cathédrale de Liége, et de le faire porter dans une cave à Spire. Ce fut ainsi qu' il consomma son hypocrisie dénaturée. CHAPITRE 37 De l' empereur Henri V et de Rome, jusqu' à Fréderic I. Ce même Henri V qui avait détrôné et exhumé son pére, une bulle du pape à la main, soûtint les mêmes droits de Henri IV contre l' église, dès qu' il fut maître. Déja les papes savaient se faire un apui des rois de <LOCATION>France</LOCATION> contre les empereurs. Les prétentions de la papauté attaquaient, il est vrai, tous les souverains ; mais on ménageait par des négociations ceux qu' on insultait par des bulles. Les rois de France ne prétendaient rien à Rome. Ils étaient voisins et jaloux de l' Allemagne. Ils étaient donc les alliés naturels des papes. Aussi Pascal II vint en France, et implora le secours du roi Philippe : ses successeurs en usèrent souvent de même. Les domaines que possédait le st siége, le droit qu' il reclamait en vertu des prétendues donations de Pepin et de <PERSON>Charlemagne</PERSON>, la donation réelle de la comtesse Matilde, ne faisaient point encor du pape un souverain puissant. Toutes ces terres étaient ou contestées ou possédées par d' autres."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Charlemagne
    Description: empereur d'Occident et roi des Francs
    Born: ['+0748-04-02T00:00:00Z', '+0742-00-00T00:00:00Z', '+0747-00-00T00:00:00Z', '+0742-04-02T00:00:00Z', '+0742-04-10T00:00:00Z']
    Died: ['+0814-01-28T00:00:00Z', '+0814-02-01T00:00:00Z']
    Birth place: ['royaume des Francs', 'Liège', 'Aix-la-Chapelle']
    Death place: ['Aix-la-Chapelle']
  Location Wikidata:
    Label: France
    Description: pays transcontinental au territoire métropolitain situé en Europe de l'Ouest
    Country: ['France']
    Aliases: {'en': ['French Republic'], 'fr': ['République française', 'RF', 'fr', 'la République française', 'Fr.', 'La France', "L'Hexagone"], 'de': ['Französische Republik', 'fr', 'RF']}
    Coordinates: [{'lat': 47, 'lon': 2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Charlemagne' and 'France' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Charlemagne' near 'France' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 203 [ID: surprise_test_fr__102]:
  Publication date : 1756
  Language         : fr
  Person  : 'Charles Le Simple'  (QID: Q187519)
  Location: 'Angleterre'  (QID: Q21)

  [ARTICLE TEXT — entity markers added]
  "Enfin Rolon ou Raoul, le plus illustre de ces brigands du nord, après avoir été chassé du Dannemarck, ayant rassemblé en Scandinavie tous ceux qui voulurent s' attacher à sa fortune, tenta de nouvelles avantures, et fonda l' espérance de sa grandeur sur la faiblesse de l' Europe. Il aborda l' <LOCATION>Angleterre</LOCATION>, où ses compatriotes étaient déja établis ; mais après deux victoires inutiles, il tourna du côté de la France, que d' autres normands savaient ruiner, mais qu' ils ne savaient pas asservir. Rolon fut le seul de ces barbares qui cessa d' en mériter le nom, en cherchant un établissement fixe. Maître de Rouen sans peine, au lieu de la détruire, il en fit relever les murailles et les tours. Rouen devint sa place d' armes ; de là il volait tantôt en Angleterre, tantôt en France, faisant la guerre avec politique, comme avec fureur. La France était expirante sous le régne de <PERSON>Charles Le Simple</PERSON>, roi de nom, et dont la monarchie était encor plus démembrée par les ducs, par les comtes et par les barons ses sujets, que par les normands. Charles Le Gros n' avait donné que de l' or aux barbares : Charles Le Simple offrit à Rolon sa fille et des provinces. Raoul demanda d' abord la Normandie : et on fut trop heureux de la lui céder. Il demanda ensuite la Bretagne ; on disputa ; mais il fallut la céder encor avec des clauses que le plus fort explique toûjours à son avantage. Ainsi la Bretagne, qui était tout - à - l' heure un royaume, devint un fief de la Neustrie ; et la Neustrie, qu' on s' accoutuma bientôt à nommer Normandie du nom de ses usurpateurs, fut un état séparé, dont les ducs rendaient un vain hommage à la couronne de France. L' archevêque de Rouen sut persuader à Rolon de se faire chrêtien. Ce prince embrassa volontiers une religion qui affermissait sa puissance. Les véritables conquérans sont ceux qui savent faire des loix. Leur puissance est stable ; les autres sont des torrens qui passent. Rolon paisible fut le seul législateur de son tems dans le continent chrêtien."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Charles III le Simple
    Description: roi des Francs de Francie occidentale
    Born: ['+0879-09-17T00:00:00Z']
    Died: ['+0929-10-07T00:00:00Z']
    Birth place: ['Q217768']
    Death place: ['Q217768']
  Location Wikidata:
    Label: Angleterre
    Description: pays du nord-ouest de l'Europe, faisant partie du Royaume-Uni
    Country: ['Royaume-Uni', "Royaume-Uni de Grande-Bretagne et d'Irlande", 'Q161885']
    Located in: ['Q145', "Royaume-Uni de Grande-Bretagne et d'Irlande", 'royaume de Grande-Bretagne']
    Aliases: {'en': ['ENG', 'England, United Kingdom', 'England, UK'], 'fr': ['Ang.', 'England']}
    Coordinates: [{'lat': 53, 'lon': -1}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après, avant, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Charles Le Simple' and 'Angleterre' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Charles Le Simple' near 'Angleterre' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 204 [ID: surprise_test_fr__240]:
  Publication date : 1797
  Language         : fr
  Person  : 'Frézier'  (QID: N/A)
  Location: 'mer du sud'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "D' après le rapport de M De Vaujuas et de M Boutin, il était évident que nous ne pouvions trouver à la Trinité l' eau et le bois qui nous manquaient. Je me décidai tout de suite à faire route pour l' île Sainte - Catherine, sur la côte du Brésil : c' était l' ancienne relâche des bâtimens français qui allaient dans la <LOCATION>mer du sud</LOCATION>. <PERSON>Frézier</PERSON> et l' amiral Anson y trouvèrent abondamment à se pourvoir de tous leurs besoins. Ce fut pour ne pas perdre un seul jour, que je donnai la préférence à l' île Sainte - Catherine sur Rio - Janéïro, où les différentes formalités auraient exigé plus de temps qu' il n' en fallait pour faire l' eau et le bois qui nous manquaient. Mais en dirigeant ma route vers l' île Sainte - Catherine, je voulus m' assurer de l' existence de l' île de l' Ascençaon, que M Daprès place à cent lieues dans l' ouest de la Trinité, et à 15 minutes seulement plus sud. Suivant le journal de M Poncel De La Haye, qui commandait la frégate la renommée, j' étais certain que différens navigateurs, entr' autres Frézier, homme très - éclairé, avaient cru aborder à l' Ascençaon, et qu' ils n' avaient été réellement qu' à la Trinité. Malgré l' autorité de M Poncel De La Haye, je crus que ce point de géographie demandait un nouvel éclaircissement. Les deux jours que nous passâmes vers la partie sud de l' île de la Trinité, nous mirent à portée de faire les relèvemens d' après lesquels M Bernizet traça le plan de la partie sud de l' île : il diffère très - peu de celui du docteur Halley, qui m' avait été remis par M De Fleurieu. La vue, peinte par M Duché De Vancy, est d' une vérité si frappante, qu' elle suffira seule pour que les navigateurs qui aborderont dans la partie du sud de la Trinité, ne puissent jamais se tromper."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien, ancienne, plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Frézier' and 'mer du sud' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Frézier' near 'mer du sud' around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 205 [ID: surprise_test_fr__245]:
  Publication date : 1797
  Language         : fr
  Person  : "l' amiral Anson"  (QID: N/A)
  Location: 'mer du sud'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "D' après le rapport de M De Vaujuas et de M Boutin, il était évident que nous ne pouvions trouver à la Trinité l' eau et le bois qui nous manquaient. Je me décidai tout de suite à faire route pour l' île Sainte - Catherine, sur la côte du Brésil : c' était l' ancienne relâche des bâtimens français qui allaient dans la <LOCATION>mer du sud</LOCATION>. Frézier et <PERSON>l' amiral Anson</PERSON> y trouvèrent abondamment à se pourvoir de tous leurs besoins. Ce fut pour ne pas perdre un seul jour, que je donnai la préférence à l' île Sainte - Catherine sur Rio - Janéïro, où les différentes formalités auraient exigé plus de temps qu' il n' en fallait pour faire l' eau et le bois qui nous manquaient. Mais en dirigeant ma route vers l' île Sainte - Catherine, je voulus m' assurer de l' existence de l' île de l' Ascençaon, que M Daprès place à cent lieues dans l' ouest de la Trinité, et à 15 minutes seulement plus sud. Suivant le journal de M Poncel De La Haye, qui commandait la frégate la renommée, j' étais certain que différens navigateurs, entr' autres Frézier, homme très - éclairé, avaient cru aborder à l' Ascençaon, et qu' ils n' avaient été réellement qu' à la Trinité. Malgré l' autorité de M Poncel De La Haye, je crus que ce point de géographie demandait un nouvel éclaircissement. Les deux jours que nous passâmes vers la partie sud de l' île de la Trinité, nous mirent à portée de faire les relèvemens d' après lesquels M Bernizet traça le plan de la partie sud de l' île : il diffère très - peu de celui du docteur Halley, qui m' avait été remis par M De Fleurieu. La vue, peinte par M Duché De Vancy, est d' une vérité si frappante, qu' elle suffira seule pour que les navigateurs qui aborderont dans la partie du sud de la Trinité, ne puissent jamais se tromper."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien, ancienne, plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between "l' amiral Anson" and 'mer du sud' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing "l' amiral Anson" near 'mer du sud' around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 206 [ID: surprise_test_fr__279]:
  Publication date : 1756
  Language         : fr
  Person  : 'Soliman'  (QID: N/A)
  Location: 'Syrie'  (QID: Q858)

  [ARTICLE TEXT — entity markers added]
  "Mais enfin abandonné et livré au roi, condamné seulement à la prison, et ayant voulu s' évader, il paya sa hardiesse de sa tête. Ce fut alors que l' esprit de faction fut anéanti, et que les anglais, n' étant plus redoutables à leur monarque, commencèrent à le devenir à leurs voisins, surtout lorsque Henri VIII en montant au trône, fut, par l' économie extrême de son pére, possesseur d' un ample trésor, et par la sagesse de ce gouvernement, maître d' un peuple belliqueux, et pourtant soumis autant que les anglais peuvent l' être. CHAPITRE 97 Idée générale du seizième siècle. Le commencement du seiziéme siécle que nous avons déja entamé, nous présente à la fois les plus grands spectacles que le monde ait jamais fournis. Si on jette la vuë sur ceux qui régnaient pour lors en Europe, leur gloire, ou leur conduite, ou les grands changements dont ils ont été cause, rendent leurs noms immortels. C' est à Constantinople un Sélim qui met sous la domination ottomane la <LOCATION>Syrie</LOCATION> et l' égypte, dont les mahométans mammelucs avaient été en possession depuis le treiziéme siécle. C' est après lui son fils, le grand <PERSON>Soliman</PERSON>, qui le premier des empereurs turcs marche jusqu' à Vienne, et se fait couronner roi de Perse dans Bagdat prise par ses armes, faisant trembler à la fois l' Europe et l' Asie. On voit en même tems vers le nord, Gustave Vasa, brisant dans la Suéde le joug étranger, élu roi du pays, dont il est le libérateur. En Moscovie Jean Basilowitz soustrait sa patrie aux tartares dont elle était tributaire ; prince à la vérité barbare, et chef d' une nation plus barbare encore ; mais le vengeur de son pays mérite d' être compté parmi les grands princes."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Syrie
    Description: État arabe du Proche-Orient indépendant depuis 1946
    Country: ['Syrie']
    Aliases: {'en': ['Syrian Arab Republic', 'Surya'], 'fr': ['République arabe syrienne']}
    Coordinates: [{'lat': 35.216667, 'lon': 38.583333}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Soliman' and 'Syrie' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Soliman' near 'Syrie' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 207 [ID: surprise_test_fr__314]:
  Publication date : 1756
  Language         : fr
  Person  : 'Jean Basilide'  (QID: N/A)
  Location: 'Uglis'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "C' est que tous deux firent mourir leurs fils. <PERSON>Jean Basilide</PERSON> soupçonnant son fils d' une conspiration pendant le siége de Pleskou, le tua d' un coup de pique ; et Pierre ayant fait condamner le sien à la mort, ne permit pas que ce prince survécut à sa condamnation et à sa grace. L' histoire ne fournit guère d' événement plus extraordinaire que celui des faux Demetrius, qui agita si longtems la Russie après la mort de Jean Basilides. Ce czar laissa deux fils, l' un nommé Fédor ou Théodor, l' autre Demetri ou Demetrius. Fédor régna ; Demetri fut confiné dans un village nommé <LOCATION>Uglis</LOCATION> avec la czarine sa mére. Jusques -là les moeurs grossiéres de cette cour n' avaient point encor adopté la politique des sultans, et des anciens empereurs grecs, de sacrifier les princes du sang à la sûreté du trône. Un premier ministre nommé Boris - Gudenou, dont Fédor avait épousé la soeur, persuada au czar Fédor, qu' on ne pouvait bien régner qu' en imitant les turcs, et en assassinant son frére. Ce premier ministre Boris envoya un officier dans le village où était élevé le jeune Demetri, avec ordre de le tuer. L' officier de retour dit qu' il avait exécuté sa commission, et demanda la récompense qu' on lui avait promise. Boris pour toute récompense fit tuer le meurtrier, afin de supprimer les preuves du crime. On prétend que Boris quelque tems après empoisonna le czar Fédor ; et quoiqu' il en fût soupçonné, il n' en monta pas moins sur le trône. Il parut alors dans la Lithuanie un jeune homme qui prétendait être le prince Demetri échapé à l' assassin. Plusieurs personnes qui l' avaient vû auprès de sa mére, le reconnaissaient à des marques certaines. Il ressemblait parfaitement au prince ; il montrait la croix d' or enrichie de pierreries qu' on avait attachée au cou de Demetri à son baptême. Un palatin de Sandomir le reconnut d' abord pour le fils de Jean Basilide, et pour le véritable czar."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: ancien, plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Jean Basilide' and 'Uglis' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Jean Basilide' near 'Uglis' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 208 [ID: surprise_test_fr__325]:
  Publication date : 1797
  Language         : fr
  Person  : 'Cook'  (QID: Q7324)
  Location: 'île de Pâque'  (QID: Q14452)

  [ARTICLE TEXT — entity markers added]
  "Il découvre : l' <LOCATION>île de Pâque</LOCATION>, par 27 degrés 4 minutes de latitude sud, et 265 degrés 42 minutes de longitude orientale du méridien de Ténériffe, suivant l' auteur des vies des gouverneurs de Batavia ; ce qui répond à 113 degrés 18 minutes de longitude à l' ouest du méridien de Paris : île habitée, de seize lieues hollandaises de circuit, et remarquable par des statues ou figures colossales élevées en grand nombre sur ses côtes ; ( elle a été reconnue depuis par <PERSON>Cook</PERSON>, qui l' a trouvée par 27 degrés 5 minutes de latitude, et 112 degrés 6 minutes de longitude à l' ouest de Paris, et qui l' a nommée Easter ou Pâque : elle a été vue aussi en 1770, par les espagnols, qui la placent par 27 degrés 6 minutes de latitude, et 268 degrés 19 minutes de longitude, méridien de Ténériffe, ce qui répond à 110 degrés 41 minutes de notre longitude, à l' ouest de Paris ; ces derniers lui ont donné le nom de San - Carlos ). Charls - Hof, ou cour de Charles, par 15 degrés 45 minutes de latitude sud, et après huit cents lieues de course depuis l' île de Pâque ; ( suivant la relation française de ce voyage, c' est une petite île rase, avec une espèce de lac dans l' intérieur. Roggewein crut que c' était l' île des Chiens de Le Maire et Schouten, et la relation hollandaise ne lui assigne ni latitude ni longitude : on l' a placée sur la carte relativement à sa distance des îles Pernicieuses, qui en sont à douze lieues à l' ouest, et dont la position est aujourd'hui connue ). Les îles Pernicieuses, par 14 degrés 41 minutes de latitude sud, et à douze lieues hollandaises à l' ouest de Charls - Hof : ce sont quatre îles basses et peuplées, qui ont depuis quatre jusqu' à dix lieues de tour ; ( Roggewein y perdit un vaisseau, ce qui fit donner le nom de Pernicieuse à l' une de ces îles : deux autres furent appelées les deux Frères, et une autre la Soeur ; il y resta cinq hommes de l' équipage, qui désertèrent et qu' on abandonna."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: James Cook
    Description: navigateur, cartographe et explorateur britannique
    Born: ['+1728-10-27T00:00:00Z', '+1728-01-01T00:00:00Z', '+1728-11-07T00:00:00Z']
    Died: ['+1779-02-14T00:00:00Z', '+1779-01-01T00:00:00Z']
    Birth place: ['Marton']
    Death place: ['baie de Kealakekua']
  Location Wikidata:
    Label: Rapa Nui
    Description: île du Pacifique, au Chili
    Country: ['Chili']
    Located in: ['Isla de Pascua']
    Aliases: {'en': ['Te pito o te kainga a Hau Maka'], 'fr': ['Ile de Pasques', 'île de Pâques']}
    Coordinates: [{'lat': -27.12, 'lon': -109.35}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1770" → 1770
    Temporal signal words: aujourd'hui, après
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 27 days
    OCR quality estimate: 0.941

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Cook' and 'île de Pâque' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Cook' near 'île de Pâque' around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 209 [ID: surprise_test_fr__332]:
  Publication date : 1797
  Language         : fr
  Person  : 'Charls - Hof'  (QID: N/A)
  Location: 'île des Chiens'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Il découvre : l' île de Pâque, par 27 degrés 4 minutes de latitude sud, et 265 degrés 42 minutes de longitude orientale du méridien de Ténériffe, suivant l' auteur des vies des gouverneurs de Batavia ; ce qui répond à 113 degrés 18 minutes de longitude à l' ouest du méridien de Paris : île habitée, de seize lieues hollandaises de circuit, et remarquable par des statues ou figures colossales élevées en grand nombre sur ses côtes ; ( elle a été reconnue depuis par Cook, qui l' a trouvée par 27 degrés 5 minutes de latitude, et 112 degrés 6 minutes de longitude à l' ouest de Paris, et qui l' a nommée Easter ou Pâque : elle a été vue aussi en 1770, par les espagnols, qui la placent par 27 degrés 6 minutes de latitude, et 268 degrés 19 minutes de longitude, méridien de Ténériffe, ce qui répond à 110 degrés 41 minutes de notre longitude, à l' ouest de Paris ; ces derniers lui ont donné le nom de San - Carlos ). <PERSON>Charls - Hof</PERSON>, ou cour de Charles, par 15 degrés 45 minutes de latitude sud, et après huit cents lieues de course depuis l' île de Pâque ; ( suivant la relation française de ce voyage, c' est une petite île rase, avec une espèce de lac dans l' intérieur. Roggewein crut que c' était l' <LOCATION>île des Chiens</LOCATION> de Le Maire et Schouten, et la relation hollandaise ne lui assigne ni latitude ni longitude : on l' a placée sur la carte relativement à sa distance des îles Pernicieuses, qui en sont à douze lieues à l' ouest, et dont la position est aujourd'hui connue ). Les îles Pernicieuses, par 14 degrés 41 minutes de latitude sud, et à douze lieues hollandaises à l' ouest de Charls - Hof : ce sont quatre îles basses et peuplées, qui ont depuis quatre jusqu' à dix lieues de tour ; ( Roggewein y perdit un vaisseau, ce qui fit donner le nom de Pernicieuse à l' une de ces îles : deux autres furent appelées les deux Frères, et une autre la Soeur ; il y resta cinq hommes de l' équipage, qui désertèrent et qu' on abandonna."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1770" → 1770
    Temporal signal words: aujourd'hui, après
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 27 days
    OCR quality estimate: 0.941

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Charls - Hof' and 'île des Chiens' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Charls - Hof' near 'île des Chiens' around 1797?
  4. Resolve temporal expressions relative to 1797. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 210 [ID: surprise_test_fr__381]:
  Publication date : 1678
  Language         : fr
  Person  : 'Charles dernier Duc de Bourgogne'  (QID: Q151120)
  Location: 'France'  (QID: Q142)

  [ARTICLE TEXT — entity markers added]
  "Il est vray que ces renoncemens doivent avoir quelque cause legitime, et que les rois feroient tort à leurs successeurs, s' ils retranchoient une province du corps de l' etat sans y être contraints, ou sans y trouver de grands avantages. Mais lors qu' ils ne consentent à ces retranchemens que par necessité, ou pour le bien et l' utilité du royaume, leurs successeurs n' ont aucun sujet de se plaindre d' eux ; et s' ils en ont, la plupart de nos rois auroient eu droit de se plaindre de leurs predecesseurs, particulierement les enfans de Henry Ii qui par le traité de château Cambresy, relâcha et rendit près de deux cens villes ou forteresses. Il faut ajoutter à cela qu' il est difficile de marquer ce point de grandeur dont parle l' auteur qu' on a cité, où les etats étant parvenus, il n' est plus permis aux rois d' en retrancher aucune partie ; parce qu' il ne s' est jamais passé de temps considerable depuis l' établissement de la monarchie, que la <LOCATION>France</LOCATION> ne se soit accruë par les conquêtes de nos rois, ou n' ait diminué par celles de nos voisins. De plus, les rois de la premiere et seconde race luy ont très - souvent ôté sa grandeur, la partageant entre leurs enfans, et divisant le royaume en plusieurs royaumes. Enfin pour ne pas alleguer toutes les provinces qui ont été desunies de la couronne, il suffit de dire que la Bourgogne l' avoit été par le roy Henry, petit fils de Hugues Capet, en faveur de Robert son frere ; qu' elle y revint sous le roy Jean, qui la donna peu de temps après à Philippe Le Hardy son quatriéme fils ; et qu' après la mort de <PERSON>Charles dernier Duc de Bourgogne</PERSON>, Loüis XI s' en rendit le maître ; de sorte qu' il n' y avoit pas cinquante ans qu' elle étoit réünie à la couronne lorsque François I la voulut ceder. Passons maintenant aux autres pretextes qu' on prend pour se dispenser de la fidelité qu' on doit aux souverains."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Charles le Téméraire
    Description: duc de Bourgogne et souverain des Pays-Bas bourguignons
    Born: ['+1433-11-10T00:00:00Z']
    Died: ['+1477-01-05T00:00:00Z']
    Birth place: ['Dijon']
    Death place: ['Nancy']
  Location Wikidata:
    Label: France
    Description: pays transcontinental au territoire métropolitain situé en Europe de l'Ouest
    Country: ['France']
    Aliases: {'en': ['French Republic'], 'fr': ['République française', 'RF', 'fr', 'la République française', 'Fr.', 'La France', "L'Hexagone"], 'de': ['Französische Republik', 'fr', 'RF']}
    Coordinates: [{'lat': 47, 'lon': 2}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: maintenant, plus, après, avant
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Charles dernier Duc de Bourgogne' and 'France' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Charles dernier Duc de Bourgogne' near 'France' around 1678?
  4. Resolve temporal expressions relative to 1678. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 211 [ID: surprise_test_fr__387]:
  Publication date : 1756
  Language         : fr
  Person  : 'Henri'  (QID: N/A)
  Location: 'Russie'  (QID: Q159)

  [ARTICLE TEXT — entity markers added]
  "Ce qu' il y a de plus singulier, c' est qu' Urbain II qui prononça cette sentence, la prononça dans les propres états du roi, à Clermont en Auvergne, où il venait chercher un azile, et dans ce même concile où nous verrons qu' il prêcha la croisade. Cependant il ne paraît point que Philippe excommunié ait été en horreur à ses sujets ; c' est une raison de plus pour douter de cet abandon général où l'on dit que le roi Robert avait été réduit. Ce qu' il y eut d' assez remarquable, c' est le mariage du roi <PERSON>Henri</PERSON> pére de Philippe avec une princesse moscovite. Les moscovites ou russes commençaient à être chrêtiens ; mais ils n' avaient aucun commerce avec le reste de l' Europe. Ils habitaient au - delà de la Pologne, à peine chrêtienne elle -même, et sans aucune correspondance avec la France. Cependant le roi Henri envoya jusqu' en <LOCATION>Russie</LOCATION> demander la fille du souverain, à qui les autres européans donnaient le titre de duc, aussi - bien qu' au chef de la Pologne. Les russes le nommaient dans leur langage tzaar, dont on a fait depuis le mot de czar. On prétend que Henri se détermina à ce mariage, dans la crainte d' essuyer des querelles ecclesiastiques. De toutes les superstitions de ces tems -là, ce n' était pas la moins nuisible au bien des états, que celle de ne pouvoir épouser sa parente au septiéme degré. Presque tous les souverains de l' Europe étaient parens de Henri. Quoi qu' il en soit, Anne fille de Jaraslau czar de Moscovie fut reine de France ; et il est à remarquer qu' après la mort de son mari, elle n' eut point la régence, et n' y prétendit point. Les loix changent selon les tems. Ce fut le comte de Flandres, un des vassaux du royaume, qui en fut régent. La reine veuve se remaria à un comte de Crepi. Tout cela serait singulier aujourdhui, et ne le fut point alors. Ni Henri, ni Philippe I ne firent rien de mémorable ; mais de leur tems leurs vassaux et arrière - vassaux conquirent des royaumes."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Russie
    Description: pays d'Europe de l'Est et d'Asie du Nord
    Country: ['Russie']
    Aliases: {'en': ['Russian Federation', 'Federation of Russia'], 'fr': ['Rus.', 'Fédération de Russie', 'Fédération russe'], 'de': ['Russische Föderation', 'Russländische Föderation', 'Rußland', 'Rußische Föderation', 'Rußländische Föderation'], 'lb': ['Russesch Federatioun', 'Russesch Federatiounsrepublik', 'Rossija']}
    Coordinates: [{'lat': 66.41666666666667, 'lon': 94.25}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Henri' and 'Russie' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Henri' near 'Russie' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 212 [ID: surprise_test_fr__394]:
  Publication date : 1756
  Language         : fr
  Person  : 'roi Robert'  (QID: N/A)
  Location: 'Europe'  (QID: Q46)

  [ARTICLE TEXT — entity markers added]
  "Ce qu' il y a de plus singulier, c' est qu' Urbain II qui prononça cette sentence, la prononça dans les propres états du roi, à Clermont en Auvergne, où il venait chercher un azile, et dans ce même concile où nous verrons qu' il prêcha la croisade. Cependant il ne paraît point que Philippe excommunié ait été en horreur à ses sujets ; c' est une raison de plus pour douter de cet abandon général où l'on dit que le <PERSON>roi Robert</PERSON> avait été réduit. Ce qu' il y eut d' assez remarquable, c' est le mariage du roi Henri pére de Philippe avec une princesse moscovite. Les moscovites ou russes commençaient à être chrêtiens ; mais ils n' avaient aucun commerce avec le reste de l' <LOCATION>Europe</LOCATION>. Ils habitaient au - delà de la Pologne, à peine chrêtienne elle -même, et sans aucune correspondance avec la France. Cependant le roi Henri envoya jusqu' en Russie demander la fille du souverain, à qui les autres européans donnaient le titre de duc, aussi - bien qu' au chef de la Pologne. Les russes le nommaient dans leur langage tzaar, dont on a fait depuis le mot de czar. On prétend que Henri se détermina à ce mariage, dans la crainte d' essuyer des querelles ecclesiastiques. De toutes les superstitions de ces tems -là, ce n' était pas la moins nuisible au bien des états, que celle de ne pouvoir épouser sa parente au septiéme degré. Presque tous les souverains de l' Europe étaient parens de Henri. Quoi qu' il en soit, Anne fille de Jaraslau czar de Moscovie fut reine de France ; et il est à remarquer qu' après la mort de son mari, elle n' eut point la régence, et n' y prétendit point. Les loix changent selon les tems. Ce fut le comte de Flandres, un des vassaux du royaume, qui en fut régent. La reine veuve se remaria à un comte de Crepi. Tout cela serait singulier aujourdhui, et ne le fut point alors. Ni Henri, ni Philippe I ne firent rien de mémorable ; mais de leur tems leurs vassaux et arrière - vassaux conquirent des royaumes."

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
    Temporal signal words: plus, après
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'roi Robert' and 'Europe' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'roi Robert' near 'Europe' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 213 [ID: surprise_test_fr__401]:
  Publication date : 1561
  Language         : fr
  Person  : 'Villeneufve'  (QID: N/A)
  Location: 'chemin de Paris'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Misser Iuliano commanda à Torneto de la prendre, & de la mener chez luy en l' estable. Là ou elle se rengea aussi proprement, comme si elle n' en eust jamais bougé. Il la fit ramener le lendemain en la mesme place, pour veoir si quelqu' un la vendiqueroit. Mais il ne venoit personne, dont il fut fort esbahy : & pensoit que ce fust quelque esprit qui l' eust ramenee. De là à quelque temps maistre Arnaud s' addresse à misser Iuliano, lequel il trouva monté sus sa hacquenee, & luy dit : monsieur, je suis fort aise de savoir que ceste hacquenee soit à vous. Car asseurez vous qu' elle est bonne : je l' ay essayee, il y ha environ un an que je la trouvay pres du pont du Rosne, qu' elle s' en alloit toute seule, & qu' un garson la vouloit prendre. Mais congnoissant à sa façon qu' elle n' estoit pas sienne, je la luy ostay : & la garday un jour ou deux sans pouvoir savoir à qui elle estoit. Le troisiesme jour je la menay jusques à <PERSON>Villeneufve</PERSON>, ou j' ouy dire qu' un gentilhomme François la cherchoit, & qu' il luy avoit esté dit qu' on l' avoit veue emmener par un garson sus le <LOCATION>chemin de Paris</LOCATION>. Le gentilhomme alloit apres. Et moy sachant celà, je picque apres luy pour la luy rendre : mais je ne le peu jamais atteindre. Car il alloit grand train pour atteindre son larron. Et allay tant en le cherchant, que je me trouvay jusqu' en Lorraine. Là ou voyant que je n' oyois point de nouvelles de ce gentilhomme, je la garday long temps. Et à la fin m' en suis revenu en ceste ville, ou je l' avoys prise : & ay trouvé par quelques uns de mes amis, qu' il se souvenoit bien l' avoir veue autrefois en ceste ville : mais qu' il ne savoit à qui, sinon que ce fust à quelqu' un de vous autres messieurs de la legation. Sachant celà, je l' ay fait mener en la place du Palais, affin que celuy à qui elle estoit la peust appercevoir. Et ce pendant je m' en estois allé d' icy à Nimes, d' ou je suis retourné depuis deux jours. Mais Dieu soit loué qu' elle ha retrouvé son maistre. Car j' en estois en grand peine."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Villeneufve' and 'chemin de Paris' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Villeneufve' near 'chemin de Paris' around 1561?
  4. Resolve temporal expressions relative to 1561. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 214 [ID: surprise_test_fr__405]:
  Publication date : 1561
  Language         : fr
  Person  : 'maistre Arnaud'  (QID: N/A)
  Location: 'pont du Rosne'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Misser Iuliano commanda à Torneto de la prendre, & de la mener chez luy en l' estable. Là ou elle se rengea aussi proprement, comme si elle n' en eust jamais bougé. Il la fit ramener le lendemain en la mesme place, pour veoir si quelqu' un la vendiqueroit. Mais il ne venoit personne, dont il fut fort esbahy : & pensoit que ce fust quelque esprit qui l' eust ramenee. De là à quelque temps <PERSON>maistre Arnaud</PERSON> s' addresse à misser Iuliano, lequel il trouva monté sus sa hacquenee, & luy dit : monsieur, je suis fort aise de savoir que ceste hacquenee soit à vous. Car asseurez vous qu' elle est bonne : je l' ay essayee, il y ha environ un an que je la trouvay pres du <LOCATION>pont du Rosne</LOCATION>, qu' elle s' en alloit toute seule, & qu' un garson la vouloit prendre. Mais congnoissant à sa façon qu' elle n' estoit pas sienne, je la luy ostay : & la garday un jour ou deux sans pouvoir savoir à qui elle estoit. Le troisiesme jour je la menay jusques à Villeneufve, ou j' ouy dire qu' un gentilhomme François la cherchoit, & qu' il luy avoit esté dit qu' on l' avoit veue emmener par un garson sus le chemin de Paris. Le gentilhomme alloit apres. Et moy sachant celà, je picque apres luy pour la luy rendre : mais je ne le peu jamais atteindre. Car il alloit grand train pour atteindre son larron. Et allay tant en le cherchant, que je me trouvay jusqu' en Lorraine. Là ou voyant que je n' oyois point de nouvelles de ce gentilhomme, je la garday long temps. Et à la fin m' en suis revenu en ceste ville, ou je l' avoys prise : & ay trouvé par quelques uns de mes amis, qu' il se souvenoit bien l' avoir veue autrefois en ceste ville : mais qu' il ne savoit à qui, sinon que ce fust à quelqu' un de vous autres messieurs de la legation. Sachant celà, je l' ay fait mener en la place du Palais, affin que celuy à qui elle estoit la peust appercevoir. Et ce pendant je m' en estois allé d' icy à Nimes, d' ou je suis retourné depuis deux jours. Mais Dieu soit loué qu' elle ha retrouvé son maistre. Car j' en estois en grand peine."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'maistre Arnaud' and 'pont du Rosne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'maistre Arnaud' near 'pont du Rosne' around 1561?
  4. Resolve temporal expressions relative to 1561. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 215 [ID: surprise_test_fr__415]:
  Publication date : 1561
  Language         : fr
  Person  : 'Torneto'  (QID: N/A)
  Location: 'chemin de Paris'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Misser Iuliano commanda à <PERSON>Torneto</PERSON> de la prendre, & de la mener chez luy en l' estable. Là ou elle se rengea aussi proprement, comme si elle n' en eust jamais bougé. Il la fit ramener le lendemain en la mesme place, pour veoir si quelqu' un la vendiqueroit. Mais il ne venoit personne, dont il fut fort esbahy : & pensoit que ce fust quelque esprit qui l' eust ramenee. De là à quelque temps maistre Arnaud s' addresse à misser Iuliano, lequel il trouva monté sus sa hacquenee, & luy dit : monsieur, je suis fort aise de savoir que ceste hacquenee soit à vous. Car asseurez vous qu' elle est bonne : je l' ay essayee, il y ha environ un an que je la trouvay pres du pont du Rosne, qu' elle s' en alloit toute seule, & qu' un garson la vouloit prendre. Mais congnoissant à sa façon qu' elle n' estoit pas sienne, je la luy ostay : & la garday un jour ou deux sans pouvoir savoir à qui elle estoit. Le troisiesme jour je la menay jusques à Villeneufve, ou j' ouy dire qu' un gentilhomme François la cherchoit, & qu' il luy avoit esté dit qu' on l' avoit veue emmener par un garson sus le <LOCATION>chemin de Paris</LOCATION>. Le gentilhomme alloit apres. Et moy sachant celà, je picque apres luy pour la luy rendre : mais je ne le peu jamais atteindre. Car il alloit grand train pour atteindre son larron. Et allay tant en le cherchant, que je me trouvay jusqu' en Lorraine. Là ou voyant que je n' oyois point de nouvelles de ce gentilhomme, je la garday long temps. Et à la fin m' en suis revenu en ceste ville, ou je l' avoys prise : & ay trouvé par quelques uns de mes amis, qu' il se souvenoit bien l' avoir veue autrefois en ceste ville : mais qu' il ne savoit à qui, sinon que ce fust à quelqu' un de vous autres messieurs de la legation. Sachant celà, je l' ay fait mener en la place du Palais, affin que celuy à qui elle estoit la peust appercevoir. Et ce pendant je m' en estois allé d' icy à Nimes, d' ou je suis retourné depuis deux jours. Mais Dieu soit loué qu' elle ha retrouvé son maistre. Car j' en estois en grand peine."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Torneto' and 'chemin de Paris' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Torneto' near 'chemin de Paris' around 1561?
  4. Resolve temporal expressions relative to 1561. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 216 [ID: surprise_test_fr__455]:
  Publication date : 1666
  Language         : fr
  Person  : 'Chevalier De Rohan'  (QID: N/A)
  Location: 'Châlons'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Réponse du Comte De Bussy à Madame De S. à Chaseu, ce 1 septembre 1675. En me disant que vos lettres ne sont pas dignes de mon approbation, madame, vous m' en écrivez une qui en merite une plus grande, sans compter votre modestie. Mais pour ne la pas offenser davantage, je vais traiter d' autre chose avec vous. Ce qu' a dit monsieur le prince de Monsieur De Turenne en passant à <LOCATION>Châlons</LOCATION>, me paroît d' un fort honnête homme, et d' un homme qui sent bien son merite. Monsieur De Montecuculi se précautionnera encore davantage avec lui qu' il ne faisoit avec Monsieur De Turenne. Il est vrai que le Chevalier De G a été heureux au combat d' Altenhein ; et la trousse à celui de Consarbricq. Je m' en réjouis avec vous, et j' espere vous faire un même compliment pour monsieur vôtre fils à la fin de cette campagne. Vous devriez me conter le procès dont il est question. Je suis tellement affamé de vous entendre, que je vous donnerois une favorable audience quand vous ne me parleriez que d' interlocutoires et d' arrêts. Lettre 61. Réponse du Comte De Bussy à Madame De S. à Chaseu, ce 29 octobre 1675. Je reçus hier vôtre lettre, madame, qui me donna la joie que vos lettres ont accoutumé de me donner. Enfin voilà vôtre niéce sur le point de passer le pas ; elle va trouver ce qu' elle cherchoit. à propos de chercher, ceci me fait souvenir du pauvre <PERSON>Chevalier De Rohan</PERSON>, qui ayant rencontré un soir bien tard à Fontainebleau, Madame D' seule qui passoit dans une galerie, lui demanda ce qu' elle cherchoit : rien, dit -elle. Ma foi, madame, lui répondit -il, je ne voudrois pas avoir perdu ce que vous cherchez. Voilà mon petit conte, madame. Vous m' avez permis d' en faire un aussi, je me sers de la liberté que vous m' avez donnée. J' ai trouvé le vôtre plaisant au dernier point, et je m' en sçai bon gré, car il faut avoir de l' esprit pour trouver cela aussi plaisant qu' il est."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1675" → 1675
      - "1675" → 1675
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 9 days
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Chevalier De Rohan' and 'Châlons' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Chevalier De Rohan' near 'Châlons' around 1666?
  4. Resolve temporal expressions relative to 1666. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 217 [ID: surprise_test_fr__459]:
  Publication date : 1666
  Language         : fr
  Person  : 'Altenhein'  (QID: N/A)
  Location: 'Châlons'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Réponse du Comte De Bussy à Madame De S. à Chaseu, ce 1 septembre 1675. En me disant que vos lettres ne sont pas dignes de mon approbation, madame, vous m' en écrivez une qui en merite une plus grande, sans compter votre modestie. Mais pour ne la pas offenser davantage, je vais traiter d' autre chose avec vous. Ce qu' a dit monsieur le prince de Monsieur De Turenne en passant à <LOCATION>Châlons</LOCATION>, me paroît d' un fort honnête homme, et d' un homme qui sent bien son merite. Monsieur De Montecuculi se précautionnera encore davantage avec lui qu' il ne faisoit avec Monsieur De Turenne. Il est vrai que le Chevalier De G a été heureux au combat d' <PERSON>Altenhein</PERSON> ; et la trousse à celui de Consarbricq. Je m' en réjouis avec vous, et j' espere vous faire un même compliment pour monsieur vôtre fils à la fin de cette campagne. Vous devriez me conter le procès dont il est question. Je suis tellement affamé de vous entendre, que je vous donnerois une favorable audience quand vous ne me parleriez que d' interlocutoires et d' arrêts. Lettre 61. Réponse du Comte De Bussy à Madame De S. à Chaseu, ce 29 octobre 1675. Je reçus hier vôtre lettre, madame, qui me donna la joie que vos lettres ont accoutumé de me donner. Enfin voilà vôtre niéce sur le point de passer le pas ; elle va trouver ce qu' elle cherchoit. à propos de chercher, ceci me fait souvenir du pauvre Chevalier De Rohan, qui ayant rencontré un soir bien tard à Fontainebleau, Madame D' seule qui passoit dans une galerie, lui demanda ce qu' elle cherchoit : rien, dit -elle. Ma foi, madame, lui répondit -il, je ne voudrois pas avoir perdu ce que vous cherchez. Voilà mon petit conte, madame. Vous m' avez permis d' en faire un aussi, je me sers de la liberté que vous m' avez donnée. J' ai trouvé le vôtre plaisant au dernier point, et je m' en sçai bon gré, car il faut avoir de l' esprit pour trouver cela aussi plaisant qu' il est."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1675" → 1675
      - "1675" → 1675
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 9 days
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Altenhein' and 'Châlons' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Altenhein' near 'Châlons' around 1666?
  4. Resolve temporal expressions relative to 1666. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 218 [ID: surprise_test_fr__460]:
  Publication date : 1666
  Language         : fr
  Person  : 'S.'  (QID: N/A)
  Location: 'Châlons'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "Réponse du Comte De Bussy à Madame De <PERSON>S.</PERSON> à Chaseu, ce 1 septembre 1675. En me disant que vos lettres ne sont pas dignes de mon approbation, madame, vous m' en écrivez une qui en merite une plus grande, sans compter votre modestie. Mais pour ne la pas offenser davantage, je vais traiter d' autre chose avec vous. Ce qu' a dit monsieur le prince de Monsieur De Turenne en passant à <LOCATION>Châlons</LOCATION>, me paroît d' un fort honnête homme, et d' un homme qui sent bien son merite. Monsieur De Montecuculi se précautionnera encore davantage avec lui qu' il ne faisoit avec Monsieur De Turenne. Il est vrai que le Chevalier De G a été heureux au combat d' Altenhein ; et la trousse à celui de Consarbricq. Je m' en réjouis avec vous, et j' espere vous faire un même compliment pour monsieur vôtre fils à la fin de cette campagne. Vous devriez me conter le procès dont il est question. Je suis tellement affamé de vous entendre, que je vous donnerois une favorable audience quand vous ne me parleriez que d' interlocutoires et d' arrêts. Lettre 61. Réponse du Comte De Bussy à Madame De S. à Chaseu, ce 29 octobre 1675. Je reçus hier vôtre lettre, madame, qui me donna la joie que vos lettres ont accoutumé de me donner. Enfin voilà vôtre niéce sur le point de passer le pas ; elle va trouver ce qu' elle cherchoit. à propos de chercher, ceci me fait souvenir du pauvre Chevalier De Rohan, qui ayant rencontré un soir bien tard à Fontainebleau, Madame D' seule qui passoit dans une galerie, lui demanda ce qu' elle cherchoit : rien, dit -elle. Ma foi, madame, lui répondit -il, je ne voudrois pas avoir perdu ce que vous cherchez. Voilà mon petit conte, madame. Vous m' avez permis d' en faire un aussi, je me sers de la liberté que vous m' avez donnée. J' ai trouvé le vôtre plaisant au dernier point, et je m' en sçai bon gré, car il faut avoir de l' esprit pour trouver cela aussi plaisant qu' il est."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1675" → 1675
      - "1675" → 1675
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 9 days
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'S.' and 'Châlons' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'S.' near 'Châlons' around 1666?
  4. Resolve temporal expressions relative to 1666. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 219 [ID: surprise_test_fr__463]:
  Publication date : 1666
  Language         : fr
  Person  : 'Consarbricq'  (QID: N/A)
  Location: 'Chaseu'  (QID: Q2968914)

  [ARTICLE TEXT — entity markers added]
  "Réponse du Comte De Bussy à Madame De S. à <LOCATION>Chaseu</LOCATION>, ce 1 septembre 1675. En me disant que vos lettres ne sont pas dignes de mon approbation, madame, vous m' en écrivez une qui en merite une plus grande, sans compter votre modestie. Mais pour ne la pas offenser davantage, je vais traiter d' autre chose avec vous. Ce qu' a dit monsieur le prince de Monsieur De Turenne en passant à Châlons, me paroît d' un fort honnête homme, et d' un homme qui sent bien son merite. Monsieur De Montecuculi se précautionnera encore davantage avec lui qu' il ne faisoit avec Monsieur De Turenne. Il est vrai que le Chevalier De G a été heureux au combat d' Altenhein ; et la trousse à celui de <PERSON>Consarbricq</PERSON>. Je m' en réjouis avec vous, et j' espere vous faire un même compliment pour monsieur vôtre fils à la fin de cette campagne. Vous devriez me conter le procès dont il est question. Je suis tellement affamé de vous entendre, que je vous donnerois une favorable audience quand vous ne me parleriez que d' interlocutoires et d' arrêts. Lettre 61. Réponse du Comte De Bussy à Madame De S. à Chaseu, ce 29 octobre 1675. Je reçus hier vôtre lettre, madame, qui me donna la joie que vos lettres ont accoutumé de me donner. Enfin voilà vôtre niéce sur le point de passer le pas ; elle va trouver ce qu' elle cherchoit. à propos de chercher, ceci me fait souvenir du pauvre Chevalier De Rohan, qui ayant rencontré un soir bien tard à Fontainebleau, Madame D' seule qui passoit dans une galerie, lui demanda ce qu' elle cherchoit : rien, dit -elle. Ma foi, madame, lui répondit -il, je ne voudrois pas avoir perdu ce que vous cherchez. Voilà mon petit conte, madame. Vous m' avez permis d' en faire un aussi, je me sers de la liberté que vous m' avez donnée. J' ai trouvé le vôtre plaisant au dernier point, et je m' en sçai bon gré, car il faut avoir de l' esprit pour trouver cela aussi plaisant qu' il est."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: château de Chazeu
    Description: château fort français
    Country: ['Q142']
    Located in: ['Laizy']
    Aliases: {'fr': ['chateau de Chazeu']}
    Coordinates: [{'lat': 46.8972, 'lon': 4.19806}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1675" → 1675
      - "1675" → 1675
    Temporal signal words: hier, plus, avant, tard
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 9 days
    OCR quality estimate: 0.986

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Consarbricq' and 'Chaseu' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Consarbricq' near 'Chaseu' around 1666?
  4. Resolve temporal expressions relative to 1666. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 220 [ID: surprise_test_fr__9]:
  Publication date : 1756
  Language         : fr
  Person  : 'roi Egbert'  (QID: N/A)
  Location: 'Rome'  (QID: Q220)

  [ARTICLE TEXT — entity markers added]
  "Le pape Jean VIII le reçut à sa communion, le reconnut, lui écrivit ; et malgré ce huitiéme concile oecuménique, qui avait anathématisé ce patriarche, le pape envoya ses légats à un autre concile à Constantinople, dans lequel Photius fut reconnu innocent par quatre - cent évêques, dont trois - cent l' avaient auparavant condamné. Les légats de ce même siége de <LOCATION>Rome</LOCATION>, qui l' avaient anathématisé, servirent eux -mêmes à casser le huitiéme concile oecuménique. Combien tout change chez les hommes ! Combien ce qui était faux, devient vrai selon les tems ! Les légats de Jean VIII s' écrient en plein concile ; si quelqu' un ne reconnait pas Photius, que son partage soit avec Judas. le concile s' écrie, longues années au patriarche Photius, et au patriarche Jean. enfin à la suite des actes du concile on voit une lettre du pape à ce savant patriarche, dans laquelle il lui dit ; nous pensons comme vous... etc. il est donc clair que l' église romaine et la grecque pensaient alors différemment de ce qu' on pense aujourdhui. Il arriva depuis que Rome adopta la procession du pére et du fils ; et il arriva même qu' en 1274 l' empereur des grecs, Michel Paléologue, implorant contre les turcs une nouvelle croisade, envoya au second concile de Lyon, son patriarche et son chancelier, qui chantèrent avec le concile en latin, qui ex patre filioque procedit. mais l' église grecque retourna encor à son opinion, et sembla la quitter encor dans la réunion passagère qui se fit avec Eugène IV. Que les hommes aprennent de là à se tolerer les uns les autres. Voilà des variations et des disputes sur un point fondamental, qui n' ont ni excité de troubles, ni rempli les prisons, ni allumé les buchers. On a blâmé les déférences du pape Jean VIII pour le patriarche Photius ; on n' a pas assez songé que ce pontife avait alors besoin de l' empereur Basile. Un roi de Bulgarie, nommé Bogoris, gagné par l' habileté de sa femme qui était chrêtienne, s' était converti, à l' exemple de Clovis et du <PERSON>roi Egbert</PERSON>."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Rome
    Description: capitale de l'Italie
    Country: ['Italie', 'États pontificaux', "royaume d'Italie", 'royaume des Ostrogoths', 'Empire byzantin', "royaume d'Italie", 'royaume de Rome', 'République romaine', 'Empire romain', "Empire romain d'Occident", 'Vatican']
    Located in: ['province de Rome', 'États pontificaux', 'Rome', 'Rome antique', 'République romaine', 'Empire romain', "Empire romain d'Occident", 'ville métropolitaine de Rome Capitale', 'circle of Rome']
    Aliases: {'en': ['The Eternal City', 'Roma', 'Rome, Italy', 'City of Seven Hills'], 'fr': ['La ville éternelle', 'La ville aux sept collines', 'Roma', "l'Urbs"], 'de': ['Die Ewige Stadt', 'Roma'], 'lb': ['Roma', "D'Éiweg Stad"]}
    Coordinates: [{'lat': 41.893055555556, 'lon': 12.482777777778}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (1):
      - "1274" → 1274
    Temporal signal words: avant
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 482 days
    OCR quality estimate: 0.997

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'roi Egbert' and 'Rome' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'roi Egbert' near 'Rome' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 221 [ID: surprise_test_fr__18]:
  Publication date : 1756
  Language         : fr
  Person  : 'Maghmud'  (QID: N/A)
  Location: 'Georgie'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "C' est encor ici une de ces révolutions où le caractère des peuples qui la firent, eut plus de part que le caractère de leurs chefs : car Myri - Weis ayant été assassiné et remplacé par un autre barbare nommé <PERSON>Maghmud</PERSON>, son propre neveu, qui n' était âgé que de dix - huit ans, il n' y avait pas d' apparence que ce jeune homme pût faire beaucoup par lui -même, et qu' il conduisit ces troupes indisciplinées de montagnards féroces, comme nos généraux conduisent des armées réglées. Le gouvernement de Hussein était méprisé, et la province de Candahar ayant commencé les troubles, les provinces du Caucase du côté de la <LOCATION>Georgie</LOCATION> se révoltèrent aussi. Enfin Maghmud assiégea Ispahan en 1722. Scha - Hussein lui remit cette capitale, abdiqua le royaume à ses pieds, et le reconnut pour son maître, trop heureux que Maghmud daignât épouser sa fille. Tous les tableaux des cruautés et des malheurs des hommes que nous examinons depuis le tems de Charlemagne, n' ont rien de plus horrible que les suites de la révolution d' Ispahan. Maghmud crut ne pouvoir s' affermir qu' en faisant égorger les familles des principaux citoyens. La Perse entiére a été trente années ce qu' avait été l' Allemagne avant la paix de Westphalie, ce que fut la France du tems de Charles VI, l' Angleterre dans les guerres de la rose rouge et de la rose blanche. Mais la Perse est tombée d' un état plus florissant dans un plus grand abîme de malheurs. La religion eut encor part à ces désolations. Les aguans tenaient pour Omar, comme les persans pour Ali ; et ce Maghmud chef des aguans mêlait les plus lâches superstitions aux plus détestables cruautés. Il mourut en démence en 1725 après avoir désolé la Perse. Un nouvel usurpateur de la nation des aguans lui succéda ; il s' appellait Asraf. La désolation de la Perse redoublait de tous côtés. Les turcs l' inondaient du côté de la Georgie, l' ancienne Colchide."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1722" → 1722
      - "1725" → 1725
    Temporal signal words: ancien, ancienne, plus, après, avant
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 31 days
    OCR quality estimate: 0.994

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Maghmud' and 'Georgie' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Maghmud' near 'Georgie' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 222 [ID: surprise_test_fr__29]:
  Publication date : 1756
  Language         : fr
  Person  : 'Asraf'  (QID: N/A)
  Location: 'ancienne Colchide'  (QID: N/A)

  [ARTICLE TEXT — entity markers added]
  "C' est encor ici une de ces révolutions où le caractère des peuples qui la firent, eut plus de part que le caractère de leurs chefs : car Myri - Weis ayant été assassiné et remplacé par un autre barbare nommé Maghmud, son propre neveu, qui n' était âgé que de dix - huit ans, il n' y avait pas d' apparence que ce jeune homme pût faire beaucoup par lui -même, et qu' il conduisit ces troupes indisciplinées de montagnards féroces, comme nos généraux conduisent des armées réglées. Le gouvernement de Hussein était méprisé, et la province de Candahar ayant commencé les troubles, les provinces du Caucase du côté de la Georgie se révoltèrent aussi. Enfin Maghmud assiégea Ispahan en 1722. Scha - Hussein lui remit cette capitale, abdiqua le royaume à ses pieds, et le reconnut pour son maître, trop heureux que Maghmud daignât épouser sa fille. Tous les tableaux des cruautés et des malheurs des hommes que nous examinons depuis le tems de Charlemagne, n' ont rien de plus horrible que les suites de la révolution d' Ispahan. Maghmud crut ne pouvoir s' affermir qu' en faisant égorger les familles des principaux citoyens. La Perse entiére a été trente années ce qu' avait été l' Allemagne avant la paix de Westphalie, ce que fut la France du tems de Charles VI, l' Angleterre dans les guerres de la rose rouge et de la rose blanche. Mais la Perse est tombée d' un état plus florissant dans un plus grand abîme de malheurs. La religion eut encor part à ces désolations. Les aguans tenaient pour Omar, comme les persans pour Ali ; et ce Maghmud chef des aguans mêlait les plus lâches superstitions aux plus détestables cruautés. Il mourut en démence en 1725 après avoir désolé la Perse. Un nouvel usurpateur de la nation des aguans lui succéda ; il s' appellait <PERSON>Asraf</PERSON>. La désolation de la Perse redoublait de tous côtés. Les turcs l' inondaient du côté de la Georgie, l' <LOCATION>ancienne Colchide</LOCATION>."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    No Wikidata data available for this location.
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal expressions found (2):
      - "1722" → 1722
      - "1725" → 1725
    Temporal signal words: ancien, ancienne, plus, après, avant
    Timex within ±14-day isAt window: False
    Nearest timex distance to publication date: 31 days
    OCR quality estimate: 0.994

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Asraf' and 'ancienne Colchide' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Asraf' near 'ancienne Colchide' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 223 [ID: surprise_test_fr__78]:
  Publication date : 1756
  Language         : fr
  Person  : 'Mahomet'  (QID: Q9458)
  Location: 'Euphrate'  (QID: Q34589)

  [ARTICLE TEXT — entity markers added]
  "Les succès de ce peuple conquérant semblent dûs plutôt à l' entousiasme qui les anime, et à l' esprit de la nation, qu' à ses conducteurs : car Omar est assassiné par un esclave perse en 653. Otman son successeur l' est en 655 dans une émeute. Ali ce fameux gendre de <PERSON>Mahomet</PERSON> n' est élu, et ne gouverne qu' au milieu des troubles. Il meurt assassiné au bout de cinq ans comme ses prédécesseurs, et cependant les armes musulmanes sont toujours heureuses. Cet Ali que les persans révèrent aujourd'hui, et dont ils suivent les principes en oposition à ceux d' Omar, obtint enfin le califat, et transféra le siége des califes de la ville de Médine, où Mahomet est enseveli, dans la ville de Couffa, sur les bords de l' <LOCATION>Euphrate</LOCATION> : à peine en reste - t -il aujourd'hui des ruines. C' est le sort de Babylone, de Séleucie, et de toutes les anciennes villes de la Caldée, qui n' étaient bâties que de briques. Il est évident que le génie du peuple arabe mis en mouvement par Mahomet fit tout de lui -même pendant près de trois siécles, et ressembla en cela au génie des anciens romains. C' est en effet sous Valid le moins guerrier des califes, que se font les plus grandes conquêtes. Un de ses généraux étend son empire jusqu' à Samarkande en 707. Un autre attaque en même tems l' empire des grecs vers la mer Noire. Un autre en 711 passe d' égypte en Espagne soumise aisément tour à tour par les carthaginois, par les romains, par les goths et vandales, et enfin par ces arabes qu' on nomme maures. Ils y établirent d' abord le royaume de Cordoüe. Le sultan d' égypte secoue à la vérité le joug du grand calife de Bagdat, et Abdérame gouverneur de l' Espagne conquise ne reconnait plus le sultan d' égypte : cependant tout plie encor sous les armes musulmanes. Cet Abdérame, petit - fils du calife Hésham, prend les royaumes de Castille, de Navarre, de Portugal, d' Arragon."

  [ENTITY CONTEXT]
  Person Wikidata:
    Label: Mahomet
    Description: chef politique arabe et fondateur de l’islam
    Born: ['+0571-04-20T00:00:00Z', '+0570-00-00T00:00:00Z']
    Died: ['+0632-06-08T00:00:00Z', '+0634-00-00T00:00:00Z']
    Birth place: ['La Mecque']
    Death place: ['Médine']
    Residences: ['La Mecque', 'Médine']
  Location Wikidata:
    Label: Euphrate
    Description: fleuve d'Asie de l'Ouest
    Country: ['Turquie', 'Syrie', 'Irak']
    Aliases: {'de': ['Al-Firat', 'Eupharat', 'Eufrat']}
    Coordinates: [{'lat': 39.7283, 'lon': 40.2569}, {'lat': 31.0043, 'lon': 47.442}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: aujourd'hui, ancien, ancienne, plus, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 0.988

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Mahomet' and 'Euphrate' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Mahomet' near 'Euphrate' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?

────────────────────────────────────────────────────────────
Sample 224 [ID: surprise_test_fr__106]:
  Publication date : 1756
  Language         : fr
  Person  : 'Raoul'  (QID: N/A)
  Location: 'Bretagne'  (QID: Q327)

  [ARTICLE TEXT — entity markers added]
  "Enfin Rolon ou <PERSON>Raoul</PERSON>, le plus illustre de ces brigands du nord, après avoir été chassé du Dannemarck, ayant rassemblé en Scandinavie tous ceux qui voulurent s' attacher à sa fortune, tenta de nouvelles avantures, et fonda l' espérance de sa grandeur sur la faiblesse de l' Europe. Il aborda l' Angleterre, où ses compatriotes étaient déja établis ; mais après deux victoires inutiles, il tourna du côté de la France, que d' autres normands savaient ruiner, mais qu' ils ne savaient pas asservir. Rolon fut le seul de ces barbares qui cessa d' en mériter le nom, en cherchant un établissement fixe. Maître de Rouen sans peine, au lieu de la détruire, il en fit relever les murailles et les tours. Rouen devint sa place d' armes ; de là il volait tantôt en Angleterre, tantôt en France, faisant la guerre avec politique, comme avec fureur. La France était expirante sous le régne de Charles Le Simple, roi de nom, et dont la monarchie était encor plus démembrée par les ducs, par les comtes et par les barons ses sujets, que par les normands. Charles Le Gros n' avait donné que de l' or aux barbares : Charles Le Simple offrit à Rolon sa fille et des provinces. Raoul demanda d' abord la Normandie : et on fut trop heureux de la lui céder. Il demanda ensuite la <LOCATION>Bretagne</LOCATION> ; on disputa ; mais il fallut la céder encor avec des clauses que le plus fort explique toûjours à son avantage. Ainsi la Bretagne, qui était tout - à - l' heure un royaume, devint un fief de la Neustrie ; et la Neustrie, qu' on s' accoutuma bientôt à nommer Normandie du nom de ses usurpateurs, fut un état séparé, dont les ducs rendaient un vain hommage à la couronne de France. L' archevêque de Rouen sut persuader à Rolon de se faire chrêtien. Ce prince embrassa volontiers une religion qui affermissait sa puissance. Les véritables conquérans sont ceux qui savent faire des loix. Leur puissance est stable ; les autres sont des torrens qui passent. Rolon paisible fut le seul législateur de son tems dans le continent chrêtien."

  [ENTITY CONTEXT]
  Person Wikidata:
    No Wikidata data available for this person.
  Location Wikidata:
    Label: Bretagne
    Description: région historique et culturelle du Nord-Ouest de la France
    Country: ['France']
    Aliases: {'fr': ['Bretagne historique'], 'de': ['Kleinbritannien', 'Bretagne historique']}
    Coordinates: [{'lat': 48, 'lon': -3}]
  Known person–location links: none

  [TEMPORAL SIGNALS DETECTED]
    Temporal signal words: plus, après, avant, tôt
    Timex within ±14-day isAt window: False
    OCR quality estimate: 1.000

  [SIMILAR ANNOTATED EXAMPLES FROM TRAINING DATA]
    No similar examples retrieved.

  [STEP-BY-STEP ANALYSIS REQUIRED]
  1. What is the relationship between 'Raoul' and 'Bretagne' in this text?
  2. What textual evidence (verb tense, signals) supports or contradicts the association?
  3. Are there temporal expressions placing 'Raoul' near 'Bretagne' around 1756?
  4. Resolve temporal expressions relative to 1756. Are they within ±14 days?
