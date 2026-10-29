# Contexto do projeto Agente Whats

## Objetivo

Projeto de pesquisa de WhatsApp comercial e automação local para a Crescer Capital.
O pacote atual utiliza Evolution API, n8n Community, PostgreSQL e Redis, com uma fila de revisão de contatos.

## Arquivos principais

- `automacao-local/LEIA-ME.md`: instalação, operação, limites e estado da validação.
- `automacao-local/compose.yaml`: serviços Docker.
- `automacao-local/fila/`: aplicação e regras de atendimento.
- `automacao-local/*.ps1`: preparação, inicialização, operação e conexão do WhatsApp.
- `pesquisar_whatsapp.py` e `verificar_fontes.py`: pesquisa e verificação de fontes.
- `montar_resultado.mjs`: geração da planilha de resultados.

## Estado documentado

O LEIA-ME informa que a inicialização completa, conexão por QR e webhooks reais ainda precisam ser validados no computador definitivo. Não presumir que esses testes passaram.
O pacote começa com envio real desabilitado. Contatos precisam de revisão e autorização; números públicos não comprovam permissão para envio.

## Continuidade em outro computador

Em 29/10/2026, o usuário pediu para usar Git para continuar o projeto em outro PC.
O Git transporta os arquivos versionados e este contexto; não transporta automaticamente o histórico das conversas do Codex.
Este documento resume o que foi identificado nos arquivos existentes; não é uma transcrição de conversas anteriores.

1. Clone o repositório no outro computador e abra a pasta no Codex.
2. Peça ao Codex para ler este documento e `automacao-local/LEIA-ME.md` antes de trabalhar.
3. Transfira separadamente as planilhas, os resultados de pesquisa e `automacao-local/dados/contatos.json` se necessários.
4. Para uma instalação nova, siga o LEIA-ME para gerar credenciais locais. Para migrar uma instalação já usada, siga as instruções de backup dos volumes e do `.env`; Git não inclui esses dados.

## Fora do Git

Credenciais, QR de conexão, arquivos `.env` (exceto exemplos), dependências, backups, planilhas, resultados e contatos locais são ignorados.
O script `montar_resultado.mjs` depende de `@oai/artifact-tool`, disponibilizado no ambiente original; essa dependência precisará estar disponível para executá-lo em outro PC.

## Atualização

Atualize este documento com decisões e próximos passos relevantes ao concluir mudanças. Nunca inclua senhas ou chaves.
