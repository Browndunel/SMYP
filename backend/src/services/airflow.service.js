const axios = require("axios");

const AIRFLOW_API_URL  = process.env.AIRFLOW_API_URL  || "http://airflow:8080/api/v1";
const AIRFLOW_USERNAME = process.env.AIRFLOW_USERNAME || "admin";
const AIRFLOW_PASSWORD = process.env.AIRFLOW_PASSWORD || "admin";

exports.triggerPipeline = async (payload) => {
  const url = `${AIRFLOW_API_URL}/dags/smyp_main_pipeline/dagRuns`;

  const response = await axios.post(
    url,
    { conf: payload },
    {
      auth: { username: AIRFLOW_USERNAME, password: AIRFLOW_PASSWORD },
      headers: { "Content-Type": "application/json" },
      timeout: 10000,
    }
  );

  return response.data;
};
