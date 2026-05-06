-- Migration 0006: Convert tiene_imss / tiene_infonavit to nullable triestado
-- PRD-Ajustes §3.3 — IMSS/INFONAVIT Triestado
-- Columns become: 1=SI, 0=NO, NULL=NO_APLICA
-- Run against Supabase directly: Supabase SQL editor or local psql

-- 1. Drop NOT NULL and DEFAULT constraints
ALTER TABLE tutores
  ALTER COLUMN tiene_imss    DROP NOT NULL,
  ALTER COLUMN tiene_imss    DROP DEFAULT,
  ALTER COLUMN tiene_infonavit DROP NOT NULL,
  ALTER COLUMN tiene_infonavit DROP DEFAULT;

-- 2. Drop existing strict CHECK constraints
ALTER TABLE tutores DROP CONSTRAINT IF EXISTS tutores_tiene_imss_check;
ALTER TABLE tutores DROP CONSTRAINT IF EXISTS tutores_tiene_infonavit_check;

-- Also drop any CHECK with different naming patterns
DO $$
BEGIN
    -- Drop any remaining CHECK on tiene_imss (various naming conventions)
    EXECUTE (
        SELECT string_agg('ALTER TABLE tutores DROP CONSTRAINT IF EXISTS ' || quote_ident(conname) || ';', ' ')
        FROM pg_constraint
        WHERE conrelid = 'tutores'::regclass
          AND contype = 'c'
          AND conname LIKE '%tiene_imss%'
    );
    -- Drop any remaining CHECK on tiene_infonavit
    EXECUTE (
        SELECT string_agg('ALTER TABLE tutores DROP CONSTRAINT IF EXISTS ' || quote_ident(conname) || ';', ' ')
        FROM pg_constraint
        WHERE conrelid = 'tutores'::regclass
          AND contype = 'c'
          AND conname LIKE '%tiene_infonavit%'
    );
END $$;

-- 3. Add new CHECK constraints that allow NULL
ALTER TABLE tutores
  ADD CONSTRAINT chk_tiene_imss CHECK (tiene_imss IS NULL OR tiene_imss IN (0, 1)),
  ADD CONSTRAINT chk_tiene_infonavit CHECK (tiene_infonavit IS NULL OR tiene_infonavit IN (0, 1));

-- 4. Backfill: convert any remaining NULLs to 0 for historical consistency
--    (Historical data had NOT NULL DEFAULT 0, so NULLs shouldn't exist)
--    This is a safety measure only.
UPDATE tutores SET tiene_imss = 0 WHERE tiene_imss IS NULL;
UPDATE tutores SET tiene_infonavit = 0 WHERE tiene_infonavit IS NULL;
