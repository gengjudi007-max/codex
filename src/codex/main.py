from codex.services.draft_editor import edit_draft
from codex.services.interview_planner import plan_interview
from codex.services.material_builder import build_materials
from codex.services.topic_finder import find_topics


def main():
    """运行一次财经/房地产记者助手的基础工作流。"""
    input_data = {
        "source": "policy_and_market_updates",
        "keywords": ["房地产政策", "土地市场", "上市房企公告"],
    }

    topics = find_topics(input_data)
    first_topic = topics[0]
    materials = build_materials(first_topic)
    interview_plan = plan_interview(first_topic)
    edited_draft = edit_draft("  这是一段待优化的房地产报道初稿。  ")

    print("=== Codex Journalism Assistant Demo ===")
    print("\n[1] Topic")
    print(first_topic)
    print("\n[2] Materials")
    print(materials)
    print("\n[3] Interview Plan")
    print(interview_plan)
    print("\n[4] Edited Draft")
    print(edited_draft)


if __name__ == "__main__":
    main()
