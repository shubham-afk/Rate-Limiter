import apiClient from "./client";

export const checkRateLimit = (key, endpoint) => {
    return apiClient.post("/check", {
        key,
        endpoint,
    });
};