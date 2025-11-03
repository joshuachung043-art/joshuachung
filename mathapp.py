# streamlit_math_solver_app.py
# A single-file Streamlit app that solves/simplifies/differentiates/integrates equations
# and is ready to be pushed to GitHub and deployed on Streamlit Cloud.

import streamlit as st
from sympy import (
    sympify,
    Symbol,
    diff,
    integrate,
    Eq,
    solve,
    simplify,
    factor,
    expand,
    latex,
)
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)

# --- Helper functions -----------------------------------------------------
TRANSFORMS = (standard_transformations + (implicit_multiplication_application,))


def safe_parse(expr_str: str):
    """Parse a string into a SymPy expression safely (as much as SymPy allows)."""
    expr_str = expr_str.strip()
    if not expr_str:
        raise ValueError("Empty expression")
    return parse_expr(expr_str, transformations=TRANSFORMS)


def to_latex_str(expr):
    try:
        return latex(expr)
    except Exception:
        return str(expr)


# --- Streamlit UI --------------------------------------------------------
st.set_page_config(page_title="Math Solver — Streamlit", layout="centered")
st.title("🧮 Math Solver — Streamlit")
st.write("Type an expression or equation on the left and choose an operation.")

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

    # variable input only for operations that need it
    var_input = st.text_input("Variable (for differentiate/integrate/solve)", value="x")
    numeric_subs = st.text_area(
        "Numeric substitutions (e.g. x=2, y=3) — used for Evaluate and Solve",
        value="",
    )
    show_steps = st.checkbox("Show steps (where available)", value=False)
    st.markdown("---")
    st.markdown(
        "**Hints:** use `sin(x)`, `cos(x)`, `exp(x)`, `log(x)`, `sqrt(x)`, and `^` for power, e.g. `x^2`."
    )

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    input_expr = st.text_area("Enter expression or equation", height=180)
    st.caption("Examples: `x^2 + 2*x + 1`, `sin(x)/x`, `x**2 - 4 = 0`, `integrand: x*sin(x)`")
    if st.button("Run"):
        st.session_state.run = True

run_pressed = st.button("Run (again)") or st.session_state.get("run", False)

if run_pressed:
    try:
        if operation == "Solve for variable":
            # If user entered an equation like 'x^2-4=0' we try to parse both sides
            if "=" in input_expr:
                left, right = input_expr.split("=", 1)
                left_e = safe_parse(left)
                right_e = safe_parse(right)
                eq = Eq(left_e, right_e)
            else:
                # single expression assumed equals 0
                eq = Eq(safe_parse(input_expr), 0)

            var = Symbol(var_input.strip() or "x")
            solutions = solve(eq, var)

            with col2:
                st.subheader("Solutions")
                if not solutions:
                    st.write("No solutions found (or none symbolic).")
                else:
                    for sol in solutions:
                        st.latex(to_latex_str(sol))

        elif operation == "Differentiate":
            expr = safe_parse(input_expr)
            var = Symbol(var_input.strip() or "x")
            deriv = diff(expr, var)
            with col2:
                st.subheader("Derivative")
                st.latex(to_latex_str(deriv))

        elif operation == "Integrate":
            expr = safe_parse(input_expr)
            var = Symbol(var_input.strip() or "x")
            integral = integrate(expr, var)
            with col2:
                st.subheader("Indefinite Integral")
                st.latex(to_latex_str(integral))

        elif operation == "Simplify":
            expr = safe_parse(input_expr)
            simp = simplify(expr)
            with col2:
                st.subheader("Simplified")
                st.latex(to_latex_str(simp))

        elif operation == "Factor":
            expr = safe_parse(input_expr)
            f = factor(expr)
            with col2:
                st.subheader("Factored")
                st.latex(to_latex_str(f))

        elif operation == "Expand":
            expr = safe_parse(input_expr)
            e = expand(expr)
            with col2:
                st.subheader("Expanded")
                st.latex(to_latex_str(e))

        elif operation == "Evaluate (numeric)":
            expr = safe_parse(input_expr)
            subs_pairs = {}
            if numeric_subs.strip():
                for part in numeric_subs.split(","):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        k = k.strip()
                        v = v.strip()
                        try:
                            subs_pairs[Symbol(k)] = float(safe_parse(v))
                        except Exception:
                            subs_pairs[Symbol(k)] = safe_parse(v)

            val = expr.evalf(subs=subs_pairs) if subs_pairs else expr.evalf()
            with col2:
                st.subheader("Numeric Evaluation")
                st.latex(to_latex_str(val))

        else:
            st.error("Unknown operation")

    except Exception as e:
        st.error(f"Error: {e}")
        st.exception(e)

# Footer / quick examples
st.markdown("---")
st.subheader("Quick examples")
st.write(
    "Try: `x^2 + 2*x + 1`, `sin(x)/x`, `x^3 - 3*x + 2 = 0`, `diff: sin(x)*cos(x)`, or `integrate: x*exp(x)`"
)


# --------------------------
# If you plan to add this to a repo, include a short README and requirements.

# README and requirements (put these into separate files when you push to GitHub):
README = r"""
# Streamlit Math Solver

This repository contains a single-file Streamlit app `streamlit_math_solver_app.py` that
lets you simplify, differentiate, integrate, factor, expand, solve, and evaluate symbolic
mathematical expressions using SymPy.

## Quick start (locally)

1. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate    # macOS / Linux
venv\Scripts\activate      # Windows
```

2. Install requirements:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
streamlit run streamlit_math_solver_app.py
```

Open the URL shown by Streamlit in your browser.

## Deploy on Streamlit Cloud

1. Push this repository to GitHub.
2. On https://streamlit.io, choose "Deploy an app" and connect your GitHub repo.
3. Point Streamlit to `streamlit_math_solver_app.py` as the main file and select the branch.
4. Ensure the `requirements.txt` is present (example below).

## requirements.txt
```
streamlit
sympy
```

"""

REQUIREMENTS_TXT = """streamlit
sympy
"""

# We show the README and requirements in Streamlit app (only for developer convenience)
with st.expander("README (for repo) - click to view"):
    st.code(README, language="markdown")

with st.expander("requirements.txt"):
    st.code(REQUIREMENTS_TXT, language="text")

# End of file
