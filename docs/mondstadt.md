# Mondstadt — preparação da campanha

## Referências consultadas

- Mapa oficial HoYoLAB: https://act.hoyolab.com/ys/app/interactive-map/index.html — acessível em 3 de novembro de 2026.
- Catálogo oficial de marcadores: https://sg-public-api.hoyolab.com/common/map_user/ys_obc/v1/map/label/tree?app_sn=ys_obc&lang=pt-pt&map_id=2 — resposta OK; categorias como Estátuas dos Sete, teleportes, domínios e Anemoculus. Este endpoint não fornece uma descrição narrativa de cada cenário.
- Páginas Mondstadt, Whispering Woods, Thousand Winds Temple e Dadaupa Gorge na wiki Genshin Impact Fandom — acesso retornou HTTP 402; não usadas como evidência de conteúdo recuperado.

As descrições geográficas resumem locais conhecidos do jogo e não constituem transcrição verificada de textos do mapa. Nomes em inglês permitem localizar variantes de tradução no mapa oficial. Não foram inferidas distâncias, tempos de viagem ou estado político atual. A época da campanha precisa ser escolhida pelo mestre.

## Conteúdo original

Ecos sob os Mil Ventos, Mira, Elian, Sera, desaparecimento da carga, peça elemental, pistas e missões são propostas originais para o RPG. Não são missões oficiais de Genshin Impact. Nenhuma arte do jogo foi copiada.

## Recursos do mestre

Cenários pesquisáveis; criação de cenas, NPCs e missões; notas editáveis; estados de cenas e missões; iniciativa e turnos de encontro; PV e condições manuais; exportação/importação JSON separada. Preparar a abertura repetidamente não duplica seus registros iniciais.

O painel usa a chave localStorage `ecos-gm-v1`, sem migrar ou apagar fichas na chave `ecos-teyvat-v1`. O JSON da campanha não inclui o painel: exportar o backup do mestre separadamente. Sem autenticação: o painel não é um cofre privado e não deve ser mostrado aos jogadores com segredos abertos. Os dados não sincronizam entre dispositivos.

O encontro do mestre tem rodadas independentes da mesa de aventura. A interface explicita que expiração de marcas e recarga de E ainda são avançadas na mesa de aventura. PV, iniciativa e condições não possuem estatísticas de monstros oficiais nem balanceamento automático.
