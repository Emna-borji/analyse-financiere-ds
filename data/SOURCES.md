# Sources des fichiers de `data/`

Chaque fichier téléchargé doit être documenté ici : URL exacte, date de
téléchargement, licence ou conditions d'usage, et ce que le fichier couvre
dans le cours (quelle difficulté il teste).

Les fichiers générés localement (YAML reconstruits depuis le PDF du cours,
copies « défauts injectés ») sont également listés.

---

## `data/ch1/CAS_1_Societe_X_SCE_2023_2022.xlsx`

- **Fourni par l'étudiant** (document du cours, chapitre 1 partie B).
- Format : SCE tunisien, 3 feuilles (Actif, CP_et_Passif, résultat).
- Montants en dinars tunisiens (TND).
- Exercices : 2022 et 2023.
- Rôle dans le projet : cas de référence du mini-projet 1 et du mini-projet 2.
  Les corrigés C1–C4 (ch.1) et C1–C5 (ch.2) servent de tests.

## `data/ch2/societe_x_retraitements.yaml`

- **Reconstruit localement** depuis `docs/Chapitre_2_Analyse_fonctionnelle.pdf`,
  partie B, page 6 (tableau des informations complémentaires + paragraphe
  suivant pour les éléments de l'état de résultat).
- Date de reconstruction : 2026-11-02.
- Rôle : paramètres de retraitement du bilan fonctionnel de la Société X.

---

## Fichiers à venir (lots suivants)

Les fichiers des entreprises B, C, D, E et le benchmark seront ajoutés après
sélection et validation par l'étudiant. Chacun aura :

- URL exacte de téléchargement,
- date de téléchargement,
- licence ou conditions d'usage (Creative Commons, domaine public, usage libre
  non commercial…),
- taux de change USD → TND utilisé si conversion (source + date du taux).

Les copies « défauts injectés » (déséquilibre A/P de 10, valeur manquante) seront
nommées `defauts_injectes_<fichier_source>.<ext>` et conserveront la provenance
originale dans leur en-tête.
