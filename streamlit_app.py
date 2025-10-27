import streamlit as st
from sympy import symbols, simplify, factor, diff, integrate, solve, sin, cos, tan, log, exp, sqrt, latex
from sympy.parsing.sympy_parser import parse_expr
import re

# --- Streamlit setup ---
st.set_page_config(page_title="Polished Math Solver", page_icon="🧮")
st.title("🧮 Polished Textbook-Style Math Solver")
st.write("Type math expressions naturally and see results beautifully rendered in LaTeX!")

# --- Initialize history ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- Operation selection ---
operation = st.selectbox(
    "Choose operation:",
    ("Simplify", "Factor", "Solve Equation", "Derivative", "Integral")
)

# --- Expression input ---
expr_input = st.text_input("Enter your math expression (e.g., 3x^2 + sin(x)):", "")
var_input = st.text_input("Enter main variable (e.g., x):", "x")

# --- Preprocessing function ---
def preprocess_expression(expr):
    """Convert user-friendly notation to Python syntax"""
    expr = expr.replace("^", "**")
    expr = re.sub(r'(\d)([a-zA-Z(])', r'\1*\2', expr)
    expr = re.sub(r'([a-zA-Z)])([a-zA-Z(])', r'\1*\2', expr)
    return expr

# --- Solve button ---
if st.button("Solve"):
    if not expr_input.strip():
        st.error("❌ Please enter a valid expression.")
    else:
        try:
            expr_fixed = preprocess_expression(expr_input)
            var = symbols(var_input)
            allowed_functions = {
                "sin": sin, "cos": cos, "tan": tan,
                "log": log, "exp": exp, "sqrt": sqrt,
                var_input: var
            }

            # Handle equations with '='
            if "=" in expr_fixed and operation == "Solve Equation":
                lhs, rhs = expr_fixed.split("=", 1)
                lhs_expr = parse_expr(lhs, local_dict=allowed_functions)
                rhs_expr = parse_expr(rhs, local_dict=allowed_functions)
                expr = lhs_expr - rhs_expr
                result = solve(expr, var)
            else:
                expr = parse_expr(expr_fixed, local_dict=allowed_functions)
                if operation == "Simplify":
                    result = simplify(expr)
                elif operation == "Factor":
                    result = factor(expr)
                elif operation == "Derivative":
                    result = diff(expr, var)
                elif operation == "Integral":
                    result = integrate(expr, var)
                elif operation == "Solve Equation":
                    result = solve(expr, var)

            # Add to history
            st.session_state.history.append((expr, operation, result))

            # Display results
            st.success("✅ Calculation complete!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Input:**")
                st.latex(latex(expr))
            
            with col2:
                st.write("**Result:**")
                st.write(result)

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Tip: Make sure your expression uses valid syntax (e.g., 3*x^2 + sin(x))")

# --- Display calculation history ---
if st.session_state.history:
    st.divider()
    st.write("### 🕘 Calculation History")
    for i, (expr_obj, op, res) in enumerate(reversed(st.session_state.history[-10:]), 1):
        with st.expander(f"{i}. **{op}**: {latex(expr_obj)[:50]}..."):
            st.write("**Expression:**")
            st.write(expr_obj)
            st.write("**Result:**")
            st.write(res)
