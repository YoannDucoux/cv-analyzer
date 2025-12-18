# Guide de déploiement - CV Analyzer

## 📋 Prérequis

- Git installé et configuré
- Compte GitHub avec le repository du projet
- Compte Render (backend)
- Compte Netlify (frontend)

## 🔄 Workflow de déploiement

### Étape 1 : Vérifier les modifications locales

Vérifiez que tous les fichiers modifiés sont bien dans votre workspace local :

```bash
git status
```

Vous devriez voir les fichiers modifiés :
- `backend/app/main.py`
- `backend/app/api.py`
- `backend/app/core/config.py`
- `frontend/app.js`
- `frontend/index.html`
- `frontend/config.example.js` (nouveau)
- `CORRECTIONS.md` (nouveau)
- `DEPLOIEMENT.md` (nouveau)

### Étape 2 : Commiter les modifications

```bash
# Ajouter tous les fichiers modifiés
git add .

# Ou ajouter fichier par fichier
git add backend/app/main.py
git add backend/app/api.py
git add backend/app/core/config.py
git add frontend/app.js
git add frontend/index.html
git add frontend/config.example.js
git add CORRECTIONS.md
git add DEPLOIEMENT.md

# Créer un commit avec un message descriptif
git commit -m "fix: Correction bug analyse + amélioration gestion erreur + CORS configurable

- Suppression appel endpoint debug inexistant (bug critique)
- Ajout timeout pour analyse simple (3 min)
- Amélioration gestion d'erreur avec messages détaillés
- CORS configurable via variable CORS_ORIGINS
- Endpoint /api/v1/health déplacé
- Nettoyage code mort (imports/variables inutilisés)
- URL API configurable côté frontend"
```

### Étape 3 : Pousser sur GitHub

```bash
# Pousser sur la branche principale (main ou master)
git push origin main

# Ou si vous êtes sur une autre branche
git push origin votre-branche
```

### Étape 4 : Déploiement automatique

#### Render (Backend)
- ✅ **Déploiement automatique** : Render détecte automatiquement les push sur GitHub
- ⏱️ **Temps** : 2-5 minutes
- 🔍 **Vérification** : Allez sur votre dashboard Render pour voir le déploiement

#### Netlify (Frontend)
- ✅ **Déploiement automatique** : Netlify détecte automatiquement les push sur GitHub
- ⏱️ **Temps** : 1-3 minutes
- 🔍 **Vérification** : Allez sur votre dashboard Netlify pour voir le déploiement

## ⚙️ Configuration après déploiement

### Render (Backend)

1. Allez sur votre dashboard Render
2. Sélectionnez votre service backend
3. Allez dans **Environment**
4. Ajoutez/modifiez les variables d'environnement :

```
OPENAI_API_KEY=votre-clé-openai
CORS_ORIGINS=https://votre-site.netlify.app,https://preview--votre-site.netlify.app
```

5. Cliquez sur **Save Changes**
6. Render redémarre automatiquement le service

### Netlify (Frontend)

1. Allez sur votre dashboard Netlify
2. Sélectionnez votre site
3. Allez dans **Site settings** > **Environment variables**
4. (Optionnel) Ajoutez si vous voulez override l'URL API :

```
API_BASE_URL=https://cv-analyzer-api-2php.onrender.com
```

5. Cliquez sur **Save**
6. Netlify redéploie automatiquement

## 🧪 Vérification du déploiement

### Backend (Render)

1. Testez l'endpoint de santé :
```bash
curl https://cv-analyzer-api-2php.onrender.com/api/v1/health
```

Réponse attendue :
```json
{"status":"ok"}
```

2. Vérifiez les logs dans le dashboard Render pour voir s'il n'y a pas d'erreurs

### Frontend (Netlify)

1. Ouvrez votre site Netlify
2. Ouvrez la console du navigateur (F12)
3. Testez une analyse de CV
4. Vérifiez que :
   - L'analyse se lance correctement
   - Les erreurs sont affichées clairement si problème
   - Les timeouts fonctionnent

## 🔍 Dépannage

### Le backend ne se déploie pas sur Render

1. Vérifiez les logs dans le dashboard Render
2. Vérifiez que `requirements.txt` est à jour
3. Vérifiez que la variable `OPENAI_API_KEY` est définie
4. Vérifiez que le service est connecté au bon repository GitHub

### Le frontend ne se déploie pas sur Netlify

1. Vérifiez les logs de build dans le dashboard Netlify
2. Vérifiez que le dossier de build est correct (généralement `frontend/` ou `/`)
3. Vérifiez que le repository GitHub est bien connecté

### L'analyse ne fonctionne toujours pas

1. Vérifiez la console du navigateur (F12) pour les erreurs
2. Vérifiez que l'URL API dans `app.js` correspond à votre backend Render
3. Vérifiez que `CORS_ORIGINS` sur Render inclut votre URL Netlify
4. Testez l'endpoint `/api/v1/health` directement

### Erreur CORS

1. Vérifiez que `CORS_ORIGINS` sur Render inclut exactement votre URL Netlify
2. Vérifiez qu'il n'y a pas d'espace dans la variable
3. Pour plusieurs origines, séparez par des virgules SANS espaces :
   ```
   https://site1.netlify.app,https://site2.netlify.app
   ```

## 📝 Commandes Git utiles

```bash
# Voir les différences avant de commiter
git diff

# Voir l'historique des commits
git log --oneline

# Annuler un commit local (avant push)
git reset --soft HEAD~1

# Voir les fichiers modifiés
git status

# Voir les différences d'un fichier spécifique
git diff backend/app/main.py
```

## 🚀 Déploiement manuel (si nécessaire)

Si le déploiement automatique ne fonctionne pas :

### Render
1. Dashboard Render > Votre service > **Manual Deploy**
2. Sélectionnez la branche et le commit
3. Cliquez sur **Deploy**

### Netlify
1. Dashboard Netlify > Votre site > **Deploys**
2. Cliquez sur **Trigger deploy** > **Deploy site**
3. Sélectionnez la branche

## ✅ Checklist de déploiement

- [ ] Tous les fichiers modifiés sont committés
- [ ] Les modifications sont poussées sur GitHub
- [ ] Render a détecté le push et déploie
- [ ] Netlify a détecté le push et déploie
- [ ] Variable `CORS_ORIGINS` configurée sur Render
- [ ] Variable `OPENAI_API_KEY` configurée sur Render
- [ ] Endpoint `/api/v1/health` répond correctement
- [ ] Test d'analyse fonctionne sur le site Netlify
- [ ] Pas d'erreurs dans les logs Render
- [ ] Pas d'erreurs dans la console navigateur

## 📞 Support

En cas de problème :
1. Vérifiez les logs Render et Netlify
2. Vérifiez la console du navigateur (F12)
3. Testez les endpoints directement avec curl/Postman
4. Vérifiez que toutes les variables d'environnement sont correctes

