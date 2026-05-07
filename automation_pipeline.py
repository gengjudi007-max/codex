#!/usr/bin/env python3
"""
Codex 自动化流程脚本
实现：信息采集 → 线索识别 → 选题生成 → 报道策划 → 稿件优化 的完整自动化流程
"""
import sys
import json
import time
from typing import Any, Dict, List
from datetime import datetime

sys.path.insert(0, 'src')

print("=" * 80)
print("Codex 自动化流程系统")
print("=" * 80)

# 导入所有需要的模块
print("\n📦 加载模块...")
try:
    from codex.interaction import analyze_payload
    from codex.services.signal_monitor import monitor_signals
    from codex.services.topic_finder import find_topics
    from codex.services.topic_scoring import score_topics
    from codex.services.material_builder import build_materials
    from codex.services.interview_planner import plan_interview
    from codex.services.photo_planner import plan_photography
    from codex.services.evidence import attach_credibility
    from codex.services.draft_editor import edit_draft
    from codex.services.source_ingestion import ingest_sources
    from codex.connectors.beijing_land_connector import fetch_beijing_land_items
    from codex.connectors.guangzhou_land_connector import GuangzhouLandConnector
    from codex.connectors.shenzhen_land_connector import ShenzhenLandConnector
    from codex.connectors.hangzhou_land_connector import HangzhouLandConnector
    from codex.connectors.simple_city_land_connector import SimpleCityLandConnector
    print("  ✅ 所有模块加载成功")
except Exception as e:
    print(f"  ❌ 模块加载失败：{e}")
    sys.exit(1)


def normalize_item(item: Dict[str, Any], city: str, source: str) -> Dict[str, Any]:
    """标准化数据项"""
    return {
        'title': item.get('title', item.get('name', '未知标题')),
        'content': item.get('content', item.get('title', '')),
        'city': city,
        'source': source,
        'url': item.get('url', ''),
        'date': item.get('date', '')
    }


def collect_data() -> List[Dict[str, Any]]:
    """步骤1：信息采集"""
    print("\n" + "=" * 80)
    print("步骤 1：信息采集")
    print("=" * 80)
    
    all_data = []
    
    # 1. 采集土地市场数据
    print("\n📍 采集土地市场数据...")
    
    # 北京
    try:
        print("  - 北京...")
        beijing_data = fetch_beijing_land_items(max_pages=1, limit=10)
        # 标准化
        for item in beijing_data:
            all_data.append(normalize_item(item, '北京', '北京自然资源委员会'))
        print(f"    ✅ 获取到 {len(beijing_data)} 条数据")
    except Exception as e:
        print(f"    ❌ 失败：{e}")
    
    # 广州
    try:
        print("  - 广州...")
        connector = GuangzhouLandConnector()
        guangzhou_data = connector.fetch_land_data(page_num=1, max_pages=1)
        # 标准化
        for item in guangzhou_data:
            if isinstance(item, dict):
                all_data.append(normalize_item(item, '广州', '广州公共资源交易中心'))
            else:
                print(f"    ⚠️  跳过非字典数据：{type(item)}")
        print(f"    ✅ 获取到 {len(guangzhou_data)} 条数据")
    except Exception as e:
        print(f"    ❌ 失败：{e}")
    
    # 深圳
    try:
        print("  - 深圳...")
        connector = ShenzhenLandConnector()
        shenzhen_data = connector.fetch_land_data(page_num=1, max_pages=1)
        # 标准化
        for item in shenzhen_data:
            if isinstance(item, dict):
                all_data.append(normalize_item(item, '深圳', '深圳土地交易平台'))
            else:
                print(f"    ⚠️  跳过非字典数据：{type(item)}")
        print(f"    ✅ 获取到 {len(shenzhen_data)} 条数据")
    except Exception as e:
        print(f"    ❌ 失败：{e}")
    
    # 杭州
    try:
        print("  - 杭州...")
        connector = HangzhouLandConnector()
        hangzhou_data = connector.fetch_land_data(page_num=1, max_pages=1)
        # 标准化
        for item in hangzhou_data:
            if isinstance(item, dict):
                all_data.append(normalize_item(item, '杭州', '杭州国土资源局'))
            else:
                print(f"    ⚠️  跳过非字典数据：{type(item)}")
        print(f"    ✅ 获取到 {len(hangzhou_data)} 条数据")
    except Exception as e:
        print(f"    ❌ 失败：{e}")
    
    # 简化版连接器（多个城市）
    simple_cities = ['成都', '西安', '武汉', '天津', '重庆']
    for city in simple_cities:
        try:
            print(f"  - {city}...")
            connector = SimpleCityLandConnector(city_name=city)
            city_data = connector.fetch_data(max_per_category=1)
            # 标准化
            for item in city_data:
                if isinstance(item, dict):
                    all_data.append(normalize_item(item, city, f'{city}公共资源交易中心'))
                else:
                    print(f"    ⚠️  跳过非字典数据：{type(item)}")
            print(f"    ✅ 获取到 {len(city_data)} 条数据")
        except Exception as e:
            print(f"    ❌ 失败：{e}")
    
    print(f"\n📊 信息采集完成：共获取 {len(all_data)} 条数据")
    return all_data


