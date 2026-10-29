import json
import sys
from pathlib import Path
import pytest
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda
CODE_DIR = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(CODE_DIR / '3-agent-evaluation'), str(CODE_DIR / '2-agentic-rag')]
from evaluation_framework import parse_evaluation,evaluate_relevancy,evaluate_faithfulness,evaluate_report_quality,calculate_aggregate_score,EvaluationResult
from evaluation_support import *
from client_messages import normalize_message,stream_error

@pytest.mark.parametrize('score',[0,6,99,-1,True,'4',float('nan'),float('inf')])
def test_invalid_scores_are_errors(score):
 r=parse_evaluation(json.dumps({'score':score,'explanation':'x'}),'m')
 assert r.status=='error' and r.score is None

@pytest.mark.parametrize('text',['{"score": 4.5, "explanation": "supported"}','```json\n{"score": 4.5, "explanation": "supported"}\n```'])
def test_decimal_and_fenced_scores(text):
 assert parse_evaluation(text,'m').score==4.5

@pytest.mark.parametrize('text',['score: 4','{}','[]','{"score":4,"explanation":""}','{"score":4}'])
def test_malformed_scores_do_not_become_quality(text):
 assert parse_evaluation(text,'m').status=='error'

def test_provider_failure_and_empty_answers():
 def fail(_): raise RuntimeError('HTTP 503 secret-example')
 r=evaluate_relevancy('q','a',RunnableLambda(fail))
 assert r.status=='error' and r.score is None and 'secret-example' not in r.explanation
 assert evaluate_relevancy('q','',RunnableLambda(fail)).status=='not_applicable'
 assert evaluate_faithfulness('q','a','',RunnableLambda(fail)).status=='not_applicable'
 assert calculate_aggregate_score({'r':r}) is None

def test_report_scores_need_actual_evidence():
 output={m:{'score':5,'explanation':'x'} for m in ['structure','content','coverage','accuracy','writing']}
 judge=RunnableLambda(lambda _:AIMessage(content='```json\n'+json.dumps(output)+'\n```'))
 scored=evaluate_report_quality('q','a',['intro'],judge_llm=judge)
 assert scored['accuracy'].status=='not_applicable'
 assert scored['structure'].score==5
 assert evaluate_report_quality('q','a',['intro'],judge_llm=judge,source_context='actual excerpts')['accuracy'].score==5

def test_rewritten_and_multiple_retrievals_only_use_observed_artifacts():
 d=Document(page_content='retrieved',metadata={'source_id':'file#a'})
 state={'messages':[AIMessage(content='',tool_calls=[{'name':'company_llc_it_knowledge_base','args':{'query':'rewritten'},'id':'a','type':'tool_call'}]),ToolMessage(content='shown',name='company_llc_it_knowledge_base',tool_call_id='a',artifact=[d]),AIMessage(content='',tool_calls=[{'name':'company_llc_it_knowledge_base','args':{'query':'second'},'id':'b','type':'tool_call'}]),ToolMessage(content='shown2',name='company_llc_it_knowledge_base',tool_call_id='b',artifact=[d]),AIMessage(content='Answer [KB:file#a]')]}
 trace=retrieval_trace(state)
 assert [x['query'] for x in trace]==['rewritten','second']
 assert trace_contexts(trace)==['[KB:file#a]\nretrieved']*2
 assert citation_check(final_answer(state),trace)['all_citations_resolve']
 assert citation_check('Answer 【KB:file#a】',trace)['all_citations_resolve']
 assert not citation_check('[KB:invented]',trace)['all_citations_resolve']
 assert retrieval_trace({'messages':[AIMessage(content='direct answer')]})==[]
 assert final_answer({'messages':state['messages'][:-1]})==''

def test_failed_metrics_keep_denominators_and_prevent_aggregate():
 row={'agent_status':'ok'}
 store_scores(row,{'a':EvaluationResult(metric_name='a',score=1,explanation='low'), 'b':EvaluationResult(metric_name='b',status='error',explanation='provider')})
 assert row['a_score']==.2 and row['b_score'] is None and row['aggregate_score'] is None
 summary=quality_summary([row],['a','b'])
 assert summary['metrics']['a']['valid']==1 and summary['metrics']['b']['valid']==0 and not summary['complete']

