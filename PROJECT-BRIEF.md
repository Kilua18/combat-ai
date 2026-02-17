# PROJECT-BRIEF.md - Combat.AI

> **Ce fichier sert de contexte pour toute IA (Claude Code, Grok, Gemini, etc.) travaillant sur ce projet.**
> Derniere mise a jour : Fevrier 2026

---

## 1. VISION PRODUIT

Combat.AI est un coach de boxe IA en temps reel qui fonctionne 100% dans le navigateur.
Le systeme utilise MediaPipe Pose pour tracker le squelette du corps via webcam, puis analyse chaque mouvement pour detecter et scorer des coups de boxe (jab, cross, crochet, uppercut).

**Cible** : Combattants amateurs/pro, coach de boxe, fitness. Modele SaaS a 20EUR/mois.

**Stack** : HTML/CSS/JS pur + MediaPipe Pose (CDN). Zero backend, zero installation.

---

## 2. ARCHITECTURE DES FICHIERS

| Fichier | Role | Lignes |
|---------|------|--------|
| `index.html` | Landing page marketing (SEO, waitlist) | ~300 |
| `combat-ai-v1.html` | Premier POC (detection basique) - archive | ~800 |
| `combat-ai-v2.html` | **VERSION ACTIVE** - Moteur de detection complet | ~1760 |
| `dashboard.html` | Dashboard analytics (sessions exportees) | ~770 |
| `metrics-launch.md` | Template de suivi des metriques de lancement | ~185 |
| `config.env` | Fichier de config sensible (vide, gitignore) | 0 |

**Le fichier principal est `combat-ai-v2.html`** - tout le moteur de detection est dedans.

---

## 3. PIPELINE DE DETECTION (combat-ai-v2.html)

### 3.1 Flux complet frame-par-frame

```
Camera (30fps) -> MediaPipe Pose (33 landmarks)
    -> onResults() [L1228-1249] : dessine squelette
    -> analyzeMovement() [L1325-1421] : pipeline principal
        1. checkStanding()     [L1348] -- GARDE : si assis, return early
        2. detectDefense()     [L1365] -- garde haute (2 mains pres du visage)
        3. Position history    [L1368] -- stocke 5 derniers frames
        4. smoothPosition()    [L1375] -- lissage 3-frames pondere [0.2, 0.3, 0.5]
        5. Calcul vitesse      [L1378] -- compare frame N vs frame N-2
        6. Filtre artefacts    [L1396] -- speed > MAX_REALISTIC_SPEED (0.35) = ignore
        7. Calcul extension    [L1400] -- distance horizontale poignet-epaule + angle coude
        8. processArm() x2     [L1411] -- machine a etats par bras
        9. MAJ HUD             [L1414] -- affichage temps reel
```

### 3.2 Machine a etats par bras (processArm, L1424-1480)

```
IDLE -> speed > speedMin -> EXTENDING
EXTENDING -> tracking peaks (vitesse, extension) -> vitesse ralentit -> RETRACTING
RETRACTING -> validation 4 criteres:
    - validSpeed: peakSpeed >= speedMin * 1.5
    - validExtension: peakExt >= extensionMin * 0.7
    - validFrames: frames >= MIN_MOTION_FRAMES (2)
    - validCooldown: now - lastPunchTime > config.cooldown
    -> Si 4/4 valides: classifyTechnique() -> registerPunch()
    -> Reset a IDLE
```

### 3.3 Classification des techniques (L1483-1518)

| Technique | Conditions | Seuils |
|-----------|-----------|--------|
| UPPERCUT | mouvement vertical (nDirY < -0.6) + coude plie | elbowAngle < 115 |
| CROCHET | mouvement lateral (abs(nDirX) > 0.6) + coude plie | 60 < elbowAngle < 135 |
| JAB | bras gauche, extension large, bras tendu | extH >= extensionMin, elbowAngle > 125 |
| CROSS | bras droit, extension large, bras tendu | extH >= extensionMin, elbowAngle > 125 |
| Fallback JAB/CROSS | extension moyenne | extH >= extensionMin * 0.6, elbowAngle > 100 |

