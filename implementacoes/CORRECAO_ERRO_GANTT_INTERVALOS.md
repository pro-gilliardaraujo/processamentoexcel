# 🔧 Correção: Erro gantt_intervalos no Supabase

## ❌ Problema Identificado

**Erro:** `Could not find the 'gantt_intervalos' column of 'registros_painelmaq' in the schema cache`

**Causa:** A coluna `gantt_intervalos` não existe na tabela `registros_painelmaq` do Supabase.

## ✅ Solução

### 1. Executar Script SQL no Supabase

Acesse o **Supabase SQL Editor** e execute o seguinte comando:

```sql
-- Adicionar a coluna gantt_intervalos como JSONB
ALTER TABLE public.registros_painelmaq 
ADD COLUMN gantt_intervalos JSONB NULL DEFAULT '{}'::jsonb;

-- Comentário descritivo para a coluna
COMMENT ON COLUMN public.registros_painelmaq.gantt_intervalos IS 
'Dados dos intervalos operacionais por frota em formato JSON. Contém tipos: Colhendo, Manobras, Manutenção, Disponível';
```

### 2. Verificar se a Coluna foi Criada

Execute este comando para confirmar:

```sql
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'registros_painelmaq' 
  AND column_name = 'gantt_intervalos';
```

**Resultado esperado:**
```
column_name      | data_type | is_nullable | column_default
gantt_intervalos | jsonb     | YES         | '{}'::jsonb
```

## 📋 Estrutura da Coluna gantt_intervalos

A coluna armazenará dados no formato:

```json
{
  "tem_dados": true,
  "total_intervalos": 5,
  "tipos": {
    "colhendo": {"intervalos": 2, "tempo_total_horas": 3.75},
    "manobras": {"intervalos": 1, "tempo_total_horas": 0.25},
    "manutencao": {"intervalos": 1, "tempo_total_horas": 1.0},
    "disponivel": {"intervalos": 1, "tempo_total_horas": 1.0}
  },
  "detalhes": [
    {
      "equipamento": 7032,
      "data": "2025-08-07",
      "intervalo": "1",
      "tipo": "colhendo",
      "inicio": "08:00:00",
      "fim": "10:30:00",
      "duracao_horas": 2.5
    }
  ]
}
```

## 🎯 Filtro por Frota Garantido

✅ **Cada registro de frota recebe apenas seus próprios intervalos**

- Frota 7032: intervalos onde `equipamento = 7032`
- Frota 7034: intervalos onde `equipamento = 7034`
- Frota 7035: intervalos onde `equipamento = 7035`

## 📝 Logs do Terminal Confirmam o Processamento

Os logs mostram que a lógica está funcionando corretamente:

```
📊 Processando intervalos para frota 7041: 359 de 586 registros
🎯 Intervalos processados: 359 total
    - Colhendo: 165 (11.98h)
    - Manobras: 160 (3.14h)
    - Manutenção: 3 (1.78h)
    - Disponível: 31 (7.00h)
```

## 🚀 Após Executar o Script SQL

1. **Execute o script SQL** no Supabase
2. **Teste novamente** o processamento dos arquivos
3. **Verifique** se os dados são enviados corretamente

O código está pronto e funcionando - só faltava a coluna no banco de dados!
