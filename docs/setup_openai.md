# Configuration OpenAI

Pour utiliser l'analyseur de CV avec OpenAI, vous devez configurer votre clé API.

## 1. Obtenir une clé API OpenAI

1. Allez sur https://platform.openai.com/
2. Créez un compte ou connectez-vous
3. Allez dans "API keys" (https://platform.openai.com/api-keys)
4. Créez une nouvelle clé API

## 2. Configurer la clé API

### Option A : Variable d'environnement (recommandé)

**Windows PowerShell :**
```powershell
$env:OPENAI_API_KEY = "sk-votre-cle-api-ici"
```

**Windows CMD :**
```cmd
set OPENAI_API_KEY=sk-votre-cle-api-ici
```

**Linux/Mac :**
```bash
export OPENAI_API_KEY="sk-votre-cle-api-ici"
```

### Option B : Fichier .env (recommandé pour la persistance)

Créez un fichier `.env` dans le dossier `backend` :

```
OPENAI_API_KEY=sk-votre-cle-api-ici
```

Le fichier `.env` est automatiquement chargé au démarrage (pas besoin d'installer python-dotenv).

## 3. Vérifier la configuration

Lancez le serveur et testez l'analyse. Si la clé n'est pas configurée, vous verrez des messages d'avertissement dans les résultats.

## 4. Modèle utilisé

Le projet utilise `gpt-4o-mini` par défaut (modèle économique et rapide). Vous pouvez modifier le modèle dans `backend/app/services/llm.py` si nécessaire.
