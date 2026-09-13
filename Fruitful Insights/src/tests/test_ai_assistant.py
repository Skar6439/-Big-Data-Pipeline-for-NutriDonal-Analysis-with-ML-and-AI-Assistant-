import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_assistant import (
    generate_sql_from_question,
    execute_sql_query,
    ask_question
)

class TestAIAssistant:

    def test_generate_sql_simple(self):
        """Test SQL generation for a simple question"""
        question = "What is the average calories?"
        sql = generate_sql_from_question(question)

        assert sql is not None
        assert "SELECT" in sql.upper()
        assert "CALORIES" in sql.upper()
        assert "clean_fruits" in sql.lower()

    def test_generate_sql_with_filter(self):
        """Test SQL generation with a filter"""
        question = "Which fruits have more than 100 calories?"
        sql = generate_sql_from_question(question)

        assert sql is not None
        assert "SELECT" in sql.upper()
        assert "WHERE" in sql.upper()
        assert "100" in sql

    def test_execute_sql_valid(self):
        """Test executing a valid SQL query"""
        sql = "SELECT COUNT(*) as total FROM clean_fruits"
        results, error = execute_sql_query(sql)

        assert error is None
        assert results is not None
        assert len(results) > 0
        assert 'total' in results[0]

    def test_execute_sql_invalid(self):
        """Test executing an invalid SQL query (should handle gracefully)"""
        sql = "SELECT invalid_column FROM clean_fruits"
        results, error = execute_sql_query(sql)

        assert results is None
        assert error is not None
        assert "SQL Error" in error

    def test_execute_sql_non_select(self):
        """Test that non-SELECT queries are blocked"""
        sql = "DELETE FROM clean_fruits WHERE fruit_id = 1"
        results, error = execute_sql_query(sql)

        assert results is None
        assert error is not None
        assert "Only SELECT queries are allowed" in error

    def test_ask_question_normal(self):
        """Test full question-answer flow"""
        question = "Which fruit has the most sugar?"
        answer = ask_question(question)

        assert answer is not None
        assert len(answer) > 0
        # Answer should mention a fruit name and sugar value
        assert "sugar" in answer.lower() or "g" in answer

    def test_ask_question_unanswerable(self):
        """Test how assistant handles unanswerable questions"""
        question = "What is the weather today?"
        answer = ask_question(question)

        assert answer is not None
        # Should gracefully handle or ask for clarification
        # (Not crash with an exception)

    def test_ask_question_ambiguous(self):
        """Test how assistant handles ambiguous questions"""
        question = "Tell me about fruits"
        answer = ask_question(question)

        assert answer is not None
        # Should handle gracefully

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])