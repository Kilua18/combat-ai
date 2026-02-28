# PROJECT-BRIEF.md - Combat.AI

> **Ce fichier sert de contexte pour toute IA (Claude Code, Grok, Gemini, etc.) travaillant sur ce projet.**
> Derniere mise a jour : 28 Fevrier 2026

---

## 1. VISION PRODUIT

Combat.AI est un coach de boxe IA en temps reel qui fonctionne 100% dans le navigateur.
Le systeme utilise MediaPipe Pose pour tracker le squelette du corps via webcam/camera telephone,
puis analyse chaque mouvement pour detecter et scorer des coups de boxe (jab, cross, crochet, uppercut).

**Cible** : Combattants amateurs/pro, coach de boxe, fitness.
**Modele** : Freemium — Gratuit (5 modules) / Premium 9,90EUR/mois / Pro Coach 20EUR/mois.

**Stack** : HTML/CSS/JS pur + MediaPipe Pose (CDN). Zero backend sauf Cloudflare Worker pour la waitlist.

**Plateforme principale** : **Telephone mobile** (le PC du dev est trop lent pour MediaPipe).
Sur mobile : `modelComplexity: 0` (leger), resolution 640x480.
Sur desktop : `modelComplexity: 1` (moyen), resolution 1280x720.

**Deploiement** : GitHub Pages — https://kilua18.github.io/combat-ai/

---

## 2. ARCHITECTURE DES FICHIERS

| Fichier | Role | Lignes |
|---------|------|--------|
| `index.html` | Landing page marketing (SEO, pricing, waitlist, video demo) | ~379 |
| `combat-ai-v2.html` | **VERSION ACTIVE** - Moteur de detection + enregistrement video | ~2165 |
| `dashboard.html` | Dashboard analytics (sessions exportees) | ~770 |
| `emails.html` | Dashboard email Brevo (contacts, campagnes, welcome email) | ~344 |
| `sw.js` | Service Worker PWA (cache = `combat-ai-v3`) | ~49 |
| `manifest.json` | PWA manifest (fullscreen, portrait, icon SVG) | ~18 |
| `icon.svg` | Icone PWA "CAI" verte | - |
| `export-excel.py` | Script Python pour convertir JSON sessions en Excel | - |
| `show-stats.py` | Script Python pour afficher stats sessions en CLI | - |
| `monitor.py` | Script Python monitoring | ~283 |
| `metrics-launch.md` | Template de suivi des metriques de lancement | ~184 |

**Le fichier principal est `combat-ai-v2.html`** - tout le moteur de detection est dedans.

---

## 3. INFRASTRUCTURE & SERVICES

### Waitlist (index.html)
- **Frontend** : formulaire email dans `index.html` section waitlist
- **Backend** : Cloudflare Worker (`https://combat-ai-waitlist.kkamagra18.workers.dev`)
- **CRM** : Brevo (ex-Sendinblue) — collecte les emails, envoie les campagnes
- **Flow** : `index.html` → POST Cloudflare Worker → Brevo API v3

### Email Dashboard (emails.html)
- Page d'admin locale pour voir les contacts Brevo, envoyer des campagnes, gerer le welcome email
- Utilise l'API Brevo directement

### PWA (sw.js + manifest.json)
- Service Worker cache `combat-ai-v2.html`, `manifest.json`, `icon.svg`
- Strategie : cache-first pour l'app shell, network-only pour CDN (MediaPipe, Google Fonts)
- `CACHE_NAME = 'combat-ai-v3'` — bumper pour forcer MAJ sur les telephones
- Auto-reload via `controllerchange` listener dans combat-ai-v2.html

---

## 4. LANDING PAGE (index.html)

### Sections
1. **Nav** : Logo, liens (Features, Tarifs, Techniques, Comment ca marche, Demo live, Rejoindre)
2. **Hero** : Badge "BETA - ACCES ANTICIPE", titre, CTA (Essayer la demo + Rejoindre la waitlist)
3. **Demo** : Video `demo.mp4` en autoplay loop muted + bouton "Essayer en live"
4. **Features** : 6 cartes (Vision IA, Temps reel, 4 techniques, Score & combo, Defense, Export)
5. **Techniques** : 4 items (Jab, Cross, Crochet, Uppercut) avec emojis
6. **How it works** : 3 etapes (Ouvre ton navigateur, Lance un round, Progresse)
7. **Pricing** : 3 tiers (Gratuit 0EUR, Premium 9,90EUR/mois POPULAIRE, Pro Coach 20EUR/mois)
8. **Waitlist** : Formulaire email → Cloudflare Worker → Brevo
9. **Footer** : "Built by Norman — Combat.AI 2026"

