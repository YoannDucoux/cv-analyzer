// URL de l'API configurable via variable d'environnement Netlify ou fallback
// Netlify: définir VITE_API_BASE_URL ou API_BASE_URL dans les variables d'environnement
// Pour le développement local, utiliser window.API_BASE_URL ou la valeur par défaut
const API_BASE_URL = 
  window.API_BASE_URL || 
  (typeof import !== 'undefined' && import.meta?.env?.VITE_API_BASE_URL) ||
  (typeof import !== 'undefined' && import.meta?.env?.API_BASE_URL) ||
  "https://cv-analyzer-api-2php.onrender.com";

const API_URL = `${API_BASE_URL}/api/v1/analyze-cv`;
const COMPARE_API_URL = `${API_BASE_URL}/api/v1/compare-cvs`;
const HEALTH_URL = `${API_BASE_URL}/api/v1/health`;


// Éléments pour le système d'onglets
const modeSingle = document.getElementById("modeSingle");
const modeCompare = document.getElementById("modeCompare");
let currentMode = "single"; // "single" ou "compare"

// Éléments unifiés
const fileInput = document.getElementById("cvFile");
const analyzeBtn = document.getElementById("analyzeBtn");
const statusEl = document.getElementById("status");
const jobDescriptionEl = document.getElementById("jobDescription");
const uploadTitle = document.getElementById("uploadTitle");
const uploadDescription = document.getElementById("uploadDescription");
const jobDescriptionText = document.getElementById("jobDescriptionText");

// Éléments de résultats
const atsEl = document.getElementById("ats");
const insightsEl = document.getElementById("insights");
const canonicalEl = document.getElementById("canonical");
const jobMatchingEl = document.getElementById("jobMatching");

const atsSection = document.getElementById("atsSection");
const insightsSection = document.getElementById("insightsSection");
const jobMatchingSection = document.getElementById("jobMatchingSection");
const keywordMatchingSection = document.getElementById("keywordMatchingSection");
const canonicalSection = document.getElementById("canonicalSection");
const canonicalToggle = document.getElementById("canonicalToggle");
const comparisonSection = document.getElementById("comparisonSection");
const comparisonStatus = document.getElementById("comparisonStatus");
const comparisonResults = document.getElementById("comparisonResults");

// Gestion du changement de mode
function switchMode(mode) {
  currentMode = mode;
  
  // Mettre à jour les onglets
  modeSingle.classList.toggle("active", mode === "single");
  modeCompare.classList.toggle("active", mode === "compare");
  
  // Mettre à jour l'input file
  if (mode === "compare") {
    fileInput.setAttribute("multiple", "multiple");
    uploadTitle.textContent = "Comparaison Multi-CV";
    uploadDescription.textContent = "Uploadez plusieurs CV (minimum 2, PDF ou DOCX) pour comparer leur adéquation avec une offre d'emploi.";
    analyzeBtn.textContent = "Comparer les CV";
    jobDescriptionText.textContent = "Collez le texte de l'offre d'emploi pour comparer avec les CV et obtenir un classement.";
  } else {
    fileInput.removeAttribute("multiple");
    uploadTitle.textContent = "Analyse de CV";
    uploadDescription.textContent = "Uploadez un CV (PDF ou DOCX) pour obtenir une analyse de CV complète et des recommandations personnalisées.";
    analyzeBtn.textContent = "Analyser le CV";
    jobDescriptionText.textContent = "Collez le texte de l'offre d'emploi pour comparer avec votre CV et obtenir un score d'adéquation.";
  }
  
  // Réinitialiser les résultats
  clearResults();
}

// Réinitialiser les résultats
function clearResults() {
  statusEl.textContent = "";
  statusEl.className = "status-message";
  atsSection.style.display = "none";
  insightsSection.style.display = "none";
  jobMatchingSection.style.display = "none";
  keywordMatchingSection.style.display = "none";
  canonicalSection.style.display = "none";
  comparisonSection.style.display = "none";
  comparisonResults.innerHTML = "";
  comparisonStatus.textContent = "";
}

// Gestionnaires d'événements pour les onglets
modeSingle.addEventListener("click", () => switchMode("single"));
modeCompare.addEventListener("click", () => switchMode("compare"));

// Initialiser le mode par défaut
switchMode("single");

