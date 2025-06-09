import { DefaultSession } from 'next-auth';
import type { UserType } from '@/lib/db/schema';

declare module 'next-auth' {
  interface Session {
    user: {
      id: string;
      type: UserType;
    } & DefaultSession['user'];
  }

  interface User {
    id: string;
    type?: UserType;
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    id: string;
    type: UserType;
  }
}