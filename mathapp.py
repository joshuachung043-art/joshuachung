import streamlit as st
from sympy import symbols, simplify, factor, diff, integrate, solve, sympify, Eq
from sympy import sin, cos, tan, log, exp, sqrt
import re

# --- Streamlit setup ---
st.set_page_config(page_title="Math Solver App", page_icon="🧮")
st.title("🧮 Robust Math Solver")
st.write("Type math expressions naturally, like in textbooks!")

# --- User selects operation ---
operation = st.selectbox(
    "Choose the type of math operation:",
    ("Simplify", "Factor", "Solve Equation", "Derivative", "Integral")
)

# --- Input expression ---
expr_input = st.text_input("Enter your math expression:", "")

# --- Variable ---
var_input = st.text_input("Enter the main variable (e.g., x):", "x")

# --- Preprocessing ---
def preprocess_expression(expr):
    # Convert ^ to **
    expr = expr.replace("^", "**")
    # Insert multiplication only where appropriate
    expr = re.sub(r'(\d)([a-zA-Z(])', r'\1*\2', expr)      # number before variable/function
    expr = re.sub(r'([a-zA-Z)])([a-zA-Z(])', r'\1*\2', expr) # variable before variable/function
    return expr

# --- Solve button ---
if st.button("Solve"):
    if not expr_input.strip():
        st.error("❌ Please enter a valid expression.")
    else:
        try:
            expr_input_fixed = preprocess_expression(expr_input)

            var = symbols(var_input)

            allowed_functions = {
                "sin": sin, "cos": cos, "tan": tan,
                "log": log, "exp": exp, "sqrt": sqrt,
                var_input: var
            }

            # Check if the user entered an equation
            if "=" in expr_input_fixed and operation == "Solve Equation":
                lhs, rhs = expr_input_fixed.split("=")
                lhs_expr = sympify(lhs, locals=allowed_functions)
                rhs_expr = sympify(rhs, locals=allowed_functions)
                expr = Eq(lhs_expr, rhs_expr)
                result = solve(expr, var)
            else:
                expr = sympify(expr_input_fixed, locals=allowed_functions)
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
