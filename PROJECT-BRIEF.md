# PROJECT-BRIEF.md — Combat.AI
> Contexte universel pour toute IA (Claude Code, Grok, Gemini…) travaillant sur ce projet.
> **Dernière mise à jour : 28 Février 2026 — v2.4**

---

## 1. VISION PRODUIT

Combat.AI est un coach de boxe IA en temps réel, 100% navigateur.
MediaPipe Pose (webcam) → détection squelette → analyse coups → scoring.

**Cible** : Combattants amateurs/pro, coaches, fitness. SaaS à 20 EUR/mois.
**Stack** : HTML/CSS/JS pur + MediaPipe Pose (CDN). Zéro backend, zéro installation.
**Créateur** : Norman — pro fighter + dev (lancé 26 Déc 2025).

---

## 2. FICHIERS DU PROJET

| Fichier | Rôle | Statut |
|---------|------|--------|
| `combat-ai-v2.html` | **VERSION ACTIVE** — moteur complet v2.4 | ✅ actif |
| `combat-ai-v1.html` | Premier POC detection basique | 📦 archive |
| `index.html` | Landing page marketing + waitlist | ✅ actif |
| `dashboard.html` | Analytics sessions exportées JSON | ✅ actif |
| `show-stats.py` | Script Python affichage stats session | ✅ actif |
| `monitor.py` | Monitoring Python | ✅ actif |
| `export-excel.py` | Export Excel sessions (vide — à faire) | ⬜ vide |
| `metrics-launch.md` | Template suivi métriques lancement | ✅ actif |
| `metrics-log.json` | Données métriques | ✅ actif |
| `PROJECT-BRIEF.md` | Ce fichier — contexte projet | ✅ actif |

---

## 3. HISTORIQUE DES SESSIONS DE TEST

| Date | Version | Durée | Coups | Notes |
|------|---------|-------|-------|-------|
| 2026-02-17 | v2.0 | 325s | 201 | Assis — 100% faux positifs, bug checkStanding |
| 2026-02-17 | v2.0 | 69s | 4 | Debout, première vraie session |
| 2026-02-20 #1 | v2.1 | 76s | 3 | 0s bloqué au départ |
| 2026-02-20 #2 | v2.2 | 69s | 5 | 36s bloqué (checkStanding trop strict) |
| 2026-02-20 #3 | v2.3 | 188s | 12 | 25s bloqué (encore checkStanding) |
| Prochaine | v2.4 | — | ? | Objectif : 0s bloqué, comptage réaliste |

---

## 4. ÉTAT ACTUEL — v2.4 (28 Fév 2026)

### Ce qui fonctionne ✅
- UI complète : start screen, HUD, timer, rounds, end screen, export JSON
- MediaPipe Pose : squelette 33 landmarks, 30 fps
- Machine à états par bras (IDLE → EXTENDING → RETRACTING)
- Classification 4 techniques : JAB, CROSS, CROCHET, UPPERCUT
- Scoring réaliste (extension + vitesse + base)
- Mode Libre + Mode Combo (10 séquences)
- Pause/Resume, multi-rounds, repos entre rounds
- Audio : cloche boxe synthétique (Web Audio API)
- Export session JSON
- Dashboard analytics (`dashboard.html`)
- Debug overlay (touche D) : hipY / torso / kneeVis / standing / defFrames

### Corrections v2.4 appliquées ✅ (session 20 Fév 2026)
| # | Fix | Avant | Après |
|---|-----|-------|-------|
| 1 | MIN_MOTION_FRAMES | 2 | 1 |
| 2 | STANDING_THRESHOLD (torso) | 0.15 | 0.08 |
| 3 | checkStanding kneeVisibility | > 0.5 | > 0.3 |
| 4 | checkStanding legLength | > 0.10 | > 0.05 |
| 5 | checkStanding hipY | > 0.70 | > 0.50 |
| 6 | checkStanding mode | bloque détection | indicateur visuel seulement |
| 7 | classifyTechnique fallback | return null | return JAB/CROSS |
| 8 | detectDefense délai | instantané | 12 frames (~0.4s) |
| 9 | Debug overlay | absent | touche D |

