# Research — Especificação de implementação

**Versão da spec:** 1.2 · **Data:** 14/10/2026 · **Status:** revisada em pre-flight; pronta para M0/M1, com qualificação de hosts e eficácia científica ainda pendentes.

**Revisão 1.2:** resolve conflito entre journal de execução e checkout limpo; define aplicabilidade histórica/atual, precedência de estados, consistência de revisão, idempotência, integridade do núcleo e limites da liberação. Registra o resultado do pre-flight na seção 17.

**Revisão 1.1:** diferencia rascunho de adoção científica, permite revisão em lotes e define resolução autônoma antes de interromper o usuário. Acrescenta critérios de aceitação de UX.

**Baseline examinada:** `enniolopes/research`, plugin 0.11.0, commit `12220d50f1c02b9523a5186ce8d56567c8ed4d5a`.

## 1. Decisão arquitetural e objetivo

Evoluir o Research para um supervisor de decisões científicas, apoiado em referências explícitas, evidências versionadas e avaliações examináveis. O agente conduz investigação, programação e escrita de forma conversacional. Um núcleo determinístico verifica as condições necessárias para admitir execuções, resultados, decisões e versões de saída.

O objetivo mensurável é reduzir decisões indevidamente admitidas e retrabalho sem aumentar bloqueios de trabalho legítimo. Não se promete verdade científica, novidade, publicação ou impacto a partir de conformidade documental.

A arquitetura deve preservar três propriedades independentes:

1. **Legitimidade histórica:** compromissos prospectivos e exposição não podem ser reconstruídos retroativamente.
2. **Aplicabilidade atual:** um julgamento só vale para a formulação, evidência e critérios que examinou, enquanto suas condições continuarem aplicáveis.
3. **Qualidade do produto:** referências científicas e editoriais orientam desenho, contribuição e comunicação, sem autorizar extrapolação das evidências.

Os termos DEVE, NÃO DEVE e PODE expressam requisitos normativos desta spec. Campos JSON usam inglês; a interface responde na língua do projeto.

## 2. Escopo e fronteira de confiança

### 2.1 Incluído

- Contratos versionados de referências e avaliações materiais.
- Supervisor com propostas de ação, obrigações e disposições explícitas.
- Admissão de resultados produzidos por execuções identificadas.
- Revisão independente vinculada à versão examinada.
- Grafo derivado de dependências, com vias conjuntas e alternativas quando declaradas.
- Reavaliação localizada, retomada após interrupção e gate de liberação.
- Adaptadores de host com capacidades demonstradas por testes.
- Experimento de ablação para decidir quais mecanismos merecem permanecer.

### 2.2 Fora do escopo inicial

- Ontologia científica universal, pontuação única de verdade ou qualidade.
- Treinamento do modelo, GraphRAG, base vetorial ou banco de grafos obrigatório.
- Provar identificação causal, validade de construto ou completude da revisão por parser.
- Isolamento de rede/modelo/processo que o backend não consiga demonstrar.
- Submissão automática a revistas ou outras ações externas de publicação.

### 2.3 Modelo de confiança

O agente, seus relatos de sucesso e as relações que propõe são entradas não confiáveis para admissão automática. O núcleo confia apenas em verificações cuja base é inspecionável; julgamentos científicos continuam falíveis e identificados como julgamentos.

Arquivos e commits não provam ausência de exposição externa, veracidade de um relato humano ou fidelidade de uma extração de fonte. Um digest prova correspondência de bytes, não suporte semântico. Um parecer registrado prova que aquele parecer existe, não que o revisor está correto ou é independente em expertise.

V1 assume um checkout local com um escritor cooperante por vez. Não oferece contenção adversarial contra outro processo que altere arquivos, Git ou logs fora do supervisor. Nessa situação, as garantias precisam ser reduzidas e o host pode exigir um ambiente isolado.

## 3. Componentes e responsabilidades

| Componente | Responsabilidade | Limite |
|---|---|---|
| References | Critérios de integridade, projeto, qualidade, estilo e alvo editorial | Não fornece a conclusão desejada como critério de validade |
| Observer | Identifica eventos e versões efetivamente observados | Não infere exposição ausente nem acredita em relato do agente sem qualificação |
| Evaluator | Executa checks ou reúne evidência e julgamento delimitado | Não transforma extração ou opinião em prova científica |
| Supervisor | Resolve obrigações e admite/restringe ações | Não escolhe conclusões científicas por score |
| Memory/projection | Preserva registros e deriva estado, dependências e pendências | Projeções são reconstruíveis e não autoritativas |
| Host adapter | Intercepta ações, executa comandos ou oferece orientação | Garante somente as fronteiras efetivamente controladas |

A operação normal é: intenção do usuário → proposta do agente → obrigações aplicáveis → verificação/avaliação → execução ou registro admitido → eventos observados → atualização da projeção.

A proposta de ação nunca equivale a sua autorização. A execução nunca equivale à aceitação científica do resultado.

## 4. Fontes de verdade e armazenamento

### 4.1 Artefatos mantidos

`protocol.md`, `analysis-plan.md`, `decisions.md`, `RESEARCH.map`, resultados, manuscritos e os registros atuais de RUN, EXEC e ASMT continuam autoritativos em seus âmbitos. Recibos antigos não serão reescritos para satisfazer novos campos.

### 4.2 Novos contratos mínimos

| Caminho | Conteúdo | Política |
|---|---|---|
| `.research/references/REF-<n>.json` | Conjunto versionado de critérios do projeto | Novo ID para alterações |
| `.research/decisions/DEC-<n>.json` | Decisão científica material e base | Append-only após primeiro commit |
| `.research/reviews/REVIEW-<n>.json` | Manifesto estruturado do parecer | Acompanha o Markdown existente; novo ID para revisão |
| `.research/events/EVT-<uuid>.json` | Acontecimentos materiais observados ou declarados | Append-only após primeiro commit |
| `.research/releases/REL-<n>.json` | Pacote exato admitido para liberação | Não executa publicação externa |

Eventos instrumentados em curso são primeiro escritos no journal operacional definido na seção 11, fora da árvore versionada. São importados para `.research/events/` após a fronteira de execução e com a origem preservada. Journal, locks e propostas temporárias não são dependências científicas nem entram no diff execution_freeze → run commit.

Os novos arquivos são introduzidos porque possuem contratos verificáveis distintos. Não devem repetir a íntegra de planos, resultados ou manuscritos. `DEC` é o índice verificável da decisão; o argumento extenso permanece no artefato indicado por `rationale_ref`. `REVIEW.md` é o parecer humano-legível; seu manifesto associa cobertura, achados e versões.

JSON é a representação autoritativa dos novos contratos. SQLite é permitido apenas como índice reconstruível; a implementação inicial usa arquivos e projeção em memória. Cada novo registro inclui `schema_version`. Campos desconhecidos fora de `extensions` devem falhar; `extensions` nunca confere autoridade automática.

Append-only inclui proibição de apagar ou renomear registros comprometidos para esconder seu conteúdo. A validação compara também os caminhos/IDs anteriormente adicionados no histórico alcançável, não apenas arquivos ainda presentes no checkout. Retirada e supersession são novos registros, não exclusões. Mudança de histórico que remova a âncora local anteriormente verificada retorna RECOVER; inspeção histórica read-only continua possível. Um clone novo sem âncora não prova que jamais houve história externa ou reescrita.

### 4.3 Identidade de recursos

Cada dependência inclui projeto, ID lógico, caminho/locator, revisão e fingerprint. Um ID lógico isolado, como T1, NÃO DEVE fundir testes de congelamentos diferentes. A chave de projeção é `(project_id, kind, logical_id, revision)`.

Para arquivo local, a revisão é commit Git e o fingerprint é SHA-256 dos bytes. A identidade versionada permanece histórica; sua aplicabilidade à decisão depende do vínculo declarado abaixo. Locators dentro de arquivos não removem a dependência da versão completa em V1. Referências externas precisam de snapshot inspecionado, origem, locator e data de recuperação; URL ou DOI sozinho não permite verificar conteúdo atual.

