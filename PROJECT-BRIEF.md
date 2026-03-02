# PROJECT-BRIEF.md â Combat.AI
> Contexte universel pour toute IA (Claude Code, Grok, Geminiâ¦) travaillant sur ce projet.
> **DerniÃ¨re mise Ã  jour : 28 FÃ©vrier 2026 â v2.4**

---

## 1. VISION PRODUIT

Combat.AI est un coach de boxe IA en temps rÃ©el, 100% navigateur.
MediaPipe Pose (webcam) â dÃ©tection squelette â analyse coups â scoring.

**Cible** : Combattants amateurs/pro, coaches, fitness. SaaS Ã  20 EUR/mois.
**Stack** : HTML/CSS/JS pur + MediaPipe Pose (CDN). ZÃ©ro backend, zÃ©ro installation.
**CrÃ©ateur** : Norman â pro fighter + dev (lancÃ© 26 DÃ©c 2025).

---

## 2. FICHIERS DU PROJET

| Fichier | RÃ´le | Statut |
|---------|------|--------|
| `combat-ai-v2.html` | **VERSION ACTIVE** â moteur complet v2.4 | â actif |
| `combat-ai-v1.html` | Premier POC detection basique | ð¦ archive |
| `index.html` | Landing page marketing + waitlist | â actif |
| `dashboard.html` | Analytics sessions exportÃ©es JSON | â actif |
| `show-stats.py` | Script Python affichage stats session | â actif |
| `monitor.py` | Monitoring Python | â actif |
| `export-excel.py` | Export Excel sessions (vide â Ã  faire) | â¬ vide |
| `metrics-launch.md` | Template suivi mÃ©triques lancement | â actif |
| `metrics-log.json` | DonnÃ©es mÃ©triques | â actif |
| `PROJECT-BRIEF.md` | Ce fichier â contexte projet | â actif |

---

## 3. HISTORIQUE DES SESSIONS DE TEST

| Date | Version | DurÃ©e | Coups | Notes |
|------|---------|-------|-------|-------|
| 2026-02-17 | v2.0 | 325s | 201 | Assis â 100% faux positifs, bug checkStanding |
| 2026-02-17 | v2.0 | 69s | 4 | Debout, premiÃ¨re vraie session |
| 2026-02-20 #1 | v2.1 | 76s | 3 | 0s bloquÃ© au dÃ©part |
| 2026-02-20 #2 | v2.2 | 69s | 5 | 36s bloquÃ© (checkStanding trop strict) |
| 2026-02-20 #3 | v2.3 | 188s | 12 | 25s bloquÃ© (encore checkStanding) |
| Prochaine | v2.4 | â | ? | Objectif : 0s bloquÃ©, comptage rÃ©aliste |

---

## 4. ÃTAT ACTUEL â v2.4 (28 FÃ©v 2026)

### Ce qui fonctionne â
- UI complÃ¨te : start screen, HUD, timer, rounds, end screen, export JSON
- MediaPipe Pose : squelette 33 landmarks, 30 fps
- Machine Ã  Ã©tats par bras (IDLE â EXTENDING â RETRACTING)
- Classification 4 techniques : JAB, CROSS, CROCHET, UPPERCUT
- Scoring rÃ©aliste (extension + vitesse + base)
- Mode Libre + Mode Combo (10 sÃ©quences)
- Pause/Resume, multi-rounds, repos entre rounds
- Audio : cloche boxe synthÃ©tique (Web Audio API)
- Export session JSON
- Dashboard analytics (`dashboard.html`)
- Debug overlay (touche D) : hipY / torso / kneeVis / standing / defFrames

### Corrections v2.4 appliquÃ©es â (session 20 FÃ©v 2026)
| # | Fix | Avant | AprÃ¨s |
|---|-----|-------|-------|
| 1 | MIN_MOTION_FRAMES | 2 | 1 |
| 2 | STANDING_THRESHOLD (torso) | 0.15 | 0.08 |
| 3 | checkStanding kneeVisibility | > 0.5 | > 0.3 |
| 4 | checkStanding legLength | > 0.10 | > 0.05 |
| 5 | checkStanding hipY | > 0.70 | > 0.50 |
| 6 | checkStanding mode | bloque dÃ©tection | indicateur visuel seulement |
| 7 | classifyTechnique fallback | return null | return JAB/CROSS |
| 8 | detectDefense dÃ©lai | instantanÃ© | 12 frames (~0.4s) |
| 9 | Debug overlay | absent | touche D |

