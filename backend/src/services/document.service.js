const axios = require("axios");
const FormData = require("form-data");
const Document = require("../models/document.model");
const minioService = require("../services/minio.service");
const airflowService = require("../services/airflow.service");

exports.Upload = async (fileBuffer, originalFileName, mimeType, userId) => {
  // Renvoi les document à l'OCR et attend la réponse

  const form = new FormData();
  form.append("file", fileBuffer, originalFileName);

  const ocrApiUrl = process.env.OCR_API_URL + "/ocr";

  const response = await axios.post(ocrApiUrl, form, {
    headers: {
      ...form.getHeaders(),
    },
  });

  if (response.status != 200) {
    return {
      error: true,
      data: response.data,
      statusCode: 503,
    };
  }

  const jsonRecu = response.data;

  // Appel au service anomaly (non-bloquant)
  let anomalyResult = { status: "OK", anomalies: [], anomaly_score: 0 };
  try {
    const anomalyPayload = {
      file_id: jsonRecu.file_id || originalFileName,
      file_name: originalFileName,
      doc_type: jsonRecu.doc_type || "INCONNU",
      ocr_confidence: jsonRecu.ocr_confidence || 0,
      classification_confidence: jsonRecu.classification_confidence || 0,
      fields: jsonRecu.fields || {},
      related_docs: [],
    };
    const anomalyResp = await axios.post(
      `${process.env.ANOMALY_API_URL}/validate`,
      anomalyPayload,
    );
    anomalyResult = anomalyResp.data;
  } catch (err) {
    console.error("Anomaly service error:", err.message);
  }

  let minioFileName = null;

  // Enregistre le document dans minIO (non-bloquant)
  try {
    const result = await minioService.uploadFile(
      fileBuffer,
      originalFileName,
      mimeType,
    );
    if (result.error !== true) {
      minioFileName = result.data;
    } else {
      console.warn("MinIO upload échoué (non-bloquant):", result.data);
    }
  } catch (error) {
    console.warn("MinIO indisponible (non-bloquant):", error.message);
  }

  // Sauvegarde dans MongoDB
  const nouvelleEntree = new Document({
    nomFichierDOrigine: originalFileName,
    userId: userId,
    minioPath: minioFileName,
    donneeExtraites: jsonRecu,
    status: anomalyResult.status || "OK",
    anomalies: (anomalyResult.anomalies || []).map((a) => a.description),
    anomalyScore: anomalyResult.anomaly_score || 0,
  });
  await nouvelleEntree.save();

  // Déclenche le pipeline Airflow (non-bloquant) avec les données déjà traitées
  airflowService.triggerPipeline({
    file_id:       String(nouvelleEntree._id),
    file_name:     originalFileName,
    doc_type:      jsonRecu.doc_type || "INCONNU",
    status:        nouvelleEntree.status,
    anomaly_score: nouvelleEntree.anomalyScore,
    anomalies:     nouvelleEntree.anomalies,
    fields:        jsonRecu.fields || {},
    ocr_confidence: jsonRecu.ocr_confidence || 0,
    user_id:       String(userId),
  }).then(() => {
    console.log(`[Airflow] Pipeline déclenché pour ${nouvelleEntree._id}`);
  }).catch((err) => {
    console.warn(`[Airflow] Trigger échoué (non-bloquant) : ${err.message}`);
  });

  return {
    error: false,
    data: {
      id: nouvelleEntree._id,
      dateTraitement: nouvelleEntree.dateTraitement,
      nomFichierDOrigine: nouvelleEntree.nomFichierDOrigine,
      userId: nouvelleEntree.userId,
      minioPth: nouvelleEntree.minioPath,
      donneeExtraites: nouvelleEntree.donneeExtraites,
      status: nouvelleEntree.status,
      anomalies: nouvelleEntree.anomalies,
      anomalyScore: nouvelleEntree.anomalyScore,
    },
    statusCode: 201,
  };
};

exports.GetAll = async (userId) => {
  const document = await Document.find({ userId });
  return {
    error: false,
    data: document,
    statusCode: 200,
  };
};

exports.Delete = async (id) => {
  const document = await Document.findById(id);

  if (!document) {
    return {
      error: true,
      data: "Le document est introuvable",
      statusCode: 404,
    };
  }

  await Document.findByIdAndDelete(id);

  return {
    error: false,
    data: "Suppression effectuée",
    statusCode: 204,
  };
};

exports.Update = async (id, data) => {
  try {
    const {
      nomFichierDOrigine,
      dateTraitement,
      donneeExtraites,
      userId,
      minioPath,
    } = data;

    const document = await Document.findById(id);

    if (!document) {
      return {
        error: true,
        data: "Le document est introuvable.",
        statusCode: 404,
      };
    }

    const updatedDocumentData = {
      nomFichierDOrigine: nomFichierDOrigine ?? document.nomFichierDOrigine,
      dateTraitement: dateTraitement ?? document.dateTraitement,
      userId: userId ?? document.userId,
      minioPath: minioPath ?? document.minioPath,
      donneeExtraites: donneeExtraites ?? document.donneeExtraites,
    };

    const updatedDocument = await Document.findByIdAndUpdate(
      id,
      updatedDocumentData,
      {
        new: true,
      },
    );

    return {
      error: false,
      data: updatedDocument,
      statusCode: 200,
    };
  } catch (error) {
    return {
      error: true,
      data: error,
      statusCode: 500,
    };
  }
};
