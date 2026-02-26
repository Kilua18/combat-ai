# PROJECT-BRIEF.md - Combat.AI

> **Ce fichier sert de contexte pour toute IA (Claude Code, Grok, Gemini, etc.) travaillant sur ce projet.**
> Derniere mise a jour : 26 Fevrier 2026

---

## 1. VISION PRODUIT

Combat.AI est un coach de boxe IA en temps reel qui fonctionne 100% dans le navigateur.
Le systeme utilise MediaPipe Pose pour tracker le squelette du corps via webcam/camera telephone,
puis analyse chaque mouvement pour detecter et scorer des coups de boxe (jab, cross, crochet, uppercut).

**Cible** : Combattants amateurs/pro, coach de boxe, fitness. Modele SaaS a 20EUR/mois.

**Stack** : HTML/CSS/JS pur + MediaPipe Pose (CDN). Zero backend, zero installation.

**Plateforme principale** : **Telephone mobile** (le PC du dev est trop lent pour MediaPipe).
Sur mobile : `modelComplexity: 0` (leger), resolution 640x480.
Sur desktop : `modelComplexity: 1` (moyen), resolution 1280x720.

---

## 2. ARCHITECTURE DES FICHIERS

| Fichier | Role | Lignes |
|---------|------|--------|
| `index.html` | Landing page marketing (SEO, waitlist) | ~580 |
| `combat-ai-v2.html` | **VERSION ACTIVE** - Moteur de detection complet | ~1988 |
| `dashboard.html` | Dashboard analytics (sessions exportees) | ~770 |
| `sw.js` | Service Worker PWA (cache = `combat-ai-v3`) | ~50 |
| `manifest.json` | PWA manifest | - |
| `export-excel.py` | Script Python pour convertir JSON sessions en Excel | - |
| `show-stats.py` | Script Python pour afficher stats sessions en CLI | - |
| `metrics-launch.md` | Template de suivi des metriques de lancement | ~185 |

**Le fichier principal est `combat-ai-v2.html`** - tout le moteur de detection est dedans.

---

## 3. PIPELINE DE DETECTION (combat-ai-v2.html)

### 3.1 Flux complet frame-par-frame

```
Camera (30fps) -> MediaPipe Pose (33 landmarks)
    -> onResults() [L1350] : dessine squelette
    -> analyzeMovement() [L1478] : pipeline principal
        1. checkStanding()     [L1420] -- GARDE : si assis, return early
        2. detectDefense()     [L1671] -- garde haute (2 mains pres du visage, tenue 12 frames)
        3. Position history    [~L1500] -- stocke 5 derniers frames par bras
        4. smoothPosition()    [L1385] -- lissage 3-frames pondere [0.2, 0.3, 0.5]
        5. Calcul vitesse      [~L1518] -- compare frame N vs frame N-2
        6. Filtre artefacts    [~L1536] -- speed > MAX_REALISTIC_SPEED (0.35) = ignore
        7. Calcul extension    [~L1540] -- distance horizontale poignet-epaule + angle coude
        8. processArm() x2     [L1564] -- machine a etats par bras
        9. MAJ HUD             [~L1555] -- affichage temps reel
```

### 3.2 Machine a etats par bras (processArm, L1564)

```
IDLE -> speed > speedMin -> EXTENDING
EXTENDING -> tracking peaks (vitesse, extension) -> vitesse ralentit -> RETRACTING
RETRACTING -> validation 4 criteres:
    - validSpeed:     peakSpeed >= speedMin * 1.5
    - validExtension: peakExt >= extensionMin * 0.7
    - validFrames:    frames >= MIN_MOTION_FRAMES (1)
    - validCooldown:  now - lastPunchTime > config.cooldown
    -> Si 4/4 valides: classifyTechnique() -> registerPunch()
    -> Reset a IDLE
```

### 3.3 Classification des techniques (classifyTechnique, L1623)

| Technique | Conditions | Seuils |
|-----------|-----------|--------|
| UPPERCUT G/D | mouvement vertical (nDirY < -0.6) + coude plie | elbowAngle < 115 |
| CROCHET G/D | mouvement lateral (abs(nDirX) > 0.6) + coude plie | 60 < elbowAngle < 135 |
| JAB | bras gauche, extension large, bras tendu | extH >= extensionMin, elbowAngle > 125 |
| CROSS | bras droit, extension large, bras tendu | extH >= extensionMin, elbowAngle > 125 |
| Fallback JAB/CROSS | extension moyenne | extH >= extensionMin * 0.6, elbowAngle > 100 |
| Fallback large | extension faible | extH >= extensionMin * 0.4 OU elbowAngle > 90 |

