const mongoose = require("mongoose");

const documentSchema = new mongoose.Schema({
  nomFichierDOrigine: String,
  dateTraitement: { type: Date, default: Date.now },
  donneesExtraites: mongoose.Schema.Types.Mixed,
  userId: String,
});

const Document = mongoose.model("Document", documentSchema);

module.exports = Document;
