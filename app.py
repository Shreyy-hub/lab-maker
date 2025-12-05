import streamlit as st
import google.generativeai as genai
import graphviz
import json
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Network Lab Gen", layout="wide")

# --- SIDEBAR: SETUP ---
st.sidebar.title("⚙️ Control Panel")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
topic = st.sidebar.selectbox("Select Topic", ["OSPF Single Area", "VLANs & Trunking", "ACL (Standard/Extended)", "NAT (Static/Dynamic)", "BGP Basics"])
difficulty = st.sidebar.select_slider("Difficulty Level", ["Junior Admin", "Network Engineer", "CCIE Expert"])

# --- THE SYSTEM: PROMPT ENGINEERING ---
# We force the AI to return JSON so we can parse it for the diagram.
def get_lab_prompt(topic, difficulty):
    return f"""
    Act as a Cisco Certified Internetwork Expert (CCIE).
    Create a CCNA Practice Lab for the topic: {topic}.
    Difficulty Level: {difficulty}.

    You MUST return the output in valid JSON format ONLY. Do not add markdown backticks (```json).
    Structure the JSON exactly like this:
    {{
        "lab_title": "String",
        "scenario_description": "String (Short business context)",
        "topology_connections": [
            "Router1 (G0/0) -> Switch1 (G0/1)",
            "Switch1 (F0/1) -> PC1"
        ],
        "device_configurations": {{
            "Router1": "IP: 192.168.1.1/24",
            "PC1": "IP: 192.168.1.10/24"
        }},
        "tasks": [
            "Step 1: ...",
            "Step 2: ..."
        ],
        "solution_commands": "Full IOS command list to solve it",
        "verification_commands": "List of 'show' commands to verify"
    }}
    """

# --- THE LOGIC ---
def generate_lab():
    if not api_key:
        st.error("Please enter the API Key in the sidebar!")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    with st.spinner('🤖 Designing Network Topology...'):
        try:
            response = model.generate_content(get_lab_prompt(topic, difficulty))
            # Clean up if AI adds markdown
            clean_text = response.text.replace("```json", "").replace("```", "")
            lab_data = json.loads(clean_text)
            return lab_data
        except Exception as e:
            st.error(f"Error generating lab: {e}")
            return None

# --- THE UI ---
st.title("⚡ Infinite CCNA Lab Generator")
st.markdown("### For: Dad's IT Firm | Powered by AI")

if st.sidebar.button("Generate New Lab"):
    lab_data = generate_lab()
    
    if lab_data:
        # Save data to session state to keep it on screen
        st.session_state['lab_data'] = lab_data

# Display Logic
if 'lab_data' in st.session_state:
    data = st.session_state['lab_data']
    
    # 1. Header
    st.header(f"Lab: {data['lab_title']}")
    st.info(f"📝 **Scenario:** {data['scenario_description']}")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📍 Topology Map")
        # Draw the graph
        graph = graphviz.Digraph()
        graph.attr(rankdir='LR') # Left to Right layout
        
        for connection in data['topology_connections']:
            # Simple parsing of "A -> B" logic
            try:
                parts = connection.split('->')
                src = parts[0].strip()
                dst = parts[1].strip()
                graph.edge(src, dst)
            except:
                pass # Skip bad lines
        
        st.graphviz_chart(graph)
        
        st.subheader("IP Table / Constraints")
        st.json(data['device_configurations'])

    with col2:
        st.subheader("🛠️ Mission Tasks")
        for i, task in enumerate(data['tasks']):
            st.write(f"**{i+1}.** {task}")
            
    st.divider()
    
    with st.expander("🔐 REVEAL SOLUTION KEY (Instructor Only)"):
        st.subheader("Verification")
        st.write(data['verification_commands'])
        st.subheader("IOS Commands")
        st.code(data['solution_commands'], language='bash')

    # DATA COLLECTION (The "System -> Data" Step)
    # In a real app, you would save this JSON to a database here.
    st.download_button(
        label="Download Lab as JSON",
        data=json.dumps(data, indent=4),
        file_name=f"lab_{topic.replace(' ', '_')}.json",
        mime="application/json"
    )