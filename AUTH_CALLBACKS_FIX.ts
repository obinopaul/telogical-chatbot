// Update the callbacks section in your frontend/app/(auth)/auth.ts file
// Replace the entire callbacks section with this:

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
      } else {
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
      session.user.type = token.type;
    }
    return session;
  },
},