const validateWithJoi = (schema) => {
  return async (req, res, next) => {
    try {
      await schema.validateAsync(req.body);
      next();
    } catch (error) {
      console.error(error);
      return res.status(400).json({
        error: true,
        message: error.message,
        statusCode: 400,
      });
    }
  };
};

module.exports = validateWithJoi;