### 3.4 Scoring (registerPunch, L1543-1633)

```
extNorm = clamp((extension - 0.10) / 0.30, 0, 1)   // 0.10->0%, 0.40->100%
spdNorm = clamp((speedMs - 1) / 10, 0, 1)            // 1 m/s->0%, 11 m/s->100%
score = round(extNorm*100*0.4 + spdNorm*100*0.4 + 20) // 40% ext + 40% speed + 20% base
finalScore = min(score, 100)
```

Force estimee : `speedMs * 0.7 + (extension * 10) * 0.3`
- FAIBLE < 3 | MOYEN 3-6 | FORT 6-9 | DEVASTATEUR 9+

---

## 4. CONSTANTES & CONFIGURATION (L800-814)

### CONFIG par difficulte (L803-807)

| Param | Easy | Normal | Hard |
|-------|------|--------|------|
| speedMin | 0.05 | 0.07 | 0.10 |
| speedIdeal | 0.10 | 0.14 | 0.18 |
| extensionMin | 0.18 | 0.24 | 0.30 |
| cooldown (ms) | 500 | 400 | 300 |
| comboWindow (ms) | 2500 | 2000 | 1500 |

### Constantes globales (L809-814)

```
MAX_REALISTIC_SPEED = 0.35   // Au-dessus = artefact tracking
MIN_MOTION_FRAMES = 2        // Minimum frames pour valider
STANDING_THRESHOLD = 0.15    // Ratio minimum torse pour etre debout
```

---

## 5. BUGS CRITIQUES DOCUMENTES

### BUG #1 : checkStanding() ne bloque PAS quand on est assis (L1287-1322)

**Symptome** : 201 coups detectes pendant un test ASSIS (sans boxer).

**Cause racine** : Le seuil utilise `torsoLength > 0.15 && fullLength > 0.25` ou :
- `torsoLength = hipY - shoulderY` (distance hanches-epaules en coordonnees normalisees 0-1)
- `fullLength = hipY - noseY` (distance hanches-nez)

**Probleme** : Quand on est assis, MediaPipe voit quand meme un torse (epaules + hanches sur la chaise). La distance `torsoLength` peut depasser 0.15 facilement si le torse est visible. Le check ne prend PAS en compte les genoux/chevilles, donc il ne peut pas distinguer "debout" de "assis avec le torse visible".

**Ligne affectee** : L1308 - `const isStanding = torsoLength > STANDING_THRESHOLD && fullLength > 0.25;`

**Impact** : Tout le moteur de detection est compromis. Les scores, combos, vitesses sont du bruit.

### BUG #2 : normSpeedToMs() produit des vitesses irrealistes (L1283-1285)

**Symptome** : Vitesses affichees jusqu'a 229 m/s (un vrai coup pro = 10-15 m/s max).

**Cause racine** : La formule `normSpeed * 2 * state.fps` est incorrecte.
- Le commentaire dit "1 unite norm ~= 2m" mais c'est une approximation grossiere
- A 30 fps avec normSpeed = 0.35 (le max avant filtre) : 0.35 * 2 * 30 = 21 m/s (deja trop)
- A 60 fps : 0.35 * 2 * 60 = 42 m/s (absurde)
- En pratique, les normSpeed ne sont pas filtrees avant d'etre passees a normSpeedToMs dans le HUD (L1417), seul le peakSpeed est filtre dans processArm

**Ligne affectee** : L1283-1284

**Impact** : Tous les scores de vitesse sont faux. Le scoring qui depend de speedMs est gonfle artificiellement.

### BUG #3 : Combo counter monte a 187 sans reset

**Symptome** : Combo atteint 187 pendant un test (assis, sans boxer).

**Cause racine** : Le combo reset depend d'un `setTimeout` de 2000ms (normal). Mais si des faux coups sont detectes en rafale (a cause du bug #1), chaque faux coup appelle `registerPunch()` -> `state.combo++` -> `clearTimeout` -> nouveau timeout. Le timeout est perpetuellement repousse et le combo ne reset jamais tant que les faux positifs continuent.

**Lignes affectees** : L1590-1598