**Note** : Droitier suppose par defaut (bras gauche = JAB, bras droit = CROSS).
Pas de support gaucher pour l'instant.

### 3.4 Scoring (registerPunch, L1697)

```
extNorm = clamp((extension - 0.10) / 0.30, 0, 1)   // 0.10->0%, 0.40->100%
spdNorm = clamp((speedMs - 1) / 10, 0, 1)            // 1 m/s->0%, 11 m/s->100%
score = round(extNorm*100*0.4 + spdNorm*100*0.4 + 20) // 40% ext + 40% speed + 20% base
finalScore = min(score, 100)
```

Force estimee : `speedMs * 0.7 + (extension * 10) * 0.3`
- FAIBLE < 3 | MOYEN 3-6 | FORT 6-9 | DEVASTATEUR 9+

### 3.5 Detection defense (detectDefense, L1671)

```
leftNearFace  = abs(leftW.x - nose.x) < 0.10 AND leftW.y < nose.y + 0.10
rightNearFace = abs(rightW.x - nose.x) < 0.10 AND rightW.y < nose.y + 0.10
leftHandUp    = leftW.y < leftShoulder.y - 0.02
rightHandUp   = rightW.y < rightShoulder.y - 0.02
defending = toutes 4 conditions vraies, tenues 12 frames consecutifs (~0.4s a 30fps)
```

---

## 4. CONSTANTES & CONFIGURATION (L916-930)

### CONFIG par difficulte (L919-923)

| Param | Easy | Normal | Hard |
|-------|------|--------|------|
| speedMin | 0.05 | 0.07 | 0.10 |
| speedIdeal | 0.10 | 0.14 | 0.18 |
| extensionMin | 0.18 | 0.24 | 0.30 |
| cooldown (ms) | 500 | 400 | 300 |
| comboWindow (ms) | 2500 | 2000 | 1500 |

### Constantes globales

```
MAX_REALISTIC_SPEED = 0.35   // Au-dessus = artefact tracking (filtre dans processArm)
MIN_MOTION_FRAMES = 1        // Minimum frames pour valider un coup
STANDING_THRESHOLD = 0.15   // Seuil torse minimal (utilise dans checkStanding)
NORM_TO_METERS = 2.0         // 1 unite normalisee ~= 2 metres en espace reel
SPEED_FRAME_GAP = 3          // Compare frame N vs frame N-3 pour le calcul de vitesse
MAX_DISPLAY_SPEED = 25       // Cap affichage vitesse a 25 m/s
MAX_COMBO = 50               // Cap combo realiste
MIN_PUNCH_INTERVAL = 200     // ms - si 2 coups < 200ms c'est du bruit (reset combo)
DEFENSE_HOLD_REQUIRED = 12   // frames consecutifs pour valider une defense (~0.4s)
```

---

## 5. ETAT ACTUEL DES BUGS

### BUG #1 : checkStanding() -- RESOLU (v2.4)

**Ancien probleme** : 201 coups detectes assis. Resolu en v2.4 avec double critere :
- A) Genoux visibles (visibility > 0.3) ET en dessous des hanches (`legLength > 0.05`)
- B) Hanches dans la moitie basse de l'image (`hipY > 0.50`) -- cadrage tronc

**Code actuel (L1446-1449)** :
```javascript
const kneesDetected = kneeVisibility > 0.3 && legLength > 0.05;
const hipsLow       = hipY > 0.50;
let isStanding = goodTorso && (kneesDetected || hipsLow);
```

**Validation** : Sessions mobiles (Feb 26) montrent 10-40 coups en 65-87s = rythme normal.

---

### BUG #2 : normSpeedToMs() vitesses irrealistes -- RESOLU (v2.2)

**Ancien probleme** : Vitesses jusqu'a 229 m/s. Resolu avec calibration correcte.

**Formule actuelle (L1413-1416)** :
```javascript
const fps = Math.max(state.fps, 15);  // plancher fps
const speedMs = normSpeed * NORM_TO_METERS * fps / SPEED_FRAME_GAP;
return Math.min(speedMs, MAX_DISPLAY_SPEED);  // cap a 25 m/s
```

