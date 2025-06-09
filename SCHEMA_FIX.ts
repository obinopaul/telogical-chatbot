// Update your frontend/lib/db/schema.ts
// Add this import to the existing imports:
import { pgEnum } from 'drizzle-orm/pg-core';

// Add this enum definition before the user table:
export const userTypeEnum = pgEnum('user_type', ['regular', 'credentials']);

// In the user table definition, add this field:
export const user = pgTable('User', {
  id: varchar('id').primaryKey().notNull(),
  email: varchar('email', { length: 128 }).notNull().unique(),
  password: varchar('password', { length: 64 }),
  name: varchar('name', { length: 128 }),
  image: text('image'),
  type: userTypeEnum('type').default('regular').notNull(), // ADD THIS LINE
  createdAt: timestamp('created_at').notNull().defaultNow(),
});

// Export the UserType for use in other files:
export type UserType = 'regular' | 'credentials';