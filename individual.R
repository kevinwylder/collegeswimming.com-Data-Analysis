library(RSQLite)

name <- "Kevin D Wylder"
event <- "M4100Y"

db <- dbConnect(SQLite(), dbname="collegeswimming.db")
id <- dbGetQuery(db, paste("select id from Swimmers where name='", name, "'", sep=""))[1, ]
data <- dbGetQuery(db, paste("select date, time from", event, "where name=", id))
#times <- dbGetQuery(db, paste("select time from", event, "where name=", id))
#dates <- dbGetQuery(db, paste("select date from", event, "where name=", id))
plot(data)