# -*- coding: utf-8 -*-
"""
skills_dict.py

Dicionário de skills para extração via regex.

ESTRUTURA (simples de manter):
    "Nome Canônico": ["alias1", "alias2", ...]

REGRAS DE MATCHING (implementadas em extract-skills-regex.py):
- Cada alias casa como termo inteiro (com fronteiras), case-insensitive e sem acento.
- Variação junto/separado/hífen é automática: "data integration" também casa
  "dataintegration" e "data-integration".
- AGRUPAMENTO: tudo que estiver sob o mesmo "Nome Canônico" vira aquele nome.
  Ex.: "power query" e "dax" -> "Power BI".

PARA ADICIONAR: acrescente uma string na lista do grupo certo, ou crie uma nova
chave canônica. Mantenha aliases em minúsculas (a normalização cuida do resto).
"""

SKILLS = {
    # ---- Linguagens / bibliotecas core ----
    "SQL":              ["sql", "t-sql", "tsql", "pl/sql", "plsql", "spark sql", "ansi sql",
                          "advanced sql", "sql server", "oracle sql", "googlesql", "hiveql", "hql", "ksql", "kql"],
    "Python":           ["python", "pandas", "numpy", "pyspark", "scikit-learn", "sklearn",
                          "scipy", "matplotlib", "seaborn", "polars", "fastapi", "flask", "django",
                          "pytest", "sqlalchemy", "openpyxl", "beautifulsoup", "scrapy"],
    "Scala":            ["scala"],
    "Java":             ["java"],
    "JavaScript":       ["javascript", "typescript", "node", "node.js", "react", "angular", "vue"],
    "R":                ["rstudio", "shiny"],
    "VBA":              ["vba", "macros", "macro"],

    # ---- BI / Visualização ----
    "Power BI":         ["power bi", "powerbi", "power query", "power pivot", "dax", "power bi dax",
                          "power dax", "power bi gateway", "power bi intermediario", "power bi avancado"],
    "Tableau":          ["tableau"],
    "Looker":           ["looker", "looker studio", "google looker studio", "data studio", "google data studio"],
    "Qlik":             ["qlik", "qlik sense", "qlikview"],
    "Metabase":         ["metabase"],
    "Superset":         ["superset", "apache superset"],
    "Data Visualization":["data visualization", "visualizacao de dados", "dataviz", "dashboards", "dashboard"],

    # ---- Cloud ----
    "AWS":              ["aws", "amazon web services", "s3", "redshift", "aws glue", "glue", "athena",
                          "aws lambda", "lambda", "emr", "aws emr", "kinesis", "ec2", "sagemaker",
                          "aws sagemaker", "step functions", "dynamodb", "aws rds", "rds", "cloudwatch",
                          "amazon redshift", "aws athena", "aws s3", "aws redshift"],
    "Azure":            ["azure", "microsoft azure", "azure data factory", "adf", "azure devops",
                          "azure synapse", "synapse", "azure functions", "azure data lake",
                          "azure event hub", "azure synapse analytics", "microsoft fabric", "fabric",
                          "azure data lake storage", "adls", "azure sql", "azure blob storage"],
    "GCP":              ["gcp", "google cloud", "google cloud platform", "bigquery", "google bigquery",
                          "dataflow", "dataproc", "cloud composer", "cloud functions", "cloud run",
                          "pub/sub", "cloud storage", "dataform", "vertex ai", "vertex"],
    "Oracle Cloud":     ["oci", "oracle cloud"],

    # ---- Plataformas de dados / processamento ----
    "Databricks":       ["databricks", "unity catalog", "delta lake", "delta table", "delta tables",
                          "lakehouse", "data lakehouse", "mlflow", "pyspark"],
    "Spark":            ["spark", "apache spark", "spark sql", "spark streaming", "structured streaming"],
    "Hadoop":           ["hadoop", "hive", "hdfs", "mapreduce", "impala"],
    "Kafka":            ["kafka", "apache kafka", "confluent", "amazon msk", "msk"],
    "Flink":            ["flink", "apache flink"],
    "dbt":              ["dbt"],
    "Snowflake":        ["snowflake", "snowpark", "snowpipe"],

    # ---- Orquestração ----
    "Airflow":          ["airflow", "apache airflow", "mwaa", "cloud composer"],
    "Dagster":          ["dagster"],
    "Prefect":          ["prefect"],
    "Luigi":            ["luigi"],

    # ---- Bancos de dados ----
    "PostgreSQL":       ["postgresql", "postgres"],
    "MySQL":            ["mysql", "mariadb"],
    "SQL Server":       ["sql server", "ssis", "ssas", "mssql"],
    "Oracle":           ["oracle", "oracle database"],
    "MongoDB":          ["mongodb"],
    "NoSQL":            ["nosql", "cassandra", "redis", "dynamodb", "elasticsearch"],
    "ClickHouse":       ["clickhouse"],

    # ---- Engenharia / arquitetura de dados ----
    "ETL":              ["etl", "elt", "etls", "elts", "etl/elt"],
    "Data Integration": ["data integration", "integracao de dados"],
    "Data Modeling":    ["data modeling", "modelagem de dados", "modelagem dimensional",
                          "dimensional modeling", "star schema", "snowflake schema", "data vault",
                          "modelagem dados", "data modelling"],
    "Data Warehouse":   ["data warehouse", "data warehousing", "data mart", "datawarehouse",
                          "data warehouses", "data marts"],
    "Data Lake":        ["data lake", "data lakes", "delta lake", "lakehouse"],
    "Data Pipelines":   ["data pipeline", "data pipelines", "pipeline de dados", "pipelines"],
    "Big Data":         ["big data", "bigdata"],
    "Data Governance":  ["data governance", "governanca de dados", "governanca", "lgpd", "gdpr",
                          "data quality", "data catalog", "data lineage", "dama", "dmbok"],
    "Data Architecture":["data architecture", "arquitetura de dados", "data mesh", "medallion architecture"],
    "APIs":             ["api", "apis", "rest", "rest api", "rest apis", "restful", "api rest",
                          "apis rest", "graphql", "soap", "api integration"],

    # ---- DevOps / infra ----
    "Git":              ["git", "github", "gitlab", "github actions", "gitflow", "bitbucket", "versionamento", "version control"],
    "Docker":           ["docker", "containers", "containerization"],
    "Kubernetes":       ["kubernetes", "k8s", "eks", "gke", "helm"],
    "Terraform":        ["terraform", "infrastructure as code", "iac", "opentofu", "pulumi"],
    "CI/CD":            ["ci/cd", "cicd", "jenkins", "github actions", "gitlab ci", "azure devops"],
    "Linux":            ["linux", "unix", "bash", "shell script", "shell scripting", "powershell"],

    # ---- ML / IA ----
    "Machine Learning": ["machine learning", "aprendizado de maquina", "scikit-learn", "xgboost",
                          "lightgbm", "catboost", "random forest", "regression", "clustering"],
    "Deep Learning":    ["deep learning", "tensorflow", "pytorch", "keras", "neural networks", "redes neurais"],
    "LLM":              ["llm", "llms", "openai", "anthropic", "claude", "chatgpt", "gpt", "gemini",
                          "langchain", "langgraph", "rag", "prompt engineering", "generative ai",
                          "genai", "vector databases", "embeddings"],
    "MLOps":            ["mlops", "mlflow", "kubeflow", "sagemaker", "feature store", "model deployment"],
    "NLP":              ["nlp", "natural language processing"],
    "Estatistica":      ["estatistica", "statistics", "statistical analysis", "analise estatistica",
                          "probabilidade", "probability", "inferencia estatistica"],

    # ---- Ferramentas de produtividade ----
    "Excel":            ["excel", "microsoft excel", "tabelas dinamicas", "pivot tables", "procv",
                          "vlookup", "power query", "formulas", "pacote office", "microsoft office", "office"],
    "Google Sheets":    ["google sheets", "google planilhas", "google workspace", "gsheet"],
    "PowerPoint":       ["powerpoint", "power point", "microsoft powerpoint"],
    "Power Automate":   ["power automate", "power apps", "power platform", "microsoft power platform"],
    "Jira":             ["jira", "confluence"],

    # ---- Domínio / ERP ----
    "SAP":              ["sap", "abap", "sap bw", "sap hana"],
    "ERP":              ["erp", "protheus", "totvs", "netsuite"],
    "CRM":              ["crm", "salesforce", "hubspot"],
    "BPM":              ["bpm", "business process management"],
    "ECM":              ["ecm", "enterprise content management"],
    "Workflow":         ["workflow", "workflows"],

    # ---- Metodologias ----
    "Agile":            ["agile", "agil", "scrum", "kanban", "metodologias ageis", "metodologia agil", "safe", "lean"],

    # ---- Soft skills ----
    "Comunicacao":      ["comunicacao", "communication", "good communication", "clear communication"],
    "Trabalho em Equipe":["trabalho em equipe", "teamwork", "team work", "colaboracao", "collaboration", "collaborative"],
    "Proatividade":     ["proatividade", "proactivity", "proactive", "proativo", "iniciativa", "initiative"],
    "Resolucao de Problemas":["resolucao de problemas", "problem solving", "problem-solving", "problem solver"],
    "Pensamento Analitico":["pensamento analitico", "analytical thinking", "analytical", "raciocinio logico",
                          "logical reasoning", "capacidade analitica", "perfil analitico", "analytical skills"],
    "Organizacao":      ["organizacao", "organization", "organized", "organizado", "atencao aos detalhes",
                          "attention to detail", "detail-oriented"],
    "Autonomia":        ["autonomia", "autonomy", "independence", "senso de dono", "ownership"],
    "Lideranca":        ["lideranca", "leadership", "mentorship", "mentoring", "mentoria"],
    "Curiosidade":      ["curiosidade", "curiosity", "curioso", "curious", "vontade de aprender", "willingness to learn"],
    "Storytelling":     ["storytelling", "data storytelling"],
    "Visao Estrategica":["visao estrategica", "strategic thinking", "strategic vision", "visao de negocio"],

    # ---- Idiomas ----
    "Ingles":           ["ingles", "english", "ingles intermediario", "ingles avancado",
                          "advanced english", "english (advanced)", "english (intermediate)"],
    "Espanhol":         ["espanhol", "spanish"],
}