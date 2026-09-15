"""Em caso de dúvidas, entrar em contato com nathan.barros@bayer.com""" 

import os
import sys
import json
import uuid
import base64
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
from agno.models.openai import OpenAIChat
import streamlit.components.v1 as components
from components.camera_capture import camera_capture

# ---------------------------------------------------------------------------
# Garantir diretório de trabalho correto
# ---------------------------------------------------------------------------
# Forçar o diretório de trabalho para onde o script está localizado
# Isso garante que caminhos relativos funcionem independente de como o script é executado
BASE_DIR = Path(__file__).parent.absolute()
os.chdir(BASE_DIR)

# ---------------------------------------------------------------------------
# Carrega variáveis de ambiente
# ---------------------------------------------------------------------------
env_path = BASE_DIR / "functions" / ".env"

# Verificar se o arquivo .env existe
if not env_path.exists():
    print(f"[ERRO CRÍTICO] Arquivo .env não encontrado!", file=sys.stderr)
    print(f"  Caminho esperado: {env_path}", file=sys.stderr)
    print(f"  Diretório atual: {os.getcwd()}", file=sys.stderr)
    print(f"  BASE_DIR: {BASE_DIR}", file=sys.stderr)
    print(f"  Verifique se o arquivo 'functions/.env' existe no projeto.", file=sys.stderr)
else:
    print(f"[OK] Arquivo .env encontrado: {env_path}", file=sys.stderr)

load_dotenv(dotenv_path=env_path)

# Verificar se a API key foi carregada com sucesso
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print(f"[ERRO] OPENAI_API_KEY não encontrada após load_dotenv!", file=sys.stderr)
    print(f"  Verifique se a variável está definida em: {env_path}", file=sys.stderr)
elif len(api_key) < 10:
    print(f"[AVISO] OPENAI_API_KEY parece estar vazia ou inválida.", file=sys.stderr)
else:
    print(f"[OK] OPENAI_API_KEY carregada com sucesso (primeiros 10 caracteres: {api_key[:10]}...)", file=sys.stderr)

# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------
LOGO_PATH = BASE_DIR / "resources" / "logo_peroxscan.png"
LOGO_B64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()

