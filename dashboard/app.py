import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path
import sys

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import pipeline functions
from pipeline.ocr import extract_text
from pipeline.gemini_fallback import extract_with_gemini
from pipeline.validator import normalize

# Page configuration
st.set_page_config(page_title="Invoice Analytics Dashboard", layout="wide")

# Title
st.title("📊 InvoiceIQ")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload Data", "📋 Query Data", "📈 Analytics", "⬇️ Download"])

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None

# ============ TAB 1: UPLOAD DATA ============
with tab1:
    st.subheader("📤 Upload Data")
    
    upload_type = st.radio("Choose upload type:", ["CSV File", "PDF Invoice"], horizontal=True)
    
    if upload_type == "CSV File":
        st.info("Upload a CSV file to analyze invoice data")
        
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=["csv"],
            help="Upload a CSV file with your data"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state.df = df
                
                st.success(f"✅ File uploaded successfully! ({len(df)} rows, {len(df.columns)} columns)")
                
                # Display preview
                st.subheader("📋 Data Preview")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Display basic info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Rows", len(df))
                with col2:
                    st.metric("Total Columns", len(df.columns))
                with col3:
                    st.metric("File Size", f"{uploaded_file.size / 1024:.2f} KB")
                
                # Display column info
                st.subheader("📊 Column Information")
                col_info = pd.DataFrame({
                    "Column Name": df.columns,
                    "Data Type": df.dtypes.values,
                    "Non-Null Count": df.count().values,
                    "Null Count": df.isnull().sum().values
                })
                st.dataframe(col_info, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    else:  # PDF Invoice
        st.info("Upload PDF invoice file(s) to extract invoice data")
        
        pdf_files = st.file_uploader(
            "Choose PDF file(s)",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload one or more PDF invoice files"
        )
        
        if pdf_files:
            st.write(f"Uploaded {len(pdf_files)} PDF file(s)")
            
            if st.button("🚀 Process PDFs", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                all_invoices = []
                all_line_items = []
                
                for idx, pdf_file in enumerate(pdf_files):
                    try:
                        status_text.text(f"Processing: {pdf_file.name} ({idx + 1}/{len(pdf_files)})")
                        
                        # Save temp file
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                            tmp_file.write(pdf_file.getbuffer())
                            tmp_path = tmp_file.name
                        
                        # Extract text from PDF
                        text = extract_text(tmp_path)
                        
                        if not text or not text.strip():
                            st.warning(f"⚠️ No text extracted from {pdf_file.name}")
                            os.unlink(tmp_path)
                            continue
                        
                        # Extract invoice data using Gemini or fallback
                        data = extract_with_gemini(text)
                        
                        if not data:
                            st.warning(f"⚠️ Could not parse data from {pdf_file.name}")
                            os.unlink(tmp_path)
                            continue
                        
                        # Normalize data
                        data = normalize(data)
                        
                        # Add to results
                        all_invoices.append({
                            "invoice_number": data.get("invoice_number", ""),
                            "vendor": data.get("vendor", ""),
                            "date": data.get("date", ""),
                            "total_amount": data.get("total_amount", 0)
                        })
                        
                        # Add line items
                        for item in data.get("line_items", []):
                            item["invoice_number"] = data.get("invoice_number", "")
                            all_line_items.append(item)
                        
                        progress = (idx + 1) / len(pdf_files)
                        progress_bar.progress(progress)
                        
                        # Clean up temp file
                        os.unlink(tmp_path)
                        
                    except Exception as e:
                        st.warning(f"⚠️ Error processing {pdf_file.name}: {str(e)}")
                
                status_text.text("✅ Processing complete!")
                
                # Display results
                if all_invoices or all_line_items:
                    st.success(f"✅ Successfully processed {len(all_invoices)} invoice(s)")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Invoices", len(all_invoices))
                    with col2:
                        if all_line_items:
                            st.metric("Total Line Items", len(all_line_items))
                    
                    # Create DataFrames for display and download
                    df_invoices = pd.DataFrame(all_invoices)
                    df_line_items = pd.DataFrame(all_line_items)
                    
                    # Store in session state
                    st.session_state.df = df_line_items
                    
                    # Display preview
                    st.subheader("📋 Preview of Processed Data")
                    
                    tab_preview1, tab_preview2 = st.tabs(["Invoices", "Line Items"])
                    
                    with tab_preview1:
                        st.dataframe(df_invoices, use_container_width=True)
                    
                    with tab_preview2:
                        st.dataframe(df_line_items, use_container_width=True)
                    
                    # Download buttons
                    st.subheader("⬇️ Download Processed Files")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        csv_invoices = df_invoices.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Invoices CSV",
                            data=csv_invoices,
                            file_name="processed_invoices.csv",
                            mime="text/csv",
                            key="download_invoices_pdf"
                        )
                    
                    with col2:
                        csv_line_items = df_line_items.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Line Items CSV",
                            data=csv_line_items,
                            file_name="processed_line_items.csv",
                            mime="text/csv",
                            key="download_line_items_pdf"
                        )
                else:
                    st.error("❌ No invoices were successfully processed")

