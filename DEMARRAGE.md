# Guide de démarrage - CV Analyzer

## Démarrage du serveur backend

### Option 1 : Script PowerShell (recommandé)

1. Ouvrez PowerShell dans le dossier `backend`
2. Exécutez :
   ```powershell
   .\start-server.ps1
   ```

### Option 2 : Commande manuelle

1. Ouvrez un terminal dans le dossier `backend`
2. Exécutez :
   ```powershell
   py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   
   Ou si `python` fonctionne :
   ```powershell
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

### Vérification

Une fois le serveur démarré, vous devriez voir :
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Vous pouvez tester que le serveur répond en ouvrant dans votre navigateur :
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/api/v1/debug/test

## Démarrage du frontend

1. Ouvrez le fichier `frontend/index.html` dans votre navigateur
2. Ou servez-le avec un serveur local (optionnel) :
   ```powershell
   cd frontend
   python -m http.server 8080
   ```
   Puis ouvrez http://localhost:8080

## Dépannage

### Le serveur ne démarre pas

- Vérifiez que Python est installé : `py --version`
- Vérifiez que les dépendances sont installées : `py -m pip install -r requirements.txt`
- Vérifiez que le port 8000 n'est pas déjà utilisé

### Erreur "failed to fetch" dans le frontend

- Vérifiez que le serveur backend est bien démarré
- Vérifiez que le serveur écoute sur http://127.0.0.1:8000
- Ouvrez la console du navigateur (F12) pour voir les erreurs détaillées

### Erreur de configuration OpenAI

- Vérifiez que votre clé API est configurée dans `backend/.env`
- Exécutez `.\setup-openai.ps1` pour configurer la clé
- Testez avec `.\check-config.ps1`
