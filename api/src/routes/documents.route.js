const express = require("express");
const router = express.Router();
const multer = require("multer");
const documentController = require("../controllers/documents.controller");

const upload = multer({ storage: multer.memoryStorage() });

/**
 * @openapi
 * /documents/upload:
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
 *       200:
 *         description: Envoi réussi
 */
router.post(
  "/upload",
  upload.single("uploadedDocument"),
  documentController.Upload,
);

module.exports = router;