# ============ TAB 2: QUERY DATA ============
with tab2:
    st.subheader("🔍 Query & Filter Data")
    
    if st.session_state.df is None:
        st.warning("⚠️ Please upload a CSV file first in the Upload Data tab")
    else:
        df = st.session_state.df
        
        # Filter options
        st.write("### Filter Options")
        
        # Create filter columns
        col1, col2, col3 = st.columns(3)
        
        # Column selector for filtering
        with col1:
            filter_column = st.selectbox(
                "Select column to filter",
                options=df.columns,
                key="filter_col"
            )
        
        # Get unique values for the selected column
        unique_values = df[filter_column].unique()
        
        with col2:
            if len(unique_values) <= 20:
                # Use multiselect for small number of values
                selected_values = st.multiselect(
                    f"Select values from {filter_column}",
                    options=sorted([str(v) for v in unique_values]),
                    default=sorted([str(v) for v in unique_values])[:5] if len(unique_values) > 0 else [],
                    key="filter_values"
                )
                
                if selected_values:
                    filtered_df = df[df[filter_column].astype(str).isin(selected_values)]
                else:
                    filtered_df = df
            else:
                # Use text search for large number of values
                search_term = st.text_input(
                    f"Search in {filter_column}",
                    key="search_term"
                )
                if search_term:
                    filtered_df = df[df[filter_column].astype(str).str.contains(search_term, case=False, na=False)]
                else:
                    filtered_df = df
        
        # Search in all columns
        with col3:
            global_search = st.text_input(
                "Search across all columns",
                key="global_search"
            )
            if global_search:
                mask = df.astype(str).apply(lambda x: x.str.contains(global_search, case=False, na=False)).any(axis=1)
                filtered_df = df[mask]
        
        # Display filtered results
        st.subheader(f"Results ({len(filtered_df)} rows)")
        st.dataframe(filtered_df, use_container_width=True)
        
        # Display statistics for filtered data
        if len(filtered_df) > 0:
            st.subheader("📊 Filtered Data Statistics")
            
            # Numeric columns statistics
            numeric_cols = filtered_df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                stats_df = filtered_df[numeric_cols].describe().T
                st.dataframe(stats_df, use_container_width=True)

