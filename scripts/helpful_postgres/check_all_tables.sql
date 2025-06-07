  -- First, let's see what tables actually exist
  SELECT
      schemaname,
      tablename,
      tableowner
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY tablename;

  -- Get detailed information about each table structure
  SELECT
      t.table_name,
      c.column_name,
      c.data_type,
      c.character_maximum_length,
      c.column_default,
      c.is_nullable,
      CASE
          WHEN pk.column_name IS NOT NULL THEN 'PRIMARY KEY'
          WHEN fk.column_name IS NOT NULL THEN 'FOREIGN KEY'
          ELSE ''
      END as key_type
  FROM information_schema.tables t
  LEFT JOIN information_schema.columns c ON c.table_name = t.table_name
  LEFT JOIN (
      SELECT ku.table_name, ku.column_name
      FROM information_schema.table_constraints tc
      JOIN information_schema.key_column_usage ku ON tc.constraint_name = ku.constraint_name
      WHERE tc.constraint_type = 'PRIMARY KEY'
  ) pk ON pk.table_name = t.table_name AND pk.column_name = c.column_name
  LEFT JOIN (
      SELECT ku.table_name, ku.column_name
      FROM information_schema.table_constraints tc
      JOIN information_schema.key_column_usage ku ON tc.constraint_name = ku.constraint_name
      WHERE tc.constraint_type = 'FOREIGN KEY'
  ) fk ON fk.table_name = t.table_name AND fk.column_name = c.column_name
  WHERE t.table_schema = 'public'
  ORDER BY t.table_name, c.ordinal_position;

  -- Check foreign key constraints
  SELECT
      tc.table_name,
      kcu.column_name,
      ccu.table_name AS foreign_table_name,
      ccu.column_name AS foreign_column_name,
      tc.constraint_name
  FROM information_schema.table_constraints AS tc
  JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
  JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
  WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema = 'public'
  ORDER BY tc.table_name;
