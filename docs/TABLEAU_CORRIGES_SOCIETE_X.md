# Societe X : valeurs calculees vs corriges (ch.1 C2 + ch.2 C1-C5)

Genere par `python -m scripts.tableau_corriges`. Les tolerances sont
celles utilisees dans les tests pytest (`tests/test_ch1_societe_x.py` et
`tests/test_ch2_societe_x.py`).

## Ch.1 C1 - Lecture common-size (tolerance 0.002 absolue)

### 2023

| Poste | Attendu | Calcule | Ecart | Tol | Statut |
|---|---:|---:|---:|---:|---|
| actifs_non_courants_pct | 0.7930 | 0.7929 | -0.0001 | 0.002 | OK |
| actifs_courants_pct | 0.2070 | 0.2071 | +0.0001 | 0.002 | OK |
| liquidites_pct | 0.0170 | 0.0173 | +0.0003 | 0.002 | OK |
| capitaux_propres_pct | 0.3750 | 0.3746 | -0.0004 | 0.002 | OK |
| passifs_non_courants_pct | 0.4630 | 0.4631 | +0.0001 | 0.002 | OK |
| passifs_courants_pct | 0.1620 | 0.1624 | +0.0004 | 0.002 | OK |

### 2022

| Poste | Attendu | Calcule | Ecart | Tol | Statut |
|---|---:|---:|---:|---:|---|
| actifs_non_courants_pct | 0.4720 | 0.4717 | -0.0003 | 0.002 | OK |
| actifs_courants_pct | 0.5280 | 0.5283 | +0.0003 | 0.002 | OK |
| liquidites_pct | 0.3290 | 0.3292 | +0.0002 | 0.002 | OK |
| capitaux_propres_pct | 0.6160 | 0.6155 | -0.0005 | 0.002 | OK |
| passifs_non_courants_pct | 0.2460 | 0.2457 | -0.0003 | 0.002 | OK |
| passifs_courants_pct | 0.1390 | 0.1388 | -0.0002 | 0.002 | OK |

## Ch.1 C2 - Tableau des ratios

Tolerances : jours = +/-1 ; grandes valeurs (|v|>50) = +/-1 ; ratios usuels = +/-0.02 ; pourcentages = +/-0.01.

### 2023

| Ratio | Attendu | Calcule | Ecart | Tol | Statut |
|---|---:|---:|---:|---:|---|
| liquidite_generale | 1.2800 | 1.2754 | -0.0046 | 0.02 | OK |
| liquidite_immediate | 0.1100 | 0.1063 | -0.0037 | 0.01 | OK |
| endettement_global | 1.6700 | 1.6697 | -0.0003 | 0.02 | OK |
| autonomie_financiere | 0.3750 | 0.3746 | -0.0004 | 0.01 | OK |
| gearing | 1.3400 | 1.3378 | -0.0022 | 0.02 | OK |
| dette_nette_ebitda | 2.4500 | 2.4514 | +0.0014 | 0.02 | OK |
| couverture_interets | 6.1600 | 6.1555 | -0.0045 | 0.02 | OK |
| marge_nette | 0.2240 | 0.2243 | +0.0003 | 0.01 | OK |
| marge_operationnelle | 0.3230 | 0.3225 | -0.0005 | 0.01 | OK |
| marge_ebitda | 0.3850 | 0.3850 | -0.0000 | 0.01 | OK |
| roe | 0.3180 | 0.3180 | -0.0000 | 0.01 | OK |
| roa | 0.1190 | 0.1191 | +0.0001 | 0.01 | OK |
| rotation_actif | 0.5300 | 0.5310 | +0.0010 | 0.01 | OK |
| dso | 62.0000 | 62.4083 | +0.4083 | 1.0 | OK |
| dpo | 65.0000 | 64.6392 | -0.3608 | 1.0 | OK |
| taux_effectif_impot | 0.1800 | 0.1800 | +0.0000 | 0.01 | OK |

### 2022

| Ratio | Attendu | Calcule | Ecart | Tol | Statut |
|---|---:|---:|---:|---:|---|
| liquidite_generale | 3.8100 | 3.8070 | -0.0030 | 0.02 | OK |
| liquidite_immediate | 2.3700 | 2.3722 | +0.0022 | 0.02 | OK |
| endettement_global | 0.6200 | 0.6246 | +0.0046 | 0.02 | OK |
| autonomie_financiere | 0.6160 | 0.6155 | -0.0005 | 0.01 | OK |
| gearing | -0.1000 | -0.0952 | +0.0048 | 0.01 | OK |
| dette_nette_ebitda | -0.2200 | -0.2191 | +0.0009 | 0.01 | OK |
| couverture_interets | 843 | 843.37 | +0.37 | 1.0 | OK |
| marge_nette | 0.2440 | 0.2443 | +0.0003 | 0.01 | OK |
| marge_operationnelle | 0.2790 | 0.2794 | +0.0004 | 0.01 | OK |
| marge_ebitda | 0.3390 | 0.3385 | -0.0005 | 0.01 | OK |
| roe | 0.3130 | 0.3134 | +0.0004 | 0.01 | OK |
| roa | 0.1930 | 0.1929 | -0.0001 | 0.01 | OK |
| rotation_actif | 0.7900 | 0.7897 | -0.0003 | 0.01 | OK |
| dso | 73.0000 | 73.2809 | +0.2809 | 1.0 | OK |
| dpo | 37.0000 | 37.2511 | +0.2511 | 1.0 | OK |
| taux_effectif_impot | 0.1340 | 0.1338 | -0.0002 | 0.01 | OK |

