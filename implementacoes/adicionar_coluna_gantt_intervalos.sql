-- Script para adicionar a coluna gantt_intervalos na tabela registros_painelmaq
-- Execute este script no Supabase SQL Editor

-- Adicionar a coluna gantt_intervalos como JSONB
ALTER TABLE public.registros_painelmaq 
ADD COLUMN gantt_intervalos JSONB NULL DEFAULT '{}'::jsonb;

-- Comentário descritivo para a coluna
COMMENT ON COLUMN public.registros_painelmaq.gantt_intervalos IS 
'Dados dos intervalos operacionais por frota em formato JSON. Contém tipos: Colhendo, Manobras, Manutenção, Disponível';

-- Verificar se a coluna foi adicionada corretamente
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'registros_painelmaq' 
  AND column_name = 'gantt_intervalos';
