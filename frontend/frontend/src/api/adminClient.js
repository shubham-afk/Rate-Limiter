import axios from "axios";

const adminClient = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${import.meta.env.VITE_ADMIN_API_TOKEN}`,
    },
});

export default adminClient;