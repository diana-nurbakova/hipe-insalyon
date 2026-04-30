# Hardest instances for `at` (cross-config)

Cross-config sample: **20 configurations** over **188 instances**.

- universally-wrong: **1** instances (every config got the label wrong)
- near-universally-wrong: **10** instances (≤ 2 configs got it right, of 20)

Each entry shows gold, modal predicted label, language, and an article snippet. When the modal-wrong label dominates and matches what a careful human reader would say, the instance is a candidate for re-annotation review.

---

## Universally wrong (n_correct = 0)

### sn88068010-1890-09-25-a-i0006  ·  `sn88068010-1890-09-25-a-i0006_Q44105` ↔ `sn88068010-1890-09-25-a-i0006_Q46`

- language: **en**  ·  date: 1890-09-25
- person: **'M. Pliillippe de Ferrari'**  ·  location: **'European'**
- gold at: **TRUE**
- 0/20 configs correct  ·  modal predicted: **FALSE**
- predicted-label breakdown: FALSE×11, PROBABLE×9

> The museum of the Berlin post-cfllce alone contains a collection of between 4,000 and 5,000 specimens, half of which are European and the remain der divided between tbe Americans, Asia, Africa and Australia. The emblems upon the stamps of nations are legion; the earth, the sea and the vaulted canopy above have been ransacked for curious and mraning less devices and legends. The en tire animal kingdom, the stars and the moon iu all its phases, besides legendary emblems by the…

---


## Near-universally wrong (n_correct ≤ 2)

### NZZ-1848-10-21-a-p0003  ·  `NZZ-1848-10-21-a-p0003_Q153500` ↔ `NZZ-1848-10-21-a-p0003_Q183`

- language: **de**  ·  date: 1848-10-21
- person: **'Radetzky'**  ·  location: **'Deutschland'**
- gold at: **FALSE**
- 1/20 configs correct  ·  modal predicted: **TRUE**
- predicted-label breakdown: TRUE×13, PROBABLE×6, FALSE×1

> Der gestern erwähnte Tagsbefehl Radetzky's lautet: „Soldaten! Ihr habt mich oft Euern Generalquartier Mailand, 12. Okt. Radetzky. Deutschland.

---

### NZZ-1948-07-19-c-p0002  ·  `NZZ-1948-07-19-c-p0002_Q382070` ↔ `NZZ-1948-07-19-c-p0002_Q142`

- language: **de**  ·  date: 1948-07-19
- person: **'Einanzminister\nFene Hage'**  ·  location: **'Frankreich'**
- gold at: **TRUE**
- 1/20 configs correct  ·  modal predicted: **PROBABLE**
- predicted-label breakdown: PROBABLE×10, FALSE×9, TRUE×1

> Man rechnet namentlich damit, dals für Grolbritannien Senatzanzler Sir Stafford C'ripye und für Frankreich Einanzminister Fene Hage; erscheinen werden. Bei dieser Gelenenheit wird vohi eine allgemeine Aus prache über die Ddurehführune des Mars!nll Plancs Kattfinden. Der Europäische Wirtschaftsrat hat be schlonsen, den ihm von amenilennischer Seite gemnchten Vorsehing anzunchmen und sic mit der Verteilung der amerihanischen Hise an seine Mitelieder zu befassen. Dur Vorherei tu…

---

### GDL-1981-12-11-62  ·  `GDL-1981-12-11-62-NIL_m_benjamin` ↔ `GDL-1981-12-11-62-NIL_fulgur`

- language: **fr**  ·  date: 1981-12-11
- person: **'M. Benjamin'**  ·  location: **'Fulgur'**
- gold at: **FALSE**
- 1/20 configs correct  ·  modal predicted: **TRUE**
- predicted-label breakdown: TRUE×10, PROBABLE×9, FALSE×1

> on s'aventure grâce à M. Benjamin sur la froide planète Fulgur.

---

### 9838247_1868-02-19_0_0_001  ·  `9838247_1868-02-19_0_0_001_Q57428` ↔ `9838247_1868-02-19_0_0_001_Q1142`

- language: **de**  ·  date: 1868-02-19
- person: **'Georg'**  ·  location: **'Elſaß'**
- gold at: **FALSE**
- 2/20 configs correct  ·  modal predicted: **PROBABLE**
- predicted-label breakdown: PROBABLE×13, TRUE×5, FALSE×2

> Aufenthalt in Hietzing , die Regierung dann verpflichtet ſein wird , das Während die preußiſche Regierung dem früheren König von Hannover die größte und edelſte Rückſicht zu Theil werden läßt , während andererſeits ihre Fürſorge für die neue Provinz unter der be — des Königs Georg und ſeiner Umgebung in Hietzing die verwerflichen Verſuche fortgeſetzt , einen Theil ſeiner früheren Unterthanen , meiſt aus den unterſten Ständen , für das völlige boffnungsloſe und thörichte Unter…

---

