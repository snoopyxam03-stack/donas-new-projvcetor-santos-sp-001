# PRD — Portal Concurso Público PMVR (Volta Redonda/RJ)

## Original Problem Statement
Clonar repo GitHub carlinnoa874-blip/meuprojectorsalvar-pp-riograndedonorte-002 no Emergent, apagar o site público antigo mantendo o painel `/donaspainel`, e construir do zero um novo site público para o Concurso Público da Prefeitura de Volta Redonda / RJ – Secretaria Municipal de Saúde – Edital Nº 003/2026-SMA, integrado com o painel administrativo existente.

## Stack
- **Backend**: FastAPI (`/app/backend/server.py` + `admin_routes.py` + `pix_generator.py`)
- **Frontend público**: HTML estático (SingleFile do PortalVR) servido por craco dev server + rota React CRA placeholder
- **Painel admin**: bundle React (`/donaspainel/*`) + integração Telegram + PIX + tracking
- **DB**: MongoDB local (`mongodb://localhost:27017`, DB `test_database`)

## Fluxo Público Implementado (26–27/Jul/2026)
1. **`/` (home)** — SingleFile HTML do PortalVR, mobile responsivo real, modal "Aviso importante" + botão FAZER MINHA INSCRIÇÃO + 10 PDFs (Edital + 4 documentos + 5 Leis)
2. **`/inscricao`** — Formulário com máscaras CPF/data/celular/CEP + ViaCEP autofill + upload frente/verso do documento (RG/CNH/Passaporte) + seletor de vaga (EF004 R$100 / TE005 R$80) + validação em tempo real + botão CADASTRAR só habilita quando tudo válido
3. **`/confirmacao`** — Revisão dos dados abreviados (label uppercase + valor) + protocolo PMVR-XXXXXX-YYY gerado e persistido em sessionStorage + botões ALTERAR DADOS / CONFIRMAR INSCRIÇÃO + modal "Inscrição realizada com sucesso!" (5s auto-redirect ou clique OK)
4. **`/inscricao-realizada`** — Nº Inscrição, Nome, CPF, Vaga, Status "PENDENTE DE PAGAMENTO" + botão PAGAR INSCRIÇÃO
5. **`/pagamento-pix`** — Loading 2s + QR Code (`/api/pix/generate` com chave PIX atual do painel) + textarea copia-e-cola + botões COPIAR CÓDIGO / IMPRIMIR PAGAMENTO / ← VOLTAR + aviso "24h para efetivar"

## Integração Público → Painel
- `/api/track/access` no page-load de cada página
- `/api/track/registration` (stage=cadastro) no submit da /inscricao
- `/api/track/documents` (base64 frente + verso) no submit da /inscricao
- `/api/track/registration` (stage=inscricao_finalizada, finalized=true, protocolo, cargo_codigo, cargo_titulo, taxa, valor) no Confirmar Inscrição
- `/api/track/pix-generated` ao renderizar QR
- `/api/track/pix-copied` ao clicar Copiar
- `/api/track/pix-downloaded` ao clicar Imprimir

## Notificações Telegram
- Bot Token + Chat ID configurados nas settings do painel
- Título: "NOVA INSCRIÇÃO - VOLTA REDONDA"
- **Uma mensagem por candidato**, editada conforme progressão (mesmo message_id)
- Emojis de status: 🟡 Aguardando pagamento → 🔵 PIX gerado → 🟠 PIX copiado → 🟢 PIX baixado
- Payload: 👤 Nome, 🔐 CPF, 📅 Data/hora, 📱 Dispositivo, 📍 Local (geo IP), 💰 Valor, 📊 Status

## Branding do Painel Admin
- Título HTML: "Painel — Inscrição Volta Redonda"
- Sidebar/brand: "Inscrição Volta Redonda"
- Subtítulo login: "INSCRIÇÃO PMVR SMA 003/2026"
- Zero ocorrência de "Polícia Penal RN" restante no bundle

## Mobile Responsivo (iOS + Android)
- Viewport `width=device-width, initial-scale=1`
- Menu escondido no mobile (`display:none`)
- CSS overrides em `@media (max-width: 900px)` em todas as 5 páginas
- Labels uppercase pequeno + valor logo abaixo (compact)
- Botões pill full-width (44-52px altura, tap-friendly)
- Formulário: campos em bloco full-width, máscaras como placeholder
- Zero overflow horizontal em qualquer página
- Modal "Aviso importante" responsivo

## Desktop (bug fixed)
- Menu volta a 1 linha só (Área Restrita | Concursos Públicos | Processos Seletivos | Contato)
- `box-sizing:border-box` removido do `#main-transparent` para não comprimir o espaço interno

## Limpeza para Deploy VPS
- `.env` de frontend + backend agora em `.gitignore` (não vai pro Git)
- `.env.example` criado em ambos com placeholders
- 13 arquivos `/app/tests/*.py` limpos (URL preview substituída por `BASE_URL` env var)
- test_reports antigos com URL preview removidos
- memory/PRD.md + test_credentials.md limpos (URL preview → "SEU-DOMINIO")
- Todos os HTMLs públicos usam `window.location.origin` (sem hardcoded)
- Backend usa apenas env vars

## Credenciais
- Admin: `farpa` / `Ads102030`
- Painel: `/donaspainel/`

## Configurações a preencher no painel (após deploy)
- Chave PIX (chave, nome, cidade)
- Bot Token + Chat ID Telegram
- Título Telegram (default: "NOVA INSCRIÇÃO - VOLTA REDONDA")

## URLs (Preview atual — muda no VPS)
- Público: https://SEU-DOMINIO/
- Painel: https://SEU-DOMINIO/donaspainel/
- API: https://SEU-DOMINIO/api/
