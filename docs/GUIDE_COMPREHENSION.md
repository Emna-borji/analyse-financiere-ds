# Guide de compréhension lot par lot

Ce document explique en français simple ce que fait chaque module du projet,
les choix de conception, et un exemple chiffré sur la **Société X** (le cas
de référence du cours, états financiers 2022–2023).

Les noms de fichiers et de fonctions sont donnés au format `module.py:fonction`
pour que tu puisses sauter directement dans le code.

---

## Préalable — Le schéma pivot

**Fichier** : `analyse_financiere/pivot.py`

### Qu'est-ce que c'est

Une classe Pydantic v2, `EtatsFinanciers`, qui porte un exercice d'une
entreprise avec **60+ champs** : identité, bilan (actif et passif), état de
résultat, hors bilan, retraitements. C'est **le langage unique** dans lequel
tous les adaptateurs traduisent les fichiers sources.

### Pourquoi

Une analyse financière multi-entreprises impose un format commun : SCE,
IFRS et US GAAP désignent les mêmes concepts économiques avec des libellés
différents. Le pivot est la table de traduction interne, analogue au
« schéma canonique » d'un data warehouse.

### Points importants

- **Libellés en français** : `ca`, `ebit`, `actif_total`, `capitaux_propres`…
  Noms exacts du lot 1 du cours. Les adaptateurs IFRS/EDGAR convertissent
  vers ce français pivot.
- **Signes positifs** : les charges (`charges_financieres`, `impot_benefices`,
  `autres_pertes_ordinaires`) sont stockées en **valeur absolue**, même si
  le fichier source les affiche en négatif. Convention unique = moins de bugs
  de signe en aval.
- **Valeurs brutes ET nettes** : le ch.1 utilise le net (immos après amort),
  le ch.2 utilise le brut (bilan fonctionnel). Les deux coexistent dans
  le pivot : `immobilisations_corporelles` (net) et
  `immobilisations_corporelles_brutes` (brut), plus `amortissements_corporelles`.
- **Propriété dérivée** : `credit_bail_dette_residuelle` = valeur_origine −
  amort_cumulés. Pas stocké, recalculé à la demande → une seule source de
  vérité.

### Société X 2023 (extrait)

```
entreprise = Societe_X
annee = 2023, devise = TND, référentiel = SCE
ca = 4 229 401, ebit = 1 364 124, résultat_net = 948 657
actif_total = 7 965 124, capitaux_propres = 2 983 490
dettes_financieres_lt = 3 688 389, dettes_financieres_ct = 440 478
dividendes (reconstitués) = 661 826
```

---

## Lot ch.1-1 — Ingestion et schéma pivot

**Fichier** : `analyse_financiere/adapters/sce_excel.py`

### Ce que fait le code

La fonction `charger_societe_x(excel, yaml)` lit l'Excel 3 feuilles de la
Société X et retourne une liste d'`EtatsFinanciers` (un par exercice). Elle :

1. Détecte automatiquement la ligne d'en-tête (les années en colonnes).
2. Parcourt chaque ligne, normalise le libellé (minuscule, sans accents).
3. Mappe le libellé vers un champ du pivot via une table `MAPPING_SCE`.
4. Reconnaît le motif **brute / « Moins : Amortissements » / net** et stocke
   les trois valeurs séparément (clé pour le bilan fonctionnel du ch.2).
5. Agrège les amortissements incorporelles + corporelles en
   `amortissements_cumules`.
6. Incorpore les données du YAML de retraitements (hors bilan, prêt société
   sœur, dettes acq. immos, crédit-bail, EENE, autres gains/pertes).
7. Reconstitue les dividendes par variation des CP (voir lot ch.2-3).

### Pourquoi ce choix

Le format SCE condense sur la même colonne, en trois lignes consécutives,
la valeur brute, l'amortissement et la valeur nette d'une immobilisation.
Un adaptateur naïf perdrait la décomposition. Celui-ci la préserve.

### Exemple Société X

