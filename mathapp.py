import streamlit as st
from sympy import symbols, simplify, factor, diff, integrate, solve, sympify
from sympy import sin, cos, tan, log, exp, sqrt
import re

# --- Streamlit app setup ---
st.set_page_config(page_title="Math Solver App", page_icon="🧮")
st.title("🧮 Textbook-Style Math Solver")
st.write("Type math expressions naturally, like you see in textbooks!")

# --- User selects operation ---
operation = st.selectbox(
    "Choose the type of math operation:",
    ("Simplify", "Factor", "Solve Equation", "Derivative", "Integral")
)

# --- Input expression ---
expr_input = st.text_input("Enter your math expression:", "")

# --- Variable for calculus or equations ---
var_input = st.text_input("Enter the main variable (e.g., x):", "x")

# --- Preprocessing function ---
def preprocess_expression(expr):
    """
    Convert textbook-style math input to sympy-compatible format:
    - ^ to **
    - implicit multiplication (3x -> 3*x, xy -> x*y)
    """
    # Convert ^ to **
    expr = expr.replace("^", "**")

    # Handle implicit multiplication:
    # 1. Between number and variable/function: 3x -> 3*x, 2sin(x) -> 2*sin(x)
    expr = re.sub(r'(\d)([a-zA-Z(])', r'\1*\2', expr)
    # 2. Between variable and variable/function: xy -> x*y, xsin(x) -> x*sin(x)
    expr = re.sub(r'([a-zA-Z)])([a-zA-Z(])', r'\1*\2', expr)

    return expr

# --- Solve button ---
if st.button("Solve"):
    if not expr_input.strip():
        st.error("❌ Please enter a valid expression.")
    else:
        try:
            # Preprocess input
            expr_input_fixed = preprocess_expression(expr_input)

            # Define main symbol
            var = symbols(var_input)

            # Define allowed functions
            allowed_functions = {
                "sin": sin, "cos": cos, "tan": tan,
                "log": log, "exp": exp, "sqrt": sqrt,
                var_input: var
            }

            # Convert to sympy expression
            expr = sympify(expr_input_fixed, locals=allowed_functions)

            # Perform selected operation
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
            else:
                result = "Invalid operation"

            st.success(f"✅ Result: {result}")

        except Exception as e:
            st.error(f"❌ Error: {e}")
