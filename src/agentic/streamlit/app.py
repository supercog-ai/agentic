import streamlit as st

st.set_page_config(
    page_title="Agentic"
)

#======================
# Pages               #
#======================

agent_console = st.Page(
    "agent_console.py", title="Agent Console", icon=":material/chat:", default=True
)

#======================
# Navigation          #
#======================

pg = st.navigation(
    {
        "Agents": [agent_console]
    }
)

pg.run()
