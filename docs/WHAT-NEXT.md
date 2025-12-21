# What Next - Analyse Stratégique Post-MVP

> **Date:** 22 décembre 2025
> **Contexte:** MVP fonctionnel, consolidation et évolution du projet
> **Objectif:** Identifier les axes d'amélioration prioritaires

---

## 1. État Actuel - Analyse Critique

### 1.1 Ce qui fonctionne

| Composant | Status | Performance |
|-----------|--------|-------------|
| Orchestration n8n | ✅ Stable | Trigger 8h, workflow complet |
| Claude Service (FastAPI) | ✅ Stable | /summarize + /log-workflow |
| Logging bidirectionnel | ✅ Fonctionnel | Corrélation workflow ↔ Claude |
| Publication Discord | ✅ Fonctionnel | Webhook + embed basique |
| Merge 3 sources RSS | ✅ Fixé | Google, OpenAI, HuggingFace |

### 1.2 Diagnostic des Faiblesses

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE ACTUELLE (MVP)                       │
│                                                                      │
│   [RSS x3] ───► [n8n Merge] ───► [Claude CLI] ───► [Discord]        │
│                     │                  │                             │
│                     │                  │                             │
│              Collecte passive    "API call"      Texte brut          │
│              Sources limitées    Pas d'outils    Pas d'interaction   │
└─────────────────────────────────────────────────────────────────────┘
```

**Problèmes identifiés:**

| Problème | Sévérité | Impact |
|----------|----------|--------|
| Sources pauvres (3 RSS) | 🔴 Élevée | Couverture incomplète de l'actualité AI |
| Claude sous-utilisé | 🔴 Élevée | On paye pour des capacités non exploitées |
| Pas de recherche web | 🟠 Moyenne | Manque d'enrichissement contextuel |
| Output texte brut | 🟠 Moyenne | UX médiocre sur Discord |
| Pas d'interactivité | 🟡 Faible | Utilisateurs passifs |

---

## 2. Axe 1 : Enrichissement des Sources de Données

### 2.1 Analyse du problème

**État actuel:** 3 flux RSS (Google AI, OpenAI, HuggingFace)

**Ce qui manque:**
- Anthropic (ironie : on utilise Claude mais pas leur blog)
- Reddit (r/MachineLearning, r/LocalLLaMA)
- Hacker News (discussions techniques)
- arXiv (papers)
- Twitter/X (annonces rapides)
- Newsletters (The Batch, Import AI, etc.)

### 2.2 Pistes d'amélioration

#### Option A : Ajouter plus de RSS (Effort: Faible)

```
Sources RSS supplémentaires recommandées:
├── Anthropic          https://www.anthropic.com/feed.xml
├── MIT Tech Review    https://www.technologyreview.com/topic/artificial-intelligence/feed
├── The Verge AI       https://www.theverge.com/rss/ai-artificial-intelligence/index.xml
├── VentureBeat AI     https://venturebeat.com/category/ai/feed/
├── MarkTechPost       https://www.marktechpost.com/feed/
├── Analytics Vidhya   https://www.analyticsvidhya.com/feed/
└── BAIR Blog          https://bair.berkeley.edu/blog/feed.xml
```

**Avantages:** Implémentation triviale (ajouter des nodes RSS dans n8n)
**Inconvénients:** Toujours passif, pas de contenu "chaud"

#### Option B : Intégrer Reddit/HN via API (Effort: Moyen)

```javascript
// Reddit JSON API (pas d'auth nécessaire pour lecture)
GET https://www.reddit.com/r/MachineLearning/hot.json?limit=25

// Hacker News Algolia API
GET https://hn.algolia.com/api/v1/search?query=AI&tags=story&numericFilters=created_at_i>${timestamp_24h_ago}
```

**Avantages:** Contenu communautaire, discussions, trending topics
**Inconvénients:** Bruit, nécessite filtrage intelligent

#### Option C : Déléguer la recherche à Claude (Effort: Moyen) ⭐

Au lieu de collecter passivement, **demander à Claude de rechercher activement**.

```
Prompt actuel:          "Voici des articles, fais un résumé"
Prompt amélioré:        "Recherche les actualités AI importantes d'aujourd'hui,
                         puis fais un résumé éditorialisé"
