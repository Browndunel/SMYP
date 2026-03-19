const jwt = require("jsonwebtoken");

const jwtSecret = process.env.JWT_SECRET;

const generateJWT = (payload) => jwt.sign(payload, jwtSecret, { expiresIn: "1h" });
const validateJWT = (token) => jwt.verify(token, jwtSecret);

module.exports = {
  generateJWT,
  validateJWT,
};
