# 💻 Exemplos de Código Frontend - Integração Supabase

## 🎯 Visão Geral

Este documento contém exemplos práticos de como acessar e utilizar os dados de parâmetros médios armazenados no Supabase em aplicações frontend.

## 🔧 Configuração Inicial

### JavaScript/TypeScript (Supabase Client)

```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://kjlwqezxzqjfhacmjhbh.supabase.co'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
const supabase = createClient(supabaseUrl, supabaseKey)
```

## 📊 Exemplos React/Next.js

### 1. Hook Personalizado para Buscar Frotas

```typescript
// hooks/useFrotas.ts
import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

interface ParametrosFrota {
  frota: number
  horimetro: number
  uso_rtk: number
  horas_elevador: number
  horas_motor: number
  vel_media: number
  rpm_motor_media: number
  rpm_extrator_media: number
  pressao_corte_media: number
  corte_base_auto: number
}

interface RegistroFrota {
  data_dia: string
  frente_id: string
  maquina_id: number
  parametros_medios: ParametrosFrota[]
}

export const useFrotas = (dataDia: string, frenteId: string) => {
  const [frotas, setFrotas] = useState<RegistroFrota[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchFrotas = async () => {
      try {
        setLoading(true)
        const { data, error } = await supabase
          .from('registros_painelmaq')
          .select('data_dia, frente_id, maquina_id, parametros_medios')
          .eq('data_dia', dataDia)
          .eq('frente_id', frenteId)
          .order('maquina_id')

        if (error) throw error
        setFrotas(data || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erro desconhecido')
      } finally {
        setLoading(false)
      }
    }

    if (dataDia && frenteId) {
      fetchFrotas()
    }
  }, [dataDia, frenteId])

  return { frotas, loading, error }
}
```

### 2. Componente Dashboard de Frotas

```tsx
// components/FrotasDashboard.tsx
import React from 'react'
import { useFrotas } from '../hooks/useFrotas'

interface Props {
  dataDia: string
  frenteId: string
}

export const FrotasDashboard: React.FC<Props> = ({ dataDia, frenteId }) => {
  const { frotas, loading, error } = useFrotas(dataDia, frenteId)

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <h3 className="text-red-800 font-medium">Erro ao carregar dados</h3>
        <p className="text-red-600 mt-1">{error}</p>
      </div>
    )
  }

  if (frotas.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">Nenhuma frota encontrada para {frenteId} em {dataDia}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-2xl font-bold text-gray-900">
          {frenteId} - {new Date(dataDia).toLocaleDateString('pt-BR')}
        </h2>
        <p className="text-gray-600 mt-1">{frotas.length} frotas ativas</p>
      </div>

      {/* Grid de Frotas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {frotas.map((registro) => {
          const params = registro.parametros_medios[0]
          return (
            <FrotaCard key={registro.maquina_id} params={params} />
          )
        })}
      </div>

      {/* Estatísticas Resumo */}
      <EstatisticasResumo frotas={frotas} />
    </div>
  )
}
```

### 3. Componente Card de Frota