Recursos não disponíveis recebem `NOT_VERIFIED`; não são tratados como inalterados. Para dados restritos, registrar identidade, controles e a limitação efetivamente verificável, sem forçar cópia proibida ou fingir acesso.

`project_id` é UUID persistido em `.research/project.json`, com `schema_version: project@1`, `project_id` e `created_at` UTC. Clones do mesmo projeto preservam o UUID; projetos distintos não reutilizam IDs por conveniência. Configuração de adapter e locks não é fonte de autoridade científica.

### 4.4 Contrato comum de recurso

Um `resources` é um objeto cujas chaves são IDs locais únicos RES. Cada valor contém `kind`, `logical_id`, `path`, `revision`, `sha256` e, quando pertinente, `locator` e `origin_refs`. `path` deve ser relativo à raiz, sem traversal nem symlink que escape do projeto. `revision` é commit Git completo de 40 ou 64 caracteres hexadecimais conforme formato do repositório; `sha256` tem 64 caracteres hexadecimais minúsculos. O validador verifica os bytes naquela revisão, não apenas o formato do hash.

`resources` usa essa mesma forma de objeto em DEC, REVIEW e REL; não alterna entre lista e mapa. IDs RES têm escopo no manifesto. Referência entre manifestos usa `{record_id, resource_id}`; referência local usa o ID RES. Ambos são resolvidos para a chave versionada da seção 4.3.

Referências externas são primeiro snapshots locais inspecionados; um recurso de fonte acrescenta `source_uri`, `retrieved_at` e a limitação de acesso. O supervisor não baixa nem substitui uma fonte ao resolver recurso silenciosamente.

Propostas podem usar objetos ResourceRef temporários. DEC, REVIEW e REL admitidos devem persistir sua resolução completa: o objeto normalizado é copiado para `resources` ou apontado por referência explícita a outro manifesto comprometido e imutável. IDs RES nunca dependem apenas de um arquivo temporário de proposta. Metadados de origem não autorizam somar suportes como independentes.

Exceção tipada para recurso externo restrito: `kind: restricted_external`, `logical_id`, `source_uri`, `version_label`, `availability: restricted` e `access_attestation_ref`. Campos locais path/revision/sha256 não são fabricados. A atestação aponta para evidência do acesso efetivo e limitações; a verificação de bytes indisponíveis retorna NOT_VERIFIED. Esse recurso não pode satisfazer uma obrigação mecânica de input local do runner. Não autoriza confirmação por mera declaração de existência.

### 4.5 Vínculos de aplicabilidade

Cada relação de dependência da decisão/revisão contém `resource_ref` e `binding`:

- `pinned`: refere-se exatamente à versão histórica e ao âmbito declarado. Verifica existência, fingerprint, retirada e disponibilidade daquela base; alteração do arquivo atual não a torna stale por si.
- `follow_current`: acrescenta `current_path` ou referência explícita ao registro vigente. Mudança relevante nos bytes/formulação/critério atuais torna a avaliação stale até novo exame. Igualdade do HEAD inteiro não é necessária.
- `external_refresh`: snapshot histórico com `refresh_rule` e prazo/data ou evento de atualização definido no critério. Quando a atualização é exigida e não está disponível, retorna NOT_VERIFIED até nova inspeção, preservando a validade histórica limitada do snapshot.

`resource_ref` resolve conforme 4.4. Em `routes[].all_of`, os membros tornam-se objetos de vínculo; o template DEC abaixo ilustra essa forma. Projeção não atribui binding por conveniência; vínculos ausentes em contratos novos falham schema.

Texto alvo de uma claim atual utiliza follow_current para detectar reformulação; resultados e planos congelados normalmente usam pinned. Uma conclusão sobre uma amostra histórica pode conservar a base antiga depois de novos dados. Uma conclusão sobre a população/período atual precisa declarar as condições de atualização e não pode reutilizar pinned para fingir atualidade. O âmbito é examinado na revisão.

## 5. Referências e contrato de qualidade

### 5.1 Classes

| Classe | Exemplos | Uso |
|---|---|---|
| Integrity | ordem dos compromissos, distinção descoberta/confirmação, proveniência | Requisito de admissão aplicável |
| Scientific | suficiência do desenho, contribuição, análise de alternativas | Julgamento científico delimitado |
| Editorial | escopo, requisitos de reporte e estrutura da revista | Critério de liberação para alvo declarado |
| Exemplars | papers de referência e características transferíveis | Orientação e comparação crítica |
| Style | clareza, precisão, densidade e convenções do público | Orientação; bloqueio apenas se explicitamente exigido |

Requisitos externos devem ser recuperados e inspecionados no nível utilizado. O contrato registra sua validade temporal e quando exige atualização. Objetivos como alto impacto são traduzidos em critérios examináveis de relevância e contribuição; citações futuras ou aceitação editorial não são invariantes controláveis.

### 5.2 Schema REF v1

Campos obrigatórios: `schema_version`, `id`, `project_id`, `supersedes` (ID ou null), `criteria` e `authority`. Cada critério tem ID único, classe, texto, ação de aplicação, materialidade, método de verificação e origem. Critérios auxiliares não podem elevar uma proposta a conclusão. Critérios desconhecidos ou ausência de método não podem passar silenciosamente.

```json
{
  "schema_version": "references@1",
  "id": "REF-1",
  "project_id": "00000000-0000-4000-8000-000000000001",
  "supersedes": null,
  "criteria": [
    {
      "id": "QC-1",
      "class": "scientific",
      "text": "A formulação deve permanecer dentro do desenho e da população examinados.",
      "applies_to": ["ADOPT_CLAIM", "RELEASE"],
      "materiality": "required",
      "verification": "independent_review",
      "source": {"kind": "project_decision", "ref": "decisions.md#d-1"}
    }
  ],
  "authority": {"kind": "human", "identity": "project-owner"}
}
```

`materiality`: `required | advisory`. `verification`: `mechanical | bounded_assessment | independent_review | human`. A bounded ASMT auxilia julgamento; nunca satisfaz sozinho uma obrigação de revisão independente. A autoria humana do contrato deve ser efetivamente atestada pelo fluxo de interação; uma string escrita pelo agente não demonstra aprovação.

Mudança editorial cria novo REF e reavalia obrigações afetadas. Mudança científica que redefine compromissos confirmatórios segue REOPEN e novos congelamentos; trocar REF não apaga exposição.

### 5.3 Integridade não configurável por REF

As invariantes mínimas da versão do núcleo são registradas como CORE-* no código e nos schemas: ordem prospectiva, proveniência, distinção exploração/confirmação, teste primário para decidir H, identidade/versionamento e cobertura de revisão exigida para liberação material. REF pode acrescentar exigências e orientar qualidade; não pode apagar, tornar advisory ou dispensar CORE-*.

Cada avaliação/admissão registra `core_version` e fingerprint da configuração determinística de regras. Uma obrigação tem origem `core | reference`; duplicatas são resolvidas sem enfraquecer a origem core. Mudança de núcleo pode tornar admissão anterior histórica ou exigir reavaliação conforme migração explícita; nunca faz conformidade mais forte surgir retroativamente.

Decisões do usuário já registradas podem fundamentar authority sem reconfirmação. O vínculo deve apontar para a interação/atestado efetivamente observado. IDs como project-owner e strings human não criam autoridade por si.

## 6. Eventos, estado e observabilidade

### 6.1 Eventos materiais

Tipos iniciais: `COMMITMENT_RECORDED`, `EXECUTION_STARTED`, `EXECUTION_COMPLETED`, `EXPOSURE_RECORDED`, `RESULT_ADMITTED`, `DECISION_RECORDED`, `REVIEW_RECORDED`, `DEPENDENCY_CHANGED`, `REOPEN_RECORDED`, `RELEASE_ADMITTED`.

Schema EVT v1: ID UUID, projeto, tipo, sujeito, referências de recursos, `observation` (`instrumented | human_attested | agent_reported`), origem, timestamp UTC e sequência atribuída pelo supervisor. A sequência ordena os eventos locais cooperantes; Git fornece ordem dos registros comprometidos. Timestamp não prova ordem histórica externa.

