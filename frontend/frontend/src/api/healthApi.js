import apiClient from "./client";

export const getHealth = () => {
    return apiClient.get("/health");
};