st.set_page_config(
    page_title="PeroxScan",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Paleta de cores e CSS global
# ---------------------------------------------------------------------------
DARK_BLUE  = "#10384F"
LIGHT_BLUE = "#00BCFF"
GREEN      = "#89D329"

st.markdown(f"""
<style>
    /* ── Fundo e sidebar ───────────────────────────────────────────── */
    [data-testid="stAppViewContainer"] {{
        background-color: #F4F8FB;
    }}
    [data-testid="stSidebar"] {{
        background-color: {DARK_BLUE};
    }}
    [data-testid="stSidebar"] * {{
        color: #FFFFFF !important;
    }}
    [data-testid="stSidebar"] hr {{
        border-color: rgba(255,255,255,0.2);
    }}

    /* ── Cabeçalho principal ───────────────────────────────────────── */
    .main-header {{
        background: linear-gradient(135deg, {DARK_BLUE} 0%, #1a5070 100%);
        color: #FFFFFF;
        padding: 24px 32px;
        border-radius: 12px;
        margin-bottom: 24px;
    }}
    .main-header h1 {{
        margin: 0;
        font-size: 1.9rem;
        font-weight: 700;
        color: #FFFFFF;
    }}
    .main-header p {{
        margin: 6px 0 0;
        font-size: 0.95rem;
        opacity: 0.85;
        color: #FFFFFF;
    }}

    /* ── Cards de etapa ────────────────────────────────────────────── */
    .step-card {{
        background: #FFFFFF;
        border-left: 5px solid {LIGHT_BLUE};
        border-radius: 10px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    }}
    .step-card h3 {{
        color: {DARK_BLUE};
        margin-top: 0;
    }}

    /* ── Botão primário ────────────────────────────────────────────── */
    .stButton > button[kind="primary"] {{
        background-color: {LIGHT_BLUE} !important;
        color: {DARK_BLUE} !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        transition: opacity .2s;
    }}
    .stButton > button[kind="primary"]:hover {{
        opacity: 0.88 !important;
    }}

    /* ── Botão secundário ──────────────────────────────────────────── */
    .stButton > button[kind="secondary"] {{
        border: 2px solid {DARK_BLUE} !important;
        color: {DARK_BLUE} !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }}

    /* ── Métricas ──────────────────────────────────────────────────── */
    [data-testid="stMetric"] {{
        background: #FFFFFF;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-top: 4px solid {LIGHT_BLUE};
    }}
    [data-testid="stMetricLabel"] {{
        color: {DARK_BLUE} !important;
        font-weight: 600 !important;
    }}
    [data-testid="stMetricValue"] {{
        color: {DARK_BLUE} !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }}

    /* ── Stepper itens na sidebar ──────────────────────────────────── */
    .step-item {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        border-radius: 8px;
        margin-bottom: 6px;
        font-size: 0.95rem;
        font-weight: 500;
    }}
    .step-item.active {{
        background: rgba(0,188,255,0.25);
        border-left: 4px solid {LIGHT_BLUE};
        font-weight: 700;
    }}
    .step-item.done {{
        opacity: 0.75;
    }}
    .step-item.pending {{
        opacity: 0.45;
    }}

    /* ── Progress bar ──────────────────────────────────────────────── */
    [data-testid="stProgressBar"] > div > div {{
        background-color: {LIGHT_BLUE} !important;
    }}

    /* ── Tabs ──────────────────────────────────────────────────────── */
    [data-baseweb="tab-list"] {{
        border-bottom: 2px solid {LIGHT_BLUE} !important;
    }}
    [data-baseweb="tab"][aria-selected="true"] {{
        color: {DARK_BLUE} !important;
        border-bottom: 3px solid {LIGHT_BLUE} !important;
        font-weight: 700 !important;
    }}

    /* ── Download button ───────────────────────────────────────────── */
    .stDownloadButton > button {{
        background-color: {GREEN} !important;
        color: {DARK_BLUE} !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
    }}
    .stDownloadButton > button:hover {{
        opacity: 0.88 !important;
    }}

    /* ── Divider ───────────────────────────────────────────────────── */
    hr {{
        border-color: rgba(16, 56, 79, 0.15) !important;
    }}
</style>
""", unsafe_allow_html=True)


###Eruda para teste
components.html(
        """
        <script>
        (function() {
            const doc = window.parent.document;
            if (doc.getElementById('eruda-script')) return;
            const s = doc.createElement('script');
            s.id = 'eruda-script';
            s.src = 'https://cdn.jsdelivr.net/npm/eruda';
            s.onload = () => window.parent.eruda.init();
            doc.head.appendChild(s);
        })();
        </script>
        """,
        height=0,
    )


# ---------------------------------------------------------------------------
# Modelo de IA (cache para não recriar a cada rerun)
# ---------------------------------------------------------------------------
@st.cache_resource(ttl=14400)
def get_model():
    return OpenAIChat(
        id="gpt-5.2",
        temperature=0.1,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE"),
        default_headers={
            "x-baychatgpt-accesstoken": os.getenv("OPENAI_API_KEY"),
        },
    )



# ---------------------------------------------------------------------------
# salvar_log — copiada do bot.py sem alterações
# ---------------------------------------------------------------------------
def salvar_log(results: list, sap_status: dict, log_dir: Path, sp_status: dict = None) -> None:
    """Gera um arquivo .txt com o status da execução."""
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now()
    filename = log_dir / f"log_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"LOG DE EXECUÇÃO - {timestamp.strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")

        f.write("RESULTADOS POR IMAGEM\n")
        f.write("=" * 60 + "\n")
        for r in results:
            f.write(f"Arquivo: {r['arquivo']}\n")
            f.write(f"  Número: {r['numero']}\n")
            f.write(f"  Classificação: {r['classificacao']}\n")
            f.write(f"  Confiança: {r.get('confianca', 'N/A')}\n")
            if r.get('observacao'):
                f.write(f"  Observação: {r['observacao']}\n")
            if 'erro' in r:
                f.write(f"  Erro análise: {r['erro']}\n")
            status_sap = sap_status.get(r['arquivo'], 'NÃO PROCESSADO')
            f.write(f"  SAP: {status_sap}\n")
            f.write("\n")

        sap_ok = sum(1 for s in sap_status.values() if s == 'OK via API')
        sap_err = sum(1 for s in sap_status.values() if s.startswith('ERRO'))

        f.write("=" * 60 + "\n")
        f.write("STATUS GERAL\n")
        f.write(f"  Total de imagens processadas: {len(results)}\n")
        f.write(f"  SAP preenchido com sucesso: {sap_ok}\n")
        f.write(f"  SAP com erro: {sap_err}\n")
        f.write("=" * 60 + "\n")

        if sp_status:
            f.write("\n")
            f.write("=" * 60 + "\n")
            f.write("UPLOAD SHAREPOINT\n")
            f.write("=" * 60 + "\n")
            sp_ok = 0
            sp_err = 0
            for nome_sp, status_sp in sp_status.items():
                f.write(f"  {nome_sp}: {status_sp}\n")
                if status_sp == "OK":
                    sp_ok += 1
                else:
                    sp_err += 1
            f.write(f"\n  Upload com sucesso: {sp_ok}\n")
            f.write(f"  Upload com erro: {sp_err}\n")
            f.write("=" * 60 + "\n")

    return filename


# ---------------------------------------------------------------------------
# Inicialização do session_state
# ---------------------------------------------------------------------------
defaults = {
    "step": 1,
    "images": [],         # lista de dicts: {"nome": str, "bytes": bytes}
    "results": [],        # lista de dicts retornados por analyze_peroxidase_reaction
    "sap_status": {},     # dict: {arquivo: str_status}
    "sp_status": {},      # dict: {nome_arquivo: str_status} — upload SharePoint
    "aprovados": {},      # dict: {arquivo: bool} — seleção do usuário na revisão
    "running": False,
    "modo_simulacao": False,  # True = analisa mas NÃO envia ao SAP
    "step4_done": False,      # True após SAP+SharePoint executados
    "camera_counter": 0,      # incrementa a cada captura para resetar o widget de câmera
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------------------------------------------------------------------
# Cabeçalho principal
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="main-header">
    <h1>🧪 PeroxScan</h1>
    <p>
        <span style="background:rgba(0,188,255,0.25); border:1px solid #00BCFF; border-radius:6px; padding:2px 10px; font-size:0.82rem; font-weight:700; letter-spacing:0.5px; margin-right:10px;">PEROXSCAN</span>
        Classificação autônoma de reações de peroxidase · Integração SAP
    </p>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Stepper na sidebar
# ---------------------------------------------------------------------------
step_labels = [
    ("📷", "1. Entrada de Dados"),
    ("🤖", "2. Análise IA"),
    ("✅", "3. Revisão Humana"),
    ("📊", "4. Relatório"),
]

with st.sidebar:
    st.markdown(f'<div style="text-align:center; padding:8px 0;"><img src="data:image/png;base64,{LOGO_B64}" style="width:100%; max-width:220px;"/></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:0.75rem; font-weight:700; letter-spacing:1px; color:#89D329; margin-bottom:4px;">PEROXSCAN</div>
    <div style="font-size:1.05rem; font-weight:700; margin-bottom:16px; color:#00BCFF; letter-spacing:0.5px;">FLUXO DE EXECUÇÃO</div>
    """, unsafe_allow_html=True)

    for i, (icon, label) in enumerate(step_labels, 1):
        if st.session_state.step == i:
            css_class = "active"
        elif st.session_state.step > i:
            css_class = "done"
        else:
            css_class = "pending"

        check = "✅ " if st.session_state.step > i else ""
        arrow = "→ " if st.session_state.step == i else ""

        st.markdown(f"""
        <div class="step-item {css_class}">
            {icon}&nbsp;&nbsp;{arrow}{check}{label}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Info de imagens carregadas
    n_imgs = len(st.session_state.images)
    if n_imgs > 0:
        st.markdown(f"""
        <div style="font-size:0.85rem; opacity:0.85; margin-top:8px;">
            📂 <b>{n_imgs}</b> imagem(ns) carregada(s)
        </div>
        """, unsafe_allow_html=True)

    # Verificação da API key
    api_ok = bool(os.getenv("OPENAI_API_KEY"))
    st.markdown(f"""
    <div style="font-size:0.82rem; margin-top:12px; opacity:0.8;">
        {'🟢' if api_ok else '🔴'} API OpenAI: {'configurada' if api_ok else 'não encontrada'}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.75rem; font-weight:700; letter-spacing:1px; color:#89D329; margin-bottom:8px;">
        MODO DE OPERAÇÃO
    </div>
    """, unsafe_allow_html=True)
    modo_sim = st.toggle(
        "Modo Simulação",
        value=st.session_state.modo_simulacao,
        help="Ativado: o Agente analisa as imagens normalmente, mas NÃO envia dados ao SAP.",
        key="toggle_simulacao",
    )
    st.session_state.modo_simulacao = modo_sim
    if modo_sim:
        st.markdown(f"""
        <div style="background:rgba(137,211,41,0.18); border:1px solid #89D329; border-radius:6px;
                    padding:8px 10px; font-size:0.8rem; color:#FFFFFF; margin-top:6px;">
            🧪 <b>Simulação ativa</b><br/>Resultados não serão enviados ao SAP.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:rgba(0,188,255,0.15); border:1px solid #00BCFF; border-radius:6px;
                    padding:8px 10px; font-size:0.8rem; color:#FFFFFF; margin-top:6px;">
            📡 <b>Modo produção</b><br/>Resultados serão enviados ao SAP.
        </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# ETAPA 1 — Anexar ou Tirar Fotos
# ---------------------------------------------------------------------------
def render_step1():
    st.markdown("""
    <div class="step-card">
        <h3>📷 Etapa 1 — Entrada de Dados</h3>
        <p style="color:#555; margin:0;">Forneça as imagens das fichas de peroxidase. Você pode carregar arquivos ou capturar fotos diretamente pela câmera do dispositivo.</p>
    </div>
    """, unsafe_allow_html=True)

    tab_camera, tab_upload = st.tabs(["📷  Câmera", "📂  Galeria / Arquivos"])

    with tab_camera:
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            f"<div style='color:{DARK_BLUE}; font-weight:600; margin-bottom:10px; font-size:1.05rem;'>"
            "Toque no botão para abrir a câmera e capturar a próxima ficha:"
            "</div>",
            unsafe_allow_html=True,
        )

        # `key` dinâmica: incrementada após cada captura para que o componente
        # seja remontado (stream reiniciado) e o usuário possa tirar a próxima
        # foto sem precisar interagir com outros controles.
        camera_key = f"camera_shot_{st.session_state.camera_counter}"
        data_url = camera_capture(key=camera_key)

        if data_url:
            img_bytes = base64.b64decode(data_url.split(",", 1)[1])
            nome_foto = f"camera_{uuid.uuid4().hex[:8]}.jpg"
            st.session_state.images.append({"nome": nome_foto, "bytes": img_bytes})
            st.session_state.camera_counter += 1
            try:
                st.toast("📸 Foto adicionada à fila!", icon="✅")
            except Exception:
                pass
            st.rerun()

        # Feedback rápido logo abaixo do botão (contador + última miniatura)
        if st.session_state.images:
            ultima = st.session_state.images[-1]
            col_info, col_thumb = st.columns([3, 1])
            with col_info:
                st.markdown(
                    f"<div style='background:{LIGHT_BLUE}22; border-left:4px solid {LIGHT_BLUE}; "
                    f"border-radius:8px; padding:12px 16px; margin-top:12px;'>"
                    f"<div style='font-size:1.1rem; font-weight:700; color:{DARK_BLUE};'>"
                    f"✅ {len(st.session_state.images)} foto(s) na fila</div>"
                    f"<div style='font-size:0.85rem; color:#555; margin-top:4px;'>"
                    f"Toque novamente em <b>📸 Tirar Foto</b> para adicionar a próxima.</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            with col_thumb:
                st.image(ultima["bytes"], caption="Última foto", width="stretch")

    with tab_upload:
        uploaded = st.file_uploader(
            "Selecione uma ou mais imagens",
            type=["jpg", "jpeg", "png", "bmp", "tiff"],
            accept_multiple_files=True,
            key="file_uploader",
            help="Formatos aceitos: JPG, JPEG, PNG, BMP, TIFF",
        )
        if uploaded:
            nomes_existentes = {img["nome"] for img in st.session_state.images}
            for f in uploaded:
                if f.name not in nomes_existentes:
                    st.session_state.images.append({"nome": f.name, "bytes": f.read()})
                    nomes_existentes.add(f.name)

    # ── Preview das imagens ──────────────────────────────────────────────
    if st.session_state.images:
        st.markdown(f"""
        <div style="margin: 20px 0 12px; font-weight:600; color:{DARK_BLUE}; font-size:1rem;">
            {len(st.session_state.images)} imagem(ns) na fila de análise
        </div>
        """, unsafe_allow_html=True)

        indices_remover = []
        cols = st.columns(4)
        for i, img in enumerate(st.session_state.images):
            with cols[i % 4]:
                st.image(img["bytes"], caption=img["nome"], width="stretch")
                if st.button("❌ Remover", key=f"remove_{i}", use_container_width=True):
                    indices_remover.append(i)

        if indices_remover:
            for idx in sorted(indices_remover, reverse=True):
                st.session_state.images.pop(idx)
            st.rerun()  # necessário: o clique no botão já executou o rerun, este força re-render do grid
    else:
        st.markdown(f"""
        <div style="
            border: 2px dashed {LIGHT_BLUE};
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            color: #888;
            margin: 20px 0;
        ">
            <div style="font-size:2.5rem;">📂</div>
            <div style="margin-top:8px;">Nenhuma imagem carregada ainda</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    col_left, col_right = st.columns([3, 1])
    with col_right:
        if st.button(
            "Avançar para Análise →",
            disabled=len(st.session_state.images) == 0,
            type="primary",
            use_container_width=True,
        ):
            st.session_state.step = 2
            st.rerun()

render_step1()