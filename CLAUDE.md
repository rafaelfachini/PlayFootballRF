# Play Football RF — padrão do canal

## Identidade visual (obrigatória em toda animação)
- Cores: **marrom escuro** (predominante; é o piso de uma quadra de futsal marrom escura), **preto** e **branco**.
  Tokens em `mg/common.js` (`C.brown #3a2215`, `C.brownDeep`, `C.brownMid`, `C.brownLight`, `C.black #0a0908`, `C.white #f6f2ea`).
- Fontes: Anton (títulos e números), Bebas Neue (rótulos espaçados), Archivo Black (reserva). Arquivos em `mg/fonts/`.

## Motion graphics: padrão = Modelo A + Modelo B intercalados
- **Modelo A — "Quadra"** (`mg/styleA.html`): fundo de parquet marrom com as linhas da quadra se desenhando em branco,
  "#N" gigante vazado, texto subindo por máscara, barra preta com contador, carimbo "NO PAPEL", wipe preto diagonal.
- **Modelo B — "Placar"** (`mg/styleB.html`): painel de LED branco sobre preto com moldura de madeira marrom,
  números em odômetro, barras segmentadas, faixa de texto correndo, placar "PROMESSA × REALIDADE".
- Intercalar: alterne A e B ao longo do vídeo (por exemplo, títulos de seção em A e dados/placares em B), sem repetir
  o mesmo estilo mais de duas vezes seguidas.
- O Modelo C ("Recorte") foi descartado.
- Renderização: `node scripts/render_mg.js <pagina.html> <saida.mp4> 30` (1920x1080, 30 fps). Página dos cards do vídeo: `mg/cards.html#<json>`.

## Composição dos vídeos
- ~75% clipes do YouTube sem transmissão (torcedores, vlogs, imagens do local), ~15% fotos (Wikimedia Commons / prints de
  posts oficiais), ~10% motion graphics. As imagens devem corresponder à fala; use o Whisper para alinhar (`scripts/transcribe.py`).
- Imagens da FIFA (finais, Copa Árabe, Intercontinental): no máximo 3 a 5 s por clipe, em câmera lenta e com gráfico por cima.
- Guerras e conflitos: só em texto ou card, nunca imagens de míssil ou explosão.
- Música: Biblioteca de Áudio do YouTube.
- Roteiros: os áudios recebidos já estão verificados; se o roteiro tiver trechos que não estão no áudio, siga o áudio.
- Créditos das fotos do Commons: `images/credits.jsonl` (vão para a descrição do vídeo).