```tsx
// components/FrotaCard.tsx
import React from 'react'

interface ParametrosFrota {
  frota: number
  horimetro: number
  uso_rtk: number
  horas_elevador: number
  horas_motor: number
  vel_media: number
  rpm_motor_media: number
  rpm_extrator_media: number
  pressao_corte_media: number
  corte_base_auto: number
}

interface Props {
  params: ParametrosFrota
}

export const FrotaCard: React.FC<Props> = ({ params }) => {
  const getStatusColor = (valor: number, limite: number) => {
    return valor >= limite ? 'text-green-600' : 'text-yellow-600'
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="bg-blue-50 px-6 py-4 border-b">
        <h3 className="text-lg font-semibold text-blue-900">
          Frota {params.frota}
        </h3>
        <p className="text-blue-600 text-sm">
          {params.horimetro.toFixed(1)}h horímetro
        </p>
      </div>

      {/* Métricas Principais */}
      <div className="p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500">Velocidade Média</p>
            <p className={`text-xl font-bold ${getStatusColor(params.vel_media, 10)}`}>
              {params.vel_media.toFixed(1)} km/h
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Uso RTK</p>
            <p className={`text-xl font-bold ${getStatusColor(params.uso_rtk, 80)}`}>
              {params.uso_rtk.toFixed(1)}%
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500">Horas Motor</p>
            <p className="text-lg font-medium">{params.horas_motor.toFixed(1)}h</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Horas Elevador</p>
            <p className="text-lg font-medium">{params.horas_elevador.toFixed(1)}h</p>
          </div>
        </div>

        {/* Detalhes Técnicos */}
        <div className="pt-4 border-t border-gray-100">
          <details className="group">
            <summary className="cursor-pointer text-sm font-medium text-gray-700 group-open:text-blue-600">
              Detalhes Técnicos
            </summary>
            <div className="mt-2 text-sm text-gray-600 space-y-1">
              <p>RPM Motor: {params.rpm_motor_media.toFixed(0)}</p>
              <p>RPM Extrator: {params.rpm_extrator_media.toFixed(0)}</p>
              <p>Pressão Corte: {params.pressao_corte_media.toFixed(0)} psi</p>
              <p>Corte Base Auto: {params.corte_base_auto.toFixed(1)}%</p>
            </div>
          </details>
        </div>
      </div>
    </div>
  )
}
```

### 4. Componente de Estatísticas

```tsx
// components/EstatisticasResumo.tsx
import React from 'react'

interface Props {
  frotas: RegistroFrota[]
}

export const EstatisticasResumo: React.FC<Props> = ({ frotas }) => {
  const calcularEstatisticas = () => {
    const params = frotas.map(f => f.parametros_medios[0])
    
    return {
      velocidadeMedia: params.reduce((acc, p) => acc + p.vel_media, 0) / params.length,
      usoRtkMedio: params.reduce((acc, p) => acc + p.uso_rtk, 0) / params.length,
      totalHorasMotor: params.reduce((acc, p) => acc + p.horas_motor, 0),
      frotaMaisRapida: params.reduce((prev, curr) => 
        prev.vel_media > curr.vel_media ? prev : curr
      ),
      frotaMaiorRtk: params.reduce((prev, curr) => 
        prev.uso_rtk > curr.uso_rtk ? prev : curr
      )
    }
  }

  const stats = calcularEstatisticas()

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Estatísticas do Dia
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-blue-600">
            {stats.velocidadeMedia.toFixed(1)}
          </p>
          <p className="text-sm text-gray-500">Velocidade Média km/h</p>
        </div>
        
        <div className="text-center">
          <p className="text-2xl font-bold text-green-600">
            {stats.usoRtkMedio.toFixed(1)}%
          </p>
          <p className="text-sm text-gray-500">Uso RTK Médio</p>
        </div>
        
        <div className="text-center">
          <p className="text-2xl font-bold text-purple-600">
            {stats.totalHorasMotor.toFixed(1)}h
          </p>
          <p className="text-sm text-gray-500">Total Horas Motor</p>
        </div>
        
        <div className="text-center">
          <p className="text-2xl font-bold text-orange-600">
            {stats.frotaMaisRapida.frota}
          </p>
          <p className="text-sm text-gray-500">Frota Mais Rápida</p>
        </div>
        
        <div className="text-center">
          <p className="text-2xl font-bold text-indigo-600">
            {stats.frotaMaiorRtk.frota}
          </p>
          <p className="text-sm text-gray-500">Maior Uso RTK</p>
        </div>
      </div>
    </div>
  )
}
```

## 📈 Exemplos Vue.js

### 1. Composable para Frotas (Vue 3)