**Validation** : Sessions mobiles (Feb 26) : vitesses entre 1.0 et 7.0 m/s.
Jab amateur cible = 5-8 m/s. Resultats conformes.

---

### BUG #3 : Combo counter infini -- RESOLU (v2.2)

**Ancien probleme** : Combo atteignait 187 sur faux positifs. Resolu avec :
- Cap a 50 (`MAX_COMBO`)
- Reset si 2 coups < 200ms ET combo > 3 (detection bruit)

**Validation** : Combo max 13 en session facile (40 coups). Normal et coherent.

---

### BUG #4 : best_speed export = string au lieu de number -- ACTIF (mineur)

**Symptome** : Dans le JSON exporte, `best_speed` vaut `"4.6"` (string) au lieu de `4.6` (number).

**Cause** : `Math.max(...state.speeds).toFixed(1)` retourne une string, pas un nombre.

**Ligne affectee (L1901)** :
```javascript
best_speed: state.speeds.length > 0 ? Math.max(...state.speeds).toFixed(1) : 0,
//                                                                ^^^^^^^^^^
//                                               toFixed() retourne "4.6" pas 4.6
```

**Fix** : Entourer de `parseFloat()` comme pour `speed` dans l'historique (L1803).

**Impact** : Faible. Le dashboard peut planter si il fait un calcul numerique sur ce champ.

---

### NOTE : Cles JSON en francais sur telephone (version cachee PWA)

**Observation** : Le telephone exporte avec des cles francaises (`temps`, `vitesse`, `rond`,
`durée_secondes`) alors que le code actuel utilise des cles anglaises (`time`, `speed`,
`round`, `duration_seconds`).

**Cause probable** : Le service worker a mis en cache une ancienne version de l'app.
Le `CACHE_NAME = 'combat-ai-v3'` dans `sw.js` n'a pas change lors de la mise a jour,
donc l'ancien HTML reste en cache sur le telephone.

**Fix** : Bumper `CACHE_NAME` a `'combat-ai-v4'` dans `sw.js` pour forcer l'invalidation.
**ATTENTION** : Ne faire ce fix que quand l'app est stable, car ca force un rechargement
sur tous les appareils qui ont l'app installee.

---

## 6. SESSIONS DE TEST REELLES (26 Fevrier 2026 - Mobile)

### Session 1 - Difficultie Normale (87s)

| Stat | Valeur |
|------|--------|
| Total coups | 10 |
| Score moyen | 49/100 |
| Meilleur score | 77/100 (CROCHET G, 7.0 m/s) |
| Max combo | 3 |
| Meilleure vitesse | 7.0 m/s |
| Defenses | 2 |

Techniques : JAB x3, CROSS x2, CROCHET x2, UPPERCUT x3
Distribution des vitesses : 2.8 a 7.0 m/s -- **realiste, moteur OK**

### Session 2 - Difficulte Facile (65s)

| Stat | Valeur |
|------|--------|
| Total coups | 40 |
| Score moyen | 41/100 |
| Meilleur score | 72/100 (JAB, 4.0 m/s) |
| Max combo | 13 |
| Meilleure vitesse | 5.3 m/s |
| Defenses | 0 |

Techniques : JAB x22 (55%), CROSS x8, CROCHET x3, UPPERCUT x7
Distribution des vitesses : 1.0 a 5.3 m/s -- rythme rapide, majoritairement jabs

**Analyse** :
- Session 2 : spam de jabs -> scores bas (28-41 range), manque de puissance/extension
- Session 1 : moins de coups mais plus varies et mieux executes
- La defense ne se declenche pas quand on est en mode attaque pure (normal)
- Le combo 13 montre que la detection enchaine bien les frappes rapides en facile

---

## 7. FONCTIONS CLES -- REFERENCE RAPIDE

| Fonction | Ligne | Role |
|----------|-------|------|
| `checkStanding(landmarks)` | L1420 | Verifie posture debout (v2.4) |
| `normSpeedToMs(normSpeed)` | L1413 | Convertit vitesse norm -> m/s (v2.2 corrige) |
| `smoothPosition(history)` | L1385 | Lissage 3-frames pondere |
| `getAngle(a, b, c)` | L1374 | Calcul angle coude (degres) |
| `dist2D(a, b)` | L1381 | Distance euclidienne 2D |
| `analyzeMovement(landmarks)` | L1478 | Pipeline principal par frame |
| `processArm(side, ...)` | L1564 | Machine a etats par bras |
| `classifyTechnique(...)` | L1623 | Classification jab/cross/crochet/uppercut |
| `detectDefense(...)` | L1671 | Detection garde haute (12 frames) |
| `registerPunch(...)` | L1697 | Enregistrement + scoring + combo |
| `startSession()` | L1194 | Initialisation session |
| `endSession()` | L1828 | Fin session + ecran resultats |
| `exportSession()` | L1886 | Export JSON (bug best_speed string) |

