const axios = require("axios");
const FormData = require("form-data");
const Document = require("../models/document.model");
const minioService = require("../services/minio.service");

exports.Upload = async (fileBuffer, originalFileName, mimeType, userId) => {
  // Renvoi les document à l'OCR et attend la réponse

  const form = new FormData();
  form.append("file", fileBuffer, originalFileName);

  const ocrApiUrl = process.env.OCR_API_URL + "/ocr";

  const ocrResponse = await axios.post(ocrApiUrl, form, {
    headers: {
      ...form.getHeaders(),
    },
  });

  if (ocrResponse.status != 200) {
    return {
      error: true,
      data: ocrResponse.data,
      statusCode: 503,
    };
  }

  const jsonRecu = ocrResponse.data;
  console.log(jsonRecu);

  // Envoi des réponses à l'anomaly service

  const anomalyApiUrl = process.env.ANOMALY_API_URL + "/validate";

  const anomalyResponse = await axios.post(ocrApiUrl, ocrResponse.data);

  console.log(anomalyResponse);

  // Enregistre le document dans minIO
  let minioFileName = null;
  try {
    const result = await minioService.uploadFile(
      fileBuffer,
      originalFileName,
      mimeType,
    );
    if (result.error == true) {
      return result;
    }
    minioFileName = result.data;
  } catch (error) {
    return {
      error: true,
      data: error,
      statusCode: 500,
    };
  }

  // Sauvegarde dans MongoDB
  const nouvelleEntree = new Document({
    nomFichierDOrigine: originalFileName,
    userId: userId,
    minioPath: minioFileName,
    donneeExtraites: jsonRecu,
  });
  await nouvelleEntree.save();

  return {
    error: false,
    data: {
      id: nouvelleEntree._id,
      dateTraitement: nouvelleEntree.dateTraitement,
      nomFichierDOrigine: nouvelleEntree.nomFichierDOrigine,
      userId: nouvelleEntree.userId,
      minioPth: nouvelleEntree.minioPath,
      donneeExtraites: nouvelleEntree.donneeExtraites,
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