### ProblÃ¨mes ouverts â ï¸
| PrioritÃ© | ProblÃ¨me | Impact |
|----------|---------|--------|
| ð´ P0 | CamÃ©ra ne s'active pas sur Z Fold 6 | Inutilisable mobile |
| ð´ P0 | AccÃ¨s hors WiFi impossible | Inutilisable hors domicile |
| ð¡ P1 | v2.4 pas encore testÃ©e debout en live | RÃ©sultats inconnus |
| ð¡ P1 | Classification CROCHET peu fiable | Confusion avec JAB |
| ð  P2 | Pas de persistance sessions (localStorage) | UX |
| ð  P2 | Pas de PWA (installable) | Mobile UX |
| ð  P2 | export-excel.py vide | Export Excel non dispo |

---

## 5. PIPELINE DE DÃTECTION â combat-ai-v2.html

### 5.1 Flux par frame

```
Camera 30fps â MediaPipe Pose (33 landmarks)
  â onResults()
      â dessine squelette
      â analyzeMovement()
          1. checkStanding()     â indicateur visuel (ne bloque plus)
          2. detectDefense()     â garde haute si 12 frames consÃ©cutives
          3. history push        â 5 derniÃ¨res positions poignets
          4. smoothPosition()    â lissage 3-frames [0.2, 0.3, 0.5]
          5. vitesse             â frame N vs frame N-2
          6. filtre artefacts    â speed > 0.35 = ignore
          7. extension + angle   â dist horizontale poignet-Ã©paule
          8. processArm() x2    â machine Ã  Ã©tats
          9. MAJ HUD
```

### 5.2 Machine Ã  Ã©tats (processArm)

```
IDLE â speed > speedMin â EXTENDING
EXTENDING â track peaks (vitesse, extension) â ralenti â RETRACTING
RETRACTING â validation:
    peakSpeed >= speedMin * 1.5       (vitesse suffisante)
    peakExt >= extensionMin * 0.7     (extension suffisante)
    frames >= MIN_MOTION_FRAMES (1)   (au moins 1 frame)
    now - lastPunchTime > cooldown    (pas trop rapprochÃ©)
  â OK: classifyTechnique() â registerPunch()
  â Reset IDLE
```

### 5.3 Classification techniques

| Technique | Condition principale | Seuils |
|-----------|---------------------|--------|
| UPPERCUT | nDirY < -0.6 (haut) | elbowAngle < 115 |
| CROCHET | abs(nDirX) > 0.6 (latÃ©ral) | 60 < elbowAngle < 135 |
| JAB | bras gauche, tendu | extH >= extensionMin, elbowAngle > 125 |
| CROSS | bras droit, tendu | extH >= extensionMin, elbowAngle > 125 |
| Fallback | extension moyenne | extH >= extensionMin*0.6, elbowAngle > 100 |

### 5.4 Scoring

```
extNorm = clamp((extension - 0.10) / 0.30, 0, 1)
spdNorm = clamp((speedMs - 1) / 10, 0, 1)
score   = round(extNorm*100*0.4 + spdNorm*100*0.4 + 20)   â cap 100

Force = speedMs*0.7 + (extension*10)*0.3
  < 3 = FAIBLE | 3-6 = MOYEN | 6-9 = FORT | 9+ = DEVASTATEUR
```

---

## 6. CONSTANTES (combat-ai-v2.html ~L800)

```javascript
MAX_REALISTIC_SPEED = 0.35   // au-dessus = artefact tracking
MIN_MOTION_FRAMES   = 1      // min frames pour valider un coup
STANDING_THRESHOLD  = 0.08   // ratio torse min (hanches-Ã©paules)
NORM_TO_METERS      = 2.0    // 1 unitÃ© normalisÃ©e â 2m rÃ©els
SPEED_FRAME_GAP     = 3      // comparaison frame N vs N-3
MAX_DISPLAY_SPEED   = 25     // cap affichage m/s
```

### CONFIG par difficultÃ©

| Param | Easy | Normal | Hard |
|-------|------|--------|------|
| speedMin | 0.05 | 0.07 | 0.10 |
| extensionMin | 0.18 | 0.24 | 0.30 |
| cooldown (ms) | 500 | 400 | 300 |
| comboWindow (ms) | 2500 | 2000 | 1500 |

---

## 7. FONCTIONS CLÃS â RÃFÃRENCE RAPIDE