### Problèmes ouverts ⚠️
| Priorité | Problème | Impact |
|----------|---------|--------|
| 🔴 P0 | Caméra ne s'active pas sur Z Fold 6 | Inutilisable mobile |
| 🔴 P0 | Accès hors WiFi impossible | Inutilisable hors domicile |
| 🟡 P1 | v2.4 pas encore testée debout en live | Résultats inconnus |
| 🟡 P1 | Classification CROCHET peu fiable | Confusion avec JAB |
| 🟠 P2 | Pas de persistance sessions (localStorage) | UX |
| 🟠 P2 | Pas de PWA (installable) | Mobile UX |
| 🟠 P2 | export-excel.py vide | Export Excel non dispo |

---

## 5. PIPELINE DE DÉTECTION — combat-ai-v2.html

### 5.1 Flux par frame

```
Camera 30fps → MediaPipe Pose (33 landmarks)
  → onResults()
      → dessine squelette
      → analyzeMovement()
          1. checkStanding()     → indicateur visuel (ne bloque plus)
          2. detectDefense()     → garde haute si 12 frames consécutives
          3. history push        → 5 dernières positions poignets
          4. smoothPosition()    → lissage 3-frames [0.2, 0.3, 0.5]
          5. vitesse             → frame N vs frame N-2
          6. filtre artefacts    → speed > 0.35 = ignore
          7. extension + angle   → dist horizontale poignet-épaule
          8. processArm() x2    → machine à états
          9. MAJ HUD
```

### 5.2 Machine à états (processArm)

```
IDLE → speed > speedMin → EXTENDING
EXTENDING → track peaks (vitesse, extension) → ralenti → RETRACTING
RETRACTING → validation:
    peakSpeed >= speedMin * 1.5       (vitesse suffisante)
    peakExt >= extensionMin * 0.7     (extension suffisante)
    frames >= MIN_MOTION_FRAMES (1)   (au moins 1 frame)
    now - lastPunchTime > cooldown    (pas trop rapproché)
  → OK: classifyTechnique() → registerPunch()
  → Reset IDLE
```

### 5.3 Classification techniques

| Technique | Condition principale | Seuils |
|-----------|---------------------|--------|
| UPPERCUT | nDirY < -0.6 (haut) | elbowAngle < 115 |
| CROCHET | abs(nDirX) > 0.6 (latéral) | 60 < elbowAngle < 135 |
| JAB | bras gauche, tendu | extH >= extensionMin, elbowAngle > 125 |
| CROSS | bras droit, tendu | extH >= extensionMin, elbowAngle > 125 |
| Fallback | extension moyenne | extH >= extensionMin*0.6, elbowAngle > 100 |

### 5.4 Scoring

```
extNorm = clamp((extension - 0.10) / 0.30, 0, 1)
spdNorm = clamp((speedMs - 1) / 10, 0, 1)
score   = round(extNorm*100*0.4 + spdNorm*100*0.4 + 20)   → cap 100

Force = speedMs*0.7 + (extension*10)*0.3
  < 3 = FAIBLE | 3-6 = MOYEN | 6-9 = FORT | 9+ = DEVASTATEUR
```

---

## 6. CONSTANTES (combat-ai-v2.html ~L800)

```javascript
MAX_REALISTIC_SPEED = 0.35   // au-dessus = artefact tracking
MIN_MOTION_FRAMES   = 1      // min frames pour valider un coup
STANDING_THRESHOLD  = 0.08   // ratio torse min (hanches-épaules)
NORM_TO_METERS      = 2.0    // 1 unité normalisée ≈ 2m réels
SPEED_FRAME_GAP     = 3      // comparaison frame N vs N-3
MAX_DISPLAY_SPEED   = 25     // cap affichage m/s
```

### CONFIG par difficulté

| Param | Easy | Normal | Hard |
|-------|------|--------|------|
| speedMin | 0.05 | 0.07 | 0.10 |
| extensionMin | 0.18 | 0.24 | 0.30 |
| cooldown (ms) | 500 | 400 | 300 |
| comboWindow (ms) | 2500 | 2000 | 1500 |

---

## 7. FONCTIONS CLÉS — RÉFÉRENCE RAPIDE

