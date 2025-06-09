import NextAuth from 'next-auth';
import { authConfig } from './app/(auth)/auth.config';

// The middleware is now just a re-export of the configured auth object.
// The logic inside auth.config.ts will handle all the routing protection.
export default NextAuth(authConfig).auth;

export const config = {
  // This matcher ensures the middleware runs on all paths
  // except for static files and Next.js internals.
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