**Impact** : Le combo n'a pas de cap, et depend directement de la fiabilite de la detection. Tant que le bug #1 n'est pas fixe, le combo sera toujours gonfle.

---

## 6. FONCTIONS CLES -- REFERENCE RAPIDE

| Fonction | Ligne | Role |
|----------|-------|------|
| `checkStanding(landmarks)` | L1287 | Verifie posture debout |
| `normSpeedToMs(normSpeed)` | L1283 | Convertit vitesse norm -> m/s |
| `smoothPosition(history)` | L1263 | Lissage 3-frames pondere |
| `analyzeMovement(landmarks)` | L1325 | Pipeline principal par frame |
| `processArm(side, ...)` | L1424 | Machine a etats par bras |
| `classifyTechnique(...)` | L1483 | Classification jab/cross/crochet/uppercut |
| `registerPunch(...)` | L1543 | Enregistrement + scoring + combo |
| `detectDefense(...)` | L1521 | Detection garde haute |
| `getAngle(a, b, c)` | L1252 | Calcul angle coude (degres) |
| `startSession()` | L1075 | Initialisation session |
| `endSession()` | L1655 | Fin session + ecran resultats |
| `exportSession()` | L1710 | Export JSON |

---

## 7. UI / UX

### Ecrans
1. **Start Screen** (L643-677) : Config round/difficulte/mode
2. **HUD** (L679-756) : Technique, vitesse, extension, force, combo, timer, posture
3. **End Screen** (L759-796) : Stats finales, breakdown techniques, export

### Modes de jeu
- **Mode Libre** : Frappe comme tu veux, scoring en continu
- **Mode Combo** : Sequences predefinies a reproduire (10 combos, L949-960)

### Defense
- Detection garde haute : 2 mains pres du visage + au-dessus des epaules (L1521-1529)
- Seuils : < 0.12 horizontal et < 0.15 vertical du nez

---

## 8. DONNEES DE TEST (Session assis - invalide)

Resultats d'une session ou le testeur etait **ASSIS** (pas debout) :
- 201 coups detectes (devrait etre ~0)
- Combo max : 187 (devrait etre 0)
- checkStanding() a retourne `true` alors que le testeur etait assis
- Vitesses jusqu'a 229 m/s (irrealiste)
- Distribution : jabs, cross, crochets detectes sans mouvement de boxe

**Conclusion** : Le moteur de detection ne distingue pas encore un vrai coup d'un mouvement de bras assis. L'UI est prete (~80%), l'algorithme non (~30%).

---

## 9. ROADMAP PRIORISEE

### P0 - Bloquant (Detection inutilisable)
- [ ] Fixer `checkStanding()` : ajouter detection genoux/chevilles, ratio hanches/genoux
- [ ] Fixer `normSpeedToMs()` : calibrer avec des vitesses reelles de coups
- [ ] Ajouter un cap au combo counter

### P1 - Important (Qualite des scores)
- [ ] Recalibrer les seuils de `processArm()` pour reduire les faux positifs
- [ ] Ajouter un seuil d'acceleration (pas juste vitesse) pour valider un coup
- [ ] Filtrer les mouvements non-intentionnels (bras qui tombent, gestes quotidiens)

### P2 - Nice to have (UX)
- [ ] Mode calibration (demander a l'utilisateur de se mettre debout pour calibrer)
- [ ] Historique des sessions (localStorage)
- [ ] Sons/vibrations sur detection de coup
- [ ] PWA pour mobile

---

## 10. LANCEMENT / METRIQUES

Le projet a ete lance le 26 Dec 2025 sur :
- Instagram (Reel POC)
- Twitter/X
- Reddit (r/MMA, r/MachineLearning, r/SideProject)
- LinkedIn

Voir `metrics-launch.md` pour le template de suivi.

---

## 11. DEPENDENCIES EXTERNES

```html
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js">
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/control_utils/control_utils.js">
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js">
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js">
```

MediaPipe Pose config (L1214-1226) :
- `modelComplexity: 1` (medium)
- `smoothLandmarks: true`
- `minDetectionConfidence: 0.5`
- `minTrackingConfidence: 0.5`

---

*Genere par Claude Code - Fevrier 2026*
