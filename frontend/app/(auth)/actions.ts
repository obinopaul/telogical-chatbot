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
    console.log('🔍 Has error?', !!result?.error);
    console.log('🔍 Has url?', !!result?.url);
    console.log('🔍 Has ok?', !!result?.ok);

    if (result?.error) {
      console.log('❌ Login failed:', result.error);
      return { status: 'failed' };
    }

    // NextAuth returns URL on success when redirect: false
    if (result?.url || result?.ok) {
      console.log('✅ ACTIONS.TS: Login successful! Returning success status...');
      return { status: 'success' };
    }

    console.log('❌ ACTIONS.TS: No success indicators found, returning failed');
    return { status: 'failed' };
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

    if (result?.error) {
      console.log('❌ Auto sign-in failed:', result.error);
      return { status: 'failed' };
    }

    // NextAuth returns URL on success when redirect: false  
    if (result?.url || result?.ok) {
      console.log('✅ Registration and auto sign-in successful!');
      return { status: 'success' };
    }

    return { status: 'failed' };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { status: 'invalid_data' };
    }

    return { status: 'failed' };
  }
};
