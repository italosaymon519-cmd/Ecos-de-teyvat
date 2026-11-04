# Ecos de Teyvat

Mesa de RPG em português, com fichas, PV, EE, recargas, reações elementais, dados e diário.

Requer Node.js 22 ou superior. Sem dependências de runtime. Os testes de permissões usam PostgreSQL/PGlite como dependência de desenvolvimento.

```sh
npm ci
npm start
npm test
```

Servidor na porta 3000, configurável por `PORT`. O progresso fica no localStorage do navegador. Exporte regularmente uma cópia JSON; a importação substitui a campanha local após confirmação. Fora de uma sala, fichas e diário são locais. Com a atualização 004, selecionar uma sala carrega as fichas vinculadas à conta e à campanha, conforme as instruções abaixo.

Regras: máximo 3 EE; E gera 1 EE se funcionar e volta após um turno de intervalo; Q exige 3 EE e respeita limites por descanso. Reações dão 1 EE a cada um dos dois participantes e consomem a marca. Avançar rodada remove marcas. Cada ficha registra uma marca preparada em um inimigo narrativo: não é um gerenciador individual de inimigos. O elemento usado pelo segundo participante é o da sua Visão; efeitos espalhados e autorreações ficam para a mesa.

Dano, cura, escudos, condições e modificadores são resolvidos manualmente. Descansos liberam os limites de Q; recuperação de PV/EE fica a cargo da mesa. Rodadas de combate presumem um turno por personagem; efeitos que alteram iniciativa exigem arbitragem. Não existe custo ou limite adicional de energia por reação além do teto de 3.

O mapa enviado na conversa ainda não integra o site: o arquivo original precisa ser disponibilizado como recurso do projeto para inclusão fiel. O site não depende de serviços, fontes ou imagens externas.

## Publicação automática no Netlify

Conecte este repositório ao projeto existente e selecione a branch `main`. O arquivo `netlify.toml` configura `npm run build` e a pasta pública `dist`. Somente HTML, CSS e JavaScript do site são incluídos; o servidor local e os testes não são publicados.

A biblioteca inclui os três guias da campanha. A seção Mapa permite carregar uma imagem local com zoom; o mapa fica no IndexedDB do navegador e não integra o backup JSON.

## Painel do mestre

Inclui dez cenários de Mondstadt e a abertura original “Ecos sob os Mil Ventos”, com cenas, NPCs e missões editáveis. Iniciativa, turnos, PV e condições são manuais; o painel usa backup separado, sem senha ou sincronização. Consulte [as referências e limitações](docs/mondstadt.md).

## Contas, mapas e sala compartilhada

A sala permite contas individuais, convites e acervo de mapas, cenas e NPCs. O mestre controla revelação e apresentação; jogadores recebem atualizações a cada cinco segundos. Siga [a configuração do Supabase e Netlify](docs/sala-compartilhada.md). Sem as duas variáveis públicas e o SQL aplicado, o site informa que as contas ainda não estão disponíveis. As funcionalidades locais continuam funcionando.

### Tabuleiro e tokens

O mapa compartilhado permite tokens de personagens, aliados e inimigos, arraste, zoom e tela cheia. Jogadores movem apenas personagens atribuídos a eles; o mestre controla todos. Para ativar, aplique a migração [002-map-tokens.sql](supabase/002-map-tokens.sql) após o setup inicial. Nenhum dado existente precisa ser apagado.

### Iniciativa compartilhada

A opção Combate da sala mostra a ordem de jogadores e inimigos, turno atual e rodada. O mestre pode importar tokens ou fichas da mesa selecionada, rolar/ajustar iniciativas e avançar a fila. Aplique [003-combat-initiative.sql](supabase/003-combat-initiative.sql) para persistir o controle compartilhado; o encontro local permanece disponível.

### Limites de criação e reações

A ficha permite no máximo duas perícias treinadas e dois talentos, conforme a criação dos guias. A interface bloqueia uma terceira opção e valida novamente ao salvar e importar. Fichas locais antigas com excesso continuam preservadas, mas precisam ser corrigidas antes de salvar. Não foi inventada progressão adicional de escolhas, pois os guias ainda não a definem.

