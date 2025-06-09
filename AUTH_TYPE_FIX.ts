// Fix for frontend/app/(auth)/auth.ts line 178
// In the jwt callback, replace this section:

} else {
  // For credentials login, authUser already has the type from authorize()
  token.id = authUser.id;
  token.type = authUser.type || 'credentials';
}

// With this:

} else if (authUser?.id) {
  // For credentials login, authUser already has the type from authorize()
  token.id = authUser.id;
  token.type = authUser.type || 'credentials';
}