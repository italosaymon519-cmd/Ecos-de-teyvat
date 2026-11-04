# Ativar contas e sala compartilhada

O código está preparado para Supabase Auth, banco PostgreSQL com RLS e armazenamento privado. Ainda é necessário criar e conectar um projeto real. A publicação do frontend, sozinha, não cria o banco nem contas.

## 1. Criar o projeto Supabase

1. Abra https://supabase.com/dashboard e entre ou crie sua conta.
2. Crie um projeto em sua organização, com o nome que preferir (por exemplo, Ecos de Teyvat).
3. Defina e guarde a senha do banco no seu gerenciador de senhas. Não envie a senha no chat e não a coloque no site.
4. Aguarde o projeto ficar disponível.

## 2. Preparar banco e imagens

Abra SQL Editor → New query. Copie o conteúdo completo de [`supabase/setup.sql`](../supabase/setup.sql) e execute uma vez.

O script cria salas, participantes, acervo e o bucket privado `campaign-images` com políticas de acesso. Execute em um projeto novo dedicado à campanha; não desative RLS. Ele é transacional: uma falha desfaz as alterações dessa execução. Após sucesso, não execute novamente como se fosse uma migração incremental.

As contas e armazenamento são os serviços normais do Supabase. O teste local usa funções de autenticação e tabelas de Storage simplificadas no PostgreSQL/PGlite; a integração com um projeto Supabase hospedado ainda precisa ser verificada depois desta configuração.

## 3. Autorizar os links de e-mail

Em Authentication → URL Configuration:

- Site URL: `https://comfy-jalebi-598a6d.netlify.app`
- Redirect URLs: `https://comfy-jalebi-598a6d.netlify.app/`

Mantenha confirmação de e-mail habilitada. As contas são de cada jogador; não crie uma senha comum para o grupo. Os e-mails padrão do Supabase têm limites de envio; caso eles impeçam os convites/testes, configure o serviço SMTP suportado no Supabase. Não desabilite confirmação só para contornar um erro de envio.

## 4. Conectar ao site no Netlify

No Supabase, obtenha a **Project URL** e a chave **publishable** (ou a chave legada **anon**). A chave publishable costuma começar com `sb_publishable_`. Essas duas informações são públicas e serão incluídas no código do navegador. A proteção dos dados vem da autenticação e das políticas RLS.

No projeto **comfy-jalebi-598a6d** do Netlify, abra Project configuration → Environment variables e adicione, para o build de produção:

