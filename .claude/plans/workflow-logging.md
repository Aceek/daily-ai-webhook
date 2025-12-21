# Plan Directeur : Logging des Workflows n8n

**Date de creation** : 2025-12-21
**Complexite Globale** : Moyenne
**Duree Estimee Totale** : 3h - 4h

---

## Vue d'Ensemble

### Description

Cette feature ajoute un systeme de logging pour les executions du workflow n8n, permettant de capturer chaque execution (succes ET echecs) dans des fichiers de logs structures. Les logs workflow seront correles avec les logs Claude existants via un `workflow_execution_id` partage.

Le systeme permettra de :
1. Tracer les executions n8n independamment de claude-service (capture des erreurs en amont)
2. Correler les logs workflow avec les logs Claude CLI
3. Consulter l'historique des executions via fichiers (utile pour le vibe coding)

### Objectifs

- Ajouter un endpoint `/log-workflow` dans claude-service pour recevoir les logs n8n
- Modifier le workflow n8n pour generer un `workflow_execution_id` et logger chaque execution
- Implementer un Error Trigger n8n pour capturer les echecs
- Correler les logs workflow avec les logs Claude existants

### Dependances

**Librairies/Packages necessaires :**
- Aucune nouvelle dependance (utilise FastAPI/Pydantic existants)

**Modules existants impactes :**
- `claude-service/main.py` : Ajout endpoint + modification `/summarize`
- `claude-service/execution_logger.py` : Ajout classes/fonctions pour workflow logs
- `workflows/daily-news-workflow.json` : Modifications substantielles

### Risques Identifies

- **Modification du workflow n8n complexe** : L'ajout de l'Error Trigger et des nodes de logging necessite une bonne comprehension de n8n
  - **Mitigation** : Tester incrementalement chaque modification

- **Synchronisation des IDs** : Le `workflow_execution_id` doit etre genere tot et transmis partout
  - **Mitigation** : Generer l'ID dans le premier node Code et le propager via expressions n8n

- **Logs dupliques en cas d'erreur partielle** : Si le workflow echoue apres l'appel Claude mais avant le log final
  - **Mitigation** : Le log workflow capture l'etat final, le log Claude existe deja

---

## Plan d'Implementation

### Phase 1 : Backend - Modeles et Logger Workflow

**Duree Estimee** : 1h - 1h15

**Objectif de cette phase :** Creer les structures de donnees et le logger pour les executions workflow, en reutilisant le pattern existant de `ExecutionLogger`.

---

#### Etape 1.1 : Creer les modeles Pydantic pour WorkflowLog

**Description :**

Ajouter dans `execution_logger.py` les classes Pydantic pour representer un log d'execution workflow n8n. Ces classes suivent le meme pattern que `ExecutionLog` mais avec des champs specifiques aux workflows.

Champs a inclure :
- `workflow_execution_id` : ID unique genere par n8n
- `workflow_name` : Nom du workflow
- `started_at`, `finished_at` : Timestamps
- `duration_seconds` : Duree totale
- `status` : "success" | "error"
- `error` : Message d'erreur + node qui a echoue (optionnel)
- `nodes_executed` : Liste des nodes avec leur status
- `articles_count` : Nombre d'articles traites (si disponible)
- `claude_execution_id` : ID du log Claude correspondant (optionnel)
- `discord_sent` : Boolean

**Fichiers Concernes :**

- `/home/ilan/code/daily-ai-webhook/claude-service/execution_logger.py` (a modifier)

**Complexite :** Faible

**Duree Estimee :** 20-25 min

**Points d'Attention :**

- Utiliser `Field(default=...)` pour les champs optionnels
- Le `workflow_execution_id` est fourni par n8n, pas genere ici
- Ajouter les type hints obligatoires

---

#### Etape 1.2 : Creer la classe WorkflowLogger

**Description :**

Creer une classe `WorkflowLogger` similaire a `ExecutionLogger` mais pour les logs workflow. Cette classe gere :
- La creation du sous-dossier `logs/workflows/`
- La generation du nom de fichier (format : `YYYY-MM-DD_HH-MM-SS_exec-id`)
- Le formatage Markdown et JSON
- La sauvegarde des fichiers

