"""
Combat.AI - Show Stats (v2)
Affiche les statistiques sociales + sessions d'entrainement
Usage:
    python show-stats.py           # Dernieres stats
    python show-stats.py all       # Historique complet
    python show-stats.py sessions  # Sessions d'entrainement
    python show-stats.py report    # Rapport complet
"""

import json
import sys
import os
import glob
from pathlib import Path
from datetime import datetime

# Chemins
PROJECT_DIR = Path(__file__).parent
METRICS_LOG = PROJECT_DIR / "metrics-log.json"
SESSIONS_DIR = PROJECT_DIR / "sessions"

# Couleurs terminal
class C:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    ORANGE = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'


def load_metrics():
    """Charge les metriques sociales"""
    if not METRICS_LOG.exists():
        return []
    with open(METRICS_LOG, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_sessions():
    """Charge les sessions d'entrainement exportees"""
    sessions = []

    # Cherche dans le dossier sessions/ et a la racine
    patterns = [
        str(PROJECT_DIR / "sessions" / "combat-ai-session-*.json"),
        str(PROJECT_DIR / "combat-ai-session-*.json"),
    ]

    for pattern in patterns:
        for filepath in glob.glob(pattern):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('app', '').startswith('Combat.AI'):
                        data['_file'] = os.path.basename(filepath)
                        sessions.append(data)
            except:
                pass

    # Trie par date
    sessions.sort(key=lambda s: s.get('date', ''), reverse=True)
    return sessions


def show_latest_stats():
    """Affiche les dernieres stats sociales"""
    data = load_metrics()

    if not data:
        print(f"\n{C.RED}Pas de donnees sociales trouvees{C.END}")
        print(f"{C.DIM}Fichier: {METRICS_LOG}{C.END}")
        return

    latest = data[-1]

    print(f"\n{C.BOLD}{'='*60}{C.END}")
    print(f"{C.GREEN}{C.BOLD} COMBAT.AI - METRIQUES SOCIALES{C.END}")
    print(f"{C.BOLD}{'='*60}{C.END}")
    print(f"{C.DIM} {latest.get('timestamp', 'N/A')}{C.END}")

    # Instagram
    ig = latest.get('instagram', {})
    print(f"\n {C.ORANGE}INSTAGRAM{C.END}")
    print(f"   Vues:         {C.BOLD}{ig.get('views', 'N/A')}{C.END}")
    print(f"   Likes:        {ig.get('likes', 'N/A')}")
    print(f"   Commentaires: {ig.get('comments', 'N/A')}")

    # Twitter
    tw = latest.get('twitter', {})
    print(f"\n {C.BLUE}TWITTER/X{C.END}")
    print(f"   Impressions:  {C.BOLD}{tw.get('impressions', 'N/A')}{C.END}")
    print(f"   Likes:        {tw.get('likes', 'N/A')}")
    print(f"   Retweets:     {tw.get('retweets', 'N/A')}")
    print(f"   Reponses:     {tw.get('replies', 'N/A')}")

    # Reddit
    rd = latest.get('reddit', {})
    print(f"\n {C.RED}REDDIT{C.END}")
    print(f"   Upvotes:      {C.BOLD}{rd.get('upvotes', 'N/A')}{C.END}")
    print(f"   Commentaires: {rd.get('comments', 'N/A')}")

    # LinkedIn
    li = latest.get('linkedin', {})
    print(f"\n {C.BLUE}LINKEDIN{C.END}")
    print(f"   Impressions:  {C.BOLD}{li.get('impressions', 'N/A')}{C.END}")
    print(f"   Reactions:    {li.get('reactions', 'N/A')}")
    print(f"   Commentaires: {li.get('comments', 'N/A')}")

    # Google Form
    gf = latest.get('google_form', {})
    print(f"\n {C.GREEN}GOOGLE FORM{C.END}")
    print(f"   Total signups:   {C.BOLD}{gf.get('total_signups', 'N/A')}{C.END}")
    print(f"   Oui a 20E/mois:  {gf.get('yes_to_pricing', 'N/A')}")

    print(f"\n{C.BOLD}{'='*60}{C.END}")

    # Croissance
    if len(data) > 1:
        prev = data[-2]
        print(f"\n {C.GREEN}CROISSANCE{C.END}")
        print(f"{C.DIM}{'-'*60}{C.END}")

        metrics_to_compare = [
            ('instagram', 'views', 'IG Vues'),
            ('instagram', 'likes', 'IG Likes'),
            ('twitter', 'impressions', 'TW Impressions'),
            ('reddit', 'upvotes', 'RD Upvotes'),
            ('linkedin', 'impressions', 'LI Impressions'),
            ('google_form', 'total_signups', 'Signups'),
        ]

        for platform, key, label in metrics_to_compare:
            try:
                prev_val = int(prev.get(platform, {}).get(key, 0))
                curr_val = int(latest.get(platform, {}).get(key, 0))
                diff = curr_val - prev_val

                if diff > 0:
                    color = C.GREEN
                    sign = '+'
                elif diff < 0:
                    color = C.RED
                    sign = ''
                else:
                    color = C.DIM
                    sign = ''

                print(f"   {label:18} {prev_val:>6} -> {curr_val:>6}  {color}{sign}{diff}{C.END}")
            except:
                pass

    print(f"\n{C.DIM} {len(data)} mesure(s) enregistree(s){C.END}")


def show_all_history():
    """Historique complet des metriques"""
    data = load_metrics()

    if not data:
        print(f"{C.RED}Pas de donnees{C.END}")
        return

    print(f"\n{C.BOLD}{'='*60}{C.END}")
    print(f"{C.GREEN}{C.BOLD} HISTORIQUE COMPLET{C.END}")
    print(f"{C.BOLD}{'='*60}{C.END}")

    for i, entry in enumerate(data, 1):
        ig_views = entry.get('instagram', {}).get('views', '?')
        tw_imp = entry.get('twitter', {}).get('impressions', '?')
        rd_up = entry.get('reddit', {}).get('upvotes', '?')
        signups = entry.get('google_form', {}).get('total_signups', '?')

        print(f"\n  {C.BOLD}[{i}]{C.END} {C.DIM}{entry.get('timestamp', '?')}{C.END}")
        print(f"      IG: {ig_views} vues | TW: {tw_imp} imp | RD: {rd_up} up | Signups: {signups}")

    print(f"\n{C.BOLD}{'='*60}{C.END}")


def show_sessions():
    """Affiche les sessions d'entrainement"""
    sessions = load_sessions()

    if not sessions:
        print(f"\n{C.ORANGE}Pas de sessions trouvees{C.END}")
        print(f"{C.DIM}Exporte une session depuis Combat.AI v2 (bouton EXPORTER)")
        print(f"et place le fichier JSON dans: {PROJECT_DIR}{C.END}")
        return

    print(f"\n{C.BOLD}{'='*60}{C.END}")
    print(f"{C.GREEN}{C.BOLD} SESSIONS D'ENTRAINEMENT{C.END}")
    print(f"{C.BOLD}{'='*60}{C.END}")

    total_punches = 0
    total_scores = []
    all_techniques = {'jab': 0, 'cross': 0, 'crochet': 0, 'uppercut': 0}

    for i, s in enumerate(sessions, 1):
        date_str = s.get('date', 'N/A')
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            date_display = dt.strftime('%d/%m/%Y %H:%M')
        except:
            date_display = date_str[:16]

        punches = s.get('total_punches', 0)
        avg_score = s.get('avg_score', 0)
        max_combo = s.get('max_combo', 0)
        best_speed = s.get('best_speed', 0)
        rounds = s.get('rounds', '?')
        difficulty = s.get('difficulty', '?')
        defense = s.get('defense_count', 0)

        total_punches += punches
        if avg_score > 0:
            total_scores.append(avg_score)

        for tech in all_techniques:
            all_techniques[tech] += s.get('techniques', {}).get(tech, 0)

        # Score color
        if avg_score >= 75:
            score_color = C.GREEN
        elif avg_score >= 50:
            score_color = C.ORANGE
        else:
            score_color = C.RED

        print(f"\n  {C.BOLD}Session #{i}{C.END}  {C.DIM}{date_display}{C.END}")
        print(f"  {rounds} rounds | {difficulty} | {punches} coups | "
              f"Score: {score_color}{avg_score}/100{C.END} | "
              f"Combo: {max_combo} | Vitesse: {best_speed} m/s | "
              f"Defense: {defense}")

        # Detail techniques
        techs = s.get('techniques', {})
        tech_parts = []
        for t, c in techs.items():
            if c > 0:
                tech_parts.append(f"{t.upper()}:{c}")
        if tech_parts:
            print(f"  {C.DIM}Techniques: {' | '.join(tech_parts)}{C.END}")

    # Resume global
    print(f"\n{C.BOLD}{'='*60}{C.END}")
    print(f"\n  {C.GREEN}{C.BOLD}RESUME GLOBAL{C.END}")
    print(f"  Sessions:      {len(sessions)}")
    print(f"  Total coups:   {total_punches}")

    if total_scores:
        avg_global = round(sum(total_scores) / len(total_scores))
        print(f"  Score moyen:   {avg_global}/100")

    print(f"\n  {C.BOLD}Techniques:{C.END}")
    total_tech = sum(all_techniques.values())
    for tech, count in sorted(all_techniques.items(), key=lambda x: -x[1]):
        pct = round(count / total_tech * 100) if total_tech > 0 else 0
        bar = '#' * (pct // 2)
        print(f"    {tech.upper():10} {count:>4}  {C.GREEN}{bar}{C.END} {pct}%")

    print(f"\n{C.BOLD}{'='*60}{C.END}")


def show_report():
    """Rapport complet"""
    print(f"\n{C.GREEN}{C.BOLD}")
    print(f"  ╔══════════════════════════════════════╗")
    print(f"  ║       COMBAT.AI - RAPPORT COMPLET    ║")
    print(f"  ╚══════════════════════════════════════╝{C.END}")
    print(f"  {C.DIM}{datetime.now().strftime('%d/%m/%Y %H:%M')}{C.END}\n")

    show_latest_stats()
    print()
    show_sessions()


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == 'all':
            show_all_history()
        elif cmd == 'sessions':
            show_sessions()
        elif cmd == 'report':
            show_report()
        elif cmd == 'help':
            print(__doc__)
        else:
            print(f"Commande inconnue: {cmd}")
            print("Utilise: python show-stats.py [all|sessions|report|help]")
    else:
        show_latest_stats()


if __name__ == "__main__":
    main()
