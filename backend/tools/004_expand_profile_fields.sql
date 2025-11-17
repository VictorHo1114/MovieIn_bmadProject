-- Migration: Expand Profile Fields for Social Features
-- Date: 2025-11-17

-- Add new columns to profiles table
ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS bio TEXT,
ADD COLUMN IF NOT EXISTS favorite_genres JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS privacy_level VARCHAR(20) DEFAULT 'public',
ADD COLUMN IF NOT EXISTS last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Update existing rows to have default values
UPDATE profiles SET
  bio = NULL WHERE bio IS NULL,
  favorite_genres = '[]'::jsonb WHERE favorite_genres IS NULL,
  privacy_level = 'public' WHERE privacy_level IS NULL,
  last_active = NOW() WHERE last_active IS NULL;

-- Create index for faster queries on privacy_level and last_active
CREATE INDEX IF NOT EXISTS idx_profiles_privacy ON profiles(privacy_level);
CREATE INDEX IF NOT EXISTS idx_profiles_last_active ON profiles(last_active DESC);

-- Add comment to document the schema
COMMENT ON COLUMN profiles.bio IS 'User biography/self-introduction for social features';
COMMENT ON COLUMN profiles.favorite_genres IS 'Array of favorite movie genres';
COMMENT ON COLUMN profiles.privacy_level IS 'Privacy setting: public, friends, or private';
COMMENT ON COLUMN profiles.last_active IS 'Last activity timestamp for online status';
