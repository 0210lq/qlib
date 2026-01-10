import os
import argparse
import pickle
from datetime import datetime
import pandas as pd
import numpy as np
import qlib
from qlib.utils import init_instance_by_config
from qlib.data import D
import sys
import yaml
from pathlib import Path
from config_utils import load_config_with_substitution

def parse_args():
    p = argparse.ArgumentParser()
    cfg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'paths.yaml'))
    script_dir = Path(__file__).parent.absolute()
    config_path = os.path.join(script_dir, '..', 'Optimizer_matlab','config', 'opt_project_config_history.xlsx')
    portfolio_info_df = pd.read_excel(config_path, sheet_name='portfolio_info')
    start_date = portfolio_info_df['start_date'].tolist()
    start_date = min(start_date).strftime('%Y-%m-%d')
    end_date = portfolio_info_df['end_date'].tolist()
    end_date = max(end_date).strftime('%Y-%m-%d')




    cfg = load_config_with_substitution(cfg_path)
    provider_uri = cfg['provider_uri']
    model_path = cfg['model_path']
    output_dir = cfg['prediction_output_dir']


    p.add_argument("--model-path", default=model_path)
    p.add_argument("--provider-uri", default=provider_uri, help="Qlib provider uri")
    p.add_argument("--output-dir", default=output_dir, help="Directory to save daily CSVs")
    p.add_argument('--start_date', default=start_date, type=str, help='开始日期')
    p.add_argument('--end_date', default=end_date, type=str, help='结束日期')
    p.add_argument("--instruments", default="all", help="Market instruments argument passed to D.instruments (default 'all')")
    p.add_argument("--debug", action="store_true", help="Print diagnostic info (length checks, per-date counts)")
    return p.parse_args()


def main():
    args = parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # initialize qlib provider first so D.instruments works
    qlib.init(provider_uri=args.provider_uri)

    print("Loading model:", args.model_path)
    with open(args.model_path, "rb") as f:
        model = pickle.load(f)

    instruments = D.instruments(market=args.instruments)
    if getattr(args, "debug", False):
        try:
            instr_sample = list(instruments)[:20]
        except Exception:
            instr_sample = instruments
        try:
            print("DEBUG: D.instruments returned count:", len(instruments), "sample:", instr_sample)
        except Exception:
            print("DEBUG: D.instruments returned (unable to get len/sample)")

    handler_config = {
        "start_time": args.start_date,
        "end_time": args.end_date,
        "instruments": instruments,
    }

    dataset_config = {
        "class": "DatasetH",
        "module_path": "qlib.data.dataset",
        "kwargs": {
            "handler": {
                "class": "Alpha158",
                "module_path": "qlib.contrib.data.handler",
                "kwargs": handler_config,
            },
            "segments": {
                "test": [args.start_date, args.end_date],
            },
        },
    }

    # Disable qlib multiprocessing for predict stability
    os.environ["QLIB_DISABLE_MP"] = "1"

    dataset = init_instance_by_config(dataset_config)
    test_df = dataset.prepare("test")

    # Run prediction across the full test dataset
    print("Generating predictions for test set...")
    pred = model.predict(dataset)
    pred_values = pred.values if isinstance(pred, pd.Series) else pred.ravel()

    # Diagnostic checks: ensure prediction length matches prepared test dataframe
    if getattr(args, "debug", False):
        try:
            import numpy as _np
        except Exception:
            _np = None
        print("DEBUG: test_df rows:", len(test_df))
        try:
            print("DEBUG: pred type:", type(pred), " pred length:", len(pred_values))
        except Exception:
            print("DEBUG: unable to determine pred length/type")

    # Recover index levels for datetime and instrument
    idx_names = test_df.index.names
    try:
        datetimes = test_df.index.get_level_values("datetime")
    except Exception:
        datetimes = test_df.index.get_level_values(0)

    try:
        instruments_idx = test_df.index.get_level_values("instrument")
    except Exception:
        # assume instrument is second level
        instruments_idx = test_df.index.get_level_values(1)

    df = pd.DataFrame({
        "datetime": pd.to_datetime(datetimes),
        "code": instruments_idx,
        "final_score": pred_values,
        "score_name": "vp08"
    })

    try:
        scores = df['final_score'].astype(float)
        raw_scores = scores.copy()
        mean_s = scores.mean()
        std_s = scores.std(ddof=0)
        if pd.isna(mean_s) or pd.isna(std_s):
            df['final_score'] = scores
        else:
            if std_s == 0 or np.isclose(std_s, 0):
                z_scores = pd.Series(0.0, index=scores.index)
            else:
                z_scores = (scores - mean_s) / std_s
            try:
                max_abs_z = np.nanmax(np.abs(z_scores.values))
            except Exception:
                max_abs_z = 0
            if max_abs_z == 0 or np.isclose(max_abs_z, 0):
                norm_scores = pd.Series(0.0, index=scores.index)
            else:
                norm_scores = z_scores / float(max_abs_z)
            df['raw_score'] = raw_scores
            df['final_score'] = norm_scores
    except Exception as e:
        print(f"标准化失败，使用原始分数继续：{e}")

    if getattr(args, "debug", False):
        # show first few index entries and a per-date count to help diagnose missing rows
        print("DEBUG: sample of prepared test dataframe index (first 10):")
        try:
            print(test_df.index[:10])
        except Exception:
            print("DEBUG: could not print test_df.index slice")
        df["date_str"] = df["datetime"].dt.strftime("%Y%m%d")
        counts = df.groupby("date_str").size()
        print("DEBUG: counts per date (sample 20):")
        print(counts.head(20).to_string())
        # continue normal flow

    df["date_str"] = df["datetime"].dt.strftime("%Y%m%d")

    print("Exporting daily CSVs to:", args.output_dir)
    grouped = df.groupby("date_str")
    count = 0
    for date_str, g in grouped:
        custom_path  = os.getenv('GLOBAL_TOOLSFUNC_test')
        sys.path.append(custom_path )
        converted_dates = pd.to_datetime(date_str, format='%Y%m%d').strftime('%Y-%m-%d')
        import global_tools as gt
        pre_date = gt.last_workday_calculate(converted_dates)
    

        out_path = os.path.join(args.output_dir, f"prediction_{pre_date}.csv")
        # Only keep code and score columns
        g_out = g[["code", "final_score", "score_name"]].sort_values("final_score", ascending=False)
        g_out.to_csv(out_path, index=False)
        count += 1
        # Optionally print each code's score to stdout
        if getattr(args, "print_console", False):
            print("\n===== Predictions for", pre_date, "=====")
            try:
                print(g_out.to_string(index=False))
            except Exception:
                for _, row in g_out.iterrows():
                    print(f"{row['code']}: {row['final_score']}")

    print(f"Exported {count} daily files to {args.output_dir}")


if __name__ == "__main__":
    main()
