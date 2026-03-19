const Joi = require("joi");

const documentSchema = Joi.object({
  nomFichierDOrigine: Joi.string().required(),
  dateTraitement: Joi.date().required(),
  userId: Joi.string().required(),
  minioPath: Joi.string(),
  donneeExtraites: Joi.object().unknown(true),
});

module.exports = { documentSchema };