Ligne « Immobilisations corporelles » = 7 253 810 (brut).
Ligne « Moins : Amortissements » = −1 049 249.
Ligne vide suivante = 6 204 561 (net).

Le code produit :
- `immobilisations_corporelles_brutes = 7 253 810` (pour C4 ch.2)
- `amortissements_corporelles = 1 049 249` (valeur absolue)
- `immobilisations_corporelles = 6 204 561` (net, pour le bilan comptable)

---

## Lot ch.1-2 — Correspondance sémantique des libellés

**Fichier** : `analyse_financiere/mapping.py` + `config/mapping_libelles.yaml`

### Ce que fait le code

La classe `MapperLibelles` associe un libellé source à un champ du pivot en
trois passes :
1. **Alias exact** (après normalisation : minuscule, sans accents).
2. **Regex** (patterns comme `property.*plant.*equipment`).
3. **Fuzzy matching** (rapidfuzz, score ≥ 85 par défaut).

La fonction `mapper_liste` retourne un `RapportMapping` qui contient les
postes non reconnus et calcule **précision / rappel** sur un jeu annoté.

### Exemple

- `"IMMOBILISATIONS CORPORELLES"` → `immobilisations_corporelles_brutes`
  (alias exact, score 100).
- `"Property, Plant and Equipment, Net"` → même champ (regex).
- `"Immobilisation corporelle"` (typo) → même champ (fuzzy, score ≈ 95).
- `"Lorem ipsum"` → None, journalisé dans `non_reconnus`.

### Mesure

Le test `test_precision_rappel` évalue le mapper sur 10 libellés SCE et
IFRS annotés à la main : **≥ 80 % précision et rappel** sont requis.

---

## Lot ch.1-3 — Contrôles qualité

**Fichier** : `analyse_financiere/quality.py`

### Ce que fait le code

Pour un `EtatsFinanciers`, la fonction `controler()` renvoie une liste de
`Controle(nom, niveau, message)`, où `niveau ∈ {OK, Avertissement, Bloquant}`.
Contrôles implémentés :

1. **Équation fondamentale** : `|actif_total − total_passif| / actif_total < 1 %`.
2. **Sous-totaux actif** : `AC + ANC ≈ actif_total`.
3. **Sous-totaux CP** : `capital + réserves + RR + RN ≈ capitaux_propres`.
4. **Signes attendus** : actif_total et CA doivent être positifs.
5. **Capitaux propres négatifs** → Avertissement (faillite technique,
   certains ratios deviennent non significatifs).
6. **Valeurs manquantes critiques** (ca, actif_total, capitaux_propres) →
   Bloquant.
7. **Cohérence SIG** : REX reconstitué par la cascade doit être ≈ EBIT
   déclaré.

### Société X