### Pricing tiers
| Tier | Prix | Features |
|------|------|----------|
| Gratuit | 0EUR | 5 modules, detection 4 coups, score temps reel |
| Premium | 9,90EUR/mois | + historique illimite, export JSON, detection garde, nouvelles techniques |
| Pro Coach | 20EUR/mois | + dashboard multi-athletes, rapports progression, acces API, support prioritaire |

---

## 5. PIPELINE DE DETECTION (combat-ai-v2.html)

### 5.1 Flux complet frame-par-frame

```
Camera (30fps) -> MediaPipe Pose (33 landmarks)
    -> onResults() [L1444] : dessine squelette
    -> analyzeMovement() [L1572] : pipeline principal
        1. checkStanding()     [L1514] -- GARDE : si assis, return early
        2. detectDefense()     [L1765] -- garde haute (2 mains pres du visage, tenue 12 frames)
        3. Position history    [~L1594] -- stocke 5 derniers frames par bras
        4. smoothPosition()    [L1479] -- lissage 3-frames pondere [0.2, 0.3, 0.5]
        5. Calcul vitesse      [~L1612] -- compare frame N vs frame N-3
        6. Filtre artefacts    [~L1630] -- speed > MAX_REALISTIC_SPEED (0.35) = ignore
        7. Calcul extension    [~L1634] -- distance horizontale poignet-epaule + angle coude
        8. processArm() x2     [L1658] -- machine a etats par bras
        9. MAJ HUD             [~L1649] -- affichage temps reel
```

### 5.2 Machine a etats par bras (processArm)

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

### 5.3 Classification des techniques (classifyTechnique)

| Technique | Conditions | Seuils |
|-----------|-----------|--------|
| UPPERCUT G/D | mouvement vertical (nDirY < -0.6) + coude plie | elbowAngle < 115 |
| CROCHET G/D | mouvement lateral (abs(nDirX) > 0.6) + coude plie | 60 < elbowAngle < 135 |
| JAB | bras gauche, extension large, bras tendu | extH >= extensionMin, elbowAngle > 125 |
| CROSS | bras droit, extension large, bras tendu | extH >= extensionMin, elbowAngle > 125 |
| Fallback JAB/CROSS | extension moyenne | extH >= extensionMin * 0.6, elbowAngle > 100 |
| Fallback large | extension faible | extH >= extensionMin * 0.4 OU elbowAngle > 90 |

**Note** : Droitier suppose par defaut (bras gauche = JAB, bras droit = CROSS).

### 5.4 Scoring (registerPunch)

```
extNorm = clamp((extension - 0.10) / 0.30, 0, 1)   // 0.10->0%, 0.40->100%
spdNorm = clamp((speedMs - 1) / 10, 0, 1)            // 1 m/s->0%, 11 m/s->100%
score = round(extNorm*100*0.4 + spdNorm*100*0.4 + 20) // 40% ext + 40% speed + 20% base
finalScore = min(score, 100)
```

Force estimee : `speedMs * 0.7 + (extension * 10) * 0.3`
- FAIBLE < 3 | MOYEN 3-6 | FORT 6-9 | DEVASTATEUR 9+

### 5.5 Enregistrement video de session (NOUVEAU - 28 Fev 2026)

- Enregistre automatiquement la video de la camera pendant la session (MediaRecorder API)
- Preference : MP4 h264 > WebM VP9 > WebM (selon support navigateur)
- Bitrate : 2.5 Mbps, chunks de 1s
- A la fin de session : lecteur replay avec boutons Telecharger + Rejouer
- Section `#replay-section` visible apres fin de session

---

## 6. CONSTANTES & CONFIGURATION

### CONFIG par difficulte

| Param | Easy | Normal | Hard |
|-------|------|--------|------|
| speedMin | 0.05 | 0.07 | 0.10 |
| speedIdeal | 0.10 | 0.14 | 0.18 |
| extensionMin | 0.18 | 0.24 | 0.30 |
| cooldown (ms) | 500 | 400 | 300 |
| comboWindow (ms) | 2500 | 2000 | 1500 |

### Constantes globales

```
MAX_REALISTIC_SPEED = 0.35   // Au-dessus = artefact tracking
MIN_MOTION_FRAMES = 1        // Minimum frames pour valider un coup
NORM_TO_METERS = 2.0         // 1 unite normalisee ~= 2 metres
SPEED_FRAME_GAP = 3          // Compare frame N vs frame N-3
MAX_DISPLAY_SPEED = 25       // Cap affichage vitesse a 25 m/s
MAX_COMBO = 50               // Cap combo realiste
MIN_PUNCH_INTERVAL = 200     // ms - 2 coups < 200ms = bruit (reset combo)
DEFENSE_HOLD_REQUIRED = 12   // frames pour valider defense (~0.4s)
```

---

