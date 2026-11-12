# My Recon Beacon

**Inventário de sistemas, coleta de informações do host e organização de relatórios em Python.**

My Recon Beacon reúne componentes para consultar informações do computador, estruturar os resultados em JSON e estudar um fluxo de telemetria por HTTP. A organização do projeto separa a coleta, a coordenação dos ciclos, o transporte e o recebimento dos dados.

O repositório também contém uma implementação independente de relatório local, permitindo conhecer duas formas de organização do inventário: um coletor autônomo e uma arquitetura dividida em módulos.

## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias utilizadas](#tecnologias-utilizadas)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Arquitetura e componentes](#arquitetura-e-componentes)
- [Informações do inventário](#informações-do-inventário)
- [Requisitos](#requisitos)
- [Preparação do ambiente](#preparação-do-ambiente)
- [Organização dos relatórios](#organização-dos-relatórios)
- [Exemplo de dados](#exemplo-de-dados)
- [Ciclos e registros de execução](#ciclos-e-registros-de-execução)
- [Receptor de demonstração](#receptor-de-demonstração)
- [Dados sensíveis](#dados-sensíveis)
- [Publicação no GitHub](#publicação-no-github)
- [Contribuições](#contribuições)

## Sobre o projeto

A proposta é organizar informações de um host em uma estrutura que possa ser inspecionada, exportada e consumida por outros componentes. O código reúne consultas ao sistema operacional, ao hardware, às interfaces de rede, aos processos e aos discos.

A arquitetura possui duas entradas:

| Implementação | Arquivo principal | Organização |
| --- | --- | --- |
| Coletor modular | `main.py` | Coordenação dos ciclos com `Beacon`, coleta com `SystemCollector` e transmissão com `Transporter`. |
| Relatório local | `recon_beacon.py` | Implementação independente em `SystemRecon`, com método de exportação para JSON e exibição no terminal. |

O coletor modular também inclui rotinas de acesso a registros de credenciais de navegadores, descritas em [Dados sensíveis](#dados-sensíveis).

## Funcionalidades

- Consulta de identificação, versão e arquitetura do sistema operacional.
- Levantamento de interfaces e estatísticas de rede.
- Consulta de CPU, memória e utilização de discos.
- Listagem de processos ordenados pelo consumo de memória.
- Identificação do usuário e de informações do contexto de execução.
- Leitura de um conjunto definido de variáveis de ambiente.
- Inclusão de saídas de comandos do sistema nos relatórios.
- Organização dos resultados em dicionários e JSON.
- Método de exportação de relatório para arquivo local.
- Coordenação de coleta em ciclo único ou contínuo.
- Cálculo de hash SHA-256 do conteúdo coletado.
- Componente de envio de JSON por HTTP POST.
- Registro de eventos em arquivo e no terminal.
- Servidor HTTP de demonstração para recebimento de dados.

Cada funcionalidade pertence ao componente correspondente; a distribuição entre os dois coletores está descrita nas seções seguintes.

## Tecnologias utilizadas

| Tecnologia | Aplicação no projeto |
| --- | --- |
| Python 3 | Implementação dos coletores, do controlador e do receptor. |
| `psutil` | Consultas de CPU, memória, processos, rede e discos. |
| `requests` | Envio de requisições HTTP no transporte. |
| `platform`, `socket` e `getpass` | Identificação do sistema, do host e do usuário. |
| `subprocess` | Execução de comandos complementares de inventário. |
| `json` | Serialização, leitura e exportação dos relatórios. |
| `hashlib` | Cálculo de SHA-256. |
| `logging` | Registro de eventos e exceções. |
| `http.server` | Implementação do servidor de demonstração. |

## Estrutura do repositório

| Arquivo | Descrição |
| --- | --- |
| `main.py` | Entrada do fluxo modular e implementação da classe `Beacon`. |
| `collector.py` | Classe `SystemCollector` e rotinas de coleta de dados do host. |
| `transport.py` | Classe `Transporter` e comunicação HTTP. |
| `mock_server.py` | Classe `MockC2` e receptor HTTP de demonstração. |
| `recon_beacon.py` | Classe `SystemRecon` e implementação do relatório local. |
| `utils.py` | Funções auxiliares de hash, Base64 e diretório temporário. |
| `requirements.txt` | Dependências externas declaradas. |
| `README.md` | Documentação do projeto. |

Os arquivos `beacon.log` e `recon_report.json` são saídas de execução, associadas aos componentes que os produzem.

## Arquitetura e componentes

### `Beacon` — coordenação

Definida em `main.py`, a classe `Beacon` mantém as referências do coletor e do transporte, além das configurações de intervalo e de execução única.

Seu método `run_cycle()` organiza a coleta, a inclusão do hash no relatório, a chamada ao transporte e o registro do resultado. O método `start()` controla a repetição dos ciclos.

### `SystemCollector` — coleta modular

Definida em `collector.py`, a classe `SystemCollector` centraliza as consultas do fluxo modular. Seu método `collect()` monta um dicionário com metadados, informações do sistema e resultados das demais rotinas de coleta.

Os metadados incluem horário da coleta, identificador do host e uma versão interna do coletor. O identificador utiliza o hostname e, quando encontrado, um endereço IPv4 diferente de loopback.

### `Transporter` — envio HTTP

Definida em `transport.py`, a classe `Transporter` recebe o dicionário, serializa o conteúdo com `json.dumps()` e realiza uma requisição POST com `requests`.

O método `send()` retorna um resultado booleano para o controlador. A implementação considera HTTP `200` como sucesso de envio e registra os demais resultados ou exceções.

### `SystemRecon` — relatório local

Definida em `recon_beacon.py`, a classe `SystemRecon` contém uma implementação independente de inventário. A inicialização reúne os dados em `self.data`, e o método `export()` define a gravação do relatório em JSON e a impressão do conteúdo no terminal.

O nome padrão definido para a exportação é `recon_report.json`. O método também recebe um nome de arquivo como argumento. A escrita utiliza UTF-8, indentação de quatro espaços e substituição do conteúdo anterior quando o destino já existe.

### `MockC2` — recebimento de demonstração

Definida em `mock_server.py`, a classe `MockC2` estende `BaseHTTPRequestHandler`. Ela implementa o recebimento de POST, a leitura do corpo JSON e a apresentação de informações no terminal.

### Utilitários

| Função | Responsabilidade |
| --- | --- |
| `hash_payload()` | Calcula SHA-256 sobre a representação textual do dicionário recebido. |
| `obfuscate_string()` | Retorna a representação Base64 de uma string. |
| `get_temp_dir()` | Consulta as variáveis de diretório temporário e possui `/tmp` como alternativa. |

No fluxo principal, `hash_payload()` é chamado antes da inclusão do próprio hash em `meta.integrity_hash`.

## Informações do inventário

| Categoria | Informações organizadas |
| --- | --- |
| Sistema operacional | Sistema, versão, arquitetura, identificação do processador e versão do Python. |
| Identificação do host | Hostname, nome do nó e FQDN. |
| Rede | Interfaces, endereços, máscaras, estado, velocidade e contadores de tráfego. |
| CPU | Quantidade de núcleos, frequência disponível e percentual de utilização. |
| Memória | Capacidade total, memória disponível e percentual de uso. |
| Processos | PID, nome, usuário, consumo de memória e linha de comando. |
| Contexto de execução | Usuário atual e identificadores disponibilizados pelas APIs do sistema. |
| Ambiente | Variáveis selecionadas relacionadas a caminhos e configurações do ambiente. |
| Armazenamento | Dispositivos, pontos de montagem, capacidade e utilização. |
| Comandos complementares | Saídas textuais de comandos de identificação e inventário. |

O coletor modular mantém até 50 processos, e a implementação local mantém até 20, ordenados pelo consumo de memória. As saídas textuais dos comandos são armazenadas com até 2.000 caracteres por comando.

A implementação local também inclui informações de swap, tempo de CPU, horário de inicialização e contadores de pacotes. A disponibilidade dos valores acompanha as respostas das APIs e dos comandos do sistema consultado.

## Requisitos

- Python 3.
- `pip` para instalação de dependências.
- Módulo `venv` para organização do ambiente virtual.
- Acesso de leitura às informações do host utilizadas pelo inventário.
- Comandos do sistema correspondentes ao ambiente consultado.

Dependências declaradas em `requirements.txt`:

| Dependência | Versão |
| --- | --- |
| `psutil` | `>=5.9.0` |
| `requests` | `>=2.31.0` |

O código contém condições específicas para Windows e Linux. As rotinas complementares de navegadores utilizam outros módulos, incluindo uma importação dinâmica de `cryptography`.

## Preparação do ambiente

Extraia o projeto e abra um terminal na pasta que contém `requirements.txt`. Os comandos abaixo criam um ambiente virtual e instalam as dependências declaradas.

### Windows — PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se o comando `py` não estiver disponível, utilize `python` para criar o ambiente virtual.

### Linux

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

Os exemplos utilizam diretamente o interpretador do ambiente virtual, dispensando a ativação prévia do ambiente.

## Organização dos relatórios

Os dois coletores possuem estruturas próprias:

| Campo | Coletor modular — `SystemCollector` | Relatório local — `SystemRecon` |
| --- | --- | --- |
| Metadados | Objeto `meta` com `timestamp`, `beacon_id` e `script_version`. | Campo `timestamp` na raiz. |
| Sistema | `os` | `os` |
| Rede | `network` | `network` |
| Hardware | `hardware` | `hardware` |
| Processos | `processes` | `processes` |
| Contexto do usuário | `security` | `security` |
| Ambiente | `environment` | `environment` |
| Discos | `disk_usage` | `disk_usage` |
| Saídas de comandos | `raw_output` | `raw_system_output` |
| Registros de navegadores | `credentials` na raiz. | Fora da rotina de coleta desta classe. |
| Hash | Acrescentado pelo controlador em `meta.integrity_hash`. | Fora da estrutura definida por esta classe. |

A informação de versão em `meta.script_version` é um campo do coletor modular. Ela é independente da versão do Python consultada em `os`.

## Exemplo de dados

O exemplo abaixo é **fictício e simplificado**, com campos do inventário local:

```json
{
    "timestamp": "2026-11-12T12:00:00",
    "os": {
        "system": "Linux",
        "hostname": "host-exemplo"
    },
    "network": {
        "interfaces": {},
        "stats": {},
        "io_counters": {
            "bytes_sent": 0,
            "bytes_recv": 0
        }
    },
    "hardware": {
        "cpu": {
            "count": 4
        },
        "memory": {
            "total_bytes": 8589934592
        }
    },
    "processes": [],
    "security": {
        "current_user": "usuario-exemplo"
    },
    "environment": {},
    "disk_usage": [],
    "raw_system_output": {}
}
```

A estrutura completa é definida pelos métodos de cada coletor. Os exemplos publicados no repositório devem utilizar dados fictícios.

## Ciclos e registros de execução

O controlador modular organiza cada ciclo em quatro etapas:

1. Reunião dos dados pelo coletor.
2. Cálculo e inclusão do hash no relatório.
3. Encaminhamento do conteúdo ao transporte.
4. Registro do resultado da operação.

O intervalo padrão definido no controlador é de **300 segundos**, aguardado após o término de cada ciclo. A duração efetiva entre os inícios das coletas também inclui o tempo gasto nas operações.

O registro de execução utiliza o formato:

```text
horário [NÍVEL] mensagem
```

As mensagens são direcionadas ao terminal e ao arquivo `beacon.log`. Os registros incluem início de ciclo, resultado da coleta, retorno do transporte e exceções identificadas pelo controlador.

| Saída | Componente responsável | Conteúdo |
| --- | --- | --- |
| `beacon.log` | Logging de `main.py` | Eventos da execução modular. |
| `recon_report.json` | Método `SystemRecon.export()` | Conteúdo do inventário local quando a exportação é concluída. |
| Terminal | Componentes de execução e receptor | Mensagens de acompanhamento e informações apresentadas pelos módulos. |

Os nomes de arquivo relativos são resolvidos a partir do diretório de trabalho do processo.

## Receptor de demonstração

O servidor de `mock_server.py` possui endereço local definido como `127.0.0.1` e porta `8000`. Seu processamento de POST realiza a leitura do corpo, a interpretação do JSON e a apresentação de informações no terminal.

A apresentação utiliza os campos `os.hostname` e `security.current_user` para identificar o host e o usuário. O receptor também contém apresentação de campos de navegadores recebidos no corpo da requisição.

A resposta HTTP implementada utiliza status `200` e corpo `ACK`. O servidor funciona como um componente de demonstração do recebimento e da leitura de mensagens JSON.

## Dados sensíveis

O inventário pode reunir nomes de usuários, endereços de rede, caminhos e argumentos de processos. Esses dados devem ser tratados como informações do ambiente consultado.

Além do inventário, `SystemCollector` chama automaticamente rotinas de acesso a registros de credenciais de navegadores. Os resultados são incorporados ao campo `credentials` e integram o relatório encaminhado pelo fluxo modular. Dependendo dos registros e do processamento realizado, o conteúdo pode incluir endereços de sites, identificadores de login e senhas.

A implementação independente `SystemRecon` possui sua própria rotina de inventário e exportação local. Os exemplos destinados à documentação devem utilizar dados fictícios, sem conteúdo de perfis pessoais ou de ambientes de terceiros.

## Publicação no GitHub

Coloque este `README.md` na pasta principal do repositório, junto aos arquivos de código e ao `requirements.txt`. Assim, o GitHub apresenta a documentação na página inicial do projeto.

Para organizar os arquivos que serão versionados, uma sugestão de `.gitignore` é:

```gitignore
# Ambiente virtual
.venv/
venv/

# Cache e arquivos compilados do Python
__pycache__/
*.py[cod]

# Relatórios e registros locais
recon_report.json
beacon.log

# Configurações locais
.env
.env.*
!.env.example
```

As regras do `.gitignore` são aplicadas aos arquivos ainda não rastreados. Revise relatórios e exemplos de dados separadamente antes de adicioná-los ao repositório.

A licença de distribuição deve ser escolhida pelo responsável pelo projeto e registrada em um arquivo `LICENSE`, conforme os termos que desejar estabelecer.

## Contribuições

Contribuições podem abranger documentação, organização do inventário, clareza dos registros, padronização dos relatórios e tratamento de informações do sistema.

Ao propor uma alteração:

1. Descreva o objetivo e os componentes envolvidos.
2. Informe o sistema operacional e a versão do Python utilizados na avaliação.
3. Apresente exemplos com dados fictícios.
4. Atualize a documentação quando houver mudanças nos formatos ou no comportamento dos componentes.
