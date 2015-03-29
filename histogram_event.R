library(RSQLite)
require(ggplot2)

# get command line args
event <- "M150Y" #commandArgs(trailingOnly=TRUE)[1]
title <- "Men's 50 Yard Freestyle 2014-2015" #commandArgs(trailingOnly=TRUE)[2]
step <- .1 ##commandArgs(trailingOnly=TRUE)[3]

# get the date from the database
db <- dbConnect(SQLite(), dbname="collegeswimming.db")
table <- dbGetQuery(db, paste("select time from Swims where event='", event,"'", sep=""))

# graph and save the data
graph <- ggplot(data=table, aes(x=time))
graph <- graph + geom_histogram(aes(y=..density..), binwidth=step) 
graph <- graph + geom_density(color="red", alpha=.4)
graph <- graph + ggtitle(title)
ggsave(filename=paste("graphs/", event,"_histogram.png"))