```typescript
// composables/useFrotas.ts
import { ref, computed, watchEffect } from 'vue'
import { supabase } from '../lib/supabase'

export const useFrotas = (dataDia: Ref<string>, frenteId: Ref<string>) => {
  const frotas = ref([])
  const loading = ref(false)
  const error = ref(null)

  const fetchFrotas = async () => {
    if (!dataDia.value || !frenteId.value) return

    try {
      loading.value = true
      error.value = null

      const { data, error: supabaseError } = await supabase
        .from('registros_painelmaq')
        .select('data_dia, frente_id, maquina_id, parametros_medios')
        .eq('data_dia', dataDia.value)
        .eq('frente_id', frenteId.value)
        .order('maquina_id')

      if (supabaseError) throw supabaseError
      frotas.value = data || []
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
  }

  // Reativo: busca automaticamente quando dataDia ou frenteId mudam
  watchEffect(() => {
    fetchFrotas()
  })

  const estatisticas = computed(() => {
    if (!frotas.value.length) return null

    const params = frotas.value.map(f => f.parametros_medios[0])
    return {
      velocidadeMedia: params.reduce((acc, p) => acc + p.vel_media, 0) / params.length,
      usoRtkMedio: params.reduce((acc, p) => acc + p.uso_rtk, 0) / params.length,
      totalFrotas: frotas.value.length
    }
  })

  return {
    frotas: readonly(frotas),
    loading: readonly(loading),
    error: readonly(error),
    estatisticas,
    refetch: fetchFrotas
  }
}
```

### 2. Componente Vue Dashboard

```vue
<!-- components/FrotasDashboard.vue -->
<template>
  <div class="frotas-dashboard">
    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Carregando frotas...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <h3>Erro ao carregar dados</h3>
      <p>{{ error }}</p>
      <button @click="refetch" class="retry-btn">Tentar Novamente</button>
    </div>

    <!-- Data Display -->
    <div v-else class="content">
      <!-- Header -->
      <div class="header">
        <h2>{{ frenteId }} - {{ formatDate(dataDia) }}</h2>
        <p>{{ frotas.length }} frotas ativas</p>
      </div>

      <!-- Estatísticas -->
      <div v-if="estatisticas" class="stats-grid">
        <div class="stat-card">
          <span class="stat-value">{{ estatisticas.velocidadeMedia.toFixed(1) }}</span>
          <span class="stat-label">Velocidade Média (km/h)</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ estatisticas.usoRtkMedio.toFixed(1) }}%</span>
          <span class="stat-label">Uso RTK Médio</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ estatisticas.totalFrotas }}</span>
          <span class="stat-label">Total de Frotas</span>
        </div>
      </div>

      <!-- Grid de Frotas -->
      <div class="frotas-grid">
        <FrotaCard 
          v-for="registro in frotas" 
          :key="registro.maquina_id"
          :parametros="registro.parametros_medios[0]"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useFrotas } from '../composables/useFrotas'
import FrotaCard from './FrotaCard.vue'

const props = defineProps<{
  dataDia: string
  frenteId: string
}>()

const dataDiaRef = computed(() => props.dataDia)
const frenteIdRef = computed(() => props.frenteId)

const { frotas, loading, error, estatisticas, refetch } = useFrotas(dataDiaRef, frenteIdRef)

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('pt-BR')
}
</script>
```

## 🔍 Exemplos de Filtros e Pesquisa

### 1. Filtro Avançado de Frotas