// Fonction utilitaire pour obtenir la classe de couleur selon le score
function getScoreClass(score) {
  if (score >= 80) return "score-excellent";
  if (score >= 60) return "score-good";
  if (score >= 40) return "score-fair";
  return "score-poor";
}

function getScoreBgClass(score) {
  if (score >= 80) return "bg-excellent";
  if (score >= 60) return "bg-good";
  if (score >= 40) return "bg-fair";
  return "bg-poor";
}

// Fonction pour formater le score ATS
function renderATS(data) {
  if (!data) return "";
  
  const score = data.total_score || 0;
  const subscores = data.subscores || {};
  const issues = data.issues || [];
  const quickWins = data.quick_wins || [];
  
  let html = '<div class="score-container">';
  
  // Score principal
  html += '<div class="score-main">';
  html += `<div><div class="score-value ${getScoreClass(score)}">${score}</div><div class="score-label">Score global ATS</div></div>`;
  html += '</div>';
  
  // Sous-scores
  if (subscores.readability !== undefined || subscores.structure !== undefined) {
    html += '<div class="score-subscores">';
    
    const subscoreItems = [
      { key: 'readability', label: 'Lisibilité' },
      { key: 'structure', label: 'Structure' },
      { key: 'chronology', label: 'Chronologie' },
      { key: 'evidence', label: 'Preuves' },
      { key: 'skills_clarity', label: 'Clarté des compétences' }
    ];
    
    subscoreItems.forEach(item => {
      const value = subscores[item.key];
      if (value !== undefined) {
        html += `<div class="subscore-item">`;
        html += `<div class="subscore-label">${item.label}</div>`;
        html += `<div class="subscore-value ${getScoreClass(value)}">${value}/100</div>`;
        html += `<div class="subscore-bar"><div class="subscore-fill ${getScoreBgClass(value)}" style="width: ${value}%"></div></div>`;
        html += `</div>`;
      }
    });
    
    html += '</div>';
  }
  
  // Problèmes
  if (issues.length > 0) {
    html += '<div class="issues-list">';
    html += '<h3>Points d\'amélioration</h3>';
    html += '<ul>';
    issues.forEach(issue => {
      html += `<li>${escapeHtml(issue)}</li>`;
    });
    html += '</ul>';
    html += '</div>';
  }
  
  // Quick wins
  if (quickWins.length > 0) {
    html += '<div class="quick-wins-list">';
    html += '<h3>Actions rapides</h3>';
    html += '<ul>';
    quickWins.forEach(win => {
      html += `<li>${escapeHtml(win)}</li>`;
    });
    html += '</ul>';
    html += '</div>';
  }
  
  html += '</div>';
  return html;
}

// Fonction pour formater les insights
function renderInsights(data) {
  if (!data) return "";
  
  const positioning = data.positioning || [];
  const strengths = data.strengths || [];
  const blindSpots = data.blind_spots || [];
  const rewriteSuggestions = data.rewrite_suggestions || [];
  
  let html = '<div class="insights-grid">';
  
  if (strengths.length > 0) {
    html += '<div class="insight-box">';
    html += '<h3>Forces</h3>';
    html += '<ul>';
    strengths.forEach(item => {
      html += `<li>${escapeHtml(item)}</li>`;
    });
    html += '</ul>';
    html += '</div>';
  }
  
  if (blindSpots.length > 0) {
    html += '<div class="insight-box">';
    html += '<h3>Points d\'attention</h3>';
    html += '<ul>';
    blindSpots.forEach(item => {
      html += `<li>${escapeHtml(item)}</li>`;
    });
    html += '</ul>';
    html += '</div>';
  }
  
  if (positioning.length > 0) {
    html += '<div class="insight-box">';
    html += '<h3>Positionnement</h3>';
    html += '<ul>';
    positioning.forEach(item => {
      html += `<li>${escapeHtml(item)}</li>`;
    });
    html += '</ul>';
    html += '</div>';
  }
  
  if (rewriteSuggestions.length > 0) {
    html += '<div class="insight-box">';
    html += '<h3>Suggestions de réécriture</h3>';
    html += '<ul>';
    rewriteSuggestions.forEach(item => {
      html += `<li>${escapeHtml(item)}</li>`;
    });
    html += '</ul>';
    html += '</div>';
  }
  
  html += '</div>';
  return html;
}

