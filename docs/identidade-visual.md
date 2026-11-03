# Identidade visual — Ecos de Teyvat

Referência solicitada pelo autor: https://gi.yatta.moe/en (Project Amber / Yatta). Foram consultados a página pública, sua aparência em navegador, cores e catálogo público de imagens. A adaptação mantém a marca Ecos de Teyvat, suas regras e seus fluxos de jogo.

Direção: fundos roxos, superfícies em camadas, texto creme, destaques dourados, cartões de retrato e os sete ícones elementais. A abertura da campanha em Mondstadt recebe a arte de Jean e o cartão “Mondstadt: Blessing”. Não foram incorporados anúncios, rastreadores, código da aplicação ou dados de usuários do site de referência.

As imagens originais do jogo foram obtidas dos recursos públicos de Project Amber e são propriedade de seus respectivos titulares, incluindo HoYoverse. O uso nesta campanha de fãs não implica afiliação oficial. O rodapé inclui atribuição; a lista exata de recursos e URLs está em `assets/sources.json`.

Poppins é distribuída sob a SIL Open Font License; cópia incluída em `assets/OFL-Poppins.txt`. Imagens e fontes ficam no próprio deploy, sem dependência de requisições ao Yatta durante as sessões. O build copia a pasta `assets/` para `dist/`.

## Retratos

O retrato é opcional e cosmético. O jogador pode usar as iniciais ou uma referência visual entre Amber, Kaeya, Lisa, Jean, Barbara, Venti, Noelle e Collei. A escolha não altera povo, Visão, poderes ou estatísticas e não transfere a identidade do personagem oficial para a ficha. Fichas anteriores mantêm as iniciais até que um retrato seja escolhido.

## Validação

O teste `tests/browser/design.py` verifica carregamento de imagens e fontes, navegação dos atalhos, pesquisa por elemento, seleção de retrato e ausência de rolagem horizontal em celular/tablet. Os testes de fichas e sala compartilhada continuam cobrindo os fluxos de jogo; estilos do tabuleiro preservam posições e permissões dos tokens.
