-- Fix schema state: ensure all columns exist without conflicts
-- This migration is idempotent and safe to run multiple times

-- Ensure User table has all required columns
DO $$ BEGIN
 ALTER TABLE "User" ADD COLUMN "name" varchar(128);
EXCEPTION
 WHEN duplicate_column THEN null;
END $$;

DO $$ BEGIN
 ALTER TABLE "User" ADD COLUMN "image" text;
EXCEPTION
 WHEN duplicate_column THEN null;
END $$;

DO $$ BEGIN
 ALTER TABLE "User" ADD COLUMN "created_at" timestamp DEFAULT now() NOT NULL;
EXCEPTION
 WHEN duplicate_column THEN null;
END $$;

-- Ensure Chat table has all required columns
DO $$ BEGIN
 ALTER TABLE "Chat" ADD COLUMN "title" text NOT NULL DEFAULT 'New Chat';
EXCEPTION
 WHEN duplicate_column THEN null;
END $$;

DO $$ BEGIN
 ALTER TABLE "Chat" ADD COLUMN "visibility" varchar DEFAULT 'private' NOT NULL;
EXCEPTION
 WHEN duplicate_column THEN null;
END $$;

-- Create QueryCache table if it doesn't exist
CREATE TABLE IF NOT EXISTS "QueryCache" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"chat_id" uuid NOT NULL,
	"user_question_hash" varchar(64) NOT NULL,
	"user_question" text NOT NULL,
	"ai_response" text NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"expires_at" timestamp,
	"hit_count" varchar DEFAULT '1' NOT NULL,
	"user_id" uuid NOT NULL
);

-- Add foreign key constraints for QueryCache if they don't exist
DO $$ BEGIN
 ALTER TABLE "QueryCache" ADD CONSTRAINT "QueryCache_chat_id_Chat_id_fk" FOREIGN KEY ("chat_id") REFERENCES "public"."Chat"("id") ON DELETE cascade ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
 ALTER TABLE "QueryCache" ADD CONSTRAINT "QueryCache_user_id_User_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."User"("id") ON DELETE cascade ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;