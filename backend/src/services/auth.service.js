const { generateJWT } = require("../utils/jwt.utils");
const { hashPassword, comparePassword } = require("../utils/password.utils");
const User = require("../models/user.model");

exports.SignUp = async (data) => {
  try {
    const { email, password } = data;

    const isExists = await User.findOne({ email });

    if (isExists) {
      return {
        error: true,
        data: "Un utilisateur existe déjà avec ces informations.",
        statusCode: 400,
      };
    }

    const hashedPassword = await hashPassword(password);

    const newUserData = {
      email,
      password: hashedPassword,
    };

    const newUser = new User(newUserData);
    await newUser.save();

    return {
      error: false,
      data: "Utilisateur créé avec succès.",
      statusCode: 201,
    };
  } catch (error) {
    console.error(error);
    return {
      error: true,
      data: error,
      statusCode: 500,
    };
  }
};

exports.SignIn = async (data) => {
  try {
    const { email, password } = data;

    const user = await User.findOne({ email });

    if (!user) {
      return {
        error: true,
        data: "Identifiants invalide.",
        statusCode: 401,
      };
    }

    const isPasswordValid = await comparePassword(password, user.password);

    if (!isPasswordValid) {
      return {
        error: true,
        data: "Identifiants invalide.",
        statusCode: 401,
      };
    }

    const token = await generateJWT({
      userId: user.id,
      email: user.email,
    });

    return {
      error: false,
      data: token,
      statusCode: 200,
    };
  } catch (error) {
    console.error(error);
    return {
      error: true,
      data: error,
      statusCode: 500,
    };
  }
};
