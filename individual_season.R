library(RSQLite)
require(ggplot2)
library(scales)

# create a database object and get command line args
nameId <- commandArgs(trailingOnly=TRUE)[1]
title <- commandArgs(trailingOnly=TRUE)[2]
dateStart <- commandArgs(trailingOnly=TRUE)[3]
dateEnd <- commandArgs(trailingOnly=TRUE)[4]
db <- dbConnect(SQLite(), dbname=commandArgs(trailingOnly=TRUE)[5])

# get the data from the database
command <- paste("select scaled, date, event from Swims where swimmer=", nameId, "and date>", dateStart, "and date<", dateEnd)
data <- dbGetQuery(db, command)
data$asDate <- as.Date(as.POSIXct(data$date, origin="1970-01-01"))

stopifnot(nrow(data)!=0)

#graph and save the data
graph <- ggplot(data, aes(x=asDate, y=scaled))
graph <- graph + geom_point(aes(color=event))
graph <- graph + geom_line(aes(color=event))
graph <- graph + theme_bw()
graph <- graph + labs(x="Date", y="Scaled Time", title=title)
graph <- graph + scale_x_date()
ggsave(filename=paste("graphs/individual", nameId, ",", dateStart, "-", dateEnd,".png", sep=""), width=12, height=6)