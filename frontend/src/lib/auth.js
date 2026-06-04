export const setToken = (t) => localStorage.setItem("jade_token", t);
export const getToken = () => localStorage.getItem("jade_token");
export const clearToken = () => localStorage.removeItem("jade_token");
export const isAuthed = () => !!getToken();
