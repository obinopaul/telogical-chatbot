// Fix for line 85 in route.complex.ts
// Change this line:
// const userType: UserType = session.user.type;

// To this:
const userType: UserType = (session.user as any).type || 'guest';