library(RSQLite)
require(ggplot2)
library(scales)

# create a database object and get command line args
db <- dbConnect(SQLite(), dbname="collegeswimming.db")
teamId <- commandArgs(trailingOnly=TRUE)[1]
title <- commandArgs(trailingOnly=TRUE)[2]
dateStart <- commandArgs(trailingOnly=TRUE)[3]
dateEnd <- commandArgs(trailingOnly=TRUE)[4]

# get the data
command <- paste("select scaled, date, taper from Swims where team=", teamId, "and date>", dateStart, "and date<", dateEnd, "and taper!=3")
data <- dbGetQuery(db, command)
data$asDate <- as.Date(as.POSIXct(data$date, origin="1970-01-01"))

#graph and save the data
graph <- ggplot(data, aes(x=asDate, y=scaled, group=date))
graph <- graph + scale_x_date(breaks=date_breaks("months"), labels=date_format("%b"))
graph <- graph + geom_boxplot() #aes(fill=factor(taper, labels=c("tapered", "untapered"))))
graph <- graph + theme_bw()
graph <- graph + labs(x="Date", y="Scaled Time", title=title)
ggsave(filename=paste("graphs/", teamId, ",", dateStart, "-", dateEnd,".png", sep=""), width=12, height=6)