// Fonction pour formater les mots-clés
function renderKeywordMatching(data) {
  if (!data) return "";
  if (!data.keywords || (Array.isArray(data.keywords) && data.keywords.length === 0)) {
    return '<p style="color: var(--color-text-light);">Aucun mot-clé extrait de l\'offre.</p>';
  }
  
  const keywords = data.keywords || [];
  const coverageScore = data.coverage_score || 0;
  const criticalMissing = data.critical_missing || [];
  
  // Grouper par catégorie
  const byCategory = {
    technical_skill: [],
    soft_skill: [],
    tool: [],
    education: [],
    experience: [],
    other: []
  };
  
  const categoryLabels = {
    technical_skill: "Compétences techniques",
    soft_skill: "Compétences comportementales",
    tool: "Outils et technologies",
    education: "Formation",
    experience: "Expérience",
    other: "Autres"
  };
  
  keywords.forEach(kw => {
    const cat = kw.category || "other";
    if (byCategory[cat]) {
      byCategory[cat].push(kw);
    }
  });
  
  let html = '<div class="keyword-matching-container">';
  
  // Score de couverture
  html += '<div class="keyword-coverage-header">';
  html += `<div class="keyword-coverage-score"><span class="score-value ${getScoreClass(coverageScore)}">${coverageScore}%</span><span class="score-label">Couverture des mots-clés</span></div>`;
  html += '</div>';
  
  // Mots-clés critiques manquants
  if (criticalMissing.length > 0) {
    html += '<div class="critical-missing">';
    html += '<h3>⚠️ Mots-clés critiques absents</h3>';
    html += '<ul>';
    criticalMissing.forEach(item => {
      html += `<li>${escapeHtml(item)}</li>`;
    });
    html += '</ul>';
    html += '</div>';
  }
  
  // Mots-clés par catégorie
  Object.keys(byCategory).forEach(cat => {
    if (byCategory[cat].length > 0) {
      html += `<div class="keyword-category">`;
      html += `<h3>${categoryLabels[cat] || cat}</h3>`;
      html += '<div class="keyword-list">';
      
      byCategory[cat].forEach(kw => {
        const status = kw.status || "absent";
        const statusClass = status === "present" ? "keyword-present" : 
                           status === "partial" ? "keyword-partial" : "keyword-absent";
        const statusIcon = status === "present" ? "✓" : 
                          status === "partial" ? "~" : "✗";
        const importanceStars = "★".repeat(kw.importance || 1);
        
        html += `<div class="keyword-item ${statusClass}">`;
        html += `<div class="keyword-header">`;
        html += `<span class="keyword-status-icon">${statusIcon}</span>`;
        html += `<span class="keyword-name">${escapeHtml(kw.keyword)}</span>`;
        html += `<span class="keyword-importance" title="Importance: ${kw.importance || 1}/5">${importanceStars}</span>`;
        html += `</div>`;
        if (kw.evidence) {
          html += `<div class="keyword-evidence">Preuve: ${escapeHtml(kw.evidence)}</div>`;
        }
        html += `</div>`;
      });
      
      html += '</div>';
      html += `</div>`;
    }
  });
  
  html += '</div>';
  return html;
}

// Fonction pour formater le job matching
function renderJobMatching(data) {
  if (!data) return "";
  
  const overallScore = data.overall_score || 0;
  const skillsMatch = data.skills_match || 0;
  const experienceMatch = data.experience_match || 0;
  const educationMatch = data.education_match || 0;
  const missingRequirements = data.missing_requirements || [];
  const strengths = data.strengths || [];
  const recommendations = data.recommendations || [];
  
  let html = '<div class="matching-container">';
  
  // Scores
  html += '<div class="matching-scores">';
  html += `<div class="matching-score-card"><div class="matching-score-value ${getScoreClass(overallScore)}">${overallScore}%</div><div class="matching-score-label">Adéquation globale</div></div>`;
  html += `<div class="matching-score-card"><div class="matching-score-value ${getScoreClass(skillsMatch)}">${skillsMatch}%</div><div class="matching-score-label">Compétences</div></div>`;
  html += `<div class="matching-score-card"><div class="matching-score-value ${getScoreClass(experienceMatch)}">${experienceMatch}%</div><div class="matching-score-label">Expérience</div></div>`;
  html += `<div class="matching-score-card"><div class="matching-score-value ${getScoreClass(educationMatch)}">${educationMatch}%</div><div class="matching-score-label">Formation</div></div>`;
  html += '</div>';
  
  // Détails
  html += '<div class="matching-details">';
  
  if (strengths.length > 0) {
    html += '<div class="matching-section">';
    html += '<h3>Points forts</h3>';
    html += '<ul>';
    strengths.forEach(item => {
      html += `<li>${escapeHtml(item)}</li>`;
    });
    html += '</ul>';
    html += '</div>';
  }
  
  if (missingRequirements.length > 0) {
    html += '<div class="matching-section">';
    html += '<h3>Exigences manquantes</h3>';
    html += '<ul>';
    missingRequirements.forEach(item => {
      html += `<li>${escapeHtml(item)}</li>`;
    });
    html += '</ul>';
    html += '</div>';
  }
  
  if (recommendations.length > 0) {
    html += '<div class="matching-section">';
    html += '<h3>Recommandations</h3>';
    html += '<ul>';
    recommendations.forEach(item => {
      html += `<li>${escapeHtml(item)}</li>`;
    });
    html += '</ul>';
    html += '</div>';
  }
  
  html += '</div>';
  html += '</div>';
  return html;
}

