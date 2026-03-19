const express = require("express");
const router = express.Router();
const multer = require("multer");
const documentController = require("../controllers/documents.controller");
const pipelineController = require("../controllers/pipeline.controller");
const authenticate = require("../middlewares/authenticate.middlware");
const { documentSchema } = require("../dtos/document.dtos");
const validateWithJoi = require("../middlewares/validation.middleware");

const upload = multer({ storage: multer.memoryStorage() });

/**
 * @openapi
 * /api/upload:
 *   post:
 *     description: Envoi des documents à l'OCR et enregistrement dans la base de données
 *     tags:
 *       - Documents
 *     security:
 *       - bearerAuth: []
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
 *       401:
 *         description: Utilisateur déconnecté
 *       403:
 *         description: Token expiré
 *       500:
 *         description: Erreur serveur
 *       503:
 *         description: API OCR innaccesible
 */
router.post(
  "/upload",
  authenticate,
  upload.single("uploadedDocument"),
  documentController.Upload,
);

/**
 * @openapi
 * /api/documents:
 *   get:
 *     description: Recupère les informations des documents
 *     tags:
 *       - Documents
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Récupération réussi
 *       401:
 *         description: Utilisateur déconnecté
 *       403:
 *         description: Token expiré
 *       500:
 *         description: Erreur serveur
 */
router.get("/documents", authenticate, documentController.GetAll);

/**
 * @openapi
 * /api/documents/{id}:
 *   delete:
 *     description: Supprime un documents
 *     tags:
 *       - Documents
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *     - in: path
 *       name: id
 *       required: true
 *       schema:
 *         type: string
 *     responses:
 *       204:
 *         description: Suppression réussi
 *       401:
 *         description: Utilisateur déconnecté
 *       403:
 *         description: Token expiré
 *       404:
 *         description: Element introuvable
 *       500:
 *         description: Erreur serveur
 */
router.delete("/documents/:id", authenticate, documentController.Delete);

/**
 * @openapi
 * /api/documents/{id}:
 *   put:
 *     description: Modifie les informations d'un document existant
 *     tags:
 *       - Documents
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: L'ID MongoDB du document à modifier
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               nomFichierDOrigine:
 *                 type: string
 *               dateTraitement:
 *                 type: string
 *                 format: date-time
 *               donneeExtraites:
 *                 type: object
 *               userId:
 *                 type: string
 *               minioPath:
 *                 type: string
 *     responses:
 *       '200':
 *         description: Document mis à jour avec succès
 *       '400':
 *         description: Données invalides envoyées
 *       '404':
 *         description: Document introuvable
 *       '500':
 *         description: Erreur serveur
 */
router.put(
  "/documents/:id",
  authenticate,
  validateWithJoi(documentSchema),
  documentController.Update,
);

// ── Routes internes appelées par Airflow ─────────────────────
router.post("/pipeline/status",       pipelineController.UpdateStatus);
router.get("/pipeline/status/:file_id", authenticate, pipelineController.GetStatus);
router.post("/internal/store",        pipelineController.StoreDocument);

module.exports = router;
