import streamlit as st
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalysisHistoryManager:
    """
    사용자의 분석 기록을 관리하고 사이드바에 표시합니다.
    이 클래스는 사용자가 이전에 수행한 분석 내역을 저장하고,
    필요할 때 다시 참조할 수 있도록 돕습니다.
    """
    HISTORY_KEY = "analysis_history"

    @staticmethod
    def initialize():
        if AnalysisHistoryManager.HISTORY_KEY not in st.session_state:
            st.session_state[AnalysisHistoryManager.HISTORY_KEY] = []

    @staticmethod
    def save_to_history(file_name: str, item_count: int, processing_time: float):
        """분석 결과를 기록에 추가합니다."""
        AnalysisHistoryManager.initialize()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "file_name": file_name,
            "item_count": item_count,
            "processing_time": f"{processing_time:.1f}초"
        }
        st.session_state[AnalysisHistoryManager.HISTORY_KEY].insert(0, entry) # Add to top
        # Keep history size limited
        # if len(st.session_state[AnalysisHistoryManager.HISTORY_KEY]) > st.session_state.MAX_HISTORY_SIZE: # MAX_HISTORY_SIZE is in app.py
        #     st.session_state[AnalysisHistoryManager.HISTORY_KEY].pop()
        logger.info(f"Analysis history saved: {entry}")

    @staticmethod
    def display_sidebar_history():
        """사이드바에 분석 기록을 표시합니다."""
        AnalysisHistoryManager.initialize()
        st.markdown("### 📚 분석 기록")
        if st.session_state[AnalysisHistoryManager.HISTORY_KEY]:
            for i, entry in enumerate(st.session_state[AnalysisHistoryManager.HISTORY_KEY]):
                st.markdown(f"- **{entry['file_name']}** ({entry['timestamp']})")
                st.caption(f"  {entry['item_count']}개 항목, {entry['processing_time']}")
        else:
            st.info("아직 분석 기록이 없습니다.")

class SessionStateManager:
    """
    Streamlit 세션 상태를 관리하고 초기화합니다.
    """
    @staticmethod
    def initialize():
        """필요한 세션 상태 변수들을 초기화합니다."""
        if "show_progress" not in st.session_state:
            st.session_state.show_progress = True
        if "auto_clean" not in st.session_state:
            st.session_state.auto_clean = True
        if "use_rag" not in st.session_state:
            st.session_state.use_rag = True
        # Removed image-related session states
        # if "current_ingredients" not in st.session_state:
        #     st.session_state.current_ingredients = []
        # if "current_ocr_result" not in st.session_state:
        #     st.session_state.current_ocr_result = None
        # if "image_analysis_complete" not in st.session_state:
        #     st.session_state.image_analysis_complete = False
        if "MAX_HISTORY_SIZE" not in st.session_state:
            st.session_state.MAX_HISTORY_SIZE = 10 # Define MAX_HISTORY_SIZE here
        
        # Chatbot related
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "rag_system" not in st.session_state:
            st.session_state.rag_system = None
        if "analyzer" not in st.session_state:
            st.session_state.analyzer = None

    @staticmethod
    def reset_chatbot():
        """챗봇 관련 세션 상태를 초기화합니다."""
        st.session_state.messages = []
        st.session_state.rag_system = None
        st.session_state.analyzer = None
        logger.info("Chatbot session state reset.")

class ChatbotAnalyzer:
    """
    AI 챗봇 분석 섹션을 관리합니다.
    """
    @staticmethod
    def display_analysis_section(dataframe_path: str): # Changed from ingredients to dataframe_path
        """AI 분석 섹션을 표시하고 챗봇과 상호작용합니다."""
        # 챗봇 초기화
        if st.session_state.rag_system is None:
            from frontend.services.rag import OptimizedRAGSystem
            st.session_state.rag_system = OptimizedRAGSystem()
            logger.info("RAGSystem initialized.")
        
        if st.session_state.analyzer is None:
            from frontend.services.chatbot import IngredientsAnalyzer # Renamed to ChatbotService or similar
            st.session_state.analyzer = IngredientsAnalyzer(st.session_state.rag_system) # Needs to be adapted for CSV
            logger.info("IngredientsAnalyzer initialized.")

        # 챗봇 메시지 표시
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # 사용자 입력 처리
        if prompt := st.chat_input("모델에 대해 궁금한 점을 물어보세요."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("AI가 답변을 생성 중입니다..."):
                    # response = st.session_state.analyzer.analyze_ingredients_with_rag(ingredients, prompt) # Needs adaptation
                    response = st.session_state.analyzer.analyze_model_with_rag(dataframe_path, prompt) # New function
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
