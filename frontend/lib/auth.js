export const getToken = () =>
  typeof window !== "undefined" ? localStorage.getItem("token") : null;

export const setToken = (t) => {
  if (typeof window !== "undefined") localStorage.setItem("token", t);
};

export const clearToken = () => {
  if (typeof window !== "undefined") localStorage.removeItem("token");
};

export const authHeader = () => {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
};
