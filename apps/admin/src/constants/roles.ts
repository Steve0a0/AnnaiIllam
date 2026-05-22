export const ROLES = {
  ADMIN: "admin",
  CLIENT: "client",
  WORKER: "worker",
} as const;

export type Role = (typeof ROLES)[keyof typeof ROLES];
