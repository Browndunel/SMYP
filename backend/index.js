require("dotenv").config({ path: ".env.dev" });

const express = require("express");
const swaggerJsdoc = require("swagger-jsdoc");
const swaggerUi = require("swagger-ui-express");
const mongoose = require("mongoose");

const app = express();

const port = process.env.API_PORT || 5000;

mongoose
  .connect(process.env.MONGODB_URI)
  .then(() => console.log("Connecté à MongoDB !"))
  .catch((err) => console.error("Erreur de connexion MongoDB :", err));

const swaggerOptions = {
  definition: {
    openapi: "3.0.0",
    info: {
      title: "SMYP API",
      version: "1.0.0",
    },
    components: {
      securitySchemes: {
        bearerAuth: {
          type: "http",
          scheme: "bearer",
          bearerFormat: "JWT",
        },
      },
    },
  },
  apis: ["./index.js", "./src/routes/*.js"],
};
const swaggerSpec = swaggerJsdoc(swaggerOptions);
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));

app.use(express.json());

app.use("/api", require("./src/routes/documents.route"));
app.use("/api", require("./src/routes/auth.route"));

app.listen(port, () => {
  console.log(`API listening on port ${port}`);
});