def identify_signals(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """步骤2：线索识别（信号监测）"""
    print("\n" + "=" * 80)
    print("步骤 2：线索识别（直接使用数据进行选题分析）")
    print("=" * 80)
    
    try:
        # 直接使用数据，不需要通过 monitor_signals
        # monitor_signals 主要用于连续监测，这里我们直接使用数据生成选题
        print(f"\n📊 线索识别完成：处理了 {len(data)} 条数据")
        return {"items": data}  # 返回字典格式，符合 find_topics 的期望
    except Exception as e:
        print(f"  ❌ 线索识别失败：{e}")
        return {"items": []}


def generate_topics(signals: Dict[str, Any]) -> List[Dict[str, Any]]:
    """步骤3：选题生成（新闻价值判断）"""
    print("\n" + "=" * 80)
    print("步骤 3：选题生成（新闻价值判断）")
    print("=" * 80)
    
    try:
        # find_topics 期望接收 {"items": [...]} 格式的字典
        topics = find_topics(signals)
        
        print(f"\n📊 选题生成完成：生成 {len(topics)} 个选题")
        
        # 显示前3个选题
        for i, topic in enumerate(topics[:3], 1):
            print(f"  {i}. {topic.get('topic', '')}")
            print(f"     优先级：{topic.get('priority', '')}")
            print(f"     评分：{topic.get('final_score', 0)}")
        
        return topics
    except Exception as e:
        print(f"  ❌ 选题生成失败：{e}")
        import traceback
        traceback.print_exc()
        return []


def plan_report(topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """步骤4：报道策划（素材、采访、摄影）"""
    print("\n" + "=" * 80)
    print("步骤 4：报道策划（素材、采访、摄影）")
    print("=" * 80)
    
    enriched_topics = []
    
    for i, topic in enumerate(topics[:3], 1):  # 只处理前3个选题
        print(f"\n📝 策划选题 {i}：{topic.get('topic', '')}")
        
        try:
            # 素材整理
            print("  - 素材整理...")
            material_plan = build_materials(topic)
            print(f"    ✅ 素材清单：{len(material_plan.get('must_have', []))} 项")
            
            # 采访策划
            print("  - 采访策划...")
            interview_plan = plan_interview(topic)
            print(f"    ✅ 采访对象：{len(interview_plan.get('interview_targets', []))} 个")
            
            # 摄影策划
            print("  - 摄影策划...")
            photo_plan = plan_photography(topic)
            print(f"    ✅ 拍摄画面：{len(photo_plan.get('must_have_shots', []))} 个")
            
            # 证据链管理
            print("  - 证据链管理...")
            enriched = attach_credibility(
                {key: value for key, value in topic.items() if key != "input_item"},
                topic.get("input_item", {}),
                required_materials=material_plan.get("must_have", []),
            )
            enriched["material_plan"] = material_plan
            enriched["interview_plan"] = interview_plan
            enriched["photo_plan"] = photo_plan
            
            enriched_topics.append(enriched)
            print(f"    ✅ 策划完成")
            
        except Exception as e:
            print(f"    ❌ 策划失败：{e}")
    
    print(f"\n📊 报道策划完成：共策划 {len(enriched_topics)} 个选题")
    return enriched_topics


def optimize_draft(enriched_topics: List[Dict[str, Any]], draft_text: str = "") -> Dict[str, Any]:
    """步骤6：稿件优化（编辑稿件）"""
    print("\n" + "=" * 80)
    print("步骤 6：稿件优化（编辑稿件）")
    print("=" * 80)
    
    if not draft_text:
        # 如果没有提供稿件，生成一个简单的草稿
        draft_text = f"# {enriched_topics[0].get('topic', '报道选题')}\n\n"
        draft_text += f"## 报道角度\n{enriched_topics[0].get('angle', '')}\n\n"
        draft_text += "## 素材清单\n"
        for item in enriched_topics[0].get('material_plan', {}).get('must_have', [])[:5]:
            draft_text += f"- {item}\n"
    
    try:
        print("\n📝 优化稿件...")
        optimization_result = edit_draft(draft_text)
        
        print(f"\n📊 稿件优化完成：")
        print(f"  - 问题数：{len(optimization_result.get('issues', []))}")
        print(f"  - 建议数：{len(optimization_result.get('suggestions', []))}")
        
        return optimization_result
    except Exception as e:
        print(f"  ❌ 稿件优化失败：{e}")
        return {}


def generate_full_draft(enriched_topic: Dict[str, Any]) -> str:
    """生成完整的报道稿件（使用模板）"""
    print("\n📝 生成完整稿件...")
    
    try:
        # 使用模板生成稿件（更可控）
        draft = generate_template_draft(enriched_topic)
        print(f"  ✅ 稿件生成成功（{len(draft)} 字）")
        return draft
            
    except Exception as e:
        print(f"  ❌ 生成稿件失败：{e}")
        import traceback
        traceback.print_exc()
        # 返回一个最简单的稿件
        return f"# {enriched_topic.get('topic', '报道选题')}\n\n报道内容待补充。"


def generate_template_draft(enriched_topic: Dict[str, Any]) -> str:
    """生成模板稿件（备用）"""
    topic = enriched_topic.get('topic', '报道选题')
    angle = enriched_topic.get('angle', '')
    materials = enriched_topic.get('material_plan', {}).get('must_have', [])
    
    draft = f"""# {topic}

## 导语

近期，{topic}引发市场关注。本文将从{topic}的角度，分析其背后的逻辑与影响。

## 正文

### 一、事件背景

{angle}

### 二、数据分析

"""
    
    for i, material in enumerate(materials[:5], 1):
        draft += f"{i}. {material}\n\n"
    
    draft += """### 三、市场影响

该事件对房地产市场将产生深远影响，值得持续关注。

### 四、专家观点

（待采访补充）

## 结语

综合以上分析，该事件反映了房地产市场的新趋势，值得投资者和决策者关注。

---
生成时间：""" + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return draft


def save_results(enriched_topics: List[Dict[str, Any]], optimization_result: Dict[str, Any], generated_drafts: List[Dict[str, Any]] = None):
    """保存结果到文件"""
    print("\n" + "=" * 80)
    print("保存结果")
    print("=" * 80)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存选题和策划结果
    result_file = f"data/automation_result_{timestamp}.json"
    try:
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                "topics": enriched_topics,
                "optimization": optimization_result,
                "generated_drafts": generated_drafts or [],
                "generated_at": timestamp
            }, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 结果已保存：{result_file}")
    except Exception as e:
        print(f"  ❌ 保存失败：{e}")
    
    # 生成 Markdown 报告
    report_file = f"data/automation_report_{timestamp}.md"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Codex 自动化流程报告\n\n")
            f.write(f"生成时间：{timestamp}\n\n")
            f.write("## 选题列表\n\n")
            
            for i, topic in enumerate(enriched_topics, 1):
                f.write(f"### {i}. {topic.get('topic', '')}\n\n")
                f.write(f"- **优先级**：{topic.get('priority', '')}\n")
                f.write(f"- **评分**：{topic.get('final_score', 0)}\n")
                f.write(f"- **报道角度**：{topic.get('angle', '')}\n\n")
                
                f.write("**采访对象**：\n")
                for target in topic.get('interview_plan', {}).get('interview_targets', [])[:3]:
                    f.write(f"- {target}\n")
                f.write("\n")
            
            f.write("## 稿件优化建议\n\n")
            for issue in optimization_result.get('issues', [])[:5]:
                f.write(f"- {issue}\n")
        
        print(f"  ✅ 报告已生成：{report_file}")
    except Exception as e:
        print(f"  ❌ 生成报告失败：{e}")
    
    # 保存生成的稿件（新增）
    if generated_drafts:
        for i, draft_info in enumerate(generated_drafts, 1):
            draft_file = f"data/generated_draft_{timestamp}_{i}.md"
            try:
                # 确保 draft 是字符串
                draft_content = draft_info['draft']
                if isinstance(draft_content, dict):
                    draft_content = json.dumps(draft_content, ensure_ascii=False, indent=2)
                elif not isinstance(draft_content, str):
                    draft_content = str(draft_content)
                
                with open(draft_file, 'w', encoding='utf-8') as f:
                    f.write(draft_content)
                print(f"  ✅ 稿件 {i} 已保存：{draft_file}")
            except Exception as e:
                print(f"  ❌ 保存稿件 {i} 失败：{e}")


def main():
    """主流程"""
    print("\n📋 开始执行自动化流程...")
    start_time = time.time()
    
    # 步骤1：信息采集
    data = collect_data()
    
    if not data:
        print("\n⚠️  未采集到数据，流程终止")
        return
    
    # 步骤2：线索识别
    signals = identify_signals(data)
    
    # 步骤3：选题生成
    topics = generate_topics(signals)
    
    if not topics:
        print("\n⚠️  未生成选题，流程终止")
        return
    
    # 步骤4：报道策划
    enriched_topics = plan_report(topics)
    
    if not enriched_topics:
        print("\n⚠️  报道策划失败，流程终止")
        return
    
    # 步骤5：生成完整稿件（新增）
    print("\n" + "=" * 80)
    print("步骤 5：生成完整稿件")
    print("=" * 80)
    
    generated_drafts = []
    for i, topic in enumerate(enriched_topics[:3], 1):  # 只处理前3个选题
        print(f"\n📝 生成选题 {i} 的稿件...")
        draft = generate_full_draft(topic)
        generated_drafts.append({
            'topic': topic.get('topic', ''),
            'draft': draft
        })
    
    # 步骤6：稿件优化（原步骤5）
    optimization_result = optimize_draft(enriched_topics, generated_drafts[0]['draft'] if generated_drafts else "")
    
    # 保存结果（修改以包含生成的稿件）
    save_results(enriched_topics, optimization_result, generated_drafts)
    
    # 统计
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 80)
    print("✅ 自动化流程执行完成！")
    print("=" * 80)
    print(f"\n📊 执行统计：")
    print(f"  - 采集数据：{len(data)} 条")
    print(f"  - 生成选题：{len(topics)} 个")
    print(f"  - 策划报道：{len(enriched_topics)} 个")
    print(f"  - 耗时：{elapsed_time:.2f} 秒")
    print(f"\n结果已保存到 data/ 目录")


if __name__ == '__main__':
    main()
