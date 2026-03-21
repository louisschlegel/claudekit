# Workflow: Voice Mode

## DÉCLENCHEUR
Commande directe : `/voice`, "voice mode", "mode vocal", "parler à claude", "push to talk".
Intent classifié comme `voice` par le hook UserPromptSubmit.

## AGENTS IMPLIQUÉS
Aucun agent spécifique — le voice mode est une interface d'entrée, pas un workflow de traitement.
Tous les workflows normaux s'appliquent après transcription.

---

## CONCEPT

Le voice mode de Claude Code transcrit la parole en texte avant de le soumettre comme prompt ordinaire. Le résultat transcrit est traité exactement comme si l'utilisateur l'avait tapé. Tous les hooks, le routing d'intent, et les workflows s'appliquent normalement.

**Ce que le voice mode change :** l'interface d'entrée (voix → texte).
**Ce qu'il ne change pas :** le traitement, la sécurité, les permissions, les outputs.

---

## ÉTAPE 1 — Activer le voice mode

### Vérifier la disponibilité
Le voice mode est en rollout progressif (5% → 100%). Si la commande `/voice` ne répond pas, la feature n'est pas encore disponible dans votre compte.

```
/voice
```

Si disponible, Claude Code confirme l'activation et explique les contrôles.

### Statut du rollout
- Pas disponible en CI/CD ou environnements headless
- Nécessite un terminal interactif avec accès au microphone
- Permissions microphone requises au niveau OS (macOS : Paramètres système > Confidentialité > Microphone)

---

## ÉTAPE 2 — Contrôles push-to-talk

### Raccourci par défaut
- **Maintenir Espace** : enregistrer (push-to-talk)
- **Relâcher Espace** : envoyer la transcription

### Raccourcis alternatifs configurables
```
meta+k  — toggle microphone on/off (pratique pour les longues dictées)
```

---

## ÉTAPE 3 — Configurer les keybindings

Créer ou modifier `~/.claude/keybindings.json` :

```json
{
  "key voice:pushToTalk": "space",
  "key voice:toggle": "meta+k",
  "key voice:cancel": "escape"
}
```

**Options disponibles pour `key voice:pushToTalk` :**
- `"space"` — barre d'espace (défaut)
- `"meta+k"` — Cmd+K sur macOS, Alt+K sur Linux/Windows
- `"ctrl+shift+v"` — alternative sans conflit

**Note macOS :** si la barre d'espace est déjà mappée dans votre terminal (tmux, vim, etc.), utiliser `meta+k` ou une combinaison non conflictuelle.

---

## ÉTAPE 4 — Usage patterns

### Dicter des tâches longues
Plutôt que de taper une longue description de feature, dicter en langage naturel.
La transcription peut contenir des hésitations ("euh", "donc") — Claude les ignore et comprend l'intention.

```
[maintien espace]
"Implémente une page de profil utilisateur avec un formulaire pour changer l'email et le mot de passe, ajoute la validation côté client, et connecte-la à l'endpoint PUT /api/users/me qu'on a créé hier."
[relâche espace]
```

### Revue de code orale
```
[maintien espace]
"Est-ce qu'il y a des problèmes de sécurité dans ce code ? Regarde surtout la validation des inputs et comment on gère les erreurs."
[relâche espace]
```

### Standup audio
```
[maintien espace]
"Génère un résumé des commits d'aujourd'hui pour mon standup de demain matin."
[relâche espace]
```

### Navigation dans le codebase
```
[maintien espace]
"Où est définie la logique d'authentification et comment ça marche ?"
[relâche espace]
```

---

## ÉTAPE 5 — Limitations et considérations

### Limitations techniques
- **Latence** : la transcription prend 0.5-2 secondes selon la longueur de l'énoncé
- **Précision** : les termes techniques (noms de fonctions, URLs, regex) sont moins bien transcrits — épeler si nécessaire ou corriger avant envoi
- **Langue** : le switch entre langues dans une même phrase peut créer des ambiguïtés
- **Environnements** : pas disponible en SSH sans forwarding audio, pas en CI, pas headless

### Sécurité
- La transcription s'affiche dans le terminal avant envoi — toujours vérifier avant de soumettre des commandes sensibles
- Les secrets (tokens, mots de passe) dictés à voix haute sont dans l'air ambiant — ne pas dicter de credentials
- Le contenu vocal n'est pas stocké — seul le texte transcrit est traité

### Workflow identique après transcription
Une fois transcrit, le texte passe par tous les hooks normaux :
- Détection d'injection de prompt (user-prompt-submit.sh)
- Classification d'intent et routing
- Pre-bash guards si des commandes sont générées

---

## CONTRAT DE SORTIE

Le voice mode n'a pas de contrat de sortie propre — il délègue immédiatement au workflow correspondant à l'intent détecté dans la transcription.

```
VOICE_INPUT: [transcription]
INTENT_DETECTED: [intent classifié]
ROUTED_TO: [workflow ou réponse directe]
```

**HANDOFF JSON (pour orchestrateur) :**
```json
{
  "input_mode": "voice",
  "transcription": "...",
  "intent": "...",
  "routed_to": "workflows/....md | direct_response"
}
```
