# Suporte para Arquivos transbordosMonit

Este projeto adiciona suporte para processamento de arquivos no formato "transbordosMonit" ao sistema existente de processamento de arquivos "transbordos".

## Funcionalidades Implementadas

1. **Detecção Automática**: O sistema detecta automaticamente os arquivos do tipo "transbordosMonit" por seu nome.

2. **Extração de ZIPs**: Ao extrair arquivos ZIP, o sistema reconhece os arquivos transbordosMonit e os prepara para processamento.

3. **Processamento Direto de ZIPs**: Para arquivos transbordosMonit*.zip que contêm CSVs, implementamos processamento específico que extrai e lê os CSVs diretamente, filtrando apenas as colunas desejadas.

4. **Conversão de Formato**: O sistema converte arquivos transbordosMonit para o formato padrão de transbordos, permitindo que eles sejam processados pelo fluxo existente.

5. **Mapeamento de Colunas**: Um mapeamento abrangente de colunas foi implementado para lidar com diferentes variações de nomes de colunas comuns em arquivos de monitoramento.

6. **Preservação de Dados**: Os dados essenciais do formato original são preservados, como o Operador, Equipamento, coordenadas e outros.

## Como Funciona

O processo segue estas etapas:

1. Ao detectar um arquivo com "transbordosMonit" ou "monit" no nome, o sistema o identifica como candidato para processamento especial.

2. Para arquivos ZIP:
   - Se o nome contiver "transbordosMonit" ou "monit", o sistema usa a função `processar_csv_transbordosmonit_zip` para extrair e processar os CSVs internos.
   - A função usa a lógica de leitura de CSV similar à implementada em `tempoManobras.py`, mas adaptada para manter apenas as colunas desejadas.
   - Os dados são convertidos para o formato padrão e então seguem o fluxo normal de processamento.

3. Para arquivos individuais:
   - A função `processar_arquivo_base` foi modificada para verificar se um arquivo é do tipo transbordosMonit.
   - Se for, o arquivo é processado usando lógica específica antes de continuar com o fluxo normal.

4. O restante do processamento (cálculos, geração de planilhas, etc.) permanece intacto, garantindo compatibilidade com o sistema existente.

## Mapeamento de Colunas

O sistema suporta várias nomenclaturas comuns para as colunas essenciais:

- **Equipamento**: EQUIPAMENTO, EQUIP, EQUIPMENT, EQUIPMENT_CODE, ID_EQUIPAMENTO
- **Data/Hora**: DATA, DATE, DT, HORA, HORARIO, TIME, HR
- **Coordenadas**: LATITUDE, LAT, LONGITUDE, LONG, LNG
- **Velocidade**: VELOCIDADE, VELOC, VEL, SPEED
- **RPM**: RPM, RPM_MOTOR, ROTACAO, ENGINE_RPM
- **Motor**: MOTOR, MOTOR_LIGADO, IGNIÇÃO, IGNIÇÃO_LIGADA, IGNITION, ENGINE_STATUS
- **Operação**: OPERACAO, OPERAÇÃO, GRUPO_OPERACAO, OPERATION, OPERATION_GROUP, OPERATION_TYPE
- **Operador**: OPERADOR, OPERATOR, DRIVER, MOTORISTA
- **Estado**: ESTADO, STATE
- **Estado Operacional**: ESTADO_OPERACIONAL, ESTADO OPERACIONAL, OPERATIONAL_STATE

## Testes

Foram implementados dois scripts de teste:

1. `teste_transbordosMonit.py`: Verifica o funcionamento da detecção e conversão de arquivos transbordosMonit individuais.
2. `teste_transbordosMonit_zip.py`: Testa o processamento específico de arquivos transbordosMonit ZIP com CSVs internos.

## Uso

O uso permanece o mesmo do sistema original. Os arquivos transbordosMonit são automaticamente detectados e processados, gerando os mesmos tipos de planilhas de resultado que o processamento de arquivos transbordos padrão.

```python
# Exemplo de uso
from scripts.transbordosMinOcioso import processar_arquivo

# Processar um arquivo transbordosMonit
processar_arquivo("caminho/para/arquivo_transbordosMonit.txt", "caminho/para/saida")

# Ou processar um ZIP contendo arquivos transbordosMonit
processar_arquivo("caminho/para/arquivoZIP_transbordosMonit.zip", "caminho/para/saida")
``` 