// Fonction utilitaire pour échapper le HTML
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Toggle pour les données canoniques
canonicalToggle.addEventListener("click", () => {
  const content = document.getElementById("canonical");
  const isVisible = content.style.display !== "none";
  content.style.display = isVisible ? "none" : "block";
  canonicalToggle.classList.toggle("active", !isVisible);
});

// Gestion de l'analyse (unifié pour les deux modes)
analyzeBtn.addEventListener("click", async () => {
  // Réinitialiser l'affichage
  clearResults();
  atsEl.innerHTML = "";
  insightsEl.innerHTML = "";
  canonicalEl.innerHTML = "";
  jobMatchingEl.innerHTML = "";
  comparisonResults.innerHTML = "";

  if (!fileInput.files.length) {
    statusEl.textContent = currentMode === "compare" 
      ? "❌ Veuillez sélectionner au moins 2 fichiers CV."
      : "❌ Merci de sélectionner un fichier PDF ou DOCX.";
    statusEl.style.background = "#fef2f2";
    statusEl.style.color = "#991b1b";
    return;
  }

  // Mode comparaison
  if (currentMode === "compare") {
    if (fileInput.files.length < 2) {
      statusEl.textContent = "❌ Veuillez sélectionner au moins 2 fichiers CV.";
      statusEl.style.background = "#fef2f2";
      statusEl.style.color = "#991b1b";
      return;
    }

    const jobDescription = jobDescriptionEl.value.trim();
    if (!jobDescription) {
      statusEl.textContent = "❌ Veuillez fournir le texte de l'offre d'emploi.";
      statusEl.style.background = "#fef2f2";
      statusEl.style.color = "#991b1b";
      return;
    }

    const formData = new FormData();
    for (let i = 0; i < fileInput.files.length; i++) {
      formData.append("files", fileInput.files[i]);
    }
    formData.append("job_description", jobDescription);

    statusEl.textContent = "⏳ Comparaison en cours…";
    statusEl.style.background = "#fef3c7";
    statusEl.style.color = "#92400e";
    analyzeBtn.disabled = true;

    try {
      console.log("Envoi de la requête de comparaison...");
      console.log("Nombre de fichiers:", fileInput.files.length);
      console.log("Description de l'offre:", jobDescription.substring(0, 50) + "...");
      console.log("URL API:", COMPARE_API_URL);
      
      // Timeout de 5 minutes pour la comparaison
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 300000);
      
      const response = await fetch(COMPARE_API_URL, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      console.log("Réponse reçue, status:", response.status);
      
      if (!response.ok) {
        let errorText = await response.text();
        console.error("Erreur HTTP:", response.status, errorText);
        try {
          const errorJson = JSON.parse(errorText);
          errorText = errorJson.detail || errorText;
        } catch {
          // Garder le texte brut si ce n'est pas du JSON
        }
        throw new Error(`Erreur ${response.status}: ${errorText}`);
      }
      
      const data = await response.json();
      console.log("Données de comparaison reçues:", data);
      
      statusEl.textContent = "✅ Comparaison terminée.";
      statusEl.style.background = "#d1fae5";
      statusEl.style.color = "#065f46";
      analyzeBtn.disabled = false;
      
      comparisonResults.innerHTML = renderComparison(data);
      comparisonSection.style.display = "block";
      comparisonStatus.textContent = ""; // Réinitialiser le statut de comparaison
      
    } catch (error) {
      console.error("Erreur complète:", error);
      
      let errorMessage = "❌ Erreur lors de la comparaison.";
      
      if (error.name === "AbortError") {
        errorMessage = "❌ La requête a pris trop de temps (timeout 5 min). La comparaison de plusieurs CV peut être longue. Réessayez.";
      } else if (error.name === "TypeError" && error.message.includes("fetch")) {
        errorMessage = `❌ Impossible de contacter le serveur (${API_BASE_URL}). Vérifiez votre connexion internet.`;
      } else if (error.message) {
        errorMessage += ` ${error.message}`;
      }
      
      statusEl.textContent = errorMessage;
      statusEl.style.background = "#fef2f2";
      statusEl.style.color = "#991b1b";
      analyzeBtn.disabled = false;
      
      if (error.stack) {
        console.error("Stack trace:", error.stack);
      }
    }
    return;
  }

  // Mode analyse simple
  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);
  
  const jobDescription = jobDescriptionEl.value.trim();
  if (jobDescription) {
    formData.append("job_description", jobDescription);
  }

  statusEl.textContent = "⏳ Analyse en cours…";
  statusEl.style.background = "#fef3c7";
  statusEl.style.color = "#92400e";
  analyzeBtn.disabled = true;

  try {
    console.log("Envoi de la requête d'analyse...");
    console.log("Fichier:", file.name);
    console.log("URL API:", API_URL);
    
    // Timeout de 3 minutes pour l'analyse simple
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 180000);
    
    const response = await fetch(API_URL, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    console.log("Réponse reçue, status:", response.status);

    if (!response.ok) {
      let errorText = await response.text();
      console.error("Erreur HTTP:", response.status, errorText);
      try {
        const errorJson = JSON.parse(errorText);
        errorText = errorJson.detail || errorText;
      } catch {
        // Garder le texte brut si ce n'est pas du JSON
      }
      throw new Error(`Erreur ${response.status}: ${errorText}`);
    }

    const data = await response.json();
    console.log("Données reçues:", data);

    statusEl.textContent = "✅ Analyse terminée.";
    statusEl.style.background = "#d1fae5";
    statusEl.style.color = "#065f46";
    analyzeBtn.disabled = false;

    // Afficher les résultats
    if (data.ats) {
      atsEl.innerHTML = renderATS(data.ats);
      atsSection.style.display = "block";
    }
    
    if (data.insights) {
      insightsEl.innerHTML = renderInsights(data.insights);
      insightsSection.style.display = "block";
    }
    
    if (data.job_matching) {
      jobMatchingEl.innerHTML = renderJobMatching(data.job_matching);
      jobMatchingSection.style.display = "block";
      
      // Afficher les mots-clés si disponibles
      console.log("Job matching:", data.job_matching);
      console.log("Keyword matching:", data.job_matching.keyword_matching);
      
      if (data.job_matching.keyword_matching) {
        const keywordMatchingEl = document.getElementById("keywordMatching");
        if (keywordMatchingEl) {
          const keywordHtml = renderKeywordMatching(data.job_matching.keyword_matching);
          console.log("HTML mots-clés généré:", keywordHtml ? "Oui" : "Non");
          if (keywordHtml) {
            keywordMatchingEl.innerHTML = keywordHtml;
            keywordMatchingSection.style.display = "block";
          }
        } else {
          console.error("Élément keywordMatching non trouvé dans le DOM");
        }
      } else {
        console.log("Aucun keyword_matching dans job_matching");
      }
    } else if (jobDescription) {
      jobMatchingEl.innerHTML = '<p style="color: var(--color-text-light);">⚠️ Aucune analyse de matching disponible (vérifiez la configuration OpenAI).</p>';
      jobMatchingSection.style.display = "block";
    }
    
    if (data.canonical) {
      canonicalEl.innerHTML = `<pre>${escapeHtml(JSON.stringify(data.canonical, null, 2))}</pre>`;
      canonicalSection.style.display = "block";
    }

  } catch (error) {
    console.error("Erreur complète:", error);
    
    let errorMessage = "❌ Erreur lors de l'analyse.";
    
    if (error.name === "AbortError") {
      errorMessage = "❌ La requête a pris trop de temps (timeout 3 min). Réessayez.";
    } else if (error.name === "TypeError" && error.message.includes("fetch")) {
      errorMessage = `❌ Impossible de contacter le serveur (${API_BASE_URL}). Vérifiez votre connexion internet.`;
    } else if (error.message) {
      errorMessage += ` ${error.message}`;
    }
    
    statusEl.textContent = errorMessage;
    statusEl.style.background = "#fef2f2";
    statusEl.style.color = "#991b1b";
    analyzeBtn.disabled = false;
    
    if (error.stack) {
      console.error("Stack trace:", error.stack);
    }
  }
});

