# 🎓 Sistema de Apoio e Previsão de Risco - Passos Mágicos

Projeto desenvolvido como parte do **Datathon**, do curso de  
**Pós-Graduação em Data Analytics** da **FIAP (Faculdade de Informática e Administração Paulista)**.

## 👥 Integrantes do Grupo
- **Gabriel Mariusso Campachi**
- **José Eduardo Augusto Couto Fontes**
- **Mayara Soares Santos**

---

## 📌 Sobre o Projeto

Este projeto apresenta uma **aplicação interativa desenvolvida em Streamlit** para a **gestão de alunos e predição de risco de queda de desempenho**, utilizando técnicas de **Machine Learning** e integração em tempo real com banco de dados em nuvem.

O sistema foi desenvolvido para apoiar a ONG **Passos Mágicos**, fornecendo ferramentas baseadas em dados para direcionar intervenções pedagógicas e psicossociais precisas.

---

## 🌐 Aplicação Online (Deploy)

A aplicação está disponível online e pode ser acessada pelo link abaixo:

🔗 https://app-paapps-magicos-n8zdmdibp8vpkn3rcdiyrl.streamlit.app/

> Através da interface web, a equipe pedagógica pode gerenciar o cadastro de alunos, inserir notas de indicadores de desempenho, e obter instantaneamente o **nível de risco do estudante**, além de visualizar um **Dashboard completo** com o panorama da associação.

---

## 🎯 Objetivo do Projeto

- Predizer a **probabilidade de queda de desempenho** dos alunos da ONG.
- Utilizar os **indicadores educacionais e psicossociais** (IAN, IDA, IEG, IAA, IPS, IPP, IPV).
- Oferecer uma **interface de gestão (CRUD)** integrada com o Google Sheets.
- Disponibilizar um **Dashboard interativo** para tomada de decisão gerencial.

> ⚠️ **Aviso** > Este sistema atua como um **apoio à decisão pedagógica** para identificar alunos que necessitam de atenção especial e **não substitui** o acompanhamento humano e psicológico individualizado.

---

## 🧠 Modelo de Machine Learning

- O modelo de classificação foi treinado com o histórico de dados dos alunos da associação.
- **Processamento:** O modelo avalia a Fase de ensino, o Gênero e os 7 indicadores de desempenho do aluno para calcular o risco.
- **Saída:** O sistema retorna uma probabilidade percentual (ex: 75.5%) e classifica o aluno em **ADEQUADO** ou **ALERTA DE RISCO**, sugerindo ações de intervenção (Manutenção, Atenção ou Ação Imediata).

O modelo final foi salvo utilizando **Joblib** e é consumido em tempo real pela aplicação.

---

## 🧩 Funcionalidades da Aplicação

### 🔍 Análise Exploratória
- Apresentação dos insights obtidos durante a fase de descoberta de dados (EDA).
- Gráficos e conclusões sobre o cenário histórico da associação.

### 👤 Gestão de Alunos - Previsão de Risco
- **Lista Integrada:** Visualização de todos os alunos cadastrados com leitura direta do banco de dados (Google Sheets) via sistema de cache otimizado.
- **Dossiê do Aluno:** Seleção de um aluno para visualizar seu perfil completo.
- **Motor de IA:** Formulário para input de notas e cálculo instantâneo do risco de queda.
- **Ações CRUD:** Cadastro de novos alunos, atualização de indicadores e exclusão de registros.

### 📊 Dashboard de Resultados
- **Métricas Globais (Cards):** Total de alunos, quantidade em risco vs adequados, e a média geral de risco da ONG.
- **Visão por Fase:** Gráfico de barras comparando o volume de alunos adequados e em risco em cada fase escolar.
- **Distribuição Geral:** Gráfico de pizza ilustrando o percentual da situação atual da associação.
- **Onde estão os problemas?** Gráfico comparativo exibindo a nota média de cada indicador (IAN, IDA, etc.), separando os grupos de Risco e Adequado para fácil identificação de gargalos.
