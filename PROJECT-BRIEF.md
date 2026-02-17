# COMBAT.AI -- BRIEF TECHNIQUE COMPLET

> Document de reference pour tout AI assistant travaillant sur ce projet.
> Derniere mise a jour: 17 Fevrier 2026
> Auteur du projet: Norman Nonnon

---

## CONTEXTE

**Nom:** Combat.AI
**Createur:** Norman Nonnon -- combattant MMA (2 victoires 2024), futur coach BPJEPS (mars 2026), developpeur autodidacte
**Concept:** Application web de coaching boxe/MMA par computer vision, 100% navigateur
**Stack:** HTML/CSS/JS vanilla + MediaPipe Pose (CDN) + Python (tooling)
**Status:** V2 fonctionnelle, UI prete, algorithme a calibrer

---

## ARCHITECTURE DU REPO

```
combat-ai/
├── index.html              (727 lines) Landing page marketing
├── combat-ai-v1.html       (290 lines) V1 originale (dec 2025)
├── combat-ai-v2.html       (1770 lines) Application principale
├── dashboard.html           (770 lines) Dashboard metriques/sessions
├── monitor.py               (283 lines) Monitoring social (entree manuelle + JSON log)
├── show-stats.py            (298 lines) Dashboard terminal (stats sociales + sessions)
├── export-excel.py          (vide)      A implementer
├── metrics-launch.md        (184 lines) Template de suivi lancement
├── metrics-log.json         (55 lines)  Historique metriques sociales
├── marketing/               (vide)      A peupler
└── combat-ai-session-*.json (4 fichiers) Sessions exportees
```

---

## COMBAT-AI-V2.HTML -- ARCHITECTURE DETAILLEE

### Stack & Dependances
- MediaPipe Pose via CDN (33 keypoints du corps)
- Camera Utils, Drawing Utils, Control Utils (CDN)
- Fonts: Orbitron (titres) + Rajdhani (corps)
- Web Audio API (sons synthetiques)
- Zero backend, zero build system

### Systeme de detection (analyzeMovement, ligne 1325)

**Landmarks utilises:**
- Epaules: 11 (gauche), 12 (droite)
- Coudes: 13 (gauche), 14 (droite)
- Poignets: 15 (gauche), 16 (droite)
- Hanches: 23 (gauche), 24 (droite)
- Nez: 0

**Pipeline de detection:**
1. `checkStanding()` -- Verifie posture debout (ratio hanches/epaules)
2. `detectDefense()` -- Garde haute (2 mains pres du visage au-dessus des epaules)
3. Stockage positions avec lissage (moyenne ponderee sur 3 frames: 0.2, 0.3, 0.5)
4. Calcul vitesse lissee (entre frame N-2 et frame N)
5. Filtrage artefacts (MAX_REALISTIC_SPEED = 0.35)
6. Calcul extensions horizontales
7. Calcul angles coudes via `getAngle()`
8. Machine a etats par bras via `processArm()` (idle -> extending -> retracting)
9. Classification via `classifyTechnique()` au moment du retour (retracting)

**Machine a etats par bras (processArm, ligne 1424):**
- **idle:** En attente. Transition vers `extending` si vitesse > speedMin
- **extending:** Mouvement en cours. Track peak speed, peak extension, motion frames
- **retracting:** Mouvement ralenti. Valide le coup si:
  - peakSpeed >= speedMin * 1.5
  - peakExtension >= extensionMin * 0.7
  - motionFrames >= MIN_MOTION_FRAMES (2)
  - Cooldown respecte (500ms easy, 400ms normal, 300ms hard)

**Classification (classifyTechnique, ligne 1483):**

| Technique | Condition | Side |
|-----------|-----------|------|
| UPPERCUT G/D | nDirY < -0.6 AND elbowAngle < 115 | G=left, D=right |
| CROCHET G/D | abs(nDirX) > 0.6 AND 60 < elbowAngle < 135 | G=left, D=right |
| JAB | extH >= extensionMin AND elbowAngle > 125 | left arm only |
| CROSS | extH >= extensionMin AND elbowAngle > 125 | right arm only |
| JAB/CROSS (fallback) | extH >= extensionMin*0.6 AND elbowAngle > 100 | left=JAB, right=CROSS |

Note: Suppose stance orthodox (gaucher = JAB main gauche, droite = CROSS main droite).
Le mirroring CSS (scaleX(-1)) ne change PAS les coordonnees MediaPipe.

