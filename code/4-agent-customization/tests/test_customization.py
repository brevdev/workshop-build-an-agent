import json
import sys
from pathlib import Path

import numpy as np
import pytest
import requests
from fastapi.testclient import TestClient

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))
from nemo_gym_resources.langgraph_cli.app import app, score_cli_output
from training_support import prepare_examples, check_split
from bash_agent.helpers import HuggingFaceLLM


@pytest.mark.parametrize('response', ['[]', '42', 'true', '"text"', '{}',
    '{"command":"dev","port":8080.9}', '{"command":"dev","port":true}',
    '{"command":"dev","port":8080,"made_up_flag":true}'])
def test_invalid_model_output_is_worst_reward(response):
    result = TestClient(app).post('/verify', json={
        'task_id':'test', 'task_input':{'input':'Start port8080','output':{'command':'dev','port':8080}},
        'model_response':response,
    })
    assert result.status_code == 200
    assert result.json()['reward'] == -1
    assert not result.json()['exact_match']


def test_path_equivalence_does_not_hide_absolute_destination():
    ref = {'command':'new','path':'./project'}
    assert score_cli_output({'command':'new','path':'project'},ref)[0] == 1
    assert score_cli_output({'command':'new','path':'/home/alice/project'},ref)[0] == -1


def test_data_integrity_and_held_out_split():
    records = [[json.loads(line) for line in (LAB/f'data/langgraph_cli/{name}.jsonl').read_text().splitlines()]
               for name in ('train','val')]
    for rows in records:
        assert len(rows) == len(prepare_examples(rows))
    check_split(*records)
    with pytest.raises(ValueError, match='Conflicting'):
        prepare_examples([{'input':'Build it','output':{'command':'build','tag':'one'}},
                          {'input':' Build it ','output':{'command':'build','tag':'two'}}])
    with pytest.raises(ValueError, match='overlap'):
        check_split(records[0], records[0][:1])


def test_callback_uses_row_answers_and_stops_on_server_error(monkeypatch):
    cells=json.loads((LAB/'answer_key/02_grpo_training.answers.ipynb').read_text())['cells']
    source=next(''.join(c['source']) for c in cells if 'def create_nemo_gym_reward_function' in ''.join(c['source']))
    ns={'requests':requests,'np':np,'VERIFY_ENDPOINT':'http://invalid.local/verify'}
    exec(source, ns)
    sent=[]
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'reward':1}
    def post(url,json,timeout):sent.append(json);return Response()
    monkeypatch.setattr(requests,'post',post)
    result=ns['reward_fn']([[{'content':'{}'}]],answer=[{'command':'build','tag':'held-out'}])
    assert result.tolist()==[1]
    assert sent[0]['task_input']['output']['tag']=='held-out'
    def fail(*a,**kw): raise requests.ConnectionError('offline')
    monkeypatch.setattr(requests,'post',fail)
    with pytest.raises(requests.ConnectionError):
        ns['reward_fn']([[{'content':'[]'}]],answer=[{'command':'new'}])


def test_json_to_command_preserves_path_as_one_argument():
    import shlex
    model=object.__new__(HuggingFaceLLM)
    cmd=model._json_to_bash_command({'command':'new','path':'./my project; $(touch unsafe)'})
    assert shlex.split(cmd)==['langgraph','new','./my project; $(touch unsafe)']


def test_bash_does_not_execute_newline_or_substitution(tmp_path):
    from bash_agent.bash import Bash
    from bash_agent.config import Config
    bash=Bash(Config(root_dir=str(tmp_path)))
    assert bash.exec_bash_command('echo safe\ntouch INJECTED').get('error')
    result=bash.exec_bash_command('echo "$(touch INJECTED)"')
    assert '$(touch INJECTED)' in result['stdout']
    assert bash.exec_bash_command('find . -exec touch INJECTED ;').get('error')
    assert not (tmp_path/'INJECTED').exists()
    (tmp_path/'sub folder').mkdir()
    assert not bash.exec_bash_command("cd 'sub folder'").get('error')
    assert bash.exec_bash_command('pwd')['stdout'].strip()==str(tmp_path/'sub folder')


def test_false_switches_are_equivalent_to_omitted_cli_flags():
    expected={"command":"dev","port":8080,"no_browser":False}
    assert score_cli_output({"command":"dev","port":8080},expected)[0]==1
    assert score_cli_output({"command":"dev","port":8080,"no_browser":True},expected)[0]<1


def test_inference_rejects_cli_values_the_verifier_rejects():
    model=object.__new__(HuggingFaceLLM)
    assert not model._parse_tool_calls('{"command":"dev","port":8080.9}')
    assert not model._parse_tool_calls('{"command":"unknown"}')


def test_assistant_tool_call_precedes_tool_result():
    from bash_agent.helpers import Messages
    messages=Messages('system')
    call={'id':'one','type':'function','function':{'name':'exec_bash_command','arguments':'{}'}}
    messages.add_assistant_message('',tool_calls=[call])
    messages.add_tool_message('done','one')
    history=messages.to_list()
    assert history[-2]['tool_calls'][0]['id']==history[-1]['tool_call_id']


