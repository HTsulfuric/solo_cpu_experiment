# Results Directory / 結果ディレクトリ

## Main Output Files / 主要な出力ファイル

### Ray Tracing Output / レイトレーシング出力

- **`contest_64x64_python.ppm`** / **`contest_64x64_python.png`**
  - Python実装によるcontest.sldの64x64レンダリング結果
  - 完全なmin-rt実装（影、反射、テクスチャ対応）
  - Output from Python implementation of min-rt (64x64 rendering of contest.sld)
  - Full implementation with shadows, reflections, and textures

- **`contest_64x64_reference_cpp.ppm`** / **`contest_64x64_reference_cpp.png`**
  - C++リファレンス実装による出力（検証用）
  - min-caml公式リポジトリのRayTrace.cxxによる出力
  - Reference output from C++ implementation (for validation)
  - Generated using RayTrace.cxx from official min-caml repository

### Comparison / 比較結果

Python実装とC++リファレンスの比較:
- 82%のピクセルが完全一致
- 94%のピクセルが±2以内（浮動小数点丸め誤差）
- 残りの差分は異なる言語間での浮動小数点演算の精度差によるもの（許容範囲内）

Comparison between Python and C++ implementations:
- 82% of pixels are identical
- 94% of pixels differ by ≤2 (floating point rounding)
- Remaining differences are due to FP precision variations (acceptable)

## Subdirectories / サブディレクトリ

### `reports/`
開発過程のレポートとログ:
- `compiler_optimization_report.md` - コンパイラ最適化レポート
- `optimization_report.md` - 最適化戦略レポート
- `final_summary.txt` - 最終サマリー
- `instruction_count.txt` - 命令数カウント
- `sample_assembly.asm` - サンプルアセンブリコード
- `execution_*.md` / `*.txt` - 実行ログ

Development reports and logs:
- Compiler optimization reports
- Instruction count analysis
- Sample assembly code
- Execution logs

### `archive/`
中間生成物とデバッグ用ファイル:
- `contest_fixed*.ppm` - バグ修正過程の中間出力
- `contest_verify.ppm` - 検証実行の出力
- `contest_64x64_final.ppm` - 古いバージョンの出力
- `output_64x64.ppm` - 初期テスト出力
- `ball_test.ppm` - 単純なテストシーン

Intermediate files and debugging outputs:
- Bug fixing iterations
- Verification runs
- Old versions
- Test scenes

## Tools Used / 使用ツール

レンダリング出力の生成と検証に使用したツール:
- `../minrt_correct.py` - 完全なmin-rt Python実装
- `../raytracer` (C++) - リファレンス実装（コンパイル済み）
- `../tools/compare_ppm.py` - PPMファイル比較ツール
- `../tools/analyze_diffs.py` - ピクセル差分分析ツール
- `../tools/ppm_to_png.py` - PPM→PNG変換ツール

Tools used for generating and validating outputs:
- Complete min-rt Python implementation
- C++ reference implementation (compiled)
- PPM comparison and analysis tools
- PPM to PNG converter