| Fonction | Rôle |
|----------|------|
| `checkStanding(landmarks)` | Détecte posture debout — visuel seulement depuis v2.4 |
| `analyzeMovement(landmarks)` | Pipeline principal, appelé chaque frame |
| `processArm(side, ...)` | Machine à états par bras |
| `classifyTechnique(...)` | JAB / CROSS / CROCHET / UPPERCUT |
| `registerPunch(...)` | Enregistrement + scoring + combo + HUD |
| `detectDefense(...)` | Garde haute (12 frames) |
| `normSpeedToMs(normSpeed)` | Vitesse normalisée → m/s affichage |
| `smoothPosition(history)` | Lissage 3-frames pondéré |
| `startSession()` | Init session + timer + cloche |
| `endSession()` | Fin + écran résultats |
| `exportSession()` | Export JSON téléchargeable |
| `callNewCombo()` | Mode Combo — nouvelle séquence |

---

## 8. UI / ÉCRANS

| Écran | Contenu |
|-------|---------|
| Start Screen | Durée round (1/2/3 min), Rounds (1/3/5/12), Mode (Libre/Combo), Sensibilité |
| HUD | Technique, Vitesse (m/s), Extension (%), Force, Total coups, Posture, Timer, Combo |
| Debug (D) | hipY, torso, kneeVis, standing, defFrames |
| End Screen | Total coups, Score moyen, Max combo, Meilleure vitesse, Meilleur score, Défenses, Breakdown techniques, Export |

---

## 9. ROADMAP PRIORISÉE

### 🔴 P0 — Bloquant immédiat

- [ ] **Fix caméra Z Fold 6** : fallback `getUserMedia` direct + erreur visible à l'écran
- [ ] **Accès hors WiFi** : déploiement HTTPS public (localtunnel ou hébergement statique)

### 🟡 P1 — Prochaine session de test

- [ ] **Test v2.4 en conditions réelles** : vérifier que 0s bloqué au départ, coups détectés dès le début
- [ ] **Calibrer MODE FACILE** : speedMin 0.05 peut encore générer du bruit de fond
- [ ] **Améliorer CROCHET** : souvent confondu avec JAB (même côté gauche)
- [ ] **Vitesse affichée** : vérifier que les m/s sont réalistes sur le Z Fold (fps différent)

### 🟠 P2 — Features

- [ ] **PWA** : manifest.json + service worker → installable sur écran d'accueil Z Fold
- [ ] **Persistance sessions** : localStorage → historique des 10 dernières sessions sans export
- [ ] **export-excel.py** : script Python pour convertir JSON → Excel (actuellement vide)
- [ ] **Mode calibration** : demander à l'utilisateur de faire 3 jabs pour auto-calibrer les seuils
- [ ] **Sounds on punch** : son d'impact à chaque coup détecté (Web Audio)

### 🟢 P3 — Vision long terme

- [ ] Détection kicks (jambes) — MediaPipe Pose a les landmarks chevilles
- [ ] Multi-utilisateur (coaching à distance)
- [ ] Intégration sac de frappe connecté (BLE)
- [ ] Backend pour persistence + leaderboard (Supabase ou Firebase)

---

## 10. LANCEMENT (26 Déc 2025)

Posté sur : Instagram, Twitter/X, Reddit (r/MMA, r/MachineLearning, r/SideProject), LinkedIn.
Voir `metrics-launch.md` pour les URLs et le template de suivi.

**Waitlist** : Google Form — objectif SaaS 20 EUR/mois.

---

## 11. DÉPENDANCES EXTERNES

```html
<!-- CDN MediaPipe (pas de npm, pas de bundler) -->
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js">
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/control_utils/control_utils.js">
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js">
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js">
```

MediaPipe Pose config :
- `modelComplexity: 1` (medium — bon équilibre perf/précision)
- `smoothLandmarks: true`
- `minDetectionConfidence: 0.5`
- `minTrackingConfidence: 0.5`

---

## 12. DÉMARRAGE RAPIDE

```bash
# Desktop — double-clic sur combat-ai-v2.html

# Serveur local HTTPS (requis pour caméra mobile sur réseau local)
cd /tmp
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 7 -nodes \
  -subj "/CN=combat-ai" 2>/dev/null
python3 /tmp/serve_combat.py &
# → https://[TON_IP]:8443/combat-ai-v2.html

# Tunnel public HTTPS (accès hors WiFi)
npx localtunnel --port 8080
# → https://xxx.loca.lt/combat-ai-v2.html
```

---

*Généré par Claude Code — 28 Février 2026*