**Scoring (registerPunch, ligne 1543):**
- Extension normalisee: (extension - 0.10) / 0.30, clamp [0,1]
- Vitesse normalisee: (speedMs - 1) / 10, clamp [0,1]
- Score = extension * 40% + vitesse * 40% + 20 points base
- Cap a 100

**Estimation de force:**
- `forceEstimate = speedMs * 0.7 + (extension * 10) * 0.3`
- 4 niveaux: FAIBLE (<3), MOYEN (3-6), FORT (6-9), DEVASTATEUR (9+)

### Systeme de combos

**Mode Combo (vs Mode Libre):**
- 10 sequences predefinies (JAB-CROSS, JAB-JAB-CROSS, JAB-CROSS-CROCHET, etc.)
- Combo caller affiche la sequence a realiser
- Validation en temps reel coup par coup
- Timeout 6 secondes par combo
- Feedback audio (playComboSuccess) et visuel

**Combo counter (mode libre):**
- Fenetre temporelle par difficulte (easy:2500ms, normal:2000ms, hard:1500ms)
- Reset a 0 apres timeout sans coup

### Configuration par difficulte

| Param | Easy | Normal | Hard |
|-------|------|--------|------|
| speedMin | 0.05 | 0.07 | 0.10 |
| speedIdeal | 0.10 | 0.14 | 0.18 |
| extensionMin | 0.18 | 0.24 | 0.30 |
| cooldown (ms) | 500 | 400 | 300 |
| comboWindow (ms) | 2500 | 2000 | 1500 |

### Timer & Rounds
- Duree configurable: 60/120/180 secondes
- Rounds: 1/3/5/12
- Repos entre rounds: 60 secondes (fixe)
- Cloche: 1x debut, 2x fin round, 3x fin session
- Beep 10 dernieres secondes
- Pause/Resume (barre espace ou bouton)

### Audio (Web Audio API)
- `playBell()` -- Cloche synthetique (800Hz -> 400Hz, decay 0.8s)
- `playBeep()` -- Beep court (600Hz square, 0.15s)
- `playComboSuccess()` -- Arpege ascendant (C5-E5-G5)

### Export JSON
- Structure: app, date, duration, rounds, difficulty, total_punches, avg_score, max_combo, best_speed, best_score, defense_count, techniques{}, history[]
- BUG: best_speed exporte en string (.toFixed(1) renvoie string)

---

## INDEX.HTML -- LANDING PAGE

- Nav fixe avec scroll effect
- Hero: badge BETA + CTA dual (demo + waitlist)
- Section demo: placeholder video + bouton play -> redirect vers v2
- 6 feature cards
- 4 techniques visuelles (JAB, CROSS, CROCHET, UPPERCUT)
- How it works en 3 etapes
- Waitlist form avec stockage localStorage
- **PROBLEME CRITIQUE:** Emails stockes en localStorage = perdus cross-device/navigateur

---

## DASHBOARD.HTML -- METRIQUES

- KPIs agreges: total sessions, coups, score moyen, max combo, waitlist count
- Metriques sociales (charge depuis metrics-log.json via fetch)
- Import de sessions JSON (file input + drag & drop)
- Graphiques CSS: repartition techniques + historique scores
- Export CSV
- Persistence via localStorage

---

## DONNEES DE SESSION REELLES (17 Fev 2026)

### Session 1 (combat-ai-session-2026-02-17.json)
- 325 sec, easy, 201 coups, avg 40/100, max combo 187, best speed 229.2 m/s
- Techniques: jab 1, **cross 142**, crochet 2, uppercut 56
- **PROBLEME:** Donnees aberrantes. 229.2 m/s = Mach 0.67. Combo 187 = reset defaillant.

### Session 2 (nonocombat-ai-session-2026-02-17.json)
- 68 sec, easy, 11 coups, avg 53/100, max combo 4, best speed 9.9 m/s
- Techniques: jab 1, cross 0, crochet 0, **uppercut 10**
- Biais fort vers uppercut

### Session 3 (combat-ai-session-2026-02-17 (2).json)
- 71 sec, easy, 14 coups, avg 61/100, max combo 3, best speed 9.9 m/s
- Techniques: jab 6, cross 0, crochet 3, uppercut 5

### Observations critiques
- **TOUTES ces sessions ont ete faites ASSIS, sans vraiment boxer** -- juste pour tester la fiabilite
- 201 coups detectes en position assise = le `checkStanding()` ne filtre PAS correctement
- Le CROSS detection est INCONSISTANT (142 dans session 1, 0 dans sessions 2 et 3)
- L'UPPERCUT est sur-detecte dans les sessions courtes
- Le speedMin easy (0.05) est trop bas, genere des faux positifs massifs meme assis
- La vitesse n'est pas plafonnee apres normSpeedToMs(), d'ou 229.2 m/s
- **Conclusion:** Le moteur de detection ne peut PAS distinguer un vrai coup d'un mouvement parasite en l'etat actuel. Le calibrage est la priorite absolue avant toute monetisation.

