/**
 * Mock authentication setup for Docker environment
 * This replaces the database-dependent auth with a simple in-memory version
 */

import NextAuth from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { v4 as uuidv4 } from 'uuid';

// Simple in-memory guest user storage
const guestUsers = new Map();

export const {
  handlers: { GET, POST },
  auth,
  signIn,
  signOut,
} = NextAuth({
  pages: {
    signIn: '/login',
    newUser: '/',
  },
  providers: [
    CredentialsProvider({
      id: 'guest',
      credentials: {},
      async authorize() {
        // Create a guest user with a random ID
        const userId = uuidv4();
        const guestUser = {
          id: userId,
          type: 'guest',
          name: `Guest-${userId.substring(0, 8)}`,
        };
        
        // Store in memory
        guestUsers.set(userId, guestUser);
        
        return guestUser;
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.type = user.type;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id;
        session.user.type = token.type;
      }
      return session;
    },
  },
});