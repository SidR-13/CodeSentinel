import client from "./client";

export const submitReview = (prUrl) =>
  client.post("/api/reviews", { pr_url: prUrl });

export const listReviews = (page = 1, perPage = 20, filters = {}) => {
  const params = { page, per_page: perPage };
  if (filters.repo) params.repo = filters.repo;
  if (filters.status) params.status = filters.status;
  if (filters.scoreMin != null) params.score_min = filters.scoreMin;
  if (filters.scoreMax != null) params.score_max = filters.scoreMax;
  return client.get("/api/reviews", { params });
};

export const getReview = (id) => client.get(`/api/reviews/${id}`);

export const getStats = () => client.get("/api/reviews/stats");

export const deleteReview = (id) => client.delete(`/api/reviews/${id}`);

export const validatePR = (prUrl) =>
  client.post("/api/github/validate", { pr_url: prUrl });

export const postGithubComment = (id, githubToken) =>
  client.post(`/api/reviews/${id}/post-comment`, { github_token: githubToken });

export const getSSEUrl = (id) => {
  const base = import.meta.env.VITE_API_URL || "";
  return `${base}/api/reviews/${id}/progress`;
};
