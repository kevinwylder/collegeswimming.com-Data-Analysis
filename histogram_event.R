library(RSQLite)
require(ggplot2)

# get command line args
event <- commandArgs(trailingOnly=TRUE)[1]
title <- commandArgs(trailingOnly=TRUE)[2]
db <- dbConnect(SQLite(), dbname=commandArgs(trailingOnly=TRUE)[3])
print(db)

# get the date from the database
table <- dbGetQuery(db, paste("select time from Swims where event='", event,"' and taper!=3", sep=""))

# calculate a good step size
step <- sd(table$time) / 5

# graph and save the data
graph <- ggplot(data=table, aes(x=time))
graph <- graph + geom_histogram(aes(y=..density..), binwidth=step)
graph <- graph + geom_density(color="red", alpha=.4)
graph <- graph + ggtitle(title)
ggsave(filename=paste("graphs/histogram_", event,".png"))
