library(RSQLite)
require(ggplot2)
library(scales)

# create a database object and get command line args
db <- dbConnect(SQLite(), dbname="collegeswimming.db")
nameId <- 195199 #commandArgs(trailingOnly=TRUE)[1]
title <- "Kevin Wylder 2014-2015 Season" #commandArgs(trailingOnly=TRUE)[2]
dateStart <- 1410739200 #commandArgs(trailingOnly=TRUE)[3]
dateEnd <- 1442275200 #commandArgs(trailingOnly=TRUE)[4]

# get the data from the database
command <- paste("select scaled, date, event from Swims where swimmer=", nameId, "and date>", dateStart, "and date<", dateEnd)
data <- dbGetQuery(db, command)
data$asDate <- as.Date(as.POSIXct(data$date, origin="1970-01-01"))

#graph and save the data
graph <- ggplot(data, aes(x=asDate, y=scaled))
graph <- graph + geom_point(aes(color=event))
graph <- graph + theme_bw()
graph <- graph + labs(x="Date", y="Scaled Time", title=title)
graph <- graph + scale_x_date()