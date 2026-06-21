# Comparison Report: Base vs Optimized CatBoost

|                        | Base               |   Optimized |
|:-----------------------|:-------------------|------------:|
| Model                  | CatBoost           | nan         |
| CV_R2_Mean             | 0.8649688688491883 |   0.859867  |
| CV_RMSE_Mean           | 0.1174854948054803 | nan         |
| CV_MAE_Mean            | 0.0808687879436929 | nan         |
| Train_R2_Orig          | 0.9866739061964044 |   0.951167  |
| Train_RMSE_Orig        | 0.1237005940248383 |   0.236797  |
| Train_MAE_Orig         | 0.0894326900226859 |   0.168742  |
| Val_R2_Orig            | 0.933396419886099  |   0.969217  |
| Val_RMSE_Orig          | 0.2645953045577839 |   0.179882  |
| Val_MAE_Orig           | 0.1932181324594044 |   0.142595  |
| Test_R2_Orig           | 0.9102476939826992 |   0.915099  |
| Test_RMSE_Orig         | 0.3258694330712543 |   0.316941  |
| Test_MAE_Orig          | 0.2092574741485104 |   0.216176  |
| Train_R2_Log           | 0.9847265940838266 |   0.936816  |
| Val_R2_Log             | 0.9154013578451968 |   0.957008  |
| Test_R2_Log            | 0.9167526571884708 |   0.912323  |
| Overfitting            | 0.0532774863103053 | nan         |
| Fit_Time (s)           | 6.720731496810913  | nan         |
| Train_RMSE_Log         | nan                |   0.0809248 |
| Train_MAE_Log          | nan                |   0.0581214 |
| Val_RMSE_Log           | nan                |   0.0623216 |
| Val_MAE_Log            | nan                |   0.0499349 |
| Test_RMSE_Log          | nan                |   0.0960997 |
| Test_MAE_Log           | nan                |   0.0717439 |
| Overfitting_Train_Val  | nan                |  -0.0180501 |
| Overfitting_Train_Test | nan                |   0.0360683 |