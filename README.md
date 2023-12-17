# Bear-Market-Stock-Trading-Robot

***** Please be patient with me because this is a Really New Python Project and I am still looking for any bugs in the beta code. 
This message is posted on 11-26-2023. ***** 

***** Upgrade to the newest version of this Python Robot today because some Python code updates were finished and some errors were recently fixed on 12-10-2023. *****

A stock trading robot for the 2023 and likely 2024 "bear market" conditions for the USA stock market. 

A bear market can be identified if a length of time like a month or a few months is consistently 
causing a daily portfolio loss or a decrease in money every 24 hours. 
( This is describing a condition of Losing money daily when you have been trading on the Bullish ETF Fund side or Long side. )

***** Then you need to realize that it is a bear market. ***** 

***** The problem that is a loss of profit when holding stock positions overnight is known as a Bear Market. It is extremely important to know if the market is currently a Bull Market or a Bear Market before deciding to hold stock positions overnight.

I recommend that you primarily invest in Vanguard ETF funds to be defensive against loss of profit when holding overnight stock positions. 

***** You are fortunate that I have a python script that checks if the Stock Market is currently a Bear Market or a Bull Market. I recommend running it every 24 hours to be alerted of changes from Bull Market to Bear Market conditions: 

https://github.com/CodeProSpecialist/Stock-Market-Status-Check-for-a-Bear-Market-or-a-Bull-Market

*****

A bear market is not always identified as a 100% recession, although a bear market can precede a recession. 
A bear market can also precede an all-out widespread stock market crash, so be careful. 

Trading in a bear market is effective when only 
being strict about purchasing ETF Funds that are Bearish on the Short side. 

Run the commands below:

python3 ETF-fund-backtesting-for-profit-stock-list-writer.py

or

python3 performance-stock-list-writer.py

or

python3 new-performance-stock-list-writer.py

open an additional command line terminal and run the following command:

python3 bear-market-stock-robot.py 

( My personal new favorite stock list writer is: ETF-fund-backtesting-for-profit-stock-list-writer.py )


Disclaimer:

This software is not affiliated with or endorsed by TradingView or Alpaca Securities, LLC. It aims to be a valuable tool for stock market trading, but all trading involves risks. Use it responsibly and consider seeking advice from financial professionals.

Important: Don't forget to regularly update your list of stocks to buy and keep an eye on the market conditions. Happy trading!

Remember that all trading involves risks. The ability to successfully implement these strategies depends on both market conditions and individual skills and knowledge. As such, trading should only be done with funds that you can afford to lose. Always do thorough research before making investment decisions, and consider consulting with a financial advisor. This is use at your own risk software. This software does not include any warranty or guarantees other than the useful tasks that may or may not work as intended for the software application end user. The software developer shall not be held liable for any financial losses or damages that occur as a result of using this software for any reason to the fullest extent of the law. Using this software is your agreement to these terms. This software is designed to be helpful and useful to the end user.

Place your alpaca code keys in the location: /home/name-of-your-home-folder/.bashrc Be careful to not delete the entire .bashrc file. Just add the 4 lines to the bottom of the .bashrc text file in your home folder, then save the file. .bashrc is a hidden folder because it has the dot ( . ) in front of the name. Remember that the " # " pound character will make that line unavailable. To be helpful, I will comment out the real money account for someone to begin with an account that does not risk using real money. The URL with the word "paper" does not use real money. The other URL uses real money. Making changes here requires you to reboot your computer or logout and login to apply the changes.

The 4 lines to add to the bottom of .bashrc are:

export APCA_API_KEY_ID='zxzxzxzxzxzxzxzxzxzxz'

export APCA_API_SECRET_KEY='zxzxzxzxzxzxzxzxzxzxzxzxzxzxzxzxzxzxzxzx'

#export APCA_API_BASE_URL='https://api.alpaca.markets'

export APCA_API_BASE_URL='https://paper-api.alpaca.markets'
