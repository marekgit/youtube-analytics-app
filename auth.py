import streamlit as st
import hmac

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # Default password is 'admin' if no secrets file is found
        correct_password = "admin"
        
        # Try to get password from secrets if available
        try:
            if "password" in st.secrets:
                correct_password = st.secrets["password"]
        except Exception:
            # If secrets are not available, use the default password
            pass
            
        if hmac.compare_digest(st.session_state["password"], correct_password):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        if not st.session_state["password_correct"]:
            st.error("😕 Password incorrect")
    return False

def auth_required(func):
    """Decorator to require authentication before accessing a function."""
    def wrapper(*args, **kwargs):
        if check_password():
            func(*args, **kwargs)
    return wrapper
