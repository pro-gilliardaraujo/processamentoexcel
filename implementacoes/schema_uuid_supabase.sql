-- =====================================================================
-- SOLUÇÃO UUID: Schema atualizado para usar UUID como chave única
-- =====================================================================
-- Esta solução adiciona uma coluna UUID como identificador único
-- e mantém a chave primária composta para integridade relacional
-- =====================================================================

-- 1. ADICIONAR COLUNA UUID À TABELA EXISTENTE
ALTER TABLE public.registros_painelmaq 
ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid() UNIQUE;

-- 2. REMOVER O ÍNDICE PROBLEMÁTICO (se existir)
DROP INDEX IF EXISTS public.uniq_registro_dia;

-- 3. CRIAR ÍNDICE ÚNICO NA COLUNA UUID
CREATE UNIQUE INDEX IF NOT EXISTS registros_painelmaq_uuid_idx 
ON public.registros_painelmaq (id);

-- 4. MANTER A CHAVE PRIMÁRIA COMPOSTA (importante para lógica de negócio)
-- A chave primária (data_dia, frente_id, maquina_id) permanece inalterada
-- Isso garante que não podemos ter registros duplicados para a mesma frota/data

-- 5. ADICIONAR COMENTÁRIOS PARA DOCUMENTAÇÃO
COMMENT ON COLUMN public.registros_painelmaq.id IS 'Identificador único UUID para cada registro';
COMMENT ON TABLE public.registros_painelmaq IS 'Registros de parâmetros por frota com UUID único e chave primária composta';

-- =====================================================================
-- VERIFICAÇÕES PÓS-IMPLEMENTAÇÃO
-- =====================================================================

-- Verificar se a coluna UUID foi criada
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'registros_painelmaq' 
  AND column_name = 'id';

-- Verificar todos os índices da tabela
SELECT schemaname, indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'registros_painelmaq'
ORDER BY indexname;

-- Verificar constraints da tabela
SELECT constraint_name, constraint_type 
FROM information_schema.table_constraints 
WHERE table_name = 'registros_painelmaq'
ORDER BY constraint_type, constraint_name;

-- =====================================================================
-- ESTRUTURA FINAL DA TABELA
-- =====================================================================
/*
Após executar este script, a tabela terá:

COLUNAS:
- id UUID (UNIQUE, DEFAULT gen_random_uuid()) ← NOVO
- data_dia DATE (NOT NULL)
- frente_id TEXT (NOT NULL)  
- maquina_id INTEGER (NOT NULL)
- parametros_medios JSONB
- painel_esquerdo JSONB
- gantt_intervals JSONB
- painel_direito JSONB
- afericao_rolos JSONB DEFAULT '{}'
- acumulado JSONB DEFAULT '{}'
- updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()

CONSTRAINTS:
- PRIMARY KEY: (data_dia, frente_id, maquina_id)
- UNIQUE: id (UUID)

ÍNDICES:
- registros_painelmaq_pkey (PRIMARY KEY)
- registros_painelmaq_uuid_idx (UNIQUE UUID)
- registros_painelmaq_frente_dia_idx (performance)
- registros_painelmaq_maquina_dia_idx (performance)
*/

-- =====================================================================
-- EXEMPLO DE USO
-- =====================================================================

-- Inserir registro com UUID automático
INSERT INTO public.registros_painelmaq 
(data_dia, frente_id, maquina_id, parametros_medios)
VALUES 
('2025-08-07', 'Frente04', 7032, '[{"frota": 7032, "vel_media": 12.3}]');

-- UUID será gerado automaticamente
-- Buscar pelo UUID gerado
SELECT id, data_dia, frente_id, maquina_id 
FROM public.registros_painelmaq 
WHERE data_dia = '2025-08-07' AND frente_id = 'Frente04';

-- =====================================================================
-- ROLLBACK (se necessário)
-- =====================================================================
/*
Se precisar reverter as mudanças:

-- Remover coluna UUID
ALTER TABLE public.registros_painelmaq DROP COLUMN IF EXISTS id;

-- Recriar índice original (NÃO RECOMENDADO)
-- CREATE UNIQUE INDEX uniq_registro_dia ON public.registros_painelmaq (data_dia);
*/
