import client from "./client";

export const register = (email, password, githubUsername, githubToken) =>
  client.post("/api/auth/register", { email, password, github_username: githubUsername, github_token: githubToken });

export const login = (email, password) =>
  client.post("/api/auth/login", { email, password });

export const getMe = () => client.get("/api/auth/me");
