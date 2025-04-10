# processamentoexcel

Sistema automatizado para processamento de dados de monitoramento de colhedoras.

## Descrição

Este projeto automatiza o processamento de dados de monitoramento de colhedoras agrícolas, transformando arquivos TXT brutos em relatórios Excel estruturados e formatados. Elimina a necessidade de processamento manual, garantindo resultados rápidos e consistentes.

## Funcionalidades

- Processa automaticamente arquivos TXT na pasta raiz
- Calcula métricas importantes para análise de desempenho:
  - Disponibilidade Mecânica por equipamento
  - Eficiência Energética por operador
  - Horas de Elevador por operador
  - Percentual de Motor Ocioso por operador
  - Uso de GPS por operador
  - Contabilização de horas totais por frota
- Filtra registros não relevantes como "TROCA DE TURNO"
- Gera planilhas auxiliares formatadas prontas para uso em relatórios finais

## Como usar

1. Coloque os arquivos TXT que deseja processar na mesma pasta do script `processamento_completo.py`
2. Execute o script com o comando:
   ```
   python processamento_completo.py
   ```
3. O script processará todos os arquivos TXT e gerará arquivos Excel correspondentes com o mesmo nome base

## Planilhas geradas

Para cada arquivo processado, o script gera um arquivo Excel com as seguintes planilhas:

1. **BASE**: Contém todos os dados processados do arquivo TXT original
2. **Base Calculo**: Tabela com os cálculos intermediários (horas totais, elevador, etc.)
3. **1_Disponibilidade Mecânica**: Percentual de tempo em que o equipamento esteve disponível
4. **2_Eficiência Energética**: Eficiência do uso de energia por operador
5. **3_Hora Elevador**: Horas de uso do elevador por operador
6. **4_Motor Ocioso**: Percentual de tempo com motor ligado parado, por operador
7. **5_Uso GPS**: Percentual de uso do sistema GPS, por operador
8. **Horas por Frota**: Contabilização do total de horas registradas e diferença para 24h