def test_generated_labels_require_seed_literals_and_requested_flags():
    from training_support import prepare_generated_examples
    good={'command':'dev','port':8080,'no_browser':False,
          'input':'Start the dev server on port8080.', 'output':{'command':'dev','port':8080}}
    invented={**good,'output':{'command':'dev','port':8080,'no_browser':True}}
    omitted={**good,'no_browser':True,'output':{'command':'dev','port':8080,'no_browser':True}}
    wrong={**good,'input':'Start the dev server on port3000.'}
    rows=prepare_generated_examples([good,invented,omitted,wrong])
    assert rows==[{'input':good['input'],'output':good['output']}]


LANGGRAPH_COMMAND = 'langgraph new ./demo --template react-agent-python'


class Translator:
    """Stands in for the fine-tuned model: one request in, one CLI command out."""
    def __init__(self, command=LANGGRAPH_COMMAND):
        self.command, self.requests = command, []

    def query(self, messages):
        history = messages.to_list()
        self.requests.append(history)
        return '{}', [{'id': 'one', 'function': {'name': 'exec_bash_command',
                                                 'arguments': json.dumps({'cmd': self.command})}}]


class ScriptedPlanner:
    """A chat model that replays fixed tool calls, then answers."""
    def __new__(cls, steps):
        from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

        class Planner(GenericFakeChatModel):
            def bind_tools(self, tools, **kwargs):
                return self
        return Planner(messages=iter(steps))


def run_notebook_agent(tmp_path, monkeypatch, planner_steps, answers):
    import builtins
    from bash_agent.config import Config
    from bash_agent.bash import Bash
    from bash_agent.helpers import Messages
    config = Config(root_dir=str(tmp_path), llm_api_key='test-only')
    translator = Translator()
    context = {'config': config, 'bash': Bash(config), 'Messages': Messages, 'llm': translator, 'json': json}
    cells = json.loads((LAB/'answer_key/03_run_agent.answers.ipynb').read_text())['cells']
    source = next(''.join(c['source']) for c in cells if 'def langgraph_cli' in ''.join(c['source']))
    import langchain_openai
    monkeypatch.setattr(langchain_openai, 'ChatOpenAI', lambda **kwargs: ScriptedPlanner(planner_steps))
    exec(source, context)
    replies = iter(answers)
    monkeypatch.setattr(builtins, 'input', lambda _: next(replies))
    result = context['agent'].invoke({'messages': [{'role': 'user', 'content': 'make a project'}]},
                                     config={'configurable': {'thread_id': 't'}})
    return translator, result


def test_fine_tuned_model_is_queried_with_its_training_prompt(tmp_path, monkeypatch):
    from langchain_core.messages import AIMessage
    from bash_agent.prompts import JSON_SYSTEM_PROMPT
    steps = [AIMessage(content='', tool_calls=[{'name': 'langgraph_cli', 'args': {'request': 'make a project'}, 'id': 'a'}]),
             AIMessage(content='', tool_calls=[{'name': 'exec_bash_command', 'args': {'cmd': 'echo translated'}, 'id': 'b'}]),
             AIMessage(content='Done.')]
    translator, result = run_notebook_agent(tmp_path, monkeypatch, steps, answers=['y'])
    assert len(translator.requests) == 1
    system, user = translator.requests[0]
    assert system == {'role': 'system', 'content': JSON_SYSTEM_PROMPT}
    assert user == {'role': 'user', 'content': 'make a project'}
    tool_results = [m for m in result['messages'] if m.type == 'tool']
    assert tool_results[0].content == LANGGRAPH_COMMAND      # the specialist returns, never runs
    assert 'translated' in tool_results[1].content            # the confirmed command ran
    assert result['messages'][-1].content == 'Done.'


def test_declined_specialist_command_does_not_run(tmp_path, monkeypatch):
    from langchain_core.messages import AIMessage
    steps = [AIMessage(content='', tool_calls=[{'name': 'exec_bash_command', 'args': {'cmd': 'touch never'}, 'id': 'b'}]),
             AIMessage(content='Skipped.')]
    _, result = run_notebook_agent(tmp_path, monkeypatch, steps, answers=['n'])
    assert 'declined' in [m for m in result['messages'] if m.type == 'tool'][0].content
    assert not (tmp_path / 'never').exists()


def test_main_hf_agent_has_bash_and_specialist_tools(tmp_path, monkeypatch):
    import bash_agent.combined as combined
    from bash_agent.config import Config
    from bash_agent.bash import Bash
    seen = {}
    monkeypatch.setattr(combined, 'create_react_agent', lambda **kwargs: seen.update(kwargs) or 'agent')
    config = Config(root_dir=str(tmp_path), llm_api_key='test-only')
    assert combined.build_combined_agent(config, Translator(), Bash(config)) == 'agent'
    assert [t.name if hasattr(t, 'name') else t.__name__ for t in seen['tools']] == ['exec_bash_command', 'langgraph_cli']
    assert 'langgraph' in config.allowed_commands
    assert 'langgraph_cli' in seen['prompt']
    tool = seen['tools'][1]
    assert tool.invoke({'request': 'build it'}) == LANGGRAPH_COMMAND


def test_specialist_tool_refuses_non_langgraph_commands(tmp_path):
    import bash_agent.combined as combined
    from bash_agent.config import Config
    tool = combined.make_langgraph_cli_tool(Translator('cat /project/secrets.env'), Config(root_dir=str(tmp_path)))
    assert 'did not produce a valid LangGraph CLI command' in tool.invoke({'request': 'show secrets'})
