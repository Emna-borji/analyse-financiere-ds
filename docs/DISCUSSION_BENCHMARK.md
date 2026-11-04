# Discussion sur le benchmark EDGAR

## Ce qu'il est — ce qu'il n'est pas

Le fichier `data/ch1/benchmark_edgar_frames_2023.csv` est construit depuis
l'API publique **SEC EDGAR Frames** (`data.sec.gov`). Il contient, pour
l'exercice fiscal 2023 :

- **ROA, ROE, marge nette, autonomie financière** (rentabilité et
  structure financière) ;
- **liquidité générale, liquidité réduite** (court terme).

Chaque ratio est résumé par ses quartiles (Q1, médiane, Q3) sur la
population des **sociétés US à exercice calendaire** (`end = 2023-12-31`).
Après filtrage, **2 268 sociétés** sont retenues (soit ~35 % des ~6 400
dépôts XBRL annuels).

## Limites à connaître pour la présentation

### 1. Non sectoriel

Le filtrage est **temporel seulement** (sociétés à exercice calendaire).
Aucune restriction par code SIC ou par taille. La médiane croise donc une
société pharma, une banque régionale et une PME industrielle.

**Impact** : le benchmark reflète la distribution totale de l'économie
US cotée, pas la distribution **au sein du secteur** de la société
comparée. Il faut l'interpréter comme un repère large, pas comme une
médiane sectorielle Damodaran.

### 2. Biais small cap déficitaire sur le ROA

La médiane ROA 2023 ressort à **-0,09 %** (quasi nulle), tandis que la
marge nette médiane est à **+0,02 %**. Cela s'explique par le poids
important des **small caps biotech / tech déficitaires** dans l'univers
EDGAR coté : ces sociétés ont souvent des revenus faibles et des actifs
importants (R&D capitalisée, levée de fonds), donc un ROA négatif qui
tire la médiane vers le bas.

**Conséquence pratique** : toute société rentable sort rapidement au
dessus de la médiane. Societe X 2023, avec ROA = 11,9 %, obtient un
centile **> 90** et un feu vert. C'est cohérent mais la barre est basse
en absolu.

### 3. Population US, pas tunisienne

Les comparaisons avec Monoprix ou Societe X doivent intégrer que :

- le coût du capital en Tunisie est **significativement plus élevé** qu'aux
  US (taux directeur BCT ~8 %) ;
- les marges de distribution tunisiennes sont **plus compressées** à
  cause de l'inflation et du contrôle des prix ;
- la structure du bilan (fournisseurs > clients) est caractéristique de
  la distribution, mais la médiane inclut des secteurs à cycle inverse.

**Convention adoptée** : le benchmark EDGAR sert de **point de repère**
pour les ratios de rentabilité et de structure, pas pour les ratios de
rotation (DSO/DPO/DIO). Les ratios d'activité restent commentés en
absolu, avec les repères du cours (DSO Tunisie ~60 jours, DPO ~90 jours).

### 4. Provenance des valeurs

Les Frames API retournent la dernière valeur rapportée par chaque CIK
pour `end = 2023-12-31`. Cette valeur provient d'un :

- **10-K** (dépôt annuel) pour la grande majorité ;
- **10-K/A** (amendement) pour les sociétés ayant corrigé un rapport ;
- **10-Q** postérieur qui présente le 31/12 en comparatif.

Les trois cas citent le **même bilan annuel audité** par l'auditeur
inscrit à la SEC. Un test (`test_echantillon_depot_10k`) confirme sur
un échantillon de 10 CIK que les accessions correspondent bien à l'un
de ces trois types.

### 5. Comparaisons à prendre avec recul

- **Microsoft, Apple, Amazon** : exercice fiscal décalé (30 juin, 29 sept,
  31 déc) → Microsoft et Apple sont **exclus** par le filtre calendaire ;
  Amazon est inclus.
- **Sociétés déficitaires chroniques** (WeWork, Peloton) : incluses mais
  excluent les ratios dont le dénominateur est négatif (ROE avec CP
  négatifs).
- **Variations annuelles** : la médiane 2023 n'est pas celle de 2022.
  Pour une analyse multi-exercices, il faut recharger le benchmark
  pour chaque année (`python -m scripts.actualiser_benchmark_edgar 2022`).

## Alternative sectorielle (Damodaran Online)

Le fichier de repli `data/ch1/benchmark_sectoriel_synthetique.csv`
reconstitue, à partir des médianes publiées par Damodaran en janvier
2024, des quartiles sectoriels (**Services / Distribution / Industrie**).
C'est **moins frais** (dernière mise à jour manuelle) mais **plus
discriminant** par secteur.

Pour la présentation, les deux fichiers sont conservés et l'utilisateur
peut basculer via la sidebar du dashboard Streamlit.

## Recommandation de lecture

1. **Centile EDGAR** → situation vs. l'économie US globale ;
2. **Feu tricolore Damodaran** → situation vs. le secteur ;
3. **Repères du cours** (DSO ≤ 60 j, liquidité générale > 1) → règles de
   pouce indépendantes du benchmark.

Un diagnostic solide **croise les trois** et ne se contente pas d'un seul
chiffre.
