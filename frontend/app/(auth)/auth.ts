/**
 * PostgreSQL authentication setup for production environment
 * This connects to the real database for user authentication
 */

import NextAuth from 'next-auth';
import Google from 'next-auth/providers/google';
import CredentialsProvider from 'next-auth/providers/credentials';
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import { eq } from 'drizzle-orm';
import { user } from '@/lib/db/schema';
import { verifyPassword } from '@/lib/password';

// Database connection
const client = postgres(process.env.POSTGRES_URL!, {
  ssl: { rejectUnauthorized: false }
});
const db = drizzle(client);

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
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    CredentialsProvider({
      id: 'credentials', // ← CORRECT ID (matches actions.ts)
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        console.log('🔐 POSTGRESQL-AUTH: Attempting credentials login for:', credentials?.email);
        
        if (!credentials?.email || !credentials?.password) {
          console.log('❌ POSTGRESQL-AUTH: Missing email or password');
          return null;
        }

        try {
          console.log('🔍 POSTGRESQL-AUTH: Querying PostgreSQL User table...');
          
          // Query the SAME table that registration uses
          const users = await db
            .select()
            .from(user)  // This is the "User" table in PostgreSQL
            .where(eq(user.email, credentials.email as string));

          console.log('📊 POSTGRESQL-AUTH: Query result - found', users.length, 'users');

          if (users.length === 0) {
            console.log('❌ POSTGRESQL-AUTH: User not found in PostgreSQL:', credentials.email);
            return null;
          }

          const dbUser = users[0];
          console.log('👤 POSTGRESQL-AUTH: Found user:', {
            id: dbUser.id,
            email: dbUser.email,
            name: dbUser.name,
            hasPassword: !!dbUser.password
          });

          if (!dbUser.password) {
            console.log('❌ POSTGRESQL-AUTH: User has no password (OAuth user?):', credentials.email);
            return null;
          }

          // Verify password using SAME method as registration
          const isValidPassword = verifyPassword(credentials.password as string, dbUser.password);
          
          if (!isValidPassword) {
            console.log('❌ POSTGRESQL-AUTH: Invalid password for:', credentials.email);
            return null;
          }

          console.log('✅ POSTGRESQL-AUTH: Password verified! Login successful for:', credentials.email);

          return {
            id: dbUser.id,
            email: dbUser.email,
            name: dbUser.name,
            type: 'credentials',
          };
        } catch (error) {
          console.error('💥 POSTGRESQL-AUTH: Database error during auth:', error);
          return null;
        }
      },
    }),
  ],

  callbacks: {
    async signIn({ user: authUser, account }) {
      console.log('🚪 POSTGRESQL-AUTH: Sign-in callback triggered');
      console.log('🔑 Account type:', account?.provider);
      console.log('👤 User:', authUser?.email);
      
      if (account?.provider === 'google') {
        try {
          // Check if Google user exists in database
          const existingUsers = await db
            .select()
            .from(user)
            .where(eq(user.email, authUser.email!));

          if (existingUsers.length === 0) {
            // Create new user for Google OAuth
            console.log('🆕 POSTGRESQL-AUTH: Creating new Google user:', authUser.email);
            const newUserId = crypto.randomUUID();
            try {
              await db.insert(user).values({
                id: newUserId,
                email: authUser.email!,
                name: authUser.name || authUser.email!.split('@')[0],
                image: authUser.image,
                type: 'regular', // Set type for Google OAuth users
              });
              console.log('✅ POSTGRESQL-AUTH: Successfully created Google user with ID:', newUserId);
              // Set the authUser properties for immediate use
              authUser.id = newUserId;
              authUser.type = 'regular';
            } catch (createError) {
              console.error('💥 POSTGRESQL-AUTH: Failed to create Google user:', createError);
              return false;
            }
          } else {
            console.log('👤 POSTGRESQL-AUTH: Google user already exists:', authUser.email);
            // Set the authUser properties from existing user
            authUser.id = existingUsers[0].id;
            authUser.type = existingUsers[0].type || 'regular';
          }
        } catch (error) {
          console.error('💥 POSTGRESQL-AUTH: Error handling Google sign-in:', error);
          return false;
        }
      }
      
      return true;
    },
    
    async jwt({ token, user: authUser, account }) {
      if (authUser) {
        console.log('🎫 POSTGRESQL-AUTH: JWT callback - setting token for:', authUser.email);
        
        // For Google OAuth, fetch the user type from database
        if (account?.provider === 'google' && authUser.email) {
          try {
            const users = await db
              .select()
              .from(user)
              .where(eq(user.email, authUser.email));
            
            if (users.length > 0) {
              token.id = users[0].id;
              token.type = users[0].type || 'regular';
              console.log('✅ POSTGRESQL-AUTH: Set JWT token from database:', users[0].id, users[0].type);
            } else {
              console.error('❌ POSTGRESQL-AUTH: User not found in database for JWT:', authUser.email);
              token.type = 'regular'; // fallback
            }
          } catch (error) {
            console.error('💥 POSTGRESQL-AUTH: Error fetching user for JWT:', error);
            token.type = 'regular'; // fallback
          }
        } else if (authUser?.id) {
          // For credentials login, authUser already has the type from authorize()
          token.id = authUser.id;
          token.type = authUser.type || 'credentials';
        }
      }
      return token;
    },
    
    async session({ session, token }) {
      if (session.user) {
        console.log('📋 POSTGRESQL-AUTH: Session callback for:', session.user.email);
        session.user.id = token.id as string;
        session.user.type = token.type as "regular" | "credentials";
      }
      return session;
    },
  },

  session: {
    strategy: 'jwt',
  },
  secret: process.env.NEXTAUTH_SECRET,
});