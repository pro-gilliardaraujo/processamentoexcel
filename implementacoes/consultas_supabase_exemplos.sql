-- =====================================================================
-- CONSULTAS SUPABASE - EXEMPLOS PRÁTICOS
-- =====================================================================
-- Este arquivo contém exemplos de consultas SQL para acessar os dados
-- de parâmetros médios armazenados na tabela registros_painelmaq
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. CONSULTAS BÁSICAS
-- ---------------------------------------------------------------------

-- Buscar todas as frotas de uma data específica
SELECT 
    data_dia,
    frente_id,
    maquina_id,
    parametros_medios
FROM registros_painelmaq 
WHERE data_dia = '2025-08-05'
ORDER BY frente_id, maquina_id;

-- Buscar frotas de uma frente específica
SELECT 
    maquina_id,
    parametros_medios->0->>'frota' as numero_frota,
    parametros_medios->0->>'vel_media' as velocidade,
    parametros_medios->0->>'uso_rtk' as uso_rtk
FROM registros_painelmaq 
WHERE data_dia = '2025-08-05' 
  AND frente_id = 'Frente03'
ORDER BY maquina_id;

-- Buscar dados de uma frota específica
SELECT 
    data_dia,
    frente_id,
    parametros_medios
FROM registros_painelmaq 
WHERE data_dia = '2025-08-05' 
  AND frente_id = 'Frente03' 
  AND maquina_id = 7032;

-- ---------------------------------------------------------------------
-- 2. CONSULTAS COM FILTROS NOS PARÂMETROS
-- ---------------------------------------------------------------------

-- Frotas com uso RTK acima de 80%
SELECT 
    data_dia,
    frente_id,
    maquina_id,
    parametros_medios->0->>'frota' as frota,
    CAST(parametros_medios->0->>'uso_rtk' AS DECIMAL) as uso_rtk
FROM registros_painelmaq 
WHERE CAST(parametros_medios->0->>'uso_rtk' AS DECIMAL) > 80
ORDER BY uso_rtk DESC;

-- Frotas com velocidade média acima de 12 km/h
SELECT 
    data_dia,
    frente_id,
    maquina_id,
    parametros_medios->0->>'frota' as frota,
    CAST(parametros_medios->0->>'vel_media' AS DECIMAL) as velocidade
FROM registros_painelmaq 
WHERE CAST(parametros_medios->0->>'vel_media' AS DECIMAL) > 12
ORDER BY velocidade DESC;

-- Frotas com mais de 8 horas de motor
SELECT 
    data_dia,
    frente_id,
    maquina_id,
    parametros_medios->0->>'frota' as frota,
    CAST(parametros_medios->0->>'horas_motor' AS DECIMAL) as horas_motor
FROM registros_painelmaq 
WHERE CAST(parametros_medios->0->>'horas_motor' AS DECIMAL) > 8
ORDER BY horas_motor DESC;

-- ---------------------------------------------------------------------
-- 3. CONSULTAS AGREGADAS
-- ---------------------------------------------------------------------

-- Estatísticas por frente em uma data
SELECT 
    frente_id,
    COUNT(*) as total_frotas,
    AVG(CAST(parametros_medios->0->>'vel_media' AS DECIMAL)) as velocidade_media,
    AVG(CAST(parametros_medios->0->>'uso_rtk' AS DECIMAL)) as uso_rtk_medio,
    AVG(CAST(parametros_medios->0->>'horas_motor' AS DECIMAL)) as horas_motor_media
FROM registros_painelmaq 
WHERE data_dia = '2025-08-05'
GROUP BY frente_id
ORDER BY frente_id;

-- Top 5 frotas por velocidade em uma data
SELECT 
    frente_id,
    maquina_id,
    parametros_medios->0->>'frota' as frota,
    CAST(parametros_medios->0->>'vel_media' AS DECIMAL) as velocidade
FROM registros_painelmaq 
WHERE data_dia = '2025-08-05'
ORDER BY velocidade DESC
LIMIT 5;

