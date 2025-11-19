from unittest.mock import Mock, patch

from praise_team import praise_team


def test_praise_team_successful_ollama_response():
    mock_response = Mock()
    mock_response.response = "Excellent work, team! 🚀"
    with patch("ollama.generate", return_value=mock_response):
        result = praise_team()
        assert isinstance(result, str)
        assert len(result) > 0