### NZZ-1848-10-21-a-p0003  ·  `NZZ-1848-10-21-a-p0003-NIL_teichert` ↔ `NZZ-1848-10-21-a-p0003_Q490`

- language: **de**  ·  date: 1848-10-21
- person: **'HH. Reichskommissare Teichert'**  ·  location: **'Mailand'**
- gold at: **FALSE**
- 2/20 configs correct  ·  modal predicted: **TRUE**
- predicted-label breakdown: TRUE×11, PROBABLE×7, FALSE×2

> Mailand. Der gestern erwähnte Tagsbefehl Radetzky's lautet: „Soldaten! Frankfurt. Am 14. Oktober haben die HH.

---

### NZZ-1928-02-17-i-p0001  ·  `NZZ-1928-02-17-i-p0001-NIL_niederer` ↔ `NZZ-1928-02-17-i-p0001_Q2244426`

- language: **de**  ·  date: 1928-02-17
- person: **'Pfarrer Niederer'**  ·  location: **'Schloßberg'**
- gold at: **FALSE**
- 2/20 configs correct  ·  modal predicted: **PROBABLE**
- predicted-label breakdown: PROBABLE×13, TRUE×5, FALSE×2

> Vom Hin tersässenschulmeister am Schloßberg steigt er auf zum Seminardirektor auf dem Schloß Burgdorf. „Sein Streben war, die Wege zu erkennen, auf denen die pädagogische Arbeit — nicht nur seine eigne, sondern eine jede — vorwärtsgehen müsse. Er glaubte an die unabänderliche Gleichheit der menschlichen Natur und an die Ewigkeit der menschlichen Ziele; und darum glaubte er, daß eine Methode der Erziehung die richtige, die not wendige sein müsse." Wenn uns auch heute seine Ein…

---

### sn83030483-1790-03-03-a-i0004  ·  `sn83030483-1790-03-03-a-i0004_Q3934904` ↔ `sn83030483-1790-03-03-a-i0004_Q84`

- language: **en**  ·  date: 1790-03-03
- person: **'General D’Alton'**  ·  location: **'LONDON'**
- gold at: **FALSE**
- 2/20 configs correct  ·  modal predicted: **TRUE**
- predicted-label breakdown: TRUE×13, PROBABLE×5, FALSE×2

> LONDON, Dec. 31. The official account of the capture ofBruffels pnbliflied by the Patriots, is as under. The firft attenpt was.tp make prifoners of all the loldiers who guarded the Mint, and thofe who were quartered in the different converts. General D’Alton did his tu rnoff from fix o’clock in the morning to negociate an armifiice.

---

### sn89058133-1920-04-22-a-i0003  ·  `sn89058133-1920-04-22-a-i0003-NIL_bob_maggart` ↔ `sn89058133-1920-04-22-a-i0003_Q142`

- language: **en**  ·  date: 1920-04-22
- person: **'Bob Maggart'**  ·  location: **'France'**
- gold at: **TRUE**
- 2/20 configs correct  ·  modal predicted: **FALSE**
- predicted-label breakdown: FALSE×9, PROBABLE×9, TRUE×2

> If I do I still want your custom and trade Bob Maggart. I understand you did not get killed in France.

---

### EXP-1918-04-22-a-i0077  ·  `EXP-1918-04-22-a-i0077-NIL_schoeller` ↔ `EXP-1918-04-22-a-i0077_Q64461`

- language: **fr**  ·  date: 1918-04-22
- person: **'Schoeller'**  ·  location: **'N-ûenhoî'**
- gold at: **FALSE**
- 2/20 configs correct  ·  modal predicted: **PROBABLE**
- predicted-label breakdown: PROBABLE×11, TRUE×7, FALSE×2

> N-ûenhoî, près Wettingen, 19 avril 1918. Lorsque, un jour, un de mes copains de lège avait à donner la définition du mot « Ce geste, le Conseil fédéral n' avait pas le droit de le faire. M. Schœller n'étant pas fonctionnaire fédéral, mais un simple particulier.

---

### GDL-1928-05-06-a-i0059  ·  `GDL-1928-05-06-a-i0059_Q16524004` ↔ `GDL-1928-05-06-a-i0059_Q41`

- language: **fr**  ·  date: 1928-05-06
- person: **'Dr Doxiadès'**  ·  location: **'Grèce'**
- gold at: **TRUE**
- 2/20 configs correct  ·  modal predicted: **PROBABLE**
- predicted-label breakdown: PROBABLE×10, FALSE×8, TRUE×2

> Pour les enfants sinistrés de Bulgarie et de Grèce Mgr. Stéphane, archevêque de Sofia, rient d'adresser à l'Union internationale de secours aux enfants une dépêche, où, après avoir rendu hommage à cette institution, il s'exprime comme suit : La solidarité humaine ae manifeste le plue sensiblement dane les heures critiques. En outre, elle a fourni des couvertures à l'hôpital de dix baraques ouvert près de Philippopoli par le chef de la garnison de cette ville, le général Koutz…

---
