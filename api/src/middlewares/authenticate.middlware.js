const { validateJWT } = require("../utils/jwt.utils");

const authenticate = (req, res, next) => {
  const authHeader = req.headers.authorization;

  if (!authHeader) {
    return res.status(401).json({
      error: "Header manquant",
    });
  }

  const token = authHeader.split(" ")[1];

  if (!token) {
    return res.status(401).json({
      error: "Token manquant",
    });
  }

  try {
    const decodedToken = validateJWT(token);

    req.user = decodedToken;

    next();
  } catch (error) {
    return res.status(403).json({
      error: "Token invalide ou expiré",
    });
  }
};

module.exports = authenticate;