## Ch.2 C1 - Soldes intermediaires de gestion (tolerance +/-1 TND)

### 2023

| Solde | Attendu (TND) | Calcule | Ecart | Tol | Statut |
|---|---:|---:|---:|---:|---|
| production_exercice | 4 229 401 | 4 229 401.14 | +0.14 | 1 | OK |
| consommations_intermediaires | 1 780 899 | 1 780 898.59 | -0.41 | 1 | OK |
| valeur_ajoutee | 2 448 503 | 2 448 502.55 | -0.45 | 1 | OK |
| ebe | 1 628 256 | 1 628 256.27 | +0.27 | 1 | OK |
| rex | 1 364 124 | 1 364 124.43 | +0.43 | 1 | OK |
| rcai | 1 156 924 | 1 156 924.35 | +0.35 | 1 | OK |
| resultat_net | 948 657 | 948 656.97 | -0.03 | 1 | OK |

### 2022

| Solde | Attendu (TND) | Calcule | Ecart | Tol | Statut |
|---|---:|---:|---:|---:|---|
| production_exercice | 3 459 549 | 3 459 548.67 | -0.33 | 1 | OK |
| consommations_intermediaires | 1 633 250 | 1 633 249.72 | -0.28 | 1 | OK |
| valeur_ajoutee | 1 826 299 | 1 826 298.95 | -0.05 | 1 | OK |
| ebe | 1 171 051 | 1 171 050.91 | -0.09 | 1 | OK |
| rex | 966 547 | 966 546.77 | -0.23 | 1 | OK |
| rcai | 975 755 | 975 754.53 | -0.47 | 1 | OK |
| resultat_net | 845 182 | 845 181.63 | -0.37 | 1 | OK |

### Ratios de repartition (tolerance 0.005 absolue)

#### 2023

| Ratio | Attendu | Calcule | Ecart | Tol | Statut |
|---|---:|---:|---:|---:|---|
| taux_valeur_ajoutee | 0.5790 | 0.5789 | -0.0001 | 0.005 | OK |
| part_personnel | 0.3350 | 0.3350 | -0.0000 | 0.005 | OK |
| taux_ebe | 0.3850 | 0.3850 | -0.0000 | 0.005 | OK |
| poids_frais_financiers | 0.1360 | 0.1361 | +0.0001 | 0.005 | OK |

#### 2022

| Ratio | Attendu | Calcule | Ecart | Tol | Statut |
|---|---:|---:|---:|---:|---|
| taux_valeur_ajoutee | 0.5280 | 0.5279 | -0.0001 | 0.005 | OK |
| part_personnel | 0.3590 | 0.3588 | -0.0002 | 0.005 | OK |
| taux_ebe | 0.3390 | 0.3385 | -0.0005 | 0.005 | OK |
| poids_frais_financiers | 0.0010 | 0.0010 | -0.0000 | 0.005 | OK |

## Ch.2 C2 - Capacite d'autofinancement

Tolerances : CAF sous/add = +/-1 TND ; capacite remb. = +/-0.01 an.

### 2023

| Mesure | Attendu | Calcule | Ecart | Tol | Statut |
|---|---:|---:|---:|---:|---|
| caf_soustractive | 1 212 789 | 1 212 788.81 | -0.19 | 1 | OK |
| caf_additive | 1 212 789 | 1 212 788.81 | -0.19 | 1 | OK |
| capacite_remboursement | 3.4000 | 3.4044 | +0.0044 | 0.01 | OK |

### 2022

| Mesure | Attendu | Calcule | Ecart | Tol | Statut |
|---|---:|---:|---:|---:|---|
| caf_soustractive | 1 049 686 | 1 049 685.77 | -0.23 | 1 | OK |
| caf_additive | 1 049 686 | 1 049 685.77 | -0.23 | 1 | OK |
| capacite_remboursement | 1.1300 | 1.1295 | -0.0005 | 0.01 | OK |

## Ch.2 C3 - Dividendes 2023 (tolerance +/-1 TND)

| Mesure | Attendu | Calcule | Ecart | Tol | Statut |
|---|---:|---:|---:|---:|---|
| dividendes_2023 | 661 826 | 661 825.81 | -0.19 | 1 | OK |
| autofinancement_2023 | 550 963 | 550 963.00 | +0.00 | 1 | OK |

## Ch.2 C4 - Bilan fonctionnel sans retraitement (tolerance +/-1 TND)

### 2023

