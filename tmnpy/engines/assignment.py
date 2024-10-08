import json
import re
import os
from tmnpy.dsl import (
    Asset,
    ExternalEntity,
    Datastore,
    Process,
    Finding,
    Control,
    DataFlow,
    Issue,
)

from tmnpy import kb

from .engine import Engine


# Given the list of Components in a TM, return Findings for each Component
def get_findings(tm_components, threat_map):
    findings = []
    for component in tm_components:
        mt, umt = threat_map.component_threats(component)
        finding = Finding(affected_components=component, issues=umt)
        findings.append(finding)
    return findings


class Assignment(Engine):
    """
    Assignment represent a list of rules (mappings between a component and a threat/control). The default assignments are from the threatlib.
    """

    __threatmap: list  # list of Rules

    def __init__(self, threatmap: list = None) -> None:
        if threatmap == None:
            self.__threatmap = self.parse_threatlib()
        else:
            self.__threatmap = threatmap

    @property
    def threatmap(self) -> type:
        return self.__threatmap

    @threatmap.setter
    def threatmap(self, x):
        self.__threatmap = x

    def component_threats(self, component):
        mitigated_threats = []
        unmitigated_threats = []
        applicable_rules = [
            t for t in self.__threatmap if type(component) == t.component
        ]
        for r in applicable_rules:
            result = r.mitigated_threat(component)
            if result["is_mitigated"]:
                mitigated_threats.append(result["threat"])
            else:
                unmitigated_threats.append(result["threat"])
        return mitigated_threats, unmitigated_threats

    def parse_threatlib(self):
        data = kb.load_threatlib()
        capec = kb.load_capec()
        rules = []

        for d in data:
            # get CAPEC ID
            capec_ref = re.search(
                "capec\.mitre\.org\/data\/definitions\/(\d*)\.html",
                d["references"],
            )
            if capec_ref:
                capec_id = capec_ref.group(1)
                for c in capec:
                    if c.meta["ref_id"] == "CAPEC-" + capec_id:
                        threat = c
            else:
                threat = Issue(d["description"])

            # get controls
            controls_strs = re.findall(
                "target\.controls\.(\w*) is (True|False)", d["condition"]
            )  # pretty sure it's always False
            controls_list_2 = re.findall(
                "target\.controls\.(\w*)", d["condition"]
            )

            controls_list = []
            for i, c in enumerate(controls_strs):
                controls_list.append(Control(cid=str(i), name=c[0]))

            for t in d["target"]:
                if t in ["Process", "Datastore", "ExternalEntity"]:
                    rules.append(
                        Rule(globals()[t], threat, controls_list)
                    )
                elif t == "Dataflow":
                    rules.append(Rule(DataFlow, threat, controls_list))
                elif t in ["Server", "Lambda"]:
                    rules.append(Rule(Asset, threat, controls_list))
                else:
                    raise Exception("Unknown Asset type")
        return rules


class Rule:
    """
    A Rule represents a potential Issue for a type of Component, and the Controls necessary to mitigate this Issue.
    """

    __component: type
    __issue: Issue
    __controls: list

    def __init__(
        self,
        component: type,
        issue: Issue,
        controls: list = None,
    ) -> None:
        self.__component = component
        self.__issue = issue
        self.__controls = controls

    @property
    def component(self) -> type:
        return self.__component

    @component.setter
    def component(self, x):
        self.__component = x

    @property
    def issue(self) -> Issue:
        return self.__issue

    @issue.setter
    def issue(self, x):
        self.__issue = x

    @property
    def controls(self) -> list:
        return self.__controls

    @controls.setter
    def controls(self, x):
        self.__controls = x

    # Given a Rule and an Asset with some Controls, use the Rule to determine whether the Threat applies on this Asset. Return the Threat, True iff it was mitigated, and the Controls that were found to apply/not apply.
    def mitigated_threat(self, component: Asset):
        applied_controls = []
        not_applied_controls = []
        for control in self.controls:
            if control.name in [x.name for x in component.controls]:
                applied_controls.append(control)
            else:
                not_applied_controls.append(control)

        # TODO - Currently returns mitigated if any one of the controls is applied, ignoring logical relationships between conditions.
        is_mitigated = True if len(applied_controls) > 0 else False

        return {
            "threat": self.issue,
            "is_mitigated": is_mitigated,
            "applied_controls": applied_controls,
            "not_applied_controls": not_applied_controls,
        }