```

Cela exploite la capacité de **web search** de Claude Code.

#### Option D : Sources hybrides avec APIs (Effort: Élevé)

| Source | API | Coût |
|--------|-----|------|
| NewsAPI.org | REST | 100 req/jour gratuit |
| Perplexity Sonar | MCP | Payant |
| Feedly API | REST | Pro requis |
| Twitter/X | v2 API | $100+/mois |

### 2.3 Recommandation

**Court terme:** Option A + B (plus de RSS + Reddit/HN)
**Moyen terme:** Option C (Claude agentique avec web search)

---

## 3. Axe 2 : Exploiter les Capacités Agentiques de Claude Code

### 3.1 Analyse du problème

**Utilisation actuelle:**
```python
# main.py - ligne 240
cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose"]
```

On utilise Claude Code comme une **simple API de génération de texte**. C'est comme acheter une voiture de sport pour faire ses courses.

**Capacités non exploitées:**

| Capacité | Utilisée | Potentiel |
|----------|----------|-----------|
| Web Search | ❌ Non | Recherche d'actualités en temps réel |
| MCP Servers | ❌ Non | Perplexity, GitHub, bases de données |
| Tool Use | ❌ Non | Validation de liens, extraction de données |
| Agentic Loops | ❌ Non | Recherche itérative, vérification croisée |
| Agent Skills | ❌ Non | Comportements spécialisés réutilisables |

### 3.2 Pistes d'amélioration

#### Option A : Activer la recherche web dans le prompt

```bash
# Modifier le prompt pour autoriser/encourager la recherche web
claude -p "
Tu es un journaliste AI/ML. Ta mission:
1. Recherche sur le web les actualités AI importantes des dernières 24h
2. Vérifie les informations sur les sites officiels
3. Rédige un résumé éditorialisé

Utilise ta capacité de recherche web pour trouver les news.
"
```

**Note:** Claude Code peut faire des recherches web nativement si le contexte l'y encourage.

#### Option B : Configurer des MCP Servers

```json
// .mcp.json (à la racine du projet ou dans CLAUDE_HOME)
{
  "mcpServers": {
    "perplexity": {
      "command": "npx",
      "args": ["-y", "@anthropic/perplexity-mcp"],
      "env": {
        "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}"
      }
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@anthropic/fetch-mcp"]
    }
  }
}
```

**Serveurs MCP utiles:**
- **Perplexity Sonar:** Recherche web avec citations
- **Fetch:** Récupération de pages web
- **GitHub:** Suivi des repos/releases

#### Option C : Créer un Agent Skill "AI News Researcher"

Anthropic a introduit les [Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) en décembre 2025.

```
.claude/skills/
└── ai-news-researcher/
    ├── SKILL.md           # Instructions de comportement
    ├── sources.json       # Liste des sources prioritaires
    └── fact-check.md      # Règles de vérification
```

**SKILL.md:**
```markdown
# AI News Researcher Skill

## Comportement
Tu es un journaliste spécialisé AI/ML. Pour chaque exécution:

1. **Collecte:** Recherche les actualités des dernières 24h via:
   - Web search pour les breaking news
   - Vérification des blogs officiels (Anthropic, OpenAI, Google, Meta)
   - Scan de r/MachineLearning et Hacker News

2. **Vérification:** Pour chaque news importante:
   - Vérifie la source primaire
   - Cross-check avec au moins une autre source
   - Note le niveau de confiance

3. **Synthèse:** Produis un résumé selon le format éditorial
```

#### Option D : Workflow Agentique Multi-étapes

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW AGENTIQUE PROPOSÉ                        │
│                                                                      │
│   [Trigger]                                                          │
│      │                                                               │
│      ▼                                                               │
│   [Claude: Collecte]  ──────► Web Search + RSS + Reddit              │
│      │                                                               │
│      ▼                                                               │
│   [Claude: Analyse]   ──────► Triage, pertinence, fact-check         │
│      │                                                               │
│      ▼                                                               │
│   [Claude: Rédaction] ──────► Résumé + format Discord                │
│      │                                                               │
│      ▼                                                               │
│   [Discord]                                                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Recommandation

**Priorité 1:** Option A (modifier le prompt pour encourager web search)
**Priorité 2:** Option B (configurer Perplexity MCP)
**Priorité 3:** Option C (créer un Agent Skill dédié)

---

## 4. Axe 3 : Améliorer la Présentation (UI)

### 4.1 Analyse du problème

**Output actuel:**
```
TOP HEADLINES
OpenAI releases GPT-5.2-Codex...