La methode `_format_markdown` doit produire un document lisible avec :
- Metadata (ID, timestamps, status, duree)
- Liste des nodes executes avec leur status
- Details de l'erreur si echec
- Lien vers le log Claude si disponible

**Fichiers Concernes :**

- `/home/ilan/code/daily-ai-webhook/claude-service/execution_logger.py` (a modifier)

**Complexite :** Moyenne

**Duree Estimee :** 35-40 min

**Points d'Attention :**

- Creer le dossier `logs/workflows/` dans `__init__`
- Reutiliser le pattern de `ExecutionLogger.save()`
- Le format Markdown doit etre coherent avec les logs Claude existants

---

### Phase 2 : Backend - Endpoint /log-workflow

**Duree Estimee** : 45 min - 1h

**Objectif de cette phase :** Exposer un endpoint HTTP pour recevoir les logs workflow depuis n8n.

---

#### Etape 2.1 : Creer les modeles de requete/reponse

**Description :**

Ajouter dans `main.py` les classes Pydantic pour l'endpoint `/log-workflow` :

`WorkflowLogRequest` :
- `workflow_execution_id` : str (requis)
- `workflow_name` : str (requis)
- `started_at` : str (ISO format)
- `finished_at` : str (ISO format)
- `status` : Literal["success", "error"]
- `error_message` : str | None
- `error_node` : str | None
- `nodes_executed` : list[NodeExecution]
- `articles_count` : int
- `claude_execution_id` : str | None
- `discord_sent` : bool

`NodeExecution` :
- `name` : str
- `status` : Literal["success", "error", "skipped"]
- `error` : str | None

`WorkflowLogResponse` :
- `success` : bool
- `log_file` : str | None
- `error` : str | None

**Fichiers Concernes :**

- `/home/ilan/code/daily-ai-webhook/claude-service/main.py` (a modifier)

**Complexite :** Faible

**Duree Estimee :** 15-20 min

**Points d'Attention :**

- Utiliser `Literal` pour les enums simples
- Les timestamps doivent accepter le format ISO de n8n

---

#### Etape 2.2 : Implementer l'endpoint POST /log-workflow

**Description :**

Creer l'endpoint FastAPI qui :
1. Recoit les donnees du workflow depuis n8n
2. Convertit en `WorkflowLog`
3. Sauvegarde via `WorkflowLogger`
4. Retourne le nom du fichier cree

Gerer les erreurs proprement (try/except avec logging).

**Fichiers Concernes :**

- `/home/ilan/code/daily-ai-webhook/claude-service/main.py` (a modifier)

**Complexite :** Faible

**Duree Estimee :** 20-25 min

**Points d'Attention :**

- Logger l'evenement avec `logger.info`
- Retourner une erreur 500 propre si la sauvegarde echoue
- Importer `WorkflowLogger` depuis `execution_logger`

---

#### Etape 2.3 : Modifier /summarize pour accepter workflow_execution_id

**Description :**

Modifier `SummarizeRequest` pour accepter un champ optionnel `workflow_execution_id`. Si fourni, ce champ sera :
1. Inclus dans le `ExecutionLog` genere
2. Retourne dans la reponse pour confirmation

Cela permet la correlation entre les logs workflow et Claude.

Modifier egalement `ExecutionLog` pour inclure ce champ optionnel.

**Fichiers Concernes :**

- `/home/ilan/code/daily-ai-webhook/claude-service/main.py` (a modifier)
- `/home/ilan/code/daily-ai-webhook/claude-service/execution_logger.py` (a modifier)

**Complexite :** Faible

**Duree Estimee :** 15-20 min

**Points d'Attention :**

- Le champ est optionnel (backward compatible)
- Propager l'ID jusqu'a `create_execution_log()`

---

### Phase 3 : Workflow n8n - Generation ID et Logging

**Duree Estimee** : 1h - 1h30

**Objectif de cette phase :** Modifier le workflow n8n pour generer un ID d'execution, le propager a travers les nodes, et logger chaque execution.

---