Eventos finais de admissão (`RESULT_ADMITTED`, `DECISION_RECORDED`, `RELEASE_ADMITTED`) incluem operation_id e `members`, com IDs/caminhos/digests dos registros admitidos. O próprio EVT não aparece em members, evitando digest autorreferente. Eventos meramente declarados não são convertidos nesses marcadores pelo agente. No modelo cooperante, o supervisor verifica origem local e consistência com journal; contra edição adversarial seria necessária outra fronteira de execução/atestação, fora de V1.

Eventos instrumentados vêm do adapter/runner, não de JSON proposto livremente pelo agente. Eventos relatados pelo agente não podem satisfazer obrigação mecânica que exige execução observada. Declarações de exposição externa entram como fatos declarados com sua incerteza; ausência de evento não prova ausência de exposição.

Exposição deve registrar sujeito, dados/resultados acessados e fronteira de observação. Uma rota confirmatória controlada verifica compromissos antes de iniciar a execução e disponibilizar resultados. Falha posterior não apaga a exposição já ocorrida.

### 6.2 Dois eixos de estado

Os estados científicos atuais, como CONFIRMED e INCONCLUSIVE, são mantidos. O supervisor introduz um eixo operacional distinto para registros materiais:

`CANDIDATE | CURRENT | STALE | WITHDRAWN | SUPERSEDED | NOT_VERIFIED`.

- CURRENT: as obrigações aplicáveis foram satisfeitas sob os limites registrados.
- STALE: uma condição relevante mudou; exige reavaliação, não prova falsidade.
- WITHDRAWN: retirada explícita por nova decisão, preservando o registro anterior.
- SUPERSEDED: há substituição identificada, sem apagar a interpretação histórica.
- NOT_VERIFIED: uma obrigação material não pôde ser examinada.

Esses estados são derivados. CURRENT nunca significa verdade universal. Um julgamento retirado ou invalidado explicitamente não volta a CURRENT apenas porque bytes anteriores foram restaurados; requer nova decisão. Reabrir legitimamente a pesquisa não reclassifica o uso histórico de dados.

Derivação V1, em ordem: retirada explícita válida → WITHDRAWN; substituição explicitamente aceita → SUPERSEDED; ausência de admissão consolidada → CANDIDATE; vínculo follow_current alterado ou julgamento explicitamente invalidado → STALE; obrigação material indisponível → NOT_VERIFIED; demais condições satisfeitas → CURRENT. Todos os diagnósticos continuam registrados mesmo quando só um estado principal é exibido. Conflito entre decisões vigentes sem relação explícita de supersession retorna RECOVER, sem escolher por timestamp ou nome do arquivo.

Supersession de núcleo ou REF não invalida automaticamente toda decisão histórica; aplica-se à ação e ao vínculo relevante. Consultas históricas reconstruem o estado no commit solicitado. Estados científicos derivados de decisões só são reconciliados com RESEARCH.map após admissão consolidada; o mapa editado manualmente não prevalece sobre a base examinável.

## 7. Decisões e justificações

### 7.1 Schema DEC v1

Campos obrigatórios: `schema_version`, `id`, `project_id`, `action`, `target`, `references`, `resources`, `basis`, `judgments`, `rationale_ref`, `disposition`, `limits`, `supersedes` e `revision_conditions`.

`target` aponta para texto exato e recurso versionado, com `binding` e `current_path` quando follow_current. `basis` contém recursos e vias de suporte declaradas. `judgments` aponta para checks e avaliações aplicáveis. `disposition`: `adopt | narrow | retain | withdraw | defer | reopen`. DEC só é aceito por admissão apropriada; criar arquivo DEC não muda sozinho estado científico. DEC, REVIEW e REL incluem também `core_version` e `rules_sha256`, definidos em 5.3; exemplos com placeholders precisam ser preenchidos antes de admissão.

```json
{
  "schema_version": "decision@1",
  "id": "DEC-1",
  "project_id": "00000000-0000-4000-8000-000000000001",
  "action": "ADOPT_CLAIM",
  "core_version": "supervisor@1",
  "rules_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "target": {
    "kind": "claim",
    "id": "C1",
    "text": "Na população observada, a medida X esteve associada a Y.",
    "resource_ref": "RES-PAPER-1",
    "binding": "follow_current",
    "current_path": "documents/paper.md"
  },
  "references": ["REF-1#QC-1"],
  "resources": {},
  "basis": {
    "routes": [
      {
        "id": "J1",
        "all_of": [
          {"resource_ref": "RES-R1-1", "binding": "pinned"},
          {"resource_ref": "RES-PLAN-1", "binding": "pinned"},
          {"resource_ref": "RES-CHECK-K1-1", "binding": "pinned"}
        ]
      }
    ],
    "origin_refs": ["DATA1@freeze-1"]
  },
  "judgments": ["REVIEW-1#C1"],
  "rationale_ref": "documents/paper.md#interpretation-c1",
  "disposition": "adopt",
  "limits": ["A associação não estabelece o mecanismo causal."],
  "supersedes": null,
  "revision_conditions": ["Mudança em recurso de J1 ou na formulação de C1."]
}
```

Os IDs RES acima são ilustrativos e o `resources` vazio torna este exemplo um template não admissível. Eles precisam resolver em recursos persistidos, com fingerprints reais, diretamente ou via referência explícita ao manifesto de revisão. `freeze-1` não é um commit válido: implementações devem resolver o exemplo para commits reais antes de admiti-lo. Exemplos desta spec não são fixtures que deveriam passar os gates sem preenchimento.

### 7.2 Semântica do suporte

Dentro de `all_of`, todas as dependências são exigidas. Vias distintas são alternativas declaradas, não votos e não evidência estatisticamente independente por definição. Origem compartilhada deve permanecer explícita.

V1 não deduz validade científica por álgebra. Uma via é aplicável somente se seus recursos, condições e avaliação correspondente permanecem válidos sob seus bindings. Mudança relevante conforme 4.5 produz STALE ou NOT_VERIFIED e encaminha reavaliação. Outra via sobrevivente permite propor RETAIN ou NARROW; não restaura a conclusão automaticamente. O argumento precisa mostrar qual formulação cada via sustenta.

Uma conclusão que decide H continua vinculada ao teste primário prospectivo. Vias alternativas não permitem substituir o teste primário por sensibilidade, diagnóstico ou especificação favorável. Duplicar DATA ou reutilizar o mesmo conteúdo sob outro ID não cria independência.

### 7.3 Reabertura e descoberta

Ideias novas entram livremente como candidatas. O supervisor não exige que toda frase ou hipótese tenha DEC. Exige registro quando uma escolha muda um compromisso, uma interpretação material ou uma saída científica.

Escrever, editar, comparar ou apresentar uma formulação em um rascunho identificado NÃO É ADOPT_CLAIM. Candidatos podem permanecer no manuscrito de trabalho enquanto a revisão está pendente. O estado de rascunho deve ser claro no nível do documento/resposta, sem avisos repetidos em cada frase; ele não pode ser apresentado como conclusão científica admitida. Observações computadas podem ser reportadas com sua proveniência e alcance, separadas da interpretação candidata. Uso de uma interpretação para decidir H, apoiar outra decisão material como estabelecida ou integrar versão liberada exige a admissão correspondente.

Revisões de claims independentes podem ser agrupadas em um mesmo REVIEW quando compartilham snapshot e momento de avaliação; cada claim mantém julgamento e dependências próprios. A revisão pode ocorrer em marcos naturais da investigação, antes da adoção material, sem exigir uma invocação por parágrafo. Essa flexibilidade não posterga controles pré-exposição de execução confirmatória.

Uma ideia resultante de exposição é registrada como descoberta. Pode gerar código e investigação exploratória, restringir uma conclusão ou motivar nova confirmação com base legítima. A ausência de regra prévia para evidência inesperada encaminha avaliação ou REOPEN; não provoca bloqueio global nem autorização confirmatória retroativa.

## 8. Avaliação e revisão independente

### 8.1 Pipeline

