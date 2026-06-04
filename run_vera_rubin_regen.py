import json
import os
from pathlib import Path

import map_generator as mg

TOPIC = "Vera Rubin 機櫃級 AI 升級追蹤"


def main():
    search_context = mg.get_search_context(TOPIC)
    print('[vera] step1 lessons')
    lessons_data = mg.generate_lessons(TOPIC, search_context)
    print('[vera] step2 structure')
    structure_data = mg.generate_structure(TOPIC, search_context, lessons_data)
    print('[vera] step3 capital_flow')
    capital_data = mg.generate_capital_flow(TOPIC, search_context, lessons_data, structure_data)
    print('[vera] step4 stocks')
    try:
        stocks_data = mg.generate_stocks(TOPIC, search_context, lessons_data, structure_data, capital_data)
    except Exception:
        raw_path = Path('last_vllm_raw_output.txt')
        if raw_path.exists():
            raw = raw_path.read_text(encoding='utf-8', errors='ignore')
            snippet = raw.rsplit('},', 1)[0].rstrip()
            if not snippet.endswith('}'):
                snippet += '\n    }'
            repaired = snippet + '\n  ]\n}'
            stocks_data = json.loads(repaired)
            print('[vera] stocks repaired from truncated raw output')
        else:
            raise
    print('[vera] step5 merge')
    merged = mg.merge_map(TOPIC, search_context, lessons_data, structure_data, capital_data, stocks_data)
    normalized = mg.normalize_generated_map(merged, TOPIC)
    valid, errors = mg.validate_map_repository(normalized)
    if not valid:
        raise RuntimeError('\n'.join(errors))
    repo = mg.load_repository()
    repo.update(normalized)
    mg.save_repository(repo)
    print('[vera] updated maps_repo.json')
    print(json.dumps(normalized, ensure_ascii=False)[:3000])


if __name__ == '__main__':
    main()
