const bcrypt = require("bcrypt");

const hashPassword = async (password) => await bcrypt.hash(password, 10);
const comparePassword = async (password, hashPassword) => await bcrypt.compare(password, hashPassword);

module.exports = {
    hashPassword,
    comparePassword
}