def test_unique_runs_pair_cases_and_show_configuration_changes(tmp_path):
 data=tmp_path/'data.json';data.write_text('[1]')
 a=start_run('test',data,{'prompt':'a'},tmp_path);b=start_run('test',data,{'prompt':'b'},tmp_path)
 assert a!=b
 rows=[{'case_id':'ok','agent_status':'ok','judge_status':'ok','aggregate_score':.8,'aggregate_metrics':['quality']},{'case_id':'bad','agent_status':'error','judge_status':'skipped','aggregate_score':None}]
 checkpoint(a,rows);checkpoint(b,rows)
 compared=compare_runs(a,b)
 assert compared['paired_cases']==1 and compared['configuration_changes']['prompt']['after']=='b'
 data.write_text('[2]');c=start_run('test',data,{},tmp_path);checkpoint(c,rows)
 with pytest.raises(ValueError):compare_runs(a,c)

def test_missing_evidence_does_not_make_different_aggregates_comparable(tmp_path):
 data=tmp_path/'data.json';data.write_text('[1]')
 a=start_run('test',data,{},tmp_path);b=start_run('test',data,{},tmp_path)
 full={'case_id':'x','agent_status':'ok'};partial=dict(full)
 score=EvaluationResult(metric_name='support',score=5,explanation='supported')
 unavailable=EvaluationResult(metric_name='support',status='not_applicable',explanation='no excerpts')
 store_scores(full,{'support':score,'writing':score})
 store_scores(partial,{'support':unavailable,'writing':score})
 assert not quality_summary([partial],['support','writing'])['complete']
 checkpoint(a,[full]);checkpoint(b,[partial])
 compared=compare_runs(a,b)
 assert compared['paired_cases']==0 and compared['excluded_missing_or_different_criteria']==['x']
 assert compare_runs(a,b,metric='writing_score')['paired_cases']==1

def test_content_blocks_and_error_event():
 m=normalize_message({'id':'x','type':'ai','content':[{'type':'text','text':'hello'},{'type':'image','image_url':'x'}]})
 assert m['content']=='hello'
 assert normalize_message({'type':'human','content':'old'}) is None
 assert normalize_message({'type':'ai','content':'<think>thinking</think>answer'})['content']=='answer'
 assert 'failed' in stream_error({'error':'GraphRecursionError','message':'private URL'})
 assert 'private' not in stream_error({'error':'GraphRecursionError','message':'private URL'})
 assert 'HTTP 429' in stream_error({'error':'Exception','message':'[429] Too Many Requests: https://private?key=secret'})
 assert 'secret' not in stream_error({'error':'Exception','message':'[429] Too Many Requests: https://private?key=secret'})


def test_context_overflow_says_to_start_a_new_conversation():
    # The error event a local NIM (vLLM) overflow produces through ChatNVIDIA.
    detail = ("[400] {'message': \"This model's maximum context length is 32768 tokens. However, you requested "
              "4096 output tokens and your prompt contains at least 28673 input tokens, for a total of at least "
              "32769 tokens.\", 'type': 'BadRequestError', 'param': 'input_tokens', 'code': 400}")
    message = stream_error({'error': 'Exception', 'message': detail})
    assert "context window" in message and "New conversation" in message
    assert "28673" not in message


def test_quote_check_ignores_formatting_but_not_changed_facts():
    source = "### Procedure\n\n- **Wait 15 minutes** before contacting support."
    assert quote_is_present("Wait 15 minutes before contacting support.", source)
    assert not quote_is_present("Wait 5 minutes before contacting support.", source)
    assert not quote_is_present("UNSUPPORTED", source)


def test_quote_check_accepts_flattened_lists_and_typographic_marks():
    source = "Include these details:\n- Current asset tag\n- Reason for the refresh\n\nThe user’s AI-assisted triage"
    assert quote_is_present("Include these details: - Current asset tag - Reason for the refresh", source)
    assert quote_is_present("The user's AI‑assisted triage", source)
    assert not quote_is_present("Include these details: - Previous asset tag", source)


CONTROL = json.loads((CODE_DIR.parent / "data/evaluation/report_control.json").read_text())


def test_numbers_missing_from_the_evidence_are_listed():
    inputs = CONTROL["inputs"]
    assert unsupported_numbers(inputs["report"], inputs["source_context"]) == CONTROL["planted_numbers"]
    # Thousands separators, citation markers and single digits are not differences.
    assert unsupported_numbers("Reached 3600 GW [12] in 2 steps 【3】", "reached 3,600 GW") == []
    # Nor are a report's date stamp and its section or reference-list numbers.
    assert unsupported_numbers("*Date: 2026‑10‑08*\n### 4.1 Threats\n11. Slack Blog", "") == []


