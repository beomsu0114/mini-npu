import json
import os
import time

EPSILON = 1e-9
BENCHMARK_ITERATIONS = 10


# ==========================================
# 1. 데이터 구조 및 패턴 생성기 (보너스 포함)
# ==========================================
class Matrix2D:
    """N×N 2차원 패턴 및 필터를 저장하고 조회하는 데이터 구조"""

    def __init__(self, grid):
        if not isinstance(grid, list) or len(grid) == 0:
            raise ValueError("유효하지 않은 2차원 배열입니다.")
        self.size = len(grid)
        for row in grid:
            if not isinstance(row, list) or len(row) != self.size:
                raise ValueError(f"행과 열의 크기가 {self.size}×{self.size}로 일치하지 않습니다.")
        # 모든 원소를 float으로 변환해 저장
        self.data = [[float(val) for val in row] for row in grid]

    def get(self, r, c):
        return self.data[r][c]

    def set(self, r, c, value):
        self.data[r][c] = float(value)

    def to_1d(self):
        """보너스: 2차원 배열을 길이 N^2의 1차원 리스트로 평탄화"""
        flat = []
        for row in self.data:
            flat.extend(row)
        return flat


def generate_pattern(n, pattern_type):
    """보너스: N×N 크기의 십자가(Cross) 또는 X 패턴 자동 생성기"""
    if n < 3 or n % 2 == 0:
        raise ValueError("대칭 패턴 생성을 위해 N은 3 이상의 홀수여야 합니다.")

    grid = [[0.0] * n for _ in range(n)]
    mid = n // 2

    if pattern_type == "Cross":
        for i in range(n):
            grid[mid][i] = 1.0
            grid[i][mid] = 1.0
    elif pattern_type == "X":
        for i in range(n):
            grid[i][i] = 1.0
            grid[i][n - 1 - i] = 1.0
    else:
        raise ValueError("지원하지 않는 패턴 타입입니다. (Cross 또는 X)")

    return Matrix2D(grid)


# ==========================================
# 2. 라벨 정규화 (표준화)
# ==========================================
def normalize_label(raw_label):
    """다양한 표기('+', 'cross', 'x', 'X')를 표준 라벨('Cross', 'X')로 정규화"""
    if not isinstance(raw_label, str):
        return str(raw_label)

    cleaned = raw_label.strip().lower()
    if cleaned in ("+", "cross"):
        return "Cross"
    if cleaned in ("x",):
        return "X"
    return raw_label.strip()


# ==========================================
# 3. MAC 연산 및 비교 정책 (외부 라이브러리 금지)
# ==========================================
def compute_mac_2d(pattern_mat, filter_mat):
    """2차원 중첩 반복문을 이용한 기본 MAC(Multiply-Accumulate) 연산"""
    n = pattern_mat.size
    p_data = pattern_mat.data
    f_data = filter_mat.data

    acc = 0.0
    for r in range(n):
        for c in range(n):
            acc += p_data[r][c] * f_data[r][c]
    return acc


def compute_mac_1d(pattern_1d, filter_1d):
    """보너스: 1차원 배열 단일 루프를 이용한 메모리 접근 최적화 MAC 연산"""
    acc = 0.0
    for i in range(len(pattern_1d)):
        acc += pattern_1d[i] * filter_1d[i]
    return acc


def judge_scores(score_a, score_b, label_a="A", label_b="B", undecided_label="UNDECIDED"):
    """허용오차(epsilon) 기반 점수 비교 및 판정"""
    if abs(score_a - score_b) < EPSILON:
        return undecided_label
    return label_a if score_a > score_b else label_b


def measure_mac_time_ms(pattern_mat, filter_mat, iterations=BENCHMARK_ITERATIONS):
    """순수 연산 함수 호출 구간의 평균 실행 시간(ms) 측정"""
    start = time.perf_counter()
    for _ in range(iterations):
        compute_mac_2d(pattern_mat, filter_mat)
    end = time.perf_counter()
    return ((end - start) / iterations) * 1000.0


# ==========================================
# 4. 모드 1: 사용자 입력 (3×3)
# ==========================================
def read_3x3_matrix(prompt_title):
    """3×3 행렬 입력 및 행/열/숫자 검증 (오류 시 재입력 유도)"""
    print(f"{prompt_title} (3줄 입력, 공백 구분)")
    while True:
        grid = []
        valid = True
        for row_idx in range(3):
            line = input().strip()
            parts = line.split()
            if len(parts) != 3:
                print(f"입력 형식 오류: 각 줄에 3개의 숫자를 공백으로 구분해 입력하세요. (현재 {row_idx + 1}번째 줄 오류 - 처음부터 다시 입력)")
                valid = False
                break
            try:
                row = [float(x) for x in parts]
                grid.append(row)
            except ValueError:
                print(f"입력 형식 오류: 숫자만 입력해야 합니다. (현재 {row_idx + 1}번째 줄 오류 - 처음부터 다시 입력)")
                valid = False
                break

        if valid:
            return Matrix2D(grid)


