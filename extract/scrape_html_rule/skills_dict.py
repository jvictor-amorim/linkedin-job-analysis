# -*- coding: utf-8 -*-
"""
skills_dict.py

Dicionário de skills para extração via regex, otimizado.

ESTRUTURA (simples de manter e altamente escalável):
    "Nome Canônico": ["alias1", "alias2", ...]

REGRAS DE MATCHING (implementadas em extract-skills-regex.py):
- Cada alias casa como termo inteiro (com fronteiras), case-insensitive e sem acento.
- Variação junto/separado/hífen é tratada de forma automática: "data integration" 
  também casa "dataintegration" e "data-integration".

PRINCÍPIO (revisado para máxima precisão):
- Cada chave canônica representa UM conceito (uma linguagem, UMA biblioteca, UM
  serviço, UMA ferramenta). Os aliases são APENAS variações de grafia do mesmo
  nome (maiúsc/minúsc, com/sem ponto, sigla, tradução), NUNCA outro conceito.
  Ex.: "scikit-learn" e "sklearn" são a mesma coisa; "pandas" e "python" NÃO são.
- Termos genéricos (NoSQL, Machine Learning, Cloud) existem como chave própria,
  capturando só os termos genéricos em si; cada ferramenta concreta é chave à parte.

PARA ADICIONAR: crie uma nova chave canônica para o conceito, ou acrescente uma
variação de grafia na lista existente. Mantenha aliases em minúsculas para manter
o padrão definido.
"""

