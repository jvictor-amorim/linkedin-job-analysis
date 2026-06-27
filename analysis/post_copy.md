# Carrossel LinkedIn — Skills × Senioridade no mercado de Dados (BR)

Imagens em `output/carousel/` (1080×1350 px, ordem 01 → 09). Suba na ordem do nome
do arquivo. Abaixo, a legenda do post e o texto que aparece em cada slide.

---

## Legenda do post (copiar/colar)

Analisei **1.011 vagas de Dados publicadas no LinkedIn** para responder uma pergunta
simples: **o que muda nas skills exigidas conforme você sobe de júnior para sênior?**

3 coisas me chamaram atenção:

🔹 **SQL e Python são inegociáveis** — lideram o ranking em TODOS os níveis. Se você
está começando, é por aqui.

🔹 **O júnior vive de visualização; o sênior, de engenharia.** Júnior puxa Power BI,
Excel e dashboards. Sênior puxa Data Pipelines, ETL, AWS e Databricks. A skill que mais
cresce de júnior → sênior é **construir pipelines de dados (+50 pontos percentuais)**.

🔹 **Governança de dados é divisor de águas.** Quase some nas vagas júnior e aparece em
metade das vagas sênior. É o tipo de skill que diferencia quem está subindo.

E não é só técnica: **autonomia, trabalho em equipe e liderança** aparecem cada vez mais
conforme a senioridade.

Os dados, a metodologia e as ressalvas estão no último slide. 👇

Qual dessas skills te surpreendeu? Comenta aí 👇

\#dados #dataanalytics #engenhariadedados #carreiraemdados #powerbi #python #sql #dataengineering

---

## Texto por slide (já embutido nas imagens — referência)

1. **Capa** — "O que o mercado de Dados pede em cada senioridade?" · 1.011 vagas (LinkedIn BR).
2. **A amostra** — Distribuição das vagas por nível. ⚠ 52% não declaram o nível no título e
   ficam fora da comparação júnior/pleno/sênior.
3. **Top 10 — Júnior** — SQL (70%), Power BI (61%), Dashboards (57%), Python (56%), Excel (43%)…
4. **Top 10 — Pleno** — transição: começa a entrar pipeline/ETL/cloud.
5. **Top 10 — Sênior** — SQL (76%), Data Pipelines (74%), Python (68%), Data Governance (48%)…
6. **Sempre no top 10** — SQL, Python, Data Pipelines, ETL, Data Modeling aparecem nos 3 níveis.
7. **A virada** — maior salto júnior→sênior: Data Pipelines +50pp, Governance +33pp, AWS +31pp.
8. **Soft skills** — autonomia, trabalho em equipe e liderança crescem com a senioridade.
9. **Conclusão + metodologia + CTA**.

---

## Dicas de publicação
- LinkedIn favorece **imagens nativas** (não link externo). Publique como post de múltiplas
  imagens, na ordem 01→09.
- Alternativa: exportar os PNGs como um único PDF e publicar como **documento** (também
  vira carrossel no feed).
- Primeira hora é decisiva: responda os comentários rápido para alavancar o alcance.
- O texto da legenda já entrega o "gancho" nas 2 primeiras linhas (o que o feed mostra antes
  do "ver mais").

## Como regenerar as imagens
```bash
python analysis/dashboard_linkedin.py            # gera os 9 PNGs em output/carousel/
python analysis/dashboard_linkedin.py --validate # inspeciona os números sem plotar
```
