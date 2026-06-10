const PROD_API_URL = "https://api.your-app.com"; // Replace with your production API URL
const DEV_API_URL = "http://localhost:8000";

export const API_URL =
  import.meta.env.MODE === "production" ? PROD_API_URL : DEV_API_URL;
