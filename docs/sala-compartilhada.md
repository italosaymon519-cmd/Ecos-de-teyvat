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

Fichas, rolagens, combates e diário originais continuam no navegador. As notas do painel local do mestre também: não são automaticamente copiadas para o banco. Ao usar um registro local como base, somente seu nome é copiado; o mestre redige a descrição pública.

O backup JSON existente não inclui o acervo do Supabase. O mapa local em IndexedDB também continua separado. Para compartilhar o mapa é preciso enviá-lo no formulário da sala; ter a imagem no mapa local não faz upload automático.

## Permissões e limites desta versão

- O criador é o mestre, identificado pelo usuário autenticado no banco.
- Jogadores só leem itens revelados das salas em que participam. Não podem gravar, apresentar conteúdo nem ler rascunhos ou seus arquivos.
- Os links de imagem são assinados e expiram em 60 segundos; o bucket não é público.
- Conteúdo novo começa oculto. A opção Visualizar como jogador é uma prévia do mestre; não é o mecanismo de segurança. A segurança é aplicada no banco e no Storage.
- A sessão é mantida em sessionStorage da aba. Logout limpa imediatamente a sessão e a tela compartilhada. Se o pedido de revogação remota falhar, a interface informa o erro.
- Ainda não há expulsão de membros, rotação de convite, transferência de mestre, edição compartilhada de fichas ou backup/exportação de acervo. Compartilhe convites apenas com seu grupo.

## Desenvolvimento e validação

```sh
npm ci
npm test
npm run build
npm run preview
```

O preview serve somente `dist/`. Para um build conectado, forneça as duas variáveis públicas ao processo de build, conforme `.env.example`; o projeto não lê `.env` automaticamente. `npm start` continua servindo o desenvolvimento local com configuração de sala vazia.

Testes de navegador disponíveis em `tests/browser/shared_room.py` exigem Python Playwright e Chromium em `/usr/bin/chromium`. Exercitam duas contas e uma API simulada. As políticas SQL são testadas separadamente com PostgreSQL/PGlite, incluindo leitura de arquivos ocultos, alteração de papel, acesso fora da sala e convites.