Les 7 contrôles passent en OK. L'équation fondamentale donne un écart
d'arrondi d'Excel < 0,02 TND (on l'accepte à 1 %).

---

## Lot ch.1-4 — Moteur de ratios déclaratif

**Fichiers** : `analyse_financiere/ratios.py` + `config/ratios.yaml`

### Ce que fait le code

Les ratios ne sont **pas codés en dur** : ils sont décrits dans un YAML
(id, famille, formule texte, sens favorable, unité, repère, garde-fous).
Le moteur évalue la formule via un **visiteur AST restreint** : seuls les
opérateurs arithmétiques, les noms de variables et quelques fonctions sûres
(`abs`, `min`, `max`) sont autorisés. Pas d'`eval()`, pas d'import.

### Exemple de ratio déclaratif

```yaml
- id: dette_nette_ebitda
  famille: structure
  formule: "(dettes_financieres_lt + dettes_financieres_ct - liquidites) / (ebit + dotations)"
  sens_favorable: plus_bas
  unite: annees
  repere: { seuil: 3.0, operateur: "<" }
```

### Garde-fous

- **Division par zéro** → `valeur = None`, note « Non calculable ».
- **Capitaux propres négatifs** (décoration `capitaux_propres_negatifs: non_significatif`)
  → `None`, note « non significatif ».
- **Stocks nuls** (DIO sur Société X) → `None`, note « non applicable ».

### Résultats Société X 2023 (vs corrigé C2)

| Ratio | Calculé | Attendu PDF |
|---|---:|---:|
| Liquidité générale | 1,28 | 1,28 |
| Endettement global | 1,67 | 1,67 |
| Dette nette / EBITDA | 2,45 | 2,45 |
| Couverture intérêts | 6,16 | 6,16 |
| Marge nette | 22,4 % | 22,4 % |
| ROE | 31,8 % | 31,8 % |
| DSO | 62 j | 62 j |
| DPO | 65 j | 65 j |

Tous les 16 ratios × 2 exercices sont vérifiés en pytest.

---

## Lot ch.1-5 — Benchmark

**Fichier** : `analyse_financiere/benchmark.py` + `data/ch1/benchmark_sectoriel_synthetique.csv`

### Ce que fait le code

Deux sources :
1. **Fichier CSV synthétique** (repli hors ligne) construit depuis
   Damodaran Online et BACH (Banque de France) — Q1, médiane, Q3 par
   secteur et par ratio.
2. **SEC EDGAR Frames API** (optionnel) : télécharge un concept XBRL pour
   toutes les sociétés d'un code SIC à une date. User-Agent descriptif
   obligatoire, cache local, temporisation 0,15 s pour respecter la
   limite SEC de 10 req/s.

Trois indicateurs par ratio :
- **Rang centile** (interpolation linéaire entre Q1, médiane, Q3).
- **Z robuste** : `(valeur − médiane) / (IQR × 0,7413)` — résiste aux outliers.
- **Feu tricolore** vert / orange / rouge selon le sens favorable du ratio.

### Pertinence pour une PME tunisienne

Le benchmark synthétique mixe des sources US (Damodaran) et européennes
(BACH). Pour une PME tunisienne, **un écart défavorable ne signifie pas
sous-performance** : la cherté du capital, les frais financiers nettement
plus élevés en Tunisie (taux directeur BCT 8 %), et les ratios de rotation
sectoriels locaux expliquent beaucoup des différences. Le feu doit se lire
comme **indicateur de positionnement**, pas comme un verdict absolu.

### Société X 2023 vs Services

Marge nette 22,4 % > Q3 Services (22 %) → **feu vert**. L'entreprise est
dans le haut de la distribution.

---

## Lot ch.1-6 — Règles expertes et commentaire

**Fichier** : `analyse_financiere/commentaire.py`

### Ce que fait le code

La fonction `regles_expertes()` applique **15 règles explicites** dérivées
du cours et les combine (ex. liquidité immédiate < 0,2 ET DPO > 60 → alerte
tension de trésorerie). Chaque alerte est classée en `force / attention /
risque`. Le gabarit Jinja2 `_GABARIT` compose un commentaire Markdown
complet.

### Pas de LLM

Conformément au brief, **aucune génération de texte par un modèle de
langage**. Toutes les phrases sont des templates déterministes avec des
nombres interpolés. Le commentaire est **traçable** : chaque chiffre cité
provient directement du pivot.

### Extrait Société X 2023

> Situation 2 (FRNG insuffisant) — Une partie du BFR est financée par
> des concours bancaires.
>
> **Risques** : Liquidité immédiate 0,11 < 0,2 ; Combinaison liquidité
> immédiate faible + DPO élevé.
>
> **Forces** : Marge nette 22,4 % ; ROE 31,8 %.

---

## Lot ch.1-7 — Restitution

**Fichier** : `analyse_financiere/restitution.py` + `app.py` (Streamlit)

### Ce que fait le code

- **Rapport HTML autonome** : un fichier unique par entreprise × exercice,
  sans dépendance externe, avec un waterfall SIG en SVG inline, un tableau
  des ratios + feux, un tableau du bilan fonctionnel condensé + retraité,
  et le commentaire rédigé.
- **Dashboard Streamlit** : 5 onglets (Ratios / SIG & CAF / Bilan fonctionnel /
  Typologie & diagnostic / Données brutes). Sélection d'exercice dans la
  barre latérale.

### Commandes

```bash
python -m scripts.generer_rapports   # génère reports/Societe_X_2022.html, 2023.html
streamlit run app.py                  # dashboard sur http://localhost:8501
```

---

## Lot ch.2-1 — Extension du pivot

**Fichiers** : `analyse_financiere/pivot.py` (champs ch.2) +
`data/ch2/societe_x_retraitements.yaml`

Les champs ajoutés au pivot :
- **Valeurs brutes et amortissements** : pour le bilan fonctionnel, qui
  reclasse les immobilisations à leur valeur d'origine.
- **Hors bilan** : `eene`, `credit_bail_valeur_origine`, `credit_bail_amort_cumules`.
- **Reclassement hors exploitation** : `pret_societe_soeur`,
  `dettes_acquisitions_immos`.
- **Affectation du résultat** : `dividendes` (reconstitués, voir ch.2-3).

Le YAML `societe_x_retraitements.yaml` reconstitue le tableau de la partie
B page 6 du chapitre 2 (hors bilan, dettes sur immos, autres gains/pertes).

---

## Lot ch.2-2 — Moteur de reclassement déclaratif

**Fichiers** : `analyse_financiere/reclassement.py` + `config/reclassement.yaml`

### Ce que fait le code

Deux modes :
- **Sans retraitement** (C4 condensé) : chaque poste va dans sa masse
  fonctionnelle par défaut. Les autres actifs/passifs courants mixtes
  restent entièrement en exploitation.
- **Avec retraitements** (C5) : la ventilation hors exploitation est
  appliquée (prêt société sœur → ACHE, dettes acq. immos → PCHE), plus
  le crédit-bail (ES/RS) et les EENE (ACE/TP).

### Lineage

Chaque masse (`Masse`) conserve la liste `lignes: list[LignePostee]` avec
`poste_source, montant, retraitement`. Exportable en CSV pour auditer.

### Résultats Société X (vs corrigé C4)

| | 2022 | 2023 |
|---|---:|---:|
| Emplois stables | 2 866 484 | 7 380 353 |
| Ressources stables | 4 573 101 | 7 781 628 |
| **FRNG** | **1 706 617** | **401 275** |
| BFR | 373 712 | 704 315 |
| TN | 1 332 905 | **−303 040** |

La trésorerie nette est devenue négative en 2023 — le FRNG ne couvre plus
le BFR, les concours bancaires paient la différence.

---

## Lot ch.2-3 — SIG, CAF, dividendes

**Fichier** : `analyse_financiere/sig_caf.py`

### Cascade SIG (Société X 2023, vs corrigé C1)

```
Production (= revenus)      4 229 401
− Consommations (achats +
   autres charges)           1 780 899
= Valeur ajoutée             2 448 503  (taux VA = 57,9 %)
− Charges de personnel         820 246
= EBE                        1 628 256  (taux EBE = 38,5 %)
− Dotations                    264 132
= REX                        1 364 124
± Charges fin. + autres        207 200
= RCAI                       1 156 924
− Impôt                        208 267
= Résultat net                 948 657
```

### CAF deux méthodes (vs corrigé C2)

- **Soustractive** : EBE − CF + autres gains − autres pertes − impôt
  = 1 628 256 − 221 611 + 15 198 − 787 − 208 267 = **1 212 789**.
- **Additive** : RN + dotations = 948 657 + 264 132 = **1 212 789**.
- **Écart = 0** → concordance OK (test unitaire).

Capacité de remboursement = dettes financières / CAF = 4 128 867 / 1 212 789
= **3,40 années** (zone de vigilance, seuil bancaire usuel = 4).

### Dividendes reconstitués (vs corrigé C3)

Formule :
```
dividendes_n = RN_(n-1) − (réserves_n − réserves_(n-1))
                        − (résultats_reportés_n − résultats_reportés_(n-1))
```

Pour 2023 :
```
dividendes_2023 = 845 182 − (34 833 − 0) − (0 − (−148 523))
                = 845 182 − 34 833 − 148 523
                = 661 826 TND
```

Le résultat 2022 a donc été affecté à 17,5 % en apurement de pertes
antérieures, 4,1 % en réserves et **78,3 % distribué en dividendes**.

Autofinancement 2023 = CAF − dividendes = 1 212 789 − 661 826 = **550 963 TND**.
Seulement 45 % de la CAF sert à l'investissement. Diagnostic sévère quand
on sait que l'entreprise a vidé sa trésorerie pour financer 4,46 M TND
d'investissements…

---

## Lot ch.2-4 — Invariants

**Fichier** : `tests/test_invariants.py`

Six invariants vérifiés en pytest sur les deux exercices :

1. **A = CP + P** (tolérance 1 TND d'arrondi Excel).
2. **FRNG − BFR = TN** (sans retraitement).
3. **FRNG − BFR = TN** (avec retraitements).
4. **CAF soustractive = CAF additive** (tolérance 1 TND).
5. **Le crédit-bail laisse le FRNG inchangé** :
   - +valeur origine en ES,
   - +amort cumulés en RS,
   - +dette résiduelle en RS,
   - RS − ES inchangé (valeur origine = amort + dette résiduelle).
6. **EENE : BFR + EENE, TN − EENE** → FRNG inchangé, BFR + TN inchangé.

---

## Lot ch.2-5 — Retraitements (C5 recalculé)

Le corrigé C5 est absent du PDF. Je l'ai recalculé rigoureusement depuis
les données de la partie B.

### 2023 retraité

| Poste | Sans | Avec retraitement |
|---|---:|---:|
| Emplois stables | 7 380 353 | **7 980 353** (+600 000 CB) |
| Ressources stables | 7 781 628 | **8 381 628** (+240 000 amort CB +360 000 dette CB) |
| FRNG | 401 275 | **401 275** (invariant) |
| ACE | 1 557 082 | 1 387 082 (−250 000 prêt sœur +80 000 EENE) |
| ACHE | 0 | **250 000** (prêt sœur) |
| PCE | 852 767 | 732 767 (−120 000 dettes acq. immos) |
| PCHE | 0 | **120 000** (dettes acq. immos) |
| BFRE | 704 315 | 654 315 |
| BFRHE | 0 | **130 000** |
| BFR total | 704 315 | 784 315 |
| TA | 137 438 | 137 438 |
| TP | 440 478 | 520 478 (+80 000 EENE) |
| **TN** | **−303 040** | **−383 040** |

### Vérification invariant

`FRNG − BFR = 401 275 − 784 315 = −383 040 = TN` ✓

### En jours de CA (base 360)

- FRNG : 401 275 / 4 229 401 × 360 = **34,2 j**
- BFR : 784 315 × 360 / 4 229 401 = **66,8 j**
- TN : −383 040 × 360 / 4 229 401 = **−32,6 j**

### Taux de couverture des ES

RS / ES = 8 381 628 / 7 980 353 = **1,050** → ES tout juste couverts.

---

## Récapitulatif — Comment ça tient ensemble

```
          +---------------+
 Excel ─► | sce_excel.py  | ─► EtatsFinanciers (pivot)
 YAML ─►  +---------------+          │
                                     ▼
                         +-----------------------+
                         |     quality.py        | → OK / Avert. / Bloquant
                         +-----------------------+
                                     │
                          ┌──────────┼──────────────────────┐
                          ▼          ▼                      ▼
                   ratios.py    sig_caf.py           reclassement.py
                      │             │                      │
                      ▼             ▼                      ▼
                   16 ratios    SIG, CAF (2 méth.)    FRNG, BFR, TN
                      │             │                      │
                      └─────────────┼──────────────────────┘
                                    ▼
                              commentaire.py
                                    │
                       ┌────────────┴─────────────┐
                       ▼                          ▼
                restitution.py               app.py
                (HTML autonome)              (Streamlit)
```