// Fonction pour extraire le nom/prénom et téléphone d'un CV
function getCandidateInfo(cv) {
  if (!cv.canonical) {
    return {
      displayName: escapeHtml(cv.filename),
      phone: "N/A"
    };
  }
  
  const canonical = cv.canonical;
  const fullName = canonical.full_name || "";
  const phone = canonical.phone || "";
  
  // Si on a un nom complet, l'utiliser, sinon utiliser le filename
  let displayName = fullName || cv.filename;
  
  // Nettoyer le nom (enlever les espaces multiples)
  displayName = displayName.trim().replace(/\s+/g, " ");
  
  return {
    displayName: escapeHtml(displayName),
    phone: phone ? escapeHtml(phone) : "N/A"
  };
}

// Fonction pour calculer les stats de mots-clés pour un CV
function calculateKeywordStats(cv) {
  // Vérifier si keyword_matching existe directement ou dans canonical
  let keywordMatching = cv.keyword_matching;
  if (!keywordMatching && cv.canonical && cv.canonical._keyword_matching) {
    keywordMatching = cv.canonical._keyword_matching;
  }
  
  if (!keywordMatching || !keywordMatching.keywords || keywordMatching.keywords.length === 0) {
    return { present: 0, partial: 0, total: 0, text: "N/A" };
  }
  
  const keywords = keywordMatching.keywords;
  const present = keywords.filter(kw => kw.status === "present" || kw.status === "PRESENT").length;
  const partial = keywords.filter(kw => kw.status === "partial" || kw.status === "PARTIAL").length;
  const total = keywords.length;
  
  // Calcul: présent compte pour 1, partiel compte pour 0.5
  const score = present + Math.floor(partial / 2);
  
  return {
    present: present,
    partial: partial,
    total: total,
    text: total > 0 ? `${score}/${total}` : "0/0"
  };
}

