# PROJECT-BRIEF.md — Combat.AI
> Contexte universel pour toute IA (Claude Code, Grok, Gemini…) travaillant sur ce projet.
> **Dernière mise à jour : 28 Février 2026 — v2.4**

---

## 1. VISION PRODUIT

Combat.AI est un coach de boxe IA en temps réel, 100% navigateur.
MediaPipe Pose (webcam) → détection squelette → analyse coups → scoring.

**Créateur** : Norman — pro fighter + dev.
**Cible** : Combattants amateurs/pro, coaches, fitness.
**Modèle** : SaaS 20 EUR/mois.
**Stack** : HTML/CSS/JS pur + MediaPipe Pose (CDN). Zéro backend, zéro installation.
**Lancé** : 26 Décembre 2025 sur Instagram, Twitter/X, Reddit, LinkedIn.

---

## 2. FICHIERS DU PROJET

| Fichier | Rôle | Statut |
|---------|------|--------|
| `combat-ai-v2.html` | **VERSION ACTIVE** — moteur complet v2.4 | ✅ actif |
| `combat-ai-v1.html` | Premier POC detection basique | 📦 archive |
| `index.html` | Landing page marketing + waitlist Brevo | ✅ actif |
| `dashboard.html` | Analytics sessions exportées JSON | ✅ actif |
| `show-stats.py` | Script Python affichage stats session | ✅ actif |
| `monitor.py` | Monitoring Python | ✅ actif |
| `export-excel.py` | Export Excel sessions | ⬜ vide — à faire |
| `metrics-launch.md` | Template suivi métriques lancement | ✅ actif |
| `metrics-log.json` | Données métriques brutes | ✅ actif |
| `PROJECT-BRIEF.md` | Ce fichier — contexte projet | ✅ actif |

**Repo GitHub** : https://github.com/Kilua18/combat-ai
**URL publique** : https://kilua18.github.io/combat-ai/combat-ai-v2.html *(GitHub Pages)*

---

## 3. HISTORIQUE DES SESSIONS DE TEST

| Date | Version | Durée | Coups | Problème identifié |
|------|---------|-------|-------|--------------------|
| 2026-02-17 | v2.0 | 325s | 201 | Assis — 100% faux positifs, checkStanding cassé |
| 2026-02-17 | v2.0 | 69s | 4 | Première vraie session debout |
| 2026-02-20 #1 | v2.1 | 76s | 3 | 0s bloqué |
| 2026-02-20 #2 | v2.2 | 69s | 5 | 36s bloqué (checkStanding trop strict) |
| 2026-02-20 #3 | v2.3 | 188s | 12 | 25s bloqué (idem) |
| Prochaine | **v2.4** | — | ? | Objectif : 0s bloqué, comptage réaliste |

---

## 4. ÉTAT ACTUEL — v2.4 (28 Fév 2026)

### Ce qui fonctionne ✅
- UI complète : start screen, HUD temps réel, end screen, export JSON
- MediaPipe Pose : squelette 33 landmarks, ~30 fps
- Machine à états par bras : IDLE → EXTENDING → RETRACTING → validation
- Classification 4 techniques : JAB, CROSS, CROCHET, UPPERCUT + fallback
- Scoring réaliste (extension 40% + vitesse 40% + base 20%)
- Mode Libre + Mode Combo (10 séquences prédéfinies)
- Pause/Resume (Space), Stop (Escape), multi-rounds, repos entre rounds
- Audio : cloche boxe synthétique (Web Audio API)
- Export session JSON → compatible dashboard.html
- Debug overlay : touche **D** → hipY / torso / kneeVis / standing / defFrames
- Caméra robuste : fallback getUserMedia si MediaPipe Camera échoue
- Accès hors WiFi : GitHub Pages HTTPS (camera autorisée partout)

### Corrections v2.4 appliquées ✅ (28 Fév 2026)

| # | Fix | Avant | Après | Impact |
|---|-----|-------|-------|--------|
| 1 | MIN_MOTION_FRAMES | 2 | 1 | Coups rapides (1 seule frame) validés |
| 2 | STANDING_THRESHOLD | 0.15 | 0.08 | Torse court/cadrage serré accepté |
| 3 | checkStanding kneeVisibility | > 0.5 | > 0.3 | Genoux flous acceptés |
| 4 | checkStanding legLength | > 0.10 | > 0.05 | Genoux partiellement hors cadre OK |
| 5 | checkStanding hipY | > 0.70 | > 0.50 | Hanches dans moitié basse = debout |
| 6 | checkStanding mode | bloque détection | visuel seulement | Plus de coupure pendant les combos |
| 7 | classifyTechnique fallback | return null | JAB/CROSS | Zéro coup perdu silencieusement |
| 8 | detectDefense délai | instantané | 12 frames (~0.4s) | Faux positifs garde éliminés |
| 9 | Debug overlay | absent | touche D | Diagnostic live |
| 10 | Caméra robuste | crash silencieux | fallback + erreur visible | Z Fold 6 / Samsung |
| 11 | Vérification HTTPS | absente | erreur claire si HTTP | Mobile Chrome bloque camera HTTP |