def test_claims_are_verified_against_the_evidence_not_the_judge():
    evidence = CONTROL["inputs"]["source_context"]
    checked = verify_claims([
        {"claim": "Capacity reached 412 MW in 2025", "quote": "reached 412 MW of installed capacity at the end of 2025"},
        {"claim": "Capacity will reach 1,150 MW", "quote": "reached 412 MW of installed capacity"},
        {"claim": "The programs created 2,400 jobs", "quote": "The programs created 2,400 local construction jobs"},
        {"claim": "Prices will fall", "quote": "UNSUPPORTED"},
        "not a claim",
    ], evidence)
    assert checked["claims_checked"] == 5 and checked["claims_verified"] == 1
    assert checked["evidence_verified"] == 0.2
    assert verify_claims(None, evidence)["evidence_verified"] is None


def test_known_bad_control_is_flagged_even_when_the_judge_is_fooled():
    inputs = CONTROL["inputs"]
    output = {m: {'score': 5, 'explanation': 'Fully supported.'} for m in ['structure', 'content', 'coverage', 'accuracy', 'writing']}
    output["accuracy"]["claims"] = [{"claim": "The programs created 2,400 local construction jobs",
                                     "quote": "created 2,400 local construction jobs"},
                                    {"claim": "Capacity is projected to reach 1,150 MW by 2030",
                                     "quote": "installed capacity is projected to reach 1,150 MW by 2030"}]
    judge = RunnableLambda(lambda _: AIMessage(content=json.dumps(output)))
    scores = evaluate_report_quality(**inputs, judge_llm=judge)
    assert scores["accuracy"].score == 5 and scores["accuracy"].claims == output["accuracy"]["claims"]
    row = dict(inputs)
    store_scores(row, scores)
    check_evidence(row, scores["accuracy"].claims)
    assert row["evidence_verified"] == 0.0
    assert "judge evidence score not backed by verified quotes" in row["evidence_flags"]
    assert any(flag.startswith("6 numbers missing") for flag in row["evidence_flags"])


def test_review_sample_shows_failures_disagreements_and_low_scores_first():
    rows = [{"case_id": "ok", "judge_status": "ok", "aggregate_score": 1.0, "judge": 1.0, "check": 0.9},
            {"case_id": "gap", "judge_status": "ok", "aggregate_score": 1.0, "judge": 1.0, "check": 0.1},
            {"case_id": "low", "judge_status": "ok", "aggregate_score": 0.4, "judge": 0.4, "check": float("nan")},
            {"case_id": "failed", "judge_status": "error", "aggregate_score": None}]
    picked = review_sample(rows, compare=("judge", "check"))
    assert [row["case_id"] for row in picked] == ["failed", "gap", "low"]
    assert [row["case_id"] for row in review_sample(rows[:3], size=2)] == ["low", "ok"]


def test_unreviewed_synthetic_references_are_not_silently_used(tmp_path):
    generated = tmp_path / "synthetic_rag_agent_test_cases.json"
    generated.write_text(json.dumps([{"review_status": "unreviewed"}]))
    assert select_dataset(tmp_path, "rag_agent").name == "rag_agent_test_cases.json"
    generated.write_text(json.dumps([{"review_status": "reviewed"}]))
    assert select_dataset(tmp_path, "rag_agent") == generated


def test_rate_limit_retries_wait_and_preserve_the_original_failure(monkeypatch):
    import evaluation_support as support
    delays, calls = [], []
    monkeypatch.setattr(support.time, "sleep", delays.append)
    def limited():
        calls.append(1)
        raise RuntimeError("HTTP 429")
    with pytest.raises(RuntimeError):
        support.invoke_with_retry(limited)
    assert len(calls) == 4 and delays == [10, 20, 40]


def test_mcp_credentials_do_not_enter_urls_argv_or_error_messages():
    import ast
    import asyncio
    from langchain_core.tools import tool
    secret = "test-credential-must-not-be-visible"
    source = ast.parse((CODE_DIR / "2-agentic-rag/rag_agent.answers.py").read_text())
    nodes = [node for node in source.body
             if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MCP_CONFIG" for t in node.targets)
             or isinstance(node, ast.AsyncFunctionDef) and node.name == "web_search"]
    class FailingClient:
        def __init__(self, config):
            raise RuntimeError("Transport error with credential " + secret)
    namespace = {"TAVILY_API_KEY": secret, "tool": tool, "MultiServerMCPClient": FailingClient}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<MCP exercise>", "exec"), namespace)
    connection = namespace["MCP_CONFIG"]["tavily"]
    assert secret not in connection["url"]
    assert "args" not in connection and "command" not in connection
    assert connection["headers"]["Authorization"] == "Bearer " + secret
    output = asyncio.run(namespace["web_search"].ainvoke({"query": "query"}))
    assert secret not in output and "RuntimeError" in output
