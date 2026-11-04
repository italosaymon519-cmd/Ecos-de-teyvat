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

O status só confirma salvamento após resposta do servidor. Falhas mantêm rascunhos separados por conta/sala, com nova tentativa automática. Alterações em campos diferentes são combinadas; versões conflitantes do mesmo campo oferecem usar a versão da mesa, salvar o próprio rascunho ou baixá-lo. O diário e as notas continuam locais e separados por sala. A atualização 005 adiciona histórico de rolagens compartilhado e vínculos opcionais entre tokens e fichas. Reentrar num combate em andamento preserva os usos já gastos; cada dono atualiza sua ficha ao receber um novo combate/rodada.

A lista de participantes mostra nomes, mestre e estado Online/Offline para todos os membros. O servidor registra presença por sessão a cada 20 segundos, a lista atualiza a cada 10 segundos e várias abas contam como uma pessoa. Sair remove apenas a sessão correspondente; fechar o navegador ou perder a conexão pode levar até 90 segundos para aparecer offline. Uma falha de conexão mostra presença indisponível. As políticas do banco impedem consultar outras salas, editar fichas alheias sem ser mestre, alterar a autoria e forjar presença de outro usuário.

Validação: testes PostgreSQL/PGlite de permissões, versões, limites, reações e expiração da presença; testes de fila offline e conflitos; navegação com duas contas e um navegador novo para recuperar a ficha, preservar recursos em combate e alternar campanhas. A integração no projeto Supabase real depende de aplicar a atualização 004.

### Desempenho da sala compartilhada

As respostas periódicas sem mudanças preservam os elementos de tokens, iniciativa, presença e fichas. Tokens são atualizados no próprio nó, inclusive durante movimentos; uma ficha alterada não reconstrói as demais. As atualizações de fichas no mesmo quadro são combinadas, confirmações sem alteração visual não refazem a tela e rascunhos sem mudanças não são regravados. O mapa já decodificado permanece na tela após expirar o link assinado; uma troca de imagem continua carregando o novo arquivo normalmente. O polling de tokens pausa fora da aba Sala compartilhada, e a presença mantém o heartbeat sem atualizar a lista quando o documento está em segundo plano.

Verificação reproduzível: após `npm run build`, execute `python tests/browser/room_performance.py --assert` (Playwright e Chromium). No cenário simulado com 40 fichas e 100 tokens, em 8,5 segundos sem alterações: antes, 1.402 nós removidos e reinseridos e duas gravações locais; depois, zero nesses contadores. O teste também verifica preservação das outras 39 fichas após editar uma, identidade do token após movimento e ausência de nova assinatura/download do mapa ao expirar o link. Esses números medem trabalho evitado nesse cenário, não uma garantia de FPS em todos os dispositivos. A atualização não exige SQL adicional.

### Rolagens compartilhadas e tokens vinculados (005)

Execute [005-shared-rolls-token-sheets.sql](supabase/005-shared-rolls-token-sheets.sql) após 002 e 004 no mesmo projeto Supabase. Pode ser repetido e preserva os dados existentes. A sala mostra um histórico com até 100 resultados recentes (50 no carregamento inicial), e a Mesa mostra os três últimos. Rolagens livres, perícias, resistências, dano e o d6 do escudo Geo são enviados automaticamente com resultado e detalhamento dos bônus. O banco atribui o nick à conta autenticada e registra o nome da ficha naquele momento; jogador só pode rolar por suas fichas e o mestre pode rolar por qualquer ficha da campanha. Os cálculos continuam no cliente: o histórico identifica autoria e registra resultados, sem oferecer um mecanismo de prevenção de trapaça nos dados.

A atualização consulta somente resultados posteriores ao cursor da sala. Reenvios usam o mesmo identificador para não duplicar uma rolagem, mesmo após perder a resposta do servidor. Falhas deixam uma fila por conta e sala neste navegador; não feche nem limpe os dados até confirmar envio. Há um botão para descartar resultados pendentes, sem apagar os já publicados. O diário local e as rolagens fora de uma sala continuam locais. O banco mantém resultados anteriores à janela recente da interface.

