"""Streamlit app for AI Expense Tracker with Enterprise UI."""
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from backend import (
    load_database,
    save_database,
    normalize_username,
    current_month_key,
    ensure_user_month,
    analyze_expense_with_ai,
    add_expense_record,
    get_month_summary,
    get_user_months,
    export_to_csv,
    format_currency,
    get_all_expenses,
    get_spending_by_day,
    ALLOWED_CATEGORIES,
    get_api_key,
)

# Page configuration
st.set_page_config(
    page_title="Spendra Enterprise",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Enterprise Glassmorphism & Advanced Animations
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
    /* Global Theme & Background */
    .stApp {
        background-color: #050814;
        background-image: 
            radial-gradient(at 0% 0%, rgba(37, 20, 85, 0.4) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(13, 35, 70, 0.4) 0px, transparent 50%);
        color: #e2e8f0;
    }

    /* Keyframe Animations */
    @keyframes slideUpFade {
        0% { opacity: 0; transform: translateY(30px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 0 0 rgba(168, 85, 247, 0.4); }
        70% { box-shadow: 0 0 15px 10px rgba(168, 85, 247, 0); }
        100% { box-shadow: 0 0 0 0 rgba(168, 85, 247, 0); }
    }

    /* Apply animations to core components */
    div[data-testid="metric-container"], .feature-card, .stPlotlyChart, .stDataFrame {
        animation: slideUpFade 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        opacity: 0;
    }

    /* Cascading delays for staggered loading effect */
    div[data-testid="metric-container"]:nth-child(1) { animation-delay: 0.1s; }
    div[data-testid="metric-container"]:nth-child(2) { animation-delay: 0.2s; }
    div[data-testid="metric-container"]:nth-child(3) { animation-delay: 0.3s; }
    div[data-testid="metric-container"]:nth-child(4) { animation-delay: 0.4s; }
    .stPlotlyChart:nth-child(1) { animation-delay: 0.4s; }
    .stPlotlyChart:nth-child(2) { animation-delay: 0.5s; }

    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(10, 15, 30, 0.75) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 6px;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4);
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    }

    /* Floating Metric Cards */
    div[data-testid="metric-container"] {
        background: rgba(20, 25, 40, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px) scale(1.02);
        border-color: rgba(168, 85, 247, 0.5);
    }

    /* DataFrames / Audit Logs */
    [data-testid="stDataFrame"] {
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.1);
        overflow: hidden;
    }

    /* Typography */
    h1, h2, h3 { font-family: 'Inter', sans-serif; letter-spacing: -0.03em; }
    
    .hero-title {
        font-size: 3.5rem; /* <-- Reduced size to keep it on one line */
        font-weight: 900;
        line-height: 1.1;
        margin-bottom: 1rem;
        background: linear-gradient(120deg, #c084fc, #ec4899, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: slideUpFade 0.8s ease-out forwards;
        white-space: nowrap; /* <-- Added this to force it onto one line if possible */
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        color: #94a3b8;
        margin-bottom: 2.5rem;
        font-weight: 400;
        animation: slideUpFade 1s ease-out forwards;
    }

    /* Feature Cards */
    .feature-card {
        background: rgba(30, 41, 59, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        backdrop-filter: blur(4px);
    }
    .feature-card:hover {
        background: rgba(30, 41, 59, 0.8);
        border-color: rgba(168, 85, 247, 0.6);
        transform: translateX(10px) scale(1.02);
        box-shadow: -5px 10px 25px rgba(168, 85, 247, 0.15);
    }
    .feature-icon {
        font-size: 1.8rem;
        margin-right: 1.25rem;
        background: rgba(255,255,255,0.05);
        height: 55px;
        width: 55px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .feature-text h4 { margin: 0; color: #f8fafc; font-size: 1.1rem; font-weight: 600; }
    .feature-text p { margin: 0; color: #94a3b8; font-size: 0.9rem; margin-top: 0.3rem; }
    
    /* Social Icons */
    .social-link {
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        color: #e2e8f0 !important;
        text-decoration: none !important;
        margin-right: 10px;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    .social-link:hover {
        background: rgba(168, 85, 247, 0.2);
        border-color: rgba(168, 85, 247, 0.5);
        transform: translateY(-2px);
    }
    .social-link i { margin-right: 8px; font-size: 1.2rem; }
    .linkedin-icon { color: #0077b5; }
    .github-icon { color: #ffffff; }
    .gmail-icon { color: #ea4335; }
    .phone-icon { color: #34d399; }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "db" not in st.session_state:
    st.session_state.db = load_database()
if "username" not in st.session_state:
    st.session_state.username = None
if "current_month" not in st.session_state:
    st.session_state.current_month = current_month_key()
if "parsed_expense" not in st.session_state:
    st.session_state.parsed_expense = None

# Sidebar for navigation
st.sidebar.title("💠 Enterprise Menu")
page = st.sidebar.radio(
    "Select a page:",
    ["Dashboard", "Add Expense", "Summary & Audit", "Analytics Reports", "System Settings"],
    label_visibility="collapsed"
)

# User management in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='margin-bottom: 0;'>🔐 Secure Access</h4>", unsafe_allow_html=True)

if st.session_state.username is None:
    username_input = st.sidebar.text_input("Enter SSO / Username:", key="user_input", placeholder="e.g. mfk_admin")
    if st.sidebar.button("Authenticate", use_container_width=True):
        if username_input.strip():
            st.session_state.username = normalize_username(username_input)
            ensure_user_month(st.session_state.db, st.session_state.username, st.session_state.current_month)
            save_database(st.session_state.db)
            st.rerun()
        else:
            st.sidebar.error("Credentials cannot be empty")
else:
    st.sidebar.markdown(f"""
    <div style='background:rgba(168,85,247,0.15); padding:10px; border-radius:8px; border:1px solid rgba(168,85,247,0.3); margin-top:10px; margin-bottom:15px;'>
        <div style='font-size:0.8rem; color:#c084fc;'>Active Session</div>
        <div style='font-weight:bold; font-size:1.1rem;'><i class='fas fa-user-shield'></i> {st.session_state.username}</div>
        <div style='font-size:0.75rem; color:#94a3b8; margin-top:3px;'>Enterprise Admin Tier</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Month selection
    months = get_user_months(st.session_state.db, st.session_state.username)
    if not months:
        months = [st.session_state.current_month]
    
    selected_month = st.sidebar.selectbox(
        "Fiscal Period:",
        months,
        index=months.index(st.session_state.current_month) if st.session_state.current_month in months else 0
    )
    
    if selected_month != st.session_state.current_month:
        st.session_state.current_month = selected_month
        ensure_user_month(st.session_state.db, st.session_state.username, selected_month)
        save_database(st.session_state.db)
    
    if st.sidebar.button("➕ Open New Fiscal Period", use_container_width=True):
        new_month = st.sidebar.text_input("Format (YYYY-MM):", key="new_month_input")
        if new_month:
            ensure_user_month(st.session_state.db, st.session_state.username, new_month)
            save_database(st.session_state.db)
            st.session_state.current_month = new_month
            st.rerun()
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Terminate Session", use_container_width=True, type="secondary"):
        st.session_state.username = None
        st.session_state.current_month = current_month_key()
        st.rerun()


# Page content
if st.session_state.username is None:
    # --- SPLIT LAYOUT ENTERPRISE LANDING PAGE ---
    
    # Adjust padding to ensure it aligns nicely with the sidebar and doesn't get cut off at the bottom
    st.markdown("<style> .block-container { padding-top: 3rem; padding-bottom: 5rem; } </style>", unsafe_allow_html=True)
    
    # Create two columns: Text on the left (slightly wider), Image on the right
    col1, col2 = st.columns([1.2, 1], gap="large")
    
    with col1:
        # Left Side: Title and Subtitle
        st.markdown("""
            <div style="animation: slideUpFade 0.4s ease-out forwards;">
                <div class="hero-title" style="font-size: 3.8rem; text-align: left; margin-top: 0;">Spendra Enterprise</div>
                <div class="hero-subtitle" style="text-align: left; font-size: 1.15rem; margin-bottom: 2.5rem; max-width: 90%;">
                    Enterprise-grade financial telemetry. Automate your departmental tracking with neural-network parsing and real-time visualization matrices.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Left Side: Feature Cards (Neural Parsing Removed)
        # Note: We removed the inline flex-direction so they go back to the sleek horizontal layout
        st.markdown("""
        <div class="feature-card" style="animation-delay: 0.2s; margin-bottom: 1.2rem;">
            <div class="feature-icon"><i class="fas fa-chart-line" style="color: #3b82f6;"></i></div>
            <div class="feature-text">
                <h4 style="font-size: 1.15rem; margin-bottom: 0.2rem;">Live Telemetry</h4>
                <p style="font-size: 0.95rem;">Interactive Plotly infrastructure mapping your fiscal trajectory instantly.</p>
            </div>
        </div>
        
        <div class="feature-card" style="animation-delay: 0.4s; margin-bottom: 2rem;">
            <div class="feature-icon"><i class="fas fa-database" style="color: #10b981;"></i></div>
            <div class="feature-text">
                <h4 style="font-size: 1.15rem; margin-bottom: 0.2rem;">Secure Infrastructure</h4>
                <p style="font-size: 0.95rem;">Encrypted JSON backend with compliant CSV payload generation.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Left Side: Security Badge at the bottom
        st.markdown("""
        <div style="animation: slideUpFade 0.6s ease-out forwards;">
            <div style="background: rgba(168,85,247,0.1); border: 1px solid rgba(168,85,247,0.3); padding: 15px 20px; border-radius: 8px; display: inline-block;">
                <span style="color: #c084fc; font-weight: bold; font-size: 1.05rem;">🔐 System Locked.</span> 
                <span style="color: #e2e8f0; margin-left: 8px; font-size: 1.05rem;">Authenticate in the sidebar to access infrastructure.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Right Side: The Lottie Animation
        components.html(
            """
            <script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>
            <div style="display:flex; justify-content:center; align-items:center; width: 100%; height: 100%;">
                <div style="filter: drop-shadow(0px 10px 30px rgba(168,85,247,0.3)); width: 100%; display: flex; justify-content: center;">
                    <lottie-player
                        src="https://assets1.lottiefiles.com/packages/lf20_w51pcehl.json"
                        background="transparent"
                        speed="1"
                        style="width: 100%; max-width: 650px; animation: slideUpFade 1.0s ease-out forwards;" 
                        loop
                        autoplay
                    ></lottie-player>
                </div>
            </div>
            """,
            height=650, # Generous height so it doesn't cut off on the bottom
        )

else:
    # Dashboard page
    if page == "Dashboard":
        st.title(f"📈 Telemetry Dashboard — {st.session_state.current_month}")
        
        month_data = st.session_state.db.get(st.session_state.username, {}).get(st.session_state.current_month, {})
        summary = get_month_summary(month_data)
        
        # Top metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Gross Expenditure", format_currency(summary["total"]))
        with col2:
            st.metric("Total Ledgers", summary["item_count"])
        with col3:
            avg_spending = summary["total"] / max(1, summary["item_count"])
            st.metric("Mean Tx Value", format_currency(avg_spending))
        with col4:
            st.metric("Active Days", len(get_spending_by_day(get_all_expenses(month_data))))
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Charts 
        col1, col2 = st.columns([1, 1], gap="large")
        
        with col1:
            category_data = [
                (cat, summary["categories"][cat]["subtotal"])
                for cat in ALLOWED_CATEGORIES
                if summary["categories"][cat]["subtotal"] > 0
            ]
            
            if category_data:
                categories, amounts = zip(*category_data)
                fig_pie = go.Figure(data=[go.Pie(
                    labels=categories, 
                    values=amounts,
                    hole=0.5, 
                    marker=dict(colors=px.colors.qualitative.Bold)
                )])
                fig_pie.update_layout(
                    title="Capital Allocation Matrix",
                    height=400,
                    showlegend=True,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0'),
                    margin=dict(t=50, b=20, l=20, r=20)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No expense data mapped for this period yet.")
        
        with col2:
            spending_by_day = get_spending_by_day(get_all_expenses(month_data))
            
            if spending_by_day:
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(
                    x=list(spending_by_day.keys()),
                    y=list(spending_by_day.values()),
                    mode='lines+markers',
                    name='Burn Rate',
                    fill='tozeroy',
                    line=dict(color='#8b5cf6', width=3),
                    marker=dict(size=8, color='#f8fafc', line=dict(width=2, color='#8b5cf6'))
                ))
                fig_line.update_layout(
                    title="Temporal Burn Rate Trajectory",
                    xaxis_title="Timeline",
                    yaxis_title="Volume ($)",
                    height=400,
                    hovermode='x unified',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                    margin=dict(t=50, b=20, l=20, r=20)
                )
                st.plotly_chart(fig_line, use_container_width=True)

    # Add Expense page
    elif page == "Add Expense":
        st.title("➕ Log Transaction")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            description = st.text_area(
                "Unstructured Data Input (NLP)",
                height=120,
                placeholder="e.g., 'Procured AWS server hosting for $250.00'"
            )
        
        with col2:
            st.markdown("**System Override:**")
            manual_mode = st.checkbox("Enable Manual Data Entry")
        
        st.markdown("---")
        
        if manual_mode:
            col1, col2 = st.columns(2)
            with col1:
                item = st.text_input("Asset / Service")
                price = st.number_input("Capital Expended ($)", min_value=0.0, step=0.01)
            with col2:
                category = st.selectbox("Fiscal Category", ALLOWED_CATEGORIES)
                note = st.text_input("Audit Note (optional)")
            
            if st.button("Commit Ledger", use_container_width=True, type="primary"):
                if item and price > 0:
                    add_expense_record(
                        st.session_state.db,
                        st.session_state.username,
                        st.session_state.current_month,
                        item,
                        price,
                        category,
                        note
                    )
                    st.success(f"✅ Record Executed: {item} mapped to {category} at {format_currency(price)}")
                    st.rerun()
                else:
                    st.error("Validation Error: Asset name and non-zero capital required.")
        
        else:
            if st.button("🤖 Engage AI Processor", use_container_width=True, type="primary", key="parse_button"):
                if description.strip():
                    with st.spinner("Neural network processing natural language..."):
                        parsed = analyze_expense_with_ai(description)
                        st.session_state.parsed_expense = parsed
                        st.session_state.parse_attempted = True
                else:
                    st.error("Input stream empty. Provide text payload.")

            if st.session_state.parsed_expense:
                parsed = st.session_state.parsed_expense
                
                st.markdown(f"""
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 1.5rem; margin-bottom: 1rem; animation: slideUpFade 0.4s ease-out forwards;">
                    <div style="color: #10b981; font-weight: bold; margin-bottom: 10px;"><i class="fas fa-check-circle"></i> NLP Extraction Successful</div>
                    <h3 style="margin-top:0; color:#f8fafc;">{parsed['item']}</h3>
                    <p style="font-size: 1.4rem; font-weight: 800; color: #10b981; margin-bottom: 5px;">{format_currency(parsed['price'])}</p>
                    <div style="display: flex; gap: 15px; font-size: 0.9rem; color: #94a3b8;">
                        <span><i class="fas fa-folder"></i> <b>{parsed['category']}</b></span>
                        <span><i class="fas fa-comment-alt"></i> {parsed.get('note', 'N/A')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ Authorize & Commit", use_container_width=True, type="primary", key="confirm_add"):
                        add_expense_record(
                            st.session_state.db,
                            st.session_state.username,
                            st.session_state.current_month,
                            parsed['item'],
                            parsed['price'],
                            parsed['category'],
                            parsed.get('note', ''),
                        )
                        st.success("Ledger committed to secure storage.")
                        st.session_state.parsed_expense = None
                        st.session_state.parse_attempted = False
                        st.rerun()
                with col_b:
                    if st.button("❌ Discard", use_container_width=True, type="secondary"):
                        st.session_state.parsed_expense = None
                        st.session_state.parse_attempted = False
                        st.rerun()

            elif st.session_state.get("parse_attempted", False):
                st.warning("NLP Engine failed to parse context. Awaiting manual override.")
                with st.expander("Manual Override Protocol"):
                    item = st.text_input("Asset Name", key="fallback_item")
                    price = st.number_input("Value ($)", min_value=0.0, step=0.01, key="fallback_price")
                    category = st.selectbox("Category", ALLOWED_CATEGORIES, key="fallback_category")
                    note = st.text_input("Audit Note", key="fallback_note")
                    if st.button("Force Commit", use_container_width=True, type="secondary", key="fallback_add"):
                        if item and price > 0:
                            add_expense_record(
                                st.session_state.db,
                                st.session_state.username,
                                st.session_state.current_month,
                                item, price, category, note,
                            )
                            st.success(f"✅ Executed: {item} logged.")
                            st.session_state.parsed_expense = None
                            st.session_state.parse_attempted = False
                            st.rerun()

    # Summary & Audit page
    elif page == "Summary & Audit":
        st.title(f"📋 Financial Audit Log — {st.session_state.current_month}")
        
        month_data = st.session_state.db.get(st.session_state.username, {}).get(st.session_state.current_month, {})
        all_expenses = get_all_expenses(month_data)
        
        if not all_expenses:
            st.info("Database empty for current temporal query.")
        else:
            # Enterprise Data Grid implementation
            st.subheader("Master Ledger")
            
            # Convert to Pandas DataFrame for a clean grid view
            df = pd.DataFrame(all_expenses)
            # Reorder and format columns
            if not df.empty:
                df = df[['timestamp', 'item', 'category', 'price', 'note']]
                df.columns = ['Timestamp', 'Asset/Service', 'Classification', 'Amount ($)', 'Audit Notes']
                
                # Render interactive dataframe
                st.dataframe(
                    df,
                    use_container_width=True,
                    height=300,
                    hide_index=True,
                    column_config={
                        "Amount ($)": st.column_config.NumberColumn(
                            "Amount ($)", format="$%.2f"
                        ),
                        "Timestamp": st.column_config.DatetimeColumn(
                            "Timestamp", format="D MMM YYYY, h:mm a"
                        )
                    }
                )

            st.markdown("---")
            
            # High Impact Analysis
            st.subheader("High-Impact Transactions (Top 5)")
            top_expenses = sorted(all_expenses, key=lambda x: x["price"], reverse=True)[:5]
            
            for expense in top_expenses:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.03); border-left: 4px solid #c084fc; padding: 10px 15px; margin-bottom: 8px; border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #e2e8f0; font-size: 1.1rem;">{expense['item']}</strong><br>
                            <span style="color: #94a3b8; font-size: 0.85rem;"><i class="fas fa-tag"></i> {expense['category']} | {expense['timestamp']}</span>
                        </div>
                        <div style="font-size: 1.2rem; font-weight: bold; color: #c084fc;">
                            {format_currency(expense['price'])}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Reports page
    elif page == "Analytics Reports":
        st.title(f"📊 Deep Analytics — {st.session_state.current_month}")
        
        month_data = st.session_state.db.get(st.session_state.username, {}).get(st.session_state.current_month, {})
        summary = get_month_summary(month_data)
        
        if summary["item_count"] == 0:
            st.info("Insufficient data for model generation.")
        else:
            st.subheader("Departmental Overview")
            
            categories = []
            amounts = []
            for cat in ALLOWED_CATEGORIES:
                if summary["categories"][cat]["subtotal"] > 0:
                    categories.append(cat)
                    amounts.append(summary["categories"][cat]["subtotal"])
            
            if categories:
                fig = go.Figure(data=[
                    go.Bar(
                        x=categories, 
                        y=amounts, 
                        marker=dict(
                            color=amounts, 
                            colorscale='Plasma',
                            line=dict(color='rgba(255,255,255,0.1)', width=1)
                        )
                    )
                ])
                fig.update_layout(
                    title="Sector Allocation Analysis",
                    xaxis_title="Classification",
                    yaxis_title="Volume ($)",
                    height=450,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            st.subheader("📥 Data Egress (Export)")
            st.write("Generate compliant CSV payload for external auditing software.")
            
            if st.button("🔨 Compile CSV Payload", type="primary"):
                csv_file = export_to_csv(st.session_state.db, st.session_state.username, st.session_state.current_month)
                if csv_file:
                    st.success(f"✅ Artifact compiled: `{csv_file}`")
                    with open(csv_file, 'rb') as f:
                        st.download_button(
                            label="⬇️ Download Secure Payload",
                            data=f,
                            file_name=csv_file,
                            mime="text/csv",
                            use_container_width=True,
                        )

    # Settings page
    elif page == "System Settings":
        st.title("⚙️ System Administration")
        
        # Custom CSS for the Admin Control Panel
        st.markdown("""
        <style>
        .admin-panel-card {
            background: rgba(30, 41, 59, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 1.5rem;
            height: 100%;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .admin-card-title {
            color: #f8fafc;
            font-size: 1.15rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .admin-card-text {
            color: #94a3b8;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
            line-height: 1.5;
        }
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 10px 16px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.95rem;
            width: 100%;
        }
        .status-online {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #10b981;
        }
        .status-offline {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #ef4444;
        }
        .pulse-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        .pulse-green {
            background: #10b981;
            box-shadow: 0 0 10px #10b981;
            animation: pulse-green-anim 2s infinite;
        }
        @keyframes pulse-green-anim {
            0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.5); }
            70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
            100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
        
        /* Architecture Grid */
        .arch-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2.5rem;
            margin-top: 1rem;
        }
        .arch-card {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.05);
            padding: 1.2rem;
            border-radius: 10px;
            transition: transform 0.2s ease;
        }
        .arch-card:hover {
            transform: translateY(-2px);
            border-color: rgba(192, 132, 252, 0.3);
        }
        .arch-label {
            color: #94a3b8;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        .arch-value {
            color: #f8fafc;
            font-size: 1.1rem;
            font-weight: 600;
            margin-top: 4px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 1. Dashboard Control Modules
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            st.markdown("""
            <div class="admin-panel-card">
                <div class="admin-card-title"><i class="fas fa-microchip" style="color: #c084fc;"></i> Core Integrations</div>
                <div class="admin-card-text">Manage external API connections and neural engine endpoints for natural language processing.</div>
            """, unsafe_allow_html=True)
            
            api_key = get_api_key()
            if api_key:
                st.markdown("""
                <div class="status-indicator status-online">
                    <div class="pulse-dot pulse-green"></div>
                    Neural Engine (Groq API): Authenticated
                </div>
                </div> """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="status-indicator status-offline">
                    <div class="pulse-dot" style="background:#ef4444;"></div>
                    Neural Engine (Groq API): Disconnected
                </div>
                </div> """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="admin-panel-card">
                <div class="admin-card-title"><i class="fas fa-database" style="color: #3b82f6;"></i> Storage Layer</div>
                <div class="admin-card-text">Manually synchronize the local application memory state with the persistent JSON backend volume.</div>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 Force Database Sync", use_container_width=True):
                st.session_state.db = load_database()
                st.success("✅ State synchronized successfully.")
                
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<br><hr style='border-color: rgba(255,255,255,0.05); margin: 2rem 0;'><br>", unsafe_allow_html=True)
        
        # 2. System Architecture Grid
        st.subheader("ℹ️ System Architecture")
        st.markdown("""
        <div class="arch-grid">
            <div class="arch-card">
                <div class="arch-label">Frontend Engine</div>
                <div class="arch-value">Streamlit UI</div>
            </div>
            <div class="arch-card">
                <div class="arch-label">Data Persistence</div>
                <div class="arch-value">Secure JSON Volume</div>
            </div>
            <div class="arch-card">
                <div class="arch-label">Visualizations</div>
                <div class="arch-value">Plotly Dynamic</div>
            </div>
            <div class="arch-card">
                <div class="arch-label">NLP Model</div>
                <div class="arch-value">Groq High-Speed AI</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 3. Lead Architect Card
        st.markdown("---")
        st.subheader("👤 Lead Architect")
        
        st.markdown("""
        <style>
        .saas-profile-container {
            background-color: rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 1.5rem 2rem;
            max-width: 850px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-top: 1rem;
        }
        
        .saas-profile-header {
            display: flex;
            align-items: center;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .saas-avatar {
            width: 76px;
            height: 76px;
            min-width: 76px;
            border-radius: 50%;
            object-fit: cover;
            object-position: top center;
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 3px; /* Creates a clean, premium double-ring effect */
            background-color: #0f172a;
        }
        
        .saas-name {
            color: #f8fafc;
            font-size: 1.3rem;
            font-weight: 600;
            margin: 0 0 0.25rem 0 !important;
            letter-spacing: -0.01em;
        }
        
        .saas-role {
            color: #94a3b8;
            font-size: 0.95rem;
            margin: 0 !important;
            font-weight: 400;
        }
        
        .saas-profile-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.85rem;
            padding-top: 1.25rem;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
        }
        
        .saas-btn {
            display: inline-flex;
            align-items: center;
            gap: 0.6rem;
            background-color: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #cbd5e1 !important;
            text-decoration: none !important;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .saas-btn:hover {
            background-color: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.2);
            color: #ffffff !important;
        }
        
        .saas-btn i {
            font-size: 0.95rem;
            color: #64748b;
            transition: color 0.2s ease;
        }
        
        .saas-btn:hover i {
            color: #f8fafc;
        }

        @media (max-width: 600px) {
            .saas-profile-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }
        }
        </style>

        <div class="saas-profile-container">
            <div class="saas-profile-header">
                <img src="https://raw.githubusercontent.com/ItsFaizan-official/ItsFaizan-official/main/faizan%20pic.jpg" class="saas-avatar" alt="Mohammad Faizan Khan">
                <div>
                    <h3 class="saas-name">Mohammad Faizan Khan</h3>
                    <p class="saas-role">Enterprise Systems & AI Engineer &nbsp;|&nbsp; Professional IT Trainer</p>
                </div>
            </div>
            <div class="saas-profile-actions">
                <a href="https://www.linkedin.com/in/faizan-ngp/" target="_blank" class="saas-btn">
                    <i class="fab fa-linkedin"></i> LinkedIn
                </a>
                <a href="https://github.com/ItsFaizan-official" target="_blank" class="saas-btn">
                    <i class="fab fa-github"></i> GitHub
                </a>
                <a href="mailto:faizankhanofficial71@gmail.com" class="saas-btn">
                    <i class="fas fa-envelope"></i> Email
                </a>
                <a href="tel:+918459414568" class="saas-btn">
                    <i class="fas fa-phone-alt"></i> +91-8459414568
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)