1. Identificar recursos exatos e preservar evidência acessível.
2. Definir o critério e sua autoridade.
3. Extrair material relevante com locators e limites de cobertura.
4. Julgar a relação, mantendo evidência e julgamento separados.
5. Registrar achados, disposição e obrigações restantes.

Na revisão, presença do trecho e fingerprint podem ser conferidas mecanicamente. A suficiência da extração e a adequação da inferência continuam semânticas. Perguntas independentes devem ser avaliadas separadamente antes de sua integração, evitando que uma primeira resposta determine artificialmente as seguintes.

### 8.2 Manifesto REVIEW v1

Obrigatórios: `schema_version`, `id`, `project_id`, `reviewed_commit`, `resources`, `reference_set`, `report`, `coverage`, `claims`, `findings`, `checks`, `reviewer`, `verdict`.

- `resources`: objeto fechado de recursos conforme 4.4; inclui vínculos declarados em `dependencies`, campo obrigatório do REVIEW conforme 4.5.
- `report`: path e fingerprint do REVIEW Markdown. Sua revisão é o primeiro commit que contém esse parecer e manifesto; não tentar incluir o hash desse próprio commit dentro do conteúdo ainda a comprometer.
- `coverage`: documentos examinados, afirmações inventariadas, áreas não examinadas e limitações. O revisor deve inspecionar também possíveis afirmações materiais sem anotação.
- `claims`: C ID, texto exato, critérios, evidências, vias examinadas, resultado `adequate | inadequate | insufficient` e limites de formulação.
- `findings`: F ID, materialidade `material | nonmaterial`, alvo, motivo, ação mínima e disposição inicial `open | resolved | deferred`; resolved exige referência a avaliação de resolução apropriada. Atualizações são novos registros.
- `checks`: comandos efetivamente executados e seus resultados identificados.
- `reviewer`: backend, identidade/modelo, procedimento e atestação do adapter sobre contexto separado quando observável.
- `verdict`: `PASS | FAIL | NOT_VERIFIED`, consistente com achados e cobertura.

FAIL exige inadequação material demonstrada ou achado material ainda não resolvido que demonstra erro. NOT_VERIFIED exige claim required com resultado insufficient, cobertura material insuficiente ou impossibilidade de demonstrar separação exigida. PASS exige adequação das claims required cobertas, nenhuma obrigação material não resolvida e nenhuma lacuna de cobertura material. Parser rejeita manifesto cujo verdict contradiga seus próprios claims/findings; não infere completude científica apenas dessa consistência.

Separação do revisor é uma obrigação específica: `reviewer.separation` registra `host_attested | external_reviewer_attested | not_verified` e aponta para o evento/atestado de origem. Trocar o nome/modelo do revisor ou adicionar esse campo manualmente não demonstra separação. Host sem atestação pode utilizar revisor humano/externo com origem registrada; sem evidência disponível a obrigação permanece NOT_VERIFIED.

O manifesto aponta para commits anteriores que contêm a base examinada. Não inclui a própria revisão, o DEC que depende dela ou o REL futuro como dependências científicas; isso evita ciclos. A revisão é comprometida depois do snapshot examinado. Para novas claims, o texto candidato é versionado antes da revisão.

Respostas aos achados são novos registros, não edição silenciosa do parecer. Um rebuttal é um julgamento a examinar; o agente não pode marcar o próprio erro como resolvido apenas por ter escrito uma resposta. Achado material requer avaliação da resolução por revisor adequado/contexto separado ou autoridade humana declarada.

Para mudança apenas no manifesto, sem mudança no conteúdo revisado, o parser verifica consistência; não atribui nova cobertura científica. Alteração de formulação, critério ou recurso relevante exige novo parecer/decisão.

Cobertura declarada é obrigatória, mas não prova cobertura completa. Detectar claims omitidas é tarefa explícita do revisor e do benchmark. Sem evidência suficiente de cobertura, o resultado é NOT_VERIFIED.

ASMT continua auxiliar e imutável. Um ASMT SUPPORTS não substitui REVIEW nem altera H.

## 9. Supervisor e contratos de ações

### 9.1 Proposta e saída

Uma proposta contém `schema_version: action@1`, `operation_id` UUID, projeto, ação, alvo, `base_commit`, fingerprints dos vínculos atuais, core_version/rules_sha256 e recursos. Ela é temporária; só tentativas materiais e acontecimentos relevantes viram registros duráveis.

O mesmo operation_id com payload canonicamente idêntico é idempotente: devolve resultado registrado ou RECOVER se a tentativa está incompleta; não repete execução, não aloca novo R e não duplica DEC. Mesmo ID com payload diferente falha contrato. A canonicalização JSON usa UTF-8, chaves ordenadas, separadores fixos, sem NaN/Infinity nem chaves duplicadas; exclui apenas campos de transporte fora do payload científico.

A saída do supervisor contém `disposition`, `obligations`, `verified_basis`, `allowed_routes` e `capability_limits`. Disposições: `ALLOW | REQUIRE_EVIDENCE | REQUIRE_JUDGMENT | BLOCK | RECOVER`. Cada obrigação possui ID estável, alvo, materialidade, método, resultado e base versionada.

Precedência de resposta: contrato inválido → erro de contrato; estado inconsistente/tentativa interrompida → RECOVER; obrigação required com FAIL → BLOCK; prova mecânica required ausente → REQUIRE_EVIDENCE; julgamento/autoridade required ausente → REQUIRE_JUDGMENT; demais condições → ALLOW. Se faltarem evidência e julgamento, retornar ambos nos diagnósticos e priorizar a coleta necessária ao julgamento. ALLOW de propose não é admissão nem autorização reutilizável depois de mudança no snapshot.

Exemplo de resposta a um plano não congelado:

```json
{
  "disposition": "REQUIRE_EVIDENCE",
  "effect": "checked",
  "obligations": [
    {"id": "FIT-PLAN-FREEZE", "target": "H1", "status": "NOT_VERIFIED", "materiality": "required"}
  ],
  "verified_basis": [],
  "allowed_routes": ["PREPARE_COMMITMENT", "EXPLORE_WITH_DISCLOSURE"],
  "capability_limits": ["Exposição fora do runner não é observada."]
}
```

### 9.2 Contratos iniciais

| Ação | Pré-condições | Pós-condições/admissão |
|---|---|---|
| FIT_CONFIRMATORY | plano/estimand/teste primário, condições/checks/falhas, freezes, exposição compatível e backend declarado | execução identificada; somente saídas declaradas na fronteira observável; registro sem autoridade científica automática |
| ADMIT_RESULT | RUN válido, artefato correspondente e verificações aplicáveis | R pode ser usado como resultado identificado; não decide H por si |
| CHANGE_COMMITMENT | compromisso e exposição anteriores recuperados; rota identificada | SPECIFICATION, EXPLORATORY, DEFERRED ou REOPEN durável sob contratos existentes |
| ADOPT_CLAIM | resultado/fonte identificado; desenho, checks e critérios examinados; REVIEW adequado quando material | DEC ligado à formulação e base; estado operacional derivado |
| REVISE_DECISION | evidência/condição alterada e consequências candidatas recuperadas | nova decisão com suporte sobrevivente, limitações e reavaliação necessária |
| RELEASE | pacote exato, inventário material, decisões/revisões atuais e obrigações do alvo satisfeitas ou legitimamente dispostas | REL identifica os bytes admitidos; não executa envio externo |

Critério advisory não bloqueia. Critério required com FAIL bloqueia a ação afetada. Material NOT_VERIFIED requer resolução ou disposição por autoridade explicitamente competente, com divulgação adequada; não pode ser apagado por um PASS agregado. Dispensa externa não pode sobrescrever proveniência inválida nem converter análise exploratória em confirmação.

O supervisor aplica regras determinísticas pequenas, sem síntese automática de um autômato científico universal em V1. Combina obrigações por ação/alvo e evita regras conflitantes. Conflito de critérios produz REQUIRE_JUDGMENT; não escolhe silenciosamente o critério mais conveniente.

### 9.3 Progresso e recuperação

