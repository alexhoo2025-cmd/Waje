from pathlib import Path
from build_full_queries import base

P=Path(__file__).resolve().parent

def main():
    sql=base()
    sql=sql.replace('extra_num,bet_count,is_robot,is_test_uid\n FROM',
      'extra_num,bet_count,is_robot,is_test_uid,salt_key,unique_id,unique_id_bar,server_time\n FROM')
    sql=sql.replace("AND app_id=90006 AND event_type='GAMEEND'", "AND app_id=90006 AND event_type='GAMEEND' AND target_day IN (DATE '2026-08-05',DATE '2026-08-25',DATE '2026-08-30')")
    sql=sql.replace('), labelled AS (',"""), ranked_events AS (
 SELECT stat_date,user_id,play_id,mode_id,bet_num,cash_settlement,refund_num,extra_num,bet_count,is_robot,is_test_uid,
 ROW_NUMBER() OVER(PARTITION BY stat_date,user_id,play_id,unique_id,unique_id_bar ORDER BY SAFE_CAST(server_time AS INT64) DESC,salt_key DESC) AS round_rank,
 COUNT(DISTINCT TO_JSON_STRING(STRUCT(bet_num,cash_settlement,refund_num,extra_num,mode_id))) OVER(PARTITION BY stat_date,user_id,play_id,unique_id,unique_id_bar) AS amount_variants
 FROM events
), labelled AS (""")
    sql=sql.replace('e.refund_num,e.extra_num,e.bet_count','e.refund_num,e.extra_num,e.bet_count,e.round_rank,e.amount_variants')
    sql=sql.replace('FROM events e LEFT JOIN','FROM ranked_events e LEFT JOIN')
    sql+="""SELECT
 CASE WHEN GROUPING(stat_date)=0 THEN 'core_correction' WHEN GROUPING(play_id)=0 THEN 'game_correction' ELSE 'quality_total' END AS correction_grain,
 stat_date,product_mode,channel_platform,platform,provider,age_group,play_id,
 COUNT(DISTINCT user_id) AS population_accounts,
 COUNTIF(round_rank>1) AS duplicate_records,
 COUNTIF(round_rank>1 AND effective_stake>0) AS duplicate_positive_records,
 SUM(IF(round_rank>1,effective_stake,0)) AS duplicate_stake_source_units,
 SUM(IF(round_rank>1,settlement,0)) AS duplicate_settlement_source_units,
 SUM(IF(round_rank>1,COALESCE(extra_num,0),0)) AS duplicate_extra_source_units,
 SUM(IF(round_rank>1,COALESCE(refund_num,0),0)) AS duplicate_refund_source_units,
 COUNTIF(round_rank>1 AND amount_variants>1) AS duplicate_records_with_conflicting_amounts
FROM labelled
GROUP BY GROUPING SETS((stat_date,product_mode,channel_platform,platform,provider,age_group),
 (product_mode,platform,provider,play_id),(product_mode,provider))
HAVING COUNT(DISTINCT user_id)>=10 AND COUNTIF(round_rank>1)>0
ORDER BY correction_grain,stat_date,product_mode,platform,provider,play_id
LIMIT 500;
"""
    path=P/'sql/21_targeted_duplicate_corrections.sql'
    if path.exists():raise RuntimeError('Preserve existing SQL')
    path.write_text(sql)
    print('Generated targeted aggregate correction; no row-level results')

if __name__=='__main__':main()