## 7. ETAT ACTUEL DES BUGS

### BUG #1 : checkStanding() -- RESOLU (v2.4)
201 coups assis → corrige avec double critere genoux/hanches basses.

### BUG #2 : normSpeedToMs() -- RESOLU (v2.2)
229 m/s → corrige avec calibration + cap 25 m/s. Sessions reelles : 1-7 m/s.

### BUG #3 : Combo counter infini -- RESOLU (v2.2)
Combo 187 → cap 50 + reset si 2 coups < 200ms.

### BUG #4 : best_speed export = string -- ACTIF (mineur)
`Math.max(...state.speeds).toFixed(1)` retourne `"4.6"` (string) pas `4.6` (number).
Fix : entourer de `parseFloat()`.

### NOTE : Cache PWA telephone
Le telephone peut avoir une ancienne version en cache (cles JSON francaises).
Fix : bumper `CACHE_NAME` dans sw.js de `combat-ai-v3` a `combat-ai-v4`.

---

## 8. SESSIONS DE TEST REELLES (26 Fevrier 2026 - Mobile)

### Session 1 - Normale (87s)
| Stat | Valeur |
|------|--------|
| Total coups | 10 |
| Score moyen | 49/100 |
| Meilleur score | 77/100 (CROCHET G, 7.0 m/s) |
| Max combo | 3 |
| Defenses | 2 |

### Session 2 - Facile (65s)
| Stat | Valeur |
|------|--------|
| Total coups | 40 |
| Score moyen | 41/100 |
| Meilleur score | 72/100 (JAB, 4.0 m/s) |
| Max combo | 13 |
| Defenses | 0 |

**Conclusion** : Moteur fonctionnel sur mobile. Vitesses 1-7 m/s = realiste.

---

## 9. HISTORIQUE DES COMMITS (resume)

| Date | Commit | Description |
|------|--------|-------------|
| 28 Fev | `921fdd8` | Enregistrement video de session + lecteur replay |
| 28 Fev | `4f1e611` | Section pricing 3 tiers + video player demo.mp4 |
| 28 Fev | `c315759` | Cloudflare Worker proxy pour waitlist (remplace appel direct Brevo) |
| 27 Fev | `f47109b` | emails.html — dashboard Brevo (contacts, campagnes, welcome email) |
| 26 Fev | `78fad1c` | Waitlist form connecte a Brevo API |
| 26 Fev | `1847ad3` | Mise a jour PROJECT-BRIEF.md |
| 25 Fev | `28143e5` | Auto-reload page quand nouveau SW |
| 25 Fev | `26b2d61` | Bump cache SW v3 |
| 25 Fev | `00ab593` | Fix isMobile ReferenceError (crash total) |
| 24 Fev | `247ae88` | PWA + mobile responsive |
| 20 Fev | `f953be3` | Fix sous-detection, classifyTechnique fallback |
| 20 Fev | `affc1a5` | Fix checkStanding trop strict |
| 17 Fev | `0c7d2f1` | Fix checkStanding + normSpeedToMs + combo cap |
| 17 Fev | `d78466e` | Combat.AI v2 - premier commit MediaPipe |

---

## 10. ROADMAP

### RESOLU
- [x] checkStanding() trop permissif (BUG #1)
- [x] normSpeedToMs() vitesses irrealistes (BUG #2)
- [x] Combo counter sans cap (BUG #3)
- [x] PWA + mobile responsive
- [x] Gestion erreur camera
- [x] Auto-reload nouveau SW
- [x] Landing page avec pricing
- [x] Waitlist Brevo via Cloudflare Worker
- [x] Dashboard email (emails.html)
- [x] Enregistrement video de session + replay
- [x] Video demo sur landing page

### P0 - A faire (mineur)
- [ ] Fix best_speed export string -> number
- [ ] Bump CACHE_NAME -> 'combat-ai-v4' pour forcer MAJ telephones

### P1 - Important
- [ ] Support gaucher
- [ ] Detection defense plus sensible
- [ ] Historique sessions en localStorage

### P2 - Monetisation
- [ ] Stripe Checkout integration (paywall Premium/Pro)
- [ ] Limiter features gratuites (5 modules, pas d'export, pas d'historique)
- [ ] Dashboard coach multi-athletes

### P3 - Nice to have
- [ ] Sons/vibrations sur detection
- [ ] Mode calibration
- [ ] Graphiques dashboard
- [ ] Rapports de progression PDF

---

## 11. DEPENDENCIES EXTERNES

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

Services externes :
- **Brevo** (CRM email) via Cloudflare Worker proxy
- **GitHub Pages** (hebergement)
- **Google Fonts** (Orbitron, Inter, Rajdhani)

---

*Genere par Claude Code - 28 Fevrier 2026*
