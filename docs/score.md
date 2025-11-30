1. 频率分 freq_score
0 ~ 200      → 0 分
200 ~ 1000   → +5 分
1000 ~ 5000  → +10 分
> 5000       → +20 分
 2.状态分 error_score
 5xx > 50  → +10 分
4xx > 200 → +5 分
3.限速分 limit_score
出现一次 429 → +5 分
429 占比 > 50% → +10 分

temp_increment = freq_score + error_score + limit_score
