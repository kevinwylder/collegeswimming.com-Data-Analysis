library(RSQLite)

sqliteDriver <- SQLite(fetch.default.rec=5000)
db <- dbConnect(sqliteDriver, dbname="collegeswimming.db")
data <- dbGetQuery(db, "select time,date from M4100Y where time < 70")
plot(data)
