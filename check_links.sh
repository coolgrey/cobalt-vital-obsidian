#!/bin/bash

broken_links=()
all_md_files=$(find . -type f -name "*.md" -not -path "./.*" | sort)

# 모든 링크 수집 및 확인
while IFS= read -r file; do
    # [[링크]] 형식 찾기
    while IFS= read -r line; do
        # [[...]] 패턴 추출
        while [[ $line =~ \[\[([^\]]+)\]\] ]]; do
            link="${BASH_REMATCH[1]}"
            # 별칭 제거 (| 이후)
            target="${link%%|*}"
            
            # 파일 존재 여부 확인
            target_file="${target}.md"
            if [[ ! "$target" =~ \.md$ ]]; then
                target_file="${target}.md"
            else
                target_file="$target"
            fi
            
            # 찾기
            found=0
            if [ -f "$target_file" ]; then
                found=1
            elif [ -f "$target" ]; then
                found=1
            else
                # 루트에서 파일 검색
                if find . -type f -name "${target_file##*/}" -o -name "${target##*/}" 2>/dev/null | grep -q .; then
                    found=1
                fi
            fi
            
            if [ $found -eq 0 ]; then
                broken_links+=("$target (in: $file)")
            fi
            
            line="${line#*]]}}" # 처리한 링크 제거
        done
    done < "$file"
done <<< "$all_md_files"

echo "=== 깨진 링크 목록 ==="
if [ ${#broken_links[@]} -eq 0 ]; then
    echo "깨진 링크 없음 ✅"
else
    printf '%s\n' "${broken_links[@]}" | sort -u
fi
echo ""
echo "총 깨진 링크: ${#broken_links[@]}"
