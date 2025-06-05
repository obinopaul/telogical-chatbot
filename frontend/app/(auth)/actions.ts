'use server';

import { z } from 'zod';
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import { eq } from 'drizzle-orm';
import { user } from '@/lib/db/schema';
import { hashPassword } from '@/lib/password';
import { signIn } from './auth';

// Database connection
const client = postgres(process.env.POSTGRES_URL!, {
  ssl: { rejectUnauthorized: false }
});
const db = drizzle(client);

const authFormSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
  name: z.string().min(2).optional(),
});

const registerFormSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
  confirmPassword: z.string().min(6),
  name: z.string().min(2),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

export interface LoginActionState {
  status: 'idle' | 'in_progress' | 'success' | 'failed' | 'invalid_data';
}

export const login = async (
  _: LoginActionState,
  formData: FormData,
): Promise<LoginActionState> => {
  try {
    const validatedData = authFormSchema.parse({
      email: formData.get('email'),
      password: formData.get('password'),
    });

    console.log('🚀 Attempting login for:', validatedData.email);

    const result = await signIn('credentials', {
      email: validatedData.email,
      password: validatedData.password,
      redirect: false,
    });

    console.log('📊 Login result:', result);
    console.log('🔍 Login result type:', typeof result);
    console.log('🔍 Login result keys:', result ? Object.keys(result) : 'null');

    // 1. Handle the expected successful object response
    if (result && typeof result === 'object' && result.ok === true) {
      console.log('✅ ACTIONS.TS: Standard success path - signIn returned object with ok: true');
      return { status: 'success' };
    }
    
    // 2. Handle the OBSERVED ANOMALY: signIn returns a URL string on (backend) success
    // Based on console analysis, backend authentication IS successful when this string is returned
    else if (typeof result === 'string' && (result.startsWith('http://') || result.startsWith('https://'))) {
      console.log('✅ ACTIONS.TS: NextAuth returned URL string - interpreting as success based on backend confirmation');
      console.log('🎯 ACTIONS.TS: URL result:', result);
      return { status: 'success' };
    }
    
    // 3. Handle the expected error object response
    else if (result && typeof result === 'object' && result.error) {
      console.log('❌ ACTIONS.TS: NextAuth returned error object:', result.error);
      return { status: 'failed' };
    }
    
    // 4. Fallback for any other unexpected results
    else {
      console.log('❌ ACTIONS.TS: Unexpected signIn result structure:', result);
      return { status: 'failed' };
    }
  } catch (error) {
    console.error('💥 Login error:', error);
    if (error instanceof z.ZodError) {
      return { status: 'invalid_data' };
    }

    return { status: 'failed' };
  }
};

export interface RegisterActionState {
  status:
    | 'idle'
    | 'in_progress'
    | 'success'
    | 'failed'
    | 'user_exists'
    | 'invalid_data';
}

export const register = async (
  _: RegisterActionState,
  formData: FormData,
): Promise<RegisterActionState> => {
  try {
    const validatedData = registerFormSchema.parse({
      email: formData.get('email'),
      password: formData.get('password'),
      confirmPassword: formData.get('confirmPassword'),
      name: formData.get('name'),
    });

    // Check if user already exists
    const existingUsers = await db
      .select()
      .from(user)
      .where(eq(user.email, validatedData.email));

    if (existingUsers.length > 0) {
      return { status: 'user_exists' };
    }

    // Hash password and create user
    const hashedPassword = hashPassword(validatedData.password);
    
    await db.insert(user).values({
      id: crypto.randomUUID(),
      email: validatedData.email,
      password: hashedPassword,
      name: validatedData.name || validatedData.email.split('@')[0],
    });

    console.log('✅ User created, attempting auto sign-in...');

    // Auto sign-in after registration
    const result = await signIn('credentials', {
      email: validatedData.email,
      password: validatedData.password,
      redirect: false,
    });

    console.log('📊 Auto sign-in result:', result);
    console.log('🔍 Auto sign-in result type:', typeof result);

    // 1. Handle the expected successful object response
    if (result && typeof result === 'object' && result.ok === true) {
      console.log('✅ REGISTRATION: Standard success path - signIn returned object with ok: true');
      return { status: 'success' };
    }
    
    // 2. Handle the OBSERVED ANOMALY: signIn returns a URL string on (backend) success
    else if (typeof result === 'string' && (result.startsWith('http://') || result.startsWith('https://'))) {
      console.log('✅ REGISTRATION: NextAuth returned URL string - interpreting as success based on backend confirmation');
      console.log('🎯 REGISTRATION: URL result:', result);
      return { status: 'success' };
    }
    
    // 3. Handle the expected error object response
    else if (result && typeof result === 'object' && result.error) {
      console.log('❌ REGISTRATION: Auto sign-in failed:', result.error);
      return { status: 'failed' };
    }
    
    // 4. Fallback for any other unexpected results
    else {
      console.log('❌ REGISTRATION: Unexpected auto sign-in result structure:', result);
      return { status: 'failed' };
    }
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { status: 'invalid_data' };
    }

    return { status: 'failed' };
  }
};
