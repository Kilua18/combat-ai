// ===== Combat.AI — Cloudflare Worker (Brevo Proxy) =====
// Déployer sur : https://dash.cloudflare.com → Workers → combat-ai-waitlist
// API Key Brevo : récupérer depuis app.brevo.com → Settings → SMTP & API
// =========================================================

const BREVO_API_KEY = 'REMPLACER_PAR_CLE_BREVO';  // ← coller ta clé ici
const BREVO_LIST_ID = 2;

const ALLOWED_ORIGINS = [
  'https://kilua18.github.io',
  'http://localhost:3000',
  'http://127.0.0.1:5500'
];

function getCorsHeaders(request) {
  const origin = request.headers.get('Origin') || '';
  const allowedOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': allowedOrigin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
  };
}

export default {
  async fetch(request) {
    const corsHeaders = getCorsHeaders(request);

    // Preflight CORS
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'Method not allowed' }), {
        status: 405,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    try {
      const { email } = await request.json();

      if (!email || !email.includes('@')) {
        return new Response(JSON.stringify({ error: 'Email invalide' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      const brevoResponse = await fetch('https://api.brevo.com/v3/contacts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'api-key': BREVO_API_KEY
        },
        body: JSON.stringify({
          email: email,
          listIds: [BREVO_LIST_ID],
          updateEnabled: true
        })
      });

      // 201 = créé, 204 = déjà existant mis à jour
      if (brevoResponse.status === 201 || brevoResponse.status === 204) {
        return new Response(JSON.stringify({ success: true }), {
          status: 200,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } else {
        const data = await brevoResponse.json();
        return new Response(JSON.stringify({ error: data.message || 'Erreur Brevo' }), {
          status: brevoResponse.status,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

    } catch (err) {
      return new Response(JSON.stringify({ error: 'Erreur serveur' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
  }
};