-- Frotas com maior uso de RTK por frente
SELECT DISTINCT ON (frente_id)
    frente_id,
    maquina_id,
    parametros_medios->0->>'frota' as frota,
    CAST(parametros_medios->0->>'uso_rtk' AS DECIMAL) as uso_rtk
FROM registros_painelmaq 
WHERE data_dia = '2025-08-05'
ORDER BY frente_id, uso_rtk DESC;

-- ---------------------------------------------------------------------
-- 4. CONSULTAS TEMPORAIS
-- ---------------------------------------------------------------------

-- Evolução de uma frota ao longo do tempo
SELECT 
    data_dia,
    CAST(parametros_medios->0->>'vel_media' AS DECIMAL) as velocidade,
    CAST(parametros_medios->0->>'uso_rtk' AS DECIMAL) as uso_rtk,
    CAST(parametros_medios->0->>'horas_motor' AS DECIMAL) as horas_motor
FROM registros_painelmaq 
WHERE frente_id = 'Frente03' 
  AND maquina_id = 7032
ORDER BY data_dia;

-- Comparar performance entre frotas ao longo do tempo
SELECT 
    data_dia,
    maquina_id,
    parametros_medios->0->>'frota' as frota,
    CAST(parametros_medios->0->>'vel_media' AS DECIMAL) as velocidade
FROM registros_painelmaq 
WHERE frente_id = 'Frente03'
  AND data_dia BETWEEN '2025-08-01' AND '2025-08-05'
ORDER BY data_dia, maquina_id;

-- Média móvel de 3 dias para uma frota
WITH dados_frota AS (
    SELECT 
        data_dia,
        CAST(parametros_medios->0->>'vel_media' AS DECIMAL) as velocidade
    FROM registros_painelmaq 
    WHERE frente_id = 'Frente03' 
      AND maquina_id = 7032
    ORDER BY data_dia
)
SELECT 
    data_dia,
    velocidade,
    AVG(velocidade) OVER (
        ORDER BY data_dia 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) as media_movel_3dias
FROM dados_frota;

-- ---------------------------------------------------------------------
-- 5. CONSULTAS PARA DASHBOARDS
-- ---------------------------------------------------------------------

-- Resumo executivo de uma data
SELECT 
    COUNT(*) as total_frotas,
    COUNT(DISTINCT frente_id) as total_frentes,
    AVG(CAST(parametros_medios->0->>'vel_media' AS DECIMAL)) as velocidade_geral,
    AVG(CAST(parametros_medios->0->>'uso_rtk' AS DECIMAL)) as uso_rtk_geral,
    SUM(CAST(parametros_medios->0->>'horas_motor' AS DECIMAL)) as total_horas_motor
FROM registros_painelmaq 
WHERE data_dia = '2025-08-05';

-- Ranking de frotas por eficiência (combinando velocidade e RTK)
SELECT 
    frente_id,
    maquina_id,
    parametros_medios->0->>'frota' as frota,
    CAST(parametros_medios->0->>'vel_media' AS DECIMAL) as velocidade,
    CAST(parametros_medios->0->>'uso_rtk' AS DECIMAL) as uso_rtk,
    -- Score combinado (velocidade * uso_rtk / 100)
    (CAST(parametros_medios->0->>'vel_media' AS DECIMAL) * 
     CAST(parametros_medios->0->>'uso_rtk' AS DECIMAL) / 100) as score_eficiencia
FROM registros_painelmaq 
WHERE data_dia = '2025-08-05'
ORDER BY score_eficiencia DESC;

-- Alertas: frotas com performance abaixo da média
WITH media_geral AS (
    SELECT 
        AVG(CAST(parametros_medios->0->>'vel_media' AS DECIMAL)) as vel_media_geral,
        AVG(CAST(parametros_medios->0->>'uso_rtk' AS DECIMAL)) as rtk_media_geral
    FROM registros_painelmaq 
    WHERE data_dia = '2025-08-05'
)
SELECT 
    r.frente_id,
    r.maquina_id,
    r.parametros_medios->0->>'frota' as frota,
    CAST(r.parametros_medios->0->>'vel_media' AS DECIMAL) as velocidade,
    CAST(r.parametros_medios->0->>'uso_rtk' AS DECIMAL) as uso_rtk,
    m.vel_media_geral,
    m.rtk_media_geral