def run_mode_1():
    print("\n#---------------------------------------")
    print("# [1] 필터 입력")
    print("#---------------------------------------")
    choice = input("직접 입력하시겠습니까? (y: 직접 입력 / n: 자동 생성기 사용): ").strip().lower()
    if choice == "n":
        filter_a = generate_pattern(3, "Cross")
        filter_b = generate_pattern(3, "X")
        print("✓ 3×3 기본 필터 A(Cross), B(X) 자동 생성 완료")
    else:
        filter_a = read_3x3_matrix("필터 A")
        print()
        filter_b = read_3x3_matrix("필터 B")
        print("✓ 필터 A, B 저장 완료")

    print("\n#---------------------------------------")
    print("# [2] 패턴 입력")
    print("#---------------------------------------")
    pattern = read_3x3_matrix("패턴")

    # 순수 MAC 연산 수행 및 시간 측정 (10회 반복 평균)
    score_a = compute_mac_2d(pattern, filter_a)
    score_b = compute_mac_2d(pattern, filter_b)
    avg_time_ms = (
        measure_mac_time_ms(pattern, filter_a) + measure_mac_time_ms(pattern, filter_b)
    ) / 2.0

    verdict = judge_scores(
        score_a,
        score_b,
        label_a="A",
        label_b="B",
        undecided_label=f"판정 불가 (|A-B| < {EPSILON})",
    )

    print("\n#---------------------------------------")
    print("# [3] MAC 결과 & 성능 분석 (3×3)")
    print("#---------------------------------------")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/{BENCHMARK_ITERATIONS}회): {avg_time_ms:.4f} ms (연산 횟수: 9회)")
    print(f"판정: {verdict}")


# ==========================================
# 5. 모드 2: data.json 분석 및 성능 리포트
# ==========================================
def parse_size_from_key(key):
    """'size_5_1' 또는 'size_13' 형태의 키에서 정수 N 추출"""
    parts = key.split("_")
    if len(parts) < 2 or parts[0] != "size":
        raise ValueError(f"잘못된 키 형식: {key}")
    return int(parts[1])