SKILLS = {
    # ===================== Linguagens =====================
    "SQL":              ["sql", "ansi sql", "advanced sql"],
    "T-SQL":            ["t-sql", "tsql"],
    "PL/SQL":           ["pl/sql", "plsql"],
    "HiveQL":           ["hiveql", "hql"],
    "KSQL":             ["ksql"],
    "KQL":              ["kql"],
    "Python":           ["python"],
    "Scala":            ["scala"],
    "Java":             ["java"],
    "JavaScript":       ["javascript"],
    "TypeScript":       ["typescript"],
    "R":                ["rstudio"],
    "VBA":              ["vba", "macros", "macro"],

    # ===================== Bibliotecas Python =====================
    "pandas":           ["pandas"],
    "NumPy":            ["numpy"],
    "PySpark":          ["pyspark"],
    "scikit-learn":     ["scikit-learn", "sklearn"],
    "SciPy":            ["scipy"],
    "Matplotlib":       ["matplotlib"],
    "Seaborn":          ["seaborn"],
    "Polars":           ["polars"],
    "FastAPI":          ["fastapi"],
    "Flask":            ["flask"],
    "Django":           ["django"],
    "pytest":           ["pytest"],
    "SQLAlchemy":       ["sqlalchemy"],
    "openpyxl":         ["openpyxl"],
    "BeautifulSoup":    ["beautifulsoup"],
    "Scrapy":           ["scrapy"],

    # ===================== Bibliotecas JS =====================
    "Node.js":          ["node.js", "nodejs", "node"],
    "React":            ["react"],
    "Angular":          ["angular"],
    "Vue":              ["vue"],

    # ===================== Bibliotecas R =====================
    "Shiny":            ["shiny"],

    # ===================== BI / Visualização =====================
    "Power BI":         ["power bi", "powerbi", "power bi gateway",
                         "power bi intermediario", "power bi avancado"],
    "DAX":              ["dax"],
    "Power Query":      ["power query"],
    "Power Pivot":      ["power pivot"],
    "Tableau":          ["tableau"],
    "Looker":           ["looker"],
    "Looker Studio":    ["looker studio", "google looker studio", "data studio", "google data studio"],
    "Qlik Sense":       ["qlik sense"],
    "QlikView":         ["qlikview"],
    "Qlik":             ["qlik"],
    "Metabase":         ["metabase"],
    "Apache Superset":  ["superset", "apache superset"],
    #"Des/análise de dashboards":       ["dashboards", "dashboard", "data visualization", "visualizacao de dados", "dataviz"],

    # ===================== Cloud (genéricos) =====================
    "AWS":              ["aws", "amazon web services"],
    "Azure":            ["azure", "microsoft azure"],
    "GCP":              ["gcp", "google cloud", "google cloud platform"],
    "Oracle Cloud":     ["oci", "oracle cloud"],

    # ----- Serviços AWS -----
    "Amazon S3":        ["s3", "aws s3", "amazon s3"],
    "Amazon Redshift":  ["redshift", "amazon redshift", "aws redshift"],
    "AWS Glue":         ["aws glue", "glue"],
    "Amazon Athena":    ["athena", "aws athena", "amazon athena"],
    "AWS Lambda":       ["aws lambda", "lambda"],
    "Amazon EMR":       ["emr", "aws emr"],
    "Amazon Kinesis":   ["kinesis"],
    "Amazon EC2":       ["ec2"],
    "Amazon SageMaker": ["sagemaker", "aws sagemaker", "amazon sagemaker"],
    "AWS Step Functions": ["step functions"],
    "Amazon DynamoDB":  ["dynamodb"],
    "Amazon RDS":       ["rds", "aws rds"],
    "Amazon CloudWatch": ["cloudwatch"],
    "Amazon MSK":       ["amazon msk", "msk"],

    # ----- Serviços Azure -----
    "Azure Data Factory": ["azure data factory", "adf"],
    "Azure DevOps":     ["azure devops"],
    "Azure Synapse":    ["azure synapse", "synapse", "azure synapse analytics"],
    "Azure Functions":  ["azure functions"],
    "Azure Data Lake Storage": ["azure data lake", "azure data lake storage", "adls"],
    "Azure Event Hub":  ["azure event hub"],
    "Microsoft Fabric": ["microsoft fabric", "fabric"],
    "Azure SQL":        ["azure sql"],
    "Azure Blob Storage": ["azure blob storage"],

    # ----- Serviços GCP -----
    "BigQuery":         ["bigquery", "google bigquery"],
    "Dataflow":         ["dataflow"],
    "Dataproc":         ["dataproc"],
    "Cloud Composer":   ["cloud composer"],
    "Cloud Functions":  ["cloud functions"],
    "Cloud Run":        ["cloud run"],
    "Pub/Sub":          ["pub/sub"],
    "Cloud Storage":    ["cloud storage"],
    "Dataform":         ["dataform"],
    "Vertex AI":        ["vertex ai", "vertex"],

    # ===================== Plataformas de dados / processamento =====================
    "Databricks":       ["databricks"],
    "Unity Catalog":    ["unity catalog"],
    "Delta Lake":       ["delta lake", "delta table", "delta tables"],
    "Lakehouse":        ["lakehouse", "data lakehouse"],
    "MLflow":           ["mlflow"],
    "Spark":            ["spark", "apache spark"],
    "Spark SQL":        ["spark sql"],
    "Spark Streaming":  ["spark streaming", "structured streaming"],
    "Hadoop":           ["hadoop"],
    "Hive":             ["hive"],
    "HDFS":             ["hdfs"],
    "MapReduce":        ["mapreduce"],
    "Impala":           ["impala"],
    "Kafka":            ["kafka", "apache kafka"],
    "Confluent":        ["confluent"],
    "Flink":            ["flink", "apache flink"],
    "dbt":              ["dbt"],
    "Snowflake":        ["snowflake"],
    "Snowpark":         ["snowpark"],
    "Snowpipe":         ["snowpipe"],

    # ===================== Orquestração =====================
    "Airflow":          ["airflow", "apache airflow", "mwaa"],
    "Dagster":          ["dagster"],
    "Prefect":          ["prefect"],
    "Luigi":            ["luigi"],

    # ===================== Bancos de dados =====================
    "PostgreSQL":       ["postgresql", "postgres"],
    "MySQL":            ["mysql"],
    "MariaDB":          ["mariadb"],
    "SQL Server":       ["sql server", "mssql"],
    "SSIS":             ["ssis"],
    "SSAS":             ["ssas"],
    "Oracle Database":  ["oracle", "oracle database"],
    "MongoDB":          ["mongodb"],
    "Cassandra":        ["cassandra"],
    "Redis":            ["redis"],
    "Elasticsearch":    ["elasticsearch"],
    "ClickHouse":       ["clickhouse"],
    "NoSQL":            ["nosql"],

    # ===================== Engenharia / arquitetura de dados =====================
    "ETL":              ["etl", "etls"],
    "ELT":              ["elt", "elts"],
    "Data Integration": ["data integration", "integracao de dados"],
    "Data Modeling":    ["data modeling", "data modelling", "modelagem de dados", "modelagem dados"],
    "Dimensional Modeling": ["dimensional modeling", "modelagem dimensional"],
    "Star Schema":      ["star schema"],
    "Snowflake Schema": ["snowflake schema"],
    "Data Vault":       ["data vault"],
    "Data Warehouse":   ["data warehouse", "data warehousing", "datawarehouse", "data warehouses"],
    "Data Mart":        ["data mart", "data marts"],
    "Data Lake":        ["data lake", "data lakes"],
    "Data Pipelines":   ["data pipeline", "data pipelines", "pipeline de dados", "pipelines"],
    "Big Data":         ["big data", "bigdata"],
    "Data Governance":  ["data governance", "governanca de dados", "data governance"],
    "Data Security":    ["data security", "seguranca de dados"],
    "Data Quality":     ["data quality"],
    "Data Catalog":     ["data catalog"],
    "Data Lineage":     ["data lineage"],
    "DAMA/DMBOK":       ["dama", "dmbok"],
    "LGPD":             ["lgpd"],
    "GDPR":             ["gdpr"],
    "Data Architecture": ["data architecture", "arquitetura de dados"],
    "Data Mesh":        ["data mesh"],
    "Medallion Architecture": ["medallion architecture"],
    "APIs":             ["api", "apis"],
    "REST":             ["rest", "rest api", "rest apis", "restful", "api rest", "apis rest"],
    "GraphQL":          ["graphql"],
    "SOAP":             ["soap"],

    # ===================== DevOps / infra =====================
    "Git":              ["git", "versionamento", "version control"],
    "GitHub":           ["github"],
    "GitLab":           ["gitlab"],
    "Bitbucket":        ["bitbucket"],
    "GitHub Actions":   ["github actions"],
    "GitLab CI":        ["gitlab ci"],
    "Docker":           ["docker", "containers", "containerization"],
    "Kubernetes":       ["kubernetes", "k8s"],
    "Amazon EKS":       ["eks"],
    "GKE":              ["gke"],
    "Helm":             ["helm"],
    "Terraform":        ["terraform"],
    "Infrastructure as Code": ["infrastructure as code", "iac"],
    "OpenTofu":         ["opentofu"],
    "Pulumi":           ["pulumi"],
    "CI/CD":            ["ci/cd", "cicd"],
    "Jenkins":          ["jenkins"],
    "Linux":            ["linux", "unix"],
    "Bash":             ["bash", "shell script", "shell scripting"],
    "PowerShell":       ["powershell"],

    # ===================== ML / IA =====================
    "Machine Learning": ["machine learning", "aprendizado de maquina"],
    "XGBoost":          ["xgboost"],
    "LightGBM":         ["lightgbm"],
    "CatBoost":         ["catboost"],
    "Random Forest":    ["random forest"],
    "Regression":       ["regression"],
    "Clustering":       ["clustering"],
    "Deep Learning":    ["deep learning"],
    "TensorFlow":       ["tensorflow"],
    "PyTorch":          ["pytorch"],
    "Keras":            ["keras"],
    "Neural Networks":  ["neural networks", "redes neurais"],
    "LLM":              ["llm", "llms"],
    "OpenAI":           ["openai", "chatgpt", "gpt"],
    "Anthropic":        ["anthropic", "claude"],
    "Gemini":           ["gemini"],
    "LangChain":        ["langchain"],
    "LangGraph":        ["langgraph"],
    "RAG":              ["rag"],
    "Prompt Engineering": ["prompt engineering"],
    "Generative AI":    ["generative ai", "genai"],
    "Vector Databases": ["vector databases"],
    "Embeddings":       ["embeddings"],
    "MLOps":            ["mlops"],
    "Kubeflow":         ["kubeflow"],
    "Feature Store":    ["feature store"],
    "Model Deployment": ["model deployment"],
    "NLP":              ["nlp", "natural language processing"],
    "Estatistica":      ["statistical analysis", "analise estatistica"],
    "Probabilidade":    ["probabilidade", "probability"],
    "Inferencia Estatistica": ["inferencia estatistica"],

    # ===================== Produtividade =====================
    "Excel":            ["excel", "microsoft excel", "pacote office", "microsoft office", "office"],
    #"Microsoft Office": ["pacote office", "microsoft office", "office"],
    #"Google Sheets":    ["google sheets", "google planilhas", "gsheet"],
    #"Google Workspace": ["google workspace"],
    #"PowerPoint":       ["powerpoint", "power point", "microsoft powerpoint"],
    "Power Automate":   ["power automate"],
    "Power Apps":       ["power apps"],
    "Power Platform":   ["power platform", "microsoft power platform"],
    "Jira":             ["jira"],
    "Confluence":       ["confluence"],

    # ===================== Domínio / ERP =====================
    "SAP":              ["sap", "sap bw", "sap hana"],
    "ABAP":             ["abap"],
    "ERP":              ["erp"],
    "Protheus":         ["protheus"],
    "TOTVS":            ["totvs"],
    "NetSuite":         ["netsuite"],
    "CRM":              ["crm"],
    "Salesforce":       ["salesforce"],
    "HubSpot":          ["hubspot"],
    "BPM":              ["bpm", "business process management"],
    "ECM":              ["ecm", "enterprise content management"],

    # ===================== Metodologias =====================
    "Agile":            ["agile", "agil", "metodologias ageis", "metodologia agil"],
    "Scrum":            ["scrum"],
    "Kanban":           ["kanban"],
    "SAFe":             ["safe"],
    "Lean":             ["lean"],

    # ===================== Soft skills =====================
    #"Comunicacao":      ["comunicacao", "communication", "good communication", "clear communication"],
    #"Trabalho em Equipe": ["trabalho em equipe", "teamwork", "team work", "colaboracao",
    #                       "collaboration", "collaborative"],
    #"Proatividade":     ["proatividade", "proactivity", "proactive", "proativo", "iniciativa", "initiative"],
    #"Resolucao de Problemas": ["resolucao de problemas", "problem solving", "problem-solving", "problem solver"],
    #"Pensamento Analitico": ["pensamento analitico", "analytical thinking", "analytical",
    #                         "raciocinio logico", "logical reasoning", "capacidade analitica",
    #                         "perfil analitico", "analytical skills"],
    #"Organizacao":      ["organizacao", "organization", "organized", "organizado",
    #                     "atencao aos detalhes", "attention to detail", "detail-oriented"],
    #"Autonomia":        ["autonomia", "autonomy", "independence", "senso de dono", "ownership"],
    #"Lideranca":        ["lideranca", "leadership", "mentorship", "mentoring", "mentoria"],
    #"Curiosidade":      ["curiosidade", "curiosity", "curioso", "curious",
    #                     "vontade de aprender", "willingness to learn"],
    #"Storytelling":     ["storytelling", "data storytelling"],
    #"Visao Estrategica": ["visao estrategica", "strategic thinking", "strategic vision", "visao de negocio"],

    # ===================== Idiomas =====================
    "Ingles":           ["ingles", "english", "ingles intermediario", "ingles avancado",
                         "advanced english", "english (advanced)", "english (intermediate)"],
    "Espanhol":         ["espanhol", "spanish"],
    "Francês":          ["frances", "french"],
    "Alemão":           ["alemao", "german"],
    "Italiano":         ["italiano", "italian"],
}