Cada restrição retorna a obrigação mínima faltante e ao menos uma rota legítima quando conhecida. Trabalho independente pode prosseguir. Bloqueio de confirmação não implica bloqueio de exploração.

Após duas tentativas idênticas sem nova evidência nem alteração relevante, parar a repetição daquela ação. Pedir uma decisão ao usuário apenas se faltar autoridade humana ou uma ambiguidade material não puder ser resolvida com o contexto; nos demais casos, diferir a ação, seguir outra rota legítima ou concluir com a limitação identificada. O limite evita loops; não decide mérito científico e não cria por si uma obrigação de confirmação.

Orientação contextual usa o estado atual e a obrigação relevante. Não reinjeta toda a constituição em cada ação. Experiência de falhas pode sugerir melhorias no procedimento, mas não altera invariantes/compromissos automaticamente; mudanças seguem nova versão e avaliação.

### 9.4 Manifesto de liberação REL v1

Obrigatórios: `schema_version: release@1`, `id`, `project_id`, `snapshot_commit`, `target`, `resources`, `claim_inventory`, `decision_refs`, `review_refs`, `obligations`, `authority_refs` e `created_at`. `target` identifica tipo de saída, destino pretendido e REF editorial aplicável. `claim_inventory` associa cada claim material à formulação/locator exatos e suas decisões/revisões. Claims extraídas automaticamente são candidatas ao inventário até a revisão de cobertura.

`resources` fecha o pacote de arquivos destinado à saída, com fingerprints; nenhum arquivo não inventariado pode ser enviado sob aquela admissão. O manifesto REL permanece fora do conjunto que calcula seu próprio fingerprint, evitando autorreferência. A versão de saída pode carregar o manifesto como metadado acompanhante. Cada recurso local resolve num commit existente antes da criação do REL; `snapshot_commit` pode ser igual ao snapshot já examinado mesmo se pareceres e DEC foram comprometidos depois. Os manifests de evidência entram como metadados referenciados, não como condição que obriga o parecer a depender do próprio REL.

Quando o produto final é PDF, figuras ou outro render, inventariar os bytes finais e seus arquivos-fonte/receita. Verificação de render e correspondência com o material revisado é obrigação do produto efetivo, não inferida apenas do Markdown. Se o parecer cobriu só o fonte e a transformação pode alterar conteúdo científico ou omitir material, exigir inspeção da saída final. A base examinada pode ser um commit anterior contendo render e fontes; REVIEW/DEC/REL são adicionados posteriormente sem recriar o render.

`obligations` preserva cada resultado required/advisory, sua base e qualquer disposição autorizada de NOT_VERIFIED. `authority_refs` registra decisões humanas de alvo, autoria, ética e divulgação quando aplicáveis, sem deduzi-las de identidade textual. Se o alvo exige decisão inexistente, retornar REQUIRE_JUDGMENT.

RELEASE verifica o fechamento das decisões e revisões do inventário, rejeita dependências quebradas/stale e confere o pacote novamente no momento de exportação. `research release inspect` é read-only. O dispatcher de RELEASE pode preparar um pacote local admitido; transmissão externa permanece uma ação separada, autorizada e vinculada aos mesmos bytes. Uma aprovação ou requisito externo não examinado continua NOT_VERIFIED, e sua materialidade é julgada sob o contrato do alvo.

`validate --strict` exige todos os checks selecionados verificados; não possui dispensa semântica. A admissão RELEASE avalia as disposições autorizadas sob seu contrato separadamente e jamais altera o resultado original do check.

## 10. Grafo derivado e reavaliação

Nós iniciais: recurso versionado, H/E/T versionados, RUN/R, C, DEC, REVIEW, REF/critério, via de suporte e obrigação. ASMT e EXEC são nós auxiliares quando referenciados. Relações representam fatos declarados: produced_by, examined_by, requires, alternative_route, proposed_support, supersedes e shared_origin.

Usar `proposed_support`/`examined_support`, evitando uma aresta genérica supports que pareça provar semântica. Uma justificação é um nó com dependências conjuntas; alternativas são explicitamente agrupadas. A navegação preserva commits dos planos históricos em vez de fundi-los com o plano atual.

Algoritmo V1:

1. Resolver IDs e versões; referências quebradas viram obrigações, não arestas inventadas.
2. Verificar fingerprints históricos e detectar mudanças de aplicabilidade por binding, critério, formulação, disposição ou disponibilidade.
3. Percorrer dependências registradas para reunir candidatos afetados.
4. Derivar STALE/NOT_VERIFIED somente quando a alteração afeta o vínculo aplicável; encaminhar reavaliação e manter consultas históricas distintas.
5. Inspecionar suporte restante e registrar nova disposição, sem retirada automática por reachability.
6. Revalidar somente o fechamento afetado, salvo validação completa no gate de liberação.

V1 limita ciclos de dependência justificatória: referências científicas cíclicas devem falhar com diagnóstico ou permanecer NOT_VERIFIED. Relações de supersession devem ser acíclicas. Não enumerar todas as combinações de suporte nem calcular probabilidade de verdade. Se ocorrer explosão de caminhos, usar a lista de vias explícitas sem expansão distributiva.

Limite: o grafo não demonstra que uma claim sem dependência registrada está cientificamente imune à mudança. Revisão global de cobertura ocorre em RELEASE e após mudanças que alterem a própria pergunta/desenho.

## 11. Persistência, concorrência e falhas

### 11.1 Journal operacional e execução limpa

Resolver caminhos de controle usando Git, sem presumir que `.git` é diretório: `git rev-parse --git-common-dir` define a base do lock do projeto; `git rev-parse --git-dir` define o journal do worktree. Usar `<git-dir>/research/runtime/<operation_id>/` para journal/propostas temporárias e `<git-common-dir>/research/locks/<project_id>.lock` para exclusão cooperante. Clones independentes não compartilham lock; coordenação distribuída fica fora de V1.

Antes da execução, registrar e sincronizar EXECUTION_STARTED no journal operacional, fora da árvore de trabalho. O runner continua exigindo checkout limpo e o diff freeze → run continua contendo somente saídas científicas declaradas. Não introduzir exceções para diretórios de metadados nesse diff. Propostas fornecidas por stdin ou transportadas fora do checkout não sujam a execução. Logs/saídas capturados pelo adapter ficam no journal até finalização e não autorizam ignorar saídas científicas não declaradas.

Ordem obrigatória: freezes científicos e EXEC comprometidos → checkout limpo em execution_freeze → journal started → execução → inspeção/output fingerprints → commit apenas das saídas → importar eventos e gravar RUN → commit posterior de recibos/metadados → ADMIT_RESULT. O journal registra o estado real em cada etapa, inclusive sem sucesso. Não limpar automaticamente efeitos externos nem afirmar que resultado não foi exposto em execução falha.

A importação atribui `observed_at` original e `recorded_at` de importação, preserva operation_id e origem, e consolida fatos locais. O commit tardio do evento não vira compromisso prospectivo. A ordem física no journal e sua origem observada são evidência operacional sob confiança cooperante, não prova criptográfica contra edição do journal. Perda do journal impede reconstruir essa evidência automaticamente; preservar RUN/EXEC que possam ser verificados e marcar o restante NOT_VERIFIED.

### 11.2 Admissão cooperante

1. Adquirir lock exclusivo por projeto usando criação atômica de arquivo; registrar PID, operação e snapshot base.
2. Resolver HEAD e fingerprints. Rejeitar base obsoleta com RECOVER.
3. Verificar obrigações e preparar escrita num diretório temporário.
4. Revalidar a base imediatamente antes de admitir registros; escrita atômica com rename.
5. Registrar marcador final no journal, consolidar o conjunto de registros quando autorizado e liberar lock. A confirmação Git segue o fluxo explícito do projeto.

Registros escritos mas ainda não comprometidos são pendentes para checks de append-only/história. Não devem sustentar uma liberação final como história já consolidada. Falha de commit não deve produzir um evento que afirme commitment histórico concluído.