---

## 8. UI / UX

### Ecrans
1. **Start Screen** : Config rounds/difficulte/mode (libre ou combo)
2. **HUD** : Technique, vitesse, extension, force, combo, timer, posture
3. **End Screen** : Stats finales, breakdown techniques, bouton export, bouton rejouer
4. **Pause Overlay** : Reprendre ou arreter

### Modes de jeu
- **Mode Libre** : Frappe comme tu veux, scoring en continu
- **Mode Combo** : 10 sequences predefinies a reproduire (jab-cross, jab-jab-cross, etc.)

### Debug
- Touche `D` sur clavier : affiche overlay debug en bas (hipY, torso, kneeVis, leg, hipsLow)
- Permet de diagnostiquer les problemes de detection de posture en direct

### Mobile specifique
- Bouton toggle camera (avant/arriere)
- Resolution reduite (640x480)
- MediaPipe modelComplexity: 0 (plus leger)
- Gestion erreur camera avec message clair et bouton "Reessayer"

---

## 9. ROADMAP

### RESOLU
- [x] checkStanding() trop permissif (BUG #1) -- v2.4
- [x] normSpeedToMs() vitesses irrealistes (BUG #2) -- v2.2
- [x] Combo counter sans cap (BUG #3) -- v2.2
- [x] PWA + mobile responsive
- [x] Gestion erreur camera (message visible)
- [x] Auto-reload sur nouveau service worker

### P0 - A faire (mineur)
- [ ] Fixer best_speed export : string -> number (1 ligne, L1901)

### P1 - Important
- [ ] Bump CACHE_NAME -> 'combat-ai-v4' pour forcer MAJ sur les telephones (apres stabilisation)
- [ ] Support gaucher (actuellement bras gauche = toujours JAB)
- [ ] Detection defense plus sensible (seuils actuels 0.10 horizontal tres stricts)

### P2 - Nice to have
- [ ] Historique des sessions en localStorage (pas besoin d'exporter manuellement)
- [ ] Sons/vibrations sur detection de coup
- [ ] Mode calibration (se mettre debout pour calibrer les seuils)
- [ ] Graphiques dans le dashboard

---

## 10. DEPENDENCIES EXTERNES

```html
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js">
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/control_utils/control_utils.js">
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js">
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js">
```

MediaPipe Pose config :
- `modelComplexity: 0` sur mobile, `1` sur desktop
- `smoothLandmarks: true`
- `minDetectionConfidence: 0.5`
- `minTrackingConfidence: 0.5`

---

## 11. FORMAT D'EXPORT JSON (version actuelle du code)

```json
{
  "app": "Combat.AI v2",
  "date": "2026-02-20T14:38:45.838Z",
  "duration_seconds": 76,
  "rounds": 1,
  "difficulty": "easy",
  "total_punches": 3,
  "avg_score": 43,
  "max_combo": 1,
  "best_speed": "4.6",   // BUG : string au lieu de number
  "best_score": 54,
  "defense_count": 4,
  "techniques": { "jab": 2, "cross": 1, "crochet": 0, "uppercut": 0 },
  "history": [
    { "time": 1822, "technique": "CROSS", "score": 28, "speed": 2.0, "round": 1 }
  ]
}
```

**Note** : Le telephone a peut-etre une version PWA cachee avec des cles francaises
(`temps`, `vitesse`, `rond`, `durée_secondes`). C'est une ancienne version. Le code
actuel produit les cles anglaises ci-dessus.

---

## 12. LANCEMENT / METRIQUES

Le projet a ete lance le 26 Dec 2025 sur :
- Instagram (Reel POC)
- Twitter/X
- Reddit (r/MMA, r/MachineLearning, r/SideProject)
- LinkedIn

Voir `metrics-launch.md` pour le template de suivi.

---

*Genere par Claude Code - 26 Fevrier 2026*
