dosecoef 2.0.0 :
Passage à python 3.6.


dosecoef 1.1.0 :
- Ajout dose transcutané.
- Passage utf-8


dosecoef 1.0.5 :
Passage à python 2.6 et numpy.


dosecoef 1.0.4 :
- Correction Bug (rev. >= 1290): si l'isotope est absent d'ECRIN mais dans la liste de
référence (Ref.pxs), dosecoef retourne 0. et émet un warning.


dosecoef 1.0.3 :
- Les solubilités par defaut sont prises en compte selon le JO 2003:
  En résumé:
   * Si dans le tableau 1.3 du JO (personnes du public), une solubilité est précisée (via une *), elle
  est utilisée.
   * Sinon, la solubilité par défaut proposée par le tableau 3.3 (travailleurs
  exposés) est utilsée.
   * Si aucune solubilité par défaut n'est trouvée dans les deux tableaux
  précdents, le système determinera la plus pénalisante à chaque fois
  (solubilité par défaut à "none" dans le fichier statique).
Un message warning prévient lorsqu'un isotope n'a pas de solubilité par
défaut.


dosecoef 1.0.2 :

- Correctifs (bug #4). Gestion des isotopes du Mercure. Par défaut, les isotopes standards sont supposés de la forme organique.
  Hg-xxx_HG equivaut donc à Hg-xxx.
  Pour les formes chimiques inorganiques (HI) et organiques (HG) la granulo par défaut vaut 1.0 (comme pour les iso particulaires std).
- Correctifs (bug #24)


dosecoef 1.0.1 :

- Traitement du cas particulier ou la solubilité par défaut n'existe pas pour la cible choisie.
  dosecoef lève un warning et utilise la plus pénalisante.
- Si pour la cible travailleur, une VA n'existe pas, dosecoef utilise la cible adulte et lève un warning.
- L'utilisation ou pas de majuscules pour la dénomination de la cible ou de la voie d'atteinte n'engendre plus d'erreur (utilisation manuelle de dosecoef).
- Amélioration gestion des erreurs et log en unicode.
- Fichiers Coef et solu testes sur la liste d'isotopes du fichier de référence Ref.pxs.
- Correctif sur anomalie #2, #3, #24 du bug tracker de consx.
- Modification de forme des fichiers statiques (None => none) (Les anciens fichiers SolubDefault.pxs ne sont plus compatibles!).


Bug connus :
 ras.