// Fonction pour formater la comparaison multi-CV
function renderComparison(data) {
  if (!data || !data.cvs || data.cvs.length === 0) {
    return '<p style="color: var(--color-text-light);">Aucune donnée de comparaison disponible.</p>';
  }
  
  const cvs = data.cvs;
  const ranking = data.overall_ranking || [];
  const criteria = data.criteria_comparison || [];
  const summary = data.summary || "";
  
  // Si pas de classement, créer un basé sur les scores
  if (ranking.length === 0) {
    ranking.push(...cvs.sort((a, b) => b.matching_score - a.matching_score).map(c => c.cv_id));
  }
  
  let html = '<div class="comparison-container">';
  
  // Résumé
  if (summary) {
    html += '<div class="comparison-summary">';
    html += `<p>${escapeHtml(summary)}</p>`;
    html += '</div>';
  }
  
  // Classement global avec notes
  html += '<div class="comparison-ranking">';
  html += '<h3>Classement global</h3>';
  html += '<div class="ranking-list">';
  ranking.forEach((cvId, index) => {
    const cv = cvs.find(c => c.cv_id === cvId);
    if (cv) {
      const rank = index + 1;
      const medal = rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : `${rank}.`;
      const candidateInfo = getCandidateInfo(cv);
      html += `<div class="ranking-item ${rank === 1 ? 'ranking-first' : ''}">`;
      html += `<span class="ranking-medal">${medal}</span>`;
      html += `<span class="ranking-filename"><strong>${candidateInfo.displayName}</strong><br/><span style="font-size: 0.85em; color: var(--color-text-light);">${candidateInfo.phone}</span></span>`;
      html += `<span class="ranking-score ${getScoreClass(cv.matching_score)}"><strong>${cv.matching_score}/100</strong></span>`;
      html += `</div>`;
    }
  });
  html += '</div>';
  html += '</div>';
  
  // Tableau comparatif amélioré
  html += '<div class="comparison-table-container">';
  html += '<h3>Comparaison détaillée</h3>';
  html += '<table class="comparison-table">';
  html += '<thead><tr>';
  html += '<th>CV</th>';
  html += '<th>Note globale<br/><span class="th-subtitle">/100</span></th>';
  html += '<th>Compétences<br/><span class="th-subtitle">/100</span></th>';
  html += '<th>Expérience<br/><span class="th-subtitle">/100</span></th>';
  html += '<th>Formation<br/><span class="th-subtitle">/100</span></th>';
  html += '<th>Mots-clés<br/><span class="th-subtitle">présents/total</span></th>';
  html += '</tr></thead>';
  html += '<tbody>';
  
  // Trier par classement
  const sortedCvs = [];
  ranking.forEach(cvId => {
    const cv = cvs.find(c => c.cv_id === cvId);
    if (cv) sortedCvs.push(cv);
  });
  // Ajouter les CV non classés
  cvs.forEach(cv => {
    if (!ranking.includes(cv.cv_id)) {
      sortedCvs.push(cv);
    }
  });
  
  sortedCvs.forEach(cv => {
    const keywordStats = calculateKeywordStats(cv);
    const keywordClass = keywordStats.total > 0 ? 
      (keywordStats.present / keywordStats.total >= 0.7 ? "score-excellent" :
       keywordStats.present / keywordStats.total >= 0.5 ? "score-good" :
       keywordStats.present / keywordStats.total >= 0.3 ? "score-fair" : "score-poor") : "";
    
    const candidateInfo = getCandidateInfo(cv);
    
    html += '<tr>';
    html += `<td><strong>${candidateInfo.displayName}</strong><br/><span style="font-size: 0.85em; color: var(--color-text-light);">${candidateInfo.phone}</span></td>`;
    html += `<td class="score-cell ${getScoreClass(cv.matching_score)}"><strong>${cv.matching_score}</strong></td>`;
    html += `<td class="score-cell ${getScoreClass(cv.skills_score)}">${cv.skills_score}</td>`;
    html += `<td class="score-cell ${getScoreClass(cv.experience_score)}">${cv.experience_score}</td>`;
    html += `<td class="score-cell ${getScoreClass(cv.education_score)}">${cv.education_score}</td>`;
    html += `<td class="score-cell ${keywordClass}">${keywordStats.text}</td>`;
    html += '</tr>';
  });
  
  html += '</tbody>';
  html += '</table>';
  html += '</div>';
  
  // Justifications par CV
  if (sortedCvs.some(cv => cv.justification)) {
    html += '<div class="comparison-justifications">';
    html += '<h3>Justifications</h3>';
    sortedCvs.forEach(cv => {
      if (cv.justification) {
        const candidateInfo = getCandidateInfo(cv);
        html += '<div class="cv-justification">';
        html += `<h4>${candidateInfo.displayName} <span style="font-size: 0.85em; font-weight: normal; color: var(--color-text-light);">(${candidateInfo.phone})</span></h4>`;
        html += `<p>${escapeHtml(cv.justification)}</p>`;
        html += '</div>';
      }
    });
    html += '</div>';
  }
  
  // Comparaison par critère
  if (criteria.length > 0) {
    html += '<div class="comparison-criteria">';
    html += '<h3>Analyse par critère</h3>';
    criteria.forEach(criterion => {
      html += '<div class="criterion-item">';
      html += `<h4>${escapeHtml(criterion.criterion_name)}</h4>`;
      html += `<p class="criterion-justification">${escapeHtml(criterion.justification)}</p>`;
      html += '<div class="criterion-ranking">';
      criterion.ranking.forEach((cvId, index) => {
        const cv = cvs.find(c => c.cv_id === cvId);
        if (cv) {
          const candidateInfo = getCandidateInfo(cv);
          html += `<div class="criterion-rank-item">`;
          html += `<span class="rank-number">${index + 1}.</span>`;
          html += `<span>${candidateInfo.displayName} <span style="font-size: 0.85em; color: var(--color-text-light);">(${candidateInfo.phone})</span></span>`;
          html += `</div>`;
        }
      });
      html += '</div>';
      html += '</div>';
    });
    html += '</div>';
  }
  
  html += '</div>';
  return html;
}
