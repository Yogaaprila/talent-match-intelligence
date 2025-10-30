-- Create Benchmark Based Feature on Succes Formula
/* 
The benchmark is determined based on the average of each feature within the success formula.
*/
CREATE TABLE benchmark_score AS
SELECT
  AVG("avg_STO") AS bench_STO,
  AVG("avg_SEA") AS bench_SEA,
  AVG("avg_CEX") AS bench_CEX,
  AVG("avg_CSI") AS bench_CSI,
  AVG("avg_LIE") AS bench_LIE,
  AVG("avg_QDD") AS bench_QDD,
  AVG("avg_FTC") AS bench_FTC,
  AVG("iq") AS bench_iq,
  AVG("tiki") AS bench_tiki,
  AVG("gtq") AS bench_gtq,
  AVG("years_of_service_months") AS bench_years_service
FROM df_final2
WHERE "is_high_performer" = 1;

-- Measure TV Match Rate 
/* 
The TV Match Rate will be calculated using the following formula :
TV Match Rate  =  (1- ((user score - benchmark score) /(benchmark score))) * 100
*/
CREATE TABLE talent_variable_match AS
SELECT
  f."employee_id",
  f."fullname",
  f."position_name",
  f."grade_name",
  100 * (1 - ABS(f."avg_STO" - b."bench_sto")/b."bench_sto") AS tv_STO,
  100 * (1 - ABS(f."avg_SEA" - b."bench_sea")/b."bench_sea") AS tv_SEA,
  100 * (1 - ABS(f."avg_CEX" - b."bench_cex")/b."bench_cex") AS tv_CEX,
  100 * (1 - ABS(f."avg_CSI" - b."bench_csi")/b."bench_csi") AS tv_CSI,
  100 * (1 - ABS(f."avg_LIE" - b."bench_lie")/b."bench_lie") AS tv_LIE,
  100 * (1 - ABS(f."avg_QDD" - b."bench_qdd")/b."bench_qdd") AS tv_QDD,
  100 * (1 - ABS(f."avg_FTC" - b."bench_ftc")/b."bench_ftc") AS tv_FTC,
  100 * (1 - ABS(f."iq" - b."bench_iq")/b."bench_iq") AS tv_IQ,
  100 * (1 - ABS(f."tiki" - b."bench_tiki")/b."bench_tiki") AS tv_TIKI,
  100 * (1 - ABS(f."gtq" - b."bench_gtq")/b."bench_gtq") AS tv_GTQ,
  100 * (1 - ABS(f."years_of_service_months" - b."bench_years_service")/b."bench_years_service") AS tv_Experience
FROM df_final2 f
CROSS JOIN benchmark_score b;

-- Measure TGV Match Rate
/* 
1. SEA, STO, etc., scores are included in TGV Competency. 
2. IQ, TIKI, GTQ scores are included in TGV Cognitive. 
3. Years of service scores are included in TGV Experience. 
Based on these TV values, the TGV Match Rate is obtained using the formula:
TGV Match Rate = Average(TV Competency ,TV Cognitive ,TV Experience)
*/
CREATE TABLE tgv_match AS
SELECT
  employee_id,
  fullname,
  position_name,
  grade_name,
  (tv_STO + tv_SEA + tv_CEX + tv_CSI + tv_LIE + tv_QDD + tv_FTC)/7 AS tgv_competency,
  (tv_IQ + tv_GTQ + tv_TIKI)/3 AS tgv_cognitive,
  tv_Experience AS tgv_experience
FROM talent_variable_match;

-- Measure Final Match Rate 
/* 
The features used in the success formula are determined based on the correlation results from the heatmap chart. Seven features with strong correlation, such as the average competency scores (STO, SEA, CEX, etc.), are assigned a total weight of 90%. Features with minimal influence, such as IQ, TIKI, etc., are assigned a total weight of 10%. The Final Match Rate is determined by the success formula :
FinalMatch = 0.9 × TGVCompetency + 0.05 × TGVCognitive ​+ 0.05 × TGVExperience​
*/
CREATE TABLE final_match_rate AS
SELECT
  employee_id,
  tgv_competency,
  tgv_cognitive,
  tgv_experience,
  ROUND(
    (0.9 * tgv_competency + 0.05 * tgv_cognitive + 0.05 * tgv_experience)::numeric, 
    2
  ) AS final_match_rate
FROM tgv_match;

-- Creata expected table ouput
-- Merging several tables into one: the benchmark table with the TV score table
CREATE TABLE table_1 AS
SELECT
    t.employee_id,
    t.fullname,
    t.position_name,
    t.grade_name,
    t.tv_sto,
    t.tv_sea,
    t.tv_cex,
    t.tv_csi,
    t.tv_lie,
    t.tv_ftc,
    t.tv_iq,
    t.tv_tiki,
    t.tv_gtq,
    t.tv_experience,
    b.bench_sto,
    b.bench_sea,
    b.bench_cex,
    b.bench_csi,
    b.bench_lie,
    b.bench_qdd,
    b.bench_ftc,
    b.bench_iq,
    b.bench_tiki,
    b.bench_gtq,
    b.bench_years_service
FROM
    talent_variable_match t
CROSS JOIN
    benchmark_score b;

----- The final table is the merged result of the benchmark, TV, TGV, and Final Match Rate tables.
SELECT 
    t.*, 
    f.tgv_competency,
    f.tgv_cognitive,
    f.tgv_experience,
    f.final_match_rate
FROM table_1 t
LEFT JOIN final_match_rate f 
    ON t.employee_id = f.employee_id;

select * from df_final_fix
-- thus we get final table named 'df_final_fix'