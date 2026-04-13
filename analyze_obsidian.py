#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
from pathlib import Path
from collections import defaultdict
import json

def find_all_files():
    """모든 마크다운 파일 찾기"""
    md_files = []
    for root, dirs, files in os.walk('.'):
        # .obsidian, .git, .smart-env 폴더 제외
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.normpath(os.path.join(root, file)))
    return sorted(md_files)

def extract_links(content, filepath):
    """마크다운에서 링크 추출
    - [[파일명]] 형식 (옵시디언 내부 링크)
    - [텍스트](경로) 형식 (마크다운 링크)
    """
    links = []

    # 옵시디언 내부 링크 [[파일명]] 또는 [[폴더/파일명|별칭]]
    obsidian_links = re.findall(r'\[\[([^\]]+)\]\]', content)
    for link in obsidian_links:
        # 별칭이 있으면 제거
        target = link.split('|')[0].strip()
        links.append(('obsidian', target, filepath))

    # 마크다운 링크 [텍스트](경로)
    md_links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', content)
    for text, path in md_links:
        # 외부 링크는 무시 (http, #)
        if not path.startswith('http') and not path.startswith('#'):
            links.append(('markdown', path, filepath))

    return links

def resolve_link(link_target, filepath):
    """링크 대상 파일 경로 해석"""
    # 상대 경로 해석
    current_dir = os.path.dirname(filepath)

    # 옵시디언 내부 링크는 파일명으로 검색
    if link_target.endswith('.md'):
        target_path = link_target
    else:
        target_path = link_target + '.md'

    # 절대 경로로 시도
    if os.path.exists(target_path):
        return os.path.normpath(target_path)

    # 상대 경로로 시도
    relative_path = os.path.join(current_dir, target_path)
    if os.path.exists(relative_path):
        return os.path.normpath(relative_path)

    # 전체 폴더에서 검색 (옵시디언 방식)
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            full_path = os.path.join(root, file)
            if os.path.normpath(full_path) == os.path.normpath(target_path):
                return os.path.normpath(full_path)
            # 파일명으로도 비교
            if os.path.basename(full_path) == os.path.basename(target_path):
                return os.path.normpath(full_path)

    return None

def main():
    md_files = find_all_files()
    print(f"총 마크다운 파일: {len(md_files)}\n")

    all_links = []
    broken_links = []
    duplicate_filenames = defaultdict(list)

    # 파일 내용 저장 (중복 검사용)
    file_contents = {}

    # 각 파일 분석
    for filepath in md_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                file_contents[filepath] = content

            links = extract_links(content, filepath)
            all_links.extend(links)

            # 깨진 링크 찾기
            for link_type, target, source in links:
                resolved = resolve_link(target, source)
                if resolved is None:
                    broken_links.append({
                        'type': link_type,
                        'target': target,
                        'source': source
                    })
        except Exception as e:
            print(f"오류 {filepath}: {e}")

    # 파일명 중복 찾기
    filename_map = defaultdict(list)
    for filepath in md_files:
        basename = os.path.basename(filepath)
        filename_map[basename].append(filepath)

    for basename, paths in filename_map.items():
        if len(paths) > 1:
            duplicate_filenames[basename] = paths

    # 결과 출력
    print("=" * 80)
    print("📋 분석 결과")
    print("=" * 80)

    print(f"\n총 링크 수: {len(all_links)}")
    print(f"깨진 링크: {len(broken_links)}")
    print(f"파일명 중복: {len(duplicate_filenames)}\n")

    if broken_links:
        print("\n❌ 깨진 링크 목록:")
        print("-" * 80)
        for link in broken_links:
            print(f"  [{link['type'].upper()}] {link['target']}")
            print(f"    → 소스: {link['source']}")

    if duplicate_filenames:
        print("\n⚠️  파일명 중복 목록:")
        print("-" * 80)
        for basename, paths in sorted(duplicate_filenames.items()):
            print(f"  파일명: {basename}")
            for path in paths:
                print(f"    - {path}")

    # JSON으로 저장
    report = {
        'total_files': len(md_files),
        'total_links': len(all_links),
        'broken_links': broken_links,
        'duplicate_filenames': {k: v for k, v in duplicate_filenames.items()},
        'all_files': md_files
    }

    with open('obsidian_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n✅ 분석 결과를 obsidian_analysis.json에 저장했습니다.")

if __name__ == '__main__':
    main()
