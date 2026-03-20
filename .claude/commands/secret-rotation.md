# Command: /secret-rotation

Playbook de rotation de secrets en production.

## Pré-requis
- Accès au secret manager (Vault, AWS Secrets Manager, GCP Secret Manager, ou .env)
- Droits de déploiement

## Étapes

### 1. Inventaire
- Lister tous les secrets utilisés par l'application
- Identifier le secret à rotater et son scope (API key, DB password, token, cert)
- Vérifier où il est référencé (code, CI/CD, infrastructure, services tiers)

### 2. Générer le nouveau secret
- Utiliser un générateur cryptographique (`openssl rand -hex 32` ou le secret manager)
- Respecter les contraintes du service (longueur, caractères autorisés)
- NE PAS supprimer l'ancien secret encore

### 3. Déployer en double
- Ajouter le nouveau secret dans le secret manager / .env
- Configurer l'application pour accepter les DEUX secrets (ancien + nouveau)
- Déployer cette version d'abord

### 4. Basculer
- Mettre à jour toutes les références pour utiliser le nouveau secret
- Vérifier que tous les services fonctionnent avec le nouveau
- Monitorer les logs pendant 15 min

### 5. Révoquer l'ancien
- Supprimer l'ancien secret du secret manager
- Vérifier qu'aucun service ne tombe
- Mettre à jour la documentation

### 6. Audit trail
- Logger la rotation : date, qui, quel secret, raison
- Mettre à jour le calendrier de rotation
- Notifier l'équipe

## Fréquence recommandée
| Type | Fréquence |
|------|-----------|
| API keys | 90 jours |
| DB passwords | 180 jours |
| SSL certs | Avant expiration |
| SSH keys | 365 jours |
| Tokens OAuth | Selon le provider |
