from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from analyst.llm import Plan


def test_chat_approval_result_and_clear(monkeypatch):
    monkeypatch.setenv('APP_PASSWORD', 'test-password')
    monkeypatch.setenv('GROQ_API_KEY', 'fake')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://unused')
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / 'app.py').run()
    app.text_input[0].set_value('test-password')
    app.button[0].click().run()
    assert not app.exception
    with patch('analyst.llm.generate', return_value=Plan(
        sql='SELECT COUNT(*) FROM analytics.sales', explanation='Count sales.')):
        app.chat_input[0].set_value('How many sales?').run()
    assert not app.exception
    assert app.session_state['pending']
    with patch('analyst.db.query', return_value={
        'columns': ['n'], 'rows': [(1080,)], 'truncated': False}) as execute:
        next(b for b in app.button if b.label == 'Run approved query').click().run()
        execute.assert_called_once()
    assert not app.exception
    assert len(app.dataframe) == 1
    assert app.dataframe[0].value.iloc[0, 0] == 1080
    next(b for b in app.button if b.label == 'Clear session').click().run()
    assert len(app.text_input) == 1