---

## BUGS CONNUS -- PAR PRIORITE

### P0 - Bloquants pour MVP
1. **checkStanding() ne filtre pas** -- 201 coups detectes en position assise. Le seuil STANDING_THRESHOLD (0.15) et la condition fullLength > 0.25 sont trop permissifs. La detection continue meme quand l'utilisateur ne boxe pas.
2. **Vitesse aberrante** -- normSpeedToMs() (ligne 1283) produit des valeurs impossibles (229 m/s). Le FPS variable amplifie le bruit.
3. **Combo counter sans reset fiable** -- Combo monte a 187 au lieu de se reset (ligne 1594)
4. **Classificateur inconsistant** -- Memes mouvements, resultats differents selon les sessions. Manque de validation profondeur/trajectoire.
5. **best_speed exporte en string** -- .toFixed(1) retourne un string (ligne 1725)

### P1 - Importants
5. **speedMin easy trop bas** -- 0.05 detecte du bruit comme des coups
6. **Waitlist localStorage** -- Emails perdus hors navigateur local
7. **metrics-log.json entree 1 corrompue** -- Texte terminal dans les champs numeriques
8. **export-excel.py vide**

### P2 - Ameliorations
9. Pas de kicks (round kick, teep, genou)
10. Pas de backend / persistence cross-session
11. Pas de video demo dans la landing page
12. Pas de stance selection (orthodox/southpaw)

---

## INFRASTRUCTURE MONITORING

### monitor.py
- Classe SocialMonitor avec entree manuelle des stats
- Scraping basique (Reddit uniquement, non fiable)
- Sauvegarde dans metrics-launch.md (append) et metrics-log.json
- Calcul de croissance entre 2 mesures

### show-stats.py
- Dashboard terminal avec couleurs ANSI
- Commandes: (none)=latest, all=historique, sessions=entrainement, report=complet
- Charge sessions depuis ./sessions/ et racine du projet

### metrics-log.json
- 2 entrees (26 dec 2025)
- Entree 1: corrompue (texte terminal dans les champs)
- Entree 2: IG 322 vues, 4 likes | TW 10 impressions | RD 0 upvotes | LI 4 impressions | 0 signups

---

## STATS LANCEMENT POC V1 (26 Dec 2025)

| Plateforme | Metrique | Valeur |
|------------|----------|--------|
| Instagram | Vues | 322 |
| Instagram | Likes | 4 |
| Twitter/X | Impressions | 10 |
| Reddit r/MMA | Upvotes | 0 |
| LinkedIn | Impressions | 4 |
| Google Form | Signups | 0 |

Liens:
- Instagram: instagram.com/reel/DSuRcB-DYWh/
- Reddit: reddit.com/user/No-Baseball8221/comments/1pw1iqh/
- LinkedIn: linkedin.com/posts/norman-nonnon-74248816a_combining-my-2-passions-fighting-coding
- Twitter: x.com/datingandeat/status/2004504927029322023

---

## PROCHAINES ETAPES RECOMMANDEES

### Phase 1 -- Fiabilite du moteur (critique)
- [ ] Plafonner normSpeedToMs() a 15 m/s max
- [ ] Fixer le combo reset (force reset si temps > comboWindow)
- [ ] Augmenter speedMin easy a 0.07-0.08
- [ ] Ajouter des assertions/guards dans classifyTechnique()
- [ ] Tester avec des sessions controlees (mouvements connus, resultats attendus)
- [ ] Corriger le type de best_speed en number dans l'export JSON

### Phase 2 -- Fonctionnalites manquantes
- [ ] Kicks (round kick, teep) via landmarks genoux (25,26) et chevilles (27,28)
- [ ] Selection de stance (orthodox/southpaw) dans le start screen
- [ ] Backend leger (Supabase gratuit) pour waitlist + persistence sessions
- [ ] Video demo pour la landing page
- [ ] PWA manifest pour installation mobile

### Phase 3 -- Monetisation
- [ ] Prix early adopter a 9.99 EUR/mois
- [ ] Stripe integration
- [ ] Mode free (1 round) vs premium (illimite)
- [ ] Historique multi-sessions dans l'app