| Variável | Valor |
| --- | --- |
| `PUBLIC_SUPABASE_URL` | URL HTTPS do seu projeto, sem caminho adicional |
| `PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Chave publishable ou anon pública |

**Nunca use** `service_role`, `sb_secret_`, senha do banco ou chave secreta nessas variáveis. O build recusa chaves de serviço reconhecidas. Não é necessário fornecer nenhum segredo do banco ao navegador ou ao Codex.

Após salvar, faça um novo deploy em Deploys → Trigger deploy. Alterar variável não substitui um build que já terminou. Somente as duas configurações públicas são necessárias; nenhum servidor adicional roda no Netlify.

## 5. Primeiro uso e verificação real

1. Abra Sala compartilhada, crie sua conta, confirme o e-mail e entre.
2. Crie a sala como mestre, informe o nome da campanha e seu nome na mesa.
3. Use Copiar convite e envie aos participantes. Somente o mestre pode consultar o código no banco.
4. Cada jogador cria/confirma sua própria conta e entra pelo convite. O convite concede papel de jogador, nunca de mestre.
5. Como mestre, salve um conteúdo ainda oculto; em outra conta, confirme que ele não aparece.
6. Envie o mapa original em PNG, JPG ou WebP de até 15 MB. Dê um nome e salve.
7. Clique em **Apresentar a todos**. O mapa deve aparecer na segunda conta após até cinco segundos; o zoom é individual.
8. Faça o mesmo com cenas e NPCs. Eles podem ter descrição e imagem. **Revelar** disponibiliza no acervo; **Apresentar** também coloca em destaque.
9. Oculte novamente e confira que a outra conta deixa de ver o conteúdo. Uma imagem já entregue pode continuar acessível pelo link assinado por até 60 segundos. Nenhum sistema consegue apagar uma imagem já baixada ou capturada por um participante.
10. Saia da conta e confirme que o acervo compartilhado é removido da tela.

Até concluir esse teste com o projeto real, não considerar contas, e-mail e armazenamento hospedados validados em produção.

## O que é compartilhado

- Salas e nomes dos participantes.
- Mapas, cenas e NPCs salvos no acervo, conforme visibilidade definida pelo mestre.
- Um conteúdo apresentado por sala, com atualização automática a cada cinco segundos enquanto o navegador está visível.

Não há WebSocket nesta versão: a sincronização usa consultas periódicas e indicação do horário da última atualização. Sem conexão, o painel informa que os dados podem estar desatualizados.

## O que continua local

As fichas da mesa local, rolagens fora de sala e diário continuam no navegador. A atualização 005 compartilha as rolagens feitas na sala. As fichas da sala e sua iniciativa são salvas no banco após as atualizações 003 e 004. As notas do painel local do mestre também: não são automaticamente copiadas para o banco. Ao usar um registro local como base, somente seu nome é copiado; o mestre redige a descrição pública.

O backup JSON existente não inclui o acervo do Supabase. O mapa local em IndexedDB também continua separado. Para compartilhar o mapa é preciso enviá-lo no formulário da sala; ter a imagem no mapa local não faz upload automático.

## Permissões e limites desta versão

- O criador é o mestre, identificado pelo usuário autenticado no banco.
- Jogadores só leem itens revelados das salas em que participam. Não podem gravar, apresentar conteúdo nem ler rascunhos ou seus arquivos.
- Os links de imagem são assinados e expiram em 60 segundos; o bucket não é público.
- Conteúdo novo começa oculto. A opção Visualizar como jogador é uma prévia do mestre; não é o mecanismo de segurança. A segurança é aplicada no banco e no Storage.
- A sessão é mantida em sessionStorage da aba. Logout limpa imediatamente a sessão e a tela compartilhada. Se o pedido de revogação remota falhar, a interface informa o erro.
- Ainda não há expulsão de membros, rotação de convite, transferência de mestre ou backup/exportação de acervo. Compartilhe convites apenas com seu grupo.

## Desenvolvimento e validação

```sh
npm ci
npm test
npm run build
npm run preview
```

O preview serve somente `dist/`. Para um build conectado, forneça as duas variáveis públicas ao processo de build, conforme `.env.example`; o projeto não lê `.env` automaticamente. `npm start` continua servindo o desenvolvimento local com configuração de sala vazia.

Testes de navegador disponíveis em `tests/browser/shared_room.py` exigem Python Playwright e Chromium em `/usr/bin/chromium`. Exercitam duas contas e uma API simulada. As políticas SQL são testadas separadamente com PostgreSQL/PGlite, incluindo leitura de arquivos ocultos, alteração de papel, acesso fora da sala e convites.

## Tabuleiro compartilhado com tokens

Depois da configuração inicial, execute **somente** [`supabase/002-map-tokens.sql`](../supabase/002-map-tokens.sql) em uma nova consulta no SQL Editor do Supabase. Não execute o script inicial novamente. Essa migração adiciona tokens e suas permissões sem apagar salas, mapas ou participantes. Ela pode ser repetida preservando os tokens existentes.

Na sala, apresente um conteúdo do tipo **Mapa**, com uma imagem. Clique em **Atualizar agora** após aplicar a migração. A área **Tokens do tabuleiro** aparece para o mestre:

1. Informe nome, tipo, cor e tamanho do token.
2. Para um personagem, escolha o membro que poderá movê-lo; jogadores precisam entrar na sala antes de serem atribuídos. Inimigos e aliados são movidos pelo mestre.
3. Clique em **Colocar no mapa**. Tokens novos recebem um pequeno deslocamento para evitar sobreposição inicial.
4. Arraste os tokens ou use as setas do teclado quando estiverem focados. As posições são salvas como porcentagens do mapa, mantendo a referência entre telas e níveis de zoom.
5. Outros participantes recebem as posições a cada dois segundos. Uma falha no salvamento restaura a posição anterior e informa o erro.

As permissões são aplicadas no banco: somente o mestre cria/remove tokens; o jogador só pode alterar as coordenadas de personagens atribuídos a ele em mapas revelados. Não pode mudar dono, nome ou posição de inimigos. Tokens de mapas ocultos não são consultáveis por jogadores.

O mapa suporta arraste com zoom, Ctrl/Command + rolagem e tela cheia. Em celulares, use os botões de zoom e deslize o mapa; tokens atribuídos podem ser arrastados com o dedo. Não há contagem automática de movimento, colisão, visão de parede ou neblina de guerra nesta versão. Todos os tokens de um mapa revelado são visíveis.

Também foram adicionados busca por nome/descrição, filtros de visibilidade, miniaturas, prévia de upload, remoção de imagem ao editar, salvar e apresentar em um passo e retorno à apresentação do mestre depois de uma prévia individual. A última sala é lembrada por usuário neste navegador.

## Ordem de iniciativa e turnos compartilhados

Execute [`supabase/003-combat-initiative.sql`](../supabase/003-combat-initiative.sql) em uma nova consulta no SQL Editor. Essa atualização é independente da migração de tokens e pode ser repetida sem apagar combates. Não execute o setup inicial novamente.

Na Sala compartilhada, clique em **Combate** ou localize **Ordem de iniciativa** junto ao mapa. O mestre escolhe **Preparar combate**, importa os tokens do mapa apresentado ou as fichas da mesa selecionada e pode adicionar participantes manualmente. Os tokens sem ficha vinculada não fornecem atributos: informe seu bônus de Agilidade. Tokens vinculados usam o atributo da ficha com a atualização 005. A importação de fichas usa a Agilidade registrada.

O botão **Rolar iniciativas** aplica 1d20 + bônus a cada participante. Alternativamente, digite o resultado total. Ao iniciar, o maior total age primeiro. Empates preservam a sequência de preparação, uma convenção explícita desta versão que a mesa pode ajustar alterando os totais.

Todos os membros veem a ordem e o turno atual, atualizados a cada dois segundos. Somente o mestre inicia/encerra, avança ou retira/reativa participantes. Uma volta completa incrementa a rodada. Participantes retirados são ignorados; se todos forem retirados, o combate encerra. Reativar alguém não interrompe o turno atual.

A rodada compartilhada passa a controlar a Mesa de aventura neste navegador: início de um novo combate zera EE e marcas e libera E, preservando PV e limites de Q por descanso; a próxima rodada expira marcas e atualiza a referência da recarga de E. Fichas continuam locais. Abrir novamente o mesmo combate não repete o reset. Dois mestres/abas tentando alterar a mesma versão recebem um aviso de conflito, evitando sobrescrita silenciosa.

Fora de uma sala, **Novo combate** prepara a ordem no Painel do mestre com fichas locais e participantes já cadastrados. Os totais podem ser ajustados, e a rodada do encontro local atualiza a Mesa de aventura. Esses registros não são enviados à sala automaticamente.

A persistência do combate usa `campaign_combats`, com leitura restrita a membros e escrita através de função autenticada do mestre. Não há dados privados do painel do mestre nessa tabela. O teste de políticas verifica permissões, conflitos de versão e rejeição de turnos inválidos em PostgreSQL/PGlite; o teste de navegador exercita dois clientes com API simulada.


## Fichas persistentes e quem está online (atualização 004)

No mesmo SQL Editor, abra uma consulta nova, cole o conteúdo completo de [004-campaign-sheets-presence.sql](../supabase/004-campaign-sheets-presence.sql) e clique em **Run**. Não apague tabelas nem execute novamente o setup inicial. A atualização 004 pode ser executada de novo sem apagar fichas, salas, mapas ou tokens. Depois, atualize o site com Ctrl + F5 e entre na sala.

Use **Abrir fichas da campanha** para consultar, criar ou editar. As alterações são salvas automaticamente; aguarde **Todas as fichas salvas na campanha** antes de fechar. Em outro computador, entre com a mesma conta e escolha a mesma sala. Para trazer uma ficha antiga, abra **Trazer uma ficha que já existe neste navegador**, selecione-a e use **Copiar ficha local para esta campanha**. Cada jogador deve fazer isso com sua própria conta. A original permanece local.

As fichas são visíveis aos membros da campanha; somente o dono e o mestre podem alterá-las. PV, EE, recursos, perícias, talentos e usos dos artefatos/Visão ficam persistidos. As fichas de outras campanhas não aparecem na mesa atual. Diários, notas e histórico de rolagem permanecem no navegador. Os tokens continuam sendo posicionados e atribuídos separadamente.

A lista de participantes indica **Online** ou **Offline**. Outra aba ou dispositivo da mesma pessoa não duplica o participante. O logout remove a sessão correspondente; ao fechar sem sair ou perder internet, a presença expira em até 90 segundos. Se o servidor não responder, o site informa que a presença está indisponível.

Uma edição sem conexão fica como rascunho neste navegador e tenta novamente ao reconectar. Quando duas sessões alteram o mesmo campo, o site preserva o rascunho e permite escolher entre a versão da mesa e a própria versão, além de baixar o rascunho. Não limpe o armazenamento enquanto houver alterações pendentes.


## Rolagens para todos e fichas nos tokens (005)

1. Copie todo o [SQL 005](../supabase/005-shared-rolls-token-sheets.sql) para uma consulta nova no SQL Editor e clique em Run. Execute após as atualizações 002 e 004, preservando as tabelas existentes.
2. Atualize o site com Ctrl + F5, entre na conta e escolha a campanha. Role pela Mesa ou pela ficha: o histórico da sala mostra o nick, o personagem, o resultado e o cálculo. A Mesa também mostra as três últimas rolagens. Aguarde o envio antes de fechar; os resultados pendentes podem ser reenviados sem duplicação.
3. Como mestre, selecione uma **Ficha vinculada** ao colocar um token, ou use **Vincular ficha** na lista de tokens existentes. Os PV, nome e condições acompanham as alterações da ficha. Cada jogador pode editar suas condições no campo **Condições atuais** da ficha.
4. Para trocar ou remover a ligação, use **Trocar ficha**. O controle de um token Personagem acompanha o dono da ficha; inimigos e aliados são controlados pelo mestre. Desvincular devolve o controle ao mestre.

As condições são anotações manuais, sem aplicação automática de efeitos ou contagem de rodadas. As rolagens são calculadas pelo navegador e registradas com autoria confirmada pela conta; o histórico não valida a aleatoriedade de um cliente modificado. A janela mostra até 100 resultados recentes, com 50 ao entrar; os registros anteriores continuam no banco.
