# Automação local da Crescer Capital — primeira versão

Pacote para um computador dedicado. Usa Evolution API, n8n Community, PostgreSQL e Redis. A fila local controla revisão e histórico. As interfaces ficam acessíveis somente no próprio computador, sem abrir portas no roteador.

## O que está pronto

- Instalação por Docker Compose, com dados persistentes e credenciais aleatórias.
- Importação dos números candidatos encontrados na pesquisa de 27/10/2026. Nenhum contato entra aprovado ou autorizado.
- Revisão do número, registro de autorização, texto escrito por você e simulação.
- Recebimento de mensagens por webhook, eliminação de eventos repetidos, classificação conservadora e pausa para atendimento humano.
- Bloqueio de novos envios ao mesmo telefone após pedido de saída, mesmo quando o número aparece em mais de um CNPJ.
- Um fluxo n8n manual para simular o próximo contato. Nenhum agendamento ativo.

## Computador

No Windows, use Windows 10/11 de 64 bits compatível com o Docker Desktop e WSL 2. Sugestão prática: 8 GB de RAM como ponto de partida, preferencialmente 16 GB, espaço livre para as imagens e conexão estável. Esses valores são uma estimativa para este conjunto, não um requisito oficial do fabricante. O computador deve permanecer ligado e sem suspensão enquanto estiver atendendo.

O software do pacote não exige assinatura. Verifique a elegibilidade da empresa para o uso gratuito do Docker Desktop; a licença tem condições próprias. Internet, energia, manutenção e eventual hospedagem não estão incluídas. Não há serviço pago de inteligência artificial neste pacote.

## Instalação no Windows

1. Instale o Docker Desktop pelo site oficial, com o mecanismo WSL 2. Reinicie se solicitado e abra o Docker até ele ficar pronto.
2. Copie esta pasta inteira para uma pasta local do computador definitivo. Não execute de dentro do ZIP ou de uma pasta pública/compartilhada.
3. Abra um PowerShell nessa pasta. Execute `powershell -NoProfile -ExecutionPolicy Bypass -File .\Preparar.ps1`. A opção vale apenas para esse processo; não altera a política permanente.
4. Execute `powershell -NoProfile -ExecutionPolicy Bypass -File .\Iniciar.ps1`. A primeira execução baixa componentes e requer internet.
5. Execute `powershell -NoProfile -ExecutionPolicy Bypass -File .\Operar.ps1`. Confira os contatos e teste a simulação. Use um número interno autorizado antes de qualquer envio real.

O banco importa a pesquisa uma vez por par CNPJ/número; reiniciar não duplica os registros nem apaga revisões. Quando há vários números para a empresa, cada número é um candidato separado. Confira a fonte antes de escolher. A fila não é uma validação de conta ativa, titularidade ou autorização.

## Conectar o WhatsApp

Execute `Conectar-WhatsApp.ps1` somente no computador definitivo, com o número autorizado pela Crescer. Abra o arquivo `qr-whatsapp.png` gerado e use a opção Aparelhos conectados do WhatsApp. O QR expira e deve ser tratado como credencial. Apague a imagem depois do pareamento.

O conector Baileys é não oficial e pode desconectar, parar após atualizações ou causar restrição da conta. Não existe garantia de ausência de bloqueio. O texto natural da conversa não elimina esse risco.

## Automação n8n

Abra http://localhost:5678 e crie a conta local de administrador. Importe `n8n/Simular-contato.json`. Crie uma credencial do tipo Header Auth chamada **Crescer fila local**, com Name `X-Api-Key` e Value igual ao `ADMIN_KEY` do `.env`. Selecione essa credencial no nó HTTP e execute manualmente. Não compartilhe a chave ou o `.env`.

O fluxo chama `http://fila:8000/dispatch` na rede interna dos contêineres. A simulação não envia mensagem e não marca o contato como enviado; repetir pode apresentar o mesmo contato.

## Envio real — etapa posterior ao teste

O pacote começa com `LIVE_SEND_ENABLED=false`. O menu e o fluxo n8n fornecidos sempre pedem simulação. Portanto, alterar essa variável, isoladamente, não cria disparos.

Depois dos testes, o operador pode habilitar a variável, recriar o serviço fila e configurar um fluxo que envie `{"live":true}` para `/dispatch`. Cada chamada processa no máximo um contato revisado e autorizado; não há sequência automática de follow-up. Essa configuração deve ser feita com o responsável acompanhando o piloto. Não use a lista pública como prova de autorização.

Se a API retornar erro ou o resultado do envio for incerto, o telefone fica reservado com status UNKNOWN, sem repetição automática. Antes de qualquer intervenção, confira a conversa no WhatsApp. ACCEPTED significa que a API aceitou o pedido; não comprova entrega ou leitura.

## Respostas e atendimento

O menu mostra as últimas 100 mensagens. Toda mensagem recebida de uma conversa individual identificada por telefone pausa os contatos daquele número. Responda pelo WhatsApp; o sistema não responde automaticamente e não possui botão de retomar a conversa nesta versão. Classificações são sugestões por regras simples, sem IA: OPERA, OPERA_COM_BANCO, NAO_OPERA, INCONCLUSIVO, ATENDIMENTO_HUMANO ou OPT_OUT.

Áudio e outras mídias ficam indicados para revisão manual. Grupos, eventos de histórico e remetentes identificados apenas por LID são ignorados nesta versão; não há associação automática de LID a telefone. Isso deve ser conferido com mensagens reais antes de habilitar envios.

## Cuidados e manutenção

- Não exponha as portas à internet. n8n e os demais serviços usam HTTP local, sem proteção HTTPS externa.
- Guarde o `.env` de forma privada. Não o envie junto de capturas ou logs.
- Antes de atualizar ou transferir: pare os serviços, faça backup dos volumes Docker e guarde o `.env`. Copiar a pasta não copia os volumes nem conversas.
- `Parar.ps1` interrompe os serviços sem apagar os dados. Evite `docker compose down -v`, que apaga os volumes.
- Conserve os avisos e a atribuição de uso da Evolution API na documentação e interfaces aplicáveis.

## Validação desta entrega

Arquivos e regras são conferidos no computador de preparação. O Docker Engine estava parado nesse computador e o destino é outro PC: inicialização completa, conexão por QR, entrega de mensagens e webhooks reais precisam ser validados no destino. Nenhuma mensagem foi enviada durante a preparação.

## Fontes dos componentes

- Evolution API: https://github.com/evolution-foundation/evolution-api
- n8n: https://docs.n8n.io/hosting/
- Docker Desktop: https://docs.docker.com/desktop/setup/install/windows-install/
- Licença Docker Desktop: https://docs.docker.com/subscription/desktop-license/
