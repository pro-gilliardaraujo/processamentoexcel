#!/usr/bin/env python3
"""
Exemplo prático de como ficará no Supabase após processar um arquivo com 4 frotas.

Este arquivo demonstra o resultado exato da integração implementada.
"""

import json
from datetime import datetime

def exemplo_arquivo_processado():
    """
    Simula o processamento de um arquivo: colhedorasFrente03_05082025.txt
    com 4 frotas diferentes.
    """
    
    print("📁 ARQUIVO PROCESSADO: colhedorasFrente03_05082025.txt")
    print("📊 PARÂMETROS MÉDIOS CALCULADOS: 4 frotas encontradas")
    print("="*80)
    
    # Dados que seriam calculados pelo sistema
    parametros_calculados = [
        {
            "Frota": 7032,
            "Horimetro": 1234.50,
            "Uso RTK (%)": 85.67,
            "Horas Elevador": 8.25,
            "Horas Motor": 9.50,
            "Velocidade Media (km/h)": 12.30,
            "RPM Motor Media": 2100.00,
            "RPM Extrator Media": 850.00,
            "Pressao Corte Media (psi)": 450.00,
            "Corte Base Auto (%)": 95.25
        },
        {
            "Frota": 7042,
            "Horimetro": 1156.75,
            "Uso RTK (%)": 78.90,
            "Horas Elevador": 7.80,
            "Horas Motor": 8.90,
            "Velocidade Media (km/h)": 11.80,
            "RPM Motor Media": 2050.00,
            "RPM Extrator Media": 825.00,
            "Pressao Corte Media (psi)": 440.00,
            "Corte Base Auto (%)": 92.50
        },
        {
            "Frota": 7052,
            "Horimetro": 987.25,
            "Uso RTK (%)": 92.15,
            "Horas Elevador": 6.50,
            "Horas Motor": 7.75,
            "Velocidade Media (km/h)": 13.20,
            "RPM Motor Media": 2150.00,
            "RPM Extrator Media": 875.00,
            "Pressao Corte Media (psi)": 465.00,
            "Corte Base Auto (%)": 98.75
        },
        {
            "Frota": 7062,
            "Horimetro": 1890.30,
            "Uso RTK (%)": 88.45,
            "Horas Elevador": 9.10,
            "Horas Motor": 10.25,
            "Velocidade Media (km/h)": 11.90,
            "RPM Motor Media": 2080.00,
            "RPM Extrator Media": 840.00,
            "Pressao Corte Media (psi)": 455.00,
            "Corte Base Auto (%)": 94.80
        }
    ]
    
    return parametros_calculados

def converter_chaves_snake_case(dados_dict):
    """Converte chaves para snake_case (mesma função do sistema)."""
    mapeamento_chaves = {
        'Frota': 'frota',
        'Horimetro': 'horimetro',
        'Uso RTK (%)': 'uso_rtk',
        'Horas Elevador': 'horas_elevador',
        'Horas Motor': 'horas_motor',
        'Velocidade Media (km/h)': 'vel_media',
        'RPM Motor Media': 'rpm_motor_media',
        'RPM Extrator Media': 'rpm_extrator_media',
        'Pressao Corte Media (psi)': 'pressao_corte_media',
        'Corte Base Auto (%)': 'corte_base_auto'
    }
    
    dados_convertidos = {}
    for chave_original, valor in dados_dict.items():
        chave_nova = mapeamento_chaves.get(chave_original, chave_original.lower().replace(' ', '_'))
        dados_convertidos[chave_nova] = valor
    
    return dados_convertidos

