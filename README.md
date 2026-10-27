# Coletivo Respirartes · site oficial

Site do **Coletivo Respirartes**, Ponto de Cultura de Ji-Paraná (RO), reconhecido pela Política Nacional Cultura Viva (ID 13152755).

**No ar:** [respirartes.com](https://respirartes.com)

O site reúne a história do coletivo, os sete filmes produzidos em Ji-Paraná, as ações culturais com fotos, o certificado de Ponto de Cultura e um vídeo de apresentação de 2 minutos narrado por Carlos Reis.

Projeto desenvolvido como **projeto de extensão** do curso de Tecnólogo em Análise e Desenvolvimento de Sistemas da Universidade Anhembi Morumbi, por João Paulo Crestani Ferreira, em 2026.

## O que tem no site

| Seção | Conteúdo |
| --- | --- |
| Apresentação | Nome, lema e ficha do coletivo |
| Vídeo | Apresentação de 2 minutos, com download em 1080p |
| Filmes | Sete filmes com sinopse, créditos e link para o YouTube |
| Sobre e Trajetória | A história do coletivo, de 2014 aos projetos de 2027 |
| Certificado | Certificado do Ministério da Cultura, com link de conferência |
| Ações | Sete ações com 21 fotos ampliáveis |
| Onde ver | YouTube e Instagram do coletivo |

## Tecnologia

- HTML, CSS e JavaScript puros, sem framework e sem etapa de build
- Layout responsivo, pensado primeiro para o celular
- Tipografia Anybody, Newsreader e DM Mono (Google Fonts)
- Acessibilidade: textos alternativos em todas as imagens, navegação por teclado, respeito à preferência de reduzir animações
- SEO: metadados Open Graph, imagem de compartilhamento e dados estruturados (JSON-LD)
- Hospedagem na Vercel, com domínio próprio e HTTPS

## Estrutura

```
respirartes-site/
├── site/                     # tudo o que vai ao ar
│   ├── index.html            # a página
│   ├── img/                  # logo, cenas dos filmes, fotos das ações, certificado
│   ├── video/                # vídeo de apresentação e capa do player
│   └── certificado-ponto-de-cultura-respirartes.pdf
├── video-animacao/           # código que gera o vídeo de apresentação
├── docs/                     # roteiro de narração
├── .gitattributes            # vídeos guardados com Git LFS
└── .gitignore
```

## Rodar localmente

Não precisa instalar nada. Basta servir a pasta `site`:

```bash
cd site
python3 -m http.server 8000
```

Depois abra http://localhost:8000 no navegador.

## Publicar na Vercel

1. Na Vercel, crie um projeto importando este repositório.
2. Em **Root Directory**, escolha `site`.
3. Em **Framework Preset**, deixe **Other**, sem comando de build.
4. Em Settings › Git, ative **Git LFS** para os vídeos serem publicados.
5. Em Settings › Domains, adicione `respirartes.com` e `www.respirartes.com`.

A partir daí, cada `git push` na branch `main` publica o site automaticamente.

## Vídeos e Git LFS

Os arquivos `.mp4` passam de 50 MB, então ficam no [Git LFS](https://git-lfs.com). Antes de clonar, instale o Git LFS:

```bash
git lfs install
git clone https://github.com/<seu-usuario>/respirartes-site.git
```

## Créditos

- Conteúdo, filmes, fotos e certificado: Coletivo Respirartes
- Narração do vídeo: Carlos Reis, presidente do coletivo
- Desenvolvimento, textos e vídeo: João Paulo Crestani Ferreira

Os textos, as imagens e os filmes pertencem ao Coletivo Respirartes e não podem ser reutilizados sem autorização. O código pode ser consultado como referência.