```typescript
// hooks/useFrotasComFiltros.ts
export const useFrotasComFiltros = () => {
  const [filtros, setFiltros] = useState({
    dataDia: '',
    frenteId: '',
    velocidadeMin: 0,
    usoRtkMin: 0,
    ordenarPor: 'frota' as 'frota' | 'velocidade' | 'uso_rtk'
  })

  const fetchFrotasComFiltros = async () => {
    let query = supabase
      .from('registros_painelmaq')
      .select('data_dia, frente_id, maquina_id, parametros_medios')

    // Filtros básicos
    if (filtros.dataDia) {
      query = query.eq('data_dia', filtros.dataDia)
    }
    if (filtros.frenteId) {
      query = query.eq('frente_id', filtros.frenteId)
    }

    const { data, error } = await query

    if (error) throw error

    // Filtros avançados (lado cliente)
    let frotasFiltradas = data || []

    if (filtros.velocidadeMin > 0) {
      frotasFiltradas = frotasFiltradas.filter(registro => 
        registro.parametros_medios[0].vel_media >= filtros.velocidadeMin
      )
    }

    if (filtros.usoRtkMin > 0) {
      frotasFiltradas = frotasFiltradas.filter(registro => 
        registro.parametros_medios[0].uso_rtk >= filtros.usoRtkMin
      )
    }

    // Ordenação
    frotasFiltradas.sort((a, b) => {
      const paramA = a.parametros_medios[0]
      const paramB = b.parametros_medios[0]
      
      switch (filtros.ordenarPor) {
        case 'velocidade':
          return paramB.vel_media - paramA.vel_media
        case 'uso_rtk':
          return paramB.uso_rtk - paramA.uso_rtk
        default:
          return paramA.frota - paramB.frota
      }
    })

    return frotasFiltradas
  }

  return { filtros, setFiltros, fetchFrotasComFiltros }
}
```

### 2. Componente de Pesquisa em Tempo Real

```tsx
// components/PesquisaFrotas.tsx
export const PesquisaFrotas: React.FC = () => {
  const [termoPesquisa, setTermoPesquisa] = useState('')
  const [resultados, setResultados] = useState([])
  
  const pesquisarFrotas = useCallback(
    debounce(async (termo: string) => {
      if (!termo) {
        setResultados([])
        return
      }

      const { data, error } = await supabase
        .from('registros_painelmaq')
        .select('data_dia, frente_id, maquina_id, parametros_medios')
        .or(`frente_id.ilike.%${termo}%,maquina_id.eq.${parseInt(termo) || 0}`)
        .limit(10)

      if (!error) {
        setResultados(data || [])
      }
    }, 300),
    []
  )

  useEffect(() => {
    pesquisarFrotas(termoPesquisa)
  }, [termoPesquisa, pesquisarFrotas])

  return (
    <div className="relative">
      <input
        type="text"
        placeholder="Pesquisar por frente ou número da frota..."
        value={termoPesquisa}
        onChange={(e) => setTermoPesquisa(e.target.value)}
        className="w-full px-4 py-2 border rounded-lg"
      />
      
      {resultados.length > 0 && (
        <div className="absolute top-full left-0 right-0 bg-white border rounded-lg shadow-lg mt-1 max-h-64 overflow-y-auto">
          {resultados.map((resultado) => (
            <div key={`${resultado.data_dia}-${resultado.frente_id}-${resultado.maquina_id}`} 
                 className="p-3 hover:bg-gray-50 cursor-pointer">
              <p className="font-medium">
                Frota {resultado.parametros_medios[0].frota} - {resultado.frente_id}
              </p>
              <p className="text-sm text-gray-500">
                {resultado.data_dia} | Velocidade: {resultado.parametros_medios[0].vel_media.toFixed(1)} km/h
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

## 📱 Exemplo para Mobile (React Native)

```tsx
// screens/FrotasScreen.tsx
import React from 'react'
import { ScrollView, View, Text, RefreshControl } from 'react-native'
import { useFrotas } from '../hooks/useFrotas'

export const FrotasScreen: React.FC = () => {
  const { frotas, loading, error, refetch } = useFrotas('2025-08-05', 'Frente03')

  return (
    <ScrollView
      refreshControl={
        <RefreshControl refreshing={loading} onRefresh={refetch} />
      }
    >
      {frotas.map((registro) => {
        const params = registro.parametros_medios[0]
        return (
          <View key={registro.maquina_id} style={styles.frotaCard}>
            <Text style={styles.frotaTitle}>Frota {params.frota}</Text>
            <Text>Velocidade: {params.vel_media.toFixed(1)} km/h</Text>
            <Text>Uso RTK: {params.uso_rtk.toFixed(1)}%</Text>
          </View>
        )
      })}
    </ScrollView>
  )
}
```

---

**Observação**: Todos os exemplos utilizam as chaves em formato snake_case conforme implementado na integração, garantindo consistência e facilidade de uso em código.