No formulário de tokens, o mestre escolhe **Ficha vinculada**; para tokens existentes, usa **Vincular ficha / Trocar ficha**. O token passa a mostrar nome, PV atuais/máximos e condições da ficha, sem manter cópias desses valores. Edite **Anotações de condições (sem duração)** na ficha; o campo é narrativo e não possui duração ou efeitos automáticos. Dois cliques no token ou Enter abrem a ficha. Ao importar tokens na iniciativa, as fichas vinculadas também fornecem Agilidade. Um token do tipo Personagem passa a ser controlado pelo dono da ficha; Inimigo/Aliado continuam controlados pelo mestre. Desvincular devolve o controle ao mestre. Se a ficha for removida, o token informa que está indisponível e não apresenta PV antigos. O vínculo é sempre com uma ficha da mesma campanha.

Testes: fila/idempotência e cursor de histórico, permissões PostgreSQL/PGlite contra falsificação de autoria e vínculos entre salas, e integração com duas contas para resultados de cinco tipos e propagação de nome, PV e condições no mapa.

### Grade, régua e marcadores no mapa (006)

Execute [006-map-grid-measure-markers.sql](supabase/006-map-grid-measure-markers.sql) após o setup e 002 no mesmo projeto Supabase. A atualização é repetível e preserva os dados. A interface fica dentro da apresentação do mapa, inclusive em tela cheia; cenas e NPCs não recebem ferramentas de mapa.

O mestre abre **Grade e escala deste mapa**, define colunas na largura da imagem, distância por quadrado, metros/quilômetros, cor e visibilidade da grade. Cada célula é quadrada, usando a proporção natural da imagem; a régua mede distância euclidiana em linha reta. Não há escala assumida antes do primeiro salvamento. É possível ocultar a grade e manter a medição, por exemplo em um mapa do mundo calibrado em quilômetros. Ao trocar a imagem, confira se a escala continua adequada. As configurações e marcadores pertencem ao mapa, e retornam ao selecioná-lo em outra sessão.

Em **Medir distância**, arraste da origem ao destino ou use dois cliques/toques. A régua é pessoal; **Compartilhar medida** salva a linha para quem pode ver o mapa. **Limpar medida pessoal** não apaga medidas compartilhadas. Em **Colocar marcador**, escolha nome/cor e clique no ponto desejado. O autor e o mestre podem remover marcadores; o mestre remove qualquer um. **Localizar** centraliza o ponto no mapa ampliado. Use **Mover mapa/tokens** ou Escape para voltar à navegação normal. As ferramentas não alteram os movimentos dos tokens.

Os registros usam coordenadas percentuais e a régua usa a proporção natural da imagem, preservando distância com zoom/rolagem. Marcadores e medidas compartilhadas atualizam a cada quatro segundos com a sala visível; respostas sem alterações preservam os elementos. O servidor confirma salvamento antes de exibir novos marcadores. Uma falha mantém um envio pendente nesta tela com opção de tentar novamente pelo mesmo identificador, evitando duplicação; mudar de mapa ou recarregar descarta esse rascunho ainda não confirmado. Há limite de 200 marcadores por mapa. Alterações simultâneas de escala são protegidas por revisão; **Recarregar configuração** busca a escala atual sem sobrescrever um formulário que está sendo editado durante o polling normal.

Validação: geometria em mapas retangulares e zoom/rolagem, permissões PostgreSQL/PGlite de leitura por visibilidade, gravação exclusiva de escala pelo mestre e remoção por autor/mestre; navegador com duas contas, escalas distintas por mapa, réguas privadas/compartilhadas, envio repetido após perda de resposta, persistência e layout móvel. Teste específico: `python tests/browser/map_tools.py` após `npm run build`.

### Escolha de grade hexagonal (007)

Execute [007-hex-grid.sql](supabase/007-hex-grid.sql) após 006. O mestre pode selecionar **Quadrada** ou **Hexagonal** em **Grade e escala deste mapa → Tipo de grade** e salvar. A escolha persiste por mapa e é recebida pelos jogadores. Mapas existentes continuam quadrados até alteração pelo mestre; clientes anteriores continuam podendo salvar escala sem remover um formato hexagonal já configurado.

