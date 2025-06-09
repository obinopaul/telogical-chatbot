import { DefaultSession } from 'next-auth';
import type { UserType } from '@/lib/types/auth';

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