---

## 5. PIPELINE DE DÉTECTION — combat-ai-v2.html

### 5.1 Flux par frame
```
Camera 30fps → MediaPipe Pose (33 landmarks)
  → onResults()
      → dessine squelette (vert/cyan)
      → analyzeMovement()  [si started && !paused && !resting]
          1. checkStanding()      → indicateur visuel (ne bloque plus depuis v2.4)
          2. detectDefense()      → garde haute si 12 frames consécutives
          3. history push         → 5 dernières positions poignets
          4. smoothPosition()     → lissage 3-frames [0.2, 0.3, 0.5]
          5. vitesse              → distance frame N vs N-2
          6. filtre artefacts     → speed > 0.35 = ignore (tracking perdu)
          7. extension + angle    → dist horizontale poignet-épaule + angle coude
          8. processArm() x2      → machine à états bras droit + gauche
          9. MAJ HUD              → technique, vitesse, extension, force
```

### 5.2 Machine à états par bras (processArm)
```
IDLE
  → speed > speedMin                     → EXTENDING (démarre tracking)
EXTENDING
  → toujours en mouvement                → track peakSpeed, peakExtension, frames++
  → vitesse tombe sous speedMin          → RETRACTING
RETRACTING
  → validation 4 critères :
      peakSpeed >= speedMin * 1.5        (vitesse suffisante)
      peakExt   >= extensionMin * 0.7    (extension suffisante)
      frames    >= 1                     (au moins 1 frame de mouvement)
      now - lastPunchTime > cooldown     (pas trop rapproché)
  → 4/4 OK : classifyTechnique() → registerPunch()
  → Reset → IDLE
```

### 5.3 Classification techniques

| Technique | Condition principale | Seuils |
|-----------|---------------------|--------|
| UPPERCUT | mouvement vertical (nDirY < -0.6) | elbowAngle < 115 |
| CROCHET | mouvement latéral (|nDirX| > 0.6) | 60 < elbowAngle < 135 |
| JAB | bras gauche, extension + bras tendu | extH >= extensionMin, elbowAngle > 125 |
| CROSS | bras droit, extension + bras tendu | extH >= extensionMin, elbowAngle > 125 |
| Fallback | extension moyenne | extH >= extensionMin*0.6, elbowAngle > 100 |

> Note : bras gauche = JAB (droitier). Si gaucher, il faudra inverser.

### 5.4 Scoring par coup
```
extNorm  = clamp((extension - 0.10) / 0.30, 0, 1)   → 0.10=0%, 0.40=100%
spdNorm  = clamp((speedMs - 1) / 10, 0, 1)            → 1m/s=0%, 11m/s=100%
score    = round(extNorm*100*0.4 + spdNorm*100*0.4 + 20)   → cap 100

Force = speedMs*0.7 + (extension*10)*0.3
  FAIBLE < 3 | MOYEN 3-6 | FORT 6-9 | DEVASTATEUR 9+
```

---

## 6. CONSTANTES (combat-ai-v2.html ~L800)

```javascript
MAX_REALISTIC_SPEED = 0.35    // au-dessus = artefact tracking, ignoré
MIN_MOTION_FRAMES   = 1       // min frames mouvement pour valider un coup
STANDING_THRESHOLD  = 0.08    // ratio torse min (distance hanches-épaules)
NORM_TO_METERS      = 2.0     // 1 unité normalisée ≈ 2 mètres réels
SPEED_FRAME_GAP     = 3       // comparaison frame N vs N-3
MAX_DISPLAY_SPEED   = 25      // cap affichage à 25 m/s
```

### CONFIG par difficulté

| Param | Facile | Normal | Expert |
|-------|--------|--------|--------|
| speedMin | 0.05 | 0.07 | 0.10 |
| extensionMin | 0.18 | 0.24 | 0.30 |
| cooldown ms | 500 | 400 | 300 |
| comboWindow ms | 2500 | 2000 | 1500 |

---

## 7. FONCTIONS CLÉS — RÉFÉRENCE RAPIDE

