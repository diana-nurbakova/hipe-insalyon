# Hardest instances for `isAt` (cross-config)

Cross-config sample: **19 configurations** over **188 instances**.

- universally-wrong: **0** instances (every config got the label wrong)
- near-universally-wrong: **1** instances (≤ 2 configs got it right, of 19)

Each entry shows gold, modal predicted label, language, and an article snippet. When the modal-wrong label dominates and matches what a careful human reader would say, the instance is a candidate for re-annotation review.

---

## Universally wrong (n_correct = 0)

_No instances are universally wrong._


## Near-universally wrong (n_correct ≤ 2)

### GDL-1928-05-06-a-i0059  ·  `GDL-1928-05-06-a-i0059_Q16524004` ↔ `GDL-1928-05-06-a-i0059_Q41`

- language: **fr**  ·  date: 1928-05-06
- person: **'Dr Doxiadès'**  ·  location: **'Grèce'**
- gold isAt: **TRUE**
- 1/19 configs correct  ·  modal predicted: **FALSE**
- predicted-label breakdown: FALSE×18, TRUE×1

> Pour les enfants sinistrés de Bulgarie et de Grèce Mgr. Stéphane, archevêque de Sofia, rient d'adresser à l'Union internationale de secours aux enfants une dépêche, où, après avoir rendu hommage à cette institution, il s'exprime comme suit : La solidarité humaine ae manifeste le plue sensiblement dane les heures critiques. En outre, elle a fourni des couvertures à l'hôpital de dix baraques ouvert près de Philippopoli par le chef de la garnison de cette ville, le général Koutz…

---
