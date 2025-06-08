/**
 * Simple password hashing utility
 * For production, replace with bcryptjs
 */

import { createHash } from 'crypto';

export function hashPassword(password: string): string {
  // Simple hash for now - replace with bcryptjs in production
  return createHash('sha256').update(password + 'telogical-salt').digest('hex');
}

export function verifyPassword(password: string, hash: string): boolean {
  return hashPassword(password) === hash;
}