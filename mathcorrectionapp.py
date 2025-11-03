# streamlit_math_solver_app.py
# A single-file Streamlit app for solving, differentiating, integrating,
# simplifying, factoring, and evaluating math expressions using SymPy.

import streamlit as st
from sympy import (
    sympify, Symbol, diff, integrate, Eq, solve, simplify,
    factor, expand, latex
)
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application
)

# -----------------------------
# Helper Functions
# -----------------------------
TRANSFORMS = (standard_transformations + (implicit_multiplication_application,))

def safe_parse(expr_str: str):
    """Parse a string safely into a SymPy expression."""
    expr_str = expr_str.strip()
    if not expr_str:
        raise ValueError("Empty expression")
    return parse_expr(expr_str, transformations=TRANSFORMS)

def to_latex_str(expr):
    try:
        return latex(expr)
    except Exception:
        return str(expr)

# -----------------------------
# Streamlit App UI
# -----------------------------
st.set_page_config(page_title="Math Solver", layout="centered")
st.title("🧮 Math Solver App")
st.write("Solve, simplify, differentiate, integrate, or evaluate math expressions interactively.")

# Sidebar
with st.sidebar:
    st.header("Options")
    operation = st.selectbox(
        "Operation",
        [
            "Simplify",
            "Differentiate",
            "Integrate",
            "Solve for variable",
            "Factor",
            "Expand",
            "Evaluate (numeric)",
        ],
    )

    var_input = st.text_input("Variable (for differentiation/integration/solve)", value="x")
    numeric_subs = st.text_area(
        "Numeric substitutions (e.g. x=2, y=3) — used for Evaluate and Solve",
        value="",
    )
    st.markdown("---")
    st.markdown("💡 Use `sin(x)`, `cos(x)`, `exp(x)`, `log(x)`, `sqrt(x)`, and `^` for powers (e.g., `x^2`).")

# Main layout
col1, col2 = st.columns([1, 1])
with col1:
    input_expr = st.text_area("Enter your expression or equation", height=180)
    st.caption("Examples: `x^2 + 2*x + 1`, `sin(x)/x`, `x^3 - 3*x + 2 = 0`")
    run = st.button("Run")

if run:
    try:
        # --------------------------------
        # Solve for variable
        # --------------------------------
        if operation == "Solve for variable":
            if "=" in input_expr:
                left, right = input_expr.split("=", 1)
                eq = Eq(safe_parse(left), safe_parse(right))
            else:
                eq = Eq(safe_parse(input_expr), 0)

            var = Symbol(var_input.strip() or "x")
            solutions = solve(eq, var)

            with col2:
                st.subheader("Solutions")
                if not solutions:
                    st.write("No symbolic solutions found.")
                else:
                    for sol in solutions:
                        st.latex(to_latex_str(sol))

        # --------------------------------
        # Differentiate
        # --------------------------------
        elif operation == "Differentiate":
            expr = safe_parse(input_expr)
            var = Symbol(var_input.strip() or "x")
            result = diff(expr, var)
            with col2:
                st.subheader("Derivative")
                st.latex(to_latex_str(result))

        # --------------------------------
        # Integrate
        # --------------------------------
        elif operation == "Integrate":
            expr = safe_parse(input_expr)
            var = Symbol(var_input.strip() or "x")
            result = integrate(expr, var)
            with col2:
                st.subheader("Indefinite Integral")
                st.latex(to_latex_str(result))

        # --------------------------------
        # Simplify
        # --------------------------------
        elif operation == "Simplify":
            expr = safe_parse(input_expr)
            result = simplify(expr)
            with col2:
                st.subheader("Simplified Expression")
                st.latex(to_latex_str(result))

        # --------------------------------
        # Factor
        # --------------------------------
        elif operation == "Factor":
            expr = safe_parse(input_expr)
            result = factor(expr)
            with col2:
                st.subheader("Factored Expression")
                st.latex(to_latex_str(result))

        # --------------------------------
        # Expand
        # --------------------------------
        elif operation == "Expand":
            expr = safe_parse(input_expr)
            result = expand(expr)
            with col2:
                st.subheader("Expanded Expression")
                st.latex(to_latex_str(result))

        # --------------------------------
        # Evaluate numeric
        # --------------------------------
        elif operation == "Evaluate (numeric)":
            expr = safe_parse(input_expr)
            subs_pairs = {}
            if numeric_subs.strip():
                for part in numeric_subs.split(","):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        k, v = k.strip(), v.strip()
                        try:
                            subs_pairs[Symbol(k)] = float(safe_parse(v))
                        except Exception:
                            subs_pairs[Symbol(k)] = safe_parse(v)
            val = expr.evalf(subs=subs_pairs) if subs_pairs else expr.evalf()
            with col2:
                st.subheader("Numeric Result")
                st.latex(to_latex_str(val))

        else:
            st.error("Unknown operation.")

    except Exception as e:
        st.error(f"⚠️ Error: {e}")

# Footer
st.markdown("---")
st.caption("Built with ❤️ using Streamlit + SymPy")

