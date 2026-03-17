const documentService = require("../services/document.service");

exports.Upload = async (req, res) => {
  if (!req.file) {
    return res.status(400).send({ error: "Aucun fichier n'a été reçu." });
  }
  try {
    const resultat = await documentService.Upload(
      req.file.buffer,
      req.file.originalName,
    );
    return res.status(200).send({
      message: "Fichier traité",
      ...resultat,
    });
  } catch (error) {
    console.error("Erreur dans le contrôleur :", error.message);
    res.status(500).send({
      error: "Une erreur est survenue lors du traitement du document.",
    });
  }
};
