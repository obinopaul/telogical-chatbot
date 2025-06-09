import type { NextAuthConfig } from 'next-auth';

// The default redirect path after a user logs in
export const DEFAULT_LOGIN_REDIRECT = '/';

export const authConfig = {
  pages: {
    signIn: '/login',
    newUser: '/',
  },
  providers: [
    // added later in auth.ts since it requires bcrypt which is only compatible with Node.js
    // while this file is also used in non-Node.js environments
  ],
  callbacks: {},
} satisfies NextAuthConfig;
