"""Reproducible entry point: python run.py [--config config.json] [--out results]."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from heat_reuse.profiles import make_synthetic_profiles
from heat_reuse.io import write_timestamped_csv
from heat_reuse.observed import build_observed_profiles
from heat_reuse.simulation import simulate
from heat_reuse.economics import summarize
from heat_reuse.studies import scenario_cases,price_surface,assumptions_sweep,capacity_sizing
from heat_reuse.visuals import figures


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config',default='config.json')
    ap.add_argument('--out',default='results')
    args=ap.parse_args()
    cfg=json.loads(Path(args.config).read_text(encoding='utf-8'))
    p, data_meta=build_observed_profiles(cfg,make_synthetic_profiles(cfg))
    d=simulate(cfg,p)
    base=summarize(d,cfg)
    cases=scenario_cases(cfg,p)
    surface=price_surface(cfg,p)
    sweep=assumptions_sweep(cfg,p)
    sizing=capacity_sizing(cfg,p)
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    write_timestamped_csv(d,out/'hourly_results.csv')
    cases.to_csv(out/'scenario_comparison.csv',index=False)
    sweep.to_csv(out/'assumption_sweep.csv',index=False)
    sizing.to_csv(out/'capacity_sizing.csv',index=False)
    with (out/'summary.json').open('w',encoding='utf-8') as f:
        best=sizing.loc[sizing['npv_eur'].idxmax()]
        json.dump({'scenario':cfg['project_name'],'provenance':data_meta,
                  'illustrative_size_optimum':{'rated_heat_mw':round(float(best['rated_output_mw']),3),
                                              'npv_eur':round(float(best['npv_eur']),2),
                                              'warning':'Grid search under hypothetical linear CAPEX; not an equipment recommendation'},
                  'metrics':base,'limitations':[
                      'IT load, thermal demand coefficients, capture fraction and plant parameters are assumptions; weather and market prices are observed ONLY when supplied',
                      'The COP relation is a parametric approximation, not a measured heat-pump curve',
                      'PUE is background electricity only and is not counted as recovered heat',
                      'Counterfactual assumes marginal heat supplied by a gas boiler',
                      'Emissions are operational and conditional on assumed grid/boiler factors',
                      'No thermal storage, hydraulic network model, redundancy or heat-exchanger sizing',
                      'Real-capex, tax and tariff quotations are not available']},f,indent=2)
    figdir=Path('figures') if out == Path('results') else out/'figures'
    figures(d,cases,surface,sweep,sizing,figdir)
    print(json.dumps(base,indent=2))
    print(f'Wrote {out} and {figdir}. Data provenance: {data_meta}.')

if __name__=='__main__':main()
