from enum import StrEnum


class DashboardType(StrEnum):
    DASH = 'DASH'
    STREAMLIT = 'STREAMLIT'
    GRADIO = 'GRADIO'
    TAIPY = 'TAIPY'