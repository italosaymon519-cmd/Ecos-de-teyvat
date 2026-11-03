# Ecos de Teyvat

Mesa de RPG em português, com fichas, PV, EE, recargas, reações elementais, dados e diário.

Requer Node.js 22 ou superior. Sem dependências de runtime. Os testes de permissões usam PostgreSQL/PGlite como dependência de desenvolvimento.

```sh
npm ci
npm start
npm test
```

Servidor na porta 3000, configurável por `PORT`. O progresso fica no localStorage do navegador. Exporte regularmente uma cópia JSON; a importação substitui a campanha local após confirmação. As fichas e o diário originais são locais. Contas e sala compartilhada ficam disponíveis após conectar o Supabase, conforme as instruções abaixo.

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

A opção Combate da sala mostra a ordem de jogadores e inimigos, turno atual e rodada. O mestre pode importar tokens ou fichas locais, rolar/ajustar iniciativas e avançar a fila. Aplique [003-combat-initiative.sql](supabase/003-combat-initiative.sql) para persistir o controle compartilhado; o encontro local permanece disponível.

### Limites de criação e reações

A ficha permite no máximo duas perícias treinadas e dois talentos, conforme a criação dos guias. A interface bloqueia uma terceira opção e valida novamente ao salvar e importar. Fichas locais antigas com excesso continuam preservadas, mas precisam ser corrigidas antes de salvar. Não foi inventada progressão adicional de escolhas, pois os guias ainda não a definem.

A reação mostra preparação e resultado no próprio painel. Prepare a marca do primeiro personagem e selecione o segundo. A reação consome a marca e dá 1 EE a cada participante, até 3; dano, escudos e condições continuam manuais. O fluxo usa as fichas locais deste navegador e explica quando faltam dois participantes. As combinações de Anemo/Geo com elementos compatíveis aceitam ambas as ordens descritas na tabela.