INDUSTRY & PRODUCTS
Developers can now submit apps...
```

C'est du **texte brut** dans un embed Discord basique. Pas d'images, pas de liens cliquables bien formatés, pas d'interaction.

### 4.2 Pistes d'amélioration côté Discord

#### Option A : Embeds riches multiples

```python
# Au lieu d'un seul embed avec tout le texte
embeds = [
    {
        "title": "🔥 TOP HEADLINES",
        "color": 0xFF6B6B,
        "fields": [
            {
                "name": "GPT-5.2-Codex Released",
                "value": "[OpenAI](https://openai.com/...) - Most advanced coding model...",
                "inline": False
            }
        ]
    },
    {
        "title": "📊 INDUSTRY & PRODUCTS",
        "color": 0x4ECDC4,
        "fields": [...]
    }
]
```

#### Option B : Discord Components v2 (Boutons + Interactions)

Discord a lancé [Components v2](https://dev.to/best_codes/using-discord-components-v2-with-discordjs-8f) en mars 2025.

```python
# Exemple avec discord.py
components = [
    ActionRow(
        Button(label="🔍 Détails", custom_id="details", style=ButtonStyle.primary),
        Button(label="📰 Sources", custom_id="sources", style=ButtonStyle.secondary),
        Button(label="🔄 Refresh", custom_id="refresh", style=ButtonStyle.success),
    ),
    SelectMenu(
        custom_id="topic_select",
        placeholder="Filtrer par catégorie",
        options=[
            SelectOption(label="Research", value="research"),
            SelectOption(label="Products", value="products"),
            SelectOption(label="All", value="all"),
        ]
    )
]
```

**Nécessite:** Bot Discord (pas juste webhook)

#### Option C : Threads automatiques pour discussions

```python
# Créer un thread pour chaque headline importante
message = await channel.send(embed=headline_embed)
thread = await message.create_thread(
    name=f"Discussion: {headline_title}",
    auto_archive_duration=1440  # 24h
)
```

### 4.3 Pistes d'amélioration côté Claude

#### Option A : Demander un output structuré JSON

```python
prompt = """
...
Output au format JSON:
{
  "headlines": [
    {
      "title": "...",
      "summary": "...",
      "url": "...",
      "source": "...",
      "importance": "high|medium|low",
      "category": "research|product|business|regulation"
    }
  ],
  "meta": {
    "total_articles_analyzed": 20,
    "date": "2025-12-22"
  }
}
"""
```

Ensuite, n8n/claude-service transforme ce JSON en embeds riches.

#### Option B : Claude génère directement le payload Discord

```python
prompt = """
...
Génère directement un payload Discord embed valide au format JSON.
Utilise plusieurs embeds avec des couleurs différentes par catégorie.
Inclus des liens markdown [texte](url).
"""
```

### 4.4 Pistes UI hors Discord

#### Option A : Dashboard Web (Phase 3)

- Vue historique des news
- Filtres par catégorie/date
- Recherche full-text
- Analytics (tendances)

**Stack suggérée:** Next.js + SQLite/PostgreSQL

#### Option B : Newsletter Email

- Résumé hebdomadaire en plus du daily Discord
- Format HTML riche
- Liens cliquables

### 4.5 Recommandation

**Court terme:** Option A Discord (embeds riches) + Option A Claude (JSON structuré)
**Moyen terme:** Phase 2 Bot avec Components v2
**Long terme:** Dashboard web

---

## 5. Priorisation - Roadmap Recommandée

### 5.1 Quick Wins (1-2 jours)

| Action | Impact | Effort |
|--------|--------|--------|
| Ajouter 4-5 RSS supplémentaires | 🟢 Moyen | 🟢 Faible |
| Modifier le prompt pour encourager web search | 🟢 Moyen | 🟢 Faible |
| Demander output JSON structuré | 🟢 Moyen | 🟢 Faible |
| Embeds Discord multiples + couleurs | 🟢 Moyen | 🟢 Faible |

### 5.2 Consolidation (1 semaine)

| Action | Impact | Effort |
|--------|--------|--------|
| Intégrer Reddit + HN dans n8n | 🟡 Élevé | 🟡 Moyen |
| Configurer MCP Perplexity | 🟡 Élevé | 🟡 Moyen |
| Bot Discord basique (remplace webhook) | 🟡 Moyen | 🟡 Moyen |
| Créer Agent Skill "AI News Researcher" | 🟢 Élevé | 🟡 Moyen |

### 5.3 Évolutions (1 mois+)

| Action | Impact | Effort |
|--------|--------|--------|
| Discord Components v2 (boutons, menus) | 🟡 Moyen | 🔴 Élevé |
| Commandes slash (/news now, /news topic) | 🟡 Moyen | 🟡 Moyen |
| Dashboard web historique | 🟡 Moyen | 🔴 Élevé |
| Multi-thématiques (channels) | 🟡 Moyen | 🟡 Moyen |

### 5.4 Matrice de Priorisation

```
                    IMPACT
                    Élevé │ MCP Perplexity │ Agent Skill │
                          │ Reddit/HN      │             │
                    ──────┼────────────────┼─────────────┤
                    Moyen │ JSON output    │ Bot Discord │
                          │ Embeds riches  │ Components  │
                    ──────┼────────────────┼─────────────┤
                    Faible│ Plus de RSS    │ Dashboard   │
                          │                │             │
                          └────────────────┴─────────────┘
                              Faible          Élevé
                                   EFFORT
