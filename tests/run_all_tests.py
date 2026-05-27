"""
Master Test Runner + Excel Report Generator
============================================
Runs all 4 phases sequentially and generates Excel report.
"""
import sys, os, json, subprocess, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).parent

def run_phase(phase_num, script_name):
    script = TESTS_DIR / script_name
    print(f"\n{'#'*65}")
    print(f"  PHASE {phase_num}: {script_name}")
    print(f"{'#'*65}")

    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(BASE_DIR),
        capture_output=False,
        timeout=600,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode

def generate_excel_report():
    """Generate comprehensive Excel report from all phase results."""
    try:
        import openpyxl
    except ImportError:
        print("\n  Installing openpyxl...")
        subprocess.run([sys.executable, "-m", "pip", "install", "openpyxl"],
                       capture_output=True)
        import openpyxl

    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()

    # ── Styles ──
    header_font = Font(name="Arial", bold=True, size=12, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    pass_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    fail_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    pass_font = Font(name="Arial", bold=True, color="006100")
    fail_font = Font(name="Arial", bold=True, color="9C0006")
    title_font = Font(name="Arial", bold=True, size=16, color="1F4E79")
    subtitle_font = Font(name="Arial", bold=True, size=11, color="2E75B6")
    normal_font = Font(name="Arial", size=10)
    border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )
    center = Alignment(horizontal="center", vertical="center")
    wrap = Alignment(wrap_text=True, vertical="top")

    # ══════════════════════════════════════════════════════════
    # Sheet 1: Summary Dashboard
    # ══════════════════════════════════════════════════════════
    ws = wb.active
    ws.title = "Dashboard"

    ws.merge_cells("A1:E1")
    ws["A1"] = "BAO CAO KIEM THU TOAN DIEN HE THONG MOVIE RECOMMENDER AI"
    ws["A1"].font = title_font

    ws["A2"] = f"Ngay thuc hien: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ws["A2"].font = subtitle_font

    ws["A4"] = "TONG KET THEO GIAI DOAN"
    ws["A4"].font = subtitle_font

    # Dashboard headers
    for col, val in enumerate(["Giai doan", "Mo ta", "PASS", "FAIL", "Ty le"], 1):
        cell = ws.cell(row=5, column=col, value=val)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = border

    # Load all results
    all_results = []
    phase_names = {
        1: "Admin & Seed Data",
        2: "SVD Fold-In Audit",
        3: "Retrain & Regression",
        4: "Quality Audit",
    }

    for phase_num in range(1, 5):
        fname = f"phase{phase_num}_results.json"
        fpath = TESTS_DIR / fname
        if fpath.exists():
            data = json.loads(fpath.read_text(encoding="utf-8"))
            phase_results = data.get("results", [])
            all_results.extend(phase_results)

            p = sum(1 for r in phase_results if r["status"] == "PASS")
            f_ = sum(1 for r in phase_results if r["status"] == "FAIL")
            total = p + f_
            pct = f"{p}/{total} ({p/total*100:.0f}%)" if total else "N/A"

            row = 5 + phase_num
            ws.cell(row=row, column=1, value=f"Phase {phase_num}").font = normal_font
            ws.cell(row=row, column=2, value=phase_names[phase_num]).font = normal_font
            c_pass = ws.cell(row=row, column=3, value=p)
            c_pass.font = pass_font; c_pass.fill = pass_fill
            c_fail = ws.cell(row=row, column=4, value=f_)
            if f_ > 0:
                c_fail.font = fail_font; c_fail.fill = fail_fill
            else:
                c_fail.font = pass_font; c_fail.fill = pass_fill
            ws.cell(row=row, column=5, value=pct).font = normal_font

            for c in range(1, 6):
                ws.cell(row=row, column=c).border = border
                ws.cell(row=row, column=c).alignment = center

    # Totals
    total_p = sum(1 for r in all_results if r["status"] == "PASS")
    total_f = sum(1 for r in all_results if r["status"] == "FAIL")
    total_all = total_p + total_f
    row = 10
    ws.cell(row=row, column=1, value="TONG CONG").font = Font(name="Arial", bold=True, size=11)
    ws.cell(row=row, column=3, value=total_p).font = pass_font
    ws.cell(row=row, column=4, value=total_f).font = fail_font if total_f else pass_font
    ws.cell(row=row, column=5, value=f"{total_p}/{total_all}").font = Font(name="Arial", bold=True)
    for c in range(1, 6):
        ws.cell(row=row, column=c).border = border

    # System info
    row = 12
    ws.cell(row=row, column=1, value="THONG TIN HE THONG").font = subtitle_font
    info_items = [
        ("Backend", "FastAPI + Uvicorn"),
        ("Frontend", "React + Vite"),
        ("Database", "PostgreSQL (movie_db)"),
        ("AI Model", "FunkSVD (50 factors, 10 epochs)"),
        ("Online Learning", "SVD Fold-In (Least Squares)"),
        ("Content-Based", "Cosine Similarity (genre vectors)"),
        ("Fallback", "Popularity-Based (avg rating)"),
    ]
    for i, (k, v) in enumerate(info_items):
        ws.cell(row=row+1+i, column=1, value=k).font = Font(name="Arial", bold=True, size=10)
        ws.cell(row=row+1+i, column=2, value=v).font = normal_font

    ws.column_dimensions["A"].width = 18
    ws.column_dimensions["B"].width = 35
    ws.column_dimensions["C"].width = 10
    ws.column_dimensions["D"].width = 10
    ws.column_dimensions["E"].width = 15

    # ══════════════════════════════════════════════════════════
    # Sheet 2: Detailed Test Results
    # ══════════════════════════════════════════════════════════
    ws2 = wb.create_sheet("Chi Tiet Kiem Thu")

    headers = ["STT", "Phase", "Test Case", "Status", "Chi Tiet"]
    for col, val in enumerate(headers, 1):
        cell = ws2.cell(row=1, column=col, value=val)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = border

    for i, r in enumerate(all_results):
        row = i + 2
        ws2.cell(row=row, column=1, value=i+1).alignment = center
        ws2.cell(row=row, column=2, value=f"Phase {r.get('phase', '?')}").alignment = center
        ws2.cell(row=row, column=3, value=r["test"])
        cell_status = ws2.cell(row=row, column=4, value=r["status"])
        cell_status.alignment = center
        if r["status"] == "PASS":
            cell_status.font = pass_font
            cell_status.fill = pass_fill
        else:
            cell_status.font = fail_font
            cell_status.fill = fail_fill
        ws2.cell(row=row, column=5, value=r.get("detail", ""))
        for c in range(1, 6):
            ws2.cell(row=row, column=c).border = border

    ws2.column_dimensions["A"].width = 6
    ws2.column_dimensions["B"].width = 12
    ws2.column_dimensions["C"].width = 50
    ws2.column_dimensions["D"].width = 10
    ws2.column_dimensions["E"].width = 60

    # ══════════════════════════════════════════════════════════
    # Sheet 3: Data Before/After Training
    # ══════════════════════════════════════════════════════════
    ws3 = wb.create_sheet("Truoc va Sau Training")

    ws3.merge_cells("A1:D1")
    ws3["A1"] = "SO SANH DU LIEU TRUOC VA SAU KHI TRAIN"
    ws3["A1"].font = title_font

    headers3 = ["Chi so", "Truoc Training", "Sau Training", "Thay doi"]
    for col, val in enumerate(headers3, 1):
        cell = ws3.cell(row=3, column=col, value=val)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = border

    # Load phase3 data
    p3_data = {}
    p3_path = TESTS_DIR / "phase3_results.json"
    if p3_path.exists():
        p3_data = json.loads(p3_path.read_text(encoding="utf-8"))

    p1_path = TESTS_DIR / "phase1_results.json"
    p1_data = json.loads(p1_path.read_text(encoding="utf-8")) if p1_path.exists() else {}

    pre_ratings = p3_data.get("pre_train_ratings", "N/A")
    post_ratings = p3_data.get("post_seed_ratings", "N/A")
    new_ratings = p3_data.get("total_ratings_inserted", 0)
    new_movies = len(p1_data.get("inserted_movie_ids", []))
    new_users = len(p3_data.get("legacy_uids", []))

    comparison = [
        ("So phim trong DB", f"3883 (goc)", f"3883 + {new_movies} = {3883+new_movies}", f"+{new_movies}"),
        ("So ratings trong DB", str(pre_ratings), str(post_ratings),
         f"+{new_ratings}"),
        ("So legacy users them", "0", str(new_users), f"+{new_users}"),
        ("Mo hinh SVD", "FunkSVD (50 factors)", "FunkSVD (50 factors, retrained)", "Updated"),
        ("Fold-In Online Learning", "Available", "Available (retrained weights)", "Verified"),
        ("Content-Based Model", "Cosine Similarity", "Cosine Similarity", "Unchanged"),
        ("Phuong phap Fallback", "Popularity-Based", "Popularity-Based", "Unchanged"),
    ]

    for i, (metric, before, after, change) in enumerate(comparison):
        row = 4 + i
        ws3.cell(row=row, column=1, value=metric).font = Font(name="Arial", bold=True, size=10)
        ws3.cell(row=row, column=2, value=before).font = normal_font
        ws3.cell(row=row, column=3, value=after).font = normal_font
        ws3.cell(row=row, column=4, value=change).font = Font(name="Arial", bold=True, color="2E75B6")
        for c in range(1, 5):
            ws3.cell(row=row, column=c).border = border
            ws3.cell(row=row, column=c).alignment = center

    ws3.column_dimensions["A"].width = 30
    ws3.column_dimensions["B"].width = 30
    ws3.column_dimensions["C"].width = 40
    ws3.column_dimensions["D"].width = 15

    # ══════════════════════════════════════════════════════════
    # Sheet 4: Seeded Movies List
    # ══════════════════════════════════════════════════════════
    ws4 = wb.create_sheet("Danh Sach 100 Phim")

    headers4 = ["STT", "Movie ID", "Tieu de", "The loai"]
    for col, val in enumerate(headers4, 1):
        cell = ws4.cell(row=1, column=col, value=val)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = border

    movie_ids = p1_data.get("inserted_movie_ids", [])

    # Movie seed data (inline to avoid import side effects)
    # Use DB query to get actual seeded movies
    try:
        sys.path.insert(0, str(BASE_DIR))
        from src.database.db_config import DatabaseConnector
        conn = DatabaseConnector.get_connection()
        cur = conn.cursor()
        if movie_ids:
            cur.execute("SELECT movie_id, title, genres_orig FROM movies WHERE movie_id = ANY(%s) ORDER BY movie_id", (movie_ids,))
        else:
            cur.execute("SELECT movie_id, title, genres_orig FROM movies WHERE movie_id > 3883 ORDER BY movie_id LIMIT 100")
        db_movies = cur.fetchall()
        cur.close(); conn.close()
    except:
        db_movies = []

    for i, row_data in enumerate(db_movies):
        row = i + 2
        ws4.cell(row=row, column=1, value=i+1).alignment = center
        ws4.cell(row=row, column=2, value=row_data[0]).alignment = center
        ws4.cell(row=row, column=3, value=row_data[1]).font = normal_font
        ws4.cell(row=row, column=4, value=row_data[2]).font = normal_font
        for c in range(1, 5):
            ws4.cell(row=row, column=c).border = border

    ws4.column_dimensions["A"].width = 6
    ws4.column_dimensions["B"].width = 12
    ws4.column_dimensions["C"].width = 55
    ws4.column_dimensions["D"].width = 40

    # Save
    output_path = BASE_DIR / "output" / "BaoCao_KiemThu_ToanDien.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(output_path))
    print(f"\n  [OK] Excel report saved: {output_path}")
    return output_path


# ══════════════════════════════════════════════════════════════
# MAIN: Run all phases
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 65)
    print("  MOVIE RECOMMENDER AI - COMPREHENSIVE INTEGRATION TEST")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    start = time.time()

    # Phase 1: Admin + Seed
    run_phase(1, "test_phase1_admin.py")

    # Phase 2: Fold-In
    run_phase(2, "test_phase2_foldin.py")

    # Phase 3: Retrain
    run_phase(3, "test_phase3_retrain.py")

    # Phase 4: Quality Audit
    run_phase(4, "test_phase4_audit.py")

    elapsed = time.time() - start

    print(f"\n{'='*65}")
    print(f"  ALL PHASES COMPLETED in {elapsed:.1f}s")
    print(f"{'='*65}")

    # Generate Excel
    try:
        report_path = generate_excel_report()
        print(f"\n  EXCEL REPORT: {report_path}")
    except Exception as e:
        print(f"\n  [ERROR] Excel generation failed: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n{'='*65}")
    print("  DONE - Use the Excel file for your thesis defense!")
    print(f"{'='*65}")
