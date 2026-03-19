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
      req.user.userId,
    );
    if (resultat.error == true) {
      console.error(resultat);
    }
    return res.status(resultat.statusCode).send(resultat.data);
  } catch (error) {
    console.error("Erreur dans upload document contrôleur :", error);
    res.status(500).send({
      error: "Une erreur est survenue lors du traitement du document.",
    });
  }
};

exports.GetAll = async (req, res) => {
  try {
    const resultat = await documentService.GetAll(req.user.userId);
    if (resultat.error == true) {
      console.error(resultat);
    }
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

exports.Update = async (req, res) => {
  try {
    const { id } = req.params;
    if (!id) {
      console.error("Id introuvable");
      return res.status(404).json({
        error: true,
        message: "Id introuvable",
        statusCode: 404,
      });
    }
    const {
      nomFichierDOrigine,
      dateTraitement,
      donneeExtraites,
      userId,
      minioPath,
    } = req.body;
    const result = await documentService.Update(id, {
      nomFichierDOrigine,
      dateTraitement,
      donneeExtraites,
      userId,
      minioPath,
    });
    if (result.error == true) {
      console.error(result);
    }
    return res.status(result.statusCode).send(result.data);
  } catch (error) {
    console.error("Erreur dans le contrôleur :", error.message);
    res.status(500).send({
      error: "Une erreur est survenue lors de la modification du document.",
    });
  }
};
