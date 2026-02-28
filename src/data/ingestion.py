"""
Data ingestion and cleaning for Conut bakery report-style CSVs.
All files have repeated page headers, comma-formatted numbers, and embedded metadata rows.
"""
import re
import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _clean_number(value: str) -> Optional[float]:
    """Convert comma-formatted or blank strings to float."""
    if pd.isna(value):
        return np.nan
    s = str(value).strip().replace(",", "").replace('"', "")
    if s in ("", "-", "0.00"):
        try:
            return float(s.replace("-", "0"))
        except ValueError:
            return np.nan
    try:
        return float(s)
    except ValueError:
        return np.nan


def _is_header_row(row: pd.Series, header_keywords: list[str]) -> bool:
    """Return True if the row looks like a repeated page header."""
    row_str = " ".join(str(v) for v in row if pd.notna(v))
    return any(kw.lower() in row_str.lower() for kw in header_keywords)


def _drop_copyright_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows that contain the copyright/footer boilerplate."""
    mask = df.apply(
        lambda row: row.astype(str).str.contains(
            r"Copyright|omegapos|Page \d+ of", regex=True, case=False
        ).any(),
        axis=1,
    )
    return df[~mask].reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────────────
# File-specific loaders
# ──────────────────────────────────────────────────────────────────────────────

def load_monthly_sales() -> pd.DataFrame:
    """
    rep_s_00334_1_SMRY.csv – Monthly sales by branch.
    Returns: branch, month, year, total_sales (numeric).
    """
    raw = pd.read_csv(DATA_DIR / "rep_s_00334_1_SMRY.csv", header=None, dtype=str, on_bad_lines="skip", engine="python")
    raw = _drop_copyright_rows(raw)

    records = []
    current_branch = None
    header_kws = ["Month", "Year", "Total", "Branch Name"]

    for _, row in raw.iterrows():
        row_vals = [str(v).strip() for v in row if pd.notna(v) and str(v).strip()]
        if not row_vals:
            continue
        first = row_vals[0]

        # Detect branch name lines like "Branch Name: Conut"
        if first.startswith("Branch Name"):
            current_branch = first.replace("Branch Name:", "").strip().strip(":").strip()
            continue

        if _is_header_row(row, header_kws):
            continue

        # Data rows: "August  2025  554,074,782.88"
        if len(row_vals) >= 2 and current_branch:
            month_candidate = row_vals[0]
            # skip total/grand-total rows
            if any(x in month_candidate for x in ["Total", "Grand", "REP_"]):
                continue
            months = [
                "January","February","March","April","May","June",
                "July","August","September","October","November","December",
            ]
            if any(m.lower() == month_candidate.lower() for m in months):
                year_val = None
                sales_val = None
                for v in row_vals[1:]:
                    if re.fullmatch(r"\d{4}", v):
                        year_val = int(v)
                    else:
                        n = _clean_number(v)
                        if n is not None and not np.isnan(n) and n > 0:
                            sales_val = n
                if year_val and sales_val is not None:
                    records.append(
                        dict(branch=current_branch, month=month_candidate,
                             year=year_val, total_sales=sales_val)
                    )

    df = pd.DataFrame(records)
    # Month ordering
    month_order = {m: i for i, m in enumerate(
        ["January","February","March","April","May","June",
         "July","August","September","October","November","December"], 1
    )}
    df["month_num"] = df["month"].map(month_order)
    df.sort_values(["branch","year","month_num"], inplace=True)
    return df.reset_index(drop=True)


def load_branch_tax_summary() -> pd.DataFrame:
    """
    REP_S_00194_SMRY.csv – Tax (revenue) summary by branch.
    Returns: branch, vat_total (proxy for revenue).
    """
    raw = pd.read_csv(DATA_DIR / "REP_S_00194_SMRY.csv", header=None, dtype=str, on_bad_lines="skip", engine="python")
    records = []
    current_branch = None
    for _, row in raw.iterrows():
        row_vals = [str(v).strip() for v in row if pd.notna(v) and str(v).strip()]
        if not row_vals:
            continue
        first = row_vals[0]
        if "Branch Name" in first:
            current_branch = first.replace("Branch Name:", "").strip().strip(":").strip()
        elif first == "Total By Branch" and current_branch:
            total = _clean_number(row_vals[1]) if len(row_vals) > 1 else np.nan
            records.append(dict(branch=current_branch, revenue=total))
    return pd.DataFrame(records)


def load_sales_by_item() -> pd.DataFrame:
    """
    rep_s_00191_SMRY.csv – Sales by items and groups (all branches).
    Returns: branch, division, group, item, qty, total_amount.
    """
    raw = pd.read_csv(DATA_DIR / "rep_s_00191_SMRY.csv", header=None, dtype=str, on_bad_lines="skip", engine="python")
    raw = _drop_copyright_rows(raw)

    records = []
    current_branch = current_division = current_group = None
    skip_kws = ["Description", "Barcode", "Total by", "Branch:", "Division:", "Group:"]

    for _, row in raw.iterrows():
        row_vals = [str(v).strip() for v in row if pd.notna(v) and str(v).strip()]
        if not row_vals:
            continue
        first = row_vals[0]

        if first.startswith("Branch:"):
            current_branch = first.replace("Branch:", "").strip()
        elif first.startswith("Division:"):
            current_division = first.replace("Division:", "").strip()
        elif first.startswith("Group:"):
            current_group = first.replace("Group:", "").strip()
        elif any(first.startswith(k) for k in skip_kws):
            continue
        elif current_branch and current_group and len(row_vals) >= 3:
            # item row: name, (barcode?), qty, amount
            # skip total rows
            if "Total" in first or "REP_" in first:
                continue
            # try to parse qty and amount from the last two numeric fields
            nums = []
            item_name = first
            for v in row_vals[1:]:
                n = _clean_number(v)
                if n is not None and not np.isnan(n):
                    nums.append(n)
            if len(nums) >= 2:
                records.append(dict(
                    branch=current_branch,
                    division=current_division,
                    group=current_group,
                    item=item_name,
                    qty=nums[0],
                    total_amount=nums[-1],
                ))
            elif len(nums) == 1:
                records.append(dict(
                    branch=current_branch,
                    division=current_division,
                    group=current_group,
                    item=item_name,
                    qty=nums[0],
                    total_amount=0.0,
                ))

    return pd.DataFrame(records)


def load_delivery_line_items() -> pd.DataFrame:
    """
    REP_S_00502.csv – Sales by customer (delivery), line-item detail.
    Returns: branch, customer, item, qty, price.
    Used for combo (basket) analysis.
    """
    raw = pd.read_csv(DATA_DIR / "REP_S_00502.csv", header=None, dtype=str, on_bad_lines="skip", engine="python")
    raw = _drop_copyright_rows(raw)

    records = []
    current_branch = current_customer = None

    for _, row in raw.iterrows():
        row_vals = [str(v).strip() for v in row if pd.notna(v) and str(v).strip()]
        if not row_vals:
            continue
        first = row_vals[0]

        if first.startswith("Branch :"):
            current_branch = first.replace("Branch :", "").strip()
        elif re.fullmatch(r"Person_\d+", first):
            current_customer = first
        elif first in ("Full Name", "Total :") or _is_header_row(
            row, ["Full Name","Qty","Description","Price","From Date","To Date","Page"]
        ):
            continue
        elif current_customer and current_branch:
            # item row: qty in first numeric col, description, price
            qty_str = row_vals[0]
            if qty_str and len(row_vals) >= 3:
                try:
                    qty = float(qty_str)
                except ValueError:
                    continue
                desc = row_vals[1].strip().lstrip()
                price = _clean_number(row_vals[-1]) if len(row_vals) > 2 else 0.0
                if desc and not desc.startswith("Total"):
                    records.append(dict(
                        branch=current_branch,
                        customer=current_customer,
                        item=desc,
                        qty=qty,
                        price=price if price else 0.0,
                    ))

    return pd.DataFrame(records)


def load_customer_orders() -> pd.DataFrame:
    """
    rep_s_00150.csv – Customer orders (delivery) with first/last order dates, totals.
    Returns: branch, customer, first_order, last_order, total, num_orders.
    """
    raw = pd.read_csv(DATA_DIR / "rep_s_00150.csv", header=None, dtype=str,
                      on_bad_lines="skip", engine="python")
    raw = _drop_copyright_rows(raw)

    records = []
    current_branch = None

    for _, row in raw.iterrows():
        row_vals = [str(v).strip() for v in row if pd.notna(v) and str(v).strip()]
        if not row_vals:
            continue
        first = row_vals[0]

        if _is_header_row(row, ["Customer Name","Address","Phone","First Order","Page","From Date"]):
            continue

        # Branch header rows appear as stand-alone branch name lines
        known_branches = ["Conut - Tyre","Conut Jnah","Main Street Coffee","Conut"]
        if first in known_branches:
            current_branch = first
            continue

        if re.fullmatch(r"Person_\d+", first) and current_branch and len(row_vals) >= 5:
            # row: customer, address, phone, first_order, last_order, total, num_orders
            try:
                total = _clean_number(row_vals[-2])
                num_orders = int(float(row_vals[-1]))
                # dates in various positions
                dates = [v for v in row_vals if re.match(r"\d{4}-\d{2}-\d{2}", v)]
                first_order = pd.to_datetime(dates[0], errors="coerce") if dates else pd.NaT
                last_order = pd.to_datetime(dates[1], errors="coerce") if len(dates) > 1 else first_order
                records.append(dict(
                    branch=current_branch,
                    customer=first,
                    first_order=first_order,
                    last_order=last_order,
                    total=total,
                    num_orders=num_orders,
                ))
            except (IndexError, ValueError):
                continue

    return pd.DataFrame(records)


def load_attendance() -> pd.DataFrame:
    """
    REP_S_00461.csv – Time & Attendance logs.
    Returns: employee_id, name, branch, date, punch_in, punch_out, work_hours.
    """
    raw = pd.read_csv(DATA_DIR / "REP_S_00461.csv", header=None, dtype=str, on_bad_lines="skip", engine="python")

    records = []
    current_emp_id = current_emp_name = current_branch = None

    for _, row in raw.iterrows():
        row_vals = [str(v).strip() for v in row if pd.notna(v) and str(v).strip()]
        if not row_vals:
            continue
        first = row_vals[0]

        # Employee header: "EMP ID :1.0" and "NAME :Person_0001"
        if "EMP ID" in first:
            emp_id_match = re.search(r"EMP ID\s*:\s*([\d.]+)", first)
            if emp_id_match:
                current_emp_id = int(float(emp_id_match.group(1)))
            name_parts = [v for v in row_vals if "NAME" in v]
            if name_parts:
                name_match = re.search(r"NAME\s*:\s*(Person_\d+)", name_parts[0])
                if name_match:
                    current_emp_name = name_match.group(1)
        # Branch name (a line with a known branch, no date pattern)
        elif any(b in first for b in ["Conut","Main Street"]) and not re.match(r"\d{2}-", first):
            current_branch = first.strip()
        # Date row: "01-Dec-25  07.39.35  01-Dec-25  19.37.56  11.58.21"
        elif re.match(r"\d{2}-\w{3}-\d{2}", first):
            try:
                date_str = first  # e.g. 01-Dec-25
                work_duration_str = row_vals[-1]  # e.g. 11.58.21 or 173:36:38
                # Parse punch_in / punch_out times
                time_vals = [v for v in row_vals if re.match(r"\d{2}[.:]\d{2}[.:]\d{2}", v)]
                punch_in_str = time_vals[0] if time_vals else None
                punch_out_str = time_vals[1] if len(time_vals) > 1 else None

                def parse_duration(s: str) -> float:
                    """Return decimal hours from HH.MM.SS or HH:MM:SS."""
                    s = s.replace(".", ":")
                    parts = s.split(":")
                    if len(parts) == 3:
                        return int(parts[0]) + int(parts[1]) / 60 + int(parts[2]) / 3600
                    return 0.0

                # Skip "Total :" rows
                if "Total" in str(row_vals):
                    continue

                work_hours = parse_duration(work_duration_str)
                records.append(dict(
                    employee_id=current_emp_id,
                    employee_name=current_emp_name,
                    branch=current_branch,
                    date=pd.to_datetime(date_str, format="%d-%b-%y", errors="coerce"),
                    punch_in=punch_in_str,
                    punch_out=punch_out_str,
                    work_hours=work_hours,
                ))
            except (IndexError, ValueError):
                continue

    return pd.DataFrame(records)


def load_menu_avg_sales() -> pd.DataFrame:
    """
    rep_s_00435_SMRY.csv – Average sales by menu (channel).
    Returns: branch, menu_channel, num_customers, sales, avg_per_customer.
    """
    raw = pd.read_csv(DATA_DIR / "rep_s_00435_SMRY.csv", header=None, dtype=str, on_bad_lines="skip", engine="python")
    raw = _drop_copyright_rows(raw)

    records = []
    current_branch = None
    for _, row in raw.iterrows():
        row_vals = [str(v).strip() for v in row if pd.notna(v) and str(v).strip()]
        if not row_vals:
            continue
        first = row_vals[0]

        if _is_header_row(row, ["Menu Name","# Cust","Sales","Avg","Page","Year"]):
            continue
        if first in ["Conut - Tyre","Conut","Conut Jnah","Main Street Coffee"]:
            current_branch = first
        elif first in ["DELIVERY","TABLE","TAKE AWAY"] and current_branch and len(row_vals) >= 4:
            nums = []
            for v in row_vals[1:]:
                n = _clean_number(v)
                if n is not None and not np.isnan(n):
                    nums.append(n)
            if len(nums) >= 3:
                records.append(dict(
                    branch=current_branch,
                    menu_channel=first,
                    num_customers=nums[0],
                    sales=nums[1],
                    avg_per_customer=nums[2],
                ))

    return pd.DataFrame(records)


def load_division_summary() -> pd.DataFrame:
    """
    REP_S_00136_SMRY.csv – Summary by division/menu channel.
    Returns: branch, category, delivery, table, takeaway, total.
    """
    raw = pd.read_csv(DATA_DIR / "REP_S_00136_SMRY.csv", header=None, dtype=str, on_bad_lines="skip", engine="python")
    raw = _drop_copyright_rows(raw)

    # The file has two layout styles; we parse the simpler repeating-row style
    records = []
    current_branch = None

    for _, row in raw.iterrows():
        vals = [str(v).strip() for v in row]
        row_stripped = [v for v in vals if v]
        if not row_stripped:
            continue
        first = row_stripped[0]

        known_branches = ["Conut","Conut - Tyre","Conut Jnah","Main Street Coffee"]
        if first in known_branches:
            current_branch = first

        if _is_header_row(row, ["DELIVERY","TABLE","TAKE AWAY","TOTAL","Page","Year","Summary"]):
            continue

        # Look for rows where col[0]=branch, col[1]=category, then 4 numbers
        if len(vals) >= 6 and current_branch:
            cat = vals[1].strip() if vals[1].strip() else None
            if cat and not any(
                x in cat for x in ["TOTAL","Total","Copyright","REP_","www.","Page","Year"]
            ):
                nums = []
                for v in vals[2:]:
                    n = _clean_number(v)
                    if n is not None:
                        nums.append(n)
                if len(nums) >= 3:
                    records.append(dict(
                        branch=current_branch,
                        category=cat,
                        delivery=nums[0],
                        table=nums[1] if len(nums) > 1 else 0,
                        takeaway=nums[2] if len(nums) > 2 else 0,
                        total=nums[3] if len(nums) > 3 else sum(nums[:3]),
                    ))

    return pd.DataFrame(records)


# ──────────────────────────────────────────────────────────────────────────────
# Master loader
# ──────────────────────────────────────────────────────────────────────────────

def load_all():
    """Return a dict of all cleaned DataFrames."""
    return {
        "monthly_sales": load_monthly_sales(),
        "branch_revenue": load_branch_tax_summary(),
        "sales_by_item": load_sales_by_item(),
        "delivery_items": load_delivery_line_items(),
        "customer_orders": load_customer_orders(),
        "attendance": load_attendance(),
        "menu_avg_sales": load_menu_avg_sales(),
        "division_summary": load_division_summary(),
    }


if __name__ == "__main__":
    datasets = load_all()
    for name, df in datasets.items():
        print(f"\n{'='*50}")
        print(f"{name}: {df.shape}")
        print(df.head(3))