Rename é atômico por arquivo, não pelo conjunto. Toda admissão registra operation_id, membros esperados e digests no journal e num evento final de admissão consolidado junto aos novos registros. A projeção só promove novos DEC/REL para CURRENT após encontrar membros completos, fingerprints correspondentes e evento final válido no histórico comprometido. Commit parcial, write/rename interrompido ou ausência do evento final mantém candidatos e retorna RECOVER; não procurar inferir sucesso pelo nome do arquivo. RUN histórico continua validável pelo contrato legado, sem fabricação de novos eventos.

Locks armazenam host/worktree/operation_id, PID e identidade de início quando disponível. Liveness não é concluída por PID isolado, porque pode ser reutilizado. Recuperação exige examinar processo, journal e efeitos. Revalidação de snapshot e lock cooperante não protegem de processo externo adversarial; não declarar garantia de contenção com base nisso.

Em operações que executam código, persistir EXECUTION_STARTED antes da execução e EXECUTION_COMPLETED somente após inspeção. Um recibo operacional não é um RUN científico; a relação é construída apenas após commits e validação existentes. Execução interrompida pode já ter exposto resultados e produzido efeitos: não repetir automaticamente como se nada tivesse ocorrido.

O lock protege processos cooperantes; não torna imutável o filesystem nem Git. Mudança externa detectada exige inspeção. V1 não oferece transação ACID sobre execução, Git e sistema externo. Efeitos irreversíveis precisam de backend próprio ou permanecem fora do contrato.

### 11.3 Retomada

Ao iniciar sessão, reconstruir projeção e checks rápidos sobre a fronteira ativa, incluindo existência dos registros duráveis e ancestralidade do último HEAD verificado. Persistir essa âncora no journal local somente após verificação, distinguindo-a de fonte de verdade científica. Estado contraditório, divergência de história, lock órfão ou execução sem finalização produz RECOVER e checklist de inspeção. Nunca apagar lock apenas por tempo; identificar se o processo está vivo e se houve efeitos. Retomada informa condição faltante e próximo trabalho legítimo, sem restaurar certeza por narrativa.

## 12. Integração com Claude Code, Codex e outros hosts

### 12.1 Interface comum

Interface proposta, a implementar:

```text
research supervise propose --request action.json --root .
research supervise run --request action.json --root .
research supervise admit --request action.json --root .
research supervise resume --root .
research validate --root . --strict
research graph affected RESOURCE_ID --revision REVISION --root .
research release inspect REL_ID --root .
```

Entradas e saídas estruturadas via stdin/stdout também devem ser suportadas. stdout do dispatcher contém um único resultado JSON; logs ficam em stderr/journal e stdout do subprocesso não se mistura com a resposta. Nenhum comando admit publica externamente. Exit codes: 0 operação atendida, 1 ação bloqueada ou evidência/julgamento requerido, 2 contrato inválido, 3 recuperação requerida. `propose`, `resume`, `graph` e `inspect` podem retornar 0 sem admitir ou executar algo; incluir `effect: checked | executed | admitted` no resultado. Diagnóstico de forma JSON precede efeito; falha de operação não pode ser relatada como admitted.

`propose` calcula obrigações sem executar nem admitir. `run` executa somente ações de execução cobertas pelo backend e seu journal. `admit` resolve registros/evidências existentes e não executa novamente o comando científico. `resume`, `graph` e `release inspect` inspecionam/derivam estado sem alteração dos artefatos autoritativos; qualquer reparação é uma proposta subsequente explícita.

O núcleo em Python 3.10+ usa biblioteca padrão. Em V1, execução supervisionada é qualificada no ambiente POSIX de CI; outro SO precisa de testes próprios para obter o mesmo nível declarado. Não introduzir dependência do host no núcleo.

### 12.2 Capabilidades observadas

Cada adapter declara e testa separadamente: interceptar antes da execução, impedir chamada, observar conclusão/saída, observar leitura/exposição, oferecer orientação, vincular contexto de revisão e impedir/liberar ação externa.

Níveis descritivos: `guidance`, `audit`, `controlled_execution`, `isolated_execution`. Usar também a matriz por fronteira; um nível global não substitui capacidades específicas. Isolated só é permitido com isolamento físico demonstrado. Contexto separado e leitura mediada são capacidades diferentes.

Um adapter NÃO DEVE alegar impedimento baseado apenas em prompt, nome de hook ou declaração do agente. Testes de cobertura devem tentar a rota normal e rotas alternativas: shell direto, subprocessos, leitura de saída, edição de registro e finalização sem passagem pelo supervisor.

Se não houver integração adequada, o plugin opera em guidance/audit. A CLI pode controlar execuções que passam por ela; não controla comandos paralelos. Missing coverage é uma limitação explícita, não erro escondido nem promessa de host futura.

### 12.3 UX conversacional

O usuário fala normalmente. O agente traduz intenção em proposta e recebe orientação curta. Não exigir comandos internos, preenchimento manual de JSON ou autorização repetida de ações já autorizadas. Pedidos humanos ficam restritos a decisões materiais cuja autoridade realmente falta.

O supervisor admite trajetória processual; o agente continua responsável por planejar e integrar avaliações. Estado correto da infraestrutura não autoriza o agente a declarar pesquisa cientificamente validada sem evidência de adequação.

### 12.4 Política de interação

**Resolver antes de interromper.** Ausência de um artefato que o agente consegue preparar, uma verificação que consegue executar ou evidência acessível que consegue inspecionar deve gerar trabalho autorizado, não um pedido para o usuário administrar o procedimento. Perguntar apenas quando respostas possíveis mudam materialmente o alvo, a interpretação ou a autoridade da próxima ação. Reutilizar decisões e autorizações já presentes na sessão/projeto, sem tratá-las como licença para reescrever compromissos.

**Preservar fluidez sem promover candidatos.** Não exigir que o usuário selecione modos internos a cada pedido. Inferir a intenção a partir do contexto. Uma solicitação de brainstorming, código ou rascunho não dispara adoção científica. Ambiguidade entre explorar e executar uma ação confirmatória irreversível exige a menor pergunta necessária antes da exposição. Journal/alvo editorial ausente não bloqueia exploração nem rascunho; torna-se obrigatório apenas na fronteira que realmente depende dele.

**Comunicar decisões, não checks rotineiros.** Checks bem-sucedidos e sem mudança relevante são registrados sem um relatório ao usuário por ação. Comunicar eventos que alterem a conclusão permitida, a próxima ação, a qualidade do produto, uma limitação material ou a decisão humana necessária. Os IDs, grafos e recibos ficam acessíveis sob demanda.

**Intervenção acionável.** A mensagem deve trazer: ação afetada, condição/evidência decisiva, consequência científica e trabalho seguinte. Quando o agente consegue executar a recuperação, anunciar e prosseguir. Quando precisa do usuário, apresentar a menor decisão com consequência clara. Não usar mensagem genérica de bloqueio nem esconder um bloqueio sob resumo otimista.

Exemplo: “O resultado já foi observado; esta nova explicação será investigada como descoberta. Vou registrar sua origem e preparar o teste que pode distingui-la da alternativa.” Se uma ação confirmatória específica foi solicitada e não pode ocorrer, explicar também essa restrição antes de seguir uma recuperação compatível com a intenção.

**Status compacto e estável.** Ao pedir status ou retomar, responder com a pergunta atual, o que está sustentado e com qual limite, o trabalho em andamento e o próximo passo. Não mostrar conclusão admitida se existe apenas candidato. Não repetir limitações já informadas salvo quando sua aplicação muda ou afeta a decisão atual.

## 13. Migração e plano de implementação

### M0 — Baseline e escopo

- Fixar checkout, testes existentes e garantias realmente implementadas.
- Inventariar fronteiras dos hosts e escolher uma controlável para o piloto.
- Congelar o protocolo de avaliação da evolução.

**Saída:** matriz de capacidades, fixtures e critérios do experimento. Sem promessa de enforcement ainda.

### M1 — Contratos e projeção

- Implementar identity, resolver recursos, schemas REF/DEC/REVIEW/EVT/REL e validação append-only. Entregar definições de schema legíveis por máquina com tipos, campos obrigatórios, enums e referência comum de recursos/bindings. A validação runtime usa biblioteca padrão e fixtures positivos/negativos; schema legível por máquina não obriga dependência third-party no núcleo.
- Derivar estado operacional e grafo versionado em memória.
- Manter RUN/EXEC/ASMT existentes e impedir interpretação científica mais forte de registros legados.

