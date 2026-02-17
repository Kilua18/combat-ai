"""
Combat.AI - Monitoring Automatique
Auteur: Norman
Date: 26 Déc 2025
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import os
from pathlib import Path
import re

# Configuration
METRICS_FILE = Path.home() / "combat-ai" / "metrics-launch.md"
URLS_FILE = Path.home() / "combat-ai" / "config.env"

class SocialMonitor:
    def __init__(self):
        self.stats = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'instagram': {},
            'twitter': {},
            'reddit': {},
            'linkedin': {},
            'google_form': {}
        }
        self.load_urls()
    
    def load_urls(self):
        """Charge URLs depuis config.env"""
        if URLS_FILE.exists():
            with open(URLS_FILE, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        setattr(self, key, value)
    
    def scrape_basic_metrics(self, url, platform):
        """Scraping basique (attention aux rate limits)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Patterns de détection (simplifié, nécessite ajustement)
                if platform == 'reddit':
                    # Cherche upvotes
                    score = soup.find('div', {'class': re.compile('.*score.*')})
                    return {'upvotes': score.text if score else 'N/A'}
                
                return {'scraped': True}
            
        except Exception as e:
            print(f"Erreur scraping {platform}: {e}")
            return {'error': str(e)}
    
    def check_reddit(self):
        """Check stats Reddit"""
        if hasattr(self, 'REDDIT_URL'):
            print("📊 Checking Reddit...")
            metrics = self.scrape_basic_metrics(self.REDDIT_URL, 'reddit')
            self.stats['reddit'] = metrics
            print(f"   Reddit: {metrics}")
    
    def check_twitter(self):
        """Check stats Twitter"""
        if hasattr(self, 'TWITTER_URL'):
            print("📊 Checking Twitter...")
            # Twitter nécessite API pour stats précises
            self.stats['twitter'] = {'note': 'Check manuel requis (API payante)'}
            print("   Twitter: Vérification manuelle recommandée")
    
    def check_instagram(self):
        """Check stats Instagram"""
        if hasattr(self, 'INSTAGRAM_URL'):
            print("📊 Checking Instagram...")
            # Instagram nécessite API ou Instaloader
            self.stats['instagram'] = {'note': 'Check manuel requis (API restreinte)'}
            print("   Instagram: Vérification manuelle recommandée")
    
    def check_linkedin(self):
        """Check stats LinkedIn"""
        if hasattr(self, 'LINKEDIN_URL'):
            print("📊 Checking LinkedIn...")
            self.stats['linkedin'] = {'note': 'Check manuel requis (API entreprise)'}
            print("   LinkedIn: Vérification manuelle recommandée")
    
    def manual_input(self):
        """Entrée manuelle rapide des stats"""
        print("\n" + "="*50)
        print("📝 ENTRÉE MANUELLE DES STATS")
        print("="*50)
        
        # Instagram
        print("\n📱 INSTAGRAM:")
        ig_views = input("  Vues: ").strip() or "N/A"
        ig_likes = input("  Likes: ").strip() or "N/A"
        ig_comments = input("  Commentaires: ").strip() or "N/A"
        self.stats['instagram'] = {
            'views': ig_views,
            'likes': ig_likes,
            'comments': ig_comments
        }
        
        # Twitter
        print("\n🐦 TWITTER:")
        tw_views = input("  Impressions: ").strip() or "N/A"
        tw_likes = input("  Likes: ").strip() or "N/A"
        tw_rt = input("  Retweets: ").strip() or "N/A"
        tw_replies = input("  Réponses: ").strip() or "N/A"
        self.stats['twitter'] = {
            'impressions': tw_views,
            'likes': tw_likes,
            'retweets': tw_rt,
            'replies': tw_replies
        }
        
        # Reddit
        print("\n🔴 REDDIT:")
        rd_upvotes = input("  Upvotes: ").strip() or "N/A"
        rd_comments = input("  Commentaires: ").strip() or "N/A"
        self.stats['reddit'] = {
            'upvotes': rd_upvotes,
            'comments': rd_comments
        }
        
        # LinkedIn
        print("\n💼 LINKEDIN:")
        li_impressions = input("  Impressions: ").strip() or "N/A"
        li_reactions = input("  Réactions: ").strip() or "N/A"
        li_comments = input("  Commentaires: ").strip() or "N/A"
        self.stats['linkedin'] = {
            'impressions': li_impressions,
            'reactions': li_reactions,
            'comments': li_comments
        }
        
        # Google Form
        print("\n📋 GOOGLE FORM:")
        form_signups = input("  Total signups: ").strip() or "N/A"
        form_yes_price = input("  Oui à 20€/mois: ").strip() or "N/A"
        self.stats['google_form'] = {
            'total_signups': form_signups,
            'yes_to_pricing': form_yes_price
        }
    
    def update_metrics_file(self):
        """Met à jour le fichier metrics-launch.md"""
        print(f"\n💾 Mise à jour {METRICS_FILE}...")
        
        timestamp = self.stats['timestamp']
        
        update_text = f"""
---
## UPDATE {timestamp}

### Instagram
- Vues: {self.stats['instagram'].get('views', 'N/A')}
- Likes: {self.stats['instagram'].get('likes', 'N/A')}
- Commentaires: {self.stats['instagram'].get('comments', 'N/A')}

### Twitter
- Impressions: {self.stats['twitter'].get('impressions', 'N/A')}
- Likes: {self.stats['twitter'].get('likes', 'N/A')}
- Retweets: {self.stats['twitter'].get('retweets', 'N/A')}
- Réponses: {self.stats['twitter'].get('replies', 'N/A')}

### Reddit
- Upvotes: {self.stats['reddit'].get('upvotes', 'N/A')}
- Commentaires: {self.stats['reddit'].get('comments', 'N/A')}

### LinkedIn
- Impressions: {self.stats['linkedin'].get('impressions', 'N/A')}
- Réactions: {self.stats['linkedin'].get('reactions', 'N/A')}
- Commentaires: {self.stats['linkedin'].get('comments', 'N/A')}

### Google Form
- Total signups: {self.stats['google_form'].get('total_signups', 'N/A')}
- Oui à 20€/mois: {self.stats['google_form'].get('yes_to_pricing', 'N/A')}

"""
        
        # Ajoute à la fin du fichier
        with open(METRICS_FILE, 'a', encoding='utf-8') as f:
            f.write(update_text)
        
        print("✅ Fichier mis à jour!")
    
    def save_json_log(self):
        """Sauvegarde aussi en JSON pour historique"""
        log_file = Path.home() / "combat-ai" / "metrics-log.json"
        
        # Charge historique existant
        history = []
        if log_file.exists():
            with open(log_file, 'r') as f:
                history = json.load(f)
        
        # Ajoute nouvelle entrée
        history.append(self.stats)
        
        # Sauvegarde
        with open(log_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"💾 Log JSON sauvegardé: {log_file}")
    
    def calculate_growth(self):
        """Calcule croissance depuis dernière mesure"""
        log_file = Path.home() / "combat-ai" / "metrics-log.json"
        
        if not log_file.exists():
            return None
        
        with open(log_file, 'r') as f:
            history = json.load(f)
        
        if len(history) < 2:
            return None
        
        prev = history[-2]
        curr = history[-1]
        
        growth = {}
        
        # Calcule croissance Instagram
        if 'views' in prev['instagram'] and 'views' in curr['instagram']:
            try:
                prev_views = int(prev['instagram']['views'])
                curr_views = int(curr['instagram']['views'])
                growth['instagram_views'] = curr_views - prev_views
            except:
                pass
        
        # Ajoute autres calculs...
        
        return growth
    
    def display_summary(self):
        """Affiche résumé dans terminal"""
        print("\n" + "="*50)
        print("📊 RÉSUMÉ MONITORING")
        print("="*50)
        print(f"⏰ {self.stats['timestamp']}")
        print(f"\n📱 Instagram: {self.stats['instagram'].get('views', 'N/A')} vues, "
              f"{self.stats['instagram'].get('likes', 'N/A')} likes")
        print(f"🐦 Twitter: {self.stats['twitter'].get('impressions', 'N/A')} impressions")
        print(f"🔴 Reddit: {self.stats['reddit'].get('upvotes', 'N/A')} upvotes")
        print(f"📋 Google Form: {self.stats['google_form'].get('total_signups', 'N/A')} signups")
        print("="*50)
    
    def run(self):
        """Exécution principale"""
        print("\n🤖 COMBAT.AI - MONITORING AUTO")
        print("="*50)
        
        # Mode interactif recommandé (APIs sociales sont restrictives)
        self.manual_input()
        self.update_metrics_file()
        self.save_json_log()
        
        # Calcule croissance
        growth = self.calculate_growth()
        if growth:
            print(f"\n📈 Croissance: {growth}")
        
        self.display_summary()
        
        print("\n✅ Monitoring terminé!")
        print(f"📁 Fichiers mis à jour dans: {Path.home() / 'combat-ai'}")

def main():
    monitor = SocialMonitor()
    monitor.run()

if __name__ == "__main__":
    main()