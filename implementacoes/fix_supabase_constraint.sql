-- =====================================================================
-- FIX: Remover constraint única problemática no Supabase
-- =====================================================================
-- PROBLEMA: O índice 'uniq_registro_dia' impede múltiplos registros
-- por data, mas precisamos de um registro por frota por data.
-- =====================================================================

-- 1. REMOVER O ÍNDICE ÚNICO PROBLEMÁTICO
DROP INDEX IF EXISTS public.uniq_registro_dia;

-- 2. VERIFICAR SE A CONSTRAINT FOI REMOVIDA
-- Execute esta query para confirmar:
SELECT schemaname, indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'registros_painelmaq' 
  AND indexname = 'uniq_registro_dia';
-- (Deve retornar 0 resultados se foi removido)

-- 3. CONFIRMAR QUE A CHAVE PRIMÁRIA AINDA EXISTE (deve existir)
SELECT constraint_name, constraint_type 
FROM information_schema.table_constraints 
WHERE table_name = 'registros_painelmaq' 
  AND constraint_type = 'PRIMARY KEY';
-- (Deve mostrar: registros_painelmaq_pkey | PRIMARY KEY)

-- =====================================================================
-- EXPLICAÇÃO:
-- 
-- ANTES (problemático):
-- - Chave Primária: (data_dia, frente_id, maquina_id) ✅ Correto
-- - Índice Único: (data_dia) ❌ Problemático - impede múltiplas frotas
--
-- DEPOIS (correto):
-- - Chave Primária: (data_dia, frente_id, maquina_id) ✅ Permite múltiplas frotas
-- - Sem índice único em data_dia ✅ Permite um registro por frota
-- =====================================================================

-- 4. COMANDOS ALTERNATIVOS (se necessário)

-- Se houver problemas, usar comando mais específico:
-- DROP INDEX CONCURRENTLY IF EXISTS public.uniq_registro_dia;

-- Para verificar todos os índices da tabela:
-- SELECT * FROM pg_indexes WHERE tablename = 'registros_painelmaq';

-- =====================================================================
-- TESTE APÓS CORREÇÃO:
-- 
-- Depois de executar o DROP INDEX, teste inserindo dados:
-- 
-- INSERT INTO registros_painelmaq (data_dia, frente_id, maquina_id, parametros_medios) 
-- VALUES 
--   ('2025-08-07', 'Frente04', 7032, '[{"frota": 7032, "vel_media": 12.3}]'),
--   ('2025-08-07', 'Frente04', 7036, '[{"frota": 7036, "vel_media": 11.8}]'),
--   ('2025-08-07', 'Frente04', 7037, '[{"frota": 7037, "vel_media": 13.2}]');
-- 
-- Se não houver erro, a correção funcionou!
-- =====================================================================