A opção hexagonal usa hexágonos regulares com ponta para cima. A largura de referência é a distância entre centros vizinhos (igual à distância entre faces laterais opostas). Isso mantém a calibração da régua ao trocar entre quadrados e hexágonos: as medidas seguem em linha reta, sem contagem de passos/células. Zoom, proporção da imagem, réguas e marcadores preservam seu comportamento. O desenho usa um padrão SVG repetido, sem criar milhares de polígonos no documento.

### Condições, escudos e bônus por rodada (008)

Execute [008-combat-effects.sql](supabase/008-combat-effects.sql) depois de 003 e 004. A migração é repetível, preserva os dados e ativa o relógio compartilhado no servidor. Em **Gerenciar efeitos**, no cartão ou ficha, o dono e o mestre adicionam condições, escudos adicionais, bônus/penalidades de Defesa, perícias/resistências e dano. Os demais membros podem consultar. Até 30 efeitos por ficha, duração de 1–100 rodadas ou **Até remover**. As anotações antigas de condições permanecem como texto sem duração.

A duração diminui no início de cada rodada seguinte, quando a iniciativa volta ao começo da fila. Efeito de uma rodada aplicado na rodada 3 vence no início da 4. Avançar participantes dentro da mesma rodada não diminui duração. Repetir uma atualização ou reabrir o site também não diminui. Temporários terminam ao encerrar ou substituir o combate; permanentes ficam até remover. Um efeito criado fora de combate começa a contar no próximo. Na sala, o gatilho do banco atualiza as fichas atomicamente com o combate, inclusive de jogadores offline; o cliente aguarda a sincronização dos efeitos antes de liberar ações da nova rodada. Na mesa local, Novo combate/Avançar rodada e a iniciativa do Painel do mestre usam o mesmo critério.

Escudos adicionais absorvem dano na ordem em que foram adicionados, antes do escudo Geo e depois das reduções Pyro/Cryo. São removidos ao esgotar. Bônus de Defesa somam à Defesa exibida; bônus de testes somam em perícias e resistências da ficha; bônus de dano somam uma vez no cálculo de dano, inclusive em crítico. O crítico duplica só os dados. Benefícios da Visão e artefatos continuam separados e não são cadastrados novamente automaticamente. Condições como Congelado e Queimadura controlam nome/duração: dano periódico, deslocamento e testes de escape continuam sendo resolvidos pela mesa.

Os efeitos aparecem nas fichas, nos tokens vinculados e nos participantes vinculados da iniciativa. Ao preparar combate, importar fichas ou tokens ligados a fichas preserva a ligação; o mestre também pode escolher a ficha de cada participante no formulário da fila. Participantes sem ficha continuam com iniciativa normal; para recursos/efeitos, vincule uma ficha. Os efeitos e o restante dos recursos persistem no mesmo banco da campanha, respeitando as permissões existentes.

Validação: testes de duração idempotente, absorção conjunta com Geo, bônus de testes/Defesa/dano e crítico; PostgreSQL/PGlite com expiração no servidor, limite/validação, persistência, vínculo de participante, término/troca de combate e rejeição de rodadas retrocedidas; duas contas em navegador verificando sincronização, ações após expiração, permissões, tokens, iniciativa e retomada. `python tests/browser/effects.py` após o build.


### Administração da sala (009)

Execute [009-room-administration.sql](supabase/009-room-administration.sql) após 002–008. Em **Sala compartilhada → Administração da sala · Mestre**, o mestre pode renovar o convite, transferir fichas entre membros e remover participantes. O painel fica oculto para jogadores e na visualização como jogador; as funções do banco também verificam o mestre.

Transferir controle preserva todos os recursos e efeitos, incrementa a revisão da ficha e atribui seus tokens vinculados ao novo responsável. O dono anterior continua podendo consultar enquanto for membro, mas perde edição e movimento. Rascunhos offline do dono anterior ficam disponíveis para download/resolução sem sobrescrever a ficha transferida. O mestre mantém acesso completo.