| Fonction | Rôle |
|----------|------|
| `checkStanding(landmarks)` | Détecte posture debout — visuel seulement depuis v2.4 |
| `analyzeMovement(landmarks)` | Pipeline principal, appelé chaque frame MediaPipe |
| `processArm(side, ...)` | Machine à états par bras (idle/extending/retracting) |
| `classifyTechnique(...)` | Retourne 'JAB' / 'CROSS' / 'CROCHET G' / 'UPPERCUT D' etc. |
| `registerPunch(...)` | Enregistrement + scoring + combo + MAJ HUD + history |
| `detectDefense(...)` | Garde haute — déclenche après 12 frames consécutives |
| `normSpeedToMs(normSpeed)` | Vitesse normalisée → m/s pour affichage |
| `smoothPosition(history)` | Lissage 3-frames pondéré [0.2, 0.3, 0.5] |
| `startSession()` | Init état + timer + cloche + mode combo |
| `endSession()` | Écran résultats + stats finales |
| `exportSession()` | Télécharge JSON session |
| `callNewCombo()` | Mode Combo — lance nouvelle séquence aléatoire |
| `showCameraError(msg)` | Affiche erreur caméra visible à l'écran |
| `startCameraFallback()` | getUserMedia direct si MediaPipe Camera échoue |

---

## 8. UI / ÉCRANS

| Écran | Éléments |
|-------|----------|
| **Start Screen** | Durée round (1/2/3 min), Rounds (1/3/5/12), Mode (Libre/Combo), Sensibilité (Facile/Normal/Expert) |
| **HUD** | Technique, Vitesse (m/s), Extension (%), Force, Total coups, Posture, Timer, Round, Combo counter + barre |
| **Technique Flash** | Nom technique + score/100 + qualité (EXCELLENT/BON/FAIBLE) — 600ms |
| **Debug (D)** | hipY, torso, kneeVis, standing, defFrames |
| **End Screen** | Total, Score moyen, Max combo, Meilleure vitesse, Meilleur score, Défenses, Breakdown techniques, Export JSON |
| **Erreur Caméra** | Message + bouton RÉESSAYER si HTTP ou permission refusée |

---

## 9. ROADMAP PRIORISÉE

### 🔴 P0 — À tester immédiatement
- [ ] **Test v2.4 en conditions réelles** sur Z Fold 6 via GitHub Pages
  - Vérifier : 0s bloqué au départ, coups détectés dès les 5 premières secondes
  - Vérifier : comptage réaliste (pas 201 coups assis, pas 3 coups en 76s debout)
  - Vérifier : gardes seulement quand la position est tenue vraiment

### 🟡 P1 — Après validation détection
- [ ] **Améliorer CROCHET** : souvent confondu avec JAB côté gauche
  - Idée : ajouter critère vitesse angulaire du coude (rotation vs translation)
- [ ] **Mode gaucher** : option sur start screen pour inverser JAB/CROSS
- [ ] **Calibration auto** : 3 jabs au départ → auto-ajuste speedMin et extensionMin
- [ ] **fps mobile** : vérifier que les seuils de vitesse sont corrects à 25 fps (Z Fold)

### 🟠 P2 — Features UX
- [ ] **PWA** : manifest.json + service worker → installable sur écran d'accueil Z Fold
- [ ] **Persistance sessions** : localStorage → 10 dernières sessions sans export
- [ ] **export-excel.py** : compléter le script Python (actuellement vide)
- [ ] **Son d'impact** : bip court à chaque coup validé (Web Audio déjà en place)
- [ ] **Historique sessions** dans end screen (localStorage)

### 🟢 P3 — Vision long terme
- [ ] Détection kicks (chevilles = landmarks 27-32 disponibles dans MediaPipe)
- [ ] Mode coach à distance (partage session live)
- [ ] Backend persistence + leaderboard (Supabase ou Firebase)
- [ ] Intégration sac de frappe connecté (BLE)

---

## 10. ACCÈS À L'APPLICATION

```
# Depuis n'importe où (HTTPS GitHub Pages) :
https://kilua18.github.io/combat-ai/combat-ai-v2.html

# En local desktop (double-clic) :
combat-ai-v2.html

# Serveur local HTTPS (réseau local WiFi) :
python3 /tmp/serve_combat.py &
→ https://[IP]:8443/combat-ai-v2.html
```

---

## 11. DÉPENDANCES EXTERNES

```html
<!-- CDN MediaPipe — pas de npm, pas de bundler -->
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js">
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/control_utils/control_utils.js">
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js">
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js">

<!-- Fonts Google -->
Orbitron (titres HUD) + Rajdhani (texte)
```

MediaPipe Pose config active :
- `modelComplexity: 1` — medium (équilibre perf/précision)
- `smoothLandmarks: true`
- `minDetectionConfidence: 0.5`
- `minTrackingConfidence: 0.5`

---

*Généré par Claude Code — 28 Février 2026*
