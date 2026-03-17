const axios = require("axios");
const FormData = require("form-data");
const Document = require("../models/document.model");

exports.Upload = async (fileBuffer, originalFileName) => {
  // Renvoi les document à l'OCR et attend la réponse

  const form = new FormData();
  form.append("document", fileBuffer, originalFileName);

  const ocrApiUrl = process.env.OCR_API_URL;

  // const response = await axios.post(ocrApiUrl, form, {
  //   headers: {
  //     ...form.getHeaders(),
  //   },
  // });

  // if (response.status != 200) {
  //   res.status(response.status).send({
  //     message: "Echec du traitement",
  //     OcrApiData: response.data,
  //   });
  //   return;
  // }

  // const jsonRecu = response.data;

  // Sauvegarde dans MongoDB

  const jsonRecu = {
    type: "Facture",
    date: "12/12/23",
    createur: "Jean Dupont",
  };

  const nouvelleEntree = new Document({
    nomFichierDOrigine: originalFileName,
    donneesExtraites: jsonRecu,
  });
  await nouvelleEntree.save();

  return {
    id: nouvelleEntree._id,
    dateTraitement: nouvelleEntree.dateTraitement,
    nomFichierDOrigine: nouvelleEntree.nomFichierDOrigine,
    donneesExtraites: nouvelleEntree.donneesExtraites,
  };

  // Enregistre le document dans minIO
};
