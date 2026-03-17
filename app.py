import streamlit as st
import pandas as pd
import joblib
from datetime import datetime
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURACAO DA PAGINA E VARIAVEIS DE SESSAO
# ==========================================
st.set_page_config(page_title="Gestão Passos Mágicos", layout="wide")

if 'tela_interna_crud' not in st.session_state:
    st.session_state.tela_interna_crud = 'lista'
if 'aluno_selecionado' not in st.session_state:
    st.session_state.aluno_selecionado = None
if 'index_linha_gs' not in st.session_state:
    st.session_state.index_linha_gs = None 
if 'resultado_ia' not in st.session_state:
    st.session_state.resultado_ia = None

# Paleta de Cores Azul
COR_RISCO = "#003366"  
COR_ADEQUADO = "#00CCFF" 

# ==========================================
# 2. CONEXOES E MODELO (COM CACHE PARA VELOCIDADE)
# ==========================================
@st.cache_resource
def carregar_modelo():
    return joblib.load('modelo_passos_magicos_final.pkl'), joblib.load('colunas_modelo.pkl')

modelo, colunas_treino = carregar_modelo()

@st.cache_data(ttl=60)
def carregar_dados_cache():
    aba = obter_aba_planilha()
    if aba:
        try:
            return pd.DataFrame(aba.get_all_records())
        except Exception as e:
            st.error(f"Erro ao ler registros: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def conectar_banco_direto():
    escopo = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 1. PRIORIDADE LOCAL (VS CODE): Se o arquivo existe, usa ele direto. 
    nome_arquivo = 'credenciais.json'
    if os.path.exists(nome_arquivo):
        try:
            credenciais = ServiceAccountCredentials.from_json_keyfile_name(nome_arquivo, escopo)
            return gspread.authorize(credenciais)
        except Exception as e:
            st.error(f"Erro no arquivo local: {e}")

    # 2. SE NÃO TEM ARQUIVO, TENTA O SECRETS (NUVEM/STREAMLIT CLOUD)
    try:
        if "gcp_service_account" in st.secrets:
            credenciais_dict = {k: v for k, v in st.secrets["gcp_service_account"].items()}
            credenciais_dict["private_key"] = credenciais_dict["private_key"].replace("\\n", "\n")
            credenciais = ServiceAccountCredentials.from_json_keyfile_dict(credenciais_dict, escopo)
            return gspread.authorize(credenciais)
    except:
        return None
    
    return None

def obter_aba_planilha():
    cliente = conectar_banco_direto()
    if cliente is None:
        st.error("Falha na autenticação com o Google. Verifique os Secrets ou o arquivo JSON.")
        return None
    try:
        link = 'https://docs.google.com/spreadsheets/d/1FbQMIWePwB8dVA0syEVEroF45A_s1tJp9r2Zo9f8nXE/edit'
        return cliente.open_by_url(link).sheet1
    except Exception as e:
        st.error(f"Erro ao abrir a planilha. Verifique se ela foi compartilhada com o e-mail do robô: {e}")
        return None

# ==========================================
# 3. FUNCOES DE APOIO
# ==========================================
def converter_float_seguro(valor):
    try: 
        v = float(str(valor).replace(',', '.'))
        if v > 10.0 and v <= 100.0: v = v / 10.0
        if v > 10.0: v = 10.0
        if v < 0.0: v = 0.0
        return round(v, 2)
    except: return 0.0

def obter_recomendacao(probabilidade):
    if probabilidade > 70:
        return "ACAO IMEDIATA: Alto risco detectado. Recomenda-se reforco escolar e apoio psicossocial imediato."
    elif probabilidade > 40:
        return "ATENCAO: Risco moderado. Recomenda-se monitoramento preventivo e engajamento nas atividades."
    else:
        return "MANUTENCAO: Aluno em trajetoria adequada. Incentivar a continuidade do desempenho."

def calcular_risco_ia(ra, genero, fase_num, ian, ida, ieg, iaa, ips, ipp, ipv):
    df_final = pd.DataFrame(0, index=[0], columns=colunas_treino)
    if 'IAN_atual' in df_final.columns: df_final['IAN_atual'] = float(ian)
    if 'IDA' in df_final.columns: df_final['IDA'] = float(ida)
    if 'IEG' in df_final.columns: df_final['IEG'] = float(ieg)
    if 'IAA' in df_final.columns: df_final['IAA'] = float(iaa)
    if 'IPS' in df_final.columns: df_final['IPS'] = float(ips)
    if 'IPP' in df_final.columns: df_final['IPP'] = float(ipp)
    if 'IPV' in df_final.columns: df_final['IPV'] = float(ipv)
    
    col_fase = f"Fase_{fase_num}"
    if col_fase in df_final.columns: df_final[col_fase] = 1.0
    elif f"Fase_{float(fase_num)}" in df_final.columns: df_final[f"Fase_{float(fase_num)}"] = 1.0
    col_gen = f"Gênero_{genero}"
    if col_gen in df_final.columns: df_final[col_gen] = 1.0
    
    df_final = df_final.astype(float)
    previsao = modelo.predict(df_final)[0]
    probabilidade = modelo.predict_proba(df_final)[0][1] * 100
    status = "ALERTA DE RISCO" if previsao == 1 else "ADEQUADO"
    
    return {
        'Data e Hora': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'RA do Aluno': str(ra), 'Fase': f"Fase {fase_num}", 'Gênero': genero,
        'IAN': ian, 'IDA': ida, 'IEG': ieg, 'IAA': iaa, 'IPS': ips, 'IPP': ipp, 'IPV': ipv,
        'Probabilidade de Queda': f"{probabilidade:.1f}%".replace('.', ','), 
        'Status': status, 'previsao_raw': previsao, 'probabilidade_raw': probabilidade,
        'Recomendacao': obter_recomendacao(probabilidade)
    }

# ==========================================
# 4. LOGICA DE NAVEGACAO
# ==========================================
st.sidebar.title("📌 Menu Principal")
# Nomes de menu atualizados para melhor UX
menu = st.sidebar.radio("Selecione uma seção:", ["👤 Gestão de Alunos", "📊 Painel Geral"])

if menu == "👤 Gestão de Alunos":
    st.title("👤 Gestão de Alunos")
    # Nova descrição de UX adicionada
    st.markdown("*Acompanhe os indicadores da turma, identifique precocemente os alertas de risco e cadastre novas avaliações para manter o histórico atualizado.*")
    st.divider()
    
    if st.session_state.tela_interna_crud == 'lista':
        if st.button("Cadastrar e Analisar Novo Aluno", type="primary"):
            st.session_state.tela_interna_crud = 'formulario'
            st.session_state.aluno_selecionado = None
            st.session_state.resultado_ia = None
            st.rerun()

        try:
            df = carregar_dados_cache()
            if not df.empty:
                st.markdown("*Dica: Selecione a caixa na primeira coluna para abrir, editar ou excluir o registro.*")
                df_view = df.copy()
                for c in ['IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV']:
                    if c in df_view.columns:
                        df_view[c] = df_view[c].apply(lambda x: f"{converter_float_seguro(x):.1f}".replace('.', ','))

                selecao = st.dataframe(df_view, use_container_width=True, hide_index=True, selection_mode="single-row", on_select="rerun")

                if len(selecao.selection.rows) > 0:
                    idx = selecao.selection.rows[0]
                    st.session_state.aluno_selecionado = df.iloc[idx].to_dict()
                    st.session_state.index_linha_gs = idx + 2
                    st.session_state.tela_interna_crud = 'formulario'
                    st.session_state.resultado_ia = None
                    st.rerun()
            else:
                st.info("Nenhum registro encontrado na planilha.")
        except Exception as e: 
            st.error(f"Erro ao carregar lista de alunos: {e}")

    elif st.session_state.tela_interna_crud == 'formulario':
        modo_edit = st.session_state.aluno_selecionado is not None
        aluno = st.session_state.aluno_selecionado if modo_edit else {}
        
        with st.form("form_aluno"):
            ra = st.text_input("RA do Aluno *", value=str(aluno.get('RA do Aluno', '')), disabled=modo_edit)
            c1, c2 = st.columns(2)
            with c1:
                genero = st.selectbox("Genero", ["Masculino", "Feminino"], index=0 if aluno.get('Gênero') == "Masculino" else 1)
            with c2:
                fases = ["Fase 1", "Fase 2", "Fase 3", "Fase 4", "Fase 5", "Fase 6", "Fase 7", "Fase 8"]
                f_idx = fases.index(aluno.get('Fase')) if aluno.get('Fase') in fases else 0
                fase_sel = st.selectbox("Fase Escolar", fases, index=f_idx)
                fase_n = int(fase_sel.replace("Fase ", ""))

            st.markdown("**Indicadores**")
            n1, n2, n3, n4 = st.columns(4)
            ian = n1.number_input("IAN", 0.0, 10.0, converter_float_seguro(aluno.get('IAN', 8.0)))
            ida = n2.number_input("IDA", 0.0, 10.0, converter_float_seguro(aluno.get('IDA', 7.0)))
            ieg = n3.number_input("IEG", 0.0, 10.0, converter_float_seguro(aluno.get('IEG', 8.0)))
            iaa = n4.number_input("IAA", 0.0, 10.0, converter_float_seguro(aluno.get('IAA', 8.5)))
            
            p1, p2, p3 = st.columns(3)
            ips = p1.number_input("IPS", 0.0, 10.0, converter_float_seguro(aluno.get('IPS', 7.5)))
            ipp = p2.number_input("IPP", 0.0, 10.0, converter_float_seguro(aluno.get('IPP', 7.5)))
            ipv = p3.number_input("IPV", 0.0, 10.0, converter_float_seguro(aluno.get('IPV', 7.0)))
            
            submit = st.form_submit_button("Fazer Previsão de Risco", type="primary", use_container_width=True)
            
            if submit:
                if not ra: st.warning("RA obrigatorio")
                else: st.session_state.resultado_ia = calcular_risco_ia(ra, genero, fase_n, ian, ida, ieg, iaa, ips, ipp, ipv)

        if st.session_state.resultado_ia:
            res = st.session_state.resultado_ia
            st.divider()
            if res['previsao_raw'] == 1: st.error(f"Status: {res['Status']} | Probabilidade: {res['Probabilidade de Queda']}")
            else: st.success(f"Status: {res['Status']} | Probabilidade: {res['Probabilidade de Queda']}")
            st.info(res['Recomendacao'])

        st.write("")
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            pode_persistir = st.session_state.resultado_ia is not None
            label_btn = "Atualizar Registro" if modo_edit else "Salvar Novo Aluno"
            if st.button(label_btn, type="primary", use_container_width=True, disabled=not pode_persistir):
                res_f = st.session_state.resultado_ia
                dados_f = [res_f['Data e Hora'], res_f['RA do Aluno'], res_f['Fase'], res_f['Gênero'], res_f['IAN'], res_f['IDA'], res_f['IEG'], res_f['IAA'], res_f['IPS'], res_f['IPP'], res_f['IPV'], res_f['Probabilidade de Queda'], res_f['Status']]
                aba = obter_aba_planilha()
                if aba:
                    if modo_edit: aba.update(f"A{st.session_state.index_linha_gs}:M{st.session_state.index_linha_gs}", [dados_f])
                    else: aba.append_row(dados_f)
                    st.cache_data.clear()
                    st.session_state.tela_interna_crud = 'lista'
                    st.rerun()
                else: st.error("Erro ao conectar com a planilha para salvar.")

        with col_b2:
            if modo_edit and st.button("Excluir Aluno", use_container_width=True):
                aba = obter_aba_planilha()
                if aba:
                    aba.delete_rows(st.session_state.index_linha_gs)
                    st.cache_data.clear()
                    st.session_state.tela_interna_crud = 'lista'
                    st.rerun()
                else: st.error("Erro ao conectar com a planilha para excluir.")

        with col_b3:
            if st.button("Voltar / Cancelar", use_container_width=True): 
                st.session_state.tela_interna_crud = 'lista'
                st.rerun()

elif menu == "📊 Painel Geral":
    st.title("📊 Painel Geral")
    # Nova descrição de UX adicionada
    st.markdown("*Visão panorâmica do cenário atual da instituição. Acompanhe a proporção de alunos em risco e identifique rapidamente quais fases escolares demandam maior atenção e recursos.*")
    st.divider()
    try:
        df_dash = carregar_dados_cache()
        if not df_dash.empty:
            df_dash['Prob_Num'] = df_dash['Probabilidade de Queda'].str.replace('%','').str.replace(',','.').astype(float)
            indicadores = ['IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV']
            for c in indicadores: df_dash[c] = df_dash[c].apply(converter_float_seguro)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Alunos", len(df_dash))
            c2.metric("Em Risco", len(df_dash[df_dash['Status'] == 'ALERTA DE RISCO']))
            c3.metric("Adequados", len(df_dash[df_dash['Status'] == 'ADEQUADO']))
            c4.metric("Media Risco Escola", f"{df_dash['Prob_Num'].mean():.1f}%")

            st.divider()
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                fig_pizza = px.pie(df_dash, names='Status', title='Status', color='Status', color_discrete_map={'ADEQUADO': COR_ADEQUADO, 'ALERTA DE RISCO': COR_RISCO})
                st.plotly_chart(fig_pizza, use_container_width=True)
            with col_g2:
                df_fase = df_dash.groupby(['Fase', 'Status']).size().reset_index(name='Qtd')
                fig_bar = px.bar(df_fase, x='Fase', y='Qtd', color='Status', barmode='group', title='Risco por Fase', color_discrete_map={'ADEQUADO': COR_ADEQUADO, 'ALERTA DE RISCO': COR_RISCO})
                fig_bar.update_layout(xaxis={'type': 'category', 'categoryorder': 'category ascending'}, bargap=0.3, bargroupgap=0.0)
                st.plotly_chart(fig_bar, use_container_width=True)

            st.subheader("Media de Indicadores: Grupo Risco vs Grupo Adequado")
            df_medias = df_dash.groupby('Status')[indicadores].mean().reset_index()
            df_plot = df_medias.melt(id_vars='Status', var_name='Indicador', value_name='Nota Media')
            fig_comp = px.bar(df_plot, x='Indicador', y='Nota Media', color='Status', barmode='group', title='Comparativo de Notas Medias', color_discrete_map={'ADEQUADO': COR_ADEQUADO, 'ALERTA DE RISCO': COR_RISCO}, text_auto='.1f')
            fig_comp.update_layout(yaxis_range=[0, 11], bargap=0.2)
            st.plotly_chart(fig_comp, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar gráficos: {e}")