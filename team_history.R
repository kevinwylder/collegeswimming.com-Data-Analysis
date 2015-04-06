library(RSQLite)
require(ggplot2)
library(scales)

# create a database object and get command line args
teamId <- commandArgs(trailingOnly=TRUE)[1]
title <- commandArgs(trailingOnly=TRUE)[2]
dateStart <- as.integer(commandArgs(trailingOnly=TRUE)[3])
dateEnd <- as.integer(commandArgs(trailingOnly=TRUE)[4])
db <- dbConnect(SQLite(), dbname=commandArgs(trailingOnly=TRUE)[5])
dateStep <- 31536000 # one year

command <- paste("select event from Swims where team=", teamId, "and date>", dateStart, "and date<", dateEnd)
events <- unique(dbGetQuery(db, command)$event)

distance <- integer()
stroke <- character()
gender <- character()
scale <- double()
date <- integer()

for(event in events){
	for(start in seq(dateStart, dateEnd, by=dateStep)){
		command <- paste("select avg(scaled) from Swims where event='", event,"' and team=", teamId, " and date>", start, " and date<", start + dateStep, " and taper!=3", sep="")
		avg <- dbGetQuery(db, command)$"avg(scaled)"
		distance <- c(distance, as.integer(substring(event, 3, nchar(event) - 1)))
		gender <- c(gender, substring(event, 1, 1))
		stroke <- c(stroke, substring(event, 2, 2))
		scale <- c(scale, avg)
		date <- c(date, start)
	}
}

date <- as.Date(as.POSIXct(date, origin="1970-01-01"))
scale <- as.double(scale)
df <- data.frame(date, scale, stroke, distance)
print(typeof(df$scale))
graph <- ggplot(df, aes(x=date, y=scale, color=gender, shape=stroke, size=log(distance) + 1))
graph <- graph + geom_point()
ggsave(paste("graphs/",teamId,"events.png", sep=""), height=20)