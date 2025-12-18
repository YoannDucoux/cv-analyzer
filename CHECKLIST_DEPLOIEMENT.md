# ✅ Checklist de déploiement - CV Analyzer

## 📋 Avant de pousser sur GitHub

Vérifiez que ces fichiers sont modifiés et prêts :
- [x] `backend/app/main.py` - CORS configurable
- [x] `backend/app/api.py` - Gestion d'erreur améliorée
- [x] `backend/app/core/config.py` - Variable CORS_ORIGINS
- [x] `frontend/app.js` - Spinner + fonctions setLoading/setStatus
- [x] `frontend/index.html` - Structure bouton avec spinner
- [x] `frontend/styles.css` - Animation spinner

## 🚀 Étape 1 : Pousser sur GitHub

```bash
git add .
git commit -m "feat: Ajout spinner loading + URL Netlify + améliorations"
git push origin main
```

## ⚙️ Étape 2 : Configuration Render (Backend)

**IMPORTANT** : Après le déploiement automatique sur Render, configurez ces variables :

1. Allez sur votre dashboard Render
2. Sélectionnez votre service backend
3. Allez dans **Environment** (Variables d'environnement)
4. **AJOUTEZ/MODIFIEZ** ces variables :

### Variables REQUISES :

```
OPENAI_API_KEY=votre-clé-openai-ici
```

### Variables IMPORTANTES (CORS) :

```
CORS_ORIGINS=https://cv-analyzer-api.netlify.app
```

**OU** si vous avez plusieurs URLs (production + preview) :

```
CORS_ORIGINS=https://cv-analyzer-api.netlify.app,https://preview--cv-analyzer-api.netlify.app
```

5. Cliquez sur **Save Changes**
6. Render redémarre automatiquement le service (attendre 1-2 minutes)

## 🌐 Étape 3 : Vérification Netlify (Frontend)

Netlify se déploie automatiquement après le push GitHub.

1. Allez sur votre dashboard Netlify
2. Vérifiez que le déploiement est réussi (statut vert)
3. Ouvrez votre site : https://cv-analyzer-api.netlify.app

## 🧪 Étape 4 : Tests de vérification

### Test 1 : Backend Health Check

Ouvrez dans votre navigateur ou avec curl :
```
https://cv-analyzer-api-2php.onrender.com/api/v1/health
```

**Résultat attendu** :
```json
{"status":"ok"}
```

### Test 2 : Frontend - Analyse simple

1. Ouvrez https://cv-analyzer-api.netlify.app
2. Sélectionnez un CV (PDF ou DOCX)
3. Cliquez sur "Analyser le CV"
4. **Vérifiez** :
   - ✅ Le bouton affiche "Analyse…" avec un spinner
   - ✅ Le bouton est désactivé (grisé)
   - ✅ Un message "Analyse en cours…" apparaît avec un spinner
   - ✅ Après quelques secondes, les résultats s'affichent
   - ✅ Le bouton revient à "Analyser le CV" (normal)

### Test 3 : Frontend - Erreur réseau

1. Déconnectez votre internet OU modifiez temporairement l'URL API dans app.js
2. Essayez d'analyser un CV
3. **Vérifiez** :
   - ✅ Le spinner s'affiche
   - ✅ Un message d'erreur clair apparaît
   - ✅ Le bouton revient à l'état normal

### Test 4 : Frontend - Comparaison multi-CV

1. Passez en mode "Comparaison Multi-CV"
2. Sélectionnez 2+ CV
3. Ajoutez une offre d'emploi
4. Cliquez sur "Comparer les CV"
5. **Vérifiez** :
   - ✅ Le bouton affiche "Comparaison…" avec spinner
   - ✅ Le message "Comparaison en cours…" apparaît
   - ✅ Les résultats s'affichent après traitement

## ❌ Problèmes courants et solutions

### Problème : Erreur CORS dans la console

**Solution** :
1. Vérifiez que `CORS_ORIGINS` sur Render contient EXACTEMENT votre URL Netlify
2. Pas d'espace avant/après les URLs
3. Pour plusieurs URLs, séparez par des virgules SANS espaces
4. Redémarrez le service Render après modification

### Problème : "Analyse en cours…" puis rien

**Solution** :
1. Ouvrez la console du navigateur (F12)
2. Vérifiez les erreurs dans l'onglet Console
3. Vérifiez l'onglet Network pour voir si la requête est bloquée
4. Vérifiez que l'URL API dans app.js correspond à votre backend Render

### Problème : Le spinner ne s'affiche pas

**Solution** :
1. Vérifiez que `analyzeBtnSpinner` existe dans le HTML
2. Ouvrez la console (F12) et tapez : `document.getElementById('analyzeBtnSpinner')`
3. Si `null`, le HTML n'est pas à jour - vérifiez le déploiement Netlify

### Problème : Backend ne répond pas

**Solution** :
1. Vérifiez les logs Render (dashboard > Logs)
2. Vérifiez que `OPENAI_API_KEY` est bien configurée
3. Vérifiez que le service Render est "Live" (pas en pause)

## ✅ Checklist finale

- [ ] Fichiers poussés sur GitHub
- [ ] Render a déployé automatiquement
- [ ] Netlify a déployé automatiquement
- [ ] Variable `OPENAI_API_KEY` configurée sur Render
- [ ] Variable `CORS_ORIGINS` configurée sur Render avec l'URL Netlify
- [ ] Test `/api/v1/health` fonctionne
- [ ] Test analyse simple fonctionne avec spinner
- [ ] Test comparaison fonctionne avec spinner
- [ ] Pas d'erreurs CORS dans la console
- [ ] Les résultats s'affichent correctement

## 🎉 Si tout est vert, c'est bon !

Votre application est opérationnelle :
- ✅ Frontend : https://cv-analyzer-api.netlify.app
- ✅ Backend : https://cv-analyzer-api-2php.onrender.com
- ✅ Spinner fonctionnel
- ✅ Gestion d'erreur améliorée
- ✅ CORS configuré

