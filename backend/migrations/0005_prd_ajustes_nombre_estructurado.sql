-- 0005_prd_ajustes_nombre_estructurado.sql
-- PRD-Ajustes.md: Structured beneficiary name (three fields replacing single "nombre").
--
-- Adds nombres, apellido_paterno, apellido_materno columns to beneficiarios.
-- All three are NOT NULL with empty-string defaults for existing rows.
-- The legacy "nombre" column is preserved for backward compatibility.
-- The backend will compose nombre = "{NOMBRES} {APELLIDO_PATERNO} {APELLIDO_MATERNO}" on INSERT.

ALTER TABLE public.beneficiarios
  ADD COLUMN IF NOT EXISTS nombres           TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS apellido_paterno  TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS apellido_materno  TEXT NOT NULL DEFAULT '';