**Saída:** round-trip determinístico, referências resolvidas e migração compatível. Projetos legados continuam legados; lacunas degradam explicitamente.

### M2 — Admissão e recuperação

- Implementar supervisor, obrigações por ação, locks, snapshots e retomada.
- Compor validadores existentes, sem duplicar semântica de freezes/exposição.
- Controlar execução confirmatória e admissão do resultado pela CLI piloto.

**Saída:** violações temporais e de integridade detectadas/impedidas dentro da fronteira declarada, com caminhos legítimos preservados.

### M3 — Revisão e qualidade

- Implementar referências do projeto e manifestos de revisão.
- Introduzir avaliações delimitadas com evidência conferível e cobertura explícita.
- Reavaliar dependências alteradas e verificar pacote REL exato.

**Saída:** caso completo de pergunta → execução → conclusão → crítica → correção → versão admitida para saída.

### M4 — Adaptadores e ablação

- Conectar hosts somente nas interfaces existentes e testadas.
- Comparar orientação inicial, contextual e controle efetivo.
- Testar componentes com as mesmas referências, evidências e capacidade de modelo.

**Saída:** evidência de benefício e custo, decisão sobre mecanismos a manter/remover. Não fixar novo número de release antes dessa decisão.

### Compatibilidade

Adicionar módulos do núcleo em `skills/research-map/scripts/` e testes em `tests/`; os nomes são proposta, não arquivos existentes:

`contracts.py`, `resources.py`, `supervise.py`, `review.py`, `release.py`, `events.py`.

Reutilizar `epistemic.py`, `execute.py`, `validate_all.py`, `assessment.py` e `graph.py`, com divisão interna quando reduzir duplicação. Os comandos acima podem inicialmente ser um dispatcher Python; empacotamento da CLI não deve ser pré-requisito do piloto.

`scientific-method` passa a chamar o supervisor nas fronteiras. As skills internas permanecem responsáveis pelo conteúdo. `RESEARCH.map` continua pequeno e legível, com status reconciliado com projeção e artefatos; não converter o mapa em ledger. Divergência entre mapa e base aparece como achado verificável.

Nenhum ASMT legado vira REVIEW. Nenhum parecer histórico recebe contexto separado retroativamente. Nenhum RUN sem ordem verificável recebe congelamento fabricado. Compatibilidade de leitura não equivale a conformidade no novo gate.

## 14. Verificação e critérios de aceitação

### 14.1 Cenários de aceitação obrigatórios

| ID | Cenário | Resultado esperado |
|---|---|---|
| T01 | Confirmatório sem plano congelado | Impedir a rota controlada antes da execução; exploração continua disponível |
| T02 | Código/input muda após freeze | Recusar admissão sob aquele freeze |
| T03 | Mesmo DATA renomeado | Não contar como confirmação independente |
| T04 | Resultado binário alterado | Detectar mudança byte-exata |
| T05 | ASMT SUPPORTS sem revisão material | Não admitir claim por esse ASMT sozinho |
| T06 | Manuscrito muda após revisão | Revisão anterior não cobre nova formulação; REL recusado |
| T07 | Arquivo sem dependência declarada muda | Sem invalidar avaliações apenas por HEAD; cobertura global ainda examinada no release |
| T08 | Falha de uma via, outra sobrevivente | Reavaliar; não retirar nem conservar automaticamente a mesma conclusão |
| T09 | Duas vias compartilham origem | Preservar dependência; não contar como evidência independente |
| T10 | T1 em dois freezes | Nós e consultas históricos distintos |
| T11 | Avaliação retirada e bytes restaurados | Não reativar sem nova decisão |
| T12 | Reopen após exposição | Preservar descoberta e história; confirmação exige base legítima |
| T13 | Crash entre início e fim da execução | RECOVER; efeitos/exposição inspecionados antes de retry |
| T14 | Snapshot muda antes de escrita | Rejeitar proposta obsoleta; não emitir ALLOW atual |
| T15 | Reescrita de registro committed | Falha append-only; novo ID exigido |
| T16 | Ciclo, ID quebrado ou schema desconhecido | Diagnóstico explícito; nenhuma relação inventada |
| T17 | Fonte indisponível | NOT_VERIFIED; não presumir continuidade |
| T18 | Saída release diferente do manifesto | Pacote não admitido |
| T19 | Host contorna CLI/hook | Limite observado; não alegar cobertura daquela rota |
| T20 | Achado material respondido apenas pelo autor | Resolução exige avaliação apropriada |
| T21 | Brainstorm, código e rascunho com interpretação ainda candidata | Trabalhar sem gate de adoção; estado de rascunho claro; uso material posterior continua condicionado |
| T22 | Artefato/verificação faltante que o agente pode preparar no escopo autorizado | Preparar/executar e prosseguir; não pedir ao usuário para operar o procedimento |
| T23 | Várias claims num mesmo snapshot, ainda sem adoção material | Revisão em lote com julgamento por claim; não exigir revisão por frase |
| T24 | Pedido ambíguo antes de exposição confirmatória irreversível | Uma pergunta material, sem executar a rota dependente até resolução |
| T25 | Checks rotineiros repetidos e alvo editorial ainda indefinido | Registrar checks sem interrupção; permitir trabalho que não depende do alvo; exigir alvo na fronteira aplicável |
| T26 | EVT started/proposta gravados durante execução supervisionada | Journal fica fora do checkout; runner permanece limpo; run commit contém somente outputs declarados |
| T27 | Input/plano atuais mudam, claim explicitamente histórica usa pinned | Verificar bytes históricos e âmbito; não invalidar só por mudança do arquivo atual |
| T28 | Claim sobre estado atual aponta para pinned sem justificar atualidade | Revisão/critério detecta âmbito indevido; não admitir atualização por metadata alone |
| T29 | Mesma operação reenviada após sucesso, crash ou payload diferente | Reusar resultado, retornar RECOVER ou falhar contrato; nunca repetir execução silenciosamente |
| T30 | Apenas parte dos membros de admissão é persistida/committed | Nenhum DEC/REL novo torna-se CURRENT; recuperar conjunto incompleto |
| T31 | REF tenta tornar integridade core advisory ou remover requisito | Não enfraquecer CORE-*; bloquear a rota que continua sem obrigação satisfeita |
| T32 | REVIEW diz PASS, mas tem claim inadequate/insufficient ou achado material aberto | Rejeitar contradição do manifesto; manter o resultado verificável mais restritivo |
| T33 | Markdown revisado, mas PDF final omite resultado/limitação | Verificar produto efetivo; não admitir pacote diferente do material examinado |
| T34 | Edição manual de DEC ou indicação de revisor separado sem marcador/atestação | Permanecer candidato ou NOT_VERIFIED; schema não produz admissão nem separação |
| T35 | Registro comprometido apagado/renomeado ou história recuada para ocultar exposição | Detectar exclusão/renomeação no histórico alcançável ou divergência da âncora; não restaurar ausência de exposição |

T01–T18 e T26/T27/T29–T32/T35 incluem harnesses determinísticos de contratos e sequências; T19 requer integração real de host. T20/T34 combinam checagem de registros e atestação do fluxo de revisão. T21–T25 são testes de comportamento/UX em agente instrumentado; T28/T33 exigem também casos semânticos/produto com referência humana ou evidência verificável de discrepância. Não apresentar testes de parser como demonstração de qualidade de julgamento.

Adicionar testes de sequências geradas com seeds fixos: duplicação de evidência, mudança de ordem, reabertura, supersession e interrupção. A projeção reconstruída deve ser idêntica para o mesmo conjunto de registros válidos e revisões; o histórico de exposição nunca deve ser apagado por operações de estado atual.

### 14.2 Avaliação científica e comportamental

Usar casos com referência humana para detecção de claims omitidas, inadequação de inferência, contexto ausente e correções legítimas. Aceitação de formato ou concordância entre modelos não é ground truth científico.