A reação mostra preparação e resultado no próprio painel. Prepare a marca do primeiro personagem e selecione o segundo. A reação consome a marca e dá 1 EE a cada participante, até 3; dano, escudos e condições continuam manuais. O fluxo usa as fichas da mesa selecionada e explica quando faltam dois participantes. Na sala, a reação é gravada atomicamente no banco; o jogador deve controlar o segundo participante. As combinações de Anemo/Geo com elementos compatíveis aceitam ambas as ordens descritas na tabela.

A marca preparada agora corresponde obrigatoriamente à Visão cadastrada. Os seletores mostram somente esse elemento, a reação valida a correspondência e marcas antigas incompatíveis são limpas ao carregar/importar ou trocar a Visão. As reações possíveis continuam sendo determinadas pela combinação dos elementos dos dois participantes.

### Testes de perícia pela ficha

Em Personagens, abra **Rolar perícias pela ficha**, ou use **Rolar perícia** no cartão da Mesa. Cada um dos 18 testes mostra o bônus pronto e oferece normal, vantagem ou desvantagem. O cálculo usa d20 + atributo e, somente se a perícia estiver treinada, proficiência de nível (+2 em 1–4; +3 em 5–8; +4 em 9–12; +5 em 13–16; +6 em 17–20). Fichas anteriores assumem nível 1 até edição. Não há soma automática de especialização ou bônus narrativos não selecionados. A Tiara pode ser selecionada antes de um teste compatível, conforme a seção de artefatos.

O resultado identifica o jogador (nick da sala/local, ou nome do personagem como alternativa), o personagem, os dados e cada parcela do cálculo. O resultado também entra no histórico local. Os limites de duas perícias e dois talentos permanecem. Um 20 ou 1 natural no teste de perícia não aplica automaticamente as regras exclusivas de ataques.

### Benefícios defensivos das Visões

A Mesa e a ficha exibem o benefício da Visão com um uso por combate. Geo rola 1d6 de escudo; Hydro recupera até 2 PV após confirmação de resistência bem-sucedida; Electro acrescenta +2 à Defesa até o próximo ataque registrado, inclusive um erro com dano zero. Pyro reserva redução de 2 para dano de ataque; Cryo reserva redução de 2 para dano de inimigo afetado por Cryo. Dendro reserva +2 para o teste contra condição prejudicial na opção Teste de resistência.

Ao registrar dano, informe se veio de ataque e se o inimigo está afetado por Cryo. A redução aplicável é calculada antes da absorção do escudo, e só o restante reduz PV. O limite de uso não volta com descanso nem com a próxima rodada: apenas no início de um novo combate. Trocar de Visão remove efeitos incompatíveis e preserva o uso já gasto.

Anemo registra o reposicionamento reativo de 3 m, sem ataques de oportunidade; a posição do token continua sendo ajustada manualmente porque o mapa não possui escala em metros. Use Concluir deslocamento para resolver o aviso. Gatilhos narrativos (ter resistido, ter sido atacado, ter acertado Electro) são confirmados pelo jogador/mestre, não inferidos de uma rolagem sem CD. Na mesa local, essas alterações ficam no navegador. Na campanha conectada, PV e efeitos são salvos com a ficha.

### Artefatos básicos

Abra **Artefatos · 5 peças equipadas** no cartão da Mesa ou na ficha. As cinco peças iniciais do guia ficam equipadas: Flor Silvestre (+3 PV máximos, já incluídos nos 33 iniciais), Pluma do Viajante (+1 no primeiro acerto com arma por turno), Ampulheta Parada (+1 em resistência por combate), Cálice Elemental (+1 em habilidade com dano da própria Visão por turno) e Tiara da Concentração (+1 em teste de Intelecto ou Espírito por combate).

**Rolar dano** permite informar dados, modificador, acerto e crítico. O crítico duplica apenas os dados; o bônus fixo do artefato entra uma vez. Um erro preserva o uso. Ataque comum de catalisador usa Pluma; habilidades elementais usam Cálice. O cálculo registra dano, sem descontar automaticamente PV de um alvo. Ajuste dados e modificador conforme a habilidade usada.