# ============ TAB 3: ANALYTICS ============
with tab3:
    st.subheader("📈 Data Analytics")
    
    if st.session_state.df is None:
        st.warning("⚠️ Please upload a CSV file first in the Upload Data tab")
    else:
        df = st.session_state.df
        
        # Get numeric and categorical columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        # Analytics by numeric columns
        if len(numeric_cols) > 0:
            st.subheader("Numeric Data Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                col_for_chart = st.selectbox(
                    "Select numeric column for distribution",
                    options=numeric_cols,
                    key="numeric_col"
                )
                
                st.write(f"### Distribution of {col_for_chart}")
                fig, ax = plt.subplots()
                ax.hist(df[col_for_chart].dropna(), bins=30, edgecolor='black')
                ax.set_xlabel(col_for_chart)
                ax.set_ylabel("Frequency")
                st.pyplot(fig)
            
            with col2:
                st.write(f"### Statistics for {col_for_chart}")
                stats = df[col_for_chart].describe()
                st.dataframe(stats)
        
        # Analytics by categorical columns
        if len(categorical_cols) > 0:
            st.subheader("Categorical Data Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                cat_col = st.selectbox(
                    "Select categorical column",
                    options=categorical_cols,
                    key="cat_col"
                )
                
                st.write(f"### Value Counts for {cat_col}")
                value_counts = df[cat_col].value_counts().head(10)
                st.bar_chart(value_counts)
            
            with col2:
                st.write(f"### Top Values in {cat_col}")
                top_values = df[cat_col].value_counts().head(10)
                st.dataframe(top_values)
        
        # Correlation heatmap
        if len(numeric_cols) > 1:
            st.subheader("Correlation Analysis")
            
            corr_matrix = df[numeric_cols].corr()
            
            fig, ax = plt.subplots(figsize=(10, 8))
            im = ax.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
            
            ax.set_xticks(range(len(numeric_cols)))
            ax.set_yticks(range(len(numeric_cols)))
            ax.set_xticklabels(numeric_cols, rotation=45, ha='right')
            ax.set_yticklabels(numeric_cols)
            
            # Add correlation values
            for i in range(len(numeric_cols)):
                for j in range(len(numeric_cols)):
                    text = ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                                 ha="center", va="center", color="black", fontsize=9)
            
            plt.colorbar(im, ax=ax)
            st.pyplot(fig)

# ============ TAB 4: DOWNLOAD ============
with tab4:
    st.subheader("⬇️ Download Data")
    
    if st.session_state.df is None:
        st.warning("⚠️ Please upload a CSV file first in the Upload Data tab")
    else:
        df = st.session_state.df
        
        # Download original data
        st.subheader("📥 Download Original Data")
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name="data.csv",
            mime="text/csv",
            key="download_csv"
        )
        
        # Export as Excel
        try:
            st.subheader("📊 Download as Excel")
            
            from io import BytesIO
            
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Data', index=False)
            
            buffer.seek(0)
            
            st.download_button(
                label="📊 Download as Excel",
                data=buffer.getvalue(),
                file_name="data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel"
            )
        except ImportError:
            st.info("Install openpyxl to export as Excel: `pip install openpyxl`")
        
        # Download filtered data
        st.subheader("⬇️ Download Filtered Data")
        
        # Allow user to select specific columns
        columns_to_download = st.multiselect(
            "Select columns to download",
            options=df.columns,
            default=df.columns.tolist(),
            key="cols_download"
        )
        
        if columns_to_download:
            filtered_for_download = df[columns_to_download]
            csv_filtered = filtered_for_download.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Selected Columns as CSV",
                data=csv_filtered,
                file_name="filtered_data.csv",
                mime="text/csv",
                key="download_filtered"
            )
        
        # Summary statistics
        st.subheader("📊 Data Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Rows", len(df))
        with col2:
            st.metric("Total Columns", len(df.columns))
        with col3:
            null_count = df.isnull().sum().sum()
            st.metric("Missing Values", null_count)
        with col4:
            numeric_count = len(df.select_dtypes(include=['number']).columns)
            st.metric("Numeric Columns", numeric_count)

# ============ FOOTER ============
st.divider()
st.sidebar.divider()
st.sidebar.info(
    "💡 **Tips:**\n"
    "- Upload CSV in Tab 1\n"
    "- Query & filter data in Tab 2\n"
    "- View analytics in Tab 3\n"
    "- Download results in Tab 4"
)
