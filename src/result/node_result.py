
from __future__ import annotations

import json
from typing import Dict, Any

from openai import OpenAI

from src.result.node_action_extractor import node_action_extractor
from src.result.node_result_packager import node_result_packager, format_action_instructions
    
# act_title_text을 state로 저장하는 버전
def node_result(state: Dict[str, Any]) -> Dict[str, Any]:
    # 1) 행동 추출
    state = node_action_extractor(state)

    # 2) summary / needs_action / action_info 생성
    state = node_result_packager(state)


    web_result_list = []

    # 3) 자연어 행동안내 생성
    if state.get("needs_action") and state.get("action_info"):
        formatted_actions = format_action_instructions(state["action_info"])
        state["formatted_actions"] = formatted_actions

        # 행동이 여러개일 수 있으므로 리스트로 묶어 생성
        for item in formatted_actions:
            web_result_list.append({
                "title": item["title"],
                "text": item["text"],
            })
    else:
        state["formatted_actions"] = []

        # 행동이 없으면 title/text는 빈 문자열
        web_result_list.append({
            "title": "",
            "text": "",
        })

    # 4) state에 저장
    state["web_package"] = web_result_list

    return state


# 초기 버전
# def node_result (state: Dict[str, Any]) -> Dict[str, Any]:

#     state = node_action_extractor(state)
#     print("\n최종 결과:", json.dumps(state, ensure_ascii=False, indent=2))
    
#     state = node_result_packager(state)
#     print("\n--- 최종 결과 ---")
#     print("\n핵심 요약:\n")
#     print(state['summary'])
#     print()

    
#     if state["needs_action"] and state["action_info"]:
#         formatted = format_action_instructions(state["action_info"])
#         for item in formatted:
#             print(f"\n======= {item['title']} =======")
#             print(item["text"])
#     else:
#         print("특별히 취해야 할 행동 없음.")


#     return state