Areias e Tiara devem ser selecionadas antes de rolar, no teste de resistência ou no painel de perícias. A Tiara preparada aguarda um teste de Intelecto/Espírito. Os usos persistem ao recarregar e editar a ficha; apenas novo combate restaura os usos por combate. A iniciativa compartilhada/local identifica cada turno para Pluma/Cálice; sem iniciativa, Avançar rodada renova esses bônus. A Flor não é somada novamente ao editar/importar: o campo de PV máximos contém o valor final. Na mesa local, fichas e usos ficam no navegador; na sala conectada com a atualização 004, ficam vinculados à conta e à campanha.


### Fichas por campanha e participantes online

Execute [004-campaign-sheets-presence.sql](supabase/004-campaign-sheets-presence.sql) no SQL Editor do mesmo projeto Supabase. A migração pode ser repetida, preserva os dados e não exige novas variáveis no Netlify. O arquivo também pode ser baixado na própria sala pelo aviso de ativação.

Ao selecionar uma sala, a Mesa e Personagens passam a mostrar suas fichas. Criar/editar salva automaticamente o conteúdo completo, incluindo PV, EE, habilidades, proficiências, Visão e artefatos. O dono e o mestre editam; os demais membros consultam. A mesma conta pode recuperar as fichas em outro navegador ou dispositivo. A sala deve continuar existindo e ser selecionada novamente. Para as fichas antigas, use **Trazer uma ficha que já existe neste navegador → Copiar ficha local para esta campanha**. A cópia pertence à conta que a trouxe; a original permanece na mesa local. Selecione a opção vazia de Suas salas para voltar à mesa local.

O status só confirma salvamento após resposta do servidor. Falhas mantêm rascunhos separados por conta/sala, com nova tentativa automática. Alterações em campos diferentes são combinadas; versões conflitantes do mesmo campo oferecem usar a versão da mesa, salvar o próprio rascunho ou baixá-lo. O diário, notas e histórico de rolagem continuam locais e separados por sala; os tokens permanecem independentes das fichas. Reentrar num combate em andamento preserva os usos já gastos; cada dono atualiza sua ficha ao receber um novo combate/rodada.

A lista de participantes mostra nomes, mestre e estado Online/Offline para todos os membros. O servidor registra presença por sessão a cada 20 segundos, a lista atualiza a cada 10 segundos e várias abas contam como uma pessoa. Sair remove apenas a sessão correspondente; fechar o navegador ou perder a conexão pode levar até 90 segundos para aparecer offline. Uma falha de conexão mostra presença indisponível. As políticas do banco impedem consultar outras salas, editar fichas alheias sem ser mestre, alterar a autoria e forjar presença de outro usuário.

Validação: testes PostgreSQL/PGlite de permissões, versões, limites, reações e expiração da presença; testes de fila offline e conflitos; navegação com duas contas e um navegador novo para recuperar a ficha, preservar recursos em combate e alternar campanhas. A integração no projeto Supabase real depende de aplicar a atualização 004.

### Desempenho da sala compartilhada

As respostas periódicas sem mudanças preservam os elementos de tokens, iniciativa, presença e fichas. Tokens são atualizados no próprio nó, inclusive durante movimentos; uma ficha alterada não reconstrói as demais. As atualizações de fichas no mesmo quadro são combinadas, confirmações sem alteração visual não refazem a tela e rascunhos sem mudanças não são regravados. O mapa já decodificado permanece na tela após expirar o link assinado; uma troca de imagem continua carregando o novo arquivo normalmente. O polling de tokens pausa fora da aba Sala compartilhada, e a presença mantém o heartbeat sem atualizar a lista quando o documento está em segundo plano.

Verificação reproduzível: após `npm run build`, execute `python tests/browser/room_performance.py --assert` (Playwright e Chromium). No cenário simulado com 40 fichas e 100 tokens, em 8,5 segundos sem alterações: antes, 1.402 nós removidos e reinseridos e duas gravações locais; depois, zero nesses contadores. O teste também verifica preservação das outras 39 fichas após editar uma, identidade do token após movimento e ausência de nova assinatura/download do mapa ao expirar o link. Esses números medem trabalho evitado nesse cenário, não uma garantia de FPS em todos os dispositivos. A atualização não exige SQL adicional.