Remover um participante preserva suas fichas, inclusive arquivadas, com o mestre. Tokens vinculados ativos acompanham as fichas; tokens independentes desse jogador passam a controle exclusivo do mestre; vínculos com fichas arquivadas são desfeitos. A presença é removida e o convite é renovado na mesma transação. Os links anteriores deixam de funcionar para todos, mas quem já está na sala permanece. O participante removido pode voltar se receber o novo convite. Rolagens e marcadores anteriores permanecem com a autoria histórica. A sessão aberta detecta a remoção na próxima sincronização da sala (normalmente até cinco segundos com a página visível), limpa a mesa e mantém a conta conectada para outras campanhas. Imagens já visualizadas/baixadas não podem ser recolhidas.

As funções serializam entrada, presença e administração pela sala; transferências exigem a revisão atual. A migração pode ser executada novamente. Validação: permissões PostgreSQL/PGlite, convites antigos/novos, transferência e movimento de tokens, preservação de efeitos/histórico, limpeza de presença, remoção e retomada; rascunhos offline e duas contas no navegador. Teste: `python tests/browser/room_admin.py` após o build.

### Backup e restauração da campanha (010)

Execute [010-campaign-backups.sql](supabase/010-campaign-backups.sql) depois de 002–009. Em **Sala compartilhada → Backup e restauração · Mestre**, use **Baixar backup completo**. O arquivo JSON versionado reúne fichas ativas/arquivadas, mapas/cenas/NPCs, visibilidade e apresentação, tokens e seus vínculos, grades quadradas/hexagonais e escalas, marcadores/réguas, iniciativa e histórico de rolagens. As imagens enviadas para o acervo acompanham o arquivo em base64, com SHA-256; uma falha de download impede gerar um backup incompleto. Inclui somente alterações confirmadas no servidor: resolva os rascunhos pendentes antes de exportar. A captura dos dados ocorre em uma única consulta no banco; uma imagem removida durante o download exige repetir a exportação.

Para restaurar, selecione o arquivo, confira a prévia e dê um nome à nova sala. A leitura, validação e verificação das imagens acontecem antes de criar qualquer sala ou enviar arquivos. O limite é de 100 MB por arquivo, 64 MB de imagens no total e 15 MB por imagem; até 50 fichas ativas, 500 fichas totais/itens, 2.000 tokens, 5.000 marcadores e 10.000 rolagens, com até 16 MB de dados sem imagens. Limites existentes de cada mapa continuam aplicáveis.

A restauração reserva **uma nova sala** com um novo convite, copia as imagens para caminhos próprios e grava o conjunto de dados em uma transação. Referências entre mapas, tokens, fichas e iniciativa recebem novos identificadores; recursos, artefatos, benefícios da Visão e duração restante dos efeitos são preservados. As fichas ficam com o mestre, que convida novamente os jogadores e transfere o controle pelo painel de administração. Tokens ligados a fichas arquivadas são desvinculados. Nomes históricos de autores de rolagens/marcadores permanecem como registro; as contas antigas, credenciais, convites e presença online não são importados.

Falhas no envio ou na resposta final podem ser retomadas com **o mesmo arquivo, nome, conta e sala de origem**, inclusive após recarregar o navegador. O identificador da tentativa fica no armazenamento local, e o servidor impede duplicar a sala ou os dados. A sala reservada pode existir vazia até a conclusão; não a edite nem convide jogadores enquanto a restauração estiver pendente. As imagens já enviadas são reutilizadas na próxima tentativa. Alterar o nome ou limpar o armazenamento do navegador inicia outra tentativa. O backup não muda nem sobrescreve a campanha original. Para importar em outra instalação/conta, primeiro crie uma sala vazia da qual você seja mestre e abra o painel nela.

Validação: `npm test` inclui PostgreSQL/PGlite com autorização do mestre, isolamento entre salas, transação/rollback, convite independente, imagens ausentes, reenvio idempotente, efeitos e vínculos; validação do arquivo inclui imagens ausentes/corrompidas/duplicadas e referências inválidas. `python tests/browser/room_backup.py` após o build cobre download, prévia, duas contas, falha no upload, perda de resposta após gravação, retomada na mesma sala e layout móvel. A configuração não adiciona consultas periódicas de backup à sala.
