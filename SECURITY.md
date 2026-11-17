# Segurança

## Princípios

- A ARCA funciona offline; nenhuma função essencial envia dados para fora.
- Integrações online (GPT, Claude, Gemini, downloads, atualizações) vêm desligadas e passam pelo guarda de rede do motor.
- Chaves de API ficam no Cofre do Windows (Credential Manager), nunca em arquivos do repositório.
- Documentos pessoais só são enviados a serviços externos com confirmação explícita, item a item.
- Módulos declaram permissões em manifesto; nenhuma permissão é concedida implicitamente.

## Reportar uma vulnerabilidade

Abra uma issue **sem detalhes exploráveis** pedindo contato, ou use o recurso "Report a vulnerability" (Security Advisories) do GitHub neste repositório.

Detalhes do modelo de ameaças: [`docs/seguranca/MODELO-DE-AMEACAS.md`](docs/seguranca/MODELO-DE-AMEACAS.md).
