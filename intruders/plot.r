# set global chunk options
knitr::opts_chunk$set(echo = FALSE, warning=FALSE, message=FALSE, cache=FALSE)

suppressPackageStartupMessages(library(tidyverse))

#get the data
dnames <- read_csv("full_log.csv", col_types = "ccDD", locale = locale(date_format = "%d.%m.%Y %H:%M:%S"))

#entries with total count < 5 are grouped as other.
addressSummary <- dnames %>% group_by(address) %>% mutate(count=n()) %>% arrange(count) %>% ungroup %>% mutate(new_address=case_when(count <= 5 ~ "Other", count > 5 ~ address))

#split dates
addressSummary <- addressSummary %>% separate(registeredDate, c("Year", "Month", "Day", "Hour", "Minute", "Second"), sep = "-", remove = FALSE)

#Plot domain names by country
ggplot(addressSummary, aes(new_address)) + geom_bar(aes(x = reorder(new_address, count), fill=new_address), width = 0.3, colour="white") + scale_fill_brewer(palette = "Paired") + coord_flip() + labs(title="Земји од каде лица регистирале 5 или повеќе МК домени\n (во Other се групирани тие со помалку од 5)", x = "Земји", y = "Број на регистрирани домени", fill = "Земја")

#Plot domain registration by country over time
addressSummary %>% group_by(new_address, Year) %>% mutate(N=n()) %>% ggplot(aes(x=Year, y=N, group=new_address, colour=new_address)) + geom_line() + geom_point() + scale_color_brewer(palette="Paired") + labs(title="Регистрирани домени по земја на потекло на регистрант по години (во Other се групирани тие со помалку од 5)", x = "Години", y = "Број на регистрирани домени", color = "Земја") + theme(axis.text.x = element_text(angle=45, vjust=1, hjust=1))


