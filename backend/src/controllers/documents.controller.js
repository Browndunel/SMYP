const documentService = require("../services/document.service");

exports.Upload = async (req, res) => {
  if (!req.file) {
    return res.status(400).send({ error: "Aucun fichier n'a été reçu." });
  }
  try {
    const resultat = await documentService.Upload(
      req.file.buffer,
      req.file.originalname,
      req.file.mimetype,
    );
    return res.status(resultat.statusCode).send(resultat.data);
  } catch (error) {
    console.error("Erreur dans le contrôleur :", error.message);
    res.status(500).send({
      error: "Une erreur est survenue lors du traitement du document.",
    });
  }
};

exports.GetAll = async (req, res) => {
  try {
    const resultat = await documentService.GetAll();
    return res.status(resultat.statusCode).send(resultat.data);
  } catch (error) {
    console.error("Erreur dans le contrôleur :", error.message);
    res.status(500).send({
      error: "Une erreur est survenue lors de la récupération du document.",
    });
  }
};

exports.Delete = async (req, res) => {
  try {
    const { id } = req.params;
    const result = await documentService.Delete(id);
    return res.status(result.statusCode).send(result.data);
  } catch (error) {
    console.error("Erreur dans le contrôleur :", error.message);
    res.status(500).send({
      error: "Une erreur est survenue lors de la suppression du document.",
    });
  }
};