| Masse | Attendu | Calcule | Ecart | Tol | Statut |
|---|---:|---:|---:|---:|---|
| emplois_stables | 7 380 353 | 7 380 353.17 | +0.17 | 1 | OK |
| ressources_stables | 7 781 628 | 7 781 628.00 | +0.00 | 1 | OK |
| frng | 401 275 | 401 274.83 | -0.17 | 1 | OK |
| ace | 1 557 082 | 1 557 081.70 | -0.30 | 1 | OK |
| pce | 852 767 | 852 767.11 | +0.11 | 1 | OK |
| bfr | 704 315 | 704 314.59 | -0.41 | 1 | OK |
| ta | 137 438 | 137 438.01 | +0.01 | 1 | OK |
| tp | 440 478 | 440 477.77 | -0.23 | 1 | OK |
| tn | -303 040 | -303 039.76 | +0.24 | 1 | OK |
| **Invariant FRNG-BFR-TN** | 0 | 0.0000 | +0.0000 | 0.01 | OK |

### 2022

| Masse | Attendu | Calcule | Ecart | Tol | Statut |
|---|---:|---:|---:|---:|---|
| emplois_stables | 2 866 484 | 2 866 483.73 | -0.27 | 1 | OK |
| ressources_stables | 4 573 101 | 4 573 100.72 | -0.28 | 1 | OK |
| frng | 1 706 617 | 1 706 616.99 | -0.01 | 1 | OK |
| ace | 872 361 | 872 361.48 | +0.48 | 1 | OK |
| pce | 498 649 | 498 649.25 | +0.25 | 1 | OK |
| bfr | 373 712 | 373 712.24 | +0.24 | 1 | OK |
| ta | 1 442 247 | 1 442 246.70 | -0.30 | 1 | OK |
| tp | 109 342 | 109 341.95 | -0.05 | 1 | OK |
| tn | 1 332 905 | 1 332 904.75 | -0.25 | 1 | OK |
| **Invariant FRNG-BFR-TN** | 0 | 0.0000 | +0.0000 | 0.01 | OK |

## Ch.2 C5 - Bilan fonctionnel RETRAITE (recalcule, pas de corrige PDF)

Valeurs recalculees depuis la partie B du ch.2. Tolerance +/-1 TND.
Verification : FRNG retraite = FRNG non retraite (invariant credit-bail).

### 2023 retraite

| Masse | Attendu | Calcule | Ecart | Tol | Statut |
|---|---:|---:|---:|---:|---|
| emplois_stables | 7 980 353 | 7 980 353.17 | +0.17 | 1 | OK |
| ressources_stables | 8 381 628 | 8 381 628.00 | +0.00 | 1 | OK |
| frng | 401 275 | 401 274.83 | -0.17 | 1 | OK |
| ace | 1 387 082 | 1 387 081.70 | -0.30 | 1 | OK |
| ache | 250 000 | 250 000.00 | +0.00 | 1 | OK |
| pce | 732 767 | 732 767.11 | +0.11 | 1 | OK |
| pche | 120 000 | 120 000.00 | +0.00 | 1 | OK |
| bfre | 654 315 | 654 314.59 | -0.41 | 1 | OK |
| bfrhe | 130 000 | 130 000.00 | +0.00 | 1 | OK |
| bfr | 784 315 | 784 314.59 | -0.41 | 1 | OK |
| ta | 137 438 | 137 438.01 | +0.01 | 1 | OK |
| tp | 520 478 | 520 477.77 | -0.23 | 1 | OK |
| tn | -383 040 | -383 039.76 | +0.24 | 1 | OK |
| **Invariant FRNG-BFR-TN** | 0 | 0.0000 | +0.0000 | 0.01 | OK |

### 2022 retraite

| Masse | Attendu | Calcule | Ecart | Tol | Statut |
|---|---:|---:|---:|---:|---|
| emplois_stables | 3 466 484 | 3 466 483.73 | -0.27 | 1 | OK |
| ressources_stables | 5 173 101 | 5 173 100.72 | -0.28 | 1 | OK |
| frng | 1 706 617 | 1 706 616.99 | -0.01 | 1 | OK |
| ace | 922 361 | 922 361.48 | +0.48 | 1 | OK |
| ache | 0.0000 | 0.0000 | +0.0000 | 1 | OK |
| pce | 498 649 | 498 649.25 | +0.25 | 1 | OK |
| pche | 0.0000 | 0.0000 | +0.0000 | 1 | OK |
| bfre | 423 712 | 423 712.24 | +0.24 | 1 | OK |
| bfrhe | 0.0000 | 0.0000 | +0.0000 | 1 | OK |
| bfr | 423 712 | 423 712.24 | +0.24 | 1 | OK |
| ta | 1 442 247 | 1 442 246.70 | -0.30 | 1 | OK |
| tp | 159 342 | 159 341.95 | -0.05 | 1 | OK |
| tn | 1 282 905 | 1 282 904.75 | -0.25 | 1 | OK |
| **Invariant FRNG-BFR-TN** | 0 | 0.0000 | +0.0000 | 0.01 | OK |
