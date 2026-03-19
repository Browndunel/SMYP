const express = require("express");
const router = express.Router();
const authController = require("../controllers/auth.controller");
const validateWithJoi = require("../middlewares/validation.middleware");
const { authSchema } = require("../dtos/auth.dtos");

/**
 * @openapi
 * /api/sign-up:
 *   post:
 *     description: Inscription
 *     tags:
 *       - Auth
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               email:
 *                 type: string
 *                 format: email
 *               password:
 *                 type: string
 *                 format: password
 *     responses:
 *       201:
 *         description: Compte créé
 *       400:
 *         description: Utilisateur déjà existant
 *       500:
 *         description: Erreur serveur
 */
router.post("/sign-up", validateWithJoi(authSchema), authController.SignUp);

/**
 * @openapi
 * /api/sign-in:
 *   post:
 *     description: Connexion
 *     tags:
 *       - Auth
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               email:
 *                 type: string
 *                 format: email
 *               password:
 *                 type: string
 *                 format: password
 *     responses:
 *       200:
 *         description: Connexion réussie
 *       401:
 *         description: Mauvais identifiants
 *       500:
 *         description: Erreur serveur
 */
router.post("/sign-in", validateWithJoi(authSchema), authController.SignIn);

module.exports = router;
