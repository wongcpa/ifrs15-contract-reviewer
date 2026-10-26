"""
tests/test_contract_reviewer.py
Run: pytest tests/ -v
"""
import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__),'..','src'))
from contract_reviewer import review_contract, REVENUE_RULES, RISK_ORDER

def flags_for(text, rule_id=None):
    flags = review_contract(text, "Test")
    return [f for f in flags if f["rule_id"]==rule_id] if rule_id else flags

class TestStep1:
    def test_contingent_effectiveness(self):
        flags = flags_for("This Agreement is effective only if regulatory approval is received.","IFRS15-S1-01")
        assert flags and flags[0]["risk_level"]=="HIGH"
    def test_subject_to(self):
        assert flags_for("The contract is subject to board approval.","IFRS15-S1-01")
    def test_clean_no_flag(self):
        assert not flags_for("This Agreement is entered into as of January 1, 2025.","IFRS15-S1-01")

class TestStep2:
    def test_bundled_HIGH(self):
        flags = flags_for("This covers a bundled package of services.","IFRS15-S2-01")
        assert flags and flags[0]["risk_level"]=="HIGH"
    def test_streaming_rights_HIGH(self):
        flags = flags_for("Licensor grants streaming rights and distribution rights.","IFRS15-S2-02")
        assert flags and flags[0]["risk_level"]=="HIGH"
    def test_exclusive_license(self):
        assert flags_for("Exclusive license to exhibit the content.","IFRS15-S2-02")

class TestStep3:
    def test_royalty_HIGH(self):
        flags = flags_for("Royalties at a per-stream rate of $0.004.","IFRS15-S3-01")
        assert flags and flags[0]["risk_level"]=="HIGH"
    def test_minimum_guarantee(self):
        assert flags_for("Minimum Guarantee (MG) as advance against royalties.","IFRS15-S3-01")
    def test_milestone_payment(self):
        assert flags_for("Milestone payment of $500,000 upon reaching targets.","IFRS15-S3-01")
    def test_net_270_MEDIUM(self):
        flags = flags_for("Payment terms: Net 270 days from invoice.","IFRS15-S3-02")
        assert flags and flags[0]["risk_level"]=="MEDIUM"
    def test_net_30_no_flag(self):
        assert not flags_for("Payment terms are Net 30 days.","IFRS15-S3-02")
    def test_in_kind_MEDIUM(self):
        flags = flags_for("Distributor shall provide in-kind promotional services.","IFRS15-S3-03")
        assert flags and flags[0]["risk_level"]=="MEDIUM"

class TestStep4:
    def test_package_discount_LOW(self):
        flags = flags_for("The package discount of 12% is applied.","IFRS15-S4-01")
        assert flags and flags[0]["risk_level"]=="LOW"

class TestStep5:
    def test_ratable_LOW(self):
        flags = flags_for("Payments recognized ratably on a straight-line basis.","IFRS15-S5-01")
        assert flags and flags[0]["risk_level"]=="LOW"
    def test_uat_HIGH(self):
        flags = flags_for("Revenue recognized upon UAT and customer sign-off.","IFRS15-S5-02")
        assert flags and flags[0]["risk_level"]=="HIGH"

class TestPrincipalAgent:
    def test_agent_commission_HIGH(self):
        flags = flags_for("Distributor acts as agent on a net settlement basis.","IFRS15-B34")
        assert flags and flags[0]["risk_level"]=="HIGH"

class TestASPE:
    def test_upon_completion_MEDIUM(self):
        flags = flags_for("Upon completion of post-production content shall be delivered.","ASPE3400-01")
        assert flags and flags[0]["risk_level"]=="MEDIUM"

class TestStructure:
    def test_risk_order(self):
        assert RISK_ORDER["HIGH"] < RISK_ORDER["LOW"]
    def test_all_rules_have_fields(self):
        required = {"rule_id","name","pattern","standard","risk_level","flag_reason","guidance"}
        for r in REVENUE_RULES:
            assert required.issubset(set(r.keys()))
    def test_flag_has_required_keys(self):
        flags = review_contract("effective only if regulatory approval streaming rights royalties Net 270.", "T")
        if flags:
            required = {"contract","rule_id","name","standard","risk_level","flag_reason","guidance","match_count","snippets"}
            assert required.issubset(set(flags[0].keys()))
    def test_clean_contract_no_high_flags(self):
        text = "Consulting services at $10,000 payable Net 30. Either party may terminate upon 30 days notice."
        high = [f for f in review_contract(text,"T") if f["risk_level"]=="HIGH"]
        assert len(high) == 0

class TestIntegration:
    SAMPLE = """effective only if regulatory approval. streaming rights bundled package.
    Minimum Guarantee advance against royalties tiered pricing. Net 270 days. in-kind services.
    UAT customer sign-off. agent net settlement commission. upon completion post-production.
    package discount 12%."""
    def test_has_high_flags(self):
        assert any(f["risk_level"]=="HIGH" for f in review_contract(self.SAMPLE,"S"))
    def test_has_medium_flags(self):
        assert any(f["risk_level"]=="MEDIUM" for f in review_contract(self.SAMPLE,"S"))
    def test_detects_variable_consideration(self):
        assert any(f["rule_id"]=="IFRS15-S3-01" for f in review_contract(self.SAMPLE,"S"))
    def test_detects_principal_agent(self):
        assert any(f["rule_id"]=="IFRS15-B34" for f in review_contract(self.SAMPLE,"S"))
