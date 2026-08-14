from routing_lab_answers_import_helper import answers as lab
from conftest import FakeResponse, FakeChat
from constants import STRONG_MODEL, EFFICIENT_MODEL, PRICING

def test_bill_call_prices_and_counterfactuals():
    bill = lab.RunningBill()
    # Asymmetric on purpose: 1M/1M would price the same even if in/out rates swapped.
    chat = FakeChat([FakeResponse("hi", in_tok=2_000_000, out_tok=1_000_000)])
    resp, receipt = lab.bill_call(EFFICIENT_MODEL, chat, "prompt", bill)
    p = PRICING[EFFICIENT_MODEL]; pf = PRICING[STRONG_MODEL]
    assert abs(receipt["cost"] - (2 * p["in"] + p["out"])) < 1e-9
    assert abs(receipt["counterfactual_cost"] - (2 * pf["in"] + pf["out"])) < 1e-9
    assert bill.total_cost == receipt["cost"]

def test_running_bill_accumulates_by_model():
    bill = lab.RunningBill()
    bill.add(EFFICIENT_MODEL, {"input_tokens": 10, "output_tokens": 10}, 0.01, 0.5)
    bill.add(STRONG_MODEL, {"input_tokens": 10, "output_tokens": 10}, 0.20, 1.5)
    assert set(bill.by_model) == {EFFICIENT_MODEL, STRONG_MODEL}
    assert abs(bill.total_cost - 0.21) < 1e-9

def test_receipt_carries_every_key_the_client_reads():
    # The client and race mode index these by name -- all eight must be present.
    bill = lab.RunningBill()
    chat = FakeChat([FakeResponse("hi")])
    _, receipt = lab.bill_call(EFFICIENT_MODEL, chat, "prompt", bill)
    assert set(receipt) == {"model", "input_tokens", "output_tokens", "cost",
                            "latency", "counterfactual_cost", "why", "router_tax"}
    assert receipt["model"] == EFFICIENT_MODEL
    assert (receipt["input_tokens"], receipt["output_tokens"]) == (100, 20)
    assert receipt["router_tax"] == 0.0 and receipt["latency"] >= 0.0

def test_default_judge_grades_with_the_strong_model(monkeypatch):
    graded = FakeChat([FakeResponse("PASS -- meets the rubric.")])
    monkeypatch.setattr(lab, "build_model_pool",
                        lambda: {"strong": graded, "efficient": FakeChat([FakeResponse("nope")])})
    assert lab._default_judge("rubric text", "answer text") is True
    assert len(graded.calls) == 1          # the judge asks the strong model, once

    failed = FakeChat([FakeResponse("FAIL: only one bullet.")])
    monkeypatch.setattr(lab, "build_model_pool",
                        lambda: {"strong": failed, "efficient": FakeChat([FakeResponse("nope")])})
    assert lab._default_judge("rubric text", "answer text") is False

def test_run_suite_bills_every_task_under_a_passthrough_strategy(monkeypatch):
    chat = FakeChat([FakeResponse("1969")])   # one queued response, replayed for all 12
    monkeypatch.setattr(lab, "build_model_pool", lambda: {"strong": chat, "efficient": chat})
    bill = lab.RunningBill()
    results = lab.run_suite("efficient_only", bill, judge=lambda rubric, out: True)
    assert len(results) == 12 and len(chat.calls) == 12
    assert set(results[0]) == {"id", "kind", "passed", "cost", "latency", "models", "router_tax"}
    assert bill.by_model[EFFICIENT_MODEL]["calls"] == 12
    assert abs(sum(r["cost"] for r in results) - bill.total_cost) < 1e-9