def mostrar_resultado_supabase():
    """Mostra como ficará exatamente na tabela do Supabase."""
    
    parametros = exemplo_arquivo_processado()
    
    print("\n🎯 RESULTADO NO SUPABASE:")
    print("📋 Tabela: registros_painelmaq")
    print("🔑 Chave primária: (data_dia, frente_id, maquina_id)")
    print("="*80)
    
    # Informações extraídas do arquivo
    data_dia = "2025-08-05"
    frente_id = "Frente03"
    
    registros_criados = []
    
    for i, params in enumerate(parametros, 1):
        frota = params["Frota"]
        maquina_id = frota  # maquina_id = número da frota
        
        # Converter para snake_case
        params_convertidos = converter_chaves_snake_case(params)
        
        # Registro que será criado no Supabase
        registro = {
            "data_dia": data_dia,
            "frente_id": frente_id,
            "maquina_id": maquina_id,
            "parametros_medios": [params_convertidos],
            "painel_esquerdo": None,
            "gantt_intervals": None,
            "painel_direito": None,
            "afericao_rolos": {},
            "acumulado": {},
            "updated_at": datetime.now().isoformat()
        }
        
        registros_criados.append(registro)
        
        print(f"\n📝 REGISTRO {i}/4 - FROTA {frota}")
        print(f"   🔑 Chave: data_dia='{data_dia}', frente_id='{frente_id}', maquina_id={maquina_id}")
        print(f"   📊 parametros_medios:")
        print("   " + json.dumps(params_convertidos, indent=6, ensure_ascii=False))
    
    print(f"\n" + "="*80)
    print("📊 RESUMO DOS REGISTROS CRIADOS:")
    print(f"   • Total de registros: {len(registros_criados)}")
    print(f"   • Data: {data_dia}")
    print(f"   • Frente: {frente_id}")
    print(f"   • Frotas: {[r['maquina_id'] for r in registros_criados]}")
    
    print("\n🔍 CONSULTA SQL EQUIVALENTE:")
    print("="*80)
    print("SELECT data_dia, frente_id, maquina_id, parametros_medios")
    print("FROM registros_painelmaq")
    print(f"WHERE data_dia = '{data_dia}' AND frente_id = '{frente_id}'")
    print("ORDER BY maquina_id;")
    
    print("\n📋 RESULTADO DA CONSULTA:")
    print("-" * 80)
    for registro in registros_criados:
        print(f"| {registro['data_dia']} | {registro['frente_id']} | {registro['maquina_id']} | [1 parâmetro] |")
    
    print("\n💡 OBSERVAÇÕES IMPORTANTES:")
    print("="*80)
    print("1. 🔑 CHAVE PRIMÁRIA: Cada frota tem seu próprio registro")
    print("2. 📊 ESTRUTURA: maquina_id = número da frota")
    print("3. 🔄 UPSERT: Se processar o mesmo arquivo novamente, atualiza os registros")
    print("4. 🐍 SNAKE_CASE: Todas as chaves estão em formato amigável para código")
    print("5. 📈 ESCALABILIDADE: Cada frota pode ter dados diferentes")

def exemplo_acesso_dados():
    """Mostra como acessar os dados no código."""
    print("\n💻 EXEMPLO DE ACESSO AOS DADOS:")
    print("="*80)
    
    print("# JavaScript/TypeScript:")
    print("const frotas = await supabase")
    print("  .from('registros_painelmaq')")
    print("  .select('maquina_id, parametros_medios')")
    print("  .eq('data_dia', '2025-08-05')")
    print("  .eq('frente_id', 'Frente03');")
    print()
    print("frotas.forEach(frota => {")
    print("  const params = frota.parametros_medios[0];")
    print("  console.log(`Frota ${params.frota}: ${params.vel_media} km/h`);")
    print("});")
    
    print("\n# Python:")
    print("from supabase import create_client")
    print("response = supabase.table('registros_painelmaq') \\")
    print("  .select('maquina_id, parametros_medios') \\")
    print("  .eq('data_dia', '2025-08-05') \\")
    print("  .eq('frente_id', 'Frente03') \\")
    print("  .execute()")
    print()
    print("for registro in response.data:")
    print("    params = registro['parametros_medios'][0]")
    print("    print(f\"Frota {params['frota']}: {params['vel_media']} km/h\")")

def exemplo_dashboard():
    """Exemplo de como usar os dados em um dashboard."""
    print("\n📊 EXEMPLO DE DASHBOARD:")
    print("="*80)
    
    print("# React Component Example:")
    print("""
const FrotasPanel = () => {
  const [frotas, setFrotas] = useState([]);
  
  useEffect(() => {
    const fetchFrotas = async () => {
      const { data } = await supabase
        .from('registros_painelmaq')
        .select('maquina_id, parametros_medios')
        .eq('data_dia', '2025-08-05')
        .eq('frente_id', 'Frente03');
      
      setFrotas(data);
    };
    
    fetchFrotas();
  }, []);
  
  return (
    <div className="frotas-grid">
      {frotas.map(frota => {
        const params = frota.parametros_medios[0];
        return (
          <div key={frota.maquina_id} className="frota-card">
            <h3>Frota {params.frota}</h3>
            <p>Velocidade: {params.vel_media} km/h</p>
            <p>Uso RTK: {params.uso_rtk}%</p>
            <p>Horas Motor: {params.horas_motor}h</p>
          </div>
        );
      })}
    </div>
  );
};
""")

if __name__ == "__main__":
    print("🧪 EXEMPLO - RESULTADO NO SUPABASE COM 4 FROTAS")
    print("="*80)
    
    mostrar_resultado_supabase()
    exemplo_acesso_dados()
    exemplo_dashboard()
