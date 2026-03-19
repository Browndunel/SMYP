const axios = require("axios");
const FormData = require("form-data");
const Document = require("../models/document.model");
const minioService = require("../services/minio.service");

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

  const minioFileName = null;

  // // Enregistre le document dans minIO
  // try {
  //   const result = await minioService.uploadFile(
  //     fileBuffer,
  //     originalFileName,
  //     mimeType,
  //   );
  //   if (result.error == true) {
  //     return result;
  //   }
  //   minioFileName = result.data;
  // } catch (error) {
  //   return {
  //     error: true,
  //     data: error,
  //     statusCode: 500,
  //   };
  // }

  // Sauvegarde dans MongoDB
  const nouvelleEntree = new Document({
    nomFichierDOrigine: originalFileName,
    nomFichierMinIO: minioFileName,
    donneesExtraites: jsonRecu,
    userId: userId,
  });
  await nouvelleEntree.save();

  return {
    error: false,
    data: {
      id: nouvelleEntree._id,
      dateTraitement: nouvelleEntree.dateTraitement,
      nomFichierDOrigine: nouvelleEntree.nomFichierDOrigine,
      donneesExtraites: nouvelleEntree.donneesExtraites,
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
