const { validateJWT } = require("../utils/jwt.utils");

const authenticate = (req, res, next) => {
  const authHeader = req.headers.authorization;

  if (!authHeader) {
    return res.status(401).json({
      error: true,
      message: "Header manquant",
      statusCode: 401,
    });
  }

  const token = authHeader.split(" ")[1];

  if (!token) {
    return res.status(401).json({
      error: true,
      message: "Token manquant",
      statusCode: 401,
    });
  }

  try {
    const decodedToken = validateJWT(token);

    req.user = decodedToken;

    next();
  } catch (error) {
    return res.status(403).json({
      error: true,
      message: "Token invalide ou expiré",
      statusCode: 403,
    });
  }
};

module.exports = authenticate;