#### Etape 3.1 : Ajouter node "Init Execution" pour generer l'ID

**Description :**

Ajouter un node Code au debut du workflow (juste apres le trigger) qui :
1. Genere un `workflow_execution_id` unique (format : `wf-{timestamp}-{random}`)
2. Capture `started_at` (timestamp ISO)
3. Stocke ces valeurs pour propagation

Ce node doit etre le premier a s'executer apres le trigger.

**Fichiers Concernes :**

- `/home/ilan/code/daily-ai-webhook/workflows/daily-news-workflow.json` (a modifier)

**Complexite :** Faible

**Duree Estimee :** 15-20 min

**Points d'Attention :**

- Le node doit etre connecte entre le trigger et les RSS feeds
- Utiliser `$execution.id` de n8n comme base si disponible, sinon generer
- Format suggere : `wf-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`

---

#### Etape 3.2 : Modifier "Prepare Payload" pour inclure l'ID

**Description :**

Modifier le node "Prepare Payload" pour :
1. Recuperer le `workflow_execution_id` depuis le contexte
2. L'inclure dans le payload envoye a `/summarize`

Le payload devient :
```json
{
  "articles": [...],
  "workflow_execution_id": "wf-xxx-yyy"
}
```

**Fichiers Concernes :**

- `/home/ilan/code/daily-ai-webhook/workflows/daily-news-workflow.json` (a modifier)

**Complexite :** Faible

**Duree Estimee :** 10-15 min

**Points d'Attention :**

- Acceder aux donnees du node "Init Execution" via expressions n8n
- Syntaxe : `$('Init Execution').first().json.workflow_execution_id`

---

#### Etape 3.3 : Ajouter node "Log Workflow Success" en fin de workflow

**Description :**

Ajouter un node HTTP Request apres "Send to Discord" qui appelle `/log-workflow` avec les donnees de l'execution reussie :
- `workflow_execution_id` : depuis Init
- `workflow_name` : "Daily AI News - MVP"
- `started_at` : depuis Init
- `finished_at` : now()
- `status` : "success"
- `nodes_executed` : liste des nodes parcourus
- `articles_count` : depuis Prepare Payload
- `claude_execution_id` : depuis reponse Claude
- `discord_sent` : true

**Fichiers Concernes :**

- `/home/ilan/code/daily-ai-webhook/workflows/daily-news-workflow.json` (a modifier)

**Complexite :** Moyenne

**Duree Estimee :** 25-30 min

**Points d'Attention :**

- Utiliser les expressions n8n pour recuperer les donnees des nodes precedents
- `finished_at` : `new Date().toISOString()`
- La liste `nodes_executed` peut etre simplifiee (noms des nodes principaux)

---

#### Etape 3.4 : Ajouter Error Trigger et node "Log Workflow Error"

**Description :**

Implementer la capture des erreurs :

1. Ajouter un node "Error Trigger" (type: `n8n-nodes-base.errorTrigger`)
   - Ce node se declenche automatiquement quand un node echoue

2. Ajouter un node Code "Prepare Error Log" qui :
   - Recupere les infos d'erreur (`$execution.error`)
   - Recupere le `workflow_execution_id` si disponible
   - Formate les donnees pour `/log-workflow`

3. Ajouter un node HTTP Request "Log Workflow Error" qui :
   - Appelle `/log-workflow` avec `status: "error"`
   - Inclut `error_message` et `error_node`

**Fichiers Concernes :**

- `/home/ilan/code/daily-ai-webhook/workflows/daily-news-workflow.json` (a modifier)

**Complexite :** Moyenne

**Duree Estimee :** 30-35 min

**Points d'Attention :**

- L'Error Trigger est un workflow separe dans n8n (branche parallele)
- Acceder aux donnees de l'execution qui a echoue via `$execution`
- Si l'erreur survient avant "Init Execution", le `workflow_execution_id` sera absent

---

### Phase 4 : Finalisation

**Duree Estimee** : 15-30 min

**Objectif de cette phase :** Mettre a jour la configuration et la documentation.

---

#### Etape 4.1 : Mettre a jour .gitignore pour logs/workflows/

**Description :**

