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


def test_customized_loop_translates_once_per_request(tmp_path, monkeypatch):
    import builtins
    from bash_agent.config import Config
    from bash_agent.bash import Bash
    from bash_agent.helpers import Messages
    class Translator:
        calls = 0
        def query(self, messages):
            self.calls += 1
            assert len(messages.to_list()) == 2
            return '{}', [{'id':'one','function':{'name':'exec_bash_command','arguments':'{"cmd":"echo translated"}'}}]
    translator = Translator()
    config = Config(root_dir=str(tmp_path))
    context = {'config':config,'bash':Bash(config),'Messages':Messages,'llm':translator,'json':json}
    cells=json.loads((LAB/'answer_key/03_run_agent.answers.ipynb').read_text())['cells']
    source=next(''.join(cell['source']) for cell in cells if 'def run_agent_loop' in ''.join(cell['source']))
    exec(source, context)
    answers=iter(['one request','y','quit'])
    monkeypatch.setattr(builtins,'input',lambda _:next(answers))
    context['run_agent_loop']()
    assert translator.calls == 1
