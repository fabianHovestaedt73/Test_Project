import io

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from sklearn.preprocessing import MinMaxScaler

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Excel / CSV Analyzer & Rebuilder",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Excel / CSV Analyzer & Rebuilder")
st.markdown(
    "Upload an **Excel** (`.xlsx`, `.xls`) or **CSV** file, choose the "
    "analysis and engineering steps you want applied, then download the "
    "rebuilt dataset."
)

# ── File upload ───────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Upload your file",
    type=["xlsx", "xls", "csv"],
    help="Supported formats: Excel (.xlsx, .xls) and CSV (.csv)",
)

if uploaded_file is None:
    st.info("👆 Please upload an Excel or CSV file to get started.")
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading file …")
def load_data(file) -> pd.DataFrame:
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)


df_original = load_data(uploaded_file)

st.success(
    f"✅ Loaded **{uploaded_file.name}** — "
    f"{df_original.shape[0]:,} rows × {df_original.shape[1]} columns"
)

st.subheader("📋 Raw Data Preview")
st.dataframe(df_original.head(50), use_container_width=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.header("⚙️ Analysis & Engineering Options")

st.sidebar.markdown("### 🔍 Data Analysis")
show_shape = st.sidebar.checkbox("Shape & column info", value=True)
show_dtypes = st.sidebar.checkbox("Data types", value=True)
show_stats = st.sidebar.checkbox("Basic statistics", value=True)
show_missing = st.sidebar.checkbox("Missing values", value=True)
show_corr = st.sidebar.checkbox("Correlation matrix (numeric)", value=False)
show_dist = st.sidebar.checkbox("Distributions (numeric columns)", value=False)
show_value_counts = st.sidebar.checkbox("Value counts (categorical columns)", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 Data Engineering")
do_drop_duplicates = st.sidebar.checkbox("Remove duplicate rows", value=False)
do_drop_high_missing = st.sidebar.checkbox(
    "Drop columns with > 50 % missing values", value=False
)
missing_strategy = st.sidebar.selectbox(
    "Fill remaining missing values with",
    options=["— (do nothing) —", "Mean (numeric)", "Median (numeric)", "Mode (all columns)", "Drop rows"],
)
do_normalize = st.sidebar.checkbox("Normalize numeric columns (Min-Max)", value=False)
do_encode = st.sidebar.checkbox("One-hot encode categorical columns", value=False)

st.sidebar.markdown("---")

# ── Apply engineering steps ───────────────────────────────────────────────────
df = df_original.copy()

with st.expander("🔧 Data Engineering Steps", expanded=True):
    steps_applied = []

    if do_drop_duplicates:
        before = len(df)
        df = df.drop_duplicates()
        removed = before - len(df)
        steps_applied.append(f"Removed **{removed}** duplicate row(s).")

    if do_drop_high_missing:
        threshold = 0.5
        cols_before = df.shape[1]
        df = df.loc[:, df.isnull().mean() < threshold]
        dropped = cols_before - df.shape[1]
        steps_applied.append(
            f"Dropped **{dropped}** column(s) with more than 50 % missing values."
        )

    if missing_strategy == "Mean (numeric)":
        numeric_cols = df.select_dtypes(include="number").columns
        filled = df[numeric_cols].isnull().sum().sum()
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
        steps_applied.append(f"Filled **{filled}** missing numeric value(s) with column means.")

    elif missing_strategy == "Median (numeric)":
        numeric_cols = df.select_dtypes(include="number").columns
        filled = df[numeric_cols].isnull().sum().sum()
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        steps_applied.append(
            f"Filled **{filled}** missing numeric value(s) with column medians."
        )

    elif missing_strategy == "Mode (all columns)":
        filled = df.isnull().sum().sum()
        mode_row = df.mode()
        if not mode_row.empty:
            df = df.fillna(mode_row.iloc[0])
        steps_applied.append(
            f"Filled **{filled}** missing value(s) with column modes."
        )

    elif missing_strategy == "Drop rows":
        before = len(df)
        df = df.dropna()
        removed = before - len(df)
        steps_applied.append(f"Dropped **{removed}** row(s) containing missing values.")

    if do_normalize:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if numeric_cols:
            scaler = MinMaxScaler()
            df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
            steps_applied.append(
                f"Normalized **{len(numeric_cols)}** numeric column(s) to [0, 1]."
            )
        else:
            steps_applied.append("No numeric columns found to normalize.")

    if do_encode:
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if cat_cols:
            df = pd.get_dummies(df, columns=cat_cols, drop_first=False)
            steps_applied.append(
                f"One-hot encoded **{len(cat_cols)}** categorical column(s): "
                + ", ".join(f"`{c}`" for c in cat_cols)
            )
        else:
            steps_applied.append("No categorical columns found to encode.")

    if steps_applied:
        for step in steps_applied:
            st.markdown(f"- {step}")
        st.markdown(
            f"**Rebuilt dataset:** {df.shape[0]:,} rows × {df.shape[1]} columns"
        )
    else:
        st.info("No engineering steps selected — showing the original data.")

# ── Data Analysis ─────────────────────────────────────────────────────────────
st.subheader("🔍 Data Analysis")

if show_shape:
    with st.expander("📐 Shape & Column Info", expanded=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", f"{df.shape[0]:,}")
        col2.metric("Columns", df.shape[1])
        col3.metric("Total cells", f"{df.shape[0] * df.shape[1]:,}")
        st.write("**Columns:**", list(df.columns))

if show_dtypes:
    with st.expander("🏷️ Data Types"):
        dtype_df = pd.DataFrame(
            {"Column": df.dtypes.index, "Data Type": df.dtypes.values}
        ).reset_index(drop=True)
        st.dataframe(dtype_df, use_container_width=True)

if show_stats:
    with st.expander("📊 Basic Statistics"):
        st.dataframe(df.describe(include="all").T, use_container_width=True)

if show_missing:
    with st.expander("❓ Missing Values"):
        missing = df.isnull().sum()
        missing_pct = (df.isnull().mean() * 100).round(2)
        missing_df = pd.DataFrame(
            {"Missing count": missing, "Missing %": missing_pct}
        )
        missing_df = missing_df[missing_df["Missing count"] > 0]
        if missing_df.empty:
            st.success("🎉 No missing values found.")
        else:
            st.dataframe(missing_df, use_container_width=True)

if show_corr:
    with st.expander("📈 Correlation Matrix"):
        numeric_df = df.select_dtypes(include="number")
        if numeric_df.shape[1] < 2:
            st.warning("Not enough numeric columns to compute a correlation matrix.")
        else:
            _WIDTH_PER_COL = 1.2
            _WIDTH_PADDING = 2
            _HEIGHT_PER_COL = 1.0
            fig, ax = plt.subplots(
                figsize=(min(16, numeric_df.shape[1] * _WIDTH_PER_COL + _WIDTH_PADDING),
                         min(12, numeric_df.shape[1] * _HEIGHT_PER_COL + _WIDTH_PADDING))
            )
            sns.heatmap(
                numeric_df.corr(),
                annot=numeric_df.shape[1] <= 15,
                fmt=".2f",
                cmap="coolwarm",
                ax=ax,
            )
            st.pyplot(fig)
            plt.close(fig)

if show_dist:
    with st.expander("📉 Distributions"):
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if not numeric_cols:
            st.warning("No numeric columns available for distribution plots.")
        else:
            selected_cols = st.multiselect(
                "Select columns to plot",
                options=numeric_cols,
                default=numeric_cols[:min(4, len(numeric_cols))],
            )
            for col in selected_cols:
                fig, ax = plt.subplots(figsize=(8, 3))
                ax.hist(df[col].dropna(), bins="auto", edgecolor="white", color="#4C8BF5")
                ax.set_title(f"Distribution of `{col}`")
                ax.set_xlabel(col)
                ax.set_ylabel("Count")
                st.pyplot(fig)
                plt.close(fig)

if show_value_counts:
    with st.expander("🔢 Value Counts (Categorical)"):
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if not cat_cols:
            st.warning("No categorical columns found.")
        else:
            selected_cat = st.selectbox("Choose a column", options=cat_cols)
            vc = df[selected_cat].value_counts().reset_index()
            vc.columns = [selected_cat, "Count"]
            st.dataframe(vc, use_container_width=True)
            fig, ax = plt.subplots(figsize=(8, max(3, len(vc) * 0.35)))
            ax.barh(vc[selected_cat].astype(str)[:20], vc["Count"][:20], color="#4C8BF5")
            ax.invert_yaxis()
            ax.set_xlabel("Count")
            ax.set_title(f"Top values in `{selected_cat}`")
            st.pyplot(fig)
            plt.close(fig)

# ── Rebuilt data preview ──────────────────────────────────────────────────────
st.subheader("📋 Rebuilt Data Preview")
st.dataframe(df.head(50), use_container_width=True)

# ── Download ──────────────────────────────────────────────────────────────────
st.subheader("⬇️ Download Rebuilt Data")

col_xlsx, col_csv = st.columns(2)

with col_xlsx:
    xlsx_buffer = io.BytesIO()
    with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Rebuilt")
    st.download_button(
        label="📥 Download as Excel (.xlsx)",
        data=xlsx_buffer.getvalue(),
        file_name="rebuilt_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with col_csv:
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download as CSV (.csv)",
        data=csv_data,
        file_name="rebuilt_data.csv",
        mime="text/csv",
    )