def run_mode_2(json_path="data.json"):
    if not os.path.exists(json_path):
        print(f"\n[오류] '{json_path}' 파일을 찾을 수 없습니다. 같은 폴더에 파일을 배치해주세요.")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"\n[오류] JSON 파싱 실패: {e}")
        return

    raw_filters = raw_data.get("filters", {})
    raw_patterns = raw_data.get("patterns", {})

    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")
    filters_by_size = {}  # { 5: {"Cross": Matrix2D, "X": Matrix2D}, ... }

    for size_key, filter_dict in raw_filters.items():
        try:
            n = parse_size_from_key(size_key)
            normalized_group = {}
            for raw_f_label, grid in filter_dict.items():
                std_label = normalize_label(raw_f_label)
                mat = Matrix2D(grid)
                if mat.size != n:
                    raise ValueError(f"{size_key}의 {raw_f_label} 필터 크기가 {n}×{n}과 다릅니다.")
                normalized_group[std_label] = mat

            if "Cross" not in normalized_group or "X" not in normalized_group:
                raise ValueError(f"{size_key}에 Cross 또는 X 필터가 누락되었습니다.")

            filters_by_size[n] = normalized_group
            print(f"✓ {size_key:<7} 필터 로드 완료 (Cross, X)")
        except Exception as e:
            print(f"✗ {size_key:<7} 필터 로드 실패: {e}")

    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")
    total_tests = 0
    passed_tests = 0
    failed_cases = []  # (case_id, reason)
    benchmark_samples = {}  # { N: (pattern_mat, filter_mat) }

    # 3×3 벤치마크용 기본 샘플 사전 등록 (표에 3×3 포함 요구사항 충족)
    benchmark_samples[3] = (generate_pattern(3, "Cross"), generate_pattern(3, "Cross"))

    for case_id, case_body in raw_patterns.items():
        total_tests += 1
        print(f"--- {case_id} ---")

        try:
            n = parse_size_from_key(case_id)
            if n not in filters_by_size:
                raise ValueError(f"size_{n}에 해당하는 정상 필터가 로드되지 않았습니다.")

            if not isinstance(case_body, dict) or "input" not in case_body or "expected" not in case_body:
                raise ValueError("패턴 데이터에 'input' 또는 'expected' 필드가 누락되었습니다.")

            pattern_mat = Matrix2D(case_body["input"])
            if pattern_mat.size != n:
                raise ValueError(
                    f"크기 불일치: 키는 {n}×{n}이나 입력 패턴은 {pattern_mat.size}×{pattern_mat.size}입니다."
                )

            expected_label = normalize_label(case_body["expected"])
            if expected_label not in ("Cross", "X"):
                raise ValueError(f"알 수 없는 expected 라벨: '{case_body['expected']}'")

            cross_filter = filters_by_size[n]["Cross"]
            x_filter = filters_by_size[n]["X"]

            # 벤치마크용 샘플 저장
            if n not in benchmark_samples:
                benchmark_samples[n] = (pattern_mat, cross_filter)

            score_cross = compute_mac_2d(pattern_mat, cross_filter)
            score_x = compute_mac_2d(pattern_mat, x_filter)
            verdict = judge_scores(score_cross, score_x, label_a="Cross", label_b="X")

            print(f"Cross 점수: {score_cross}")
            print(f"X 점수: {score_x}")

            if verdict == expected_label:
                passed_tests += 1
                print(f"판정: {verdict} | expected: {expected_label} | PASS")
            else:
                if verdict == "UNDECIDED":
                    reason = f"동점(UNDECIDED) 처리 규칙에 따라 FAIL (|Cross-X| = {abs(score_cross - score_x):.2e} < {EPSILON})"
                else:
                    reason = f"판정 불일치 (판정: {verdict}, expected: {expected_label})"
                failed_cases.append((case_id, reason))
                print(f"판정: {verdict} | expected: {expected_label} | FAIL ({reason})")

        except Exception as e:
            reason = f"데이터/스키마 오류: {e}"
            failed_cases.append((case_id, reason))
            print(f"판정: ERROR | FAIL ({reason})")

    # 성능 분석 (3×3, 5×5, 13×13, 25×25)
    print("\n#---------------------------------------")
    print(f"# [3] 성능 분석 (평균/{BENCHMARK_ITERATIONS}회)")
    print("#---------------------------------------")
    print(f"{'크기':<10} {'2D 평균(ms)':<15} {'1D 최적화(ms)':<17} {'연산 횟수(N²)'}")
    print("-" * 58)

    for n in sorted(benchmark_samples.keys()):
        p_mat, f_mat = benchmark_samples[n]
        ops = n * n

        # 2D 측정
        avg_2d_ms = measure_mac_time_ms(p_mat, f_mat, BENCHMARK_ITERATIONS)

        # 보너스: 1D 최적화 측정
        p_1d = p_mat.to_1d()
        f_1d = f_mat.to_1d()
        start_1d = time.perf_counter()
        for _ in range(BENCHMARK_ITERATIONS):
            compute_mac_1d(p_1d, f_1d)
        avg_1d_ms = ((time.perf_counter() - start_1d) / BENCHMARK_ITERATIONS) * 1000.0

        size_str = f"{n}×{n}"
        print(f"{size_str:<10} {avg_2d_ms:<15.4f} {avg_1d_ms:<17.4f} {ops}")

    # 결과 요약 리포트
    print("\n#---------------------------------------")
    print("# [4] 결과 요약")
    print("#---------------------------------------")
    print(f"총 테스트: {total_tests}개")
    print(f"통과: {passed_tests}개")
    print(f"실패: {len(failed_cases)}개")

    if failed_cases:
        print("\n실패 케이스:")
        for cid, reason in failed_cases:
            print(f"- {cid}: {reason}")
    else:
        print("\n모든 테스트 케이스를 통과했습니다! (실패 0건)")


# ==========================================
# 6. 메인 실행 루프
# ==========================================
def main():
    print("=== Mini NPU Simulator ===")
    while True:
        print("\n[모드 선택]")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")
        print("0. 종료")
        choice = input("선택: ").strip()

        if choice == "1":
            run_mode_1()
        elif choice == "2":
            run_mode_2("data.json")
        elif choice == "0":
            print("시뮬레이터를 종료합니다.")
            break
        else:
            print("잘못된 선택입니다. 1, 2, 또는 0을 입력하세요.")


if __name__ == "__main__":
    main()