Verifier que le pattern `logs/*` dans `.gitignore` couvre bien le nouveau sous-dossier `logs/workflows/`. Si necessaire, ajouter explicitement :
```
logs/workflows/*
!logs/workflows/.gitkeep
```

Creer le fichier `logs/workflows/.gitkeep` pour que le dossier soit tracke.

**Fichiers Concernes :**

- `/home/ilan/code/daily-ai-webhook/.gitignore` (a verifier/modifier)
- `/home/ilan/code/daily-ai-webhook/logs/workflows/.gitkeep` (a creer)

**Complexite :** Faible

**Duree Estimee :** 5-10 min

**Points d'Attention :**

- Le pattern `logs/*` devrait deja couvrir les sous-dossiers
- Creer `.gitkeep` vide pour tracker le dossier

---

#### Etape 4.2 : Mettre a jour CLAUDE.md avec la nouvelle fonctionnalite

**Description :**

Ajouter dans la section "Systeme de Logs" de CLAUDE.md :
- Description du nouveau sous-dossier `logs/workflows/`
- Format des fichiers workflow logs
- Commandes pour consulter les logs workflow
- Explication de la correlation via `workflow_execution_id`

**Fichiers Concernes :**

- `/home/ilan/code/daily-ai-webhook/.claude/CLAUDE.md` (a modifier)

**Complexite :** Faible

**Duree Estimee :** 10-15 min

**Points d'Attention :**

- Garder la coherence avec la documentation existante
- Inclure des exemples de commandes bash

---

## Points de Vigilance

**Liste des elements critiques a surveiller pendant l'implementation :**

- **Type hints Python obligatoires** : Toutes les nouvelles fonctions et classes doivent avoir des type hints complets
- **Docstrings** : Toutes les fonctions publiques doivent avoir une docstring
- **Logging structure** : Utiliser `logger.info/error`, pas de `print()`
- **Backward compatibility** : Le champ `workflow_execution_id` dans `/summarize` est optionnel
- **Format de timestamp** : Utiliser ISO format pour coherence avec les logs existants
- **Gestion d'erreurs** : L'endpoint `/log-workflow` ne doit pas faire planter le workflow n8n

---

## Dependances Entre Etapes

**Indiquer clairement les dependances sequentielles :**

- Etape 1.2 depend de 1.1 (WorkflowLogger utilise WorkflowLog)
- Etape 2.1 depend de 1.1 (les modeles request utilisent NodeExecution)
- Etape 2.2 depend de 2.1 et 1.2 (endpoint utilise modeles et logger)
- Etape 2.3 depend de 1.1 (modification de ExecutionLog)
- Phase 3 depend de Phase 2 complete (l'endpoint doit exister avant de l'appeler)
- Etape 3.2 depend de 3.1 (besoin de l'ID genere)
- Etape 3.3 depend de 3.1 et 3.2 (besoin des donnees)
- Etape 3.4 depend de 3.1 (besoin de l'ID si disponible)
- Phase 4 depend de toutes les phases precedentes (finalisation)

---

## Notes

**Structure finale des logs :**

```
logs/
  |- 2024-12-21_08-00-00_abc123.md      # Log Claude (existant)
  |- 2024-12-21_08-00-00_abc123.json
  |- workflows/
      |- 2024-12-21_08-00-00_wf-xxx.md  # Log Workflow (nouveau)
      |- 2024-12-21_08-00-00_wf-xxx.json
```

**Correlation des logs :**

Le fichier workflow log contient `claude_execution_id` qui pointe vers le log Claude correspondant. Inversement, le log Claude contiendra `workflow_execution_id` pour permettre la navigation bidirectionnelle.

**Format du workflow_execution_id :**

Format suggere : `wf-{timestamp_ms}-{random_6chars}`
Exemple : `wf-1703145600000-a3f2b1`

**Expressions n8n utiles :**

- `$execution.id` : ID interne de l'execution n8n
- `$('NodeName').first().json.field` : Acceder aux donnees d'un node
- `new Date().toISOString()` : Timestamp actuel
- `$execution.error` : Infos d'erreur dans Error Trigger