```

---

## 6. Proposition de Sprint 2

### 6.1 Objectif

**Transformer Claude d'une "API de génération de texte" en "Agent de veille intelligent"**

### 6.2 Livrables

1. **Sources enrichies:**
   - +5 flux RSS (Anthropic, MIT, etc.)
   - Reddit r/MachineLearning intégré
   - HN intégré

2. **Claude agentique:**
   - Web search activé dans le prompt
   - MCP Perplexity configuré (optionnel)
   - Output JSON structuré

3. **Discord amélioré:**
   - Embeds multiples par catégorie
   - Liens cliquables propres
   - Couleurs par type de news

### 6.3 Non-objectifs (reportés)

- Bot Discord complet (Phase 3)
- Dashboard web (Phase 4)
- Multi-thématiques (Phase 4)

---

## 7. Questions Ouvertes à Discuter

1. **Fréquence:** Garder 1x/jour ou passer à 2x/jour (matin + soir) ?

2. **Langue:** Rester en anglais ou ajouter option français ?

3. **Coût:** Budget acceptable pour APIs payantes (Perplexity, NewsAPI) ?

4. **Interactivité:** Priorité au bot Discord interactif ou au dashboard web ?

5. **Scope:** Rester focus AI/ML ou élargir (Tech général, Crypto, etc.) ?

---

## Annexes

### A. Ressources Consultées

- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Building Agents with Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [MCP Servers for Web Search](https://intuitionlabs.ai/articles/mcp-servers-claude-code-internet-search)
- [Agent Skills Framework](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Discord Components v2](https://dev.to/best_codes/using-discord-components-v2-with-discordjs-8f)
- [allainews_sources (GitHub)](https://github.com/foorilla/allainews_sources)
- [Feedspot AI RSS Feeds](https://rss.feedspot.com/ai_rss_feeds/)

### B. Coûts Estimés

| Service | Gratuit | Payant |
|---------|---------|--------|
| RSS | Illimité | - |
| Reddit API | 60 req/min | - |
| HN API | Illimité | - |
| NewsAPI | 100 req/jour | $449/mois (pro) |
| Perplexity | - | ~$20/mois |
| Claude Code | Inclus abo | - |

### C. Schéma Architecture Cible

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ARCHITECTURE CIBLE (v2.0)                           │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                        SOURCES                                  │    │
│   │   [RSS x8] [Reddit] [HN] [Web Search] [MCP Perplexity]         │    │
│   └───────────────────────────┬────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                    CLAUDE CODE (Agentique)                      │    │
│   │                                                                  │    │
│   │   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │    │
│   │   │ Collecte │ → │ Analyse  │ → │ Fact-    │ → │ Rédaction│    │    │
│   │   │ Active   │   │ Triage   │   │ Check    │   │ JSON     │    │    │
│   │   └──────────┘   └──────────┘   └──────────┘   └──────────┘    │    │
│   │                                                                  │    │
│   │   Agent Skill: "AI News Researcher"                             │    │
│   └───────────────────────────┬────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                         OUTPUT                                  │    │
│   │                                                                  │    │
│   │   [Discord Bot]  [Embeds Riches]  [Interactions]  [Threads]    │    │
│   │                                                                  │    │
│   │   [Dashboard Web] (Phase 4)                                     │    │
│   └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*Document généré le 22 décembre 2025 - À discuter et itérer*
