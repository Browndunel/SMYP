const Minio = require("minio");

const minioClient = new Minio.Client({
  endPoint: process.env.MINIO_ENDPOINT,
  useSSL: process.env.MINIO_SECURE === "true",
  accessKey: process.env.MINIO_ACCESS_KEY,
  secretKey: process.env.MINIO_SECRET_KEY,
});

const bucketName = process.env.MINIO_BUCKET_NAME;

// 2. La fonction d'upload
const uploadFile = async (fileBuffer, originalName, mimetype) => {
  try {
    const exists = await minioClient.bucketExists(bucketName);
    if (!exists) {
      return {
        error: true,
        data: "Le bucket minio n'existe pas",
        statusCode: 500,
      };
    }

    const uniqueFileName = `raw/${Date.now()}-${originalName.replace(/\s+/g, "_")}`;

    const metaData = {
      "Content-Type": mimetype,
    };

    await minioClient.putObject(
      bucketName,
      uniqueFileName,
      fileBuffer,
      fileBuffer.length,
      metaData,
    );

    return {
      error: false,
      data: uniqueFileName,
    };
  } catch (error) {
    console.error(error);
    throw new Error(`Erreur lors de l'envoi vers MinIO : ${error.message}`);
  }
};

module.exports = {
  uploadFile,
};
