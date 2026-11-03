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

A marca preparada agora corresponde obrigatoriamente à Visão cadastrada. Os seletores mostram somente esse elemento, a reação valida a correspondência e marcas antigas incompatíveis são limpas ao carregar/importar ou trocar a Visão. As reações possíveis continuam sendo determinadas pela combinação dos elementos dos dois participantes.

### Testes de perícia pela ficha

Em Personagens, abra **Rolar perícias pela ficha**, ou use **Rolar perícia** no cartão da Mesa. Cada um dos 18 testes mostra o bônus pronto e oferece normal, vantagem ou desvantagem. O cálculo usa d20 + atributo e, somente se a perícia estiver treinada, proficiência de nível (+2 em 1–4; +3 em 5–8; +4 em 9–12; +5 em 13–16; +6 em 17–20). Fichas anteriores assumem nível 1 até edição. Não há soma automática de especialização, artefatos ou bônus narrativos não selecionados.

O resultado identifica o jogador (nick da sala/local, ou nome do personagem como alternativa), o personagem, os dados e cada parcela do cálculo. O resultado também entra no histórico local. Os limites de duas perícias e dois talentos permanecem. Um 20 ou 1 natural no teste de perícia não aplica automaticamente as regras exclusivas de ataques.

### Benefícios defensivos das Visões

A Mesa e a ficha exibem o benefício da Visão com um uso por combate. Geo rola 1d6 de escudo; Hydro recupera até 2 PV após confirmação de resistência bem-sucedida; Electro acrescenta +2 à Defesa até o próximo ataque registrado, inclusive um erro com dano zero. Pyro reserva redução de 2 para dano de ataque; Cryo reserva redução de 2 para dano de inimigo afetado por Cryo. Dendro reserva +2 para o teste contra condição prejudicial na opção Teste de resistência.

Ao registrar dano, informe se veio de ataque e se o inimigo está afetado por Cryo. A redução aplicável é calculada antes da absorção do escudo, e só o restante reduz PV. O limite de uso não volta com descanso nem com a próxima rodada: apenas no início de um novo combate. Trocar de Visão remove efeitos incompatíveis e preserva o uso já gasto.

Anemo registra o reposicionamento reativo de 3 m, sem ataques de oportunidade; a posição do token continua sendo ajustada manualmente porque o mapa não possui escala em metros. Use Concluir deslocamento para resolver o aviso. Gatilhos narrativos (ter resistido, ter sido atacado, ter acertado Electro) são confirmados pelo jogador/mestre, não inferidos de uma rolagem sem CD. Essas alterações continuam nas fichas locais; não enviam PV ou efeitos ao banco da sala.
