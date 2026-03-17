const express = require("express");
const router = express.Router();
const multer = require("multer");
const documentController = require("../controllers/documents.controller");

const upload = multer({ storage: multer.memoryStorage() });

/**
 * @openapi
 * /api/upload:
 *   post:
 *     description: Envoi des documents à l'OCR et enregistrement dans la base de données
 *     requestBody:
 *       required: true
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               uploadedDocument:
 *                 type: string
 *                 format: binary
 *     responses:
 *       201:
 *         description: Traiement réussi
 *       400:
 *         description: Document abscent
 *       500:
 *         description: Erreur serveur
 *       503:
 *         description: API OCR innaccesible
 */
router.post(
  "/upload",
  upload.single("uploadedDocument"),
  documentController.Upload,
);

/**
 * @openapi
 * /api/documents:
 *   get:
 *     description: Recupère les informations des documents
 *     responses:
 *       200:
 *         description: Récupération réussi
 *       500:
 *         description: Erreur serveur
 */
router.get("/documents", documentController.GetAll);

/**
 * @openapi
 * /api/documents/{id}:
 *   delete:
 *     description: Supprime un documents
 *     parameters:
 *     - in: path
 *       name: id
 *       required: true
 *       schema:
 *         type: string
 *     responses:
 *       204:
 *         description: Suppression réussi
 *       404:
 *         description: Element introuvable
 *       500:
 *         description: Erreur serveur
 */
router.delete("/documents/:id", documentController.Delete);

module.exports = router;
