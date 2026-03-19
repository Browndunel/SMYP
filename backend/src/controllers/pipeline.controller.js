const Document = require("../models/document.model");

// Stockage en mémoire des statuts de pipeline (par file_id)
const pipelineStatuses = new Map();

/**
 * POST /api/pipeline/status
 * Appelé par Airflow à chaque étape pour mettre à jour le statut.
 */
exports.UpdateStatus = (req, res) => {
  const { file_id, step, status, progress, ...extra } = req.body;

  if (!file_id) {
    return res.status(400).json({ error: "file_id manquant" });
  }

  pipelineStatuses.set(file_id, {
    file_id,
    step,
    status,
    progress,
    ...extra,
    updated_at: new Date().toISOString(),
  });

  return res.json({ ok: true });
};

/**
 * GET /api/pipeline/status/:file_id
 * Polled par le frontend pour savoir où en est le traitement.
 */
exports.GetStatus = (req, res) => {
  const { file_id } = req.params;
  const entry = pipelineStatuses.get(file_id);

  if (!entry) {
    return res.status(404).json({ error: "Aucun pipeline en cours pour ce file_id" });
  }

  return res.json(entry);
};

/**
 * POST /api/internal/store
 * Appelé par Airflow (t2) pour confirmer/mettre à jour le document dans MongoDB.
 */
exports.StoreDocument = async (req, res) => {
  const { file_id, status, anomaly_score, anomalies, pipeline_version } = req.body;

  if (!file_id) {
    return res.status(400).json({ error: "file_id manquant" });
  }

  try {
    const updated = await Document.findByIdAndUpdate(
      file_id,
      {
        status: status || "OK",
        anomalyScore: anomaly_score || 0,
        anomalies: (anomalies || []).map((a) =>
          typeof a === "string" ? a : a.description || JSON.stringify(a)
        ),
      },
      { new: true }
    );

    if (!updated) {
      return res.status(404).json({ error: "Document introuvable" });
    }

    return res.json({ ok: true, document_id: file_id });
  } catch (error) {
    console.error("[Pipeline] Erreur StoreDocument :", error.message);
    return res.status(500).json({ error: error.message });
  }
};
