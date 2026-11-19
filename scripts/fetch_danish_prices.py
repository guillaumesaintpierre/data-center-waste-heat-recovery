"""Optional online retrieval of ENERGINET DayAheadPrices (DK1 or DK2).

The project itself does not require internet access. This utility is not run
for the bundled synthetic case. Usage is described in docs/DATA.md.
"""
from __future__ import annotations
import argparse,json,sys,urllib.parse,urllib.request
from pathlib import Path
import pandas as pd


def fetch(start,end,area='DK2'):
    if area not in {'DK1','DK2'}:raise ValueError('Only DK1 or DK2 allowed')
    q=urllib.parse.urlencode({'start':start,'end':end,
        'filter':json.dumps({'PriceArea':[area]},separators=(',',':')),
        'sort':'TimeUTC','limit':'0'})
    url='https://api.energidataservice.dk/dataset/DayAheadPrices?'+q
    req=urllib.request.Request(url,headers={'User-Agent':'student-energy-study/1.0'})
    with urllib.request.urlopen(req,timeout=80) as stream:
        data=json.loads(stream.read())
    rows=data.get('records',[])
    if not rows:raise ValueError('No records returned; check year and provider API')
    needed={'TimeUTC','DayAheadPriceEUR'}
    if not needed.issubset(set(rows[0])):
        raise ValueError('Provider API schema changed. Review metadata and modify parser.')
    out=pd.DataFrame(rows)[['TimeUTC','DayAheadPriceEUR']].copy()
    out['TimeUTC']=pd.to_datetime(out['TimeUTC'],utc=True)
    out['DayAheadPriceEUR']=pd.to_numeric(out['DayAheadPriceEUR'],errors='raise')
    if out['TimeUTC'].duplicated().any():raise ValueError('Repeated provider timestamps')
    out=out.sort_values('TimeUTC').reset_index(drop=True)
    return url,out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start',required=True,help='YYYY-MM-DD')
    parser.add_argument('--end',required=True,help='YYYY-MM-DD (exclusive)')
    parser.add_argument('--area',choices=['DK1','DK2'],default='DK2')
    parser.add_argument('--out',default='data/day_ahead_prices.csv')
    args=parser.parse_args()
    url,frame=fetch(args.start,args.end,args.area)
    target=Path(args.out);target.parent.mkdir(parents=True,exist_ok=True)
    frame.to_csv(target,index=False)
    metadata={'provider':'Energi Data Service (Energinet)',
         'dataset':'DayAheadPrices','price_zone':args.area,'period_start':args.start,
         'period_end_exclusive':args.end,'times':'UTC',
         'unit':'EUR/MWh electrical','dataset_url':url,
         'records':len(frame),
         'note':'DayAheadPrices is a 15-min series after 2025-10-01; the simulator averages four quarter-hours per UTC hour.'}
    target.with_suffix('.metadata.json').write_text(json.dumps(metadata,indent=2))
    print(f'Saved {len(frame)} original price records to {target}')

if __name__=='__main__':main()