FROM registros_painelmaq r, media_geral m
WHERE r.data_dia = '2025-08-05'
  AND (CAST(r.parametros_medios->0->>'vel_media' AS DECIMAL) < m.vel_media_geral * 0.8
       OR CAST(r.parametros_medios->0->>'uso_rtk' AS DECIMAL) < m.rtk_media_geral * 0.8)
ORDER BY r.frente_id, r.maquina_id;

-- ---------------------------------------------------------------------
-- 6. CONSULTAS DE MANUTENÇÃO
-- ---------------------------------------------------------------------

-- Verificar integridade dos dados
SELECT 
    data_dia,
    frente_id,
    COUNT(*) as total_registros,
    COUNT(CASE WHEN parametros_medios IS NOT NULL THEN 1 END) as com_parametros,
    COUNT(CASE WHEN parametros_medios IS NULL THEN 1 END) as sem_parametros
FROM registros_painelmaq 
GROUP BY data_dia, frente_id
ORDER BY data_dia DESC, frente_id;

-- Encontrar registros duplicados (não deveria acontecer)
SELECT 
    data_dia,
    frente_id,
    maquina_id,
    COUNT(*) as total
FROM registros_painelmaq 
GROUP BY data_dia, frente_id, maquina_id
HAVING COUNT(*) > 1;

-- Últimas atualizações por frente
SELECT DISTINCT ON (frente_id)
    frente_id,
    data_dia,
    updated_at
FROM registros_painelmaq 
ORDER BY frente_id, updated_at DESC;

-- ---------------------------------------------------------------------
-- 7. VIEWS ÚTEIS (para criar views no Supabase)
-- ---------------------------------------------------------------------

-- View com dados "achatados" para facilitar consultas
CREATE OR REPLACE VIEW vw_parametros_frotas AS
SELECT 
    data_dia,
    frente_id,
    maquina_id,
    CAST(parametros_medios->0->>'frota' AS INTEGER) as frota,
    CAST(parametros_medios->0->>'horimetro' AS DECIMAL) as horimetro,
    CAST(parametros_medios->0->>'uso_rtk' AS DECIMAL) as uso_rtk,
    CAST(parametros_medios->0->>'horas_elevador' AS DECIMAL) as horas_elevador,
    CAST(parametros_medios->0->>'horas_motor' AS DECIMAL) as horas_motor,
    CAST(parametros_medios->0->>'vel_media' AS DECIMAL) as vel_media,
    CAST(parametros_medios->0->>'rpm_motor_media' AS DECIMAL) as rpm_motor_media,
    CAST(parametros_medios->0->>'rpm_extrator_media' AS DECIMAL) as rpm_extrator_media,
    CAST(parametros_medios->0->>'pressao_corte_media' AS DECIMAL) as pressao_corte_media,
    CAST(parametros_medios->0->>'corte_base_auto' AS DECIMAL) as corte_base_auto,
    updated_at
FROM registros_painelmaq;

-- View com estatísticas diárias por frente
CREATE OR REPLACE VIEW vw_estatisticas_diarias AS
SELECT 
    data_dia,
    frente_id,
    COUNT(*) as total_frotas,
    AVG(CAST(parametros_medios->0->>'vel_media' AS DECIMAL)) as velocidade_media,
    AVG(CAST(parametros_medios->0->>'uso_rtk' AS DECIMAL)) as uso_rtk_medio,
    AVG(CAST(parametros_medios->0->>'horas_motor' AS DECIMAL)) as horas_motor_media,
    SUM(CAST(parametros_medios->0->>'horas_motor' AS DECIMAL)) as total_horas_motor
FROM registros_painelmaq 
GROUP BY data_dia, frente_id;

-- ---------------------------------------------------------------------
-- FIM DO ARQUIVO
-- ---------------------------------------------------------------------
