// FINAL FIX for frontend/app/(auth)/auth.ts
// Replace line 176-180 with this code to fix the TypeScript compilation error:

        } else if (authUser?.id) {
          // For credentials login, authUser already has the type from authorize()
          token.id = authUser.id;
          token.type = authUser.type || 'credentials';
        }

// This adds a type guard to ensure authUser.id exists before assigning it to token.id
// This resolves: Type 'string | undefined' is not assignable to type 'string'