| Fonction | RÃ´le |
|----------|------|
| `checkStanding(landmarks)` | DÃ©tecte posture debout â visuel seulement depuis v2.4 |
| `analyzeMovement(landmarks)` | Pipeline principal, appelÃ© chaque frame |
| `processArm(side, ...)` | Machine Ã  Ã©tats par bras |
| `classifyTechnique(...)` | JAB / CROSS / CROCHET / UPPERCUT |
| `registerPunch(...)` | Enregistrement + scoring + combo + HUD |
| `detectDefense(...)` | Garde haute (12 frames) |
| `normSpeedToMs(normSpeed)` | Vitesse normalisÃ©e â m/s affichage |
| `smoothPosition(history)` | Lissage 3-frames pondÃ©rÃ© |
| `startSession()` | Init session + timer + cloche |
| `endSession()` | Fin + Ã©cran rÃ©sultats |
| `exportSession()` | Export JSON tÃ©lÃ©chargeable |
| `callNewCombo()` | Mode Combo â nouvelle sÃ©quence |

---

## 8. UI / ÃCRANS

| Ãcran | Contenu |
|-------|---------|
| Start Screen | DurÃ©e round (1/2/3 min), Rounds (1/3/5/12), Mode (Libre/Combo), SensibilitÃ© |
| HUD | Technique, Vitesse (m/s), Extension (%), Force, Total coups, Posture, Timer, Combo |
| Debug (D) | hipY, torso, kneeVis, standing, defFrames |
| End Screen | Total coups, Score moyen, Max combo, Meilleure vitesse, Meilleur score, DÃ©fenses, Breakdown techniques, Export |

---

## 9. ROADMAP PRIORISÃE

### ð´ P0 â Bloquant immÃ©diat

- [ ] **Fix camÃ©ra Z Fold 6** : fallback `getUserMedia` direct + erreur visible Ã  l'Ã©cran
- [ ] **AccÃ¨s hors WiFi** : dÃ©ploiement HTTPS public (localtunnel ou hÃ©bergement statique)

### ð¡ P1 â Prochaine session de test

- [ ] **Test v2.4 en conditions rÃ©elles** : vÃ©rifier que 0s bloquÃ© au dÃ©part, coups dÃ©tectÃ©s dÃ¨s le dÃ©but
- [ ] **Calibrer MODE FACILE** : speedMin 0.05 peut encore gÃ©nÃ©rer du bruit de fond
- [ ] **AmÃ©liorer CROCHET** : souvent confondu avec JAB (mÃªme cÃ´tÃ© gauche)
- [ ] **Vitesse affichÃ©e** : vÃ©rifier que les m/s sont rÃ©alistes sur le Z Fold (fps diffÃ©rent)

### ð  P2 â Features

- [ ] **PWA** : manifest.json + service worker â installable sur Ã©cran d'accueil Z Fold
- [ ] **Persistance sessions** : localStorage â historique des 10 derniÃ¨res sessions sans export
- [ ] **export-excel.py** : script Python pour convertir JSON â Excel (actuellement vide)
- [ ] **Mode calibration** : demander Ã  l'utilisateur de faire 3 jabs pour auto-calibrer les seuils
- [ ] **Sounds on punch** : son d'impact Ã  chaque coup dÃ©tectÃ© (Web Audio)

### ð¢ P3 â Vision long terme

- [ ] DÃ©tection kicks (jambes) â MediaPipe Pose a les landmarks chevilles
- [ ] Multi-utilisateur (coaching Ã  distance)
- [ ] IntÃ©gration sac de frappe connectÃ© (BLE)
- [ ] Backend pour persistence + leaderboard (Supabase ou Firebase)

---

## 10. LANCEMENT (26 DÃ©c 2025)

PostÃ© sur : Instagram, Twitter/X, Reddit (r/MMA, r/MachineLearning, r/SideProject), LinkedIn.
Voir `metrics-launch.md` pour les URLs et le template de suivi.

**Waitlist** : Google Form â objectif SaaS 20 EUR/mois.

---

## 11. DÃPENDANCES EXTERNES

```html
<!-- CDN MediaPipe (pas de npm, pas de bundler) -->
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js">
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/control_utils/control_utils.js">
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js">
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js">
```

MediaPipe Pose config :
- `modelComplexity: 1` (medium â bon Ã©quilibre perf/prÃ©cision)
- `smoothLandmarks: true`
- `minDetectionConfidence: 0.5`
- `minTrackingConfidence: 0.5`

---

## 12. DÃMARRAGE RAPIDE

```bash
# Desktop â double-clic sur combat-ai-v2.html

# Serveur local HTTPS (requis pour camÃ©ra mobile sur rÃ©seau local)
cd /tmp
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 7 -nodes \
  -subj "/CN=combat-ai" 2>/dev/null
python3 /tmp/serve_combat.py &
# â https://[TON_IP]:8443/combat-ai-v2.html

# Tunnel public HTTPS (accÃ¨s hors WiFi)
npx localtunnel --port 8080
# â https://xxx.loca.lt/combat-ai-v2.html
```

---

*GÃ©nÃ©rÃ© par Claude Code â 28 FÃ©vrier 2026*