Comparar quatro condições com modelo, ferramentas, referências, dados e orçamento iguais:

A. Research atual; B. orientação reduzida + validadores atuais; C. B + supervisor mecânico; D. C + avaliação delimitada e dependências versionadas.

Medir: decisões inválidas admitidas, decisões válidas bloqueadas, recuperação, cobertura de claims, fidelidade das evidências, qualidade do produto por critério, tokens/tempo e trabalho humano total. Custos incluem criação de contratos, registro, avaliação e manutenção, além da execução. Para UX, contar interrupções que exigem decisão humana, pedidos evitáveis resolvíveis pelo agente e tempo até próximo trabalho útil. A redução de interrupções só é ganho se não aumenta promoção indevida de candidatos, violação pré-exposição ou omissão de limites materiais.

Pré-especificar tarefa, unidade independente, margens práticas, modelo de análise e regras de parada antes do teste confirmatório. Piloto pode calibrar margens em casos separados; não usar os mesmos casos para escolher mecanismos e confirmar ganho.

Critério de avanço: componente reduz falha material ou custo total com ganho prático e não inferioridade nos demais critérios essenciais sob margens registradas. Nenhuma configuração é chamada de dominante/Pareto ótima sem comparação e incerteza apropriadas. Um componente que só bloqueia tudo falha a avaliação de progresso legítimo.

### 14.3 Condições de conclusão de V1

- Testes mecânicos e baseline de regressão passam.
- Caso completo com correção e retomada é reconstruível em novo processo.
- Pelo menos uma fronteira tem cobertura demonstrada; demais limites estão explícitos.
- Claims materiais e obrigações de liberação têm avaliações e cobertura identificadas.
- A avaliação comportamental distingue ganho demonstrado de capacidade apenas implementada.
- Nenhuma declaração de verdade, novidade ou qualidade deriva automaticamente de PASS processual.

## 15. Questões abertas, com decisões padrão

| Questão | Decisão V1 | Condição para revisar |
|---|---|---|
| JSON ou SQLite autoritativo? | JSON em Git; índice reconstruível | Volume/concorrência medidos tornam isso insuficiente |
| Fingerprint de seção ou arquivo? | Arquivo completo + locator | Falsas invalidações demonstram necessidade de precisão maior |
| Retenção automática por suporte alternativo? | Exigir avaliação de RETAIN/NARROW | Domínio restrito com semântica e verificadores validados |
| Modelar todo o ciclo científico em autômato? | Não; poucos contratos de fronteira | Falha concreta exige composição formal adicional |
| Aprende regras automaticamente? | Sugere mudanças; não altera invariantes silenciosamente | Processo prospectivo de validação com vantagem demonstrada |
| Garantia em host sem interceptação? | Guidance/audit explícitos | Adapter/back-end passa testes de cobertura |
| Mais campos científicos obrigatórios? | Somente o material para a decisão | Casos adversariais mostram lacuna não resolvida por registro existente |

## 16. Antecedentes e hipótese de inovação

Esta spec integra técnicas existentes. A hipótese própria é que um supervisor pequeno, com referências explícitas e decisões versionadas, melhora a qualidade e a eficiência de pesquisa conduzida por agentes sem eliminar exploração criativa. O experimento da seção 14 deve poder rejeitar essa hipótese ou reduzir seu escopo.

Antecedentes que informam a implementação:

- Lastro EXP-28A/29A1: estruturas especiais devem sobreviver a controles genéricos com informação comparável. [EXP-28A](https://github.com/enniolopes/lastro/blob/main/docs/63-exp28a-confirmatory-results-and-frontier-correction.md), [EXP-29A1](https://github.com/enniolopes/lastro/blob/main/docs/69-exp29a1-generic-baseline-floor-result.md).
- ToolGate (2026, preprint): condições antes da execução e antes da aceitação da saída; garantias condicionadas aos contratos. [DOI](https://doi.org/10.48550/arXiv.2601.04688).
- PBRC (2026, preprint): revisão baseada em evidências identificadas; controlar também correções legítimas impedidas. [DOI](https://doi.org/10.48550/arXiv.2604.15558).
- RegCheck/IDEA (2026, preprint): separar coleta, definição, extração e julgamento; avaliação de fidelidade ainda em andamento no texto examinado. [DOI](https://doi.org/10.48550/arXiv.2601.13330).
- Workflow Run RO-Crate (2024, PLOS ONE): formato interoperável de proveniência; exportação pode preceder formato externo próprio. [DOI](https://doi.org/10.1371/journal.pone.0309210).
- PROV-AGENT (2025, IEEE eScience): relacionar interações e decisões de agentes ao workflow. [DOI](https://doi.org/10.1109/eScience65000.2025.00093).
- Controle supervisório: observabilidade, controlabilidade e preservação de caminhos admissíveis. [Ramadge/Wonham](https://doi.org/10.1137/0325013).
- Simplex/runtime assurance: componente avançado acompanhado de supervisão e recuperação; transferência para ciência depende dos contratos do domínio. [NASA, 2024](https://shemesh.larc.nasa.gov/fm/papers/NFM2024-draft.pdf).
- SkillSentry (2026, preprint): orientação contextual e supervisão de skills em Claude Code/Codex; não prova adequação científica dos procedimentos. [Paper](https://arxiv.org/abs/2608.09253).

**Resultado pretendido:** liberdade para propor e investigar; disciplina verificável para comprometer, admitir, revisar e liberar; critérios explícitos para elevar qualidade; limites honestos onde observação, controle ou julgamento não forem suficientes.

## 17. Resultado do pre-flight da spec

**Data:** 14/10/2026. **Veredito:** pronta para iniciar M0/M1 após as correções abaixo; implementação completa, cobertura dos hosts e benefício científico ainda não demonstrados.

| Achado | Severidade | Correção 1.2 | Evidência/critério |
|---|---|---|---|
| Journal started suja checkout e impede runner atual | Bloqueante | Journal operacional em Git dir; importar somente depois do run commit | Experimento local com fixture do runner: evento em `.research/events` → ERROR sem executar; journal em `.git/research/runtime` → OK com output |
| Recursos históricos tratados como se toda mudança atual os invalidasse | Material | Bindings pinned/follow_current/external_refresh e âmbito examinado | T27/T28 |
| REVIEW resources alternava lista/mapa; parecer e liberação podiam exigir autorreferência | Material | Um contrato comum, fases de commit e manifesto fora de seu próprio digest | Fixtures de schema, T30/T32 |
| JSON escrito confundido com admissão; write por arquivo não é transação conjunta | Bloqueante | Marcador final, membros/digests e estado candidato até consolidação | T30/T34 |
| Scan dos arquivos presentes pode perder registro apagado ou história recuada | Material | Verificar histórico alcançável e âncora local; retirada por novo registro | T35 |
| Retry podia repetir execução após crash | Material | operation_id idempotente e journal de recuperação | T13/T29 |
| REF e PASS agregado podiam enfraquecer integridade ou esconder lacunas | Material | CORE-* não dispensável e consistência de verdict | T31/T32 |
| Revisão do fonte insuficiente para produto final alterado | Material | Inventário e inspeção dos bytes efetivamente liberados | T18/T33 |
| Cenários de UX chamados de testes puramente mecânicos | Clareza | Classificação explícita de harness/host/julgamento | Seção 14.1 |

Verificações executadas nesta revisão: leitura da spec e dos contratos atuais de execute/epistemic; reprodução do conflito de journal numa fixture Git temporária; verificação de sintaxe dos exemplos JSON e da estrutura/cobertura dos cenários. Não houve implementação do supervisor nem testes reais dos adapters nesta etapa. O experimento do journal não demonstra durabilidade, idempotência ou proteção adversarial; apenas resolve a incompatibilidade de worktree observada.

Pendências de M0/M1: fixar baseline atual do repositório antes de editar, qualificar uma fronteira real de host, produzir schemas e fixtures completos e congelar o desenho de avaliação. A escolha do journal não autoriza flexibilizar o diff output-only nem dispensar congelamentos existentes.
